import pandas as pd
from datetime import timedelta

# ------------------------------------------------------------
# Priority order (higher number = higher priority)
# ------------------------------------------------------------
CAUSE_PRIORITY = {
    "BPDU_GUARD": 6,          # STP errdisable (highest)
    "IF_FLAP": 5,             # Physical link down
    "POE_ERR": 4,             # PoE electrical failure
    "AP_CRASH": 3,            # AP reboot due to crash
    "AP_CONFIG_FAILOVER": 2,  # AP config / IP failover
    "CAPWAP_ERR": 1,          # WAN / control plane
}

# ------------------------------------------------------------
# Load AP → Switch mapping
# ------------------------------------------------------------
def load_ap_switch_map(path):
    df = pd.read_csv(path)
    df["ap_name"] = df["ap_name"].str.lower()
    df["switch"] = df["switch"].str.lower()
    df["port"] = df["port"].str.lower()
    return df


# ------------------------------------------------------------
# Correlation engine with cause prioritization
# ------------------------------------------------------------
def correlate(events, ap_map, window_minutes=180):
    incidents = []
    window = timedelta(minutes=window_minutes)

    # Normalize events
    for ev in events:
        ev["etype"] = ev["etype"].upper()
        ev["raw_lc"] = ev["raw"].lower()

    # Group AP_DISJOIN events by AP
    ap_disjoins = {}
    for ev in events:
#        if ev["etype"] == "AP_DISJOIN":
         if ev["etype"] in ("AP_DISJOIN", "AP_CRASH"):
            ap = ev["context"]["ap"].lower()
            ap_disjoins.setdefault(ap, []).append(ev)

    # Process each AP
    for ap, disjoin_events in ap_disjoins.items():

        # Use first disjoin as incident start
        disjoin_time = disjoin_events[0]["timestamp"]

        # Lookup AP mapping
        row = ap_map[ap_map["ap_name"] == ap]
        if row.empty:
            continue

        switch = row.iloc[0]["switch"]
        port = row.iloc[0]["port"]
        site = row.iloc[0].get("site", "UNKNOWN")

        # Find candidate LAN/WAN events in time window
        candidates = []
        for ev in events:
            if abs(ev["timestamp"] - disjoin_time) <= window:
                # IF_FLAP must match port
                if ev["etype"] == "IF_FLAP" and port in ev["raw_lc"]:
                    candidates.append(ev)
                # POE_ERR must match port
                elif ev["etype"] == "POE_ERR" and port in ev["raw_lc"]:
                    candidates.append(ev)
                # AP_CRASH must match port
                elif ev["etype"] == "AP_CRASH" and port in ev["raw_lc"]:
                    candidates.append(ev)
                # BPDU_GUARD must match port
                elif ev["etype"] == "BPDU_GUARD" and port in ev["raw_lc"]:
                    candidates.append(ev)    
                # CAPWAP_ERR is controller-wide
                elif ev["etype"] == "CAPWAP_ERR":
                    candidates.append(ev)

        # Select highest-priority cause
        root_cause = None
        highest_priority = 0

        for ev in candidates:
            prio = CAUSE_PRIORITY.get(ev["etype"], 0)
            if prio > highest_priority:
                highest_priority = prio
                root_cause = ev

        # Check for AP_JOIN (recovery)
        recovery = None
        for ev in events:
            if ev["etype"] == "AP_JOIN":
                if ev["context"]["ap"].lower() == ap:
                    if ev["timestamp"] > disjoin_time:
                        recovery = ev
                        break

        # Build incident
        incident = {
            "ap": ap,
            "site": site,
            "switch": switch,
            "port": port,
            "disjoin_time": disjoin_time,
            "root_cause_type": root_cause["etype"] if root_cause else "UNKNOWN",
            "root_cause_event": root_cause,
            "recovered": True if recovery else False,
            "recovery_time": recovery["timestamp"] if recovery else None,
            "all_disjoins": disjoin_events,
            "candidate_events": candidates,
        }

        incidents.append(incident)

    return incidents

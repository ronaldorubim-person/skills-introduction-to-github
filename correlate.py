import pandas as pd
from datetime import timedelta

# ------------------------------------------------------------
# Cause priority (higher = stronger root cause)
# ------------------------------------------------------------
CAUSE_PRIORITY = {
    "BPDU_GUARD": 6,          # STP / errdisable
    "IF_FLAP": 5,             # Physical link down
    "POE_ERR": 4,             # PoE fault
    "AP_CRASH": 3,            # AP reboot
    "AP_CONFIG_FAILOVER": 2,  # AP config issue
    "CAPWAP_ERR": 1,          # WAN/control plane
    "AAA_TIMEOUT": 1,         # AAA issues
}

# ------------------------------------------------------------
# Normalize / match interface names
# ------------------------------------------------------------
def port_match(port, raw):
    p = port.lower()
    r = raw.lower()

    # normalize long/short interface naming
    short = p.replace("gigabitethernet", "gi")
    return (p in r) or (short in r)


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
# Correlation engine
# ------------------------------------------------------------
def correlate(events, ap_map, window_minutes=20):

    incidents = []
    window = timedelta(minutes=window_minutes)

    # Normalize events
    for ev in events:
        ev["etype"] = ev["etype"].upper()
        ev["raw_lc"] = ev["raw"].lower()

    # --------------------------------------------------------
    # Group AP-trigger events (AP_DISJOIN OR AP_CRASH)
    # --------------------------------------------------------
    ap_triggers = {}

    for ev in events:
        if ev["etype"] in ("AP_DISJOIN", "AP_CRASH"):
            ap = ev["context"].get("ap", "").lower()
            if not ap:
                continue

            ap_triggers.setdefault(ap, []).append(ev)

    # --------------------------------------------------------
    # Process each AP
    # --------------------------------------------------------
    for ap, trigger_events in ap_triggers.items():

        # earliest trigger defines incident time
        incident_time = min(e["timestamp"] for e in trigger_events)

        # lookup AP mapping
        row = ap_map[ap_map["ap_name"] == ap]
        if row.empty:
            continue

        switch = row.iloc[0]["switch"]
        port = row.iloc[0]["port"]
        site = row.iloc[0].get("site", "UNKNOWN")

        # ----------------------------------------------------
        # Find candidate causal events
        # ----------------------------------------------------
        candidates = []

        for ev in events:

            # time filter
            if abs(ev["timestamp"] - incident_time) > window:
                continue

            # ----- LAN events -----
            if ev["etype"] == "IF_FLAP" and port_match(port, ev["raw_lc"]):
                candidates.append(ev)

            elif ev["etype"] == "POE_ERR" and port_match(port, ev["raw_lc"]):
                candidates.append(ev)

            elif ev["etype"] == "BPDU_GUARD" and port_match(port, ev["raw_lc"]):
                candidates.append(ev)

            # ----- AP-side events -----
            elif ev["etype"] in ("AP_CRASH", "AP_CONFIG_FAILOVER"):
                if ev["context"].get("ap", "").lower() == ap:
                    candidates.append(ev)

            # ----- Network/control events -----
            elif ev["etype"] in ("CAPWAP_ERR", "AAA_TIMEOUT"):
                candidates.append(ev)

        # ----------------------------------------------------
        # Root cause selection
        # ----------------------------------------------------
        root_cause = None

        # ✅ Step 1: use candidates if available
        if candidates:
            types = {e["etype"] for e in candidates}
            
            # AP crash overrides IF_FLAP if simultaneous
            if "AP_CRASH" in types and "IF_FLAP" in types:
                root_cause = next(e for e in candidates if e["etype"] == "AP_CRASH")

            elif "IF_FLAP" in types:
                root_cause = next(e for e in candidates if e["etype"] == "IF_FLAP")

            else:
                root_cause = max(
                    candidates,
                    key=lambda e: CAUSE_PRIORITY.get(e["etype"], 0)
                )

        # ✅ Step 2: fallback → check AP triggers
        else:
            trigger_types = {e["etype"] for e in trigger_events}
            # ✅ CRITICAL FIX
            if "AP_CRASH" in trigger_types:
                root_cause = next(e for e in trigger_events if e["etype"] == "AP_CRASH")

            elif "AP_CONFIG_FAILOVER" in trigger_types:
                root_cause = next(e for e in trigger_events if e["etype"] == "AP_CONFIG_FAILOVER")

        # ----------------------------------------------------
        # Detect AP recovery
        # ----------------------------------------------------
        recovery = None

        for ev in events:
            if ev["etype"] == "AP_JOIN":
                if ev["context"].get("ap", "").lower() == ap:
                    if ev["timestamp"] > incident_time:
                        recovery = ev
                        break

        # ----------------------------------------------------
        # Build incident object
        # ----------------------------------------------------
        incident = {
            "ap": ap,
            "site": site,
            "switch": switch,
            "port": port,
            "incident_time": incident_time,
            "root_cause_type": root_cause["etype"] if root_cause else "NO_CAUSE_DETECTED",
            "root_cause_origin": "LAN" if root_cause and root_cause["etype"] in ("IF_FLAP","POE_ERR","BPDU_GUARD") else "AP",
            "root_cause_event": root_cause,
            "recovered": True if recovery else False,
            "recovery_time": recovery["timestamp"] if recovery else None,
            "trigger_events": trigger_events,
            "candidate_events": candidates,
        }

        incidents.append(incident)

    return incidents

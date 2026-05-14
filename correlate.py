import pandas as pd
from datetime import timedelta

# ------------------------------------------------------------
# Cause priority (higher = stronger root cause)
# ------------------------------------------------------------
CAUSE_PRIORITY = {
    "BPDU_GUARD": 6,
    "IF_FLAP": 5,
    "POE_ERR": 4,
    "AP_CRASH": 3,
    "AP_CONFIG_FAILOVER": 2,
    "CAPWAP_ERR": 1,
    "AAA_TIMEOUT": 1,
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
# Correlation engine
# ------------------------------------------------------------
def correlate(events, ap_map, window_minutes=10):
    incidents = []
    window = timedelta(minutes=window_minutes)

    # Normalize events
    for ev in events:
        ev["etype"] = ev["etype"].upper()
        ev["raw_lc"] = ev["raw"].lower()

    # --------------------------------------------------------
    # Build AP-trigger events (AP_DISJOIN or AP_CRASH)
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

        incident_time = min(e["timestamp"] for e in trigger_events)

        # Lookup AP mapping
        row = ap_map[ap_map["ap_name"] == ap]
        if row.empty:
            continue

        switch = row.iloc[0]["switch"]
        port = row.iloc[0]["port"]
        site = row.iloc[0].get("site", "UNKNOWN")

        # ----------------------------------------------------
        # Find candidate causal events in time window
        # ----------------------------------------------------
        candidates = []

        for ev in events:
            if abs(ev["timestamp"] - incident_time) > window:
                continue

            if ev["etype"] == "IF_FLAP" and port in ev["raw_lc"]:
                candidates.append(ev)
            elif ev["etype"] == "POE_ERR" and port in ev["raw_lc"]:
                candidates.append(ev)
            elif ev["etype"] == "BPDU_GUARD" and port in ev["raw_lc"]:
                candidates.append(ev)
            elif ev["etype"] in ("AP_CRASH", "AP_CONFIG_FAILOVER"):
                if ev["context"].get("ap", "").lower() == ap:
                    candidates.append(ev)
            elif ev["etype"] in ("CAPWAP_ERR", "AAA_TIMEOUT"):
                candidates.append(ev)

        # ----------------------------------------------------
        # Determine root cause
        # ----------------------------------------------------
        root_cause = None

        types = {e["etype"] for e in candidates}

        # Special rule: LAN beats AP crash
        if "IF_FLAP" in types and "AP_CRASH" in types:
            root_cause = next(e for e in candidates if e["etype"] == "IF_FLAP")

        elif candidates:
            root_cause = max(
                candidates,
                key=lambda e: CAUSE_PRIORITY.get(e["etype"], 0)
            )

        # ----------------------------------------------------
        # Detect recovery (AP_JOIN)
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
            "root_cause_type": root_cause["etype"] if root_cause else "UNKNOWN",
            "root_cause_event": root_cause,
            "recovered": True if recovery else False,
            "recovery_time": recovery["timestamp"] if recovery else None,
            "trigger_events": trigger_events,
            "candidate_events": candidates,
        }

        incidents.append(incident)

    return incidents
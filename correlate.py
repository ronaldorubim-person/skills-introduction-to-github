import pandas as pd

# ---------------------------------------------------------------------
# Load AP → Switch mapping
# site_mapping.csv must contain:
# ap_name,switch,port,site
# ---------------------------------------------------------------------
def load_ap_switch_map(path):
    df = pd.read_csv(path)
    df["ap_name"] = df["ap_name"].astype(str)
    df["switch"] = df["switch"].astype(str)
    df["port"] = df["port"].astype(str)
    return df


# ---------------------------------------------------------------------
# The CORRELATOR:
# Detects AP storm patterns and correlates them with LAN-side events.
#
# WLAN Event Types:
#   - AP_DISJOIN
#   - AP_JOIN
#
# LAN Event Types:
#   - IF_FLAP (switchport bouncing)
#   - POE_ERR (power issues on switch)
#
# Logic:
#   - If an AP disjoins >= 3 times within the scan window → possible AP storm
#   - Check AP→Switch mapping for the access switch & port
#   - If IF_FLAP or POE_ERR exists on that switch → likely LAN root cause
#
# Returns list of incidents for AI analysis.
# ---------------------------------------------------------------------
def correlate(events, ap_map):
    ap_storms = {}

    # Collect AP disjoins by AP name
    for ev in events:
        if ev["etype"] == "AP_DISJOIN":
            ap = ev["context"]["ap"]
            if ap not in ap_storms:
                ap_storms[ap] = []
            ap_storms[ap].append(ev)

    incidents = []

    # Process each AP
    for ap, evs in ap_storms.items():
        # Require minimum 3 events in window
        if len(evs) < 3:
            continue

        # Look up AP in the mapping file
        row = ap_map[ap_map["ap_name"].str.lower() == ap.lower()]
        if row.empty:
            continue

        sw = row.iloc[0]["switch"]
        port = row.iloc[0]["port"]
        site = row.iloc[0].get("site", "UNKNOWN")

        # Gather LAN-side faults for this switch
        lan_faults = [
            e for e in events
            if e["etype"] in ("IF_FLAP", "POE_ERR") and sw.lower() in e["raw"].lower()
        ]

        incidents.append({
            "ap": ap,
            "switch": sw,
            "port": port,
            "site": site,
            "ap_events": evs,
            "lan_faults": lan_faults
        })

    return incidents
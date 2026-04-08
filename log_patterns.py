import re

# ------------------------------------------------------------
# Syslog Pattern Definitions
# ------------------------------------------------------------
# These regex patterns identify high-value Cisco events that are
# critical for WLAN/LAN/WAN correlation. Designed specifically
# for Cisco Catalyst 9800 WLCs + Cisco IOS-XE switches.
# ------------------------------------------------------------

PATTERNS = {
    # Wireless AP Disjoin
    "AP_DISJOIN": re.compile(
        r"%APMGR-5-AP_DISJOINED.*AP\s+(?P<ap>[A-Za-z0-9_.:-]+)",
        re.IGNORECASE
    ),

    # Wireless AP Join
    "AP_JOIN": re.compile(
        r"%APMGR-5-AP_JOIN.*AP\s+(?P<ap>[A-Za-z0-9_.:-]+)",
        re.IGNORECASE
    ),

    # LAN Interface Flap
    "IF_FLAP": re.compile(
        r"%LINK-3-UPDOWN: Interface\s+(?P<intf>[\w/.:-]+),.*state",
        re.IGNORECASE
    ),

    # PoE Errors (brownouts, denies, controller faults)
    "POE_ERR": re.compile(
        r"%ILPOWER-.*(DENY|FAULT|ERR|UNSUPPORTED|CONTROLLER)",
        re.IGNORECASE
    ),

    # AAA / RADIUS Failures
    "RADIUS_TIMEOUT": re.compile(
        r"%AAA-3-RADIUS_TIMEOUT",
        re.IGNORECASE
    ),

    # DFS Radar Detection (RF instability)
    "DFS": re.compile(
        r"%DOT11-4-DFS_RADAR_DETECTED",
        re.IGNORECASE
    ),

    # CAPWAP Errors (AP tunnel/control instability)
    "CAPWAP_ERR": re.compile(
        r"%CAPWAP-.*(ERROR|DTLS|JOIN|RECV|TIMEOUT)",
        re.IGNORECASE
    ),
}
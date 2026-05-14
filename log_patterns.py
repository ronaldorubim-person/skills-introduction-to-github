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
        r"AP Name:\s+(?P<ap>[A-Za-z0-9_.:-]+).*Disjoined",
        re.IGNORECASE
    ),

    # Wireless AP Join
    "AP_JOIN": re.compile(
        r"AP Name:\s+(?P<ap>[A-Za-z0-9_.:-]+).*Joined",
        re.IGNORECASE
    ),
    
    # AP CRASH
    "AP_CRASH": re.compile(
        r"Last\s+(?P<ap>[A-Za-z0-9_.:-]+)\s+reboot was due to crash",
        re.IGNORECASE
    ),

    # AP Config Failover
    "AP_CONFIG_FAILOVER": re.compile(
        r"error received from AP\s+(?P<ap>[A-Za-z0-9_.:-]+).*failover occurred",
        re.IGNORECASE
    ),

    # AP CAPWAP Errors (AP tunnel/control instability)
    "CAPWAP_ERR": re.compile(
        r"%CAPWAP-.*(ERROR|DTLS|JOIN|RECV|TIMEOUT)",
        re.IGNORECASE
    ),

    # LAN Interface Flap
        "IF_FLAP": re.compile(
        r"%LINK-\d+-UPDOWN:\s+Interface\s+(?P<intf>[\w/]+),\s+changed state to down",
        re.IGNORECASE
    ),
    
    # LAN BPDU Guard
    "BPDU_GUARD": re.compile(
        r"%SPANTREE-\d+-BLOCK_BPDUGUARD.*port\s+(?P<intf>[\w/]+).*Disabling port",
        re.IGNORECASE
    ),

    # LAN PoE Errors (brownouts, denies, controller faults)
    "POE_ERR": re.compile(
        r"%ILPOWER-\d+-CONTROLLER_PORT_ERR.*Interface\s+(?P<intf>[\w/]+)",
        re.IGNORECASE
    ),
    
    
    # AAA / RADIUS Failures
    "RADIUS_TIMEOUT": re.compile(
        r"%AAA-\d+-RADIUS_TIMEOUT.*AP\s+(?P<ap>[A-Za-z0-9_.:-]+)",
        re.IGNORECASE
    ),

    # DFS Radar Detection (RF instability)
    "DFS": re.compile(
        r"%DOT11-4-DFS_RADAR_DETECTED",
        re.IGNORECASE
    ),
}

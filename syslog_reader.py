import datetime as dt
from log_patterns import PATTERNS


# ---------------------------------------------------------------------
# Extract the timestamp from Kiwi syslog lines
# ---------------------------------------------------------------------
def extract_timestamp(line):
    """
    Parses typical Kiwi syslog timestamps:
      Example: "Feb 03 15:11:22 HOSTNAME %APMGR-5-AP_DISJOINED ..."
    """
    try:
        month = line[0:3]
        day = int(line[4:6])
        timepart = line[7:15]
        year = dt.datetime.now().year

        dt_str = f"{month} {day} {year} {timepart}"
        return dt.datetime.strptime(dt_str, "%b %d %Y %H:%M:%S")

    except Exception:
        return None


# ---------------------------------------------------------------------
# Parse a single syslog line into a structured event
# ---------------------------------------------------------------------
def parse_syslog_line(line):
    ts = extract_timestamp(line)
    if not ts:
        return None

    # Match patterns defined in log_patterns.py
    for etype, regex in PATTERNS.items():
        m = regex.search(line)
        if m:
            return {
                "timestamp": ts,
                "etype": etype,
                "context": m.groupdict(),
                "raw": line.strip(),
            }

    return None


# ---------------------------------------------------------------------
# Read all syslog files and return list of matching events
# ---------------------------------------------------------------------
def read_logs(paths, minutes):
    """
    Reads all logs from the configured syslog_paths for the last <minutes>.
    Returns: list of parsed events.
    """
    cutoff = dt.datetime.now() - dt.timedelta(minutes=minutes)
    events = []

    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    ev = parse_syslog_line(line)
                    if ev and ev["timestamp"] >= cutoff:
                        events.append(ev)
        except FileNotFoundError:
            # Skip missing files silently
            pass

    return events
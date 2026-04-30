import datetime as dt
from log_patterns import PATTERNS
import re

# ---------------------------------------------------------------------
# Extract the timestamp from Kiwi syslog lines
# ---------------------------------------------------------------------
def extract_timestamp(line):
    """
    Supports Kiwi hybrid format:
    2026-04-23,10:59:06,hostname,id: Apr 23 14:59:04.715: MESSAGE
    """
    import re

    # 1) Kiwi timestamp (preferred)
    m = re.match(r"(\d{4}-\d{2}-\d{2}),(\d{2}:\d{2}:\d{2})", line)
    if m:
        try:
            ts = f"{m.group(1)} {m.group(2)}"
            return dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    # 2) Cisco timestamp fallback
    m = re.search(r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\.\d+", line)
    if m:
        try:
            year = dt.datetime.now().year
            ts = f"{m.group(1)} {year}"
            return dt.datetime.strptime(ts, "%b %d %H:%M:%S %Y")
        except Exception:
            pass

    return None


# ---------------------------------------------------------------------
# Parse a single syslog line into a structured event
# ---------------------------------------------------------------------
def parse_syslog_line(line):
    """
    Returns a LIST of matched events (can be empty).
    """
    ts = extract_timestamp(line)
    if not ts:
        return []

    matched = []

    for etype, regex in PATTERNS.items():
        m = regex.search(line)
        if m:
            matched.append({
                "timestamp": ts,
                "etype": etype,
                "context": m.groupdict(),
                "raw": line.strip(),
            })

    return matched


# ---------------------------------------------------------------------
# Read all syslog files and return list of matching events
# ---------------------------------------------------------------------
def read_logs(paths, minutes):
    """
    Reads syslog files and returns a flat list of parsed events.
    """
    cutoff = dt.datetime.now() - dt.timedelta(minutes=minutes)
    events = []

    for p in paths:
        try:
            print(f"[DEBUG] Reading syslog file: {p}")
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parsed = parse_syslog_line(line)
                    if not parsed:
                        continue

                    for ev in parsed:           # ✅ correctly indented
                        if ev["timestamp"] >= cutoff:
                            events.append(ev)

        except FileNotFoundError:
            print(f"[WARN] Syslog file not found: {p}")

    return events

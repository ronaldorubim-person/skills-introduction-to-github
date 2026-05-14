import datetime as dt
import re
from collections import deque
from log_patterns import PATTERNS


# ---------------------------------------------------------------------
# Extract timestamp (Kiwi + Cisco hybrid)
# ---------------------------------------------------------------------
def extract_timestamp(line):
    """
    Supports formats like:
    2026-04-30,14:43:21,...
    or fallback Cisco format
    """

    # 1️⃣ Kiwi timestamp (preferred)
    m = re.match(r"(\d{4}-\d{2}-\d{2}),(\d{2}:\d{2}:\d{2})", line)
    if m:
        try:
            ts = f"{m.group(1)} {m.group(2)}"
            return dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except:
            pass

    # 2️⃣ Cisco timestamp fallback
    m = re.search(r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})", line)
    if m:
        try:
            year = dt.datetime.now().year
            ts = f"{m.group(1)} {year}"
            return dt.datetime.strptime(ts, "%b %d %H:%M:%S %Y")
        except:
            pass

    # Debug — show lines we fail to parse
    print("[WARN] Timestamp not parsed:", line.strip())
    return None


# ---------------------------------------------------------------------
# Parse a single line → multiple events
# ---------------------------------------------------------------------
def parse_syslog_line(line):
    ts = extract_timestamp(line)
    if not ts:
        return []

    matched_events = []

    for etype, regex in PATTERNS.items():
        m = regex.search(line)
        if m:
            matched_events.append({
                "timestamp": ts,
                "etype": etype,
                "context": m.groupdict(),
                "raw": line.strip(),
            })

    return matched_events


# ---------------------------------------------------------------------
# Read logs with 15-minute filtering + tail optimization
# ---------------------------------------------------------------------
def read_logs(paths, minutes):
    cutoff = dt.datetime.now() - dt.timedelta(minutes=minutes)

    events = []

    # LIMIT how many lines we read (performance)
    MAX_LINES = 5000

    for p in paths:
        try:
            print(f"[DEBUG] Reading last {MAX_LINES} lines from: {p}")

            # Read only last N lines
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                last_lines = deque(f, maxlen=MAX_LINES)

            # Process lines
            for line in last_lines:

                parsed_events = parse_syslog_line(line)

                if not parsed_events:
                    continue

                for ev in parsed_events:

                    # ✅ Time filter (last X minutes)
                    if ev["timestamp"] >= cutoff:
                        events.append(ev)

        except FileNotFoundError:
            print(f"[WARN] File not found: {p}")

    print(f"[DEBUG] Total events after filtering: {len(events)}")

    return events
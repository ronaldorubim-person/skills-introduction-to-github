import yaml
import os
from syslog_reader import read_logs
from correlate import load_ap_switch_map, correlate

# safe import
try:
    from ai_engine import analyze_incident
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# ------------------------------------------------------------
# Load config safely
# ------------------------------------------------------------
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


# ------------------------------------------------------------
# Main orchestration
# ------------------------------------------------------------
def main():

    config = load_config()

    paths = config.get("syslog_paths", [])
    minutes = config.get("time_window_minutes", 15)
    ap_map_file = config.get("ap_switch_map", "site_mapping.csv")

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    print(f"Reading last {minutes} minutes of syslog...")

    # --------------------------------------------------------
    # Read events
    # --------------------------------------------------------
    events = read_logs(paths, minutes)

    if not events:
        print("No events found in time window.")
        return

    # --------------------------------------------------------
    # Load AP mapping
    # --------------------------------------------------------
    ap_map = load_ap_switch_map(ap_map_file)

    # --------------------------------------------------------
    # Correlate incidents
    # --------------------------------------------------------
    incidents = correlate(events, ap_map, window_minutes=20)  # ✅ safer window

    if not incidents:
        print("No incidents detected.")
        return

    # --------------------------------------------------------
    # Process incidents
    # --------------------------------------------------------
    for i, inc in enumerate(incidents, 1):

        print("\n================ INCIDENT DETECTED ================")
        print(f"AP: {inc.get('ap')}")
        print(f"Switch: {inc.get('switch')}  Port: {inc.get('port')}  Site: {inc.get('site')}")

        # AI / deterministic analysis

        try:
            if AI_AVAILABLE:
                summary = analyze_incident(inc)
            else:
                summary = "[AI disabled] Basic analysis only"

        except Exception as e:
            summary = f"[AI Analysis Error] {e}"

        print("\nAI ANALYSIS:")
        print(summary)

        print("==================================================")

        # Save to file

        outfile = f"output/incident_{i}.txt"
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"Saved → {outfile}")

    print("\nDone.")

# ------------------------------------------------------------
# Entry point (correct)
# ------------------------------------------------------------
if __name__ == "__main__":
    main()

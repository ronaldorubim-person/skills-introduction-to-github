import yaml
import os
from syslog_reader import read_logs
from correlate import load_ap_switch_map, correlate
from ai_engine import analyze_incident


# ---------------------------------------------------------------------
# MAIN ORCHESTRATION LOGIC
# ---------------------------------------------------------------------
# Steps:
#   1. Load config
#   2. Read Kiwi Syslog logs
#   3. Parse & classify events
#   4. Detect AP storms + correlate LAN-side faults
#   5. Ask AI to analyze each incident
#   6. Store results in output/
#   7. (Optional) send summary to Zabbix trapper or Teams
# ---------------------------------------------------------------------
def main():

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # -----------------------------------------------------------------
    # Load config
    # -----------------------------------------------------------------
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    syslog_paths = cfg.get("syslog_paths", [])
    minutes = cfg.get("time_window_minutes", 15)
    ap_map_file = cfg.get("ap_switch_map")

    # -----------------------------------------------------------------
    # Read Syslog
    # -----------------------------------------------------------------
    print(f"Reading last {minutes} minutes of syslog...")
    events = read_logs(syslog_paths, minutes)

    if not events:
        print("No syslog events found in the last window.")
        return

    # -----------------------------------------------------------------
    # Load AP → Switch mapping
    # -----------------------------------------------------------------
    try:
        ap_map = load_ap_switch_map(ap_map_file)
    except Exception as e:
        print(f"Error loading AP switch map: {e}")
        return

    # -----------------------------------------------------------------
    # Detect incidents
    # -----------------------------------------------------------------
    incidents = correlate(events, ap_map)

    if not incidents:
        print("No incidents detected.")
        return

    # -----------------------------------------------------------------
    # Process each incident with AI
    # -----------------------------------------------------------------
    for idx, inc in enumerate(incidents, start=1):
        print("\n================ INCIDENT DETECTED ================")
        print(f"AP: {inc['ap']}")
        print(f"Switch: {inc['switch']}  Port: {inc['port']}  Site: {inc['site']}")

        # Invoke AI
        try:
            summary = analyze_incident(inc)
        except Exception as e:
            summary = f"[AI Analysis Error] {e}"

        # Print to console
        print("\nAI ANALYSIS:")
        print(summary)
        print("==================================================")

        # Save to output file
        outfile = f"output/incident_{idx}.txt"
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"Saved incident report → {outfile}")

    print("\nDone.")


# ---------------------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
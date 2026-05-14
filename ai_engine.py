#import openai


# ---------------------------------------------------------------------
# AI ENGINE: Converts correlated syslog events into human-readable
# root cause analysis using an LLM (GPT-4 or later).
# ---------------------------------------------------------------------
def analyze_incident(incident):
    """
    Accepts an incident dictionary:
    {
      "ap": "SAO-AP-11",
      "switch": "SAO-ACC-01",
      "port": "Gi1/0/24",
      "site": "SAO",
      "ap_events": [...],
      "lan_faults": [...]
    }

    Produces an LLM-generated summary containing:
      - Fault domain classification
      - Root cause explanation
      - Device involvement
      - User impact
      - Recommended next actions
    """

    ap = incident["ap"]
    sw = incident["switch"]
    port = incident["port"]
    site = incident.get("site", "UNKNOWN")

    # Combine syslog lines
    text_block = "\n".join(
        [e["raw"] for e in incident["ap_events"] + incident["lan_faults"]]
    )

    prompt = f"""
You are a senior Cisco network engineer AI responsible for correlating
WLAN (Catalyst 9800) and LAN (Cisco IOS-XE) syslog data.

Analyze the following syslog messages and produce a concise operational report.

Required output format:

FAULT DOMAIN:
LAN / WLAN / WAN / AAA / RF / PoE

ROOT CAUSE SUMMARY:
1–3 sentences explaining the root cause.

DEVICES INVOLVED:
List APs, switches, ports, controllers.

IMPACT TO USERS:
Summarize user-facing symptoms (AP outages, roaming issues, auth failures, etc.)

RECOMMENDED NEXT ACTIONS:
Actionable steps for the NOC.

----------------------------------------
SITE: {site}
AP: {ap}
SWITCH: {sw}
PORT: {port}

Syslog Extract:
{text_block}
----------------------------------------

Generate the final report below:
"""

    # Call LLM
    response = openai.ChatCompletion.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,       # keep output consistent & deterministic
        max_tokens=400
    )

    return response["choices"][0]["message"]["content"]
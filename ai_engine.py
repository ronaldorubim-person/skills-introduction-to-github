# Optional: enable AI later
# import openai

# ---------------------------------------------------------------------
# Build deterministic RCA (no AI dependency)
# ---------------------------------------------------------------------
def build_deterministic_summary(incident):

    ap = incident.get("ap")
    sw = incident.get("switch")
    port = incident.get("port")
    site = incident.get("site")
    cause = incident.get("root_cause_type")
    event = incident.get("root_cause_event")

    cause_map = {
        "IF_FLAP": "LAN / Physical",
        "POE_ERR": "LAN / PoE",
        "BPDU_GUARD": "LAN / Layer2",
        "AP_CRASH": "AP / Software",
        "AP_CONFIG_FAILOVER": "AP / Configuration",
        "CAPWAP_ERR": "WAN / Control",
        "AAA_TIMEOUT": "AAA",
    }

    fault_domain = cause_map.get(cause, "UNKNOWN")

    if not event:
        root_text = "No clear root cause event identified."
    else:
        root_text = f"{event.get('raw', '')}"

    summary = f"""
FAULT DOMAIN:
{fault_domain}

ROOT CAUSE SUMMARY:
Event '{cause}' detected. {root_text}

DEVICES INVOLVED:
AP: {ap}
Switch: {sw}
Port: {port}

IMPACT TO USERS:
Potential wireless disruption for users connected to this AP.

RECOMMENDED NEXT ACTIONS:
Investigate switch port {port} on {sw}, verify cabling, PoE status, and AP health.
"""

    return summary.strip()


# ---------------------------------------------------------------------
# Optional AI-enhanced analysis
# ---------------------------------------------------------------------
def analyze_incident(incident):

    # Always start with deterministic summary
    base_summary = build_deterministic_summary(incident)

    # If AI is NOT enabled → return deterministic output
    # (safe for production)
    USE_AI = False

    if not USE_AI:
        return base_summary

    # --------------------------------------------------
    # Optional AI path (if you enable OpenAI later)
    # --------------------------------------------------
    try:
        import openai

        prompt = f"""
You are a senior Cisco network engineer.

Based on this incident data:

{base_summary}

Refine the root cause analysis and provide:
- clearer explanation
- improved troubleshooting steps
"""

        response = openai.ChatCompletion.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400
        )

        return response["choices"][0]["message"]["content"]

    except Exception as e:
        return f"{base_summary}\n\n[AI Enhancement Failed: {e}]"

# AI Syslog Analysis Package
Cisco WLAN + LAN Correlation Engine  
Author: Internal Engineering Use  
Version: 1.0

---

## 📌 Overview

This package analyzes **Kiwi Syslog data** from:

- Cisco Catalyst 9800-CL WLCs  
- Cisco IOS-XE switches  
- FlexConnect APs across distributed sites  

It performs:

1. **Syslog Parsing**  
   Extracts timestamps, event types, AP names, switchports, PoE errors, RADIUS timeouts, DFS events, and CAPWAP errors.

2. **Event Correlation**  
   Merges WLAN + LAN signals:
   - AP storms  
   - Switchport flaps  
   - PoE brownouts  
   - WAN CAPWAP instability  
   - RADIUS timeout clusters  

3. **AI Root Cause Analysis**  
   Uses an LLM (GPT‑4 or later) to generate:
   - Fault domain (LAN/WLAN/WAN/AAA/PoE/RF)  
   - Human‑readable explanation  
   - Impact summary  
   - Recommended actions  

4. **Incident Output**  
   Each detected incident is written to:

# Python Threat-Intel Automation – Project 2 Report

## Executive Summary

This report documents Project 2 of a blue-team/SOC portfolio built by Aheedhul Faaiz: a lightweight SOAR-style Python automation pipeline that tails Wazuh alerts in real-time, enriches Indicators of Compromise (IOCs) against threat intelligence APIs (VirusTotal and AbuseIPDB), and delivers formatted alerts to a Discord channel for analyst triage.

Project 2 builds directly on the Wazuh SOC Home Lab established in Project 1, extending it from passive monitoring into active, automated threat intelligence enrichment — a key differentiator for SOC analyst roles.

## Objectives and Scope

The primary objective is to demonstrate automation skills that bridge the gap between alert generation (SIEM) and analyst action (triage), implementing the three pillars of SOAR:

- **Orchestration**: Connecting Wazuh alert output to external threat intelligence APIs
- **Automation**: Real-time Python script that parses, filters, and enriches alerts without manual intervention
- **Response**: Structured Discord notifications that give analysts enriched context at a glance

### Specific Goals

1. Tail `/var/ossec/logs/alerts/alerts.json` on the Wazuh manager in real-time
2. Extract IOCs (IP addresses and file hashes) from alert data
3. Enrich IPs via VirusTotal v3 and AbuseIPDB v2 APIs with rate-limit compliance
4. Enrich file hashes via VirusTotal file lookup
5. Send color-coded, embed-formatted alert cards to a Discord webhook
6. Handle errors gracefully (network failures, malformed JSON, API rate limits)
7. Never hardcode secrets — use environment variables or `.env` files

## Environment

- **Wazuh Manager**: Ubuntu Server 24.04 LTS (Wazuh 4.8.2 all-in-one)
- **Alert source**: `/var/ossec/logs/alerts/alerts.json` (NDJSON format)
- **Script runtime**: Python 3.x on the Wazuh manager (Ubuntu)
- **APIs**: VirusTotal v3 (free tier, 4 req/min), AbuseIPDB v2 (free tier, 1000 req/day)
- **Notification target**: Discord channel via webhook

## Architecture

```
Wazuh Manager (alerts.json)
        │
        ▼
  Python Script (wazuh_soar.py)
        │
        ├── Parse NDJSON alert
        ├── Extract IOCs (IPs, hashes)
        │
        ├──► VirusTotal API ──► IP/Hash reputation
        ├──► AbuseIPDB API  ──► IP abuse score
        │
        └──► Discord Webhook ──► Formatted alert embed
```

## Implementation

<!-- Document each phase as it is completed -->

### Phase 1: Alert Tailing and Parsing

**Status**: Complete

The `tail_alerts()` generator function implements real-time file tailing using Python's native `file.seek()` and `file.readline()` pattern. The function:

1. Opens `/var/ossec/logs/alerts/alerts.json` and seeks to the end (`seek(0, 2)`) to skip historical alerts
2. Continuously reads new lines with a 1-second poll interval
3. Parses each line as JSON (NDJSON format — one JSON object per line)
4. Yields parsed alert dicts to the caller, skipping malformed lines gracefully

**Key design decisions**:
- Seek-to-end on startup: avoids reprocessing thousands of historical alerts on restart
- `MIN_RULE_LEVEL = 5` filter: reduces noise from informational-level alerts (levels 0–4)
- `logging` module used instead of `print()` for timestamped, leveled output — professional practice
- API keys loaded from `.env` file via custom `load_dotenv()` — secrets never hardcoded in source

**Initial test** (2026-04-07): Successfully tailed alerts and captured Rule 92200 (Level 6) alerts from the Windows11 agent. Two malformed JSON warnings observed — caused by Wazuh writing a long alert across the readline boundary (a race condition during write). The error handling caught both gracefully.

### Phase 2: IOC Extraction

**Status**: Complete

Two extraction functions parse IOCs from alert data:

- `extract_ips()`: Pulls IPs from `data.srcip`, `data.dstip`, Sysmon `eventdata.sourceIp/destinationIp`, plus a broad regex sweep. Filters out RFC 1918 private IPs (10.x, 172.16-31.x, 192.168.x) to avoid enriching internal addresses.
- `extract_hashes()`: Parses Sysmon hash format (`SHA256=abc,MD5=def,...`) and FIM syscheck fields (`sha256_after`, etc.). Validates against known hash lengths (MD5=32, SHA1=40, SHA256=64).

### Phase 3: Threat Intel Enrichment (VirusTotal + AbuseIPDB)

*Coming soon*

### Phase 4: Discord Notification

*Coming soon*

### Phase 5: Error Handling and Rate Limiting

*Coming soon*

## MITRE ATT&CK Mapping

| Technique | ID | Relevance |
|-----------|----|-----------|
| Automated Collection | T1119 | Script automates IOC collection from alert stream |
| Indicator Removal on Host | T1070 | Detection gap — if attacker clears logs before alert is written |
| External Remote Services | T1133 | Enriching IPs that access external services |
| Command and Scripting Interpreter: Python | T1059.006 | The automation tool itself uses Python |

## Lessons Learned

*To be documented as the project progresses.*

## References

- [VirusTotal API v3 Documentation](https://docs.virustotal.com/reference/overview)
- [AbuseIPDB API v2 Documentation](https://docs.abuseipdb.com/)
- [Discord Webhook Documentation](https://discord.com/developers/docs/resources/webhook)
- [Wazuh Alert Format](https://documentation.wazuh.com/current/user-manual/manager/alert-logging.html)

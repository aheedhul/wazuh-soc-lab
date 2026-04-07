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

*Coming soon*

### Phase 2: IOC Extraction

*Coming soon*

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

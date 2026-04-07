"""
Wazuh SOAR — Lightweight Threat Intelligence Automation

Tails Wazuh alerts.json in real-time, enriches IOCs (IPs, file hashes)
via VirusTotal and AbuseIPDB, and sends formatted alerts to Discord.

Author: Aheedhul Faaiz
Project: wazuh-soc-lab (Project 2)

Usage:
    1. Copy .env.example to .env and fill in your API keys
    2. Run: python3 wazuh_soar.py
"""

import json
import os
import re
import time
import logging

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ALERTS_FILE = "/var/ossec/logs/alerts/alerts.json"
POLL_INTERVAL = 1  # seconds between each tail check

# Minimum Wazuh rule level to process (ignore low-noise alerts)
MIN_RULE_LEVEL = 5

# Private / internal IP ranges to SKIP enrichment on (RFC 1918 + loopback + link-local)
# No point sending 192.168.0.4 to VirusTotal — it's YOUR machine, not a threat
PRIVATE_IP_PATTERN = re.compile(
    r"^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|169\.254\.|::1|fe80:)"
)

# Regex to find IPv4 addresses in arbitrary text fields
IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

# Regex to find SHA256, SHA1, or MD5 hashes (hex strings of known lengths)
# SHA256=64 hex chars, SHA1=40, MD5=32
HASH_PATTERN = re.compile(r"\b([a-fA-F0-9]{64}|[a-fA-F0-9]{40}|[a-fA-F0-9]{32})\b")

# ---------------------------------------------------------------------------
# Logging setup — professional practice over raw print() statements
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("wazuh_soar")

# ---------------------------------------------------------------------------
# Environment — load secrets from .env file (or exported shell variables)
# ---------------------------------------------------------------------------

def load_dotenv(path: str = ".env") -> None:
    """Read key=value pairs from a .env file into os.environ."""
    if not os.path.isfile(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

VT_API_KEY = os.environ.get("VT_API_KEY", "")
ABUSEIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# ---------------------------------------------------------------------------
# Phase 1 — Tail alerts.json and parse each new NDJSON line
# ---------------------------------------------------------------------------

def tail_alerts(filepath: str):
    """
    Generator that yields new JSON alert objects as they are appended
    to the Wazuh alerts file (like 'tail -f' but in Python).

    How it works:
      1. Open the file and seek to the END (we only want NEW alerts).
      2. In a loop, read available lines.
      3. If no new data, sleep briefly and retry.
      4. Each non-empty line is one JSON object (NDJSON format).
    """
    with open(filepath, "r") as fh:
        # Move the file cursor to the end so we skip historical alerts
        fh.seek(0, 2)  # 0 offset from the end (whence=2)
        log.info("Tailing %s (starting from end of file)", filepath)

        while True:
            line = fh.readline()
            if not line:
                # No new data yet — wait before checking again
                time.sleep(POLL_INTERVAL)
                continue

            line = line.strip()
            if not line:
                continue

            # Try to parse the line as JSON
            try:
                alert = json.loads(line)
            except json.JSONDecodeError as exc:
                log.warning("Skipping malformed JSON line: %s", exc)
                continue

            yield alert


# ---------------------------------------------------------------------------
# Phase 2 — Extract IOCs (IPs and file hashes) from alert fields
# ---------------------------------------------------------------------------

def extract_ips(alert: dict) -> set:
    """
    Pull IP addresses from known Wazuh alert fields.

    Wazuh stores IPs in predictable locations depending on the alert type:
      - data.srcip  → source IP (e.g., brute-force attacker)
      - data.dstip  → destination IP (e.g., target of outbound connection)
      - data.win.eventdata.sourceIp / destinationIp → Sysmon network events
      - agent.ip    → the agent's own IP (usually internal, skip enrichment)

    We also do a broad regex sweep of the full alert JSON to catch IPs
    in unexpected fields, then filter out private/internal addresses.
    """
    ips = set()

    # --- Targeted extraction from known fields ---
    # data.srcip / data.dstip (Linux auth logs, firewall, etc.)
    data = alert.get("data", {})
    for field in ("srcip", "dstip"):
        ip = data.get(field)
        if ip:
            ips.add(ip)

    # data.win.eventdata (Sysmon Event 3 — network connection)
    win_event = data.get("win", {}).get("eventdata", {})
    for field in ("sourceIp", "destinationIp", "SourceIp", "DestinationIp"):
        ip = win_event.get(field)
        if ip:
            ips.add(ip)

    # --- Broad regex sweep for IPs anywhere in the alert ---
    alert_text = json.dumps(alert)
    for match in IPV4_PATTERN.findall(alert_text):
        # Basic validation: each octet must be 0-255
        octets = match.split(".")
        if all(0 <= int(o) <= 255 for o in octets):
            ips.add(match)

    # Filter out private/internal IPs — no point enriching 192.168.x.x
    public_ips = {ip for ip in ips if not PRIVATE_IP_PATTERN.match(ip)}

    return public_ips


def extract_hashes(alert: dict) -> set:
    """
    Pull file hashes from Wazuh alert fields.

    Sysmon logs file hashes in data.win.eventdata.hashes as a
    comma-separated string like "SHA256=abc123,MD5=def456,SHA1=..."
    FIM (syscheck) stores hashes in syscheck.sha256_after, etc.
    """
    hashes = set()
    data = alert.get("data", {})

    # --- Sysmon hash field (Events 1, 6, 7, 11, 15, etc.) ---
    win_event = data.get("win", {}).get("eventdata", {})
    hash_str = win_event.get("hashes", "") or win_event.get("Hashes", "")
    if hash_str:
        # Format: "SHA256=abc...,MD5=def...,SHA1=ghi..."
        for pair in hash_str.split(","):
            if "=" in pair:
                _, hash_val = pair.split("=", 1)
                hash_val = hash_val.strip()
                if HASH_PATTERN.match(hash_val):
                    hashes.add(hash_val)

    # --- FIM (syscheck) hash fields ---
    syscheck = alert.get("syscheck", {})
    for field in ("sha256_after", "sha1_after", "md5_after"):
        h = syscheck.get(field)
        if h and HASH_PATTERN.match(h):
            hashes.add(h)

    return hashes


def process_alert(alert: dict) -> None:
    """
    Receive a parsed alert dict and decide what to do with it.
    For now (Phase 1): log a summary line so we can verify tailing works.
    Later phases will add IOC extraction, enrichment, and Discord posting.
    """
    rule = alert.get("rule", {})
    rule_id = rule.get("id", "?")
    level = rule.get("level", 0)
    description = rule.get("description", "No description")
    agent_name = alert.get("agent", {}).get("name", "unknown")
    timestamp = alert.get("timestamp", "")

    # Filter: only process alerts at or above our minimum level
    if level < MIN_RULE_LEVEL:
        return

    log.info(
        "ALERT | Level %s | Rule %s | Agent: %s | %s",
        level, rule_id, agent_name, description,
    )

    # Phase 2: extract IOCs (IPs, hashes) from this alert
    public_ips = extract_ips(alert)
    file_hashes = extract_hashes(alert)

    if public_ips:
        log.info("  IOC IPs:    %s", ", ".join(sorted(public_ips)))
    if file_hashes:
        log.info("  IOC Hashes: %s", ", ".join(sorted(file_hashes)))

    # TODO Phase 3: enrich IOCs via VirusTotal / AbuseIPDB
    # TODO Phase 4: send enriched alert to Discord


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    log.info("=" * 60)
    log.info("Wazuh SOAR — Threat Intel Automation starting")
    log.info("=" * 60)

    # Verify the alerts file exists
    if not os.path.isfile(ALERTS_FILE):
        log.error("Alerts file not found: %s", ALERTS_FILE)
        log.error("Are you running this on the Wazuh manager?")
        raise SystemExit(1)

    # Verify API keys are loaded (warn but don't crash — Phase 1 doesn't need them)
    if not VT_API_KEY:
        log.warning("VT_API_KEY not set — VirusTotal enrichment will be skipped")
    if not ABUSEIPDB_API_KEY:
        log.warning("ABUSEIPDB_API_KEY not set — AbuseIPDB enrichment will be skipped")
    if not DISCORD_WEBHOOK_URL:
        log.warning("DISCORD_WEBHOOK_URL not set — Discord notifications will be skipped")

    # Start tailing and processing
    for alert in tail_alerts(ALERTS_FILE):
        process_alert(alert)


if __name__ == "__main__":
    main()

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
import time
import logging

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ALERTS_FILE = "/var/ossec/logs/alerts/alerts.json"
POLL_INTERVAL = 1  # seconds between each tail check

# Minimum Wazuh rule level to process (ignore low-noise alerts)
MIN_RULE_LEVEL = 5

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

    # TODO Phase 2: extract IOCs (IPs, hashes) from this alert
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

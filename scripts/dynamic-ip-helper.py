#!/usr/bin/env python3
import ipaddress
import os
import re
import subprocess
import sys

OSSEC_CONF = "/var/ossec/etc/ossec.conf"
CLIENT_KEYS = "/var/ossec/etc/client.keys"

def update_wazuh_agent_ip():
    print("--- Wazuh Agent Dynamic IP Helper ---")
    new_ip = input("Enter the new Ubuntu server IP address: ").strip()

    try:
        ipaddress.ip_address(new_ip)
    except ValueError:
        print("[!] Error: Invalid IP address format.")
        sys.exit(1)

    print("[*] Updating configuration file...")
    try:
        with open(OSSEC_CONF, "r") as file:
            config_data = file.read()

        updated_data = re.sub(r"<address>.*?</address>", f"<address>{new_ip}</address>", config_data)

        with open(OSSEC_CONF, "w") as file:
            file.write(updated_data)

    except PermissionError:
        print("[!] Error: You must run this script as root (sudo).")
        sys.exit(1)

    try:
        # Only run agent-auth if the agent has never been registered.
        # If client.keys already exists and has content, the agent
        # is already registered and just needs a restart.
        already_registered = (
            os.path.isfile(CLIENT_KEYS)
            and os.path.getsize(CLIENT_KEYS) > 0
        )

        if already_registered:
            print("[*] Agent already registered — skipping re-authentication.")
        else:
            print("[*] First-time registration — requesting key from server...")
            subprocess.run(["/var/ossec/bin/agent-auth", "-m", new_ip], check=True)

        print("[*] Restarting Wazuh agent...")
        subprocess.run(["systemctl", "restart", "wazuh-agent"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error: Command failed with exit code {e.returncode}")
        sys.exit(1)

    print(f"[+] Success! Kali agent is now reporting to {new_ip}")

if __name__ == "__main__":
    update_wazuh_agent_ip()

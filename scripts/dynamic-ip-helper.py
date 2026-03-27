#!/usr/bin/env python3
import ipaddress
import re
import subprocess
import sys

def update_wazuh_agent_ip():
    print("--- Wazuh Agent Dynamic IP Helper ---")
    new_ip = input("Enter the new Ubuntu server IP address: ").strip()

    try:
        ipaddress.ip_address(new_ip)
    except ValueError:
        print("[!] Error: Invalid IP address format.")
        sys.exit(1)

    file_path = "/var/ossec/etc/ossec.conf"

    print("[*] Updating configuration file...")
    try:
        with open(file_path, "r") as file:
            config_data = file.read()

        # Using regex to safely find and replace the IP address inside the <address> tags
        updated_data = re.sub(r"<address>.*?</address>", f"<address>{new_ip}</address>", config_data)

        with open(file_path, "w") as file:
            file.write(updated_data)
            
    except PermissionError:
        print("[!] Error: You must run this script as root (sudo).")
        sys.exit(1)

    try:
        print("[*] Requesting new security key...")
        subprocess.run(["/var/ossec/bin/agent-auth", "-m", new_ip], check=True)

        print("[*] Restarting Wazuh agent...")
        subprocess.run(["systemctl", "restart", "wazuh-agent"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error: Command failed with exit code {e.returncode}")
        sys.exit(1)

    print(f"✅ Success! Kali agent is now reporting to {new_ip}")

if __name__ == "__main__":
    update_wazuh_agent_ip()

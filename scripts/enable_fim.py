#!/usr/bin/env python3
import sys

file_path = "/var/ossec/etc/ossec.conf"

# The XML rule telling Wazuh to monitor our trap folder instantly
fim_rule = '    <directories realtime="yes">/root/soc_trap</directories>\n'

try:
    with open(file_path, "r") as file:
        lines = file.readlines()
except PermissionError:
    print("[!] Error: You must run this script as root (sudo).")
    sys.exit(1)
except FileNotFoundError:
    print(f"[!] Error: Configuration file not found at {file_path}")
    sys.exit(1)

# Check if FIM rule already exists to avoid duplicate injection
if any("/root/soc_trap" in line for line in lines):
    print("ℹ️  FIM rule for /root/soc_trap already exists. No changes made.")
    sys.exit(0)

# Loop through the configuration to find the Syscheck (FIM) section
for i in range(len(lines)):
    if "<syscheck>" in lines[i]:
        # Inject our rule right below the <syscheck> opening tag
        lines.insert(i + 1, fim_rule)
        break

with open(file_path, "w") as file:
    file.writelines(lines)

print("✅ FIM Real-Time Monitoring configured successfully via Python!")

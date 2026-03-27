#!/usr/bin/env python3

# Script to safely inject the Active Response XML block into the Wazuh Manager config
file_path = "/var/ossec/etc/ossec.conf"

xml_block = """
  <active-response>
    <command>firewall-drop</command>
    <location>local</location>
    <rules_id>5763</rules_id>
    <timeout>180</timeout>
  </active-response>
"""

try:
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Loop backwards through the list of lines to find the bottom configuration tag
    for i in range(len(lines)-1, -1, -1):
        if "</ossec_config>" in lines[i]:
            # Insert our XML block right before the closing tag
            lines.insert(i, xml_block)
            break

    with open(file_path, "w") as file:
        file.writelines(lines)

    print("✅ Active Response successfully injected via Python!")
    
except PermissionError:
    print("[!] Error: You must run this script as root (sudo).")

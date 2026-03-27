#!/bin/bash
# The line above is the "shebang". It tells Linux to use the Bash interpreter.
set -euo pipefail

# 1. Prompt the user for input (Like System.out.print / std::cout)
echo "Enter the new Ubuntu server IP address:"

# 2. Read the input into a variable (Like Scanner / std::cin)
read -r NEW_IP

# 3. Validate the IP address format before using it
if [[ ! "$NEW_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "[!] Error: Invalid IP address format."
    exit 1
fi

echo "[*] Updating configuration file..."
# 4. String manipulation: 'sed' searches for the old IP and replaces it with the variable $NEW_IP
sudo sed -i "s/<address>.*<\/address>/<address>${NEW_IP}<\/address>/g" /var/ossec/etc/ossec.conf

echo "[*] Requesting new security key..."
# 5. Execute the auth command using the variable
sudo /var/ossec/bin/agent-auth -m "$NEW_IP"

echo "[*] Restarting Wazuh agent..."
# 6. Restart the service
sudo systemctl restart wazuh-agent

echo "✅ Success! Kali is now reporting to $NEW_IP"

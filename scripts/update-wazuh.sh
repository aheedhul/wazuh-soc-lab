#!/bin/bash
# The line above is the "shebang". It tells Linux to use the Bash interpreter.

# 1. Prompt the user for input (Like System.out.print / std::cout)
echo "Enter the new Ubuntu server IP address:"

# 2. Read the input into a variable (Like Scanner / std::cin)
read NEW_IP

echo "[*] Updating configuration file..."
# 3. String manipulation: 'sed' searches for the old IP and replaces it with the variable $NEW_IP
sudo sed -i "s/<address>.*<\/address>/<address>$NEW_IP<\/address>/g" /var/ossec/etc/ossec.conf

echo "[*] Requesting new security key..."
# 4. Execute the auth command using the variable
sudo /var/ossec/bin/agent-auth -m $NEW_IP

echo "[*] Restarting Wazuh agent..."
# 5. Restart the service
sudo systemctl restart wazuh-agent

echo "✅ Success! Kali is now reporting to $NEW_IP"

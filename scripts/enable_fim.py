file_path = "/var/ossec/etc/ossec.conf"

# The XML rule telling Wazuh to monitor our trap folder instantly
fim_rule = '    <directories realtime="yes">/root/soc_trap</directories>\n'

with open(file_path, "r") as file:
    lines = file.readlines()

# Loop through the configuration to find the Syscheck (FIM) section
for i in range(len(lines)):
    if "<syscheck>" in lines[i]:
        # Inject our rule right below the <syscheck> opening tag
        lines.insert(i + 1, fim_rule)
        break

with open(file_path, "w") as file:
    file.writelines(lines)

print("✅ FIM Real-Time Monitoring configured successfully via Python!")

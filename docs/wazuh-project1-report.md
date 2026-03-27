# Wazuh SOC Home Lab – Project 1 Report

## Executive Summary

This report documents Project 1 of a blue-team/SOC portfolio built by Aheedhul Faaiz: a Wazuh-based Security Operations Center (SOC) home lab running on Ubuntu Server 24.04 LTS with Kali Linux and Windows 11 endpoints virtualized on VMware Workstation 17 Player. The lab demonstrates end‑to‑end SOC capabilities: SIEM deployment, agent onboarding, attack simulation, log analysis, file integrity monitoring, and automated response to brute‑force attacks.[^1]

The environment successfully detects and correlates SSH brute‑force activity from a Kali attacker using Hydra, escalates repeated authentication failures into a high‑severity brute‑force alert, and triggers Wazuh Active Response to firewall‑block the attacking IP in real time. It also employs File Integrity Monitoring (FIM) to detect the creation of a suspicious payload in a monitored directory, while explicitly documenting a visibility gap where a TCP SYN‑scan (Nmap -sS) generates no alert due to lack of underlying application logs.[^1]

This project is intended both as a learning vehicle and as portfolio evidence for near‑term SOC internship applications and longer‑term blue‑team roles, emphasizing practical troubleshooting, accurate detection logic, and honest reporting of what the lab can and cannot see.[^1]

## Objectives and Scope

The primary objective of this project is to build a realistic, small‑scale SOC lab that mirrors core workflows in an enterprise environment: ingesting endpoint telemetry, correlating events, simulating attacks, and responding to alerts. Rather than following purely theoretical material or guided CTFs, the focus is on operating a production‑grade open‑source SIEM (Wazuh) and documenting concrete attack–detection–response chains.[^1]

The specific goals are:

- Deploy Wazuh all‑in‑one (manager, indexer, dashboard) on Ubuntu Server and make it accessible from a Windows 11 host via HTTPS on port 443.[^1]
- Onboard at least one Linux endpoint (Kali) as both a monitored agent and an attacker, and prepare for a future Windows agent.[^1]
- Simulate real attacks (Nmap scan, SSH brute force, suspicious file drop) and understand exactly how—and whether—Wazuh detects them.
- Configure FIM on a targeted directory and confirm file‑creation alerts.
- Implement Wazuh Active Response so a high‑severity brute‑force alert results in automatic firewall blocking of the attacker IP.[^1]

The project is intentionally scoped as a foundation for follow‑on work: Python‑based log and threat‑intel automation (Project 2) and network forensics incident reporting (Project 3).

## Environment and Architecture

### Host and Virtualization

- Physical host: Windows 11 laptop running VMware Workstation 17 Player.[^1]
- Storage: External 512 GB HDD used to store VM disks to avoid overloading the internal drive.[^1]

### Virtual Machines

- **Ubuntu Server 24.04 LTS**
  - Role: Wazuh all‑in‑one stack (manager, indexer, dashboard, Filebeat).
  - Services: Wazuh manager, Wazuh indexer (OpenSearch‑based), Wazuh dashboard (HTTPS on port 443), Filebeat for log shipping.[^1]

- **Kali GNU/Linux Rolling 2026.1**
  - Role: Dual‑purpose endpoint and attacker.
  - Uses: Wazuh agent, Nmap, Hydra, and payload simulation for FIM.[^1]

- **Planned Windows endpoint**
  - Role: Future Wazuh agent to demonstrate Windows event log ingestion (not yet central to this report but planned as a next step).[^1]

### Network Topology

Initially the environment used NAT networking, but this complicated direct connectivity between the manager and agents. The topology was later shifted to bridged networking so both Ubuntu and Kali receive addresses on the same 192.168.x.x segment as the home router, simplifying manager–agent communication and attack simulation.[^1]

Logical roles:

- Windows 11 host: analyst workstation and hypervisor.
- Ubuntu Server: SIEM backend (log processing, indexing, dashboards, rules, Active Response).
- Kali: monitored endpoint and adversary emulation box for reconnaissance and brute‑force activity.[^1]

## Wazuh Deployment and Hardening

### Installation and Initial Access

Wazuh 4.8.2 was installed on Ubuntu Server using the official all‑in‑one deployment script, which provisioned the manager, indexer, Filebeat, and dashboard components. Installation logs confirmed successful startup of `wazuh-indexer`, `wazuh-manager`, `filebeat`, and `wazuh-dashboard` services.[^1]

On first login, the dashboard accepted factory default credentials (`admin/admin` and `kibanaserver/kibanaserver`), even though a `wazuh-passwords.txt` file existed with randomly generated strong credentials. This discrepancy indicated that the password‑injection step of the installer (which should push those generated credentials into the indexer’s security database) had not run correctly due to earlier corruption of the install script.[^1]

### Password Reconciliation with wazuh-passwords-tool

To bring the environment into a secure, production‑like state, the following remediation was performed:

1. Downloaded the official password‑sync tool for Wazuh 4.8 with `curl -sO https://packages.wazuh.com/4.8/wazuh-passwords-tool.sh` on the Ubuntu server.[^1]
2. Executed `sudo bash wazuh-passwords-tool.sh -a`, instructing it to regenerate and inject new complex passwords for core users such as `admin`, `kibanaserver`, `kibanaro`, `logstash`, `readall`, and `snapshotrestore`.[^1]
3. Copied and safely stored the newly generated credentials output by the script.
4. Restarted all key services—indexer, manager, Filebeat, and dashboard—so they would pick up the updated keystores and internal users configuration.[^1]

After this process, the default `admin/admin` login was replaced by a long, randomly generated `admin` password sourced from the tool output, eliminating the risky dependency on factory defaults and aligning the lab more closely with real‑world security practices.[^1]

## Agent Deployment and Linux Service Management

The Kali endpoint was configured as a Wazuh agent using the official installer command:

- `curl -s https://packages.wazuh.com/4.8/apt/install.sh | sudo WAZUH_MANAGER=<Ubuntu_IP> bash` (conceptual form).

This installer created the `wazuh-agent` service and registered the Kali machine with the manager’s IP on the bridged network.[^1]

To integrate cleanly with `systemd` and ensure persistence across reboots, the following service management commands were used on Kali:

- `sudo systemctl daemon-reload` to reload service definitions after installation.
- `sudo systemctl enable wazuh-agent` to configure the agent to start automatically at boot.
- `sudo systemctl start wazuh-agent` to start the agent immediately for the current session.[^1]

Through the Wazuh dashboard, the Kali box appeared as an Active agent, confirming successful bidirectional communication between agent and manager.[^1]

## Attack Scenarios and Detection Outcomes

This section summarizes the attack simulations performed from Kali against the Ubuntu server, along with the corresponding Wazuh detection behavior.

### Scenario 1 – Nmap SYN Scan (Visibility Gap)

- **Tool and command**: Nmap with a TCP SYN stealth scan (`-sS`) against the Ubuntu server’s IP to enumerate open ports.[^1]
- **Expectation**: Many beginners expect Wazuh or similar SIEMs to raise an alert when a SYN scan occurs.
- **Observed reality**: No Wazuh alert was generated for the Nmap -sS scan.

The reason is that Wazuh relies primarily on logs generated by the operating system and applications, not on raw network packets. A SYN scan that results in dropped or closed connections does not necessarily produce detailed log entries unless a host firewall or another network middleware explicitly logs that behavior. In this lab, the lack of such logs meant the scan was effectively invisible to Wazuh.[^1]

This outcome is documented in the project as a legitimate **visibility gap** rather than a failure of configuration, underscoring that SIEM visibility is limited by what the underlying infrastructure actually logs.

### Scenario 2 – SSH Brute Force with Hydra (Detected)

- **Tool and command**: Hydra from Kali, targeting the Ubuntu server’s SSH service with a dictionary‑based password guessing attack using `rockyou.txt` or a similar wordlist.[^1]
- **Telemetry path**: Each failed SSH attempt was recorded in `/var/log/auth.log` on Ubuntu, shipped to the Wazuh manager, decoded, and evaluated by correlation rules.

Wazuh processed these events in a two‑stage fashion:

1. Individual failed logins generated low‑severity alerts corresponding to generic authentication failures.
2. When the number of failures from a single source IP exceeded a defined threshold in a given time window, Wazuh escalated this to a high‑severity brute‑force event (Level 10), for example mapped to Rule 5763 (SSH brute‑force condition met).[^1]

In the dashboard, this appeared as a distinct brute‑force alert with the attacker source IP, target account, and MITRE ATT&CK tags for Credential Access > Brute Force (T1110 and relevant sub‑techniques).[^1]

### Scenario 3 – File Integrity Monitoring on /root/soc_trap (Detected)

- **Monitored directory**: `/root/soc_trap` on Ubuntu.
- **Configuration**: Wazuh File Integrity Monitoring (FIM) was configured to watch this directory in real time, tracking file creations, modifications, and deletions.[^1]

To simulate a post‑compromise scenario, a suspicious Python script (for example, `reverse_shell.py`) was dropped into `/root/soc_trap`.

- **Observed detection**: Wazuh generated a Level 5 alert such as “File added to the system” (Rule 554) showing the filename, path, and timestamp.[^1]
- **Analysis**: This demonstrates the lab’s ability to detect persistence or tooling dropped onto sensitive directories after an attacker gains a foothold, a common pattern in real incidents.

## Active Response – Automated Firewall Blocking

To move beyond passive detection, Wazuh Active Response was configured so that a high‑severity SSH brute‑force alert would trigger automatic mitigation.

### Configuration Approach

- Added an Active Response configuration (e.g., using XML in `ossec.conf`) instructing Wazuh to run a firewall helper script when specific brute‑force rule IDs fired at or above a defined severity.[^1]
- Used a small Python helper to inject or update the XML configuration reliably and avoid syntax errors, then restarted the Wazuh manager to apply changes.[^1]
- The Active Response action invoked `firewall-drop` (typically implemented with iptables/ufw) to add a temporary rule blocking the attacker source IP.

### Validation with Hydra

A second Hydra SSH brute‑force run from Kali was used to validate the automated response end‑to‑end:

- Wazuh again observed a burst of authentication failures, escalated them into a brute‑force alert, and immediately triggered the configured Active Response action.
- On the Kali side, Hydra began reporting `[ERROR] Timeout connecting` for subsequent attempts, indicating that the TCP connections were being dropped before completing the SSH handshake.[^1]
- In the Wazuh dashboard, corresponding Active Response events showed the firewall‑drop action being added (and later removed, if a timeout/expiration was configured), tying the block decision to the original brute‑force alert.[^1]

A key nuance acknowledged in the lab documentation is that threshold‑based detection cannot prevent the very first few login attempts; Wazuh must see enough failed attempts to trigger the brute‑force rule, after which Active Response interrupts the remainder of the attack. This precise timing was discussed and clarified to avoid overstating the system’s capabilities.[^1]

## Troubleshooting and Lessons Learned

### Installation and Credential Issues

The initial Wazuh installation exposed how partial script failures can leave back‑end services with factory default credentials even when password files have been generated. Resolving this required understanding how the installer’s final security configuration step works and then manually invoking the password‑sync tool to bring the indexer, dashboard, API, and related components into alignment.[^1]

### Kali Rolling Upgrade Problems

Because the Kali VM had been idle for some time, running `apt update && apt upgrade` triggered a large rolling‑release upgrade that produced several `dpkg` conflicts and errors such as `Sub-process /usr/bin/dpkg returned an error code 1`.[^1]

The recovery steps included:

- Running `sudo dpkg --configure -a` to complete partially configured packages.
- Using `sudo apt --fix-broken install` to resolve dependency issues.
- Cleaning up the package cache and unused dependencies with `apt clean` and `apt autoremove`.
- For specific file‑overwrite conflicts (e.g., involving `pyinstaller-hooks-contrib`), forcing installation with `dpkg -i --force-overwrite` before re‑running configuration and upgrades.[^1]

This troubleshooting phase reinforced practical Linux administration skills, including reading package‑manager error messages and understanding how to repair a broken rolling distribution.

### Networking and Connectivity

Agent connectivity issues highlighted the importance of understanding VMware networking modes (NAT vs bridged) and host firewalls. Through testing and iteration, Ubuntu and Kali were moved to a bridged network segment, simplifying connectivity and making IP addresses predictable and visible from the Windows analyst workstation.[^1]

These experiences echo common real‑world hurdles when deploying SIEM agents across mixed environments—misconfigured network segments and blocked agent ports are frequent sources of onboarding failures.

## Skills Demonstrated

By completing this project to its current state, Aheedhul Faaiz has demonstrated:

- **SIEM deployment and hardening**
  - Installed Wazuh all‑in‑one on Ubuntu Server, troubleshot installer corruption, and secured the environment by regenerating and synchronizing back‑end credentials using the official password tool.[^1]

- **Endpoint telemetry onboarding**
  - Deployed and configured a Wazuh agent on Kali, managed it via `systemctl`, and validated agent heartbeat and event flow in the dashboard.[^1]

- **Attack simulation and log analysis**
  - Executed Nmap and Hydra attacks from Kali and analyzed how Linux logs and Wazuh rules respond, including correctly identifying a blind spot where a SYN scan produced no logs and thus no alert.[^1]

- **Correlation and high‑fidelity alerts**
  - Observed and interpreted Wazuh’s escalation from individual authentication failures to a high‑severity brute‑force alert based on threshold logic and correlation rules (e.g., Rule 5763).[^1]

- **File Integrity Monitoring**
  - Configured FIM for a targeted directory and validated that adding a suspicious payload generated the expected file‑creation alert, demonstrating basic persistence detection capability.[^1]

- **Automated response engineering**
  - Implemented Wazuh Active Response so that an SSH brute‑force alert triggers firewall blocking of the attacker IP, and validated the behavior from both the attacker and defender perspectives.[^1]

- **Troubleshooting and systems thinking**
  - Recovered a broken Kali rolling‑release upgrade, resolved package conflicts, and iteratively debugged connectivity and configuration issues across OS, hypervisor, and SIEM layers.[^1]

## Future Work and Next Steps

This lab is deliberately designed as the foundation for additional blue‑team automation and analysis projects.

Planned next steps include:

- **Windows agent deployment**: Onboard a Windows endpoint to demonstrate ingestion of Windows event logs and show cross‑platform monitoring in Wazuh.[^1]
- **Custom rules and dashboards**: Implement custom Wazuh rules (for example, tuned thresholds for SSH brute force or execution from unusual directories) and build focused dashboards for authentication activity and security alerts.[^1]
- **Python log and threat‑intel automation (Project 2)**: Develop a Python tool that tails Wazuh `alerts.json`, enriches suspicious IPs with VirusTotal/AbuseIPDB, and sends formatted alerts to a Discord channel, effectively implementing a simple SOAR workflow.[^1]
- **Network forensics and incident reports (Project 3)**: Capture packet traces for the same attacks (Nmap, Hydra, HTTP attacks) and produce incident reports with Wireshark/Scapy analysis, mapping findings back to Wazuh alerts and MITRE ATT&CK techniques.[^1]

Together, these projects will form a cohesive SOC portfolio demonstrating not only tool usage, but also an understanding of detection mechanics, automation, and documented incident response workflows.

---
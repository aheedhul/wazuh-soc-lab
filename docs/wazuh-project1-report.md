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

## Windows Agent Deployment and Endpoint Hardening

### Agent Installation and Onboarding

A Windows 11 Pro endpoint (hostname: Elite) was onboarded as the second Wazuh agent (agent ID 002, named "Windows11"). The agent was installed using the official Wazuh 4.8.2 Windows installer and configured to report to the Wazuh manager over TCP/1514 on the bridged network.

On startup, the agent confirmed connectivity and immediately began collecting logs from the three default Windows Event Log channels: Application, Security, and System. It also ran an initial File Integrity Monitoring scan against the default monitored paths (critical system binaries in `%WINDIR%`, `System32`, and the Startup folder), a Security Configuration Assessment evaluation against the CIS Windows 11 Enterprise Benchmark v1.0.0, a Syscollector hardware and software inventory, and a Rootcheck anomaly scan.

### Sysmon Deployment for Deep Endpoint Visibility

Out of the box, Windows Security logs provide authentication events (Event IDs 4624/4625 for successful and failed logins) and basic system changes, but critically lack visibility into process execution, network connections, file creation, and DNS queries. To close this gap, Sysmon (System Monitor) v15.x from Microsoft Sysinternals was deployed with a custom minimal configuration.

The Sysmon configuration was designed to log four high‑value event types while filtering out known‑noisy Windows background processes:

- **Event ID 1 (Process Creation)**: Logs every new process with full command line, parent process tree, and MD5/SHA256 file hashes. Excludes known Windows internal processes such as `backgroundTaskHost.exe`, `SearchIndexer.exe`, `RuntimeBroker.exe`, and child processes of `svchost.exe` to reduce noise.
- **Event ID 3 (Network Connection)**: Logs which process initiates which network connection, with source and destination IP/port. Excludes `svchost.exe`, Windows Defender, and common broadcast/multicast ports (137, 138, 1900, 5353).
- **Event ID 11 (File Create)**: Logs new files created in high‑value locations (Desktop, Downloads, Documents, Temp, Startup, Start Menu) and files with executable or scripting extensions (`.exe`, `.dll`, `.bat`, `.cmd`, `.ps1`, `.vbs`, `.js`, `.hta`, `.scr`, `.lnk`). Uses include‑only mode to avoid drowning in temporary file noise.
- **Event ID 22 (DNS Query)**: Logs which process resolves which domain name, excluding common Microsoft infrastructure domains (`*.microsoft.com`, `*.windowsupdate.com`, `*.bing.com`, etc.) to focus on unusual or suspicious lookups.

All other Sysmon event types (DLL loads, registry modifications, process injection, etc.) were intentionally excluded from the initial configuration to keep the lab manageable, with a plan to expand coverage incrementally.

After installation, the Sysmon event channel (`Microsoft-Windows-Sysmon/Operational`) was added to the Wazuh agent's `ossec.conf` as a new `<localfile>` entry with `eventchannel` format. Upon agent restart, the log confirmed: `Analyzing event log: 'Microsoft-Windows-Sysmon/Operational'`.

### Windows Audit Policy Hardening

The default Windows 11 audit policy was found to have `Process Creation` set to `No Auditing`, meaning Event ID 4688 was not being generated. To provide a defense‑in‑depth layer alongside Sysmon, the following audit policy changes were applied:

- **Process Creation**: Enabled for Success and Failure — provides basic process execution logging as a fallback if Sysmon is ever stopped or tampered with.
- **Command‑line logging**: Enabled via registry key `ProcessCreationIncludeCmdLine_Enabled` under `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit`, ensuring Event ID 4688 entries include full command‑line arguments.
- **Logon/Logoff**: Confirmed at Success and Failure — preserves 4624/4625 event generation for authentication monitoring.
- **User Account Management** and **Security Group Management**: Enabled for Success — captures account creation (4720) and group membership changes (4732).
- **Audit Policy Change**: Enabled for Success — detects if an attacker disables auditing to cover their tracks.
- Noisy categories such as Object Access (Handle Manipulation, Filtering Platform Connection) and Privilege Use were explicitly kept disabled to avoid overwhelming the SIEM with low‑value events.

### Initial Alert Analysis and False Positive Identification

Immediately after Sysmon integration, Wazuh began generating alerts from the Windows endpoint. The first investigation session identified two categories of false positives:

1. **SCA‑induced process alerts**: The Wazuh SCA module, upon evaluating the CIS Windows 11 Enterprise benchmark, executed system commands such as `net.exe accounts` and `SecEdit.exe /export` to check security configurations. Sysmon captured these as process creation events, and Wazuh rules 92031 ("Discovery activity executed") and 92039 ("A net.exe account discovery command was initiated") fired repeatedly. Investigation confirmed the parent process was the Wazuh agent's SCA module, classifying these as false positives generated by the agent's own compliance checking.

2. **Browser auto‑update file drops**: The Brave browser's component updater extracted update files into `AppData\Local\Temp`, triggering Rule 92213 ("Executable file dropped in folder commonly used by malware") at Level 15 (maximum severity). Investigation confirmed the process was `brave.exe` performing routine component updates, classifying this as a false positive despite its critical severity rating — demonstrating that alert severity alone does not determine whether an event is malicious.

### CIS Benchmark Baseline

The initial SCA evaluation against the CIS Windows 11 Enterprise Benchmark v1.0.0 returned a score of 33% (129 passed, 259 failed, 7 not applicable), reflecting a default Windows 11 installation without enterprise hardening. This baseline will be used to measure improvement as specific security configurations are remediated.

## Windows Attack Scenarios and Detection Outcomes

### Scenario 1 – RDP Brute Force with Hydra (Detected)

- **Tool and command**: Hydra from Kali, targeting the Windows 11 endpoint's RDP service (TCP/3389) with a dictionary‑based password guessing attack.
- **Setup**: RDP was temporarily enabled on the Windows endpoint with a scoped inbound firewall rule (`RDP-Lab-Kali-Only`) restricting access to the Kali attacker IP only. The target account (`user`) was added to the Remote Desktop Users group for the duration of the test.
- **NLA discovery**: The initial attack attempt with Network Level Authentication (NLA) enabled produced no Windows Security events at all. Hydra's experimental RDP module cannot complete CredSSP/NLA negotiation, so authentication attempts never reached the Windows Security subsystem — making the attack invisible to the SIEM. This is a significant real‑world defense: NLA stops brute‑force tools that cannot speak current authentication protocols, and the absence of log entries means such blocked attempts require network‑level detection (IDS/IPS, firewall connection logs) rather than endpoint telemetry.
- **Test execution**: After temporarily disabling NLA to allow classic RDP authentication, two Hydra runs were performed:
  1. A 5‑password wordlist where the correct password appeared at position 3 — Hydra successfully discovered the credential.
  2. A 14‑password wordlist with the correct password placed near the bottom to maximize failed attempts and trigger correlation rules.

**Detection chain observed in Wazuh**:

| Time | Rule ID | Rule Description | Level | Event ID |
|------|---------|-----------------|-------|----------|
| 11:20:36–38 | 60122 | Logon failure – Unknown user or bad password | 5 | 4625 |
| 11:20:40 | 92657 | Successful Remote Logon Detected – NTLM auth, possible pass‑the‑hash – Possible RDP connection | 6 | 4624 |
| 11:21:49–59 | 60122 | Logon failure – Unknown user or bad password (×5) | 5 | 4625 |
| 11:21:59 | **60204** | **Multiple Windows logon failures** | **10** | 4625 |
| 11:22:01–07 | 60122 | Logon failure – Unknown user or bad password (×4) | 5 | 4625 |
| 11:22:07 | **60115** | **User account locked out (multiple login errors)** | **9** | 4740 |

**Key observations**:

1. **Brute‑force escalation (Rule 60204, Level 10)**: After a threshold of repeated 4625 events from the same source, Wazuh correlated them into a high‑severity "Multiple Windows logon failures" alert — the Windows equivalent of the SSH brute‑force Rule 5763 observed in the Linux scenarios.
2. **Account lockout (Rule 60115, Level 9, Event 4740)**: Windows automatically locked the account after exceeding the failed‑attempt threshold, stopping the attack at the OS level. Hydra then entered a RE‑ATTEMPT loop and eventually errored out with "all children were disabled due too many connection errors." This demonstrates a layered defense: the SIEM detects the pattern while the OS simultaneously mitigates it.
3. **Suspicious successful logon (Rule 92657, Level 6)**: The first Hydra run that found the correct password triggered a detection noting NTLM authentication over RDP with a recommendation to verify that the source host (kali) is authorized. This is the kind of alert a SOC analyst would investigate as potential lateral movement or credential compromise.
4. **Logon Type 3 (Network)**: All RDP authentication events appeared as Logon Type 3 rather than the interactive Type 10 typically seen with full RDP sessions, because Hydra performs network‑level credential checks without establishing a full desktop session.

**Post‑simulation cleanup**: After testing, NLA was re‑enabled, the user account was removed from Remote Desktop Users, RDP was disabled (`fDenyTSConnections = 1`), and the scoped firewall rule was removed — restoring the endpoint to its pre‑test security posture.

### Scenario 2 – Suspicious PowerShell Execution (Detected)

- **Objective**: Simulate post‑exploitation behavior by running commands commonly used by attackers after gaining initial access — Base64‑encoded PowerShell execution, system discovery commands, and a download cradle.
- **Technique mapping**: MITRE ATT&CK T1059.001 (Command and Scripting Interpreter: PowerShell), T1087 (Account Discovery), T1082 (System Information Discovery).

Three categories of suspicious activity were executed from an elevated PowerShell session on the Windows endpoint:

1. **Base64‑encoded command**: `powershell.exe -EncodedCommand dwBoAG8AYQBtAGkA` — this decodes to `whoami`, a harmless command, but the technique of encoding commands in Base64 is the most common obfuscation method in real‑world post‑exploitation.
2. **Reconnaissance chain**: `whoami /all`, `net user`, `net localgroup administrators`, `systeminfo`, `ipconfig /all` — standard enumeration commands an attacker runs after gaining a foothold.
3. **Download cradle**: `Invoke-WebRequest` targeting the EICAR antivirus test file URL, simulating a second‑stage payload download.

**Detection chain observed in Wazuh**:

| Time | Rule ID | Rule Description | Level |
|------|---------|-----------------|-------|
| 12:07:14 | **92057** | **Powershell.exe spawned a powershell process which executed a base64 encoded command** | **12** |
| 12:09:53 | 92052 | Windows command prompt started by an abnormal process | 4 |
| 12:09:53 | 92032 | Suspicious Windows cmd shell execution | 3 |
| 12:17:03 | 92031 | Discovery activity executed (×2) | 3 |
| 12:17:03 | 92033 | Discovery activity spawned via PowerShell execution (×2) | 3 |

**Key observations**:

1. **Encoded command detection (Rule 92057, Level 12)**: Wazuh's highest‑value detection from this scenario. Sysmon Event 1 recorded `powershell.exe` spawning a child `powershell.exe` with the `-EncodedCommand` parameter, and Wazuh's rule engine flagged this as a high‑severity event. In a real incident, the SOC analyst's first step would be decoding the Base64 payload to determine what was executed.
2. **Discovery clustering**: The reconnaissance commands individually triggered low‑severity alerts (Level 3), but their temporal clustering on a single host — especially following an encoded PowerShell execution — would constitute a high‑confidence indicator of post‑exploitation activity when analyzed as a group.
3. **Process lineage via Sysmon**: Sysmon Event 1 captured the full parent–child process tree for every command, enabling an analyst to trace the execution chain back to the originating process. This is critical for determining the initial access vector (e.g., distinguishing user‑initiated activity from a malicious document macro spawning PowerShell).

### Scenario 3 – Test Payload Drop and Endpoint Protection Visibility (Detected)

- **Objective**: Simulate an attacker dropping tooling and malware onto the endpoint, and validate that both Sysmon file creation monitoring and Windows Defender event forwarding detect the activity.
- **Technique mapping**: MITRE ATT&CK T1105 (Ingress Tool Transfer), T1036 (Masquerading).
- **Prerequisite**: The Windows Defender event channel (`Microsoft-Windows-Windows Defender/Operational`) was added to the Wazuh agent's `ossec.conf` to close a previously identified visibility gap where Defender detections were not forwarded to the SIEM.

Four test files were created via PowerShell's `Set-Content` cmdlet in locations commonly used by attackers:

1. `%TEMP%\update-helper.exe` — a benign text file with an `.exe` extension, simulating a masqueraded executable drop.
2. `%USERPROFILE%\Downloads\cleanup.bat` — a batch script containing reconnaissance commands (`whoami`, `net user`, `ipconfig /all`).
3. `%TEMP%\invoke-scan.ps1` — a PowerShell script simulating a post‑exploitation scanner.
4. `%TEMP%\totally-legit.exe` — containing the EICAR standard antivirus test string, designed to trigger Windows Defender.

**Detection chain observed in Wazuh**:

| Time | Rule ID | Rule Description | Level | Source |
|------|---------|-----------------|-------|--------|
| 18:47:36 | **92213** | **Executable file dropped in folder commonly used by malware (×2)** | **15** | Sysmon Event 11 |
| 18:47:36 | **62123** | **Windows Defender: Antimalware platform detected potentially unwanted software** | **12** | Defender Event 1116 |

**Key observations**:

1. **Maximum severity file drop alerts (Rule 92213, Level 15)**: Sysmon Event 11 detected `.exe` files being created in the Temp directory, and Wazuh classified these at the highest severity level. The process responsible was recorded as `powershell.exe`, which in a real attack would indicate PowerShell‑based payload staging.
2. **Defender integration validated (Rule 62123, Level 12)**: The EICAR test file triggered Windows Defender's Real‑Time Protection, which classified it as `Virus:DOS/EICAR_Test_File` with severity "Severe." Critically, this detection was now visible in the Wazuh dashboard because the Defender event channel had been added to `ossec.conf`. The alert includes rich context: the detection source (Real‑Time Protection), the responsible process (`powershell.exe`), the exact file path, and the Defender engine version — all information a SOC analyst needs for triage.
3. **Visibility gap closed**: In an earlier test, the same EICAR file triggered a Defender notification on the endpoint but generated no SIEM alert because the Defender channel was not configured. After adding the channel to `ossec.conf`, the detection now flows through the full pipeline: Defender detects → logs to its event channel → Wazuh agent ships the event → manager classifies as Rule 62123 → indexed and visible in the dashboard. This demonstrates the operational importance of forwarding all endpoint protection logs to the SIEM.
4. **Layered detection**: The same malicious file drop was caught by two independent detection layers — Sysmon (file creation in a suspicious location) and Defender (content‑based malware signature match) — illustrating defense in depth at the endpoint level.

**Post‑simulation cleanup**: All test files were removed. Defender had already quarantined the EICAR test file automatically.

## Alert Tuning — Custom Rule Overrides

### Rationale

After completing the attack simulations and initial false positive investigations, the Wazuh dashboard contained a significant volume of recurring false positive alerts. Left unaddressed, this noise leads to **alert fatigue** — the primary reason real breaches go undetected in production SOC environments. The goal of alert tuning is to reduce noise without reducing visibility: suppress only the specific patterns that have been investigated and confirmed benign, while preserving all rules that could indicate real threats.

### Tuning Methodology

Wazuh supports three approaches to alert suppression:

1. **Custom rule override (Method 1)**: Create a new rule in `local_rules.xml` that matches the specific false positive pattern and sets Level 0 (suppressed). The original rule remains active for all other events.
2. **Rule exclusion (Method 2)**: Add `<rule_exclude>` in `ossec.conf` to disable a rule ID entirely. This is dangerous because it suppresses the rule for all events, including potential real attacks.
3. **CDB lists / whitelists (Method 3)**: Reference a list of known‑good values (processes, IPs, hashes) within rules. Most flexible, used in enterprise environments.

Method 1 was chosen for this lab because it offers **surgical precision**: each suppression targets only the exact combination of process, path, and parent process that was confirmed benign during investigation, while leaving the underlying detection rule fully active for all other patterns.

### Rules Implemented

Four custom rules were added to `/var/ossec/etc/rules/local_rules.xml` on the Wazuh manager, using rule IDs 100002–100005:

| Custom Rule | Suppresses | Original Level | Match Condition | Investigation Reference |
|-------------|-----------|----------------|-----------------|------------------------|
| 100002 | Rule 92031 (Discovery activity) | 3 | Parent process is `wazuh-agent` or `ossec-agent` | SCA module running CIS benchmark checks |
| 100003 | Rule 92039 (net.exe discovery) | 3 | Parent process is `wazuh-agent` or `ossec-agent` | SCA module running `net.exe accounts` |
| 100004 | Rule 92213 (Executable in malware folder) | 15 | Process is `brave.exe` AND path contains `BraveUpdate` or `BraveSoftware` | [SOC-2026-0328-001](investigations/SOC-2026-0328-001.md) |
| 100005 | Rule 92200 (Scripting file in Temp) | 6 | Process is `svchost.exe` AND filename contains `pool_tags_summary` | [SOC-2026-0328-002](investigations/SOC-2026-0328-002.md) |

All rules use PCRE2 regular expressions with case‑insensitive matching (`(?i)`) and precise anchoring (e.g., `\\brave\.exe$`) to prevent over‑broad suppression. Each rule requires multiple field matches (AND logic), ensuring that only the exact investigated false positive pattern is suppressed.

### Precision Tuning Example

Rule 100004 demonstrates the precision approach:

```xml
<rule id="100004" level="0">
  <if_sid>92213</if_sid>
  <field name="win.eventdata.image" type="pcre2">(?i)\\brave\.exe$</field>
  <field name="win.eventdata.targetFilename" type="pcre2">(?i)BraveUpdate|BraveSoftware</field>
  <description>Suppressed: Brave browser component updater file drop (92213)</description>
</rule>
```

This suppresses ONLY when `brave.exe` drops files into Brave‑specific update directories. If any other process drops an executable in the same Temp folder, Rule 92213 still fires at Level 15. If `brave.exe` creates files in an unexpected location, it is also not suppressed. The two‑condition AND logic narrows the suppression window to the minimum necessary.

### Validation

After deploying the rules and restarting the Wazuh manager, `wazuh-analysisd -t` confirmed valid rule syntax and the manager restarted successfully. Subsequent SCA evaluation cycles on the Windows agent no longer generated spurious discovery alerts in the dashboard, while genuine discovery commands (e.g., from the PowerShell attack simulation) continued to trigger alerts as expected.

## Future Work and Next Steps

This lab is deliberately designed as the foundation for additional blue‑team automation and analysis projects.

Planned next steps include:

- **Custom rules and dashboards**: Build focused dashboards for cross‑platform authentication monitoring, process execution anomalies, and Sysmon‑based network connection visibility.
- **Python log and threat‑intel automation (Project 2)**: Develop a Python tool that tails Wazuh `alerts.json`, enriches suspicious IPs and file hashes with VirusTotal/AbuseIPDB, and sends formatted alerts to a Discord channel, implementing a simple SOAR workflow.
- **Network forensics and incident reports (Project 3)**: Capture packet traces for attack simulations and produce incident reports with Wireshark/Scapy analysis, mapped to Wazuh alerts and MITRE ATT&CK techniques.

Together, these projects will form a cohesive SOC portfolio demonstrating not only tool usage, but also an understanding of detection mechanics, automation, and documented incident response workflows.

---
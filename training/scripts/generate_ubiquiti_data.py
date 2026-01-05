#!/usr/bin/env python3
"""Generate Ubiquiti UniFi/Protect training data."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

UNIFI_NETWORK = [
    ("How do I adopt a new UniFi device?", "In the UniFi Network Controller, go to Devices. New devices appear as 'Pending Adoption'. Click the device and select 'Adopt'. For factory reset devices, they auto-discover via L2 adoption. For L3 adoption across VLANs, set the inform URL: `set-inform http://controller-ip:8080/inform` via SSH."),
    ("How do I set up a VLAN in UniFi?", "In UniFi Network: Settings > Networks > Create New. Set VLAN ID (2-4094), configure DHCP settings, and assign to WiFi networks or switch ports. For tagged ports, edit the switch port profile to include the VLAN as tagged. Guest networks auto-isolate from other VLANs."),
    ("How do I create firewall rules in UniFi?", "Settings > Firewall & Security > Create New Rule. Choose type (LAN In/Out, WAN In/Out, Guest), set action (Allow/Drop/Reject), define source/destination networks or IPs, specify ports/protocols. Rules process top-to-bottom; drag to reorder priority."),
    ("How do I set up a site-to-site VPN in UniFi?", "Settings > VPN > Site-to-Site VPN > Create. Choose Auto IPsec VPN for UniFi-to-UniFi (easiest), or Manual IPsec for third-party. Configure remote gateway IP, shared secret, local/remote networks. Enable 'Auto' for dynamic routing or specify static routes."),
    ("How do I configure UniFi switch port profiles?", "Settings > Profiles > Switch Ports. Create profiles for different use cases: All (all VLANs tagged), Native VLAN only, or custom with specific tagged/native VLANs. Apply to ports via Devices > Switch > Ports > Select port > Profile."),
    ("How do I enable RADIUS authentication in UniFi?", "Settings > Profiles > RADIUS. Add RADIUS server IP, port (1812), shared secret. For WiFi: create network with WPA Enterprise, select RADIUS profile. For wired 802.1X: enable on switch port profile. UniFi can also act as RADIUS server for hotspot."),
    ("How do I set up traffic management and QoS in UniFi?", "Settings > Traffic Management. Enable Smart Queues for bufferbloat control. Set bandwidth limits per client/network. Create Traffic Rules to prioritize (gaming, video) or limit (downloads) by app category, IP, or protocol. DPI must be enabled."),
    ("How do I configure UniFi's Intrusion Prevention System?", "Settings > Firewall & Security > Intrusion Prevention. Enable IPS/IDS, select sensitivity (Low/Medium/High/Max), choose categories to block (malware, exploits, etc.). High sensitivity impacts throughput on smaller gateways. Review Threat Management for blocked events."),
    ("How do I set up a guest hotspot portal in UniFi?", "Settings > WiFi > Create Guest Network. Enable Guest Portal, choose authentication (password, voucher, social login, RADIUS). Customize landing page, set session/bandwidth limits. For vouchers: Hotspot Manager > Create vouchers with usage limits."),
    ("How do I back up UniFi controller settings?", "Settings > System > Backups. Enable Auto Backup (daily/weekly/monthly). Download manual backup via 'Download Backup'. Restore via 'Restore from Backup' file upload. For Cloud Key/Dream Machine, backups store locally and optionally to UniFi cloud."),
    ("How do I update UniFi device firmware?", "Devices > Select device > Settings > Manage > Upgrade. For bulk: Settings > System > Updates > enable Auto Update or select update channel (Release/Release Candidate/Beta). Schedule updates for maintenance windows. Dream Machine updates via Settings > Updates."),
    ("How do I troubleshoot UniFi device connectivity?", "Check: 1) Device LED status (white=connected, blue=isolated), 2) Controller > Devices for status/uptime, 3) SSH to device: `info` shows adoption status, `mca-cli-op info` for detailed state. For network issues: check cables, PoE budget, VLAN tagging, and controller connectivity."),
    ("How do I configure port forwarding in UniFi?", "Settings > Firewall & Security > Port Forwarding > Create. Set name, incoming port, forward IP, forward port, protocol (TCP/UDP/Both). For ranges: use 'Port Range'. Enable 'Log' to track usage. Ensure destination firewall allows traffic."),
    ("How do I set up WireGuard VPN in UniFi?", "Settings > VPN > VPN Server > WireGuard. Enable server, set listen port, generate keys. Add clients with public key, assign IP from server range. Download client config or scan QR. Enable 'Allow Internet' for full tunnel or specify routes for split tunnel."),
    ("How do I monitor UniFi network statistics?", "Dashboard shows real-time throughput, client count, ISP usage. Statistics > select timeframe for historical data. Enable DPI (Settings > Traffic Management) for per-app breakdown. Export via Insights > Traffic or use UniFi API for automation."),
]

UNIFI_PROTECT = [
    ("How do I add cameras to UniFi Protect?", "Cameras auto-discover when connected to UniFi network. In Protect: Devices > Add Device. For cameras on different VLANs, ensure Protect controller IP is reachable and port 7442/TCP is open. Factory reset camera if previously adopted elsewhere."),
    ("How do I configure motion detection in Protect?", "Select camera > Settings > Recording > Motion Events. Adjust sensitivity (1-100), set motion zones by drawing on preview. Configure 'Smart Detection' for person/vehicle/package detection on supported cameras (G4 line). Set recording mode: Always/Motion Only/Schedule."),
    ("How do I set up recording schedules in Protect?", "Camera > Settings > Recording. Choose Always, Detections Only, or create Schedule with time blocks. Set retention per camera or globally (Settings > Recording). Storage depends on camera count, resolution, and bitrate. Protect calculates estimated days."),
    ("How do I view and export Protect recordings?", "Timeline: scrub to find event. Click event thumbnail or drag on timeline. Export: select clip on timeline, click 'Export'. Choose quality (high/low), timeframe. Download or share via UniFi cloud link. Batch export via Playback > Download icon."),
    ("How do I configure Protect smart detections?", "Camera > Settings > Smart Detections. Enable Person, Vehicle, Package, Animal (varies by model). Adjust sensitivity per type. Create alerts for specific detection types only. Smart detections require AI-capable cameras and processing on Protect controller."),
    ("How do I set up Protect notifications?", "Settings > Notifications. Enable push notifications per camera or globally. Configure motion/smart detection triggers, set schedule, enable 'Rich Notifications' for thumbnails. Per-camera: Camera > Settings > Notifications for granular control."),
    ("How do I share Protect access with others?", "Users > Invite User. Assign role: Full Admin, Local Access Only (no cloud), or Custom (per-camera). Share live view links: Timeline > Share icon > generate time-limited link. Cloud account required for remote access unless using local-only."),
    ("How do I configure Protect privacy zones?", "Camera > Settings > Privacy Zone. Draw area on preview to permanently black out. Use for neighbor's property, windows, etc. Zones apply to live view and recordings. Multiple zones per camera supported."),
    ("How do I troubleshoot Protect camera issues?", "Check: 1) Camera LED (solid=recording, slow blink=no controller), 2) Protect > Devices for status, 3) Network connectivity and PoE delivery. Common fixes: restart camera, check firmware, verify storage space, ensure correct Protect controller IP."),
    ("How do I set up Protect chimes and doorbell?", "Pair UniFi Chime via Bluetooth in Protect app. G4 Doorbell: add like camera, wire to existing doorbell transformer (16-24V AC). Configure ring detection, motion zones, quick response messages. Chime settings per doorbell under Chime device."),
]

UNIFI_API = [
    ("How do I authenticate to the UniFi Controller API?", """Use cookie-based auth:
```python
import requests
session = requests.Session()
login = session.post('https://controller:8443/api/login',
    json={'username': 'admin', 'password': 'password'},
    verify=False)
# Session cookie now set for subsequent requests
sites = session.get('https://controller:8443/api/self/sites')
```
For local API key (UDM/Cloud Key): Settings > System > API > Create API Key."""),
    ("How do I get all UniFi clients via API?", """```python
# After authentication
clients = session.get('https://controller:8443/api/s/default/stat/sta')
for client in clients.json()['data']:
    print(f"{client['hostname']}: {client['ip']} - {client['mac']}")
```
Use `/stat/alluser` for historical clients, `/stat/user/{mac}` for specific client."""),
    ("How do I block/unblock a client via UniFi API?", """```python
# Block client
session.post('https://controller:8443/api/s/default/cmd/stamgr',
    json={'cmd': 'block-sta', 'mac': '00:11:22:33:44:55'})

# Unblock client
session.post('https://controller:8443/api/s/default/cmd/stamgr',
    json={'cmd': 'unblock-sta', 'mac': '00:11:22:33:44:55'})
```"""),
    ("How do I get UniFi device statistics via API?", """```python
# All devices
devices = session.get('https://controller:8443/api/s/default/stat/device')

# Specific device by MAC
device = session.get('https://controller:8443/api/s/default/stat/device/aabbccddeeff')

# Response includes: uptime, load, temperature, ports, tx/rx bytes
```"""),
    ("How do I provision a new network via UniFi API?", """```python
network = {
    'name': 'IoT_Network',
    'purpose': 'corporate',
    'vlan': 30,
    'subnet': '192.168.30.1/24',
    'dhcpd_enabled': True,
    'dhcpd_start': '192.168.30.100',
    'dhcpd_stop': '192.168.30.254'
}
session.post('https://controller:8443/api/s/default/rest/networkconf', json=network)
```"""),
    ("How do I create firewall rules via UniFi API?", """```python
rule = {
    'name': 'Block_IoT_to_LAN',
    'enabled': True,
    'ruleset': 'LAN_IN',
    'rule_index': 2000,
    'action': 'drop',
    'src_networkconf_type': 'NETv4',
    'dst_networkconf_type': 'NETv4',
    'src_network_id': 'iot_network_id',
    'dst_network_id': 'default_network_id'
}
session.post('https://controller:8443/api/s/default/rest/firewallrule', json=rule)
```"""),
    ("How do I get Protect camera snapshots via API?", """```python
# Get cameras
cameras = session.get('https://protect:7443/proxy/protect/api/cameras')

# Get snapshot
camera_id = cameras.json()[0]['id']
snapshot = session.get(f'https://protect:7443/proxy/protect/api/cameras/{camera_id}/snapshot',
    params={'force': 'true'})
with open('snapshot.jpg', 'wb') as f:
    f.write(snapshot.content)
```"""),
    ("How do I trigger recordings via Protect API?", """```python
import time
# Start recording
session.post(f'https://protect:7443/proxy/protect/api/cameras/{camera_id}/recording/start')

time.sleep(30)  # Record for 30 seconds

# Stop recording
session.post(f'https://protect:7443/proxy/protect/api/cameras/{camera_id}/recording/stop')
```"""),
    ("How do I get UniFi Protect events via API?", """```python
# Get motion events (last 24h)
events = session.get('https://protect:7443/proxy/protect/api/events',
    params={
        'start': int(time.time() - 86400) * 1000,
        'end': int(time.time()) * 1000,
        'types': ['motion', 'smartDetectZone']
    })
for event in events.json():
    print(f"{event['type']}: {event['camera']} at {event['start']}")
```"""),
    ("How do I automate UniFi with Python?", """Use pyunifi or build custom:
```python
from pyunifi.controller import Controller
c = Controller('192.168.1.1', 'admin', 'password', ssl_verify=False)

# Get all clients
clients = c.get_clients()

# Block a client
c.block_client('00:11:22:33:44:55')

# Get AP stats
aps = c.get_aps()
for ap in aps:
    print(f"{ap['name']}: {ap.get('num_sta', 0)} clients")
```"""),
]

UNIFI_ADVANCED = [
    ("How do I set up multi-site management in UniFi?", "Network app supports multiple sites under one controller. Settings > System > Sites > Add Site. Each site has isolated configuration. Use cloud controller or host-based controller for remote sites. Site-to-site VPN connects networks; admin can switch between sites in UI."),
    ("How do I integrate UniFi with Home Assistant?", "Install UniFi integration via HACS or built-in. Configure with controller IP, username, password. Exposes: device trackers (clients), switches (PoE ports, block clients), sensors (bandwidth, uptime). Protect integration adds camera entities and event triggers."),
    ("How do I configure UniFi Traffic Identification (DPI)?", "Settings > Traffic Management > Enable Deep Packet Inspection. DPI identifies app-level traffic (Netflix, YouTube, gaming). View in Statistics > App breakdown. Create Traffic Rules based on DPI categories. Note: DPI impacts gateway performance on smaller devices."),
    ("How do I set up OSPF/BGP routing in UniFi?", "Advanced routing available on UDM-Pro/UXG. Settings > Routing > Dynamic Routing. Configure OSPF: area ID, networks to advertise, neighbor IPs. BGP: ASN, neighbor configuration. Use for multi-gateway failover or datacenter integration."),
    ("How do I configure UniFi for high-density WiFi?", "Use UniFi 6 Enterprise or U6 Pro. Settings per AP: lower TX power (medium), set min RSSI (-75dBm), enable band steering (5GHz prefer), disable slower rates (6/9/12Mbps). Use non-overlapping channels (1,6,11 for 2.4GHz). Enable BSS Coloring for WiFi 6."),
    ("How do I automate Protect with webhooks?", """Settings > System > Webhooks. Add endpoint URL. Protect sends JSON on events:
```json
{"type": "smartDetectZone", "camera": "Front Door", "smartDetectTypes": ["person"], "timestamp": 1234567890}
```
Use for home automation, logging, or alerting systems."""),
    ("How do I set up UniFi Access for door control?", "UniFi Access manages door locks and access control. Install Access hub, connect door locks. Configure: user credentials (PIN, NFC, mobile), access schedules, door groups. Integration: Protect shows door events, Network manages Access network. API available for custom integration."),
    ("How do I configure UniFi Talk for VoIP?", "UniFi Talk is the VoIP phone system. Requires Cloud Key Gen2+ or UDM. Add Talk devices, configure extensions, set up auto-attendant. Features: voicemail, call routing, conference calling. Integration: Protect shows caller on screen, Access unlocks on intercom."),
    ("How do I monitor UniFi with SNMP?", "Settings > System > SNMP. Enable SNMPv1/v2c or SNMPv3. Configure community string or SNMPv3 credentials. Monitor: device health, client counts, bandwidth, CPU/memory. MIBs available from Ubiquiti. Integration: Nagios, Zabbix, LibreNMS, PRTG."),
    ("How do I use UniFi Network Application in Docker?", """Run official container:
```bash
docker run -d --name unifi \\
  -p 8443:8443 -p 3478:3478/udp -p 10001:10001/udp \\
  -p 8080:8080 -p 8843:8843 -p 6789:6789 \\
  -v unifi_data:/unifi \\
  jacobalberty/unifi:latest
```
Access at https://localhost:8443. Persist data in volume. For L3 adoption, set inform URL to Docker host IP."""),
]

UNIFI_TROUBLESHOOTING = [
    ("Why won't my UniFi device adopt?", "Common causes: 1) Device on different VLAN - enable L2 adoption or set inform URL, 2) Device previously adopted - factory reset (hold reset 10+ seconds), 3) Firewall blocking ports 8080/8443, 4) SSH to device and run 'set-inform http://controller:8080/inform'. Check controller can reach device on management VLAN."),
    ("How do I fix slow WiFi speeds on UniFi?", "Check: 1) Channel utilization (change to less congested channel), 2) TX power (too high causes interference), 3) Client distance (min RSSI setting), 4) Band steering (force 5GHz capable devices), 5) Legacy rates (disable 1-12Mbps), 6) Interference from neighbors or microwaves. Run WiFiman app to diagnose."),
    ("Why is my UniFi gateway running hot/slow?", "Check: 1) IDS/IPS enabled (high CPU impact), 2) DPI enabled (uses resources), 3) Smart Queues (impacts throughput), 4) Number of firewall rules. Solutions: disable unused features, upgrade hardware (UDM-Pro for higher throughput). Monitor via Settings > System > Application."),
    ("How do I recover a UniFi device with SSH?", "SSH to device (ubnt/ubnt default, or your controller password). Commands: 'info' shows state, 'set-default' factory resets, 'set-inform http://ip:8080/inform' forces adoption. For bricked device: TFTP recovery with firmware image. Check device-specific recovery procedures."),
    ("How do I migrate UniFi controller to new hardware?", "Backup: Settings > System > Backups > Download. On new hardware: install UniFi Network Application, run through setup wizard, restore from backup file. Site data, device adoption keys transfer. Devices may need to readopt - SSH and set-inform to new controller IP. For Dream Machine: cloud backup/restore."),
]

def generate_examples():
    examples = []
    
    # UniFi Network
    for q, a in UNIFI_NETWORK:
        examples.append({
            "system": "You are AJ, an expert in Ubiquiti UniFi network management, configuration, and troubleshooting.",
            "instruction": q,
            "response": a
        })
    
    # UniFi Protect
    for q, a in UNIFI_PROTECT:
        examples.append({
            "system": "You are AJ, an expert in Ubiquiti UniFi Protect camera systems, NVR management, and video surveillance.",
            "instruction": q,
            "response": a
        })
    
    # API Integration
    for q, a in UNIFI_API:
        examples.append({
            "system": "You are AJ, an expert in Ubiquiti UniFi API integration, automation, and programmatic network management.",
            "instruction": q,
            "response": a
        })
    
    # Advanced Topics
    for q, a in UNIFI_ADVANCED:
        examples.append({
            "system": "You are AJ, an expert in Ubiquiti UniFi advanced configuration, enterprise deployments, and integrations.",
            "instruction": q,
            "response": a
        })
    
    # Troubleshooting
    for q, a in UNIFI_TROUBLESHOOTING:
        examples.append({
            "system": "You are AJ, an expert in Ubiquiti UniFi troubleshooting and problem resolution.",
            "instruction": q,
            "response": a
        })
    
    return examples

def main():
    examples = generate_examples()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DATA_DIR / "ubiquiti_unifi.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    print(f"  [OK] Saved {len(examples)} examples to {output_file}")

if __name__ == "__main__":
    main()

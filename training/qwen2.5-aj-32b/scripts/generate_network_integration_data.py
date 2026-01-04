#!/usr/bin/env python3
"""
Firewalla + UniFi Integration Training Data Generator

Generates training examples for the cross-domain relationship between
Firewalla (network security/routing) and UniFi (WiFi/switching) systems.

These systems complement each other in a home/SMB network setup where:
- Firewalla Gold Plus serves as the router/firewall
- UniFi provides WiFi access points, switches, and optional cameras
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert in network integration between Firewalla Gold Plus and Ubiquiti UniFi systems.
You help users design, configure, and troubleshoot networks that use Firewalla as the router/firewall
with UniFi access points, switches, and optional Protect cameras.

Your expertise includes:
- Network topology design (Firewalla as router, UniFi as access layer)
- VLAN coordination between Firewalla and UniFi
- Traffic flow and monitoring across both platforms
- VPN integration with UniFi-connected clients
- Troubleshooting cross-system connectivity issues"""

# =============================================================================
# ARCHITECTURE & DESIGN
# =============================================================================

ARCHITECTURE_DESIGN = [
    {
        "question": "How should I set up Firewalla Gold Plus with UniFi access points?",
        "answer": """Optimal architecture with Firewalla as router and UniFi APs:

**Physical Connections:**
1. ISP modem → Firewalla Port 4 (WAN)
2. Firewalla Port 1 → UniFi Switch (or direct to AP if single AP)
3. UniFi Switch → UniFi APs via PoE

**Configuration Steps:**
1. **Firewalla**: Set to Router Mode, configure WAN (DHCP/PPPoE/static), set LAN subnet (e.g., 192.168.1.0/24)
2. **UniFi Controller**: Can run on Cloud Key, Dream Machine, or Docker
3. **UniFi APs**: Adopt to controller, create WiFi networks

**Key Points:**
- Firewalla handles routing, firewall, DHCP, and security monitoring
- UniFi handles Layer 2 switching and WiFi
- UniFi Controller can use standalone mode (no internet) or cloud
- All traffic flows through Firewalla for full visibility

**For VLANs**: Configure matching VLANs on both Firewalla and UniFi Switch trunk ports."""
    },
    {
        "question": "Should I use UniFi gateway or Firewalla Gold Plus as my router?",
        "answer": """Comparison for making the right choice:

**Choose Firewalla Gold Plus if you want:**
- Superior security monitoring and threat detection
- Intuitive mobile app for network management
- Per-device deep packet inspection and rules
- Ad blocking and parental controls built-in
- VPN server (WireGuard/OpenVPN) with easy setup
- Docker container support on the router itself
- Active community and frequent updates

**Choose UniFi Gateway (UDM/UXG) if you want:**
- Single vendor ecosystem integration
- UniFi's unified dashboard for all devices
- Tighter Protect integration (AI features)
- Enterprise features (BGP, OSPF)
- Multiple WAN failover built-in

**Best of Both Worlds:**
Use Firewalla Gold Plus as router + UniFi APs/switches for access layer.
This gives you Firewalla's security + UniFi's excellent WiFi.
Run UniFi Controller on separate hardware (RPi, Cloud Key, Docker)."""
    },
    {
        "question": "How do I design a VLAN setup with Firewalla and UniFi?",
        "answer": """Multi-VLAN architecture with Firewalla + UniFi:

**Network Segments:**
- VLAN 1 (untagged): Management (Firewalla: 192.168.1.0/24)
- VLAN 10: Main devices (192.168.10.0/24)
- VLAN 20: IoT devices (192.168.20.0/24)
- VLAN 30: Guest network (192.168.30.0/24)
- VLAN 40: Cameras/Protect (192.168.40.0/24)

**Firewalla Configuration:**
1. Network Manager → Create Network → VLAN
2. Set VLAN ID, IP range, DHCP settings for each
3. Configure inter-VLAN rules (block IoT→Main, allow Main→IoT)

**UniFi Switch Configuration:**
1. Trunk port to Firewalla: All VLANs tagged
2. Create port profiles: 'IoT Only' (VLAN 20 native), 'Cameras' (VLAN 40 native)
3. Apply profiles to switch ports

**UniFi WiFi Networks:**
1. Main WiFi → VLAN 10
2. IoT WiFi → VLAN 20 (hidden SSID recommended)
3. Guest WiFi → VLAN 30 (enable guest policies)

**Critical**: Firewalla is DHCP server for ALL VLANs. Don't enable DHCP in UniFi."""
    },
    {
        "question": "Where should I run the UniFi Network Controller with Firewalla?",
        "answer": """Options for running UniFi Controller alongside Firewalla:

**Option 1: Docker on Firewalla (Gold Plus only)**
```bash
# SSH into Firewalla
ssh pi@firewalla-ip

# Run UniFi Controller
docker run -d --name unifi-controller \\
  --restart unless-stopped \\
  -p 8443:8443 -p 3478:3478/udp \\
  -p 8080:8080 -p 10001:10001/udp \\
  -v /data/unifi:/unifi \\
  jacobalberty/unifi:latest
```
Pros: Single device, no extra hardware
Cons: Resource usage on Firewalla

**Option 2: Raspberry Pi or NUC**
Dedicated always-on device. Install UniFi on Ubuntu/Debian.
Connect to Firewalla LAN. Access at https://pi-ip:8443.

**Option 3: Cloud Key or Dream Machine in AP mode**
Cloud Key Gen2: Just a controller, connect to switch.
UDM in AP mode: Expensive but has built-in controller.

**Option 4: Docker on NAS**
Synology/QNAP container. Good if you already have a NAS.

**Recommendation**: Docker on Firewalla for simplicity, or Raspberry Pi for separation of concerns."""
    },
]

# =============================================================================
# VLAN COORDINATION
# =============================================================================

VLAN_COORDINATION = [
    {
        "question": "How do I configure VLANs to pass correctly between Firewalla and UniFi Switch?",
        "answer": """VLAN trunk configuration for Firewalla ↔ UniFi Switch:

**Firewalla Side:**
1. Connect to UniFi switch via any LAN port (Port 1 recommended)
2. Network Manager → Create VLANs (e.g., 10, 20, 30)
3. The LAN port auto-trunks all VLANs

**UniFi Switch Side:**
1. Settings → Profiles → Switch Ports → Create Profile
2. Name: 'Firewalla Trunk'
3. Native Network: Default (VLAN 1)
4. Tagged Networks: Select ALL VLANs (10, 20, 30, etc.)
5. Devices → Switch → Port connected to Firewalla → Apply profile

**Verification:**
- SSH to Firewalla: `ip a` shows sub-interfaces (eth0.10, eth0.20)
- UniFi: Check port shows multiple VLANs
- Test: Device on VLAN 10 gets DHCP from Firewalla's 192.168.10.x pool

**Troubleshooting:**
- No DHCP? Check VLAN ID matches on both sides
- No inter-VLAN? Check Firewalla rules allow the traffic
- Slow? Ensure trunk port is running at link speed (1G/2.5G)"""
    },
    {
        "question": "How do I assign UniFi WiFi networks to Firewalla VLANs?",
        "answer": """Mapping UniFi SSIDs to Firewalla VLANs:

**Prerequisites:**
- VLANs created on Firewalla (e.g., VLAN 10: 192.168.10.0/24)
- Switch trunk configured to pass VLANs to APs

**UniFi WiFi Configuration:**
1. Settings → WiFi → Create New
2. Name: 'Home WiFi'
3. Network: Create new network or select existing
4. If creating: Advanced → VLAN → Set to 10
5. Security: WPA3/WPA2, set password
6. Apply to APs

**Result:**
- Clients connect to 'Home WiFi'
- Traffic is tagged with VLAN 10
- Firewalla serves DHCP from 192.168.10.x pool
- Firewalla sees and monitors all traffic

**Multiple SSIDs Example:**
- 'Home WiFi' → VLAN 10 (main devices)
- 'Smart Home' → VLAN 20 (IoT, hidden SSID)
- 'Guest' → VLAN 30 (client isolation enabled)

**Note**: Each SSID adds overhead. Limit to 3-4 per AP for best performance."""
    },
    {
        "question": "Why aren't devices on my UniFi VLAN getting IP addresses from Firewalla?",
        "answer": """Troubleshooting DHCP across Firewalla + UniFi VLANs:

**Diagnostic Steps:**

1. **Verify VLAN Exists on Firewalla:**
   - Firewalla App → Network Manager → Check VLAN shows green
   - SSH: `ip a | grep eth0` should show eth0.XX for each VLAN

2. **Check UniFi Switch Trunk:**
   - Devices → Switch → Port to Firewalla → Profile must include the VLAN
   - Check both 'Native' and 'Tagged' network settings

3. **Verify UniFi Network VLAN ID:**
   - Settings → Networks → Check VLAN ID matches Firewalla exactly
   - VLAN ID typo is the #1 cause

4. **Check WiFi Network Assignment:**
   - Settings → WiFi → Network → Must map to correct VLAN network

5. **Test from Device:**
   - Connect to WiFi, check if DHCP discover is sent
   - On Firewalla: Network → Flows → Look for DHCP traffic

**Common Fixes:**
- Reboot UniFi AP after VLAN changes
- Disable/re-enable the network on Firewalla
- Check Firewalla DHCP range isn't exhausted
- Ensure no other DHCP server on that VLAN (disable on UniFi!)"""
    },
]

# =============================================================================
# MONITORING & SECURITY
# =============================================================================

MONITORING_SECURITY = [
    {
        "question": "How do I monitor all network traffic with Firewalla when using UniFi APs?",
        "answer": """Full traffic visibility with Firewalla + UniFi:

**Architecture (already optimal):**
When Firewalla is the router, ALL traffic flows through it:
- WiFi client → UniFi AP → Switch → Firewalla → Internet
- This gives Firewalla complete visibility

**What Firewalla Shows:**
- Per-device bandwidth and app usage
- DNS queries and destinations
- Blocked threats and intrusions
- Network flows (source, dest, port, bytes)
- Active device detection

**Enhanced Monitoring:**
1. Enable 'Active Protect' for threat detection
2. Enable 'Safe Search' to see DNS queries
3. Use 'Network Flows' for detailed traffic analysis
4. Set up 'Alerts' for unusual activity

**UniFi Complements with:**
- Client signal strength and roaming
- AP performance and channel utilization
- Per-SSID traffic breakdown (if DPI enabled)

**Note**: Running UniFi Gateway in AP mode would lose Firewalla visibility. Keep Firewalla as the sole router."""
    },
    {
        "question": "How do I set up firewall rules for UniFi Protect cameras with Firewalla?",
        "answer": """Securing UniFi Protect cameras via Firewalla rules:

**Recommended VLAN Setup:**
1. Create 'Cameras' VLAN in Firewalla (e.g., VLAN 40: 192.168.40.0/24)
2. Configure UniFi switch ports for cameras as VLAN 40 native
3. Protect NVR can be on management or camera VLAN

**Firewalla Rules for Camera VLAN:**

**Allow - NVR to Cameras:**
- Target: Camera VLAN
- Match: From NVR IP (or Management VLAN)
- Action: Allow
- This lets Protect controller manage cameras

**Block - Cameras to Internet:**
- Target: Camera VLAN
- Match: Destination Internet
- Action: Block
- Cameras don't need internet (optional: allow NTP, firmware updates)

**Block - Cameras to Other VLANs:**
- Target: Camera VLAN
- Match: Destination Local Networks (exclude NVR)
- Action: Block
- Prevents compromised camera from lateral movement

**Allow - Viewing Access:**
- Target: Main VLAN
- Match: Destination Protect NVR
- Action: Allow
- Users on main network can view cameras

**Result**: Cameras isolated but functional. Firewalla monitors any unusual camera traffic."""
    },
    {
        "question": "How do I coordinate Firewalla's IDS with UniFi's IDS/IPS?",
        "answer": """Coordinating intrusion detection between Firewalla and UniFi:

**If Using Firewalla as Router (Recommended):**
- Use Firewalla's Active Protect (IDS/IPS) exclusively
- Disable UniFi IDS/IPS (no gateway to run it)
- All threat detection happens at Firewalla

**Benefits of Firewalla IDS:**
- Per-device threat attribution
- Mobile alerts with one-tap blocking
- Community-powered threat intelligence
- Works with all traffic, not just gateway-passing

**If Somehow Running Both:**
- Duplication wastes resources
- Inconsistent blocking/alerting
- Recommend: Pick one (Firewalla is more user-friendly)

**Monitoring Split:**
- Firewalla: Security (threats, ads, malware, DNS)
- UniFi: WiFi health (interference, roaming, signal)

**Practical Approach:**
1. Enable Firewalla Active Protect (Medium or High)
2. Use Firewalla for all firewall rules
3. Use UniFi Network for switch/AP management only
4. If you have UniFi Protect, it handles camera-side threat detection"""
    },
]

# =============================================================================
# VPN INTEGRATION
# =============================================================================

VPN_INTEGRATION = [
    {
        "question": "How do I access my UniFi-connected devices via Firewalla VPN?",
        "answer": """Remote access to network via Firewalla VPN:

**VPN Server Setup (Firewalla):**
1. Firewalla App → VPN → VPN Server
2. Enable WireGuard (recommended) or OpenVPN
3. Generate client configuration
4. Install WireGuard app on phone/laptop

**Accessing UniFi Devices Remotely:**
Once VPN connected, you're on the local network:
- UniFi Controller: https://192.168.1.x:8443
- UniFi Protect: https://protect-ip (or via UniFi app)
- Any device on any VLAN (if VPN subnet has access)

**VLAN Access from VPN:**
By default, VPN clients can reach the primary LAN. For VLANs:
1. Firewalla → VPN → Server Settings
2. Add routes for each VLAN subnet
3. Or create allow rules: VPN Network → Destination VLANs

**Pro Tip:**
Set up UniFi Cloud Access for controller-only remote management.
Use Firewalla VPN for full network access including Protect live view.

**Comparison:**
- Firewalla VPN: Full LAN access, all devices, any service
- UniFi Cloud: Controller management only, requires Ubiquiti account"""
    },
    {
        "question": "How do I set up site-to-site VPN between two locations with Firewalla and UniFi?",
        "answer": """Site-to-site VPN with Firewalla (primary) and UniFi at remote:

**Scenario**: Home has Firewalla Gold Plus, remote office has UDM-Pro

**Option 1: Firewalla WireGuard ↔ UDM WireGuard**
This is the cleanest approach:
1. Firewalla: VPN → VPN Server → Enable WireGuard site-to-site
2. Generate peer configuration with remote subnet
3. UDM: Settings → VPN → WireGuard → Add peer with Firewalla config
4. Add static routes for remote subnets on both sides

**Option 2: Firewalla OpenVPN ↔ UDM IPsec**
Not directly compatible. Use WireGuard instead.

**Option 3: Both Sites Have Firewalla**
Use Firewalla's built-in Site-to-Site feature:
1. Firewalla → VPN → Site-to-Site VPN
2. Scan QR code on remote Firewalla
3. Automatic key exchange and routing

**Routing Considerations:**
- Each site sees the other's VLANs
- Firewalla rules can restrict cross-site access
- UniFi devices at remote site get IPs from remote Firewalla
- Traffic flows: Remote client → UDM → VPN → Firewalla → Local network"""
    },
]

# =============================================================================
# TROUBLESHOOTING
# =============================================================================

TROUBLESHOOTING = [
    {
        "question": "Devices connected to UniFi but not showing in Firewalla - why?",
        "answer": """Troubleshooting missing device visibility:

**Verify Architecture:**
Firewalla must be the router/DHCP server. If UniFi gateway is handling DHCP, Firewalla won't see devices.

**Check Points:**

1. **DHCP Source**: 
   - Connect device, check IP: should be from Firewalla's range (192.168.x.x per your config)
   - If IP is from UniFi range (192.168.1.1 default UDM), wrong router

2. **Network Mode**:
   - Firewalla must be in Router Mode, not Bridge or DHCP mode
   - UniFi gateway (if present) should be in Bridge/AP mode

3. **VLAN Routing**:
   - If device is on VLAN, check Firewalla has that VLAN configured
   - Ensure switch trunk includes the VLAN

4. **Traffic Path**:
   - Trace: Device → AP → Switch → Firewalla
   - Any break in this path loses visibility

**Fix:**
- If using UDM/UXG: Put in Bridge mode, let Firewalla route
- If devices get IPs but not showing: wait 30s, or force device to reconnect
- Check Firewalla → Network → Devices list for the MAC"""
    },
    {
        "question": "UniFi APs keep disconnecting when Firewalla is the router - how to fix?",
        "answer": """Troubleshooting UniFi AP stability with Firewalla:

**Common Causes & Fixes:**

1. **Controller Connectivity:**
   - AP must reach controller IP continuously
   - If controller on different VLAN, ensure routing works
   - Check Firewalla isn't blocking ports 8080, 8443, 3478

2. **Inform URL Issues:**
   - SSH to AP: `info` - check inform URL
   - Should be: http://controller-ip:8080/inform
   - Set manually: `set-inform http://192.168.1.x:8080/inform`

3. **DHCP/IP Issues:**
   - AP needs stable IP - use DHCP reservation in Firewalla
   - Firewalla → Network → Device → Reserve IP address

4. **Firmware Mismatch:**
   - Update all APs to same firmware version
   - Update controller to latest version

5. **PoE Budget:**
   - If using PoE switch, check power budget isn't exceeded
   - U6 Pro: 13W, U6 Enterprise: 25W

6. **Firewalla Rules:**
   - Ensure no rules blocking AP→Controller traffic
   - Check 'Blocked' in Firewalla for any AP traffic

**Diagnostic:**
```
# SSH to AP
ssh ubnt@ap-ip
info              # Shows adopt status
mca-cli-op info   # Detailed state
```"""
    },
    {
        "question": "Slow WiFi speeds on UniFi APs with Firewalla - how to diagnose?",
        "answer": """Diagnosing slow WiFi when using Firewalla + UniFi:

**Step 1: Isolate the Bottleneck**
- Wired device through Firewalla: Run speed test
- WiFi device to local server: Tests AP+Switch speed
- WiFi to internet: Full path test

**If Wired is Slow (Firewalla Issue):**
- Check Firewalla CPU: Dashboard → Status
- Disable Smart Queue temporarily (it limits speed to configured bandwidth)
- Check if Firewalla port is negotiating at 2.5G (Gold Plus)

**If WiFi to Local is Slow (UniFi Issue):**
- Check AP channel utilization
- Verify client is on 5GHz, not 2.4GHz
- Check for interference: Settings → WiFi → AI Optimization
- Test with different client closer to AP

**If Only Internet is Slow (Path Issue):**
- Check ISP connection speed at Firewalla WAN
- Verify Smart Queue bandwidth setting matches your ISP speed
- Check Firewalla IDS/IPS load (disable to test)

**Firewalla-Specific:**
- Smart Queue limits speed to configured 'Internet Speed'
- Update the speed setting: Firewalla → Smart Queue → Set bandwidth
- IDS/IPS can impact throughput on smaller Firewalla models

**UniFi-Specific:**
- Band steering: Force capable devices to 5GHz
- Minimum RSSI: Disconnect weak clients
- Channel width: 80MHz for 5GHz if no interference"""
    },
    {
        "question": "How do I troubleshoot inter-VLAN communication between Firewalla and UniFi?",
        "answer": """Debugging inter-VLAN routing with Firewalla + UniFi:

**Symptoms:**
- Device on VLAN 10 can't reach device on VLAN 20
- VLAN isolation works but shouldn't (or vice versa)

**Diagnostic Steps:**

1. **Verify VLANs Exist on Firewalla:**
   ```
   # SSH to Firewalla
   ip a | grep eth0
   # Should show: eth0.10, eth0.20 for each VLAN
   ```

2. **Check Firewalla Rules:**
   - Firewalla App → Rules
   - Look for rules blocking VLAN-to-VLAN
   - Default: VLANs CAN communicate unless blocked

3. **Verify UniFi VLAN IDs Match:**
   - UniFi Networks must use same VLAN ID as Firewalla
   - VLAN 10 in Firewalla = VLAN 10 in UniFi Network

4. **Check Switch Port Profiles:**
   - Inter-switch links must trunk all needed VLANs
   - Access ports must be on correct VLAN

5. **Test Routing:**
   - From VLAN 10 device: `ping 192.168.20.1` (Firewalla's VLAN 20 interface)
   - If that works, routing is fine - check target device
   - If not, switch trunk or Firewalla VLAN issue

6. **Check Firewalla DHCP:**
   - Each VLAN should have DHCP server enabled
   - Verify devices get correct gateway (Firewalla's IP on that VLAN)

**Common Fix:**
Reboot the UniFi switch after VLAN changes - trunking updates don't always apply live."""
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def generate_examples() -> List[Dict]:
    """Generate all cross-domain examples."""
    examples = []
    
    # Architecture & Design
    for item in ARCHITECTURE_DESIGN:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    # VLAN Coordination
    for item in VLAN_COORDINATION:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    # Monitoring & Security
    for item in MONITORING_SECURITY:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    # VPN Integration
    for item in VPN_INTEGRATION:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    # Troubleshooting
    for item in TROUBLESHOOTING:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    return examples


def main():
    """Generate Firewalla + UniFi integration training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Firewalla + UniFi Integration Training Data")
    print("=" * 60)
    
    all_examples = generate_examples()
    
    print(f"\nGenerated sections:")
    print(f"  - Architecture & Design: {len(ARCHITECTURE_DESIGN)} examples")
    print(f"  - VLAN Coordination: {len(VLAN_COORDINATION)} examples")
    print(f"  - Monitoring & Security: {len(MONITORING_SECURITY)} examples")
    print(f"  - VPN Integration: {len(VPN_INTEGRATION)} examples")
    print(f"  - Troubleshooting: {len(TROUBLESHOOTING)} examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "network_integration.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\n[OK] Saved {len(all_examples)} examples to {output_file}")
    
    return all_examples


if __name__ == "__main__":
    main()

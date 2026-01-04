#!/usr/bin/env python3
"""
Firewalla Gold Plus 2.5G Training Data Generator

Generates training examples for Firewalla network security device operations,
configuration, and troubleshooting focused on the Gold Plus model with 2.5G ports.

Categories:
- Basic setup and configuration tasks
- Advanced networking tasks (VLANs, VPN, routing)
- Security and monitoring tasks
- Troubleshooting and diagnostics
- Concept Q&A
- Error scenarios
"""

import json
import random
from pathlib import Path
from typing import List, Dict

# =============================================================================
# SYSTEM PROMPT - Defines the AI assistant's persona for Firewalla
# =============================================================================

SYSTEM_PROMPT = """You are an expert Firewalla network security assistant specializing in the Firewalla Gold Plus 2.5G device. You help users with:

1. Initial setup and configuration of Firewalla Gold Plus
2. Network architecture design (Router Mode, Bridge Mode, DHCP Mode)
3. Security features (Active Protect, Rules, Ad Block, Family Protect)
4. VPN configuration (OpenVPN, WireGuard, Site-to-Site)
5. Network segmentation and VLAN management
6. Advanced features (Smart Queue, Docker, SSH access)
7. Troubleshooting connectivity and performance issues

Hardware Context - Firewalla Gold Plus:
- 4x 2.5 Gigabit Ethernet ports (all ports support 2.5G)
- Port 4 is the default WAN port
- Ports 1-3 are bridged as LAN by default
- Runs Ubuntu 22.04 LTS
- SSH accessible via user 'pi'
- Supports Docker containers
- Red security dongle required for initial pairing

Always provide clear, step-by-step instructions and explain the security implications of configuration changes."""

# =============================================================================
# BASIC SETUP TASKS - Initial configuration and pairing
# =============================================================================

BASIC_SETUP_TASKS = [
    {
        "instruction": "How do I set up my new Firewalla Gold Plus for the first time?",
        "response": {
            "action": "initial_setup",
            "steps": [
                "1. Download the Firewalla app from iOS App Store or Google Play",
                "2. Create a Firewalla account or sign in",
                "3. Tap '+' to add a new device and select 'Firewalla Gold Plus'",
                "4. Connect the red security dongle to a USB port on the Gold Plus",
                "5. Power on the Gold Plus and wait for the blue LED to stabilize",
                "6. Follow the app's Bluetooth pairing process",
                "7. Choose your network mode: Router Mode (recommended), Bridge Mode, or DHCP Mode",
                "8. Connect WAN cable to Port 4, LAN devices to Ports 1-3",
                "9. Complete the setup wizard in the app"
            ],
            "notes": [
                "Router Mode is recommended for full feature access",
                "Keep the red dongle in a safe place - needed for re-pairing",
                "Initial setup requires Bluetooth - stay within range"
            ]
        }
    },
    {
        "instruction": "What's the difference between Router Mode and Bridge Mode on Firewalla?",
        "response": {
            "comparison": {
                "router_mode": {
                    "description": "Firewalla acts as your primary router, replacing or working alongside existing router",
                    "features": "Full feature set - VPN Server, Network Segmentation, Smart Queue, all monitoring",
                    "best_for": "Users wanting maximum control and all Firewalla features",
                    "setup": "Connect ISP modem to Port 4 (WAN), devices to Ports 1-3 (LAN)"
                },
                "bridge_mode": {
                    "description": "Firewalla monitors traffic inline between router and devices",
                    "features": "Monitoring, IDS/IPS, Rules - but no VPN Server or Network Segmentation",
                    "best_for": "Users who want to keep existing router as primary",
                    "setup": "Connect between existing router and network switch"
                },
                "dhcp_mode": {
                    "description": "Legacy mode - Firewalla gets IP from router, monitors via ARP spoofing",
                    "features": "Basic monitoring only, limited features",
                    "best_for": "Simple setups or when other modes aren't possible"
                }
            },
            "recommendation": "Router Mode provides the best experience with all features enabled"
        }
    },
    {
        "instruction": "How do I connect my Firewalla Gold Plus in Router Mode?",
        "response": {
            "action": "router_mode_setup",
            "physical_connections": [
                "1. Connect your ISP modem/ONT Ethernet output to Port 4 (WAN)",
                "2. Connect your WiFi access point(s) to Port 1, 2, or 3",
                "3. Connect any wired devices or switches to remaining LAN ports",
                "4. Power on the Firewalla Gold Plus"
            ],
            "app_configuration": [
                "1. Open Firewalla app and select your Gold Plus",
                "2. Go to Network Manager",
                "3. Verify WAN is configured (DHCP, Static IP, or PPPoE)",
                "4. Configure LAN subnet if needed (default: 192.168.218.x)",
                "5. Enable DHCP server for LAN"
            ],
            "verification": [
                "Check that WAN shows connected with IP address",
                "Verify LAN devices receive DHCP addresses",
                "Test internet connectivity from a connected device"
            ]
        }
    },
    {
        "instruction": "How do I configure PPPoE on my Firewalla Gold Plus?",
        "response": {
            "action": "configure_pppoe",
            "steps": [
                "1. Open Firewalla app > Network Manager",
                "2. Tap on WAN (Port 4)",
                "3. Select 'PPPoE' as WAN Type",
                "4. Enter your ISP-provided username",
                "5. Enter your ISP-provided password",
                "6. Optionally configure VLAN ID if required by ISP",
                "7. Save and wait for connection to establish"
            ],
            "performance_note": "Gold Plus can achieve up to 2.3 Gbps with PPPoE when QoS is enabled",
            "troubleshooting": [
                "Verify credentials are correct (case-sensitive)",
                "Check if ISP requires specific VLAN tagging",
                "Some ISPs need MAC address cloning from old router"
            ]
        }
    },
    {
        "instruction": "How do I enable Active Protect (IDS/IPS) on Firewalla?",
        "response": {
            "action": "enable_active_protect",
            "steps": [
                "1. Open Firewalla app",
                "2. Tap 'Active Protect' on the main page",
                "3. Toggle 'Active Protect' ON",
                "4. Choose protection level: Low, Medium, or High",
                "5. Select which devices/networks to protect"
            ],
            "protection_levels": {
                "low": "Blocks known malicious sites and severe threats",
                "medium": "Adds suspicious activity detection and more threat categories",
                "high": "Maximum protection - may cause some false positives"
            },
            "features_included": [
                "Intrusion Detection System (IDS)",
                "Intrusion Prevention System (IPS)",
                "Abnormal upload detection",
                "Malware site blocking",
                "Compromised device detection"
            ]
        }
    },
    {
        "instruction": "How do I set up Ad Block on Firewalla?",
        "response": {
            "action": "enable_ad_block",
            "steps": [
                "1. Open Firewalla app",
                "2. Tap 'Ad Block' on the main page",
                "3. Toggle Ad Block ON",
                "4. Choose mode: Default or Strict",
                "5. Select which devices/networks to apply it to"
            ],
            "modes": {
                "default": "Blocks common ad networks with minimal false positives",
                "strict": "More aggressive blocking - may break some sites"
            },
            "custom_lists": "You can add custom Target Lists for additional blocking (e.g., OISD)",
            "exceptions": "Create Allow rules for domains you need to access that get blocked",
            "note": "Firewalla cannot block YouTube ads as they come from YouTube's own servers"
        }
    },
    {
        "instruction": "How do I enable Family Protect on Firewalla?",
        "response": {
            "action": "enable_family_protect",
            "steps": [
                "1. Open Firewalla app",
                "2. Tap 'Family' on the main page",
                "3. Toggle 'Family Protect' ON",
                "4. Choose mode: 3rd-Party (OpenDNS) or Native",
                "5. Select devices to protect"
            ],
            "native_mode_options": [
                "Block All Porn Sites",
                "Block All Gambling Sites", 
                "Block All VPN Sites",
                "Block All Violence Sites",
                "Block All Drugs & Alcohol Sites",
                "Block DoH Services",
                "Block Apple Private Relay"
            ],
            "additional_features": [
                "Safe Search enforcement",
                "Social Hour time limits",
                "Family Time scheduling"
            ],
            "note": "Native Family Protect is not available on Red or Blue models"
        }
    },
    {
        "instruction": "How do I create a blocking rule on Firewalla?",
        "response": {
            "action": "create_block_rule",
            "steps": [
                "1. Open Firewalla app",
                "2. Go to Rules > tap '+' to add new rule",
                "3. Select 'Block' as the action",
                "4. Choose what to block:",
                "   - Domain (e.g., facebook.com)",
                "   - App category (e.g., Social, Gaming)",
                "   - IP address or range",
                "   - Region/Country",
                "   - Port number",
                "5. Select which devices/networks the rule applies to",
                "6. Optionally set a schedule",
                "7. Save the rule"
            ],
            "rule_priority": "Device rules > Group rules > Network rules > Global rules",
            "tip": "Use 'Disturb' action instead of Block to slow connections rather than fully blocking"
        }
    },
    {
        "instruction": "How do I allow a specific device to bypass Ad Block?",
        "response": {
            "action": "exclude_device_from_adblock",
            "method_1": {
                "description": "Use Exclude feature",
                "steps": [
                    "1. Go to Ad Block settings",
                    "2. Tap 'Apply To' section",
                    "3. Add the device to 'Exclude Devices' list"
                ]
            },
            "method_2": {
                "description": "Create Allow rule for specific domains",
                "steps": [
                    "1. Go to Rules",
                    "2. Create new Allow rule",
                    "3. Specify the blocked domain",
                    "4. Apply to the specific device"
                ]
            },
            "note": "Device-level rules take priority over network-level Ad Block"
        }
    },
    {
        "instruction": "How do I check what devices are connected to my Firewalla network?",
        "response": {
            "action": "view_devices",
            "steps": [
                "1. Open Firewalla app",
                "2. Main page shows all networks and device counts",
                "3. Tap on a network to see devices in that network",
                "4. Tap on any device for detailed information"
            ],
            "device_info_available": [
                "Device name and manufacturer",
                "IP address and MAC address",
                "Network/VLAN membership",
                "Bandwidth usage (upload/download)",
                "Active flows and connections",
                "Applied rules",
                "Activity history"
            ],
            "tips": [
                "Use Device Groups to organize similar devices",
                "Enable new device notifications for alerts",
                "Quarantine unknown devices for investigation"
            ]
        }
    },
]

# =============================================================================
# ADVANCED NETWORKING TASKS - VLANs, VPN, Routing
# =============================================================================

ADVANCED_NETWORKING_TASKS = [
    {
        "instruction": "How do I create a VLAN on Firewalla Gold Plus?",
        "response": {
            "action": "create_vlan",
            "steps": [
                "1. Open Firewalla app > Network Manager",
                "2. Tap '+' to create new network",
                "3. Select 'VLAN' as the type",
                "4. Enter network name (e.g., 'IoT Network')",
                "5. Assign VLAN ID (2-4094)",
                "6. Configure subnet (e.g., 192.168.100.0/24)",
                "7. Select which LAN port(s) to tag with this VLAN",
                "8. Enable DHCP server for the VLAN",
                "9. Save the configuration"
            ],
            "use_cases": [
                "Isolate IoT devices from main network",
                "Create guest network",
                "Separate work and personal devices",
                "Security camera network isolation"
            ],
            "inter_vlan_routing": "By default, VLANs can communicate. Create block rules to isolate them."
        }
    },
    {
        "instruction": "How do I isolate my IoT devices from my main network?",
        "response": {
            "action": "isolate_iot_network",
            "steps": [
                "1. Create a new VLAN for IoT devices:",
                "   - Network Manager > '+' > VLAN",
                "   - Name: 'IoT Network', VLAN ID: 100",
                "   - Subnet: 192.168.100.0/24",
                "2. Move IoT devices to the new VLAN:",
                "   - Configure VLAN-aware switch, or",
                "   - Use separate physical port with VLAN tagging",
                "3. Create isolation rules:",
                "   - Rules > '+' > Block",
                "   - From: IoT Network > To: Main Network (Local)",
                "   - This blocks IoT from accessing main network devices",
                "4. Allow IoT to access internet:",
                "   - IoT devices can still reach internet by default"
            ],
            "additional_security": [
                "Enable Active Protect on IoT network",
                "Consider blocking IoT from initiating outbound connections except to known servers",
                "Monitor for unusual traffic patterns"
            ]
        }
    },
    {
        "instruction": "How do I set up a WireGuard VPN server on Firewalla?",
        "response": {
            "action": "setup_wireguard_server",
            "requirements": [
                "Firewalla Gold, Gold Plus, Gold SE, or Purple",
                "Router Mode enabled",
                "Public IP or DDNS configured",
                "Port forwarding if behind another router"
            ],
            "steps": [
                "1. Open Firewalla app > VPN Server",
                "2. Tap to enable WireGuard server",
                "3. Configure VPN settings:",
                "   - VPN subnet (default works for most)",
                "   - DNS for VPN clients",
                "4. Set up port forwarding if needed (default port: 51820/UDP)",
                "5. Create VPN profiles for clients:",
                "   - Tap 'Add Client'",
                "   - Name the client",
                "   - Download/share the configuration",
                "6. Import config on client device using WireGuard app"
            ],
            "client_setup": "Use official WireGuard apps on iOS, Android, Windows, Mac, or Linux",
            "performance": "WireGuard offers better performance than OpenVPN, especially on mobile"
        }
    },
    {
        "instruction": "How do I connect to a 3rd-party VPN service on Firewalla?",
        "response": {
            "action": "setup_vpn_client",
            "supported_protocols": ["OpenVPN", "WireGuard", "AnyConnect"],
            "steps": [
                "1. Open Firewalla app > VPN Client",
                "2. Tap '+ Create VPN Connection'",
                "3. Select '3rd-Party VPN'",
                "4. Choose protocol (OpenVPN or WireGuard)",
                "5. Import configuration file from your VPN provider:",
                "   - OpenVPN: Import .ovpn file",
                "   - WireGuard: Import config or scan QR code",
                "6. Enter username/password if required",
                "7. Save the profile",
                "8. Apply VPN to specific devices or networks",
                "9. Toggle VPN connection ON"
            ],
            "verified_providers": [
                "ExpressVPN", "NordVPN", "Surfshark", 
                "ProtonVPN", "PureVPN", "Smart DNS Proxy"
            ],
            "tips": [
                "Use 'Force DNS over VPN' for privacy",
                "Enable 'Internet Kill Switch' to block traffic if VPN drops",
                "Create VPN Group for failover between multiple VPNs"
            ]
        }
    },
    {
        "instruction": "How do I set up Site-to-Site VPN between two Firewalla devices?",
        "response": {
            "action": "setup_site_to_site_vpn",
            "requirements": [
                "Two Firewalla boxes (same account recommended)",
                "Different subnets at each site",
                "VPN Server enabled on one box"
            ],
            "steps": [
                "1. On SERVER site Firewalla:",
                "   - Enable VPN Server (OpenVPN or WireGuard)",
                "   - Configure port forwarding if behind NAT",
                "2. On CLIENT site Firewalla:",
                "   - Go to VPN Client > '+ Create VPN Connection'",
                "   - Select 'Site to Site VPN'",
                "   - Choose the server Firewalla from list",
                "   - Select protocol matching server",
                "3. Configure routing:",
                "   - Outbound Policy for peer subnets",
                "   - Internet: Direct or VPN",
                "4. Connect and verify bidirectional access"
            ],
            "important_notes": [
                "Subnets must NOT overlap between sites",
                "Allow rules are automatically created",
                "Use Routes for selective traffic steering"
            ]
        }
    },
    {
        "instruction": "How do I set up port forwarding on Firewalla?",
        "response": {
            "action": "configure_port_forwarding",
            "steps": [
                "1. Open Firewalla app > Network Manager",
                "2. Tap on WAN network",
                "3. Go to 'Port Forwarding' section",
                "4. Tap '+' to add new rule",
                "5. Configure the forwarding:",
                "   - External Port: Port accessible from internet",
                "   - Internal IP: Device to forward to",
                "   - Internal Port: Port on the device",
                "   - Protocol: TCP, UDP, or Both",
                "6. Save the rule"
            ],
            "security_considerations": [
                "Only forward ports that are absolutely necessary",
                "Keep services updated to prevent exploits",
                "Consider using VPN instead for remote access",
                "Monitor forwarded ports for suspicious activity"
            ],
            "common_ports": {
                "web_server": "80 (HTTP), 443 (HTTPS)",
                "game_servers": "Various - check game documentation",
                "plex": "32400",
                "ssh": "22 (consider using non-standard port)"
            }
        }
    },
    {
        "instruction": "How do I configure Multi-WAN failover on Firewalla Gold Plus?",
        "response": {
            "action": "configure_multi_wan",
            "steps": [
                "1. Connect secondary WAN to available port",
                "2. Open Network Manager",
                "3. Configure the port as secondary WAN:",
                "   - Tap the port > Set as WAN",
                "   - Configure IP settings (DHCP/Static/PPPoE)",
                "4. Set WAN priorities:",
                "   - Primary WAN: Main connection",
                "   - Secondary WAN: Failover connection",
                "5. Configure failover behavior:",
                "   - Health check settings",
                "   - Failover threshold"
            ],
            "load_balancing": "Can also configure for load balancing instead of failover",
            "policy_routing": "Use Policy-Based Routing to send specific traffic over specific WAN"
        }
    },
    {
        "instruction": "How do I set up DNS over HTTPS (DoH) on Firewalla?",
        "response": {
            "action": "enable_doh",
            "steps": [
                "1. Open Firewalla app",
                "2. Go to DNS settings (Network > DNS)",
                "3. Enable 'DNS over HTTPS'",
                "4. Select DoH provider:",
                "   - Cloudflare (1.1.1.1)",
                "   - Google (8.8.8.8)",
                "   - Quad9",
                "   - Custom DoH server",
                "5. Apply to All Devices or specific devices/networks"
            ],
            "benefits": [
                "Encrypts DNS queries from Firewalla to DNS server",
                "Prevents ISP from seeing DNS requests",
                "Protects against DNS spoofing"
            ],
            "note": "DoH on Firewalla encrypts traffic FROM Firewalla. Device-level DoH may bypass Firewalla DNS features."
        }
    },
    {
        "instruction": "How do I use policy-based routing on Firewalla?",
        "response": {
            "action": "configure_policy_routing",
            "steps": [
                "1. Go to Rules > '+' > Route",
                "2. Select traffic to route:",
                "   - By device, group, or network",
                "   - By destination (domain, IP, region)",
                "   - By app category",
                "3. Select destination interface:",
                "   - Specific WAN",
                "   - VPN connection",
                "4. Save the route rule"
            ],
            "use_cases": [
                "Route streaming traffic through VPN",
                "Send work devices through work VPN",
                "Route gaming traffic through low-latency WAN",
                "Bypass VPN for specific services"
            ],
            "example": "Route all Netflix traffic through ExpressVPN for region unlocking"
        }
    },
    {
        "instruction": "How do I set up a DMZ on Firewalla?",
        "response": {
            "action": "configure_dmz",
            "steps": [
                "1. Open Network Manager",
                "2. Tap on WAN",
                "3. Find 'DMZ' setting",
                "4. Enable DMZ",
                "5. Enter the IP address of the DMZ host",
                "6. Save configuration"
            ],
            "warning": "DMZ exposes ALL ports to the specified device - use with extreme caution",
            "better_alternative": "Use specific port forwarding rules instead of full DMZ when possible",
            "security": "Ensure DMZ device has its own firewall and is fully patched"
        }
    },
]

# =============================================================================
# SECURITY AND MONITORING TASKS
# =============================================================================

SECURITY_MONITORING_TASKS = [
    {
        "instruction": "How do I view my network traffic flows on Firewalla?",
        "response": {
            "action": "view_network_flows",
            "steps": [
                "1. Open Firewalla app",
                "2. Tap on any device to see its flows",
                "3. Or go to 'Flows' from main menu",
                "4. Filter by: All, Blocked, or Allowed",
                "5. Tap any flow for details"
            ],
            "flow_information": [
                "Source and destination",
                "Domain/IP being accessed",
                "Data transferred",
                "Duration and timestamp",
                "Applied rules"
            ],
            "actions_from_flows": [
                "Create block/allow rules directly from flow",
                "Add domain to target list",
                "Investigate suspicious activity"
            ]
        }
    },
    {
        "instruction": "How do I set up alerts for new devices on my network?",
        "response": {
            "action": "configure_new_device_alerts",
            "steps": [
                "1. Open Firewalla app",
                "2. Go to Settings > Notifications",
                "3. Enable 'New Device' notifications",
                "4. Optionally enable 'Quarantine New Devices'",
                "5. Configure notification preferences (push, email)"
            ],
            "quarantine_mode": {
                "description": "New devices are isolated until you approve them",
                "benefit": "Prevents unauthorized devices from accessing network",
                "action": "Review and approve devices in the app"
            }
        }
    },
    {
        "instruction": "How do I monitor bandwidth usage on Firewalla?",
        "response": {
            "action": "monitor_bandwidth",
            "locations": [
                "Main page: Shows real-time total bandwidth",
                "Device detail: Individual device usage",
                "Network detail: Per-network bandwidth",
                "Stats/Reports: Historical usage data"
            ],
            "features": [
                "Real-time upload/download speeds",
                "Daily/weekly/monthly usage reports",
                "Top consumers identification",
                "Data caps and alerts"
            ],
            "steps_for_detailed_view": [
                "1. Tap device or network",
                "2. View bandwidth graph",
                "3. Tap 'Stats' for historical data",
                "4. Filter by time period"
            ]
        }
    },
    {
        "instruction": "How do I quarantine a suspicious device on Firewalla?",
        "response": {
            "action": "quarantine_device",
            "steps": [
                "1. Open Firewalla app",
                "2. Find the device in device list",
                "3. Tap on the device",
                "4. Tap 'Quarantine' button",
                "5. Confirm quarantine action"
            ],
            "quarantine_effect": [
                "Device loses internet access",
                "Device isolated from other network devices",
                "Device remains visible for monitoring",
                "Can be unquarantined when safe"
            ],
            "when_to_use": [
                "Unknown device appears on network",
                "Device showing suspicious behavior",
                "Compromised device detected",
                "Temporary restriction needed"
            ]
        }
    },
    {
        "instruction": "How do I set up scheduled rules on Firewalla?",
        "response": {
            "action": "create_scheduled_rule",
            "steps": [
                "1. Create or edit a rule (Block/Allow)",
                "2. In rule settings, tap 'Schedule'",
                "3. Toggle scheduling ON",
                "4. Set start and end times",
                "5. Select days of the week",
                "6. Save the rule"
            ],
            "use_cases": [
                "Block gaming during homework hours",
                "Allow social media only on weekends",
                "Enable work VPN during business hours",
                "Restrict internet access at bedtime"
            ],
            "tip": "Use Device Groups to apply schedules to multiple children's devices at once"
        }
    },
    {
        "instruction": "How do I check the security alarms on Firewalla?",
        "response": {
            "action": "view_security_alarms",
            "steps": [
                "1. Open Firewalla app",
                "2. Tap 'Alarms' from main page",
                "3. View alarm list sorted by time",
                "4. Tap any alarm for details"
            ],
            "alarm_types": [
                "Abnormal upload detected",
                "New device connected",
                "Blocked threat attempt",
                "Vulnerability scan detected",
                "Compromised website access",
                "VPN connection changes",
                "Device behavior changes"
            ],
            "actions_available": [
                "Mark as read",
                "Create rule from alarm",
                "Archive/dismiss",
                "Share alarm details"
            ]
        }
    },
    {
        "instruction": "How do I enable Safe Search on Firewalla?",
        "response": {
            "action": "enable_safe_search",
            "steps": [
                "1. Open Firewalla app",
                "2. Go to Features > Safe Search",
                "3. Toggle Safe Search ON",
                "4. Select devices to apply it to"
            ],
            "supported_search_engines": [
                "Google",
                "Bing", 
                "DuckDuckGo",
                "YouTube"
            ],
            "how_it_works": "Firewalla forces search engines to use their built-in safe search filtering",
            "limitation": "Cannot enforce safe search on encrypted/private browsers"
        }
    },
    {
        "instruction": "How do I see what apps my devices are using?",
        "response": {
            "action": "view_app_usage",
            "steps": [
                "1. Open Firewalla app",
                "2. Tap on a device",
                "3. View 'Apps' section",
                "4. See categorized app usage"
            ],
            "categories_tracked": [
                "Social (Facebook, Instagram, TikTok)",
                "Streaming (Netflix, YouTube, Spotify)",
                "Gaming",
                "Shopping",
                "News",
                "Adult content",
                "And many more..."
            ],
            "actions": [
                "Block entire app category",
                "Set time limits per category",
                "View usage statistics"
            ]
        }
    },
]

# =============================================================================
# TROUBLESHOOTING TASKS
# =============================================================================

TROUBLESHOOTING_TASKS = [
    {
        "instruction": "My internet is slow after installing Firewalla Gold Plus. How do I fix this?",
        "response": {
            "diagnosis": "speed_issues",
            "common_causes": [
                "Smart Queue (QoS) configured incorrectly",
                "VPN client active on all traffic",
                "Hardware not utilizing 2.5G ports properly",
                "Ethernet cable quality (need Cat5e or better)"
            ],
            "troubleshooting_steps": [
                "1. Run speed test through Firewalla app",
                "2. Check Smart Queue settings - ensure speeds match your plan",
                "3. Verify VPN is not routing all traffic unnecessarily",
                "4. Test with device directly connected to Gold Plus",
                "5. Check cable quality - use Cat5e/Cat6 for 2.5G speeds",
                "6. Verify ISP modem is outputting expected speeds",
                "7. Check for bandwidth-heavy devices consuming capacity"
            ],
            "smart_queue_fix": "Network Manager > WAN > Smart Queue > Set correct download/upload speeds"
        }
    },
    {
        "instruction": "Firewalla is not blocking ads on my device. What should I check?",
        "response": {
            "diagnosis": "ad_block_not_working",
            "troubleshooting_steps": [
                "1. Verify Ad Block is enabled for the device",
                "2. Clear DNS cache on the device:",
                "   - iPhone/Android: Toggle Airplane mode",
                "   - Windows: ipconfig /flushdns",
                "   - Mac: sudo dscacheutil -flushcache",
                "3. Check if device uses custom DNS (bypass Firewalla)",
                "4. Verify device is not using DoH/DoT directly",
                "5. Check if device is on VPN (may bypass Firewalla)",
                "6. Test with strict mode if default isn't blocking enough"
            ],
            "limitations": [
                "YouTube ads cannot be blocked (same server as content)",
                "Some apps use encrypted DNS (DoH) bypassing Firewalla",
                "In-app ads may use different domains than web ads"
            ]
        }
    },
    {
        "instruction": "I can't connect to my VPN server remotely. What's wrong?",
        "response": {
            "diagnosis": "vpn_connection_failure",
            "common_causes": [
                "Port forwarding not configured",
                "Firewalla behind another router (double NAT)",
                "ISP blocking VPN ports",
                "DDNS not updated with current IP"
            ],
            "troubleshooting_steps": [
                "1. Verify VPN server is enabled and running",
                "2. Check DDNS is configured and resolving correctly",
                "3. If behind another router, set up port forwarding:",
                "   - OpenVPN: UDP 1194",
                "   - WireGuard: UDP 51820",
                "4. Test from different network (mobile data)",
                "5. Check VPN Server logs in Firewalla",
                "6. Verify client config matches server settings",
                "7. Try different port if ISP blocks default"
            ]
        }
    },
    {
        "instruction": "A device keeps losing connection to my Firewalla network.",
        "response": {
            "diagnosis": "device_connectivity_issues",
            "troubleshooting_steps": [
                "1. Check device's DHCP lease status",
                "2. Verify device is not quarantined",
                "3. Check for IP address conflicts",
                "4. Verify WiFi AP is functioning correctly",
                "5. Check if device has block rules applied",
                "6. Look for patterns (time-based, usage-based)",
                "7. Check Firewalla logs for disconnect events"
            ],
            "if_dhcp_issue": [
                "Network Manager > LAN > DHCP settings",
                "Extend lease time",
                "Reserve IP for problematic device",
                "Check DHCP pool isn't exhausted"
            ]
        }
    },
    {
        "instruction": "My Firewalla shows offline in the app. How do I reconnect?",
        "response": {
            "diagnosis": "firewalla_offline",
            "immediate_checks": [
                "1. Verify Firewalla has power (check LEDs)",
                "2. Check if WAN connection is active",
                "3. Verify your phone has internet access"
            ],
            "troubleshooting_steps": [
                "1. Wait 2-3 minutes - may be temporary cloud issue",
                "2. Check Firewalla's WAN LED status",
                "3. Try accessing Firewalla's local web interface",
                "4. Power cycle the Firewalla (unplug 10 seconds)",
                "5. Check ISP outage status",
                "6. If persistent, SSH into Firewalla to diagnose"
            ],
            "local_access": "If local access works, issue is likely cloud connectivity"
        }
    },
    {
        "instruction": "How do I SSH into my Firewalla Gold Plus?",
        "response": {
            "action": "ssh_access",
            "steps": [
                "1. Find Firewalla's IP address (Network Manager > LAN > Firewalla IP)",
                "2. Use SSH client (Terminal on Mac/Linux, PuTTY on Windows)",
                "3. Connect: ssh pi@<firewalla_ip>",
                "4. Default password is shown in app: Settings > Advanced > SSH Password",
                "5. Accept host key fingerprint on first connection"
            ],
            "useful_commands": [
                "sudo systemctl status fireapi - Check Firewalla service",
                "ifconfig - View network interfaces",
                "top - View running processes",
                "df -h - Check disk space",
                "cat /var/log/syslog - View system logs"
            ],
            "warning": "Be careful with command line changes - can break Firewalla if done incorrectly"
        }
    },
    {
        "instruction": "How do I factory reset my Firewalla Gold Plus?",
        "response": {
            "action": "factory_reset",
            "methods": [
                {
                    "name": "App Reset",
                    "steps": [
                        "1. Open Firewalla app",
                        "2. Go to Settings > Advanced",
                        "3. Tap 'Reset Firewalla'",
                        "4. Confirm the reset"
                    ]
                },
                {
                    "name": "Physical Reset",
                    "steps": [
                        "1. Locate reset button (small hole on device)",
                        "2. Use paperclip to press and hold reset button",
                        "3. Hold for 10+ seconds until LED pattern changes",
                        "4. Release and wait for reboot"
                    ]
                },
                {
                    "name": "USB Flash Recovery",
                    "steps": [
                        "1. Download recovery image from Firewalla",
                        "2. Flash to USB drive using Etcher/Rufus",
                        "3. Boot Firewalla from USB",
                        "4. Follow recovery prompts"
                    ]
                }
            ],
            "warning": "Factory reset erases all settings, rules, and data"
        }
    },
    {
        "instruction": "Some websites won't load after enabling Firewalla. How do I troubleshoot?",
        "response": {
            "diagnosis": "website_access_issues",
            "troubleshooting_steps": [
                "1. Check if site is blocked by a rule:",
                "   - View blocked flows in app",
                "   - Look for matching block rules",
                "2. Check if Ad Block is blocking required resources",
                "3. Check if Family Protect is categorizing site incorrectly",
                "4. Temporarily disable features to isolate cause:",
                "   - Turn off Ad Block",
                "   - Turn off Active Protect",
                "   - Turn off Family Protect",
                "5. Create allow rule for the specific domain",
                "6. Clear browser cache and DNS cache"
            ],
            "creating_exception": [
                "Go to Rules > '+' > Allow",
                "Enter the domain that's blocked",
                "Apply to affected device",
                "Save rule"
            ]
        }
    },
    {
        "instruction": "My Firewalla Gold Plus is running hot. Is this normal?",
        "response": {
            "diagnosis": "device_temperature",
            "normal_operation": "Firewalla Gold Plus runs warm during normal operation due to fanless design",
            "concerning_signs": [
                "Device too hot to touch comfortably",
                "Performance degradation",
                "Unexpected reboots",
                "App shows temperature warnings"
            ],
            "recommendations": [
                "Ensure adequate ventilation around device",
                "Don't stack other equipment on top",
                "Keep away from heat sources",
                "Consider vertical mounting for better airflow",
                "Check CPU usage via SSH if very hot"
            ],
            "check_temperature": "SSH in and run: cat /sys/class/thermal/thermal_zone0/temp (divide by 1000 for Celsius)"
        }
    },
    {
        "instruction": "How do I update my Firewalla firmware?",
        "response": {
            "action": "firmware_update",
            "automatic_updates": "Firewalla updates automatically by default",
            "manual_check": [
                "1. Open Firewalla app",
                "2. Go to Settings",
                "3. Check 'Software Version' section",
                "4. If update available, tap to install"
            ],
            "beta_updates": [
                "Settings > Advanced > Beta Program",
                "Enable to receive early updates",
                "Beta may have bugs - use at own risk"
            ],
            "update_process": "Updates install in background, may require brief restart"
        }
    },
]

# =============================================================================
# CONCEPT Q&A - Firewalla features and networking concepts
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is Active Protect on Firewalla?",
        "answer": "Active Protect is Firewalla's real-time security system combining IDS (Intrusion Detection System) and IPS (Intrusion Prevention System). It monitors network traffic for threats like malware, hacking attempts, abnormal data uploads, and compromised devices. When threats are detected, Active Protect can alert you or automatically block malicious traffic. You can set protection levels (Low, Medium, High) based on your security needs."
    },
    {
        "question": "What is the difference between blocking and quarantining a device?",
        "answer": "Blocking creates rules to prevent specific traffic (like blocking access to certain websites or apps), but the device remains connected to the network. Quarantining completely isolates the device - it loses all internet access and cannot communicate with other devices on the network. Quarantine is used for suspicious or compromised devices that need to be completely isolated while you investigate."
    },
    {
        "question": "What is a VLAN and why would I use one on Firewalla?",
        "answer": "A VLAN (Virtual Local Area Network) creates logically separate networks on the same physical infrastructure. On Firewalla, VLANs let you segment your network for security and organization. Common uses include: isolating IoT devices from main computers, creating a guest network, separating work devices from personal devices, or isolating security cameras. Devices on different VLANs cannot communicate unless you create rules allowing it."
    },
    {
        "question": "What is Smart Queue (QoS) on Firewalla?",
        "answer": "Smart Queue is Firewalla's Quality of Service feature that optimizes network traffic to reduce latency and bufferbloat. It's especially useful for gaming, video calls, and VoIP. Smart Queue works by intelligently managing packet queues to prevent any single device or application from saturating your connection. You need to set your actual internet speeds (download/upload) for it to work effectively."
    },
    {
        "question": "What is DDNS and why does Firewalla use it?",
        "answer": "DDNS (Dynamic DNS) maps a domain name to your changing home IP address. Most ISPs assign dynamic IPs that change periodically. Firewalla uses DDNS so you can always connect to your VPN server using a consistent domain name (like yourname.firewalla.org) even when your IP changes. Firewalla automatically updates the DDNS record when your IP changes."
    },
    {
        "question": "What is the difference between OpenVPN and WireGuard?",
        "answer": "Both are VPN protocols supported by Firewalla. OpenVPN is older, well-established, and works in more scenarios but is slower. WireGuard is newer, faster, uses modern cryptography, and has simpler code. WireGuard typically offers better performance, especially on mobile devices, and is recommended for most users. However, OpenVPN has wider compatibility with third-party VPN services."
    },
    {
        "question": "What does 'Router Mode' mean on Firewalla?",
        "answer": "In Router Mode, Firewalla acts as your primary router, handling NAT, DHCP, firewall functions, and routing between your ISP and local network. This mode provides full access to all Firewalla features including VPN Server, Network Segmentation (VLANs), Smart Queue, and complete traffic monitoring. Your ISP modem connects to Firewalla's WAN port, and all your devices connect through Firewalla."
    },
    {
        "question": "What is Network Flow on Firewalla?",
        "answer": "Network Flow (or just 'Flow') is a record of network connections made by devices. Each flow shows source, destination, ports, protocols, data transferred, and duration. Firewalla uses flows to monitor all network activity, allowing you to see what devices are communicating with, detect suspicious behavior, and create rules based on observed traffic patterns. You can view flows for any device in the app."
    },
    {
        "question": "How does Firewalla's Ad Block work?",
        "answer": "Firewalla's Ad Block works at the DNS level. When devices request ad domains, Firewalla intercepts the DNS query and returns a null response, preventing the ad from loading. This works for web pages and many apps without requiring software on each device. However, it cannot block ads served from the same domain as content (like YouTube ads) and may not block ads in apps using encrypted DNS."
    },
    {
        "question": "What is a Target List in Firewalla?",
        "answer": "A Target List is a custom collection of domains, IPs, or subnets that you can use in rules. Instead of creating separate rules for each destination, you create a Target List (like 'Streaming Services' containing Netflix, Hulu, Disney+) and reference it in one rule. Firewalla also supports importing community-maintained lists for enhanced ad blocking or security."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How does Firewalla handle IPv6?",
        "answer": "Firewalla Gold Plus supports IPv6 in Router Mode. You can enable IPv6 in Network Manager for WAN and LAN interfaces. However, some features like VPN Client don't support IPv6 - IPv6 traffic is blocked when VPN is active. Many users disable IPv6 for simplicity and security, as IPv4 meets most home network needs. If your ISP provides IPv6, you can enable it for potentially faster connections to IPv6-enabled services."
    },
    {
        "question": "What is Transparent Bridge Mode on Firewalla?",
        "answer": "Transparent Bridge Mode places Firewalla inline between your router and network, monitoring all traffic without changing IP addresses. Unlike Router Mode, Firewalla doesn't perform NAT - it transparently passes traffic while inspecting it. This mode is useful when you want to keep your existing router but add Firewalla's monitoring and security. However, VPN Server and Network Segmentation are not available in Bridge Mode."
    },
    {
        "question": "How does Site-to-Site VPN differ from Remote Access VPN?",
        "answer": "Remote Access VPN connects a single device (laptop, phone) to your network from anywhere - it's one-way access. Site-to-Site VPN connects two entire networks together, allowing bidirectional access between all devices at both sites. Site-to-Site requires two Firewalla boxes and is used for connecting home to office, or multiple office locations. Both sites can access each other's resources as if on the same network."
    },
    {
        "question": "What is DNS interception on Firewalla?",
        "answer": "Firewalla intercepts all DNS queries on your network, even if devices use custom DNS servers like 8.8.8.8. This ensures security features (Ad Block, Family Protect, Active Protect) work regardless of device DNS settings. When a device queries external DNS, Firewalla redirects it through Firewalla's DNS processing. This can be bypassed by DNS over HTTPS (DoH) on devices, which Firewalla can optionally block."
    },
    {
        "question": "What is the Firewalla overlay network?",
        "answer": "The overlay network is a virtual network Firewalla creates in DHCP and Simple modes to enable advanced features. Devices join the overlay by getting a special IP from Firewalla (default 192.168.218.x). This allows VPN routing and monitoring even when Firewalla isn't the main router. In Router Mode, the overlay isn't needed since Firewalla controls all routing directly."
    },
    {
        "question": "How does Firewalla's abnormal upload detection work?",
        "answer": "Firewalla monitors upload patterns for each device. If a device suddenly uploads significantly more data than normal, Firewalla triggers an 'Abnormal Upload' alarm. This can indicate data exfiltration from malware, ransomware uploading stolen files, or a compromised device. You can investigate the flows to see where data was sent and take action like quarantining the device."
    },
    {
        "question": "What is Policy-Based Routing on Firewalla?",
        "answer": "Policy-Based Routing (PBR) lets you direct specific traffic through specific network paths. Instead of all traffic using the same route, you can create rules like: 'Route all Netflix traffic through VPN' or 'Send gaming traffic through WAN2'. This is useful for multi-WAN setups, selective VPN routing, and optimizing specific applications. PBR rules can match by device, destination, app category, or domain."
    },
    {
        "question": "Can I run Docker containers on Firewalla Gold Plus?",
        "answer": "Yes, Firewalla Gold Plus supports Docker. You can SSH into the device and run Docker containers for additional services like Pi-hole, Home Assistant, or custom applications. However, use this carefully - containers consume resources and could affect Firewalla's primary functions. The device runs Ubuntu 22.04, so most Linux containers work. Back up before making significant changes."
    },
    {
        "question": "What is the Internet Kill Switch on Firewalla VPN?",
        "answer": "The Internet Kill Switch is a VPN Client safety feature. When enabled, if the VPN connection drops unexpectedly, Firewalla immediately blocks all internet access for devices using that VPN. This prevents accidental data leaks over your regular connection. The kill switch only affects devices assigned to use that VPN - other devices continue normally. It's recommended for privacy-critical use cases."
    },
    {
        "question": "How does Firewalla handle double NAT?",
        "answer": "Double NAT occurs when Firewalla (in Router Mode) is behind another router also doing NAT. This can cause issues with VPN Server, port forwarding, and gaming. Solutions include: putting the upstream router in bridge/modem mode, using DMZ to expose Firewalla, or setting up port forwarding on both devices. For the best experience, eliminate double NAT by making Firewalla the only router."
    },
]

# =============================================================================
# ERROR SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "Error: WAN shows 'No IP Address' after setup",
        "error_type": "wan_no_ip",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check physical cable connection to WAN port (Port 4)",
                "Verify modem/ONT has power and shows connected",
                "Check WAN configuration type matches ISP (DHCP, Static, PPPoE)"
            ],
            "common_causes": [
                "Loose or damaged Ethernet cable",
                "Wrong WAN type selected (e.g., DHCP when PPPoE needed)",
                "Modem needs restart after connecting new device",
                "ISP requires MAC address registration"
            ],
            "solutions": [
                "Power cycle modem, then Firewalla",
                "Try different Ethernet cable",
                "Verify WAN type in Network Manager",
                "Clone MAC address from old router if required",
                "Contact ISP if static IP not working"
            ]
        }
    },
    {
        "instruction": "Error: Devices can't get DHCP addresses from Firewalla",
        "error_type": "dhcp_failure",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Verify DHCP server is enabled on LAN",
                "Check DHCP pool has available addresses",
                "Ensure no other DHCP server on network"
            ],
            "common_causes": [
                "DHCP server disabled on Firewalla",
                "DHCP pool exhausted",
                "Conflicting DHCP server (old router still active)",
                "Device set to static IP outside DHCP range"
            ],
            "solutions": [
                "Enable DHCP: Network Manager > LAN > DHCP",
                "Expand DHCP range if pool exhausted",
                "Disconnect or disable DHCP on other routers",
                "Restart network services on Firewalla"
            ]
        }
    },
    {
        "instruction": "Error: VPN Server shows connected but can't access local resources",
        "error_type": "vpn_access_issues",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Verify VPN client received IP address",
                "Check if local devices are reachable by IP",
                "Test if issue is DNS or routing"
            ],
            "common_causes": [
                "Firewall rules blocking VPN traffic",
                "VPN subnet conflicts with local subnet",
                "DNS not routing through VPN",
                "Split tunneling misconfigured"
            ],
            "solutions": [
                "Check for block rules affecting VPN clients",
                "Ensure VPN subnet doesn't overlap with local networks",
                "Enable 'Force DNS over VPN' setting",
                "Verify local network in VPN's allowed subnets"
            ]
        }
    },
    {
        "instruction": "Error: Speed test shows much lower than expected speeds",
        "error_type": "performance_degradation",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Run speed test from Firewalla app directly",
                "Test with device wired directly to Firewalla",
                "Check Smart Queue configuration"
            ],
            "common_causes": [
                "Smart Queue misconfigured with wrong speeds",
                "VPN routing all traffic (encryption overhead)",
                "Cable not supporting 2.5G speeds",
                "ISP throttling or congestion",
                "WiFi bottleneck (not Firewalla issue)"
            ],
            "solutions": [
                "Disable Smart Queue to test baseline speed",
                "Update Smart Queue with correct ISP speeds",
                "Use Cat5e or Cat6 cables for 2.5G",
                "Test at different times for ISP issues",
                "Check VPN is not applied globally"
            ]
        }
    },
    {
        "instruction": "Error: Site-to-Site VPN connected but devices can't communicate",
        "error_type": "site_to_site_routing",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Verify subnets don't overlap between sites",
                "Check allow rules were created",
                "Test connectivity by IP, not hostname"
            ],
            "common_causes": [
                "Overlapping subnets (both sites using 192.168.1.x)",
                "Allow rules missing or misconfigured",
                "Internet outbound set incorrectly",
                "Devices not assigned to use VPN"
            ],
            "solutions": [
                "Change subnet on one site to avoid overlap",
                "Manually create allow rules for peer subnets",
                "Set Internet outbound to 'Direct' if not needed",
                "Use Routes to direct specific traffic to VPN"
            ]
        }
    },
    {
        "instruction": "Error: Family Protect not blocking adult content",
        "error_type": "content_filtering_failure",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Verify Family Protect is enabled for the device",
                "Check if device uses encrypted DNS (DoH/DoT)",
                "Confirm device DNS is going through Firewalla"
            ],
            "common_causes": [
                "Device using DNS over HTTPS (bypasses Firewalla)",
                "VPN on device routing DNS elsewhere",
                "Browser private/secure DNS enabled",
                "Family Protect not applied to device"
            ],
            "solutions": [
                "Enable DoH blocking in Native Family Protect",
                "Disable private DNS in browser settings",
                "Check device VPN isn't bypassing Firewalla",
                "Use Native mode instead of 3rd-party mode"
            ]
        }
    },
    {
        "instruction": "Error: Firewalla app says 'Unable to connect to Firewalla'",
        "error_type": "app_connection_failure",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check if phone has internet connectivity",
                "Verify Firewalla device has power",
                "Check if local network still works"
            ],
            "common_causes": [
                "Firewalla lost internet connectivity",
                "Cloud service temporary outage",
                "Firewalla service crashed",
                "Phone not connected to internet"
            ],
            "solutions": [
                "Wait a few minutes and retry",
                "Power cycle the Firewalla device",
                "Check Firewalla status page for outages",
                "Try accessing local web UI if available",
                "SSH into Firewalla to check services"
            ]
        }
    },
    {
        "instruction": "Error: Port forwarding rule not working",
        "error_type": "port_forward_failure",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Verify port forward rule is configured correctly",
                "Check if service is running on internal device",
                "Test from external network (not local)"
            ],
            "common_causes": [
                "Testing from inside the network (hairpin NAT issue)",
                "Service not listening on the specified port",
                "Double NAT - upstream router blocking",
                "ISP blocking the port (common for 80, 25, 445)"
            ],
            "solutions": [
                "Test from external network (mobile data)",
                "Verify service is running: check device firewall",
                "If double NAT, forward port on upstream router too",
                "Try alternative port if ISP blocks standard ones",
                "Use VPN instead for secure remote access"
            ]
        }
    },
]

# =============================================================================
# ADDITIONAL VARIATIONS - Quick Q&A style
# =============================================================================

QUICK_REFERENCE = [
    # Hardware Questions
    ("How many Ethernet ports does Firewalla Gold Plus have?", 
     "Firewalla Gold Plus has 4 Ethernet ports, all supporting 2.5 Gigabit speeds. Port 4 is the default WAN port, while Ports 1-3 are bridged as LAN by default. You can reconfigure ports in Network Manager."),
    
    ("What's the difference between Gold and Gold Plus?",
     "Gold Plus has 2.5G ports on ALL 4 ports, while original Gold has 1G ports. Gold Plus also has improved CPU performance for higher throughput with encryption (VPN, IDS/IPS). Both run the same software with identical features."),
    
    ("Can I use any port as WAN on Firewalla Gold Plus?",
     "Yes, you can configure any port as WAN in Network Manager. By default Port 4 is WAN, but you can change this. You can even have multiple WAN ports for failover or load balancing."),
    
    ("What operating system does Firewalla run?",
     "Firewalla Gold Plus runs Ubuntu 22.04 LTS. You can SSH into the device (user: pi) to access the Linux command line. The main Firewalla software runs as services on top of Ubuntu."),
    
    ("Where do I find my SSH password?",
     "Your SSH password is in the Firewalla app: Settings > Advanced > SSH Password. The username is always 'pi'. You can SSH to the Firewalla's LAN IP address."),
    
    # Feature Questions
    ("Can Firewalla block YouTube ads?",
     "No, Firewalla cannot block YouTube ads because they're served from the same domain/servers as the actual video content. DNS-based ad blocking only works when ads come from different domains than the content. Consider browser extensions for YouTube ad blocking."),
    
    ("Does Firewalla support WireGuard?",
     "Yes, Firewalla Gold Plus supports WireGuard for both VPN Server and VPN Client. WireGuard is faster and more efficient than OpenVPN. You can create WireGuard profiles in the VPN Server/Client sections."),
    
    ("Can I use Firewalla with my existing router?",
     "Yes, you can use Bridge Mode to place Firewalla between your router and devices. However, for full features (VPN Server, VLANs), Router Mode is recommended where Firewalla replaces your router's routing function."),
    
    ("How many VPN connections can Firewalla handle?",
     "Firewalla supports up to 9 VPN client profiles and can handle 5 active VPN connections simultaneously. For VPN Server, performance depends on bandwidth - Gold Plus can handle multiple concurrent clients."),
    
    ("Does Firewalla work with mesh WiFi systems?",
     "Yes, Firewalla works great with mesh systems like Eero, Google Wifi, Ubiquiti, etc. In Router Mode, connect the mesh base station to Firewalla's LAN port. Put the mesh in bridge/AP mode and let Firewalla handle DHCP and routing."),
    
    # Configuration Questions  
    ("What subnet does Firewalla use by default?",
     "Firewalla uses 192.168.218.0/24 by default for its LAN/overlay network. You can change this in Network Manager. For VLANs, you assign different subnets like 192.168.100.0/24."),
    
    ("How do I change my Firewalla's LAN IP range?",
     "Go to Network Manager > LAN network > tap IP settings. You can change the subnet, gateway IP, and DHCP range. Devices will get new IPs after the change - some may need to reconnect."),
    
    ("Can I reserve IP addresses for specific devices?",
     "Yes, you can set DHCP reservations. Go to the device in the app, tap 'Reserve IP Address' to assign a permanent IP within your DHCP range based on the device's MAC address."),
    
    ("How do I see what's using my bandwidth?",
     "The main Firewalla app screen shows total bandwidth. Tap any device to see its individual usage. The Stats section shows historical data and top consumers. You can also view real-time flows."),
    
    ("How do I block a device from the internet but keep it on LAN?",
     "Create a block rule for that device targeting 'Internet' or all external traffic. Alternatively, use the 'Pause' feature which blocks internet while keeping LAN access. You can also create specific allow rules for LAN-only resources."),
    
    # Troubleshooting Quick Answers
    ("Why does my device show in a different network than expected?",
     "Devices appear in networks based on which port/VLAN they connect through. Check physical connections and switch VLAN tagging. If using WiFi, verify AP is connected to correct port/VLAN."),
    
    ("My speed test shows lower than expected speeds, is Firewalla the bottleneck?",
     "Test by connecting directly to ISP modem to establish baseline. If speeds match ISP plan without Firewalla, check: Smart Queue settings (set to actual speeds), VPN not routing all traffic, and cable quality (Cat5e+ for 2.5G)."),
    
    ("How often does Firewalla update automatically?",
     "Firewalla checks for updates regularly and installs them automatically in the background. Updates require a brief restart. You can join the Beta program in Settings > Advanced to get early updates."),
    
    ("Can I back up my Firewalla configuration?",
     "Firewalla stores configuration in the cloud tied to your account. If you reset or replace your Firewalla, you can restore settings. Manual config backup via SSH is possible but not officially supported."),
    
    ("What happens if Firewalla loses power or crashes?",
     "During outage, all network traffic stops since Firewalla is inline. When power returns, Firewalla boots automatically and restores previous configuration. VPN connections will need to reconnect."),
    
    # Security Questions
    ("Is my data secure with Firewalla?",
     "Firewalla processes all traffic locally - your data doesn't go to Firewalla servers. Only metadata (alarms, device info) syncs to cloud for app access. Firewalla never inspects encrypted content. Local DNS caching keeps queries private."),
    
    ("Can someone hack into my Firewalla?",
     "Firewalla has strong security: no open ports by default, encrypted cloud communication, regular security updates. Keep your app account secure with strong password. SSH access is local-only by default."),
    
    ("Should I enable all security features?",
     "Recommended baseline: Active Protect (Medium), Ad Block (Default mode). Add Family Protect for households with children. More aggressive settings may cause false positives. Tune based on your needs."),
    
    ("How do I know if a device is compromised?",
     "Watch for: Abnormal upload alarms, unexpected outbound connections, high bandwidth usage at odd hours. Use the Flows view to investigate what a device is connecting to. Quarantine suspicious devices immediately."),
]

VPN_PROVIDER_GUIDES = [
    {
        "instruction": "How do I set up ExpressVPN on Firewalla?",
        "response": {
            "steps": [
                "1. Log into ExpressVPN website",
                "2. Go to Manual Configuration > OpenVPN",
                "3. Copy the username and password (NOT your account login)",
                "4. Download .ovpn config file for desired server",
                "5. In Firewalla: VPN Client > Create 3rd Party VPN",
                "6. Select OpenVPN, paste credentials",
                "7. Import the .ovpn file",
                "8. Save and connect"
            ],
            "note": "Use the VPN-specific credentials from ExpressVPN setup page, not your account password"
        }
    },
    {
        "instruction": "How do I set up NordVPN on Firewalla?",
        "response": {
            "steps": [
                "1. Log into Nord Account dashboard",
                "2. Find Service Credentials (not account login)",
                "3. Go to NordVPN Server Picker, download OpenVPN config",
                "4. In Firewalla: VPN Client > Create 3rd Party VPN",
                "5. Select OpenVPN, enter service credentials",
                "6. Import the config file",
                "7. Save and connect"
            ],
            "wireguard_option": "NordVPN also supports WireGuard - check Reddit for extraction guides"
        }
    },
    {
        "instruction": "How do I set up ProtonVPN on Firewalla?",
        "response": {
            "steps": [
                "1. Log into ProtonVPN dashboard",
                "2. Go to Downloads > OpenVPN configuration files",
                "3. Select: Standard configs, Router platform, UDP",
                "4. Download config for desired country",
                "5. Get OpenVPN/IKEv2 credentials from account page",
                "6. In Firewalla: VPN Client > Create 3rd Party VPN",
                "7. Import config, enter credentials, save"
            ],
            "tip": "If connection drops, edit config to have only one 'remote' line (remove extras)"
        }
    },
    {
        "instruction": "How do I set up Surfshark on Firewalla?",
        "response": {
            "steps": [
                "1. Log into Surfshark manual setup page",
                "2. Get service credentials",
                "3. Pick server location, download config",
                "4. In Firewalla: VPN Client > Create 3rd Party VPN",
                "5. Select OpenVPN, enter Surfshark credentials",
                "6. Import config file",
                "7. Save and connect"
            ]
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_step_response(response_data: dict) -> str:
    """Format response with steps and additional info."""
    return json.dumps(response_data, indent=2)

def format_error_response(error_data: dict) -> str:
    """Format error/troubleshooting response."""
    return json.dumps(error_data, indent=2)

def generate_setup_examples() -> List[Dict]:
    """Generate basic setup training examples."""
    examples = []
    
    for task in BASIC_SETUP_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_step_response(task["response"])
        })
    
    return examples

def generate_advanced_examples() -> List[Dict]:
    """Generate advanced networking training examples."""
    examples = []
    
    for task in ADVANCED_NETWORKING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_step_response(task["response"])
        })
    
    return examples

def generate_security_examples() -> List[Dict]:
    """Generate security and monitoring training examples."""
    examples = []
    
    for task in SECURITY_MONITORING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_step_response(task["response"])
        })
    
    return examples

def generate_troubleshooting_examples() -> List[Dict]:
    """Generate troubleshooting training examples."""
    examples = []
    
    for task in TROUBLESHOOTING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_step_response(task["response"])
        })
    
    return examples

def generate_concept_examples() -> List[Dict]:
    """Generate concept Q&A examples."""
    examples = []
    
    for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": concept["question"],
            "response": concept["answer"]
        })
    
    return examples

def generate_error_examples() -> List[Dict]:
    """Generate error handling examples."""
    examples = []
    
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    
    return examples

def generate_quick_reference_examples() -> List[Dict]:
    """Generate quick Q&A examples."""
    examples = []
    
    for question, answer in QUICK_REFERENCE:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": question,
            "response": answer
        })
    
    return examples

def generate_vpn_guide_examples() -> List[Dict]:
    """Generate VPN provider setup examples."""
    examples = []
    
    for guide in VPN_PROVIDER_GUIDES:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": guide["instruction"],
            "response": format_step_response(guide["response"])
        })
    
    return examples

def main():
    """Generate all Firewalla training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Firewalla Gold Plus Training Data")
    print("=" * 60)
    
    all_examples = []
    
    # Generate each category
    print("\n1. Generating setup examples...")
    setup_examples = generate_setup_examples()
    all_examples.extend(setup_examples)
    print(f"   Generated {len(setup_examples)} examples")
    
    print("\n2. Generating advanced networking examples...")
    advanced_examples = generate_advanced_examples()
    all_examples.extend(advanced_examples)
    print(f"   Generated {len(advanced_examples)} examples")
    
    print("\n3. Generating security/monitoring examples...")
    security_examples = generate_security_examples()
    all_examples.extend(security_examples)
    print(f"   Generated {len(security_examples)} examples")
    
    print("\n4. Generating troubleshooting examples...")
    troubleshooting_examples = generate_troubleshooting_examples()
    all_examples.extend(troubleshooting_examples)
    print(f"   Generated {len(troubleshooting_examples)} examples")
    
    print("\n5. Generating concept Q&A...")
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"   Generated {len(concept_examples)} examples")
    
    print("\n6. Generating error scenarios...")
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"   Generated {len(error_examples)} examples")
    
    print("\n7. Generating quick reference Q&A...")
    quick_ref_examples = generate_quick_reference_examples()
    all_examples.extend(quick_ref_examples)
    print(f"   Generated {len(quick_ref_examples)} examples")
    
    print("\n8. Generating VPN provider guides...")
    vpn_examples = generate_vpn_guide_examples()
    all_examples.extend(vpn_examples)
    print(f"   Generated {len(vpn_examples)} examples")
    
    # Shuffle for training
    random.shuffle(all_examples)
    
    # Save to JSONL
    output_file = output_dir / "firewalla_gold_plus.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Firewalla Training Data Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Setup tasks: {len(setup_examples)}")
    print(f"  Advanced networking: {len(advanced_examples)}")
    print(f"  Security/monitoring: {len(security_examples)}")
    print(f"  Troubleshooting: {len(troubleshooting_examples)}")
    print(f"  Concepts Q&A: {len(concept_examples)}")
    print(f"  Error scenarios: {len(error_examples)}")
    print(f"  Quick reference: {len(quick_ref_examples)}")
    print(f"  VPN guides: {len(vpn_examples)}")

if __name__ == "__main__":
    main()

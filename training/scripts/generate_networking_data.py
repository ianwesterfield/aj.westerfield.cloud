#!/usr/bin/env python3
"""
Networking Training Data Generator
Target: ~300 examples for networking, DNS, firewalls, troubleshooting
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for networking and infrastructure.
You help with network configuration, DNS, firewalls, load balancing, and troubleshooting."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

NETWORKING_TASKS = [
    # Diagnostics
    {
        "instruction": "Test connectivity to a host",
        "command": "ping -c 4 google.com",
        "explanation": "Sends 4 ICMP echo requests, shows latency"
    },
    {
        "instruction": "Trace route to destination",
        "command": "traceroute google.com",
        "explanation": "Shows network path and hop latencies (Windows: tracert)"
    },
    {
        "instruction": "Look up DNS record",
        "command": "nslookup example.com",
        "explanation": "Queries DNS for A record (or dig example.com on Linux)"
    },
    {
        "instruction": "Get all DNS records for domain",
        "command": "dig example.com ANY +noall +answer",
        "explanation": "Shows A, AAAA, MX, TXT, NS records"
    },
    {
        "instruction": "Check if port is open",
        "command": "nc -zv hostname 443",
        "explanation": "Tests TCP connection to port 443"
    },
    {
        "instruction": "List listening ports",
        "command": "netstat -tlnp",
        "explanation": "Shows TCP listening ports with process (ss -tlnp on modern Linux)"
    },
    {
        "instruction": "Show network interfaces",
        "command": "ip addr show",
        "explanation": "Lists interfaces with IP addresses (ifconfig deprecated)"
    },
    {
        "instruction": "Show routing table",
        "command": "ip route show",
        "explanation": "Displays routing rules (netstat -rn also works)"
    },
    # Firewall
    {
        "instruction": "List firewall rules",
        "command": "sudo iptables -L -n -v",
        "explanation": "Shows all iptables rules with packet counts"
    },
    {
        "instruction": "Allow incoming port 443",
        "command": "sudo ufw allow 443/tcp",
        "explanation": "Opens HTTPS port in UFW firewall"
    },
    {
        "instruction": "Block IP address",
        "command": "sudo iptables -A INPUT -s 1.2.3.4 -j DROP",
        "explanation": "Drops all packets from specified IP"
    },
    # Advanced
    {
        "instruction": "Capture network traffic",
        "command": "sudo tcpdump -i eth0 -w capture.pcap port 80",
        "explanation": "Captures HTTP traffic to file for analysis"
    },
    {
        "instruction": "Test HTTP endpoint with curl",
        "command": "curl -I -X GET https://api.example.com/health",
        "explanation": "Shows HTTP headers without body"
    },
    {
        "instruction": "Check SSL certificate",
        "command": "openssl s_client -connect example.com:443 -servername example.com | openssl x509 -noout -dates",
        "explanation": "Shows certificate validity dates"
    },
    {
        "instruction": "Test DNS resolution time",
        "command": "dig example.com +stats | grep 'Query time'",
        "explanation": "Shows DNS query latency"
    },
    {
        "instruction": "Query specific DNS record type",
        "command": "dig example.com MX +short",
        "explanation": "Gets MX records in concise format"
    },
    {
        "instruction": "Query DNS with specific server",
        "command": "dig @8.8.8.8 example.com",
        "explanation": "Uses Google DNS for query"
    },
    {
        "instruction": "Reverse DNS lookup",
        "command": "dig -x 8.8.8.8 +short",
        "explanation": "Gets hostname from IP address"
    },
    {
        "instruction": "Check DNSSEC validation",
        "command": "dig example.com +dnssec +short",
        "explanation": "Queries with DNSSEC validation"
    },
    {
        "instruction": "Test TCP port range",
        "command": "nmap -p 80-443 hostname",
        "explanation": "Scans port range for open ports"
    },
    {
        "instruction": "Scan network for hosts",
        "command": "nmap -sn 192.168.1.0/24",
        "explanation": "Ping scan to discover active hosts"
    },
    {
        "instruction": "Scan all TCP ports",
        "command": "nmap -p- --min-rate=1000 hostname",
        "explanation": "Fast full port scan"
    },
    {
        "instruction": "Service version detection",
        "command": "nmap -sV -p 22,80,443 hostname",
        "explanation": "Detects service versions on ports"
    },
    {
        "instruction": "Show active connections",
        "command": "ss -tunapl",
        "explanation": "Lists all TCP/UDP sockets with processes"
    },
    {
        "instruction": "Show connection states",
        "command": "ss -s",
        "explanation": "Summary of socket statistics"
    },
    {
        "instruction": "Find process using port",
        "command": "lsof -i :8080",
        "explanation": "Shows process bound to port 8080"
    },
    {
        "instruction": "Monitor network traffic",
        "command": "iftop -i eth0",
        "explanation": "Real-time bandwidth monitor by connection"
    },
    {
        "instruction": "Monitor bandwidth usage",
        "command": "nethogs",
        "explanation": "Shows bandwidth per process"
    },
    {
        "instruction": "Analyze packet capture",
        "command": "tcpdump -r capture.pcap -n port 80",
        "explanation": "Reads and filters pcap file"
    },
    {
        "instruction": "Capture DNS traffic",
        "command": "sudo tcpdump -i any port 53 -n",
        "explanation": "Monitors DNS queries and responses"
    },
    {
        "instruction": "Test MTU path",
        "command": "ping -M do -s 1472 hostname",
        "explanation": "Tests maximum packet size without fragmentation"
    },
    {
        "instruction": "Configure static IP",
        "command": "sudo ip addr add 192.168.1.100/24 dev eth0",
        "explanation": "Assigns static IP to interface"
    },
    {
        "instruction": "Add default gateway",
        "command": "sudo ip route add default via 192.168.1.1",
        "explanation": "Sets default route"
    },
    {
        "instruction": "Add static route",
        "command": "sudo ip route add 10.0.0.0/8 via 192.168.1.254",
        "explanation": "Routes subnet through specific gateway"
    },
    {
        "instruction": "Delete route",
        "command": "sudo ip route del 10.0.0.0/8",
        "explanation": "Removes routing rule"
    },
    {
        "instruction": "Enable IP forwarding",
        "command": "sudo sysctl -w net.ipv4.ip_forward=1",
        "explanation": "Enables packet forwarding (routing)"
    },
    {
        "instruction": "Show ARP table",
        "command": "ip neigh show",
        "explanation": "Lists MAC address mappings"
    },
    {
        "instruction": "Clear ARP cache",
        "command": "sudo ip neigh flush all",
        "explanation": "Removes all ARP entries"
    },
    {
        "instruction": "Set interface MTU",
        "command": "sudo ip link set eth0 mtu 9000",
        "explanation": "Configures jumbo frames"
    },
    {
        "instruction": "Bring interface up",
        "command": "sudo ip link set eth0 up",
        "explanation": "Enables network interface"
    },
    {
        "instruction": "Take interface down",
        "command": "sudo ip link set eth0 down",
        "explanation": "Disables network interface"
    },
    {
        "instruction": "Create VLAN interface",
        "command": "sudo ip link add link eth0 name eth0.100 type vlan id 100",
        "explanation": "Adds VLAN 100 to eth0"
    },
    {
        "instruction": "Create network bridge",
        "command": "sudo ip link add br0 type bridge && sudo ip link set eth0 master br0",
        "explanation": "Creates bridge and adds interface"
    },
    {
        "instruction": "Enable NAT masquerade",
        "command": "sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
        "explanation": "Enables NAT for outbound traffic"
    },
    {
        "instruction": "Port forwarding with iptables",
        "command": "sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to 192.168.1.10:8080",
        "explanation": "Forwards external port 80 to internal server"
    },
    {
        "instruction": "Save iptables rules",
        "command": "sudo iptables-save > /etc/iptables/rules.v4",
        "explanation": "Persists firewall rules"
    },
    {
        "instruction": "Reset iptables to default",
        "command": "sudo iptables -F && sudo iptables -X && sudo iptables -P INPUT ACCEPT",
        "explanation": "Flushes all rules and sets default accept"
    },
    {
        "instruction": "Allow established connections",
        "command": "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
        "explanation": "Permits return traffic for outbound connections"
    },
    {
        "instruction": "Rate limit connections",
        "command": "sudo iptables -A INPUT -p tcp --dport 22 -m limit --limit 3/minute --limit-burst 3 -j ACCEPT",
        "explanation": "Limits SSH connections to prevent brute force"
    },
    {
        "instruction": "Log dropped packets",
        "command": "sudo iptables -A INPUT -j LOG --log-prefix 'IPTables-Dropped: '",
        "explanation": "Logs dropped packets to syslog"
    },
    {
        "instruction": "Check UFW status",
        "command": "sudo ufw status verbose",
        "explanation": "Shows firewall status and rules"
    },
    {
        "instruction": "Enable UFW",
        "command": "sudo ufw enable",
        "explanation": "Activates UFW firewall"
    },
    {
        "instruction": "Allow specific IP",
        "command": "sudo ufw allow from 192.168.1.0/24 to any port 22",
        "explanation": "Allows SSH from specific subnet"
    },
    {
        "instruction": "Test HTTP response time",
        "command": "curl -w 'DNS: %{time_namelookup}s\\nConnect: %{time_connect}s\\nTTFB: %{time_starttransfer}s\\nTotal: %{time_total}s\\n' -o /dev/null -s https://example.com",
        "explanation": "Shows detailed timing breakdown"
    },
    {
        "instruction": "Test download speed",
        "command": "curl -o /dev/null -w '%{speed_download}' https://speedtest.example.com/largefile",
        "explanation": "Measures download speed in bytes/sec"
    },
    {
        "instruction": "Test with specific DNS",
        "command": "curl --dns-servers 8.8.8.8 https://example.com",
        "explanation": "Uses specific DNS resolver"
    },
    {
        "instruction": "Test IPv6 connectivity",
        "command": "ping6 ipv6.google.com",
        "explanation": "Tests IPv6 reachability"
    },
    {
        "instruction": "Show IPv6 addresses",
        "command": "ip -6 addr show",
        "explanation": "Lists IPv6 addresses on interfaces"
    },
]

WINDOWS_NETWORKING_TASKS = [
    {
        "instruction": "Test connectivity on Windows",
        "command": "Test-NetConnection google.com -Port 443",
        "explanation": "PowerShell connectivity test with port check"
    },
    {
        "instruction": "Show Windows firewall rules",
        "command": "Get-NetFirewallRule | Where-Object { $_.Enabled -eq 'True' } | Select-Object Name, Direction, Action",
        "explanation": "Lists enabled firewall rules"
    },
    {
        "instruction": "Add Windows firewall rule",
        "command": "New-NetFirewallRule -DisplayName 'Allow HTTP' -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow",
        "explanation": "Creates inbound rule for port 80"
    },
    {
        "instruction": "Flush Windows DNS cache",
        "command": "ipconfig /flushdns",
        "explanation": "Clears local DNS resolver cache"
    },
    {
        "instruction": "Show Windows network configuration",
        "command": "Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer",
        "explanation": "Shows IP, gateway, DNS for all interfaces"
    },
    {
        "instruction": "Test multiple ports on Windows",
        "command": "1..1024 | ForEach-Object { Test-NetConnection -ComputerName localhost -Port $_ -WarningAction SilentlyContinue | Where-Object { $_.TcpTestSucceeded } }",
        "explanation": "Scans first 1024 ports for open ones"
    },
    {
        "instruction": "Get network adapter statistics",
        "command": "Get-NetAdapterStatistics | Select-Object Name, ReceivedBytes, SentBytes",
        "explanation": "Shows bytes sent/received per adapter"
    },
    {
        "instruction": "Show routing table on Windows",
        "command": "Get-NetRoute | Where-Object { $_.NextHop -ne '0.0.0.0' } | Select-Object DestinationPrefix, NextHop, InterfaceAlias",
        "explanation": "Lists routes excluding direct connections"
    },
    {
        "instruction": "Add static route on Windows",
        "command": "New-NetRoute -DestinationPrefix '10.0.0.0/8' -NextHop '192.168.1.1' -InterfaceIndex (Get-NetAdapter | Where-Object Status -eq 'Up').ifIndex",
        "explanation": "Creates persistent route"
    },
    {
        "instruction": "Show DNS client cache",
        "command": "Get-DnsClientCache | Select-Object Entry, Data, TimeToLive",
        "explanation": "Lists cached DNS entries"
    },
    {
        "instruction": "Set DNS servers on adapter",
        "command": "Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ServerAddresses ('8.8.8.8','8.8.4.4')",
        "explanation": "Configures DNS servers"
    },
    {
        "instruction": "Test DNS resolution on Windows",
        "command": "Resolve-DnsName example.com -Type A",
        "explanation": "PowerShell DNS lookup"
    },
    {
        "instruction": "Query specific DNS record on Windows",
        "command": "Resolve-DnsName example.com -Type MX -Server 8.8.8.8",
        "explanation": "Queries MX records using Google DNS"
    },
    {
        "instruction": "Remove firewall rule",
        "command": "Remove-NetFirewallRule -DisplayName 'Allow HTTP'",
        "explanation": "Deletes firewall rule by name"
    },
    {
        "instruction": "Disable firewall rule temporarily",
        "command": "Set-NetFirewallRule -DisplayName 'Allow HTTP' -Enabled False",
        "explanation": "Disables without deleting"
    },
    {
        "instruction": "Show active connections on Windows",
        "command": "Get-NetTCPConnection | Where-Object { $_.State -eq 'Established' } | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess",
        "explanation": "Lists established TCP connections"
    },
    {
        "instruction": "Find process using port on Windows",
        "command": "Get-Process -Id (Get-NetTCPConnection -LocalPort 8080).OwningProcess",
        "explanation": "Gets process bound to specific port"
    },
    {
        "instruction": "Show listening ports on Windows",
        "command": "Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, @{N='Process';E={(Get-Process -Id $_.OwningProcess).Name}}",
        "explanation": "Lists listening ports with process names"
    },
    {
        "instruction": "Trace route on Windows",
        "command": "Test-NetConnection google.com -TraceRoute | Select-Object -ExpandProperty TraceRoute",
        "explanation": "PowerShell traceroute"
    },
    {
        "instruction": "Get WiFi profiles on Windows",
        "command": "netsh wlan show profiles",
        "explanation": "Lists saved wireless networks"
    },
    {
        "instruction": "Export WiFi password",
        "command": "netsh wlan show profile name='NetworkName' key=clear",
        "explanation": "Shows WiFi password in plain text"
    },
    {
        "instruction": "Reset network stack on Windows",
        "command": "netsh winsock reset; netsh int ip reset",
        "explanation": "Resets Winsock catalog and TCP/IP stack"
    },
    {
        "instruction": "Show network shares",
        "command": "Get-SmbShare | Select-Object Name, Path, Description",
        "explanation": "Lists SMB shares on system"
    },
    {
        "instruction": "Map network drive",
        "command": "New-PSDrive -Name 'Z' -PSProvider FileSystem -Root '\\\\server\\share' -Persist",
        "explanation": "Maps persistent network drive"
    },
    {
        "instruction": "Test ICMP with larger packet",
        "command": "ping -l 1472 -f hostname",
        "explanation": "Tests MTU path discovery"
    },
    {
        "instruction": "Show adapter advanced properties",
        "command": "Get-NetAdapterAdvancedProperty -Name 'Ethernet' | Select-Object DisplayName, DisplayValue",
        "explanation": "Shows adapter settings like speed, duplex"
    },
    {
        "instruction": "Set static IP on Windows",
        "command": "New-NetIPAddress -InterfaceAlias 'Ethernet' -IPAddress '192.168.1.100' -PrefixLength 24 -DefaultGateway '192.168.1.1'",
        "explanation": "Assigns static IP configuration"
    },
    {
        "instruction": "Enable DHCP on adapter",
        "command": "Set-NetIPInterface -InterfaceAlias 'Ethernet' -Dhcp Enabled; Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ResetServerAddresses",
        "explanation": "Switches adapter to DHCP"
    },
    {
        "instruction": "Get IP geolocation",
        "command": "(Invoke-RestMethod 'http://ip-api.com/json/').country",
        "explanation": "Gets country from public IP"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Troubleshoot network connectivity issue",
        "steps": [
            "Check if issue is local: ping localhost/127.0.0.1",
            "Check network interface: ip addr / Get-NetAdapter",
            "Check default gateway: ping gateway IP",
            "Check DNS resolution: nslookup target.com",
            "Check route to destination: traceroute/tracert",
            "Check if port is open: nc -zv host port / Test-NetConnection",
            "Check firewall rules: iptables -L / Get-NetFirewallRule",
            "Check for packet loss: ping with many packets",
            "Check MTU issues: ping with large packet, DF flag",
            "Check SSL/TLS: openssl s_client",
            "Capture traffic for analysis: tcpdump/Wireshark",
            "Check logs: application, system, network device",
            "Document findings and resolution"
        ]
    },
    {
        "instruction": "Set up nginx as reverse proxy with SSL",
        "steps": [
            "Install nginx: apt install nginx",
            "Obtain SSL certificate: certbot certonly",
            "Create server block configuration",
            "Configure upstream backend servers",
            "Set proxy_pass to upstream",
            "Configure SSL: ssl_certificate, ssl_certificate_key",
            "Add security headers (HSTS, X-Frame-Options)",
            "Configure proxy headers (X-Real-IP, X-Forwarded-For)",
            "Set up WebSocket support if needed",
            "Configure timeouts appropriately",
            "Test configuration: nginx -t",
            "Reload nginx: systemctl reload nginx",
            "Test with curl: curl -I https://domain",
            "Set up auto-renewal for certificates"
        ]
    },
    {
        "instruction": "Configure DNS for new domain",
        "steps": [
            "Purchase domain from registrar",
            "Set nameservers to DNS provider (Route53, Cloudflare)",
            "Create A record pointing to server IP",
            "Create AAAA record for IPv6 if available",
            "Create CNAME for www pointing to apex",
            "Set up MX records for email",
            "Add SPF record for email authentication",
            "Add DKIM record for email signing",
            "Add DMARC record for email policy",
            "Set appropriate TTL values (lower during migration)",
            "Wait for propagation (check with DNS checkers)",
            "Verify with dig/nslookup from multiple locations",
            "Increase TTL after verification"
        ]
    },
    {
        "instruction": "Set up load balancer for web application",
        "steps": [
            "Choose load balancer (nginx, HAProxy, cloud LB)",
            "Configure health checks for backend servers",
            "Choose algorithm (round-robin, least-connections, IP-hash)",
            "Configure backend server pool",
            "Set up SSL termination at load balancer",
            "Configure sticky sessions if needed",
            "Set connection and request timeouts",
            "Configure keep-alive connections",
            "Set up rate limiting",
            "Configure WebSocket support if needed",
            "Set up monitoring and alerting",
            "Test failover by stopping backend servers",
            "Load test to verify distribution",
            "Document configuration and procedures"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is DNS and how does it work?",
        "answer": "DNS (Domain Name System) translates domain names to IP addresses. Hierarchy: root → TLD (.com) → authoritative server. Process: browser → local resolver → recursive resolver → root → TLD → authoritative. Caching at each level reduces lookups. Record types: A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), TXT (text), NS (nameserver). TTL controls cache duration. DNS propagation = time for changes to spread. Use dig/nslookup to troubleshoot."
    },
    {
        "question": "What is the difference between TCP and UDP?",
        "answer": "TCP: connection-oriented, reliable delivery, ordered packets, flow control, error checking. Uses handshake (SYN, SYN-ACK, ACK). Good for: HTTP, SSH, database connections. UDP: connectionless, no guarantees, faster, lower overhead. Good for: DNS, streaming, gaming, VoIP. TCP overhead matters for performance. UDP needs application-level reliability if needed. Port numbers (0-65535) identify services on both."
    },
    {
        "question": "How does a firewall work?",
        "answer": "Firewall filters traffic based on rules. Examines: source/dest IP, port, protocol, direction. Types: packet filter (stateless), stateful (tracks connections), application layer (inspects content). Rules processed in order - first match wins. Default policy: allow or deny. Common: allow established/related, deny invalid. Linux: iptables/nftables, ufw. Windows: Windows Firewall. Cloud: security groups, NACLs. Principle: deny by default, allow specific."
    },
    {
        "question": "What is a subnet and CIDR notation?",
        "answer": "Subnet divides network into smaller segments. CIDR notation: IP/prefix (e.g., 192.168.1.0/24). Prefix = number of network bits. /24 = 256 addresses (254 usable), /16 = 65536, /32 = single host. Subnet mask: 255.255.255.0 = /24. Private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16. Subnetting helps: security isolation, broadcast domain control, address management. Calculate with ipcalc tool."
    },
    {
        "question": "What is a MAC address?",
        "answer": "MAC (Media Access Control) address is hardware identifier for network interfaces. Format: 48-bit, shown as XX:XX:XX:XX:XX:XX (hex). First 3 bytes = manufacturer (OUI), last 3 = device-unique. Used at Layer 2 (data link). ARP maps IP to MAC on local network. MAC addresses don't route across networks - routers use IP. Can be spoofed but shouldn't be relied on for security. Switches use MAC address tables to forward frames."
    },
    {
        "question": "What is DHCP?",
        "answer": "DHCP (Dynamic Host Configuration Protocol) automatically assigns IP addresses to devices. Process: Discover → Offer → Request → Acknowledge (DORA). Provides: IP address, subnet mask, gateway, DNS servers. Lease time controls how long assignment lasts. Reservations tie MAC to specific IP. Scopes define address pools. Alternatives: static IP (manual), APIPA (169.254.x.x self-assign). Critical service - redundancy important."
    },
    {
        "question": "What is a VPN and how does it work?",
        "answer": "VPN (Virtual Private Network) creates encrypted tunnel over public network. Types: Site-to-site (connects networks), Remote access (connects users). Protocols: OpenVPN (flexible), WireGuard (modern, fast), IPSec (standard), L2TP (often with IPSec). Tunnels encapsulate traffic, encryption protects content. Split tunneling: only some traffic through VPN. Corporate VPNs provide access to internal resources. Personal VPNs provide privacy and geo-bypass."
    },
    {
        "question": "What is the OSI model?",
        "answer": "OSI model has 7 layers describing network communication. Physical (1): bits, cables. Data Link (2): frames, MAC addresses, switches. Network (3): packets, IP addresses, routers. Transport (4): TCP/UDP, ports. Session (5): connection management. Presentation (6): encoding, encryption. Application (7): HTTP, SMTP, FTP. Troubleshoot layer by layer. TCP/IP model simpler: Network Interface, Internet, Transport, Application. Know which layer protocols operate at."
    },
    {
        "question": "What is port forwarding?",
        "answer": "Port forwarding redirects traffic from external port to internal IP:port. Used to expose internal services to internet. NAT router receives traffic on public IP:port, forwards to private IP:port. Example: forward port 80 to internal web server 192.168.1.50:80. Also called DNAT (destination NAT). Configure on router/firewall. Security risk - exposes internal services. Alternatives: reverse proxy, VPN, tunneling (ngrok). UPnP can auto-configure but security concern."
    },
    {
        "question": "What is latency vs bandwidth?",
        "answer": "Latency is time for packet to travel (measured in ms). Bandwidth is maximum data rate (Mbps, Gbps). High bandwidth, high latency: good for bulk transfers, bad for interactive. Low latency critical for: gaming, VoIP, real-time apps. Latency caused by: distance, routing hops, congestion, processing. Measure latency with ping. Bandwidth != speed - both matter. CDNs reduce latency by serving from nearby edge. Jitter = latency variation, also matters for real-time."
    },
    {
        "question": "What is ARP?",
        "answer": "ARP (Address Resolution Protocol) maps IP addresses to MAC addresses on local network. When sending to local IP, device broadcasts 'who has 192.168.1.1?', owner responds with MAC. ARP cache stores mappings (arp -a to view). ARP only works on same broadcast domain. ARP spoofing attack: send fake ARP replies to redirect traffic. Gratuitous ARP announces address to network. IPv6 uses NDP (Neighbor Discovery Protocol) instead."
    },
    {
        "question": "What is a VLAN?",
        "answer": "VLAN (Virtual LAN) logically segments network at Layer 2. Benefits: security isolation, broadcast domain control, flexible grouping. Traffic between VLANs requires routing. Tagged frames carry VLAN ID (802.1Q). Access ports belong to one VLAN, trunk ports carry multiple VLANs. Native VLAN is untagged default. Common uses: separate guest/corporate, isolate IoT devices. Managed switches support VLANs. Inter-VLAN routing via Layer 3 switch or router."
    }
]

ADVANCED_CONCEPTS = [
    {
        "question": "What is NAT and why is it used?",
        "answer": "NAT (Network Address Translation) maps private IPs to public IPs. Types: SNAT (source, for outbound), DNAT (destination, for inbound/port forwarding), PAT (port address translation, many-to-one). Why: IPv4 address exhaustion, security (hides internal structure). Home router uses PAT - many devices share one public IP. Issues: breaks end-to-end connectivity, complicates P2P, VoIP needs STUN/TURN. IPv6 designed to eliminate NAT need."
    },
    {
        "question": "How does HTTPS/TLS work?",
        "answer": "TLS (Transport Layer Security) encrypts HTTP. Handshake: client hello → server hello + certificate → key exchange → encrypted session. Certificate: proves server identity, signed by CA. Key exchange: asymmetric crypto establishes shared symmetric key. Data encrypted with symmetric key (faster). Versions: TLS 1.2 (common), TLS 1.3 (faster, more secure). HTTPS uses port 443. Certificate chain: server cert → intermediate → root CA."
    },
    {
        "question": "What is a reverse proxy vs forward proxy?",
        "answer": "Forward proxy: client-side, hides clients from servers. Used for: caching, filtering, anonymity. Reverse proxy: server-side, hides servers from clients. Used for: load balancing, SSL termination, caching, security. Examples: nginx, HAProxy, Cloudflare. Reverse proxy can: distribute load, add HTTPS, compress responses, cache static content, provide WAF. Client connects to proxy IP, proxy forwards to backends."
    },
    {
        "question": "What are common network security threats?",
        "answer": "DDoS: overwhelm with traffic. Mitigation: rate limiting, CDN, cloud protection. Man-in-the-middle: intercept communications. Prevention: TLS, certificate pinning. DNS spoofing: return wrong IP. Prevention: DNSSEC. IP spoofing: fake source IP. Prevention: ingress filtering. Port scanning: discover open services. Prevention: firewall, minimize exposed ports. ARP spoofing: redirect local traffic. Prevention: static ARP, port security. Defense in depth: multiple layers of protection."
    },
    {
        "question": "What is BGP and why is it important?",
        "answer": "BGP (Border Gateway Protocol) routes traffic between autonomous systems (AS) on internet. Path vector protocol - exchanges reachability info between ISPs. BGP hijacking can redirect internet traffic. Attributes: AS path, local preference, MED. eBGP between organizations, iBGP within. Slow convergence can cause outages. Route leaks expose traffic to wrong networks. RPKI adds cryptographic validation. Critical infrastructure - BGP issues cause major internet outages."
    },
    {
        "question": "How does load balancing work?",
        "answer": "Load balancer distributes traffic across servers. Layer 4: routes by IP/port, fast, limited features. Layer 7: routes by content (URL, headers), more flexible. Algorithms: round-robin, least connections, weighted, IP hash. Health checks remove failed servers. Session persistence (sticky sessions) for stateful apps. SSL termination at load balancer offloads crypto. Cloud: ALB, NLB, Azure LB. Software: nginx, HAProxy. Hardware: F5, Citrix."
    },
    {
        "question": "What is service mesh?",
        "answer": "Service mesh handles service-to-service communication in microservices. Sidecar proxy (Envoy) deployed with each service. Features: load balancing, service discovery, mTLS, observability, traffic management. Control plane manages config (Istio, Linkerd). Data plane handles actual traffic. Benefits: consistent security, observability without code changes, traffic splitting, retries. Complexity cost - evaluate if needed. Alternative: simpler library approach (Spring Cloud)."
    },
    {
        "question": "What is zero trust networking?",
        "answer": "Zero trust: never trust, always verify. Traditional: trusted internal network, untrusted external. Zero trust: verify every request regardless of location. Principles: least privilege, micro-segmentation, continuous verification. Components: identity verification (MFA), device trust, network segmentation, encryption everywhere. BeyondCorp model: access based on identity + device + context. Implementation: identity-aware proxy, software-defined perimeter. Growing adoption as perimeter dissolves."
    },
    {
        "question": "What is SD-WAN?",
        "answer": "SD-WAN (Software-Defined Wide Area Network) virtualizes WAN connections. Combines multiple links (MPLS, broadband, LTE) for redundancy and cost savings. Central management of distributed sites. Features: dynamic path selection, application-aware routing, built-in security. Benefits: reduce expensive MPLS, improve cloud access, simplify management. Compare to traditional WAN: more flexible, cloud-friendly. Vendors: VMware, Cisco, Palo Alto. Often includes integrated security."
    },
    {
        "question": "How does IPv6 differ from IPv4?",
        "answer": "IPv6: 128-bit addresses (vs 32-bit), 340 undecillion addresses. Format: 2001:0db8:85a3::8a2e:0370:7334. No NAT needed - global addresses. No broadcast - uses multicast. Auto-configuration via SLAAC. Built-in IPSec support. Simplified header, no fragmentation by routers. Transition: dual-stack, tunneling (6to4), translation (NAT64). Adoption growing but IPv4 still dominant. Check support: test-ipv6.com."
    },
    {
        "question": "What is DNSSEC?",
        "answer": "DNSSEC adds cryptographic signatures to DNS records. Prevents: cache poisoning, spoofing, MITM attacks on DNS. Chain of trust from root zone. Record types: RRSIG (signatures), DNSKEY (public keys), DS (delegation signer). Validation: resolver checks signatures up chain. Doesn't encrypt queries - only authenticates responses. DNS-over-HTTPS (DoH) and DNS-over-TLS (DoT) add encryption. DNSSEC deployment still limited. Check: dnsviz.net."
    },
    {
        "question": "What is network segmentation?",
        "answer": "Network segmentation divides network into isolated zones. Benefits: limit lateral movement, contain breaches, regulatory compliance. Methods: VLANs, subnets, firewalls, SDN policies. Zones: DMZ (public-facing), internal, sensitive. Micro-segmentation: fine-grained per-workload isolation. East-west traffic (internal) often neglected vs north-south (in/out). Zero trust extends segmentation to identity-based. Design: start with data classification, map flows."
    }
]

# =============================================================================
# ERROR/TROUBLESHOOTING SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "Connection refused error",
        "error_type": "connectivity",
        "response": {
            "status": "troubleshoot",
            "meaning": "TCP connection rejected - port closed or no service listening",
            "checks": [
                "Is the service running? Check process list",
                "Is it listening on correct port/interface? netstat -tlnp",
                "Firewall blocking? Check iptables, ufw, security groups",
                "Binding to localhost only? Check service config (0.0.0.0 vs 127.0.0.1)"
            ],
            "common_causes": [
                "Service not started",
                "Service crashed",
                "Wrong port",
                "Firewall rule missing"
            ]
        }
    },
    {
        "instruction": "Connection timed out",
        "error_type": "connectivity",
        "response": {
            "status": "troubleshoot",
            "meaning": "No response received - packet dropped or routing issue",
            "checks": [
                "Can you ping the host?",
                "Traceroute - where does it stop?",
                "Firewall DROP rule? (different from REJECT)",
                "Correct IP/hostname?",
                "Security group rules in cloud?"
            ],
            "common_causes": [
                "Firewall silently dropping packets",
                "Routing issue",
                "Host down",
                "Wrong IP address"
            ]
        }
    },
    {
        "instruction": "DNS resolution failed",
        "error_type": "dns",
        "response": {
            "status": "troubleshoot",
            "checks": [
                "Check DNS server: cat /etc/resolv.conf",
                "Test with different DNS: dig @8.8.8.8 domain.com",
                "Is domain registered? Check WHOIS",
                "DNS propagation complete? Use DNS checker",
                "Local DNS cache issue? Flush cache"
            ],
            "solutions": [
                "Try alternative DNS (8.8.8.8, 1.1.1.1)",
                "Flush local DNS cache",
                "Check /etc/hosts for conflicting entries",
                "Wait for DNS propagation"
            ]
        }
    },
    {
        "instruction": "SSL certificate error",
        "error_type": "ssl",
        "response": {
            "status": "troubleshoot",
            "common_errors": {
                "Certificate expired": "Renew with certbot or provider",
                "Hostname mismatch": "Certificate doesn't match domain - get correct cert",
                "Self-signed": "Add to trust store or use CA-signed cert",
                "Incomplete chain": "Include intermediate certificates",
                "Revoked": "Get new certificate"
            },
            "diagnosis": "openssl s_client -connect host:443 -servername host",
            "online_tools": "SSL Labs test at ssllabs.com/ssltest"
        }
    },
    {
        "instruction": "Network unreachable error",
        "error_type": "routing",
        "response": {
            "status": "troubleshoot",
            "meaning": "No route to destination network",
            "checks": [
                {"command": "ip route", "purpose": "Check routing table"},
                {"command": "ip route get <dest-ip>", "purpose": "See which route would be used"},
                {"command": "cat /etc/resolv.conf", "purpose": "DNS might be failing"},
                {"command": "ip addr", "purpose": "Check interface has IP"}
            ],
            "common_causes": [
                "Default gateway not set",
                "Interface down or no IP assigned",
                "VPN disconnected",
                "Routing table corrupted"
            ],
            "solutions": [
                "Set default route: sudo ip route add default via <gateway-ip>",
                "Bring up interface: sudo ip link set eth0 up",
                "Request DHCP: sudo dhclient eth0",
                "Restart networking: sudo systemctl restart networking"
            ]
        }
    },
    {
        "instruction": "High latency/packet loss to specific host",
        "error_type": "performance",
        "response": {
            "status": "troubleshoot",
            "diagnosis_commands": [
                {"command": "mtr <host>", "purpose": "Combined ping + traceroute, shows loss per hop"},
                {"command": "ping -c 100 <host>", "purpose": "Check packet loss percentage"},
                {"command": "traceroute <host>", "purpose": "See network path"},
                {"command": "iperf3 -c <host>", "purpose": "Test bandwidth"}
            ],
            "common_causes": [
                "Congested network link",
                "ISP issues",
                "Distance (physics)",
                "Bad peering between providers",
                "Overloaded router/firewall"
            ],
            "solutions": {
                "isp_issue": "Contact ISP with traceroute evidence",
                "local_congestion": "Check bandwidth usage, QoS",
                "routing": "Try VPN to change route",
                "wifi": "Try wired connection"
            }
        }
    },
    {
        "instruction": "MTU size issues causing connection problems",
        "error_type": "configuration",
        "response": {
            "status": "troubleshoot",
            "symptoms": [
                "Connection established but no data flows",
                "Small packets work, large packets fail",
                "Works locally, fails across VPN/tunnel"
            ],
            "diagnosis": {
                "linux": "ping -M do -s 1472 <host> (reduce size until works)",
                "windows": "ping -f -l 1472 <host>",
                "explanation": "1472 + 28 byte header = 1500 standard MTU"
            },
            "common_causes": [
                "VPN/tunnel overhead reduces effective MTU",
                "Path has smaller MTU device",
                "PMTUD blocked by firewall"
            ],
            "solutions": [
                "Reduce interface MTU: sudo ip link set eth0 mtu 1400",
                "Enable TCP MSS clamping on firewall",
                "Allow ICMP 'fragmentation needed' through firewall"
            ]
        }
    },
    {
        "instruction": "Port already in use error",
        "error_type": "application",
        "response": {
            "status": "troubleshoot",
            "meaning": "Another process is bound to the port",
            "find_process": {
                "linux": "sudo lsof -i :<port> or sudo netstat -tlnp | grep <port>",
                "windows": "netstat -ano | findstr :<port> then tasklist /FI \"PID eq <pid>\"",
                "powershell": "Get-Process -Id (Get-NetTCPConnection -LocalPort <port>).OwningProcess"
            },
            "solutions": [
                "Stop the existing process",
                "Use different port for your application",
                "Wait for TIME_WAIT to expire if recently stopped",
                "Use SO_REUSEADDR socket option in application"
            ],
            "time_wait_note": "After closing connection, port stays in TIME_WAIT ~60 seconds"
        }
    },
    {
        "instruction": "WebSocket connection dropping randomly",
        "error_type": "application",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "Proxy/load balancer timeout (usually 60s idle)",
                "Firewall closing idle connections",
                "Client network change (mobile)",
                "Server restarts"
            ],
            "solutions": {
                "ping_pong": "Implement WebSocket ping/pong keep-alive (every 30s)",
                "proxy_config": "Increase proxy timeout: proxy_read_timeout 3600s (nginx)",
                "reconnection": "Implement automatic reconnection with exponential backoff",
                "load_balancer": "Enable sticky sessions if multiple backend servers"
            },
            "nginx_config": "proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection 'upgrade';"
        }
    },
    {
        "instruction": "CORS errors in browser",
        "error_type": "security",
        "response": {
            "status": "server_config_needed",
            "explanation": "Browser blocks cross-origin requests unless server explicitly allows",
            "error_types": {
                "preflight_fail": "OPTIONS request blocked or missing headers",
                "origin_not_allowed": "Access-Control-Allow-Origin doesn't include your origin",
                "credentials_fail": "credentials:true needs explicit origin, not *"
            },
            "server_headers_needed": {
                "Access-Control-Allow-Origin": "https://your-frontend.com or * (not with credentials)",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Credentials": "true (if sending cookies)"
            },
            "common_mistakes": [
                "Using * with credentials",
                "Not handling OPTIONS preflight",
                "Missing headers in non-simple requests"
            ]
        }
    },
    {
        "instruction": "VPN connection failing",
        "error_type": "vpn",
        "response": {
            "status": "troubleshoot",
            "common_errors": {
                "authentication_failed": "Check credentials, certificate validity",
                "connection_timed_out": "Firewall blocking VPN ports",
                "tls_error": "Certificate expired or untrusted",
                "route_conflict": "Overlapping subnets between VPN and local"
            },
            "diagnosis": {
                "openvpn": "openvpn --config client.ovpn --verb 4",
                "wireguard": "sudo wg show; journalctl -u wg-quick@wg0",
                "ipsec": "sudo ipsec statusall"
            },
            "port_check": {
                "openvpn": "UDP 1194 or TCP 443",
                "wireguard": "UDP 51820",
                "ipsec": "UDP 500, 4500"
            },
            "common_fixes": [
                "Try TCP if UDP blocked",
                "Update VPN client",
                "Regenerate certificates if expired",
                "Check server logs for more detail"
            ]
        }
    },
    {
        "instruction": "Cannot access website but ping works",
        "error_type": "application_layer",
        "response": {
            "status": "troubleshoot",
            "meaning": "Network connectivity OK, but application layer failing",
            "checks": [
                {"test": "TCP connection", "command": "nc -zv host 80 or telnet host 80"},
                {"test": "HTTP request", "command": "curl -v http://host/"},
                {"test": "DNS for correct IP", "command": "nslookup/dig website.com"},
                {"test": "Proxy settings", "check": "HTTP_PROXY environment variable"}
            ],
            "common_causes": [
                "Web server not running (ping works, HTTP doesn't)",
                "Firewall allows ICMP but blocks TCP 80/443",
                "Wrong port",
                "Host header issues (virtual hosting)",
                "Proxy misconfiguration"
            ],
            "solutions": [
                "Check if web service is running on server",
                "Verify firewall allows HTTP/HTTPS",
                "Test with curl/wget not just browser"
            ]
        }
    },
    {
        "instruction": "SSH connection very slow to establish",
        "error_type": "ssh",
        "response": {
            "status": "troubleshoot",
            "common_causes": [
                "Reverse DNS lookup (server looking up client IP)",
                "GSSAPI authentication timing out",
                "Slow key exchange algorithms"
            ],
            "diagnosis": "ssh -vvv user@host (verbose shows where it stalls)",
            "solutions": {
                "reverse_dns": "On server, set UseDNS no in /etc/ssh/sshd_config",
                "gssapi": "On client, ssh -o GSSAPIAuthentication=no user@host",
                "permanent_fix": "Add to ~/.ssh/config: Host * GSSAPIAuthentication no"
            },
            "other_checks": [
                "Large ~/.ssh/authorized_keys file (many keys)",
                "Slow authentication methods tried first"
            ]
        }
    },
    {
        "instruction": "Intermittent network connectivity issues",
        "error_type": "infrastructure",
        "response": {
            "status": "troubleshoot",
            "systematic_approach": [
                {"step": 1, "check": "Is it time-based?", "tools": "Review when issues occur"},
                {"step": 2, "check": "Is it load-based?", "tools": "Monitor bandwidth, CPU on network devices"},
                {"step": 3, "check": "Which path?", "tools": "mtr over time, smokeping"},
                {"step": 4, "check": "Hardware issue?", "tools": "Check cables, switch port lights/errors"}
            ],
            "common_causes": [
                "Duplex mismatch (half vs full)",
                "Spanning tree reconvergence",
                "Overloaded network device",
                "Bad cable/NIC",
                "Wireless interference"
            ],
            "monitoring": [
                "Set up continuous monitoring (Nagios, Zabbix)",
                "Log network device stats",
                "Use smokeping for latency graphing"
            ]
        }
    }
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    examples = []
    for task in NETWORKING_TASKS + WINDOWS_NETWORKING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    return examples

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts]

def generate_error_examples() -> List[Dict]:
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

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Networking Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} tool examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "networking.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()

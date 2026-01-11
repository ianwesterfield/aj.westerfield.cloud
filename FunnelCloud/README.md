# FunnelCloud Agent

> **FunnelCloud** is the distributed task execution layer for AJ. It enables remote agents on Windows, Linux, or macOS machines to execute tasks on behalf of the orchestrator.

---

## Overview

FunnelCloud extends AJ's capabilities beyond Docker containers to any machine on your network:

```
┌─────────────────────────────────────────────────────────────────┐
│                         AJ Orchestrator                         │
│                    (Docker - layers/orchestrator)               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ gRPC (mTLS)
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ FunnelCloud   │ │ FunnelCloud   │ │ FunnelCloud   │
    │ Agent         │ │ Agent         │ │ Agent         │
    │ (Windows)     │ │ (Linux)       │ │ (macOS)       │
    │ dev-workstation │ r730xd       │ │ build-server  │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### Key Features

- **UDP Discovery**: Agents announce themselves on the network (port 41420)
- **gRPC Task Execution**: Secure RPC for task submission and results (port 41235)
- **mTLS Security**: Certificate-based mutual authentication
- **Windows Service**: Runs as a background service with auto-start

---

## Architecture

### Components

| Component              | Purpose                             | Technology              |
| ---------------------- | ----------------------------------- | ----------------------- |
| **FunnelCloud.Agent**  | Task execution service              | .NET 8 / gRPC / Kestrel |
| **FunnelCloud.Shared** | Common contracts                    | .NET 8 class library    |
| **scripts/**           | Certificate & deployment automation | PowerShell              |

### Network Ports

| Port  | Protocol | Purpose                      |
| ----- | -------- | ---------------------------- |
| 41420 | UDP      | Discovery broadcast/response |
| 41235 | TCP      | gRPC task execution (mTLS)   |

### Security Model

```
┌──────────────────────────────────────────────────────────────┐
│                     Certificate Authority                     │
│                    (FunnelCloud/certs/ca/)                   │
│                                                              │
│  ca.crt          - CA public certificate                    │
│  ca.key          - CA private key (keep secure!)            │
│  ca-fingerprint.txt - SHA256 fingerprint for pinning        │
└──────────────────────────────────────────────────────────────┘
                              │
                    Signs agent certificates
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ dev-workstation │   │    r730xd     │     │ build-server  │
│ agent.pfx      │    │ agent.pfx     │     │ agent.pfx     │
│ agent-fingerprint │ │ agent-fingerprint │ │ agent-fingerprint │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## Quick Start

### Prerequisites

- **Build Server** (your development workstation):
  - .NET 8 SDK
  - OpenSSL (comes with Git for Windows)
  - PowerShell 5.1+
- **Client Machines** (where agents will run):
  - PowerShell Remoting enabled
  - Administrator access
  - NSSM (installed automatically)

### Step 1: Create the Certificate Authority (One Time)

On your build server, create the CA that will sign all agent certificates:

```powershell
cd C:\Code\aj.westerfield.cloud\FunnelCloud\scripts
.\New-CACertificate.ps1
```

This creates:

- `certs/ca/ca.crt` - CA certificate
- `certs/ca/ca.key` - CA private key (protect this!)
- `certs/ca/ca-fingerprint.txt` - SHA256 fingerprint

### Step 2: Enable PowerShell Remoting (Build Server)

On your build server, enable remoting so clients can trigger builds:

```powershell
Enable-PSRemoting -Force
```

### Step 3: Configure Client Trust (Each Client)

On each client machine, add the build server to TrustedHosts:

```powershell
# Run as Administrator on the CLIENT machine
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "BUILD_SERVER_NAME" -Force
```

Or use the setup script:

```powershell
.\Setup-FunnelCloudClient.ps1 -BuildServer "ians-r16"
```

### Step 4: Deploy Agent (From Client)

On the client machine, run the deployment script:

```powershell
# Copy the script to the client first, then run:
.\Deploy-FunnelCloudAgent.ps1 -BuildServer "ians-r16"
```

This will:

1. Connect to build server via PowerShell Remoting
2. Generate a unique certificate for this agent
3. Build the agent with embedded certificate
4. Download and install as a Windows service

---

## Scripts Reference

### New-CACertificate.ps1

Creates the Certificate Authority for signing agent certificates.

```powershell
.\New-CACertificate.ps1 [-OutputPath <path>] [-ValidDays <int>] [-Force]
```

| Parameter  | Default     | Description              |
| ---------- | ----------- | ------------------------ |
| OutputPath | ../certs/ca | Where to create CA files |
| ValidDays  | 3650        | CA validity (10 years)   |
| Force      | false       | Overwrite existing CA    |

### New-AgentCertificate.ps1

Creates a signed certificate for a specific agent.

```powershell
.\New-AgentCertificate.ps1 -AgentId <name> [-CAPath <path>] [-ValidDays <int>] [-Force]
```

| Parameter | Default     | Description                    |
| --------- | ----------- | ------------------------------ |
| AgentId   | (required)  | Unique agent identifier        |
| CAPath    | ../certs/ca | Path to CA certificate         |
| ValidDays | 730         | Certificate validity (2 years) |
| Force     | false       | Overwrite existing certificate |

**Output files** (in `certs/agents/<AgentId>/`):

- `agent.key` - Private key
- `agent.crt` - Signed certificate
- `agent.pfx` - PKCS#12 bundle for .NET
- `agent-fingerprint.txt` - SHA256 fingerprint

### Setup-FunnelCloudClient.ps1

Configures a client machine for PowerShell Remoting to the build server.

```powershell
.\Setup-FunnelCloudClient.ps1 [-BuildServer <name>]
```

| Parameter   | Default  | Description              |
| ----------- | -------- | ------------------------ |
| BuildServer | ians-r16 | Build server hostname/IP |

### Deploy-FunnelCloudAgent.ps1

One-click deployment from a client machine.

```powershell
.\Deploy-FunnelCloudAgent.ps1 [-BuildServer <name>] [-AgentId <name>] [-InstallPath <path>] [-Insecure]
```

| Parameter   | Default              | Description              |
| ----------- | -------------------- | ------------------------ |
| BuildServer | ians-r16             | Build server hostname/IP |
| AgentId     | $env:COMPUTERNAME    | Unique agent identifier  |
| InstallPath | C:\FunnelCloud\Agent | Local installation path  |
| Insecure    | false                | Skip mTLS (testing only) |

---

## Manual Installation

If you prefer manual installation over the deployment script:

### 1. Generate Certificate

On the build server:

```powershell
cd C:\Code\aj.westerfield.cloud\FunnelCloud\scripts
.\New-AgentCertificate.ps1 -AgentId "my-machine"
```

### 2. Build Agent

```powershell
cd C:\Code\aj.westerfield.cloud\FunnelCloud\FunnelCloud.Agent
dotnet publish -c Release -r win-x64 --self-contained -o C:\FunnelCloud\Agent
```

### 3. Copy Certificates

```powershell
# Copy to target machine
Copy-Item "certs\agents\my-machine\agent.pfx" -Destination "C:\FunnelCloud\Agent\Certificates\"
Copy-Item "certs\ca\ca-fingerprint.txt" -Destination "C:\FunnelCloud\Agent\Certificates\"
```

### 4. Install Service

```powershell
# On target machine (as Administrator)
nssm install FunnelCloudAgent "C:\FunnelCloud\Agent\FunnelCloud.Agent.exe"
nssm set FunnelCloudAgent AppDirectory "C:\FunnelCloud\Agent"
nssm set FunnelCloudAgent AppEnvironmentExtra "FUNNEL_CERT_PATH=C:\FunnelCloud\Agent\Certificates\agent.pfx" "FUNNEL_CERT_PASSWORD=funnelcloud"
nssm set FunnelCloudAgent Start SERVICE_AUTO_START
nssm start FunnelCloudAgent
```

---

## Service Management

### View Service Status

```powershell
Get-Service FunnelCloudAgent
```

### View Logs

```powershell
Get-Content "C:\FunnelCloud\Agent\logs\stdout.log" -Tail 50 -Wait
```

### Restart Service

```powershell
Restart-Service FunnelCloudAgent
```

### Stop Service

```powershell
Stop-Service FunnelCloudAgent
```

### Uninstall Service

```powershell
nssm stop FunnelCloudAgent
nssm remove FunnelCloudAgent confirm
```

---

## Insecure Mode (Testing Only)

For initial testing without certificates:

```powershell
# Deploy without mTLS
.\Deploy-FunnelCloudAgent.ps1 -BuildServer "ians-r16" -Insecure

# Or run manually
$env:FUNNEL_INSECURE = "true"
.\FunnelCloud.Agent.exe
```

**⚠️ Warning**: Insecure mode disables all authentication. Use only for testing on isolated networks.

---

## Troubleshooting

### Agent not discovered?

1. Check firewall allows UDP 41420 and TCP 41235
2. Verify agent is running: `Get-Service FunnelCloudAgent`
3. Check logs: `Get-Content "C:\FunnelCloud\Agent\logs\stderr.log" -Tail 50`

### "Can't connect to build server"?

1. Verify PowerShell Remoting: `Test-WSMan -ComputerName BUILD_SERVER`
2. Check TrustedHosts: `Get-Item WSMan:\localhost\Client\TrustedHosts`
3. Verify firewall allows WinRM (TCP 5985)

### Certificate errors?

1. Verify CA exists: `Test-Path "certs\ca\ca.crt"`
2. Verify agent cert: `Test-Path "certs\agents\AGENT_ID\agent.pfx"`
3. Check certificate dates: `openssl x509 -in agent.crt -noout -dates`

### Service won't start?

1. Check Windows Event Viewer: `eventvwr.msc` → Windows Logs → Application
2. Try running manually: `.\FunnelCloud.Agent.exe`
3. Verify executable exists: `Test-Path "C:\FunnelCloud\Agent\FunnelCloud.Agent.exe"`

---

## Development

### Project Structure

```
FunnelCloud/
├── certs/
│   ├── ca/                    # Certificate Authority
│   │   ├── ca.crt
│   │   ├── ca.key
│   │   └── ca-fingerprint.txt
│   └── agents/                # Per-agent certificates
│       ├── dev-workstation/
│       └── r730xd/
├── FunnelCloud.Agent/         # Main agent executable
│   ├── Program.cs
│   ├── TrustConfig.cs
│   ├── Services/
│   │   ├── DiscoveryListener.cs
│   │   ├── GrpcServerHost.cs
│   │   ├── TaskServiceImpl.cs
│   │   └── TaskExecutor.cs
│   └── Protos/
│       └── task_service.proto
├── FunnelCloud.Shared/        # Shared contracts
│   └── Contracts/
└── scripts/                   # Deployment automation
    ├── New-CACertificate.ps1
    ├── New-AgentCertificate.ps1
    ├── Setup-FunnelCloudClient.ps1
    └── Deploy-FunnelCloudAgent.ps1
```

### Building

```powershell
cd FunnelCloud
dotnet build
dotnet test
```

### Debugging

Run with verbose logging:

```powershell
$env:ASPNETCORE_ENVIRONMENT = "Development"
$env:Logging__LogLevel__Default = "Debug"
.\FunnelCloud.Agent.exe
```

---

## Integration with AJ

The orchestrator discovers and communicates with agents automatically:

```python
# layers/orchestrator/services/agent_discovery.py
async def discover_agents() -> List[AgentInfo]:
    """Discover all FunnelCloud agents on the network."""
    # UDP broadcast on port 41420
    # Returns list of agents with capabilities
```

```python
# layers/orchestrator/services/grpc_client.py
async def execute_remote_task(agent: AgentInfo, task: TaskRequest) -> TaskResult:
    """Execute a task on a remote agent via gRPC."""
    # mTLS connection to port 41235
    # Returns execution result
```

---

## Security Considerations

1. **Protect the CA private key** (`ca.key`) - if compromised, all agent identities can be forged
2. **Use unique agent IDs** - each machine should have its own certificate
3. **Rotate certificates** before expiration (default: 2 years)
4. **Restrict network access** - only allow gRPC traffic from known orchestrator IPs
5. **Enable mTLS in production** - never use insecure mode outside testing

---

_Last Updated: January 4, 2026_

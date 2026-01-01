# FunnelCloud + Mesosync Design Session
**Date:** December 31, 2025

## Naming Hierarchy

| Name | Role | Technology |
|------|------|------------|
| **AJ** | User-facing persona (Open WebUI) | Open WebUI + filters |
| **Mesosync** | System brand for the reasoning platform | Python, FastAPI, Docker |
| **FunnelCloud** | Distributed execution agents | .NET 8, PowerShell Core |

*Concept: A mesoscale convective system (Mesosync) coordinates and spawns funnel clouds (FunnelCloud agents) that touch down on target systems.*

---

## Architecture Decisions

### 1. Layer Naming
- **Keep functional names** (`orchestrator`, `pragmatics`, etc.) — don't rename folders to "mesosync"
- "Mesosync" is the brand, not a folder rename

### 2. Agent Trust Model
**Decision:** mTLS + build-time CA fingerprint pinning

```
BUILD TIME:
1. Mesosync generates internal CA (aj-internal-ca.crt)
2. For each agent: generate keypair, sign cert with CA
3. Bake into agent binary:
   - agent.pfx (cert + key)
   - aj-fingerprint (SHA256 of CA cert)
   - aj-endpoint (https://aj.westerfield.cloud)

RUNTIME:
1. TLS handshake (wildcard cert for transport)
2. Agent validates: SHA256(server cert) == baked fingerprint
3. Agent sends client cert (mTLS)
4. Mesosync validates: agent cert signed by its CA
```

**Why not just UUID?** UUIDs can be stolen; private keys can't.

### 3. Agent Discovery
**Decision:** On-demand UDP broadcast with lazy re-discovery

```
Session start → UDP broadcast "who's alive?" → Agents respond (50-200ms) →
Orchestrator caches available platforms → Reasoning begins

Execute step → Agent unreachable?
     ↓ Yes
Re-discover → Retry with new agent list
     ↓ Still no agent?
Report to user: "No Windows agent available for this task"
```

**Why not heartbeats?** UDP discovery takes ~100-500ms. LLM inference takes seconds. Discovery latency is noise. Heartbeats add complexity and stale state risk.

### 4. Command Guardrails
**Decision:** Intent classification lives in Mesosync (AJ), NOT in agents

FunnelCloud agents are "truly dumb" — they execute whatever Mesosync sends. All intelligence (including safety classification) stays centralized.

**Blocked intents:**
- `remote-exec` — Commands targeting other machines
- `install-software` — Package installs, downloads
- `modify-security` — Firewall, permissions, registry security
- `privilege-escalation` — sudo, runas, elevation

### 5. Platform Specialists
YAML profiles in `layers/orchestrator/profiles/`:
- `windows-enterprise.yaml` — PowerShell, AD, Windows networking
- `linux-server.yaml` — bash, systemd, ip/ss
- `macos-admin.yaml` — launchctl, brew, defaults, dscl

---

## Implementation Steps

### Phase 1: Certificate Infrastructure
- [ ] Create `scripts/mesosync-ca/` with CA generation tooling
- [ ] Script to generate agent certs signed by CA
- [ ] Fingerprint extraction for build-time binding

### Phase 2: FunnelCloud.Agent (.NET 8)
```
FunnelCloud.Agent/
├── Program.cs                 # Minimal API setup
├── FunnelCloud.Agent.csproj
├── appsettings.json
├── Services/
│   ├── PowerShellExecutor.cs  # In-process pwsh via System.Management.Automation
│   ├── CapabilityProber.cs    # Detects AD, Docker, workspaces, etc.
│   └── AjTrustValidator.cs    # mTLS + fingerprint validation
└── Api/
    ├── CapabilitiesEndpoint.cs
    └── ExecuteEndpoint.cs
```

**Endpoints:**
- `GET /capabilities` — Returns platform info, available tools, probed resources
- `POST /execute` — Runs command, returns stdout/stderr/exit code

### Phase 3: Mesosync Integration
- [ ] Add `agent_discovery.py` — UDP broadcast, collect responses, stateless per-request
- [ ] Add `agent_dispatcher.py` — mTLS connection pool, command routing
- [ ] Extend `tool_dispatcher.py` with `remote_execute` tool type

### Phase 4: Command Intent Classifier
- [ ] Train or use small model (phi3:mini) for command classification
- [ ] Categories: `local-query`, `local-modify`, `remote-exec`, `install-software`, `modify-security`
- [ ] Integrate into orchestrator planning phase

### Phase 5: Platform Profiles
- [ ] Create YAML schema for platform profiles
- [ ] Windows, Linux, macOS base profiles
- [ ] Profile selection based on agent capabilities

### Phase 6: Build Pipeline
```powershell
# build-funnelcloud-agent.ps1
param(
    [string]$AgentId,
    [string]$TargetPlatform = "win-x64"
)

# 1. Generate agent cert signed by Mesosync CA
python scripts/mesosync-ca/generate_agent_cert.py --agent-id $AgentId

# 2. Get CA fingerprint
$fingerprint = (Get-FileHash -Algorithm SHA256 ./certs/mesosync-ca.crt).Hash

# 3. Build with secrets baked in
dotnet publish FunnelCloud.Agent `
    -c Release -r $TargetPlatform --self-contained `
    /p:MesosyncFingerprint=$fingerprint `
    /p:MesosyncEndpoint="https://aj.westerfield.cloud"

# 4. Bundle agent cert
Copy-Item ./certs/agent-$AgentId.pfx ./publish/
```

---

## Security Summary

| Threat | Mitigation |
|--------|------------|
| MITM intercepts commands | TLS encryption (wildcard cert) |
| Rogue Mesosync sends commands | Fingerprint pinning (agent only trusts YOUR Mesosync) |
| Rogue agent joins | mTLS (Mesosync only accepts certs it signed) |
| Stolen agent cert | Revocation list checked by Mesosync |
| Dangerous commands | Intent classification before dispatch |
| Replay attacks | Nonce/timestamp in command payload |

---

## Open Questions

1. **Agent revocation** — CRL (Certificate Revocation List) or re-deploy with new CA?
2. **WAN deployment** — UDP broadcast only works on LAN; need registration endpoint for remote agents?
3. **Multi-agent execution** — If 1 of 3 agents fails mid-task, re-discover once or let others complete?
4. **User visibility** — Show connected agents in UI? ("Connected: DESKTOP-ABC (Windows), srv-linux-01 (Ubuntu)")

---

## Session Context

This design session addressed:
1. Moving from Docker-mounted workspaces to native service + network shares
2. .NET Core for Windows enterprise focus (PowerShell Core works everywhere)
3. Distributed execution agents that self-discover via UDP broadcast
4. Centralized intelligence in Mesosync (AJ) — FunnelCloud agents are minimal executors
5. mTLS + fingerprint pinning for cryptographic trust binding
6. On-demand discovery (not heartbeats) for simplicity

**Prior completed work in this session:**
- ✅ Fixed follow-up questions bypassing orchestrator (trained classifier, added markers)
- ✅ Added anti-jargon prompts to reasoning engine
- ✅ Updated `.github/copilot-instructions.md`

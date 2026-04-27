# ⚠️ DEPRECATED

**This Python orchestrator has been replaced by the .NET 9 orchestrator.**

## Active Development

All orchestrator development is now in:

```
layers/orchestrator-dotnet/
```

## Why Deprecated?

The .NET 9 orchestrator provides:
- Better performance and type safety
- Native gRPC support for FunnelCloud agents
- Two-tier skill system (YAML deterministic + LLM-guided)
- Improved SSE streaming
- 262 unit tests

## This Directory

Retained for reference only. Do not use for new development.

## Migration

If you have code referencing the Python orchestrator:

| Old (Python) | New (.NET) |
|--------------|------------|
| `layers/orchestrator/` | `layers/orchestrator-dotnet/AJ.Orchestrator.API/` |
| `services/reasoning_engine.py` | `AJ.Orchestrator.Domain/Services/ReasoningEngine.cs` |
| `services/agent_discovery.py` | `AJ.Orchestrator.Domain/Services/AgentDiscoveryService.cs` |

See `layers/orchestrator-dotnet/README.md` for the new architecture.

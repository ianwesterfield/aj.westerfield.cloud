using System.Collections.Concurrent;
using System.Net.Http.Json;
using AJ.Shared.Contracts;

namespace AJ.Orchestrator.Services;

/// <summary>
/// Service for discovering FunnelCloud agents via the local agent's HTTP API.
/// </summary>
public class AgentDiscoveryService : IAgentDiscovery
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<AgentDiscoveryService> _logger;
    private readonly ConcurrentDictionary<string, AgentCapabilities> _agents = new();

    private const string LocalAgentUrl = "http://localhost:41421";

    public AgentDiscoveryService(
        IHttpClientFactory httpClientFactory,
        ILogger<AgentDiscoveryService> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;

        // Add localhost agent by default
        _agents["localhost"] = new AgentCapabilities
        {
            AgentId = "localhost",
            Hostname = Environment.MachineName,
            Platform = OperatingSystem.IsWindows() ? "windows" :
                       OperatingSystem.IsLinux() ? "linux" : "macos",
            Capabilities = new[] { "powershell", "dotnet", "git" },
            WorkspaceRoots = new[] { Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) },
            CertificateFingerprint = "local",
            IpAddress = "127.0.0.1"
        };
    }

    public async Task<List<AgentCapabilities>> DiscoverAgentsAsync(CancellationToken ct = default)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromSeconds(5);

            var response = await client.GetAsync($"{LocalAgentUrl}/discover-peers", ct);

            if (response.IsSuccessStatusCode)
            {
                var peers = await response.Content.ReadFromJsonAsync<List<AgentCapabilities>>(ct);

                if (peers != null)
                {
                    foreach (var peer in peers)
                    {
                        _agents[peer.AgentId] = peer;
                    }

                    _logger.LogInformation("Discovered {Count} agents", peers.Count);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to discover agents, using cached list");
        }

        return _agents.Values.ToList();
    }

    public AgentCapabilities? GetAgent(string agentId)
    {
        return _agents.TryGetValue(agentId, out var agent) ? agent : null;
    }

    public IReadOnlyList<AgentCapabilities> GetAllAgents()
    {
        return _agents.Values.ToList();
    }

    public Task RefreshAsync(CancellationToken ct = default)
    {
        return DiscoverAgentsAsync(ct);
    }
}

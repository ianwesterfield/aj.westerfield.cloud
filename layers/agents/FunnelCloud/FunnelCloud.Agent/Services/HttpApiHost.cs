using System.Net;
using System.Text.Json;
using FunnelCloud.Shared.Contracts;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace FunnelCloud.Agent.Services;

/// <summary>
/// Simple HTTP API server for the agent.
/// 
/// Provides endpoints for:
/// - /health - Health check
/// - /discover-peers - Trigger multicast discovery and return all found agents
/// 
/// This allows the orchestrator to use this agent as a discovery proxy
/// when multicast doesn't work from its network (e.g., WSL NAT, Docker bridge).
/// </summary>
public class HttpApiHost : BackgroundService
{
  private readonly ILogger<HttpApiHost> _logger;
  private readonly AgentCapabilities _capabilities;
  private readonly PeerDiscoveryService _peerDiscovery;
  private readonly int _port;
  private IHost? _host;

  public HttpApiHost(
      ILogger<HttpApiHost> logger,
      AgentCapabilities capabilities,
      PeerDiscoveryService peerDiscovery,
      int? port = null)
  {
    _logger = logger;
    _capabilities = capabilities;
    _peerDiscovery = peerDiscovery;
    _port = port ?? TrustConfig.HttpApiPort;
  }

  protected override async Task ExecuteAsync(CancellationToken stoppingToken)
  {
    _logger.LogInformation("Starting HTTP API server on port {Port}", _port);

    try
    {
      var builder = WebApplication.CreateBuilder();

      builder.Logging.ClearProviders();
      builder.Logging.AddConsole();

      builder.WebHost.ConfigureKestrel(options =>
      {
        options.Listen(IPAddress.Any, _port);
      });

      var app = builder.Build();

      // Health check endpoint
      app.MapGet("/health", () => Results.Json(new
      {
        status = "healthy",
        agentId = _capabilities.AgentId,
        hostname = _capabilities.Hostname,
        platform = _capabilities.Platform
      }));

      // Self capabilities endpoint
      app.MapGet("/capabilities", () => Results.Json(_capabilities, new JsonSerializerOptions
      {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
      }));

      // Peer discovery endpoint - this is the key feature!
      // The orchestrator calls this to discover all agents on the network
      app.MapGet("/discover-peers", async (HttpContext ctx) =>
      {
        var timeoutStr = ctx.Request.Query["timeout"].FirstOrDefault();
        var timeout = double.TryParse(timeoutStr, out var t) ? t : 2.0;

        _logger.LogInformation("Peer discovery requested from {RemoteIp} (timeout={Timeout}s)",
                  ctx.Connection.RemoteIpAddress, timeout);

        var agents = await _peerDiscovery.DiscoverPeersAsync(timeout);

        return Results.Json(new
        {
          agents = agents,
          count = agents.Count,
          discoveredBy = _capabilities.AgentId
        }, new JsonSerializerOptions
        {
          PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });
      });

      _logger.LogInformation("HTTP API server listening on port {Port}", _port);
      _logger.LogInformation("  GET /health - Health check");
      _logger.LogInformation("  GET /capabilities - This agent's capabilities");
      _logger.LogInformation("  GET /discover-peers - Discover all network agents via multicast");

      _host = app;
      await app.RunAsync(stoppingToken);
    }
    catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
    {
      _logger.LogInformation("HTTP API server shutting down");
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "HTTP API server failed");
      throw;
    }
  }

  public override async Task StopAsync(CancellationToken cancellationToken)
  {
    if (_host != null)
    {
      await _host.StopAsync(cancellationToken);
    }
    await base.StopAsync(cancellationToken);
  }
}

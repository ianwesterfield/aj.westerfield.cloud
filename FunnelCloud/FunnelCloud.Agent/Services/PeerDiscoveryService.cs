using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using FunnelCloud.Shared.Contracts;
using Microsoft.Extensions.Logging;

namespace FunnelCloud.Agent.Services;

/// <summary>
/// Service to discover peer FunnelCloud agents via UDP multicast.
/// 
/// Used by the orchestrator (via HTTP API on local agent) to discover
/// all agents on the network when multicast doesn't work from the
/// orchestrator's network (e.g., WSL NAT, Docker bridge).
/// 
/// Protocol:
/// 1. Send "FUNNEL_DISCOVER" to multicast group 239.255.77.77:41420
/// 2. Collect responses for timeout duration
/// 3. Return list of discovered AgentCapabilities
/// </summary>
public class PeerDiscoveryService
{
  private readonly ILogger<PeerDiscoveryService> _logger;
  private readonly AgentCapabilities _selfCapabilities;

  public PeerDiscoveryService(
      ILogger<PeerDiscoveryService> logger,
      AgentCapabilities selfCapabilities)
  {
    _logger = logger;
    _selfCapabilities = selfCapabilities;
  }

  /// <summary>
  /// Discover all FunnelCloud agents on the network via multicast.
  /// </summary>
  /// <param name="timeoutSeconds">How long to wait for responses</param>
  /// <returns>List of discovered agent capabilities (including self)</returns>
  public async Task<List<AgentCapabilities>> DiscoverPeersAsync(double timeoutSeconds = 2.0)
  {
    var agents = new List<AgentCapabilities>();
    var seenIds = new HashSet<string>();

    _logger.LogInformation("Starting peer discovery via multicast group {MulticastGroup}:{Port}",
        TrustConfig.MulticastGroup, TrustConfig.DiscoveryPort);

    try
    {
      using var udpClient = new UdpClient();

      // Allow address reuse
      udpClient.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);

      // Bind to any available port for receiving responses
      udpClient.Client.Bind(new IPEndPoint(IPAddress.Any, 0));
      var localPort = ((IPEndPoint)udpClient.Client.LocalEndPoint!).Port;
      _logger.LogDebug("Discovery socket bound to port {Port}", localPort);

      // Set multicast TTL for cross-subnet discovery
      udpClient.Client.SetSocketOption(SocketOptionLevel.IP, SocketOptionName.MulticastTimeToLive, 32);

      // Send discovery message to multicast group
      var message = Encoding.UTF8.GetBytes(TrustConfig.DiscoveryMagic);
      var multicastEndpoint = new IPEndPoint(IPAddress.Parse(TrustConfig.MulticastGroup), TrustConfig.DiscoveryPort);

      await udpClient.SendAsync(message, message.Length, multicastEndpoint);
      _logger.LogDebug("Sent discovery multicast to {Endpoint}", multicastEndpoint);

      // Also send to broadcast for same-subnet discovery (backup)
      try
      {
        var broadcastEndpoint = new IPEndPoint(IPAddress.Broadcast, TrustConfig.DiscoveryPort);
        udpClient.EnableBroadcast = true;
        await udpClient.SendAsync(message, message.Length, broadcastEndpoint);
        _logger.LogDebug("Sent discovery broadcast to {Endpoint}", broadcastEndpoint);
      }
      catch (Exception ex)
      {
        _logger.LogDebug("Broadcast failed (expected on some networks): {Error}", ex.Message);
      }

      // Collect responses with timeout
      var endTime = DateTime.UtcNow.AddSeconds(timeoutSeconds);
      udpClient.Client.ReceiveTimeout = (int)(timeoutSeconds * 1000);

      while (DateTime.UtcNow < endTime)
      {
        try
        {
          var remainingMs = (int)(endTime - DateTime.UtcNow).TotalMilliseconds;
          if (remainingMs <= 0) break;

          udpClient.Client.ReceiveTimeout = Math.Min(500, remainingMs);

          var result = await Task.Run(() =>
          {
            try
            {
              IPEndPoint? remoteEp = null;
              var data = udpClient.Receive(ref remoteEp);
              return (Data: data, RemoteEndPoint: remoteEp);
            }
            catch (SocketException)
            {
              return (Data: null, RemoteEndPoint: null);
            }
          });

          if (result.Data == null || result.RemoteEndPoint == null) continue;

          try
          {
            var json = Encoding.UTF8.GetString(result.Data);
            var agent = JsonSerializer.Deserialize<AgentCapabilities>(json, new JsonSerializerOptions
            {
              PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            if (agent != null && !seenIds.Contains(agent.AgentId))
            {
              seenIds.Add(agent.AgentId);
              agents.Add(agent);
              _logger.LogInformation("Discovered peer: {AgentId} at {IP} ({Platform})",
                  agent.AgentId, result.RemoteEndPoint.Address, agent.Platform);
            }
          }
          catch (JsonException ex)
          {
            _logger.LogDebug("Invalid JSON from {RemoteEndPoint}: {Error}",
                result.RemoteEndPoint, ex.Message);
          }
        }
        catch (SocketException)
        {
          // Timeout, continue
        }
      }
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Peer discovery failed");
    }

    // Always include self in the results
    if (!seenIds.Contains(_selfCapabilities.AgentId))
    {
      agents.Add(_selfCapabilities);
      _logger.LogDebug("Added self to discovery results: {AgentId}", _selfCapabilities.AgentId);
    }

    _logger.LogInformation("Peer discovery complete: found {Count} agent(s)", agents.Count);
    return agents;
  }
}

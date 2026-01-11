using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using FunnelCloud.Shared.Contracts;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace FunnelCloud.Agent.Services;

/// <summary>
/// UDP listener that responds to FunnelCloud discovery messages.
/// 
/// Protocol:
/// 1. "FUNNEL_DISCOVER" - Agent responds with its own capabilities
/// 2. "FUNNEL_DISCOVER_PEERS" - Agent does multicast discovery and returns ALL found agents
/// 
/// The DISCOVER_PEERS command allows the orchestrator to use any reachable agent
/// as a discovery proxy when multicast doesn't work from its network.
/// </summary>
public class DiscoveryListener : BackgroundService
{
  private readonly ILogger<DiscoveryListener> _logger;
  private readonly AgentCapabilities _capabilities;
  private readonly PeerDiscoveryService _peerDiscovery;
  private readonly int _port;
  private readonly string _multicastGroup;

  public DiscoveryListener(
      ILogger<DiscoveryListener> logger,
      AgentCapabilities capabilities,
      PeerDiscoveryService peerDiscovery,
      int? port = null)
  {
    _logger = logger;
    _capabilities = capabilities;
    _peerDiscovery = peerDiscovery;
    _port = port ?? TrustConfig.DiscoveryPort;
    _multicastGroup = TrustConfig.MulticastGroup;
  }

  protected override async Task ExecuteAsync(CancellationToken stoppingToken)
  {
    _logger.LogInformation(
        "Discovery listener starting on UDP port {Port}, multicast group {MulticastGroup} for agent {AgentId}",
        _port, _multicastGroup, _capabilities.AgentId);

    using var udpClient = new UdpClient();

    // Allow address reuse for multiple listeners on same machine
    udpClient.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);

    // Bind to the discovery port on all interfaces
    udpClient.Client.Bind(new IPEndPoint(IPAddress.Any, _port));

    // Join the multicast group on all network interfaces
    try
    {
      var multicastAddress = IPAddress.Parse(_multicastGroup);
      udpClient.JoinMulticastGroup(multicastAddress);
      _logger.LogInformation("Joined multicast group {MulticastGroup}", _multicastGroup);
    }
    catch (Exception ex)
    {
      _logger.LogWarning(ex, "Failed to join multicast group {MulticastGroup}, falling back to unicast only", _multicastGroup);
    }

    // Also accept direct unicast discovery (for Docker host.docker.internal)
    _logger.LogInformation("Also listening for direct unicast discovery on port {Port}", _port);

    try
    {
      while (!stoppingToken.IsCancellationRequested)
      {
        try
        {
          // Wait for incoming message (multicast or unicast)
          var result = await udpClient.ReceiveAsync(stoppingToken);
          var message = Encoding.UTF8.GetString(result.Buffer);

          _logger.LogDebug(
              "Received UDP message from {RemoteEndPoint}: {Message}",
              result.RemoteEndPoint, message);

          // Check for discovery commands
          if (message.StartsWith("FUNNEL_DISCOVER_PEERS"))
          {
            // Peer discovery proxy request - do multicast and return all agents
            await HandlePeerDiscoveryRequest(udpClient, result.RemoteEndPoint);
          }
          else if (message.StartsWith(TrustConfig.DiscoveryMagic))
          {
            // Standard self-discovery request
            await HandleDiscoveryRequest(udpClient, result.RemoteEndPoint, message);
          }
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
        {
          break;
        }
        catch (SocketException ex)
        {
          _logger.LogWarning(ex, "Socket error in discovery listener");
          await Task.Delay(1000, stoppingToken); // Brief pause before retry
        }
      }
    }
    finally
    {
      // Leave multicast group on shutdown
      try
      {
        var multicastAddress = IPAddress.Parse(_multicastGroup);
        udpClient.DropMulticastGroup(multicastAddress);
      }
      catch { /* ignore cleanup errors */ }

      _logger.LogInformation("Discovery listener stopped");
    }
  }

  private async Task HandleDiscoveryRequest(UdpClient client, IPEndPoint remoteEndPoint, string message)
  {
    _logger.LogInformation(
        "Discovery request from {RemoteEndPoint}",
        remoteEndPoint);

    try
    {
      // Serialize capabilities to JSON
      var response = JsonSerializer.Serialize(_capabilities, new JsonSerializerOptions
      {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false
      });

      var responseBytes = Encoding.UTF8.GetBytes(response);

      // Send response back to the requester (unicast)
      await client.SendAsync(responseBytes, responseBytes.Length, remoteEndPoint);

      _logger.LogDebug(
          "Sent discovery response to {RemoteEndPoint}: {AgentId}",
          remoteEndPoint, _capabilities.AgentId);
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Failed to send discovery response to {RemoteEndPoint}", remoteEndPoint);
    }
  }

  private async Task HandlePeerDiscoveryRequest(UdpClient client, IPEndPoint remoteEndPoint)
  {
    _logger.LogInformation(
        "Peer discovery proxy request from {RemoteEndPoint}",
        remoteEndPoint);

    try
    {
      // Do multicast discovery to find all peers
      var peers = await _peerDiscovery.DiscoverPeersAsync(2.0);

      _logger.LogInformation("Peer discovery found {Count} agent(s)", peers.Count);

      // Build response with all discovered agents
      var response = new
      {
        discoveredBy = _capabilities.AgentId,
        agents = peers,
        count = peers.Count
      };

      var json = JsonSerializer.Serialize(response, new JsonSerializerOptions
      {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false
      });

      var responseBytes = Encoding.UTF8.GetBytes(json);

      // UDP datagram size limit is ~65KB, but practical limit is ~1400 bytes for MTU
      // For large responses, we may need to split - but for typical agent counts this is fine
      if (responseBytes.Length > 60000)
      {
        _logger.LogWarning("Peer discovery response is very large ({Size} bytes), may be truncated", responseBytes.Length);
      }

      await client.SendAsync(responseBytes, responseBytes.Length, remoteEndPoint);

      _logger.LogDebug(
          "Sent peer discovery response to {RemoteEndPoint}: {Count} agents",
          remoteEndPoint, peers.Count);
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Failed to handle peer discovery request from {RemoteEndPoint}", remoteEndPoint);
    }
  }
}

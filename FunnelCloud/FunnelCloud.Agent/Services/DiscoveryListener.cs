using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using FunnelCloud.Shared.Contracts;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace FunnelCloud.Agent.Services;

/// <summary>
/// UDP listener that responds to Mesosync discovery broadcasts.
/// 
/// Protocol:
/// 1. Mesosync broadcasts "FUNNEL_DISCOVER" to UDP port 41234
/// 2. Agent responds with JSON-serialized AgentCapabilities
/// 3. Mesosync caches discovered agents for the conversation
/// </summary>
public class DiscoveryListener : BackgroundService
{
  private readonly ILogger<DiscoveryListener> _logger;
  private readonly AgentCapabilities _capabilities;
  private readonly int _port;

  public DiscoveryListener(
      ILogger<DiscoveryListener> logger,
      AgentCapabilities capabilities,
      int? port = null)
  {
    _logger = logger;
    _capabilities = capabilities;
    _port = port ?? TrustConfig.DiscoveryPort;
  }

  protected override async Task ExecuteAsync(CancellationToken stoppingToken)
  {
    _logger.LogInformation(
        "Discovery listener starting on UDP port {Port} for agent {AgentId}",
        _port, _capabilities.AgentId);

    using var udpClient = new UdpClient(_port);

    // Allow broadcast reception
    udpClient.EnableBroadcast = true;

    try
    {
      while (!stoppingToken.IsCancellationRequested)
      {
        try
        {
          // Wait for incoming broadcast
          var result = await udpClient.ReceiveAsync(stoppingToken);
          var message = Encoding.UTF8.GetString(result.Buffer);

          _logger.LogDebug(
              "Received UDP message from {RemoteEndPoint}: {Message}",
              result.RemoteEndPoint, message);

          // Check for discovery magic
          if (message.StartsWith(TrustConfig.DiscoveryMagic))
          {
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

      // Send response back to the requester
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
}

using System.Diagnostics;
using System.Runtime.CompilerServices;
using AJ.Orchestrator.Abstractions.Protos;
using AJ.Orchestrator.Abstractions.Services;
using AJ.Shared.Contracts;
using Grpc.Net.Client;
using Microsoft.Extensions.Logging;

namespace AJ.Orchestrator.Domain.Services;

/// <summary>
/// gRPC client for executing tasks on FunnelCloud agents.
/// Delegates to FunnelCloud agents for command execution.
/// </summary>
public class GrpcAgentClient : IGrpcAgentClient
{
  private readonly IAgentDiscovery _discovery;
  private readonly ILogger<GrpcAgentClient> _logger;
  private readonly string? _localAgentGrpcUrl;

  public GrpcAgentClient(
      IAgentDiscovery discovery,
      ILogger<GrpcAgentClient> logger)
  {
    _discovery = discovery;
    _logger = logger;

    // Pre-compute the local agent gRPC URL from the FunnelCloud HTTP URL
    // FunnelCloud HTTP is on 41421, gRPC is on 41235
    var funnelUrl = Environment.GetEnvironmentVariable("FunnelCloud__Url");
    if (!string.IsNullOrEmpty(funnelUrl))
    {
      var uri = new Uri(funnelUrl);
      _localAgentGrpcUrl = $"http://{uri.Host}:41235";
    }
  }

  public async Task<List<AgentCapabilities>> DiscoverAgentsAsync(CancellationToken ct = default)
  {
    return await _discovery.DiscoverAgentsAsync(ct);
  }

  public async Task<TaskExecutionResult> ExecuteAsync(
      string agentId,
      string command,
      int timeoutSeconds = 30,
      CancellationToken ct = default)
  {
    var stopwatch = Stopwatch.StartNew();

    try
    {
      var agent = _discovery.GetAgent(agentId);
      if (agent == null)
      {
        return new TaskExecutionResult(
            false, null, null, 1, stopwatch.ElapsedMilliseconds,
            $"Agent not found: {agentId}. Use list_agents to see available agents.");
      }

      // Build gRPC address — use agent's IP for remote, or local FunnelCloud URL for self
      var grpcAddress = GetGrpcAddress(agent, agentId);
      if (grpcAddress == null)
      {
        return new TaskExecutionResult(
            false, null, null, 1, stopwatch.ElapsedMilliseconds,
            $"Cannot determine gRPC address for agent {agentId}");
      }

      return await ExecuteViaGrpcAsync(grpcAddress, command, timeoutSeconds, ct, stopwatch);
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Failed to execute command on {AgentId}", agentId);
      return new TaskExecutionResult(
          false, null, ex.Message, 1, stopwatch.ElapsedMilliseconds,
          ex.Message);
    }
  }

  private string? GetGrpcAddress(AgentCapabilities agent, string agentId)
  {
    // For remote agents with known IP, connect directly
    if (!string.IsNullOrEmpty(agent.IpAddress))
      return $"http://{agent.IpAddress}:{agent.GrpcPort}";

    // For agents without an IP (local FunnelCloud agent), use the configured gRPC URL
    return _localAgentGrpcUrl;
  }

  private async Task<TaskExecutionResult> ExecuteViaGrpcAsync(
      string grpcAddress,
      string command,
      int timeoutSeconds,
      CancellationToken ct,
      Stopwatch stopwatch)
  {
    _logger.LogInformation("Executing via gRPC at {Address}: {Command}", grpcAddress, command);

    using var channel = GrpcChannel.ForAddress(grpcAddress);
    var client = new TaskService.TaskServiceClient(channel);

    var request = new Abstractions.Protos.TaskRequest
    {
      TaskId = Guid.NewGuid().ToString("N"),
      Type = Abstractions.Protos.TaskType.Powershell,
      Command = command,
      TimeoutSeconds = timeoutSeconds
    };

    using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
    cts.CancelAfter(TimeSpan.FromSeconds(timeoutSeconds + 5));

    var result = await client.ExecuteAsync(request, cancellationToken: cts.Token);

    stopwatch.Stop();

    return new TaskExecutionResult(
        result.Success,
        string.IsNullOrEmpty(result.Stdout) ? null : result.Stdout,
        string.IsNullOrEmpty(result.Stderr) ? null : result.Stderr,
        result.ExitCode,
        result.DurationMs > 0 ? result.DurationMs : stopwatch.ElapsedMilliseconds,
        result.ErrorCode != ErrorCode.ErrorNone && result.ErrorCode != ErrorCode.Unspecified
            ? $"Agent error: {result.ErrorCode}" : null);
  }

  public async IAsyncEnumerable<string> ExecuteStreamingAsync(
      string agentId,
      string command,
      [EnumeratorCancellation] CancellationToken ct = default)
  {
    // For all agents, delegate to non-streaming gRPC and return lines
    var result = await ExecuteAsync(agentId, command, 30, ct);
    if (result.Stdout != null)
    {
      foreach (var line in result.Stdout.Split('\n'))
      {
        yield return line;
      }
    }
    if (result.ErrorMessage != null)
    {
      yield return $"[ERROR] {result.ErrorMessage}";
    }
  }
}

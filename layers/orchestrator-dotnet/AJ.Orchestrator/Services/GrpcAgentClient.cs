using System.Diagnostics;
using System.Runtime.CompilerServices;

namespace AJ.Orchestrator.Services;

/// <summary>
/// gRPC client for executing tasks on FunnelCloud agents.
/// Falls back to local PowerShell execution for localhost.
/// </summary>
public class GrpcAgentClient : IGrpcAgentClient
{
    private readonly IAgentDiscovery _discovery;
    private readonly ILogger<GrpcAgentClient> _logger;

    public GrpcAgentClient(
        IAgentDiscovery discovery,
        ILogger<GrpcAgentClient> logger)
    {
        _discovery = discovery;
        _logger = logger;
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
            if (agentId == "localhost" || agentId == Environment.MachineName)
            {
                // Execute locally via PowerShell
                return await ExecuteLocalAsync(command, timeoutSeconds, ct);
            }

            // Find agent
            var agent = _discovery.GetAgent(agentId);
            if (agent == null)
            {
                return new TaskExecutionResult(
                    false, null, null, 1, stopwatch.ElapsedMilliseconds,
                    $"Agent not found: {agentId}");
            }

            // TODO: Implement actual gRPC call to remote agent
            // For now, return error indicating remote execution not yet implemented
            return new TaskExecutionResult(
                false, null, null, 1, stopwatch.ElapsedMilliseconds,
                $"Remote gRPC execution not yet implemented for agent: {agentId}");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to execute command on {AgentId}", agentId);
            return new TaskExecutionResult(
                false, null, ex.Message, 1, stopwatch.ElapsedMilliseconds,
                ex.Message);
        }
    }

    public async IAsyncEnumerable<string> ExecuteStreamingAsync(
        string agentId,
        string command,
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        if (agentId == "localhost" || agentId == Environment.MachineName)
        {
            await foreach (var line in ExecuteLocalStreamingAsync(command, ct))
            {
                yield return line;
            }
            yield break;
        }

        // For remote agents, fall back to non-streaming for now
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

    private async Task<TaskExecutionResult> ExecuteLocalAsync(
        string command,
        int timeoutSeconds,
        CancellationToken ct)
    {
        var stopwatch = Stopwatch.StartNew();

        var psi = new ProcessStartInfo
        {
            FileName = FindPowerShell(),
            Arguments = $"-NoProfile -NonInteractive -Command \"{EscapeCommand(command)}\"",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = Process.Start(psi);
        if (process == null)
        {
            return new TaskExecutionResult(false, null, "Failed to start PowerShell", 1, 0);
        }

        using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        cts.CancelAfter(TimeSpan.FromSeconds(timeoutSeconds));

        try
        {
            var stdoutTask = process.StandardOutput.ReadToEndAsync(cts.Token);
            var stderrTask = process.StandardError.ReadToEndAsync(cts.Token);

            await process.WaitForExitAsync(cts.Token);

            var stdout = await stdoutTask;
            var stderr = await stderrTask;

            stopwatch.Stop();

            return new TaskExecutionResult(
                process.ExitCode == 0,
                stdout.TrimEnd(),
                string.IsNullOrEmpty(stderr) ? null : stderr.TrimEnd(),
                process.ExitCode,
                stopwatch.ElapsedMilliseconds);
        }
        catch (OperationCanceledException)
        {
            try { process.Kill(entireProcessTree: true); } catch { }
            return new TaskExecutionResult(
                false, null, null, 1, stopwatch.ElapsedMilliseconds,
                $"Command timed out after {timeoutSeconds} seconds");
        }
    }

    private async IAsyncEnumerable<string> ExecuteLocalStreamingAsync(
        string command,
        [EnumeratorCancellation] CancellationToken ct)
    {
        var psi = new ProcessStartInfo
        {
            FileName = FindPowerShell(),
            Arguments = $"-NoProfile -NonInteractive -Command \"{EscapeCommand(command)}\"",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = Process.Start(psi);
        if (process == null)
        {
            yield return "[ERROR] Failed to start PowerShell";
            yield break;
        }

        while (!ct.IsCancellationRequested)
        {
            var line = await process.StandardOutput.ReadLineAsync(ct);
            if (line == null)
                break;
            yield return line;
        }

        await process.WaitForExitAsync(ct);
    }

    private static string FindPowerShell()
    {
        // Prefer pwsh (PowerShell Core) over Windows PowerShell
        var pwshPaths = new[]
        {
            "pwsh",
            @"C:\Program Files\PowerShell\7\pwsh.exe",
            "powershell"
        };

        foreach (var path in pwshPaths)
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = path,
                    Arguments = "-Version",
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var p = Process.Start(psi);
                if (p != null)
                {
                    p.WaitForExit(2000);
                    return path;
                }
            }
            catch { }
        }

        return "powershell"; // Fallback
    }

    private static string EscapeCommand(string command)
    {
        return command.Replace("\"", "\\\"");
    }
}

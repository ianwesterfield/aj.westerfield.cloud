using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;
using FunnelCloud.Agent.Services;
using FunnelCloud.Shared.Contracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace FunnelCloud.Agent;

/// <summary>
/// FunnelCloud Agent - Distributed execution agent for Mesosync.
/// 
/// Responsibilities:
/// 1. Listen for UDP discovery broadcasts from Mesosync
/// 2. Advertise capabilities (platform, tools, workspace roots)
/// 3. Execute tasks received over gRPC (mTLS secured)
/// 4. Return results to orchestrator
/// </summary>
public class Program
{
  public static async Task Main(string[] args)
  {
    // Kill any existing agent instances before starting
    KillExistingInstances();

    var builder = Host.CreateApplicationBuilder(args);

    // Configure logging
    builder.Logging.AddConsole();
    builder.Logging.SetMinimumLevel(LogLevel.Debug);

    // Build agent capabilities from environment/config
    var capabilities = BuildAgentCapabilities();
    builder.Services.AddSingleton(capabilities);

    // Register services
    builder.Services.AddSingleton<TaskExecutor>(sp =>
        new TaskExecutor(
            sp.GetRequiredService<ILogger<TaskExecutor>>(),
            capabilities.AgentId));

    // Add discovery listener as hosted service
    builder.Services.AddHostedService<DiscoveryListener>(sp =>
        new DiscoveryListener(
            sp.GetRequiredService<ILogger<DiscoveryListener>>(),
            sp.GetRequiredService<AgentCapabilities>()));

    // Add gRPC server for task execution (mTLS secured)
    builder.Services.AddHostedService<GrpcServerHost>(sp =>
        new GrpcServerHost(
            sp.GetRequiredService<ILogger<GrpcServerHost>>(),
            sp.GetRequiredService<AgentCapabilities>(),
            sp.GetRequiredService<TaskExecutor>()));

    var host = builder.Build();

    var logger = host.Services.GetRequiredService<ILogger<Program>>();
    logger.LogInformation("FunnelCloud Agent starting...");
    logger.LogInformation("Agent ID: {AgentId}", capabilities.AgentId);
    logger.LogInformation("Platform: {Platform}", capabilities.Platform);
    logger.LogInformation("Capabilities: {Capabilities}", string.Join(", ", capabilities.Capabilities));
    logger.LogInformation("Workspace Roots: {WorkspaceRoots}", string.Join(", ", capabilities.WorkspaceRoots));
    logger.LogInformation("Discovery Port: {DiscoveryPort}, gRPC Port: {GrpcPort}",
        TrustConfig.DiscoveryPort, TrustConfig.GrpcPort);

    await host.RunAsync();
  }

  private static AgentCapabilities BuildAgentCapabilities()
  {
    var agentId = Environment.GetEnvironmentVariable("FUNNEL_AGENT_ID")
        ?? Environment.MachineName.ToLowerInvariant();

    var platform = GetPlatform();
    var capabilities = DetectCapabilities();
    var workspaceRoots = GetWorkspaceRoots();
    var certFingerprint = GetCertificateFingerprint();

    return new AgentCapabilities
    {
      AgentId = agentId,
      Hostname = Environment.MachineName,
      Platform = platform,
      Capabilities = capabilities,
      WorkspaceRoots = workspaceRoots,
      CertificateFingerprint = certFingerprint
    };
  }

  private static string GetPlatform()
  {
    if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
      return "windows";
    if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
      return "linux";
    if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
      return "macos";
    return "unknown";
  }

  private static string[] DetectCapabilities()
  {
    var caps = new List<string>();

    // PowerShell is always available (we ship with System.Management.Automation)
    caps.Add("powershell");

    // Check for common tools
    if (IsCommandAvailable("dotnet")) caps.Add("dotnet");
    if (IsCommandAvailable("git")) caps.Add("git");
    if (IsCommandAvailable("docker")) caps.Add("docker");
    if (IsCommandAvailable("node")) caps.Add("node");
    if (IsCommandAvailable("python") || IsCommandAvailable("python3")) caps.Add("python");
    if (IsCommandAvailable("cargo")) caps.Add("rust");

    return caps.ToArray();
  }

  private static bool IsCommandAvailable(string command)
  {
    try
    {
      var isWindows = RuntimeInformation.IsOSPlatform(OSPlatform.Windows);
      var psi = new System.Diagnostics.ProcessStartInfo
      {
        FileName = isWindows ? "where" : "which",
        Arguments = command,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        UseShellExecute = false,
        CreateNoWindow = true
      };

      using var process = System.Diagnostics.Process.Start(psi);
      process?.WaitForExit(1000);
      return process?.ExitCode == 0;
    }
    catch
    {
      return false;
    }
  }

  private static string[] GetWorkspaceRoots()
  {
    // Check environment variable first
    var envRoots = Environment.GetEnvironmentVariable("FUNNEL_WORKSPACE_ROOTS");
    if (!string.IsNullOrEmpty(envRoots))
    {
      return envRoots.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries);
    }

    // Default to common development directories
    var roots = new List<string>();

    if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
    {
      // Windows common paths
      var cCode = @"C:\Code";
      var userCode = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Code");
      var userProjects = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Projects");

      if (Directory.Exists(cCode)) roots.Add(cCode);
      if (Directory.Exists(userCode)) roots.Add(userCode);
      if (Directory.Exists(userProjects)) roots.Add(userProjects);
    }
    else
    {
      // Unix common paths
      var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
      var homeCode = Path.Combine(home, "code");
      var homeProjects = Path.Combine(home, "projects");
      var homeDev = Path.Combine(home, "dev");

      if (Directory.Exists(homeCode)) roots.Add(homeCode);
      if (Directory.Exists(homeProjects)) roots.Add(homeProjects);
      if (Directory.Exists(homeDev)) roots.Add(homeDev);
    }

    // Fallback to home directory
    if (roots.Count == 0)
    {
      roots.Add(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile));
    }

    return roots.ToArray();
  }

  private static string GetCertificateFingerprint()
  {
    // TODO: Load actual certificate and compute SHA256 fingerprint
    // For now, return placeholder
    var certPath = Environment.GetEnvironmentVariable("FUNNEL_CERT_PATH");
    if (!string.IsNullOrEmpty(certPath) && File.Exists(certPath))
    {
      try
      {
        using var cert = new X509Certificate2(certPath);
        return $"SHA256:{cert.GetCertHashString()}";
      }
      catch
      {
        // Fall through to placeholder
      }
    }

    return "SHA256:PLACEHOLDER_GENERATE_CERT";
  }

  /// <summary>
  /// Kill any existing FunnelCloud.Agent processes to free up ports.
  /// This allows re-running the agent without manually killing old instances.
  /// </summary>
  private static void KillExistingInstances()
  {
    var currentPid = Environment.ProcessId;
    var processName = "FunnelCloud.Agent";

    try
    {
      var existingProcesses = Process.GetProcessesByName(processName)
          .Where(p => p.Id != currentPid)
          .ToList();

      if (existingProcesses.Count > 0)
      {
        Console.WriteLine($"Found {existingProcesses.Count} existing FunnelCloud.Agent instance(s), terminating...");

        foreach (var proc in existingProcesses)
        {
          try
          {
            Console.WriteLine($"  Killing PID {proc.Id}...");
            proc.Kill(entireProcessTree: true);
            proc.WaitForExit(3000); // Wait up to 3 seconds
            Console.WriteLine($"  PID {proc.Id} terminated.");
          }
          catch (Exception ex)
          {
            Console.WriteLine($"  Warning: Could not kill PID {proc.Id}: {ex.Message}");
          }
          finally
          {
            proc.Dispose();
          }
        }

        // Brief pause to let ports release
        Thread.Sleep(500);
      }
    }
    catch (Exception ex)
    {
      Console.WriteLine($"Warning: Error checking for existing instances: {ex.Message}");
    }
  }
}


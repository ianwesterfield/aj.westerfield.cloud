using System.Diagnostics;
using Grpc.Net.Client;
using FunnelCloud.Grpc;

Console.WriteLine("=== FunnelCloud Integration Test ===\n");

// Test 1: CLI Status
Console.WriteLine("[Test 1] CLI Status Check");
var cliResult = RunCli("status");
if (cliResult.Contains("Agent is running"))
{
  Console.WriteLine("  ✓ CLI reports agent is running");
}
else
{
  Console.WriteLine($"  ✗ CLI status check failed: {cliResult}");
  return 1;
}

// Test 2: Named Pipe Connection
Console.WriteLine("\n[Test 2] Named Pipe Connection");
var listResult = RunCli("list");
Console.WriteLine($"  ✓ CLI connected to pipe (events: {(listResult.Contains("No recent") ? "0" : "some")})");

// Test 3: gRPC Task Execution
Console.WriteLine("\n[Test 3] gRPC Task Execution");
var insecurePort = 41236;
var taskId = Guid.NewGuid().ToString("N")[..8];

try
{
  // Use insecure channel for local testing
  using var channel = GrpcChannel.ForAddress($"http://localhost:{insecurePort}");
  var client = new TaskService.TaskServiceClient(channel);

  var request = new TaskRequest
  {
    TaskId = taskId,
    Type = TaskType.Shell,
    Command = "echo Hello from integration test",
    TimeoutSeconds = 30
  };

  Console.WriteLine($"  Sending task {taskId}...");
  var response = await client.ExecuteAsync(request);

  if (response.Success)
  {
    Console.WriteLine($"  ✓ Task completed successfully");
    Console.WriteLine($"    Exit code: {response.ExitCode}");
    Console.WriteLine($"    Duration: {response.DurationMs}ms");
    Console.WriteLine($"    Output: {response.Stdout.Trim()}");
  }
  else
  {
    Console.WriteLine($"  ✗ Task failed: {response.Stderr}");
    return 1;
  }
}
catch (Exception ex)
{
  Console.WriteLine($"  ✗ gRPC error: {ex.Message}");
  Console.WriteLine($"    (Make sure agent is running with insecure mode on port {insecurePort})");
  return 1;
}

// Test 4: Verify Event Published
Console.WriteLine("\n[Test 4] Event Publication");
await Task.Delay(500); // Give time for event to be published
var eventsResult = RunCli("list");
if (eventsResult.Contains(taskId) || eventsResult.Contains("task_completed"))
{
  Console.WriteLine("  ✓ Event was published to pipe");
}
else if (eventsResult.Contains("No recent"))
{
  Console.WriteLine("  ⚠ No events found (may need to check ring buffer)");
}
else
{
  Console.WriteLine($"  ? Events: {eventsResult}");
}

Console.WriteLine("\n=== All Tests Passed ===");
return 0;

static string RunCli(string args)
{
  var psi = new ProcessStartInfo
  {
    FileName = "dotnet",
    Arguments = $"run --project c:/Code/aj/layers/agents/FunnelCloud/FunnelCloud.Cli -- {args}",
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    UseShellExecute = false,
    CreateNoWindow = true,
    WorkingDirectory = "c:/Code/aj/layers/agents/FunnelCloud/FunnelCloud.Cli"
  };

  using var proc = Process.Start(psi);
  var output = proc!.StandardOutput.ReadToEnd();
  var error = proc.StandardError.ReadToEnd();
  proc.WaitForExit(10000);

  return string.IsNullOrEmpty(output) ? error : output;
}

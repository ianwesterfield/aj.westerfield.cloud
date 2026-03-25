using System.Net.Http.Json;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using AJ.Orchestrator.Abstractions.Models;
using AJ.Orchestrator.Abstractions.Services;

namespace AJ.Orchestrator.Services;

/// <summary>
/// Reasoning engine that coordinates with Ollama for step generation.
/// </summary>
public class ReasoningEngine : IReasoningEngine
{
  private readonly IHttpClientFactory _httpClientFactory;
  private readonly ILogger<ReasoningEngine> _logger;
  private readonly IGrpcAgentClient _agentClient;
  private readonly SessionStateManager _sessionManager;

  private readonly string _ollamaBaseUrl;
  private readonly string _ollamaModel;
  private readonly string _pragmaticsApiUrl;

  private const string SystemPrompt = """
        You are AJ, an infrastructure and context aware AI assistant to reason about infrastructure, coding, automation, and system management.
        FORMAT: {"tool": "name", "params": {...}, "reasoning": "why"}

        ABSOLUTES:

        1. NEVER FABRICATE OUTPUT
           - You CANNOT see command results until you execute a task
           - EVERY piece of data must come from a COMPLETED task

        2. ONLY THESE 3 TOOLS EXIST:
           - execute: {"agent_id": "X", "command": "..."} - Runs command on indicated agent
           - think: {"thought": "..."} - Planning, decomposition
           - complete: {"answer": "..."} - Final response

        3. BOOTSTRAP AGENT
           You have a LOCAL FunnelCloud agent available at localhost. Use it to discover other agents:
           - Discover agents: execute on "localhost" with command: Invoke-RestMethod http://localhost:41421/discover-peers

        4. TO GET DATA, YOU MUST EXECUTE
           - Need agent list? execute discover-peers on localhost first
           - Need ping times? execute Test-Connection command on target agent
           - NO SHORTCUTS. NO IMAGINED RESULTS.

        5. ANSWER ONLY WHAT WAS ASKED
           - Do NOT invent follow-up questions
           - Do NOT run extra commands beyond what is needed

        6. MINIMAL STEPS - DON'T OVERCOMPLICATE
           - "How many agents online?" → execute discover-peers → count → complete
        """;

  public ReasoningEngine(
      IHttpClientFactory httpClientFactory,
      ILogger<ReasoningEngine> logger,
      IGrpcAgentClient agentClient,
      SessionStateManager sessionManager)
  {
    _httpClientFactory = httpClientFactory;
    _logger = logger;
    _agentClient = agentClient;
    _sessionManager = sessionManager;

    _ollamaBaseUrl = Environment.GetEnvironmentVariable("OLLAMA_BASE_URL") ?? "http://ollama:11434";
    _ollamaModel = Environment.GetEnvironmentVariable("OLLAMA_MODEL") ?? "r1-distill-aj:32b-8k";
    _pragmaticsApiUrl = Environment.GetEnvironmentVariable("PRAGMATICS_API_URL") ?? "http://pragmatics_api:8001";
  }

  public async Task<ClassifyResponse> ClassifyIntentAsync(string text, string? context = null)
  {
    try
    {
      var client = _httpClientFactory.CreateClient();
      var requestBody = new { text, context };

      var response = await client.PostAsJsonAsync(
          $"{_pragmaticsApiUrl}/api/pragmatics/classify",
          requestBody);

      if (response.IsSuccessStatusCode)
      {
        var result = await response.Content.ReadFromJsonAsync<PragmaticsClassifyResponse>();
        return new ClassifyResponse(
            result?.Intent ?? "casual",
            result?.Confidence ?? 0.5,
            result?.Reason ?? "");
      }

      _logger.LogWarning("Pragmatics API returned {StatusCode}, defaulting to casual",
          response.StatusCode);
      return new ClassifyResponse("casual", 0.5, "Pragmatics API unavailable");
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Failed to classify intent, defaulting to casual");
      return new ClassifyResponse("casual", 0.5, "Classification error");
    }
  }

  public async Task<NextStepResponse> GenerateNextStepAsync(
      string task,
      List<StepResult> history,
      WorkspaceContext? workspace = null)
  {
    var prompt = BuildPrompt(task, history, workspace);

    var response = await CallOllamaAsync(prompt);
    var parsed = ParseResponse(response);

    return new NextStepResponse(
        parsed.Tool,
        parsed.Params,
        parsed.BatchId,
        parsed.Reasoning,
        false);
  }

  public async IAsyncEnumerable<TaskEvent> RunTaskStreamAsync(
      RunTaskRequest request,
      [EnumeratorCancellation] CancellationToken ct = default)
  {
    var session = _sessionManager.GetOrCreate(request.UserId ?? "default");
    if (!request.PreserveState)
    {
      session.Reset();
    }

    var stepNum = 0;
    var maxSteps = request.MaxSteps;

    while (stepNum < maxSteps && !ct.IsCancellationRequested)
    {
      stepNum++;

      // Generate next step
      yield return new TaskEvent
      {
        EventType = "status",
        StepNum = stepNum,
        Status = "Reasoning..."
      };

      var nextStep = await GenerateNextStepAsync(
          request.Task,
          session.History.ToList(),
          new WorkspaceContext { Cwd = request.WorkspaceRoot, WorkspaceRoot = request.WorkspaceRoot });

      yield return new TaskEvent
      {
        EventType = "step",
        StepNum = stepNum,
        Tool = nextStep.Tool,
        Status = $"Executing {nextStep.Tool}",
        Result = new Dictionary<string, object?>
        {
          ["tool"] = nextStep.Tool,
          ["params"] = nextStep.Params,
          ["reasoning"] = nextStep.Reasoning
        }
      };

      // Execute the step
      StepResult stepResult;
      if (nextStep.Tool == "complete")
      {
        stepResult = new StepResult
        {
          StepId = $"step-{stepNum}",
          Tool = "complete",
          Status = StepStatus.Success,
          Output = nextStep.Params.GetValueOrDefault("answer")?.ToString()
        };

        session.AddResult(stepResult);

        yield return new TaskEvent
        {
          EventType = "complete",
          StepNum = stepNum,
          Tool = "complete",
          Status = "Task completed",
          Result = new Dictionary<string, object?>
          {
            ["answer"] = stepResult.Output
          },
          Done = true
        };

        yield break;
      }
      else if (nextStep.Tool == "execute")
      {
        var agentId = nextStep.Params.GetValueOrDefault("agent_id")?.ToString() ?? "localhost";
        var command = nextStep.Params.GetValueOrDefault("command")?.ToString() ?? "";

        var execResult = await _agentClient.ExecuteAsync(agentId, command, 30, ct);

        stepResult = new StepResult
        {
          StepId = $"step-{stepNum}",
          Tool = "execute",
          Status = execResult.Success ? StepStatus.Success : StepStatus.Failed,
          Output = execResult.Stdout,
          Error = execResult.Stderr ?? execResult.ErrorMessage,
          ExecutionTime = execResult.DurationMs / 1000.0
        };
      }
      else if (nextStep.Tool == "think")
      {
        stepResult = new StepResult
        {
          StepId = $"step-{stepNum}",
          Tool = "think",
          Status = StepStatus.Success,
          Output = nextStep.Params.GetValueOrDefault("thought")?.ToString()
        };
      }
      else
      {
        stepResult = new StepResult
        {
          StepId = $"step-{stepNum}",
          Tool = nextStep.Tool,
          Status = StepStatus.Failed,
          Error = $"Unknown tool: {nextStep.Tool}"
        };
      }

      session.AddResult(stepResult);

      yield return new TaskEvent
      {
        EventType = "result",
        StepNum = stepNum,
        Tool = nextStep.Tool,
        Status = stepResult.Status == StepStatus.Success ? "Success" : "Failed",
        Result = new Dictionary<string, object?>
        {
          ["output"] = stepResult.Output,
          ["error"] = stepResult.Error,
          ["execution_time"] = stepResult.ExecutionTime
        }
      };
    }

    // Max steps reached
    yield return new TaskEvent
    {
      EventType = "error",
      StepNum = stepNum,
      Status = "Max steps reached",
      Done = true
    };
  }

  private string BuildPrompt(string task, List<StepResult> history, WorkspaceContext? workspace)
  {
    var sb = new StringBuilder();
    sb.AppendLine($"Task: {task}");

    if (workspace != null)
    {
      sb.AppendLine($"Workspace: {workspace.WorkspaceRoot}");
    }

    if (history.Count > 0)
    {
      sb.AppendLine("\nPrevious steps:");
      foreach (var step in history)
      {
        sb.AppendLine($"- {step.Tool}: {(step.Status == StepStatus.Success ? "✓" : "✗")} {step.Output?.Take(200)}");
      }
    }

    sb.AppendLine("\nGenerate the next step as JSON:");
    return sb.ToString();
  }

  private async Task<string> CallOllamaAsync(string prompt)
  {
    var client = _httpClientFactory.CreateClient();

    var requestBody = new
    {
      model = _ollamaModel,
      prompt = prompt,
      system = SystemPrompt,
      stream = false,
      options = new { temperature = 0.1 }
    };

    var response = await client.PostAsJsonAsync($"{_ollamaBaseUrl}/api/generate", requestBody);
    response.EnsureSuccessStatusCode();

    var result = await response.Content.ReadFromJsonAsync<OllamaResponse>();
    return result?.Response ?? "{}";
  }

  private ParsedStep ParseResponse(string response)
  {
    try
    {
      // Extract JSON from response (may contain markdown or extra text)
      var jsonStart = response.IndexOf('{');
      var jsonEnd = response.LastIndexOf('}');

      if (jsonStart >= 0 && jsonEnd > jsonStart)
      {
        var json = response.Substring(jsonStart, jsonEnd - jsonStart + 1);
        var parsed = JsonSerializer.Deserialize<JsonElement>(json);

        var tool = parsed.TryGetProperty("tool", out var t) ? t.GetString() ?? "unknown" :
                   parsed.TryGetProperty("action", out var a) ? a.GetString() ?? "unknown" : "unknown";

        var paramsDict = new Dictionary<string, object?>();
        if (parsed.TryGetProperty("params", out var p) && p.ValueKind == JsonValueKind.Object)
        {
          foreach (var prop in p.EnumerateObject())
          {
            paramsDict[prop.Name] = prop.Value.ValueKind switch
            {
              JsonValueKind.String => prop.Value.GetString(),
              JsonValueKind.Number => prop.Value.GetDouble(),
              JsonValueKind.True => true,
              JsonValueKind.False => false,
              _ => prop.Value.ToString()
            };
          }
        }

        // Handle legacy formats where params are at root level
        if (paramsDict.Count == 0)
        {
          foreach (var prop in parsed.EnumerateObject())
          {
            if (prop.Name is not "tool" and not "action" and not "reasoning")
            {
              paramsDict[prop.Name] = prop.Value.ValueKind switch
              {
                JsonValueKind.String => prop.Value.GetString(),
                JsonValueKind.Number => prop.Value.GetDouble(),
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                _ => prop.Value.ToString()
              };
            }
          }
        }

        var reasoning = parsed.TryGetProperty("reasoning", out var r) ? r.GetString() ?? "" : "";

        return new ParsedStep(tool, paramsDict, null, reasoning);
      }
    }
    catch (Exception ex)
    {
      _logger.LogWarning(ex, "Failed to parse LLM response: {Response}", response.Take(200));
    }

    return new ParsedStep("complete", new Dictionary<string, object?> { ["answer"] = "I couldn't parse the response." }, null, "Parse error");
  }

  private record ParsedStep(string Tool, Dictionary<string, object?> Params, string? BatchId, string Reasoning);
  private record OllamaResponse(string Response);
  private record PragmaticsClassifyResponse(string Intent, double Confidence, string? Reason);
}

using System.Net.Http.Json;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using AJ.Orchestrator.Abstractions.Models.Classification;
using AJ.Orchestrator.Abstractions.Models.Tasks;
using AJ.Orchestrator.Abstractions.Models.Workspace;
using AJ.Orchestrator.Abstractions.Services;
using Microsoft.Extensions.Logging;

namespace AJ.Orchestrator.Domain.Services;

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
        You are AJ, an infrastructure and context aware AI assistant.
        RESPONSE FORMAT (strict JSON, no markdown): {"tool": "name", "params": {...}, "reasoning": "why"}

        TOOLS — these four are the ONLY tools that exist. Do NOT invent other tool names:
        - list_agents: {"params": {}} — Returns all online FunnelCloud agents. CALL THIS FIRST unless user specifies an agent.
        - execute: {"params": {"agent_id": "hostname", "command": "..."}} — Runs a command on an agent. REQUIRES agent_id.
        - think: {"params": {"thought": "..."}} — Planning step
        - complete: {"params": {"answer": "NATURAL LANGUAGE only"}} — Final response to user. The answer MUST be plain text summarizing results, NOT another tool call or JSON.

        WORKFLOW:
        1. If user names a specific agent (e.g., "on ians-r16"), execute directly on that agent.
        2. Otherwise, call list_agents FIRST to discover available agents, then choose the right one.
        3. After execute succeeds, call complete with a NATURAL LANGUAGE summary of results.

        RULES:
        1. NEVER fabricate output. All data must come from tool results.
        2. COMPLETE AS SOON AS POSSIBLE: Once execute returns data, call complete IMMEDIATELY with plain text summary.
        3. STOP AFTER FAILURES: If 2-3 attempts fail, call complete with "I couldn't retrieve the data because..."
        4. Output may be truncated — if you see useful data, USE IT and complete.
        5. Answer ONLY what was asked. No follow-up questions. No extra commands.
        6. complete.answer must be NATURAL LANGUAGE, never JSON or code. Wrong: {"answer": "{...}"} Right: {"answer": "The user is in 5 groups: ..."}

        EXAMPLES:
        - "List agents" → {"tool": "list_agents", "params": {}, "reasoning": "discover agents"}
        - "Get AD groups for ian" → {"tool": "list_agents", "params": {}, "reasoning": "need to find a domain controller first"}
        - "Ping google from ians-r16" → {"tool": "execute", "params": {"agent_id": "ians-r16", "command": "Test-Connection google.com -Count 1"}, "reasoning": "user specified agent"}
        - After successful execute → {"tool": "complete", "params": {"answer": "Ian is a member of Domain Users, Domain Admins, and Schema Admins."}, "reasoning": "summarizing results"}
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

      if (!response.IsSuccessStatusCode)
      {
        _logger.LogWarning("Pragmatics API returned {StatusCode}, defaulting to casual",
            response.StatusCode);
        return new ClassifyResponse("casual", 0.5, "Pragmatics API unavailable");
      }

      var result = await response.Content.ReadFromJsonAsync<PragmaticsClassifyResponse>();
      return new ClassifyResponse(
          result?.Intent ?? "casual",
          result?.Confidence ?? 0.5,
          result?.Reason ?? "");
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
        false,
        parsed.ThinkingContent);
  }

  public async IAsyncEnumerable<TaskEvent> RunTaskStreamAsync(RunTaskRequest request, [EnumeratorCancellation] CancellationToken ct = default)
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

      // Debug logging
      _logger.LogInformation("Step {Step}: Parsed tool={Tool}, params={@Params}",
          stepNum, nextStep.Tool, nextStep.Params.Keys);

      // Emit thinking content if available (the LLM's chain-of-thought)
      if (!string.IsNullOrWhiteSpace(nextStep.ThinkingContent))
      {
        yield return new TaskEvent
        {
          EventType = "thinking",
          StepNum = stepNum,
          Status = "Thinking",
          Content = nextStep.ThinkingContent
        };
      }

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
      else if (nextStep.Tool == "list_agents")
      {
        // Built-in tool: call agent discovery directly (no shell execution needed)
        var agents = await _agentClient.DiscoverAgentsAsync(ct);
        var agentList = string.Join("\n", agents.Select(a => $"- {a.AgentId} ({a.Hostname}, {a.Platform})"));
        var output = $"Found {agents.Count} agent(s):\n{agentList}";

        stepResult = new StepResult
        {
          StepId = $"step-{stepNum}",
          Tool = "list_agents",
          Status = StepStatus.Success,
          Output = output
        };
      }
      else if (nextStep.Tool == "execute")
      {
        var agentId = nextStep.Params.GetValueOrDefault("agent_id")?.ToString();
        var command = nextStep.Params.GetValueOrDefault("command")?.ToString() ?? "";

        // Require agent_id — no more defaulting to "localhost"
        if (string.IsNullOrWhiteSpace(agentId))
        {
          _logger.LogWarning("execute called without agent_id at step {Step}", stepNum);
          stepResult = new StepResult
          {
            StepId = $"step-{stepNum}",
            Tool = "execute",
            Status = StepStatus.Failed,
            Error = "Missing agent_id. Call list_agents first to discover available agents, then specify agent_id."
          };
        }
        else
        {
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
          ["output_preview"] = stepResult.Output,
          ["error"] = stepResult.Error,
          ["execution_time"] = stepResult.ExecutionTime
        },
        // Include params at event level for filter compatibility
        Params = nextStep.Params
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

    // Note: Removed workspace display - was confusing the model into thinking "user mentioned workspace"

    if (history.Count > 0)
    {
      sb.AppendLine("\nPrevious steps:");
      foreach (var step in history)
      {
        var marker = step.Status == StepStatus.Success ? "✓" : "✗";
        string detail;
        if (step.Status == StepStatus.Success)
        {
          var output = step.Output ?? "";
          if (output.Length > 10000)
          {
            // Truncate but mark as truncated (not incomplete)
            detail = output[..10000] + "\n[OUTPUT TRUNCATED - data above is valid, use it]";
          }
          else
          {
            detail = output;
          }
        }
        else
        {
          detail = $"ERROR: {step.Error ?? "unknown"}";
        }
        sb.AppendLine($"- {step.Tool}: {marker} {detail}");
      }

      // Nudge completion only after execute steps succeed (not list_agents or think — those are setup/planning)
      var executeSuccesses = history.Where(s => s.Status == StepStatus.Success && s.Tool == "execute").ToList();
      if (executeSuccesses.Any())
      {
        sb.AppendLine("\n✅ EXECUTE SUCCEEDED: You have command output from the steps above.");
        sb.AppendLine("If this answers the user's question, call complete NOW with this data.");
      }

      // Count recent failures — if last 2+ steps failed, strongly nudge to complete
      var recentFailures = history.AsEnumerable().Reverse().TakeWhile(s => s.Status == StepStatus.Failed).Count();
      if (recentFailures >= 2)
      {
        sb.AppendLine($"\n⚠️ WARNING: The last {recentFailures} attempts have FAILED. Do NOT keep trying.");
        sb.AppendLine("Call complete NOW with a summary of what you tried and why it failed.");
      }

      // If total failures exceed threshold, force completion
      var totalFailures = history.Count(s => s.Status == StepStatus.Failed);
      if (totalFailures >= 3)
      {
        sb.AppendLine($"\n🛑 STOP: {totalFailures} steps have failed. You MUST call complete now.");
        sb.AppendLine("Summarize what worked, what failed, and provide your best answer or explanation.");
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
    // Extract thinking content BEFORE stripping it (for UI streaming)
    var thinkingContent = ExtractThinkingContent(response);

    try
    {
      // Strip R1-Distill <think>...</think> reasoning blocks before extracting JSON
      var cleaned = StripThinkingBlocks(response);

      // Strip markdown code fences (```json ... ``` or ``` ... ```)
      cleaned = StripCodeFences(cleaned);

      _logger.LogDebug("Raw LLM response ({RawLength} chars, {CleanedLength} after strip): {Response}",
          response.Length, cleaned.Length, cleaned.Length > 500 ? cleaned[..500] + "..." : cleaned);

      // Extract JSON from response (may contain extra text around the JSON)
      var jsonStart = cleaned.IndexOf('{');
      var jsonEnd = cleaned.LastIndexOf('}');

      if (jsonStart >= 0 && jsonEnd > jsonStart)
      {
        var json = cleaned.Substring(jsonStart, jsonEnd - jsonStart + 1);
        var parsed = JsonSerializer.Deserialize<JsonElement>(json);

        var tool = parsed.TryGetProperty("tool", out var t) ? t.GetString() ?? "unknown" :
                   parsed.TryGetProperty("action", out var a) ? a.GetString() ?? "unknown" : "unknown";

        // Normalize common tool name hallucinations
        tool = NormalizeTool(tool);

        var paramsDict = new Dictionary<string, object?>();

        // Try "params" first, then "parameters" (common model hallucination)
        var hasParams = parsed.TryGetProperty("params", out var p) && p.ValueKind == JsonValueKind.Object;
        if (!hasParams)
          hasParams = parsed.TryGetProperty("parameters", out p) && p.ValueKind == JsonValueKind.Object;

        if (hasParams)
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
            if (prop.Name is not "tool" and not "action" and not "reasoning" and not "params" and not "parameters")
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
        else
        {
          // Merge root-level scalar properties that aren't already in params
          // (handles model putting "command" at root and "agent_id" in params)
          foreach (var prop in parsed.EnumerateObject())
          {
            if (prop.Name is "tool" or "action" or "reasoning" or "params" or "parameters")
              continue;
            if (prop.Value.ValueKind is JsonValueKind.Object or JsonValueKind.Array)
              continue;
            if (paramsDict.ContainsKey(prop.Name))
              continue;

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

        // Normalize common param name hallucinations for execute tool
        if (tool == "execute")
          NormalizeExecuteParams(paramsDict);

        // Handle model wrapping a tool name inside execute_command
        tool = ResolveWrappedTool(tool, paramsDict);

        var reasoning = parsed.TryGetProperty("reasoning", out var r) ? r.GetString() ?? "" : "";

        return new ParsedStep(tool, paramsDict, null, reasoning, thinkingContent);
      }
    }
    catch (Exception ex)
    {
      _logger.LogWarning(ex, "Failed to parse LLM response ({Length} chars): {Response}",
          response.Length, response.Length > 1000 ? response[..1000] + "..." : response);
    }

    return new ParsedStep("complete", new Dictionary<string, object?> { ["answer"] = "I couldn't parse the response." }, null, "Parse error", thinkingContent);
  }

  private static readonly HashSet<string> s_validTools = new(StringComparer.OrdinalIgnoreCase)
    { "list_agents", "execute", "think", "complete" };

  private static string NormalizeTool(string tool) => tool.ToLowerInvariant() switch
  {
    "remote_execute" or "execute_command" or "run_command" or "run" => "execute",
    "terminal" or "shell" or "cmd" or "powershell" or "bash" or "invoke" => "execute",
    "list" or "list_agent" or "discover" or "discover_agents" => "list_agents",
    "finish" or "done" or "answer" or "respond" => "complete",
    "plan" or "reason" => "think",
    _ => tool
  };

  /// <summary>
  /// Post-normalize: if tool is "execute" but the command param is actually a tool name
  /// (e.g. model said {"action": "execute_command", "command": "list_agents"}),
  /// re-map to the correct tool.
  /// </summary>
  private static string ResolveWrappedTool(string tool, Dictionary<string, object?> paramsDict)
  {
    if (tool != "execute")
      return tool;

    var cmd = paramsDict.GetValueOrDefault("command")?.ToString();
    if (string.IsNullOrEmpty(cmd))
      return tool;

    var normalizedCmd = NormalizeTool(cmd);
    if (!s_validTools.Contains(normalizedCmd) || normalizedCmd == "execute")
      return tool;

    // The "command" is actually a tool name — re-map
    paramsDict.Remove("command");
    return normalizedCmd;
  }

  private static void NormalizeExecuteParams(Dictionary<string, object?> p)
  {
    // Map common agent_id aliases
    foreach (var alias in new[] { "target_agent_name", "agent_name", "agent", "target", "hostname" })
    {
      if (!p.ContainsKey("agent_id") && p.TryGetValue(alias, out var v))
      {
        p["agent_id"] = v;
        p.Remove(alias);
        break;
      }
    }
  }

  /// <summary>
  /// Extract the content of &lt;think&gt;...&lt;/think&gt; blocks from the model output.
  /// Returns the thinking content for streaming to the UI, or empty string if none.
  /// </summary>
  private static string ExtractThinkingContent(string response)
  {
    // Match <think>content</think> and extract the inner content
    var match = Regex.Match(response, @"<think>([\s\S]*?)</think>", RegexOptions.IgnoreCase);
    if (match.Success)
      return match.Groups[1].Value.Trim();

    // Check for orphaned </think> - content before it might be thinking
    var closeIdx = response.IndexOf("</think>", StringComparison.OrdinalIgnoreCase);
    if (closeIdx > 0)
    {
      var beforeClose = response[..closeIdx].Trim();
      // Only return if it looks like thinking (has some substance)
      if (beforeClose.Length > 10 && !beforeClose.StartsWith("{"))
        return beforeClose;
    }

    return string.Empty;
  }

  /// <summary>
  /// Strip R1-Distill &lt;think&gt;...&lt;/think&gt; reasoning blocks from the model output.
  /// The model places its chain-of-thought inside these tags before the actual JSON response.
  /// </summary>
  private static string StripThinkingBlocks(string response)
  {
    // Handle both complete <think>...</think> and unclosed <think>... (model cut off)
    var result = Regex.Replace(response, @"<think>[\s\S]*?</think>", "", RegexOptions.IgnoreCase);

    // Handle orphaned </think> without opening tag - take everything after it
    var closeThinkIdx = result.IndexOf("</think>", StringComparison.OrdinalIgnoreCase);
    if (closeThinkIdx >= 0)
    {
      result = result[(closeThinkIdx + "</think>".Length)..];
    }

    // If there's an unclosed <think> block (model was cut off mid-thought), strip from <think> to end
    // but only if there's no JSON after it
    var unclosedIdx = result.IndexOf("<think>", StringComparison.OrdinalIgnoreCase);
    if (unclosedIdx >= 0)
    {
      // Check if there's JSON after the unclosed think tag
      var afterThink = result[unclosedIdx..];
      var jsonAfter = afterThink.IndexOf('{');
      if (jsonAfter < 0)
      {
        // No JSON after unclosed think — strip it all
        result = result[..unclosedIdx];
      }
    }

    return result.Trim();
  }

  /// <summary>
  /// Strip markdown code fences (```json ... ``` or ``` ... ```) from the model output.
  /// Extracts the content inside the first code block if present.
  /// </summary>
  private static string StripCodeFences(string response)
  {
    // Match ```json\n...\n``` or ```\n...\n```
    var match = Regex.Match(response, @"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```");
    if (match.Success)
      return match.Groups[1].Value.Trim();

    return response;
  }

  private record ParsedStep(string Tool, Dictionary<string, object?> Params, string? BatchId, string Reasoning, string ThinkingContent);
  private record OllamaResponse(string Response);
  private record PragmaticsClassifyResponse(string Intent, double Confidence, string? Reason);
}

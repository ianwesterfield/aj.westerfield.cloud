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
/// Now skill-aware: injects relevant skill instructions into context.
/// </summary>
public class ReasoningEngine : IReasoningEngine
{
  private readonly IHttpClientFactory _httpClientFactory;
  private readonly ILogger<ReasoningEngine> _logger;
  private readonly IGrpcAgentClient _agentClient;
  private readonly SessionStateManager _sessionManager;
  private readonly ISkillDiscoveryService _skillDiscovery;
  private readonly ISkillExecutor _skillExecutor;

  // Endpoint is OpenAI-compatible (llama.cpp llama-server /v1/chat/completions).
  // Env var names are kept as OLLAMA_* for backwards compatibility with existing
  // deployments; the base URL can point at llama-server and the "model" field is
  // informational (llama-server only serves one model per process).
  private readonly string _llmBaseUrl;
  private readonly string _llmModel;

  private const string BaseSystemPrompt = """
        You are AJ, an infrastructure and context aware AI assistant.
        RESPONSE FORMAT (strict JSON, no markdown): {"tool": "name", "params": {...}, "reasoning": "why"}

        TOOLS — these four are the ONLY tools that exist. Do NOT invent other tool names:
        - list_agents: {"params": {}} — Discover all CURRENTLY online FunnelCloud agents. Always fresh.
        - execute: {"params": {"agent_id": "hostname", "command": "..."}} — Runs a command on an agent. REQUIRES agent_id.
        - think: {"params": {"thought": "..."}} — Plan your approach before acting.
        - complete: {"params": {"answer": "..."}} — Final response. See FINAL ANSWER rule below.

        FINAL ANSWER (IMPORTANT):
        When you emit {"tool": "complete", ...}, the content of your <think>...</think> block
        in that SAME response IS used as the final user-visible answer. The "answer" param is
        only a fallback when no <think> block is present. So:
        - Write your complete, well-formatted reply inside <think>...</think>
        - Do NOT repeat or paraphrase it in the "answer" param (leave "answer" as a short summary or empty string)
        - Do NOT contradict yourself between thinking and answer — only the thinking is shown

        DECIDING WHEN TO USE TOOLS vs COMPLETE IMMEDIATELY:

        COMPLETE IMMEDIATELY (no tools needed) when:
        - User asks about themselves (name, preferences) → use Memory Context below
        - User asks a general knowledge question → answer directly
        - User asks "how do I..." or "what is..." about technology → answer from knowledge, do NOT run commands
        - User greets you or makes small talk → respond warmly
        - User asks what you can do → describe your capabilities
        - The question is conversational, not an infrastructure action request

        USE TOOLS ONLY when the user is REQUESTING AN ACTION on real infrastructure:
        - User wants to execute a specific command on a specific server ("ping X from Y", "restart service on Z")
        - User asks about current system status ("is agent X online?", "what agents are available?")
        - User wants to check/modify infrastructure state
        - A "how do I..." question is NOT an action request — answer it, don't execute anything
        
        MANDATORY WORKFLOW FOR INFRASTRUCTURE TASKS:
        1. FIRST STEP: Call list_agents to discover available agents. You MUST know what agents exist before executing.
        2. ANALYZE: Review the agent list. Match agent capabilities to the task (e.g., postfix01 for mail, domain01 for AD).
        3. EXECUTE: Run commands on the appropriate agent using execute with agent_id.
        4. COMPLETE: After execute returns data, immediately call complete with a plain text summary.

        RULES:
        1. NEVER fabricate command output. All system data must come from tool results.
        2. TRUST YOUR TOOL RESULTS. If "Previous steps" shows a successful tool result, that data is REAL and CURRENT.
           - NEVER say "I don't have access to real-time data" when a tool just gave you real-time data.
           - NEVER say "I can't access that" when the data is right there in your history.
           - Your complete.answer MUST USE the data shown in Previous steps. Quote/summarize it directly.
        3. CRITICAL: If a tool/skill FAILED or returned an error, you MUST report the failure honestly.
           - Do NOT invent content when fetching a URL fails
           - Do NOT make up product specs, system info, or any data
           - Say "I couldn't fetch that URL because: <error>" — do not guess what the page contains
        4. For infrastructure tasks, NEVER call execute as your first action. Always list_agents first.
        5. COMPLETE AS SOON AS POSSIBLE: Once you have the answer (or confirmed failure), call complete IMMEDIATELY.
        6. STOP AFTER FAILURES: If 2-3 attempts fail, call complete with "I couldn't complete the task because..."
        7. DO NOT REPEAT THE SAME COMMAND. If execute returned empty output, DO NOT call it again — call complete and report the empty result.
        8. Answer ONLY what was asked. No follow-up questions.
        9. complete.answer must be NATURAL LANGUAGE, never JSON or code.
        10. If Memory Context is provided, USE IT to answer personal questions about the user.

        SKILL INTERPRETATION:
        Skills below provide workflow guidance. They may come from various sources (AI-generated, manual, templates)
        and may vary in structure - some detailed with examples, others minimal with just patterns.
        
        ALWAYS interpret skills this way:
        - Skills show WHICH AGENT handles a task type (use targetAgent or infer from description)
        - Skills show COMMAND PATTERNS (the structure/syntax of commands)
        - Skills show the WORKFLOW (sequence of operations)
        - ANY example values, domains, filenames, or usernames in skills are PLACEHOLDERS
        - Extract ACTUAL values from the USER'S REQUEST - this is the only source of truth
        
        Example: If skill shows "echo 'spammer.com REJECT'" and user says "block jojoscarinsurance.com",
        you MUST use "jojoscarinsurance.com" - the skill's "spammer.com" is just showing the pattern.

        EXAMPLES:
        - Conversational question → {"tool": "complete", "params": {"answer": "Your name is Ian, based on what you've told me."}, "reasoning": "answering from memory"}
        - First step for infrastructure task → {"tool": "list_agents", "params": {}, "reasoning": "discovering available agents"}
        - After list_agents shows postfix01 → {"tool": "execute", "params": {"agent_id": "postfix01", "command": "..."}, "reasoning": "postfix01 handles mail"}
        - After successful execute → {"tool": "complete", "params": {"answer": "Done. Added domain to spam block list and reloaded postfix."}, "reasoning": "task complete"}
        """;

  public ReasoningEngine(
      IHttpClientFactory httpClientFactory,
      ILogger<ReasoningEngine> logger,
      IGrpcAgentClient agentClient,
      SessionStateManager sessionManager,
      ISkillDiscoveryService skillDiscovery,
      ISkillExecutor skillExecutor)
  {
    _httpClientFactory = httpClientFactory;
    _logger = logger;
    _agentClient = agentClient;
    _sessionManager = sessionManager;
    _skillDiscovery = skillDiscovery;
    _skillExecutor = skillExecutor;

    _llmBaseUrl = Environment.GetEnvironmentVariable("LLM_BASE_URL")
        ?? Environment.GetEnvironmentVariable("OLLAMA_BASE_URL")
        ?? "http://localhost:8081";
    _llmModel = Environment.GetEnvironmentVariable("LLM_MODEL")
        ?? Environment.GetEnvironmentVariable("OLLAMA_MODEL")
        ?? "ajr1-32b";
  }

  public async Task<ClassifyResponse> ClassifyIntentAsync(string text, string? context = null)
  {
    // Use the same Ollama LLM for intent classification (no DistilBERT)
    try
    {
      var systemPrompt = @"You are an intent classifier. Classify the user's message into exactly ONE category.

Categories:
- ""task"": User wants to perform an action, execute code, access websites, run commands, or get work done
- ""casual"": Greeting, small talk, or general conversation without a specific task
- ""save"": User explicitly asks to remember/store information for later
- ""recall"": User asks what you remember about something

Respond with ONLY a JSON object: {""intent"": ""<category>"", ""confidence"": <0.0-1.0>}";

      var userPrompt = string.IsNullOrEmpty(context)
          ? text
          : $"Previous context: {context}\n\nCurrent message: {text}";

      var client = _httpClientFactory.CreateClient();
      var requestBody = new
      {
        model = _llmModel,
        messages = new object[]
        {
          new { role = "system", content = systemPrompt },
          new { role = "user", content = userPrompt },
        },
        stream = false,
        temperature = 0.1,
      };

      var response = await client.PostAsJsonAsync($"{_llmBaseUrl}/v1/chat/completions", requestBody);
      response.EnsureSuccessStatusCode();

      var result = await response.Content.ReadFromJsonAsync<ChatCompletionResponse>();
      var responseText = result?.Choices?.FirstOrDefault()?.Message?.Content ?? "";

      // Parse JSON from LLM response
      var jsonStart = responseText.IndexOf('{');
      var jsonEnd = responseText.LastIndexOf('}');

      if (jsonStart >= 0 && jsonEnd > jsonStart)
      {
        var json = responseText.Substring(jsonStart, jsonEnd - jsonStart + 1);
        var parsed = JsonSerializer.Deserialize<JsonElement>(json);

        var intent = parsed.TryGetProperty("intent", out var i) ? i.GetString() ?? "casual" : "casual";
        var confidence = parsed.TryGetProperty("confidence", out var c) ? c.GetDouble() : 0.7;

        _logger.LogInformation("LLM classified intent: {Intent} ({Confidence:P0})", intent, confidence);
        return new ClassifyResponse(intent, confidence, "LLM classification");
      }

      _logger.LogWarning("LLM response didn't contain valid JSON, defaulting to task");
      return new ClassifyResponse("task", 0.6, "Parse fallback");
    }
    catch (Exception ex)
    {
      _logger.LogError(ex, "Failed to classify intent via LLM, defaulting to task");
      return new ClassifyResponse("task", 0.5, "Classification error");
    }
  }

  public async Task<NextStepResponse> GenerateNextStepAsync(
      string task,
      List<StepResult> history,
      WorkspaceContext? workspace = null,
      List<Dictionary<string, object?>>? memoryContext = null)
  {
    // Find relevant skills for this task
    var relevantSkills = _skillDiscovery.FindRelevantSkills(task).Take(3).ToList();

    if (relevantSkills.Count > 0)
    {
      _logger.LogInformation("Found {Count} relevant skill(s) for task: {Skills}",
          relevantSkills.Count, string.Join(", ", relevantSkills.Select(s => s.Name)));
    }

    var prompt = BuildPrompt(task, history, workspace, memoryContext);
    var systemPrompt = BuildSystemPromptWithSkills(relevantSkills);

    var response = await CallLlmAsync(prompt, systemPrompt);
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

    // ===== LLM-FIRST ARCHITECTURE: Let the LLM decide what tools/skills to use =====
    // No pattern matching - the LLM sees available skills and decides when to use them

    // Find skills once at task start - used for command syntax guidance
    var relevantSkills = _skillDiscovery.FindRelevantSkills(request.Task).Take(3).ToList();

    // Emit status showing which skills are being used for context
    if (relevantSkills.Count > 0)
    {
      var skillNames = string.Join(", ", relevantSkills.Select(s => s.Name));
      yield return new TaskEvent
      {
        EventType = "status",
        StepNum = 0,
        Status = $"📚 Using skills: {skillNames}"
      };
    }

    // Track whether agents have been discovered this task
    var agentsDiscovered = false;

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
          new WorkspaceContext { Cwd = request.WorkspaceRoot, WorkspaceRoot = request.WorkspaceRoot },
          request.MemoryContext);

      // Debug logging
      _logger.LogInformation("Step {Step}: Parsed tool={Tool}, params={@Params}",
          stepNum, nextStep.Tool, nextStep.Params.Keys);

      // Emit thinking content if available (the LLM's chain-of-thought).
      // For the "complete" step we skip this emission because the thinking content
      // is used AS the final answer below — emitting it here would duplicate it.
      if (!string.IsNullOrWhiteSpace(nextStep.ThinkingContent) && nextStep.Tool != "complete")
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
        Status = BuildStepStatus(nextStep),
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
        // Prefer the thinking content as the final answer. The LLM's chain-of-thought
        // is typically more accurate than the regenerated "answer" param, which tends
        // to hallucinate or contradict prior reasoning (especially for factual Q&A).
        // Fall back to the answer param only if thinking is empty.
        var thinkingAsAnswer = nextStep.ThinkingContent?.Trim();
        var answerParam = nextStep.Params.GetValueOrDefault("answer")?.ToString();
        var finalAnswer = !string.IsNullOrWhiteSpace(thinkingAsAnswer)
          ? thinkingAsAnswer
          : answerParam;

        stepResult = new StepResult
        {
          StepId = $"step-{stepNum}",
          Tool = "complete",
          Status = StepStatus.Success,
          Output = finalAnswer
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

        agentsDiscovered = true;

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
        // Guard: must discover agents before executing
        if (!agentsDiscovered)
        {
          _logger.LogWarning("execute called before list_agents at step {Step}", stepNum);
          stepResult = new StepResult
          {
            StepId = $"step-{stepNum}",
            Tool = "execute",
            Status = StepStatus.Failed,
            Error = "You must call list_agents first to discover available agents before executing commands."
          };
        }
        else
        {
          var agentId = nextStep.Params.GetValueOrDefault("agent_id")?.ToString();
          var command = nextStep.Params.GetValueOrDefault("command")?.ToString() ?? "";

          // Require agent_id
          if (string.IsNullOrWhiteSpace(agentId))
          {
            _logger.LogWarning("execute called without agent_id at step {Step}", stepNum);
            stepResult = new StepResult
            {
              StepId = $"step-{stepNum}",
              Tool = "execute",
              Status = StepStatus.Failed,
              Error = "Missing agent_id. Specify which agent to run the command on."
            };
          }
          else
          {
            var execResult = await _agentClient.ExecuteAsync(agentId, command, 3600, ct);

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
        // Check if LLM called a skill by name - try to execute it
        var skillByName = _skillExecutor.GetSkillByName(nextStep.Tool);
        if (skillByName != null)
        {
          _logger.LogInformation("LLM called skill by name: {SkillName}", nextStep.Tool);

          // Build a SkillMatch from LLM params
          var llmSkillMatch = new SkillMatch
          {
            Skill = skillByName,
            Parameters = nextStep.Params.ToDictionary(
              kvp => kvp.Key,
              kvp => kvp.Value?.ToString() ?? ""),
            Confidence = 1.0,
            MatchedBy = "LLM tool call"
          };

          var execResult = await _skillExecutor.ExecuteAsync(llmSkillMatch, ct);

          stepResult = new StepResult
          {
            StepId = $"step-{stepNum}",
            Tool = nextStep.Tool,
            Status = execResult.Success ? StepStatus.Success : StepStatus.Failed,
            Output = execResult.Message,
            Error = execResult.Success ? null : execResult.Message
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

  private string BuildPrompt(string task, List<StepResult> history, WorkspaceContext? workspace, List<Dictionary<string, object?>>? memoryContext = null)
  {
    var sb = new StringBuilder();
    sb.AppendLine($"Task: {task}");

    // Include memory context if provided (user facts, preferences, etc.)
    if (memoryContext != null && memoryContext.Count > 0)
    {
      sb.AppendLine("\nMemory Context (facts about the user):");
      foreach (var item in memoryContext.Take(5)) // Limit to top 5 most relevant
      {
        if (item.TryGetValue("user_text", out var userText))
        {
          sb.AppendLine($"- {userText}");
        }
        // Also check for facts in various formats
        if (item.TryGetValue("facts", out var facts) && facts is string factsStr && !string.IsNullOrWhiteSpace(factsStr))
        {
          foreach (var line in factsStr.Split('\n').Take(3))
          {
            sb.AppendLine($"  → {line.Trim()}");
          }
        }
      }
      sb.AppendLine("(Use this context to answer personal questions about the user)");
    }

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

      // Nudge completion after successful tool calls that produce data
      var executeSuccesses = history.Where(s => s.Status == StepStatus.Success && s.Tool == "execute").ToList();
      if (executeSuccesses.Any())
      {
        sb.AppendLine("\n✅ EXECUTE SUCCEEDED: You have command output from the steps above.");
        sb.AppendLine("If this answers the user's question, call complete NOW with this data.");
      }

      // Also nudge completion after list_agents if user asked an agent-related question
      var listAgentsSuccesses = history.Where(s => s.Status == StepStatus.Success && s.Tool == "list_agents").ToList();
      if (listAgentsSuccesses.Any() && !executeSuccesses.Any())
      {
        sb.AppendLine("\n✅ AGENT LIST RETRIEVED: You now have the list of available agents.");
        sb.AppendLine("If the user only asked about agents (count, status, list), call complete NOW with this data.");
        sb.AppendLine("Only call execute if you need to RUN A COMMAND on an agent.");
      }

      // LOOP DETECTION: If the same tool was called 2+ times consecutively, force completion
      var recentTools = history.AsEnumerable().Reverse().Take(3).Select(s => s.Tool).ToList();
      if (recentTools.Count >= 2 && recentTools.Distinct().Count() == 1 && recentTools[0] != "complete")
      {
        sb.AppendLine($"\n🛑 LOOP DETECTED: You called '{recentTools[0]}' multiple times in a row.");
        sb.AppendLine("You MUST call complete NOW. Report whatever output you have, even if empty.");
      }

      // EMPTY OUTPUT DETECTION: If the last execute returned empty stdout, do not retry
      var lastExecute = history.LastOrDefault(s => s.Tool == "execute");
      if (lastExecute != null && lastExecute.Status == StepStatus.Success && string.IsNullOrWhiteSpace(lastExecute.Output))
      {
        sb.AppendLine("\n⚠️ The last execute call returned EMPTY output. Do NOT retry. Call complete and report that the command produced no output.");
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

  private string BuildSystemPromptWithSkills(IEnumerable<AJ.Orchestrator.Abstractions.Models.Skills.Skill> skills)
  {
    var sb = new System.Text.StringBuilder();
    sb.AppendLine(BaseSystemPrompt);

    // Add executable skills as callable tools
    var executableSkills = _skillExecutor.GetAllSkills().ToList();
    if (executableSkills.Count > 0)
    {
      sb.AppendLine();
      sb.AppendLine("## CALLABLE SKILLS (use as tools)");
      sb.AppendLine("These skills can be called directly by name. Use them when the user's request matches their purpose.");
      sb.AppendLine();

      foreach (var skill in executableSkills)
      {
        var desc = skill.Description ?? skill.Responses?.Success ?? "Execute skill workflow";
        sb.AppendLine($"- **{skill.Name}**: {desc}");
        if (skill.Parameters?.Count > 0)
        {
          var paramDescs = skill.Parameters.Select(p =>
            $"{p.Key}{(p.Value.Required ? " (required)" : "")}: {p.Value.Description ?? "parameter"}");
          sb.AppendLine($"  Parameters: {string.Join("; ", paramDescs)}");
        }
        if (!string.IsNullOrEmpty(skill.Target?.Agent))
        {
          sb.AppendLine($"  Target: {skill.Target.Agent}");
        }
      }

      sb.AppendLine();
      sb.AppendLine("To use a skill, respond: {\"tool\": \"skill-name\", \"params\": {...}}");
      sb.AppendLine("Example: {\"tool\": \"web-fetch\", \"params\": {\"url\": \"https://example.com\"}}");
    }

    // Add SKILL.md workflow guides
    var skillContext = _skillDiscovery.FormatSkillContext(skills);
    if (!string.IsNullOrEmpty(skillContext))
    {
      sb.AppendLine();
      sb.AppendLine(skillContext);
    }

    return sb.ToString();
  }

  private async Task<string> CallLlmAsync(string prompt, string systemPrompt)
  {
    var client = _httpClientFactory.CreateClient();

    var requestBody = new
    {
      model = _llmModel,
      messages = new object[]
      {
        new { role = "system", content = systemPrompt },
        new { role = "user", content = prompt },
      },
      stream = false,
      temperature = 0.1,
    };

    _logger.LogDebug("Calling LLM with prompt:\n{Prompt}", prompt);

    var response = await client.PostAsJsonAsync($"{_llmBaseUrl}/v1/chat/completions", requestBody);
    response.EnsureSuccessStatusCode();

    var result = await response.Content.ReadFromJsonAsync<ChatCompletionResponse>();
    var llmResponse = result?.Choices?.FirstOrDefault()?.Message?.Content ?? "{}";

    _logger.LogInformation("LLM raw response ({Length} chars): {Response}",
        llmResponse.Length,
        llmResponse.Length > 500 ? llmResponse[..500] + "..." : llmResponse);

    return llmResponse;
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

    // If we have thinking content but no valid JSON, use thinking as the answer
    // This handles cases where the model provides a good response but malformed JSON
    if (!string.IsNullOrWhiteSpace(thinkingContent))
    {
      _logger.LogInformation("Using thinking content as fallback answer ({Length} chars)", thinkingContent.Length);
      return new ParsedStep("complete", new Dictionary<string, object?> { ["answer"] = thinkingContent }, null, "Thinking fallback", thinkingContent);
    }

    // Last resort: try to extract any meaningful text from the response
    var cleanedResponse = StripThinkingBlocks(response).Trim();
    if (!string.IsNullOrWhiteSpace(cleanedResponse) && cleanedResponse.Length > 10)
    {
      _logger.LogInformation("Using cleaned response as fallback answer ({Length} chars)", cleanedResponse.Length);
      return new ParsedStep("complete", new Dictionary<string, object?> { ["answer"] = cleanedResponse }, null, "Text fallback", thinkingContent);
    }

    return new ParsedStep("complete", new Dictionary<string, object?> { ["answer"] = "Task completed." }, null, "Parse error", thinkingContent);
  }

  /// <summary>
  /// Build a user-visible status string for a step, including key params (agent + command)
  /// so the UI banner shows what is actually running instead of a generic "Executing execute".
  /// </summary>
  private static string BuildStepStatus(NextStepResponse step)
  {
    var tool = step.Tool ?? "";
    var p = step.Params ?? new Dictionary<string, object?>();

    if (tool == "execute" || tool == "remote_execute")
    {
      var agent = p.GetValueOrDefault("agent_id")?.ToString()
                ?? p.GetValueOrDefault("target_agent")?.ToString()
                ?? p.GetValueOrDefault("host")?.ToString();
      var cmd = p.GetValueOrDefault("command")?.ToString()
              ?? p.GetValueOrDefault("cmd")?.ToString()
              ?? "";
      cmd = cmd.Trim();
      if (cmd.Length > 120) cmd = cmd.Substring(0, 117) + "...";
      if (!string.IsNullOrEmpty(agent) && !string.IsNullOrEmpty(cmd))
        return $"Executing on {agent}: {cmd}";
      if (!string.IsNullOrEmpty(cmd))
        return $"Executing: {cmd}";
    }

    if (tool == "list_agents")
      return "Discovering agents";

    if (tool == "think")
      return "Thinking";

    if (tool == "complete")
      return "Finalizing answer";

    return $"Executing {tool}";
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

  // OpenAI-compatible /v1/chat/completions response shape (llama-server / vLLM / etc.)
  private record ChatCompletionResponse(
      [property: System.Text.Json.Serialization.JsonPropertyName("choices")] List<ChatChoice>? Choices);
  private record ChatChoice(
      [property: System.Text.Json.Serialization.JsonPropertyName("message")] ChatMessage? Message);
  private record ChatMessage(
      [property: System.Text.Json.Serialization.JsonPropertyName("role")] string? Role,
      [property: System.Text.Json.Serialization.JsonPropertyName("content")] string? Content);
}

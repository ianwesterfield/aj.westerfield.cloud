using AJ.Orchestrator.Abstractions.Models.Classification;
using AJ.Orchestrator.Abstractions.Models.Tasks;
using AJ.Orchestrator.Abstractions.Models.Workspace;
using AJ.Orchestrator.Abstractions.Services;
using AJ.Orchestrator.Domain.Services;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using Moq;
using Moq.Protected;
using System.Net;
using System.Text.Json;

namespace AJ.Orchestrator.Tests.Services;

/// <summary>
/// Tests for ReasoningEngine service.
/// </summary>
public class ReasoningEngineTests
{
  private readonly Mock<IHttpClientFactory> _httpClientFactoryMock;
  private readonly Mock<ILogger<ReasoningEngine>> _loggerMock;
  private readonly Mock<IGrpcAgentClient> _agentClientMock;
  private readonly SessionStateManager _sessionManager;

  public ReasoningEngineTests()
  {
    _httpClientFactoryMock = new Mock<IHttpClientFactory>();
    _loggerMock = new Mock<ILogger<ReasoningEngine>>();
    _agentClientMock = new Mock<IGrpcAgentClient>();
    _sessionManager = new SessionStateManager();
  }

  private ReasoningEngine CreateEngine(HttpClient? client = null)
  {
    if (client != null)
    {
      _httpClientFactoryMock.Setup(f => f.CreateClient(It.IsAny<string>()))
          .Returns(client);
    }
    else
    {
      // Default mock that returns casual intent
      var defaultClient = CreateMockHttpClient(HttpStatusCode.OK,
          new { intent = "casual", confidence = 0.5, reason = "default" });
      _httpClientFactoryMock.Setup(f => f.CreateClient(It.IsAny<string>()))
          .Returns(defaultClient);
    }

    return new ReasoningEngine(
        _httpClientFactoryMock.Object,
        _loggerMock.Object,
        _agentClientMock.Object,
        _sessionManager);
  }

  #region ClassifyIntentAsync Tests

  [Fact]
  public async Task ClassifyIntentAsync_TaskIntent_ShouldReturnTask()
  {
    // Arrange
    var response = new { intent = "task", confidence = 0.95, reason = "User wants action" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, response);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.ClassifyIntentAsync("List all files in the directory");

    // Assert
    result.Intent.Should().Be("task");
    result.Confidence.Should().BeGreaterThan(0.9);
  }

  [Fact]
  public async Task ClassifyIntentAsync_CasualIntent_ShouldReturnCasual()
  {
    // Arrange
    var response = new { intent = "casual", confidence = 0.8, reason = "General conversation" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, response);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.ClassifyIntentAsync("Hello, how are you?");

    // Assert
    result.Intent.Should().Be("casual");
  }

  [Fact]
  public async Task ClassifyIntentAsync_ApiFailure_ShouldReturnDefaultCasual()
  {
    // Arrange
    var client = CreateMockHttpClient<object>(HttpStatusCode.InternalServerError, null);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.ClassifyIntentAsync("Some text");

    // Assert
    result.Intent.Should().Be("casual");
    result.Confidence.Should().Be(0.5);
  }

  [Fact]
  public async Task ClassifyIntentAsync_NetworkError_ShouldReturnDefaultCasual()
  {
    // Arrange
    var handlerMock = new Mock<HttpMessageHandler>();
    handlerMock.Protected()
        .Setup<Task<HttpResponseMessage>>("SendAsync",
            ItExpr.IsAny<HttpRequestMessage>(),
            ItExpr.IsAny<CancellationToken>())
        .ThrowsAsync(new HttpRequestException("Network error"));

    var client = new HttpClient(handlerMock.Object);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.ClassifyIntentAsync("Some text");

    // Assert
    result.Intent.Should().Be("casual");
    result.Reason.Should().Contain("error");
  }

  [Fact]
  public async Task ClassifyIntentAsync_WithContext_ShouldIncludeItInRequest()
  {
    // Arrange
    HttpRequestMessage? capturedRequest = null;
    var handlerMock = new Mock<HttpMessageHandler>();
    handlerMock.Protected()
        .Setup<Task<HttpResponseMessage>>("SendAsync",
            ItExpr.IsAny<HttpRequestMessage>(),
            ItExpr.IsAny<CancellationToken>())
        .Callback<HttpRequestMessage, CancellationToken>((req, ct) => capturedRequest = req)
        .ReturnsAsync(new HttpResponseMessage(HttpStatusCode.OK)
        {
          Content = new StringContent(JsonSerializer.Serialize(
                new { intent = "task", confidence = 0.9, reason = "context helped" }))
        });

    var client = new HttpClient(handlerMock.Object);
    var engine = CreateEngine(client);

    // Act
    await engine.ClassifyIntentAsync("continue", "Previous conversation context");

    // Assert
    capturedRequest.Should().NotBeNull();
    var body = await capturedRequest!.Content!.ReadAsStringAsync();
    body.Should().Contain("context");
  }

  #endregion

  #region GenerateNextStepAsync Tests

  [Fact]
  public async Task GenerateNextStepAsync_ShouldReturnNextStep()
  {
    // Arrange
    var ollamaResponse = new
    {
      message = new
      {
        content = """{"tool": "execute", "params": {"command": "ls"}, "reasoning": "listing files"}"""
      }
    };

    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    var history = new List<StepResult>();
    var workspace = new WorkspaceContext { Cwd = "/test", WorkspaceRoot = "/test" };

    // Act
    var result = await engine.GenerateNextStepAsync("List files", history, workspace);

    // Assert
    result.Should().NotBeNull();
    result.Tool.Should().NotBeNullOrEmpty();
  }

  #endregion

  #region RunTaskStreamAsync Tests

  [Fact]
  public async Task RunTaskStreamAsync_ShouldYieldEvents()
  {
    // Arrange - mock Ollama to return complete tool immediately
    var completeResponse = new
    {
      message = new
      {
        content = """{"tool": "complete", "params": {"answer": "Done"}, "reasoning": "Task complete"}"""
      }
    };

    var client = CreateMockHttpClient(HttpStatusCode.OK, completeResponse);
    var engine = CreateEngine(client);

    var request = new RunTaskRequest { Task = "Simple task", WorkspaceRoot = "/workspace", UserId = "test-user" };

    // Act
    var events = new List<TaskEvent>();
    await foreach (var evt in engine.RunTaskStreamAsync(request))
    {
      events.Add(evt);
    }

    // Assert
    events.Should().NotBeEmpty();
    events.Should().Contain(e => e.EventType == "status");
  }

  [Fact]
  public async Task RunTaskStreamAsync_PreserveStateFalse_ShouldResetSession()
  {
    // Arrange
    var session = _sessionManager.GetOrCreate("test-user");
    session.CurrentTask = "Previous task";
    session.AddResult(new StepResult { StepId = "old-step", Status = StepStatus.Success });

    var completeResponse = new
    {
      message = new
      {
        content = """{"tool": "complete", "params": {"answer": "Done"}, "reasoning": "done"}"""
      }
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, completeResponse);
    var engine = CreateEngine(client);

    var request = new RunTaskRequest { Task = "New task", WorkspaceRoot = "/workspace", UserId = "test-user", PreserveState = false };

    // Act
    await foreach (var _ in engine.RunTaskStreamAsync(request)) { }

    // Assert - session should have been reset
    var currentSession = _sessionManager.GetOrCreate("test-user");
    currentSession.StepCount.Should().BeGreaterThanOrEqualTo(1); // At least the complete step
  }

  [Fact]
  public async Task RunTaskStreamAsync_CancellationRequested_ShouldStop()
  {
    // Arrange
    var cts = new CancellationTokenSource();
    var stepResponse = new
    {
      message = new
      {
        content = """{"tool": "think", "params": {"thought": "thinking..."}, "reasoning": "planning"}"""
      }
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, stepResponse);
    var engine = CreateEngine(client);

    var request = new RunTaskRequest { Task = "Long task", WorkspaceRoot = "/workspace" };

    // Act
    var events = new List<TaskEvent>();
    var iteration = 0;
    await foreach (var evt in engine.RunTaskStreamAsync(request, cts.Token))
    {
      events.Add(evt);
      iteration++;
      if (iteration >= 2)
      {
        cts.Cancel();
        break;
      }
    }

    // Assert
    events.Should().HaveCountGreaterThanOrEqualTo(1);
  }

  [Fact]
  public async Task RunTaskStreamAsync_MaxStepsReached_ShouldStop()
  {
    // Arrange - always return think tool to force continuing
    var thinkResponse = new
    {
      message = new
      {
        content = """{"tool": "think", "params": {"thought": "still thinking"}, "reasoning": "need more steps"}"""
      }
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, thinkResponse);
    var engine = CreateEngine(client);

    var request = new RunTaskRequest { Task = "Task", WorkspaceRoot = "/workspace", MaxSteps = 3 };

    // Act
    var events = new List<TaskEvent>();
    await foreach (var evt in engine.RunTaskStreamAsync(request))
    {
      events.Add(evt);
      if (events.Count > 20) break; // Safety limit
    }

    // Assert - should have stopped after max steps
    // Each step has at least a status event, so we expect limited events
    events.Count.Should().BeLessThanOrEqualTo(10);
  }

  #endregion

  #region Tool Normalization Tests

  [Theory]
  [InlineData("remote_execute", "execute")]
  [InlineData("execute_command", "execute")]
  [InlineData("run_command", "execute")]
  [InlineData("list", "list_agents")]
  [InlineData("discover_agents", "list_agents")]
  [InlineData("finish", "complete")]
  [InlineData("execute", "execute")]
  public async Task GenerateNextStepAsync_NormalizesToolNames(string inputTool, string expectedTool)
  {
    // Arrange — use correct Ollama /api/generate response format
    var ollamaResponse = new { response = $$"""{"tool": "{{inputTool}}", "params": {"command": "test"}, "reasoning": "test"}""" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("test task", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be(expectedTool);
  }

  [Fact]
  public async Task GenerateNextStepAsync_NormalizesTargetAgentName()
  {
    // Arrange — model hallucinated "target_agent_name" instead of "agent_id"
    var ollamaResponse = new { response = """{"tool": "remote_execute", "params": {"target_agent_name": "ians-r16", "command": "ping google.com"}, "reasoning": "ping"}""" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("ping from ians-r16", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be("execute");
    result.Params.Should().ContainKey("agent_id");
    result.Params["agent_id"].Should().Be("ians-r16");
    result.Params.Should().ContainKey("command");
  }

  [Fact]
  public async Task GenerateNextStepAsync_HandlesParametersInsteadOfParams()
  {
    // Arrange — model used "parameters" instead of "params"
    var ollamaResponse = new { response = """{"tool": "execute", "parameters": {"agent_id": "r730xd", "command": "hostname"}, "reasoning": "check hostname"}""" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("run hostname on r730xd", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be("execute");
    result.Params.Should().ContainKey("agent_id");
    result.Params["agent_id"].Should().Be("r730xd");
  }

  [Fact]
  public async Task GenerateNextStepAsync_FullHallucinationScenario()
  {
    // Arrange — the exact malformed response the model produced in the chat export
    var ollamaResponse = new { response = """{"action": "execute_command", "tool": "remote_execute", "command": "Test-Connection -ComputerName google.com -Count 1", "parameters": {"target_agent_name": "ians-r16"}, "reasoning": "ping from agent"}""" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("ping google from ians-r16", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be("execute");
    result.Params.Should().ContainKey("agent_id");
    result.Params["agent_id"].Should().Be("ians-r16");
    result.Params.Should().ContainKey("command");
  }

  [Fact]
  public async Task GenerateNextStepAsync_NormalizesTerminalToExecute()
  {
    // Arrange — model uses "terminal" as tool name (from chat export)
    var ollamaResponse = new
    {
      response = """
{
  "action": "execute_command",
  "tool": "terminal",
  "command": "Get-ADPrincipalGroupMembership -Identity 'ian@westerfield.cloud' | Select-Object Name",
  "explanation": "Lists AD groups"
}
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("what ad groups am I in?", new List<StepResult>(), null);

    // Assert — "terminal" should normalize to "execute"
    result.Tool.Should().Be("execute");
    result.Params["command"].Should().Be("Get-ADPrincipalGroupMembership -Identity 'ian@westerfield.cloud' | Select-Object Name");
  }

  [Fact]
  public async Task GenerateNextStepAsync_ExecuteCommandWrappingListAgents()
  {
    // Arrange — model wraps list_agents inside execute_command
    // Exact pattern from chat export: {"action": "execute_command", "command": "list_agents", "explanation": "..."}
    var ollamaResponse = new { response = """{"action": "execute_command", "command": "list_agents", "explanation": "Discovers available FunnelCloud agents"}""" };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("How many agents are there?", new List<StepResult>(), null);

    // Assert — should resolve to list_agents, not execute with command="list_agents"
    result.Tool.Should().Be("list_agents");
    result.Params.Should().NotContainKey("command");
  }

  [Fact]
  public async Task GenerateNextStepAsync_StripsR1ThinkingBlocks()
  {
    // Arrange — R1-Distill model wraps response in <think>...</think> tags
    var ollamaResponse = new
    {
      response = """
<think>
The user wants to run hostname on ians-r16. I should use the execute tool with agent_id="ians-r16" and command="hostname".
</think>
{"tool": "execute", "params": {"agent_id": "ians-r16", "command": "hostname"}, "reasoning": "run hostname on agent"}
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("run hostname on ians-r16", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be("execute");
    result.Params.Should().ContainKey("agent_id");
    result.Params["agent_id"].Should().Be("ians-r16");
    result.Params["command"].Should().Be("hostname");
  }

  [Fact]
  public async Task GenerateNextStepAsync_StripsThinkingWithJsonInThought()
  {
    // Arrange — thinking block contains curly braces that would confuse naive IndexOf('{')
    var ollamaResponse = new
    {
      response = """
<think>
Let me think about this. The user asked to list agents. I recall the format is {"tool": "list_agents"}.
I should respond with the proper JSON.
</think>
{"tool": "list_agents", "params": {}, "reasoning": "discover agents"}
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("list agents", new List<StepResult>(), null);

    // Assert — should parse the JSON AFTER the think block, not the one inside it
    result.Tool.Should().Be("list_agents");
  }

  [Fact]
  public async Task GenerateNextStepAsync_HandlesMarkdownCodeFence()
  {
    // Arrange — model wraps JSON in markdown code fence
    var ollamaResponse = new
    {
      response = """
Here is the tool call:

```json
{"tool": "execute", "params": {"agent_id": "r730xd", "command": "Get-Process"}, "reasoning": "list processes"}
```
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("list processes on r730xd", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be("execute");
    result.Params["agent_id"].Should().Be("r730xd");
    result.Params["command"].Should().Be("Get-Process");
  }

  [Fact]
  public async Task GenerateNextStepAsync_HandlesThinkingPlusCodeFence()
  {
    // Arrange — R1 thinking block + markdown code fence (worst case combo)
    var ollamaResponse = new
    {
      response = """
<think>
I need to check the size of directories. The agent is ians-r16. Let me format the execute call properly.
</think>

```json
{"tool": "execute", "params": {"agent_id": "ians-r16", "command": "Get-ChildItem C:\\Code -Directory | Select-Object Name, @{N='SizeGB';E={(Get-ChildItem $_.FullName -Recurse -File | Measure-Object Length -Sum).Sum/1GB}} | Sort-Object SizeGB -Descending | Select-Object -First 5"}, "reasoning": "get directory sizes"}
```
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("show largest dirs on ians-r16", new List<StepResult>(), null);

    // Assert
    result.Tool.Should().Be("execute");
    result.Params["agent_id"].Should().Be("ians-r16");
  }

  [Fact]
  public async Task GenerateNextStepAsync_HandlesOrphanedCloseThinkTag()
  {
    // Arrange — model outputs old-format JSON, then </think>, then actual tool JSON
    // This happens when model's thinking gets truncated or malformed
    var ollamaResponse = new
    {
      response = """
{
  "action": "execute",
  "reasoning": "I need to run the command",
  "command": "hostname"
}</think>{
  "tool": "execute",
  "params": {
    "agent_id": "ians-r16",
    "command": "hostname"
  },
  "reasoning": "Running hostname command"
}
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("run hostname on ians-r16", new List<StepResult>(), null);

    // Assert — should parse the JSON AFTER the orphaned </think>, not the malformed JSON before it
    result.Tool.Should().Be("execute");
    result.Params["agent_id"].Should().Be("ians-r16");
    result.Params["command"].Should().Be("hostname");
  }

  [Fact]
  public async Task GenerateNextStepAsync_NaturalLanguageOnly_ReturnsParseError()
  {
    // Arrange — model responds with natural language, no JSON at all
    var ollamaResponse = new
    {
      response = "I'll help you with that. Let me run the hostname command on ians-r16 to check the machine name."
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("run hostname", new List<StepResult>(), null);

    // Assert — should fall through to parse error (complete tool)
    result.Tool.Should().Be("complete");
    result.Params.Should().ContainKey("answer");
    result.Params["answer"]!.ToString().Should().Contain("parse");
  }

  [Fact]
  public async Task GenerateNextStepAsync_ExtractsThinkingContent()
  {
    // Arrange — R1-Distill model wraps response in <think>...</think> tags
    var ollamaResponse = new
    {
      response = """
<think>
The user wants to calculate 2+2. This is a simple arithmetic operation.
I should respond with the complete tool since this is basic math.
</think>
{"tool": "complete", "params": {"answer": "4"}, "reasoning": "simple math"}
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("What is 2+2?", new List<StepResult>(), null);

    // Assert — should extract the thinking content
    result.ThinkingContent.Should().NotBeNullOrEmpty();
    result.ThinkingContent.Should().Contain("simple arithmetic operation");
    result.ThinkingContent.Should().Contain("basic math");
  }

  [Fact]
  public async Task GenerateNextStepAsync_NoThinkingBlock_ReturnsEmptyThinkingContent()
  {
    // Arrange — model responds without thinking block
    var ollamaResponse = new
    {
      response = """{"tool": "list_agents", "params": {}, "reasoning": "discover agents"}"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("list agents", new List<StepResult>(), null);

    // Assert — no thinking content when no <think> block
    result.ThinkingContent.Should().BeNullOrEmpty();
  }

  [Fact]
  public async Task GenerateNextStepAsync_HandlesMarkdownTextBeforeJson()
  {
    // Arrange — model outputs markdown explanation BEFORE the JSON tool call
    // This happens when model wants to "explain" before calling the tool
    var ollamaResponse = new
    {
      response = """
**Command:** Get-ADPrincipalGroupMembership -Identity $env:USERNAME
**Explanation:** This command lists all AD groups the current user belongs to.
{
  "action": "execute_command",
  "command": "Get-ADPrincipalGroupMembership -Identity $env:USERNAME | Select-Object Name",
  "explanation": "Listing AD group membership"
}
"""
    };
    var client = CreateMockHttpClient(HttpStatusCode.OK, ollamaResponse);
    var engine = CreateEngine(client);

    // Act
    var result = await engine.GenerateNextStepAsync("what ad groups am I in?", new List<StepResult>(), null);

    // Assert — should extract JSON despite markdown prefix, normalize execute_command to execute
    result.Tool.Should().Be("execute");
    result.Params["command"].Should().Be("Get-ADPrincipalGroupMembership -Identity $env:USERNAME | Select-Object Name");
  }

  #endregion

  #region Helper Methods

  private static HttpClient CreateMockHttpClient<T>(HttpStatusCode statusCode, T? content)
  {
    var json = content != null ? JsonSerializer.Serialize(content) : "";
    var handlerMock = new Mock<HttpMessageHandler>();
    handlerMock.Protected()
        .Setup<Task<HttpResponseMessage>>("SendAsync",
            ItExpr.IsAny<HttpRequestMessage>(),
            ItExpr.IsAny<CancellationToken>())
        .ReturnsAsync(() => new HttpResponseMessage
        {
          StatusCode = statusCode,
          Content = content != null
                ? new StringContent(json)
                : null
        });

    return new HttpClient(handlerMock.Object);
  }

  #endregion
}

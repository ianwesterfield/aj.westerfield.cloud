using System.Text.Json.Serialization;

namespace AJ.Orchestrator.Abstractions.Models;

// ============================================================================
// Workspace Requests
// ============================================================================

public record SetWorkspaceRequest(string Cwd, string? UserId = null);

public record CloneWorkspaceRequest(
    string RepoUrl,
    string? Branch = null,
    string? TargetName = null,
    string? UserId = null
);

public record CloneWorkspaceResponse(
    bool Success,
    string WorkspacePath,
    string Message,
    WorkspaceContext? Context = null
);

// ============================================================================
// Step Generation
// ============================================================================

public record NextStepRequest(
    string Task,
    List<StepResult>? History = null,
    WorkspaceContext? WorkspaceContext = null,
    string? UserId = null
);

public record NextStepResponse(
    string Tool,
    Dictionary<string, object?> Params,
    string? BatchId,
    string Reasoning,
    bool IsBatch = false
);

// ============================================================================
// Task Execution (Streaming)
// ============================================================================

public record RunTaskRequest(
    string Task,
    string WorkspaceRoot,
    string? UserId = null,
    List<Dictionary<string, object?>>? MemoryContext = null,
    int MaxSteps = 100,
    bool PreserveState = false,
    string? Model = null
);

/// <summary>
/// Server-sent event during task execution.
/// </summary>
public record TaskEvent
{
  [JsonPropertyName("event_type")]
  public string EventType { get; init; } = "";

  // Alias for EventType for simpler code
  [JsonIgnore]
  public string Type { get => EventType; init => EventType = value; }

  [JsonPropertyName("step_num")]
  public int StepNum { get; init; }

  public string? Tool { get; init; }
  public string Status { get; init; } = "";
  public Dictionary<string, object?>? Result { get; init; }
  public bool Done { get; init; }
  public string? Error { get; init; }
}

// ============================================================================
// Batch Execution
// ============================================================================

public record ExecuteBatchRequest(
    List<Step> Steps,
    string BatchId,
    WorkspaceContext? WorkspaceContext = null,
    string? UserId = null
);

public record BatchResult
{
  public required string BatchId { get; init; }
  public List<StepResult> Successful { get; init; } = new();
  public List<ErrorMetadata> Failed { get; init; } = new();
  public double Duration { get; init; }

  public int SuccessfulCount => Successful.Count;
  public int FailedCount => Failed.Count;
}

// ============================================================================
// Intent Classification
// ============================================================================

public record ClassifyRequest(string Text, string? Context = null);

public record ClassifyResponse(
    string Intent,
    double Confidence,
    string Reason = ""
);

// ============================================================================
// Additional Response/Request types
// ============================================================================

public record SetWorkspaceResponse
{
  public required bool Success { get; init; }
  public string? WorkspacePath { get; init; }
  public string? SessionId { get; init; }
  public string? Error { get; init; }
}

public record ResetStateRequest(string? SessionId = null);

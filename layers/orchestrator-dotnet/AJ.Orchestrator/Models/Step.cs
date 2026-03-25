namespace AJ.Orchestrator.Models;

/// <summary>
/// Status of a step execution.
/// </summary>
public enum StepStatus
{
    Pending,
    Running,
    Success,
    Failed,
    Skipped
}

/// <summary>
/// Categories of execution errors.
/// </summary>
public enum ErrorType
{
    Timeout,
    PermissionDenied,
    InvalidParams,
    ExecutionError,
    SandboxViolation,
    ResourceLimit,
    Unknown
}

/// <summary>
/// Single tool invocation step.
/// Represents one atomic operation in a task decomposition.
/// </summary>
public record Step
{
    public required string StepId { get; init; }
    public required string Tool { get; init; }
    public Dictionary<string, object?> Params { get; init; } = new();
    public string? BatchId { get; init; }
    public string Reasoning { get; init; } = "";
    public StepStatus Status { get; init; } = StepStatus.Pending;
    public List<string> DependsOn { get; init; } = new();
}

/// <summary>
/// Result of executing a single step.
/// </summary>
public record StepResult
{
    public required string StepId { get; init; }
    public string? Tool { get; init; }
    public Dictionary<string, object?>? Params { get; init; }
    public StepStatus Status { get; init; }
    public string? Output { get; init; }
    public string? Error { get; init; }
    public double ExecutionTime { get; init; }
}

/// <summary>
/// Detailed error information for failed steps.
/// </summary>
public record ErrorMetadata
{
    public required string StepId { get; init; }
    public required string Error { get; init; }
    public ErrorType ErrorType { get; init; } = ErrorType.Unknown;
    public bool Recoverable { get; init; }
    public string? Suggestion { get; init; }
}

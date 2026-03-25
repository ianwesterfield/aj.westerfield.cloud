namespace AJ.Orchestrator.Abstractions.Models;

/// <summary>
/// Workspace scoping model.
/// Defines the active directory and permissions for all operations.
/// </summary>
public record WorkspaceContext
{
  /// <summary>Current working directory.</summary>
  public required string Cwd { get; init; }

  /// <summary>Root directory (sandbox boundary).</summary>
  public required string WorkspaceRoot { get; init; }

  /// <summary>Cached directory listing.</summary>
  public List<string> AvailablePaths { get; init; } = new();

  /// <summary>Admin valve: allow parallel execution.</summary>
  public bool ParallelEnabled { get; init; }

  /// <summary>Max concurrent tasks.</summary>
  public int MaxParallelTasks { get; init; } = 4;

  /// <summary>Languages user can execute.</summary>
  public List<string> AllowedLanguages { get; init; } = new() { "python", "powershell", "node" };

  /// <summary>Can run arbitrary code.</summary>
  public bool AllowCodeExecution { get; init; }

  /// <summary>Can write files.</summary>
  public bool AllowFileWrite { get; init; }

  /// <summary>Can run shell commands.</summary>
  public bool AllowShellCommands { get; init; }

  /// <summary>Timeout per task (seconds).</summary>
  public int MaxExecutionTime { get; init; } = 30;
}

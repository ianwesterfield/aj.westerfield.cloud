using AJ.Orchestrator.Abstractions.Models;

namespace AJ.Orchestrator.Abstractions.Services;

/// <summary>
/// Reasoning engine that coordinates LLM calls for step generation.
/// </summary>
public interface IReasoningEngine
{
  /// <summary>
  /// Classify user intent as 'task' or 'casual'.
  /// </summary>
  Task<ClassifyResponse> ClassifyIntentAsync(string text, string? context = null);

  /// <summary>
  /// Generate the next step based on task and history.
  /// </summary>
  Task<NextStepResponse> GenerateNextStepAsync(
      string task,
      List<StepResult> history,
      WorkspaceContext? workspace = null);

  /// <summary>
  /// Run a complete task with streaming updates.
  /// </summary>
  IAsyncEnumerable<TaskEvent> RunTaskStreamAsync(
      RunTaskRequest request,
      CancellationToken ct = default);
}

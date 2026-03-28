using System.Text.Json.Serialization;

namespace AJ.Orchestrator.Abstractions.Models.Classification;

/// <summary>
/// Request to classify user intent.
/// </summary>
public record ClassifyRequest
{
    [JsonPropertyName("text")]
    public required string Text { get; init; }

    [JsonPropertyName("context")]
    public string? Context { get; init; }
}

/// <summary>
/// Classification result with intent and confidence.
/// </summary>
public record ClassifyResponse(
    [property: JsonPropertyName("intent")] string Intent,
    [property: JsonPropertyName("confidence")] double Confidence,
    [property: JsonPropertyName("reason")] string Reason = ""
);

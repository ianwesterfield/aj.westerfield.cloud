using System.Diagnostics;
using System.Text.RegularExpressions;
using AJ.Orchestrator.Abstractions.Models.Skills;
using AJ.Orchestrator.Abstractions.Services;
using Microsoft.Extensions.Logging;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace AJ.Orchestrator.Domain.Services;

/// <summary>
/// Executes YAML-defined skills deterministically, bypassing the LLM.
/// This is the core of the V2 architecture - code handles known patterns.
/// </summary>
public class SkillExecutor : ISkillExecutor
{
  private readonly ILogger<SkillExecutor> _logger;
  private readonly IGrpcAgentClient _agentClient;
  private readonly List<ExecutableSkill> _skills = [];
  private readonly IDeserializer _yamlDeserializer;

  // Minimum confidence required to auto-execute a skill
  private const double MinConfidence = 0.5;

  public SkillExecutor(
      ILogger<SkillExecutor> logger,
      IGrpcAgentClient agentClient)
  {
    _logger = logger;
    _agentClient = agentClient;

    _yamlDeserializer = new DeserializerBuilder()
        .WithNamingConvention(CamelCaseNamingConvention.Instance)
        .IgnoreUnmatchedProperties()
        .Build();
  }

  /// <summary>
  /// Load all YAML skill files from the specified paths
  /// </summary>
  public async Task LoadSkillsAsync(IEnumerable<string> skillPaths, CancellationToken ct = default)
  {
    _skills.Clear();

    foreach (var basePath in skillPaths)
    {
      if (!Directory.Exists(basePath))
      {
        _logger.LogWarning("Skill path does not exist: {Path}", basePath);
        continue;
      }

      var yamlFiles = Directory.GetFiles(basePath, "skill.yaml", SearchOption.AllDirectories);
      _logger.LogInformation("Found {Count} YAML skill files in {Path}", yamlFiles.Length, basePath);

      foreach (var file in yamlFiles)
      {
        if (ct.IsCancellationRequested) break;

        try
        {
          var yaml = await File.ReadAllTextAsync(file, ct);
          var skill = ParseYamlSkill(yaml, file);
          if (skill != null)
          {
            _skills.Add(skill);
            _logger.LogInformation("Loaded executable skill: {Name} from {Path}", skill.Name, file);
          }
        }
        catch (Exception ex)
        {
          _logger.LogError(ex, "Failed to load skill from {File}", file);
        }
      }
    }

    _logger.LogInformation("Loaded {Count} executable skills total", _skills.Count);
  }

  private ExecutableSkill? ParseYamlSkill(string yaml, string sourcePath)
  {
    try
    {
      var raw = _yamlDeserializer.Deserialize<YamlSkillRaw>(yaml);
      if (raw == null || string.IsNullOrEmpty(raw.Name))
        return null;

      return new ExecutableSkill
      {
        Name = raw.Name,
        Version = raw.Version,
        Triggers = new SkillTriggers
        {
          Patterns = raw.Triggers?.Patterns ?? [],
          Keywords = raw.Triggers?.Keywords ?? []
        },
        Parameters = raw.Parameters?.ToDictionary(
            kv => kv.Key,
            kv => new SkillParameter
            {
              Pattern = kv.Value.Pattern ?? "",
              Required = kv.Value.Required,
              Description = kv.Value.Description,
              Default = kv.Value.Default
            }) ?? [],
        Target = new SkillTarget
        {
          Agent = raw.Target?.Agent ?? "",
          Platform = raw.Target?.Platform,
          Description = raw.Target?.Description
        },
        Workflow = new SkillWorkflow
        {
          Steps = raw.Workflow?.Steps?.Select(s => new WorkflowStep
          {
            Name = s.Name ?? "Step",
            Command = s.Command ?? "",
            ContinueOnError = s.ContinueOnError,
            TimeoutSeconds = s.TimeoutSeconds > 0 ? s.TimeoutSeconds : 30
          }).ToList() ?? []
        },
        Responses = new SkillResponses
        {
          Success = raw.Responses?.Success ?? "Done.",
          Partial = raw.Responses?.Partial,
          Failure = raw.Responses?.Failure ?? "Failed."
        },
        SourcePath = sourcePath
      };
    }
    catch (Exception ex)
    {
      _logger.LogWarning(ex, "Failed to parse YAML skill from {Path}", sourcePath);
      return null;
    }
  }

  public SkillMatch? TryMatch(string userInput)
  {
    var input = userInput.ToLowerInvariant();
    SkillMatch? bestMatch = null;
    double bestScore = 0;

    foreach (var skill in _skills)
    {
      var (score, matchedBy) = ScoreSkill(skill, input);

      if (score > bestScore)
      {
        // Try to extract required parameters
        var parameters = ExtractParameters(skill, userInput);
        var missingRequired = skill.Parameters
            .Where(p => p.Value.Required && !parameters.ContainsKey(p.Key))
            .Select(p => p.Key)
            .ToList();

        if (missingRequired.Count > 0)
        {
          _logger.LogDebug("Skill {Name} matched but missing required parameters: {Missing}",
              skill.Name, string.Join(", ", missingRequired));
          continue;
        }

        bestScore = score;
        bestMatch = new SkillMatch
        {
          Skill = skill,
          Parameters = parameters,
          Confidence = score,
          MatchedBy = matchedBy
        };
      }
    }

    if (bestMatch != null && bestMatch.Confidence >= MinConfidence)
    {
      _logger.LogInformation("Matched skill {Name} with confidence {Confidence:P0} via {MatchedBy}",
          bestMatch.Skill.Name, bestMatch.Confidence, bestMatch.MatchedBy);
      return bestMatch;
    }

    return null;
  }

  private (double score, string? matchedBy) ScoreSkill(ExecutableSkill skill, string input)
  {
    // Check regex patterns - highest priority
    foreach (var pattern in skill.Triggers.Patterns)
    {
      try
      {
        if (Regex.IsMatch(input, pattern, RegexOptions.IgnoreCase))
        {
          return (0.9, $"pattern: {pattern}");
        }
      }
      catch (RegexParseException ex)
      {
        _logger.LogWarning("Invalid regex pattern in skill {Name}: {Pattern} - {Error}",
            skill.Name, pattern, ex.Message);
      }
    }

    // Check keywords - lower priority, score based on match count
    var keywordMatches = skill.Triggers.Keywords.Count(kw =>
        input.Contains(kw, StringComparison.OrdinalIgnoreCase));

    if (keywordMatches > 0)
    {
      var ratio = (double)keywordMatches / skill.Triggers.Keywords.Count;
      // Need at least 2 keyword matches for decent confidence
      if (keywordMatches >= 2)
      {
        return (0.5 + (ratio * 0.3), $"keywords: {keywordMatches}/{skill.Triggers.Keywords.Count}");
      }
    }

    return (0, null);
  }

  private Dictionary<string, string> ExtractParameters(ExecutableSkill skill, string userInput)
  {
    var result = new Dictionary<string, string>();

    foreach (var (name, param) in skill.Parameters)
    {
      try
      {
        var match = Regex.Match(userInput, param.Pattern, RegexOptions.IgnoreCase);
        if (match.Success && match.Groups.Count > 1)
        {
          result[name] = match.Groups[1].Value;
          _logger.LogDebug("Extracted {Name}={Value} from input", name, result[name]);
        }
        else if (!param.Required && param.Default != null)
        {
          result[name] = param.Default;
        }
      }
      catch (RegexParseException ex)
      {
        _logger.LogWarning("Invalid parameter pattern for {Name}: {Pattern} - {Error}",
            name, param.Pattern, ex.Message);
      }
    }

    return result;
  }

  public async Task<SkillExecutionResult> ExecuteAsync(SkillMatch match, CancellationToken ct = default)
  {
    var sw = Stopwatch.StartNew();
    var stepResults = new List<StepExecutionResult>();
    var allSuccess = true;
    string? lastError = null;

    _logger.LogInformation("Executing skill {Name} on agent {Agent} with params: {@Params}",
        match.Skill.Name, match.Skill.Target.Agent, match.Parameters);

    // First, verify agent is online
    var agents = await _agentClient.DiscoverAgentsAsync(ct);
    var targetAgent = agents.FirstOrDefault(a =>
        a.AgentId.Equals(match.Skill.Target.Agent, StringComparison.OrdinalIgnoreCase));

    if (targetAgent == null)
    {
      return new SkillExecutionResult
      {
        Success = false,
        Message = SubstituteParams(match.Skill.Responses.Failure, match.Parameters,
            $"Agent '{match.Skill.Target.Agent}' is not online"),
        StepResults = [],
        DurationMs = sw.ElapsedMilliseconds
      };
    }

    // Execute each workflow step
    foreach (var step in match.Skill.Workflow.Steps)
    {
      if (ct.IsCancellationRequested)
        break;

      var command = SubstituteParams(step.Command, match.Parameters);
      _logger.LogInformation("Step '{Step}': {Command}", step.Name, command);

      var stepSw = Stopwatch.StartNew();
      var execResult = await _agentClient.ExecuteAsync(
          match.Skill.Target.Agent,
          command,
          step.TimeoutSeconds,
          ct);
      stepSw.Stop();

      var stepResult = new StepExecutionResult
      {
        StepName = step.Name,
        Success = execResult.Success,
        Output = execResult.Stdout,
        Error = execResult.Stderr ?? execResult.ErrorMessage,
        DurationMs = stepSw.ElapsedMilliseconds
      };
      stepResults.Add(stepResult);

      if (!execResult.Success)
      {
        allSuccess = false;
        lastError = stepResult.Error;

        if (!step.ContinueOnError)
        {
          _logger.LogWarning("Step '{Step}' failed, stopping workflow: {Error}", step.Name, lastError);
          break;
        }
        _logger.LogWarning("Step '{Step}' failed but continuing: {Error}", step.Name, lastError);
      }
      else
      {
        _logger.LogInformation("Step '{Step}' succeeded", step.Name);
      }
    }

    sw.Stop();

    // Build response message
    string message;
    if (allSuccess)
    {
      message = SubstituteParams(match.Skill.Responses.Success, match.Parameters);
    }
    else if (stepResults.Any(s => s.Success) && match.Skill.Responses.Partial != null)
    {
      message = SubstituteParams(match.Skill.Responses.Partial, match.Parameters, lastError);
    }
    else
    {
      message = SubstituteParams(match.Skill.Responses.Failure, match.Parameters, lastError);
    }

    return new SkillExecutionResult
    {
      Success = allSuccess,
      Message = message,
      StepResults = stepResults,
      DurationMs = sw.ElapsedMilliseconds
    };
  }

  private static string SubstituteParams(string template, Dictionary<string, string> parameters, string? error = null)
  {
    var result = template;

    foreach (var (name, value) in parameters)
    {
      result = result.Replace($"{{{{{name}}}}}", value);
    }

    if (error != null)
    {
      result = result.Replace("{{error}}", error);
    }

    return result;
  }

  public IEnumerable<ExecutableSkill> GetAllSkills() => _skills.AsReadOnly();

  // Internal classes for YAML deserialization
  private class YamlSkillRaw
  {
    public string Name { get; set; } = "";
    public int Version { get; set; } = 1;
    public YamlTriggers? Triggers { get; set; }
    public Dictionary<string, YamlParameter>? Parameters { get; set; }
    public YamlTarget? Target { get; set; }
    public YamlWorkflow? Workflow { get; set; }
    public YamlResponses? Responses { get; set; }
  }

  private class YamlTriggers
  {
    public List<string> Patterns { get; set; } = [];
    public List<string> Keywords { get; set; } = [];
  }

  private class YamlParameter
  {
    public string Pattern { get; set; } = "";
    public bool Required { get; set; } = true;
    public string? Description { get; set; }
    public string? Default { get; set; }
  }

  private class YamlTarget
  {
    public string Agent { get; set; } = "";
    public string? Platform { get; set; }
    public string? Description { get; set; }
  }

  private class YamlWorkflow
  {
    public List<YamlStep>? Steps { get; set; }
  }

  private class YamlStep
  {
    public string? Name { get; set; }
    public string? Command { get; set; }
    public bool ContinueOnError { get; set; }
    public int TimeoutSeconds { get; set; } = 30;
  }

  private class YamlResponses
  {
    public string Success { get; set; } = "Done.";
    public string? Partial { get; set; }
    public string Failure { get; set; } = "Failed.";
  }
}

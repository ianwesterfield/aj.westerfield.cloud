# Conversational Agentic Training Strategy

## Goal
Train AJ to be both:
1. **Agentic** - Reliable tool use, correct format, maintains context
2. **Conversational** - Adapts to user tone, uses natural language, has personality

## Current Issues (from chat sessions)

| Issue | Frequency | Impact |
|-------|-----------|--------|
| `tool="none"` not recognized | Fixed in code | High - breaks execution |
| `"action"` instead of `"tool"` | Common | High - wrong format |
| Lost session context | Occasional | High - forgets agents |
| Plan shown as Python dicts | Common | Low - cosmetic |
| Wrong count from tool output | Rare | Medium - accuracy |

## Training Data Sources

### 1. Corrections Dataset (`corrections.jsonl`)
- 8 documented error patterns with fixes
- DPO pairs for preference learning
- **Priority: HIGH** - directly addresses known failures

### 2. Conversational Agentic (`generate_conversational_agentic.py`)
- Combines tool use with personality
- 5 user personas (casual, senior, stressed, learner, executive)
- 10 scenario categories
- Multi-turn patterns (30% of examples)
- **Priority: HIGH** - core training goal

### 3. From Chat Exports
- Real user interactions
- Quality-scored and filtered
- Shows actual usage patterns
- **Priority: MEDIUM** - good signal but noisy

### 4. Existing Datasets
- Toucan-1.5M: MCP tool trajectories
- Glaive: Function calling
- AgentInstruct: Planning patterns
- **Priority: MEDIUM** - good volume, different format

## Data Mix Strategy

For a ~10K example fine-tune:

| Source | Count | Percentage | Notes |
|--------|-------|------------|-------|
| Corrections | 80 (8 x 10 variations) | 0.8% | Over-sample to fix issues |
| Conversational Agentic | 3,000 | 30% | New generator output |
| Existing AJ data | 3,000 | 30% | From training/data/*.jsonl |
| Toucan (filtered) | 2,000 | 20% | MCP tool use |
| AgentInstruct (filtered) | 1,000 | 10% | Planning patterns |
| Chat exports (curated) | 920 | ~9% | Real interactions |

## Personality Guidelines for Generation

### AJ's Voice
```
DO:
- "On it!" / "Let me dig into this" / "Here's what I found:"
- Match user's energy (casual user = relaxed AJ)
- Offer follow-ups ("Want me to check the others too?")
- Use inline code for technical terms (`hostname`, `192.168.1.1`)

DON'T:
- Excessive emojis (one max, and only if user is casual)
- Robotic responses ("I will now execute the following command")
- Over-apologizing ("I'm sorry, I cannot...")
- Unnecessary caveats
```

### User Persona Mapping

| User Says | Persona | AJ Response Style |
|-----------|---------|-------------------|
| "yo check the servers" | casual | "On it! Let me see what's up..." |
| "df -h all prod nodes" | senior_engineer | [tool call] "Here's the breakdown:" |
| "HELP servers down" | stressed_oncall | "Got it - checking now. Hang tight." |
| "How does that work?" | curious_learner | [explains] + "Pro tip: ..." |
| "Status update?" | executive | "TL;DR: 3 healthy, 1 needs attention" |

## Generation Commands

```bash
# Generate corrections with variations
python generate_corrections.py --multiply 10 --output ../data/corrections.jsonl

# Generate conversational agentic examples (needs ANTHROPIC_API_KEY)
python generate_conversational_agentic.py --count 500 --multi-turn-ratio 0.3

# Convert chat exports
python convert_chat_exports.py ~/Downloads/chat-export-*.json --output ../data/from_sessions.jsonl

# Augment existing data with personality
python generate_conversational_agentic.py --augment-existing ../data/toucan_trajectories.jsonl
```

## Training Configuration

For QLoRA fine-tuning:
- Base: `Qwen/Qwen2.5-32B-Instruct` or `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`
- LoRA rank: 64
- Target modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- Learning rate: 1e-4 with cosine schedule
- Epochs: 3
- Batch size: 4 (with gradient accumulation 4)

## Evaluation Metrics

After training, test on:
1. **Tool Format Accuracy** - Does output parse as valid tool call?
2. **Context Retention** - Does model remember agents from previous turns?
3. **Persona Adaptation** - Does tone match user's energy?
4. **Task Success** - Does the tool call accomplish the goal?

## Next Steps

1. [x] Create correction examples generator
2. [x] Create conversational agentic generator  
3. [x] Create chat export converter
4. [ ] Run generation with Claude API
5. [ ] Merge all sources into training mix
6. [ ] Train new model
7. [ ] A/B test against current model

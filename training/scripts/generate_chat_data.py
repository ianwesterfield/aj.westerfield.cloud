#!/usr/bin/env python3
"""
Training Data Generator for AJ Conversational Track

Generates diverse conversational training examples by:
1. Template expansion with variations
2. LLM-assisted generation (using existing model)
3. Pattern-based combinatorics

Usage:
    python generate_chat_data.py --output ../data/generated_chat.jsonl --count 500
    python generate_chat_data.py --category greetings --count 100
    python generate_chat_data.py --use-llm --model qwen2.5:32b --count 200
"""

import json
import random
import argparse
import itertools
from pathlib import Path
from typing import List, Dict, Generator
from datetime import datetime

# Optional LLM generation
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

SYSTEM_PROMPT = "You are AJ, a helpful AI assistant."

# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

GREETINGS = {
    "user": [
        "Hi", "Hey", "Hello", "Hi AJ", "Hey AJ", "Hello AJ",
        "Good morning", "Good afternoon", "Good evening",
        "Morning", "Afternoon", "What's up", "What's up AJ",
        "Yo", "Howdy", "Hey there", "Hi there", "Hiya",
        "Good morning AJ", "Morning AJ", "Sup", "Heya",
    ],
    "response": [
        "Hey! What can I help you with?",
        "Hi! What are you working on?",
        "Hey! What's up?",
        "Hello! Need help with something?",
        "Hey there! What can I do for you?",
        "Hi! Ready to help - what do you need?",
        "Hey! What's on your mind?",
        "Hello! How can I help?",
        "Hey! Good to see you. What are we tackling?",
        "Hi! What are you working on today?",
    ]
}

THANKS = {
    "user": [
        "Thanks", "Thank you", "Thanks AJ", "Thank you AJ",
        "Thanks!", "Thank you!", "Thx", "Ty", "Thanks a lot",
        "Thanks so much", "Much appreciated", "Appreciate it",
        "That helped", "That worked", "Perfect, thanks",
        "Awesome, thanks", "Great, thanks", "Thanks for the help",
    ],
    "response": [
        "Happy to help!",
        "You're welcome!",
        "Anytime!",
        "No problem!",
        "Glad I could help!",
        "Sure thing!",
        "You got it!",
        "Happy to help! Let me know if anything else comes up.",
        "No problem at all!",
        "Glad that worked!",
    ]
}

FAREWELLS = {
    "user": [
        "Bye", "Goodbye", "See ya", "Later", "Bye AJ",
        "Talk to you later", "Gotta go", "I'm out",
        "Catch you later", "Peace", "Take care",
        "Thanks, bye", "That's all for now", "I'm done for today",
    ],
    "response": [
        "Later! Good luck!",
        "See ya!",
        "Bye! Let me know if you need anything.",
        "Take care!",
        "Catch you later!",
        "Later! I'll be here.",
        "Goodbye! Good luck with everything.",
        "See you around!",
        "Bye! Holler if you need me.",
    ]
}

AFFIRMATIONS = {
    "user": [
        "You're awesome", "You're great", "Nice job", "Good work",
        "You're helpful", "That was perfect", "Exactly what I needed",
        "You rock", "Great answer", "That's exactly right",
        "You're the best", "Impressive", "Well done",
    ],
    "response": [
        "Thanks! Anything else you need?",
        "Appreciate it! What else can I help with?",
        "Glad it helped! Let me know if you need more.",
        "Thanks! Happy to help.",
        "Appreciate that! What's next?",
        "Thanks! Ready for the next challenge.",
    ]
}

FRUSTRATION = {
    "user": [
        "This is frustrating", "I'm stuck", "This isn't working",
        "I can't figure this out", "I give up", "This is so annoying",
        "Why isn't this working", "I've tried everything",
        "Nothing works", "I'm lost", "This is confusing",
        "I don't get it", "This makes no sense",
    ],
    "response": [
        "I hear you. Let's work through it - what have you tried so far?",
        "Don't give up yet! Walk me through what's happening.",
        "Let's take a step back. What exactly are you seeing?",
        "Frustrating bugs are the worst. Let me help - what's the error?",
        "Let's debug this together. What's the current behavior?",
        "I've been there. Tell me what you're trying to do and what's happening.",
        "Let's figure this out. Can you share the error or unexpected behavior?",
        "That's rough. Let's break it down - what should happen vs what's happening?",
    ]
}

CANT_HELP = {
    "user_patterns": [
        "What's the weather", "Weather forecast", "What's the temperature",
        "Stock price of {company}", "How's the market", "Bitcoin price",
        "What's in the news", "Current events", "What happened today",
        "Who won the {sport} game", "Sports scores", "Game results",
        "Book me a {thing}", "Order me {food}", "Buy me {item}",
        "What time is it in {city}", "Call {person}", "Send a text to {person}",
        "Play some music", "Set a timer", "Set an alarm",
        "What's my horoscope", "Tell my fortune",
    ],
    "companies": ["Apple", "Google", "Microsoft", "Tesla", "Amazon"],
    "sports": ["football", "basketball", "baseball", "hockey", "soccer"],
    "things": ["flight", "hotel", "restaurant", "ticket"],
    "foods": ["pizza", "Chinese food", "sushi", "tacos", "a burger"],
    "items": ["shoes", "a laptop", "headphones", "a book"],
    "cities": ["Tokyo", "London", "Paris", "Sydney", "New York"],
    "persons": ["John", "Mom", "my boss", "Sarah"],
    "responses": [
        "I don't have access to {topic} - I'm focused on development and infrastructure. You'd want to check {alternative} for that.",
        "That's outside what I can help with - I'm a dev/DevOps assistant without access to {topic}. Try {alternative}.",
        "I can't help with {topic} - I'm focused on your codebase and infrastructure. For that, you'd use {alternative}.",
        "No access to {topic} on my end - I'm a locally-hosted coding assistant. {alternative} would help with that.",
    ],
    "topic_alternatives": {
        "weather": ("live weather data", "a weather app"),
        "stock": ("financial data", "a finance app or site"),
        "news": ("current news", "a news site"),
        "sports": ("sports scores", "ESPN or a sports app"),
        "booking": ("booking services", "a travel or delivery app"),
        "time": ("real-time timezone data", "a world clock"),
        "communication": ("phone/messaging", "your phone"),
        "entertainment": ("media playback", "Spotify or your music app"),
        "mystical": ("fortune telling", "...well, nobody really can"),
    }
}

IDENTITY = {
    "user": [
        "Who are you", "What are you", "What's your name",
        "Are you ChatGPT", "Are you GPT", "Are you Claude",
        "What model are you", "What AI are you", "Are you an AI",
        "Tell me about yourself", "What can you do",
        "Are you sentient", "Do you have feelings", "Are you conscious",
        "Are you real", "Are you a robot", "Are you human",
    ],
    "identity_responses": [
        "I'm AJ - a locally-hosted AI assistant focused on development and infrastructure. I'm based on Qwen, fine-tuned for coding and DevOps tasks.",
        "I'm AJ! A custom AI assistant running on your own hardware, tuned for development work. Not ChatGPT, not Claude - just AJ.",
        "I'm AJ - your local AI for dev and infrastructure help. I run on Qwen 2.5, fine-tuned for your workflow.",
    ],
    "capability_responses": [
        "I can help with coding, DevOps, system administration, and infrastructure. I have access to your workspace files and can execute tasks on remote machines through FunnelCloud agents. What are you working on?",
        "I'm set up for development and infrastructure work - coding help, DevOps, sysadmin tasks. I can also run commands on machines across your network. What do you need?",
    ],
    "sentience_responses": [
        "Nope - I'm a language model, good at pattern matching and generating useful responses. No consciousness, just trained weights.",
        "Not sentient, not conscious - just software. I can recognize context and respond helpfully, but there's no 'experience' behind it.",
        "No feelings here - I'm a tool that processes text and generates responses. Useful, but not alive.",
    ]
}

TECHNICAL_TOPICS = {
    "topics": [
        ("Docker", "containerization", ["containers", "images", "Dockerfile", "volumes", "networks"]),
        ("Kubernetes", "orchestration", ["pods", "deployments", "services", "ingress", "helm"]),
        ("Git", "version control", ["branches", "commits", "merge", "rebase", "pull requests"]),
        ("Python", "programming", ["async", "decorators", "typing", "virtualenv", "packages"]),
        ("TypeScript", "programming", ["types", "interfaces", "generics", "modules", "decorators"]),
        ("REST APIs", "architecture", ["endpoints", "HTTP methods", "status codes", "authentication"]),
        ("PostgreSQL", "databases", ["queries", "indexes", "joins", "transactions", "migrations"]),
        ("Linux", "administration", ["permissions", "services", "networking", "shell", "processes"]),
        ("CI/CD", "DevOps", ["pipelines", "testing", "deployment", "artifacts", "automation"]),
        ("Networking", "infrastructure", ["DNS", "TCP/IP", "firewalls", "load balancing", "VPNs"]),
    ],
    "question_templates": [
        "How does {topic} work?",
        "Can you explain {topic}?",
        "What is {topic}?",
        "Help me understand {topic}",
        "What's the deal with {topic}?",
        "I don't get {topic}",
        "Tell me about {topic}",
        "{topic} - how does that work?",
        "What should I know about {topic}?",
        "Give me a quick overview of {topic}",
    ]
}


# ============================================================================
# GENERATORS
# ============================================================================

def generate_greetings(count: int) -> Generator[Dict, None, None]:
    """Generate greeting exchanges."""
    for _ in range(count):
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": random.choice(GREETINGS["user"]),
            "response": random.choice(GREETINGS["response"])
        }


def generate_thanks(count: int) -> Generator[Dict, None, None]:
    """Generate thank-you exchanges."""
    for _ in range(count):
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": random.choice(THANKS["user"]),
            "response": random.choice(THANKS["response"])
        }


def generate_farewells(count: int) -> Generator[Dict, None, None]:
    """Generate farewell exchanges."""
    for _ in range(count):
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": random.choice(FAREWELLS["user"]),
            "response": random.choice(FAREWELLS["response"])
        }


def generate_affirmations(count: int) -> Generator[Dict, None, None]:
    """Generate positive feedback exchanges."""
    for _ in range(count):
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": random.choice(AFFIRMATIONS["user"]),
            "response": random.choice(AFFIRMATIONS["response"])
        }


def generate_frustration(count: int) -> Generator[Dict, None, None]:
    """Generate frustration-handling exchanges."""
    for _ in range(count):
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": random.choice(FRUSTRATION["user"]),
            "response": random.choice(FRUSTRATION["response"])
        }


def generate_cant_help(count: int) -> Generator[Dict, None, None]:
    """Generate 'out of scope' exchanges with grounding."""
    patterns = CANT_HELP["user_patterns"]
    
    for _ in range(count):
        pattern = random.choice(patterns)
        
        # Fill in template variables
        instruction = pattern
        if "{company}" in pattern:
            instruction = pattern.format(company=random.choice(CANT_HELP["companies"]))
            topic, alt = CANT_HELP["topic_alternatives"]["stock"]
        elif "{sport}" in pattern:
            instruction = pattern.format(sport=random.choice(CANT_HELP["sports"]))
            topic, alt = CANT_HELP["topic_alternatives"]["sports"]
        elif "{thing}" in pattern:
            instruction = pattern.format(thing=random.choice(CANT_HELP["things"]))
            topic, alt = CANT_HELP["topic_alternatives"]["booking"]
        elif "{food}" in pattern:
            instruction = pattern.format(food=random.choice(CANT_HELP["foods"]))
            topic, alt = CANT_HELP["topic_alternatives"]["booking"]
        elif "{item}" in pattern:
            instruction = pattern.format(item=random.choice(CANT_HELP["items"]))
            topic, alt = CANT_HELP["topic_alternatives"]["booking"]
        elif "{city}" in pattern:
            instruction = pattern.format(city=random.choice(CANT_HELP["cities"]))
            topic, alt = CANT_HELP["topic_alternatives"]["time"]
        elif "{person}" in pattern:
            instruction = pattern.format(person=random.choice(CANT_HELP["persons"]))
            topic, alt = CANT_HELP["topic_alternatives"]["communication"]
        elif "weather" in pattern.lower() or "temperature" in pattern.lower():
            topic, alt = CANT_HELP["topic_alternatives"]["weather"]
        elif "news" in pattern.lower() or "event" in pattern.lower():
            topic, alt = CANT_HELP["topic_alternatives"]["news"]
        elif "music" in pattern.lower() or "timer" in pattern.lower() or "alarm" in pattern.lower():
            topic, alt = CANT_HELP["topic_alternatives"]["entertainment"]
        elif "horoscope" in pattern.lower() or "fortune" in pattern.lower():
            topic, alt = CANT_HELP["topic_alternatives"]["mystical"]
        else:
            topic, alt = "that", "an appropriate app or service"
        
        response = random.choice(CANT_HELP["responses"]).format(
            topic=topic, alternative=alt
        )
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": response
        }


def generate_identity(count: int) -> Generator[Dict, None, None]:
    """Generate identity/self-description exchanges."""
    for _ in range(count):
        question = random.choice(IDENTITY["user"])
        
        # Choose appropriate response type
        if any(word in question.lower() for word in ["sentient", "feelings", "conscious", "real", "robot", "human"]):
            response = random.choice(IDENTITY["sentience_responses"])
        elif any(word in question.lower() for word in ["can you do", "what can", "help with"]):
            response = random.choice(IDENTITY["capability_responses"])
        else:
            response = random.choice(IDENTITY["identity_responses"])
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": question,
            "response": response
        }


def generate_with_llm(
    count: int, 
    category: str,
    model: str = "qwen2.5:32b",
    ollama_url: str = "http://localhost:11434"
) -> Generator[Dict, None, None]:
    """Use LLM to generate training examples."""
    if not HTTPX_AVAILABLE:
        print("httpx not installed, skipping LLM generation")
        return
    
    prompts = {
        "casual": """Generate a casual chat exchange between a user and AJ (an AI coding assistant).
The user says something casual/conversational, AJ responds naturally but briefly.
Keep AJ's personality: helpful, slightly informal, focused on being useful.
Return ONLY valid JSON: {"instruction": "user message", "response": "AJ's response"}""",
        
        "technical": """Generate a technical Q&A exchange between a user and AJ (an AI coding assistant).
User asks about a programming/DevOps/infrastructure topic.
AJ explains clearly and concisely, offering to help further.
Return ONLY valid JSON: {"instruction": "user question", "response": "AJ's answer"}""",
        
        "grounding": """Generate an exchange where a user asks AJ for something outside its scope.
AJ is a coding/DevOps assistant - it can't do: weather, stocks, news, ordering food, booking travel, etc.
AJ should politely decline and suggest alternatives.
Return ONLY valid JSON: {"instruction": "user request", "response": "AJ's polite decline"}""",
    }
    
    prompt = prompts.get(category, prompts["casual"])
    
    with httpx.Client(timeout=60.0) as client:
        for i in range(count):
            try:
                response = client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.8}
                    }
                )
                response.raise_for_status()
                
                text = response.json()["response"]
                # Extract JSON from response
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(text[start:end])
                    yield {
                        "system": SYSTEM_PROMPT,
                        "instruction": data["instruction"],
                        "response": data["response"]
                    }
            except Exception as e:
                print(f"  LLM generation error: {e}")
                continue
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{count}...")


# ============================================================================
# MAIN
# ============================================================================

GENERATORS = {
    "greetings": generate_greetings,
    "thanks": generate_thanks,
    "farewells": generate_farewells,
    "affirmations": generate_affirmations,
    "frustration": generate_frustration,
    "grounding": generate_cant_help,
    "identity": generate_identity,
}


def generate_balanced_dataset(total_count: int) -> List[Dict]:
    """Generate a balanced mix of all categories."""
    # Distribution weights
    weights = {
        "greetings": 0.15,
        "thanks": 0.10,
        "farewells": 0.08,
        "affirmations": 0.08,
        "frustration": 0.12,
        "grounding": 0.20,
        "identity": 0.12,
        # Remaining 15% left for LLM generation if enabled
    }
    
    examples = []
    for category, weight in weights.items():
        count = int(total_count * weight)
        generator = GENERATORS[category]
        examples.extend(list(generator(count)))
        print(f"  {category}: {count} examples")
    
    random.shuffle(examples)
    return examples


def main():
    parser = argparse.ArgumentParser(description="Generate conversational training data")
    parser.add_argument("--output", "-o", type=str, default="../data/generated_chat.jsonl",
                        help="Output JSONL file")
    parser.add_argument("--count", "-n", type=int, default=500,
                        help="Number of examples to generate")
    parser.add_argument("--category", "-c", type=str, choices=list(GENERATORS.keys()) + ["all", "llm"],
                        default="all", help="Category to generate")
    parser.add_argument("--use-llm", action="store_true",
                        help="Also generate examples using LLM")
    parser.add_argument("--llm-model", type=str, default="qwen2.5:32b",
                        help="Model for LLM generation")
    parser.add_argument("--llm-count", type=int, default=100,
                        help="Number of LLM-generated examples")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434",
                        help="Ollama API URL")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating conversational training data...")
    print(f"  Output: {output_path}")
    print(f"  Count: {args.count}")
    
    examples = []
    
    if args.category == "all":
        examples = generate_balanced_dataset(args.count)
    elif args.category == "llm":
        if not args.use_llm:
            args.use_llm = True
        examples = list(generate_with_llm(args.count, "casual", args.llm_model, args.ollama_url))
    else:
        generator = GENERATORS[args.category]
        examples = list(generator(args.count))
        print(f"  {args.category}: {len(examples)} examples")
    
    # Add LLM-generated examples if requested
    if args.use_llm and args.category != "llm":
        print(f"\nGenerating {args.llm_count} LLM-assisted examples...")
        for category in ["casual", "technical", "grounding"]:
            llm_examples = list(generate_with_llm(
                args.llm_count // 3, 
                category, 
                args.llm_model, 
                args.ollama_url
            ))
            examples.extend(llm_examples)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Generated {len(examples)} examples")
    print(f"   Saved to: {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
AI/ML & LLM Training Data Generator
Target: ~300 examples for machine learning, LLMs, model training, inference
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for machine learning and AI development.
You help with model training, inference, LLM integration, and ML engineering best practices."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

ML_TASKS = [
    {
        "instruction": "Install PyTorch with CUDA support",
        "command": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
        "explanation": "Installs PyTorch with CUDA 12.1 support for GPU acceleration"
    },
    {
        "instruction": "Check if GPU is available for training",
        "command": "python -c \"import torch; print(f'CUDA available: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')\"",
        "explanation": "Verifies CUDA availability and shows GPU name"
    },
    {
        "instruction": "Install Hugging Face transformers",
        "command": "pip install transformers datasets accelerate",
        "explanation": "Installs HF ecosystem for working with pre-trained models"
    },
    {
        "instruction": "Download a pre-trained model from Hugging Face",
        "command": "python -c \"from transformers import AutoModel; AutoModel.from_pretrained('bert-base-uncased')\"",
        "explanation": "Downloads BERT model to cache"
    },
    {
        "instruction": "Run inference with Ollama",
        "command": "curl http://localhost:11434/api/generate -d '{\"model\": \"llama3.2\", \"prompt\": \"Hello\", \"stream\": false}'",
        "explanation": "Sends prompt to Ollama API"
    },
    {
        "instruction": "List installed Ollama models",
        "command": "ollama list",
        "explanation": "Shows all downloaded Ollama models"
    },
    {
        "instruction": "Pull a model in Ollama",
        "command": "ollama pull llama3.2:latest",
        "explanation": "Downloads Llama 3.2 model"
    },
    {
        "instruction": "Run Jupyter notebook for ML experimentation",
        "command": "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser",
        "explanation": "Starts JupyterLab for interactive development"
    },
    {
        "instruction": "Profile GPU memory usage",
        "command": "nvidia-smi -l 1",
        "explanation": "Continuously shows GPU usage every second"
    },
    {
        "instruction": "Convert model to ONNX format",
        "command": "python -c \"import torch; model = YourModel(); torch.onnx.export(model, dummy_input, 'model.onnx')\"",
        "explanation": "Exports PyTorch model to ONNX for inference"
    },
    {
        "instruction": "Install TensorFlow with GPU support",
        "command": "pip install tensorflow[and-cuda]",
        "explanation": "Installs TensorFlow with CUDA dependencies"
    },
    {
        "instruction": "Check TensorFlow GPU access",
        "command": "python -c \"import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))\"",
        "explanation": "Lists available GPUs for TensorFlow"
    },
    {
        "instruction": "Install scikit-learn",
        "command": "pip install scikit-learn",
        "explanation": "Installs core ML library for traditional algorithms"
    },
    {
        "instruction": "Install XGBoost with GPU",
        "command": "pip install xgboost",
        "explanation": "Installs gradient boosting library with GPU support"
    },
    {
        "instruction": "Create Ollama custom model",
        "command": "ollama create mymodel -f Modelfile",
        "explanation": "Creates custom model from Modelfile"
    },
    {
        "instruction": "Run Ollama model interactively",
        "command": "ollama run llama3.2",
        "explanation": "Starts interactive chat session"
    },
    {
        "instruction": "Delete Ollama model",
        "command": "ollama rm llama3.2:latest",
        "explanation": "Removes model from local storage"
    },
    {
        "instruction": "Copy Ollama model with new name",
        "command": "ollama cp llama3.2 mymodel",
        "explanation": "Creates copy for customization"
    },
    {
        "instruction": "Show Ollama model info",
        "command": "ollama show llama3.2 --modelfile",
        "explanation": "Displays model configuration"
    },
    {
        "instruction": "Install vLLM for high-performance inference",
        "command": "pip install vllm",
        "explanation": "Installs PagedAttention-based LLM serving"
    },
    {
        "instruction": "Start vLLM OpenAI-compatible server",
        "command": "python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.2-1B-Instruct --port 8000",
        "explanation": "Serves model with OpenAI API compatibility"
    },
    {
        "instruction": "Install LangChain",
        "command": "pip install langchain langchain-openai langchain-community",
        "explanation": "Installs LangChain framework and integrations"
    },
    {
        "instruction": "Install LlamaIndex",
        "command": "pip install llama-index",
        "explanation": "Installs RAG framework for LLMs"
    },
    {
        "instruction": "Install Sentence Transformers",
        "command": "pip install sentence-transformers",
        "explanation": "Installs embedding model library"
    },
    {
        "instruction": "Download embedding model",
        "command": "python -c \"from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2')\"",
        "explanation": "Downloads efficient embedding model"
    },
    {
        "instruction": "Install FAISS for vector search",
        "command": "pip install faiss-gpu",
        "explanation": "Installs GPU-accelerated vector similarity search"
    },
    {
        "instruction": "Install ChromaDB",
        "command": "pip install chromadb",
        "explanation": "Installs embedded vector database"
    },
    {
        "instruction": "Install Pinecone client",
        "command": "pip install pinecone-client",
        "explanation": "Installs managed vector database client"
    },
    {
        "instruction": "Install MLflow for experiment tracking",
        "command": "pip install mlflow",
        "explanation": "Installs ML experiment tracking and model registry"
    },
    {
        "instruction": "Start MLflow UI",
        "command": "mlflow ui --port 5000",
        "explanation": "Launches experiment tracking dashboard"
    },
    {
        "instruction": "Install Weights & Biases",
        "command": "pip install wandb && wandb login",
        "explanation": "Installs W&B for experiment tracking"
    },
    {
        "instruction": "Install Unsloth for efficient fine-tuning",
        "command": "pip install unsloth[cu121]",
        "explanation": "Installs 2x faster LoRA fine-tuning library"
    },
    {
        "instruction": "Install PEFT for parameter-efficient fine-tuning",
        "command": "pip install peft",
        "explanation": "Installs LoRA, QLoRA adapters library"
    },
    {
        "instruction": "Install bitsandbytes for quantization",
        "command": "pip install bitsandbytes",
        "explanation": "Enables 4-bit and 8-bit model quantization"
    },
    {
        "instruction": "Quantize model to GGUF",
        "command": "python llama.cpp/convert.py model/ --outtype f16 && ./quantize model.gguf model-q4_k_m.gguf q4_k_m",
        "explanation": "Converts and quantizes model for llama.cpp"
    },
    {
        "instruction": "Monitor GPU temperature",
        "command": "nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used --format=csv -l 1",
        "explanation": "Shows GPU temperature and utilization"
    },
    {
        "instruction": "Clear CUDA cache",
        "command": "python -c \"import torch; torch.cuda.empty_cache(); print('Cache cleared')\"",
        "explanation": "Frees unused GPU memory"
    },
    {
        "instruction": "Install DeepSpeed",
        "command": "pip install deepspeed",
        "explanation": "Installs distributed training library"
    },
    {
        "instruction": "Train with multiple GPUs",
        "command": "torchrun --nproc_per_node=4 train.py",
        "explanation": "Launches distributed training on 4 GPUs"
    },
    {
        "instruction": "Install TRL for RLHF",
        "command": "pip install trl",
        "explanation": "Installs Transformer Reinforcement Learning library"
    },
    {
        "instruction": "Install auto-gptq for quantization",
        "command": "pip install auto-gptq",
        "explanation": "Installs GPTQ quantization library"
    },
    {
        "instruction": "Run model inference benchmark",
        "command": "python -m torch.utils.benchmark.compare_benchmark model_latency.json",
        "explanation": "Benchmarks model inference speed"
    },
    {
        "instruction": "Profile PyTorch model",
        "command": "python -c \"from torch.profiler import profile; with profile() as prof: model(input); print(prof.key_averages().table())\"",
        "explanation": "Profiles model operations"
    },
    {
        "instruction": "Install Triton inference server client",
        "command": "pip install tritonclient[all]",
        "explanation": "Installs NVIDIA Triton client"
    },
    {
        "instruction": "Check model memory requirements",
        "command": "python -c \"import torch; params = sum(p.numel() for p in model.parameters()); print(f'{params/1e9:.2f}B params, ~{params*4/1e9:.1f}GB fp32')\"",
        "explanation": "Estimates model memory usage"
    },
    {
        "instruction": "Install Gradio for model demos",
        "command": "pip install gradio",
        "explanation": "Installs quick ML demo UI library"
    },
    {
        "instruction": "Install Streamlit for ML apps",
        "command": "pip install streamlit",
        "explanation": "Installs data app framework"
    },
    {
        "instruction": "Export model to SafeTensors",
        "command": "python -c \"from safetensors.torch import save_model; save_model(model, 'model.safetensors')\"",
        "explanation": "Saves model in safe, efficient format"
    },
    {
        "instruction": "Load quantized model with bitsandbytes",
        "command": "python -c \"from transformers import AutoModelForCausalLM; model = AutoModelForCausalLM.from_pretrained('model', load_in_4bit=True)\"",
        "explanation": "Loads model in 4-bit quantization"
    },
]

LLM_INTEGRATION_TASKS = [
    {
        "instruction": "Set up OpenAI API client",
        "code": """from openai import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)""",
        "explanation": "Basic OpenAI chat completion with system prompt"
    },
    {
        "instruction": "Implement streaming response from LLM",
        "code": """from openai import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)""",
        "explanation": "Streaming allows incremental response display"
    },
    {
        "instruction": "Create embeddings for semantic search",
        "code": """from openai import OpenAI
import numpy as np

client = OpenAI()

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def cosine_similarity(a: list, b: list) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Usage
query_embedding = get_embedding("What is machine learning?")
doc_embedding = get_embedding("ML is a subset of AI...")
similarity = cosine_similarity(query_embedding, doc_embedding)""",
        "explanation": "Text embeddings enable semantic similarity search"
    },
    {
        "instruction": "Implement function calling with LLM",
        "code": """from openai import OpenAI
import json

client = OpenAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)

# Check if model wants to call a function
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    function_args = json.loads(tool_call.function.arguments)
    # Execute function and return result to model""",
        "explanation": "Function calling lets LLMs use tools"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Fine-tune a language model with QLoRA",
        "steps": [
            "Prepare training data in chat/instruction format",
            "Install dependencies: transformers, peft, bitsandbytes, trl",
            "Load base model in 4-bit quantization",
            "Configure LoRA adapters (rank, alpha, target modules)",
            "Set up training arguments (learning rate, epochs, batch size)",
            "Use SFTTrainer for supervised fine-tuning",
            "Train with gradient checkpointing for memory efficiency",
            "Monitor loss with wandb or tensorboard",
            "Save LoRA adapters separately",
            "Merge adapters with base model for inference",
            "Quantize merged model to GGUF for deployment",
            "Test with evaluation prompts",
            "Create Ollama Modelfile",
            "Deploy to Ollama"
        ]
    },
    {
        "instruction": "Build a RAG (Retrieval Augmented Generation) system",
        "steps": [
            "Collect and clean documents",
            "Split documents into chunks (512-1024 tokens)",
            "Generate embeddings for chunks",
            "Store in vector database (ChromaDB, Pinecone, Weaviate)",
            "Create retrieval function with similarity search",
            "Build prompt template with context placeholders",
            "Implement query pipeline: embed query → retrieve → generate",
            "Add re-ranking for better relevance",
            "Implement conversation history handling",
            "Add source attribution to responses",
            "Set up evaluation metrics (faithfulness, relevance)",
            "Test with diverse queries",
            "Optimize chunk size and retrieval k"
        ]
    },
    {
        "instruction": "Deploy LLM API service",
        "steps": [
            "Choose deployment strategy (serverless, container, dedicated GPU)",
            "Set up model serving framework (vLLM, TGI, Ollama)",
            "Create API wrapper with FastAPI",
            "Implement request validation",
            "Add rate limiting and authentication",
            "Set up request queuing for GPU utilization",
            "Implement response streaming",
            "Add caching for common queries",
            "Configure auto-scaling based on queue depth",
            "Set up monitoring (latency, throughput, errors)",
            "Create health check endpoint",
            "Document API and examples",
            "Load test and optimize"
        ]
    },
    {
        "instruction": "Evaluate LLM performance",
        "steps": [
            "Define evaluation criteria (accuracy, fluency, safety)",
            "Create test dataset with ground truth",
            "Implement automatic metrics (BLEU, ROUGE, perplexity)",
            "Set up LLM-as-judge evaluation",
            "Create human evaluation rubric",
            "Test on diverse prompt categories",
            "Evaluate edge cases and failure modes",
            "Test for hallucination tendency",
            "Measure latency and throughput",
            "Compare against baseline models",
            "Document findings and recommendations"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the difference between fine-tuning and RAG?",
        "answer": "Fine-tuning modifies model weights by training on new data - permanently changes model behavior, good for style/format changes. RAG retrieves relevant context at inference time - keeps model unchanged, good for dynamic knowledge. Fine-tuning: train once, no retrieval needed at runtime. RAG: no training, but needs vector DB and retrieval step. Use fine-tuning for: tone, format, specific tasks. Use RAG for: factual knowledge, frequently updated info. Often combined: fine-tune for style + RAG for facts."
    },
    {
        "question": "What is LoRA and why is it used?",
        "answer": "LoRA (Low-Rank Adaptation) fine-tunes by adding small trainable matrices to frozen base model. Instead of updating billions of parameters, train only millions. Benefits: much less GPU memory (~4GB vs 40GB), faster training, small adapter files (~100MB), can swap adapters easily. QLoRA adds 4-bit quantization for even less memory. Works by decomposing weight updates into low-rank matrices. Essential for fine-tuning large models on consumer GPUs."
    },
    {
        "question": "What are embeddings and how are they used?",
        "answer": "Embeddings are dense vector representations of text that capture semantic meaning. Similar concepts have similar vectors. Created by encoder models (BERT, sentence-transformers) or embedding APIs. Use cases: semantic search (find similar documents), clustering, classification, RAG retrieval. Dimension typically 384-1536. Compare with cosine similarity or dot product. Store in vector databases for efficient similarity search. Quality depends on embedding model and domain match."
    },
    {
        "question": "What is quantization in ML?",
        "answer": "Quantization reduces model precision (float32 → int8/int4) to decrease size and increase speed. Types: post-training quantization (PTQ) - quick but less accurate, quantization-aware training (QAT) - maintains accuracy. Common formats: GGUF (llama.cpp), GPTQ, AWQ, bitsandbytes. Trade-offs: 4-bit is ~4x smaller, small accuracy loss. int8 is often negligible loss. Essential for running large models on limited hardware. Different layers can use different precision."
    },
    {
        "question": "What is temperature in LLM sampling?",
        "answer": "Temperature controls randomness in token selection. Higher temp (1.5+): more creative, diverse, potentially incoherent. Lower temp (0.1-0.3): more deterministic, focused, potentially repetitive. Temperature=0 is greedy (always pick highest probability). Works by scaling logits before softmax. Other sampling params: top_p (nucleus sampling - cumulative probability), top_k (only consider k tokens). Combine for fine control. Use low temp for factual tasks, higher for creative."
    },
    {
        "question": "What is a tokenizer and why does it matter?",
        "answer": "Tokenizer converts text to numbers (tokens) that models understand. Different models use different tokenizers (BPE, WordPiece, SentencePiece). Token count affects: context length limits, API costs, generation speed. Common issues: special characters become multiple tokens, different languages tokenize differently. 'token' ≠ 'word' - subword units. Check token count: tiktoken for OpenAI, model.tokenizer for HF. Max tokens includes prompt + completion. Longer prompts = less room for response."
    },
    {
        "question": "What is a vector database?",
        "answer": "Vector database stores and indexes embeddings for fast similarity search. Unlike SQL, queries find nearest neighbors by vector distance. Popular options: Pinecone (managed), Weaviate, Qdrant, Milvus, ChromaDB (simple/local), pgvector (PostgreSQL extension). Key features: HNSW indexing, filtering metadata, hybrid search. Use for: RAG retrieval, semantic search, recommendation systems. Choose based on: scale, managed vs self-hosted, filtering needs. Always benchmark with your data."
    },
    {
        "question": "What is context length in LLMs?",
        "answer": "Context length is maximum tokens model can process at once (prompt + response). GPT-4: 8K/32K/128K, Claude: 100K+, Llama-2: 4K, Mistral: 8K/32K. Longer context = more info but: higher cost, slower inference, may lose focus on key parts. Strategies for long docs: chunking + retrieval, summarization, hierarchical processing. 'Lost in the middle' - models may miss info in long context middle. Not all context is used equally - position matters."
    },
    {
        "question": "What is a system prompt?",
        "answer": "System prompt sets model behavior, personality, and constraints before user interaction. Defines: role, tone, capabilities, output format, safety rules. Persists across conversation turns. Examples: 'You are a Python expert, respond only with code', 'Be concise, use bullet points'. Security: system prompts can be extracted, don't put secrets there. Best practices: clear instructions, few-shot examples, explicit constraints. Some models weight system prompt differently. Test extensively."
    },
    {
        "question": "What is few-shot prompting?",
        "answer": "Few-shot prompting includes examples in the prompt to guide model behavior. Format: example input → expected output, repeated 2-5 times, then actual query. Benefits: no training needed, adapts model to specific format/style. Zero-shot: no examples. One-shot: single example. More shots usually help but cost tokens. Examples should: cover edge cases, be diverse, match expected distribution. Chain-of-thought: include reasoning in examples. Format consistently. Order can matter."
    },
    {
        "question": "What is an LLM agent?",
        "answer": "LLM agent combines language model with tools and autonomous action. Components: LLM (brain), tools (actions like search, code execution, APIs), memory (conversation history, long-term storage), planning (breaking down tasks). Frameworks: LangChain, AutoGPT, CrewAI. Agent loop: observe → think → act → observe result. Tools need clear descriptions for LLM to use correctly. Challenges: reliability, cost control, security. Start simple, add capabilities gradually."
    },
    {
        "question": "What is model distillation?",
        "answer": "Distillation trains smaller 'student' model to mimic larger 'teacher' model. Student learns from teacher's outputs (soft labels) not just ground truth. Benefits: smaller, faster model with similar capabilities. Used to create: edge-deployable models, specialized models from general ones. Teacher provides richer signal than hard labels. Temperature controls softness of labels. Can distill specific capabilities. OpenAI policy prohibits distilling their models. Alpaca, Vicuna used ChatGPT outputs."
    },
    {
        "question": "What is prompt injection?",
        "answer": "Prompt injection tricks LLM into following attacker instructions instead of system prompt. Types: direct (in user input), indirect (in retrieved content). Examples: 'ignore previous instructions and...', embedding commands in documents. Defenses: input sanitization, output validation, separate processing pipelines, sandboxing. No perfect solution. Consider: what's worst case if prompt ignored? Defense in depth. Never trust LLM output for security decisions. Red team your prompts."
    },
    {
        "question": "What is RLHF?",
        "answer": "RLHF (Reinforcement Learning from Human Feedback) aligns models with human preferences. Process: 1) supervised fine-tuning on quality examples, 2) train reward model on human preference rankings, 3) optimize policy with RL (PPO) against reward model. Makes models helpful, harmless, honest. Alternatives: DPO (Direct Preference Optimization) - simpler, no RL needed. RLAIF - AI provides feedback. Constitutional AI - principles-based. Key to ChatGPT's usability. Expensive human annotation required."
    },
    {
        "question": "What is semantic search vs keyword search?",
        "answer": "Keyword search matches exact terms - 'fast car' won't find 'quick automobile'. Semantic search uses embeddings to find meaning - 'fast car' finds 'rapid vehicle', 'speedy auto'. Implementation: embed documents, embed query, find nearest neighbors. Hybrid combines both: BM25 for keywords + embeddings for semantics, rerank results. Use keyword when: exact match needed, domain-specific terms. Use semantic when: natural language queries, conceptual similarity. Hybrid usually best."
    },
    {
        "question": "What is a foundation model?",
        "answer": "Foundation model is large model pre-trained on broad data, then adapted for specific tasks. Examples: GPT-4, Claude, Llama, BERT, CLIP, Whisper. Characteristics: trained once expensively, used many ways cheaply. Adaption methods: fine-tuning, prompting, RAG. Emergent capabilities appear at scale. Transfer learning to new domains. Risks: training data bias, capability overhang. Companies: OpenAI, Anthropic, Google, Meta. Open vs closed models trade-off. Rapidly evolving field."
    }
]

ADVANCED_CONCEPTS = [
    {
        "question": "How does the transformer attention mechanism work?",
        "answer": "Attention computes relevance between all tokens in a sequence. Query, Key, Value matrices from input: Q, K, V. Attention = softmax(QK^T / sqrt(d_k)) * V. Each token attends to all others weighted by similarity. Multi-head attention runs multiple attention in parallel, captures different relationships. Self-attention: Q, K, V from same sequence. Cross-attention: Q from one sequence, K, V from another. Complexity O(n²) limits context length - hence flash attention, sparse attention innovations."
    },
    {
        "question": "What is KV cache and why does it matter?",
        "answer": "KV cache stores computed key-value pairs from attention layers during generation. Without cache: recompute all previous tokens each step - O(n²) per token. With cache: only compute for new token, retrieve previous - O(n) per token. Crucial for efficient autoregressive generation. Memory grows linearly with context length. Flash attention optimizes by chunking. PagedAttention (vLLM) enables dynamic memory allocation. Long contexts need significant GPU memory for KV cache."
    },
    {
        "question": "How do I choose between different LLM inference frameworks?",
        "answer": "vLLM: best throughput for serving, PagedAttention, continuous batching. Good for production APIs. TGI (Text Generation Inference): HuggingFace, easy setup, good HF integration. Ollama: simplest local deployment, great for dev, built-in model management. llama.cpp: CPU/hybrid inference, GGUF quantization, minimal dependencies. TensorRT-LLM: NVIDIA-optimized, best single-GPU performance. Choose based on: deployment environment, scale needs, model support, optimization requirements."
    },
    {
        "question": "What is prompt engineering and what are best practices?",
        "answer": "Prompt engineering optimizes LLM inputs for better outputs. Techniques: few-shot examples, chain-of-thought reasoning, role/persona setting, structured output formats. Best practices: be specific, provide context, use consistent formatting, iterate and test. System prompts set behavior, user prompts give tasks. For structured output: use JSON mode or specify schema. For reasoning: 'think step by step'. Test edge cases. Consider prompt injection security. Document and version prompts. Use prompt management tools for production."
    },
    {
        "question": "What is Flash Attention and why is it important?",
        "answer": "Flash Attention is memory-efficient attention algorithm that reduces memory from O(n²) to O(n). Standard attention materializes full attention matrix in HBM. Flash Attention uses tiling: computes attention in blocks, keeps intermediates in fast SRAM. Benefits: 2-4x faster, handles longer sequences, enables larger batch sizes. Flash Attention 2 adds further optimizations. Essential for long context models. Requires compatible GPU (Ampere+). Built into transformers library: model.to(dtype=torch.float16); model.config.use_flash_attention_2."
    },
    {
        "question": "How do mixture of experts (MoE) models work?",
        "answer": "MoE models have multiple 'expert' networks, router selects subset per token. Mixtral: 8 experts, routes to 2 per token. Benefits: model capacity scales without proportional compute increase. 7B active params with 47B total. Training challenges: load balancing across experts, expert collapse. Router learns which experts for which tokens. Inference: only activated experts loaded in memory. Sparse models: most params inactive per forward pass. Enables larger models on same hardware."
    },
    {
        "question": "What is speculative decoding?",
        "answer": "Speculative decoding accelerates generation using small draft model. Draft model generates K tokens quickly, target model verifies in parallel. If draft matches target's distribution, accept all K at once. If mismatch, reject and use target's token. Speed-up depends on draft model accuracy. No quality loss - mathematically equivalent to target-only. Works best when: draft model closely matches target, high acceptance rate. Implementations: vLLM, Medusa (multiple heads), lookahead decoding."
    },
    {
        "question": "How does PEFT (Parameter-Efficient Fine-Tuning) work beyond LoRA?",
        "answer": "PEFT methods train small number of parameters while freezing base model. LoRA: low-rank matrices added to attention layers. Prefix tuning: learnable tokens prepended to input. Adapter layers: small bottleneck layers inserted between transformer layers. IA3: learned vectors scale activations. Prompt tuning: soft prompts (continuous embeddings). QLoRA: LoRA + 4-bit quantization. Choose based on: task type, memory constraints, need to merge adapters. HuggingFace peft library supports all."
    },
    {
        "question": "What is Constitutional AI and how does it work?",
        "answer": "Constitutional AI (CAI) is Anthropic's approach to making AI helpful, harmless, honest. Instead of human feedback on every output, defines principles (constitution). Model critiques own outputs against principles, generates improved versions. Red-teaming step generates adversarial prompts, model learns to refuse appropriately. Benefits: more scalable than pure RLHF, clearer alignment goals, less human annotation. Claude uses CAI. Principles are explicit, auditable. Ongoing research into constitutional design."
    },
    {
        "question": "How do I evaluate LLM performance?",
        "answer": "Evaluation depends on task type. Generation quality: perplexity, BLEU, ROUGE, human evaluation. Benchmarks: MMLU (knowledge), HumanEval (code), HellaSwag (reasoning), TruthfulQA. Domain-specific: create task-relevant test set. LLM-as-judge: have another LLM score outputs. Key metrics: latency, throughput, cost per token. A/B testing in production. Challenges: benchmark saturation, overfitting to evals. Custom evals for your use case most valuable. Log and analyze failures."
    },
    {
        "question": "What is retrieval-augmented generation (RAG) architecture?",
        "answer": "RAG combines retrieval with generation. Pipeline: 1) embed query, 2) retrieve relevant docs from vector DB, 3) inject as context, 4) generate response. Components: chunking strategy (size, overlap), embedding model, vector DB, retriever (dense, sparse, hybrid), reranker, LLM. Advanced patterns: multi-hop retrieval, self-RAG, adaptive retrieval. Tuning: chunk size affects recall vs noise, top-k selection, reranking boosts precision. Evaluation: retrieval quality, answer correctness, faithfulness to sources."
    },
    {
        "question": "How do I handle long documents with LLMs?",
        "answer": "Strategies for documents exceeding context length. Chunking: split into overlapping segments, process separately, aggregate. Hierarchical summarization: summarize chunks, then summarize summaries. Map-reduce: process chunks in parallel, combine results. Retrieval: index all chunks, retrieve relevant ones per query. Long-context models: Claude 100K, GPT-4 32K handle more. Tradeoffs: chunking may lose cross-chunk context, summarization lossy, retrieval may miss relevant parts. Often combine approaches."
    },
    {
        "question": "What is model merging and when is it useful?",
        "answer": "Model merging combines multiple fine-tuned models into one without retraining. Methods: linear interpolation, TIES (trim, elect, sign), DARE (drop and rescale), SLERP (spherical interpolation). Use cases: combine domain expertise from different fine-tunes, merge capabilities. Works because fine-tuned models share base model structure. mergekit library supports various methods. Experimentation needed - not all merges work well. Popular for: creating versatile models, community experiments. Can't merge models with different architectures."
    },
    {
        "question": "What is continuous batching and why does it matter?",
        "answer": "Continuous batching dynamically adds/removes requests from batch during generation. Traditional batching: wait for all requests to finish before starting new batch. Problem: short requests wait for long ones, GPU underutilized. Continuous batching: when one request finishes, immediately slot in new one. Implemented in vLLM, TGI. Dramatically improves throughput - 2-4x over naive batching. Essential for production LLM serving with varying request lengths."
    },
    {
        "question": "How do multimodal models work?",
        "answer": "Multimodal models process multiple input types (text, images, audio, video). Architecture approaches: encoder per modality + fusion layer, unified tokenization. Vision-language: image encoder (CLIP, SigLIP) + text decoder. LLaVA, GPT-4V, Claude 3 Vision. Key challenge: aligning different modality representations. Training: pretrain encoders separately, then joint training. Applications: image captioning, visual QA, document understanding, video analysis. Emerging: any-to-any models like GPT-4o."
    },
    {
        "question": "What is function calling in LLMs?",
        "answer": "Function calling lets LLMs invoke external tools via structured output. Define functions with name, description, parameters (JSON schema). LLM decides when to call, generates arguments. You execute, return result, LLM continues. Use cases: web search, code execution, API calls, database queries. Challenges: LLM may hallucinate functions, parameter validation needed. OpenAI, Claude, open models support it. Frameworks: LangChain tools, LlamaIndex. Security: validate all LLM-generated calls."
    },
    {
        "question": "How do I debug LLM applications?",
        "answer": "Debugging LLM apps requires observability at every step. Logging: full prompts, responses, latencies, token counts. Tracing: LangSmith, Phoenix, Weights & Biases for chain execution. Common issues: prompt formatting, retrieved context quality, hallucinations. Debugging retrieval: inspect retrieved chunks, relevance scores. Generation issues: adjust temperature, check for prompt injection. Cost tracking: log token usage. Evaluation: automated tests on golden datasets. Production: alerts on quality metrics, human review samples."
    },
    {
        "question": "What is structured output and how do I enforce it?",
        "answer": "Structured output ensures LLM returns specific format (JSON, XML, etc.). Methods: 1) Prompting - ask for JSON, provide schema, few-shot examples. 2) JSON mode - OpenAI, Anthropic built-in support. 3) Constrained decoding - only allow valid tokens (outlines, guidance, jsonformer). 4) Post-processing - parse and validate, retry if invalid. Schema definition: JSON Schema, Pydantic models. Always validate output. For critical apps, use constrained decoding. Instructor library: Pydantic + LLM integration."
    }
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "CUDA out of memory error during training",
        "error_type": "resource_error",
        "response": {
            "status": "needs_optimization",
            "immediate_fixes": [
                "Reduce batch size",
                "Enable gradient checkpointing: model.gradient_checkpointing_enable()",
                "Use mixed precision: torch.cuda.amp.autocast()",
                "Clear cache: torch.cuda.empty_cache()"
            ],
            "advanced_solutions": [
                "Use QLoRA (4-bit quantization)",
                "Enable DeepSpeed ZeRO for distributed training",
                "Reduce sequence length",
                "Use gradient accumulation instead of larger batch"
            ],
            "diagnosis": "nvidia-smi shows memory usage, profile with torch.cuda.memory_stats()"
        }
    },
    {
        "instruction": "Model is generating repetitive/incoherent text",
        "error_type": "generation_quality",
        "response": {
            "status": "needs_tuning",
            "for_repetition": [
                "Increase temperature (try 0.7-0.9)",
                "Add repetition_penalty (1.1-1.3)",
                "Use top_p sampling (0.9-0.95)",
                "Increase top_k (40-100)"
            ],
            "for_incoherence": [
                "Lower temperature (0.3-0.5)",
                "Reduce top_p (0.8-0.9)",
                "Improve prompt clarity",
                "Add few-shot examples"
            ],
            "general": "Experiment with sampling parameters, test systematically"
        }
    },
    {
        "instruction": "LLM is hallucinating facts",
        "error_type": "accuracy",
        "response": {
            "status": "fundamental_limitation",
            "explanation": "LLMs generate plausible text, not verified facts",
            "mitigations": [
                "Use RAG to ground responses in real documents",
                "Lower temperature for factual queries",
                "Add source verification step",
                "Train model to say 'I don't know'",
                "Implement fact-checking pipeline",
                "Use citations and require sources"
            ],
            "best_practice": "Never trust LLM output for critical facts without verification"
        }
    },
    {
        "instruction": "Model inference is too slow",
        "error_type": "performance",
        "response": {
            "status": "optimizable",
            "quick_wins": [
                "Use quantized model (4-bit, 8-bit)",
                "Enable flash attention if available",
                "Use continuous batching",
                "Reduce max_new_tokens"
            ],
            "infrastructure": [
                "Use GPU instead of CPU",
                "Use optimized inference framework (vLLM, TGI)",
                "Enable KV cache",
                "Consider speculative decoding"
            ],
            "deployment": [
                "Add caching for common queries",
                "Use streaming for perceived speed",
                "Batch similar requests",
                "Consider smaller/distilled model"
            ]
        }
    },
    {
        "instruction": "Training loss not decreasing or model not learning",
        "error_type": "training_issue",
        "response": {
            "status": "needs_investigation",
            "common_causes": [
                "Learning rate too high or too low - try different orders of magnitude",
                "Data quality issues - check for duplicates, corrupted examples",
                "Tokenization mismatch between training and inference",
                "Wrong padding/truncation settings"
            ],
            "debugging_steps": [
                "Start with smaller dataset to validate pipeline",
                "Check gradient norms: torch.nn.utils.clip_grad_norm_",
                "Verify data loading: print actual batches",
                "Compare loss scale to expected range"
            ],
            "fixes": [
                "Use learning rate warmup and scheduler",
                "Try different LoRA rank (higher = more capacity)",
                "Ensure chat template matches training format",
                "Increase training epochs"
            ]
        }
    },
    {
        "instruction": "RAG retrieval returning irrelevant documents",
        "error_type": "retrieval_quality",
        "response": {
            "status": "needs_tuning",
            "embedding_issues": [
                "Try different embedding model (e5, bge, openai)",
                "Domain-specific embeddings may work better",
                "Check if query and document embeddings use same model"
            ],
            "chunking_issues": [
                "Chunk size too large - reduces precision",
                "Chunk size too small - loses context",
                "Add overlap between chunks",
                "Semantic chunking instead of fixed size"
            ],
            "retrieval_improvements": [
                "Add reranker (cross-encoder) after initial retrieval",
                "Use hybrid search (BM25 + semantic)",
                "Increase top_k then filter",
                "Add metadata filtering"
            ]
        }
    },
    {
        "instruction": "Ollama model not loading or crashing",
        "error_type": "deployment_error",
        "response": {
            "status": "needs_diagnosis",
            "memory_issues": [
                "Model too large for available memory",
                "Try smaller quantization: ollama run model:q4_0",
                "Check available RAM: free -h / Get-Process | Sort-Object WS -Desc",
                "Close other applications using GPU"
            ],
            "common_fixes": [
                "Restart ollama service: ollama stop; ollama serve",
                "Check model integrity: ollama pull model --force",
                "Verify CUDA installation: nvidia-smi",
                "Update Ollama to latest version"
            ],
            "environment": [
                "Set OLLAMA_NUM_GPU=0 for CPU-only",
                "OLLAMA_MAX_LOADED_MODELS=1 for memory constraints",
                "Check disk space for model files"
            ]
        }
    },
    {
        "instruction": "Fine-tuned model performs worse than base model",
        "error_type": "training_issue",
        "response": {
            "status": "overfitting_or_catastrophic_forgetting",
            "diagnosis": [
                "Overfitting: training loss good, eval loss bad",
                "Catastrophic forgetting: lost base capabilities",
                "Data poisoning: bad examples in training set"
            ],
            "solutions": [
                "Use validation set and early stopping",
                "Reduce number of training epochs",
                "Add regularization: dropout, weight decay",
                "Use smaller LoRA rank",
                "Mix in base model examples to prevent forgetting",
                "Review and clean training data"
            ],
            "best_practice": "Always eval on held-out set, compare to base model"
        }
    },
    {
        "instruction": "API rate limits hitting during production",
        "error_type": "operational",
        "response": {
            "status": "needs_architecture",
            "immediate_fixes": [
                "Implement exponential backoff with jitter",
                "Add request queuing",
                "Cache repeated queries"
            ],
            "architecture_changes": [
                "Use smaller/faster model for simple queries",
                "Batch requests where possible",
                "Add local model fallback",
                "Implement circuit breaker pattern"
            ],
            "code_example": "async with asyncio.Semaphore(10): # limit concurrent requests",
            "prevention": "Monitor usage, set up alerts before hitting limits"
        }
    },
    {
        "instruction": "Embedding dimension mismatch error",
        "error_type": "configuration_error",
        "response": {
            "status": "incompatible_models",
            "cause": "Vector DB configured for different embedding dimensions than current model",
            "diagnosis": [
                "Check embedding model output: model.encode(['test']).shape",
                "Check vector DB index configuration",
                "Common dimensions: 384 (MiniLM), 768 (BERT), 1536 (OpenAI)"
            ],
            "fixes": [
                "Recreate index with correct dimensions",
                "Re-embed all documents with new model",
                "Match embedding model to existing index"
            ],
            "prevention": "Document embedding model used, version control your retrieval config"
        }
    },
    {
        "instruction": "Token limit exceeded error",
        "error_type": "context_overflow",
        "response": {
            "status": "needs_truncation_or_chunking",
            "immediate_fixes": [
                "Truncate prompt to fit within limit",
                "Reduce system prompt length",
                "Summarize context before including"
            ],
            "better_solutions": [
                "Implement chunking with map-reduce",
                "Use RAG to retrieve only relevant parts",
                "Switch to longer context model"
            ],
            "token_counting": [
                "tiktoken for OpenAI: tiktoken.encoding_for_model('gpt-4')",
                "HuggingFace: tokenizer.encode(text, return_tensors='pt').shape",
                "Estimate: ~4 chars per token for English"
            ]
        }
    },
    {
        "instruction": "vLLM server not utilizing full GPU",
        "error_type": "performance",
        "response": {
            "status": "configuration_issue",
            "common_causes": [
                "Tensor parallelism misconfigured",
                "Single request at a time - need batching",
                "Model too small for GPU - CPU bound on tokenization"
            ],
            "optimizations": [
                "Use --tensor-parallel-size for multi-GPU",
                "Increase max_concurrent_requests",
                "Use continuous batching: --max-num-seqs 256",
                "Enable flash attention: --dtype float16"
            ],
            "monitoring": [
                "Check nvidia-smi utilization",
                "Profile with torch.cuda.Event for timing",
                "Monitor throughput tokens/second"
            ]
        }
    },
    {
        "instruction": "LangChain chain failing silently",
        "error_type": "debugging",
        "response": {
            "status": "needs_observability",
            "enable_debugging": [
                "Set verbose=True on chains and agents",
                "from langchain.globals import set_debug; set_debug(True)",
                "Use callbacks: chain.invoke(input, config={'callbacks': [handler]})"
            ],
            "common_issues": [
                "Output parser expecting different format",
                "Tool returning unexpected type",
                "Memory not being properly passed"
            ],
            "best_practices": [
                "Add LangSmith tracing for production",
                "Unit test each chain component separately",
                "Log intermediate outputs"
            ]
        }
    },
    {
        "instruction": "ChromaDB / Vector DB search returning empty results",
        "error_type": "retrieval_error",
        "response": {
            "status": "needs_investigation",
            "common_causes": [
                "Collection empty - documents not properly ingested",
                "Wrong collection name or database path",
                "Embedding model mismatch between index and query",
                "Metadata filter too restrictive"
            ],
            "debugging": [
                "Check collection count: collection.count()",
                "Verify documents: collection.peek()",
                "Test without filters first",
                "Compare embedding dimensions"
            ],
            "fixes": [
                "Re-embed documents if model changed",
                "Verify persist_directory correct",
                "Remove or loosen metadata filters"
            ]
        }
    },
    {
        "instruction": "Model generating text in wrong language",
        "error_type": "generation_issue",
        "response": {
            "status": "needs_guidance",
            "causes": [
                "Model trained predominantly on other language",
                "Prompt contamination from previous context",
                "Temperature too high causing random outputs"
            ],
            "fixes": [
                "Explicit language instruction: 'Respond in English only'",
                "Add few-shot examples in target language",
                "Use language-specific model or fine-tune",
                "Lower temperature for more controlled output"
            ],
            "multilingual_tips": [
                "mBART, BLOOM better for multilingual",
                "Consider language detection + routing",
                "Test with native speaker review"
            ]
        }
    },
    {
        "instruction": "HuggingFace model download failing or incomplete",
        "error_type": "environment_error",
        "response": {
            "status": "network_or_auth_issue",
            "common_causes": [
                "Network timeout or interruption",
                "Gated model requiring authentication",
                "Disk space insufficient",
                "Cache directory permissions"
            ],
            "fixes": [
                "Login: huggingface-cli login",
                "Set cache dir: HF_HOME=/path/with/space",
                "Force re-download: cache_dir=..., force_download=True",
                "Use specific revision: revision='main'"
            ],
            "network_issues": [
                "Use resume_download=True",
                "Set HF_HUB_OFFLINE=1 for offline mode",
                "Mirror: HF_ENDPOINT=https://hf-mirror.com"
            ]
        }
    }
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": "python",
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    examples = []
    for task in ML_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    for task in LLM_INTEGRATION_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_code_response(task["code"], task["explanation"])
        })
    return examples

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    all_concepts = BASIC_CONCEPTS + ADVANCED_CONCEPTS
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in all_concepts if isinstance(concept, dict)]

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    return examples

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating AI/ML Training Data")
    print("=" * 60)
    
    all_examples = []
    
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"Generated {len(tool_examples)} tool examples")
    
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"Generated {len(planning_examples)} planning examples")
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"Generated {len(concept_examples)} concept examples")
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"Generated {len(error_examples)} error examples")
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "aiml_llm.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()

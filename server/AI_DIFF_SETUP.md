# AI-Powered Diff Summaries with Local Ollama

The DocAI system now includes AI-powered change summaries when comparing API versions. This feature uses **Ollama** with **Mistral model** running locally - no external API keys or costs!

## Quick Start

### 1. Install Ollama

Download from: [ollama.ai](https://ollama.ai)

```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Windows
# Download installer from ollama.ai
```

### 2. Pull Mistral Model

```bash
ollama pull mistral
```

This downloads the Mistral 7B model (~4GB). First time takes a few minutes.

### 3. Start Ollama Server

```bash
ollama serve
```

Server runs on `http://localhost:11434`

Keep this terminal running while using DocAI.

### 4. Start DocAI

In a new terminal:

```bash
cd /path/to/docai-server
pip install -r requirements.txt
python run.py
```

## How It Works

When you click "Compare" on the version history page:

1. **Read Versions**: The system reads both markdown files (v1 and v2)
2. **Query Mistral**: Sends both versions to local Ollama
3. **Generate Summary**: Mistral generates intelligent analysis of changes:
   - New endpoints or parameters added
   - Removed or deprecated features
   - Changed request/response formats
   - Behavior changes
   - Migration notes for users
4. **Display Summary**: Shows summary at top of diff page
5. **Show Diff**: Displays detailed line-by-line diff below summary

## Features

✅ **Zero API Keys** - Everything runs locally
✅ **Zero Cost** - No subscription fees
✅ **Fast** - Local inference is quick
✅ **Privacy** - Documentation never leaves your machine
✅ **Offline** - Works without internet
✅ **Graceful Fallback** - If Ollama not running, diff still works without summary

## System Requirements

- RAM: 8GB minimum (16GB recommended for faster inference)
- Storage: 5GB for Mistral model
- CPU: Any modern processor

## Testing

Check if Ollama is working:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "What is 2+2?",
  "stream": false
}'
```

You should get a JSON response with the model's answer.

## Troubleshooting

**"Connection refused" error?**
- Make sure Ollama is running: `ollama serve`
- Check it's on port 11434 with: `curl http://localhost:11434/api/health`

**Diff page has no summary?**
- Check Ollama terminal for any errors
- Verify Mistral model is installed: `ollama list`
- Restart Ollama server

**Slow responses?**
- First response takes ~10 seconds while Ollama loads model into memory
- Subsequent requests are faster
- Increase RAM for better performance

**Model not found?**
```bash
ollama pull mistral  # Download the model
ollama list          # Verify it's installed
```

## Using Different Models

DocAI defaults to Mistral, but you can use other models:

**Option 1: Pull another model**
```bash
ollama pull neural-chat      # Faster, smaller
ollama pull llama2           # More capable
ollama pull dolphin-mixtral  # Higher quality
```

**Option 2: Update llm_service.py**

Edit `/app/services/llm_service.py` line with `MODEL = "mistral"` and change to desired model name.

## Model Comparison

| Model | Size | Speed | Quality | RAM |
|-------|------|-------|---------|-----|
| neural-chat | 4B | ⚡⚡⚡ | ⭐⭐ | 6GB |
| mistral | 7B | ⚡⚡ | ⭐⭐⭐ | 8GB |
| llama2 | 7B | ⚡⚡ | ⭐⭐⭐ | 8GB |
| dolphin-mixtral | 46B | ⚡ | ⭐⭐⭐⭐ | 24GB |

## Reference

**Ollama**: Local LLM runtime
- Website: [ollama.ai](https://ollama.ai)
- GitHub: [jmorganca/ollama](https://github.com/jmorganca/ollama)

**Mistral**: Fast, capable 7B model
- Website: [mistral.ai](https://mistral.ai)
- License: Apache 2.0 (Open source)

**DocAI Integration**: Same pattern used in doc_generator.py for API documentation generation

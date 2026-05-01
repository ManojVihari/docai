# 🚀 Quick Start: DocAI with Local Ollama

Get AI-powered API diff summaries running in 5 minutes!

## 📋 Prerequisites
- macOS, Linux, or Windows
- 8GB RAM minimum (16GB recommended)
- 5GB free disk space for Mistral model

## ⚡ Quick Setup

### Step 1: Install Ollama (2 minutes)

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows:** Download from [ollama.ai](https://ollama.ai)

### Step 2: Pull Mistral Model (5 minutes)

```bash
ollama pull mistral
```

### Step 3: Start DocAI Services

**Terminal 1 - Ollama Server:**
```bash
ollama serve
# Runs on http://localhost:11434
```

**Terminal 2 - DocAI:**
```bash
cd /path/to/docai-server
python run.py
# Runs on http://localhost:8000
```

### Step 4: Test It

1. Open http://localhost:8000/ui
2. Click on any API
3. Click "History" button
4. Click "Compare" between two versions
5. See AI-powered summary at the top! ✨

## 🎯 How It Works

```
User clicks "Compare v1 vs v2"
         ↓
DocAI reads both markdown files
         ↓
Sends to local Ollama/Mistral
         ↓
Mistral generates intelligent summary
         ↓
Shows summary + detailed diff to user
```

## ✨ What You'll See

The comparison page shows:

1. **AI Summary Card** (top)
   - 5 key changes highlighted
   - New endpoints/parameters
   - Deprecated features
   - Breaking changes
   - Migration notes

2. **Detailed Diff Table** (bottom)
   - Line-by-line comparison
   - Color-coded changes (red=removed, green=added)
   - Full context

## ⚙️ Configuration

### Use Different Model

```bash
# Faster, smaller model
ollama pull neural-chat
# Then edit: MODEL = "neural-chat" in llm_service.py

# Larger, more capable  
ollama pull llama2
# Then edit: MODEL = "llama2" in llm_service.py
```

### List Installed Models

```bash
ollama list
```

### Download Without Installing

```bash
ollama pull dolphin-mixtral  # Download only, don't run
```

## 📊 Model Performance

| Model | RAM | Speed | Quality |
|-------|-----|-------|---------|
| neural-chat | 6GB | Fast ⚡⚡⚡ | Good ⭐⭐ |
| mistral | 8GB | Medium ⚡⚡ | Great ⭐⭐⭐ |
| llama2 | 8GB | Medium ⚡⚡ | Great ⭐⭐⭐ |
| mixtral | 48GB | Slow ⚡ | Excellent ⭐⭐⭐⭐ |

## 🐛 Troubleshooting

**Ollama won't start?**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/health

# Restart
ollama serve --debug
```

**Model download failed?**
```bash
# Check internet and retry
ollama pull mistral

# Use different model
ollama pull neural-chat
```

**No summary appearing?**
1. Check Ollama is running: `curl http://localhost:11434/api/health`
2. Check model exists: `ollama list`
3. Restart both services
4. Check browser console for errors (F12)

**Slow responses?**
- First query: ~10s (loading model into RAM)
- Subsequent queries: ~2-3s
- Add more RAM for faster performance
- Use smaller model (neural-chat)

## 📚 References

- **Ollama**: [ollama.ai](https://ollama.ai) - Local LLM runtime
- **Mistral**: [mistral.ai](https://mistral.ai) - 7B model
- **DocAI Code**: [llm_service.py](./app/services/llm_service.py)

## 💡 Tips

✅ Keep Ollama terminal running in the background  
✅ First query takes longer (model loading)  
✅ Subsequent queries are fast  
✅ CPU inference works, but GPU is faster (install nvidia-docker for GPU)  
✅ Works completely offline once model is downloaded  

## 🎉 You're All Set!

Navigate to http://localhost:8000/ui and enjoy AI-powered API diffs!

Questions? Check [AI_DIFF_SETUP.md](./AI_DIFF_SETUP.md) for detailed information.

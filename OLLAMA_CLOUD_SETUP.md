# Ollama Cloud Setup Guide

The Causation Explorer now supports both **local Ollama** and **Ollama Cloud**!

## Quick Setup

### Option 1: Local Ollama (Default)
No configuration needed - just run Ollama locally:
```bash
# Make sure Ollama is running locally
ollama serve
python causation_web_ui.py
```

### Option 2: Ollama Cloud

1. **Get your API key:**
   - Go to https://ollama.com/settings/keys
   - Create a new API key
   - Copy it

2. **Set environment variables:**
   
   **Windows (PowerShell):**
   ```powershell
   $env:OLLAMA_BASE_URL="https://ollama.com"
   $env:OLLAMA_API_KEY="your_api_key_here"
   $env:OLLAMA_TIMEOUT="60"  # Optional: increase timeout for cloud
   ```
   
   **Windows (CMD):**
   ```cmd
   set OLLAMA_BASE_URL=https://ollama.com
   set OLLAMA_API_KEY=your_api_key_here
   set OLLAMA_TIMEOUT=60
   ```
   
   **Linux/Mac:**
   ```bash
   export OLLAMA_BASE_URL="https://ollama.com"
   export OLLAMA_API_KEY="your_api_key_here"
   export OLLAMA_TIMEOUT="60"
   ```

3. **Run the web UI:**
   ```bash
   python causation_web_ui.py
   ```

## Using Cloud Models

Cloud models are models with the `-cloud` suffix. To use them:

1. **Pull a cloud model** (if using local Ollama with cloud models):
   ```bash
   ollama pull gpt-oss:120b-cloud
   ```

2. **Or use directly via cloud API** (if configured for cloud):
   - The model will automatically run on Ollama's cloud infrastructure
   - No need to download or run locally

## Switching Between Local and Cloud

You can easily switch by changing the environment variables:

- **Local mode:** `OLLAMA_BASE_URL=http://localhost:11434` (or unset it)
- **Cloud mode:** `OLLAMA_BASE_URL=https://ollama.com` + `OLLAMA_API_KEY=your_key`

## Troubleshooting

### "OLLAMA_API_KEY not set" warning
- Make sure you've set the `OLLAMA_API_KEY` environment variable
- Verify the API key is correct at https://ollama.com/settings/keys

### Connection timeouts
- Increase `OLLAMA_TIMEOUT` (default: 30 seconds)
- Cloud requests may take longer than local

### Model not found
- For cloud: Make sure the model is available in Ollama's cloud model library
- For local: Make sure you've pulled the model with `ollama pull <model-name>`

## References

- [Ollama Cloud Documentation](https://docs.ollama.com/cloud)
- [Ollama Model Library](https://ollama.com/search?c=cloud)


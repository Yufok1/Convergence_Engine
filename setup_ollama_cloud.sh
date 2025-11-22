#!/bin/bash
# Ollama Cloud Setup Script for Mac/Linux
# Cross-platform version of SETUP_OLLAMA_CLOUD.ps1

set -e  # Exit on error

echo "🔧 Ollama Cloud Setup"
echo ""

# Detect shell type for proper environment variable setting
SHELL_NAME=$(basename "$SHELL")
SHELL_RC=""

if [ "$SHELL_NAME" = "bash" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        SHELL_RC="$HOME/.bash_profile"
    fi
elif [ "$SHELL_NAME" = "zsh" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Check if API key is already set
EXISTING_KEY="${OLLAMA_API_KEY:-}"
EXISTING_URL="${OLLAMA_BASE_URL:-}"

if [ -n "$EXISTING_KEY" ] && [ -n "$EXISTING_URL" ]; then
    echo "⚠️  Ollama Cloud is already configured!"
    echo "   Base URL: $EXISTING_URL"
    echo "   API Key: ${EXISTING_KEY:0:10}..."
    echo ""
    read -p "Do you want to change it? (y/n): " change
    if [ "$change" != "y" ] && [ "$change" != "Y" ]; then
        echo "Keeping existing configuration."
        exit 0
    fi
fi

echo "Enter your Ollama Cloud API key:"
echo "(Get it from: https://ollama.com/settings/keys)"
read -s -p "API Key: " api_key
echo ""

if [ -z "$api_key" ]; then
    echo "❌ API key cannot be empty!"
    exit 1
fi

# Set environment variables for current session
export OLLAMA_BASE_URL="https://ollama.com"
export OLLAMA_API_KEY="$api_key"
export OLLAMA_TIMEOUT="60"  # Increase timeout for cloud requests

echo ""
echo "✅ Environment variables set for this shell session!"
echo ""
echo "Current configuration:"
echo "  OLLAMA_BASE_URL = $OLLAMA_BASE_URL"
echo "  OLLAMA_API_KEY = ${api_key:0:10}..."
echo "  OLLAMA_TIMEOUT = $OLLAMA_TIMEOUT"
echo ""

# Ask if user wants to make it permanent
read -p "Do you want to save this configuration permanently? (y/n): " save_permanent

if [ "$save_permanent" = "y" ] || [ "$save_permanent" = "Y" ]; then
    if [ -n "$SHELL_RC" ]; then
        echo ""
        echo "Adding to $SHELL_RC..."
        
        # Remove existing entries if any
        sed -i.bak '/OLLAMA_BASE_URL/d' "$SHELL_RC" 2>/dev/null || true
        sed -i.bak '/OLLAMA_API_KEY/d' "$SHELL_RC" 2>/dev/null || true
        sed -i.bak '/OLLAMA_TIMEOUT/d' "$SHELL_RC" 2>/dev/null || true
        
        # Add new entries
        {
            echo ""
            echo "# Ollama Cloud Configuration"
            echo "export OLLAMA_BASE_URL=\"https://ollama.com\""
            echo "export OLLAMA_API_KEY=\"$api_key\""
            echo "export OLLAMA_TIMEOUT=\"60\""
        } >> "$SHELL_RC"
        
        echo "✅ Configuration saved to $SHELL_RC"
        echo ""
        echo "To apply immediately, run:"
        echo "  source $SHELL_RC"
        echo ""
        echo "Or restart your terminal."
    else
        echo ""
        echo "⚠️  Could not detect your shell configuration file."
        echo "Please add these lines to your shell startup file manually:"
        echo ""
        echo "export OLLAMA_BASE_URL=\"https://ollama.com\""
        echo "export OLLAMA_API_KEY=\"$api_key\""
        echo "export OLLAMA_TIMEOUT=\"60\""
    fi
else
    echo ""
    echo "ℹ️  Configuration is set for this session only."
    echo "Restart the terminal or run this script again to set it again."
fi

echo ""
echo "Now you can run: python causation_web_ui.py"
echo ""


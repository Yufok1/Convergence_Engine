# Ollama Cloud Setup Script for Windows PowerShell
# Run this script to configure Ollama Cloud for the Causation Explorer

Write-Host "🔧 Ollama Cloud Setup" -ForegroundColor Cyan
Write-Host ""

# Check if API key is already set
$existingKey = $env:OLLAMA_API_KEY
$existingUrl = $env:OLLAMA_BASE_URL

if ($existingKey -and $existingUrl) {
    Write-Host "⚠️  Ollama Cloud is already configured!" -ForegroundColor Yellow
    Write-Host "   Base URL: $existingUrl" -ForegroundColor Gray
    Write-Host "   API Key: $($existingKey.Substring(0, [Math]::Min(10, $existingKey.Length)))..." -ForegroundColor Gray
    Write-Host ""
    $change = Read-Host "Do you want to change it? (y/n)"
    if ($change -ne "y" -and $change -ne "Y") {
        Write-Host "Keeping existing configuration." -ForegroundColor Green
        exit
    }
}

Write-Host "Enter your Ollama Cloud API key:"
Write-Host "(Get it from: https://ollama.com/settings/keys)" -ForegroundColor Gray
$apiKey = Read-Host "API Key"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "❌ API key cannot be empty!" -ForegroundColor Red
    exit 1
}

# Set environment variables for current session
$env:OLLAMA_BASE_URL = "https://ollama.com"
$env:OLLAMA_API_KEY = $apiKey
$env:OLLAMA_TIMEOUT = "60"  # Increase timeout for cloud requests

Write-Host ""
Write-Host "✅ Environment variables set for this PowerShell session!" -ForegroundColor Green
Write-Host ""
Write-Host "Current configuration:" -ForegroundColor Cyan
Write-Host "  OLLAMA_BASE_URL = $env:OLLAMA_BASE_URL" -ForegroundColor Gray
Write-Host "  OLLAMA_API_KEY = $($apiKey.Substring(0, [Math]::Min(10, $apiKey.Length)))..." -ForegroundColor Gray
Write-Host "  OLLAMA_TIMEOUT = $env:OLLAMA_TIMEOUT" -ForegroundColor Gray
Write-Host ""
Write-Host "To make this permanent, run:" -ForegroundColor Yellow
Write-Host "  [System.Environment]::SetEnvironmentVariable('OLLAMA_BASE_URL', 'https://ollama.com', 'User')" -ForegroundColor White
Write-Host "  [System.Environment]::SetEnvironmentVariable('OLLAMA_API_KEY', '$apiKey', 'User')" -ForegroundColor White
Write-Host "  [System.Environment]::SetEnvironmentVariable('OLLAMA_TIMEOUT', '60', 'User')" -ForegroundColor White
Write-Host ""
Write-Host "Now you can run: python causation_web_ui.py" -ForegroundColor Green


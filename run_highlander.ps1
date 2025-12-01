# Highlander Mode Launcher - Configured for survival tournament
# Settings: predation enabled, survival threshold 0.5, competition intensity 0.8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🗡️ HIGHLANDER MODE LAUNCHER" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Settings from config.json:" -ForegroundColor White
Write-Host "- Predation: ENABLED" -ForegroundColor Red
Write-Host "- Survival Threshold: 0.5" -ForegroundColor Green
Write-Host "- Competition Intensity: 0.8" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Run the system with Highlander configuration
python unified_entry.py --highlander --predation --survival-threshold 0.5 --competition-intensity 0.8
@echo off
REM Highlander Mode Launcher - Configured for survival tournament
REM Settings: predation enabled, survival threshold 0.5, competition intensity 0.8

echo ========================================
echo 🗡️ HIGHLANDER MODE LAUNCHER
echo ========================================
echo Settings from config.json:
echo - Predation: ENABLED
echo - Survival Threshold: 0.5
echo - Competition Intensity: 0.8
echo ========================================
echo.

cd /d "%~dp0"
python unified_entry.py --highlander --predation --survival-threshold 0.5 --competition-intensity 0.8

pause
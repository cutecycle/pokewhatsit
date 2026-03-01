@echo off
echo ====================================
echo Pokemon Crystal AI Emulator
echo ====================================
echo.
echo Make sure the AI server is running in another terminal!
echo (Run: python mock_ai_server.py)
echo.
timeout /t 2 >nul
python ai_emulator.py

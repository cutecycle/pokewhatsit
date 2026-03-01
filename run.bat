@echo off
echo ========================================
echo  Pokemon Crystal AI Emulator - Setup
echo ========================================
echo.

echo [1/2] Installing dependencies...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo       Dependencies installed successfully.
echo.

echo [2/2] Starting AI server and emulator...
echo       AI server will run in the background on port 5000.
echo.

start "Pokemon AI Server" /min cmd /c "python mock_ai_server.py"
timeout /t 2 >nul

echo Launching emulator... (close the game window to stop)
echo.
python ai_emulator.py

echo.
echo Shutting down AI server...
taskkill /fi "WINDOWTITLE eq Pokemon AI Server" >nul 2>&1
echo Done.
pause

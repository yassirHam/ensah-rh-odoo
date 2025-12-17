@echo off
setlocal
echo ===================================================
echo   ENSA HR - DEPENDENCY FIXER V2 (ROBUST)
echo ===================================================
echo.
echo THIS SCRIPT MUST BE RUN AS ADMINISTRATOR!
echo.
pause

echo.
echo 1. Stopping Odoo Service...
net stop "odoo-server-17.0"

echo.
echo 2. Killing any lingering Python processes (to release file locks)...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM odoo-bin.exe /T 2>nul

echo.
echo 3. Installing Dependencies...
echo We will install packages one by one to avoid conflicts.
cd /d "C:\Program Files\Odoo 17.0.20251024\python"

:: Check if pip exists, if not use python -m pip
if exist Scripts\pip.exe (
    set PIP_CMD=Scripts\pip.exe
) else (
    set PIP_CMD=.\python.exe -m pip
)

:: Set target directory explicitly
set TARGET_DIR="C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages"

echo.
echo Installing OpenAI...
%PIP_CMD% install openai --target=%TARGET_DIR% --no-user --ignore-installed

echo.
echo Installing Twilio...
%PIP_CMD% install twilio --target=%TARGET_DIR% --no-user --ignore-installed

echo.
echo Installing Other Libs...
%PIP_CMD% install qrcode scikit-learn numpy pandas Pillow --target=%TARGET_DIR% --no-user --ignore-installed

echo.
echo 4. Verifying Installation...
if exist "C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages\openai" (
    echo [SUCCESS] OpenAI package found!
) else (
    echo [ERROR] OpenAI package still missing.
)

echo.
echo 5. Restarting Odoo Service...
net start "odoo-server-17.0"

echo.
echo ===================================================
echo   FIX COMPLETE!
echo   Please refresh your browser: http://localhost:8069
echo ===================================================
pause

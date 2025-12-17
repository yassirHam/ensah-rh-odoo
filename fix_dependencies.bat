@echo off
echo ===================================================
echo   ENSA HR - DEPENDENCY FIXER
echo ===================================================
echo.
echo THIS SCRIPT MUST BE RUN AS ADMINISTRATOR!
echo Right-click this file and select "Run as administrator"
echo.
pause

echo.
echo 1. Stopping Odoo Service...
net stop "odoo-server-17.0"

echo.
echo 2. Installing Dependencies to System Location...
cd /d "C:\Program Files\Odoo 17.0.20251024\python"

:: Check if pip exists, if not use python -m pip
if exist Scripts\pip.exe (
    set PIP_CMD=Scripts\pip.exe
) else (
    set PIP_CMD=.\python.exe -m pip
)

%PIP_CMD% install --target="C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages" openai twilio qrcode scikit-learn numpy pandas Pillow requests --upgrade --no-user

echo.
echo 3. Verifying Installation...
if exist "C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages\openai" (
    echo [SUCCESS] OpenAI package found in system location!
) else (
    echo [ERROR] OpenAI package NOT found! Installation might have failed.
    echo Please check file permissions or run this script again.
)

echo.
echo 4. Restarting Odoo Service...
net start "odoo-server-17.0"

echo.
echo ===================================================
echo   FIX COMPLETE!
echo   Please refresh your browser: http://localhost:8069
echo ===================================================
pause

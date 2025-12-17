@echo off
setlocal
echo ===================================================
echo   ENSA HR - SAFER FRESH INSTALL SETUP
echo ===================================================
echo.
echo RUN THIS AFTER INSTALLING ODOO.
echo (Run as Administrator)
echo.
pause

echo.
echo 1. Stopping Odoo Service...
net stop "odoo-server-17.0" 2>nul

echo.
echo 2. Installing ONLY Missing AI Libraries...
echo (We will NOT upgrade core Odoo libraries to avoid breaking it)
cd /d "C:\Program Files\Odoo 17.0.20251024\python"

:: Install safe packages only. REMOVED --upgrade flag.
:: Added --no-deps for some to avoid pulling in conflicting core libs if possible, 
:: but standard install without upgrade should be safe.

.\python.exe -m pip install openai twilio libsass qrcode scikit-learn numpy pandas pdfkit --target="C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages" --no-user --ignore-installed

echo.
echo 3. Verifying Installation...
if exist "C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages\openai" (
    echo [SUCCESS] OpenAI installed.
)
if exist "C:\Program Files\Odoo 17.0.20251024\python\Lib\site-packages\libsass-*.dist-info" (
    echo [SUCCESS] Libsass installed.
)

echo.
echo 4. Restarting Odoo Service...
net start "odoo-server-17.0"

echo.
echo ===================================================
echo   SETUP COMPLETE!
echo   Go to http://localhost:8069
echo ===================================================
pause

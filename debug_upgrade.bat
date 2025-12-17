@echo off
echo Stopping Odoo Service to release file locks...
net stop "odoo-server-17.0"
echo.
echo Running Odoo Upgrade in shell mode to capture errors...
echo This might take a minute.
echo.
"C:\Program Files\Odoo 17.0.20251024\python\python.exe" "C:\Program Files\Odoo 17.0.20251024\server\odoo-bin" -c "C:\Program Files\Odoo 17.0.20251024\server\odoo.conf" -d odoo_tut -u ensa_hoceima_hr --stop-after-init --logfile=debug_log.txt --log-level=error
echo.
echo Upgrade attempt finished.
echo If successful, you will see minimal output.
echo If failed, the error is in debug_log.txt
echo.
echo Restarting Odoo Service...
net start "odoo-server-17.0"
echo.
echo Done. Please tell the AI assistant to "read debug_log.txt"
pause

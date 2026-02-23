@echo off
echo ===================================================
echo   Patient Monitoring System - Firewall Setup
echo ===================================================
echo.
echo This script will configure Windows Firewall to allow
echo incoming connections on port 8000 for the backend server.
echo.
echo You may need to run this as Administrator.
echo.
pause

echo.
echo Checking existing firewall rules...
powershell -Command "Get-NetFirewallRule | Where-Object { $_.DisplayName -eq 'Patient Monitor Backend' } | Select-Object DisplayName, Enabled, Action"

echo.
echo Creating/Updating firewall rule...
powershell -Command "New-NetFirewallRule -DisplayName 'Patient Monitor Backend' -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any -ErrorAction SilentlyContinue; if ($?) { Write-Host 'Firewall rule created successfully' -ForegroundColor Green } else { $existing = Get-NetFirewallRule -DisplayName 'Patient Monitor Backend' -ErrorAction SilentlyContinue; if ($existing) { Write-Host 'Firewall rule already exists' -ForegroundColor Yellow } else { Write-Host 'Failed to create firewall rule. Run as Administrator.' -ForegroundColor Red } }"

echo.
echo Verifying firewall rule...
powershell -Command "Get-NetFirewallRule -DisplayName 'Patient Monitor Backend' -ErrorAction SilentlyContinue | Select-Object DisplayName, Direction, Action, Enabled | Format-List"

echo.
echo Current network IP address:
powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' } | Select-Object IPAddress, InterfaceAlias | Format-Table"

echo.
echo ===================================================
echo   Setup Complete!
echo ===================================================
echo.
echo Your backend will be accessible at:
powershell -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress; Write-Host \"  http://$ip:8000\" -ForegroundColor Cyan"
echo.
echo Mobile app should be configured to use this IP address.
echo.
pause

@echo off
echo ===================================================
echo   Patient Monitoring System - Network Verification
echo ===================================================
echo.

echo [1] Current Network Configuration
echo -----------------------------------
powershell -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress; $interface = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' }).InterfaceAlias; Write-Host \"IP Address: $ip\" -ForegroundColor Green; Write-Host \"Interface: $interface\" -ForegroundColor Green"
echo.

echo [2] Backend Server URLs
echo -----------------------------------
powershell -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress; Write-Host \"Local access:   http://localhost:8000\" -ForegroundColor Cyan; Write-Host \"Network access: http://$ip:8000\" -ForegroundColor Cyan; Write-Host \"WebSocket:      ws://$ip:8000/ws\" -ForegroundColor Cyan; Write-Host \"Camera Stream:  http://$ip:8000/stream\" -ForegroundColor Cyan"
echo.

echo [3] Mobile App Configuration Status
echo -----------------------------------
powershell -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress; $constantsFile = 'mobile_app\NurseAlarmApp\app\src\main\java\com\example\nursealarmapp\utils\Constants.kt'; if (Test-Path $constantsFile) { $content = Get-Content $constantsFile | Select-String 'BASE_URL|WS_URL'; $configuredIP = ($content | Select-String -Pattern '\d+\.\d+\.\d+\.\d+').Matches.Value | Select-Object -First 1; if ($configuredIP -eq $ip) { Write-Host \"Mobile app is configured correctly for IP: $configuredIP\" -ForegroundColor Green; Write-Host \"Status: UP TO DATE\" -ForegroundColor Green } else { Write-Host \"WARNING: Mobile app is configured for: $configuredIP\" -ForegroundColor Red; Write-Host \"But current IP is: $ip\" -ForegroundColor Red; Write-Host \"Status: NEEDS UPDATE\" -ForegroundColor Yellow; Write-Host \"\"; Write-Host \"Update the following file:\" -ForegroundColor Yellow; Write-Host \"  $constantsFile\" -ForegroundColor Yellow } } else { Write-Host \"Constants.kt file not found\" -ForegroundColor Red }"
echo.

echo [4] Firewall Status
echo -----------------------------------
powershell -Command "$rule = Get-NetFirewallRule -DisplayName 'Patient Monitor Backend' -ErrorAction SilentlyContinue; if ($rule) { if ($rule.Enabled -eq 'True' -and $rule.Action -eq 'Allow') { Write-Host \"Firewall: CONFIGURED (Port 8000 is open)\" -ForegroundColor Green } else { Write-Host \"Firewall: EXISTS but disabled or blocked\" -ForegroundColor Yellow } } else { Write-Host \"Firewall: NOT CONFIGURED\" -ForegroundColor Red; Write-Host \"Run SETUP_FIREWALL.bat as Administrator to configure\" -ForegroundColor Yellow }"
echo.

echo [5] Testing Backend Connection
echo -----------------------------------
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/' -Method GET -TimeoutSec 5 -UseBasicParsing; Write-Host \"Backend is RUNNING\" -ForegroundColor Green; Write-Host \"Status: $($response.StatusCode)\" -ForegroundColor Green } catch { Write-Host \"Backend is NOT RUNNING\" -ForegroundColor Red; Write-Host \"Start the backend server using START_SERVERS.bat\" -ForegroundColor Yellow }"
echo.

echo [6] Quick Mobile App Test URL
echo -----------------------------------
powershell -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -eq 'Dhcp' }).IPAddress; Write-Host \"Test this URL from your phone's browser:\" -ForegroundColor Cyan; Write-Host \"  http://$ip:8000/\" -ForegroundColor White; Write-Host \"\"; Write-Host \"If it loads the API docs, your phone can connect!\" -ForegroundColor Green"
echo.

echo ===================================================
echo   Network Check Complete
echo ===================================================
echo.
pause

@echo off
echo Starting Project Aegis servers...
echo.

echo Starting backend server on port 8000...
start "Backend Server" /min python "C:\Users\Shaunak Rane\Desktop\Hacks\project_aegis\run_backend.py"

echo Starting frontend server on port 8080...
cd "C:\Users\Shaunak Rane\Desktop\Hacks\project_aegis\frontend"
start "Frontend Server" /min python serve.py

echo.
echo Servers started successfully!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8080
echo Dashboard: http://localhost:8080/dashboard.html
echo.
echo Press Ctrl+C to stop the servers, then close this window.
pause >nul
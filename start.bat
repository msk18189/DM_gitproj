@echo off
echo Starting GitHub PR Intelligence Dashboard...
echo.

echo Starting backend server...
cd backend
start cmd /k python main.py

echo Waiting for backend to start...
timeout /t 3 /nobreak

echo Starting frontend server...
cd ..\frontend
start cmd /k npm run dev

echo.
echo Dashboard is starting!
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the command windows to stop the servers.

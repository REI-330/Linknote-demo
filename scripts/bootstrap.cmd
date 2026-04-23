@echo off
setlocal

rem Install backend/frontend dependencies and build the production frontend bundle.

set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"

echo [LinkNote] Installing backend dependencies...
cd /d "%BACKEND%"
python -m pip install -e .
if errorlevel 1 exit /b 1

echo [LinkNote] Installing frontend dependencies...
cd /d "%FRONTEND%"
call npm install
if errorlevel 1 exit /b 1

echo [LinkNote] Building frontend bundle...
call npm run build
if errorlevel 1 exit /b 1

echo [LinkNote] Bootstrap complete.
echo [LinkNote] Next step: run scripts\start-app.cmd

endlocal

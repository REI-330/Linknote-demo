@echo off
setlocal

rem 安装前后端依赖，并构建前端生产包。

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

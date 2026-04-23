@echo off
setlocal

rem Start backend and Vite dev server separately for frontend development.

set "ROOT=%~dp0.."

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset-local-processes.ps1" -ProjectRoot "%ROOT%" -FrontendPort 3015
if errorlevel 1 exit /b 1

start "LinkNote Backend" cmd /k "cd /d %ROOT%\backend && set LINKNOTE_SUPPRESS_BROWSER=1 && python -m app.run_local"
start "LinkNote Frontend" cmd /k "cd /d %ROOT%\frontend && npm run dev"
start "" http://127.0.0.1:3015

endlocal

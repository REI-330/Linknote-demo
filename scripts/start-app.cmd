@echo off
setlocal

rem 启动打包模式本地应用：先检查依赖、输出健康诊断、清理旧进程，
rem 再启动一个负责托管前端构建产物的后端进程。

set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"

echo [LinkNote] Checking backend runtime dependencies...
cd /d "%BACKEND%"
python -m app.bootstrap
if errorlevel 1 (
  echo [LinkNote] Backend dependencies are missing. Run scripts\bootstrap.cmd first.
  exit /b 1
)

if not exist "%FRONTEND%\node_modules" (
  echo [LinkNote] Frontend dependencies are missing. Run scripts\bootstrap.cmd first.
  exit /b 1
)

if not exist "%FRONTEND%\dist\index.html" (
  echo [LinkNote] Frontend build not found. Building production bundle...
  cd /d "%FRONTEND%"
  call npm run build
  if errorlevel 1 exit /b 1
)

echo [LinkNote] Running startup checks...
cd /d "%BACKEND%"
python -m app.doctor

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset-local-processes.ps1" -ProjectRoot "%ROOT%"
if errorlevel 1 exit /b 1

start "LinkNote" cmd /k "cd /d %BACKEND% && python -m app.run_local"

endlocal

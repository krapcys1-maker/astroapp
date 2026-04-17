@echo off
setlocal

set "ARGS="
if /I "%~1"=="/quiet" set "ARGS=-Quiet"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %ARGS%
exit /b %errorlevel%

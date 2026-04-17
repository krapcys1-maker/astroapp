@echo off
setlocal

set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\AstroLabb"
set "DESKTOP_LINK=%USERPROFILE%\Desktop\AstroLabb.lnk"

if exist "%START_MENU_DIR%\AstroLabb.lnk" del /f /q "%START_MENU_DIR%\AstroLabb.lnk"
if exist "%START_MENU_DIR%\Uninstall AstroLabb.lnk" del /f /q "%START_MENU_DIR%\Uninstall AstroLabb.lnk"
if exist "%START_MENU_DIR%" rmdir "%START_MENU_DIR%" 2>nul
if exist "%DESKTOP_LINK%" del /f /q "%DESKTOP_LINK%"

start "" /min cmd /c "cd /d %TEMP% && timeout /t 2 /nobreak >nul && rmdir /s /q \"%INSTALL_DIR%\""
exit /b 0

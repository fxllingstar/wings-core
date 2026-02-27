@echo off
setlocal

:: This ensures the script knows it's running from the folder where it's saved
cd /d "%~dp0"

set "INSTALL_DIR=%USERPROFILE%\.wings-bin"
set "EXE_NAME=wings-core.exe"

echo 🛠️  Installing Wings-Core CLI...

:: 1. Check if the EXE actually exists in this folder before trying to copy
if not exist "%EXE_NAME%" (
    echo.
    echo ❌ ERROR: I can't find %EXE_NAME% in this folder!
    echo Current Folder: %CD%
    echo.
    echo Please make sure 'install.bat' and '%EXE_NAME%' are in the same place.
    pause
    exit /b
)

:: 2. Create the bin directory
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

:: 3. Copy the exe
echo 📦 Moving file to %INSTALL_DIR%...
copy /Y "%EXE_NAME%" "%INSTALL_DIR%\" >nul

if %errorlevel% neq 0 (
    echo ❌ Permission Error: Try right-clicking this script and 'Run as Administrator'.
    pause
    exit /b
)

:: 4. Update PATH
echo %PATH% | find /I "%INSTALL_DIR%" >nul
if %errorlevel% neq 0 (
    echo 📡 Adding to System PATH...
    setx PATH "%PATH%;%INSTALL_DIR%"
)

echo.
echo ═══ INSTALLATION COMPLETE ═══
echo 🚀 CLOSE this terminal and open a NEW one.
echo 🚀 Then type: wings-core
echo ═════════════════════════════
pause
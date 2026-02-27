@echo off
setlocal

:: Define the installation directory
set "INSTALL_DIR=%USERPROFILE%\.wings-bin"
set "EXE_NAME=wings-core.exe"

echo 🛠️  Installing Wings-Core CLI...

:: 1. Create the directory if it doesn't exist
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

:: 2. Copy the exe to the install directory
copy /Y "%EXE_NAME%" "%INSTALL_DIR%\" >nul
if %errorlevel% neq 0 (
    echo ❌ Error: Could not copy %EXE_NAME%. Make sure it's in this folder!
    pause
    exit /b
)

:: 3. Add to PATH for the current user (if not already there)
echo %PATH% | find /I "%INSTALL_DIR%" >nul
if %errorlevel% neq 0 (
    echo 📡 Adding Wings-Core to your System PATH...
    setx PATH "%PATH%;%INSTALL_DIR%"
    echo ✅ PATH updated!
) else (
    echo ✨ Wings-Core is already in your PATH.
)

echo.
echo ═══ INSTALLATION COMPLETE ═══
echo 🚀 Restart your terminal (CMD or PowerShell) to start using 'wings-core'!
echo ═════════════════════════════
pause
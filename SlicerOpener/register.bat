@echo off
setlocal enabledelayedexpansion

REM Registers the 3dprint:// protocol to launch the SlicerOpener.exe in this folder.
REM Run this script as Administrator.

set "EXE=%~dp0SlicerOpener.exe"

if not exist "%EXE%" (
  echo ERROR: SlicerOpener.exe not found next to this script at: "%EXE%"
  echo Build or copy SlicerOpener.exe into this folder, then re-run as Administrator.
  exit /b 1
)

echo Registering 3dprint protocol to "%EXE%" ...

REM Create root key
reg add "HKCR\3dprint" /ve /d "URL:3dprint Protocol" /f >nul
reg add "HKCR\3dprint" /v "URL Protocol" /d "" /f >nul

REM Optional: icon
reg add "HKCR\3dprint\DefaultIcon" /ve /d "\"%EXE%\",1" /f >nul

REM Command to execute
reg add "HKCR\3dprint\shell\open\command" /ve /d "\"%EXE%\" \"%%1\"" /f >nul

if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Failed to write registry keys. Try running as Administrator.
  exit /b 1
)

echo Successfully registered 3dprint:// protocol.
echo If your browser prompts, choose to always allow the dashboard to open 3dprint links.
exit /b 0



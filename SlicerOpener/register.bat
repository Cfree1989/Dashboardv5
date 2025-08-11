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

echo Registering 3dprint and print3d protocols to "%EXE%" ...

REM Create root key for 3dprint://
reg add "HKCR\3dprint" /ve /d "URL:3dprint Protocol" /f >nul
reg add "HKCR\3dprint" /v "URL Protocol" /d "" /f >nul
reg add "HKCR\3dprint\DefaultIcon" /ve /d "\"%EXE%\",1" /f >nul
reg add "HKCR\3dprint\shell\open\command" /ve /d "\"%EXE%\" \"%%1\"" /f >nul

REM Create root key for print3d://
reg add "HKCR\print3d" /ve /d "URL:print3d Protocol" /f >nul
reg add "HKCR\print3d" /v "URL Protocol" /d "" /f >nul
reg add "HKCR\print3d\DefaultIcon" /ve /d "\"%EXE%\",1" /f >nul
reg add "HKCR\print3d\shell\open\command" /ve /d "\"%EXE%\" \"%%1\"" /f >nul

if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Failed to write registry keys. Try running as Administrator.
  exit /b 1
)

echo Successfully registered 3dprint:// and print3d:// protocols.
echo If your browser prompts, choose to always allow the dashboard to open 3dprint links.
exit /b 0



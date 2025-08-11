# SlicerOpener (3dprint:// & print3d:// Protocol Handler)

This tool handles `3dprint://open?path=<urlencoded absolute path>` and `print3d://open?path=<urlencoded absolute path>` links on Windows. It reads `config.ini`, validates the requested file path, chooses a compatible slicer by extension, launches it, shows GUI success/error dialogs, and writes logs.

## Files
- `SlicerOpener.py` — Python app (tkinter dialogs, rotating logs)
- `config.example.ini` — Copy to `config.ini` and edit for your lab
- `register.bat` — Registers both `3dprint://` and `print3d://` protocols (run as Administrator)

## Build (PyInstaller)
1) Install Python 3.11+ and PyInstaller:
```
py -3 -m pip install pyinstaller
```
2) Build one-file exe:
```
py -3 -m PyInstaller --onefile --noconsole SlicerOpener.py
```
Output: `dist/SlicerOpener.exe`

## Install on a workstation
1) Create folder: `C:\\Program Files\\SlicerOpener\\`
2) Copy `dist/SlicerOpener.exe` and `config.example.ini` → rename to `config.ini` and edit
3) Run `register.bat` as Administrator (from the same folder)
4) On first use, allow your browser to open `3dprint://` links for the dashboard site

## Configure `config.ini`
```
[main]
AUTHORITATIVE_STORAGE_BASE_PATH = Z:\\storage
LOG_PATH = C:\\ProgramData\\SlicerOpener\\sliceropener.log

[slicer_prusa]
name = PrusaSlicer
path = C:\\Program Files\\Prusa3D\\PrusaSlicer\\prusa-slicer.exe
extensions = .stl,.3mf,.obj

[slicer_formlabs]
name = PreForm
path = C:\\Program Files\\Formlabs\\PreForm\\PreForm.exe
extensions = .form,.stl
```
Notes:
- Storage base path must match the exact drive+path used on all staff PCs
- Log directory will be created if missing
- Add more `[slicer_*]` sections as needed; extensions are case-insensitive

## Usage
- Click "Open File" in the dashboard → browser opens `print3d://...` (or `3dprint://...` for legacy)
- Windows launches `SlicerOpener.exe`
- App validates, selects slicer (or prompts), launches, shows success dialog; errors show clear dialogs

## Troubleshooting
- Path not under base/doesn’t exist → check drive mapping and network share
- No compatible slicer → add mapping in `config.ini`
- Executable not found → fix slicer `path` in `config.ini`
- Protocol not registered → re-run `register.bat` as Administrator

## Security
- Only opens files within `AUTHORITATIVE_STORAGE_BASE_PATH`
- Normalizes and compares paths to prevent traversal

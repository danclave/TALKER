@echo off
rem Builds BOTH mic executables into dist\:
rem   talker_mic.exe      - new Textual TUI (mouse support)
rem   talker_mic_old.exe  - classic prompt_toolkit TUI
rem Uses the project venv when present.
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set PY=python
)
set "COMMON=--onefile --icon=talker_mic.ico --hidden-import=gemini_proxy --hidden-import=whisper_local --hidden-import=whisper_api --hidden-import=vosk_local --collect-binaries vosk --collect-data vosk --exclude-module PIL --exclude-module matplotlib --exclude-module pandas --exclude-module scipy --exclude-module tkinter --exclude-module IPython --exclude-module pytest --exclude-module sphinx --exclude-module setuptools --exclude-module wheel --exclude-module pydoc_data --exclude-module onnxruntime --copy-metadata textual --copy-metadata rich"

"%PY%" -m PyInstaller %COMMON% --name talker_mic main.py
if errorlevel 1 exit /b 1
"%PY%" -m PyInstaller %COMMON% --name talker_mic_old main_old.py

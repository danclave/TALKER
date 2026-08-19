@echo off
rem Build the talker_mic executable. Uses the project venv when present.
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set PY=python
)
"%PY%" -m PyInstaller --onefile --name talker_mic --icon=talker_mic.ico ^
  --hidden-import=gemini_proxy --hidden-import=whisper_local --hidden-import=whisper_api --hidden-import=vosk_local ^
  --collect-binaries vosk --collect-data vosk ^
  --exclude-module PIL --exclude-module matplotlib --exclude-module pandas ^
  --exclude-module scipy --exclude-module tkinter --exclude-module IPython ^
  --exclude-module pytest --exclude-module sphinx --exclude-module setuptools ^
  --exclude-module wheel --exclude-module pydoc_data --exclude-module onnxruntime ^
  main.py

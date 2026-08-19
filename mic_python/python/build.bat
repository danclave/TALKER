@echo off
rem Builds the talker_mic executable (Textual TUI) into dist\.
rem NOTE: --splash requires Pillow installed at BUILD time (pip install pillow)
rem       to process splash.png; the runtime splash needs no Pillow.
rem The classic TUI lives in _old\ and is intentionally NOT built.
rem Uses the project venv when present.
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
) else (
    set PY=python
)
"%PY%" -m PyInstaller --onefile --name talker_mic --icon=talker_mic.ico --splash splash.png ^
  --hidden-import=gemini_proxy --hidden-import=whisper_local --hidden-import=whisper_api --hidden-import=vosk_local ^
  --collect-binaries vosk --collect-data vosk ^
  --exclude-module matplotlib --exclude-module pandas ^
  --exclude-module scipy --exclude-module IPython ^
  --exclude-module pytest --exclude-module sphinx --exclude-module setuptools ^
  --exclude-module wheel --exclude-module pydoc_data --exclude-module onnxruntime ^
  --copy-metadata textual --copy-metadata rich ^
  main.py

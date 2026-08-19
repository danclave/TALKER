python -m PyInstaller --onefile --name talker_mic --icon=talker_mic.ico --hidden-import=gemini_proxy --hidden-import=whisper_local --hidden-import=whisper_api --hidden-import=vosk_local main.py

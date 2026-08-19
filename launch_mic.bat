@echo off
IF NOT EXIST talker_mic.exe (
    echo talker_mic.exe not found.
    echo Please download it from the latest release on GitHub:
    echo https://github.com/Mirrowel/TALKER/releases
    pause
    exit
)

echo Starting TALKER Mic...
echo The configuration menu will appear in the new window.
echo.
start "TALKER Mic" talker_mic.exe
echo The microphone application has been launched in a new window.
echo You can close this window now.
timeout /t 3 >nul

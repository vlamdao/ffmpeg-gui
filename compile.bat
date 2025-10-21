@echo off
REM File compile.bat - Build FFmpeg GUI exe with PyInstaller

pyinstaller --onefile --windowed --noconsole --icon=icon/ffmpeg.ico --add-data "icon;icon" --name="FFmpeg GUI" main.py

pause

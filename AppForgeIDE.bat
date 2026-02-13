@echo off
REM Launch the native IDE for App Forge
cd /d "%~dp0projects\app-forge\ide"
python native_ide.py

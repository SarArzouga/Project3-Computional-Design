@echo off
rem Double-click this file in Windows File Explorer (not in Jupyter) to start the TopOpt3D app
cd /d "%~dp0"
"%USERPROFILE%\anaconda3\python.exe" -m gui
if errorlevel 1 pause

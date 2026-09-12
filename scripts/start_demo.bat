@echo off
title Smart Parking - Launch End-to-End Demo
echo ========================================================
echo   KHOI DONG TRINH DEMO HE THONG SMART PARKING (SIC IoT)
echo ========================================================

:: 1. Khoi dong Python ESP32 Simulator trong cua so cmd rieng
echo [1/3] Khoi dong bo gia lap phan cung ESP32 ket noi Firebase...
start "ESP32 Hardware Simulator (Firebase)" cmd /k "title ESP32 Simulator && cd /d "%~dp0" && python simulate_esp32.py"

:: 2. Mo trinh duyet sau 2 giay
echo [2/3] Mo trinh duyet tai http://localhost:5173/owner/gate ...
start "" http://localhost:5173/owner/gate

:: 3. Khoi dong Web Server Frontend
echo [3/3] Khoi dong Vite Frontend Dev Server...
cd /d "%~dp0..\frontend"

set NPM_CMD=npm
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "E:\node-v20.20.2-win-x64\npm.cmd" (
        set NPM_CMD="E:\node-v20.20.2-win-x64\npm.cmd"
    )
)

%NPM_CMD% run dev
pause

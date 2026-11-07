@echo off
title Smart Parking - Launch End-to-End Demo (TimescaleDB)
echo ========================================================
echo   KHOI DONG TRINH DEMO HE THONG SMART PARKING (TIMESCALEDB)
echo ========================================================

:: 1. Khoi dong Backend API
echo [1/4] Khoi dong Backend API (Node.js + TimescaleDB)...
start "Smart Parking Backend API" cmd /k "title Backend API && cd /d "%~dp0..\backend" && npm start"

:: 2. Cho Backend 2s roi bat ESP32 Simulator
timeout /t 2 /nobreak >nul
echo [2/4] Khoi dong bo gia lap phan cung ESP32 ket noi Backend...
start "ESP32 Hardware Simulator (TimescaleDB)" cmd /k "title ESP32 Simulator && cd /d "%~dp0" && python simulate_esp32.py"

:: 3. Mo trinh duyet
echo [3/4] Mo trinh duyet tai http://localhost:5173/owner/gate ...
start "" http://localhost:5173/owner/gate

:: 4. Khoi dong Web Server Frontend
echo [4/4] Khoi dong Vite Frontend Dev Server...
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

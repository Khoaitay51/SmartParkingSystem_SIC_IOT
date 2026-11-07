@echo off
title Smart Parking - Backend Service (TimescaleDB API)
echo ========================================================
echo   KHOI DONG BACKEND API SERVICE (Node.js)
echo ========================================================
cd /d "%~dp0..\backend"

set NPM_CMD=npm
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "E:\node-v20.20.2-win-x64\npm.cmd" (
        set NPM_CMD="E:\node-v20.20.2-win-x64\npm.cmd"
    )
)

%NPM_CMD% start
pause

@echo off
title Smart Parking - Frontend Dev Server
echo ========================================================
echo   KHOI DONG FRONTEND DEV SERVER (Vite + React)
echo ========================================================
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

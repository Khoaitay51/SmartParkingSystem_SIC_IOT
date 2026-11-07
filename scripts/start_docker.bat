@echo off
title Smart Parking - Docker TimescaleDB & Backend
echo ========================================================
echo   KHOI DONG DOCKER TIMESCALEDB & BACKEND SERVICE
echo ========================================================
cd /d "%~dp0.."

echo Dang khoi dong container TimescaleDB va Backend API...
docker-compose up -d

echo.
echo Kiem tra trang thai container:
docker-compose ps

echo.
echo ========================================================
echo TimescaleDB: localhost:5432 (User: postgres, DB: smartparking)
echo Backend API: http://localhost:3000
echo Health check: http://localhost:3000/api/health
echo ========================================================
pause

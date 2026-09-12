@echo off
title Smart Parking - Serial Monitor ESP32 (115200 baud)
echo ========================================================
echo   THEO DOI LOG SERIAL TRUC TIEP TU ESP32 (115200 baud)
echo ========================================================
echo.
echo Hay dam bao kit ESP32 da duoc cam vao cong USB may tinh.
echo Bấm phím Ctrl + C hoac Ctrl + ] de thoat.
echo.

cd /d "%~dp0..\firmware"

set PIO_CMD=pio
where pio >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%USERPROFILE%\.platformio\penv\Scripts\pio.exe" (
        set PIO_CMD="%USERPROFILE%\.platformio\penv\Scripts\pio.exe"
    )
)

%PIO_CMD% device monitor -b 115200
pause

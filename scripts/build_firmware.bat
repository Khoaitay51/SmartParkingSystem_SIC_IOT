@echo off
title Smart Parking - Build ESP32 Firmware
echo ========================================================
echo   BIEN DICH FIRMWARE ESP32 (PlatformIO)
echo ========================================================
cd /d "%~dp0..\firmware"

set PIO_CMD=pio
where pio >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%USERPROFILE%\.platformio\penv\Scripts\pio.exe" (
        set PIO_CMD="%USERPROFILE%\.platformio\penv\Scripts\pio.exe"
    )
)

%PIO_CMD% run
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Bien dich that bai! Vui long kiem tra lai thiet lap PlatformIO.
) else (
    echo.
    echo [SUCCESS] Bien dich thanh cong! File binary tao tai .pio\build\esp32dev\firmware.bin
)
pause

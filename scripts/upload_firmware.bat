@echo off
title Smart Parking - Upload Firmware to ESP32
echo ========================================================
echo   NAP CODE FIRMWARE LEN KIT ESP32 (PlatformIO Upload)
echo ========================================================
echo.
echo Hay dam bao:
echo  1. Da cam kit ESP32 vao cong USB may tinh.
echo  2. Da dien dung WiFi SSID va Password trong firmware\include\config.h.
echo.
pause

cd /d "%~dp0..\firmware"

set PIO_CMD=pio
where pio >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%USERPROFILE%\.platformio\penv\Scripts\pio.exe" (
        set PIO_CMD="%USERPROFILE%\.platformio\penv\Scripts\pio.exe"
    )
)

echo Dang bien dich va nap firmware vao ESP32...
%PIO_CMD% run -t upload

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Nap code that bai!
    echo Goi y:
    echo  - Neu bao loi 'Could not open port', hay cai driver CH340 / CP2102.
    echo  - Khi hien chu 'Connecting.....', hay nhan giu nut 'BOOT' tren kit ESP32 khoang 2 giay.
) else (
    echo.
    echo [SUCCESS] DA NAP FIRMWARE THANH CONG!
    echo Kit ESP32 dang khoi dong va ket noi WiFi + Firebase...
)
pause

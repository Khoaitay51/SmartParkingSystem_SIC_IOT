@echo off
title Smart Parking - Mo Slide Bao Cao Thuyet Trinh
echo ========================================================
echo   DANG MO SLIDE BAO CAO DU AN TRONG TRINH DUYET...
echo ========================================================
cd /d "%~dp0"
start slide_bao_cao.html
echo.
echo Da mo thanh cong file slide_bao_cao.html!
echo Huong dan dieu khien khi thuyet trinh:
echo  - Phim [Mui ten phai] hoac [Space]: Chuyen sang slide tiep theo
echo  - Phim [Mui ten trai]: Quay lai slide truoc
echo  - Phim [F]: Bat / tat che do Toan man hinh (Fullscreen)
echo  - Phim [1] - [9], [0], [-]: Nhay thang den slide 1 den 11
echo ========================================================
timeout /t 3 >nul

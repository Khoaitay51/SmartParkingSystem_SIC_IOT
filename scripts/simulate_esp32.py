#!/usr/bin/env python3
"""
=============================================================================
Smart Parking System - ESP32 Hardware Simulator (Python)
Mô phỏng phần cứng ESP32 gửi dữ liệu lên Firebase Realtime Database
và nhận lệnh điều khiển cổng từ Web Frontend theo thời gian thực.
=============================================================================
Sử dụng:
    python simulate_esp32.py
"""

import sys
import time
import json
import random
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình Firebase Realtime Database (Trùng với config.h và firebase.ts)
FIREBASE_URL = "https://smartparking-139b7-default-rtdb.asia-southeast1.firebasedatabase.app"
LOT_ID = "lot_mydinh"
LOT_NAME = "B7 Mỹ Đình"

# Trạng thái ban đầu
slots = {"1": False, "2": False, "3": False, "4": False}
gates = {"in": "closed", "out": "closed"}
gate_in_timer = 0
gate_out_timer = 0

def push_status(distance=25.0):
    free_count = sum(1 for occupied in slots.values() if not occupied)
    payload = {
        "lotId": LOT_ID,
        "lotName": LOT_NAME,
        "totalSlots": 4,
        "freeSlots": free_count,
        "distance": round(distance, 1),
        "lastHeartbeat": int(time.time() * 1000),
        "slots": slots,
        "gates": gates
    }
    try:
        url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status.json"
        res = requests.put(url, json=payload, timeout=5)
        if res.status_code == 200:
            print(f"[STATUS] Đã đồng bộ Firebase: Trống {free_count}/4 ô | Khoảng cách: {payload['distance']} cm | Cổng vào: {gates['in']}")
        else:
            print(f"[WARN] Firebase trả về status: {res.status_code}")
    except Exception as e:
        print(f"[ERROR] Lỗi gửi dữ liệu lên Firebase: {e}")

def check_commands():
    global gates, gate_in_timer, gate_out_timer
    try:
        url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.text != "null":
            data = res.json() or {}
            # Kiểm tra lệnh mở cổng vào
            if data.get("gateIn") == "open":
                print("\n🔔 [FIREBASE CMD] NHẬN LỆNH MỞ CỔNG VÀO TỪ WEB FRONTEND!")
                gates["in"] = "open"
                gate_in_timer = time.time()
                # Reset lệnh về idle
                requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands/gateIn.json", json="idle", timeout=3)

            # Kiểm tra lệnh mở cổng ra
            if data.get("gateOut") == "open":
                print("\n🔔 [FIREBASE CMD] NHẬN LỆNH MỞ CỔNG RA TỪ WEB FRONTEND!")
                gates["out"] = "open"
                gate_out_timer = time.time()
                # Reset lệnh về idle
                requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands/gateOut.json", json="idle", timeout=3)
    except Exception as e:
        pass

def main():
    global gates, gate_in_timer, gate_out_timer
    print("=" * 60)
    print(f"  ESP32 SIMULATOR - BÃI ĐỖ XE {LOT_NAME.upper()} (SIC IoT)")
    print(f"  Firebase URL: {FIREBASE_URL}")
    print("=" * 60)
    print("Mô phỏng bắt đầu chạy. Bạn hãy mở Web Frontend vào trang")
    print("  'Cổng IoT' (Owner) để xem dữ liệu nhảy realtime và bấm thử nút Mở cổng!")
    print("Nhấn Ctrl+C để dừng.")
    print("-" * 60)

    # Đặt lệnh ban đầu là idle
    try:
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands.json", json={"gateIn": "idle", "gateOut": "idle"}, timeout=5)
    except Exception:
        pass

    last_sync = 0
    last_toggle = time.time()

    while True:
        now = time.time()

        # Kiểm tra đóng barrier sau 4 giây mở
        if gates["in"] == "open" and now - gate_in_timer > 4:
            print("[BARRIER] Hết 4 giây -> Đóng Cổng Vào an toàn.")
            gates["in"] = "closed"
        if gates["out"] == "open" and now - gate_out_timer > 4:
            print("[BARRIER] Hết 4 giây -> Đóng Cổng Ra an toàn.")
            gates["out"] = "closed"

        # Giả lập xe ra/vào ngẫu nhiên sau mỗi 12-15 giây để test UI
        if now - last_toggle > 12:
            last_toggle = now
            random_slot = str(random.randint(1, 4))
            slots[random_slot] = not slots[random_slot]
            status_text = "Có xe đỗ vào" if slots[random_slot] else "Xe đã rời đi"
            print(f"\n🚗 [MÔ PHỎNG XE] Ô {random_slot}: {status_text}!")

        # Kiểm tra lệnh mở cổng từ Firebase
        check_commands()

        # Đồng bộ trạng thái mỗi 1.5 giây
        if now - last_sync >= 1.5:
            last_sync = now
            simulated_dist = random.uniform(15.0, 45.0)
            push_status(simulated_dist)

        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Đã dừng mô phỏng.")

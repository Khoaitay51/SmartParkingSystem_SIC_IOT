#!/usr/bin/env python3
"""
=============================================================================
Smart Parking System - ESP32 Hardware Simulator (TimescaleDB & Multi-Lot)
Mô phỏng phần cứng ESP32 gửi dữ liệu telemetry lên TimescaleDB Backend
và nhận lệnh điều khiển cổng từ Web Frontend theo thời gian thực.
=============================================================================
Sử dụng:
    python simulate_esp32.py
    python simulate_esp32.py --lot lot_caugiay
"""

import sys
import time
import json
import random
import requests
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser(description="ESP32 Simulator for Smart Parking")
parser.add_argument("--lot", default="lot_mydinh", help="ID của bãi đỗ xe (mặc định: lot_mydinh)")
parser.add_argument("--backend", default="http://localhost:3000/api", help="URL Backend API")
args = parser.parse_args()

BACKEND_URL = args.backend
LOT_ID = args.lot
LOT_NAME = "B7 Mỹ Đình" if LOT_ID == "lot_mydinh" else f"Bãi {LOT_ID}"

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
        "totalSlots": len(slots),
        "freeSlots": free_count,
        "distance": round(distance, 1),
        "lastHeartbeat": int(time.time() * 1000),
        "slots": slots,
        "gates": gates
    }
    try:
        url = f"{BACKEND_URL}/lots/{LOT_ID}/status"
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            print(f"[STATUS] Đã đồng bộ TimescaleDB: Trống {free_count}/{len(slots)} ô | KC: {payload['distance']} cm | Cổng: [Vào: {gates['in']}, Ra: {gates['out']}]")
        else:
            print(f"[WARN] Backend trả về status: {res.status_code}")
    except Exception as e:
        print(f"[ERROR] Lỗi gửi dữ liệu lên Backend TimescaleDB: {e}")

def check_commands():
    global gates, gate_in_timer, gate_out_timer
    try:
        url = f"{BACKEND_URL}/lots/{LOT_ID}/commands"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json() or {}
            # Kiểm tra lệnh mở cổng vào
            if data.get("gateIn") == "open":
                print("\n🔔 [BACKEND CMD] NHẬN LỆNH MỞ CỔNG VÀO TỪ WEB FRONTEND!")
                gates["in"] = "open"
                gate_in_timer = time.time()
                requests.put(f"{BACKEND_URL}/lots/{LOT_ID}/commands/gateIn", json={"value": "idle"}, timeout=3).raise_for_status()

            # Kiểm tra lệnh mở cổng ra
            if data.get("gateOut") == "open":
                print("\n🔔 [BACKEND CMD] NHẬN LỆNH MỞ CỔNG RA TỪ WEB FRONTEND!")
                gates["out"] = "open"
                gate_out_timer = time.time()
                requests.put(f"{BACKEND_URL}/lots/{LOT_ID}/commands/gateOut", json={"value": "idle"}, timeout=3).raise_for_status()
    except Exception:
        pass

def main():
    global gates, gate_in_timer, gate_out_timer
    print("=" * 68)
    print(f"  ESP32 SIMULATOR - BÃI ĐỖ XE {LOT_NAME.upper()} (TIMESCALEDB)")
    print(f"  Backend URL: {BACKEND_URL}")
    print(f"  Bãi xe mô phỏng: {LOT_ID}")
    print("=" * 68)
    print("Mô phỏng đang chạy. Dữ liệu cảm biến được ghi vào TimescaleDB Hypertable")
    print("và broadcast Realtime qua SSE tới Web Frontend.")
    print("Nhấn Ctrl+C để dừng.")
    print("-" * 68)

    last_sync = 0
    last_toggle = time.time()

    while True:
        now = time.time()

        # Kiểm tra đóng cổng an toàn sau 4 giây
        if gates["in"] == "open" and now - gate_in_timer >= 4:
            gates["in"] = "closed"
            print("🚪 Cổng vào: Tự động đóng lại an toàn.")
            push_status()

        if gates["out"] == "open" and now - gate_out_timer >= 4:
            gates["out"] = "closed"
            print("🚪 Cổng ra: Tự động đóng lại an toàn.")
            push_status()

        # Kiểm tra lệnh từ xa mỗi 500ms
        check_commands()

        # Đẩy dữ liệu định kỳ mỗi 1.5 giây
        if now - last_sync >= 1.5:
            dist = round(random.uniform(15.0, 45.0), 1)
            push_status(distance=dist)
            last_sync = now

        # Thỉnh thoảng mô phỏng xe vào/ra ô đỗ ngẫu nhiên (mỗi 18 giây)
        if now - last_toggle >= 18:
            slot_key = str(random.randint(1, len(slots)))
            slots[slot_key] = not slots[slot_key]
            action = "🚗 CÓ XE ĐỖ VÀO" if slots[slot_key] else "🅿️ XE RỜI ĐI (TRỐNG)"
            print(f"\n[EVENT PHẦN CỨNG] Ô {slot_key}: {action}")
            push_status()
            last_toggle = now

        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[DỪNG] Đã tắt mô phỏng ESP32.")

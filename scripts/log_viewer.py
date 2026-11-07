#!/usr/bin/env python3
"""
=============================================================================
  SMART PARKING - TRÌNH THEO DÕI NHẬT KÝ THỜI GIAN THỰC (TIMESCALEDB LIVE LOG)
  Lắng nghe toàn bộ sự kiện từ Docker TimescaleDB Backend:
  - Thay đổi ô đỗ (Ô 1-4 có xe / trống)
  - Đóng / mở Barrier Cổng Vào & Cổng Ra
  - Quét biển số xe AI Camera OCR & tự động trừ tiền ví
  - Cảnh báo khoảng cách siêu âm HC-SR04 & còi Buzzer
=============================================================================
"""

import sys
import time
from datetime import datetime
import requests
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser(description="Live Log Viewer")
parser.add_argument("--lot", default="lot_mydinh", help="ID bãi xe (mặc định: lot_mydinh)")
parser.add_argument("--backend", default="http://localhost:3000/api", help="URL Backend API")
args, unknown = parser.parse_known_args()

BACKEND_URL = args.backend
LOT_ID = args.lot

def get_now():
    return datetime.now().strftime("%H:%M:%S")

def main():
    print("=" * 68)
    print("      SMART PARKING - TRÌNH GIÁM SÁT NHẬT KÝ THỜI GIAN THỰC (LIVE LOG)")
    print("=" * 68)
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Bãi xe theo dõi: {LOT_ID}")
    print("  Database: Docker TimescaleDB (Time-Series Hypertables)")
    print("  Trạng thái: Đang theo dõi... (Bấm Ctrl + C để dừng)")
    print("=" * 68)

    last_slots = None
    last_gates = None
    last_distance = None
    last_ocr_ts = None

    url = f"{BACKEND_URL}/lots/{LOT_ID}/status"
    ocr_url = f"{BACKEND_URL}/lots/{LOT_ID}/ocr"

    print(f"[{get_now()}] 🟢 [HỆ THỐNG] Đã kết nối TimescaleDB Backend thành công. Chờ sự kiện...\n")

    while True:
        try:
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                status = res.json()
                curr_slots = status.get("slots", {})
                curr_gates = status.get("gates", {"in": "closed", "out": "closed"})
                curr_dist = status.get("distance", -1)
                free = status.get("freeSlots", "?")

                # 1. So sánh trạng thái Ô đỗ
                if last_slots is not None:
                    for slot_k, occ in curr_slots.items():
                        if occ != last_slots.get(slot_k):
                            if occ:
                                print(f"[{get_now()}] 🚗 [Ô ĐỖ] Ô {slot_k}: PHÁT HIỆN CÓ XE ĐỖ VÀO!  | Còn trống: {free} chỗ")
                            else:
                                print(f"[{get_now()}] 🅿️ [Ô ĐỖ] Ô {slot_k}: XE ĐÃ RỜI ĐI (TRỐNG)!    | Còn trống: {free} chỗ")
                else:
                    print(f"[{get_now()}] ℹ️ [TRẠNG THÁI HIỆN TẠI] Bãi đang trống {free} chỗ. Các ô: {curr_slots}")

                # 2. So sánh trạng thái Barrier Cổng
                if last_gates is not None:
                    if curr_gates.get("in") != last_gates.get("in"):
                        state_str = "MỞ 90° (XE QUA)" if curr_gates.get("in") == "open" else "ĐÃ ĐÓNG LẠI"
                        print(f"[{get_now()}] 🚪 [BARRIER VÀO] Cổng Vào -> {state_str}")
                    if curr_gates.get("out") != last_gates.get("out"):
                        state_str = "MỞ 90° (XE QUA)" if curr_gates.get("out") == "open" else "ĐÃ ĐÓNG LẠI"
                        print(f"[{get_now()}] 🚪 [BARRIER RA]  Cổng Ra  -> {state_str}")

                # 3. So sánh khoảng cách siêu âm & Còi Buzzer
                if curr_dist >= 0 and last_distance is not None:
                    if curr_dist <= 10 and last_distance > 10:
                        print(f"[{get_now()}] 🚨 [CẢNH BÁO LÙI] Xe đỗ quá sát ({curr_dist} cm <= 10 cm)! CÒI BUZZER KÊU LIÊN TỤC!")
                    elif curr_dist > 10 and last_distance <= 10:
                        print(f"[{get_now()}] 🟢 [CẢNH BÁO LÙI] Xe đã rời khoảng cách nguy hiểm ({curr_dist} cm). Tắt còi báo động.")

                last_slots = dict(curr_slots)
                last_gates = dict(curr_gates)
                last_distance = curr_dist

            # Kiểm tra OCR
            ocr_res = requests.get(ocr_url, timeout=3)
            if ocr_res.status_code == 200:
                ocr_data = ocr_res.json()
                if ocr_data and isinstance(ocr_data, dict):
                    ts = ocr_data.get("timestamp")
                    if ts and (last_ocr_ts is None or ts > last_ocr_ts):
                        plate = ocr_data.get("plate", "")
                        direction = ocr_data.get("direction", "in")
                        fee = ocr_data.get("fee", 0)
                        vname = ocr_data.get("vehicleName", "")
                        slot = ocr_data.get("slot", "")

                        if direction == "in":
                            print(f"[{get_now()}] 📷 [AI CAMERA OCR] Xe {plate} ({vname}) VÀO bãi -> Mở Barrier Cổng Vào -> Hướng dẫn đỗ Ô {slot}")
                        else:
                            print(f"[{get_now()}] 💳 [AI CAMERA OCR] Xe {plate} ({vname}) RA bãi -> Phí: {fee:,.0f} ₫ -> Tự động trừ ví -> Mở Barrier Cổng Ra")
                        last_ocr_ts = ts

        except Exception:
            pass

        time.sleep(0.8)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[DỪNG] Đã tắt Live Log Viewer.")

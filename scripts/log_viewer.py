#!/usr/bin/env python3
"""
=============================================================================
  SMART PARKING - TRÌNH THEO DÕI NHẬT KÝ THỜI GIAN THỰC (REALTIME LOG VIEWER)
  Lắng nghe toàn bộ sự kiện từ Firebase Realtime Database:
  - Thay đổi ô đỗ (Ô 1-4 có xe / trống)
  - Đóng / mở Barrier Cổng Vào & Cổng Ra
  - Quét biển số xe AI Camera OCR & tự động trừ tiền
  - Cảnh báo khoảng cách siêu âm HC-SR04 & còi Buzzer
=============================================================================
"""

import sys
import time
from datetime import datetime
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

FIREBASE_URL = "https://smartparking-139b7-default-rtdb.asia-southeast1.firebasedatabase.app"
LOT_ID = "lot_mydinh"

def get_now():
    return datetime.now().strftime("%H:%M:%S")

def extract_slots(raw_slots):
    result = {1: False, 2: False, 3: False, 4: False}
    if isinstance(raw_slots, list):
        for i in range(1, 5):
            if i < len(raw_slots):
                result[i] = bool(raw_slots[i])
            elif (i - 1) < len(raw_slots):
                result[i] = bool(raw_slots[i - 1])
    elif isinstance(raw_slots, dict):
        for i in range(1, 5):
            result[i] = bool(raw_slots.get(str(i), False))
    return result

def main():
    print("=" * 68)
    print("      SMART PARKING - TRÌNH GIÁM SÁT NHẬT KÝ THỜI GIAN THỰC (LIVE LOG)")
    print("=" * 68)
    print(f"  Đích kết nối: {FIREBASE_URL}")
    print(f"  Bãi xe theo dõi: {LOT_ID} (B7 Mỹ Đình)")
    print("  Trạng thái: Đang theo dõi... (Bấm Ctrl + C để dừng)")
    print("=" * 68)

    last_slots = None
    last_gates = None
    last_distance = None
    last_ocr_ts = None
    last_heartbeat = None

    url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}.json"

    # In thông báo khởi động
    print(f"[{get_now()}] 🟢 [HỆ THỐNG] Đã kết nối Firebase RTDB thành công. Chờ sự kiện...\n")

    while True:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200 and res.text != "null":
                lot_data = res.json()
                if isinstance(lot_data, dict):
                    status = lot_data.get("status", {})
                    ocr = lot_data.get("ocr", {})

                    curr_slots = extract_slots(status.get("slots"))
                    curr_gates = status.get("gates", {})
                    if not isinstance(curr_gates, dict):
                        curr_gates = {"in": "closed", "out": "closed"}
                    curr_dist = status.get("distance", -1)
                    curr_hb = status.get("lastHeartbeat", 0)

                    # 1. So sánh trạng thái Ô đỗ 1 - 4
                    if last_slots is not None:
                        for i in range(1, 5):
                            if curr_slots[i] != last_slots[i]:
                                free = status.get("freeSlots", sum(1 for v in curr_slots.values() if not v))
                                if curr_slots[i]:
                                    print(f"[{get_now()}] 🚗 [Ô ĐỖ] Ô {i}: PHÁT HIỆN CÓ XE ĐỖ VÀO!  | Còn trống: {free}/4 chỗ")
                                else:
                                    print(f"[{get_now()}] 🅿️ [Ô ĐỖ] Ô {i}: XE ĐÃ RỜI ĐI (TRỐNG)!    | Còn trống: {free}/4 chỗ")
                    else:
                        free = status.get("freeSlots", sum(1 for v in curr_slots.values() if not v))
                        print(f"[{get_now()}] ℹ️ [TRẠNG THÁI HIỆN TẠI] Bãi đang trống {free}/4 chỗ. Các ô: {curr_slots}")

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
                            print(f"[{get_now()}] 🚨 [CẢNH BÁO SIÊU ÂM] Xe đỗ quá sát ({curr_dist:.1f} cm <= 10cm) -> CÒI BUZZER ĐANG KÊU BÁO ĐỘNG!")
                        elif curr_dist > 10 and last_distance <= 10:
                            print(f"[{get_now()}] 🔊 [SIÊU ÂM] Xe đã lùi an toàn ({curr_dist:.1f} cm) -> Còi báo động đã tắt.")

                    # 4. Kiểm tra sự kiện Camera AI OCR
                    if isinstance(ocr, dict) and ocr.get("timestamp"):
                        curr_ocr_ts = ocr.get("timestamp")
                        if last_ocr_ts is not None and curr_ocr_ts > last_ocr_ts:
                            plate = ocr.get("plate", "Chưa rõ")
                            direction = ocr.get("direction", "in")
                            v_name = ocr.get("vehicleName", "")
                            fee = ocr.get("fee", 0)
                            slot = ocr.get("slot")

                            if direction == "in":
                                print(f"[{get_now()}] 📷 [AI OCR VÀO] Quét biển số: {plate} ({v_name}) -> Vào bãi{f' (Ô {slot})' if slot else ''} -> Mở Cổng Vào!")
                            else:
                                print(f"[{get_now()}] 📷 [AI OCR RA]  Quét biển số: {plate} ({v_name}) -> Rời bãi -> Phí: {fee:,.0f} ₫ -> Tự động trừ ví tài xế -> Mở Cổng Ra!")

                        last_ocr_ts = curr_ocr_ts

                    last_slots = curr_slots
                    last_gates = curr_gates
                    last_distance = curr_dist
                    last_heartbeat = curr_hb

        except Exception as e:
            pass

        time.sleep(0.6)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã dừng theo dõi log.")

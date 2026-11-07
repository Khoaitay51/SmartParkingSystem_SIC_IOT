#!/usr/bin/env python3
"""
=============================================================================
  SMART PARKING - BẢNG ĐIỀU KHIỂN THỰC TẾ (TIMESCALEDB CONTROLLER)
  Hệ thống mô phỏng & điều khiển bãi xe (Hỗ trợ Multi-Lot & TimescaleDB):
  - Cho xe vào / xe ra các ô đỗ
  - Quét biển số AI Camera OCR tự động mở cổng và trừ tiền ví tài xế
  - Điều khiển mở barrier Cổng Vào / Cổng Ra
  - Thay đổi khoảng cách cảm biến siêu âm HC-SR04 kích hoạt còi Buzzer
=============================================================================
"""

import sys
import time
import requests
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser(description="Smart Parking Terminal Controller")
parser.add_argument("--lot", default="lot_mydinh", help="ID bãi xe (mặc định: lot_mydinh)")
parser.add_argument("--backend", default="http://localhost:3000/api", help="URL Backend API")
args, unknown = parser.parse_known_args()

BACKEND_URL = args.backend
LOT_ID = args.lot

# Danh sách xe mẫu đã đăng ký trong hệ thống ParkIQ
SAMPLE_CARS = {
    "1": {
        "plate": "30A-123.45",
        "name": "VinFast VF8",
        "owner": "Nguyễn Văn An (0912345678)",
        "slot": 1,
        "fee": 15000,
    },
    "2": {
        "plate": "51G-456.78",
        "name": "Honda CR-V",
        "owner": "Trần Thị Bình (0987654321)",
        "slot": 2,
        "fee": 20000,
    },
    "3": {
        "plate": "30H-888.66",
        "name": "Toyota Corolla Cross",
        "owner": "Phạm Tuấn Anh (0933445566)",
        "slot": 3,
        "fee": 15000,
    },
}

def get_current_status():
    url = f"{BACKEND_URL}/lots/{LOT_ID}/status"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[LỖI] Không thể đọc từ Backend: {e}")
    return {
        "slots": {"1": False, "2": False, "3": False, "4": False},
        "freeSlots": 4,
        "totalSlots": 4,
        "distance": 25.0,
        "gates": {"in": "closed", "out": "closed"}
    }

def toggle_slot(slot_num):
    data = get_current_status()
    slots = data.get("slots", {})
    current_state = bool(slots.get(str(slot_num), False))
    new_state = not current_state

    # Cập nhật ô đỗ lên Backend
    url = f"{BACKEND_URL}/lots/{LOT_ID}/slots/{slot_num}"
    res = requests.put(url, json={"occupied": new_state}, timeout=5)

    action_text = "🚗 XE ĐÃ ĐỖ VÀO" if new_state else "🅿️ XE ĐÃ RỜI ĐI (TRỐNG)"
    free_count = res.json().get("freeSlots", "?") if res.status_code == 200 else "?"
    print(f"\n=> ĐÃ CẬP NHẬT: Ô {slot_num} -> {action_text}! (Còn trống {free_count} ô)")

def set_distance(dist):
    url = f"{BACKEND_URL}/lots/{LOT_ID}/distance"
    requests.put(url, json={"distance": dist}, timeout=5)
    alert = "🚨 (ĐỖ QUÁ SÁT - CÒI KÊU!)" if dist <= 10 else ""
    print(f"\n=> ĐÃ CẬP NHẬT: Khoảng cách xe = {dist} cm {alert}")

def set_gate(gate_name):
    # gate_name: 'gateIn' hoặc 'gateOut'
    url = f"{BACKEND_URL}/lots/{LOT_ID}/commands"
    requests.post(url, json={"gate": gate_name, "action": "open"}, timeout=5)
    print(f"\n=> ĐÃ GỬI LỆNH MỞ CỔNG {gate_name.upper()} 90 ĐỘ!")

def trigger_ocr(plate, direction, vehicle_name="Xe cá nhân", slot_num=1, fee=15000):
    url = f"{BACKEND_URL}/lots/{LOT_ID}/ocr"
    payload = {
        "plate": plate,
        "direction": direction,
        "vehicleName": vehicle_name,
        "slot": slot_num,
        "fee": fee if direction == "out" else 0
    }
    res = requests.post(url, json=payload, timeout=5)
    data = res.json() if res.status_code == 200 else {}
    free_count = data.get("currentLotState", {}).get("freeSlots", "?")

    if direction == "in":
        print("\n" + "=" * 62)
        print("  📸 AI CAMERA OCR: XE VÀO BÃI ĐỖ (TIMESCALEDB)")
        print("=" * 62)
        print(f"  Biển số xe:  {plate} ({vehicle_name})")
        print(f"  Ô đỗ xe:     Ô {slot_num} -> ĐÃ CÓ XE (🔴)")
        print(f"  Barrier:     CỔNG VÀO MỞ 90 ĐỘ")
        print(f"  Chỗ trống:   Còn {free_count} ô")
        print(f"  Trạng thái:  Đã ghi vào TimescaleDB Hypertable & Web hiển thị!")
        print("=" * 62)
    else:
        print("\n" + "=" * 62)
        print("  📸 AI CAMERA OCR: XE RỜI BÃI & TỰ ĐỘNG TRỪ TIỀN VÍ (TIMESCALEDB)")
        print("=" * 62)
        print(f"  Biển số xe:  {plate} ({vehicle_name})")
        print(f"  Ô đỗ xe:     Ô {slot_num} -> ĐÃ GIẢI PHÓNG (🟢 TRỐNG)")
        print(f"  Phí gửi xe:  {fee:,.0f} ₫")
        print(f"  Barrier:     CỔNG RA MỞ 90 ĐỘ")
        print(f"  Chỗ trống:   Còn {free_count} ô")
        print(f"  Ví tài xế:   Tự động trừ {fee:,.0f} ₫ trong TimescaleDB!")
        print("=" * 62)

def fill_all():
    for i in range(1, 5):
        requests.put(f"{BACKEND_URL}/lots/{LOT_ID}/slots/{i}", json={"occupied": True}, timeout=3)
    print("\n=> ĐÃ LẤP ĐẦY TOÀN BỘ Ô ĐỖ (HẾT CHỖ: 0/4)")

def clear_all():
    for i in range(1, 5):
        requests.put(f"{BACKEND_URL}/lots/{LOT_ID}/slots/{i}", json={"occupied": False}, timeout=3)
    print("\n=> ĐÃ DỌN SẠCH TOÀN BỘ BÃI XE (TRỐNG CẢ 4/4 Ô)")

def manual_ocr_input():
    print("\n--- QUÉT BIỂN SỐ TÙY CHỌN (TEST BIỂN SỐ BẠN TỰ ĐĂNG KÝ) ---")
    plate = input("👉 Nhập biển số xe (VD: 29A-686.88): ").strip().upper()
    if not plate:
        print("Biển số không hợp lệ!")
        return
    
    dir_choice = input("👉 Chọn chiều xe (1: VÀO bãi / 2: RA bãi): ").strip()
    direction = "in" if dir_choice == "1" else "out"

    slot = 1
    fee = 15000
    if direction == "in":
        s_in = input("👉 Chọn ô đỗ (1-4, Enter mặc định ô 1): ").strip()
        if s_in in ["1", "2", "3", "4"]:
            slot = int(s_in)
    else:
        f_in = input("👉 Nhập phí gửi xe VNĐ (Enter mặc định 15000): ").strip()
        if f_in.isdigit():
            fee = int(f_in)

    vname = input("👉 Tên xe / Hãng xe (Enter mặc định 'Xe đăng ký mới'): ").strip()
    if not vname:
        vname = "Xe đăng ký mới"

    trigger_ocr(plate, direction, vname, slot, fee)

def print_menu():
    st = get_current_status()
    slots = st.get("slots", {})
    slot_strs = []
    for i in range(1, 5):
        occ = bool(slots.get(str(i), False))
        slot_strs.append(f"Ô{i}:{'🔴Đỗ' if occ else '🟢Trống'}")
    slots_display = " | ".join(slot_strs)
    free = st.get("freeSlots", "?")
    dist = st.get("distance", -1)

    print("\n" + "=" * 68)
    print(f"  SMART PARKING - BẢNG ĐIỀU KHIỂN (TIMESCALEDB BACKEND)")
    print(f"  Bãi xe: {LOT_ID.upper()} | Trống: {free}/4 chỗ | Khoảng cách: {dist}cm")
    print(f"  Trạng thái: {slots_display}")
    print("=" * 68)
    print("  --- QUÉT AI OCR (TỰ ĐỘNG MỞ CỔNG & TRỪ TIỀN VÍ) ---")
    print("   [v1] Xe 1 VÀO (30A-123.45 - VinFast VF8 An)   -> Đỗ Ô 1, Mở Cổng Vào")
    print("   [r1] Xe 1 RA  (30A-123.45 - VinFast VF8 An)   -> Trống Ô 1, Trừ 15.000₫")
    print("   [v2] Xe 2 VÀO (51G-456.78 - Honda CR-V Bình)  -> Đỗ Ô 2, Mở Cổng Vào")
    print("   [r2] Xe 2 RA  (51G-456.78 - Honda CR-V Bình)  -> Trống Ô 2, Trừ 20.000₫")
    print("   [v3] Xe 3 VÀO (30H-888.66 - Corolla Anh)      -> Đỗ Ô 3, Mở Cổng Vào")
    print("   [r3] Xe 3 RA  (30H-888.66 - Corolla Anh)      -> Trống Ô 3, Trừ 15.000₫")
    print("   [ocr] Quét biển số TÙY CHỌN (Gõ bất kỳ biển số nào)")
    print("  --- ĐIỀU KHIỂN THIẾT BỊ NGOẠI VI & Ô ĐỖ ---")
    print("   [1] Đổi trạng thái Ô 1     |  [2] Đổi trạng thái Ô 2")
    print("   [3] Đổi trạng thái Ô 3     |  [4] Đổi trạng thái Ô 4")
    print("   [in] Mở barrier CỔNG VÀO   |  [out] Mở barrier CỔNG RA")
    print("   [d1] Khoảng cách XA (45cm) |  [d2] Khoảng cách VỪA (18cm)")
    print("   [d3] SÁT TƯỜNG (7cm - CÒI KÊU CẢNH BÁO!)")
    print("   [c] Dọn sạch bãi (Trống 4/4) | [f] Lấp đầy bãi (Hết chỗ 0/4)")
    print("   [q] Thoát chương trình")
    print("=" * 68)

def main():
    while True:
        print_menu()
        cmd = input("👉 Nhập lệnh: ").strip().lower()

        if cmd == "q":
            print("\nĐã thoát.")
            break
        elif cmd == "v1":
            car = SAMPLE_CARS["1"]
            trigger_ocr(car["plate"], "in", car["name"], car["slot"], car["fee"])
        elif cmd == "r1":
            car = SAMPLE_CARS["1"]
            trigger_ocr(car["plate"], "out", car["name"], car["slot"], car["fee"])
        elif cmd == "v2":
            car = SAMPLE_CARS["2"]
            trigger_ocr(car["plate"], "in", car["name"], car["slot"], car["fee"])
        elif cmd == "r2":
            car = SAMPLE_CARS["2"]
            trigger_ocr(car["plate"], "out", car["name"], car["slot"], car["fee"])
        elif cmd == "v3":
            car = SAMPLE_CARS["3"]
            trigger_ocr(car["plate"], "in", car["name"], car["slot"], car["fee"])
        elif cmd == "r3":
            car = SAMPLE_CARS["3"]
            trigger_ocr(car["plate"], "out", car["name"], car["slot"], car["fee"])
        elif cmd == "ocr":
            manual_ocr_input()
        elif cmd in ["1", "2", "3", "4"]:
            toggle_slot(int(cmd))
        elif cmd == "in":
            set_gate("gateIn")
        elif cmd == "out":
            set_gate("gateOut")
        elif cmd == "d1":
            set_distance(45.0)
        elif cmd == "d2":
            set_distance(18.0)
        elif cmd == "d3":
            set_distance(7.0)
        elif cmd == "c":
            clear_all()
        elif cmd == "f":
            fill_all()
        else:
            print("⚠️ Lệnh không hợp lệ! Vui lòng xem bảng hướng dẫn trên.")
        
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã thoát bảng điều khiển.")

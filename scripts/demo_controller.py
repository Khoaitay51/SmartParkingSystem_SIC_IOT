#!/usr/bin/env python3
"""
=============================================================================
  SMART PARKING - BẢNG ĐIỀU KHIỂN THỰC TẾ (FIREBASE REALTIME CONTROLLER)
  Hệ thống mô phỏng bãi xe B7 Mỹ Đình:
  - Cho xe vào / xe ra 4 ô đỗ
  - Quét biển số AI Camera OCR tự động mở cổng và trừ tiền ví tài xế
  - Điều khiển mở barrier Cổng Vào / Cổng Ra
  - Thay đổi khoảng cách cảm biến siêu âm HC-SR04 kích hoạt còi Buzzer
=============================================================================
"""

import sys
import time
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

FIREBASE_URL = "https://smartparking-139b7-default-rtdb.asia-southeast1.firebasedatabase.app"
LOT_ID = "lot_mydinh"

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

def extract_slots(raw_slots):
    """
    Firebase RTDB tự động chuyển object có key số sang dạng list [None, slot1, slot2, slot3, slot4].
    Hàm này chuẩn hóa về dict {1: bool, 2: bool, 3: bool, 4: bool}.
    """
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

def get_current_status():
    url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.text != "null":
            data = res.json()
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"[LỖI] Không thể đọc Firebase: {e}")
    return {
        "slots": {1: False, 2: False, 3: False, 4: False},
        "freeSlots": 4,
        "totalSlots": 4,
        "distance": 25.0,
        "gates": {"in": "closed", "out": "closed"}
    }

def toggle_slot(slot_num):
    data = get_current_status()
    slots_dict = extract_slots(data.get("slots"))
    current_state = slots_dict.get(slot_num, False)
    new_state = not current_state

    # Cập nhật trực tiếp ô đỗ lên Firebase
    slot_url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/slots/{slot_num}.json"
    requests.put(slot_url, json=new_state, timeout=5)

    slots_dict[slot_num] = new_state
    free_count = sum(1 for v in slots_dict.values() if not v)

    # Cập nhật freeSlots và heartbeat
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/freeSlots.json", json=free_count, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=int(time.time() * 1000), timeout=5)

    action_text = "🚗 XE ĐÃ ĐỖ VÀO" if new_state else "🅿️ XE ĐÃ RỜI ĐI (TRỐNG)"
    print(f"\n=> ĐÃ CẬP NHẬT: Ô {slot_num} -> {action_text}! (Còn trống {free_count}/4 ô)")

def set_distance(dist):
    url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/distance.json"
    requests.put(url, json=dist, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=int(time.time() * 1000), timeout=5)
    alert = "🚨 (ĐỖ QUÁ SÁT - CÒI KÊU!)" if dist <= 10 else ""
    print(f"\n=> ĐÃ CẬP NHẬT: Khoảng cách xe = {dist} cm {alert}")

def set_gate(gate_name, state):
    url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/gates/{gate_name}.json"
    cmd_url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands/{'gateIn' if gate_name == 'in' else 'gateOut'}.json"
    requests.put(url, json=state, timeout=5)
    requests.put(cmd_url, json=state, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=int(time.time() * 1000), timeout=5)
    state_text = "MỞ 90 ĐỘ" if state == "open" else "ĐÓNG LẠI"
    print(f"\n=> CỔNG {gate_name.upper()} -> {state_text}!")

def trigger_ocr(plate, direction, vehicle_name="Xe cá nhân", slot_num=1, fee=15000):
    """
    Kích hoạt sự kiện quét biển số AI OCR:
    - Nếu Vào (in): Đánh dấu ô slot_num có xe, mở barrier Cổng Vào, gửi node OCR
    - Nếu Ra (out): Giải phóng ô slot_num (trống), mở barrier Cổng Ra, gửi node OCR kèm phí đỗ xe
    Web App sẽ tự động bắt sự kiện, hiển thị thông báo và trừ tiền ví tài xế!
    """
    ts = int(time.time() * 1000)
    data = get_current_status()
    slots_dict = extract_slots(data.get("slots"))

    if direction == "in":
        # Chiếm ô đỗ
        slots_dict[slot_num] = True
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/slots/{slot_num}.json", json=True, timeout=5)
        free_count = sum(1 for v in slots_dict.values() if not v)
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/freeSlots.json", json=free_count, timeout=5)

        # Mở cổng vào
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/gates/in.json", json="open", timeout=5)
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands/gateIn.json", json="open", timeout=5)

        # Gửi sự kiện OCR
        ocr_payload = {
            "plate": plate,
            "direction": "in",
            "timestamp": ts,
            "vehicleName": vehicle_name,
            "slot": slot_num,
            "fee": 0
        }
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/ocr.json", json=ocr_payload, timeout=5)
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=ts, timeout=5)

        print("\n" + "=" * 62)
        print("  📸 AI CAMERA OCR: XE VÀO BÃI ĐỖ")
        print("=" * 62)
        print(f"  Biển số xe:  {plate} ({vehicle_name})")
        print(f"  Ô đỗ xe:     Ô {slot_num} -> ĐÃ CÓ XE (🔴)")
        print(f"  Barrier:     CỔNG VÀO ĐANG MỞ (90 ĐỘ)")
        print(f"  Chỗ trống:   Còn {free_count}/4 ô")
        print(f"  Trạng thái:  Đã gửi lên Firebase -> Web hiển thị xe đang đỗ!")
        print("=" * 62)

    else: # out
        # Giải phóng ô đỗ
        slots_dict[slot_num] = False
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/slots/{slot_num}.json", json=False, timeout=5)
        free_count = sum(1 for v in slots_dict.values() if not v)
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/freeSlots.json", json=free_count, timeout=5)

        # Mở cổng ra
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/gates/out.json", json="open", timeout=5)
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/commands/gateOut.json", json="open", timeout=5)

        # Gửi sự kiện OCR kèm phí gửi xe
        ocr_payload = {
            "plate": plate,
            "direction": "out",
            "timestamp": ts,
            "vehicleName": vehicle_name,
            "slot": slot_num,
            "fee": fee
        }
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/ocr.json", json=ocr_payload, timeout=5)
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=ts, timeout=5)

        print("\n" + "=" * 62)
        print("  📸 AI CAMERA OCR: XE RỜI BÃI & TỰ ĐỘNG TRỪ TIỀN VÍ")
        print("=" * 62)
        print(f"  Biển số xe:  {plate} ({vehicle_name})")
        print(f"  Ô đỗ xe:     Ô {slot_num} -> ĐÃ GIẢI PHÓNG (🟢 TRỐNG)")
        print(f"  Phí gửi xe:  {fee:,.0f} ₫")
        print(f"  Barrier:     CỔNG RA ĐANG MỞ (90 ĐỘ)")
        print(f"  Chỗ trống:   Còn {free_count}/4 ô")
        print(f"  Ví tài xế:   Web tự động trừ {fee:,.0f} ₫ và tạo biên lai!")
        print("=" * 62)

def fill_all():
    for i in range(1, 5):
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/slots/{i}.json", json=True, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/freeSlots.json", json=0, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=int(time.time() * 1000), timeout=5)
    print("\n=> ĐÃ LẤP ĐẦY TOÀN BỘ 4 Ô ĐỖ (HẾT CHỖ: 0/4)")

def clear_all():
    for i in range(1, 5):
        requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/slots/{i}.json", json=False, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/freeSlots.json", json=4, timeout=5)
    requests.put(f"{FIREBASE_URL}/parking/lots/{LOT_ID}/status/lastHeartbeat.json", json=int(time.time() * 1000), timeout=5)
    print("\n=> ĐÃ DỌN SẠCH TOÀN BỘ BÃI XE (TRỐNG CẢ 4/4 Ô)")

def manual_ocr_input():
    print("\n--- QUÉT BIỂN SỐ TÙY CHỌN (TEST BIỂN SỐ BẠN TỰ ĐĂNG KÝ) ---")
    plate = input("👉 Nhập biển số xe (VD: 29A-686.88): ").strip().upper()
    if not plate:
        print("Biển số không hợp lệ!")
        return
    
    dir_choice = input("👉 Chọn chiều xe (1: VÀO bãi / 2: RA bãi): ").strip()
    direction = "in" if dir_choice == "1" else "out"

    slot_str = input("👉 Chọn số ô đỗ (1, 2, 3 hoặc 4) [Mặc định 1]: ").strip()
    slot_num = int(slot_str) if slot_str in ["1", "2", "3", "4"] else 1

    fee = 15000
    if direction == "out":
        fee_str = input("👉 Nhập số tiền gửi xe (VNĐ) [Mặc định 15000]: ").strip()
        try:
            fee = int(fee_str) if fee_str else 15000
        except ValueError:
            fee = 15000

    trigger_ocr(plate, direction, vehicle_name="Xe tùy chọn", slot_num=slot_num, fee=fee)

def print_menu():
    data = get_current_status()
    slots_dict = extract_slots(data.get("slots"))
    dist = data.get("distance", -1)
    gates = data.get("gates", {})
    if not isinstance(gates, dict):
        gates = {"in": "closed", "out": "closed"}
    free = data.get("freeSlots", sum(1 for v in slots_dict.values() if not v))

    print("\n" + "=" * 64)
    print("       SMART PARKING - BẢNG ĐIỀU KHIỂN BÃI XE THỰC TẾ")
    print("=" * 64)
    print(f"  TRẠNG THÁI HIỆN TẠI (FIREBASE): Còn trống {free}/4 chỗ")
    for i in range(1, 5):
        is_occ = slots_dict[i]
        status = "🔴 CÓ XE ĐỖ" if is_occ else "🟢 ĐANG TRỐNG"
        action = "Bấm để CHO XE RA" if is_occ else "Bấm để XE VÀO"
        print(f"    [{i}] Ô {i}: {status}  ({action})")
    print("  --------------------------------------------------------------")
    print(f"    Khoảng cách siêu âm (HC-SR04): {dist} cm")
    print(f"    Cổng Vào: {str(gates.get('in', 'closed')).upper()} | Cổng Ra: {str(gates.get('out', 'closed')).upper()}")
    print("  --------------------------------------------------------------")
    print("  📷 QUÉT BIỂN SỐ AI OCR (TỰ ĐỘNG MỞ CỔNG & TÍNH TIỀN):")
    print("    [v1] Xe 1 VÀO: 30A-123.45 (VinFast VF8 - An)  -> Đỗ Ô 1, mở Cổng Vào")
    print("    [r1] Xe 1 RA:  30A-123.45                     -> Trừ 15.000₫, mở Cổng Ra")
    print("    [v2] Xe 2 VÀO: 51G-456.78 (Honda CR-V - Bình) -> Đỗ Ô 2, mở Cổng Vào")
    print("    [r2] Xe 2 RA:  51G-456.78                     -> Trừ 20.000₫, mở Cổng Ra")
    print("    [v3] Xe 3 VÀO: 30H-888.66 (Toyota Cross - Anh)-> Đỗ Ô 3, mở Cổng Vào")
    print("    [r3] Xe 3 RA:  30H-888.66                     -> Trừ 15.000₫, mở Cổng Ra")
    print("    [ocr] Quét biển số bất kỳ (Manual OCR - Test biển bạn tự đăng ký)")
    print("  --------------------------------------------------------------")
    print("  ⚡ CÁC PHÍM ĐIỀU KHIỂN THỦ CÔNG:")
    print("    [1-4]   Bấm số 1, 2, 3 hoặc 4 để Cho xe vào / xe ra ô đó")
    print("    [in]    Mở barrier Cổng Vào")
    print("    [out]   Mở barrier Cổng Ra")
    print("    [d1]    Đổi khoảng cách: Xa (45 cm)")
    print("    [d2]    Đổi khoảng cách: Vừa (18 cm)")
    print("    [d3]    Đổi khoảng cách: Quá sát tường (7 cm - Kích hoạt CÒI KÊU!)")
    print("    [c]     Dọn sạch bãi xe (Trống 4/4 ô)")
    print("    [f]     Lấp đầy bãi xe (Có xe cả 4/4 ô - HẾT CHỖ)")
    print("    [q]     Thoát")
    print("=" * 64)

def main():
    while True:
        print_menu()
        try:
            choice = input("👉 Nhập lệnh điều khiển: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát.")
            break

        if choice == "q":
            print("Tạm biệt!")
            break
        elif choice in ["1", "2", "3", "4"]:
            toggle_slot(int(choice))
        elif choice == "v1":
            car = SAMPLE_CARS["1"]
            trigger_ocr(car["plate"], "in", vehicle_name=car["name"], slot_num=car["slot"])
        elif choice == "r1":
            car = SAMPLE_CARS["1"]
            trigger_ocr(car["plate"], "out", vehicle_name=car["name"], slot_num=car["slot"], fee=car["fee"])
        elif choice == "v2":
            car = SAMPLE_CARS["2"]
            trigger_ocr(car["plate"], "in", vehicle_name=car["name"], slot_num=car["slot"])
        elif choice == "r2":
            car = SAMPLE_CARS["2"]
            trigger_ocr(car["plate"], "out", vehicle_name=car["name"], slot_num=car["slot"], fee=car["fee"])
        elif choice == "v3":
            car = SAMPLE_CARS["3"]
            trigger_ocr(car["plate"], "in", vehicle_name=car["name"], slot_num=car["slot"])
        elif choice == "r3":
            car = SAMPLE_CARS["3"]
            trigger_ocr(car["plate"], "out", vehicle_name=car["name"], slot_num=car["slot"], fee=car["fee"])
        elif choice == "ocr":
            manual_ocr_input()
        elif choice == "in":
            set_gate("in", "open")
        elif choice == "out":
            set_gate("out", "open")
        elif choice == "d1":
            set_distance(45.0)
        elif choice == "d2":
            set_distance(18.0)
        elif choice == "d3":
            set_distance(7.0)
        elif choice == "c":
            clear_all()
        elif choice == "f":
            fill_all()
        else:
            print("Lệnh không hợp lệ, vui lòng thử lại!")
        
        time.sleep(0.3)

if __name__ == "__main__":
    main()

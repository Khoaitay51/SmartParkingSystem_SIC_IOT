import sys
import requests
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

FIREBASE_URL = "https://smartparking-139b7-default-rtdb.asia-southeast1.firebasedatabase.app"
LOT_ID = "lot_mydinh"

def test_connection():
    print(f"[TEST] Đang kết nối tới: {FIREBASE_URL}...")
    url = f"{FIREBASE_URL}/parking/lots/{LOT_ID}/health_check.json"
    payload = {"status": "ok", "testedAt": int(time.time() * 1000)}

    try:
        res = requests.put(url, json=payload, timeout=8)
        if res.status_code == 200:
            print("✅ KẾT NỐI FIREBASE THÀNH CÔNG! (HTTP 200 OK)")
            print(f"Phản hồi: {res.text}")
            return True
        else:
            print(f"❌ KẾT NỐI THẤT BẠI: Mã HTTP {res.status_code}")
            print(f"Lý do: {res.text}")
            return False
    except Exception as e:
        print(f"❌ LỖI KẾT NỐI: {e}")
        return False

if __name__ == "__main__":
    test_connection()

#!/usr/bin/env python3
"""
Kiểm tra kết nối và độ sẵn sàng của TimescaleDB Backend
"""

import sys
import requests
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_URL = "http://localhost:3000/api"

def test_connection():
    print(f"[TEST] Đang kết nối tới Backend TimescaleDB tại: {BACKEND_URL}...")
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if res.status_code == 200:
            data = res.json()
            print("✅ KẾT NỐI BACKEND THÀNH CÔNG! (HTTP 200 OK)")
            print(f"👉 Trạng thái Database: {data.get('database')}")
            print(f"👉 Danh sách bãi đỗ xe quản lý: {data.get('managedLots')}")
            print(f"👉 Thời gian hoạt động: {data.get('uptimeSeconds')} giây")

            # Test lấy danh sách bãi xe
            lots_res = requests.get(f"{BACKEND_URL}/lots", timeout=5)
            if lots_res.status_code == 200:
                lots = lots_res.json()
                print(f"✅ Đọc thành công {len(lots)} bãi đỗ xe:")
                for l in lots:
                    print(f"   • {l.get('name')} (ID: {l.get('id')}) - Tổng {l.get('totalSlots')} chỗ, trống {l.get('freeSlots')} chỗ")
            return True
        else:
            print(f"❌ KẾT NỐI THẤT BẠI: Mã HTTP {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ LỖI KẾT NỐI: Không tìm thấy máy chủ backend tại {BACKEND_URL}")
        print(f"Chi tiết: {e}")
        print("💡 Gợi ý: Hãy khởi động Docker bằng lệnh 'docker-compose up -d' hoặc chạy 'npm start' trong thư mục backend!")
        return False

if __name__ == "__main__":
    test_connection()

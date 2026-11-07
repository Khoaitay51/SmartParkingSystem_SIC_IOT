-- =============================================================================
-- SMART PARKING SYSTEM - TIMESCALEDB SCHEMA
-- Multi-Tenant, Multi-Lot Scale Architecture
-- =============================================================================

-- 1. Kích hoạt TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 2. Bảng Người dùng (Tài xế & Chủ bãi)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'driver', -- 'driver' | 'owner' | 'admin'
    balance NUMERIC(12, 2) NOT NULL DEFAULT 200000.00,
    avatar TEXT,
    default_plate VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Bảng Phương tiện (Xe ô tô / Xe máy)
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    owner_phone VARCHAR(20) REFERENCES users(phone) ON DELETE CASCADE,
    plate VARCHAR(20) NOT NULL UNIQUE,
    type VARCHAR(50) DEFAULT 'Ô tô con',
    brand VARCHAR(100),
    color VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Bảng BÃI ĐỖ XE (Hỗ trợ SCALE VÔ HẠN BÃI ĐỖ XE - MULTI-LOT)
CREATE TABLE IF NOT EXISTS parking_lots (
    id VARCHAR(50) PRIMARY KEY, -- Mã định danh bãi xe (VD: lot_mydinh, lot_caugiay, lot_hoankiem)
    owner_id VARCHAR(50) REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    address TEXT NOT NULL,
    district VARCHAR(100),
    city VARCHAR(100) DEFAULT 'Hà Nội',
    lat NUMERIC(10, 6) DEFAULT 21.0285,
    lng NUMERIC(10, 6) DEFAULT 105.7725,
    total_slots INT NOT NULL DEFAULT 4,
    price_hour NUMERIC(10, 2) NOT NULL DEFAULT 5000.00,
    price_day NUMERIC(10, 2) NOT NULL DEFAULT 60000.00,
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'maintenance', 'closed'
    open_time VARCHAR(20) DEFAULT '00:00',
    close_time VARCHAR(20) DEFAULT '24:00',
    is_24h BOOLEAN DEFAULT TRUE,
    features TEXT[] DEFAULT ARRAY['Camera AI OCR', 'Barrier Tự Động', 'Cảm biến IR Realtime', 'ESP32 IoT'],
    api_key VARCHAR(100) DEFAULT 'sec_iot_parkiq_default',
    image TEXT DEFAULT 'https://images.unsplash.com/photo-1590674899484-d5640e854abe?w=400&h=240&fit=crop&auto=format',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Bảng trạng thái Ô đỗ theo từng Bãi xe
CREATE TABLE IF NOT EXISTS parking_slots (
    lot_id VARCHAR(50) REFERENCES parking_lots(id) ON DELETE CASCADE,
    slot_number INT NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (lot_id, slot_number)
);

-- 6. Bảng Hàng đợi Lệnh Barrier (Cổng vào / Cổng ra) cho từng Bãi xe
CREATE TABLE IF NOT EXISTS gate_commands (
    lot_id VARCHAR(50) PRIMARY KEY REFERENCES parking_lots(id) ON DELETE CASCADE,
    gate_in VARCHAR(20) DEFAULT 'idle',   -- 'open' | 'idle'
    gate_out VARCHAR(20) DEFAULT 'idle',  -- 'open' | 'idle'
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Bảng Phiên Gửi Xe (Parking Sessions)
CREATE TABLE IF NOT EXISTS parking_sessions (
    id SERIAL PRIMARY KEY,
    lot_id VARCHAR(50) REFERENCES parking_lots(id),
    slot_number INT,
    plate VARCHAR(20) NOT NULL,
    user_id VARCHAR(50) REFERENCES users(id),
    time_in TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    time_out TIMESTAMPTZ,
    fee NUMERIC(10, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' -- 'active', 'completed', 'cancelled'
);

-- 8. Bảng Lịch sử Giao dịch Ví & Doanh thu
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(id),
    lot_id VARCHAR(50) REFERENCES parking_lots(id),
    type VARCHAR(20) NOT NULL, -- 'parking', 'topup', 'withdraw', 'income'
    amount NUMERIC(12, 2) NOT NULL,
    plate VARCHAR(20),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TIMESCALEDB HYPERTABLES (TỐI ƯU HÓA CHUỖI THỜI GIAN / TIME-SERIES BIG DATA)
-- =============================================================================

-- 9. Hypertable: Dữ liệu Telemetry Cảm biến IoT (Free slots, IR sensor states, Ultrasonic distance)
CREATE TABLE IF NOT EXISTS lot_telemetry (
    time TIMESTAMPTZ NOT NULL,
    lot_id VARCHAR(50) NOT NULL,
    free_slots INT NOT NULL,
    total_slots INT NOT NULL,
    distance NUMERIC(6, 2) DEFAULT -1,
    slots JSONB NOT NULL DEFAULT '{}',
    gates JSONB NOT NULL DEFAULT '{"in": "closed", "out": "closed"}'
);

SELECT create_hypertable('lot_telemetry', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_telemetry_lot_time ON lot_telemetry (lot_id, time DESC);

-- 10. Hypertable: Sự kiện Quét Biển Số AI OCR (Lịch sử ra / vào)
CREATE TABLE IF NOT EXISTS ocr_events (
    time TIMESTAMPTZ NOT NULL,
    lot_id VARCHAR(50) NOT NULL,
    plate VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- 'in' | 'out'
    slot_number INT,
    vehicle_name VARCHAR(100),
    fee NUMERIC(10, 2) DEFAULT 0,
    user_id VARCHAR(50)
);

SELECT create_hypertable('ocr_events', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_ocr_lot_time ON ocr_events (lot_id, time DESC);

-- =============================================================================
-- DỮ LIỆU MẪU BAN ĐẦU (SEED DATA)
-- =============================================================================

-- Tài khoản mẫu
INSERT INTO users (id, name, phone, email, role, balance, avatar, default_plate)
VALUES
    ('user_1', 'Nguyễn Văn An', '0912345678', 'an.nguyen@parkiq.vn', 'driver', 350000.00, 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&auto=format', '30A-123.45'),
    ('user_2', 'Trần Thị Bình', '0987654321', 'binh.tran@parkiq.vn', 'driver', 500000.00, 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&h=80&fit=crop&auto=format', '51G-456.78'),
    ('user_3', 'Phạm Tuấn Anh', '0933445566', 'anh.pham@parkiq.vn', 'driver', 200000.00, 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=80&h=80&fit=crop&auto=format', '30H-888.66'),
    ('user_4', 'Lê Hoàng Nam (Chủ bãi)', '0909999999', 'nam.le@parkiq.vn', 'owner', 1500000.00, 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&h=80&fit=crop&auto=format', '29B-999.88')
ON CONFLICT (id) DO UPDATE SET balance = EXCLUDED.balance, name = EXCLUDED.name;

-- Phương tiện mẫu
INSERT INTO vehicles (owner_phone, plate, type, brand, color, is_primary)
VALUES
    ('0912345678', '30A-123.45', 'Ô tô con', 'VinFast VF8', 'Trắng', TRUE),
    ('0912345678', '29A-888.99', 'Xe máy', 'Honda SH 150i', 'Đen', FALSE),
    ('0987654321', '51G-456.78', 'Ô tô con', 'Honda CR-V', 'Đen', TRUE),
    ('0987654321', '59F-333.22', 'Xe máy', 'Yamaha Grande', 'Trắng', FALSE),
    ('0933445566', '30H-888.66', 'Ô tô con', 'Toyota Corolla Cross', 'Bạc', TRUE),
    ('0909999999', '29B-999.88', 'Ô tô con', 'Mazda CX-5', 'Đỏ', TRUE)
ON CONFLICT (plate) DO NOTHING;

-- Danh sách bãi xe mẫu (Hỗ trợ nhiều bãi đỗ xe)
INSERT INTO parking_lots (id, owner_id, name, address, district, city, lat, lng, total_slots, price_hour, price_day, status, is_24h, api_key)
VALUES
    ('lot_mydinh', 'user_4', 'Bãi xe B7 Mỹ Đình', 'Phạm Hùng, Mỹ Đình 2, Nam Từ Liêm, Hà Nội', 'Nam Từ Liêm', 'Hà Nội', 21.0285, 105.7725, 4, 5000.00, 60000.00, 'open', TRUE, 'sec_iot_mydinh_key'),
    ('lot_caugiay', 'user_4', 'Bãi đỗ xe Cầu Giấy Smart', 'Duy Tân, Dịch Vọng Hậu, Cầu Giấy, Hà Nội', 'Cầu Giấy', 'Hà Nội', 21.0315, 105.7835, 8, 10000.00, 80000.00, 'open', TRUE, 'sec_iot_caugiay_key'),
    ('lot_hoankiem', 'user_4', 'Bãi đỗ xe Tràng Tiền Plaza', 'Hai Bà Trưng, Tràng Tiền, Hoàn Kiếm, Hà Nội', 'Hoàn Kiếm', 'Hà Nội', 21.0245, 105.8525, 12, 20000.00, 150000.00, 'open', TRUE, 'sec_iot_hoankiem_key')
ON CONFLICT (id) DO NOTHING;

-- Khởi tạo các ô đỗ cho từng bãi xe
INSERT INTO parking_slots (lot_id, slot_number, is_occupied)
VALUES
    ('lot_mydinh', 1, FALSE),
    ('lot_mydinh', 2, FALSE),
    ('lot_mydinh', 3, FALSE),
    ('lot_mydinh', 4, FALSE),
    ('lot_caugiay', 1, FALSE),
    ('lot_caugiay', 2, TRUE),
    ('lot_caugiay', 3, FALSE),
    ('lot_caugiay', 4, FALSE),
    ('lot_caugiay', 5, FALSE),
    ('lot_caugiay', 6, TRUE),
    ('lot_caugiay', 7, FALSE),
    ('lot_caugiay', 8, FALSE)
ON CONFLICT (lot_id, slot_number) DO NOTHING;

-- Khởi tạo hàng đợi lệnh barrier cho các bãi
INSERT INTO gate_commands (lot_id, gate_in, gate_out)
VALUES
    ('lot_mydinh', 'idle', 'idle'),
    ('lot_caugiay', 'idle', 'idle'),
    ('lot_hoankiem', 'idle', 'idle')
ON CONFLICT (lot_id) DO NOTHING;

-- Khởi tạo một số telemetry mẫu ban đầu
INSERT INTO lot_telemetry (time, lot_id, free_slots, total_slots, distance, slots, gates)
VALUES
    (NOW(), 'lot_mydinh', 4, 4, 25.0, '{"1": false, "2": false, "3": false, "4": false}'::jsonb, '{"in": "closed", "out": "closed"}'::jsonb),
    (NOW(), 'lot_caugiay', 6, 8, 30.0, '{"1": false, "2": true, "3": false, "4": false, "5": false, "6": true, "7": false, "8": false}'::jsonb, '{"in": "closed", "out": "closed"}'::jsonb);

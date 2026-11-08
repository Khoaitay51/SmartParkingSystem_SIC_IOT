import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { pool, initDb, isDbConnected } from "./db.js";
import { connectParkNodes, isLotId } from "./park-node-mqtt.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

/* =============================================================================
   IN-MEMORY CACHE (TỐC ĐỘ CAO CHO ESP32 & FALLBACK KHI DB KHỞI ĐỘNG)
   ============================================================================= */
const lotsState = Object.assign(Object.create(null), {
  lot_mydinh: {
    lotId: "lot_mydinh",
    lotName: "B7 Mỹ Đình",
    totalSlots: 4,
    freeSlots: 0,
    distance: -1,
    lastHeartbeat: 0,
    slots: {},
    gates: { in: "closed", out: "closed" },
  },
  lot_caugiay: {
    lotId: "lot_caugiay",
    lotName: "Bãi đỗ xe Cầu Giấy Smart",
    totalSlots: 8,
    freeSlots: 0,
    distance: -1,
    lastHeartbeat: 0,
    slots: {},
    gates: { in: "closed", out: "closed" },
  },
});

const latestOcrEvents = Object.create(null);
const pendingOcrWrites = new Set();
const slotReadings = new Map();
const gateReports = new Map();
const parkNodes = connectParkNodes({
  url: process.env.MQTT_URL || "mqtt://127.0.0.1:1883",
  onSlot(lotId, slot, data) {
    let slots = slotReadings.get(lotId);
    if (!slots) {
      slots = new Map();
      slotReadings.set(lotId, slots);
    }
    slots.set(slot, data);
    const entries = [...slots].filter(([index, reading]) =>
      index <= data.totalSlots && reading.totalSlots === data.totalSlots);
    const validDistances = entries.flatMap(([, { distanceCm }]) => distanceCm === null ? [] : [distanceCm]);
    updateLotStatus(lotId, {
      totalSlots: data.totalSlots,
      slots: Object.fromEntries(entries.map(([index, { occupied }]) => [index, occupied])),
      freeSlots: entries.filter(([, { occupied }]) => occupied === false).length,
      distance: validDistances.length ? Math.min(...validDistances) : -1,
    }, true);
  },
  onGate(lotId, gate, { state, remoteEnabled }) {
    gateReports.set(`${lotId}/${gate}`, { remoteEnabled, seenAt: Date.now() });
    updateLotStatus(lotId, { gates: { [gate]: state } });
  },
  onOcr(lotId, data) {
    void recordConfirmedOcr({ lotId, ...data, fee: 0, slot: null, vehicleName: "Phương tiện" });
  },
});

async function requestGateOpen(lotId, gate) {
  const report = gateReports.get(`${lotId}/${gate}`);
  if (!parkNodes.isConnected() || !report?.remoteEnabled || Date.now() - report.seenAt > 5000) return false;
  try {
    await parkNodes.openGate(lotId, gate);
    return true;
  } catch (error) {
    console.error("[MQTT] Không gửi được lệnh mở cổng:", error.message);
    return false;
  }
}

function liveLotSummary(state) {
  return {
    id: state.lotId,
    name: state.lotName,
    address: "",
    totalSlots: state.totalSlots,
    freeSlots: state.freeSlots,
    status: "open",
  };
}

/* =============================================================================
   HEALTH CHECK & ROOT
   ============================================================================= */
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    mqtt: parkNodes.isConnected() ? "connected" : "disconnected",
    database: isDbConnected() ? "timescaledb_connected" : "in_memory_fallback",
    timestamp: new Date().toISOString(),
    uptimeSeconds: Math.floor(process.uptime()),
    managedLots: Object.keys(lotsState),
  });
});

/* =============================================================================
   DANH SÁCH & ĐĂNG KÝ BÃI ĐỖ XE (MULTI-LOT ARCHITECTURE)
   ============================================================================= */
// Lấy toàn bộ danh sách bãi đỗ xe (có kèm trạng thái realtime)
app.get("/api/lots", async (req, res) => {
  try {
    if (isDbConnected()) {
      const dbResult = await pool.query(
        "SELECT * FROM parking_lots ORDER BY created_at DESC"
      );
      const lots = dbResult.rows.map((row) => {
        const live = lotsState[row.id] || {
          freeSlots: 0,
          distance: -1,
          slots: {},
          gates: { in: "closed", out: "closed" },
        };
        return {
          id: row.id,
          name: row.name,
          address: row.address,
          district: row.district,
          city: row.city,
          lat: parseFloat(row.lat),
          lng: parseFloat(row.lng),
          totalSlots: row.total_slots,
          freeSlots: live.freeSlots,
          priceHour: parseFloat(row.price_hour),
          priceDay: parseFloat(row.price_day),
          status: row.status,
          openTime: row.open_time,
          closeTime: row.close_time,
          is24h: row.is_24h,
          features: row.features,
          image: row.image,
          currentDistance: live.distance,
        };
      });
      const registered = new Set(lots.map(({ id }) => id));
      return res.json([
        ...lots,
        ...Object.values(lotsState)
          .filter((state) => state.lastHeartbeat && !registered.has(state.lotId))
          .map(liveLotSummary),
      ]);
    }
  } catch (err) {
    console.error("Lỗi đọc danh sách bãi xe từ DB:", err);
  }

  // Fallback từ memory
  const fallbackLots = Object.values(lotsState).map(liveLotSummary);
  res.json(fallbackLots);
});

// ĐĂNG KÝ BÃI XE MỚI (CHỦ BÃI THÊM BÃI ĐỖ - SCALE NHIỀU BÃI)
app.post("/api/lots", async (req, res) => {
  try {
    const {
      id,
      name,
      address,
      district = "Hà Nội",
      city = "Hà Nội",
      lat = 21.0285,
      lng = 105.7725,
      totalSlots = 4,
      priceHour = 5000,
      priceDay = 60000,
      ownerId = "user_4",
      features = ["Camera AI OCR", "Barrier Tự Động", "Cảm Biến Siêu Âm", "IoT ESP32"],
    } = req.body;

    if (!name || !address) {
      return res.status(400).json({ error: "Tên và địa chỉ bãi xe không được để trống" });
    }

    const lotId = id || `lot_${Date.now().toString(36)}`;
    const slotCount = Number(totalSlots);
    if (!isLotId(lotId) || !Number.isInteger(slotCount) || slotCount < 1 || slotCount > 10) {
      return res.status(400).json({ error: "Mã bãi hoặc số ô đỗ không hợp lệ" });
    }

    // 1. Lưu vào Database nếu có kết nối
    if (isDbConnected()) {
      await pool.query(
        `INSERT INTO parking_lots (id, owner_id, name, address, district, city, lat, lng, total_slots, price_hour, price_day, features)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
         ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, total_slots = EXCLUDED.total_slots`,
        [lotId, ownerId, name, address, district, city, lat, lng, slotCount, priceHour, priceDay, features]
      );

      // Tạo các slot tương ứng
      for (let s = 1; s <= slotCount; s++) {
        await pool.query(
          `INSERT INTO parking_slots (lot_id, slot_number, is_occupied)
           VALUES ($1, $2, FALSE)
           ON CONFLICT (lot_id, slot_number) DO NOTHING`,
          [lotId, s]
        );
      }

    }

    // 2. Cập nhật In-memory state
    const existing = lotsState[lotId];
    lotsState[lotId] = existing?.lastHeartbeat ? { ...existing, lotName: name } : {
      lotId,
      lotName: name,
      totalSlots: slotCount,
      freeSlots: 0,
      distance: -1,
      lastHeartbeat: 0,
      slots: {},
      gates: { in: "closed", out: "closed" },
    };

    console.log(`🎉 [MULTI-LOT] Đã đăng ký thành công bãi xe mới: ${name} (ID: ${lotId}, ${slotCount} ô đỗ)`);
    res.status(201).json({
      success: true,
      message: "Đăng ký bãi xe thành công!",
      lot: lotsState[lotId],
    });
  } catch (err) {
    console.error("Lỗi đăng ký bãi xe:", err);
    res.status(500).json({ error: "Lỗi đăng ký bãi xe: " + err.message });
  }
});

// Lấy thông tin 1 bãi xe
app.get("/api/lots/:lotId", async (req, res) => {
  const { lotId } = req.params;
  const live = lotsState[lotId];
  if (!live) {
    return res.status(404).json({ error: "Không tìm thấy bãi xe" });
  }
  res.json(live);
});

/* =============================================================================
   REALTIME STATUS & TELEMETRY (ESP32 & WEB SYNC)
   ============================================================================= */
// Lấy trạng thái hiện tại (giống /status.json trên Firebase)
app.get("/api/lots/:lotId/status", (req, res) => {
  const { lotId } = req.params;
  const status = lotsState[lotId];
  if (!status) {
    return res.status(404).json({ error: "Bãi xe không tồn tại" });
  }
  res.json(status);
});

function updateLotStatus(lotId, payload, replaceSlots = false) {
  const current = lotsState[lotId] ?? {
    lotId,
    lotName: lotId,
    totalSlots: 0,
    freeSlots: 0,
    distance: -1,
    slots: {},
    gates: { in: "closed", out: "closed" },
  };
  const updated = lotsState[lotId] = {
    ...current,
    lotName: payload.lotName || current.lotName,
    totalSlots: payload.totalSlots ?? current.totalSlots,
    freeSlots: payload.freeSlots ?? current.freeSlots,
    distance: payload.distance ?? current.distance,
    slots: replaceSlots ? payload.slots : { ...current.slots, ...payload.slots },
    gates: { ...current.gates, ...payload.gates },
    lastHeartbeat: Date.now(),
  };

  // Lưu vào Hypertable lot_telemetry của TimescaleDB (Async không chặn)
  if (isDbConnected()) {
    pool.query(
      `INSERT INTO lot_telemetry (time, lot_id, free_slots, total_slots, distance, slots, gates)
       VALUES (NOW(), $1, $2, $3, $4, $5, $6)`,
      [
        lotId,
        updated.freeSlots,
        updated.totalSlots,
        updated.distance,
        JSON.stringify(updated.slots),
        JSON.stringify(updated.gates),
      ]
    ).catch((err) => console.error("Lỗi ghi TimescaleDB telemetry:", err.message));
  }

  return updated;
}

// REST telemetry remains available to existing test tools.
function handleStatusUpdate(req, res) {
  if (!isLotId(req.params.lotId) || !req.body || typeof req.body !== "object" || Array.isArray(req.body)) {
    return res.status(400).json({ error: "Telemetry không hợp lệ" });
  }
  res.json({ success: true, data: updateLotStatus(req.params.lotId, req.body) });
}

app.post("/api/lots/:lotId/status", handleStatusUpdate);
app.put("/api/lots/:lotId/status", handleStatusUpdate);

app.post("/api/lots/:lotId/commands", async (req, res) => {
  const { lotId } = req.params;
  const { gate, action = "open" } = req.body ?? {};
  if (!isLotId(lotId) || (gate !== "gateIn" && gate !== "gateOut") || action !== "open") {
    return res.status(400).json({ error: "Lệnh mở cổng không hợp lệ" });
  }
  if (!await requestGateOpen(lotId, gate === "gateIn" ? "in" : "out")) {
    return res.status(503).json({ error: "Park Node chưa sẵn sàng nhận lệnh mở từ xa" });
  }
  return res.status(202).json({ success: true, published: true });
});

/* =============================================================================
   AI CAMERA OCR & TRỪ TIỀN VÍ TỰ ĐỘNG
   ============================================================================= */
async function recordConfirmedOcr(event) {
  // Pi publishes its own gate command. A confirmation is a record, not a second command.
  const previous = latestOcrEvents[event.lotId];
  if (!previous || event.timestamp > previous.timestamp ||
      (event.timestamp === previous.timestamp &&
       (event.plate !== previous.plate || event.direction !== previous.direction))) {
    latestOcrEvents[event.lotId] = event;
  }

  if (!isDbConnected()) return;
  const key = JSON.stringify([event.lotId, event.direction, event.plate, event.timestamp]);
  if (pendingOcrWrites.has(key)) return;
  pendingOcrWrites.add(key);
  try {
    await insertOcrEvent(event, true);
  } catch (error) {
    console.error("[MQTT] Không lưu được sự kiện OCR:", error.message);
  } finally {
    pendingOcrWrites.delete(key);
  }
}

function insertOcrEvent({ lotId, plate, direction, slot, vehicleName, fee, timestamp }, deduplicate = false) {
  return pool.query(
    `INSERT INTO ocr_events (time, lot_id, plate, direction, slot_number, vehicle_name, fee)
     SELECT $1::timestamptz, $2, $3, $4, $5::integer, $6, $7::numeric
     WHERE NOT $8::boolean OR NOT EXISTS (
       SELECT 1 FROM ocr_events
       WHERE time = $1::timestamptz AND lot_id = $2 AND plate = $3 AND direction = $4
     )`,
    [new Date(timestamp), lotId, plate, direction, slot, vehicleName, fee, deduplicate]
  );
}

app.post("/api/lots/:lotId/ocr", async (req, res) => {
  const { lotId } = req.params;
  const {
    plate,
    direction = "in",
    fee = 15000,
    slot = 1,
    vehicleName = "Phương tiện",
  } = req.body;

  if (!isLotId(lotId) || typeof plate !== "string" || !plate.trim() || (direction !== "in" && direction !== "out")) {
    return res.status(400).json({ error: "Mã bãi, biển số hoặc hướng di chuyển không hợp lệ" });
  }

  const ocrEvent = {
    lotId,
    plate,
    direction,
    fee: Number(fee),
    slot: Number(slot),
    vehicleName,
    timestamp: Date.now(),
  };

  latestOcrEvents[lotId] = ocrEvent;

  const gateCommandPublished = await requestGateOpen(lotId, direction);

  // Ghi vào TimescaleDB Hypertable ocr_events & trừ tiền ví nếu ra bãi
  if (isDbConnected()) {
    try {
      // 1. Ghi Hypertable
      await insertOcrEvent(ocrEvent);

      // 2. Tìm chủ xe dựa vào biển số
      const vehicleRes = await pool.query(
        `SELECT v.*, u.id as user_id, u.balance FROM vehicles v
         JOIN users u ON v.owner_phone = u.phone
         WHERE v.plate = $1 LIMIT 1`,
        [plate]
      );

      if (vehicleRes.rows.length > 0 && direction === "out" && fee > 0) {
        const user = vehicleRes.rows[0];
        const newBalance = Math.max(0, parseFloat(user.balance) - fee);

        // Trừ tiền
        await pool.query("UPDATE users SET balance = $1 WHERE id = $2", [newBalance, user.user_id]);

        // Tạo transaction
        await pool.query(
          `INSERT INTO transactions (user_id, lot_id, type, amount, plate, description)
           VALUES ($1, $2, 'parking', $3, $4, $5)`,
          [user.user_id, lotId, -fee, plate, `Thanh toán gửi xe tại ${lotsState[lotId]?.lotName || lotId}`]
        );
        console.log(`💳 [BILLING] Đã trừ ${fee.toLocaleString()}₫ từ ví người dùng ${user.user_id} (${plate})`);
      }
    } catch (dbErr) {
      console.error("Lỗi ghi OCR vào TimescaleDB:", dbErr.message);
    }
  }

  console.log(`📷 [AI OCR] Biển số: ${plate} | Hướng: ${direction.toUpperCase()} | Bãi: ${lotId} | Phí: ${fee}₫`);
  res.json({ success: true, event: ocrEvent, gateCommandPublished, currentLotState: lotsState[lotId] });
});

// Lấy sự kiện OCR gần nhất
app.get("/api/lots/:lotId/ocr", (req, res) => {
  const { lotId } = req.params;
  res.json(latestOcrEvents[lotId] || null);
});

/* =============================================================================
   MANUAL CONTROLS (TỪ WEB UI - CHO XE VÀO/RA, THAY ĐỔI KHOẢNG CÁCH)
   ============================================================================= */
// Cập nhật ô đỗ đơn lẻ (Bấm vào ô 1, 2, 3, 4 trên Web)
app.put("/api/lots/:lotId/slots/:slotNum", (req, res) => {
  const { lotId, slotNum } = req.params;
  const isOccupied = Boolean(req.body.occupied ?? req.body);

  if (!lotsState[lotId]) return res.status(404).json({ error: "Bãi xe không tồn tại" });

  lotsState[lotId].slots[slotNum] = isOccupied;
  const free = Object.values(lotsState[lotId].slots).filter((v) => v === false).length;
  lotsState[lotId].freeSlots = free;

  if (isDbConnected()) {
    pool.query(
      `INSERT INTO parking_slots (lot_id, slot_number, is_occupied, updated_at)
       VALUES ($1, $2, $3, NOW())
       ON CONFLICT (lot_id, slot_number) DO UPDATE SET is_occupied = EXCLUDED.is_occupied, updated_at = NOW()`,
      [lotId, slotNum, isOccupied]
    ).catch((e) => {});
  }

  res.json({ success: true, slotNum, isOccupied, freeSlots: free });
});

// Cập nhật khoảng cách siêu âm (Nút "Sát tường (7cm)" trên Web)
app.put("/api/lots/:lotId/distance", (req, res) => {
  const { lotId } = req.params;
  const distance = parseFloat(req.body.distance ?? req.body);

  if (!lotsState[lotId]) return res.status(404).json({ error: "Bãi xe không tồn tại" });

  lotsState[lotId].distance = distance;

  res.json({ success: true, distance });
});

/* =============================================================================
   TIMESCALEDB ANALYTICS & TIME-BUCKET QUERIES
   ============================================================================= */
// Thống kê mật độ theo giờ (Time-Series Bucket)
app.get("/api/lots/:lotId/analytics/hourly", async (req, res) => {
  const { lotId } = req.params;
  if (!isDbConnected()) {
    return res.json([
      { hour: "08:00", avgOccupied: 1, pings: 120 },
      { hour: "10:00", avgOccupied: 3, pings: 140 },
      { hour: "12:00", avgOccupied: 4, pings: 150 },
      { hour: "14:00", avgOccupied: 2, pings: 130 },
      { hour: "16:00", avgOccupied: 3, pings: 140 },
      { hour: "18:00", avgOccupied: 4, pings: 160 },
    ]);
  }

  try {
    const query = `
      SELECT
        time_bucket('1 hour', time) AS bucket,
        ROUND(AVG(total_slots - free_slots), 1) as avg_occupied,
        COUNT(*) as pings
      FROM lot_telemetry
      WHERE lot_id = $1 AND time > NOW() - INTERVAL '24 hours'
      GROUP BY bucket
      ORDER BY bucket ASC
    `;
    const result = await pool.query(query, [lotId]);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* =============================================================================
   KHỞI ĐỘNG SERVER
   ============================================================================= */
app.listen(PORT, "0.0.0.0", () => {
  console.log(`=================================================================`);
  console.log(`🌟 Smart Parking TimescaleDB Backend đang chạy tại:`);
  console.log(`👉 http://localhost:${PORT}`);
  console.log(`👉 Health check: http://localhost:${PORT}/api/health`);
  console.log(`👉 Danh sách bãi đỗ xe: http://localhost:${PORT}/api/lots`);
  console.log(`=================================================================`);
  initDb();
});

import "dotenv/config";
import pg from "pg";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const { Pool } = pg;
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const DATABASE_URL = process.env.DATABASE_URL || "postgres://postgres:postgres@localhost:5432/smartparking";

export const pool = new Pool({
  connectionString: DATABASE_URL,
  connectionTimeoutMillis: 3000,
  idleTimeoutMillis: 30000,
  max: 20,
});

let isConnected = false;

export async function tryConnectOnce() {
  try {
    const client = await pool.connect();
    console.log("✅ [DATABASE] Đã kết nối thành công tới TimescaleDB / PostgreSQL!");
    isConnected = true;

    // Đọc và chạy init.sql nếu cần
    try {
      const initSqlPath = path.resolve(__dirname, "../init.sql");
      if (fs.existsSync(initSqlPath)) {
        const sql = fs.readFileSync(initSqlPath, "utf-8");
        await client.query(sql);
        console.log("✅ [DATABASE] Đã nạp thành công Schema & Hypertables cho TimescaleDB!");
      }
    } catch (sqlErr) {
      console.warn("⚠️ [DATABASE] Lưu ý khi nạp init.sql (có thể đã tồn tại):", sqlErr.message);
    }

    client.release();
    return true;
  } catch (err) {
    return false;
  }
}

export async function initDb() {
  const ok = await tryConnectOnce();
  if (ok) return true;

  console.warn("⚠️ [DATABASE] Chưa thấy TimescaleDB (có thể Docker container đang khởi động). Chạy chế độ In-Memory dự phòng và tự động kết nối lại...");

  // Tiếp tục thử kết nối ngầm trong nền mỗi 5 giây
  const interval = setInterval(async () => {
    const connected = await tryConnectOnce();
    if (connected) {
      clearInterval(interval);
    }
  }, 5000);

  return false;
}

export function isDbConnected() {
  return isConnected;
}

import mqtt from "mqtt";

export function isLotId(value) {
  return typeof value === "string" && /^[a-zA-Z0-9_-]{1,50}$/.test(value);
}

const subscriptions = [
  "parking/+/slots/+",
  "parking/v1/lots/+/gates/+/status",
  "parking/v1/lots/+/events/+",
];

export function connectParkNodes({ url, onSlot, onGate, onOcr }) {
  const client = mqtt.connect(url, { queueQoSZero: false });
  let ready = false;

  client.on("connect", () => {
    client.subscribe(subscriptions, { qos: 1 }, (error, granted) => {
      ready = !error && client.connected && granted?.length === subscriptions.length &&
        granted.every(({ qos }) => qos < 128);
      if (!ready) console.error("[MQTT] Không thể đăng ký topic Park Node", error?.message ?? "");
    });
  });
  client.on("close", () => { ready = false; });
  client.on("error", (error) => console.error("[MQTT]", error.message));

  client.on("message", (topic, payload, packet) => {
    // Telemetry định kỳ của node không dùng retained. Bỏ snapshot cũ khi kết nối lại.
    if (packet.retain || payload.length > 256) return;
    const parts = topic.split("/");
    const isSlot = parts.length === 4 && parts[0] === "parking" && parts[2] === "slots";
    const isV1 = parts[0] === "parking" && parts[1] === "v1" && parts[2] === "lots";
    const isGate = isV1 && parts.length === 7 && parts[4] === "gates" && parts[6] === "status";
    const isOcr = isV1 && parts.length === 6 && parts[4] === "events";
    if (!isSlot && !isGate && !isOcr) return;
    const lotId = isSlot ? parts[1] : parts[3];
    if (!isLotId(lotId)) return;
    let data;
    try {
      data = JSON.parse(payload);
    } catch {
      return;
    }
    if (!data || typeof data !== "object") return;

    if (isSlot) {
      const key = parts[3];
      if (!/^(?:[1-9]|10)$/.test(key)) return;
      const slot = Number(key);
      const { totalSlots, occupied, distanceCm } = data;
      if (!Number.isInteger(totalSlots) || totalSlots < slot || totalSlots > 10 ||
          (occupied !== null && typeof occupied !== "boolean") ||
          (distanceCm !== null && (!Number.isFinite(distanceCm) || distanceCm < 0))) return;
      onSlot(lotId, slot, { totalSlots, occupied, distanceCm });
    } else if (isGate) {
      const key = parts[5];
      if (key !== "in" && key !== "out") return;
      if ((data.state !== "open" && data.state !== "closed") || typeof data.remoteEnabled !== "boolean") return;
      onGate(lotId, key, data);
    } else {
      const eventType = parts[5];
      if (eventType !== "entry" && eventType !== "exit") return;
      const direction = eventType === "entry" ? "in" : "out";
      const { plate, timestamp } = data;
      if (data.lotId !== lotId || data.lane !== direction.toUpperCase() || data.status !== "CONFIRMED" ||
          typeof plate !== "string" || !/^[A-Z0-9]{5,10}$/.test(plate) ||
          !Number.isSafeInteger(timestamp) || timestamp <= 0 || timestamp > Math.floor(Date.now() / 1000) + 60) return;
      onOcr(lotId, { plate, direction, timestamp: timestamp * 1000 });
    }
  });

  return {
    isConnected: () => ready && client.connected,
    async openGate(lotId, gate) {
      if (!ready || !client.connected) throw new Error("MQTT broker chưa sẵn sàng");
      await client.publishAsync(`parking/v1/lots/${lotId}/gates/${gate}/command`, "open", { qos: 0, retain: false });
    },
  };
}

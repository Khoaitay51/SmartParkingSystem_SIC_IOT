import mqtt from "mqtt";

export function isLotId(value) {
  return typeof value === "string" && /^[a-zA-Z0-9_-]{1,50}$/.test(value);
}

export function connectParkNodes({ url, onSlot, onGate }) {
  const client = mqtt.connect(url, { queueQoSZero: false });
  let ready = false;

  client.on("connect", () => {
    client.subscribe(["parking/+/slots/+", "parking/+/gates/+"], { qos: 1 }, (error, granted) => {
      ready = !error && client.connected && granted?.length === 2 && granted.every(({ qos }) => qos < 128);
      if (!ready) console.error("[MQTT] Không thể đăng ký topic Park Node", error?.message ?? "");
    });
  });
  client.on("close", () => { ready = false; });
  client.on("error", (error) => console.error("[MQTT]", error.message));

  client.on("message", (topic, payload, packet) => {
    // Telemetry định kỳ của node không dùng retained. Bỏ snapshot cũ khi kết nối lại.
    if (packet.retain || payload.length > 256) return;
    const [, lotId, kind, key] = topic.split("/");
    if (!isLotId(lotId)) return;
    let data;
    try {
      data = JSON.parse(payload);
    } catch {
      return;
    }
    if (!data || typeof data !== "object") return;

    if (kind === "slots" && /^(?:[1-9]|10)$/.test(key)) {
      const slot = Number(key);
      const { totalSlots, occupied, distanceCm } = data;
      if (!Number.isInteger(totalSlots) || totalSlots < slot || totalSlots > 10 ||
          (occupied !== null && typeof occupied !== "boolean") ||
          (distanceCm !== null && (!Number.isFinite(distanceCm) || distanceCm < 0))) return;
      onSlot(lotId, slot, { totalSlots, occupied, distanceCm });
    } else if (kind === "gates" && (key === "in" || key === "out")) {
      if ((data.state !== "open" && data.state !== "closed") || typeof data.remoteEnabled !== "boolean") return;
      onGate(lotId, key, data);
    }
  });

  return {
    isConnected: () => ready && client.connected,
    async openGate(lotId, gate) {
      if (!ready || !client.connected) throw new Error("MQTT broker chưa sẵn sàng");
      await client.publishAsync(`parking/${lotId}/commands/${gate}`, "open", { qos: 0, retain: false });
    },
  };
}

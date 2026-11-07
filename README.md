# Hệ thống quản lý bãi đỗ xe thông minh

Hai bãi thật cùng mạng LAN, dùng chung một broker MQTT và một backend. Mỗi bãi có một ESP32 Park Node và một `lot_id` riêng. Park Node đọc cảm biến siêu âm tại ô đỗ, dùng cảm biến IR để điều khiển servo tại cổng và gửi trạng thái qua MQTT.

```text
Park Node bãi A ──┐
                  ├── MQTT broker ── Backend Express ── TimescaleDB
Park Node bãi B ──┘                         │
                                            └── REST ── Web React
```

Web đọc ảnh chụp trạng thái qua REST khoảng mỗi giây. Khi gửi lệnh cổng, web gọi REST và backend publish MQTT đến đúng mã bãi. Trạng thái cổng trên API được cập nhật từ bản tin của Park Node. API báo trạng thái góc servo đã được firmware yêu cầu, việc xác nhận vị trí cơ khí cần quan sát tại cổng hoặc có cảm biến vị trí.

## Thành phần dự án

| Đường dẫn | Chức năng |
|---|---|
| [firmware/esp32_park_node](firmware/esp32_park_node) | Firmware chuẩn dùng ESP-IDF. Điểm vào chương trình là `main/main.c`. |
| [components](firmware/esp32_park_node/components) | Task IR, siêu âm, điều khiển servo và đọc cấu hình SPIFFS. |
| [backend](backend) | REST API, MQTT subscriber, dữ liệu hiện tại theo bãi và ghi lịch sử. |
| [frontend](frontend) | Web React. Màn quản lý cổng chọn bãi theo `lot_id`. |
| [docker-compose.yml](docker-compose.yml) | Mosquitto, TimescaleDB và backend. |

`firmware/src/main.cpp`, các script build PlatformIO cũ và simulator HTTP thuộc luồng Arduino trước đây. Quy trình dưới đây dành cho ESP32 Park Node.

## Khởi động broker và backend

Chạy từ thư mục gốc trên máy cùng mạng LAN với hai ESP32. Đặt `MQTT_BIND_IP` bằng IP LAN của máy chạy Docker. Ví dụ dưới đây dùng IP Wi-Fi hiện tại của máy này là `192.168.1.16`.

```powershell
$env:MQTT_BIND_IP = "192.168.1.16"
docker compose up -d --build
Invoke-RestMethod http://localhost:3000/api/health
docker compose logs -f mqtt backend
```

Cả hai kit dùng `mqtt://192.168.1.16:1883`. Backend trong Compose kết nối qua địa chỉ nội bộ `mqtt://mqtt:1883`. Nếu IP LAN của máy thay đổi, cập nhật cả `MQTT_BIND_IP` và địa chỉ broker trên hai kit. Nếu kit kết nối được Wi-Fi nhưng chưa thấy broker, kiểm tra tường lửa trên máy chạy Docker và chế độ cô lập thiết bị của mạng Wi-Fi.

Broker thử nghiệm trong repo cho phép kết nối ẩn danh. Giữ `remote_gate_enabled: false` khi thử telemetry. Trước khi mở điều khiển từ xa tại bãi thật, cần cấu hình xác thực, ACL cho MQTT và phân quyền API theo bãi.

Có thể chạy backend trực tiếp khi broker đã chạy. Dùng `DATABASE_URL` nếu cần lưu lịch sử, hoặc để backend chạy ở chế độ bộ nhớ cho phép thử giao tiếp.

```powershell
cd backend
npm ci
$env:MQTT_URL = "mqtt://127.0.0.1:1883"
npm start
```

## Build và cấu hình hai Park Node

Dùng shell đã kích hoạt ESP-IDF 6.x và công cụ ESP-IDF Component Manager. Project lấy ESP-MQTT và cJSON qua các manifest `idf_component.yml`. `sdkconfig.defaults` chọn bảng phân vùng tùy chỉnh có vùng SPIFFS `storage`.

```powershell
cd firmware/esp32_park_node
idf.py set-target esp32
idf.py build
idf.py -p COM5 flash
```

Sao chép [config.example.json](firmware/esp32_park_node/config_python/config.example.json) thành hai tệp cấu hình cục bộ. Điền Wi-Fi, địa chỉ broker và chân GPIO đúng với kit tại từng bãi. Hai mã `lot_mydinh` và `lot_caugiay` là dữ liệu mẫu. Có thể dùng mã khác theo địa điểm thật.

| Khóa | Bãi A | Bãi B |
|---|---|---|
| `lot_id` | Mã riêng, ví dụ `lot_mydinh` | Mã khác bãi A, ví dụ `lot_caugiay` |
| `mqtt_broker_uri` | `mqtt://192.168.1.16:1883` | `mqtt://192.168.1.16:1883` |
| `num_parking_lots` | Số ô siêu âm trên kit A, từ 1 đến 10 | Số ô siêu âm trên kit B, từ 1 đến 10 |
| `trigger_pins`, `echo_pins` | Danh sách GPIO theo thứ tự ô | Danh sách GPIO theo thứ tự ô |
| `remote_gate_enabled` | Mặc định `false` | Mặc định `false` |

Đặt `lot_id` dài từ 1 đến 50 ký tự, chỉ dùng chữ ASCII, số, gạch dưới và gạch ngang. `num_parking_lots` là **số ô** trên một kit. Mỗi địa điểm dùng một mã bãi khác nhau.

Sau khi flash, đóng Serial Monitor. Cài PySerial nếu cần, chạy script với đúng cổng và bấm RESET khi script đang chờ. Firmware nhận JSON qua UART0, lưu vào SPIFFS rồi nạp cấu hình.

```powershell
python -m pip install pyserial
python config_python/config.py --port COM5 --config config_python/config.local.a.json
python config_python/config.py --port COM6 --config config_python/config.local.b.json
```

Thay COM5 và COM6 bằng cổng USB thật. Dùng `idf.py -p COM5 monitor` để xem log sau khi cấu hình. Thiết bị đang chạy firmware cũ cần flash bản này và nạp cấu hình có `lot_id` trước khi ghép vào hệ thống hai bãi.

## Hợp đồng MQTT

Các topic có dạng `parking/{lotId}/...`. Thiết bị không phát retained. Các bản tin định kỳ cho phép backend nhận lại trạng thái sau khi kết nối lại.

| Chiều | Topic | Payload ví dụ |
|---|---|---|
| Park Node → backend | `parking/{lotId}/slots/{slot}` | `{"totalSlots":2,"occupied":true,"distanceCm":12}` |
| Park Node → backend | `parking/{lotId}/gates/in` hoặc `/out` | `{"state":"closed","remoteEnabled":false}` |
| Backend → Park Node | `parking/{lotId}/commands/in` hoặc `/out` | Văn bản `open` |

Ô đỗ đánh số từ 1. Firmware báo khi trạng thái thay đổi và định kỳ khoảng 2 giây. Timeout không có Echo được coi là không phát hiện xe, còn lỗi đo khác gửi `occupied: null`. Bản tin có thể dùng `distanceCm: null` khi thiếu khoảng cách hợp lệ. Backend đếm số ô được xác nhận trống và dùng khoảng cách hợp lệ nhỏ nhất làm giá trị tổng quan của bãi. Cổng báo trạng thái khi thay đổi và định kỳ khoảng 1 giây.

Điều khiển tại chỗ bằng IR tiếp tục hoạt động khi mất MQTT. Khi được bật điều khiển từ xa, một lệnh MQTT hợp lệ yêu cầu giữ mở khoảng 4 giây. Firmware chỉ yêu cầu đóng khi hết thời gian giữ và IR không còn phát hiện vật. Lệnh dùng QoS 0, không retained và không có hàng đợi ngoại tuyến. HTTP `202` cho biết backend đã gửi lệnh MQTT. Đọc bản tin trạng thái tiếp theo và đối chiếu tại thiết bị để xác nhận phản hồi.

## Chạy web và kiểm tra tại hai bãi

Dùng Node.js 22.22 trở lên cho frontend. Mở `http://localhost:5173/owner/gate` sau khi chạy Vite.

```powershell
cd frontend
npm ci
npm run dev
```

Đặt `VITE_API_BASE_URL` trước khi chạy Vite hoặc build nếu web và backend chạy trên hai máy khác nhau. Giá trị mặc định là `http://localhost:3000/api`.

1. Kiểm tra `GET /api/health` báo `mqtt: connected`.
2. Bật cả hai kit và kiểm tra `GET /api/lots/{lotId}/status` cho từng mã bãi. Đối chiếu `lastHeartbeat` và số ô với kit thật. Có thể tải lại trang quản lý cổng sau khi các bãi mới bắt đầu gửi dữ liệu.
3. Tác động vào cảm biến một ô ở bãi A rồi làm tương tự ở bãi B. Xác nhận chỉ đúng ô ở đúng bãi thay đổi trên giao diện.
4. Khi đã cấu hình quyền và có người giám sát tại hiện trường, kiểm tra lệnh mở từ xa ở từng cổng. So sánh bản tin trạng thái với chuyển động thực tế và xác nhận bãi còn lại không nhận lệnh.
5. Ngắt Wi-Fi một kit trong lúc kit còn lại hoạt động. Kiểm tra dữ liệu bãi còn lại tiếp tục cập nhật và kit bị ngắt gửi lại trạng thái sau khi kết nối.

Backend giữ API OCR `POST /api/lots/{lotId}/ocr`. Khi bãi có Park Node đang bật điều khiển từ xa, sự kiện có thể yêu cầu mở đúng cổng qua MQTT. Trạng thái ô tiếp tục lấy từ cảm biến. Màn tài xế đọc sự kiện OCR gần nhất của bãi mặc định, nên có thể bỏ qua sự kiện trung gian nếu nhiều bản tin đến giữa hai lượt đọc. Dữ liệu phí và số dư cần kiểm thử riêng với TimescaleDB.

## Kết quả kiểm tra

- ESP-IDF 6.1 beta đã build thành công `build/esp32_park_node.bin` cho ESP32. Frontend đã qua kiểm tra TypeScript và build Vite.
- Bài thử với broker MQTT cục bộ và hai mã bãi xác nhận trạng thái tách riêng, lệnh chỉ publish tới topic được chọn và API từ chối khi node tắt điều khiển từ xa hoặc trạng thái cổng đã cũ.
- Còn cần nghiệm thu trên hai ESP32 thật và kiểm tra lưu lịch sử với TimescaleDB. Bài thử MQTT dùng backend ở chế độ bộ nhớ.

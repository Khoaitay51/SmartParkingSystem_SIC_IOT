# 🎙️ KỊCH BẢN THUYẾT TRÌNH BÁO CÁO DỰ ÁN SMART PARKING (SIC IOT)
### Tài liệu hướng dẫn người thuyết trình (Speaker Notes & Presentation Script)
*(Dành cho buổi bảo vệ đồ án / thuyết minh trước Hội đồng giám khảo)*

---

## ⏱️ Kế Hoạch Phân Bổ Thời Gian Thuyết Trình
- **Tổng thời gian thuyết trình:** 10 – 12 phút.
- **Thời gian vấn đáp (Q&A) & Demo thực tế:** 5 – 8 phút.
- **Slide 1 - 3:** Mở đầu & Kiến trúc tổng thể (~2.5 phút).
- **Slide 4 - 5:** Chuyên sâu Firmware ESP32 (~2.5 phút).
- **Slide 6 - 8:** Chuyên sâu Backend Cloud & AI OCR Auto-billing (~3 phút).
- **Slide 9 - 10:** Bộ công cụ Scripts & Giám sát Live Log (~2 phút).
- **Slide 11:** Ứng dụng Web, Đánh giá thông số & Kết luận (~1.5 phút).

---

## 📑 KỊCH BẢN NÓI CHI TIẾT TỪNG SLIDE

---

### 🟢 SLIDE 1: TRANG BÌA (HERO TITLE)
* **Màn hình hiển thị:** Tên đề tài, biểu trưng SIC IoT, 4 thẻ chỉ số cốt lõi.
* **Thời lượng:** ~45 giây.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Kính thưa quý thầy cô trong Hội đồng giám khảo và các bạn!*
> 
> *Em xin đại diện nhóm trình bày báo cáo kỹ thuật đề tài: **'Hệ thống quản lý bãi đỗ xe thông minh - Smart Parking System'**, được phát triển trong khuôn khổ chương trình Samsung Innovation Campus (SIC) IoT.*
> 
> *Đề tài của chúng em tập trung giải quyết bài toán tự động hóa kiểm soát bãi đỗ xe bằng sự kết hợp hoàn chỉnh giữa: Vi điều khiển nhúng **ESP32**, nền tảng điện toán đám mây **Firebase Realtime Database**, công nghệ nhận diện biển số **AI Camera OCR** và ứng dụng web quản trị **React 19**.*
> 
> *Điểm đặc biệt của dự án là loại bỏ hoàn toàn các dữ liệu tĩnh giả lập, toàn bộ hệ thống vận hành 100% trên dữ liệu thực với độ trễ truyền nhận dưới 200 mili-giây, hỗ trợ thanh toán trừ tiền ví tự động không chạm. Sau đây, em xin phép đi vào nội dung chi tiết của đề tài."*

---

### 🟢 SLIDE 2: TỔNG QUAN VẤN ĐỀ & MỤC TIÊU NGHIÊN CỨU
* **Màn hình hiển thị:** Mục tiêu kỹ thuật và Khả năng mở rộng thực nghiệm.
* **Thời lượng:** ~1 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Kính thưa thầy cô, thực trạng tại các bãi đỗ xe hiện nay vẫn tồn tại nhiều hạn chế: việc ghi vé giấy hoặc quẹt thẻ từ thủ công thường gây ùn tắc giờ cao điểm, nguy cơ thất thoát doanh thu, tài xế mất nhiều thời gian tìm vị trí đỗ trống, và đặc biệt là rủi ro va quẹt khi lùi xe vào chuồng do thiếu thiết bị cảnh báo cự ly.*
> 
> *Xuất phát từ thực tế đó, mục tiêu của đề tài chúng em hướng tới 4 giá trị kỹ thuật cốt lõi:*
> 1. *Giám sát tự động trạng thái từng vị trí đỗ và tính toán số chỗ trống theo thời gian thực.*
> 2. *Điều khiển barrier tự động bằng động cơ Servo 90 độ, tích hợp thuật toán an toàn tuyệt đối chống va đập đè lên nóc xe.*
> 3. *Đo khoảng cách siêu âm chính xác hỗ trợ tài xế lùi xe và cảnh báo nguy cơ va chạm bằng còi buzzer biến thiên.*
> 4. *Tự động hóa hoàn toàn quy trình nhận diện biển số xe qua AI OCR và khấu trừ cước phí trực tiếp qua ví điện tử.*
> 
> *Hệ thống được thiết kế theo cấu trúc mô-đun mở rộng linh hoạt, sẵn sàng thích ứng với quy mô nhiều vị trí đỗ và nhiều cổng ra vào thực tế."*

---

### 🟢 SLIDE 3: KIẾN TRÚC HỆ THỐNG PHÂN TẦNG (3-TIER ARCHITECTURE)
* **Màn hình hiển thị:** Sơ đồ 3 tầng: Firmware Nhúng $\longleftrightarrow$ Backend Cloud $\longleftrightarrow$ Frontend Client.
* **Thời lượng:** ~1.5 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Để đảm bảo tính độc lập, độ tin cậy và khả năng mở rộng, hệ thống của chúng em được xây dựng theo kiến trúc phân tầng 3 lớp rõ ràng:*
> 
> * **Tầng thứ nhất là Tầng Thiết Bị Ngoại Vi (Firmware Node):** *Sử dụng vi điều khiển trung tâm ESP32 làm nhiệm vụ thu thập tín hiệu từ các cảm biến hồng ngoại tại các vị trí đỗ và trước cổng, cảm biến siêu âm HC-SR04, xuất tín hiệu điều khiển 2 động cơ Servo barrier, còi báo động và màn hình OLED SSD1306 tại chỗ.*
> 
> * **Tầng thứ hai là Tầng Đám Mây Trung Gian (Backend Cloud):** *Đóng vai trò 'trái tim' điều phối dữ liệu, sử dụng cơ sở dữ liệu Firebase Realtime NoSQL đặt tại cụm máy chủ Singapore. Tầng này phân tách thành các node chức năng: node trạng thái (status), node hàng đợi lệnh (commands) và node nhận diện biển số (ocr).*
> 
> * **Tầng thứ ba là Tầng Ứng Dụng Khách (Frontend & AI Client):** *Ứng dụng Web SPA hiện đại viết bằng React 19 và Tailwind CSS, tích hợp khối AI Camera OCR. Điểm mấu chốt là giao tiếp giữa 3 tầng này là **luồng đồng bộ hai chiều khép kín**: một sự kiện cảm biến từ phần cứng lập tức nhảy lên Web trong tích tắc, và ngược lại, một cú click chuột từ Web có thể điều khiển trực tiếp cánh tay barrier vật lý trên bàn."*

---

### 🟢 SLIDE 4: CHUYÊN SÂU FIRMWARE (PHẦN 1: CẢM BIẾN, BARRIER FSM & SIÊU ÂM)
* **Màn hình hiển thị:** Lọc nhiễu 200µs, FSM Barrier 3 trạng thái, Cảm biến siêu âm HC-SR04, Quy hoạch GPIO.
* **Thời lượng:** ~1.5 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Đi sâu vào phần kỹ thuật Firmware nhúng, em xin trình bày 4 giải pháp thiết kế quan trọng:*
> 
> * **Thứ nhất là thuật toán lọc nhiễu cảm biến hồng ngoại:** *Cảm biến ngõ ra Digital trả về mức LOW khi phát hiện vật cản. Để tránh hiện tượng chập chờn tín hiệu khi xe mới di chuyển mấp mé vào ô hoặc bị ánh sáng bên ngoài tác động, hàm đọc cảm biến được tích hợp kỹ thuật lọc nhiễu xác nhận kép với khoảng trễ vi mô 200 micro-giây.*
> 
> * **Thứ hai là Máy trạng thái hữu hạn (FSM) điều khiển Barrier:** *Barrier hoạt động theo chu trình 3 trạng thái: Đóng (CLOSED) &rarr; Mở (OPENED) &rarr; Chờ thông thoáng (WAIT_CLEAR). Sau khi mở tối thiểu 4 giây, hệ thống bắt buộc kiểm tra cảm biến cổng: **nếu xe vẫn còn đang chắn dưới thanh chắn, barrier tiếp tục giữ mở**, tuyệt đối không hạ xuống nhằm bảo vệ an toàn cho nóc xe.*
> 
> * **Thứ ba là thuật toán đo cự ly siêu âm HC-SR04:** *Vi điều khiển phát xung kích hoạt 10 micro-giây vào chân Trig và đo thời gian phản hồi ở chân Echo. Chúng em cài đặt thời gian chờ tối đa (timeout) là 25.000 micro-giây, tương đương cự ly tối đa 4.3 mét để bảo vệ CPU không bị treo chờ nếu sóng âm bị phân tán.*
> 
> * **Thứ tư là quy hoạch chân GPIO an toàn:** *Các chân PWM của Servo được gán vào GPIO 4 và GPIO 13, tách biệt hoàn toàn khỏi các chân cấu hình điện áp Strapping Pin MTDI như GPIO 12 để đảm bảo vi điều khiển khởi động an toàn 100%."*

---

### 🟢 SLIDE 5: CHUYÊN SÂU FIRMWARE (PHẦN 2: NON-BLOCKING, OLED & REST CLIENT)
* **Màn hình hiển thị:** Còi phi chặn millis(), OLED SSD1306 vẽ sơ đồ, Khối truyền thông HTTPS REST.
* **Thời lượng:** ~1.5 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Tiếp theo là kỹ thuật lập trình hướng thời gian thực trên ESP32:*
> 
> * **Thứ nhất là giải pháp Còi Buzzer phi chặn (Non-blocking):** *Trong các hệ thống thông thường, người ta hay dùng lệnh delay() để tạo tiếng bíp, điều này làm đóng băng toàn bộ CPU. Trong firmware của chúng em, hàm `Buzzer_Update` được viết hoàn toàn bằng máy trạng thái đếm thời gian `millis()`. Còi có tần số kêu biến thiên theo cự ly lùi: ngoài 30cm còi tắt; từ 10 đến 30cm còi kêu ngắt quãng dồn dập khi càng đến gần; và dưới 10cm còi phát âm thanh liên tục để tài xế phanh khẩn cấp.*
> 
> * **Thứ hai là Màn hình OLED SSD1306 tại chỗ:** *Giao tiếp qua bus I2C hiển thị sơ đồ hình học của bãi xe, ô có xe được tô đặc, ô trống để khung rỗng, kèm theo thông số chỗ trống và cự ly siêu âm tính theo cm.*
> 
> * **Thứ ba là Khối truyền thông RESTful HTTPS:** *ESP32 sử dụng thư viện `HTTPClient` kết hợp `ArduinoJson v7` đóng gói dữ liệu JSON gửi lên Firebase theo chu kỳ 800 mili-giây qua phương thức `PUT /status.json`, đồng thời lắng nghe lệnh điều khiển tại `GET /commands.json`. Khối WiFi còn tích hợp bộ giám sát tự động tái kết nối nếu mạng bị gián đoạn."*

---

### 🟢 SLIDE 6: CHUYÊN SÂU BACKEND (PHẦN 1: CẤU TRÚC DỮ LIỆU NOSQL & ĐỒNG BỘ KÉP)
* **Màn hình hiển thị:** Cấu trúc JSON NoSQL phân tầng, Giao thức đồng bộ kép REST và SSE Stream.
* **Thời lượng:** ~1 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Chuyển sang phần Backend - Trọng tâm điều phối dữ liệu của hệ thống:*
> 
> *Cơ sở dữ liệu được tổ chức theo cấu trúc NoSQL phân cấp dạng cây JSON trên Firebase Realtime Database. Như thầy cô thấy trên slide, dữ liệu bãi xe được phân tách thành 3 nhánh chức năng riêng biệt:*
> * `status`: *Chứa thông tin các vị trí đỗ, cự ly lùi, trạng thái 2 cổng và mốc nhịp tim.*
> * `commands`: *Chứa hàng đợi tiếp nhận lệnh mở barrier từ xa.*
> * `ocr`: *Ghi nhận sự kiện nhận diện biển số xe, cước phí và thời điểm quét.*
> 
> *Điểm sáng tạo trong kiến trúc Backend của chúng em là **Giao thức đồng bộ kép (Dual Protocol)**:*
> * *Đối với vi điều khiển nhúng ESP32, hệ thống sử dụng giao thức **RESTful API** ngắn gọn, tiết kiệm tối đa bộ nhớ RAM.*
> * *Đối với ứng dụng Web Client, hệ thống sử dụng giao thức **Server-Sent Events (SSE)**, mở một kênh truyền stream dữ liệu liên tục từ Cloud xuống trình duyệt. Kỹ thuật này giúp giảm đến 95% băng thông mạng so với việc polling liên tục, đưa độ trễ cập nhật trạng thái xuống dưới 200 mili-giây."*

---

### 🟢 SLIDE 7: CHUYÊN SÂU BACKEND (PHẦN 2: LIVENESS HEARTBEAT & CHUẨN HÓA DỮ LIỆU)
* **Màn hình hiển thị:** Cơ chế giám sát nhịp tim Heartbeat, Giải quyết ép kiểu mảng tự động (Array Coercion).
* **Thời lượng:** ~1 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Để hệ thống vận hành ổn định trong môi trường thực tế, Backend được trang bị 2 cơ chế kỹ thuật đặc biệt:*
> 
> * **Cơ chế thứ nhất là Giám sát nhịp tim (Liveness Heartbeat):** *Cứ sau mỗi chu kỳ cập nhật, vi điều khiển sẽ ghi mốc thời gian epoch millisecond lên Cloud. Giao diện Web liên tục đối soát mốc này với thời gian thực; nếu vượt quá ngưỡng quy định (quá 10 giây không có tín hiệu), Web sẽ cảnh báo ngay trạm IoT đang Offline. Khi phần cứng hoạt động trở lại, hệ thống tự động nhận diện và chuyển sang Online mà không cần tải lại trang.*
> 
> * **Cơ chế thứ hai là Xử lý ép kiểu dữ liệu tự động (Array Coercion):** *Cơ sở dữ liệu Firebase có đặc tính tự động chuyển đổi các đối tượng có khóa là số nguyên liên tiếp thành mảng JSON. Điều này dễ gây lỗi khi đồng bộ giữa nhiều nền tảng (C++, Python và TypeScript). Chúng em đã xây dựng hàm chuẩn hóa `extract_slots` trên cả backend script và web frontend, đảm bảo mọi truy vấn trạng thái vị trí đỗ luôn trả về kiểu dữ liệu boolean chính xác, loại bỏ hoàn toàn lỗi runtime truy cập thuộc tính mảng."*

---

### 🟢 SLIDE 8: CHUYÊN SÂU BACKEND (PHẦN 3: ĐỘNG CƠ AI OCR & AUTO-BILLING ENGINE)
* **Màn hình hiển thị:** Luồng Check-in xe Vào, Luồng Check-out tính cước xe Ra, An toàn giao dịch ví.
* **Thời lượng:** ~1.5 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Trụ cột thứ ba của Backend là **Động cơ nhận diện AI OCR và Thu phí tự động (Auto-Billing Engine)**:*
> 
> * **Khi xe tiến đến Cổng Vào (Check-in):** *Camera AI OCR nhận diện biển số và ghi vào node `/ocr` với hướng 'in'. Hệ thống tự động gửi lệnh mở barrier Cổng Vào, đối soát biển số với cơ sở dữ liệu người dùng, kích hoạt trạng thái đỗ xe `isParking = true` và bắt đầu tính giờ gửi xe trên điện thoại tài xế.*
> 
> * **Khi xe tiến đến Cổng Ra (Check-out):** *Camera quét biển số xe khi rời bãi và ghi vào node `/ocr` với hướng 'out' kèm mức cước tính toán. Barrier Cổng Ra tự động mở cho xe rời đi.*
> 
> * *Ngay tại thời điểm đó, **Auto-Billing Engine** sẽ tự động truy xuất tài khoản sở hữu xe, kiểm tra số dư ví điện tử ParkIQ, khấu trừ tiền cước và tạo một biên lai giao dịch duy nhất lưu vào lịch sử.*
> 
> *Quy trình này áp dụng cơ chế xác thực số dư khả dụng trước khi trừ và khóa chống lặp giao dịch (idempotency key), đảm bảo tính toàn vẹn tài chính tuyệt đối cho tài xế và chủ bãi."*

---

### 🟢 SLIDE 9: HỆ THỐNG KỊCH BẢN TỰ ĐỘNG HÓA & KIỂM THỬ SCRIPT
* **Màn hình hiển thị:** Script `demo_controller.py`, File `dieu_khien_xe.bat`, Phím tắt nhanh OCR.
* **Thời lượng:** ~1.5 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Để phục vụ công tác kiểm thử tích hợp toàn diện và biểu diễn demo ngay cả khi chưa cắm kit phần cứng, nhóm đã xây dựng một bộ công cụ kịch bản tự động hóa chuyên nghiệp trong thư mục `scripts/`:*
> 
> * *Trung tâm là kịch bản Python `demo_controller.py`, được kích hoạt bằng file thực thi 1-click `dieu_khien_xe.bat`.*
> * *Kịch bản này giao tiếp trực tiếp với Firebase Realtime Database qua giao thức REST, bao gồm các hàm nghiệp vụ:*
>   * `trigger_ocr()`: *Mô phỏng camera AI đọc biển số, điều khiển mở cổng và chiếm/giải phóng vị trí đỗ.*
>   * `toggle_slot()`: *Mô phỏng cảm biến hồng ngoại phát hiện có xe hoặc xe rời đi.*
>   * `set_distance()`: *Mô phỏng thay đổi cự ly lùi xe siêu âm.*
> 
> *Đặc biệt, giao diện dòng lệnh tích hợp sẵn các phím tắt nhanh: bấm `v1` để cho xe VinFast VF8 vào, `r1` để cho xe ra và trừ 15.000đ; hoặc bấm lệnh `ocr` để nhập bất kỳ biển số xe nào mà thầy cô vừa đăng ký mới trên Web, hệ thống sẽ lập tức nhận diện và xử lý theo thời gian thực."*

---

### 🟢 SLIDE 10: HỆ THỐNG GIÁM SÁT NHẬT KÝ LIVE LOG & NẠP FIRMWARE
* **Màn hình hiển thị:** Script `xem_log_firebase.bat`, `xem_log_esp32.bat`, `upload_firmware.bat`.
* **Thời lượng:** ~1 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Bên cạnh bảng điều khiển, chúng em còn trang bị các công cụ giám sát chuyên sâu:*
> 
> * **Thứ nhất là `xem_log_firebase.bat` (chạy script `log_viewer.py`):** *Áp dụng thuật toán so sánh sai khác trạng thái (state diffing). Bất kỳ thao tác nào diễn ra từ Web, từ nút bấm, từ cảm biến ESP32 hay từ kịch bản OCR đều được in ra màn hình Terminal thành từng dòng log có mốc thời gian chi tiết theo từng giây.*
> 
> * **Thứ hai là `xem_log_esp32.bat`:** *Kết nối trực tiếp cổng Serial UART của vi điều khiển ở tốc độ 115.200 baud qua PlatformIO Device Monitor, giúp theo dõi toàn bộ log debug phần cứng bên trong chip ESP32.*
> 
> * **Thứ ba là `upload_firmware.bat`:** *Tự động phát hiện môi trường PlatformIO Core trong Windows để biên dịch mã nguồn C++ và nạp thẳng file nhị phân vào kit ESP32 chỉ với 1 cú click chuột mà không cần cài đặt phần mềm phức tạp."*

---

### 🟢 SLIDE 11: ỨNG DỤNG WEB, TÀI KHOẢN MẪU & TỔNG KẾT KỸ THUẬT
* **Màn hình hiển thị:** Bảng 4 tài khoản mẫu, Thẻ thông số hiệu năng (RAM, Flash, Build time, Latency), Đánh giá kết luận.
* **Thời lượng:** ~1.5 phút.

> 🗣️ **Lời thoại thuyết trình:**
> 
> *"Cuối cùng là phần kiểm thử ứng dụng Web và đánh giá tổng thể hệ thống:*
> 
> * *Hệ thống đã chuẩn bị sẵn 4 tài khoản thử nghiệm đại diện cho các vai trò: anh Nguyễn Văn An (sở hữu xe VinFast VF8), chị Trần Thị Bình (xe Honda CR-V), anh Phạm Tuấn Anh (xe Toyota Cross) và chủ bãi Lê Hoàng Nam. Mỗi tài khoản có số dư ví, phương tiện và lịch sử giao dịch độc lập, có thể đăng nhập nhanh 1-click tại trang Login.*
> 
> *Về các chỉ số kỹ thuật đạt được:*
> * *Firmware ESP32 tối ưu hóa xuất sắc: chỉ chiếm **14.6% RAM** và **74% bộ nhớ Flash**.*
> * *Ứng dụng Web Client biên dịch đóng gói sạch trong **328 mili-giây**.*
> * *Độ trễ truyền nhận tín hiệu Cloud hai chiều đạt **dưới 200 mili-giây**.*
> 
> *Kính thưa quý thầy cô, đề tài của chúng em đã chứng minh được tính khả thi và hoàn thiện kỹ thuật cao: từ vi điều khiển nhúng an toàn, đám mây đồng bộ thời gian thực mượt mà đến trải nghiệm thanh toán AI OCR tiện lợi. Nhóm em xin chân thành cảm ơn quý thầy cô đã lắng nghe và rất mong nhận được những câu hỏi, ý kiến đóng góp từ Hội đồng ạ!"*

---

## 💡 CÁC CÂU HỎI THƯỜNG GẶP (Q&A PHẢN BIỆN) & HƯỚNG TRẢ LỜI

### Câu hỏi 1: *"Nếu xe đang đi qua cổng mà mạng WiFi bị mất kết nối thì barrier có đóng đè vào xe không?"*
* **Trả lời chuẩn kỹ thuật:**
  > *"Thưa thầy cô, tuyệt đối không ạ. Logic an toàn của barrier được xử lý hoàn toàn **cục bộ (locally) trên vi điều khiển ESP32** bằng cảm biến hồng ngoại phần cứng gắn ngay dưới cổng, độc lập hoàn toàn với mạng WiFi. Khi cảm biến phát hiện xe đang đứng chắn, biến `carDetected` luôn ở mức logic 1 và máy trạng thái FSM sẽ liên tục gia hạn mở cánh tay. Chỉ khi xe đã rời khỏi vùng quét an toàn, cánh tay mới được hạ xuống."*

### Câu hỏi 2: *"Tại sao nhóm lại kết hợp cả REST API và Server-Sent Events (SSE) mà không dùng WebSockets?"*
* **Trả lời chuẩn kỹ thuật:**
  > *"Thưa thầy cô, nhóm đã cân nhắc rất kỹ yếu tố tối ưu tài nguyên:*
  > * *Với vi điều khiển ESP32, việc duy trì một kết nối WebSocket liên tục đòi hỏi chi phí RAM lớn để lưu ngữ cảnh kết nối (handshake buffer) và dễ bị treo khi mạng WiFi chập chờn. Do đó, sử dụng RESTful HTTPS là giải pháp nhẹ nhàng và đáng tin cậy nhất cho phần cứng nhúng.*
  > * *Với trình duyệt Web, Server-Sent Events (SSE) là giao thức chuẩn chạy trên nền HTTP/1.1 hoặc HTTP/2 một chiều từ Server xuống Client, không cần mở thêm cổng đặc biệt và tự động kết nối lại khi mất mạng. Độ trễ của SSE trên Firebase đạt dưới 200ms, hoàn toàn đáp ứng thời gian thực mà tối ưu hơn WebSockets rất nhiều."*

### Câu hỏi 3: *"Nếu người dùng nhập sai biển số xe hoặc xe chưa đăng ký đi vào thì hệ thống xử lý thế nào?"*
* **Trả lời chuẩn kỹ thuật:**
  > *"Thưa thầy cô, hệ thống có 2 cơ chế linh hoạt:*
  > * *Người dùng có thể vào mục 'Xe của tôi' trên Web để đăng ký thêm biển số xe mới bất cứ lúc nào, biển số lập tức được lưu vào hệ thống và kích hoạt cờ nhận diện AI OCR.*
  > * *Nếu là xe vãng lai chưa kịp đăng ký, hệ thống vẫn cho phép mở cổng vào gửi xe và ghi nhận sự kiện tại Cổng IoT của Chủ bãi. Khi xe ra, tài xế có thể thanh toán trực tiếp hoặc đăng ký nhanh tài khoản để hưởng dịch vụ trừ ví tự động."*

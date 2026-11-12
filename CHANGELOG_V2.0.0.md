# BOT TRADER SWING – MULTI STOCK

## V2.0.0 – Khóa nền tảng và cập nhật điều hướng

### Đã thực hiện
- Giữ nguyên 5 tab và các module lõi hiện có.
- Giữ nguyên `st.session_state.market_data` và `st.session_state.analysis`.
- Giữ nguyên TAB 5 Excel/CSV độc lập.
- Bổ sung thanh tab cố định phía trên khi cuộn nội dung.
- Trên màn hình hẹp, tên tab không xuống dòng; thanh tab có thể cuộn ngang.

### Kiểm tra
- `pytest -q`: 1 test smoke hiện có đã chạy và đạt.
- Đây là kiểm tra pipeline dữ liệu/chỉ báo/quyết định cơ bản; chưa phải kiểm thử giao diện Streamlit trên trình duyệt hoặc điện thoại.

### Chưa triển khai trong bản này
- Bộ lọc chất lượng dữ liệu và trạng thái thị trường.
- Scanner đa mã và xếp hạng sức mạnh tương đối.
- Bộ chiến lược breakout/pullback/trend-following.
- Quản trị rủi ro danh mục và quản lý vị thế nâng cao.
- Bộ backtest nâng cao và các chỉ số hiệu suất.

Các hạng mục trên được triển khai theo từng phiên bản tiếp theo, không thay thế hoặc xóa chức năng cũ.

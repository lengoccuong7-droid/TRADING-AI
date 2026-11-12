# CHANGELOG V2.1.0

- Giữ nguyên 5 tab và các hàm lõi hiện có; giữ `market_data`, `analysis` trong session state.
- Cố định thanh tab khi cuộn; thanh tab có thể cuộn ngang trên màn hình nhỏ.
- Thêm kiểm tra chất lượng dữ liệu và cảnh báo dữ liệu cũ.
- Thêm đánh giá market regime từ VNINDEX hoặc market breadth.
- Thêm relative strength, scanner đa mã và điểm xếp hạng heuristic.
- Thêm nhận diện tham chiếu Trend Following, Pullback và Breakout.
- Tách sizing sang `risk_manager.py`; giữ nguyên khóa kết quả cũ, bổ sung target 2 và thông tin rủi ro.
- Thêm `portfolio_manager.py` để tổng hợp giá trị, P/L chưa thực hiện, exposure và risk tới stop.
- Sửa backtest: tín hiệu phiên trước khớp giả định ở open phiên sau; đánh dấu equity tại close; phí và trượt giá áp dụng hai chiều; bổ sung Max Drawdown, CAGR, Sharpe, Profit Factor và Expectancy.
- Giữ TAB 5 Excel/CSV độc lập.
- Bổ sung kiểm thử tự động cho pipeline, scanner, sizing, danh mục và backtest.

## Chưa triển khai / cần dữ liệu chuyên biệt
- Điều chỉnh corporate actions/giá điều chỉnh và xác minh nguồn dữ liệu.
- Walk-forward và out-of-sample validation.
- Bộ lọc thanh khoản theo giá trị giao dịch, giới hạn sức mua theo thanh khoản.
- Đồng bộ dữ liệu tự động, API broker và đặt lệnh (chủ ý không có).
- Giao diện biểu đồ nến tương tác.

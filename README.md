# BOT TRADER SWING – MULTI STOCK (V2.2.0)

Ứng dụng nghiên cứu kỹ thuật từ dữ liệu OHLCV do người dùng tải lên, có Scanner đa mã, phân loại chiến lược tham chiếu, quản trị rủi ro/danh mục mô phỏng và backtest cơ bản. Ứng dụng không kết nối sàn, không gửi lệnh và không bảo đảm lợi nhuận.

## Cài đặt và chạy
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Dữ liệu đầu vào
- OHLCV: Date, Open, High, Low, Close, Volume; có thể thêm Symbol/Ticker.
- Hỗ trợ CSV, XLSX, XLS, JSON, TXT, Parquet, PDF bảng văn bản và DOCX bảng.
- Giá được giữ nguyên theo đơn vị file; không tự nhân/chia 1.000.
- Không tự bù dữ liệu trống, không tự điều chỉnh corporate actions.
- Nếu không có VNINDEX, chế độ thị trường được ước lượng từ breadth của các mã được tải lên và có độ tin cậy thấp.

## Các tab
1. Dữ liệu & Tổng quan: nạp dữ liệu, chất lượng, ngày cập nhật và trạng thái thị trường.
2. Chỉ báo: MA5/10/20/30/40/50/100/200, EMA, RSI, MACD, ATR, ADX, Bollinger, dòng tiền; biểu đồ có HLC3 và VWAP20.
3. Trợ lý phân tích: giải thích rule-based, chiến lược trend-following/pullback/breakout và phản biện rủi ro.
4. Scanner, Swing & Danh mục: xếp hạng heuristic, mô phỏng backtest, theo dõi vị thế qua CSV.
5. Excel/CSV độc lập: giữ chức năng đọc/xuất bảng riêng, không phụ thuộc lõi phân tích.
6. Tổng hợp Trading: tổng hợp các nhóm chỉ báo, cảnh báo mâu thuẫn, vùng hỗ trợ/kháng cự, giá xác nhận tham chiếu, TP1/TP2/SL và R:R lấy từ module hiện có.

## CSV danh mục
Cột bắt buộc: `symbol, quantity, entry_price`. Cột tùy chọn: `market_price, stop_price`.

## Phương pháp và giới hạn
- Scanner sử dụng điểm heuristic để sắp xếp tương đối; không phải xác suất sinh lời.
- Tín hiệu chỉ xác định sau khi có dữ liệu đóng cửa. Backtest khớp giả định tại giá mở cửa phiên kế tiếp, tính phí và trượt giá hai chiều.
- Backtest còn thiếu thuế, cổ tức, chia tách, dữ liệu giá điều chỉnh, giới hạn thanh khoản, survivorship bias và walk-forward/out-of-sample; kết quả quá khứ không dự báo tương lai.
- Chất lượng dữ liệu kiểm tra cấu trúc, trùng ngày, OHLC, volume và độ trễ; không xác nhận dữ liệu có được điều chỉnh corporate actions hay không.
- Trợ lý TAB 3 là luật offline, không phải LLM/AI cloud.
- Điểm tổng hợp TAB 6 là thang heuristic có trọng số và độ phủ dữ liệu; không phải xác suất sinh lời.
- Giá xác nhận là mốc theo dõi tham chiếu (kháng cự + 0,1 ATR), cần xác nhận bằng giá đóng cửa và khối lượng. TP/SL tiếp tục lấy từ decision_engine hiện tại.
- Chỉ dùng cho học tập, nghiên cứu và mô phỏng. Không phải tư vấn đầu tư cá nhân, không khuyến khích giao dịch bằng tiền thật.

## Kiểm thử
```bash
pytest -q
```

# CHANGELOG V2.2.0

- Giữ nguyên 5 tab cũ và bổ sung TAB 6 – Trung tâm tổng hợp phân tích Trading.
- TAB 6 tổng hợp xu hướng, động lượng, dòng tiền/thanh khoản, sức mạnh xu hướng và vị trí giá; hiển thị điểm heuristic 0–100, tín hiệu mâu thuẫn và lý do.
- TAB 6 đọc lại vùng mua, TP1, TP2, SL và R:R từ decision_engine hiện có; không tạo biểu mẫu mua/bán hay bộ tính lời/lỗ trùng lặp.
- Bổ sung MA5, MA10, MA20, MA30, MA40, MA50; giữ SMA100 và SMA200 để tương thích.
- Bổ sung HLC3 (giá bình quân High-Low-Close); giữ VWAP20 và mô tả rõ đây là VWAP cuốn 20 phiên.
- TAB 2 có biểu đồ đường giá đóng cửa, các MA, HLC3 và VWAP20; người dùng tự chọn đường muốn hiển thị.
- Nâng cấp support_resistance.py: tìm pivot high/low, gom vùng giá gần nhau, số lần phản ứng, khoảng cách %; giữ các khóa kết quả cũ.
- Giá xác nhận chỉ là mức theo dõi tham chiếu (kháng cự + 0,1 ATR); yêu cầu xác nhận bằng giá đóng cửa và khối lượng, không xem là lệnh mua.
- Bổ sung kiểm thử MA, HLC3, VWAP20, hỗ trợ/kháng cự và tổng hợp tín hiệu.
- TAB 5 Excel/CSV vẫn độc lập; không thay đổi các module mua/bán, quản trị vị thế và backtest hiện có.

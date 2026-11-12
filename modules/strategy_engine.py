from __future__ import annotations
import pandas as pd

def evaluate_strategies(enriched: pd.DataFrame) -> dict:
    if enriched is None or len(enriched)<50: return {"signals":[],"primary":"CHƯA ĐỦ DỮ LIỆU","notes":["Cần ít nhất 50 phiên."]}
    r=enriched.iloc[-1]; close,ma20,ma50,rsi,rv=[r.get(k) for k in ["close","SMA20","SMA50","RSI14","REL_VOLUME20"]]; signals=[]
    if all(pd.notna(v) for v in [close,ma20,ma50,rsi,rv]) and close>ma20>ma50 and 50<=rsi<=68 and rv>=1:
        signals.append({"strategy":"TREND FOLLOWING","signal":"ĐỦ ĐIỀU KIỆN THEO DÕI","reason":"Giá trên MA20/MA50, RSI tích cực và khối lượng xác nhận."})
    if all(pd.notna(v) for v in [close,ma20,ma50,rsi,rv]) and ma20>ma50 and .98*ma20<=close<=1.02*ma20 and rsi>=45 and rv>=.8:
        signals.append({"strategy":"PULLBACK","signal":"VÙNG QUAN SÁT","reason":"Giá kiểm tra vùng MA20 trong xu hướng tăng; chờ nến xác nhận."})
    if len(enriched)>=21:
        prior=float(enriched.high.iloc[-21:-1].max())
        if pd.notna(close) and pd.notna(rv) and close>prior and rv>=1.3:
            signals.append({"strategy":"BREAKOUT","signal":"BREAKOUT THAM CHIẾU","reason":"Đóng cửa vượt đỉnh 20 phiên trước với khối lượng tăng; cần loại trừ false breakout."})
    return {"signals":signals,"primary":signals[0]["strategy"] if signals else "CHƯA CÓ TÍN HIỆU RÕ","notes":["Tín hiệu tính tại cuối phiên, không đảm bảo khớp giá.","Tránh mua đuổi khi giá cách xa MA20.","Cần kiểm tra thị trường chung, thanh khoản và thông tin doanh nghiệp."]}

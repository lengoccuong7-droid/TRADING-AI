from __future__ import annotations
import pandas as pd
from .risk_manager import calculate_position_size
from .strategy_engine import evaluate_strategies

def make_trading_decision(df: pd.DataFrame, capital_vnd=100_000_000,
                          risk_per_trade_pct=1.0, max_allocation_pct=20.0,
                          lot_size=100, price_multiplier=1.0):
    if df is None or len(df)<50:
        return {"decision":"CHƯA ĐỦ DỮ LIỆU","reasons":["Cần tối thiểu 50 phiên hợp lệ để đánh giá xu hướng và MA50."]}
    last=df.iloc[-1]
    needed=["close","SMA20","SMA50","RSI14","ATR14","VOL_MA20","REL_VOLUME20","MACD_HIST"]
    missing=[k for k in needed if k not in df.columns or pd.isna(last.get(k))]
    if missing: return {"decision":"CHƯA ĐỦ DỮ LIỆU","reasons":["Thiếu chỉ báo: "+", ".join(missing)]}
    close,ma20,ma50,rsi,atr,relvol=[float(last[k]) for k in ["close","SMA20","SMA50","RSI14","ATR14","REL_VOLUME20"]]
    macdh=float(last.MACD_HIST); adx=last.get("ADX14")
    if close<=0 or atr<=0: return {"decision":"KHÔNG ĐỦ ĐIỀU KIỆN","reasons":["Giá hoặc ATR không hợp lệ."]}
    trend="TĂNG" if close>ma20>ma50 else ("GIẢM" if close<ma20<ma50 else "ĐI NGANG")
    momentum="TÍCH CỰC" if rsi>=50 and macdh>=0 else "YẾU"
    entry_low=max(.01,close-.5*atr); entry_high=close; stop=max(.01,close-1.5*atr); target=close+3*atr
    rr=(target-close)/(close-stop) if close>stop else 0
    strategy=evaluate_strategies(df)
    reasons=[f"Xu hướng: {trend}.",f"Động lượng: {momentum}; RSI14={rsi:.2f}.",f"Khối lượng tương đối 20 phiên: {relvol:.2f} lần.",f"Chiến lược tham chiếu: {strategy['primary']}."]
    if pd.notna(adx): reasons.append(f"ADX14={float(adx):.2f}.")
    if trend=="TĂNG" and momentum=="TÍCH CỰC" and relvol>=1 and rr>=1.5 and strategy["signals"]: decision="THEO DÕI ĐIỂM XÁC NHẬN"
    elif trend=="GIẢM": decision="KHÔNG ĐỦ ĐIỀU KIỆN THEO DÕI"
    else: decision="CHỜ XÁC NHẬN"
    sizing=calculate_position_size(capital_vnd,close,stop,risk_per_trade_pct,max_allocation_pct,lot_size,price_multiplier)
    return {"decision":decision,"trend":trend,"momentum":momentum,"reasons":reasons,
            "close":close,"buy_zone_low":entry_low,"buy_zone_high":entry_high,"stop_loss":stop,
            "target":target,"target_2":close+4.5*atr,"reward_risk":rr,
            "suggested_quantity":sizing["quantity"],"position_value":sizing["position_value"],
            "risk_budget":sizing["risk_budget"],"risk_amount":sizing["risk_amount"],
            "rel_volume20":relvol,"strategy":strategy,"sizing":sizing,
            "disclaimer":"Chỉ là tín hiệu nghiên cứu/mô phỏng từ dữ liệu lịch sử; không phải khuyến nghị mua bán hay bảo đảm kết quả."}

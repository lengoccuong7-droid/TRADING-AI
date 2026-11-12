"""Tổng hợp chỉ báo thành báo cáo giải thích được; không phát lệnh giao dịch."""
from __future__ import annotations
import math
import pandas as pd


def _num(row, key):
    value = row.get(key) if row is not None else None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def summarize_indicators(enriched: pd.DataFrame, decision: dict | None = None,
                         sr: dict | None = None) -> dict:
    decision = decision or {}
    sr = sr or {}
    if enriched is None or enriched.empty:
        return {"status": "NO_DATA", "label": "Chưa có dữ liệu", "score": None,
                "groups": [], "reasons": ["Chưa nạp dữ liệu OHLCV."], "conflicts": []}

    row = enriched.iloc[-1]
    close = _num(row, "close")
    if close is None or close <= 0:
        return {"status": "INVALID", "label": "Dữ liệu giá không hợp lệ", "score": None,
                "groups": [], "reasons": ["Giá đóng cửa cuối cùng không hợp lệ."], "conflicts": []}

    groups, reasons, conflicts = [], [], []
    scores = []

    # Trend: MA structure and price location.
    ma_keys = [f"SMA{n}" for n in (5, 10, 20, 30, 40, 50)]
    ma_values = [_num(row, k) for k in ma_keys]
    valid_ma = [(k, v) for k, v in zip(ma_keys, ma_values) if v is not None]
    if len(valid_ma) >= 3:
        ordered = [v for _, v in valid_ma]
        bullish_stack = all(ordered[i] >= ordered[i+1] for i in range(len(ordered)-1))
        bearish_stack = all(ordered[i] <= ordered[i+1] for i in range(len(ordered)-1))
        above = sum(close > v for _, v in valid_ma)
        trend_score = 85 if bullish_stack and close > ordered[-1] else 20 if bearish_stack and close < ordered[-1] else 55
        trend_signal = "Tích cực" if trend_score >= 70 else "Tiêu cực" if trend_score <= 30 else "Trung lập"
        reasons.append(f"Giá nằm trên {above}/{len(valid_ma)} đường MA đang có dữ liệu; cấu trúc MA {'xếp chồng tăng' if bullish_stack else 'xếp chồng giảm' if bearish_stack else 'chưa đồng thuận'}.")
    else:
        trend_score, trend_signal = 50, "Thiếu dữ liệu MA"
        reasons.append("Chưa đủ số phiên để đánh giá đầy đủ cấu trúc MA5–MA50.")
    groups.append({"name":"Xu hướng", "signal":trend_signal, "score":trend_score, "available":len(valid_ma) >= 3,
                   "detail":"MA5, MA10, MA20, MA30, MA40, MA50 và vị trí giá"})
    if len(valid_ma) >= 3: scores.append((trend_score, 0.30))

    # Momentum.
    rsi, macd_hist = _num(row,"RSI14"), _num(row,"MACD_HIST")
    if rsi is not None and macd_hist is not None:
        mom_score = 75 if rsi >= 50 and macd_hist >= 0 else 25 if rsi < 50 and macd_hist < 0 else 50
        mom_signal = "Tích cực" if mom_score == 75 else "Tiêu cực" if mom_score == 25 else "Mâu thuẫn"
        if (rsi >= 50) != (macd_hist >= 0): conflicts.append("RSI và MACD chưa đồng thuận.")
        reasons.append(f"RSI14={rsi:.1f}; MACD Histogram={'dương' if macd_hist >= 0 else 'âm'}.")
    else:
        mom_score, mom_signal = 50, "Thiếu dữ liệu"
    groups.append({"name":"Động lượng", "signal":mom_signal, "score":mom_score, "available":rsi is not None and macd_hist is not None,
                   "detail":"RSI14 và MACD Histogram"})
    if rsi is not None and macd_hist is not None: scores.append((mom_score, 0.25))

    # Money flow / volume.
    cmf, mfi, relvol = _num(row,"CMF20"), _num(row,"MFI14"), _num(row,"REL_VOLUME20")
    if cmf is not None and mfi is not None and relvol is not None:
        flow_score = 75 if cmf > 0 and mfi >= 50 and relvol >= 1 else 25 if cmf < 0 and mfi < 50 else 50
        flow_signal = "Tích cực" if flow_score == 75 else "Tiêu cực" if flow_score == 25 else "Chưa rõ"
        if cmf > 0 and mfi < 50 or cmf < 0 and mfi >= 50:
            conflicts.append("CMF và MFI phát tín hiệu dòng tiền khác nhau.")
        reasons.append(f"CMF20={cmf:.3f}; MFI14={mfi:.1f}; khối lượng tương đối={relvol:.2f} lần.")
    else:
        flow_score, flow_signal = 50, "Thiếu dữ liệu"
    groups.append({"name":"Dòng tiền & thanh khoản", "signal":flow_signal, "score":flow_score, "available":cmf is not None and mfi is not None and relvol is not None,
                   "detail":"CMF20, MFI14 và Relative Volume20"})
    if cmf is not None and mfi is not None and relvol is not None: scores.append((flow_score, 0.20))

    # Trend strength.
    adx, plus_di, minus_di = _num(row,"ADX14"), _num(row,"PLUS_DI14"), _num(row,"MINUS_DI14")
    if adx is not None and plus_di is not None and minus_di is not None:
        strength_score = 70 if adx >= 20 and plus_di > minus_di else 30 if adx >= 20 and minus_di > plus_di else 50
        strength_signal = "Tăng có sức mạnh" if strength_score == 70 else "Giảm có sức mạnh" if strength_score == 30 else "Xu hướng yếu/không rõ"
        reasons.append(f"ADX14={adx:.1f}; +DI={plus_di:.1f}; -DI={minus_di:.1f}.")
    else:
        strength_score, strength_signal = 50, "Thiếu dữ liệu"
    groups.append({"name":"Sức mạnh xu hướng", "signal":strength_signal, "score":strength_score, "available":adx is not None and plus_di is not None and minus_di is not None,
                   "detail":"ADX14, +DI14 và -DI14"})
    if adx is not None and plus_di is not None and minus_di is not None: scores.append((strength_score, 0.10))

    # Price location / volatility context.
    dist_sup, dist_res = sr.get("distance_to_support_pct"), sr.get("distance_to_resistance_pct")
    if dist_sup is not None and dist_res is not None:
        location = "Gần hỗ trợ" if dist_sup <= 2 else "Gần kháng cự" if dist_res <= 2 else "Trong vùng giữa"
        location_score = 65 if location == "Gần hỗ trợ" else 40 if location == "Gần kháng cự" else 50
        reasons.append(f"Cách hỗ trợ gần nhất {dist_sup:.2f}%; cách kháng cự gần nhất {dist_res:.2f}% ({location.lower()}).")
    else:
        location, location_score = "Chưa xác định", 50
    atr = _num(row,"ATR14")
    atr_pct = atr / close * 100 if atr is not None else None
    groups.append({"name":"Vị trí giá & biến động", "signal":location, "score":location_score, "available":dist_sup is not None and dist_res is not None,
                   "detail":f"Hỗ trợ/kháng cự; ATR/giá={atr_pct:.2f}%" if atr_pct is not None else "Hỗ trợ/kháng cự và ATR"})
    if dist_sup is not None and dist_res is not None: scores.append((location_score, 0.15))

    coverage = round(sum(w for _, w in scores) / 1.0 * 100, 1)
    score = round(sum(v*w for v,w in scores) / sum(w for _,w in scores), 1) if coverage >= 60 else None
    label = "Chưa đủ độ phủ chỉ báo" if score is None else "Tích cực" if score >= 65 else "Tiêu cực" if score <= 35 else "Trung lập / chờ xác nhận"
    if score is not None and len(conflicts) >= 2:
        label = "Tín hiệu mâu thuẫn – chờ xác nhận"
    elif score is not None and score >= 65 and conflicts:
        label = "Nghiêng tích cực nhưng còn mâu thuẫn"
    elif score is not None and score <= 35 and conflicts:
        label = "Nghiêng tiêu cực nhưng còn mâu thuẫn"

    # Price plan uses existing decision-engine values; confirmation requires resistance.
    atr_value = atr or 0.0
    resistance = sr.get("resistance")
    confirmation = float(resistance) + 0.10 * atr_value if resistance is not None and atr_value > 0 else None
    plan = {
        "confirmation_price": confirmation,
        "target_1": decision.get("target"),
        "target_2": decision.get("target_2"),
        "stop_loss": decision.get("stop_loss"),
        "buy_zone_low": decision.get("buy_zone_low"),
        "buy_zone_high": decision.get("buy_zone_high"),
        "reward_risk": decision.get("reward_risk"),
        "note": "TP/SL/vùng giá lấy từ decision_engine hiện có; giá xác nhận là kháng cự + 0,1 ATR để theo dõi, cần xác nhận thêm bằng đóng cửa và khối lượng."
    }
    if confirmation is None:
        plan["confirmation_note"] = "Chưa đủ dữ liệu để xác định giá xác nhận vượt kháng cự."
    else:
        plan["confirmation_note"] = "Theo dõi đóng cửa vượt mức này và khối lượng xác nhận; không xác nhận chỉ bằng giá chạm trong phiên."

    return {"status":"OK", "score":score, "coverage_pct":coverage, "label":label, "groups":groups,
            "reasons":reasons, "conflicts":conflicts, "plan":plan,
            "decision_engine":decision.get("decision", "Chưa có kết luận từ decision_engine"),
            "close":close,
            "support_resistance":sr,
            "disclaimer":"Điểm số là thang heuristic để tổng hợp tín hiệu, không phải xác suất tăng/giảm hay khuyến nghị mua bán."}

"""Phân tích vùng hỗ trợ/kháng cự từ các điểm đảo chiều gần đây.

Giữ các khóa support/resistance và distance_*_pct để tương thích code cũ.
Các vùng chỉ là tham chiếu thống kê, không phải mức giá chắc chắn.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _cluster_levels(levels, tolerance):
    if not levels:
        return []
    values = sorted(float(v) for v in levels if pd.notna(v) and float(v) > 0)
    clusters = []
    for value in values:
        if not clusters or abs(value - np.mean(clusters[-1])) > tolerance:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return [
        {"level": float(np.mean(group)), "touches": len(group),
         "low": float(min(group)), "high": float(max(group))}
        for group in clusters
    ]


def find_support_resistance(df: pd.DataFrame, window: int = 60, pivot_span: int = 2,
                            tolerance_pct: float = 0.012) -> dict:
    if df is None or len(df) < max(10, pivot_span * 2 + 3):
        return {"support": None, "resistance": None,
                "distance_to_support_pct": None, "distance_to_resistance_pct": None,
                "support_touches": 0, "resistance_touches": 0,
                "note": "Chưa đủ dữ liệu để xác định vùng hỗ trợ/kháng cự."}

    required = {"high", "low", "close"}
    if not required.issubset(df.columns):
        return {"support": None, "resistance": None,
                "note": "Thiếu cột High, Low hoặc Close."}

    x = df.tail(window).copy().reset_index(drop=True)
    high = pd.to_numeric(x["high"], errors="coerce")
    low = pd.to_numeric(x["low"], errors="coerce")
    close = float(pd.to_numeric(x["close"], errors="coerce").iloc[-1])
    if not np.isfinite(close) or close <= 0:
        return {"support": None, "resistance": None, "note": "Giá đóng cửa không hợp lệ."}

    lows, highs = [], []
    for i in range(pivot_span, len(x) - pivot_span):
        lo_slice = low.iloc[i-pivot_span:i+pivot_span+1]
        hi_slice = high.iloc[i-pivot_span:i+pivot_span+1]
        if pd.notna(low.iloc[i]) and low.iloc[i] == lo_slice.min():
            lows.append(float(low.iloc[i]))
        if pd.notna(high.iloc[i]) and high.iloc[i] == hi_slice.max():
            highs.append(float(high.iloc[i]))

    tol = max(close * tolerance_pct, 1e-9)
    support_clusters = _cluster_levels(lows, tol)
    resistance_clusters = _cluster_levels(highs, tol)
    supports = [z for z in support_clusters if z["level"] <= close]
    resistances = [z for z in resistance_clusters if z["level"] >= close]

    # Chọn vùng gần giá nhất; nếu không có pivot phù hợp, dùng biên độ cửa sổ.
    if supports:
        sup = max(supports, key=lambda z: z["level"])
    else:
        sup = {"level": float(low.min()), "touches": 1,
               "low": float(low.min()), "high": float(low.min())}
    if resistances:
        res = min(resistances, key=lambda z: z["level"])
    else:
        res = {"level": float(high.max()), "touches": 1,
               "low": float(high.max()), "high": float(high.max())}

    support, resistance = sup["level"], res["level"]
    return {
        "support": support,
        "resistance": resistance,
        "support_zone": {"low": sup["low"], "high": sup["high"]},
        "resistance_zone": {"low": res["low"], "high": res["high"]},
        "distance_to_support_pct": (close / support - 1) * 100 if support > 0 else None,
        "distance_to_resistance_pct": (resistance / close - 1) * 100 if close > 0 else None,
        "support_touches": int(sup["touches"]),
        "resistance_touches": int(res["touches"]),
        "window": int(len(x)),
        "method": "Pivot High/Low gom cụm theo sai số 1,2%; fallback biên độ cửa sổ nếu thiếu pivot.",
        "note": "Vùng tham chiếu thống kê; cần xác nhận bằng giá đóng cửa và khối lượng.",
    }

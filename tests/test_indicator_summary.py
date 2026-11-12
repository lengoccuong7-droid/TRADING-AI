import pandas as pd
from modules.indicators import add_indicators
from modules.support_resistance import find_support_resistance
from modules.indicator_summary import summarize_indicators


def sample_frame(n=180):
    dates = pd.bdate_range("2025-01-01", periods=n)
    close = pd.Series([100 + i * 0.2 + ((i % 7) - 3) * 0.15 for i in range(n)])
    return pd.DataFrame({
        "date": dates,
        "open": close - 0.1,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": [10000 + (i % 5) * 500 for i in range(n)],
        "symbol": "TEST",
    })


def test_ma_hlc3_and_vwap_columns_added():
    enriched = add_indicators(sample_frame())
    for period in (5, 10, 20, 30, 40, 50):
        assert f"SMA{period}" in enriched.columns
        assert pd.notna(enriched.iloc[-1][f"SMA{period}"])
    assert "HLC3" in enriched.columns
    assert "VWAP20" in enriched.columns
    expected_hlc3 = (enriched.iloc[-1].high + enriched.iloc[-1].low + enriched.iloc[-1].close) / 3
    assert abs(enriched.iloc[-1].HLC3 - expected_hlc3) < 1e-9


def test_support_resistance_has_distance_and_touch_counts():
    enriched = add_indicators(sample_frame())
    result = find_support_resistance(enriched)
    assert result["support"] is not None
    assert result["resistance"] is not None
    assert result["distance_to_support_pct"] is not None
    assert result["distance_to_resistance_pct"] is not None
    assert result["support_touches"] >= 1
    assert result["resistance_touches"] >= 1


def test_indicator_summary_has_groups_and_price_plan():
    enriched = add_indicators(sample_frame())
    sr = find_support_resistance(enriched)
    report = summarize_indicators(enriched, {"target": 150, "target_2": 155,
        "stop_loss": 120, "buy_zone_low": 125, "buy_zone_high": 130,
        "reward_risk": 2.0, "decision": "CHỜ XÁC NHẬN"}, sr)
    assert report["status"] == "OK"
    assert 0 <= report["score"] <= 100
    assert len(report["groups"]) == 5
    assert "confirmation_price" in report["plan"]
    assert report["plan"]["target_1"] == 150

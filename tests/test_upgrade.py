import pandas as pd
from modules.data_loader import normalize_ohlcv
from modules.data_quality import assess_data_quality
from modules.market_analysis import analyze_universe
from modules.stock_scanner import scan_universe
from modules.risk_manager import calculate_position_size
from modules.portfolio_manager import summarize_portfolio
from modules.backtest import simple_swing_backtest

def sample(n=280, symbol="AAA", drift=0.3):
    dates=pd.bdate_range("2025-01-01",periods=n)
    close=pd.Series([100+i*drift+((i%9)-4)*.25 for i in range(n)])
    return pd.DataFrame({"Date":dates,"Open":close-.1,"High":close+1,"Low":close-1,"Close":close,"Volume":[10000+(i%5)*500 for i in range(n)],"Symbol":symbol})

def test_quality_scanner_and_legacy_contract():
    data=normalize_ohlcv(sample())
    assert assess_data_quality(data)["status"] in {"OK","WARNING"}
    results=analyze_universe(data)
    assert "AAA" in results and "decision" in results["AAA"][1]
    assert not scan_universe(results,data).empty

def test_position_size_respects_caps():
    out=calculate_position_size(100_000_000,100,95,1,20,100,1)
    assert out["quantity"]%100==0
    assert out["risk_amount"]<=out["risk_budget"]+1e-9
    assert out["position_value"]<=20_000_000+1e-9

def test_portfolio_summary():
    p=pd.DataFrame([{"symbol":"AAA","quantity":100,"entry_price":10,"market_price":12,"stop_price":9}])
    s=summarize_portfolio(p,1000)
    assert s["market_value"]==1200 and s["unrealized_pnl"]==200

def test_backtest_returns_metrics():
    data=normalize_ohlcv(sample())
    out=simple_swing_backtest(data)
    assert "error" not in out
    assert "max_drawdown_pct" in out and len(out["equity_curve"])==len(data)

from __future__ import annotations
import pandas as pd

def summarize_portfolio(positions: pd.DataFrame, capital_vnd: float, price_multiplier: float=1.0) -> dict:
    if positions is None or positions.empty: return {"positions":pd.DataFrame(),"market_value":0.0,"unrealized_pnl":0.0,"exposure_pct":0.0,"total_risk":0.0}
    x=positions.copy()
    for c in ["quantity","entry_price"]:
        if c not in x: raise ValueError(f"Thiếu cột {c}")
        x[c]=pd.to_numeric(x[c],errors="coerce").fillna(0)
    if "market_price" not in x: x["market_price"]=x.entry_price
    x["market_price"]=pd.to_numeric(x.market_price,errors="coerce").fillna(x.entry_price)
    x["market_value"]=x.quantity*x.market_price*price_multiplier; x["cost_value"]=x.quantity*x.entry_price*price_multiplier
    x["unrealized_pnl"]=x.market_value-x.cost_value
    if "stop_price" in x: x["risk_value"]=(x.entry_price-pd.to_numeric(x.stop_price,errors="coerce")).clip(lower=0)*x.quantity*price_multiplier
    else: x["risk_value"]=0.0
    mv=float(x.market_value.sum()); risk=float(x.risk_value.sum())
    return {"positions":x,"market_value":mv,"unrealized_pnl":float(x.unrealized_pnl.sum()),"exposure_pct":mv/capital_vnd*100 if capital_vnd else 0,"total_risk":risk,"risk_pct_of_capital":risk/capital_vnd*100 if capital_vnd else 0}

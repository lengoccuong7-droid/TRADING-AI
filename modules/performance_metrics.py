from __future__ import annotations
import numpy as np
import pandas as pd

def calculate_performance(equity_curve, trades=None, periods_per_year=252):
    e=pd.Series(equity_curve,dtype="float64").dropna()
    if len(e)<2 or e.iloc[0]<=0: return {"max_drawdown_pct":None,"cagr_pct":None,"sharpe":None,"profit_factor":None,"expectancy_pct":None}
    rets=e.pct_change().dropna(); dd=e/e.cummax()-1; years=len(rets)/periods_per_year
    cagr=((e.iloc[-1]/e.iloc[0])**(1/years)-1)*100 if years>0 and e.iloc[-1]>=0 else None
    sharpe=float(rets.mean()/rets.std()*np.sqrt(periods_per_year)) if rets.std()>0 else None
    t=trades or []; wins=sum(float(z.get("return_pct",0)) for z in t if float(z.get("return_pct",0))>0); losses=sum(abs(float(z.get("return_pct",0))) for z in t if float(z.get("return_pct",0))<0)
    return {"max_drawdown_pct":float(dd.min()*100),"cagr_pct":cagr,"sharpe":sharpe,"profit_factor":wins/losses if losses else (float("inf") if wins else None),"expectancy_pct":float(np.mean([float(z.get("return_pct",0)) for z in t])) if t else None}

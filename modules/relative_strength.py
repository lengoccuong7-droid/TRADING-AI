from __future__ import annotations
import pandas as pd

def relative_strength(frame: pd.DataFrame, benchmark: pd.DataFrame|None=None, lookback: int=20) -> dict:
    x=frame.sort_values("date")
    if len(x)<lookback+1: return {"return_pct":None,"relative_return_pct":None,"rank_score":None}
    ret=(float(x.close.iloc[-1])/float(x.close.iloc[-lookback-1])-1)*100; br=None
    if benchmark is not None and len(benchmark)>=lookback+1:
        b=benchmark.sort_values("date"); br=(float(b.close.iloc[-1])/float(b.close.iloc[-lookback-1])-1)*100
    return {"return_pct":ret,"relative_return_pct":ret-br if br is not None else None,"rank_score":ret-br if br is not None else ret}

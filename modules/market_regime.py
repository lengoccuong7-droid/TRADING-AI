from __future__ import annotations
import pandas as pd
from .indicators import add_indicators

def assess_market_regime(data: pd.DataFrame, benchmark_symbol: str|None=None) -> dict:
    if data is None or data.empty: return {"regime":"CHƯA CÓ DỮ LIỆU","confidence":"THẤP","reasons":["Chưa có dữ liệu."]}
    symbols=set(data.symbol.astype(str)); benchmark=benchmark_symbol if benchmark_symbol in symbols else ("VNINDEX" if "VNINDEX" in symbols else None)
    if benchmark:
        e=add_indicators(data[data.symbol==benchmark].sort_values("date")); r=e.iloc[-1]
        c,m20,m50=r.get("close"),r.get("SMA20"),r.get("SMA50")
        if pd.notna(c) and pd.notna(m20) and pd.notna(m50):
            regime="TĂNG" if c>m20>m50 else ("GIẢM" if c<m20<m50 else "ĐI NGANG/CHUYỂN PHA")
            return {"regime":regime,"confidence":"TRUNG BÌNH","benchmark":benchmark,"reasons":[f"{benchmark}: Close {c:,.2f}; MA20 {m20:,.2f}; MA50 {m50:,.2f}."]}
    states=[]
    for _,f in data.groupby("symbol"):
        e=add_indicators(f.sort_values("date")); r=e.iloc[-1]
        if pd.notna(r.get("SMA20")) and pd.notna(r.get("SMA50")): states.append(r.close>r.SMA20>r.SMA50)
    if not states: return {"regime":"CHƯA ĐỦ DỮ LIỆU","confidence":"THẤP","reasons":["Cần tối thiểu 50 phiên cho benchmark hoặc các mã."]}
    breadth=sum(states)/len(states); regime="TĂNG" if breadth>=.65 else ("GIẢM" if breadth<=.35 else "PHÂN HÓA/ĐI NGANG")
    return {"regime":regime,"confidence":"THẤP" if len(states)<5 else "TRUNG BÌNH","breadth":breadth,"reasons":[f"{len(states)} mã đủ dữ liệu; breadth tăng {breadth:.1%}."]}

from __future__ import annotations
import pandas as pd

def assess_data_quality(frame: pd.DataFrame, stale_after_days: int = 7) -> dict:
    if frame is None or frame.empty:
        return {"status":"ERROR","score":0,"issues":["Không có dữ liệu."],"metrics":{}}
    x=frame.copy(); required=["date","symbol","open","high","low","close","volume"]
    missing=[c for c in required if c not in x]
    if missing: return {"status":"ERROR","score":0,"issues":[f"Thiếu cột: {missing}"],"metrics":{}}
    x["date"]=pd.to_datetime(x.date,errors="coerce")
    for c in ["open","high","low","close","volume"]: x[c]=pd.to_numeric(x[c],errors="coerce")
    nulls=int(x[required].isna().any(axis=1).sum()); dup=int(x.duplicated(["symbol","date"]).sum())
    bad=int(((x.high<x[["open","low","close"]].max(axis=1))|(x.low>x[["open","high","close"]].min(axis=1))).sum())
    neg=int((x.volume<0).sum()); last=x.date.max()
    age=(pd.Timestamp.now().normalize()-last.normalize()).days if pd.notna(last) else None
    issues=[]
    if nulls: issues.append(f"{nulls} dòng có dữ liệu trống/không hợp lệ.")
    if dup: issues.append(f"{dup} dòng trùng mã/ngày.")
    if bad: issues.append(f"{bad} dòng sai quan hệ OHLC.")
    if neg: issues.append(f"{neg} dòng có khối lượng âm.")
    if age is not None and age>stale_after_days: issues.append(f"Dữ liệu cuối cách hiện tại {age} ngày; cần kiểm tra độ trễ.")
    score=max(0,100-25*sum(bool(v) for v in [nulls,dup,bad,neg]))
    status="ERROR" if any([nulls,dup,bad,neg]) else ("WARNING" if age is not None and age>stale_after_days else "OK")
    return {"status":status,"score":score,"issues":issues or ["Không phát hiện lỗi cấu trúc cơ bản."],"metrics":{"rows":len(x),"symbols":int(x.symbol.nunique()),"start":x.date.min(),"end":last,"stale_days":age,"duplicates":dup,"invalid_rows":nulls,"invalid_ohlc":bad,"negative_volume":neg}}

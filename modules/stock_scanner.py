from __future__ import annotations
import pandas as pd
from .relative_strength import relative_strength
from .strategy_engine import evaluate_strategies

def scan_universe(results: dict, market_data: pd.DataFrame) -> pd.DataFrame:
    rows=[]; benchmark=market_data[market_data.symbol.astype(str)=="VNINDEX"] if "VNINDEX" in set(market_data.symbol.astype(str)) else None
    for symbol,(enriched,decision) in results.items():
        rs=relative_strength(enriched,benchmark); strat=evaluate_strategies(enriched)
        vol=float(decision.get("rel_volume20") or 0); score=(20 if decision.get("trend")=="TĂNG" else 8 if decision.get("trend")=="ĐI NGANG" else 0)+(20 if decision.get("momentum")=="TÍCH CỰC" else 0)+min(15,max(0,vol*10))+min(25,max(0,(rs.get("rank_score") or 0)+10))+(20 if strat["signals"] else 0)
        rows.append({"Mã":symbol,"Điểm tổng":round(score,1),"Xu hướng":decision.get("trend"),"Động lượng":decision.get("momentum"),"RS 20 phiên (%)":rs.get("return_pct"),"Vượt benchmark (%)":rs.get("relative_return_pct"),"KL tương đối":decision.get("rel_volume20"),"Chiến lược":strat["primary"],"Tín hiệu":decision.get("decision")})
    return pd.DataFrame(rows).sort_values("Điểm tổng",ascending=False).reset_index(drop=True) if rows else pd.DataFrame()

from __future__ import annotations
import pandas as pd
from .indicators import add_indicators
from .performance_metrics import calculate_performance

def simple_swing_backtest(frame, fee_pct=0.15, slippage_pct=0.10, initial_capital=1.0):
    """Long-only educational simulation. Close signal executes at next session open.
    Equity is marked at each session close; costs apply on both entry and exit.
    """
    x=add_indicators(frame).sort_values("date").reset_index(drop=True)
    if len(x)<55: return {"error":"Cần ít nhất 55 phiên để có MA50 và giai đoạn mô phỏng."}
    cash=float(initial_capital); shares=0.0; entry_fill=None; entry_date=None; trades=[]; equity=[float(initial_capital)]
    fee=fee_pct/100; slip=slippage_pct/100
    for i in range(1,len(x)):
        prev=x.iloc[i-1]; row=x.iloc[i]; op=float(row.open); close=float(row.close)
        valid=all(pd.notna(prev.get(k)) for k in ["SMA20","SMA50","RSI14","MACD_HIST"])
        if valid:
            buy=prev.close>prev.SMA20>prev.SMA50 and prev.RSI14>=50 and prev.MACD_HIST>0
            sell=prev.close<prev.SMA20 or prev.RSI14<45 or prev.close<prev.SMA50
            if shares==0 and buy:
                fill=op*(1+slip); shares=cash/(fill*(1+fee)); cash=0.0; entry_fill=fill; entry_date=row.date
            elif shares>0 and sell:
                fill=op*(1-slip); cash=shares*fill*(1-fee)
                net_return=(cash/(shares*entry_fill*(1+fee))-1)*100 if entry_fill else 0
                trades.append({"entry_date":str(entry_date),"exit_date":str(row.date),"entry":entry_fill,"exit":fill,"return_pct":net_return})
                shares=0.0; entry_fill=None; entry_date=None
        equity.append(cash+shares*close)
    final_value=cash+shares*float(x.iloc[-1].close)
    total=(final_value/initial_capital-1)*100
    metrics=calculate_performance(equity,trades)
    return {"total_return_pct":total,"closed_trades":len(trades),"win_rate_pct":sum(t["return_pct"]>0 for t in trades)/len(trades)*100 if trades else None,
            "trades":trades,"equity_curve":equity,"open_position":bool(shares),"final_equity":final_value,
            "max_drawdown_pct":metrics["max_drawdown_pct"],"cagr_pct":metrics["cagr_pct"],"sharpe":metrics["sharpe"],
            "profit_factor":metrics["profit_factor"],"expectancy_pct":metrics["expectancy_pct"],
            "assumptions":{"fee_pct_each_side":fee_pct,"slippage_pct_each_side":slippage_pct,"execution":"Tín hiệu ở close phiên trước, khớp giả định tại open phiên sau."},
            "note":"Mô phỏng giáo dục; chưa bao gồm thuế, cổ tức, chia tách, giới hạn thanh khoản, giá điều chỉnh và các sự kiện doanh nghiệp. Vị thế còn mở được định giá theo close cuối kỳ, không tự thanh lý."}

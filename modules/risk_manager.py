from __future__ import annotations
import math

def calculate_position_size(capital_vnd, entry_price, stop_price, risk_pct=1.0, max_allocation_pct=20.0, lot_size=100, price_multiplier=1.0):
    vals=[capital_vnd,entry_price,stop_price,price_multiplier]
    if any(not math.isfinite(float(v)) for v in vals) or capital_vnd<=0 or entry_price<=0 or stop_price<=0 or stop_price>=entry_price or price_multiplier<=0 or lot_size<=0:
        return {"quantity":0,"risk_budget":0.0,"position_value":0.0,"risk_amount":0.0,"status":"INPUT_INVALID"}
    budget=capital_vnd*max(0,float(risk_pct))/100; per_share=(entry_price-stop_price)*price_multiplier
    qty=min(int(budget/per_share),int((capital_vnd*max(0,float(max_allocation_pct))/100)/(entry_price*price_multiplier)))
    qty=max(0,qty); qty=(qty//int(lot_size))*int(lot_size); value=qty*entry_price*price_multiplier; risk=qty*per_share
    return {"quantity":qty,"risk_budget":budget,"position_value":value,"risk_amount":risk,"risk_pct_of_capital":risk/capital_vnd*100,"allocation_pct":value/capital_vnd*100,"status":"OK" if qty else "NO_POSITION"}

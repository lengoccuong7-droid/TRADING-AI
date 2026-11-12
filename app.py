import streamlit as st
import pandas as pd
from config import APP_NAME, DEFAULT_CAPITAL_VND, APP_VERSION
from modules.data_loader import load_market_file
from modules.market_analysis import analyze_universe
from modules.backtest import simple_swing_backtest
from modules.ai_analyzer import run_ai_analysis
from modules import tab5_excel
from modules.data_quality import assess_data_quality
from modules.market_regime import assess_market_regime
from modules.stock_scanner import scan_universe
from modules.strategy_engine import evaluate_strategies
from modules.portfolio_manager import summarize_portfolio
from modules.support_resistance import find_support_resistance
from modules.indicator_summary import summarize_indicators

st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")
st.markdown("""
<style>
/* Sticky tab navigation; content panels remain independently scrollable. */
.stTabs [data-baseweb="tab-list"] {
 position: sticky; top: 0; z-index: 1000; background: var(--background-color);
 overflow-x: auto; flex-wrap: nowrap; white-space: nowrap;
 padding: .45rem .15rem; border-bottom: 1px solid rgba(128,128,128,.25);
 scrollbar-width: thin;
}
.stTabs [data-baseweb="tab"] { flex: 0 0 auto; white-space: nowrap; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1rem; }
@media (max-width: 700px) {
 .stTabs [data-baseweb="tab"] { padding-left: .55rem; padding-right: .55rem; font-size: .82rem; }
}
</style>
""", unsafe_allow_html=True)
st.title(APP_NAME)
st.caption(f"Phiên bản V{APP_VERSION} · Công cụ nghiên cứu dữ liệu lịch sử và mô phỏng chiến lược · Không đặt lệnh · Không bảo đảm lợi nhuận")

if "market_data" not in st.session_state: st.session_state.market_data=None
if "analysis" not in st.session_state: st.session_state.analysis=None

tabs=st.tabs(["TAB 1 · Dữ liệu & Tổng quan","TAB 2 · Chỉ báo","TAB 3 · Trợ lý phân tích","TAB 4 · Scanner, Swing & Danh mục","TAB 5 · Excel/CSV độc lập","TAB 6 · Tổng hợp Trading"])

with tabs[0]:
    st.subheader("Nạp dữ liệu OHLCV")
    up=st.file_uploader("Chọn file dữ liệu",type=["csv","xlsx","xls","json","txt","parquet","pdf","docx"],key="market_upload")
    c1,c2=st.columns(2)
    hint=c1.text_input("Mã cổ phiếu nếu file chỉ có một mã",value="")
    sheet=c2.text_input("Tên sheet Excel (để trống = sheet đầu tiên)",value="")
    if up:
        try:
            data=load_market_file(up,sheet_name=sheet if sheet.strip() else 0,symbol_hint=hint or None)
            st.session_state.market_data=data; st.session_state.analysis=None
            st.success(f"Đọc thành công {len(data):,} dòng, {data.symbol.nunique()} mã.")
        except Exception as e: st.error(f"Không thể nạp dữ liệu: {e}")
    data=st.session_state.market_data
    if data is not None:
        quality=assess_data_quality(data)
        regime=assess_market_regime(data)
        m1,m2,m3,m4=st.columns(4)
        m1.metric("Chất lượng cấu trúc",f"{quality['score']}/100")
        m2.metric("Trạng thái dữ liệu",quality["status"])
        m3.metric("Số mã",data.symbol.nunique())
        m4.metric("Trạng thái thị trường",regime["regime"])
        for issue in quality["issues"]:
            (st.warning if quality["status"]!="OK" else st.info)(issue)
        st.write("**Đánh giá thị trường:**", " ".join(regime.get("reasons",[])))
        st.caption("Nếu không có VNINDEX, trạng thái thị trường được ước lượng từ tỷ lệ mã nằm trên MA20 và MA50; độ tin cậy thấp hơn.")
        st.write(f"Khoảng dữ liệu: {data.date.min().date()} → {data.date.max().date()}")
        st.dataframe(data,use_container_width=True)
        st.download_button("Tải dữ liệu đã chuẩn hóa CSV",data.to_csv(index=False).encode("utf-8-sig"),"ohlcv_normalized.csv","text/csv")

with tabs[1]:
    st.subheader("Chỉ báo kỹ thuật")
    data=st.session_state.market_data
    if data is None: st.info("Hãy nạp dữ liệu ở TAB 1.")
    else:
        results=st.session_state.analysis
        if results is None: results=analyze_universe(data); st.session_state.analysis=results
        symbols=list(results.keys()); selected=st.selectbox("Chọn mã",symbols,key="indicator_symbol")
        enriched,decision=results[selected]; latest=enriched.iloc[-1]
        cols=st.columns(5)
        for col,key in zip(cols,["SMA20","SMA50","SMA200","RSI14","ATR14"]):
            val=latest.get(key); col.metric(key,"Chưa đủ dữ liệu" if pd.isna(val) else f"{val:,.2f}")
        show=[c for c in ["date","open","high","low","close","volume","SMA20","SMA50","SMA200","EMA20","RSI14","MACD","MACD_SIGNAL","MACD_HIST","ATR14","ADX14","REL_VOLUME20","BB_UPPER","BB_LOWER"] if c in enriched]
        st.dataframe(enriched[show].tail(60),use_container_width=True)
        st.markdown("#### Biểu đồ giá và các đường trung bình")
        available_lines = [c for c in ["close", "SMA5", "SMA10", "SMA20", "SMA30", "SMA40", "SMA50", "HLC3", "VWAP20"] if c in enriched.columns]
        default_lines = [c for c in ["close", "SMA5", "SMA20", "SMA50", "VWAP20"] if c in available_lines]
        selected_lines = st.multiselect("Chọn đường hiển thị", available_lines, default=default_lines, key=f"ma_lines_{selected}")
        if selected_lines:
            chart_data = enriched.tail(180).set_index("date")[selected_lines].copy()
            chart_data = chart_data.rename(columns={"close":"Giá đóng cửa", "HLC3":"Giá bình quân HLC3", "VWAP20":"VWAP 20 phiên"})
            st.line_chart(chart_data, use_container_width=True)
        else:
            st.info("Chọn ít nhất một đường để hiển thị biểu đồ.")
        st.caption("MA dùng giá đóng cửa; HLC3 = (High + Low + Close)/3; VWAP20 là giá bình quân gia quyền khối lượng trong 20 phiên gần nhất. Các chỉ báo cần đủ lịch sử mới hiển thị; NaN không tự động thay bằng 0.")

with tabs[2]:
    st.subheader("Trợ lý phân tích và phản biện")
    data=st.session_state.market_data
    if data is None: st.info("Hãy nạp dữ liệu ở TAB 1.")
    else:
        results=st.session_state.analysis
        if results is None: results=analyze_universe(data); st.session_state.analysis=results
        for symbol,(enriched,decision) in results.items():
            with st.expander(f"{symbol} · {decision.get('decision','')}",expanded=False):
                st.write("**Xu hướng:**",decision.get("trend","Chưa xác định")," · **Động lượng:**",decision.get("momentum","Chưa xác định"))
                for reason in decision.get("reasons",[]): st.write("•",reason)
                strat=evaluate_strategies(enriched)
                st.write("**Chiến lược tham chiếu:**",strat["primary"])
                for s in strat["signals"]: st.write(f"- {s['strategy']}: {s['signal']} — {s['reason']}")
                analyst=run_ai_analysis(enriched,symbol)
                st.markdown("**Diễn giải offline theo quy tắc**")
                st.write(analyst["summary"])
                st.write("Yếu tố tích cực:",analyst["bullish"] or ["Chưa có xác nhận rõ."])
                st.write("Rủi ro/phản biện:",analyst["risks"] or ["Chưa phát hiện theo bộ luật hiện tại."])
                st.write("Quan sát:",analyst.get("observations",[]))
                st.caption("Đây không phải mô hình AI tạo sinh, không dự báo chắc chắn và không phải khuyến nghị mua/bán.")

with tabs[3]:
    st.subheader("Scanner đa mã, mô phỏng Swing và quản trị danh mục")
    data=st.session_state.market_data
    if data is None: st.info("Hãy nạp dữ liệu ở TAB 1.")
    else:
        results=st.session_state.analysis
        c1,c2,c3,c4=st.columns(4)
        capital=c1.number_input("Vốn mô phỏng (VND)",min_value=1_000_000,value=DEFAULT_CAPITAL_VND,step=1_000_000)
        risk=c2.number_input("Ngân sách rủi ro/mã (%)",min_value=.1,max_value=5.0,value=1.0,step=.1)
        allocation=c3.number_input("Tỷ trọng tối đa/mã (%)",min_value=1.0,max_value=100.0,value=20.0,step=1.0)
        lot=c4.number_input("Bước lô",min_value=1,value=100,step=1)
        if st.button("Tính lại phân tích toàn bộ mã"):
            results=analyze_universe(data,capital_vnd=capital,risk_pct=risk,max_alloc_pct=allocation,lot_size=int(lot))
            st.session_state.analysis=results
        if results is None: results=analyze_universe(data); st.session_state.analysis=results
        scanner=scan_universe(results,data)
        st.markdown("**Bảng xếp hạng nghiên cứu**")
        st.dataframe(scanner,use_container_width=True)
        st.download_button("Xuất bảng Scanner CSV",scanner.to_csv(index=False).encode("utf-8-sig"),"scanner_ranking.csv","text/csv")
        st.caption("Điểm tổng là thang điểm heuristic nội bộ để sắp xếp dữ liệu, không phải xác suất tăng giá hay khuyến nghị đầu tư.")
        st.markdown("**Mô phỏng chiến lược trên một mã**")
        sym=st.selectbox("Mã để mô phỏng",list(data.symbol.unique()),key="bt_symbol")
        if st.button("Chạy backtest"):
            bt=simple_swing_backtest(data[data.symbol==sym].copy())
            if "error" in bt: st.warning(bt["error"])
            else:
                k1,k2,k3,k4=st.columns(4)
                k1.metric("Tổng lợi nhuận mô phỏng",f"{bt['total_return_pct']:.2f}%")
                k2.metric("Max Drawdown",f"{bt['max_drawdown_pct']:.2f}%")
                k3.metric("Số giao dịch đóng",bt["closed_trades"])
                k4.metric("Win rate", "—" if bt["win_rate_pct"] is None else f"{bt['win_rate_pct']:.1f}%")
                st.json({k:v for k,v in bt.items() if k!="equity_curve"})
                st.line_chart(pd.DataFrame({"Equity mô phỏng":bt["equity_curve"]}))
        st.markdown("**Theo dõi danh mục (nhập CSV)**")
        st.caption("Cột bắt buộc: symbol, quantity, entry_price. Cột tùy chọn: market_price, stop_price. Không kết nối tài khoản hay gửi lệnh.")
        pf=st.file_uploader("Tải CSV vị thế mô phỏng",type=["csv"],key="portfolio_upload")
        if pf:
            try:
                positions=pd.read_csv(pf); summary=summarize_portfolio(positions,capital)
                p1,p2,p3=st.columns(3); p1.metric("Giá trị thị trường",f"{summary['market_value']:,.0f} VND")
                p2.metric("Lãi/lỗ chưa thực hiện",f"{summary['unrealized_pnl']:,.0f} VND")
                p3.metric("Tỷ trọng vốn",f"{summary['exposure_pct']:.1f}%")
                st.write(f"Rủi ro tới stop tham chiếu: {summary['total_risk']:,.0f} VND ({summary['risk_pct_of_capital']:.2f}% vốn)")
                st.dataframe(summary["positions"],use_container_width=True)
            except Exception as e: st.error(f"Không đọc được danh mục: {e}")

with tabs[4]:
    st.subheader("Công cụ Excel/CSV độc lập")
    st.caption("TAB này độc lập với lõi phân tích; không sửa dữ liệu thị trường và không phụ thuộc Scanner.")
    file5=st.file_uploader("Tải Excel/CSV để xử lý riêng",type=["csv","txt","xlsx","xls"],key="tab5_upload")
    if file5:
        try:
            sheet5=st.text_input("Sheet TAB 5 (tên hoặc chỉ số)",value="0"); arg=int(sheet5) if sheet5.isdigit() else sheet5
            table=tab5_excel.read_table(file5,arg); st.dataframe(table,use_container_width=True)
            c1,c2=st.columns(2)
            c1.download_button("Xuất CSV",tab5_excel.to_csv_bytes(table),"tab5_export.csv","text/csv")
            c2.download_button("Xuất Excel",tab5_excel.to_excel_bytes(table),"tab5_export.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e: st.error(f"Lỗi TAB 5: {e}")


# =========================================================
# TAB 6 · TRUNG TÂM TỔNG HỢP PHÂN TÍCH VÀ HỖ TRỢ QUYẾT ĐỊNH
# =========================================================
with tabs[5]:
    st.subheader("Trung tâm tổng hợp phân tích Trading")
    st.caption("Tổng hợp chỉ báo, vùng giá và kế hoạch tham chiếu từ các module hiện có; không tạo chức năng mua/bán trùng lặp.")
    data = st.session_state.market_data
    if data is None:
        st.info("Hãy nạp dữ liệu OHLCV tại TAB 1 trước.")
    else:
        results = st.session_state.analysis
        if results is None:
            results = analyze_universe(data)
            st.session_state.analysis = results
        symbols = list(results.keys())
        selected_summary = st.selectbox("Chọn mã cần tổng hợp", symbols, key="summary_symbol")
        enriched_summary, decision_summary = results[selected_summary]
        sr_summary = find_support_resistance(enriched_summary)
        report = summarize_indicators(enriched_summary, decision_summary, sr_summary)

        if report.get("score") is not None:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Điểm tổng hợp", "Chưa đủ" if report["score"] is None else f"{report['score']:.1f}/100")
            m2.metric("Kết luận kỹ thuật", report["label"])
            m3.metric("Độ phủ chỉ báo", f"{report.get('coverage_pct', 0):.0f}%")
            m4.metric("Xu hướng", decision_summary.get("trend", "Chưa rõ"))
            m5.metric("Động lượng", decision_summary.get("momentum", "Chưa rõ"))

            regime_summary = assess_market_regime(data)
            st.caption(f"Bối cảnh thị trường chung: {regime_summary.get('regime', 'Chưa xác định')} · " + " ".join(regime_summary.get("reasons", [])))
            st.markdown("### 1. Đánh giá theo nhóm chỉ báo")
            group_table = pd.DataFrame(report["groups"])[["name", "signal", "score", "available", "detail"]]
            st.dataframe(group_table, use_container_width=True, hide_index=True)

            left, right = st.columns(2)
            with left:
                st.markdown("**Các dữ kiện ủng hộ kết luận**")
                for reason in report.get("reasons", []):
                    st.write("•", reason)
            with right:
                st.markdown("**Tín hiệu mâu thuẫn cần lưu ý**")
                if report.get("conflicts"):
                    for conflict in report["conflicts"]:
                        st.warning(conflict)
                else:
                    st.success("Chưa phát hiện mâu thuẫn lớn trong các nhóm chỉ báo đang đủ dữ liệu.")

            st.markdown("### 2. Bản đồ vùng giá")
            p = report.get("plan", {})
            sr = report.get("support_resistance", {})
            pcols = st.columns(4)
            pcols[0].metric("Giá đóng cửa", f"{report['close']:,.2f}")
            pcols[1].metric("Hỗ trợ gần", "—" if sr.get("support") is None else f"{sr['support']:,.2f}")
            pcols[2].metric("Kháng cự gần", "—" if sr.get("resistance") is None else f"{sr['resistance']:,.2f}")
            pcols[3].metric("Giá xác nhận tham chiếu", "—" if p.get("confirmation_price") is None else f"{p['confirmation_price']:,.2f}")
            st.caption(p.get("confirmation_note", ""))
            if sr.get("support") is not None and sr.get("resistance") is not None:
                st.write(f"Khoảng cách tới hỗ trợ: **{sr.get('distance_to_support_pct', float('nan')):.2f}%** · Khoảng cách tới kháng cự: **{sr.get('distance_to_resistance_pct', float('nan')):.2f}%**")
                st.caption(f"Số lần phản ứng pivot tham chiếu — hỗ trợ: {sr.get('support_touches', 0)} · kháng cự: {sr.get('resistance_touches', 0)}. {sr.get('method', '')}")

            st.markdown("### 3. Kịch bản giá tham chiếu")
            plan_table = pd.DataFrame([
                {"Mốc giá": "Vùng mua thấp (module cũ)", "Giá": p.get("buy_zone_low")},
                {"Mốc giá": "Vùng mua cao (module cũ)", "Giá": p.get("buy_zone_high")},
                {"Mốc giá": "Giá xác nhận theo dõi", "Giá": p.get("confirmation_price")},
                {"Mốc giá": "Chốt lời mục tiêu 1", "Giá": p.get("target_1")},
                {"Mốc giá": "Chốt lời mục tiêu 2", "Giá": p.get("target_2")},
                {"Mốc giá": "Cắt lỗ tham chiếu", "Giá": p.get("stop_loss")},
            ])
            plan_table["Giá"] = plan_table["Giá"].map(lambda v: "Chưa có dữ liệu" if v is None or pd.isna(v) else f"{float(v):,.2f}")
            st.dataframe(plan_table, use_container_width=True, hide_index=True)
            st.write("**Tỷ lệ R:R từ decision_engine:**", "Chưa xác định" if p.get("reward_risk") is None else f"{float(p['reward_risk']):.2f}")
            st.caption(p.get("note", ""))

            st.markdown("### 4. Kết luận và điều kiện theo dõi")
            st.info(f"**Kết luận từ bộ máy quyết định hiện tại:** {report.get('decision_engine', 'Chưa có')}.\n\n**Kết luận tổng hợp:** {report['label']}.")
            st.write("**Điều kiện xác nhận:** chờ giá đóng cửa vượt vùng xác nhận tham chiếu, đồng thời khối lượng và động lượng không suy yếu rõ rệt.")
            st.write("**Điều kiện vô hiệu:** đánh giá lại kịch bản nếu giá đóng cửa xuyên thủng vùng hỗ trợ hoặc chạm ngưỡng cắt lỗ do module hiện tại tính toán.")
            st.caption(report.get("disclaimer", ""))
        else:
            st.warning("Chưa đủ dữ liệu để tổng hợp chỉ báo cho mã này.")

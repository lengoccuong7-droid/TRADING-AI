
# =========================================================
# BOT TRADER SWING MULTI
# APP.PY - V2.2.1
# GIỮ 6 TAB - TAB 5 ĐỘC LẬP
# =========================================================

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import (
    APP_NAME,
    DEFAULT_CAPITAL_VND,
    APP_VERSION,
)

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


# =========================================================
# 1. CẤU HÌNH GIAO DIỆN
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>

    .stTabs [data-baseweb="tab-list"] {
        position: sticky;
        top: 0;
        z-index: 1000;
        background: var(--background-color);
        overflow-x: auto;
        flex-wrap: nowrap;
        white-space: nowrap;
        padding: .45rem .15rem;
        border-bottom: 1px solid rgba(128,128,128,.25);
        scrollbar-width: thin;
    }

    .stTabs [data-baseweb="tab"] {
        flex: 0 0 auto;
        white-space: nowrap;
    }

    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }

    @media (max-width: 700px) {

        .stTabs [data-baseweb="tab"] {
            padding-left: .55rem;
            padding-right: .55rem;
            font-size: .82rem;
        }

    }

    div[data-testid="stDataFrame"] {
        width: 100%;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


st.title(APP_NAME)

st.caption(
    f"Phiên bản V{APP_VERSION} · "
    "Công cụ nghiên cứu dữ liệu lịch sử và mô phỏng chiến lược · "
    "Không đặt lệnh · Không bảo đảm lợi nhuận"
)


# =========================================================
# 2. KHỞI TẠO SESSION STATE
# =========================================================

DEFAULT_STATE = {
    "market_data": None,
    "analysis": None,

    # Tab 5 độc lập
    "tab5_table": None,
    "tab5_source_name": "",
    "tab5_paste_text": "",
    "tab5_status": "",
    "tab5_old_preview": None,

    # Trạng thái Tab 1
    "market_data_name": "",
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 3. HÀM HỖ TRỢ
# =========================================================

def get_analysis_results(data):

    """
    Chỉ phân tích khi chưa có kết quả hoặc dữ liệu vừa thay đổi.
    """

    if data is None or data.empty:
        return None

    if st.session_state.analysis is None:

        st.session_state.analysis = analyze_universe(data)

    return st.session_state.analysis


def safe_number(value, digits=2):

    if value is None:
        return "—"

    try:

        if pd.isna(value):
            return "—"

        return f"{float(value):,.{digits}f}"

    except (TypeError, ValueError):
        return str(value)


def show_error(message, error):

    st.error(f"{message}: {error}")


# =========================================================
# 4. TẠO 6 TAB
# =========================================================

tabs = st.tabs([
    "TAB 1 · Dữ liệu & Tổng quan",
    "TAB 2 · Chỉ báo",
    "TAB 3 · Trợ lý phân tích",
    "TAB 4 · Scanner, Swing & Danh mục",
    "TAB 5 · Excel/CSV độc lập",
    "TAB 6 · Tổng hợp Trading",
])


# =========================================================
# TAB 1 · DỮ LIỆU & TỔNG QUAN
# =========================================================

with tabs[0]:

    st.subheader("Nạp dữ liệu OHLCV")

    up = st.file_uploader(
        "Chọn file dữ liệu",
        type=[
            "csv",
            "xlsx",
            "xls",
            "txt",
        ],
        key="market_upload",
    )

    c1, c2 = st.columns(2)

    hint = c1.text_input(
        "Mã cổ phiếu nếu file chỉ có một mã",
        value="",
        key="market_symbol_hint",
    )

    sheet = c2.text_input(
        "Tên sheet Excel (để trống = sheet đầu tiên)",
        value="",
        key="market_sheet_name",
    )

    # -----------------------------------------------------
    # ĐỌC DỮ LIỆU
    # -----------------------------------------------------

    if up is not None:

        try:

            filename = up.name.lower()

            sheet_arg = 0

            if filename.endswith((".xlsx", ".xls")):

                if sheet.strip().isdigit():

                    sheet_arg = int(sheet.strip())

                elif sheet.strip():

                    sheet_arg = sheet.strip()

            # Tất cả định dạng đi qua cùng một bộ chuẩn hóa.
            new_data = load_market_file(
                up,
                sheet_name=sheet_arg,
                symbol_hint=hint.strip().upper() or None,
            )

            if new_data is None or new_data.empty:

                raise ValueError(
                    "File không có dữ liệu hợp lệ."
                )

            # Chỉ cập nhật sau khi đọc và kiểm tra thành công.
            st.session_state.market_data = new_data.copy()

            st.session_state.market_data_name = up.name

            # Xóa kết quả phân tích cũ.
            st.session_state.analysis = None

            st.success(
                f"Đọc thành công {len(new_data):,} dòng, "
                f"{new_data['symbol'].nunique()} mã."
            )

        except Exception as e:

            show_error(
                "Không thể nạp dữ liệu",
                e,
            )

    data = st.session_state.market_data

    # -----------------------------------------------------
    # HIỂN THỊ DỮ LIỆU
    # -----------------------------------------------------

    if data is None:

        st.info(
            "Hãy tải dữ liệu OHLCV lên để bắt đầu phân tích."
        )

    else:

        st.caption(
            f"File hiện tại: "
            f"{st.session_state.market_data_name or 'Dữ liệu đã nạp'}"
        )

        try:

            quality = assess_data_quality(data)

            regime = assess_market_regime(data)

            m1, m2, m3, m4 = st.columns(4)

            m1.metric(
                "Chất lượng cấu trúc",
                f"{quality['score']}/100",
            )

            m2.metric(
                "Trạng thái dữ liệu",
                quality["status"],
            )

            m3.metric(
                "Số mã",
                data["symbol"].nunique(),
            )

            m4.metric(
                "Trạng thái thị trường",
                regime["regime"],
            )

            for issue in quality.get("issues", []):

                if quality["status"] != "OK":

                    st.warning(issue)

                else:

                    st.info(issue)

            st.write(
                "**Đánh giá thị trường:**",
                " ".join(regime.get("reasons", [])),
            )

            st.caption(
                "Nếu không có VNINDEX, trạng thái thị trường "
                "có thể được ước lượng từ tỷ lệ mã nằm trên MA20 "
                "và MA50; độ tin cậy thấp hơn."
            )

        except Exception as e:

            st.warning(
                f"Không thể tạo báo cáo chất lượng dữ liệu: {e}"
            )

        # Khoảng thời gian
        if "date" in data.columns:

            valid_dates = data["date"].dropna()

            if not valid_dates.empty:

                st.write(
                    f"Khoảng dữ liệu: "
                    f"{valid_dates.min().date()} → "
                    f"{valid_dates.max().date()}"
                )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Tải dữ liệu đã chuẩn hóa CSV",
            data=data.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="ohlcv_normalized.csv",
            mime="text/csv",
            key="download_market_normalized",
        )


# =========================================================
# TAB 2 · CHỈ BÁO
# =========================================================

with tabs[1]:

    st.subheader("Chỉ báo kỹ thuật")

    data = st.session_state.market_data

    if data is None:

        st.info(
            "Hãy nạp dữ liệu ở TAB 1."
        )

    else:

        try:

            results = get_analysis_results(data)

            if not results:

                st.warning(
                    "Chưa có kết quả phân tích."
                )

            else:

                symbols = list(results.keys())

                selected = st.selectbox(
                    "Chọn mã",
                    symbols,
                    key="indicator_symbol",
                )

                enriched, decision = results[selected]

                latest = enriched.iloc[-1]

                cols = st.columns(5)

                for col, key in zip(
                    cols,
                    [
                        "SMA20",
                        "SMA50",
                        "SMA200",
                        "RSI14",
                        "ATR14",
                    ],
                ):

                    val = latest.get(key)

                    col.metric(
                        key,
                        safe_number(val),
                    )

                show = [
                    c for c in [
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "SMA20",
                        "SMA50",
                        "SMA200",
                        "EMA20",
                        "RSI14",
                        "MACD",
                        "MACD_SIGNAL",
                        "MACD_HIST",
                        "ATR14",
                        "ADX14",
                        "REL_VOLUME20",
                        "BB_UPPER",
                        "BB_LOWER",
                    ]
                    if c in enriched.columns
                ]

                st.dataframe(
                    enriched[show].tail(60),
                    use_container_width=True,
                    hide_index=True,
                )

                # Biểu đồ đường trung bình
                st.markdown(
                    "#### Biểu đồ giá và các đường trung bình"
                )

                available_lines = [
                    c for c in [
                        "close",
                        "SMA5",
                        "SMA10",
                        "SMA20",
                        "SMA30",
                        "SMA40",
                        "SMA50",
                        "HLC3",
                        "VWAP20",
                    ]
                    if c in enriched.columns
                ]

                default_lines = [
                    c for c in [
                        "close",
                        "SMA5",
                        "SMA20",
                        "SMA50",
                        "VWAP20",
                    ]
                    if c in available_lines
                ]

                selected_lines = st.multiselect(
                    "Chọn đường hiển thị",
                    available_lines,
                    default=default_lines,
                    key=f"ma_lines_{selected}",
                )

                if selected_lines:

                    chart_data = (
                        enriched.tail(180)
                        .set_index("date")[selected_lines]
                        .copy()
                    )

                    chart_data = chart_data.rename(
                        columns={
                            "close": "Giá đóng cửa",
                            "HLC3": "Giá bình quân HLC3",
                            "VWAP20": "VWAP 20 phiên",
                        }
                    )

                    st.line_chart(
                        chart_data,
                        use_container_width=True,
                    )

                else:

                    st.info(
                        "Chọn ít nhất một đường để hiển thị biểu đồ."
                    )

                st.caption(
                    "MA dùng giá đóng cửa; HLC3 = (High + Low + Close)/3; "
                    "VWAP20 là giá bình quân gia quyền khối lượng trong "
                    "20 phiên gần nhất. Chỉ báo cần đủ lịch sử mới hiển thị."
                )

        except Exception as e:

            show_error(
                "Lỗi phân tích chỉ báo",
                e,
            )


# =========================================================
# TAB 3 · TRỢ LÝ PHÂN TÍCH
# =========================================================

with tabs[2]:

    st.subheader(
        "Trợ lý phân tích và phản biện"
    )

    data = st.session_state.market_data

    if data is None:

        st.info(
            "Hãy nạp dữ liệu ở TAB 1."
        )

    else:

        try:

            results = get_analysis_results(data)

            if not results:

                st.warning(
                    "Chưa có kết quả phân tích."
                )

            else:

                for symbol, (
                    enriched,
                    decision
                ) in results.items():

                    with st.expander(
                        f"{symbol} · {decision.get('decision', '')}",
                        expanded=False,
                    ):

                        st.write(
                            "**Xu hướng:**",
                            decision.get(
                                "trend",
                                "Chưa xác định",
                            ),
                            " · **Động lượng:**",
                            decision.get(
                                "momentum",
                                "Chưa xác định",
                            ),
                        )

                        for reason in decision.get(
                            "reasons",
                            [],
                        ):

                            st.write("•", reason)

                        strat = evaluate_strategies(
                            enriched
                        )

                        st.write(
                            "**Chiến lược tham chiếu:**",
                            strat["primary"],
                        )

                        for signal in strat["signals"]:

                            st.write(
                                f"- {signal['strategy']}: "
                                f"{signal['signal']} — "
                                f"{signal['reason']}"
                            )

                        analyst = run_ai_analysis(
                            enriched,
                            symbol,
                        )

                        st.markdown(
                            "**Diễn giải offline theo quy tắc**"
                        )

                        st.write(
                            analyst["summary"]
                        )

                        st.write(
                            "Yếu tố tích cực:",
                            analyst.get(
                                "bullish",
                                ["Chưa có xác nhận rõ."],
                            ),
                        )

                        st.write(
                            "Rủi ro/phản biện:",
                            analyst.get(
                                "risks",
                                ["Chưa phát hiện theo bộ luật hiện tại."],
                            ),
                        )

                        st.write(
                            "Quan sát:",
                            analyst.get(
                                "observations",
                                [],
                            ),
                        )

                        st.caption(
                            "Đây là diễn giải theo quy tắc hiện có, "
                            "không phải mô hình dự báo chắc chắn."
                        )

        except Exception as e:

            show_error(
                "Lỗi trợ lý phân tích",
                e,
            )


# =========================================================
# TAB 4 · SCANNER, SWING & DANH MỤC
# =========================================================

with tabs[3]:

    st.subheader(
        "Scanner đa mã, mô phỏng Swing và quản trị danh mục"
    )

    data = st.session_state.market_data

    if data is None:

        st.info(
            "Hãy nạp dữ liệu ở TAB 1."
        )

    else:

        try:

            c1, c2, c3, c4 = st.columns(4)

            capital = c1.number_input(
                "Vốn mô phỏng (VND)",
                min_value=1_000_000,
                value=int(DEFAULT_CAPITAL_VND),
                step=1_000_000,
                key="capital_simulation",
            )

            risk = c2.number_input(
                "Ngân sách rủi ro/mã (%)",
                min_value=.1,
                max_value=5.0,
                value=1.0,
                step=.1,
                key="risk_simulation",
            )

            allocation = c3.number_input(
                "Tỷ trọng tối đa/mã (%)",
                min_value=1.0,
                max_value=100.0,
                value=20.0,
                step=1.0,
                key="allocation_simulation",
            )

            lot = c4.number_input(
                "Bước lô",
                min_value=1,
                value=100,
                step=1,
                key="lot_simulation",
            )

            if st.button(
                "Tính lại phân tích toàn bộ mã",
                key="recalculate_universe",
            ):

                results = analyze_universe(
                    data,
                    capital_vnd=capital,
                    risk_pct=risk,
                    max_alloc_pct=allocation,
                    lot_size=int(lot),
                )

                st.session_state.analysis = results

            results = get_analysis_results(data)

            if not results:

                st.warning(
                    "Không có kết quả phân tích để Scanner."
                )

            else:

                scanner = scan_universe(
                    results,
                    data,
                )

                st.markdown(
                    "**Bảng xếp hạng nghiên cứu**"
                )

                st.dataframe(
                    scanner,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Xuất bảng Scanner CSV",
                    data=scanner.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="scanner_ranking.csv",
                    mime="text/csv",
                    key="download_scanner",
                )

                st.caption(
                    "Điểm tổng là thang điểm heuristic nội bộ, "
                    "không phải xác suất tăng giá."
                )

            st.divider()

            # Backtest
            st.markdown(
                "**Mô phỏng chiến lược trên một mã**"
            )

            sym = st.selectbox(
                "Mã để mô phỏng",
                list(data["symbol"].dropna().unique()),
                key="bt_symbol",
            )

            if st.button(
                "Chạy backtest",
                key="run_backtest",
            ):

                bt = simple_swing_backtest(
                    data[
                        data["symbol"] == sym
                    ].copy()
                )

                if "error" in bt:

                    st.warning(bt["error"])

                else:

                    k1, k2, k3, k4 = st.columns(4)

                    k1.metric(
                        "Tổng lợi nhuận mô phỏng",
                        f"{bt['total_return_pct']:.2f}%",
                    )

                    k2.metric(
                        "Max Drawdown",
                        f"{bt['max_drawdown_pct']:.2f}%",
                    )

                    k3.metric(
                        "Số giao dịch đóng",
                        bt["closed_trades"],
                    )

                    k4.metric(
                        "Win rate",
                        "—"
                        if bt["win_rate_pct"] is None
                        else f"{bt['win_rate_pct']:.1f}%",
                    )

                    st.json({
                        key: value
                        for key, value in bt.items()
                        if key != "equity_curve"
                    })

                    st.line_chart(
                        pd.DataFrame({
                            "Equity mô phỏng": bt["equity_curve"]
                        })
                    )

            st.divider()

            # Danh mục
            st.markdown(
                "**Theo dõi danh mục (nhập CSV)**"
            )

            st.caption(
                "Cột bắt buộc: symbol, quantity, entry_price. "
                "Cột tùy chọn: market_price, stop_price. "
                "Không kết nối tài khoản hay gửi lệnh."
            )

            pf = st.file_uploader(
                "Tải CSV vị thế mô phỏng",
                type=["csv"],
                key="portfolio_upload",
            )

            if pf is not None:

                try:

                    positions = pd.read_csv(pf)

                    summary = summarize_portfolio(
                        positions,
                        capital,
                    )

                    p1, p2, p3 = st.columns(3)

                    p1.metric(
                        "Giá trị thị trường",
                        f"{summary['market_value']:,.0f} VND",
                    )

                    p2.metric(
                        "Lãi/lỗ chưa thực hiện",
                        f"{summary['unrealized_pnl']:,.0f} VND",
                    )

                    p3.metric(
                        "Tỷ trọng vốn",
                        f"{summary['exposure_pct']:.1f}%",
                    )

                    st.write(
                        f"Rủi ro tới stop tham chiếu: "
                        f"{summary['total_risk']:,.0f} VND "
                        f"({summary['risk_pct_of_capital']:.2f}% vốn)"
                    )

                    st.dataframe(
                        summary["positions"],
                        use_container_width=True,
                        hide_index=True,
                    )

                except Exception as e:

                    show_error(
                        "Không đọc được danh mục",
                        e,
                    )

        except Exception as e:

            show_error(
                "Lỗi Tab 4",
                e,
            )


# =========================================================
# TAB 5 · EXCEL / CSV ĐỘC LẬP
# =========================================================

with tabs[4]:

    st.subheader(
        "Công cụ Excel / CSV độc lập"
    )

    st.caption(
        "Tab 5 hoạt động độc lập với dữ liệu thị trường. "
        "Dữ liệu tại đây không tự động chuyển sang Tab 1 "
        "và không ảnh hưởng đến các tab phân tích."
    )

    # -----------------------------------------------------
    # A. NHẬP DỮ LIỆU TRỰC TIẾP
    # -----------------------------------------------------

    st.markdown(
        "### 1. Dán dữ liệu trực tiếp"
    )

    st.caption(
        "Sao chép vùng dữ liệu từ Excel rồi dán vào ô bên dưới. "
        "Các cột phân cách bằng Tab được nhận diện tự động."
    )

    pasted_text = st.text_area(
        "Ô nhập dữ liệu",
        value=st.session_state.tab5_paste_text,
        height=180,
        placeholder=(
            "Date\tOpen\tHigh\tLow\tClose\tVolume\n"
            "2026-01-01\t100\t110\t95\t105\t1000000\n"
            "2026-01-02\t105\t115\t102\t112\t1200000"
        ),
        key="tab5_text_input",
    )

    st.session_state.tab5_paste_text = pasted_text

    c1, c2, c3 = st.columns(3)

    delimiter_choice = c1.selectbox(
        "Dấu phân cách",
        [
            "Tự nhận diện",
            "Tab",
            "Dấu phẩy (,)",
            "Chấm phẩy (;)",
            "Dấu |",
        ],
        key="tab5_delimiter",
    )

    has_header = c2.checkbox(
        "Dòng đầu là tiêu đề",
        value=True,
        key="tab5_header",
    )

    if delimiter_choice == "Tab":

        delimiter = "\t"

    elif delimiter_choice == "Dấu phẩy (,)" :

        delimiter = ","

    elif delimiter_choice == "Chấm phẩy (;)" :

        delimiter = ";"

    elif delimiter_choice == "Dấu |":

        delimiter = "|"

    else:

        delimiter = "Tự nhận diện"

    if c3.button(
        "Tách dữ liệu thành bảng",
        key="tab5_parse_button",
        use_container_width=True,
    ):

        try:

            parsed = tab5_excel.parse_pasted_text(
                pasted_text,
                delimiter=delimiter,
                header=has_header,
            )

            st.session_state.tab5_table = parsed.copy()

            st.session_state.tab5_source_name = ""

            st.session_state.tab5_old_preview = None

            st.session_state.tab5_status = (
                f"Đã tách thành công "
                f"{len(parsed):,} dòng và "
                f"{len(parsed.columns)} cột."
            )

        except Exception as e:

            show_error(
                "Không thể tách dữ liệu",
                e,
            )

    if st.session_state.tab5_status:

        st.success(
            st.session_state.tab5_status
        )

    st.divider()

    # -----------------------------------------------------
    # B. NHẬP FILE EXCEL / CSV / TXT
    # -----------------------------------------------------

    st.markdown(
        "### 2. Nhập file có sẵn"
    )

    uploaded5 = st.file_uploader(
        "Chọn file Excel / CSV / TXT",
        type=[
            "csv",
            "txt",
            "xlsx",
            "xls",
        ],
        key="tab5_upload",
    )

    if uploaded5 is not None:

        try:

            if uploaded5.name.lower().endswith(
                (".xlsx", ".xls")
            ):

                sheet5 = st.text_input(
                    "Sheet TAB 5 (tên hoặc chỉ số)",
                    value="0",
                    key="tab5_sheet_name",
                )

                if sheet5.strip().isdigit():

                    sheet_arg = int(sheet5.strip())

                else:

                    sheet_arg = sheet5.strip() or 0

            else:

                sheet_arg = 0

            table = tab5_excel.read_table(
                uploaded5,
                sheet_name=sheet_arg,
            )

            st.session_state.tab5_table = table.copy()

            st.session_state.tab5_source_name = uploaded5.name

            st.session_state.tab5_old_preview = None

            st.session_state.tab5_status = (
                f"Đã đọc file {uploaded5.name}: "
                f"{len(table):,} dòng."
            )

            st.success(
                st.session_state.tab5_status
            )

        except Exception as e:

            show_error(
                "Lỗi đọc file TAB 5",
                e,
            )

    st.divider()

    # -----------------------------------------------------
    # C. BẢNG DỮ LIỆU CÓ THỂ CHỈNH SỬA
    # -----------------------------------------------------

    st.markdown(
        "### 3. Bảng dữ liệu có thể chỉnh sửa"
    )

    table5 = st.session_state.tab5_table

    if table5 is not None:

        st.caption(
            "Có thể sửa từng ô, thêm dòng hoặc xóa dòng. "
            "Bảng chỉ thuộc Tab 5."
        )

        edited_table5 = st.data_editor(
            table5,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="tab5_editor",
        )

        # Bản đang hiển thị trong phiên làm việc.
        table5 = edited_table5.copy()

        if st.button(
            "Xác nhận bảng đã chỉnh sửa",
            key="tab5_confirm_editor",
            use_container_width=True,
        ):

            st.session_state.tab5_table = table5.copy()

            st.success(
                "Đã cập nhật bảng dữ liệu trong Tab 5."
            )

        st.divider()

        # -------------------------------------------------
        # D. CHUẨN HÓA VÀ KIỂM TRA
        # -------------------------------------------------

        st.markdown(
            "### 4. Chuẩn hóa và kiểm tra dữ liệu"
        )

        if st.button(
            "Chuẩn hóa tên cột",
            key="tab5_normalize_button",
        ):

            try:

                normalized, mapping = (
                    tab5_excel.normalize_columns(
                        table5
                    )
                )

                st.session_state.tab5_table = normalized.copy()

                st.success(
                    "Đã chuẩn hóa tên cột."
                )

                if mapping:

                    st.write(
                        "Ánh xạ tên cột:",
                        mapping,
                    )

            except Exception as e:

                show_error(
                    "Lỗi chuẩn hóa",
                    e,
                )

        table5 = st.session_state.tab5_table

        if table5 is not None:

            try:

                issues = tab5_excel.validate_table(
                    table5
                )

                if issues:

                    st.warning(
                        "Các vấn đề cần kiểm tra:"
                    )

                    for issue in issues:

                        st.write("•", issue)

                else:

                    st.success(
                        "Không phát hiện lỗi theo các quy tắc kiểm tra hiện có."
                    )

            except Exception as e:

                show_error(
                    "Lỗi kiểm tra bảng",
                    e,
                )

        st.divider()

        # -------------------------------------------------
        # E. XUẤT FILE
        # -------------------------------------------------

        st.markdown(
            "### 5. Xuất dữ liệu"
        )

        col_csv, col_excel = st.columns(2)

        try:

            csv_bytes = tab5_excel.to_csv_bytes(
                table5
            )

            excel_bytes = tab5_excel.to_excel_bytes(
                table5
            )

            col_csv.download_button(
                "Tải CSV",
                data=csv_bytes,
                file_name="tab5_export.csv",
                mime="text/csv",
                key="tab5_download_csv",
                use_container_width=True,
            )

            col_excel.download_button(
                "Tải Excel",
                data=excel_bytes,
                file_name="tab5_export.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key="tab5_download_excel",
                use_container_width=True,
            )

        except Exception as e:

            show_error(
                "Không thể xuất file",
                e,
            )

        st.divider()

        # -------------------------------------------------
        # F. LƯU FILE MỚI
        # -------------------------------------------------

        st.markdown(
            "### 6. Lưu thành file mới"
        )

        new_filename5 = st.text_input(
            "Tên file mới",
            value="du_lieu_tab5",
            key="tab5_new_filename",
        )

        new_format5 = st.selectbox(
            "Định dạng lưu",
            ["xlsx", "csv"],
            key="tab5_new_format",
        )

        if st.button(
            "Lưu file mới",
            key="tab5_save_new",
            use_container_width=True,
        ):

            try:

                saved_path = tab5_excel.save_new_file(
                    table5,
                    new_filename5,
                    new_format5,
                )

                st.success(
                    f"Đã lưu file: {saved_path.name}"
                )

            except Exception as e:

                show_error(
                    "Không thể lưu file mới",
                    e,
                )

        st.divider()

        # -------------------------------------------------
        # G. CẬP NHẬT FILE CŨ
        # -------------------------------------------------

        st.markdown(
            "### 7. Cập nhật file đã lưu"
        )

        try:

            saved_files5 = tab5_excel.list_saved_files()

        except Exception as e:

            saved_files5 = []

            show_error(
                "Không thể đọc danh sách file Tab 5",
                e,
            )

        if saved_files5:

            old_file5 = st.selectbox(
                "Chọn file cần cập nhật",
                saved_files5,
                key="tab5_old_file",
            )

            st.caption(
                "Chương trình tạo bản sao lưu trước khi cập nhật. "
                "Khi trùng khóa, dữ liệu mới được ưu tiên."
            )

            if st.button(
                "Xem cấu trúc file cũ",
                key="tab5_preview_old",
            ):

                try:

                    old_df5 = tab5_excel.load_saved_file(
                        old_file5
                    )

                    st.session_state.tab5_old_preview = old_df5.copy()

                except Exception as e:

                    show_error(
                        "Không đọc được file cũ",
                        e,
                    )

            if st.session_state.tab5_old_preview is not None:

                st.dataframe(
                    st.session_state.tab5_old_preview,
                    use_container_width=True,
                    hide_index=True,
                )

            try:

                old_data_for_keys = tab5_excel.load_saved_file(
                    old_file5
                )

                key_options = [
                    column
                    for column in table5.columns
                    if column in old_data_for_keys.columns
                ]

            except Exception as e:

                key_options = []

                show_error(
                    "Không thể xác định cột khóa",
                    e,
                )

            if key_options:

                default_keys = [
                    column
                    for column in ["symbol", "date"]
                    if column in key_options
                ]

                selected_keys5 = st.multiselect(
                    "Chọn cột khóa để nhận diện dòng trùng",
                    key_options,
                    default=default_keys,
                    key="tab5_update_keys",
                )

            else:

                selected_keys5 = []

                st.warning(
                    "Không tìm thấy cột chung giữa file mới và file cũ."
                )

            if st.button(
                "Cập nhật file cũ",
                key="tab5_update_old",
                use_container_width=True,
            ):

                try:

                    if not selected_keys5:

                        raise ValueError(
                            "Bạn cần chọn ít nhất một cột khóa."
                        )

                    (
                        merged5,
                        duplicate_count5,
                        backup5,
                    ) = tab5_excel.update_saved_file(
                        table5,
                        old_file5,
                        keys=selected_keys5,
                    )

                    st.success(
                        f"Đã cập nhật {old_file5}. "
                        f"Số dòng trùng được thay thế: "
                        f"{duplicate_count5}. "
                        f"Bản sao lưu: {backup5.name}"
                    )

                    st.dataframe(
                        merged5,
                        use_container_width=True,
                        hide_index=True,
                    )

                except Exception as e:

                    show_error(
                        "Không thể cập nhật file",
                        e,
                    )

        else:

            st.info(
                "Chưa có file nào được lưu trong Tab 5."
            )

    else:

        st.info(
            "Hãy dán dữ liệu hoặc tải file lên để bắt đầu."
        )

    st.caption(
        "Dữ liệu Tab 5 được lưu riêng trong thư mục "
        "data/tab5_saved. Không tự động đưa vào market_data "
        "và không làm thay đổi dữ liệu Tab 1."
    )


# =========================================================
# TAB 6 · TRUNG TÂM TỔNG HỢP PHÂN TÍCH
# =========================================================

with tabs[5]:

    st.subheader(
        "Trung tâm tổng hợp phân tích Trading"
    )

    st.caption(
        "Tổng hợp chỉ báo, vùng giá và kế hoạch tham chiếu "
        "từ các module hiện có."
    )

    data = st.session_state.market_data

    if data is None:

        st.info(
            "Hãy nạp dữ liệu OHLCV tại TAB 1 trước."
        )

    else:

        try:

            results = get_analysis_results(data)

            if not results:

                st.warning(
                    "Chưa có kết quả phân tích."
                )

            else:

                symbols = list(results.keys())

                selected_summary = st.selectbox(
                    "Chọn mã cần tổng hợp",
                    symbols,
                    key="summary_symbol",
                )

                (
                    enriched_summary,
                    decision_summary,
                ) = results[selected_summary]

                sr_summary = find_support_resistance(
                    enriched_summary
                )

                report = summarize_indicators(
                    enriched_summary,
                    decision_summary,
                    sr_summary,
                )

                if report.get("score") is not None:

                    m1, m2, m3, m4, m5 = st.columns(5)

                    m1.metric(
                        "Điểm tổng hợp",
                        f"{report['score']:.1f}/100",
                    )

                    m2.metric(
                        "Kết luận kỹ thuật",
                        report["label"],
                    )

                    m3.metric(
                        "Độ phủ chỉ báo",
                        f"{report.get('coverage_pct', 0):.0f}%",
                    )

                    m4.metric(
                        "Xu hướng",
                        decision_summary.get(
                            "trend",
                            "Chưa rõ",
                        ),
                    )

                    m5.metric(
                        "Động lượng",
                        decision_summary.get(
                            "momentum",
                            "Chưa rõ",
                        ),
                    )

                    regime_summary = assess_market_regime(
                        data
                    )

                    st.caption(
                        f"Bối cảnh thị trường chung: "
                        f"{regime_summary.get('regime', 'Chưa xác định')} · "
                        + " ".join(
                            regime_summary.get("reasons", [])
                        )
                    )

                    # -------------------------------------
                    # NHÓM CHỈ BÁO
                    # -------------------------------------

                    st.markdown(
                        "### 1. Đánh giá theo nhóm chỉ báo"
                    )

                    group_table = pd.DataFrame(
                        report["groups"]
                    )

                    group_columns = [
                        column
                        for column in [
                            "name",
                            "signal",
                            "score",
                            "available",
                            "detail",
                        ]
                        if column in group_table.columns
                    ]

                    st.dataframe(
                        group_table[group_columns],
                        use_container_width=True,
                        hide_index=True,
                    )

                    left, right = st.columns(2)

                    with left:

                        st.markdown(
                            "**Các dữ kiện ủng hộ kết luận**"
                        )

                        for reason in report.get(
                            "reasons",
                            [],
                        ):

                            st.write("•", reason)

                    with right:

                        st.markdown(
                            "**Tín hiệu mâu thuẫn cần lưu ý**"
                        )

                        conflicts = report.get(
                            "conflicts",
                            [],
                        )

                        if conflicts:

                            for conflict in conflicts:

                                st.warning(conflict)

                        else:

                            st.success(
                                "Chưa phát hiện mâu thuẫn lớn "
                                "trong các nhóm chỉ báo đủ dữ liệu."
                            )

                    # -------------------------------------
                    # VÙNG GIÁ
                    # -------------------------------------

                    st.markdown(
                        "### 2. Bản đồ vùng giá"
                    )

                    plan = report.get("plan", {})

                    sr = report.get(
                        "support_resistance",
                        {},
                    )

                    pcols = st.columns(4)

                    pcols[0].metric(
                        "Giá đóng cửa",
                        safe_number(report.get("close")),
                    )

                    pcols[1].metric(
                        "Hỗ trợ gần",
                        safe_number(sr.get("support")),
                    )

                    pcols[2].metric(
                        "Kháng cự gần",
                        safe_number(sr.get("resistance")),
                    )

                    pcols[3].metric(
                        "Giá xác nhận tham chiếu",
                        safe_number(
                            plan.get("confirmation_price")
                        ),
                    )

                    st.caption(
                        plan.get("confirmation_note", "")
                    )

                    if (
                        sr.get("support") is not None
                        and sr.get("resistance") is not None
                    ):

                        st.write(
                            f"Khoảng cách tới hỗ trợ: "
                            f"**{safe_number(sr.get('distance_to_support_pct'))}%** "
                            f"· Khoảng cách tới kháng cự: "
                            f"**{safe_number(sr.get('distance_to_resistance_pct'))}%**"
                        )

                        st.caption(
                            f"Số lần phản ứng pivot tham chiếu — "
                            f"hỗ trợ: {sr.get('support_touches', 0)} · "
                            f"kháng cự: {sr.get('resistance_touches', 0)}. "
                            f"{sr.get('method', '')}"
                        )

                    # -------------------------------------
                    # KỊCH BẢN GIÁ
                    # -------------------------------------

                    st.markdown(
                        "### 3. Kịch bản giá tham chiếu"
                    )

                    plan_table = pd.DataFrame([
                        {
                            "Mốc giá": "Vùng mua thấp (module cũ)",
                            "Giá": plan.get("buy_zone_low"),
                        },
                        {
                            "Mốc giá": "Vùng mua cao (module cũ)",
                            "Giá": plan.get("buy_zone_high"),
                        },
                        {
                            "Mốc giá": "Giá xác nhận theo dõi",
                            "Giá": plan.get("confirmation_price"),
                        },
                        {
                            "Mốc giá": "Chốt lời mục tiêu 1",
                            "Giá": plan.get("target_1"),
                        },
                        {
                            "Mốc giá": "Chốt lời mục tiêu 2",
                            "Giá": plan.get("target_2"),
                        },
                        {
                            "Mốc giá": "Cắt lỗ tham chiếu",
                            "Giá": plan.get("stop_loss"),
                        },
                    ])

                    plan_table["Giá"] = plan_table["Giá"].map(
                        lambda value:
                            "Chưa có dữ liệu"
                            if value is None or pd.isna(value)
                            else f"{float(value):,.2f}"
                    )

                    st.dataframe(
                        plan_table,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.write(
                        "**Tỷ lệ R:R từ decision_engine:**",
                        "Chưa xác định"
                        if plan.get("reward_risk") is None
                        else f"{float(plan['reward_risk']):.2f}",
                    )

                    st.caption(
                        plan.get("note", "")
                    )

                    # -------------------------------------
                    # KẾT LUẬN
                    # -------------------------------------

                    st.markdown(
                        "### 4. Kết luận và điều kiện theo dõi"
                    )

                    st.info(
                        f"**Kết luận từ bộ máy quyết định hiện tại:** "
                        f"{report.get('decision_engine', 'Chưa có')}.\n\n"
                        f"**Kết luận tổng hợp:** {report['label']}."
                    )

                    st.write(
                        "**Điều kiện xác nhận:** theo dõi giá đóng cửa "
                        "so với vùng xác nhận tham chiếu, đồng thời "
                        "đánh giá khối lượng và động lượng."
                    )

                    st.write(
                        "**Điều kiện vô hiệu:** đánh giá lại kịch bản "
                        "nếu giá đóng cửa xuyên thủng vùng hỗ trợ "
                        "hoặc chạm ngưỡng rủi ro do module hiện tại tính toán."
                    )

                    st.caption(
                        report.get("disclaimer", "")
                    )

                else:

                    st.warning(
                        "Chưa đủ dữ liệu để tổng hợp chỉ báo cho mã này."
                    )

        except Exception as e:

            show_error(
                "Lỗi Trung tâm tổng hợp",
                e,
            )

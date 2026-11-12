
# =========================================================
# MODULE: DATA_LOADER.PY
# BOT TRADER SWING MULTI - V2.2.1
#
# Chức năng:
# 1. Đọc Excel / CSV / TXT
# 2. Nhận diện tiêu đề Việt / Anh
# 3. Chuẩn hóa OHLCV
# 4. Giữ các cột dữ liệu bổ sung
# 5. Kiểm tra dữ liệu OHLC
# 6. Báo chi tiết từng dòng lỗi
# 7. Tương thích prepare_market_data()
#
# KHÔNG tự sửa giá, không tự xóa dòng lỗi.
# =========================================================

from __future__ import annotations

from pathlib import Path
import io
import re
import unicodedata

import pandas as pd


# =========================================================
# 1. DANH SÁCH TÊN CỘT ĐƯỢC CHẤP NHẬN
# =========================================================

ALIASES = {

    "date": [
        "date",
        "datetime",
        "time",
        "trading date",
        "tradingdate",
        "ngay",
        "ngày",
        "ngay giao dich",
        "ngày giao dịch",
        "thoi gian",
        "thời gian",
    ],

    "symbol": [
        "symbol",
        "ticker",
        "stock",
        "stock code",
        "code",
        "ma",
        "mã",
        "ma co phieu",
        "mã cổ phiếu",
        "ma ck",
        "mã ck",
    ],

    "open": [
        "open",
        "o",
        "mo cua",
        "mở cửa",
        "gia mo cua",
        "giá mở cửa",
        "gia dau ngay",
        "giá đầu ngày",
    ],

    "high": [
        "high",
        "h",
        "cao nhat",
        "cao nhất",
        "gia cao nhat",
        "giá cao nhất",
        "gia cao",
        "giá cao",
    ],

    "low": [
        "low",
        "l",
        "thap nhat",
        "thấp nhất",
        "gia thap nhat",
        "giá thấp nhất",
        "gia thap",
        "giá thấp",
    ],

    "close": [
        "close",
        "c",
        "closing price",
        "dong cua",
        "đóng cửa",
        "gia dong cua",
        "giá đóng cửa",
        "gia ket phien",
        "giá kết phiên",
        "gia dieu chinh",
        "giá điều chỉnh",
    ],

    "volume": [
        "volume",
        "vol",
        "v",
        "khoi luong",
        "khối lượng",
        "khoi luong giao dich",
        "khối lượng giao dịch",
        "kl",
        "klgd",
    ],

    "change_pct": [
        "% thay doi",
        "% thay đổi",
        "thay doi",
        "thay đổi",
        "change",
        "change %",
        "change percent",
        "pct change",
        "percent change",
        "percent_change",
    ],
}


REQUIRED_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


# =========================================================
# 2. CHUẨN HÓA TÊN CỘT
# =========================================================

def _remove_accents(value):

    value = str(value)

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    return "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )


def _norm(value):

    value = _remove_accents(value)

    value = value.strip().lower()

    value = re.sub(
        r"[%]",
        " percent ",
        value,
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def normalize_columns(df):

    """
    Chuẩn hóa tên cột.

    Trả về:
        normalized_df
        mapping
    """

    if df is None:

        raise ValueError(
            "Không có bảng dữ liệu đầu vào."
        )

    if df.empty:

        raise ValueError(
            "Bảng dữ liệu đang trống."
        )

    normalized = df.copy()

    normalized.columns = [
        str(column).strip()
        for column in normalized.columns
    ]

    alias_map = {}

    for standard_name, aliases in ALIASES.items():

        for alias in aliases:

            alias_map[_norm(alias)] = standard_name

    rename = {}

    mapping = {}

    for original in normalized.columns:

        normalized_name = _norm(original)

        if normalized_name in alias_map:

            standard_name = alias_map[normalized_name]

            if standard_name in rename.values():

                raise ValueError(
                    f"Có nhiều cột cùng được nhận diện là "
                    f"'{standard_name}'. "
                    f"Vui lòng kiểm tra tiêu đề: {original}"
                )

            rename[original] = standard_name

            mapping[original] = standard_name

    normalized = normalized.rename(
        columns=rename
    )

    return normalized, mapping


# =========================================================
# 3. ĐỌC FILE
# =========================================================

def _read_csv_bytes(raw):

    """
    Đọc CSV với nhiều kiểu mã hóa.
    Tự nhận diện dấu phân cách phổ biến.
    """

    errors = []

    for encoding in [
        "utf-8-sig",
        "utf-8",
        "cp1258",
        "latin1",
    ]:

        try:

            bio = io.BytesIO(raw)

            df = pd.read_csv(
                bio,
                encoding=encoding,
                sep=None,
                engine="python",
                skipinitialspace=True,
            )

            if df.empty:

                raise ValueError(
                    "File CSV không có dữ liệu."
                )

            return df

        except Exception as error:

            errors.append(
                f"{encoding}: {error}"
            )

    raise ValueError(
        "Không thể đọc file CSV.\n"
        + "\n".join(errors)
    )


def _read_txt_bytes(raw):

    """
    Đọc TXT:
    - Tab
    - Dấu phẩy
    - Chấm phẩy
    - Khoảng trắng
    """

    errors = []

    for encoding in [
        "utf-8-sig",
        "utf-8",
        "cp1258",
        "latin1",
    ]:

        try:

            text = raw.decode(
                encoding
            )

            text = text.strip()

            if not text:

                raise ValueError(
                    "File TXT trống."
                )

            # Tự nhận diện dấu phân cách
            first_line = next(
                line
                for line in text.splitlines()
                if line.strip()
            )

            if "\t" in first_line:

                separator = "\t"

            elif ";" in first_line:

                separator = ";"

            elif "," in first_line:

                separator = ","

            else:

                separator = r"\s+"

            df = pd.read_csv(
                io.StringIO(text),
                sep=separator,
                engine="python",
                skipinitialspace=True,
            )

            if df.empty:

                raise ValueError(
                    "Không tìm thấy dữ liệu trong TXT."
                )

            return df

        except Exception as error:

            errors.append(
                f"{encoding}: {error}"
            )

    raise ValueError(
        "Không thể đọc file TXT.\n"
        + "\n".join(errors)
    )


def _read_file(
    name,
    raw,
    sheet_name=0,
):

    ext = Path(name).suffix.lower()

    if ext in [".csv"]:

        return _read_csv_bytes(raw)

    if ext in [".txt"]:

        return _read_txt_bytes(raw)

    if ext in [".xlsx", ".xls"]:

        try:

            return pd.read_excel(
                io.BytesIO(raw),
                sheet_name=sheet_name,
            )

        except Exception as error:

            raise ValueError(
                f"Không đọc được sheet Excel '{sheet_name}': "
                f"{error}"
            ) from error

    if ext == ".json":

        return pd.read_json(
            io.BytesIO(raw)
        )

    if ext == ".parquet":

        return pd.read_parquet(
            io.BytesIO(raw)
        )

    raise ValueError(
        f"Định dạng chưa được hỗ trợ: {ext}"
    )


# =========================================================
# 4. CHUYỂN ĐỔI SỐ
# =========================================================

def _parse_number(value):

    """
    Chuyển số có dấu phân cách hàng nghìn.

    Ví dụ:
        10,644       -> 10644
        10.644       -> 10644
        10.644,50    -> 10644.50
        10,644.50    -> 10644.50
        10644        -> 10644

    Với chuỗi chỉ có một dấu phân cách và đúng 3 chữ số
    phía sau, ưu tiên hiểu đó là dấu hàng nghìn theo cách
    ghi số phổ biến trong dữ liệu chứng khoán Việt Nam.
    """

    if pd.isna(value):

        return float("nan")

    if isinstance(
        value,
        (int, float),
    ):

        return float(value)

    text = str(value).strip()

    if text == "" or text.lower() in [
        "nan",
        "none",
        "null",
        "-",
    ]:

        return float("nan")

    text = text.replace(
        "\u00a0",
        "",
    )

    text = text.replace(
        " ",
        "",
    )

    text = text.replace(
        "%",
        "",
    )

    # Loại bỏ ký hiệu tiền tệ
    text = re.sub(
        r"(?i)(vnd|vnđ|đ|dong)",
        "",
        text,
    )

    # Giữ lại chữ số, dấu âm và dấu phân cách
    text = re.sub(
        r"[^0-9,.\-+]",
        "",
        text,
    )

    if text in ["", "-", "+"]:

        return float("nan")

    negative = text.startswith("-")

    text = text.lstrip("+-")

    if "," in text and "." in text:

        # Dấu xuất hiện sau cùng được coi là dấu thập phân.
        if text.rfind(",") > text.rfind("."):

            text = text.replace(".", "")

            text = text.replace(",", ".")

        else:

            text = text.replace(",", "")

    elif "," in text:

        parts = text.split(",")

        if (
            len(parts) == 2
            and len(parts[1]) == 3
            and parts[0].isdigit()
        ):

            text = "".join(parts)

        elif len(parts) == 2:

            text = parts[0] + "." + parts[1]

        else:

            text = "".join(parts)

    elif "." in text:

        parts = text.split(".")

        if (
            len(parts) == 2
            and len(parts[1]) == 3
            and parts[0].isdigit()
        ):

            text = "".join(parts)

        elif len(parts) > 2:

            text = "".join(parts[:-1]) + "." + parts[-1]

    try:

        number = float(text)

        return -number if negative else number

    except ValueError:

        return float("nan")


# =========================================================
# 5. CHUẨN HÓA NGÀY
# =========================================================

def _parse_dates(series):

    """
    Hỗ trợ:
    - DD/MM/YYYY
    - YYYY-MM-DD
    - DD-MM-YYYY
    """

    text = series.astype(str).str.strip()

    result = pd.to_datetime(
        text,
        dayfirst=True,
        errors="coerce",
    )

    return result


# =========================================================
# 6. KIỂM TRA DỮ LIỆU OHLCV
# =========================================================

def _validate_ohlcv(df):

    errors = []

    # Kiểm tra thiếu dữ liệu
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Thiếu cột bắt buộc: "
            + ", ".join(missing)
        )

    # Ngày không hợp lệ
    bad_date = df["date"].isna()

    if bad_date.any():

        errors.append(
            f"Có {int(bad_date.sum())} dòng ngày giao dịch "
            f"không hợp lệ."
        )

    # Giá và khối lượng bị thiếu
    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    bad_numeric = df[
        numeric_columns
    ].isna().any(axis=1)

    if bad_numeric.any():

        errors.append(
            f"Có {int(bad_numeric.sum())} dòng giá hoặc "
            f"khối lượng không phải số hợp lệ."
        )

    # Chỉ kiểm tra quan hệ OHLC trên các dòng đủ dữ liệu
    valid_rows = ~(
        df["date"].isna()
        | df[numeric_columns].isna().any(axis=1)
    )

    check = df.loc[
        valid_rows
    ]

    # Giá phải lớn hơn 0
    bad_price = (
        check[
            ["open", "high", "low", "close"]
        ] <= 0
    ).any(axis=1)

    if bad_price.any():

        errors.append(
            f"Có {int(bad_price.sum())} dòng có giá "
            f"nhỏ hơn hoặc bằng 0."
        )

    # Khối lượng không được âm
    bad_volume = check["volume"] < 0

    if bad_volume.any():

        errors.append(
            f"Có {int(bad_volume.sum())} dòng có "
            f"khối lượng âm."
        )

    # High phải >= Open, Low, Close
    invalid_high = (
        check["high"]
        < check[
            ["open", "low", "close"]
        ].max(axis=1)
    )

    # Low phải <= Open, High, Close
    invalid_low = (
        check["low"]
        > check[
            ["open", "high", "close"]
        ].min(axis=1)
    )

    invalid_ohlc = (
        invalid_high
        | invalid_low
    )

    if invalid_ohlc.any():

        bad = check.loc[
            invalid_ohlc,
            [
                "date",
                "symbol",
                "open",
                "high",
                "low",
                "close",
            ],
        ].copy()

        bad["nguyen_nhan"] = ""

        bad.loc[
            invalid_high[invalid_high].index,
            "nguyen_nhan",
        ] = (
            "High thấp hơn Open, Low hoặc Close"
        )

        bad.loc[
            invalid_low[invalid_low].index,
            "nguyen_nhan",
        ] = (
            "Low cao hơn Open, High hoặc Close"
        )

        error_text = bad.to_string(
            index=False
        )

        errors.append(
            "DỮ LIỆU OHLC KHÔNG HỢP LỆ:\n"
            + error_text
        )

    # Kiểm tra trùng mã và ngày
    duplicate = df.duplicated(
        ["symbol", "date"],
        keep=False,
    )

    if duplicate.any():

        bad_duplicate = df.loc[
            duplicate,
            ["symbol", "date"],
        ]

        errors.append(
            "Có ngày giao dịch bị trùng:\n"
            + bad_duplicate.head(20).to_string(
                index=False
            )
        )

    if errors:

        raise ValueError(
            "\n\n".join(errors)
        )


# =========================================================
# 7. CHUẨN HÓA TOÀN BỘ DỮ LIỆU
# =========================================================

def normalize_ohlcv(
    df,
    symbol_hint=None,
):

    if df is None:

        raise ValueError(
            "Không có dữ liệu đầu vào."
        )

    if df.empty:

        raise ValueError(
            "File không có dữ liệu."
        )

    # Giữ dữ liệu gốc
    out = df.copy()

    # Chuẩn hóa tên cột
    out, mapping = normalize_columns(
        out
    )

    # Kiểm tra cột bắt buộc
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in out.columns
    ]

    if missing:

        raise ValueError(
            "Không nhận diện được các cột bắt buộc: "
            + ", ".join(missing)
            + "\n\nCác cột hiện có: "
            + ", ".join(map(str, out.columns))
            + "\n\nHãy kiểm tra lại hàng tiêu đề của file."
        )

    # Chuẩn hóa ngày
    out["date"] = _parse_dates(
        out["date"]
    )

    # Chuẩn hóa giá và khối lượng
    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:

        out[column] = out[column].apply(
            _parse_number
        )

    # Mã cổ phiếu
    if "symbol" not in out.columns:

        if not symbol_hint:

            symbol_hint = "UNKNOWN"

        out["symbol"] = str(
            symbol_hint
        ).strip().upper()

    else:

        out["symbol"] = (
            out["symbol"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        if symbol_hint:

            empty_symbol = (
                out["symbol"].isin(
                    ["", "NAN", "NONE", "NULL"]
                )
            )

            out.loc[
                empty_symbol,
                "symbol",
            ] = str(
                symbol_hint
            ).strip().upper()

    # Chuẩn hóa % thay đổi nếu có
    if "change_pct" in out.columns:

        out["change_pct"] = (
            out["change_pct"]
            .astype(str)
            .str.replace(
                "%",
                "",
                regex=False,
            )
            .apply(_parse_number)
        )

    # Kiểm tra dữ liệu
    _validate_ohlcv(
        out
    )

    # Giữ nguyên các cột bổ sung
    core_columns = [
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    extra_columns = [
        column
        for column in out.columns
        if column not in core_columns
    ]

    out = out[
        core_columns + extra_columns
    ]

    # Sắp xếp dữ liệu theo mã và ngày
    out = (
        out.sort_values(
            ["symbol", "date"]
        )
        .reset_index(drop=True)
    )

    return out


# =========================================================
# 8. ĐỌC FILE STREAMLIT UPLOADER
# =========================================================

def load_market_file(
    uploaded_file,
    sheet_name=0,
    symbol_hint=None,
):

    if uploaded_file is None:

        raise ValueError(
            "Bạn chưa chọn file."
        )

    if hasattr(
        uploaded_file,
        "getvalue",
    ):

        raw = uploaded_file.getvalue()

    else:

        raw = uploaded_file.read()

    if not raw:

        raise ValueError(
            "File không có dữ liệu."
        )

    filename = getattr(
        uploaded_file,
        "name",
        "uploaded.csv",
    )

    frame = _read_file(
        filename,
        raw,
        sheet_name=sheet_name,
    )

    return normalize_ohlcv(
        frame,
        symbol_hint=symbol_hint,
    )


# =========================================================
# 9. TƯƠNG THÍCH CODE CŨ
# =========================================================

def prepare_market_data(
    df,
    symbol_hint=None,
):

    """
    Giữ tương thích với app.py cũ.

    Nhận DataFrame đã đọc từ Excel hoặc nguồn khác,
    chuẩn hóa và kiểm tra trước khi phân tích.
    """

    if df is None:

        raise ValueError(
            "Không có dữ liệu đầu vào."
        )

    return normalize_ohlcv(
        df.copy(),
        symbol_hint=symbol_hint,
    )


# =========================================================
# 10. BÁO CÁO CHẤT LƯỢNG DỮ LIỆU
# =========================================================

def get_data_quality_report(df):

    if df is None or df.empty:

        return {
            "valid": False,
            "rows": 0,
            "symbols": 0,
            "issues": [
                "Không có dữ liệu."
            ],
        }

    issues = []

    for column in REQUIRED_COLUMNS:

        if column not in df.columns:

            issues.append(
                f"Thiếu cột {column}"
            )

        elif df[column].isna().any():

            issues.append(
                f"Cột {column} có dữ liệu trống."
            )

    if "date" in df.columns:

        if df["date"].duplicated().any():

            issues.append(
                "Có ngày giao dịch trùng."
            )

    if (
        "symbol" in df.columns
        and "date" in df.columns
    ):

        if df.duplicated(
            ["symbol", "date"]
        ).any():

            issues.append(
                "Có mã cổ phiếu bị trùng ngày giao dịch."
            )

    return {
        "valid": len(issues) == 0,
        "rows": len(df),
        "symbols": (
            df["symbol"].nunique()
            if "symbol" in df.columns
            else 0
        ),
        "start_date": (
            str(df["date"].min())
            if "date" in df.columns
            else None
        ),
        "end_date": (
            str(df["date"].max())
            if "date" in df.columns
            else None
        ),
        "issues": issues,
    }


# =========================================================
# END DATA_LOADER.PY
# =========================================================

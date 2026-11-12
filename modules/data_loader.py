
from __future__ import annotations

from pathlib import Path
import io
import re
import unicodedata

import pandas as pd


# =========================================================
# 1. ÁNH XẠ TÊN CỘT
# =========================================================

ALIASES = {
    "date": [
        "date", "datetime", "time",
        "ngay", "ngay giao dich", "ngay gd",
        "trading date", "tradingdate"
    ],
    "open": [
        "open", "o", "mo cua",
        "gia mo cua", "open price"
    ],
    "high": [
        "high", "h", "cao nhat",
        "gia cao nhat", "highest"
    ],
    "low": [
        "low", "l", "thap nhat",
        "gia thap nhat", "lowest"
    ],
    "close": [
        "close", "c", "dong cua",
        "gia dong cua", "gia ket phien",
        "closing price"
    ],
    "volume": [
        "volume", "vol", "v",
        "khoi luong", "khoi luong giao dich",
        "kl", "klgd"
    ],
    "symbol": [
        "symbol", "ticker", "ma",
        "ma co phieu", "stock",
        "code", "ticker code"
    ],
}


# =========================================================
# 2. CHUẨN HÓA TÊN CỘT
# =========================================================

def _norm(value):
    """
    Chuẩn hóa tên cột:
    - Chữ thường
    - Bỏ dấu tiếng Việt
    - Bỏ ký tự phân cách thừa
    """

    text = str(value).strip().lower()

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    text = text.replace("đ", "d")

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return re.sub(r"\s+", " ", text).strip()


def _normalize_columns(df):
    """
    Đổi tên các cột nhận diện được sang:
    date, symbol, open, high, low, close, volume.
    """

    if df is None or df.empty:
        raise ValueError("File không có dữ liệu.")

    result = df.copy()

    normalized_map = {}

    for column in result.columns:
        key = _norm(column)

        if key in normalized_map:
            raise ValueError(
                f"Có tên cột bị trùng sau chuẩn hóa: {column}"
            )

        normalized_map[key] = column

    rename = {}

    for target, aliases in ALIASES.items():

        matched = None

        for alias in aliases:

            key = _norm(alias)

            if key in normalized_map:
                matched = normalized_map[key]
                break

        if matched is not None:
            rename[matched] = target

    # Không cho phép hai cột cùng ánh xạ vào một tên.
    targets = list(rename.values())

    if len(targets) != len(set(targets)):
        raise ValueError(
            "Có nhiều cột cùng được nhận diện thành một trường dữ liệu."
        )

    result = result.rename(columns=rename)

    return result


# =========================================================
# 3. ĐỌC FILE
# =========================================================

def _read_file(name, raw, sheet_name=0):

    ext = Path(name).suffix.lower()

    bio = io.BytesIO(raw)

    if ext == ".csv":

        errors = []

        for encoding in (
            "utf-8-sig",
            "utf-8",
            "cp1258",
            "latin1"
        ):

            try:

                bio.seek(0)

                return pd.read_csv(
                    bio,
                    encoding=encoding,
                    dtype=object
                )

            except Exception as exc:
                errors.append(str(exc))

        raise ValueError(
            "Không đọc được CSV. Hãy kiểm tra mã hóa và dấu phân cách."
        )

    if ext in (".xlsx", ".xls"):

        bio.seek(0)

        return pd.read_excel(
            bio,
            sheet_name=sheet_name,
            dtype=object
        )

    if ext == ".json":

        bio.seek(0)

        return pd.read_json(bio)

    if ext == ".txt":

        bio.seek(0)

        try:

            return pd.read_csv(
                bio,
                sep=None,
                engine="python",
                dtype=object
            )

        except Exception:

            bio.seek(0)

            return pd.read_csv(
                bio,
                sep=r"\s+",
                engine="python",
                dtype=object
            )

    if ext == ".parquet":

        bio.seek(0)

        return pd.read_parquet(bio)

    if ext == ".pdf":

        try:
            import pdfplumber
        except ImportError as exc:
            raise ValueError(
                "Cần cài pdfplumber để đọc PDF."
            ) from exc

        rows = []

        with pdfplumber.open(bio) as pdf:

            for page in pdf.pages:

                tables = page.extract_tables() or []

                for table in tables:
                    rows.extend(table)

        if not rows:
            raise ValueError(
                "Không tìm thấy bảng dữ liệu dạng văn bản trong PDF."
            )

        return pd.DataFrame(
            rows[1:],
            columns=rows[0]
        )

    if ext == ".docx":

        try:
            from docx import Document
        except ImportError as exc:
            raise ValueError(
                "Cần cài python-docx để đọc DOCX."
            ) from exc

        doc = Document(bio)

        rows = []

        for table in doc.tables:

            for row in table.rows:

                rows.append([
                    cell.text.strip()
                    for cell in row.cells
                ])

        if len(rows) < 2:
            raise ValueError(
                "Không tìm thấy bảng dữ liệu trong DOCX."
            )

        return pd.DataFrame(
            rows[1:],
            columns=rows[0]
        )

    raise ValueError(
        f"Định dạng chưa hỗ trợ: {ext}"
    )


# =========================================================
# 4. CHUYỂN ĐỔI SỐ
# =========================================================

def _parse_number(value):

    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text or text.lower() in (
        "nan", "none", "null", "-"
    ):
        return None

    text = text.replace(" ", "")

    # Hỗ trợ số dạng 57,500 hoặc 57.500.
    # Với dữ liệu giá chứng khoán Việt Nam,
    # dấu phân cách hàng nghìn thường là dấu chấm hoặc phẩy.
    if "," in text and "." in text:

        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "")
            text = text.replace(",", ".")

        else:
            text = text.replace(",", "")

    elif "," in text:

        parts = text.split(",")

        if len(parts) == 2 and len(parts[1]) == 3:
            text = "".join(parts)
        else:
            text = text.replace(",", ".")

    elif "." in text:

        parts = text.split(".")

        if len(parts) == 2 and len(parts[1]) == 3:
            text = "".join(parts)

    try:
        return float(text)
    except ValueError:
        return None


# =========================================================
# 5. CHUẨN HÓA OHLCV
# =========================================================

def normalize_ohlcv(
    df: pd.DataFrame,
    symbol_hint=None
) -> pd.DataFrame:

    if df is None or df.empty:
        raise ValueError("File không có dữ liệu.")

    out = _normalize_columns(df)

    required = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    missing = [
        column
        for column in required
        if column not in out.columns
    ]

    if missing:
        raise ValueError(
            "Thiếu cột bắt buộc: "
            + ", ".join(missing)
        )

    # Ngày giao dịch.
    out["date"] = pd.to_datetime(
        out["date"],
        dayfirst=True,
        errors="coerce"
    )

    # Giá và khối lượng.
    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:

        out[column] = out[column].apply(
            _parse_number
        )

    # Mã cổ phiếu.
    if "symbol" not in out.columns:

        out["symbol"] = (
            str(symbol_hint).strip().upper()
            if symbol_hint
            else "UNKNOWN"
        )

    else:

        out["symbol"] = (
            out["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        if symbol_hint:

            out["symbol"] = out["symbol"].replace(
                "",
                str(symbol_hint).strip().upper()
            )

            out["symbol"] = out["symbol"].fillna(
                str(symbol_hint).strip().upper()
            )

    # Chỉ giữ các cột chuẩn.
    out = out[
        [
            "date",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    ].copy()

    # Kiểm tra dữ liệu thiếu hoặc sai định dạng.
    invalid_rows = out[required].isna().any(axis=1)

    if invalid_rows.any():

        count = int(invalid_rows.sum())

        raise ValueError(
            f"Có {count} dòng ngày, giá hoặc khối lượng "
            "không hợp lệ. Chương trình không tự điền dữ liệu."
        )

    # Kiểm tra giá.
    price_columns = [
        "open",
        "high",
        "low",
        "close"
    ]

    if (out[price_columns] <= 0).any().any():
        raise ValueError(
            "Giá OHLC phải lớn hơn 0."
        )

    if (out["volume"] < 0).any():
        raise ValueError(
            "Khối lượng không được âm."
        )

    # Kiểm tra quan hệ OHLC.
    invalid_ohlc = (
        (out["high"] < out[price_columns].max(axis=1))
        |
        (out["low"] > out[price_columns].min(axis=1))
    )

    if invalid_ohlc.any():

        raise ValueError(
            f"Có {int(invalid_ohlc.sum())} dòng sai quan hệ OHLC."
        )

    # Kiểm tra mã rỗng.
    if out["symbol"].isna().any():
        raise ValueError(
            "Có dòng chưa xác định được mã cổ phiếu."
        )

    if (out["symbol"].astype(str).str.strip() == "").any():
        raise ValueError(
            "Có mã cổ phiếu rỗng."
        )

    # Kiểm tra trùng mã/ngày.
    duplicated = out.duplicated(
        ["symbol", "date"],
        keep=False
    )

    if duplicated.any():

        examples = out.loc[
            duplicated,
            ["symbol", "date"]
        ].head(5)

        raise ValueError(
            "Trùng mã/ngày giao dịch: "
            + str(examples.to_dict("records"))
        )

    out = out.sort_values(
        ["symbol", "date"]
    ).reset_index(drop=True)

    return out


# =========================================================
# 6. HÀM ĐỌC FILE CHO APP.PY
# =========================================================

def load_market_file(
    uploaded_file,
    sheet_name=0,
    symbol_hint=None
):

    if uploaded_file is None:
        raise ValueError("Chưa chọn file dữ liệu.")

    if hasattr(uploaded_file, "getvalue"):
        raw = uploaded_file.getvalue()
    else:
        raw = uploaded_file.read()

    if not raw:
        raise ValueError("File dữ liệu đang trống.")

    frame = _read_file(
        uploaded_file.name,
        raw,
        sheet_name=sheet_name
    )

    return normalize_ohlcv(
        frame,
        symbol_hint=symbol_hint
    )


# =========================================================
# 7. HÀM TƯƠNG THÍCH VỚI APP.PY
# =========================================================

def prepare_market_data(
    df,
    symbol_hint=None
):

    if df is None or df.empty:
        raise ValueError("Không có dữ liệu đầu vào.")

    return normalize_ohlcv(
        df.copy(),
        symbol_hint=symbol_hint
    )


# =========================================================
# 8. BÁO CÁO CHẤT LƯỢNG DỮ LIỆU
# =========================================================

def get_data_quality_report(df):

    if df is None or df.empty:

        return {
            "rows": 0,
            "symbols": 0,
            "duplicate_rows": 0,
            "missing_rows": 0,
            "status": "EMPTY"
        }

    required = [
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    missing_columns = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing_columns:

        return {
            "rows": len(df),
            "symbols": 0,
            "duplicate_rows": 0,
            "missing_rows": 0,
            "status": "MISSING_COLUMNS",
            "missing_columns": missing_columns
        }

    missing_rows = int(
        df[required].isna().any(axis=1).sum()
    )

    duplicate_rows = int(
        df.duplicated(
            ["symbol", "date"],
            keep=False
        ).sum()
    )

    return {
        "rows": len(df),
        "symbols": int(df["symbol"].nunique()),
        "duplicate_rows": duplicate_rows,
        "missing_rows": missing_rows,
        "status": (
            "OK"
            if missing_rows == 0 and duplicate_rows == 0
            else "WARNING"
        )
    }

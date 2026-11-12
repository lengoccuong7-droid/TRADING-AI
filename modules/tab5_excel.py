
"""
TAB 5 - QUẢN LÝ DỮ LIỆU EXCEL / CSV ĐỘC LẬP

Chức năng:
1. Nhập dữ liệu từ Excel, CSV, TXT.
2. Dán dữ liệu trực tiếp và tự động tách thành bảng.
3. Chuẩn hóa tên cột.
4. Kiểm tra dữ liệu OHLCV.
5. Lưu file mới.
6. Cập nhật file cũ và loại bỏ dòng trùng.
7. Tạo bản sao lưu trước khi cập nhật.
8. Xuất Excel / CSV.

Lưu ý:
- Module này độc lập với market_data.
- Không tự động ghi dữ liệu vào Tab 1.
- Không tác động đến các module phân tích khác.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from pathlib import Path

import pandas as pd


# =========================================================
# 1. THƯ MỤC LƯU FILE RIÊNG CỦA TAB 5
# =========================================================

DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "tab5_saved"
)


# =========================================================
# 2. NHẬN DIỆN TÊN CỘT
# =========================================================

ALIASES = {
    "date": [
        "date",
        "datetime",
        "time",
        "ngay",
        "ngay giao dich",
        "ngay gd",
        "trading date",
        "tradingdate",
    ],

    "symbol": [
        "symbol",
        "ticker",
        "ma",
        "ma co phieu",
        "stock",
        "code",
    ],

    "open": [
        "open",
        "o",
        "mo cua",
        "gia mo cua",
        "gia mo cua vnd",
        "opening price",
    ],

    "high": [
        "high",
        "h",
        "cao nhat",
        "gia cao nhat",
        "highest",
        "highest price",
    ],

    "low": [
        "low",
        "l",
        "thap nhat",
        "gia thap nhat",
        "lowest",
        "lowest price",
    ],

    "close": [
        "close",
        "c",
        "dong cua",
        "gia dong cua",
        "gia ket phien",
        "closing price",
        "last price",
    ],

    "volume": [
        "volume",
        "vol",
        "kl",
        "khoi luong",
        "khoi luong giao dich",
        "tong khoi luong",
        "trading volume",
    ],
}


# =========================================================
# 3. CHUẨN HÓA CHUỖI
# =========================================================

def _norm(value: object) -> str:
    """
    Chuẩn hóa tên cột:
    - Chuyển chữ thường.
    - Bỏ dấu tiếng Việt.
    - Bỏ ký tự đặc biệt.
    - Chuẩn hóa khoảng trắng.
    """

    text = unicodedata.normalize(
        "NFKD",
        str(value).strip().lower()
    )

    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )

    text = text.replace("đ", "d")

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        text
    ).strip()


def _safe_filename(filename: str) -> str:
    """
    Làm sạch tên file để tránh đường dẫn không an toàn.
    """

    name = Path(str(filename)).name.strip()

    name = re.sub(
        r"[^\w\-.() ]+",
        "_",
        name,
        flags=re.UNICODE
    )

    name = re.sub(
        r"\s+",
        "_",
        name
    ).strip("._")

    if not name:
        raise ValueError("Tên file không hợp lệ.")

    return name


def _path_for(filename: str) -> Path:
    """
    Chỉ cho phép thao tác file bên trong thư mục Tab 5.
    """

    name = _safe_filename(filename)

    root = DATA_DIR.resolve()
    path = (DATA_DIR / name).resolve()

    if path.parent != root:
        raise ValueError("Đường dẫn file không hợp lệ.")

    return path


# =========================================================
# 4. TỰ NHẬN DIỆN DẤU PHÂN CÁCH
# =========================================================

def detect_separator(text: str) -> str:
    """
    Nhận diện:
    - Tab
    - Dấu phẩy
    - Dấu chấm phẩy
    - Dấu |
    - Khoảng trắng
    """

    sample = "\n".join(
        line for line in text.splitlines()
        if line.strip()
    )[:12000]

    if not sample:
        raise ValueError("Không có dữ liệu để phân tách.")

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters="\t,;|"
        )

        return dialect.delimiter

    except csv.Error:

        counts = {
            sep: sample.count(sep)
            for sep in ("\t", ";", "|", ",")
        }

        best = max(
            counts,
            key=counts.get
        )

        if counts[best] > 0:
            return best

        return "whitespace"


# =========================================================
# 5. ĐỌC DỮ LIỆU DÁN TRỰC TIẾP
# =========================================================

def parse_pasted_text(
    text: str,
    delimiter: str = "Tự nhận diện",
    header: bool = True
) -> pd.DataFrame:

    """
    Đọc dữ liệu người dùng dán trực tiếp.

    Ví dụ dữ liệu từ Excel:

    Date    Open    High    Low    Close    Volume
    2026-01-01    100    110    95    105    1000000

    Tự động tách hàng và cột.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Ô nhập dữ liệu đang trống.")

    if delimiter == "Tự nhận diện":
        sep = detect_separator(text)
    else:
        sep = delimiter

    source = io.StringIO(text.strip())

    if sep == "whitespace":

        df = pd.read_csv(
            source,
            sep=r"\s+",
            header=0 if header else None,
            engine="python",
            dtype=object
        )

    else:

        df = pd.read_csv(
            source,
            sep=sep,
            header=0 if header else None,
            engine="python",
            dtype=object
        )

    if df.empty or len(df.columns) == 0:
        raise ValueError(
            "Không tách được dữ liệu thành bảng. "
            "Hãy kiểm tra dấu phân cách."
        )

    if not header:

        df.columns = [
            f"Cột_{i + 1}"
            for i in range(len(df.columns))
        ]

    return df


# =========================================================
# 6. ĐỌC CSV / TXT
# =========================================================

def _read_csv_bytes(raw: bytes) -> pd.DataFrame:

    errors = []

    for encoding in (
        "utf-8-sig",
        "utf-8",
        "cp1258",
        "latin1"
    ):

        try:

            text = raw.decode(encoding)

            sep = detect_separator(text)

            if sep == "whitespace":

                return pd.read_csv(
                    io.StringIO(text),
                    sep=r"\s+",
                    engine="python",
                    dtype=object
                )

            return pd.read_csv(
                io.StringIO(text),
                sep=sep,
                engine="python",
                dtype=object
            )

        except Exception as exc:

            errors.append(str(exc))

    raise ValueError(
        "Không đọc được CSV/TXT. "
        + (errors[-1] if errors else "")
    )


# =========================================================
# 7. ĐỌC FILE EXCEL / CSV / TXT
# =========================================================

def read_table(uploaded_file, sheet_name=0) -> pd.DataFrame:

    name = str(uploaded_file.name).lower()

    raw = (
        uploaded_file.getvalue()
        if hasattr(uploaded_file, "getvalue")
        else uploaded_file.read()
    )

    if name.endswith((".csv", ".txt")):

        return _read_csv_bytes(raw)

    if name.endswith((".xlsx", ".xls")):

        return pd.read_excel(
            io.BytesIO(raw),
            sheet_name=sheet_name,
            dtype=object
        )

    raise ValueError(
        "Tab 5 hỗ trợ CSV, TXT, XLSX và XLS."
    )


# =========================================================
# 8. CHUẨN HÓA TÊN CỘT
# =========================================================

def normalize_columns(df: pd.DataFrame):

    if df is None or df.empty:
        raise ValueError("Bảng không có dữ liệu.")

    rename = {}
    mapping = {}

    normalized = {
        _norm(col): col
        for col in df.columns
    }

    for target, aliases in ALIASES.items():

        candidates = {
            _norm(target),
            *(_norm(a) for a in aliases)
        }

        found = next(
            (
                normalized[a]
                for a in candidates
                if a in normalized
            ),
            None
        )

        if found is not None and found != target:

            rename[found] = target
            mapping[str(found)] = target

        elif found is not None:

            mapping[str(found)] = target

    out = df.rename(
        columns=rename
    ).copy()

    # Giữ lại tất cả cột.
    # Nếu cột trùng tên thì tự đánh số.

    new_cols = []
    seen = {}

    for i, col in enumerate(out.columns, start=1):

        name = str(col).strip() or f"Cột_{i}"

        count = seen.get(name, 0)

        seen[name] = count + 1

        if count == 0:
            new_cols.append(name)
        else:
            new_cols.append(f"{name}_{count + 1}")

    out.columns = new_cols

    return out, mapping


# =========================================================
# 9. CHUYỂN DỮ LIỆU SỐ
# =========================================================

def _to_number(series: pd.Series) -> pd.Series:

    def parse(value):

        if pd.isna(value):
            return pd.NA

        s = str(value).strip()

        s = s.replace("\u00a0", "")
        s = s.replace(" ", "")

        if not s or s.lower() in {
            "nan",
            "none",
            "null",
            "-"
        }:
            return pd.NA

        # Có cả dấu chấm và dấu phẩy.
        if "," in s and "." in s:

            if s.rfind(",") > s.rfind("."):

                s = s.replace(".", "")
                s = s.replace(",", ".")

            else:

                s = s.replace(",", "")

        # Chỉ có dấu phẩy.
        elif "," in s:

            tail = s.rsplit(",", 1)[-1]

            if len(tail) in (1, 2):

                s = s.replace(",", ".")

            else:

                s = s.replace(",", "")

        # Chỉ có dấu chấm.
        elif "." in s:

            tail = s.rsplit(".", 1)[-1]

            if len(tail) == 3 and s.count(".") == 1:

                s = s.replace(".", "")

        try:

            return float(s)

        except ValueError:

            return pd.NA

    return series.map(parse).astype("Float64")


# =========================================================
# 10. CHUẨN HÓA DỮ LIỆU THỊ TRƯỜNG
# =========================================================

def normalize_market_data(
    df: pd.DataFrame,
    symbol: str = ""
):

    out, mapping = normalize_columns(df)

    required = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    missing = [
        c for c in required
        if c not in out.columns
    ]

    if missing:

        raise ValueError(
            "Thiếu cột OHLCV: "
            + ", ".join(missing)
        )

    out["date"] = pd.to_datetime(
        out["date"],
        dayfirst=True,
        errors="coerce"
    )

    for col in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:

        out[col] = _to_number(out[col])

    if "symbol" not in out.columns:

        out["symbol"] = (
            str(symbol).strip().upper()
            if symbol
            else "UNKNOWN"
        )

    else:

        out["symbol"] = (
            out["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        if symbol:

            out["symbol"] = out["symbol"].replace(
                "",
                symbol.strip().upper()
            )

    out = out.sort_values(
        ["symbol", "date"],
        na_position="last"
    ).reset_index(drop=True)

    return out, mapping


# =========================================================
# 11. KIỂM TRA CHẤT LƯỢNG DỮ LIỆU
# =========================================================

def validate_table(df: pd.DataFrame):

    issues = []

    if df is None or df.empty:

        return ["Bảng không có dữ liệu."]

    required = {
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume"
    }

    # Bảng tổng quát không nhất thiết là OHLCV.
    if not required.issubset(df.columns):

        return [
            "Không đủ 6 cột OHLCV; "
            "đây được xem là bảng dữ liệu tổng quát."
        ]

    # Kiểm tra ô trống.
    missing = df[list(required)].isna().any(axis=1)

    if missing.any():

        issues.append(
            f"Có {int(missing.sum())} dòng thiếu "
            "ngày/giá/khối lượng."
        )

    numeric = [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    n = df[numeric].apply(
        pd.to_numeric,
        errors="coerce"
    )

    bad_numeric = n.isna().any(axis=1)

    if bad_numeric.any():

        issues.append(
            f"Có {int(bad_numeric.sum())} dòng "
            "có dữ liệu số không hợp lệ."
        )

    # Kiểm tra quan hệ OHLC.
    bad_ohlc = (
        (n["high"] < n[["open", "low", "close"]].max(axis=1))
        |
        (n["low"] > n[["open", "high", "close"]].min(axis=1))
    )

    if bad_ohlc.fillna(False).any():

        issues.append(
            f"Có {int(bad_ohlc.fillna(False).sum())} dòng "
            "sai quan hệ High/Low/OHLC."
        )

    # Khối lượng không được âm.
    if (n["volume"] < 0).fillna(False).any():

        issues.append("Có khối lượng âm.")

    # Kiểm tra dòng trùng.
    key_cols = [
        c for c in ["symbol", "date"]
        if c in df.columns
    ]

    if key_cols and df.duplicated(key_cols).any():

        issues.append(
            f"Có {int(df.duplicated(key_cols).sum())} "
            f"dòng trùng theo khóa {key_cols}."
        )

    return issues


# =========================================================
# 12. GỘP FILE CŨ VÀ DỮ LIỆU MỚI
# =========================================================

def merge_old_and_new(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
    keys=None
):

    if keys is None:

        keys = [
            c for c in ["symbol", "date"]
            if c in old_df.columns
            and c in new_df.columns
        ]

    keys = list(keys or [])

    if not keys:

        raise ValueError(
            "Cần chọn ít nhất một cột khóa để cập nhật."
        )

    missing = [
        c for c in keys
        if c not in old_df.columns
        or c not in new_df.columns
    ]

    if missing:

        raise ValueError(
            "Thiếu cột khóa ở file cũ hoặc dữ liệu mới: "
            + ", ".join(missing)
        )

    # Dữ liệu mới được ưu tiên khi trùng khóa.
    combined = pd.concat(
        [old_df, new_df],
        ignore_index=True,
        sort=False
    )

    duplicate_mask = combined.duplicated(
        keys,
        keep="last"
    )

    duplicate_count = int(
        duplicate_mask.sum()
    )

    merged = combined.loc[
        ~duplicate_mask
    ].copy()

    if "date" in merged.columns:

        parsed = pd.to_datetime(
            merged["date"],
            errors="coerce",
            dayfirst=True
        )

        merged = (
            merged.assign(_sort_date=parsed)
            .sort_values(
                keys,
                kind="stable"
            )
            .drop(columns="_sort_date")
        )

    else:

        merged = merged.sort_values(
            keys,
            kind="stable"
        )

    return merged.reset_index(drop=True), duplicate_count


# =========================================================
# 13. ĐỌC FILE ĐÃ LƯU
# =========================================================

def _read_saved(path: Path) -> pd.DataFrame:

    if path.suffix.lower() == ".csv":

        return _read_csv_bytes(
            path.read_bytes()
        )

    if path.suffix.lower() == ".xlsx":

        return pd.read_excel(
            path,
            dtype=object
        )

    raise ValueError(
        "Định dạng file lưu không được hỗ trợ."
    )


# =========================================================
# 14. DANH SÁCH FILE ĐÃ LƯU
# =========================================================

def list_saved_files():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return sorted(
        p.name
        for p in DATA_DIR.iterdir()
        if (
            p.is_file()
            and p.suffix.lower() in {".csv", ".xlsx"}
            and ".backup" not in p.name
            and not p.name.endswith(".tmp")
        )
    )


# =========================================================
# 15. MỞ FILE ĐÃ LƯU
# =========================================================

def load_saved_file(filename: str) -> pd.DataFrame:

    path = _path_for(filename)

    if not path.exists():

        raise FileNotFoundError(
            f"Không tìm thấy file: {filename}"
        )

    return _read_saved(path)


# =========================================================
# 16. GHI FILE
# =========================================================

def _write_file(
    df: pd.DataFrame,
    path: Path
):

    if path.suffix.lower() == ".csv":

        df.to_csv(
            path,
            index=False,
            encoding="utf-8-sig"
        )

    elif path.suffix.lower() == ".xlsx":

        df.to_excel(
            path,
            index=False,
            engine="openpyxl"
        )

    else:

        raise ValueError(
            "Chỉ lưu được CSV hoặc XLSX."
        )


# =========================================================
# 17. LƯU FILE MỚI
# =========================================================

def save_new_file(
    df: pd.DataFrame,
    filename: str,
    file_type: str = "xlsx"
) -> Path:

    if df is None or df.empty:

        raise ValueError(
            "Không thể lưu bảng trống."
        )

    ext = (
        ".csv"
        if file_type.lower() == "csv"
        else ".xlsx"
    )

    name = _safe_filename(filename)

    if not name.lower().endswith(ext):

        name = Path(name).stem + ext

    path = _path_for(name)

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if path.exists():

        raise FileExistsError(
            f"File {path.name} đã tồn tại. "
            "Hãy chọn tên khác hoặc dùng chức năng "
            "cập nhật file cũ."
        )

    _write_file(
        df,
        path
    )

    return path


# =========================================================
# 18. CẬP NHẬT FILE CŨ + SAO LƯU
# =========================================================

def update_saved_file(
    df_new: pd.DataFrame,
    filename: str,
    keys=None
):

    if df_new is None or df_new.empty:

        raise ValueError(
            "Dữ liệu mới đang trống."
        )

    path = _path_for(filename)

    if not path.exists():

        raise FileNotFoundError(
            f"Không tìm thấy file cũ: {filename}"
        )

    old_df = _read_saved(path)

    merged, duplicate_count = merge_old_and_new(
        old_df,
        df_new,
        keys=keys
    )

    # Tạo bản sao lưu trước khi ghi đè.
    backup = path.with_name(
        path.stem + ".backup" + path.suffix
    )

    if backup.exists():

        from datetime import datetime

        backup = path.with_name(
            path.stem
            + ".backup_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + path.suffix
        )

    backup.write_bytes(
        path.read_bytes()
    )

    # Ghi file tạm, sau đó thay thế file cũ.
    temp = path.with_name(
        path.stem + ".tmp" + path.suffix
    )

    try:

        _write_file(
            merged,
            temp
        )

        temp.replace(path)

    except Exception:

        if temp.exists():
            temp.unlink()

        raise

    return (
        merged,
        duplicate_count,
        backup
    )


# =========================================================
# 19. XUẤT CSV
# =========================================================

def to_csv_bytes(df: pd.DataFrame) -> bytes:

    if df is None:
        raise ValueError("Không có dữ liệu để xuất.")

    return df.to_csv(
        index=False
    ).encode("utf-8-sig")


# =========================================================
# 20. XUẤT EXCEL
# =========================================================

def to_excel_bytes(df: pd.DataFrame) -> bytes:

    if df is None:
        raise ValueError("Không có dữ liệu để xuất.")

    bio = io.BytesIO()

    with pd.ExcelWriter(
        bio,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Data"
        )

    return bio.getvalue()

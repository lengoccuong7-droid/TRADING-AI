
"""
TAB 5 - TRUNG TÂM QUẢN LÝ DỮ LIỆU EXCEL / CSV
- Đọc Excel, CSV, TXT
- Tự nhận diện dấu phân cách và tên cột
- Chuẩn hóa tên cột
- Kiểm tra dữ liệu
- Lưu thành file mới
- Cập nhật file cũ, chống trùng dữ liệu
- Không tự ghi đè file gốc khi nhập
"""

from pathlib import Path
import io
import re
import pandas as pd


DATA_DIR = Path("data") / "tab5_saved"

# Các tên cột thường gặp
ALIASES = {
    "date": [
        "date", "datetime", "time", "trading_date",
        "ngay", "ngày", "ngay_giao_dich", "ngày_giao_dịch"
    ],
    "symbol": [
        "symbol", "ticker", "stock", "code",
        "ma", "mã", "ma_ck", "mã_ck", "ma_co_phieu"
    ],
    "open": ["open", "o", "gia_mo_cua", "giá_mở_cửa"],
    "high": ["high", "h", "gia_cao_nhat", "giá_cao_nhất"],
    "low": ["low", "l", "gia_thap_nhat", "giá_thấp_nhất"],
    "close": [
        "close", "c", "adj_close", "price",
        "gia_dong_cua", "giá_đóng_cửa"
    ],
    "volume": [
        "volume", "vol", "kl", "khoi_luong",
        "khối_lượng", "khoi_luong_giao_dich"
    ],
}


def _clean_name(value):
    """Chuẩn hóa tên cột để so khớp."""
    value = str(value).strip().lower()
    value = value.replace(" ", "_").replace("-", "_")
    value = re.sub(r"[^\w]", "", value)
    return value


def detect_separator(raw):
    """Tự nhận diện dấu phân cách CSV."""
    sample = raw[:10000].decode("utf-8-sig", errors="replace")

    candidates = [",", ";", "\t", "|"]
    counts = {sep: sample.count(sep) for sep in candidates}

    best = max(counts, key=counts.get)

    return best if counts[best] > 0 else ","


def read_table(uploaded_file, sheet_name=0):
    """Đọc file Excel/CSV/TXT."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if name.endswith((".csv", ".txt")):
        sep = detect_separator(raw)

        try:
            return pd.read_csv(
                io.BytesIO(raw),
                sep=sep,
                encoding="utf-8-sig",
                engine="python"
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                io.BytesIO(raw),
                sep=sep,
                encoding="latin1",
                engine="python"
            )

    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(
            io.BytesIO(raw),
            sheet_name=sheet_name
        )

    raise ValueError("Chỉ hỗ trợ CSV, TXT, XLSX, XLS.")


def normalize_columns(df):
    """Tự nhận diện tên cột phổ biến."""
    result = df.copy()
    mapping = {}

    for col in result.columns:
        clean = _clean_name(col)

        for standard, aliases in ALIASES.items():
            normalized_aliases = [_clean_name(x) for x in aliases]

            if clean in normalized_aliases:
                mapping[col] = standard
                break

    result = result.rename(columns=mapping)

    # Xử lý tên cột bị trùng sau chuẩn hóa
    result = result.loc[:, ~result.columns.duplicated()]

    return result, mapping


def normalize_market_data(df, symbol=""):
    """
    Chuẩn hóa bảng OHLCV.
    Không tự suy đoán giá trị bị thiếu.
    """
    result, mapping = normalize_columns(df)

    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in result.columns]

    if missing:
        raise ValueError(
            "Thiếu cột bắt buộc: " + ", ".join(missing)
        )

    result["date"] = pd.to_datetime(
        result["date"], errors="coerce"
    )

    for col in ["open", "high", "low", "close", "volume"]:
        result[col] = pd.to_numeric(
            result[col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

    if "symbol" not in result.columns:
        result["symbol"] = symbol.strip().upper() if symbol else ""

    result["symbol"] = (
        result["symbol"].astype(str).str.strip().str.upper()
    )

    # Loại bỏ khoảng trắng và dòng hoàn toàn trống
    result = result.dropna(
        subset=["date", "open", "high", "low", "close", "volume"],
        how="any"
    )

    result = result.sort_values(
        ["symbol", "date"]
    ).reset_index(drop=True)

    return result, mapping


def validate_table(df):
    """Trả về danh sách cảnh báo, không tự sửa dữ liệu."""
    issues = []

    if df is None or df.empty:
        return ["Bảng dữ liệu đang trống."]

    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        return ["Thiếu cột: " + ", ".join(missing)]

    if df["date"].isna().any():
        issues.append("Có ngày giao dịch không hợp lệ.")

    price_cols = ["open", "high", "low", "close"]

    for col in price_cols + ["volume"]:
        if pd.to_numeric(df[col], errors="coerce").isna().any():
            issues.append(f"Cột {col} có giá trị không phải số.")

    valid = df.dropna(subset=price_cols)

    if not valid.empty:
        if (valid[price_cols] <= 0).any().any():
            issues.append("Có giá OHLC nhỏ hơn hoặc bằng 0.")

        invalid_ohlc = (
            (valid["high"] < valid[["open", "close", "low"]].max(axis=1))
            | (valid["low"] > valid[["open", "close", "high"]].min(axis=1))
        )

        if invalid_ohlc.any():
            issues.append(
                f"Có {int(invalid_ohlc.sum())} dòng sai quan hệ OHLC."
            )

    if (pd.to_numeric(df["volume"], errors="coerce") < 0).any():
        issues.append("Có khối lượng âm.")

    if "symbol" in df.columns:
        duplicate_keys = ["symbol", "date"]
    else:
        duplicate_keys = ["date"]

    duplicated = df.duplicated(duplicate_keys, keep=False)

    if duplicated.any():
        issues.append(
            f"Có {int(duplicated.sum())} dòng trùng mã/ngày."
        )

    return issues


def merge_old_and_new(old_df, new_df, keys=None):
    """
    Ghép dữ liệu cũ và mới.
    Dòng mới được ưu tiên nếu trùng khóa.
    """
    old_df = old_df.copy()
    new_df = new_df.copy()

    if keys is None:
        keys = (
            ["symbol", "date"]
            if "symbol" in old_df.columns and "symbol" in new_df.columns
            else ["date"]
        )

    missing_keys = [
        key for key in keys
        if key not in old_df.columns or key not in new_df.columns
    ]

    if missing_keys:
        raise ValueError(
            "Không thể đối chiếu vì thiếu khóa: "
            + ", ".join(missing_keys)
        )

    combined = pd.concat(
        [old_df, new_df],
        ignore_index=True,
        sort=False
    )

    before = len(combined)

    combined = combined.drop_duplicates(
        subset=keys,
        keep="last"
    )

    combined = combined.sort_values(
        keys
    ).reset_index(drop=True)

    removed = before - len(combined)

    return combined, removed


def list_saved_files():
    """Danh sách file đã lưu trong kho Tab 5."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return sorted(
        [
            p.name for p in DATA_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in [".csv", ".xlsx"]
        ]
    )


def load_saved_file(filename):
    """Đọc một file trong kho dữ liệu Tab 5."""
    path = DATA_DIR / Path(filename).name

    if not path.exists():
        raise FileNotFoundError("Không tìm thấy file đã lưu.")

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    return pd.read_excel(path)


def save_new_file(df, filename, file_type="xlsx"):
    """Lưu thành file mới, không ghi đè file đã tồn tại."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).stem.strip()

    if not safe_name:
        raise ValueError("Tên file không được để trống.")

    extension = ".csv" if file_type == "csv" else ".xlsx"
    path = DATA_DIR / f"{safe_name}{extension}"

    if path.exists():
        raise FileExistsError(
            f"File {path.name} đã tồn tại. Hãy chọn tên khác."
        )

    if extension == ".csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(path, index=False, engine="openpyxl")

    return path


def update_saved_file(df_new, filename, keys=None):
    """
    Cập nhật file cũ:
    - Đọc dữ liệu cũ
    - Ghép dữ liệu mới
    - Dòng mới thay thế dòng cũ nếu trùng khóa
    - Tạo bản sao lưu trước khi ghi
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    path = DATA_DIR / Path(filename).name

    if not path.exists():
        raise FileNotFoundError("File cần cập nhật không tồn tại.")

    if path.suffix.lower() == ".csv":
        old_df = pd.read_csv(path)
    elif path.suffix.lower() == ".xlsx":
        old_df = pd.read_excel(path)
    else:
        raise ValueError("Chỉ cập nhật file CSV hoặc XLSX.")

    merged, duplicate_count = merge_old_and_new(
        old_df, df_new, keys=keys
    )

    # Tạo bản sao lưu trước khi cập nhật
    backup_path = path.with_name(
        path.stem + "_backup" + path.suffix
    )

    counter = 1
    while backup_path.exists():
        backup_path = path.with_name(
            f"{path.stem}_backup_{counter}{path.suffix}"
        )
        counter += 1

    backup_path.write_bytes(path.read_bytes())

    if path.suffix.lower() == ".csv":
        merged.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        merged.to_excel(path, index=False, engine="openpyxl")

    return merged, duplicate_count, backup_path


def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df):
    bio = io.BytesIO()

    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Data"
        )

    return bio.getvalue()


"""
TAB 5 - TRUNG TÂM QUẢN LÝ DỮ LIỆU EXCEL / CSV

Chức năng:
- Đọc Excel, CSV, TXT.
- Tự nhận diện dấu phân cách CSV/TXT.
- Tự nhận diện tên cột tiếng Việt và tiếng Anh.
- Chuẩn hóa dữ liệu OHLCV khi đủ cột.
- Kiểm tra lỗi dữ liệu và dòng trùng.
- Lưu thành file mới, không ghi đè file cũ.
- Cập nhật file cũ, tạo bản sao lưu trước khi ghi.
- Xuất CSV UTF-8-SIG và Excel XLSX.

Lưu ý:
- Không sửa file gốc người dùng tải lên.
- Không thay đổi các module khác của BOT TRADER.
"""

from pathlib import Path
import csv
import io
import re
import unicodedata

import pandas as pd


# =========================================================
# 1. THƯ MỤC LƯU TRỮ
# =========================================================

DATA_DIR = Path("data") / "tab5_saved"

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".txt"}


# =========================================================
# 2. NHẬN DIỆN TÊN CỘT
# =========================================================

ALIASES = {
    "date": [
        "date", "datetime", "time", "trading_date",
        "ngay", "ngày", "ngay_giao_dich",
        "ngày_giao_dịch", "tradingdate"
    ],

    "symbol": [
        "symbol", "ticker", "stock", "code",
        "ma", "mã", "ma_ck", "mã_ck",
        "ma_co_phieu", "mã_cổ_phiếu",
        "stock_code", "stock_symbol"
    ],

    "open": [
        "open", "o", "gia_mo_cua",
        "giá_mở_cửa", "opening_price"
    ],

    "high": [
        "high", "h", "gia_cao_nhat",
        "giá_cao_nhất", "highest_price"
    ],

    "low": [
        "low", "l", "gia_thap_nhat",
        "giá_thấp_nhất", "lowest_price"
    ],

    "close": [
        "close", "c", "adj_close", "price",
        "gia_dong_cua", "giá_đóng_cửa",
        "closing_price", "last_price"
    ],

    "volume": [
        "volume", "vol", "kl", "khoi_luong",
        "khối_lượng", "khoi_luong_giao_dich",
        "trading_volume"
    ],
}


# =========================================================
# 3. HÀM HỖ TRỢ
# =========================================================

def _clean_name(value):
    """
    Chuẩn hóa tên cột:
    - Chữ thường.
    - Bỏ dấu tiếng Việt.
    - Khoảng trắng thành dấu gạch dưới.
    - Bỏ ký tự đặc biệt.
    """

    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    value = value.replace("đ", "d")
    value = value.replace(" ", "_")
    value = value.replace("-", "_")

    value = re.sub(r"[^\w]", "", value)
    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def _safe_filename(filename):
    """
    Chỉ lấy tên file, không cho phép đường dẫn bên ngoài
    thư mục lưu trữ Tab 5.
    """

    name = Path(str(filename)).name.strip()

    if not name or name in {".", ".."}:
        raise ValueError("Tên file không hợp lệ.")

    return name


def _get_saved_path(filename):
    """Tạo đường dẫn an toàn tới file trong kho Tab 5."""

    safe_name = _safe_filename(filename)
    path = DATA_DIR / safe_name

    if path.suffix.lower() not in {".csv", ".xlsx"}:
        raise ValueError("Kho Tab 5 chỉ hỗ trợ file CSV và XLSX.")

    return path


def _read_csv_bytes(raw):
    """
    Đọc CSV/TXT:
    - Tự nhận diện dấu phân cách.
    - Thử các bảng mã phổ biến.
    - Giữ nguyên dữ liệu dạng bảng.
    """

    if not raw:
        raise ValueError("File đang trống.")

    separator = detect_separator(raw)

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1258",
        "latin1"
    ]

    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(
                io.BytesIO(raw),
                sep=separator,
                encoding=encoding,
                engine="python"
            )
        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"Không đọc được CSV/TXT. Chi tiết: {last_error}"
    )


def _numeric_series(series):
    """
    Chuyển cột số về dạng numeric.
    Không tự thay giá trị lỗi bằng 0.
    """

    text = series.astype(str).str.strip()

    text = text.replace({
        "": None,
        "nan": None,
        "None": None,
        "NaN": None,
        "null": None,
        "NULL": None,
        "-": None
    })

    # Loại bỏ khoảng trắng và dấu phân cách hàng nghìn dạng dấu phẩy.
    text = text.str.replace(" ", "", regex=False)
    text = text.str.replace(",", "", regex=False)

    return pd.to_numeric(text, errors="coerce")


# =========================================================
# 4. NHẬN DIỆN DẤU PHÂN CÁCH
# =========================================================

def detect_separator(raw):
    """Tự nhận diện dấu phân cách CSV/TXT."""

    if isinstance(raw, bytes):
        sample = raw[:20000].decode(
            "utf-8-sig",
            errors="replace"
        )
    else:
        sample = str(raw)[:20000]

    try:
        dialect = csv.Sniffer().sniff(
            sample,
            delimiters=",;\t|"
        )
        return dialect.delimiter
    except Exception:
        pass

    candidates = [",", ";", "\t", "|"]

    lines = [
        line for line in sample.splitlines()
        if line.strip()
    ][:20]

    if not lines:
        return ","

    scores = {}

    for separator in candidates:
        counts = [
            line.count(separator)
            for line in lines
        ]

        positive = [count for count in counts if count > 0]

        scores[separator] = (
            len(positive),
            sum(positive)
        )

    best = max(scores, key=scores.get)

    if scores[best][0] == 0:
        return ","

    return best


# =========================================================
# 5. ĐỌC FILE
# =========================================================

def read_table(uploaded_file, sheet_name=0):
    """
    Đọc Excel, CSV hoặc TXT.

    Tương thích với cách gọi hiện tại:
        tab5_excel.read_table(uploaded5)
    """

    filename = getattr(uploaded_file, "name", "")

    if not filename:
        raise ValueError("Không xác định được tên file.")

    extension = Path(filename).suffix.lower()

    raw = uploaded_file.getvalue()

    if extension in {".csv", ".txt"}:
        return _read_csv_bytes(raw)

    if extension in {".xlsx", ".xls"}:
        try:
            return pd.read_excel(
                io.BytesIO(raw),
                sheet_name=sheet_name
            )
        except ImportError as exc:
            raise ValueError(
                "Thiếu thư viện đọc Excel. "
                "Hãy kiểm tra openpyxl hoặc xlrd trong requirements.txt."
            ) from exc

    raise ValueError(
        "Định dạng không được hỗ trợ. "
        "Chỉ nhận CSV, TXT, XLSX và XLS."
    )


# =========================================================
# 6. CHUẨN HÓA TÊN CỘT
# =========================================================

def normalize_columns(df):
    """
    Nhận diện tên cột tiếng Việt/Anh.

    Trả về:
        normalized_df, mapping

    Giữ nguyên tên các cột không nhận diện được.
    """

    if df is None:
        raise ValueError("Không có dữ liệu để chuẩn hóa.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Dữ liệu đầu vào phải là pandas DataFrame.")

    if df.empty and len(df.columns) == 0:
        raise ValueError("File không có cột dữ liệu.")

    result = df.copy()
    mapping = {}

    alias_lookup = {}

    for standard_name, aliases in ALIASES.items():
        for alias in aliases:
            alias_lookup[_clean_name(alias)] = standard_name

    for column in result.columns:
        clean = _clean_name(column)

        if clean in alias_lookup:
            mapping[column] = alias_lookup[clean]

    result = result.rename(columns=mapping)

    # Nếu hai cột cùng được nhận diện thành một tên chuẩn,
    # giữ cột có dữ liệu trước, bổ sung giá trị thiếu từ cột sau.
    if result.columns.duplicated().any():
        merged_columns = {}

        for column in result.columns:
            if column not in merged_columns:
                merged_columns[column] = result[column]
            else:
                merged_columns[column] = (
                    merged_columns[column].combine_first(
                        result[column]
                    )
                )

        result = pd.DataFrame(merged_columns)

    return result, mapping


# =========================================================
# 7. CHUẨN HÓA DỮ LIỆU OHLCV
# =========================================================

def normalize_market_data(df, symbol=""):
    """
    Chuẩn hóa dữ liệu OHLCV.

    Yêu cầu:
        date, open, high, low, close, volume

    Không tự điền giá bị thiếu.
    Không tự tạo dữ liệu giả.
    """

    result, mapping = normalize_columns(df)

    required = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    missing = [
        column for column in required
        if column not in result.columns
    ]

    if missing:
        raise ValueError(
            "Thiếu cột bắt buộc: " + ", ".join(missing)
        )

    result["date"] = pd.to_datetime(
        result["date"],
        errors="coerce"
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:
        result[column] = _numeric_series(
            result[column]
        )

    if "symbol" not in result.columns:
        result["symbol"] = (
            str(symbol).strip().upper()
            if symbol else ""
        )
    else:
        result["symbol"] = (
            result["symbol"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        if symbol:
            result.loc[
                result["symbol"].isin(["", "NAN", "NONE"]),
                "symbol"
            ] = str(symbol).strip().upper()

    # Chỉ loại các dòng thiếu trường OHLCV bắt buộc.
    result = result.dropna(
        subset=required,
        how="any"
    )

    result = result.sort_values(
        ["symbol", "date"],
        kind="stable"
    ).reset_index(drop=True)

    return result, mapping


# =========================================================
# 8. KIỂM TRA DỮ LIỆU
# =========================================================

def validate_table(df):
    """
    Kiểm tra cấu trúc và chất lượng OHLCV.

    Chỉ cảnh báo, không tự sửa dữ liệu.
    """

    issues = []

    if df is None or df.empty:
        return ["Bảng dữ liệu đang trống."]

    required = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        return [
            "Thiếu cột: " + ", ".join(missing)
        ]

    # Kiểm tra ngày.
    dates = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    if dates.isna().any():
        issues.append(
            f"Có {int(dates.isna().sum())} dòng ngày giao dịch không hợp lệ."
        )

    # Kiểm tra kiểu số.
    numeric_data = {}

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]:
        numeric_data[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid_count = int(
            numeric_data[column].isna().sum()
        )

        if invalid_count:
            issues.append(
                f"Cột {column} có {invalid_count} giá trị không phải số."
            )

    valid_prices = pd.DataFrame(numeric_data)

    valid_prices = valid_prices.dropna(
        subset=["open", "high", "low", "close"]
    )

    if not valid_prices.empty:
        non_positive = (
            valid_prices[
                ["open", "high", "low", "close"]
            ] <= 0
        ).any(axis=1)

        if non_positive.any():
            issues.append(
                f"Có {int(non_positive.sum())} dòng có giá OHLC nhỏ hơn hoặc bằng 0."
            )

        invalid_ohlc = (
            (
                valid_prices["high"]
                < valid_prices[
                    ["open", "close", "low"]
                ].max(axis=1)
            )
            |
            (
                valid_prices["low"]
                > valid_prices[
                    ["open", "close", "high"]
                ].min(axis=1)
            )
        )

        if invalid_ohlc.any():
            issues.append(
                f"Có {int(invalid_ohlc.sum())} dòng sai quan hệ OHLC."
            )

    volume = numeric_data["volume"]

    negative_volume = volume < 0

    if negative_volume.any():
        issues.append(
            f"Có {int(negative_volume.sum())} dòng có khối lượng âm."
        )

    # Kiểm tra trùng mã/ngày.
    duplicate_keys = (
        ["symbol", "date"]
        if "symbol" in df.columns
        else ["date"]
    )

    duplicate_mask = df.duplicated(
        subset=duplicate_keys,
        keep=False
    )

    if duplicate_mask.any():
        issues.append(
            f"Có {int(duplicate_mask.sum())} dòng trùng khóa "
            f"{'symbol + date' if 'symbol' in df.columns else 'date'}."
        )

    return issues


# =========================================================
# 9. GHÉP DỮ LIỆU CŨ VÀ MỚI
# =========================================================

def merge_old_and_new(old_df, new_df, keys=None):
    """
    Ghép dữ liệu cũ và mới.

    Quy tắc:
    - Dữ liệu mới được ưu tiên khi trùng khóa.
    - Không tự cộng khối lượng.
    - Không tự tính trung bình giá.
    - Trả về số dòng trùng đã loại bỏ.
    """

    if old_df is None or new_df is None:
        raise ValueError("Dữ liệu cũ hoặc dữ liệu mới đang trống.")

    old_df = old_df.copy()
    new_df = new_df.copy()

    if keys is None:
        if (
            "symbol" in old_df.columns
            and "symbol" in new_df.columns
            and "date" in old_df.columns
            and "date" in new_df.columns
        ):
            keys = ["symbol", "date"]
        elif (
            "date" in old_df.columns
            and "date" in new_df.columns
        ):
            keys = ["date"]
        else:
            raise ValueError(
                "Không tìm được khóa mặc định để ghép dữ liệu."
            )

    keys = list(keys)

    if not keys:
        raise ValueError("Phải chọn ít nhất một cột khóa.")

    missing_keys = [
        key for key in keys
        if key not in old_df.columns
        or key not in new_df.columns
    ]

    if missing_keys:
        raise ValueError(
            "Thiếu cột khóa: " + ", ".join(missing_keys)
        )

    # Chuẩn hóa ngày để tránh cùng ngày nhưng khác kiểu dữ liệu.
    if "date" in keys:
        old_df["date"] = pd.to_datetime(
            old_df["date"],
            errors="coerce"
        )

        new_df["date"] = pd.to_datetime(
            new_df["date"],
            errors="coerce"
        )

    # Chuẩn hóa mã cổ phiếu.
    if "symbol" in keys:
        old_df["symbol"] = (
            old_df["symbol"].astype(str).str.strip().str.upper()
        )

        new_df["symbol"] = (
            new_df["symbol"].astype(str).str.strip().str.upper()
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

    removed = before - len(combined)

    # Sắp xếp theo mã và ngày nếu có.
    sort_columns = [
        column for column in ["symbol", "date"]
        if column in combined.columns
    ]

    if sort_columns:
        combined = combined.sort_values(
            sort_columns,
            kind="stable"
        )

    combined = combined.reset_index(drop=True)

    return combined, removed


# =========================================================
# 10. DANH SÁCH FILE ĐÃ LƯU
# =========================================================

def list_saved_files():
    """
    Liệt kê file CSV/XLSX trong kho Tab 5.

    Không hiển thị file backup.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    files = []

    for path in DATA_DIR.iterdir():
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".csv", ".xlsx"}:
            continue

        if "_backup" in path.stem.lower():
            continue

        files.append(path.name)

    return sorted(files)


# =========================================================
# 11. ĐỌC FILE ĐÃ LƯU
# =========================================================

def load_saved_file(filename):
    """Đọc một file CSV/XLSX trong kho Tab 5."""

    path = _get_saved_path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file: {path.name}"
        )

    if path.suffix.lower() == ".csv":
        return pd.read_csv(
            path,
            encoding="utf-8-sig"
        )

    return pd.read_excel(path)


# =========================================================
# 12. LƯU THÀNH FILE MỚI
# =========================================================

def save_new_file(df, filename, file_type="xlsx"):
    """
    Lưu file mới.

    Không ghi đè file đã tồn tại.
    """

    if df is None:
        raise ValueError("Không có dữ liệu để lưu.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Dữ liệu lưu phải là DataFrame.")

    if df.empty:
        raise ValueError("Không thể lưu bảng dữ liệu trống.")

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_name = Path(
        str(filename).strip()
    ).stem.strip()

    if not safe_name:
        raise ValueError("Tên file không được để trống.")

    safe_name = _safe_filename(safe_name)

    file_type = str(file_type).lower().lstrip(".")

    if file_type not in {"csv", "xlsx"}:
        raise ValueError("Chỉ hỗ trợ định dạng CSV hoặc XLSX.")

    extension = "." + file_type
    path = DATA_DIR / f"{safe_name}{extension}"

    if path.exists():
        raise FileExistsError(
            f"File {path.name} đã tồn tại. "
            "Hãy chọn tên khác để tránh ghi đè dữ liệu."
        )

    if file_type == "csv":
        df.to_csv(
            path,
            index=False,
            encoding="utf-8-sig"
        )
    else:
        df.to_excel(
            path,
            index=False,
            engine="openpyxl"
        )

    return path


# =========================================================
# 13. CẬP NHẬT FILE CŨ VÀ SAO LƯU
# =========================================================

def update_saved_file(df_new, filename, keys=None):
    """
    Cập nhật file cũ.

    Quy trình:
    1. Đọc file cũ.
    2. Ghép dữ liệu mới.
    3. Dòng mới thay thế dòng cũ nếu trùng khóa.
    4. Tạo backup trước khi cập nhật.
    5. Ghi dữ liệu mới bằng file tạm.
    6. Chỉ thay file chính sau khi ghi file tạm thành công.

    Trả về:
        merged, duplicate_count, backup_path
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = _get_saved_path(filename)

    if not path.exists():
        raise FileNotFoundError(
            "File cần cập nhật không tồn tại."
        )

    if df_new is None or df_new.empty:
        raise ValueError(
            "Dữ liệu mới đang trống, không thực hiện cập nhật."
        )

    # Đọc dữ liệu cũ.
    if path.suffix.lower() == ".csv":
        old_df = pd.read_csv(
            path,
            encoding="utf-8-sig"
        )
    elif path.suffix.lower() == ".xlsx":
        old_df = pd.read_excel(path)
    else:
        raise ValueError(
            "Chỉ cập nhật file CSV hoặc XLSX."
        )

    # Ghép dữ liệu.
    merged, duplicate_count = merge_old_and_new(
        old_df,
        df_new,
        keys=keys
    )

    # Tạo tên backup duy nhất.
    backup_path = path.with_name(
        path.stem + "_backup" + path.suffix
    )

    counter = 1

    while backup_path.exists():
        backup_path = path.with_name(
            f"{path.stem}_backup_{counter}{path.suffix}"
        )
        counter += 1

    # Sao lưu file gốc trước khi thay đổi.
    backup_path.write_bytes(
        path.read_bytes()
    )

    # Ghi ra file tạm trước.
    temp_path = path.with_name(
        path.stem + "_updating" + path.suffix
    )

    try:
        if path.suffix.lower() == ".csv":
            merged.to_csv(
                temp_path,
                index=False,
                encoding="utf-8-sig"
            )
        else:
            merged.to_excel(
                temp_path,
                index=False,
                engine="openpyxl"
            )

        # Thay file chính sau khi ghi file tạm thành công.
        temp_path.replace(path)

    except Exception:
        if temp_path.exists():
            temp_path.unlink()

        raise

    return merged, duplicate_count, backup_path


# =========================================================
# 14. XUẤT CSV
# =========================================================

def to_csv_bytes(df):
    """Xuất DataFrame thành CSV UTF-8-SIG."""

    if df is None:
        raise ValueError("Không có dữ liệu để xuất.")

    return df.to_csv(
        index=False
    ).encode("utf-8-sig")


# =========================================================
# 15. XUẤT EXCEL
# =========================================================

def to_excel_bytes(df):
    """Xuất DataFrame thành file XLSX trong bộ nhớ."""

    if df is None:
        raise ValueError("Không có dữ liệu để xuất.")

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Data"
        )

    output.seek(0)

    return output.getvalue()

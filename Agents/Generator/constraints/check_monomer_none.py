"""
Read evaluation CSV files from a directory and report rows where
SMILES1 or SMILES2 (monomer1, monomer2) are None, empty, or missing.
"""

import csv
import io
from pathlib import Path


# Column names used in evaluation CSV (monomer1 = SMILES1, monomer2 = SMILES2)
SMILES1_COL = "SMILES1"
SMILES2_COL = "SMILES2"


def _is_none_or_empty(value: str | None) -> bool:
    """Treat None, 'None', and blank as missing."""
    if value is None:
        return True
    s = str(value).strip()
    return s == "" or s.lower() == "none"


def _read_csv_text(csv_path: Path) -> tuple[str, str | None]:
    """
    Read file as bytes then decode. Returns (decoded_text, encoding_used).
    Tries utf-8, then cp1252, then latin-1. encoding_used is None if utf-8 worked.
    """
    raw = csv_path.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), enc if enc != "utf-8" else None
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8 (replace)"


def _find_bad_utf8_position(csv_path: Path) -> None:
    """Report exact line number and which CSV field contains the invalid UTF-8 byte."""
    raw = csv_path.read_bytes()
    try:
        raw.decode("utf-8")
        return
    except UnicodeDecodeError as e:
        pos = e.start
        bad_byte = raw[pos : pos + 1]
        # Exact physical line number (1-based)
        line_no = 1 + raw[:pos].count(b"\n")
        snippet_start = max(0, pos - 40)
        snippet_end = min(len(raw), pos + 40)
        snippet = raw[snippet_start:snippet_end]

        print(f"  Invalid UTF-8 in: {csv_path}")
        print(f"  Byte position: {pos}")
        print(f"  Exact line number: {line_no}")
        print(f"  Bad byte: 0x{bad_byte.hex()} = {bad_byte!r} (e.g. © in CP1252)")
        print(f"  Context: {snippet!r}")

        # Decode with fallback to find which CSV field contains the bad character
        try:
            decoded = raw.decode("cp1252")
            # In CP1252, 0xa9 is '©'
            bad_char = bad_byte.decode("cp1252")
        except Exception:
            bad_char = "\x00"  # fallback: look for nothing, we'll skip field name
        else:
            buf = io.StringIO(decoded)
            reader = csv.reader(buf)
            try:
                header = next(reader)
            except StopIteration:
                header = []
            for row_index, row in enumerate(reader):
                for col_index, cell in enumerate(row):
                    if bad_char in cell:
                        field_name = header[col_index] if col_index < len(header) else f"column_{col_index + 1}"
                        # CSV row 1 = header, row 2 = first data row
                        csv_row_one_based = row_index + 2
                        print(f"  CSV row number: {csv_row_one_based} (data row {row_index + 1})")
                        print(f"  Field name: {field_name}")
                        snippet_cell = cell[:60] + "..." if len(cell) > 60 else cell
                        print(f"  Field value (excerpt): {snippet_cell!r}")
                        return
            print("  (Could not determine field; CSV structure may have newlines inside fields.)")


def check_evaluation_csv(csv_path: Path) -> dict:
    """
    Read one evaluation CSV and return counts:
    - total_rows
    - rows_with_smiles1_none
    - rows_with_smiles2_none
    - rows_with_both_none
    - rows_ok (both SMILES present)
    - none_sl_list (SL values where either monomer is None)
    """
    result = {
        "total_rows": 0,
        "rows_with_smiles1_none": 0,
        "rows_with_smiles2_none": 0,
        "rows_with_both_none": 0,
        "rows_ok": 0,
        "none_sl_list": [],
    }

    text, fallback_enc = _read_csv_text(csv_path)
    if fallback_enc:
        print(f"  (Used encoding {fallback_enc} for {csv_path.name})")
        _find_bad_utf8_position(csv_path)

    reader = csv.DictReader(io.StringIO(text))
    if SMILES1_COL not in reader.fieldnames or SMILES2_COL not in reader.fieldnames:
        return result

    for row in reader:
        result["total_rows"] += 1
        sl = row.get("SL", "")
        v1 = row.get(SMILES1_COL)
        v2 = row.get(SMILES2_COL)
        m1_missing = _is_none_or_empty(v1)
        m2_missing = _is_none_or_empty(v2)

        if m1_missing:
            result["rows_with_smiles1_none"] += 1
        if m2_missing:
            result["rows_with_smiles2_none"] += 1
        if m1_missing and m2_missing:
            result["rows_with_both_none"] += 1
        if not m1_missing and not m2_missing:
            result["rows_ok"] += 1
        if m1_missing or m2_missing:
            result["none_sl_list"].append(sl)

    return result


def check_directory(dir_path: str | Path) -> None:
    """Find all evaluation CSVs in directory (and subdirs) and print None checks."""
    base = Path(dir_path)
    if not base.is_dir():
        print(f"Directory does not exist: {base}")
        return

    # Look for *_evaluation.csv or any CSV that might be evaluation format
    csv_files = sorted(base.rglob("*_evaluation.csv"))
    if not csv_files:
        csv_files = sorted(base.glob("*.csv"))

    if not csv_files:
        print(f"No CSV files found in {base}")
        return

    print(f"Found {len(csv_files)} CSV file(s) in {base}\n")

    total_rows_all = 0
    total_none_any = 0
    total_ok = 0

    for csv_path in csv_files:
        try:
            rel = csv_path.relative_to(base)
        except ValueError:
            rel = csv_path.name
        info = check_evaluation_csv(csv_path)

        total_rows_all += info["total_rows"]
        none_any = info["rows_with_smiles1_none"] + info["rows_with_smiles2_none"]
        # Avoid double-counting both-none; count rows with at least one None
        rows_with_any_none = len(info["none_sl_list"])
        total_none_any += rows_with_any_none
        total_ok += info["rows_ok"]

        print(f"  {rel}")
        print(f"    Total rows:        {info['total_rows']}")
        print(f"    SMILES1 None/empty: {info['rows_with_smiles1_none']}")
        print(f"    SMILES2 None/empty: {info['rows_with_smiles2_none']}")
        print(f"    Both None/empty:   {info['rows_with_both_none']}")
        print(f"    Rows OK (both set): {info['rows_ok']}")
        if info["none_sl_list"]:
            preview = info["none_sl_list"][:10]
            more = len(info["none_sl_list"]) - 10
            print(f"    SL with any None:  {preview}" + (f" ... +{more} more" if more > 0 else ""))
        print()

    print("--- Summary ---")
    print(f"Total rows across files: {total_rows_all}")
    print(f"Rows with at least one monomer None/empty: {total_none_any}")
    print(f"Rows with both monomers set: {total_ok}")


if __name__ == "__main__":
    directory = "RLHF_TSMP/src/Evaluations/Output/GRPO/DeepSeek"
    check_directory(directory)

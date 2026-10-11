"""月ごとの売上明細CSVをまとめて整形し、月別・カテゴリ別に集計するデモ。

    python clean_sales.py
    python clean_sales.py --input input --output output

標準ライブラリのみで動作します（Python 3.9 以降）。
入力データはすべて架空のものです。
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

COLUMNS = ["伝票番号", "日付", "取引先", "商品カテゴリ", "数量", "単価", "金額"]

# 月によって違う列名を、共通の列名に読み替える
HEADER_ALIASES = {
    "伝票No": "伝票番号",
    "売上日": "日付",
    "取引先名": "取引先",
    "カテゴリ": "商品カテゴリ",
    "売上金額": "金額",
}

COMPANY_ABBREVIATIONS = {"(株)": "株式会社", "(有)": "有限会社"}
DATE_PATTERN = re.compile(r"^(\d{4})[/\-年.](\d{1,2})[/\-月.](\d{1,2})日?$")


def normalize_text(value: str | None) -> str:
    """全角英数・半角カナ・㈱などを統一し、前後と途中の余分な空白を取り除く。"""
    text = unicodedata.normalize("NFKC", value or "")
    for short, full in COMPANY_ABBREVIATIONS.items():
        text = text.replace(short, full)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value: str) -> date | None:
    """2026/7/3・2026-07-03・2026年7月3日 などを日付として読む。読めなければ None。"""
    match = DATE_PATTERN.match(value.replace(" ", ""))
    if not match:
        return None
    try:
        return date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    """「1,200」「¥1,200」「1200円」などを整数として読む。読めなければ None。"""
    digits = re.sub(r"[,¥円\s]", "", value)
    return int(digits) if digits.isdigit() else None


def read_rows(path: Path) -> list[dict[str, str]]:
    """UTF-8 と Shift_JIS(cp932) を自動判定して読み込み、列名をそろえる。"""
    for encoding in ("utf-8-sig", "cp932"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"文字コードを判定できません: {path.name}")

    reader = csv.reader(text.splitlines())
    header = [HEADER_ALIASES.get(normalize_text(h), normalize_text(h)) for h in next(reader)]
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        raise ValueError(f"{path.name} に必要な列がありません: {', '.join(missing)}")

    rows = []
    for line_no, values in enumerate(reader, start=2):
        row = dict(zip(header, values))
        row["元ファイル"] = path.name
        row["元の行番号"] = str(line_no)
        rows.append(row)
    return rows


def clean(rows: list[dict[str, str]]):
    """行を「整形済み」と「要確認」に振り分ける。判断できない行は捨てずに要確認へ回す。"""
    cleaned: list[dict] = []
    review: list[dict] = []
    stats = {"読み込み": len(rows), "空行": 0, "重複": 0}
    seen: dict[str, tuple] = {}

    for raw in rows:
        values = {c: normalize_text(raw.get(c)) for c in COLUMNS}
        if not any(values.values()):
            stats["空行"] += 1
            continue

        day = parse_date(values["日付"])
        qty, price, amount = (parse_int(values[c]) for c in ("数量", "単価", "金額"))

        reasons = []
        if not values["伝票番号"]:
            reasons.append("伝票番号が空欄")
        if day is None:
            reasons.append("日付を読み取れない")
        for label, number in (("数量", qty), ("単価", price), ("金額", amount)):
            if number is None:
                reasons.append(f"{label}が空欄または数値でない")
        if None not in (qty, price, amount) and qty * price != amount:
            reasons.append(f"数量×単価（{qty * price}）と金額が一致しない")

        # 整形後の内容が完全に同じ行は、二重入力とみなして1件にまとめる
        key = tuple(values.values())
        slip = values["伝票番号"]
        if slip and slip in seen:
            if seen[slip] == key:
                stats["重複"] += 1
                continue
            reasons.append("同じ伝票番号で内容が異なる行がある")
        elif slip:
            seen[slip] = key

        source = {"元ファイル": raw["元ファイル"], "元の行番号": raw["元の行番号"]}
        if reasons:
            review.append({**values, **source, "確認理由": " / ".join(reasons)})
        else:
            cleaned.append(
                {**values, "日付": day.isoformat(), "数量": qty, "単価": price, "金額": amount}
            )

    cleaned.sort(key=lambda r: (r["日付"], r["伝票番号"]))
    stats["整形済み"] = len(cleaned)
    stats["要確認"] = len(review)
    return cleaned, review, stats


def summarize(cleaned: list[dict]) -> list[dict]:
    """月×商品カテゴリごとに、件数・数量・金額を合計する。"""
    totals: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0])
    for row in cleaned:
        bucket = totals[(row["日付"][:7], row["商品カテゴリ"])]
        bucket[0] += 1
        bucket[1] += row["数量"]
        bucket[2] += row["金額"]
    return [
        {"年月": month, "商品カテゴリ": category, "件数": n, "数量合計": qty, "金額合計": amount}
        for (month, category), (n, qty, amount) in sorted(totals.items())
    ]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    # Excelでそのまま開けるよう、BOM付きUTF-8で書き出す
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report(files: list[Path], stats: dict, cleaned: list[dict]) -> str:
    lines = [
        "売上明細 整形・集計レポート（架空データによるデモ）",
        "=" * 40,
        f"入力ファイル   : {len(files)}件（{', '.join(f.name for f in files)}）",
        f"読み込んだ行   : {stats['読み込み']}行",
        f"  空行を除外   : {stats['空行']}行",
        f"  重複を除外   : {stats['重複']}行",
        f"  要確認へ分離 : {stats['要確認']}行 → needs_review.csv",
        f"  整形済み     : {stats['整形済み']}行 → cleaned_sales.csv",
        f"整形済みの金額合計: {sum(r['金額'] for r in cleaned):,}円",
    ]
    accounted = stats["空行"] + stats["重複"] + stats["要確認"] + stats["整形済み"]
    check = "OK" if accounted == stats["読み込み"] else "NG"
    lines.append(f"行数の検算     : {accounted} / {stats['読み込み']} … {check}")
    return "\n".join(lines) + "\n"


def main() -> None:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description="売上明細CSVの整形と月別集計（デモ）")
    parser.add_argument("--input", type=Path, default=here / "input", help="入力CSVのフォルダ")
    parser.add_argument("--output", type=Path, default=here / "output", help="出力先のフォルダ")
    args = parser.parse_args()

    files = sorted(args.input.glob("*.csv"))
    if not files:
        raise SystemExit(f"CSVファイルが見つかりません: {args.input}")

    rows = [row for path in files for row in read_rows(path)]
    cleaned, review, stats = clean(rows)
    summary = summarize(cleaned)

    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "cleaned_sales.csv", cleaned, COLUMNS)
    write_csv(args.output / "needs_review.csv", review, COLUMNS + ["元ファイル", "元の行番号", "確認理由"])
    write_csv(
        args.output / "monthly_summary.csv", summary, ["年月", "商品カテゴリ", "件数", "数量合計", "金額合計"]
    )
    report = build_report(files, stats, cleaned)
    (args.output / "report.txt").write_text(report, encoding="utf-8")
    print(report, end="")


if __name__ == "__main__":
    main()

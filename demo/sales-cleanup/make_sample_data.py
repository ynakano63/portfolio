"""デモ用の架空データ（売上明細CSV）を生成するスクリプト。

実在の企業・取引・金額とは一切関係のない、乱数で作った架空データです。
現場でよくある「表記ゆれ」をわざと混ぜています。

    python make_sample_data.py

乱数のシードを固定しているため、何度実行しても同じファイルが生成されます。
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261011
INPUT_DIR = Path(__file__).parent / "input"

# 取引先（すべて架空）: 正式名 -> 入力時に起こりがちな表記ゆれ
CLIENTS = {
    "株式会社あおば商事": ["株式会社あおば商事", "㈱あおば商事", "（株）あおば商事", "(株)あおば商事 "],
    "ミナト工房": ["ミナト工房", "ﾐﾅﾄ工房", "ミナト工房　"],
    "ひかり文具店": ["ひかり文具店", " ひかり文具店", "ひかり文具店　"],
    "有限会社こもれび食堂": ["有限会社こもれび食堂", "㈲こもれび食堂", "（有）こもれび食堂"],
}

# 商品カテゴリ -> 単価の候補（円）
CATEGORIES = {
    "文具": [120, 280, 450],
    "梱包資材": [80, 650, 1200],
    "印刷物": [1500, 3200, 4800],
    "消耗品": [300, 980, 2400],
}

# 月ごとのファイル設定。列名や文字コードが月によって違う、という想定。
FILES = [
    {
        "name": "sales_2026-07.csv",
        "month": (2026, 7),
        "encoding": "utf-8-sig",
        "header": ["伝票番号", "日付", "取引先", "商品カテゴリ", "数量", "単価", "金額"],
    },
    {
        "name": "sales_2026-08.csv",
        "month": (2026, 8),
        "encoding": "cp932",  # Excelから保存したShift_JISのファイルを想定
        "header": ["伝票番号", "日付", "取引先", "商品カテゴリ", "数量", "単価", "金額"],
    },
    {
        "name": "sales_2026-09.csv",
        "month": (2026, 9),
        "encoding": "utf-8-sig",
        "header": ["伝票No", "売上日", "取引先名", "カテゴリ", "数量", "単価", "売上金額"],
    },
]

ROWS_PER_FILE = 40
ZENKAKU_DIGITS = str.maketrans("0123456789/", "０１２３４５６７８９／")


def messy_date(rng: random.Random, d: date) -> str:
    style = rng.choice(["slash", "slash", "iso", "kanji", "zenkaku"])
    if style == "iso":
        return d.isoformat()
    if style == "kanji":
        return f"{d.year}年{d.month}月{d.day}日"
    text = f"{d.year}/{d.month}/{d.day}"
    return text.translate(ZENKAKU_DIGITS) if style == "zenkaku" else text


def messy_number(rng: random.Random, n: int, money: bool) -> str:
    styles = ["plain", "plain", "comma", "zenkaku"]
    if money:
        styles += ["yen_mark", "yen_suffix"]
    style = rng.choice(styles)
    if style == "comma":
        return f"{n:,}"
    if style == "zenkaku":
        return str(n).translate(ZENKAKU_DIGITS)
    if style == "yen_mark":
        return f"￥{n:,}"
    if style == "yen_suffix":
        return f"{n}円"
    return str(n)


def build_rows(rng: random.Random, year: int, month: int, start_no: int) -> list[list[str]]:
    first = date(year, month, 1)
    days_in_month = ((first.replace(day=28) + timedelta(days=4)).replace(day=1) - first).days
    rows: list[list[str]] = []

    for i in range(ROWS_PER_FILE):
        d = first + timedelta(days=rng.randrange(days_in_month))
        client = rng.choice(list(CLIENTS))
        category = rng.choice(list(CATEGORIES))
        qty = rng.randint(1, 30)
        price = rng.choice(CATEGORIES[category])
        rows.append(
            [
                f"S{start_no + i:05d}",
                messy_date(rng, d),
                rng.choice(CLIENTS[client]),
                category,
                messy_number(rng, qty, money=False),
                messy_number(rng, price, money=True),
                messy_number(rng, qty * price, money=True),
            ]
        )

    # 人の確認が必要になる行を、月ごとに3件ずつ仕込む
    rows[5][6] = ""  # 金額が空欄
    rows[17][1] = "未定"  # 日付として読めない
    rows[29][6] = str(int(rows[29][6].translate(str.maketrans("０１２３４５６７８９", "0123456789"))
                          .replace(",", "").replace("￥", "").replace("円", "")) + 1000)  # 検算が合わない

    # 同じ伝票を二重に貼り付けてしまった行（3件）と、空行（2件）
    for idx in (8, 20, 33):
        rows.append(list(rows[idx]))
    rng.shuffle(rows)
    rows.insert(12, [""] * 7)
    rows.insert(30, [""] * 7)
    return rows


def main() -> None:
    rng = random.Random(SEED)
    INPUT_DIR.mkdir(exist_ok=True)
    start_no = 1
    for spec in FILES:
        year, month = spec["month"]
        rows = build_rows(rng, year, month, start_no)
        start_no += ROWS_PER_FILE
        path = INPUT_DIR / spec["name"]
        with path.open("w", encoding=spec["encoding"], newline="") as f:
            writer = csv.writer(f)
            writer.writerow(spec["header"])
            writer.writerows(rows)
        print(f"作成: {path.name}（{len(rows)}行, {spec['encoding']}）")


if __name__ == "__main__":
    main()

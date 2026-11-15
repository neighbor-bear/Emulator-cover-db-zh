# -*- coding: utf-8 -*-
"""统计各平台中文名覆盖率，直接输出 Markdown 表格（README 里的表就是它生成的）

用法:
    python zh_coverage.py            # 打印 Markdown 表
    python zh_coverage.py --csv      # 打印 CSV，方便贴进表格软件
    python zh_coverage.py --zh-only  # 只统计已有中文名的平台
"""
import argparse
import csv
import glob
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))

# 平台 key -> 中文简称（README 平台清单也用这份）
PLAT_NAME = {
    "nes": "FC", "ps1": "PS1", "ps2": "PS2", "nds": "NDS", "wii": "Wii",
    "gba": "GBA", "snes": "SFC", "md": "MD", "saturn": "SS", "3ds": "3DS",
    "ngc": "NGC", "psp": "PSP", "gb": "GB", "gbc": "GBC", "dc": "DC",
    "xbox": "XBOX", "n64": "N64", "gg": "GG", "pcecd": "PCE-CD",
    "segacd": "MCD", "sms": "SMS", "pce": "PCE", "wiiu": "WiiU",
    "ws": "WS", "wsc": "WSC", "neogeo": "NEOGEO", "32x": "32X",
    "ngpc": "NGPC", "ps3": "PS3", "psvita": "PSV", "ps3dl": "PS3DL",
}


def scan():
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "mapping", "mapping_*.csv"))):
        key = os.path.basename(path)[len("mapping_"):-len(".csv")]
        cnt = Counter()
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                cnt["total"] += 1
                mt = (r.get("match_type") or "").strip()
                has_cn = bool((r.get("name_cn") or "").strip())
                if mt == "exact" and has_cn:
                    cnt["exact"] += 1
                elif mt == "series" and has_cn:
                    cnt["series"] += 1
                elif has_cn:
                    cnt["manual"] += 1
                else:
                    cnt["none"] += 1
        cnt["key"] = key
        cnt["name"] = PLAT_NAME.get(key, key.upper())
        rows.append(cnt)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="store_true", help="输出 CSV 而不是 Markdown")
    ap.add_argument("--zh-only", action="store_true", help="只列已有中文名的平台")
    args = ap.parse_args()

    rows = scan()
    if not rows:
        sys.exit("找不到 mapping/mapping_*.csv，先跑 python zh_localize.py")
    rows.sort(key=lambda c: -c["total"])

    tot = Counter()
    for c in rows:
        for k in ("total", "exact", "series", "manual", "none"):
            tot[k] += c[k]

    def pct(a, b):
        return "%.1f%%" % (a / b * 100) if b else "-"

    if args.csv:
        print("key,平台,总条数,exact,series,manual,未匹配,中文覆盖率")
        for c in rows:
            cn = c["exact"] + c["series"] + c["manual"]
            print("%s,%s,%d,%d,%d,%d,%d,%s" % (
                c["key"], c["name"], c["total"], c["exact"], c["series"],
                c["manual"], c["none"], pct(cn, c["total"])))
        return

    print("| key | 平台 | 总条数 | exact | series | manual | 未匹配 | 中文覆盖率 |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")
    for c in rows:
        cn = c["exact"] + c["series"] + c["manual"]
        if args.zh_only and cn == 0:
            continue
        print("| %s | %s | %d | %d | %d | %d | %d | %s |" % (
            c["key"], c["name"], c["total"], c["exact"], c["series"],
            c["manual"], c["none"], pct(cn, c["total"])))
    cn = tot["exact"] + tot["series"] + tot["manual"]
    print("| **合计** | **30 平台** | **%d** | **%d** | **%d** | **%d** | **%d** | **%s** |" % (
        tot["total"], tot["exact"], tot["series"], tot["manual"], tot["none"],
        pct(cn, tot["total"])))


if __name__ == "__main__":
    main()

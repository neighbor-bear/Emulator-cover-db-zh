#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 libretro 全量索引 + 中文名库合成「中英对照映射表」。

匹配策略（三级）：
  1) exact  —— 归一化后精确命中 zh/zh_titles.csv
  2) series —— 命中 zh/zh_series.csv 系列名，中文系列名 + 原副标题（标记待校对）
  3) none   —— 没命中，name_cn 留空，等人工补

归一化会抹平这些差异，所以不用为每个平台的写法单独建表：
  - 区域/语言/版本标记（已在索引阶段剥离）
  - "系列 - 副标题" 与 "系列 副标题"
  - "Legend of Zelda, The - xxx" 这种 The 后置
  - 罗马数字 ↔ 阿拉伯数字（VII / 7）
  - Pokémon / Pokemon、& / and、标点与大小写

用法：
  python3 zh_localize.py                 # 全部平台
  python3 zh_localize.py --platforms psp ps2
  python3 zh_localize.py --stats         # 只看命中率
"""

import argparse
import csv
import os
import re
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(ROOT, "index")
ZH_DIR = os.path.join(ROOT, "zh")
MAP_DIR = os.path.join(ROOT, "mapping")
ZH_TITLES = os.path.join(ZH_DIR, "zh_titles.csv")
ZH_SERIES = os.path.join(ZH_DIR, "zh_series.csv")

REGION_PRIORITY = ["USA", "World", "Europe", "Japan", "Asia", "Korea", "China", "Hong Kong",
                   "Taiwan", "Australia", "Canada", "Brazil", "United Kingdom", "UK"]

OUT_FIELDS = ["system", "system_key", "retroarch_system", "folder", "game_name", "name_cn",
              "match_type", "region", "revision", "preferred", "search_key", "file",
              "boxart", "snap", "title"]

ROMAN = {"II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17,
         "XVIII": 18, "XIX": 19, "XX": 20}


def roman_to_arabic(text):
    """把独立的罗马数字词换成阿拉伯数字：'Final Fantasy VII' -> 'Final Fantasy 7'"""
    def rep(m):
        t = m.group(0).upper()
        return str(ROMAN[t]) if t in ROMAN else m.group(0)
    return re.sub(r"\b(XIII|XVIII|XVII|XVI|XIV|XV|XII|XI|IX|VIII|VII|VI|IV|V|III|II|X|I)\b",
                  rep, text)


def norm(s):
    """归一化：用于跨平台/跨写法的匹配键，不可逆，只做 join"""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = roman_to_arabic(s)
    s = s.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\bthe\b", " ", s)          # 抹平 "Legend of Zelda, The"
    return re.sub(r"\s+", " ", s).strip()


def load_titles():
    m = {}
    dup = 0
    if not os.path.exists(ZH_TITLES):
        return m, dup
    with open(ZH_TITLES, encoding="utf-8-sig") as fp:
        for row in csv.DictReader(fp):
            k = norm(row["game_name"])
            cn = (row.get("name_cn") or "").strip()
            if not k or not cn:
                continue
            if k in m and m[k] != cn:
                dup += 1
            m[k] = cn
    return m, dup


def load_series():
    lst = []
    if not os.path.exists(ZH_SERIES):
        return lst
    with open(ZH_SERIES, encoding="utf-8-sig") as fp:
        for row in csv.DictReader(fp):
            kw = norm(row["keyword_cn"])
            cn = (row.get("name_cn") or "").strip()
            if kw and cn:
                lst.append((kw, cn))
    lst.sort(key=lambda x: -len(x[0]))       # 长关键词优先，避免 "mario" 吃掉 "mario kart"
    return lst


def series_match(name, series):
    n = norm(name)
    for kw, cn in series:
        if n == kw:
            return cn, ""
        if n.startswith(kw + " "):
            toks = name.split()
            k = len(kw.split())
            rest = " ".join(toks[k:])
            rest = roman_to_arabic(rest)
            return cn, rest
    return None


BAD_REV = ("demo", "proto", "beta", "sample", "kiosk", "debug")


def rev_penalty(revision):
    r = (revision or "").lower()
    return 3 if any(b in r for b in BAD_REV) else 0


def region_rank(region):
    parts = [p.strip() for p in region.split(",") if p.strip()]
    best = 999
    for p in parts:
        if p in REGION_PRIORITY:
            best = min(best, REGION_PRIORITY.index(p))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platforms", nargs="*", help="只处理指定 system_key")
    ap.add_argument("--stats", action="store_true", help="只打印命中率，不写文件")
    args = ap.parse_args()

    os.makedirs(MAP_DIR, exist_ok=True)
    titles, dup = load_titles()
    series = load_series()
    print("中文名库：%d 条（冲突 %d）  系列词表：%d 条\n" % (len(titles), dup, len(series)))

    # 平台清单
    keys = []
    for f in sorted(os.listdir(INDEX_DIR)):
        if f.startswith("libretro_") and f.endswith(".csv"):
            keys.append(f[len("libretro_"):-4])
    if args.platforms:
        keys = [k for k in keys if k in args.platforms]

    stat = Counter()
    stat_by_plat = {}
    all_rows = []

    for key in keys:
        p = os.path.join(INDEX_DIR, "libretro_%s.csv" % key)
        with open(p, encoding="utf-8-sig") as fp:
            rows = list(csv.DictReader(fp))
        if not rows:
            continue

        # 同平台内按 (search_key) 分组挑首选区域
        best = {}
        for r in rows:
            sk = norm(r["game_name"])
            rk = region_rank(r["region"]) + rev_penalty(r["revision"])
            if sk not in best or rk < best[sk][0]:
                best[sk] = (rk, r["file"])

        out = []
        for r in rows:
            name = r["game_name"]
            sk = norm(name)
            cn, mtype = "", "none"
            if sk in titles:
                cn, mtype = titles[sk], "exact"
            else:
                hit = series_match(name, series)
                if hit:
                    base, rest = hit
                    cn = (base + (" " + rest if rest else "")).strip()
                    mtype = "series"
            stat[mtype] += 1

            out.append({
                "system": r["system"],
                "system_key": r["system_key"],
                "retroarch_system": r["retroarch_system"],
                "folder": r["folder"],
                "game_name": name,
                "name_cn": cn,
                "match_type": mtype,
                "region": r["region"],
                "revision": r["revision"],
                "preferred": "1" if best[sk][1] == r["file"] else "0",
                "search_key": sk,
                "file": r["file"],
                "boxart": r["boxart"],
                "snap": r["snap"],
                "title": r["title"],
            })

        stat_by_plat[key] = Counter(x["match_type"] for x in out)
        with open(os.path.join(MAP_DIR, "mapping_%s.csv" % key), "w", newline="",
                  encoding="utf-8-sig") as fp:
            w = csv.DictWriter(fp, fieldnames=OUT_FIELDS)
            w.writeheader()
            w.writerows(out)
        all_rows.extend(out)
        c = stat_by_plat[key]
        print("  %-8s 共 %5d  exact %5d  series %5d  none %5d"
              % (key, len(out), c["exact"], c["series"], c["none"]))

    total = sum(stat.values())
    print("\n合计 %d 条：exact %d (%.1f%%)  series %d (%.1f%%)  none %d (%.1f%%)"
          % (total, stat["exact"], 100.0 * stat["exact"] / max(total, 1),
             stat["series"], 100.0 * stat["series"] / max(total, 1),
             stat["none"], 100.0 * stat["none"] / max(total, 1)))

    if not args.stats:
        ap_path = os.path.join(MAP_DIR, "all_games.csv")
        with open(ap_path, "w", newline="", encoding="utf-8-sig") as fp:
            w = csv.DictWriter(fp, fieldnames=OUT_FIELDS)
            w.writeheader()
            w.writerows(all_rows)
        print("合并映射表：%s" % ap_path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描本地 ROM 文件夹，自动匹配 libretro 库里的游戏名，输出「本地文件 -> 封面 / 中文名」对照表。
给你的 Launcher、格式转换工具做刮削用。

匹配顺序：
  1) 文件名归一化后精确命中
  2) 去掉 (Disc 1) / [!] / (Rev 1) 等噪声后再命中
  3) difflib 模糊匹配（同首词优先，分数 >= 阈值才采用）

用法：
  python3 match_rom.py --dir /path/to/roms --platform psp
  python3 match_rom.py --dir /path/to/roms                # 不限平台
  python3 match_rom.py --dir /path/to/roms --threshold 0.6
"""

import argparse
import csv
import difflib
import os
import re
import sys

from zh_localize import norm, region_rank, rev_penalty, load_titles

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(ROOT, "index")
OUT_DIR = os.path.join(ROOT, "match")

ROM_EXT = {".iso", ".cso", ".chd", ".bin", ".cue", ".gdi", ".rvz", ".gcz", ".wbfs", ".wia",
           ".nsp", ".xci", ".nsz", ".zip", ".7z", ".rar", ".nes", ".sfc", ".smc", ".gba",
           ".gbc", ".gb", ".n64", ".z64", ".v64", ".nds", ".3ds", ".cia", ".gcm", ".wud",
           ".wux", ".xiso", ".img", ".mdf", ".pbp", ".cso", ".zso"}

NOISE = re.compile(
    r"[\(\[]\s*(?:USA|Europe|Japan|World|Asia|Korea|China|Taiwan|Hong Kong|Australia|"
    r"Brazil|Canada|France|Germany|Spain|Italy|Netherlands|Sweden|Russia|Portugal|"
    r"Disc\s*\d|Disk\s*\d|Side\s*[AB]|Rev\s*\w+|v\d[\d.]*|En|Ja|Fr|De|Es|It|Zh|Ko|"
    r"!|b|h|T\+?|Trainer|Beta|Proto|Demo|Sample)\s*[\)\]]", re.I)


def clean_stem(name):
    stem = os.path.splitext(name)[0]
    stem = re.sub(r"\.(iso|cso|chd|bin|rvz|gcz|nsp|xci|nsz|zip|7z)$", "", stem, flags=re.I)
    stem = NOISE.sub(" ", stem)
    stem = stem.replace("_", " ").replace(".", " ")
    return re.sub(r"\s+", " ", stem).strip()


def load_index(platform):
    path = os.path.join(INDEX_DIR, "all_games.csv")
    rows = []
    with open(path, encoding="utf-8-sig") as fp:
        for r in csv.DictReader(fp):
            if platform and r["system_key"] != platform:
                continue
            rows.append(r)
    exact, by_first = {}, {}
    for r in rows:
        k = norm(r["game_name"])
        if not k:
            continue
        exact.setdefault(k, []).append(r)
        by_first.setdefault(k.split(" ")[0], []).append((k, r))
    return rows, exact, by_first


def match(name, exact, by_first, threshold):
    stem = clean_stem(name)
    for candidate in (name, stem):
        k = norm(candidate)
        if k in exact:
            best = min(exact[k], key=lambda x: region_rank(x["region"]) + rev_penalty(x["revision"]))
            return best, 1.0, k
    k = norm(stem)
    pool = by_first.get(k.split(" ")[0], [])
    if not pool:
        return None, 0.0, k
    best, score = None, 0.0
    for key, r in pool[:5000]:
        s = difflib.SequenceMatcher(None, k, key).ratio()
        if s > score:
            best, score = r, s
    if score >= threshold:
        return best, score, k
    return None, score, k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="ROM 目录")
    ap.add_argument("--platform", default="", help="只匹配某平台，如 psp")
    ap.add_argument("--threshold", type=float, default=0.72)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        print("目录不存在：%s" % args.dir, file=sys.stderr)
        sys.exit(1)

    titles, _ = load_titles()
    print("载入索引…")
    rows, exact, by_first = load_index(args.platform)
    print("  参考条目 %d 个" % len(rows))

    roms = []
    for root, _, files in os.walk(args.dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in ROM_EXT:
                roms.append(os.path.join(root, f))
    roms.sort()
    print("发现 ROM %d 个" % len(roms))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = args.out or os.path.join(OUT_DIR, "rom_match_%s.csv" % (args.platform or "all"))
    hit = 0
    with open(out, "w", newline="", encoding="utf-8-sig") as fp:
        cols = ["rom_path", "rom_name", "matched_name", "name_cn", "region",
                "score", "cover_url", "snap_url", "status"]
        w = csv.DictWriter(fp, fieldnames=cols)
        w.writeheader()
        for p in roms:
            base = os.path.basename(p)
            r, score, key = match(base, exact, by_first, args.threshold)
            if r:
                hit += 1
            w.writerow({
                "rom_path": p,
                "rom_name": base,
                "matched_name": r["game_name"] if r else "",
                "name_cn": titles.get(norm(r["game_name"]), "") if r else "",
                "region": r["region"] if r else "",
                "score": "%.3f" % score,
                "cover_url": r["boxart"] if r else "",
                "snap_url": r["snap"] if r else "",
                "status": "hit" if r else "miss",
            })
    print("命中 %d / %d (%.1f%%)" % (hit, len(roms), 100.0 * hit / max(len(roms), 1)))
    print("输出：%s" % out)


if __name__ == "__main__":
    main()

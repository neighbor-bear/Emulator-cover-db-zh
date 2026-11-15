#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
刮削参考实现：从 cover-db.sqlite 查「ROM 文件名 -> 中文名 / 多译 / 封面 URL」。

这脚本就是给模拟器前端抄的样板：norm 归一化 + 文件名清洗 + 首选区域挑选 + 多译兜底，
四步和 C++ / Kotlin 版本要一模一样，才能和库里 77 661 条记录对上。

用法：
  python3 scrape_demo.py --db cover-db.sqlite --platform psp --name "007 - From Russia with Love (USA).iso"
  python3 scrape_demo.py --db cover-db.sqlite --platform psp --dir D:\\roms\\psp --limit 20
  python3 scrape_demo.py --db cover-db.sqlite --dir D:\\roms\\psp --download covers\\psp
  python3 scrape_demo.py --db cover-db.sqlite --search 口袋妖怪      # 中文反查
"""

import argparse
import csv
import difflib
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request

from zh_localize import norm, region_rank, rev_penalty

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://thumbnails.libretro.com"

NOISE = re.compile(
    r"[\(\[]\s*(?:USA|Europe|Japan|World|Asia|Korea|China|Taiwan|Hong Kong|Australia|"
    r"Brazil|Canada|France|Germany|Spain|Italy|Netherlands|Sweden|Russia|Portugal|"
    r"Disc\s*\d|Disk\s*\d|Side\s*[AB]|Rev\s*\w+|v\d[\d.]*|En|Ja|Fr|De|Es|It|Zh|Ko|"
    r"!|b|h|T\+?|Trainer|Beta|Proto|Demo|Sample)\s*[\)\]]", re.I)


def clean_stem(name):
    """ROM 文件名 -> 能拿去 norm 的英文名。和 match_rom.py 完全一致。"""
    stem = os.path.basename(name)
    stem = re.sub(r"\.(iso|cso|chd|bin|cue|gdi|rvz|gcz|wbfs|wia|nsp|xci|nsz|zip|7z|rar|"
                  r"nes|sfc|smc|gba|gbc|gb|n64|z64|v64|nds|3ds|cia|gcm|wud|wux|pbp)$",
                  "", stem, flags=re.I)
    stem = NOISE.sub(" ", stem)          # (USA) (Disc 1) [!] (Rev 1) (v1.02) 全抹掉
    stem = stem.replace("_", " ").replace(".", " ")
    return re.sub(r"\s+", " ", stem).strip()


def url_of(folder, file, kind="Boxarts"):
    """folder / file 都要 percent-encode，空格变 %20、括号 %28 %29、逗号 %2C。"""
    return "%s/%s/Named_%s/%s" % (BASE, urllib.parse.quote(folder),
                                  kind, urllib.parse.quote(file))


REGIONS = ("USA", "Europe", "Japan", "World", "Asia", "Korea", "China", "Taiwan",
           "Hong Kong", "Australia", "Brazil", "Canada", "France", "Germany", "Spain",
           "Italy", "Netherlands", "Sweden", "Russia", "Portugal")


def region_in(name):
    """从文件名里认出区域标记，用来优先挑同名同区的封面。"""
    for r in REGIONS:
        if re.search(r"[\(\[]\s*%s" % re.escape(r), name, re.I):
            return r
    return None


class Db:
    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.con.row_factory = sqlite3.Row

    def title(self, key):
        return self.con.execute(
            "SELECT game_name, name_cn, alias_cn FROM titles WHERE search_key=?", (key,)
        ).fetchone()

    def cover(self, key, platform, want_region=None):
        rows = self.con.execute(
            "SELECT * FROM covers WHERE search_key=? AND system_key=?", (key, platform)
        ).fetchall()
        if not rows:
            return None
        # 优先级：文件名里标的区域 > preferred=1 > 区域质量 > 修订号新
        return min(rows, key=lambda r: (0 if (want_region and r["region"] == want_region) else 1,
                                        -r["preferred"],
                                        region_rank(r["region"]),
                                        rev_penalty(r["revision"])))

    def keys(self, platform):
        return [r[0] for r in self.con.execute(
            "SELECT DISTINCT search_key FROM covers WHERE system_key=?", (platform,))]

    def by_zh(self, term, limit=20):
        return self.con.execute(
            "SELECT t.name_cn, t.alias_cn, t.game_name, c.system_key, c.folder, c.file "
            "FROM zh_index z JOIN titles t ON t.search_key=z.search_key "
            "JOIN covers c ON c.search_key=z.search_key AND c.preferred=1 "
            "WHERE z.term LIKE ? LIMIT ?", ("%" + term + "%", limit)).fetchall()


def scrape(db, name, platform, threshold, fuzzy=True, all_keys=None):
    stem = clean_stem(name)
    key = norm(stem)
    want = region_in(name)
    t = db.title(key)
    if t:
        return key, 1.0, t, db.cover(key, platform, want)

    # 兜底：同平台里做一次模糊匹配，只取首个单词相同的候选
    if fuzzy and all_keys:
        first = key.split(" ")[0]
        pool = [k for k in all_keys if k.split(" ")[0] == first][:5000]
        best, score = None, 0.0
        for k in pool:
            s = difflib.SequenceMatcher(None, key, k).ratio()
            if s > score:
                best, score = k, s
        if score >= threshold:
            return best, score, db.title(best), db.cover(best, platform, want)
        return key, score, None, None
    return key, 0.0, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "cover-db.sqlite"))
    ap.add_argument("--platform", help="平台 key，如 psp / ps2 / nes")
    ap.add_argument("--name", action="append", default=[], help="单个 ROM 文件名，可重复")
    ap.add_argument("--dir", help="扫这个目录下的 ROM 文件")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threshold", type=float, default=0.72)
    ap.add_argument("--no-fuzzy", action="store_true")
    ap.add_argument("--download", help="把封面存到这个目录")
    ap.add_argument("--out", help="把结果写成 CSV")
    ap.add_argument("--search", help="中文 / 多译反查（输 口袋妖怪 也能找到 宝可梦）")
    args = ap.parse_args()

    db = Db(args.db)
    if args.search:
        rows = db.by_zh(args.search)
        if not rows:
            print("没查到：%s" % args.search)
            return
        print("%-28s %-30s %-8s %s" % ("中文名", "其它叫法", "平台", "URL"))
        for r in rows:
            print("%-28s %-30s %-8s %s" % (r["name_cn"], r["alias_cn"][:30],
                                           r["system_key"], url_of(r["folder"], r["file"])))
        return

    names = list(args.name)
    if args.dir:
        for f in sorted(os.listdir(args.dir)):
            if os.path.isfile(os.path.join(args.dir, f)):
                names.append(f)
    if not names:
        sys.exit("给 --name 或 --dir")
    if args.limit:
        names = names[:args.limit]

    keys = db.keys(args.platform) if (args.platform and not args.no_fuzzy) else None
    out, hit = [], 0
    for n in names:
        key, score, t, c = scrape(db, n, args.platform, args.threshold,
                                  not args.no_fuzzy, keys)
        if t and c:
            hit += 1
            boxart = url_of(c["folder"], c["file"])
            print("%-46s | %-22s | %-5s | %.2f | %s" % (
                n[:46], t["name_cn"][:22], c["region"], score, boxart))
            if t["alias_cn"]:
                print("%-46s |   多译：%s" % ("", t["alias_cn"]))
            out.append({"file": n, "search_key": key, "name_cn": t["name_cn"],
                        "alias_cn": t["alias_cn"], "game_name": t["game_name"],
                        "platform": c["system_key"], "region": c["region"],
                        "preferred": c["preferred"], "boxart": boxart,
                        "snap": url_of(c["folder"], c["file"], "Snaps"),
                        "title_url": url_of(c["folder"], c["file"], "Titles")})
            if args.download:
                os.makedirs(args.download, exist_ok=True)
                dst = os.path.join(args.download, c["file"])
                if not os.path.exists(dst):
                    try:
                        urllib.request.urlretrieve(boxart, dst)
                    except Exception as e:
                        print("   下载失败：%s" % e)
        else:
            print("%-46s | 未匹配（key=%s，score=%.2f）" % (n[:46], key, score))
            out.append({"file": n, "search_key": key, "name_cn": "", "alias_cn": "",
                        "game_name": "", "platform": args.platform or "", "region": "",
                        "preferred": "", "boxart": "", "snap": "", "title_url": ""})

    print("\n命中 %d / %d" % (hit, len(names)))
    if args.out:
        with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
        print("结果已写 %s" % args.out)


if __name__ == "__main__":
    main()

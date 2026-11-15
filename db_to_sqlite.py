#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 mapping/*.csv 打成一个 SQLite 库，给模拟器 / 前端做刮削用。

三张表：
  titles       每个 search_key 一行：英文名、中文名、多译
  covers       每条平台记录一行：区域、preferred、folder / file（三种图 URL 由它们拼出）
  zh_index     中文名 + 每个别名 -> search_key，用来做「输中文反查游戏」

封面 URL 模板（folder 和 file 都要按 RFC 3986 做 percent-encode）：
  https://thumbnails.libretro.com/{folder}/Named_Boxarts/{file}
  https://thumbnails.libretro.com/{folder}/Named_Snaps/{file}
  https://thumbnails.libretro.com/{folder}/Named_Titles/{file}

用法：
  python3 db_to_sqlite.py                # 输出 cover-db.sqlite（省空间，不含完整 URL）
  python3 db_to_sqlite.py --with-urls    # 另外把三种完整 URL 存进表里
  python3 db_to_sqlite.py --no-index     # 不建中文反查表（体积更小）
"""

import argparse
import csv
import glob
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MAP_DIR = os.path.join(ROOT, "mapping")

BASE = "https://thumbnails.libretro.com/%s/%s/%s"


def schema(with_urls):
    covers_cols = """    search_key TEXT NOT NULL,
    system_key TEXT NOT NULL,
    region     TEXT,
    revision   TEXT,
    preferred  INTEGER NOT NULL DEFAULT 0,
    folder     TEXT,
    file       TEXT"""
    if with_urls:
        covers_cols += """,
    boxart     TEXT,
    snap       TEXT,
    title_url  TEXT"""
    return """
CREATE TABLE IF NOT EXISTS titles (
    search_key TEXT PRIMARY KEY,
    game_name  TEXT NOT NULL,
    name_cn    TEXT NOT NULL,
    alias_cn   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS covers (
%s
);
CREATE TABLE IF NOT EXISTS zh_index (
    term       TEXT NOT NULL,
    search_key TEXT NOT NULL
);
""" % covers_cols


INDEXES = """
CREATE INDEX IF NOT EXISTS idx_covers_key ON covers(search_key);
CREATE INDEX IF NOT EXISTS idx_covers_plat ON covers(system_key, preferred);
CREATE INDEX IF NOT EXISTS idx_zh_term ON zh_index(term);
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "cover-db.sqlite"))
    ap.add_argument("--with-urls", action="store_true", help="额外存三种完整 URL")
    ap.add_argument("--no-index", action="store_true", help="不建中文反查表 zh_index")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(MAP_DIR, "mapping_*.csv")))
    if not files:
        sys.exit("没找到 mapping/mapping_*.csv，先跑 zh_localize.py")

    if os.path.exists(args.out):
        os.remove(args.out)
    con = sqlite3.connect(args.out)
    con.executescript(schema(args.with_urls))

    titles = {}
    covers = []
    zh_rows = []
    for p in files:
        with open(p, encoding="utf-8-sig", newline="") as fp:
            for r in csv.DictReader(fp):
                if not r["name_cn"].strip():
                    continue
                k = r["search_key"]
                if k not in titles:
                    titles[k] = (k, r["game_name"], r["name_cn"].strip(), r["alias_cn"].strip())
                    zh_rows.append((r["name_cn"].strip(), k))
                    if r["alias_cn"].strip():
                        for a in r["alias_cn"].split("|"):
                            a = a.strip()
                            if a:
                                zh_rows.append((a, k))
                row = [k, r["system_key"], r["region"], r["revision"],
                       int(r["preferred"] or 0), r["folder"], r["file"]]
                if args.with_urls:
                    row += [r["boxart"], r["snap"], r["title"]]
                covers.append(tuple(row))

    con.executemany("INSERT OR IGNORE INTO titles VALUES (?,?,?,?)", titles.values())
    con.executemany("INSERT INTO covers VALUES (%s)" % ",".join("?" * len(covers[0])), covers)
    if not args.no_index:
        con.executemany("INSERT INTO zh_index VALUES (?,?)", zh_rows)
    con.executescript(INDEXES)
    con.commit()

    print("titles   %6d 条（唯一英文名）" % len(titles))
    print("covers   %6d 条（平台 × 区域 × 版本）" % len(covers))
    if not args.no_index:
        print("zh_index %6d 条（中文名 + 多译 -> search_key）" % len(zh_rows))
    print("体积     %.1f MB -> %s" % (os.path.getsize(args.out) / 1048576.0, args.out))
    con.close()


if __name__ == "__main__":
    main()

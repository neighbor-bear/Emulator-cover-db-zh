#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按映射表自动拉取封面到本地缓存，供前端 / 刮削器直接读本地文件。

特点：
  - 只传图片 URL，不打包图片入库；图片由官方源托管，你仓库里只有 CSV
  - 三级回退：首选区域 Boxart -> 其他区域同款 Boxart -> Snaps -> Titles
  - 校验 PNG 魔数，避免把 404 的 HTML 页当封面存下来
  - 断点续传：已存在且合法就跳过，可随时中断再跑
  - 产出 manifest_<平台>.csv，写清「本地路径 / 状态 / 字节数」，前端照着读即可

用法：
  python3 cover_fetch.py --platforms psp --limit 20            # 试跑
  python3 cover_fetch.py --platforms psp ps2 --concurrency 8   # 正式抓
  python3 cover_fetch.py --platforms ps1 --preferred-only      # 每款游戏只抓一张
  python3 cover_fetch.py --from-csv mapping/mapping_psp.csv
  python3 cover_fetch.py --platforms psp --only-cn             # 只抓已有中文名的
"""

import argparse
import csv
import os
import re
import sys
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from zh_localize import norm

ROOT = os.path.dirname(os.path.abspath(__file__))
MAP_DIR = os.path.join(ROOT, "mapping")
INDEX_DIR = os.path.join(ROOT, "index")
CACHE_DIR = os.path.join(ROOT, "cache")
MANIFEST_DIR = os.path.join(ROOT, "manifest")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) cover-db/1.0"
PNG_MAGIC = b"\x89PNG"
LOCK = threading.Lock()


def safe_name(fname):
    """保持原名（前端按原名匹配最省事），只替换掉路径非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", fname)


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            return r.read()
    except Exception:
        return None


def is_png(data):
    return bool(data) and data[:4] == PNG_MAGIC


def fetch_one(task):
    """task: dict(row, candidates[list of url], dest_dir)"""
    row = task["row"]
    dest = os.path.join(task["dest_dir"], safe_name(row["file"]))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        with open(dest, "rb") as f:
            head = f.read(4)
        if head[:4] == PNG_MAGIC:
            return (row, dest, "skip", os.path.getsize(dest), "")

    for url in task["candidates"]:
        data = http_get(url)
        if is_png(data):
            os.makedirs(task["dest_dir"], exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            return (row, dest, "ok", len(data), url)
    return (row, "", "fail", 0, "")


def build_candidates(row, alt_index):
    """构造回退链"""
    urls = [row["boxart"]]
    if row.get("search_key") in alt_index:
        for f in alt_index[row["search_key"]]:
            qf = urllib.parse.quote(f)
            qfolder = urllib.parse.quote(row["folder"])
            u = "https://thumbnails.libretro.com/%s/Named_Boxarts/%s" % (qfolder, qf)
            if u != row["boxart"]:
                urls.append(u)
    urls.append(row["snap"])
    urls.append(row["title"])
    return urls


def load_alt_index(platform_keys):
    """search_key -> [同款游戏的其他区域文件名]，用于跨区域回退"""
    alt = {}
    path = os.path.join(INDEX_DIR, "all_games.csv")
    if not os.path.exists(path):
        return alt
    with open(path, encoding="utf-8-sig") as fp:
        for r in csv.DictReader(fp):
            if platform_keys and r["system_key"] not in platform_keys:
                continue
            alt.setdefault(norm(r["game_name"]), []).append(r["file"])
    return alt


def run(csv_path, platform, args, alt_index):
    with open(csv_path, encoding="utf-8-sig") as fp:
        rows = list(csv.DictReader(fp))
    if args.preferred_only and rows and "preferred" in rows[0]:
        rows = [r for r in rows if r["preferred"] == "1"]
    if args.only_cn and rows and "name_cn" in rows[0]:
        rows = [r for r in rows if r["name_cn"].strip()]
    if args.limit:
        rows = rows[:args.limit]
    if not rows:
        print("  [%s] 无待处理记录" % platform)
        return

    dest_dir = os.path.join(CACHE_DIR, platform)
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(MANIFEST_DIR, exist_ok=True)

    tasks = [{"row": r,
              "dest_dir": dest_dir,
              "candidates": build_candidates(r, alt_index)} for r in rows]

    ok = skip = fail = 0
    total_bytes = 0
    done = 0
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(fetch_one, t) for t in tasks]
        for fu in as_completed(futs):
            row, dest, status, size, src = fu.result()
            results.append((row, dest, status, size, src))
            if status == "ok":
                ok += 1
                total_bytes += size
            elif status == "skip":
                skip += 1
            else:
                fail += 1
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print("  [%s] %d/%d  ok=%d skip=%d fail=%d  %.1f MB"
                      % (platform, done, len(tasks), ok, skip, fail, total_bytes / 1048576.0))

    results.sort(key=lambda x: x[0]["file"])
    man = os.path.join(MANIFEST_DIR, "manifest_%s.csv" % platform)
    with open(man, "w", newline="", encoding="utf-8-sig") as fp:
        cols = ["system", "system_key", "game_name", "name_cn", "region", "file",
                "local_path", "status", "bytes", "source_url", "boxart"]
        w = csv.DictWriter(fp, fieldnames=cols)
        w.writeheader()
        for row, dest, status, size, src in results:
            rel = os.path.relpath(dest, ROOT).replace("\\", "/") if dest else ""
            w.writerow({
                "system": row["system"], "system_key": row["system_key"],
                "game_name": row["game_name"], "name_cn": row.get("name_cn", ""),
                "region": row["region"], "file": row["file"],
                "local_path": rel, "status": status, "bytes": size,
                "source_url": src, "boxart": row["boxart"],
            })
    print("  清单：%s" % man)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platforms", nargs="*", default=[], help="平台 key，如 psp ps2 ps1 ngc")
    ap.add_argument("--from-csv", help="直接用指定映射表，不按平台推导")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="每个平台最多处理多少条（试跑用）")
    ap.add_argument("--preferred-only", action="store_true", help="每款游戏只抓首选区域一张")
    ap.add_argument("--only-cn", action="store_true", help="只抓已匹配到中文名的")
    args = ap.parse_args()

    jobs = []
    if args.from_csv:
        base = os.path.basename(args.from_csv)
        m = re.match(r"mapping_(.+)\.csv$", base)
        jobs.append((m.group(1) if m else "custom", args.from_csv))
    else:
        if not args.platforms:
            print("请用 --platforms 指定平台，或 --from-csv 指定映射表", file=sys.stderr)
            sys.exit(1)
        for k in args.platforms:
            p = os.path.join(MAP_DIR, "mapping_%s.csv" % k)
            if not os.path.exists(p):
                print("跳过 %s（没有 %s）" % (k, p), file=sys.stderr)
                continue
            jobs.append((k, p))

    alt_index = load_alt_index(set(k for k, _ in jobs))
    print("回退索引：%d 个游戏名" % len(alt_index))
    for k, p in jobs:
        print("[*] %s" % k)
        run(p, k, args, alt_index)


if __name__ == "__main__":
    main()

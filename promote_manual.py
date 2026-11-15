#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把映射表里人工填好的中文名回收进 zh/zh_titles.csv，下次重新生成不会白干。

场景：你打开 mapping/mapping_psp.csv，把 name_cn 空着的填上，然后跑这个脚本，
新填的名字就并入主词库，所有平台重新生成时都能命中。

用法：
  python3 promote_manual.py                   # 扫描 mapping/ 全部
  python3 promote_manual.py --dry-run         # 只看会新增多少，不写
"""

import argparse
import csv
import glob
import os

from zh_localize import norm, ZH_TITLES

ROOT = os.path.dirname(os.path.abspath(__file__))
MAP_DIR = os.path.join(ROOT, "mapping")


def load_existing():
    m = {}
    if not os.path.exists(ZH_TITLES):
        return m
    with open(ZH_TITLES, encoding="utf-8-sig") as fp:
        for row in csv.DictReader(fp):
            if row.get("name_cn"):
                m[norm(row["game_name"])] = row
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    existing = load_existing()
    new = {}
    for p in sorted(glob.glob(os.path.join(MAP_DIR, "mapping_*.csv"))):
        with open(p, encoding="utf-8-sig") as fp:
            for row in csv.DictReader(fp):
                cn = (row.get("name_cn") or "").strip()
                name = row.get("game_name") or ""
                if not cn or not name:
                    continue
                k = norm(name)
                if k in existing or k in new:
                    continue
                if row.get("match_type") in ("exact", "series"):
                    continue  # 已经是库里的，不用回收
                new[k] = {"game_name": name, "name_cn": cn,
                          "series": "", "alias": row.get("system_key", "")}

    print("待回收中文名：%d 条" % len(new))
    for k, v in list(new.items())[:10]:
        print("  + %-45s %s" % (v["game_name"][:44], v["name_cn"]))
    if not new or args.dry_run:
        return

    need_header = not os.path.exists(ZH_TITLES)
    with open(ZH_TITLES, "a", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=["game_name", "name_cn", "series", "alias"])
        if need_header:
            w.writeheader()
        for v in new.values():
            w.writerow(v)
    print("已追加到 %s" % ZH_TITLES)
    print("建议重新跑一次：python3 zh_localize.py")


if __name__ == "__main__":
    main()

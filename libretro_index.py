#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动抓取 libretro-thumbnails 全量封面清单，生成「平台 × 游戏 × 区域」CSV 映射表。

只用 Boxarts 目录的 HTML 索引来取文件名（同一文件名在 Snaps / Titles 目录下都存在），
因此每个平台只需 1 次请求，URL 由文件名拼出来，属"自动拉取"而非硬编码。

用法：
  python3 libretro_index.py                # 抓默认主力平台
  python3 libretro_index.py --all          # 抓目录里全部平台（127 个，耗时较长）
  python3 libretro_index.py --only psp ps2 # 只抓指定平台
  python3 libretro_index.py --list         # 列出支持的平台 key

产物：
  index/libretro_<key>.csv     单平台清单
  index/all_games.csv          全部平台合并清单
"""

import argparse
import csv
import html
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://thumbnails.libretro.com"
ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(ROOT, "index")

# key -> (中文平台名, libretro 目录名, RetroArch 系统标识)
PLATFORMS = {
    # ---- 索尼 ----
    "ps1":      ("PS1",  "Sony - PlayStation",                "psx"),
    "ps2":      ("PS2",  "Sony - PlayStation 2",              "ps2"),
    "psp":      ("PSP",  "Sony - PlayStation Portable",       "psp"),
    "ps3":      ("PS3",  "Sony - PlayStation 3",              "ps3"),
    "ps3dl":    ("PS3",  "Sony - PlayStation 3 (Downloadable)", "ps3"),
    "psvita":   ("PSV",  "Sony - PlayStation Vita",           "psvita"),
    # ---- 任天堂 ----
    "ngc":      ("NGC",  "Nintendo - GameCube",               "gc"),
    "wii":      ("Wii",  "Nintendo - Wii",                    "wii"),
    "wiiu":     ("WiiU", "Nintendo - Wii U",                  "wiiu"),
    "n64":      ("N64",  "Nintendo - Nintendo 64",            "n64"),
    "nds":      ("NDS",  "Nintendo - Nintendo DS",            "nds"),
    "3ds":      ("3DS",  "Nintendo - Nintendo 3DS",           "3ds"),
    "gba":      ("GBA",  "Nintendo - Game Boy Advance",       "gba"),
    "gbc":      ("GBC",  "Nintendo - Game Boy Color",         "gbc"),
    "gb":       ("GB",   "Nintendo - Game Boy",               "gb"),
    "nes":      ("FC",   "Nintendo - Nintendo Entertainment System", "nes"),
    "snes":     ("SFC",  "Nintendo - Super Nintendo Entertainment System", "snes"),
    "vb":       ("VB",   "Nintendo - Virtual Boy",            "vb"),
    # ---- 世嘉 ----
    "dc":       ("DC",   "Sega - Dreamcast",                  "dc"),
    "saturn":   ("SS",   "Sega - Saturn",                     "saturn"),
    "md":       ("MD",   "Sega - Mega Drive - Genesis",       "genesis"),
    "sms":      ("SMS",  "Sega - Master System - Mark III",   "sms"),
    "gg":       ("GG",   "Sega - Game Gear",                  "gamegear"),
    "segacd":   ("MCD",  "Sega - Mega-CD - Sega CD",          "segacd"),
    "32x":      ("32X",  "Sega - 32X",                        "32x"),
    "naomi":    ("NAOMI", "Sega - Naomi",                     "naomi"),
    # ---- 微软 / 其他 ----
    "xbox":     ("XBOX", "Microsoft - Xbox",                  "xbox"),
    "xbox360":  ("X360", "Microsoft - Xbox 360",              "xbox360"),
    "pce":      ("PCE",  "NEC - PC Engine - TurboGrafx 16",   "pce"),
    "pcecd":    ("PCE-CD", "NEC - PC Engine CD - TurboGrafx-CD", "pcecd"),
    "ngp":      ("NGP",  "SNK - Neo Geo Pocket",              "ngp"),
    "ngpc":     ("NGPC", "SNK - Neo Geo Pocket Color",        "ngpc"),
    "neogeo":   ("NEOGEO", "SNK - Neo Geo",                   "neogeo"),
    "ws":       ("WS",   "Bandai - WonderSwan",               "wswan"),
    "wsc":      ("WSC",  "Bandai - WonderSwan Color",         "wswanc"),
    "atari2600": ("A2600", "Atari - 2600",                    "atari2600"),
    "lynx":     ("LYNX", "Atari - Lynx",                      "lynx"),
    "jaguar":   ("JAG",  "Atari - Jaguar",                    "jaguar"),
    "3do":      ("3DO",  "The 3DO Company - 3DO",             "3do"),
    "msx":      ("MSX",  "Microsoft - MSX",                   "msx"),
    "msx2":     ("MSX2", "Microsoft - MSX2",                  "msx2"),
    "amiga":    ("Amiga", "Commodore - Amiga",                 "amiga"),
    "c64":      ("C64",  "Commodore - 64",                    "c64"),
    "dos":      ("DOS",  "DOS",                               "dos"),
    "scummvm":  ("ScummVM", "ScummVM",                        "scummvm"),
    "arcade":   ("ARCADE", "FBNeo - Arcade Games",            "fbneo"),
    "mame":     ("MAME", "MAME",                              "mame"),
}

DEFAULT_KEYS = [
    "ps1", "ps2", "psp", "ps3", "psvita",
    "ngc", "wii", "wiiu", "n64", "nds", "3ds", "gba", "gbc", "gb", "nes", "snes",
    "dc", "saturn", "md", "sms", "gg", "segacd", "32x",
    "xbox", "pce", "pcecd", "neogeo", "ngpc", "ws", "wsc",
]

# 区域 / 版本标记（出现在文件名末尾括号里）
REGIONS = [
    "USA", "Europe", "Japan", "World", "Asia", "China", "Hong Kong", "Taiwan",
    "Korea", "Australia", "Brazil", "Canada", "France", "Germany", "Spain",
    "Italy", "Netherlands", "Sweden", "Norway", "Denmark", "Finland", "Poland",
    "Russia", "Portugal", "Mexico", "Argentina", "India", "Indonesia", "Thailand",
    "United Kingdom", "UK", "Unknown", "Beta", "Proto", "Demo", "Sample",
    "Pirate", "Aftermarket", "Unl", "Unlicensed", "Bootleg", "Hack",
]
REGION_SET = {r.lower() for r in REGIONS}
PAREN_RE = re.compile(r"\(([^)]*)\)")

# 语言 / 其他标签，归入 extra
LANG_SET = {"en", "ja", "jp", "fr", "de", "es", "it", "nl", "pt", "ru", "ko", "zh",
            "sv", "no", "da", "fi", "pl", "cs", "hu", "tr", "ar", "he", "el", "ca"}

LINK_RE = re.compile(r'<a href="([^"]+\.png)"', re.I)


def fetch_listing(folder):
    """抓一个平台的 Boxarts 目录，返回 png 文件名列表（已做 URL 解码）"""
    url = "%s/%s/Named_Boxarts/" % (BASE, urllib.parse.quote(folder))
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) cover-db/1.0",
        "Accept-Encoding": "gzip, deflate",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                import gzip
                data = gzip.decompress(data)
            text = data.decode("utf-8", "ignore")
            names = [html.unescape(urllib.parse.unquote(n)) for n in LINK_RE.findall(text)]
            # 过滤掉子目录 / 非图标文件
            names = [n for n in names if "/" not in n]
            return sorted(set(names))
        except Exception as e:
            if attempt == 2:
                print("  [x] %s 抓取失败: %s" % (folder, e), file=sys.stderr)
                return []
            time.sleep(3)


def split_name(fname):
    """'007 - From Russia with Love (Asia) (En).png' -> ('007 - From Russia with Love', 'Asia', 'En')"""
    stem = re.sub(r"\.png$", "", fname, flags=re.I)
    groups = PAREN_RE.findall(stem)
    first = PAREN_RE.search(stem)
    base = stem[:first.start()].strip() if first else stem.strip()

    region, extra = "", []
    for g in groups:
        tokens = [t.strip() for t in g.split(",") if t.strip()]
        hit = [t for t in tokens if t.lower() in REGION_SET]
        if hit and not region:
            region = ", ".join(hit)
        else:
            extra.append(g.strip())
    return base, region, " / ".join(extra)


def build(key, folder, name_cn, sys_id, out_dir):
    print("[*] %s -> %s" % (name_cn, folder))
    t0 = time.time()
    files = fetch_listing(folder)
    if not files:
        return 0
    rows = []
    qfolder = urllib.parse.quote(folder)
    for f in files:
        game, region, rev = split_name(f)
        qf = urllib.parse.quote(f)
        rows.append({
            "system": name_cn,
            "system_key": key,
            "retroarch_system": sys_id,
            "folder": folder,
            "game_name": game,
            "region": region,
            "revision": rev,
            "file": f,
            "boxart": "%s/%s/Named_Boxarts/%s" % (BASE, qfolder, qf),
            "snap": "%s/%s/Named_Snaps/%s" % (BASE, qfolder, qf),
            "title": "%s/%s/Named_Titles/%s" % (BASE, qfolder, qf),
        })
    path = os.path.join(out_dir, "libretro_%s.csv" % key)
    with open(path, "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("    %d 条  %.1fs  -> %s" % (len(rows), time.time() - t0, os.path.basename(path)))
    return len(rows)


FIELDS = ["system", "system_key", "retroarch_system", "folder", "game_name",
          "region", "revision", "file", "boxart", "snap", "title"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只抓指定 key，如 psp ps2 ngc")
    ap.add_argument("--all", action="store_true", help="抓 PLATFORMS 中全部平台")
    ap.add_argument("--list", action="store_true", help="列出支持的平台 key")
    ap.add_argument("--jobs", type=int, default=4, help="并发数")
    args = ap.parse_args()

    if args.list:
        for k, (cn, folder, sysid) in sorted(PLATFORMS.items()):
            print("%-10s %-6s %s" % (k, cn, folder))
        return

    os.makedirs(INDEX_DIR, exist_ok=True)
    keys = args.only if args.only else (list(PLATFORMS) if args.all else DEFAULT_KEYS)
    bad = [k for k in keys if k not in PLATFORMS]
    if bad:
        print("未知 key: %s（用 --list 查看）" % bad, file=sys.stderr)
        sys.exit(1)

    total = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = []
        for k in keys:
            cn, folder, sysid = PLATFORMS[k]
            futs.append(ex.submit(build, k, folder, cn, sysid, INDEX_DIR))
        for f in futs:
            total += f.result() or 0

    # 合并
    all_path = os.path.join(INDEX_DIR, "all_games.csv")
    n = 0
    with open(all_path, "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=FIELDS)
        w.writeheader()
        for k in keys:
            p = os.path.join(INDEX_DIR, "libretro_%s.csv" % k)
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8-sig") as r:
                rd = csv.DictReader(r)
                for row in rd:
                    w.writerow({f: row.get(f, "") for f in FIELDS})
                    n += 1
    print("\n完成：%d 个平台 / %d 条记录" % (len(keys), n))
    print("合并清单：%s" % all_path)


if __name__ == "__main__":
    main()

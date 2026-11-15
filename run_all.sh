#!/usr/bin/env bash
# 一键跑全流程：抓索引 -> 生成映射表
# 封面和 ROM 匹配按需自己跑，避免一上来就下几个 G
set -e
cd "$(dirname "$0")"

echo "[1/2] 抓取 libretro 全量索引 ..."
python3 libretro_index.py --jobs 5

echo
echo "[2/2] 生成中英对照映射表 ..."
python3 zh_localize.py

echo
echo "完成。下一步可以："
echo "  python3 cover_fetch.py --platforms psp --limit 20     # 试抓封面"
echo "  python3 match_rom.py --dir /你的/rom目录 --platform psp"

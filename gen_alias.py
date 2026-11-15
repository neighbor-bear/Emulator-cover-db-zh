#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给 zh/zh_titles.csv 生成「中文多译」列 alias_cn。

做的是**术语级替换**：同一个 franchise 的不同中文叫法（宝可梦 / 口袋妖怪 / 口袋怪兽 /
宠物小精灵 / 神奇宝贝、马力欧 / 马里奥、索尼克 / 音速小子 …）互相展开，一行一个主名，
alias_cn 里放 `|` 分隔的其余叫法。

规则：
  - 每组取「名字里出现的最长那个变体」做锚点，只替换这一个，避免短词吃掉长词；
  - 多组同时命中时做组合（最多 MERGE_GROUPS 组、每行最多 MAX_ALIAS 个）；
  - 生成结果去重、去空、去掉等值，不含英文名的纯中文行不处理（不影响可读性，只是没别名）。

用法：
  python3 gen_alias.py            # 写回 zh/zh_titles.csv（自动备份）
  python3 gen_alias.py --dry      # 只统计，不写
  python3 gen_alias.py --table    # 另外输出 术语多译表.csv（给人工核对）
"""

import argparse
import csv
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zh_localize import norm  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
ZH_TITLES = os.path.join(ROOT, "zh", "zh_titles.csv")
OUT_TABLE = os.path.join(ROOT, "terms", "术语多译表.csv")

MAX_ALIAS = 6
MERGE_GROUPS = 2

# 每组 = 同一作品/系列的不同中文叫法，第一个当「首选名」
TERM_GROUPS = [
    ["宝可梦", "精灵宝可梦", "口袋妖怪", "口袋怪兽", "宠物小精灵", "神奇宝贝", "口袋精灵"],
    ["马力欧", "马里奥", "玛莉欧", "玛利欧"],
    ["星之卡比", "卡比之星"],
    ["塞尔达", "萨尔达"],
    ["火焰纹章", "圣火徽章", "火炎纹章"],
    ["银河战士", "密特罗德"],
    ["大金刚", "森喜刚"],
    ["索尼克", "音速小子", "刺猬索尼克"],
    ["街头霸王", "街霸"],
    ["拳皇", "格斗之王"],
    ["最终幻想", "太空战士"],
    ["真·女神转生", "真女神转生"],
    ["怪物猎人", "魔物猎人"],
    ["生化危机", "恶灵古堡"],
    ["合金装备", "潜龙谍影"],
    ["寂静岭", "沉默之丘"],
    ["高达", "钢弹", "敢达"],
    ["数码宝贝", "数码暴龙", "数码怪兽"],
    ["海贼王", "航海王"],
    ["龙珠", "七龙珠"],
    ["哆啦A梦", "机器猫", "小叮当"],
    ["灌篮高手", "篮球飞人"],
    ["足球小将", "天使之翼"],
    ["美少女战士", "水手月亮"],
    ["超级机器人大战", "机器人大战", "机战"],
    ["魔法气泡", "噗哟噗哟"],
    ["侠盗猎车手", "横行霸道"],
    ["奥特曼", "超人力霸王", "咸蛋超人"],
    ["假面骑士", "蒙面超人", "幪面超人"],
    ["全职猎人", "猎人"],
    ["火影忍者", "火影"],
    ["名侦探柯南", "柯南"],
    ["合金弹头", "越南战役"],
    ["瓦力欧", "瓦里奥", "坏马力欧"],
    ["碧奇公主", "碧琪公主", "桃花公主"],
    ["炼金工房", "炼金术士"],
    ["鬼泣", "恶魔猎人"],
    ["旺达与巨像", "汪达与巨像", "巨像之影"],
    ["重力异想世界", "重力眩晕"],
    ["弹丸论破", "枪弹辩驳"],
    ["如龙", "人中之龙"],
    ["时空之轮", "超时空之轮"],
    ["梦幻模拟战", "兰古利萨"],
    ["太鼓达人", "太鼓之达人"],
    ["实况足球", "胜利十一人"],
    ["极品飞车", "极速快感"],
    ["使命召唤", "决胜时刻"],
    ["战地", "战地风云"],
    ["光环", "最后一战"],
    ["求生之路", "恶灵势力"],
    ["辐射", "异尘余生"],
    ["星际争霸", "星海争霸"],
    ["红色警戒", "红色警报"],
    ["真·三国无双", "真三国无双"],
]


def filter_groups(groups):
    """丢掉会串味的短变体：某个变体若是**别的组**的主名的子串，展开后就会出现
    「怪物猎人 -> 怪物全职猎人」这类假名字（`猎人` 落在 `怪物猎人` 里）。
    同一组自己的主名不算冲突（`柯南` 落在 `名侦探柯南` 里，是正常的缩短写法）。
    """
    mains = [g[0] for g in groups]
    out, dropped = [], []
    for g in groups:
        keep = [g[0]]
        for v in g[1:]:
            if any(v in m for m in mains if m != g[0]):
                dropped.append((v, g[0]))
                continue
            keep.append(v)
        if len(keep) > 1:
            out.append(keep)
    return out, dropped


GROUPS, DROPPED = filter_groups(TERM_GROUPS)


def variants(name, groups):
    """返回该中文名可展开出的其它叫法（含多组组合）。"""
    hits = []          # [(anchor, [others])]
    for g in groups:
        found = None
        for v in sorted(g, key=len, reverse=True):
            if v in name:
                found = v
                break
        if not found:
            continue
        others = [v for v in g if v != found]
        if others:
            hits.append((found, others))
    if not hits:
        return []

    out = []

    def walk(i, cur, depth):
        if len(out) >= MAX_ALIAS:
            return
        if i == len(hits) or depth >= MERGE_GROUPS:
            out.append(cur)
            return
        # 不改这一组
        walk(i + 1, cur, depth)
        a, others = hits[i]
        for v in others:
            if len(out) >= MAX_ALIAS:
                return
            walk(i + 1, cur.replace(a, v), depth + 1)

    walk(0, name, 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只统计不写文件")
    ap.add_argument("--table", action="store_true", help="额外输出术语多译表.csv")
    args = ap.parse_args()

    rows = list(csv.DictReader(io.open(ZH_TITLES, encoding="utf-8-sig", newline="")))
    fields = ["game_name", "name_cn", "series", "alias", "alias_cn"]

    filled = 0
    total_alias = 0
    samples = []
    for r in rows:
        cn = (r.get("name_cn") or "").strip()
        al = []
        if cn:
            for v in variants(cn, GROUPS):
                v = v.strip()
                if v and v != cn and v not in al:
                    al.append(v)
        al = al[:MAX_ALIAS]
        r["alias_cn"] = "|".join(al)
        if al:
            filled += 1
            total_alias += len(al)
            if len(samples) < 8:
                samples.append((cn, r["alias_cn"]))
        r.setdefault("alias", "")

    print("词库 %d 行，%d 行带多译，共 %d 个别名（均 %.2f 个）"
          % (len(rows), filled, total_alias, total_alias / max(filled, 1)))
    for cn, al in samples:
        print("  %s  ->  %s" % (cn, al))

    if args.dry:
        return

    shutil.copy2(ZH_TITLES, ZH_TITLES + ".bakalias")
    with io.open(ZH_TITLES, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=fields, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print("已写回：%s（备份 .bakalias）" % ZH_TITLES)

    if args.table:
        os.makedirs(os.path.dirname(OUT_TABLE), exist_ok=True)
        with io.open(OUT_TABLE, "w", encoding="utf-8-sig", newline="") as fp:
            w = csv.writer(fp, lineterminator="\r\n")
            w.writerow(["主线中文名", "其它叫法", "变体数"])
            for g in GROUPS:
                w.writerow([g[0], " / ".join(g[1:]) if len(g) > 1 else "（无其它叫法）", len(g)])
        print("术语表：%s（%d 组，已剔除会串味的短变体 %d 个）"
              % (OUT_TABLE, len(GROUPS), len(DROPPED)))
        for v, g in DROPPED:
            print("  剔除 %s（属于「%s」组）" % (v, g))


if __name__ == "__main__":
    main()

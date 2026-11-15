# -*- coding: utf-8 -*-
"""通用校验：任意平台的译名分片 → 按文件顺序重编号 → 断言 → zip 成 TSV。
用法：python build_key_cn.py snes 1704
"""
import io, os, re, sys, collections

KEY = sys.argv[1]
EXPECT = int(sys.argv[2])
BASE = r"C:\Users\myx-pc\Doubao\chats\2026-11-15\new-chat-1"
MISS = os.path.join(BASE, "%s_missing.txt" % KEY)
SER_EN = os.path.join(BASE, "%s_series.txt" % KEY)
SER_CN = os.path.join(BASE, "%s_series_cn.txt" % KEY)
OUT = os.path.join(BASE, "%s_cn_all.tsv" % KEY)
SER_UNIQ = os.path.join(BASE, "%s_series_uniq.txt" % KEY)

parts = sorted(f for f in os.listdir(BASE)
               if re.fullmatch(r"%s_cn_part\d+\.txt" % KEY, f))
print("分片：", parts)

en = [l.rstrip("\n") for l in io.open(MISS, encoding="utf-8-sig") if l.strip()]
print("英文清单 %d 条" % len(en))
if len(en) != EXPECT:
    sys.exit("!! 期望 %d 条，清单实际 %d 条" % (EXPECT, len(en)))

items, idx = [], 0
for f in parts:
    buf, n = [], 0
    for i, line in enumerate(io.open(os.path.join(BASE, f), encoding="utf-8-sig"), 1):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if "\t" not in line:
            sys.exit("!! %s 第 %d 行没有 TAB：%r" % (f, i, line))
        num, cn = line.split("\t", 1)
        cn = cn.strip()
        if not cn:
            sys.exit("!! %s 第 %d 行中文为空" % (f, i))
        if "\t" in cn:
            sys.exit("!! %s 第 %d 行中文里带 TAB" % (f, i))
        if not num.strip().isdigit():
            sys.exit("!! %s 第 %d 行序号不是数字" % (f, i))
        idx += 1
        items.append(cn)
        buf.append("%d\t%s\n" % (idx, cn))
        n += 1
    with io.open(os.path.join(BASE, f), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(buf))
    print("  %s：%d 条" % (f, n))

print("译名合计 %d 条" % len(items))
if len(items) != len(en):
    sys.exit("!! 条数不一致：译名 %d vs 英文 %d" % (len(items), len(en)))

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for e, c in zip(en, items):
        f.write("%s\t%s\n" % (e.strip(), c))
print("已写出 %s（%d 行）" % (os.path.basename(OUT), len(items)))

if os.path.exists(SER_CN):
    se = [l.rstrip("\n") for l in io.open(SER_EN, encoding="utf-8-sig") if l.strip()]
    sc = [l.rstrip("\n") for l in io.open(SER_CN, encoding="utf-8-sig") if l.strip()]
    print("series 英文 %d 条 / 中文 %d 条" % (len(se), len(sc)))
    if len(se) != len(sc):
        sys.exit("!! series 条数不一致：%d vs %d" % (len(se), len(sc)))
    with io.open(SER_UNIQ, "w", encoding="utf-8", newline="\n") as f:
        for i, line in enumerate(se, 1):
            f.write("%d\t%s\n" % (i, line.split("\t")[0].strip()))
    for i, line in enumerate(sc, 1):
        num, cn = line.split("\t", 1)
        if int(num) != i:
            sys.exit("!! series 第 %d 条序号写成 %s" % (i, num))
        if not cn.strip():
            sys.exit("!! series 第 %d 条中文为空" % i)
    print("series 校验通过，已写出 %s" % os.path.basename(SER_UNIQ))
else:
    print("（series 中文尚未落盘，跳过对齐）")

kana = re.compile(r"[\u3040-\u30ff]")
bad_kana = [(e, c) for e, c in zip(en, items) if kana.search(c)]
print("含假名的中文名 %d 条" % len(bad_kana))
for e, c in bad_kana[:20]:
    print("   ", e, "->", c)
lat = [(e, c) for e, c in zip(en, items) if re.search(r"[A-Za-z]{2,}", c)]
print("中文名保留拉丁字母（≥2连续）的 %d 条，抽查 12 条：" % len(lat))
for e, c in lat[:12]:
    print("   ", e, "->", c)
dup = [c for c, n in collections.Counter(items).items() if n > 1]
print("重复中文名 %d 个（多语言/多区域版本，正常）" % len(dup))

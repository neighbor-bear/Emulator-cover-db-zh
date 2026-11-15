# -*- coding: utf-8 -*-
"""通用：把 <key>_cn_all.tsv + series 译名并入 zh/zh_titles.csv。
用法：python apply_key_cn.py snes 1704 58
"""
import io, csv, sys, shutil, os
sys.path.insert(0, r"C:\Users\myx-pc\Downloads\cover-db")
from zh_localize import norm

KEY = sys.argv[1]
EXP_MISS = int(sys.argv[2])
EXP_SER = int(sys.argv[3])
BASE = r"C:\Users\myx-pc\Doubao\chats\2026-11-15\new-chat-1"
ZH = r"C:\Users\myx-pc\Downloads\cover-db\zh\zh_titles.csv"

pairs = []
for ln in io.open(os.path.join(BASE, "%s_cn_all.tsv" % KEY), encoding="utf-8"):
    ln = ln.rstrip("\n")
    if ln.strip():
        e, c = ln.split("\t")
        pairs.append((e.strip(), c.strip()))
assert len(pairs) == EXP_MISS, len(pairs)

uniq = []
for ln in io.open(os.path.join(BASE, "%s_series_uniq.txt" % KEY), encoding="utf-8"):
    ln = ln.rstrip("\n")
    if ln.strip():
        i, n = ln.split("\t")
        uniq.append((int(i), n.strip()))
cn_series = []
for ln in io.open(os.path.join(BASE, "%s_series_cn.txt" % KEY), encoding="utf-8"):
    ln = ln.rstrip("\n")
    if ln.strip():
        i, c = ln.split("\t")
        cn_series.append((int(i), c.strip()))

assert len(uniq) == EXP_SER, len(uniq)
assert len(cn_series) == EXP_SER, len(cn_series)
for a, b in zip(uniq, cn_series):
    assert a[0] == b[0], (a, b)
pairs += [(n, c) for (_, n), (_, c) in zip(uniq, cn_series)]
print("名称", len(pairs) - EXP_SER, "series", len(cn_series), "合计", len(pairs))
assert len(pairs) == EXP_MISS + EXP_SER, len(pairs)

shutil.copy2(ZH, os.path.join(BASE, "zh_titles.csv.bak%s" % KEY))

rows = list(csv.reader(io.open(ZH, encoding="utf-8-sig", newline="")))
rows = [r for r in rows if r and r[0].strip()]
head = rows[0]
body = rows[1:]
have = {norm(r[0]) for r in body}
before = len(body)

added, skipped, bad = 0, 0, []
for e, c in pairs:
    k = norm(e)
    if not k or not c:
        bad.append((e, c))
        continue
    if k in have:
        skipped += 1
        continue
    body.append([e, c, "", KEY])
    have.add(k)
    added += 1

with io.open(ZH, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, lineterminator="\r\n")
    w.writerow(head)
    w.writerows(body)

print("候选", len(pairs), "新增", added, "已存在跳过", skipped, "异常", bad)
print("词库", before, "->", len(body))

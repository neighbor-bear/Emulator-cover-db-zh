# Emulator-cover-db-zh · 模拟器封面索引 & 中英名映射表

本项目由AI制作给模拟器启动器、ROM 整理工具做刮削用的**纯 CSV 方案**：仓库里只放表和数据，不放图片。
封面仍然由 libretro 官方源托管，工具运行时按表里的 URL 去拉，或者用脚本提前拉到本地缓存。

- **30 个平台 / 77 661 条**记录（含区域、版本、三种图 URL）
- **中文名覆盖 83.2%**（exact 63 615 条 + series 1 028 条）；36 797 个唯一英文名里 74.1% 有中文（27 269 个）
- **PSP、3DS、PS2、PS1、NDS、FC、Wii、GBA 八个平台已 100% 中文**（PSP 1 774 条 / 3DS 2 148 条 / PS2 8 502 条 / PS1 9 301 条 / NDS 7 335 条 / FC 13 439 条 / Wii 6 668 条 / GBA 5 961 条，全部 exact，无空名、无 series 半成品）
- 中文名库 `zh/zh_titles.csv` 26 847 行（去重后 26 835 条参与匹配），系列词表 `zh/zh_series.csv` 171 条，可持续往上加

> 数据来源：libretro-thumbnails（社区托管的封面索引）。封面版权归各游戏厂商，本项目只转发索引和 URL。

---

## 一、目录说明

```
cover-db/
├── libretro_index.py     # 抓全量索引（平台 × 游戏 × 区域 × 三种图 URL）
├── zh_localize.py        # 索引 + 中文名库 -> 中英对照映射表（exact / series / none）
├── zh_coverage.py        # 统计各平台中文覆盖率，直接输出 Markdown 表
├── cover_fetch.py        # 按映射表自动下载封面到本地（多区域回退）
├── match_rom.py          # 扫本地 ROM 文件夹，自动匹配出封面和中文名
├── promote_manual.py     # 把映射表里手填的中文名回收进主词库
├── run_all.sh            # 一键跑全流程
├── index/                # 原始索引（无中文名）
│   └── libretro_<平台>.csv
├── mapping/              # 成品映射表（中文名 + 首选区域标记）
│   └── mapping_<平台>.csv
├── zh/
│   ├── zh_titles.csv     # 精确中文名库（26 847 行 / 26 835 条）
│   └── zh_series.csv     # 系列名 / 关键词表（171 条）
├── cache/<平台>/         # 下载下来的封面 png（不进 git）
├── manifest/             # 下载清单：本地路径 / 状态
└── match/                # ROM 匹配结果
```

`mapping_<平台>.csv` 字段：

| 字段 | 含义 |
|---|---|
| system / system_key | 平台中文简称 / 平台英文 key |
| retroarch_system | RetroArch 里的系统名 |
| folder | libretro 平台目录名，拼 URL 用 |
| game_name | 英文原名（已去掉区域标记） |
| name_cn | 中文名（空着就是待补） |
| match_type | `exact` 精确命中 / `series` 系列名回退（半成品，待校对）/ `manual` 人工填 / `none` 未匹配 |
| region / revision | 区域、版本（USA、Japan、v1.01、Rev 1、Demo 等） |
| preferred | `1` = 该游戏在这个平台的首选图（去重后每款一张） |
| search_key | 归一化匹配键，跨平台 join 用 |
| file | libretro 里的原始文件名（本地存图保持同名，前端最好按它匹配） |
| boxart / snap / title | 盒封面 / 游戏截图 / 标题画面 三种 URL |

---

## 二、三分钟上手

```bash
cd cover-db

# 1. 抓索引（30 个主力平台，约 25 秒）
python3 libretro_index.py

# 2. 生成中英对照表
python3 zh_localize.py

# 3. 看各平台中文覆盖率
python3 zh_coverage.py

# 4. 试抓 20 张封面看看效果
python3 cover_fetch.py --platforms psp --limit 20

# 5. 扫自己的 ROM 目录，输出「文件 -> 封面」
python3 match_rom.py --dir /你的/rom目录 --platform psp
```

一键版：`bash run_all.sh`

---

## 三、各脚本常用参数

### libretro_index.py

```bash
python3 libretro_index.py --list           # 看支持哪些平台 key
python3 libretro_index.py --only psp ps2   # 只抓指定平台
python3 libretro_index.py --all            # 抓目录里全部 127 个平台
python3 libretro_index.py --jobs 8         # 并发
```

### zh_localize.py

```bash
python3 zh_localize.py                      # 全平台重建（会顺带生成 mapping/all_games.csv）
python3 zh_localize.py --platforms psp ps2  # 只重建指定平台
python3 zh_localize.py --stats              # 只统计，不写文件
```

### zh_coverage.py

```bash
python3 zh_coverage.py            # 打印 Markdown 表（README 里那张表就是它生成的）
python3 zh_coverage.py --csv      # 打印 CSV
python3 zh_coverage.py --zh-only  # 只列已有中文名的平台
```

### cover_fetch.py

```bash
--platforms psp ps2 ps1 ngc     # 要抓的平台
--limit 20                      # 每平台最多抓多少（试跑）
--concurrency 8                 # 并发，别开太大，官方源是裸 HTTP
--preferred-only                # 每款游戏只抓首选区域一张（强烈建议）
--only-cn                       # 只抓已经有中文名的
--from-csv mapping/mapping_psp.csv
```

抓取有三级回退：**首选区域 Boxart → 同款其他区域 Boxart → Snaps → Titles**，
并校验 PNG 魔数，不会把 404 的 HTML 页面当封面存下来。已存在的合法文件直接跳过，
中断重跑不会重复下载。

> 体积提醒：单张封面 0.3–1.5 MB。PSP 全量约 1 GB，PS1 全量约 5–7 GB。
> 只想先看效果，务必加 `--limit` 或 `--preferred-only`。

### match_rom.py

```bash
--dir /path/to/roms     # 必填
--platform psp          # 不限平台就不写
--threshold 0.72        # 模糊匹配阈值，调低命中多但误配也多
```

输出 `match/rom_match_<平台>.csv`：本地路径、匹配到的英文名、中文名、区域、置信度、封面 URL、hit/miss。
文件名里的 `(USA)`、`(Disc 1)`、`[!]`、`(Rev 1)`、`(v1.02)` 会自动当噪声去掉再匹配。

### promote_manual.py

在 `mapping_xxx.csv` 里手工把 `name_cn` 填好之后：

```bash
python3 promote_manual.py     # 回收进 zh/zh_titles.csv
python3 zh_localize.py        # 重新生成，所有平台一起受益
```

---

## 四、匹配策略

英文名归一化后做 join，一次抹平这些差异：

| 差异 | 例子 |
|---|---|
| `系列 - 副标题` / `系列 副标题` | `Crisis Core - Final Fantasy VII` ⇄ `Crisis Core Final Fantasy VII` |
| The 后置 | `Legend of Zelda, The - Twilight Princess` ⇄ `The Legend of Zelda - Twilight Princess` |
| 罗马数字 / 阿拉伯数字 | `Final Fantasy VII` ⇄ `Final Fantasy 7` |
| 变音符号 | `Pokémon` ⇄ `Pokemon` |
| 符号 | `Mario & Luigi` ⇄ `Mario and Luigi` |
| 标点、大小写、多余空格 | 全部抹平 |

四级匹配：**exact 精确 → series 系列名回退（中文系列名 + 原文副标题，待校对）→ manual 人工填 → none 留空**。

### 各平台中文覆盖率

| key | 平台 | 总条数 | exact | series | manual | 未匹配 | 中文覆盖率 |
|---|---|---:|---:|---:|---:|---:|---:|
| nes | FC | 13 439 | 13 439 | 0 | 0 | 0 | 100.0% |
| ps1 | PS1 | 9 301 | 9 301 | 0 | 0 | 0 | 100.0% |
| ps2 | PS2 | 8 502 | 8 502 | 0 | 0 | 0 | 100.0% |
| nds | NDS | 7 335 | 7 335 | 0 | 0 | 0 | 100.0% |
| wii | Wii | 6 668 | 6 668 | 0 | 0 | 0 | 100.0% |
| gba | GBA | 5 961 | 5 961 | 0 | 0 | 0 | 100.0% |
| snes | SFC | 3 689 | 1 116 | 100 | 0 | 2 473 | 33.0% |
| md | MD | 2 352 | 939 | 89 | 0 | 1 324 | 43.7% |
| saturn | SS | 2 294 | 1 033 | 60 | 0 | 1 201 | 47.6% |
| 3ds | 3DS | 2 148 | 2 148 | 0 | 0 | 0 | 100.0% |
| ngc | NGC | 1 954 | 1 389 | 129 | 0 | 436 | 77.7% |
| psp | PSP | 1 774 | 1 774 | 0 | 0 | 0 | 100.0% |
| gb | GB | 1 647 | 504 | 89 | 0 | 1 054 | 36.0% |
| gbc | GBC | 1 524 | 357 | 112 | 0 | 1 055 | 30.8% |
| dc | DC | 1 332 | 454 | 45 | 0 | 833 | 37.5% |
| xbox | XBOX | 1 324 | 870 | 41 | 0 | 413 | 68.8% |
| n64 | N64 | 1 115 | 372 | 69 | 0 | 674 | 39.6% |
| gg | GG | 1 056 | 413 | 77 | 0 | 566 | 46.4% |
| pcecd | PCE-CD | 946 | 129 | 12 | 0 | 805 | 14.9% |
| segacd | MCD | 609 | 142 | 26 | 0 | 441 | 27.6% |
| sms | SMS | 559 | 226 | 5 | 0 | 328 | 41.3% |
| pce | PCE | 479 | 170 | 7 | 0 | 302 | 37.0% |
| wiiu | WiiU | 454 | 187 | 77 | 0 | 190 | 58.1% |
| ws | WS | 299 | 44 | 5 | 0 | 250 | 16.4% |
| neogeo | NEOGEO | 257 | 63 | 43 | 0 | 151 | 41.2% |
| wsc | WSC | 239 | 29 | 5 | 0 | 205 | 14.2% |
| 32x | 32X | 209 | 37 | 0 | 0 | 172 | 17.7% |
| ngpc | NGPC | 118 | 5 | 15 | 0 | 98 | 16.9% |
| ps3 | PS3 | 67 | 6 | 19 | 0 | 42 | 37.3% |
| psvita | PSV | 9 | 2 | 3 | 0 | 4 | 55.6% |
| ps3dl | PS3DL | 1 | 0 | 0 | 0 | 1 | 0.0% |
| **合计** | **30 平台** | **77 661** | **63 615** | **1 028** | **0** | **13 018** | **83.2%** |

表由 `python3 zh_coverage.py` 生成，改完词库后重跑一次就能刷新，不要手抄。

剩下的未匹配基本是三类：日本冷门作 / 同人作、欧美儿童与体育授权游戏、
以及 Action Replay 作弊卡、2-in-1 合卡、光枪合辑这种本来就没有中文名的条目。
**热门作品基本都已在表里**（最终幻想、勇者斗恶龙、塞尔达、马力欧、宝可梦、怪物猎人、
合金装备、生化危机、鬼泣、战神、皇牌空战、实况、无双、传说、女神异闻录等）。

---

## 五、继续补中文名的流程

词库是全仓库唯一的真数据源，任何补名都要回到 `zh/zh_titles.csv`。

**A. 手工路径（推荐，质量最高）**

1. 导出缺失清单：

```bash
python3 - <<'PY'
import csv, glob, os, sys
sys.path.insert(0, '.')
from zh_localize import norm
idx = {}
for p in glob.glob('index/libretro_*.csv'):
    for r in csv.DictReader(open(p, encoding='utf-8-sig', newline='')):
        idx.setdefault(r['game_name'], set()).add(r['system_key'])
known = set()
for p in glob.glob('mapping/mapping_*.csv'):
    for r in csv.DictReader(open(p, encoding='utf-8-sig', newline='')):
        if r['name_cn'].strip():
            known.add(norm(r['game_name']))
miss = sorted(n for n in idx if norm(n) not in known)
open('zh/missing.txt', 'w', encoding='utf-8').write('\n'.join(miss))
print('缺 %d 个英文名' % len(miss))
PY
```

2. 把 `zh/missing.txt` 分成每批 300–500 行，逐行翻成 `英文名<TAB>中文名` 的 TSV
   （UTF-8，不要 BOM，`\t` 分隔，中文名里不要出现制表符）。
3. 按 `norm()` 键并入词库：

```bash
python3 - <<'PY'
import csv, sys
sys.path.insert(0, '.')
from zh_localize import norm
titles, part = 'zh/zh_titles.csv', 'zh/cn_batch1.tsv'
rows = list(csv.DictReader(open(titles, encoding='utf-8-sig', newline='')))
fields, have = list(rows[0].keys()), {norm(r['game_name']) for r in rows}
added = skipped = 0
for line in open(part, encoding='utf-8'):
    if not line.strip():
        continue
    en, cn = line.rstrip('\r\n').split('\t')[:2]
    if norm(en) in have:
        skipped += 1
        continue
    rows.append({'game_name': en.strip(), 'name_cn': cn.strip(), 'series': '', 'alias': ''})
    have.add(norm(en)); added += 1
with open(titles, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
print('并入 %d 条，跳过 %d 条' % (added, skipped))
PY
```

4. 重建 + 看效果：

```bash
python3 zh_localize.py --platforms ps1 nds   # 或全量
python3 zh_coverage.py
```

**B. 表格路径（适合有校对员）**

直接在 `mapping_<平台>.csv` 的 `name_cn` 列填，`match_type` 保持 `none`，
然后 `python3 promote_manual.py && python3 zh_localize.py` —— 只回收非 exact / 非 series 的行。

**C. 已经踩过的坑**

- `zh_localize.py` 每次重建都会顺手写 `mapping/all_games.csv`（约 45 MB）。它已在 `.gitignore` 里，
  提交前删掉即可，别误提交。
- `norm()` 会把标题里独立的 `X` 转成 `10`（罗马数字表里有 X），所以 `Ace Combat X`、
  `Mega Man X` 这种系列名回退会生成「王牌空战 10」这类半成品中文名 —— 用 exact 精确名覆盖掉。
- 只用 series 回退的行是「中文系列名 + 英文副标题」，属半成品，校对时优先处理。
- 同一个英文名在多个平台出现时按 `search_key`（= `norm(game_name)`）共享同一条中文名，
  所以补一次、全平台生效；不要按平台重复翻译。
- 按行号写的译名分片必须断言「序号连续 + 无重复」。PS1 第 8 片手写时把 `4989`
  写了两遍，`build_ps1_cn.py` 一跑就报「重复序号 [4989]」并中止，比事后逐行比对省事得多。
- 分片编号手写错位时，可以用「按文件内容顺序重编号」兜底（NDS 第 7 片跳过 10 行又重复了一遍），但重编号只能修编号、不能修漏行，所以必须同时断言「总条数 == 英文清单条数」。
- 拼音标题的盗版条目（`Bao Qing Tian`、`Di Dao Zhan`、`San Guo Zhi - Qun Xiong Zheng Ba`）必须先按拼音还原成中文原意再落译名，直接照英文字面翻会译成一堆无意义音译。
- 欧版多语言条目（德/法/意/西/荷各一条）必须共用同一套中文名，只在末尾括号标语种；若各版本各造译名，同一款游戏在刮削结果里会分裂成多个名字。
- e-Reader 卡带条目（`Pokemon-e TCG`、`Pokemon Card-e`、`Animal Crossing-e`、`Pokemon Battle-e`、`Mario Party-e`、`Super Mario Advance 4-e`）不要逐条意译，按「作品名 + 卡带e/卡带e+ + 系列或卡包 + 卡号 + 角色名」机械拼装，卡号原样保留；否则 2 000 多条既翻不完也无法保持同一格式。

### 本项目 PSP 平台的完整实操（可复用的模板）

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_psp.csv` 1 774 行，只有 362 行有中文（151 exact + 211 series 半成品），1 412 行空 |
| 导出缺失 | 1 095 个唯一英文名 |
| 分批手翻 | 3 批 TSV（300 + 795 + 35 条查证修正） |
| 修 series 半成品 | 105 个唯一名整行替换（罗马数字误转、全小写等） |
| 补英文尾巴 | 23 条（如 `Akiba's Trip Plus` → 秋叶原之旅 加强版） |
| 回收进词库 | `promote_manual.py` 回收 1 191 条，词库 581 → 1 772 条 |
| 重建 | `zh_localize.py --platforms psp` → 1 774 行 **exact 1 774**，`none` / `series` 归零 |
| 校验 | 与备份逐列 diff，只有 `name_cn`、`match_type` 两列变化，行序 / URL / preferred 未动 |

跨平台又补了 1 000 余个经典标题（出现在 3 个以上平台的那批，如《大富翁》《真人快打》
《百战天虫》《波斯王子》《古墓丽影》《细胞分裂》《逆转裁判》《电车GO！》等），
一并进了词库，所以各平台覆盖率一起抬了一档。

### 3DS 全量中文化（2 148 / 2 148，100%）

3DS 的坑和 PSP 不一样：只有 258 行 exact，且有 **394 行是 series 半成品**（中文系列名 + 英文副标题，
如 `皇牌空战 - Assault Horizon Legacy`），所以“补空名”不够，得把半成品一起整行替换。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_3ds.csv` 2 148 行：exact 258 / series 394 / none 1 496（空名 1 063 个唯一名） |
| 导出清单 | `3ds_missing.txt`（1 063 个唯一空名）+ `3ds_series.txt`（170 个 series 唯一名） |
| 译名文件 | 按**行号对齐**写（`3ds_cn_part1/2/3.txt`，格式 `序号<TAB>中文名`），避免抄错英文名导致 `norm` 对不上 |
| 半成品替换 | `3ds_series_cn.txt`（170 条，中文前缀 + 英文尾巴全部改成完整中文） |
| 并入词库 | `apply_3ds_cn.py`：候选 1 233 条，新增 1 218，已存在跳过 15；词库 2 809 → 4 027 行 |
| 重建 | `zh_localize.py --platforms 3ds` → **exact 2 148 / series 0 / none 0** |
| 自检 | ① 序号连续性（1…1 063，0 处错位）；② 品牌词反向校验（英文含 `LEGO`/`Zelda`/`Pokemon`/`Yo-Kai Watch` 等 30 组关键词，中文必须含对应译名，抓错行）；③ 中文里残留 2 个以上拉丁字母的逐条人工过一遍 |

**3DS 阶段的经验**

- **按行号对齐比抄英文名安全**。1 063 条里只要手抄错一个连字符，`norm()` 就对不上，静默丢一条；
  行号文件配上「序号必须连续」的断言，错行会立刻暴露。
- **series 半成品必须整行替换**，不能靠补 `zh_series.csv` 词表糊过去——半成品本身就是“中文 + 英文”混排，
  落在 mapping 里就是不干净的中文名。
- **数据源名称先统一再入手**。同一系列中文有分歧时（本轮 `世界树的迷宫` / `世界树迷宫`），
  统一成一个写法再重生成，否则跨平台 join 出来的名字会前后不一致。
- **一类特有残留**：品牌名与商号允许保留原文（`LEGO`、`FIFA`、`PriPara`、`amiibo`、`DX`、`with JAL` 之类），
  但“中文前缀 + 英文副标题”这种半成品不算——统一改成 `羽田（JAL版）`、`超级马力欧制造 3DS版` 这种写法。
- **翻译通道实测**：Bing 走 `robots.txt` 拒绝自动访问、搜狗弹验证码、维基百科不支持抓取，
  所以冷门日系标题（`A-Ressha de Ikou 3D`、`Kokuga`、`SoniPro`、韩国版 `Chin-gumoa Apateu` 等）
  按作品原名直译处理，不假装是官方译名。


### PS2 全量中文化（8 502 / 8 502，100%）

PS2 是这批里体量最大的平台，坑在于**同族批量条目多**：`Buzz!` 各国问答、`Club Football` 各球队、
`Beatmania II DX` 全代数、`Dot Hack` 全系列、`Simple 2000` 编号百卷、`SingStar` 各地语言版，
还有 `NBA`/`NFL`/`NHL`/`NCAA`/`MLB` 的年货。这类不能逐条硬翻，按「族名 + 地区/球队/代数」批量处理最省。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ps2.csv` 8 502 行：exact 1 780 / series 631 / none 6 091（空名 3 818 个唯一名） |
| 导出清单 | `ps2_missing.txt`（3 818 个唯一空名）+ `ps2_series.txt`（269 个 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，6 片（每片 640 条，末片 618）：`ps2_cn_part1..6.txt`，格式 `序号<TAB>中文名` |
| 半成品替换 | `ps2_series_cn.txt`（269 条完整中文，如 `皇牌空战 - Distant Thunder` → 皇牌空战 遥远的雷霆） |
| 并入词库 | `apply_ps2_cn.py`：候选 4 087 条，新增 4 072，已存在跳过 15；词库 4 027 → 8 099 行 |
| 重建 | `zh_localize.py --platforms ps2` → **exact 8 502 / series 0 / none 0** |
| 自检 | ① 序号连续性（1…3 818，0 处缺号 / 0 处重复）；② 一一 zip 回英文清单生成 `ps2_cn_all.tsv`；③ 近 1 000 行含拉丁字母的逐条过一遍，品牌缩写保留、明显半成品修掉 |

**PS2 阶段新增的经验**

- **同一批里的「半成品」要先批量对齐再翻**。`SingStar`/`Buzz!`/`Simple 2000` 这类系列，
  series 回退生成的名字是「中文前缀 + 英文尾巴」，直接翻尾巴会留下几十条读着别扭的名字；
  先按族名定一个统一写法（如 `SingStar 与迪士尼同唱`、`Buzz! 芬兰体育问答`），再整行落库。
- **罗马数字坑在 PS2 更密**。`Mega Man X` 被 `norm()` 的 `X→10` 转成「洛克人 10」、
  `Resident Evil - Code - Veronica X` 转成「代号维罗妮卡 10」，靠 exact 名覆盖后才正常。
- **拼写/标点差异不是错**。数据源里 `Shadow of the Colossus + Ico`、`Fate/unlimited codes`、
  `kill.switch`、`ef - A Fairy Tale of the Two.` 这种原样保留的作品名，中文名里保留原文是刻意的，
  不要为了“纯中文”硬造译名。
- **同名人肉查证成本高**。PS2 里日系 Galgame、韩版、欧版小语种标题占比不小，
  搜索通道仍不可用（见 3DS 阶段结论），一律按作品原名直译，并在本文件里说明不是官方译名。


### PS1 全量中文化（9 301 / 9 301，100%）

PS1 是被 PSP 反哺最多的平台：起点 1 182 exact，其中很大一部分是 PSP 阶段补的跨平台经典名。
真正的工作量在 **7 760 条 none** 与 **359 条 series 半成品**，而且日系小品、柏青嫂（pachi-slot）
编号系列、廉价版（Simple 1500 / SuperLite 1500）占了近一半，属于必须逐条过一遍的类型。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ps1.csv` 9 301 行：exact 1 182 / series 359 / none 7 760（空名 5 011 个唯一名） |
| 导出清单 | `ps1_missing.txt`（5 011 个唯一空名，按字母序）+ `ps1_series.txt`（174 个 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，8 片（`ps1_cn_part1..8.txt`，前 7 片各 640 条，末片 531 条），格式 `序号<TAB>中文名` |
| 半成品替换 | `ps1_series_cn.txt`（174 条完整中文，如 `Biohazard 2 - Dual Shock Ver.` → 生化危机 2 震动版） |
| 并入词库 | `apply_ps1_cn.py`：候选 5 185 条，新增 5 185（0 跳过）；词库 8 099 → 13 284 行 |
| 重建 | `zh_localize.py --platforms ps1` → **exact 9 301 / series 0 / none 0** |
| 自检 | ① 序号连续性（1…5 011，0 处缺号 / 0 处重复）；② zip 回英文清单生成 `ps1_cn_all.tsv`；③ 885 行含拉丁字母的逐条过一遍；④ series 174 条序号与英文清单一一对齐 |

**PS1 阶段新增的经验**

- **同一款游戏的多个写法会吃满重复劳动**。`Biohazard` / `Resident Evil`、`Rockman` / `Mega Man`
  在 PS1 里同时存在日版与欧美版条目，`norm()` 不会把它们当成同一个键，两套都要落中文名；
  本轮把「生化危机」「洛克人」两族按同一套译法整族写，避免同一作品出现两个中文名。
- **编号系列（Simple 1500 / SuperLite 1500 / Slot! Pro / 柏青嫂帝王）按「卷号 + 项目名」统一格式**。
  例如 `Simple 1500 Series Vol. 47 - The Skateboard` → `廉价1500系列 第47卷 滑板`，
  统一前缀后既好读又便于以后批量补卷。
- **柏青嫂类条目不要硬译机种名**。`Wai Wai Pulsar`、`King Bary`、`Siolar`、`LequiO-30` 这类是日本机台商品名，
  按音译/原名保留处理，中文名里保留原文是刻意的。
- **重号检查要放在断言里**。本轮第 8 片末尾因为手写重复，出现 `4989` 两次，
  靠 `build_ps1_cn.py` 的「重复序号 / 缺号」断言当场抓出来（见第五节 C「已经踩过的坑」）。
- **数据源本身有拼写不一致**：`Sakkyoku Surundamon - Dance Remix Hen` 与 `Sakkyoku surun da mon - Dance Remix-hen`
  是同款两种写法，两行都要译，`norm()` 不会合并。


### NDS 全量中文化（7 335 / 7 335，100%）

NDS 是这批里“授权小品 + 学习软件 + 廉价系列”密度最高的平台：起点只有 876 行 exact，
剩下的 **5 963 行 none** 与 **496 行 series 半成品** 里，1500 DS Spirits（10 卷）、Simple DS Series（48 卷）、
Puzzle Series（13 卷）、Maru Goukaku 资格考试（20 余卷）、Tokuten Ryoku Gakushuu DS（30 余卷）、
汉检（Kanken）一族、法德西意荷小语种教辅占了很大比重。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_nds.csv` 7 335 行：exact 876 / series 496 / none 5 963（空名 4 394 个唯一名） |
| 导出清单 | `nds_missing.txt`（4 394 个唯一空名，按字母序）+ `nds_series.txt`（243 个 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，7 片（`nds_cn_part1..7.txt`，前 6 片各 640 条，末片 554 条），格式 `序号<TAB>中文名` |
| 半成品替换 | `nds_series_cn.txt`（243 条完整中文，如 `Pokemon - Black Version` → 宝可梦 黑版） |
| 并入词库 | `apply_nds_cn.py`：候选 4 637 条，新增 4 637（0 跳过）；词库 13 284 → 17 921 行 |
| 重建 | `zh_localize.py --platforms nds` → **exact 7 335 / series 0 / none 0** |
| 自检 | ① 序号连续性（1…4 394，0 处缺号 / 0 处重复）；② zip 回英文清单生成 `nds_cn_all.tsv`；③ 1 079 行含拉丁字母的逐条过一遍；④ series 243 条序号与英文清单一一对齐；⑤ 假名残留检查，抓到 2 条并修掉 |

**NDS 阶段新增的经验**

- **编号系列统一成「前缀 + 第 N 卷 + 项目名」**。`Simple DS Series Vol. 7 - The Illust Puzzle & Suuji Puzzle` →
  `简易DS系列 第7卷 插画拼图与数字拼图`；`1500 DS Spirits Vol. 2 - Shougi` → `1500 DS Spirits 第2卷 将棋`。
  后者的 `Spirits` 是系列品牌名，硬译成「灵异」会指错方向，所以保留原文（同 3DS 阶段的 `LEGO`、`DX` 处理）。
- **同一族按一条主干译法铺开**。`Tokuten Ryoku Gakushuu DS` 30 余卷统一成「得分力学习DS + 年级/科目」，
  `Maru Goukaku - Shikaku Dasshu!` 20 余条统一成「满分合格 资格冲刺！+ 考试名」，
  `Chikyuu no Arukikata DS` 统一成「地球漫步DS + 国家 + 年份」，避免同一系列出现几种写法。
- **合卡条目按「几合一 + 组成游戏」展开**。`2 in 1`/`3 in 1`/`4 in 1`/`Double Pack`/`Combo Pack` 分别写成
  二合一 / 三合一 / 四合一 / 双包 / 组合包，后面接组成作品的中文名，方便扫库时一眼看清内容。
- **小语种同名作品共用一套中文名**。`Meine Tierarztpraxis` 与 `My Vet Practice` 都作「我的兽医诊所」，
  `Tierbabys - Meine Grosse Tierpension` 作「动物宝宝 我的大型宠物旅馆」——同一作品的不同语言版本，
  `norm()` 不会合并，必须两行都落，但译法要一致。
- **手写分片的编号错位用脚本兜底**。本轮第 7 片手写时编号跳了 10 行又重复了一遍，
  `build_nds_cn.py` 直接按「文件顺序」重编号（内容顺序本身是对的），再用「条数必须等于 4 394」断言收口；
  若错位同时伴随漏行，条数断言会失败，不会静默通过。
- **DS 后缀保留原文**。`Tetris DS`、`Mario Party DS`、`Zoo Tycoon 2 DS` 里的 `DS` 是平台标记，
  统一写成「俄罗斯方块DS」「马力欧派对DS」，不翻译成「DS版」以外的说法。


### FC（NES）全量中文化（13 439 / 13 439，100%）

FC 是全部平台里条目最多、也最杂的一个：13 439 行里，除任天堂/南梦宫/太东/科乐美的正作，
还塞满了欧美体育年货（Tecmo Bowl、Bases Loaded、R.B.I. Baseball、Madden 式授权体育）、
`Vs.` 街机改版（32 条）、中韩台盗版/合卡（拼音标题、`N in 1` 批发盘）、以及海量 romhack
（`Super Mario Bros. 3 Challenge!` 九个版本、`Metroid Challenge` 三个版本、`Zelda II` 各种 Hard Type）。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_nes.csv` 13 439 行：exact 2 640 / series 567 / none 10 232（空名 2 492 个唯一名，series 唯一 167 条） |
| 导出清单 | `nes_missing.txt`（2 492 个唯一空名，按字母序）+ `nes_series.txt`（167 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，4 片（`nes_cn_part1..4.txt`：640 / 640 / 640 / 572 条），格式 `序号<TAB>中文名` |
| 半成品替换 | `nes_series_cn.txt`（167 条完整中文，如 `Donkey Kong Jr. no Sansuu Asobi` → 大金刚Jr.的算术游戏） |
| 并入词库 | `apply_nes_cn.py`：候选 2 659 条，新增 2 659（0 跳过）；词库 17 921 → 20 580 行 |
| 重建 | `zh_localize.py --platforms nes` → **exact 13 439 / series 0 / none 0** |
| 自检 | ① 条数断言 2 492 == 英文清单，series 167 == 167；② 假名残留 0 条；③ 285 条含拉丁字母的逐条过（AV 系列、`Vs.` 系列、版本号）；④ 与 part1/2 的系列前缀一致性复查 |

**FC 阶段新增的经验**

- **盗版/合卡条目按拼音还原中文，别按英文硬译**。`Bao Qing Tian` → 包青天、`Di Dao Zhan` → 地道战、
  `Feng Shen Bang` → 封神榜、`San Guo Zhi - Qun Xiong Zheng Ba` → 三国志 群雄争霸、
  `Zelda Chuanshuo - San Shen Zhili` → 塞尔达传说 三神之力、`Xian Jian Qi Xia Zhuan` → 仙剑奇侠传。
  这些标题本来就是中文 ROM 的拼音转录，硬译成英文再译回来会走样。
- **`Vs.` 街机改版保留 `Vs.` 前缀，统一写成「对战 + 作品名」**。32 条 `Vs. Super Mario Bros.`、
  `Vs. Duck Hunt`、`Vs. Excitebike` 全部照此办理，一眼能看出是街机对战版而非家用机原版。
- **系列前缀先定死再铺开头**。`Family Trainer` → 家庭教练 N + 项目名、`Famista` → 家庭球场'年份、
  `Bases Loaded` → 满垒、`Dragon Warrior` → 勇者斗恶龙（罗马数字保留）、`Adventure Island` → 冒险岛、
  `Takahashi Meijin no Bouken Jima` → 高桥名人冒险岛、`Igo Shinan` → 围棋指南'年份。
  这七个前缀横跨三片译名，必须先定再写，否则第 3、4 片会和第 1、2 片撞车。
- **hack 版本标记统一成中文后缀**。`Rev PRG0` / `Rev PRG1` / `Rev 0` / `Rev A` →（PRG0版）/（PRG1版）/
  （修订0版）/（修订A版）；`Hard Type` → 硬核版；`Easy Type` → 简单版；`Challenge!` → 挑战！；
  `Debug Menu` → 调试菜单。原版与改版成对出现，加括号最不易混。
- **欧美体育年货按「系列名 + 赛季/年份」接续**。`Tecmo Super Bowl 2005-2006 - Playoff Edition` →
  特库摩超级碗2005-2006 季后赛版，`Tecmo Bowl 2004-2005 PostSeason` → 特库摩碗2004-2005季后赛，
  不复述成整句，保持短名便于检索。


### Wii 全量中文化（6 668 / 6 668，100%）

Wii 的 6 668 行由三块几乎不相干的内容拼起来：第一方本家（马力欧、塞尔达、星之卡比、宝可梦、
银河战士、火焰纹章）、欧美授权年货（Just Dance 20 条、Cabela's 狩猎 9 条、DreamWorks 动画改编 17 条、
Nickelodeon 海绵宝宝/爱卡莉 19 条、Zumba 5 条、My Fitness Coach 8 条）、以及 Virtual Console
老游戏移植（Alex Kidd 6 条、Bonk/PC Genjin、Wonder Boy、Golden Axe、Space Harrier II、
ToeJam & Earl 等）。所以译名的难点不在生僻词，而在**同一作品的多语言版本要译成同一个中文名、
再按平台各落一行**。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_wii.csv` 6 668 行：exact 2 799 / series 430 / none 3 439（空名 1 897 个唯一名，series 唯一 195 条） |
| 导出清单 | `wii_missing.txt`（1 897 个唯一空名，按字母序）+ `wii_series.txt`（195 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，3 片（`wii_cn_part1..3.txt`：640 / 640 / 617 条），格式 `序号<TAB>中文名` |
| 半成品替换 | `wii_series_cn.txt`（195 条完整中文，如 `Biohazard - The Darkside Chronicles` → 生化危机 暗黑历代记） |
| 并入词库 | `apply_wii_cn.py`：候选 2 092 条，新增 2 092（0 跳过）；词库 20 580 → 22 672 行 |
| 重建 | `zh_localize.py --platforms wii` → **exact 6 668 / series 0 / none 0** |
| 自检 | ① 条数断言 1 897 == 英文清单，series 195 == 195；② 假名残留 0 条；③ 229 条含拉丁字母的逐条过（FIFA/NFL/WWE/SSX 等品牌缩写、`ReBirth` 系列、`Plus` / `DX` 后缀）；④ 多语言同名作中文名一致性复查 |

**Wii 阶段新增的经验**

- **同作多语言版本共用一套中文名，只用括号标语种**。sports/健身/问答类在欧版大量存在德、法、意、
  西、荷五种语言的独立条目（`Scene It Ganz grosses Kino!`、`Think - Logik Trainer`、
  `Tierliebe - Gross Geschrieben`），译名统一写「中文名（德版）/（法版）/（意版）」，不另造译名。
- **日文副标题按作品原名直译，不音译**。`Zelda no Densetsu - Skyward Sword` → 塞尔达传说 天空之剑、
  `Mujura no Kamen` → 姆吉拉的假面、`Toki no Okarina` → 时之笛、`Kamigami no Triforce` → 众神的三原力、
  `Hoshi no Kirby` → 星之卡比、`Taiko no Tatsujin` → 太鼓达人、`Wai Wai Bingo` → 欢欢宾果。
- **系列前缀与同期平台保持一致**。`Just Dance` → 舞力全开、`Rabbids` → 疯狂兔子、
  `Deca Sports` → 十项运动、`Family Trainer` → 家庭教练（与 FC 阶段同译）、
  `My Fitness Coach` → 我的健身教练、`Kororinpa` → 滚球派对、`Muramasa` → 胧村正、
  `Sengoku Basara` → 战国BASARA、`Shock Troopers` → 突击奇兵、`Sin and Punishment` → 罪与罚。
- **品牌缩写与真机硬件名保留原文**。FIFA / NFL / WWE / SSX / UFC / PGA / TNA / AMF / PSA 等
  授权品牌与 `uDraw`、`Wii MotionPlus`、`Wii遥控器Plus` 类硬件名不硬译，只把后缀译成中文。
- **`ReBirth` / `R` / `DX` / `Plus` 等版本标记保留原样**。`Gradius ReBirth`、`Contra ReBirth`、
  `Star Soldier R`、`Retro City Rampage DX`、`Arkanoid Plus!` 一律「中文名 + 原标记」，
  与同系列无标记版本形成对照。


### GBA 全量中文化（5 961 / 5 961，100%）

GBA 的 5 961 行里有一块特别的东西：**e-Reader 卡带**。`Pokemon-e TCG`、`Pokemon Card-e`、
`Animal Crossing-e`、`Pokemon Battle-e`、`Pokemon Battle Card-e+`、`Mario Party-e`、
`Super Mario Advance 4-e / Card-e+` 这些不是游戏本体，而是当年刷在纸卡上的小游戏和集换卡，
一条记录对应一张卡（`Pokemon-e TCG - Aquapolis - C-01-# - Nidoran Male` 就是「水之都市」卡包
里的一张尼多朗卡）。这类条目占了 series 清单的绝大多数，逐条意译既不可能也毫无意义，
所以按固定格式机械拼装；真正需要创意翻译的是剩下那批正作。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_gba.csv` 5 961 行：exact 842 / series 2 274 / none 2 845（空名 2 128 个唯一名，series 唯一 2 047 条） |
| 导出清单 | `gba_missing.txt`（2 128 个唯一空名，按字母序）+ `gba_series.txt`（2 047 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，4 片（`gba_cn_part1..4.txt`：640 / 640 / 640 / 208 条），格式 `序号<TAB>中文名` |
| 半成品替换 | `make_gba_series_cn.py` + `gba_dict_names.py`（词表驱动）：分组前缀表 + 卡号原样保留 + 卡名/角色名词典，2 047 条一次生成 `gba_series_cn.txt`，未识别项归零 |
| 并入词库 | `apply_gba_cn.py`：候选 4 175 条，新增 4 175（0 跳过）；词库 22 672 → 26 847 行 |
| 重建 | `zh_localize.py --platforms gba` → **exact 5 961 / series 0 / none 0** |
| 自检 | ① 条数断言 2 128 == 英文清单，series 2 047 == 2 047；② 假名残留 0 条；③ 414 条含拉丁字母的逐条过（`Advance` / `UNO` / `GT` / `GBA Video` / `bit Generations` 等品牌与版本标记）；④ 17 个重复中文名复查（均为多语言版，正常） |

**GBA 阶段新增的经验**

- **卡带编号条目按「作品名 + 卡带e/卡带e+ + 系列或卡包 + 卡号 + 角色名」机械拼装**，卡号
  （`C-01-#`、`08-A001`、`07-A002`、`E-51-a`、`Z-01-a`）原样保留，不音译不意译。
  2 000 多条靠这套格式保持一致，也让同卡不同变体（`a` / `b` / `c` / `d`）能并列区分。
- **集换卡包名按英文意译**：`Aquapolis` → 水之都市、`Skyridge` → 天空山脊、
  `Expedition Base Set` → 探险基地包、`EX Sandstorm` → EX沙暴、`EX Team Magma vs Team Aqua` → EX熔岩队对水舰队；
  日文卡包 `The Town on No Map` → 地图上没有的城镇、`Wind from the Sea` → 海上之风、
  `Split Ground` → 分裂大地、`The Mysterious Mountain` → 神秘山。
- **宝可梦卡名一律用官方中文译名**（`Nidoran Male` → 尼多朗、`Mr. Mime` → 魔墙人偶、
  `Porygon2` → 多边兽2），道具卡与训练家卡同样按官方叫法（`Master Ball` → 大师球、
  `Moo-Moo Milk` → 哞哞牛奶、`Professor Elm's Training Method` → 空木博士的修行法）。
- **动物森友会的村民名按社区通行译法**（`Tom Nook` → 狸克、`Mr. Resetti` → 雷西迪先生、
  `K.K. Slider` → K.K.），曲目名照「K.K. + 曲风」格式译（`K.K. Aria` → K.K.咏叹调）。
- **同作多语言版本共用一套中文名，只用括号标语种**，与 Wii 阶段一致：`Edicion Rubi` /
  `Version Rubis` / `Rubin-Edition` 全部译「宝可梦 红宝石版（西版）/（法版）/（德版）」。
- **拼音盗版条目还原中文原意**：`Maliou Kadingche - Chaoji Saidao` → 马力欧卡丁车 超级赛道、
  `Waliou Zhizao` → 瓦力欧制造、`Sitafei De Chuanshuo` → 斯塔菲的传说、
  `Zhuanzhuanbang Tiantang` → 转转棒天堂。

**GBA 阶段的特殊坑**

- `Pokemon-e TCG` 里有 4 张卡按字母区分画作版本（`a - Drowzee`、`b - Drowzee`），
  解析时必须把小写单字母当标记、不能当卡号，否则卡名会整体错位。
- `Super Mario Advance 4-e` 的卡号后面还会再挂一个变体码（`07-A002 - Star-02 - Classic Course W1-2`），
  连续两段都符合卡号样式，提取时要循环吃掉所有卡号段再取角色名/关卡名。


---

## 六、传到 GitHub 的正确姿势

**只传表和脚本，不传图片。**

`.gitignore` 已经写好：

```gitignore
cache/                  # 下载下来的封面
manifest/               # 下载清单
match/                  # ROM 匹配结果
logs/
__pycache__/
mapping/all_games.csv   # 45 MB 合并表，可重建，不入库
index/all_games.csv
```

- 封面版权属于各游戏厂商，libretro 只是社区托管，**仓库不要再分发图片本体**；
- 仓库里只放 URL + 中文名映射，运行时按 URL 拉，或让用户本地跑 `cover_fetch.py`；
- README（本文件）已写明「封面版权归原厂商，本项目仅提供索引，供个人模拟器使用」；
- 别拿这套东西做付费软件、内置广告或二次售卖；
- 建议代码用 MIT，数据表用 CC BY 4.0（或直接 MIT），二选一写进 `LICENSE`。

首次上传：

```bash
git init
git add .
git commit -m "cover-db: 30 platforms index + zh mapping (PSP 100%)"
git branch -M main
git remote add origin git@github.com:<你的账号>/cover-db.git
git push -u origin main
```

体积参考（不含图片，实测）：`index/` 41.4 MB，`mapping/` 44.3 MB，`zh/` 0.1 MB，合计约 86 MB。
GitHub 单文件上限 100 MB，最大的一份是 `mapping/mapping_nes.csv`（9.0 MB），可以直接推。
若嫌仓库重，可以只提交 `mapping/` 里常用的几个平台，或全部走 Git LFS。

---

## 七、已知限制

- 中文名带英文字母是常态（FIFA、NBA、WWE、CLANNAD、Fate/Extra、DJMAX、.hack//Link
   这类品牌缩写按惯例保留原文），不算未翻译。

---

## 八、平台清单

| key | 平台 | 条数 | key | 平台 | 条数 |
|---|---|---:|---|---|---:|
| nes | FC | 13 439 | psp | PSP | 1 774 |
| ps1 | PS1 | 9 301 | gb | GB | 1 647 |
| ps2 | PS2 | 8 502 | gbc | GBC | 1 524 |
| nds | NDS | 7 335 | dc | DC | 1 332 |
| wii | Wii | 6 668 | xbox | XBOX | 1 324 |
| gba | GBA | 5 961 | n64 | N64 | 1 115 |
| snes | SFC | 3 689 | gg | GG | 1 056 |
| md | MD | 2 352 | pcecd | PCE-CD | 946 |
| saturn | SS | 2 294 | segacd | MCD | 609 |
| 3ds | 3DS | 2 148 | sms | SMS | 559 |
| ngc | NGC | 1 954 | pce | PCE | 479 |
| wiiu | WiiU | 454 | ws | WS | 299 |
| neogeo | NEOGEO | 257 | wsc | WSC | 239 |
| 32x | 32X | 209 | ngpc | NGPC | 118 |
| ps3 | PS3 | 67 | psvita | PSV | 9 |
| ps3dl | PS3DL | 1 | | | |

---

## 九、更新日志

- **2026-11**：GBA 全量中文化（5 961 / 5 961，100%），含 2 047 个 series 半成品整行替换（其中大半是 e-Reader 卡带条目）；
  词库 22 672 → 26 847 行；全量重建后 exact 58 406 → 63 615（81.9%），中文覆盖 79.5% → 83.2%。
- **2026-11**：Wii 全量中文化（6 668 / 6 668，100%），含 195 个 series 半成品整行替换；
  词库 20 580 → 22 672 行；全量重建后 exact 53 899 → 58 406（75.2%），中文覆盖 74.5% → 79.5%。
- **2026-11**：FC（NES）全量中文化（13 439 / 13 439，100%），含 167 个 series 半成品整行替换；
  词库 17 921 → 20 580 行；全量重建后 exact 42 611 → 53 899（69.4%），中文覆盖 60.8% → 74.5%。
- **2026-11**：NDS 全量中文化（7 335 / 7 335，100%），含 243 个 series 半成品整行替换；
  词库 13 284 → 17 921 行；全量重建后 exact 35 351 → 42 611（54.9%），中文覆盖 52.2% → 60.8%。
- **2026-11**：PS1 全量中文化（9 301 / 9 301，100%），含 174 个 series 半成品整行替换；
  词库 8 099 → 13 284 行；全量重建后 exact 25 836 → 35 351（45.5%），中文覆盖 40.8% → 52.2%。
- **2026-11**：PS2 全量中文化（8 502 / 8 502，100%），含 269 个 series 半成品整行替换；
  词库 4 027 → 8 099 行；全量重建后 exact 17 303 → 25 836（33.3%），中文覆盖 31.1% → 40.8%。
- **2026-11**：3DS 全量中文化（2 148 / 2 148，100%），含 170 个 series 半成品整行替换；
  词库 2 809 → 4 027 行；全量重建后 exact 15 136 → 17 303（22.3%），中文覆盖 28.8% → 31.1%。
- **2026-11**：PSP 全量中文化（1 774 / 1 774，100%）；词库 581 → 2 809 条；
  补 1 000+ 跨平台经典标题；新增 `zh_coverage.py`；README 重写（含覆盖率表与补名流程）。
- 之前：从 libretro-thumbnails 抓 30 平台索引，建立 exact / series 两级匹配与三图 URL 结构。

---

封面版权归各游戏厂商所有，本项目仅提供索引、URL 与中文名映射，供个人模拟器与 ROM 管理使用。

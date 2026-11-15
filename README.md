# Emulator-cover-db-zh · 模拟器封面索引 & 中英名映射表

本项目由AI制作给模拟器启动器、ROM 整理工具做刮削用的**纯 CSV 方案**：仓库里只放表和数据，不放图片。
封面仍然由 libretro 官方源托管，工具运行时按表里的 URL 去拉，或者用脚本提前拉到本地缓存。

- **31 个平台 / 77 661 条**记录（含区域、版本、三种图 URL）
- **中文名覆盖 100.0%**（exact 77 661 条 + series 0 条，全平台零空名）；36 797 个唯一英文名里 96.1% 有中文（35 368 个）
- **全部 31 个平台 100% 中文**（FC 13 439 / PS1 9 301 / PS2 8 502 / NDS 7 335 / Wii 6 668 / GBA 5 961 / SFC 3 689 / MD 2 352 / SS 2 294 / 3DS 2 148 / NGC 1 954 / PSP 1 774 / GB 1 647 / GBC 1 524 / DC 1 332 / XBOX 1 324 / N64 1 115 / GG 1 056 / PCE-CD 946 / MCD 609 / SMS 559 / PCE 479 / WiiU 454 / WS 299 / NEOGEO 257 / WSC 239 / 32X 209 / NGPC 118 / PS3 67 / PSV 9 / PS3DL 1，全部 exact，无空名、无 series 半成品）
- 中文名库 `zh/zh_titles.csv` 35 477 行（去重后 35 465 条参与匹配），系列词表 `zh/zh_series.csv` 171 条，可持续往上加
- **中文多译**：`alias_cn` 列已铺满全库 —— 4 200 个词条、12 672 个别名（平均 3 个/条），
  8 533 条映射带多译（宝可梦 = 精灵宝可梦 / 口袋妖怪 / 口袋怪兽 / 宠物小精灵 / 神奇宝贝，
  马力欧 = 马里奥 / 玛莉欧 / 玛利欧，索尼克 = 音速小子 / 刺猬索尼克，
  生化危机 = 恶灵古堡，合金装备 = 潜龙谍影，怪物猎人 = 魔物猎人 …）

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
├── gen_alias.py          # 生成「中文多译」列 alias_cn（术语级替换）
├── run_all.sh            # 一键跑全流程
├── index/                # 原始索引（无中文名）
│   └── libretro_<平台>.csv
├── mapping/              # 成品映射表（中文名 + 首选区域标记）
│   └── mapping_<平台>.csv
├── zh/
│   ├── zh_titles.csv     # 精确中文名库（35 477 行 / 35 465 条，含 alias_cn 多译列）
│   └── zh_series.csv     # 系列名 / 关键词表（171 条）
├── terms/
│   └── 术语多译表.csv    # 54 组同义叫法（生成 alias_cn 用的词源，可人工增改）
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
| alias_cn | 其它中文叫法，`|` 分隔（口袋妖怪 / 宠物小精灵 …），搜索和显示可用来兜底 |
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

### 中文多译（`alias_cn`）

同一个作品在不同地区有几套中文叫法，全库只保留**一个主名**（`name_cn`），其余叫法进 `alias_cn`，
用 `|` 分隔。生成方式是**术语级替换**，不是逐条机翻：

| 主线名（name_cn） | 其它叫法（alias_cn） |
|---|---|
| 宝可梦 红 | 精灵宝可梦 红 / 口袋妖怪 红 / 口袋怪兽 红 / 宠物小精灵 红 / 神奇宝贝 红 |
| 马力欧赛车64 | 马里奥赛车64 / 玛莉欧赛车64 / 玛利欧赛车64 |
| 生化危机2 | 恶灵古堡2 |
| 索尼克大冒险 | 音速小子大冒险 / 刺猬索尼克大冒险 |
| 超级街头霸王2 X 对战服务版 | 超级街霸2 X 对战服务版 |
| 合金装备5 原爆点 | 潜龙谍影5 原爆点 |

规则：

- 每组取「名字里出现的**最长**那个变体」当锚点再替换，短词不会吃掉长词（`宠物小精灵` 不会被拆成 `宠物吃豆人`）；
- 两组同时命中（`超级机器人大战` + `高达`）时做组合，最多 2 组、每行 6 个别名，防止爆炸；
- 同义词源在 `terms/术语多译表.csv`（54 组），改完跑 `python3 gen_alias.py` 就能全库重算；
- `alias_cn` **不参与英文名匹配**：匹配只认 `search_key`，别名是给人看 / 给搜索框兜底用的，加错别名不会污染覆盖率。

### 各平台中文覆盖率

| key | 平台 | 总条数 | exact | series | manual | 未匹配 | 中文覆盖率 |
|---|---|---:|---:|---:|---:|---:|---:|
| nes | FC | 13 439 | 13 439 | 0 | 0 | 0 | 100.0% |
| ps1 | PS1 | 9 301 | 9 301 | 0 | 0 | 0 | 100.0% |
| ps2 | PS2 | 8 502 | 8 502 | 0 | 0 | 0 | 100.0% |
| nds | NDS | 7 335 | 7 335 | 0 | 0 | 0 | 100.0% |
| wii | Wii | 6 668 | 6 668 | 0 | 0 | 0 | 100.0% |
| gba | GBA | 5 961 | 5 961 | 0 | 0 | 0 | 100.0% |
| snes | SFC | 3 689 | 3 689 | 0 | 0 | 0 | 100.0% |
| md | MD | 2 352 | 2 352 | 0 | 0 | 0 | 100.0% |
| saturn | SS | 2 294 | 2 294 | 0 | 0 | 0 | 100.0% |
| 3ds | 3DS | 2 148 | 2 148 | 0 | 0 | 0 | 100.0% |
| ngc | NGC | 1 954 | 1 954 | 0 | 0 | 0 | 100.0% |
| psp | PSP | 1 774 | 1 774 | 0 | 0 | 0 | 100.0% |
| gb | GB | 1 647 | 1 647 | 0 | 0 | 0 | 100.0% |
| gbc | GBC | 1 524 | 1 524 | 0 | 0 | 0 | 100.0% |
| dc | DC | 1 332 | 1 332 | 0 | 0 | 0 | 100.0% |
| xbox | XBOX | 1 324 | 1 324 | 0 | 0 | 0 | 100.0% |
| n64 | N64 | 1 115 | 1 115 | 0 | 0 | 0 | 100.0% |
| gg | GG | 1 056 | 1 056 | 0 | 0 | 0 | 100.0% |
| pcecd | PCE-CD | 946 | 946 | 0 | 0 | 0 | 100.0% |
| segacd | MCD | 609 | 609 | 0 | 0 | 0 | 100.0% |
| sms | SMS | 559 | 559 | 0 | 0 | 0 | 100.0% |
| pce | PCE | 479 | 479 | 0 | 0 | 0 | 100.0% |
| wiiu | WiiU | 454 | 454 | 0 | 0 | 0 | 100.0% |
| ws | WS | 299 | 299 | 0 | 0 | 0 | 100.0% |
| neogeo | NEOGEO | 257 | 257 | 0 | 0 | 0 | 100.0% |
| wsc | WSC | 239 | 239 | 0 | 0 | 0 | 100.0% |
| 32x | 32X | 209 | 209 | 0 | 0 | 0 | 100.0% |
| ngpc | NGPC | 118 | 118 | 0 | 0 | 0 | 100.0% |
| ps3 | PS3 | 67 | 67 | 0 | 0 | 0 | 100.0% |
| psvita | PSV | 9 | 9 | 0 | 0 | 0 | 100.0% |
| ps3dl | PS3DL | 1 | 1 | 0 | 0 | 0 | 100.0% |
| **合计** | **31 平台** | **77 661** | **77 661** | **0** | **0** | **0** | **100.0%** |

表由 `python3 zh_coverage.py` 生成，改完词库后重跑一次就能刷新，不要手抄。

2026-11 起 31 个平台的**未匹配归零**：连 Action Replay 作弊卡、2-in-1 合卡、光枪合辑、
杂志附录碟、开发用示例程序这种「本来没有官方中文名」的条目，也都给了可用的中文名。
热门作品（最终幻想、勇者斗恶龙、塞尔达、马力欧、宝可梦、怪物猎人、合金装备、生化危机、
鬼泣、战神、皇牌空战、实况、无双、传说、女神异闻录等）全部走既有官方中文名。
需要说明的是，冷门日系、韩版、巴西葡版的标题**不是官方中文名，而是按作品原名直译**，
可读性优先、检索可用，但不要当作发行商官方译名引用。

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
- 授权体育年货（`John Madden` / `NFL` / `NBA` / `World Series Baseball` / `F1 Circus`）要固定成「项目 + 年份」的统一格式，`'92` `'95` `Volume 2` 这类标记原样保留；否则同一系列逐年一条，刮削结果里会出现十几种写法。
- 写译名分片时 `序号<TAB>中文名` 的 TAB 极易被打成空格，`build_key_cn.py` 会直接报「第 N 行没有 TAB」；写完先跑一行 python 扫描无 TAB 行，能省一次返工（本轮 GBC 第 22 行、NGC 第 237 行都中过这个坑）。
- 分片文件名必须严格是 `<key>_cn_partN.txt` 才会被自动发现；本轮 NGC 首片曾误存成 `ngc_cn_all_src.txt`，改名后才通过。没有 series 的平台（32X、PS3DL）要放一个**空的** `<key>_series_cn.txt`，否则 `apply_key_cn.py` 找不到对齐文件。
- Saturn 这类日本独占平台的主体是麻雀、柏青哥、赛马、将棋、偶像写真碟，标题里全是罗马字与片假名，译名要「按原名直译，不补意译副标」，`Private Idol Disc Vol. 1 - Yuu Kinoshita` 这类写真碟只做「私人偶像碟 第1卷 木下优」的对应，不要尝试加形容。
- 跨平台同名的 123 条 MD 条目被 `norm()` 判定已存在而跳过，这不是漏译：词库是全平台共享的，前几个平台译过的名字会自动生效，统计时要按 `apply_key_cn.py` 输出的「新增 / 跳过」分开看。

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


### SFC（snes）全量中文化（3 689 / 3 689，100%）

SFC 是这批平台里「日式冷门标题」密度最高的一块：`Koushien 2/3/4`（甲子园）、
`Derby Stallion 96/98/II/III`（德比赛马）、`Parlor! Mini 1–7`（柏青哥）、
`Picross NP Vol.1–8`（图片方块）、`Super F1 Circus`、`Super Fire Pro Wrestling`
系列、`Super Formation Soccer 94/95/96`、`Super Famista 1–5`、`Super Power League 1–4`，
以及一堆将棋、麻将、赛马、棒球作品。这些没有官方中文名，按作品原名直译；
动画改编侧则集中了 `Dragon Ball Z` 十余条变体、`Sailor Moon` 七条、
`Gundam` 系列、`Super Robot Taisen`；欧美授权侧是 NBA / NFL / NHL / NCAA /
John Madden / Bill Walsh / Brett Hull / Cal Ripken，以及 `Tiny Toon`、`Looney Tunes`、
`Mickey`、`Simpsons`、`Addams Family`。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_snes.csv` 3 689 行：exact 1 116 / series 100 / none 2 473（空名唯一 1 704 个，series 唯一 58 条） |
| 导出清单 | `snes_missing.txt`（1 704 个唯一空名，按字母序）+ `snes_series.txt`（58 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，6 片（`snes_cn_part1..6.txt`：300 / 300 / 300 / 300 / 300 / 204 条），格式 `序号<TAB>中文名` |
| 校验 | `build_key_cn.py snes 1704`：自动找分片、按文件顺序重编号、断言条数、与英文清单 zip 成 TSV |
| 并入词库 | `apply_key_cn.py snes 1704 58`：候选 1 762 条，新增 1 762（0 跳过）；词库 26 847 → 28 609 行 |
| 重建 | `zh_localize.py` 全量 → **exact 3 689 / series 0 / none 0**；全库 exact 63 615 → 67 921 |
| 自检 | ① 条数断言 1 704 == 英文清单，series 58 == 58；② 假名残留 0 条；③ 172 条含拉丁字母的抽查（`F-1` / `RPG` / `Vol.` / `FIFA` / `CD` 等版本与系列标记）；④ 25 个重复中文名复查（均为多语言版或同作不同区域，正常） |

**SFC 阶段 series 改写要点**

`ActRaiser 2 - Chinmoku e no Seisen` → 创造者2 沉默的圣战、`Castlevania - Dracula X` → 恶魔城 德古拉X、
`Contra IV - The Alien Wars` → 魂斗罗4 异形战争、`Fire Emblem - Monshou no Nazo` → 纹章之谜、
`Seisen no Keifu / Genealogy of the Holy War` → 圣战之系谱、`Thracia 776` → 多拉基亚776、
`Front Mission Series - Gun Hazard` → 前线任务系列 枪之危机、`Mother 2 - Gyiyg no Gyakushuu` → 地球冒险2 基格的逆袭、
`Rockman 7 - Shukumei no Taiketsu!` → 洛克人7 宿命的对决！、
`Super Mario RPG - Legend of the Seven Stars` → 超级马力欧RPG 七星传说、
`Tetris _ Dr. Mario` → 俄罗斯方块与马力欧医生、`Kirby no Kirakira Kids` → 星之卡比 闪亮小朋友、
`Kunio no Oden` → 国雄的关东煮、`FIFA - A Caminho Da Copa 98` → FIFA 98世界杯之路（巴西版）、
`Legend of Zelda, The - A Link to the Past - Redux` → 塞尔达传说 众神的三角力量 重制版。

### MD（Mega Drive / Genesis）全量中文化（2 352 / 2 352，100%）

MD 这一轮的特点有三块：一是**授权体育年货**，`John Madden Football` 从 '92 排到
Championship Edition、`NFL '94/95/98`、`NHL '94/95`、`NBA Action/Live/Showdown`、
`NCAA Football`、`World Series Baseball '95/'96/98`，同一作品每年一条，译名必须保持
「项目 + 年份」的统一格式；二是**中文 / 韩文盗版与地区改版**，`16 Zhang Ma Jiang`（16张麻将）、
`San Guo Zhi Lie Zhuan - Luan Shi Qun Ying`（三国志列传 乱世群英）、`Shui Hu - Feng Yun Zhuan`（水浒 风云传）、
`Barver Battle Saga - Tai Kong Zhan Shi`（巴贝尔战记 太空战士）、`Hua Mu Lan - Mulan`（花木兰）、
`Xin Qi Gai Wang Zi`（新乞丐王子）、`Zhuo Gui Da Shi - Ghost Hunter`（捉鬼大师）、
`On Dal Jang Goon`（温达将军）、`Uzu Keobukseon`（宇宙龟船）、`Dong Gu Ri Te Chi Jak Jeon`；
三是**葡语巴西版**，`Show do Milhao`（百万富翁秀）、`Ferias Frustradas do Pica Pau`、
`Turma da Monica na Terra dos Monstros`（莫妮卡小队在怪物之地）。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_md.csv` 2 352 行：exact 939 / series 89 / none 1 324（空名唯一 815 个，series 唯一 46 条） |
| 导出清单 | `md_missing.txt`（815 个唯一空名）+ `md_series.txt`（46 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，3 片（`md_cn_part1..3.txt`：300 / 300 / 215 条） |
| 校验 | `build_key_cn.py md 815`：断言条数、series 46 == 46、假名 0、含拉丁字母 83 条抽查、重复中文名 11 个 |
| 并入词库 | `apply_key_cn.py md 815 46`：候选 861 条，新增 738 条，**123 条因跨平台同名已存在而跳过**（Sonic、Landstalker 等在前几个平台已译过）；词库 28 609 → 29 347 行 |
| 重建 | `zh_localize.py` 全量 → **exact 2 352 / series 0 / none 0**；全库 exact 67 921 达成 87.5%，覆盖 88.5% |

**MD 阶段译名要点**

`Bare Knuckle / Streets of Rage` 统一「怒之铁拳」（2 代带副标 死斗的镇魂歌）、
`Langrisser` → 梦幻模拟战、`Landstalker` → 陆地追踪者（德版 / 法版共用，括号标语种）、
`Shining and the Darkness` → 光明与黑暗、`Ragnacenty` → 拉格纳森蒂（韩版同译）、
`Puyo Puyo 2` → 魔法气泡2、`James Pond` 系列 → 水下特工 / 代号机器鳕鱼 / 星鱼作战、
`Slime World` → 黏液世界、`Ballz 3D` 两条 → 3D球体格斗 / 3D球体之战。

**两个通用脚本替代了逐平台脚本**

这一轮起不再每平台复制一份 build / apply 脚本，改成两个参数化脚本，后续平台直接复用：

| 脚本 | 用法 | 作用 |
|---|---|---|
| `build_key_cn.py` | `python build_key_cn.py <key> <expect条数>` | 正则 `%s_cn_part\d+\.txt` 自动发现分片、按文件顺序重编号、断言条数、与英文清单 zip 成 `<key>_cn_all.tsv`、series 对齐成 `<key>_series_uniq.txt`，并抽查假名 / 拉丁字母 / 重复名 |
| `apply_key_cn.py` | `python apply_key_cn.py <key> <expect_missing> <expect_series>` | 备份 `zh_titles.csv.bak<key>`、用 `zh_localize.norm()` 去重、追加进词库，打印「候选 / 新增 / 跳过 / 词库 before→after」 |

### SS（Sega Saturn）全量中文化（2 294 / 2 294，100%）

Saturn 是这批平台里**日式作品密度最高、类型最杂**的一块：麻雀、柏青哥、赛马、将棋、
偶像写真碟、恋爱模拟、世嘉自家街机移植全挤在一张清单里。735 个唯一空名里有相当一部分
是当年只在日本发行的片子，译名按作品原名直译（`Tokimeki Mahjong Paradise` → 心跳麻将乐园、
`Private Idol Disc` → 私人偶像碟、`Jissen! Pachi-Slot Hisshou-hou!` → 实战！柏青嫂必胜法！）。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_saturn.csv` 2 294 行：exact 1 056 / series 58 / none 1 180（空名唯一 735 个，series 唯一 29 条） |
| 导出清单 | `saturn_missing.txt`（735 个唯一空名，按字母序）+ `saturn_series.txt`（29 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐，3 片（`saturn_cn_part1..3.txt`：300 / 300 / 135 条） |
| 校验 | `build_key_cn.py saturn 735`：断言条数、series 29 == 29、假名 0、含拉丁字母 72 条抽查、重复中文名 13 个 |
| 并入词库 | `apply_key_cn.py saturn 735 29`：候选 764 条，新增 764（0 跳过）；词库 29 347 → 30 111 行 |
| 重建 | `zh_localize.py` 全量 → **exact 2 294 / series 0 / none 0**；全库 exact 67 921 → 69 214（89.1%），覆盖 90.1% |

**Saturn 译名要点**

- **世嘉自家品牌统一叫法**：`Sega Ages` → 世嘉世纪（`After Burner II` → 冲破火网2、
  `Space Harrier` → 太空哈利、`Fantasy Zone` → 幻想空间、`Galaxy Force II` → 银河力量2）、
  `Virtua Fighter` → VR战士、`Virtua Cop` → 虚拟警察、`Virtual On` → 虚拟战士 赛博骑兵、
  `Daytona USA` → 戴通纳USA、`Sega Rally Championship` → 世嘉拉力锦标赛。
- **同作多区域版本共用一套中文名，只用括号标语种**：`Manoir des Ames Perdues, Le` /
  `Mansion de las Almas Ocultas, La` / `Mansion of Hidden Souls, The` 全部「隐藏灵魂的宅邸」；
  `Dragon Ball Z - La Grande Legende des Boules de Cristal` → 龙珠Z 龙珠大传说（法版）。
- **日文作品按原名直译、不加意译副标**：`Doukoku Soshite...` → 恸哭 然后…、
  `Nanatsu Kaze no Shima Monogatari` → 七风岛物语、`Ousama Game` → 国王游戏、
  `Ruriiro no Yuki` → 琉璃色的雪、`Strahl - Himerareshi Nanatsu no Hikari` → 修特拉尔 被解放的七道光。
- **版本号与改版标记原样保留**：`v1.400` / `v1.000` / `v1.100` / `v1.003` / `Ver.9.7`
  这类校验和标记不翻译，直接跟在中文名后面。
- **series 侧重点**：`Shining Force III` 三个剧本（王都的巨神 / 被瞄准的巫女 / 冰壁的邪神殿）
  + 特典碟、`Shin Megami Tensei - Devil Summoner` → 真·女神转生 恶魔召唤师、
  `Dragon Force II` → 龙之力量2 神去之大地、`Grandia` 两份（序章 / 数字博物馆）、
  29 条 `Virtua Fighter CG Portrait Series` 全部「VR战士 CG肖像系列 第N卷 角色名」。

### GB（Game Boy）全量中文化（1 647 / 1 647，100%）

GB 是这批里**日本应试学习软件与冷门独占作最密集**的一块：836 个唯一空名里有约 30 条是「Goukaku Boy Series / Goukaku Boy GOLD」出的考学软件，其余多为日本独占的麻雀、柏青哥、赛马、将棋、偶像写真与玩具衍生作。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_gb.csv` 1 647 行：exact 811 / series 65 / none 771（空名唯一 836 个，series 唯一 65 条） |
| 导出清单 | `gb_missing.txt`（836 个唯一空名）+ `gb_series.txt`（65 条 series 唯一名，带现有半成品中文） |
| 译名文件 | 按行号对齐 3 片（`gb_cn_part1..3.txt`：280 / 280 / 276 条）+ `gb_series_cn.txt` 65 条 |
| 校验 | `build_key_cn.py gb 836`：断言条数、series 65 == 65、假名 0、含拉丁字母抽查、重复中文名核对 |
| 并入词库 | `apply_key_cn.py gb 836 65`：候选 901 条，新增 901（0 跳过）；词库 30 111 → 31 012 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 647 / series 0 / none 0** |

**GB（Game Boy） 译名要点**

- **Goukaku Boy 系列统一叫法**：`Goukaku Boy Series - ...` 一律「应试小子系列 + 学科 + 目标数」，`Goukaku Boy GOLD - ...` 一律「应试小子 GOLD + 学科」，不逐条造新词。
- **冷门日本独占作按原名直译**：麻雀 / 柏青哥 / 赛马 / 将棋 / 偶像写真 / 育儿玩具衍生一律直译，不补意译副标（`Nakajima Miho - Fantasy Zone` → 中岛美穗 幻想地带）。
- **已覆盖的系列线**：`Nettou` 热斗系列 8 条、`Mani 4 in 1` 四合一合辑 5 条（逐作中文名串联）、`Little Master` / `Sa-Ga` / `Wizardry Gaiden` / `SD Gundam` / `SD Sengokuden` / `Yu Yu Hakusho Dai-2/3/4-dan`、忍者神龟 8 条、辛普森一家 4 条、`Looney Tunes` / `Tiny Toon` / `Mickey Mouse II/IV/V`、`Pocket Monsters` 红/蓝/绿/皮卡丘、`Zelda` 梦见岛、`Super Donkey Kong GB`、星之卡比 1/2。
- **series 65 条改写成纯中文**：`Bomberman GB` → 炸弹人 GB、`Castlevania - The Adventure` → 恶魔城 冒险、`Pokemon - Rote Edition` → 宝可梦 红版（德版）。

### GBC（Game Boy Color）全量中文化（1 524 / 1 524，100%）

GBC 的 823 个唯一空名以**欧美版权作 + 日本独占恋爱/育成/柏青哥**为主，同一个作品往往有英/法/德/西/意多语言卡带，中文名共用一套、只用括号标语种。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_gbc.csv` 1 524 行：exact 701 / series 80 / none 743（空名唯一 823 个，series 唯一 80 条） |
| 译名文件 | 3 片（`gbc_cn_part1..3.txt`：280 / 280 / 263 条）+ `gbc_series_cn.txt` 80 条 |
| 校验 | `build_key_cn.py gbc 823`：series 80 == 80、假名 0；曾因分片第 22 行 TAB 打成空格被拦下，修正后通过 |
| 并入词库 | `apply_key_cn.py gbc 823 80`：候选 903 条，新增 884、跳过 19；词库 31 012 → 31 896 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 524 / series 0 / none 0** |

**GBC（Game Boy Color） 译名要点**

- **多语言多区域只加语种括号**：`Harvest Moon GBC 2/3`、`Dragon Ball Z` 五种语言版、`Harry Potter` 系列均共用一套中文名。
- **韩版宝可梦按对应版本命名**：`Pocket Monsters Eun/Geum` → 宝可梦 银/金（韩版）。
- **series 80 条改写重点**：`Biohazard Gaiden` → 生化危机 外传、`Metal Gear - Ghost Babel` → 合金装备 幽灵通天塔、`Rockman X - Cyber Mission` → 洛克人X 网络任务、`Super Mario Bros. Deluxe` → 超级马力欧兄弟 豪华版、`Legend of Zelda DX` → 塞尔达传说 梦见岛 DX。

### NGC（GameCube）全量中文化（1 954 / 1 954，100%）

NGC 的 267 个唯一空名里，**金手指碟与二合一合辑占了一大块**（Action Replay 14 条、2 Games in 1 12 条），剩下是任天堂自家作 + 日本独占动画改编 + 五语种哈利波特。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ngc.csv` 1 954 行：exact 1 687 / series 48 / none 219（空名唯一 267 个，series 唯一 48 条） |
| 译名文件 | `ngc_cn_part1.txt`（267 条）+ `ngc_series_cn.txt` 48 条 |
| 校验 | `build_key_cn.py ngc 267`：series 48 == 48、假名 0；首片曾误存为 `ngc_cn_all_src.txt`，改名后才被自动发现 |
| 并入词库 | `apply_key_cn.py ngc 267 48`：候选 315 条，新增 315（0 跳过）；词库 31 896 → 32 211 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 954 / series 0 / none 0** |

**NGC（GameCube） 译名要点**

- **金手指碟统一前缀**：`Action Replay` 14 条一律「Action Replay 终极代码 / 终极金手指 + 作品名」。
- **二合一合辑统一写法**：`2 Games in 1 - A + B` → 「二合一 + 两作中文名（括号语种）」。
- **任天堂自家品牌**：`Dairantou Smash Brothers DX` → 大乱斗 斯马什兄弟 DX（保留原写法）、`Bokujou Monogatari` → 牧场物语系列、`Naruto - Gekitou Ninja Taisen!` → 火影忍者 激斗忍者大战！1–4、`Star Wars Rogue Squadron` → 星球大战 侠盗中队2/3、`Zoids Vs.` → 机兽VS. I/II/III。
- **series 48 条改写重点**：`Baten Kaitos` → 霸天开拓史 系列、`Fire Emblem - Souen no Kiseki` → 火焰纹章 苍炎之轨迹、`Phantasy Star Online` → 梦幻之星在线 第1与2章 / 第3章 卡片革命、`Sonic Adventure DX` → 索尼克大冒险 DX 导演剪辑版。

### DC（Dreamcast）全量中文化（1 332 / 1 332，100%）

DC 的 567 个唯一空名以**日本独占恋爱/柏青哥/将棋/麻将/偶像碟 + 世嘉自家作**为主，还有大量「杂志附录碟」按卷号排列。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_dc.csv` 1 332 行：exact 743 / series 22 / none 567（空名唯一 567 个，series 唯一 22 条） |
| 译名文件 | 2 片（`dc_cn_part1..2.txt`：290 / 277 条）+ `dc_series_cn.txt` 22 条 |
| 校验 | `build_key_cn.py dc 567`：series 22 == 22、假名 0 |
| 并入词库 | `apply_key_cn.py dc 567 22`：候选 589 条，新增 581、跳过 8；词库 32 211 → 32 792 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 332 / series 0 / none 0** |

**DC（Dreamcast） 译名要点**

- **杂志附录碟按卷号统一**：`Dream Passport` / `Dreamkey` / `Dorimaga GD` / `Generator` / `Official Sega Dreamcast Magazine` 一律「多利杂志 GD 第N卷」「官方世嘉DC杂志 第N卷 年月」。
- **版本号原样保留**：`VR射手2 Ver.2000.1` / `v1.000`–`v1.003` / `Ver.2000` 不翻译。
- **世嘉品牌统一**：`Virtua Tennis` → 虚拟网球、`Sega Rally 2` → 世嘉拉力2、`Daytona USA 2001` → 戴通纳USA 2001、`Sakura Taisen` → 樱花大战、`Sakura Wars 3 - Les Chattes Noires` → 樱花大战3 黑猫馆、`Jojo no Kimyou na Bouken` → JOJO的奇妙冒险 未来的遗产（3 条 + 对战服务版）。
- **series 22 条**：`Biohazard - Code - Veronica` → 生化危机 代号维罗妮卡（体验版）、`Shenmue - Ichishou Yokosuka` → 莎木 第一章 横须贺、`Street Fighter III` → 街霸3 三度冲击 / 双重冲击、`Street Fighter Zero 3` → 街霸ZERO 3 最强流道场。

### PCE-CD（PC Engine CD）全量中文化（946 / 946，100%）

PCE-CD 的 451 个唯一空名是**纯日本独占 CD 作品**，罗马字与片假名满屏，另有卡拉OK碟与「PC Engine 超级目录」这类资料碟按卷号成组出现。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_pcecd.csv` 946 行：exact 491 / series 4 / none 451（空名唯一 451 个，series 唯一 4 条） |
| 译名文件 | 2 片（`pcecd_cn_part1..2.txt`：240 / 211 条）+ `pcecd_series_cn.txt` 4 条 |
| 校验 | `build_key_cn.py pcecd 451`：series 4 == 4、假名 0、含拉丁字母 78 条抽查 |
| 并入词库 | `apply_key_cn.py pcecd 451 4`：候选 455 条，新增 454、跳过 1；词库 32 792 → 33 246 行 |
| 重建 | `zh_localize.py` 全量 → **exact 946 / series 0 / none 0** |

**PCE-CD（PC Engine CD） 译名要点**

- **卡拉OK碟两组各 5 条 + 重复 10 条统一**：`ROM2 Karaoke Volume 1–5` 与 `ROM^2 Karaoke Vol. 1–5` 全部「ROM²卡拉OK 第N集 / 第N卷 + 副标」。
- **资料碟按年份季节**：`PC Engine Hyper Catalog CD-ROM` 6 条统一「PC Engine超级目录 CD-ROM + 年份季节」。
- **系列作统一**：`Tengai Makyou` → 天外魔境 系列、`Cosmic Fantasy` → 宇宙幻想 1–4、`Valis` → 瓦利斯 2–4 幻想战士、`Tengai Makyou - Ziria` → 天外魔境 自来也（含非卖品）。
- **日本独占 CD 作按原名直译、不补意译副标**。series 4 条：炸弹人'94 体验版、炸弹人 恐慌轰炸、宇宙巡航机2 高法的野望、双蜂 归来。

### N64（Nintendo 64）全量中文化（1 115 / 1 115，100%）

N64 的 347 个唯一空名里有一批**中文拼音条目**（`Shen You Mario` / `Zhì Piàn Mario` / `Sai Er Da Chuan Shuo` 这类），是当年神游机与港台版留下的汉化名，译文直接还原成正式中文名。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_n64.csv` 1 115 行：exact 739 / series 29 / none 347（空名唯一 347 个，series 唯一 29 条） |
| 译名文件 | 2 片（`n64_cn_part1..2.txt`：180 / 167 条）+ `n64_series_cn.txt` 29 条 |
| 校验 | `build_key_cn.py n64 347`：series 29 == 29、假名 0、含拉丁字母 49 条抽查、重复中文名 6 个 |
| 并入词库 | `apply_key_cn.py n64 347 29`：候选 376 条，新增 331、跳过 45；词库 33 246 → 33 577 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 115 / series 0 / none 0** |

**N64（Nintendo 64） 译名要点**

- **拼音条目还原正式名**：`Shen You Mario` / `Shenyou Maliou` → 神游马力欧、`Zhi Pian Mario` → 纸片马力欧、`Sai Er Da Chuan Shuo - Shiguang zhi Di` / `Zelda Chuanshuo Shiguang Zhi Di` → 塞尔达传说 时光之笛、`Xing Ji Huo Hu` → 星际火狐、`Yao Xi Gu Shi` → 耀西故事、`Zui Yu Fa Diqiu De Jicheng Zhe` → 罪与罚 地球的继承者。
- **日版与欧美版分开走**：`Akumajou Dracula Mokushiroku` → 恶魔城 默示录（+ 外传 科内尔的传说）、`Banjo to Kazooie no Daibouken` → 班卓与卡祖的大冒险、`F-Zero X - Weilai Saiche` → F-Zero X 未来赛车。
- **体育/摔角按真实品牌**：`Jikkyou Powerful Pro Yakyuu` 5 条（2000 / 4 / 5 / 6 + 基础版2001）、`J.League` 4 条、`International Superstar Soccer` 3 条、`Virtual Pro Wrestling` 2 条。
- **series 29 条**：塞尔达三作（姆吉拉的假面 重制版 / 时光之笛 里时之笛 / 时光之笛 重制版）、炸弹人 3 条、马力欧派对 2/3、宝可梦竞技场 2 与 金·银。

### XBOX（初代 Xbox）全量中文化（1 324 / 1 324，100%）

Xbox 的 337 个唯一空名基本是**欧美版权作 + 世嘉/特库摩移植 + 车球年货**，最大的一坨是 `Club Football` 按俱乐部拆出来的 20 条。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_xbox.csv` 1 324 行：exact 965 / series 22 / none 337（空名唯一 337 个，series 唯一 22 条） |
| 译名文件 | 2 片（`xbox_cn_part1..2.txt`：180 / 157 条）+ `xbox_series_cn.txt` 22 条 |
| 校验 | `build_key_cn.py xbox 337`：series 22 == 22、假名 0、含拉丁字母 49 条抽查 |
| 并入词库 | `apply_key_cn.py xbox 337 22`：候选 359 条，新增 341、跳过 18；词库 33 577 → 33 918 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 324 / series 0 / none 0** |

**XBOX（初代 Xbox） 译名要点**

- **按俱乐部拆的版本统一格式**：`Club Football - 2003-04 Season [ACM]` → 俱乐部足球 2003-04赛季 [AC米兰]，16 家俱乐部（AC米兰/阿贾克斯/阿斯顿维拉/多特蒙德/凯尔特人/切尔西/巴塞罗那/拜仁/汉堡/国际米兰/尤文图斯/利兹联/利物浦/曼联/流浪者/皇马）逐个对应，`Club Football 2005` 4 条同法。
- **车球年货按品牌**：`ESPN` 系列 6 条、`NFL / NHL / NBA` 系列各 3–5 条、`NASCAR / IHRA` 赛车线。
- **汤姆·克兰西品牌统一**：`Ghost Recon` → 幽灵行动、`Rainbow Six` → 彩虹六号、`Splinter Cell` 归入同一套译法。
- **series 22 条**：光环三碟装 / 光环2 多人地图包、侠盗猎车手 双碟装 / 三部曲 / 罪恶都市与3的 XBOX合集、拳皇 2002-2003 与 极限冲击狂热、合金弹头4&5、梦幻之星在线 第1与2章。

### PCE（PC Engine HuCard）全量中文化（479 / 479，100%）

PCE 的 243 个唯一空名是**日本独占 HuCard 卡带作**：射击、麻将、柏青哥、棒球、将棋占绝大多数，译名按原名直译。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_pce.csv` 479 行：exact 231 / series 5 / none 243（空名唯一 243 个，series 唯一 5 条） |
| 译名文件 | `pce_cn_part1.txt`（243 条）+ `pce_series_cn.txt` 5 条 |
| 校验 | `build_key_cn.py pce 243`：series 5 == 5、假名 0、含拉丁字母 18 条抽查 |
| 并入词库 | `apply_key_cn.py pce 243 5`：候选 248 条，新增 242、跳过 6；词库 33 918 → 34 160 行 |
| 重建 | `zh_localize.py` 全量 → **exact 479 / series 0 / none 0** |

**PCE（PC Engine HuCard） 译名要点**

- **同一作品的美日两名并存**：`PC Genjin` → PC原人、`PC Denjin` → PC电人 朋克赛博格、`Bonk` 线统一「邦克」。
- **日本麻将/柏青哥/将棋线统一**：`Mahjong Gakuen` → 麻将学园、`Kyuukyoku Mahjong` → 究极麻将、`Pachio-kun` → 柏青哥君、`Morita Shougi` → 森田将棋。
- **体育年货按品牌**：`Power League` 5 条、`Pro Yakyuu World Stadium` 2 条、`F1 Circus` 3 条、`TV Sports` 3 条。
- **series 5 条**：炸弹人'93 特别版、炸弹人 玩家对战、大流士 Alpha / Plus、索尼克扣杀 世界锦标赛沙滩排球。

### SMS（Master System）全量中文化（559 / 559，100%）

SMS 的 238 个唯一空名里有一批**巴西/韩国独占版本**（葡版 `Sapo Xule`、`Turma da Monica`，韩版 `Agigongnyong Dooly`、`Hwarang-ui Geom`），统一在中文名后加括号标注版本。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_sms.csv` 559 行：exact 317 / series 4 / none 238（空名唯一 238 个，series 唯一 4 条） |
| 译名文件 | `sms_cn_part1.txt`（238 条）+ `sms_series_cn.txt` 4 条 |
| 校验 | `build_key_cn.py sms 238`：series 4 == 4、假名 0、含拉丁字母 7 条抽查 |
| 并入词库 | `apply_key_cn.py sms 238 4`：候选 242 条，新增 239、跳过 3；词库 34 160 → 34 399 行 |
| 重建 | `zh_localize.py` 全量 → **exact 559 / series 0 / none 0** |

**SMS（Master System） 译名要点**

- **合卡按内容直译**：`20 em 1` → 20合1、`4 PAK All Action` → 4合1 全能行动、`Astro Warrior _ Pit Pot` → 星际战士与皮特波特。
- **世嘉自家品牌**：`Alex Kidd` → 阿历克斯小子、`Wonder Boy` → 神奇男孩、`Phantasy Zone` → 幻想地带、`Golden Axe Warrior` → 战斧勇士、`Hang On` → 悬挂赛车。
- **地区版本标括号**：`Sapo Xule` 3 条、`Turma da Monica` 2 条标（葡版）；`Agigongnyong Dooly`、`Hwarang-ui Geom`、`Samgukji III` 等标（韩版）；`Ys US Master System FM sound patch` 标「美版FM音源补丁」。
- **series 4 条**：索尼克1 改良版、索尼克 爆破、索尼克 教育软件、VR战士 动画版。

### MCD（Mega-CD / Sega CD）全量中文化（609 / 609，100%）

Mega-CD 的 203 个唯一空名以**FMV 实拍游戏与日本独占 CD 作**为主，同一作品常见两种拼写（`Anett / Annet / Annett Futatabi`），译名合并成一套。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_segacd.csv` 609 行：exact 399 / series 7 / none 203（空名唯一 203 个，series 唯一 7 条） |
| 译名文件 | `segacd_cn_part1.txt`（203 条）+ `segacd_series_cn.txt` 7 条 |
| 校验 | `build_key_cn.py segacd 203`：series 7 == 7、假名 0、重复中文名 17 个（拼写变体合并，正常） |
| 并入词库 | `apply_key_cn.py segacd 203 7`：候选 210 条，新增 198、跳过 12；词库 34 399 → 34 597 行 |
| 重建 | `zh_localize.py` 全量 → **exact 609 / series 0 / none 0** |

**MCD（Mega-CD / Sega CD） 译名要点**

- **FMV 实拍作按原名直译**：`Ground Zero Texas` → 零点 德克萨斯、`Night Trap` → 夜间陷阱、`Sewer Shark` → 下水道鲨鱼、`Time Gal` → 时光少女、`Road Avenger` → 公路复仇者。
- **拼写变体合并**：`Anett / Annet / Annett Futatabi` 三条统一「安妮特 再临」；`Bakuden / Baku-Den` 统一「爆传 失衡地带」；`Blackhole / Black Hole Assault` 统一「黑洞强袭」。
- **世嘉经典合集按合卡数**：`Sega Classics Arcade Collection 4-in-1 / 5-in-1` 保留合卡个数。
- **series 7 条**：蚯蚓吉姆 特别版、海豚艾柯 CD、FIFA国际足球 锦标赛版、快打旋风 CD、露娜 永恒之蓝、光明力量 CD、索尼克 CD。

### GG（Game Gear）全量中文化（1 056 / 1 056，100%）

Game Gear 的 202 个唯一空名里**汉化版/修正版占了不少**（`[t +1 Mystic]`、`[b2]`、`[tr fr]`、`[tr ru]` 这类标记），处理方式是中文名 + 括号标注汉化组或修订号。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_gg.csv` 1 056 行：exact 875 / series 21 / none 202（空名唯一 202 个，series 唯一 21 条） |
| 译名文件 | `gg_cn_part1.txt`（202 条）+ `gg_series_cn.txt` 21 条 |
| 校验 | `build_key_cn.py gg 202`：series 21 == 21、假名 0、含拉丁字母 23 条抽查 |
| 并入词库 | `apply_key_cn.py gg 202 21`：候选 223 条，新增 185、跳过 38；词库 34 597 → 34 782 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 056 / series 0 / none 0** |

**GG（Game Gear） 译名要点**

- **标记翻译规则**：`[t +1 Mystic]` → （Mystic汉化版）、`[tr fr]` → （法语汉化版）、`[tr ru]` → （俄语汉化版）、`[tr pt ERTrans]` → （葡语汉化版）、`[b2]` → （修正版）、`[o]` → （修正）、`[h]` → 保留原意。
- **世嘉自家品牌**：`GG Aleste` → GG阿雷斯特、`GG Shinobi` → GG忍者、`Sonic` 线 → 索尼克、`Tails` 线 → 塔尔斯、`Puyo` 线 → 魔法气泡。
- **动画改编**：`Crayon Shin-chan` → 蜡笔小新、`Sailor Moon` → 美少女战士 水手月亮、`Doraemon` 2 条、`Slam Dunk` → 灌篮高手、`Yu Yu Hakusho` 3 条。
- **series 21 条**：光明力量外传 4 条、索尼克 6 条、梦幻之星 2 条、VR战士 Mini / 动画版、铁甲飞龙 Mini。

### WiiU（Wii U）全量中文化（454 / 454，100%）

Wii U 的 109 个唯一空名以**任天堂自家作 + 乐高/迪士尼授权作**为主，series 里 43 条多是「数字版/豪华版/合集」这类后缀需要中文化。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_wiiu.csv` 454 行：exact 302 / series 43 / none 109（空名唯一 109 个，series 唯一 43 条） |
| 译名文件 | `wiiu_cn_part1.txt`（109 条）+ `wiiu_series_cn.txt` 43 条 |
| 校验 | `build_key_cn.py wiiu 109`：series 43 == 43、假名 0、含拉丁字母 22 条抽查 |
| 并入词库 | `apply_key_cn.py wiiu 109 43`：候选 152 条，新增 152（0 跳过）；词库 34 782 → 34 934 行 |
| 重建 | `zh_localize.py` 全量 → **exact 454 / series 0 / none 0** |

**WiiU（Wii U） 译名要点**

- **任天堂自家品牌**：`New Super Mario Bros. U` → 新超级马力欧兄弟U、`Paper Mario - Color Splash` → 纸片马力欧 色彩飞溅、`Zelda no Densetsu` 3 条（荒野之息 / 风之律动 HD / 黄昏公主 HD）、`Zero - Nuregarasu no Miko` → 零 濡鸦之巫女。
- **授权 IP 按中国叫法**：`Disney Infinity` → 迪士尼无限、`Skylanders` → 天空之城、`LEGO` → 乐高、`Marvel Avengers` → 漫威复仇者、`Adventure Time` → 探险活宝。
- **日式合集后缀中文化**：`Musou Orochi 2 Hyper` → 无双大蛇2 终极版、`Warriors Orochi 3 Hyper` → 无双大蛇3 终极版、`Famicom Remix 1 + 2` → 红白机重制 1+2、`NES Remix Pack` → NES重制合集。
- **series 43 条重点**：勇者斗恶龙10 五个版本线、怪物猎人 Frontier G 8 条高级包、马力欧与索尼克 奥运 4 条、光明系列（`Monster Hunter` 之外全部按官方中文）。

### WS（WonderSwan）全量中文化（299 / 299，100%）

WonderSwan 的 122 个唯一空名以**日本独占 + 万代授权改编**为主，大量 `Rev 1/2/3` 是同一 ROM 的修订版，中文名保留修订号。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ws.csv` 299 行：exact 174 / series 3 / none 122（空名唯一 122 个，series 唯一 3 条） |
| 译名文件 | `ws_cn_part1.txt`（122 条）+ `ws_series_cn.txt` 3 条 |
| 校验 | `build_key_cn.py ws 122`：series 3 == 3、假名 0、含拉丁字母 44 条抽查 |
| 并入词库 | `apply_key_cn.py ws 122 3`：候选 125 条，新增 124、跳过 1；词库 34 934 → 35 058 行 |
| 重建 | `zh_localize.py` 全量 → **exact 299 / series 0 / none 0** |

**WS（WonderSwan） 译名要点**

- **万代改编线**：`Digimon` → 数码宝贝、`Gundam` → 高达、`One Piece` → 海贼王、`Hunter X Hunter` → 全职猎人、`Naruto` → 火影忍者、`Medarot` → 徽章机器人。
- **修订版保留编号**：`Rev 1/2/3` 一律「修订1/2/3」跟在中文名后，不删不改。
- **麻将/将棋/花札线统一**：`Mahjong Touryuumon` → 麻将登龙门、`Shougi Touryuumon` → 将棋登龙门、`Hanafuda Shiyouyo` → 来玩花札吧。
- **series 3 条**：洛克人与佛鲁迪 来自未来的挑战者（2 种写法合并）、铁拳 卡牌挑战。

### NEOGEO（Neo Geo AES/MVS）全量中文化（257 / 257，100%）

Neo Geo 的 118 个唯一空名几乎全是 **SNK 自家街机作的双名并列写法**（`英文 _ 日文`），译名要按作品正式中文名走，不把两种写法都翻一遍。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_neogeo.csv` 257 行：exact 139 / series 26 / none 118（空名唯一 118 个，series 唯一 26 条） |
| 译名文件 | `neogeo_cn_part1.txt`（118 条）+ `neogeo_series_cn.txt` 26 条 |
| 校验 | `build_key_cn.py neogeo 118`：series 26 == 26、假名 0、含拉丁字母 9 条抽查 |
| 并入词库 | `apply_key_cn.py neogeo 118 26`：候选 144 条，新增 141、跳过 3；词库 35 058 → 35 199 行 |
| 重建 | `zh_localize.py` 全量 → **exact 257 / series 0 / none 0** |

**NEOGEO（Neo Geo AES/MVS） 译名要点**

- **双名并列只译正式名**：`Art of Fighting _ Ryuuko no Ken` → 龙虎之拳、`Fatal Fury _ Garou Densetsu` → 饿狼传说、`Samurai Shodown _ Samurai Spirits` → 侍魂。
- **SNK 品牌线统一**：`King of Fighters` → 拳皇、`Metal Slug` → 合金弹头、`Real Bout Fatal Fury` → 饿狼传说 真实对决、`Sengoku` → 战国传承、`Super Sidekicks` → 超级侧踢（+ 得点王）。
- **盗版/加强版标注**：`[Bootleg]` → （盗版）、`Plus / Super Plus` → 加强版 / 超级加强版，`Crouching Tiger Hidden Dragon 2003` → 卧虎藏龙2003。
- **series 26 条重点**：饿狼传说 4 条、侍魂 6 条（1–5 + 特别版）、拳皇 13 条（'97–2004 各加强版）、合金弹头 4/5 加强版。

### WSC（WonderSwan Color）全量中文化（239 / 239，100%）

WonderSwan Color 的 101 个唯一空名依旧以**万代改编 + SNK 移植 + 日本独占**为主，同一作品常有拼写变体（`Eiyuu Den / Eiyuuden`、`Koujo / Oujo`）。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_wsc.csv` 239 行：exact 136 / series 2 / none 101（空名唯一 101 个，series 唯一 2 条） |
| 译名文件 | `wsc_cn_part1.txt`（101 条）+ `wsc_series_cn.txt` 2 条 |
| 校验 | `build_key_cn.py wsc 101`：series 2 == 2、假名 0、重复中文名 9 个（拼写变体合并，正常） |
| 并入词库 | `apply_key_cn.py wsc 101 2`：候选 103 条，新增 102、跳过 1；词库 35 199 → 35 301 行 |
| 重建 | `zh_localize.py` 全量 → **exact 239 / series 0 / none 0** |

**WSC（WonderSwan Color） 译名要点**

- **拼写变体合并**：`Kinnikuman II-Sei / IIsei` 4 条统一「筋肉人二世」、`SD Gundam Eiyuu Den / Eiyuuden` 4 条统一「SD高达英雄传」、`Meitantei Conan - Yuugure no Koujo / Oujo` 统一「黄昏的公主」。
- **动画改编线**：`One Piece` 7 条（乔巴的大冒险 / 天鹅斗技场 / 虹之岛 / 宝藏战争 1–2）、`Inuyasha` 3 条、`Hunter X Hunter` 3 条、`Shaman King` 3 条、`Digimon` 6 条。
- **版本号原样保留**：`v1.0` / `v1.1` / `v1.5` / `v1.6` / `v.rsc21` 不翻译。
- **series 2 条**：洛克人EXE N1战斗、洛克人EXE WS。

### 32X（Sega 32X）全量中文化（209 / 209，100%）

32X 只有 33 个唯一空名，但**一半是开发用示例程序与检测程序**（`Mars Sample Program`、`32X Sample Program`），译名保留程序名并加中文说明。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_32x.csv` 209 行：exact 176 / series 0 / none 33（空名唯一 33 个，无 series） |
| 译名文件 | `32x_cn_part1.txt`（33 条）+ 空的 `32x_series_cn.txt` |
| 校验 | `build_key_cn.py 32x 33`：series 0 == 0、假名 0 |
| 并入词库 | `apply_key_cn.py 32x 33 0`：候选 33 条，新增 32、跳过 1；词库 35 385 → 35 417 行 |
| 重建 | `zh_localize.py` 全量 → **exact 209 / series 0 / none 0** |

**32X（Sega 32X） 译名要点**

- **开发程序按功能直译**：`Mars Sample Program - Gnu Sierra` → 火星示例程序 角马山脉、`Mars Sample Program - Runlength Mode Test` → 火星示例程序 游程编码模式测试、`Mars Check Program Version 1.0` → 火星检测程序 1.0版。
- **世嘉自家作**：`After Burner Complete` → 火力压制 完全版、`Virtua Racing Deluxe` → 虚拟赛车 豪华版、`Soulstar X` → 灵魂之星 X、`Knuckles' Chaotix` → 纳克鲁斯 混乱队。

### NGPC（Neo Geo Pocket Color）全量中文化（118 / 118，100%）

NGPC 的 76 个唯一空名以**SNK 自家作 + 柏青嫂/赌场模拟 + 日本独占育成**为主，`Real Casino Series` 8 条是同一套赌场线。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ngpc.csv` 118 行：exact 42 / series 9 / none 76（空名唯一 76 个，series 唯一 9 条） |
| 译名文件 | `ngpc_cn_part1.txt`（76 条）+ `ngpc_series_cn.txt` 9 条 |
| 校验 | `build_key_cn.py ngpc 76`：series 9 == 9、假名 0、含拉丁字母 26 条抽查 |
| 并入词库 | `apply_key_cn.py ngpc 76 9`：候选 84 条，新增 84（0 跳过）；词库 35 301 → 35 385 行 |
| 重建 | `zh_localize.py` 全量 → **exact 118 / series 0 / none 0** |

**NGPC（Neo Geo Pocket Color） 译名要点**

- **赌场线统一格式**：`Neo 21 / Neo Baccarat / Neo Cherry Master Color / Neo Dragon's Wild / `Neo Mystery Bonus` 全部「NEO + 玩法 + 真实赌场系列」。
- **柏青嫂王国 8 条**：`Pachi-Slot Aruze Oukoku Pocket - Azteca / Dekahel 2 / Delsol 2 / e-Cup / Hanabi / Oohanabi / Porcano 2 / Ward of Lights` 统一「柏青嫂 阿鲁泽王国 口袋版 + 机种名」。
- **SNK 卡牌线**：`SNK vs. Capcom - Card Fighters` 6 条（Clash 两版 / Gekitotsu 三版 / 2 扩展版）+ `The Match of the Millennium` → 千年之战。
- **series 9 条**：拳皇 R-2 两版、饿狼传说 F-Contact、合金弹头 1st/2nd Mission、洛克人 战斗斗士、侍魂！2、索尼克 口袋冒险。

### PS3（PlayStation 3）全量中文化（67 / 67，100%）

PS3 只有 37 个唯一空名，但**全是知名大作**（黑暗之魂、暴雨、神秘海域、如龙、尼尔），必须用官方中文名而不是直译。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ps3.csv` 67 行：exact 30 / series 17 / none 37（空名唯一 37 个，series 唯一 17 条） |
| 译名文件 | `ps3_cn_part1.txt`（37 条）+ `ps3_series_cn.txt` 17 条 |
| 校验 | `build_key_cn.py ps3 37`：series 17 == 17、假名 0 |
| 并入词库 | `apply_key_cn.py ps3 37 17`：候选 54 条，新增 52、跳过 2；词库 35 417 → 35 469 行 |
| 重建 | `zh_localize.py` 全量 → **exact 67 / series 0 / none 0** |

**PS3（PlayStation 3） 译名要点**

- **一律用官方中文名**：`Dark Souls` → 黑暗之魂、`Demon's Souls` → 恶魔之魂、`Heavy Rain` → 暴雨、`Beyond Good & Evil` 之外的 `Remember Me` → 记住我、`NIER` → 尼尔、`Vanquish` → 征服。
- **日式 RPG 用既有品牌译法**：`Atelier` 线 → 炼金工房、`Disgaea D2` → 魔界战记D2、`Tales of` 线 → 圣恩传说 f / 无限传说2、`Valkyria Chronicles` → 战场女武神。
- **格斗线**：`Super Street Fighter IV Arcade Edition` → 超级街头霸王4 街机版、`Ultra Street Fighter IV` → 终极街头霸王4、`Yaiba - Ninja Gaiden Z` → 刃 忍者龙剑传Z。
- **series 17 条**：生化危机 2 条、恶魔城 暗影之王、死或生5、最终幻想13-2、侠盗猎车手5、王国之心 HD 两版、合金装备5 原爆点、忍者龙剑传 2 条、女神异闻录4 竞技场 2 条、寂静岭 暴雨、传说 2 条、铁拳 混合版。

### PSV（PlayStation Vita）全量中文化（9 / 9，100%）

PS Vita 只剩 4 个唯一空名，一轮就清完。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_psvita.csv` 9 行：exact 2 / series 3 / none 4（空名唯一 4 个，series 唯一 3 条） |
| 译名文件 | `psvita_cn_part1.txt`（4 条）+ `psvita_series_cn.txt` 3 条 |
| 校验并入库 | `build_key_cn.py psvita 4` + `apply_key_cn.py psvita 4 3`：候选 7 条全部新增；词库 35 469 → 35 476 行 |
| 重建 | `zh_localize.py` 全量 → **exact 9 / series 0 / none 0** |

**PSV（PlayStation Vita） 译名要点**

- **官方中文名**：`Child of Light` → 光之子、`Gravity Rush` → 重力异想世界、`Totori no Atelier Plus` → 托托莉的炼金工房 Plus 亚兰德炼金术士2、`Zettai Zetsubou Shoujo - Dangan-Ronpa` → 绝对绝望少女 弹丸论破 另一章。
- **series 3 条**：死或生5 Plus、寂静岭 记忆之书、街头霸王X铁拳。

### PS3DL（PS3 数字下载版）全量中文化（1 / 1，100%）

PS3 数字下载版只剩 1 条，顺手清掉。

| 步骤 | 结果 |
|---|---|
| 起点 | `mapping_ps3dl.csv` 1 行：exact 0 / none 1 |
| 译名文件 | `ps3dl_cn_part1.txt`（1 条）+ 空的 `ps3dl_series_cn.txt` |
| 校验并入库 | `build_key_cn.py ps3dl 1` + `apply_key_cn.py ps3dl 1 0`：新增 1；词库 35 476 → 35 477 行 |
| 重建 | `zh_localize.py` 全量 → **exact 1 / series 0 / none 0** |

**PS3DL（PS3 数字下载版） 译名要点**

- `Far Cry 3` → 孤岛惊魂3（与 Xbox/PCE 等平台的同一作品共用词条）。


---

## 六、已知限制

- 中文名带英文字母是常态（FIFA、NBA、WWE、CLANNAD、Fate/Extra、DJMAX、.hack//Link
   这类品牌缩写按惯例保留原文），不算未翻译。
- 覆盖率 100.0% 与「唯一英文名有中文 96.1%」是两个口径：前者按**记录条数**算（31 个平台 77 661 条），
   后者按 `index/` 里 `game_name` 的**原始写法去重**再和词库折叠后的 `search_key` 比，
   同一作品的多区域 / 多语言写法在词库侧已合并成一条，所以后者会略低，并不代表有漏译。
- 冷门日系、韩版、巴西葡版标题**不是官方中文名，是按作品原名直译**，可读、可检索，
   但不要当作发行商官方译名引用；有官方中文名的作品（任天堂、世嘉、SNK 主力作等）一律用官方名。

---

## 七、平台清单

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

## 八、更新日志

- **2026-11**：新增「中文多译」`alias_cn` —— 54 组同义词源，4 200 个词条、12 672 个别名，
  8 533 条映射带多译；`gen_alias.py` 生成、`terms/术语多译表.csv` 维护词源；
  映射表新增 `alias_cn` 字段（31 个平台全量重建，exact 77 661 / 100.0% 不变）。
- **2026-11**：剩余 20 个平台一次性全部中文化（gb / gbc / ngc / dc / pcecd / n64 / xbox / pce / sms / segacd / gg / wiiu / ws / neogeo / wsc / 32x / ngpc / ps3 / psvita / ps3dl），
  逐平台「导出空名 → 分批写译名 → 校验 → 并库」，候选 5 525 条、新增 5 166 条；
  词库 30 111 → 35 477 行；全量重建后 exact 69 214 → **77 661（100.0%）**，none 7 683 → **0**，
  中文覆盖 90.1% → **100.0%**，唯一英文名有中文比例 82.6% → 96.1%；**31 个平台全部 100%**。
- **2026-11**：SS（Sega Saturn）全量中文化（2 294 / 2 294，100%），29 个 series 半成品整行替换；
  候选 764 条全部新增；词库 29 347 → 30 111 行；全量重建后 exact 67 921 → 69 214（89.1%），
  中文覆盖 88.5% → 90.1%，唯一英文名有中文比例 80.6% → 82.6%；十一个平台 100%。
- **2026-11**：MD 全量中文化（2 352 / 2 352，100%），46 个 series 半成品整行替换；候选 861 条新增 738 条
  （123 条跨平台同名已存在而跳过）；词库 28 609 → 29 347 行。
- **2026-11**：SFC（snes）全量中文化（3 689 / 3 689，100%），58 个 series 半成品整行替换；
  词库 26 847 → 28 609 行；全量重建后 exact 63 615 → 67 921（87.5%），中文覆盖 83.2% → 88.5%，
  唯一英文名有中文比例 74.1% → 80.6%；十个平台 100%。
  新增通用脚本 `build_key_cn.py` / `apply_key_cn.py`，替代此后每平台各写一份的做法。
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

封面版权归各游戏厂商所有，本项目仅提供索引、URL 与中文名映射，供个人模拟器与 ROM 管理使用，如有侵权请立即联系我删除！
All cover art copyrights belong to their respective publishers. This project provides only index data, URLs, and name mappings, intended for personal emulator and ROM-management use. If you believe any content infringes your rights, please contact me and it will be removed promptly.

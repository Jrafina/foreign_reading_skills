---
name: economist-intensive-reading
description: 把《经济学人》(The Economist) 等英文外刊文章加工成一份可直接打印的中文精读讲义 PDF。当用户提供外刊 PDF（含扫描版/图片版 PDF）、文章链接或纯文本，并要求"精读""精析""考研词汇""长难句分析""逐段翻译""整理成学习资料/PDF"时使用。产出：一段式英汉对照全文 + 考研核心词汇表（例句取自考研真题）+ 长难句结构拆解 + 亮点表达/复习自测，最终导出一份竖版 A4 PDF。
description_zh: "外刊精读讲义生成：Vocab + 长难句 + 逐段翻译 → A4 PDF"
description_en: "Turn Economist articles into printable bilingual study PDFs"
agent_created: true
---

# 外刊精读讲义生成（Economist Intensive Reading）

把一篇英文外刊文章，加工成一份可直接打印的 A4 精读讲义（**只交付 PDF**）。

> 面向用户的说明文档见同目录 `README.md`。本文件是给智能体执行用的工作流。

## 设计原则：内容与版式分离（省 token）

**核心：不要把 HTML 逐字写出来。**

渲染 PDF 需要一份 HTML，但这份 HTML 由 `assets/render_pdf.py` **从内容源文件自动生成**，
是系统临时目录里的一次性中间产物，用完即删 —— 不占对话 token，也不作为交付物。

因此每次做讲义，你只需要写一份**内容源文件**（`.md`），格式是纯文本 + 少量定界符，
不写 `<div class="...">`、不写 CSS、不写表格标签。相比手写 HTML，正文 markup 开销基本为零。

版式（颜色、字体、间距、分页）全部集中在 `assets/lecture.css`。想调样式改那一个文件，
**不必重写内容**；内容源文件留在 `src/` 里，随时可重新渲染。

## 何时使用

用户给出外刊文章（PDF / 扫描图片 / 网页链接 / 粘贴文本），并希望：

- "精读 / 精析这篇文章"
- "提取考研词汇 / 高频词汇"
- "分析长难句 / 句子结构"
- "逐段翻译 / 中英对照"
- "整理成学习资料 / 做成 PDF"

## 产出结构（默认 7 节）

| # | 章节 | 源文件块 |
|---|---|---|
| 01 | 报头 | frontmatter（kicker / title / deck / meta） |
| 02 | 文章速览 | `::: facts` + `::: callout` |
| 03 | 全文精读 | `::: para`（EN + ZH） |
| 04 | 图表解读 | `::: callout`（info 变体） |
| 05 | 考研核心词汇 | `::: vocab` |
| 06 | 长难句精析 | `::: sent` |
| 07 | 亮点表达 + 复习自测 | `::: phrases` + `::: quiz` |

### 按需裁剪节数

用户常要求精简，例如"只保留全文精读、考研核心词汇、长难句精析"。**直接从源文件里删掉对应块即可**：
- 保留报头（文档需要标题），它本来就是一行 frontmatter；
- 章节编号 `01/02/03` 由渲染器按 `# ` 标题**自动重排**，不用手改；
- `::: para` 的段落序号也是**自动编号**的，删段后不用重排；
- 裁完重跑第 3、4 步确认没有孤页或大片空白。

## ★ 为词汇表配考研真题例句（本技能的核心增值点）

例证优先级：**考研真题原句 > 按考研语域自写例句**。千万不要从内容农场/自媒体抄"真题例句"——那些大量是编造的（年份和 Text 号都是假的）。可靠做法是**自己从真题原文建本地语料库再检索**。

**① 建库**（`assets/build_kaoyan_corpus.py`）
仓库：`Fantasia1999/kaoyanzhenti`（GitHub，英语一 1998–2026、英语二 2010–2026 逐年独立 PDF，可直接定位年份）。
```bash
PY="C:/Users/Jrafina/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
"$PY" assets/build_kaoyan_corpus.py      # 下载到 corpus/pdf，抽文本到 corpus/text/<年>_<卷>.txt
```
- 从 `raw.githubusercontent.com` 拉取**极易被重置连接**（`RemoteDisconnected` / `SSLEOFError`）；**失败的直接重跑**，已有 txt 会自动跳过。
- 语料库默认建在**当前工作目录**下的 `corpus/`；从别处调用时用环境变量指定：建库 `KAOYAN_CORPUS`、检索 `KAOYAN_CORPUS_TXT`。目录不存在时脚本会直接报错提示，不会静默空转。
- 这些 PDF 是 **OCR 扫描版**，有明显错字（`unanimous`→`unammous`、`California`→`Califoria`）。**引用前必须人工校订**，含错字的句子不用。

**② 检索**（`assets/search_kaoyan_corpus.py`）
```bash
"$PY" assets/search_kaoyan_corpus.py > hits.txt     # 默认跑脚本内置的目标词表
"$PY" assets/search_kaoyan_corpus.py wary withhold  # 也可指定词（须在内置 TARGETS 里）
"$PY" assets/search_kaoyan_corpus.py @words.txt     # ★ 换文章时用这个
```
`@words.txt` 是**推荐用法**：文件每行一条，支持 `#` 注释，支持两种写法
- `production` —— 用内置 TARGETS 里已写好的屈折形式；
- `quadruple=quadruple,quadrupled,quadrupling` —— **现场指定词形**（新文章的词基本都不在内置表里，必须这样写）。

不要为了检索新文章去改脚本里的 TARGETS 字典、也不要另存一份临时脚本 —— 用 `@文件` 即可。
行格式：`目标词=形式1,形式2,...`；只写一个形式时也得写 `word=word`。

- 因 OCR 噪声，**必须模糊匹配**（脚本用编辑距离 ≤1），纯 `grep` 会漏掉大量词。
- 命中里混着"答案选项"行（含 `[A] [B]`），脚本已把这类排在后面；**优先选阅读/翻译正文句**，选项行只在别无选择时用并加省略号。
- 脚本默认只打印长度 ≤300 字符的句子、每词最多 6 条，足够挑；命中后仍需人工判断。
- 一词多义要挑**与本文用法一致**的那句：例如 `strain` 本文是名词"压力"，就别选真题里作动词"消耗"的句子。

**③ 标注与诚实原则**
- 真题句：`vocab` 行的第 5 个字段写年份卷别（如 `2025 英语一`）→ 渲染成红色徽标。**年份必须来自语料库文件名，不要凭记忆写。**
- 真题里确实没有该用法的词（`pony up`、`aisle`、`earmark`、`calibrate` 这类外刊口语/生僻词）：第 5 字段写 `own` → 渲染成蓝色"考研例句"徽标。实测约 32/45 能拿到真题原句。
- 目标词在例句里用 `<em>` 包起来（已设为红色加粗）。

## 工作流

### 第 0 步：确认意图
有歧义时（要几节？词汇几条？要不要同源真题映射？）先问清楚再动手。

### 第 1 步：取出文章全文

```bash
PY="C:/Users/Jrafina/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
"$PY" assets/extract.py text   "路径/文章.pdf"            # 先看有无文本层
"$PY" assets/extract.py render "路径/文章.pdf" "路径/_t"   # 无文本层时渲染图片
```
> 路径坑：Windows 版 Python **不认** Git Bash 的 `/tmp/xxx`，必须传 `C:/...` 形式。

- **有文本层** → 直接读文本。
- **无文本层（扫描版 / Print-to-PDF 图片版，`get_text()` 返回 0 字符）** → 必须**渲染成高分辨率 PNG 后自己"看图"转录**：
  整页 3x，再按杂志双栏切分、zoom=5 放大，用 Read 工具逐张看、手工转录。
  **不要跳过转录**——后续所有分析都依赖它。

首次准备隔离环境（只需一次）：
```bash
"C:/Users/Jrafina/.workbuddy/binaries/python/versions/3.13.12/python.exe" -m venv "C:/Users/Jrafina/.workbuddy/binaries/python/envs/default"
"C:/Users/Jrafina/.workbuddy/binaries/python/envs/default/Scripts/pip.exe" install pymupdf
```

### 第 2 步：写讲义源文件 `.md`

写到 `<项目>/src/<文章名>.md`。**只写内容，不写 HTML。**

```markdown
---
kicker: The Economist · United States · 5 September 2026
title: Moral maths
deck: America's support system for disabled pupils is broken
meta: 版次|2026-09-05 · Page 21
meta: 字数|约 800 词
meta: 难度|★★★★☆（考研阅读同源）
footer: 版权与来源说明
---

# 全文精读 · 英汉对照
hint: 章节提示文字，可含 <mark> 高亮

::: para
EN: 英文原文，关键词用 <mark> 包住
ZH: 参考译文
:::

# 考研核心词汇（45 词）
::: vocab
单词 | 音标 | 词性 | 释义 | 出处徽标 | 例句（目标词用 <em>）
:::

# 长难句精析（12 句）
::: sent
ID: S1
SRC: 原句，考查成分用 <u> 下划线
MAIN: 主干说明
A: t-cl | 从句类型 | 说明，可用 **加粗**
TRANS: 译文
:::
```

**全部块类型速查**

| 块 | 行语法 | 渲染结果 |
|---|---|---|
| `::: para` | `EN:` / `ZH:` | 段落序号自动递增；EN 高亮 + ZH 译文 |
| `::: vocab` | `词 \| 音标 \| 词性 \| 释义 \| 徽标 \| 例句` | 四列词汇表；徽标 `own` → 蓝色"考研例句" |
| `::: sent` | `ID:` / `SRC:` / `MAIN:` / `A: tag\|标签\|说明` / `TRANS:` | 长难句卡片，`tag` 取 `t-main/t-cl/t-mod/t-obj` |
| `::: facts` | `标签 \| 数值` | 事实卡网格 |
| `::: callout` | `TITLE:` / `P:` / 以 `-` 开头的列表项 | 提示块；`TITLE: !...` 或加 `INFO` 行 → 蓝色变体 |
| `::: phrases` | `英文 :: 中文` | 双列亮点表达 |
| `::: quiz` | `题干 \| 答案` | 自动编号；答案红色高亮 |
| `::: pagebreak` | — | 强制分页（**慎用**，会导致大片空白） |

**内容红线**
- 值里可以**直接写原始 HTML**（`<mark>` `<u>` `<em>` `<b>` `<span class="badge">`），渲染器不转义。
- 原文的**小标题**（如 `Don't overdo it`）必须写成 `<span class="subhead">Don't overdo it</span>` —— 它被定义为 `display:block`，会独立成行。直接写纯文本会和后文粘成 `Don't overdo itGeopolitics have also...`。EN 与 ZH 两行都要包。
- 值里**不要出现 `|`**（会被当成字段分隔符）。
- 音标用标准 IPA；词性用 `v./n./adj./adv./v.phr.`。
- 页脚 `footer:` **只写来源与版权声明**（如"原文版权归 The Economist 所有，仅个人学习使用"）；**不要出现工具署名**（"由 WorkBuddy/某模型自动生成"之类一律不写）。
- 长难句必须标出**主干**与**从句/非谓语类型**（`only to do`、`so...that`、非限制性定语从句、同位语、分词伴随状语等）。
- 图表重绘必须声明"示意图，非精确数值"，不得编造坐标数值。
- 人名/机构名译文里的间隔号用 `&middot;`（如 `戈尔扬&middot;尼科利克`）；专名首次出现时括注原文。

### 第 3 步：渲染 PDF（一条命令）

```bash
"$PY" assets/render_pdf.py src/<文章名>.md output/<输出名>.pdf
```
- 脚本自己负责：生成临时 HTML → Edge headless 打印 → 输出 PDF → **删除临时 HTML**。
- 加 `--preview` 会顺便导出逐页 PNG；加 `--keep-html` 才保留中间 HTML（**默认不要加**）。

### 第 4 步：自检（必做）

```bash
"$PY" assets/render_pdf.py src/<文章名>.md output/<输出名>.pdf --preview
```
逐页 Read 预览图，检查：
- **孤页**（最后一页只有页脚）或大片空白 → 收紧 `lecture.css` 里 `@media print` 的 margin/padding；
- 表格列宽、徽标换行、标注文字是否重叠；
- 改完重跑第 3 步；**版式问题只改 `lecture.css`，不要动源文件**；
- 完成后删除 `*.pv*.png`。

**先量后改**——先跑这一条，再决定要不要调版式，比人眼看快得多：
```bash
"$PY" -c "import pymupdf;d=pymupdf.open(r'output/xxx.pdf');[print(i+1,round(100*max(b[3] for b in p.get_text('blocks') if b[4].strip())/p.rect.height)) for i,p in enumerate(d)]"
```
输出为每页"最后一行落在页高的百分之几"。判读：
- 末页 < 40% ⇒ 孤页，前面某页的 `break-inside:avoid` 卡片被整块挤下去了；
- 中间页 < 80% ⇒ 有整块内容被推到下一页，属正常分页，不必强压；
- 想消掉孤页，**依次**调 `@media print` 里的 `.sent{margin-bottom/padding}` → `.sent .src{margin}` → `.analysis{line-height}` → `.para{margin-bottom}`，每次减 1–2px 后重跑，通常几十 pt 就够（A4 一页正文区约 768pt，页脚还要占约 20pt）。

### 第 5 步：交付

`present_files` **只给 PDF**，不要给 HTML、也不要给源文件（除非用户明确要）。

## 常见坑

| 现象 | 原因 / 解法 |
|---|---|
| PDF 只有 1 页、内容是 `ERR_INVALID_URL` | 传给 Edge 的 `file://` URL 里混进了 Windows 反斜杠（被编码成 `%5C`）。脚本已用 `.replace("\\", "/")` 处理 |
| `Failed to write file ... 拒绝访问 (0x5)` | `--print-to-pdf` 的**目标文件名必须是纯 ASCII**。脚本先输出到临时 ASCII 文件再 `os.replace` 成最终名 |
| 找不到 Edge | 脚本按 `Program Files (x86)` → `Program Files` → PATH 顺序探测 |
| Edge 输出 `QQBrowser` / `fallback_task_provider` 报错 | 噪声，忽略 |
| 下载真题 `RemoteDisconnected` | `raw.githubusercontent.com` 不稳定，直接重跑脚本 |
| 某词检索不到真题 | 放宽拼写变体，或确认它是否真是考研大纲词；没有就把第 5 字段写成 `own` |
| 检索时全部输出"跳过" | 内置 `TARGETS` 只覆盖以往文章的词。换文章请用 `@words.txt` 或 `word=form1,form2` 现场指定词形，别去改脚本 |
| 小标题与后文粘成一句（`Don't overdo itGeopolitics...`） | 原文小标题没包 `<span class="subhead">…</span>`。`.subhead` 已定义为 `display:block`，包上即独立成行，EN/ZH 都要包 |
| 末页只剩一张卡片、大片空白 | 加小标题等多占一行后常见的临界溢出。按第 4 步的量化法逐步收紧 `@media print` 里的 `.sent`/`.para` 间距 |
| 译文里的人名间隔号丢失 | 用 `&middot;`，不要直接敲 `·`（部分字体回退会吃掉） |

## 质量基准

**精简版 3 节（7 页，用户常用）**：`01 全文精读 · 英汉对照`（9 段，高亮与词汇取词点一一对应）+ `02 考研核心词汇`（45 词，例句为真题原句带年份徽标）+ `03 长难句精析`（12 句）。
实测：`grey_gold`（10 段 + 48 词 + 12 句）= 7 页；`class_treason`（9 段 + 50 词 + 12 句）= 9 页。词汇 45 条≈7 页，50 条≈8 页。

**满配版 7 节（约 9 页）**：再加 文章速览 / 图表解读 / 亮点表达 / 复习自测。

## 常见追问的扩展方向

- 追加**同源真题映射**（本文话题与哪年考研阅读相近）——本地语料库已可直接支持
- 追加 **Cloze / 翻译练习** 或 **雅思/托福替换词**
- 把讲义转成 **Anki 词表 CSV**
- 批量处理整期杂志：遍历每篇文章，输出多份讲义 + 合并索引
- 扩充真题语料库卷种，提高真题例句命中率

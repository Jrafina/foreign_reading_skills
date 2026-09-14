# 外刊精读讲义生成 · economist-intensive-reading

把一篇《经济学人》等英文外刊文章，自动加工成一份**可直接打印的中文精读讲义**（A4 PDF）。
词汇例句会去**考研真题原文**里找，而不是随手编造。

> 示例产物：`output/Economist_精读_Moral_maths.pdf`（7 页）
> 源文：The Economist, 2026-09-05, United States, Page 21, *Moral maths*

---

## 目录

- [这是什么](#这是什么)
- [快速开始](#快速开始)
- [产出结构](#产出结构)
- [内容与版式分离（省 token）](#内容与版式分离省-token)
- [可以在指令里附加的要求](#可以在指令里附加的要求)
- [目录结构](#目录结构)
- [环境依赖](#环境依赖)
- [Linux 部署（Ubuntu 22.04 / Debian 12）](#linux-部署ubuntu-2204--debian-12)
- [考研真题语料库](#考研真题语料库)
- [自定义与维护](#自定义与维护)
- [排错速查](#排错速查)
- [已知限制](#已知限制)

---

## 这是什么

一个**用户级工作流技能**，安装位置为 `~/.workbuddy/skills/economist-intensive-reading/`：

```bash
git clone git@github.com:Jrafina/foreign_reading_skills.git \
  ~/.workbuddy/skills/economist-intensive-reading
```

因为放在 `~/.workbuddy/skills/` 下，它在**任何工作目录**都可用，不限于某个项目。
仓库结构（`SKILL.md` + `assets/`）遵循通用 Skill 约定，同类技能可直接复用。

**触发方式：自动。** 不需要手动调用 —— 只要你提供一篇英文外刊文章并表达"精读"类意图，它就会被匹配并接手。

工作流程：

```
外刊 PDF / 网页链接 / 纯文本
        ↓
转录全文 → 查真题例句 → 写内容源 .md → 导出 A4 PDF → 逐页预览自检 → 交付
                       （只写纯文本内容，不写 HTML/CSS）
        ↓
              A4 PDF（唯一交付物）
```

---

## 快速开始

### 直接说人话就行

- 「把这篇《经济学人》精读一下，整理成 PDF」
- 「提取这篇文章的考研词汇和长难句」
- 「逐段翻译 + 标注高频词，做成学习资料」
- 直接把 PDF 拖进来，什么都不说也可以

### 也可以点名调用

- `/economist-intensive-reading`
- 「用外刊精读技能处理这个文件」

### 三种输入形式

| 形式 | 说明 |
|---|---|
| **外刊 PDF** | 含**扫描版 / 图片版**（无文本层）也能处理 —— 会自动渲染成高分辨率图后转录 |
| **网页链接** | 直接给文章 URL |
| **粘贴文本** | 直接把正文贴进对话 |

---

## 产出结构

**交付物只有 PDF。** 生成时智能体只写一份**纯文本内容源** `.md`（不含任何 HTML 标签或 CSS），
版式（颜色、字体、分页）由渲染脚本自动套用。`.html` 只作为渲染引擎的临时输入存在，用完即删，
既不会出现在 `output/` 里，也不会占用对话 token。（详见 [内容与版式分离](#内容与版式分离省-token)）

### 满配版（7 节，约 9 页）

| # | 章节 | 内容 |
|---|---|---|
| 01 | 报头 | 栏目 / 版次 / 字数 / 难度 + 标题 + 副标题 |
| 02 | 文章速览 | 事实卡 + 一句话主旨 + 背景知识（专有名词、制度、习语） |
| 03 | 全文精读 | 逐段「英文原文（关键词高亮）+ 参考译文」 |
| 04 | 图表解读 | 原文有图时：要点 + 按趋势重绘的示意图 |
| 05 | 考研核心词汇 | 40–50 条，四列：`单词/音标 · 词性 · 中文释义 · 例句` |
| 06 | 长难句精析 | 10–12 句：原句（成分下划线）→ 结构拆解 → 译文 |
| 07 | 亮点表达 + 复习自测 | 写作句型、可套用模板句、自测题 |

### 精简版（3 节，约 7 页）

只保留 **全文精读 · 英汉对照** / **考研核心词汇** / **长难句精析**。
裁剪时只要在内容源 `.md` 里删掉对应块即可，章节编号和段落序号会自动重排，不用手改。

---

## 内容与版式分离（省 token）

这是本技能最新的一处设计，专门为了**降低生成成本**。

渲染 PDF 必须要有一份 HTML（Edge 无头打印的硬性要求），但这份 HTML **不由智能体逐字写出**：

```
智能体写的内容源  src/<文章名>.md      ← 纯文本：段落、词汇行、长难句字段
        │
        ├── assets/lecture.css         版式：颜色 / 字体 / 间距 / A4 分页
        │
        ▼
assets/render_pdf.py  ──自动拼装──▶  临时 HTML（系统 temp 目录，用完即删）
        │
        ▼
              output/<输出名>.pdf       ← 唯一交付物
```

**好处：**

| 对比项 | 旧做法（智能体写 HTML） | 现做法（智能体写 .md） |
|---|---|---|
| 智能体输出 | 每段都带 `<div class="para"><p class="en">…` | 只写 `EN: …` / `ZH: …` |
| 改版式 | 要在正文里翻找并改标签 | 只改 `lecture.css` 一个文件 |
| 可复用性 | 内容与样式缠在一起 | 内容源留在 `src/`，随时重渲染 |

也就是说，**调样式不必重写内容，重渲染也不必再花 token 让智能体重写一遍正文**。

---

## 可以在指令里附加的要求

| 你想要的 | 就这么说 |
|---|---|
| 砍章节 | 「只保留全文精读、考研词汇、长难句」 |
| 加词汇量 | 「词汇扩到 60 条」 |
| 指定例句来源 | 「例句用考研真题原句」（默认就会查本地真题库） |
| **保留内容源** | 内容源 `.md` **默认就留在 `src/`**，日后想重渲染或改版式可直接用 |
| 转 Anki | 「再导出一份 Anki 词表 CSV」 |
| 卖点/售卖文案 | 「假设要卖这份讲义，写一份商品展示文案」→ 产出到 `<项目>/marketing/`，含主标题、6 个卖点、规格表、短文案多版与发布前合规自查 |
| 批量 | 「把这一期杂志的 8 篇文章都做成讲义」 |
| 改版式 | 「例句列再宽一点」「正文字号加大」 |

---

## 目录结构

```
economist-intensive-reading/
├── SKILL.md                      技能主体：触发条件 + 工作流 + 质量红线
├── README.md                     本文件（给人看的）
├── .gitattributes                强制脚本用 LF（否则 .sh 到 Linux 会 bad interpreter）
├── corpus/                       真题语料库，**随仓库分发**（pdf/ 原始 PDF + text/ 检索文本）
└── assets/
    ├── lecture.css               讲义全部版式（颜色 / 字体 / 间距 / A4 分页）
    ├── render_pdf.py             .md 内容源 → 自动拼 HTML → A4 PDF（用完即删 HTML）
    ├── extract.py                PDF 取文本 / 渲染扫描件（text | render）
    ├── setup_linux.sh            Ubuntu 22.04 / Debian 12 一键装依赖
    ├── build_kaoyan_corpus.py    下载考研真题 PDF 并抽文本，重建语料库（可选，仓库已自带）
    └── search_kaoyan_corpus.py   在语料库里模糊检索真题原句
```

运行时会在**当前项目目录**下产生：

```
<项目>/
├── src/               内容源（<文章名>.md），**保留**，方便日后重渲染
├── corpus/            真题语料库（若没有，脚本会自动回退用技能自带的 corpus/）
└── output/            成品，**只有 PDF**
```

> **HTML 去哪了？** 智能体只写 `src/` 里的纯文本内容源；`render_pdf.py` 读它、拼上 `lecture.css`
> 生成一份 HTML 放到系统 temp 目录，交给 Chromium 系浏览器打印成 PDF 后立即删除。因此项目和输出目录里
> 都不会出现 `.html`，中间产物也不参与对话 token 计费。

---

## 环境依赖

> 下表中的路径是开发机上 WorkBuddy 内置环境的实际位置，**换机器请替换成自己的解释器路径**；
> 脚本本身只用标准库 + `pymupdf`，不依赖任何 WorkBuddy 专有组件。

| 依赖 | 说明 |
|---|---|
| **Python** | 3.10+，建议独立 venv（开发机放在 WorkBuddy 的隔离环境里） |
| **pymupdf** | `pip install pymupdf`，用于读 PDF / 渲染扫描件 / 生成预览图 |
| **Chromium 系浏览器** | Edge / Chrome / Chromium **任意一个**即可（headless 打印参数完全一致）。探测顺序：`LECTURE_BROWSER` 环境变量 → Windows 常见路径 → macOS 常见路径 → Linux 常见路径 → `PATH` 里的命令名 → Playwright 缓存目录 |
| **中文字体** | Windows / macOS 用系统自带；**Linux 必须装 `fonts-noto-cjk`**，否则讲义中文渲染成方框 |

Windows 首次准备（只需一次）：

```bash
"C:/Users/Jrafina/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
  -m venv "C:/Users/Jrafina/.workbuddy/binaries/python/envs/default"

"C:/Users/Jrafina/.workbuddy/binaries/python/envs/default/Scripts/pip.exe" install pymupdf
```

### Linux 部署（Ubuntu 22.04 / Debian 12）

一键脚本，幂等可重复跑：

```bash
bash assets/setup_linux.sh
```

它做四件事：补齐 `python3-pip` → 装 `fonts-noto-cjk` → 装一个 Chromium 系浏览器 → 装 `pymupdf`，
最后自检并打印实际用到的浏览器路径。

手工装也很简单：

```bash
# Debian 12
sudo apt update && sudo apt install -y chromium fonts-noto-cjk
pip install pymupdf

# Ubuntu 22.04 —— 注意：它的 chromium-browser 是 snap 包，容器 / 无 snapd 的环境装不上，
# 所以推荐用 Playwright 自带的 Chromium（不依赖发行版打包，路径固定可预测）
sudo apt update && sudo apt install -y fonts-noto-cjk
pip install pymupdf playwright && playwright install --with-deps chromium
```

Linux 上只有两个真会踩的坑，脚本都已经处理：

1. **中文字体**：不装 `fonts-noto-cjk`，讲义中文会渲染成方框（tofu）。
   CSS 已按 `Noto Sans CJK SC → Noto Sans SC → Source Han Sans SC → WenQuanYi Micro Hei` 顺序回退。
2. **沙箱与共享内存**：以 root 运行时（Docker / CI）Chromium 会拒绝启动，脚本检测到 `euid=0`
   会自动加 `--no-sandbox`；同时固定加 `--disable-dev-shm-usage`，规避容器里 `/dev/shm` 过小导致的崩溃。

另外脚本会先试 `--headless=new`，失败再回退老语法 `--headless`，所以老版 Chromium 也能用。
也可以直接指定浏览器，绕过全部探测：

```bash
export LECTURE_BROWSER=/usr/bin/chromium      # 或 /opt/google/chrome/chrome
```

---

## 考研真题语料库

这是本技能**最核心的增值点**：词汇表的例句优先取自考研真题原文，而不是自编。

### 为什么必须用真题原文

网上的「考研真题例句」（自媒体、内容农场）**大量是编造的** —— 连年份和 Text 号都是假的。
例如会看到给 `conversely` 伪造一条"2024 英二完形"的句子。**不可引用二手转载。**

### 数据来源与自带语料

来自 GitHub 仓库 `Fantasia1999/kaoyanzhenti`：英语一 1998 – 2026、英语二 2010 – 2026，
**逐年独立 PDF**，所以年份能精确定位。

**本仓库已内嵌其中 34 份**（英语一 2010–2026 + 英语二 2010–2026，约 51MB PDF + 0.9MB 文本），
clone 下来直接就能检索，**不需要先建库**。想补 1998–2009 的英语一或更新年份，跑一次建库脚本即可。

### 用法

```bash
PY=python3        # 换成你自己的 python

# ① 检索：默认跑脚本内置的目标词表（只覆盖历史文章用过的词）
"$PY" assets/search_kaoyan_corpus.py > hits.txt

# ② ★ 换新文章时用这个：把该文的目标词与屈折形式写进 words.txt，每行一条
#    production
#    quadruple=quadruple,quadrupled,quadrupling
"$PY" assets/search_kaoyan_corpus.py @words.txt

#    也可直接在命令行指定
"$PY" assets/search_kaoyan_corpus.py wary=wary,wariness withhold

# ③ 补齐 / 更新语料库（已存在的会自动跳过）
"$PY" assets/build_kaoyan_corpus.py
```

语料库查找顺序：环境变量 `KAOYAN_CORPUS_TXT`（检索）/ `KAOYAN_CORPUS`（建库）
→ 当前工作目录下的 `corpus/` → 技能自带的 `corpus/`。

### 实测效果

45 个外刊词汇中，**约 32 个能在真题里找到原句**，其余（多为 `pony up`、`aisle`、`earmark` 这类外刊口语词）按考研语域自写，并用不同颜色徽标区分。

### 三条使用纪律

1. **必须人工校订**：这些 PDF 是 OCR 扫描版，有错字（`unanimous` → `unammous`、`California` → `Califoria`）。含错字的句子不要引用。
2. **必须模糊匹配**：脚本用编辑距离 ≤1，纯 `grep` 会漏掉近一半。
3. **一词多义要选对**：选与本文用法一致的那句。例如 `strain` 本文是名词"压力"，就别选真题里作动词"消耗"的句子。

---

## 自定义与维护

| 想改什么 | 改哪里 |
|---|---|
| 触发词、工作流、质量红线 | `SKILL.md` |
| 版式、颜色、字体、间距 | `assets/lecture.css`（改完重跑渲染即生效，**不用动内容源**） |
| 内容源 `.md` 的块语法 | `assets/render_pdf.py` 的 `parse()` / `render_body()` |
| 默认词汇条数 / 章节构成 | `SKILL.md` 的「产出结构」 |
| 例句检索的目标词表 | 新文章用 `words.txt` + `@words.txt` 传参（见上）；脚本顶部 `TARGETS` 只是历史文章用过的词形缓存 |
| 扩语料库卷种 | `assets/build_kaoyan_corpus.py` 里的 `REPO` / `list_targets()` |

**改完技能后**，下次生成讲义即生效，无需重启。

---

## 排错速查

| 现象 | 原因 / 解法 |
|---|---|
| `Failed to write file ... 拒绝访问 (0x5)` | Edge 的 `--print-to-pdf` **目标文件名必须是纯 ASCII**。用 `assets/render_pdf.py` 自动规避：它先渲染成 `_tmp_render.pdf` 再重命名 |
| `output/` 里出现了 `.html` | 违反交付规则。智能体不应写 HTML；`.html` 只在系统 temp 目录短暂存在，渲染后由脚本删除 |
| 想调试中间 HTML | 加 `--keep-html` 会保留到 `output/`（默认不加）；确认 PDF 无误后自行删掉即可 |
| 路径报错找不到文件 | Windows 版 Python **不认** Git Bash 的 `/tmp/...`，一律传 `C:/...` |
| Edge 输出一堆 `QQBrowser` / `fallback_task_provider` 报错 | 噪声，忽略。只 `grep 'written\|fail'` 看结果 |
| PDF 里多出日期和 URL 页脚 | 命令漏了 `--no-pdf-header-footer`（`render_pdf.py` 已内置，一般不会遇到） |
| 讲义出现大片空白 / 只剩页脚的孤页 | 分页滥用 `page-break-before`（源文件里的 `::: pagebreak`）。改用 `break-inside:avoid` + 调 `lecture.css` 的 `@media print` margin |
| 下载真题 `RemoteDisconnected` / `SSLEOFError` | `raw.githubusercontent.com` 连接不稳定。**直接重跑脚本**，已有文件会自动跳过 |
| 某词检索不到真题 | 换更宽松的拼写变体，或确认该词真的是考研大纲词。实在没有就自写例句并标注 |
| 表格/文字在 PDF 里被截断 | 检查对应元素是否有 `break-inside:avoid` |
| **Linux**：`bad interpreter: /bin/bash^M` | `.sh` 被以 CRLF 检出。仓库有 `.gitattributes` 强制 LF；老工作区执行 `git rm --cached -r . && git reset --hard` 重新检出即可 |
| **Linux**：找不到浏览器 | 跑 `bash assets/setup_linux.sh`；或 `export LECTURE_BROWSER=/usr/bin/chromium` 直接指定 |
| **Linux**：讲义中文变成方框 | 缺 CJK 字体：`sudo apt install fonts-noto-cjk` |
| **Linux**：Chromium 在 Docker 里一启动就退出 | 脚本已按 `euid=0` 自动加 `--no-sandbox`，并固定加 `--disable-dev-shm-usage`。若仍失败，检查容器 `/dev/shm` 是否过小 |
| 老版 Chromium 不认 `--headless=new` | 脚本会自动回退到 `--headless`，无需干预 |

---

## 已知限制

- **扫描版 PDF 靠"看图"转录**，长文可能有零星笔误，交付前建议扫一眼原文。
- **图表重绘是示意图**，只还原趋势，不还原精确数值（讲义里会明确标注"示意，非精确数值"）。
- **考研例句覆盖率约 7 成**，剩下的词真题里确实没有该用法。
- 真题语料库**随仓库分发**（34 份，英语一/二 2010–2026，约 51MB），clone 后在任意目录都能检索；
  未收录 1998–2009 的英语一，需要时跑 `assets/build_kaoyan_corpus.py` 补齐。
- **不产出 HTML 交付物**。智能体只写 `src/` 里的 `.md` 内容源（默认保留）；`.html` 是脚本的临时中间产物，渲染后即删。想调版式只改 `lecture.css` 重渲染，无需重写内容、也不再花 token。

---

## 版权

- 外刊原文版权归原作者 / The Economist 所有。
- 考研真题版权归教育部考试中心所有。
- `corpus/` 里的真题语料仅作本地检索索引随技能分发，请勿另行传播或用于商业用途。
- 本技能生成的讲义**仅供个人英语学习使用**，请勿用于商业传播。

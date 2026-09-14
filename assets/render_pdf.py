#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""讲义源文件(.md) -> A4 PDF 渲染器。

用法:
    python render_pdf.py <讲义.md> <输出.pdf> [--preview] [--keep-html]

设计要点:
  * 版式由同目录 lecture.css 提供；中间 HTML 只是渲染引擎的输入，
    由脚本临时生成并自动删除，不占用对话 token，也不作为交付物。

讲义源文件语法（详见 SKILL.md）:
    ---
    kicker: The Economist · United States · 5 September 2026
    title: Moral maths
    deck: America's support system for disabled pupils is broken
    meta: 版次|2026-09-05 · Page 21
    meta: 字数|约 800 词
    footer: 版权与来源说明
    ---

    # 章节标题
    hint: 章节提示文字

    ::: para
    EN: 正文（可含 <mark> 高亮）
    ZH: 参考译文
    :::

    ::: vocab
    单词 | 音标 | 词性 | 释义 | 出处徽标 | 例句（可含 <em>）
    :::

    ::: sent
    ID: S1
    SRC: 原句（可含 <u> 下划线）
    MAIN: 主干说明
    A: t-cl | 从句类型 | 说明文字
    TRANS: 译文
    :::

    ::: facts      标签 | 数值
    ::: callout    TITLE: / P: / - 列表项
    ::: phrases    英文 :: 中文
    ::: quiz       题干 | 答案（答案会加高亮）
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(HERE, "lecture.css")

# 显式指定浏览器可执行文件（任何平台都优先用它）
BROWSER_ENV = "LECTURE_BROWSER"

# 各平台浏览器的常见安装位置。Chromium 系（Chrome / Edge / Chromium）
# 的 headless 打印参数完全一致，所以哪个存在就用哪个。
BROWSER_PATHS = [
    # Windows
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # Linux
    "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
    "/usr/bin/microsoft-edge", "/usr/bin/microsoft-edge-stable",
    "/snap/bin/chromium", "/opt/google/chrome/chrome",
]

# PATH 里可以直接找到的命令名
BROWSER_CMDS = [
    "msedge", "microsoft-edge", "microsoft-edge-stable",
    "google-chrome", "google-chrome-stable", "chrome",
    "chromium", "chromium-browser",
]

LINUX_HINT = """\
找不到 Chrome / Chromium / Edge，无法导出 PDF。按系统任选一种装法：

  Debian 12
    sudo apt update && sudo apt install -y chromium fonts-noto-cjk
    # 若 apt 源里没有 chromium，改用 Playwright 自带版（见下）

  Ubuntu 22.04
    sudo apt update && sudo apt install -y fonts-noto-cjk
    pip install playwright && playwright install --with-deps chromium
    # 注：Ubuntu 的 chromium-browser 是 snap 包，在容器/无 snapd 的环境里装不上，
    #     所以推荐走 Playwright（不依赖发行版打包，路径固定可预测）

  Debian 12 / Ubuntu 22.04 通用（不依赖系统包）
    pip install playwright && playwright install --with-deps chromium

中文字体是必需的：不装 fonts-noto-cjk，讲义里的中文会渲染成方框（tofu）。
也可以直接指定浏览器：export {}=/path/to/chrome""".format(BROWSER_ENV)


def _playwright_browsers():
    """Playwright 下载的 Chromium —— Linux 上最省事、版本最可控的来源。"""
    roots = [
        os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "",
        os.path.expanduser("~/.cache/ms-playwright"),
        "/ms-playwright",
    ]
    patterns = [
        "chromium-*/chrome-linux/chrome",
        "chromium_headless_shell-*/chrome-linux/headless_shell",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    ]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for pat in patterns:
            # 版本号大的通常更新，优先用
            for hit in sorted(glob.glob(os.path.join(root, pat)), reverse=True):
                if os.path.exists(hit):
                    yield hit


def find_browser():
    env = os.environ.get(BROWSER_ENV)
    if env:
        if os.path.exists(env):
            return env
        raise SystemExit("环境变量 {} 指向的文件不存在：{}".format(BROWSER_ENV, env))
    for p in BROWSER_PATHS:
        if os.path.exists(p):
            return p
    for c in BROWSER_CMDS:
        found = shutil.which(c)
        if found:
            return found
    for p in _playwright_browsers():
        return p
    raise SystemExit(LINUX_HINT)


def headless_variants(browser):
    """返回可依次尝试的参数组。

    Chromium 112+ 用 `--headless=new`，更老的版本只认 `--headless`；
    Playwright 的 headless_shell 本身就是无头程序，不需要该参数。
    """
    if "headless_shell" in os.path.basename(browser):
        return [[]]
    return [["--headless=new"], ["--headless"]]


def run_browser(browser, url, tmp_pdf):
    """调用浏览器把 HTML 打成 PDF，返回最后一次尝试的进程对象。"""
    flags = [
        "--disable-gpu",
        "--no-pdf-header-footer",      # Chrome 111+ 不打印页眉页脚
        "--print-to-pdf-no-header",    # 老版本的同义参数，新版会忽略
        "--disable-dev-shm-usage",     # 容器里 /dev/shm 往往很小，避免崩
        "--print-to-pdf=" + tmp_pdf,
    ]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        flags.insert(0, "--no-sandbox")   # Linux 上以 root 运行必须加
    proc = None
    for extra in headless_variants(browser):
        if os.path.exists(tmp_pdf):
            os.remove(tmp_pdf)
        cmd = [browser] + extra + flags + [url]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if os.path.exists(tmp_pdf) and os.path.getsize(tmp_pdf) > 0:
            return proc
    return proc


def bold(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def badge_html(v):
    v = (v or "").strip()
    if not v:
        return ""
    if v.lower() in ("own", "自写", "考研例句"):
        return '<span class="badge own">考研例句</span>'
    return '<span class="badge">{}</span>'.format(v)


def parse(text):
    """解析讲义源文件 -> (front, blocks)"""
    lines = text.splitlines()
    front, body_start = {}, 0

    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            raw = lines[i]
            if ":" in raw:
                k, v = raw.split(":", 1)
                k, v = k.strip(), v.strip()
                front.setdefault(k, [])
                front[k].append(v)
            i += 1
        body_start = i + 1

    blocks = []
    cur_type, cur_lines, pending_title = None, [], None

    def flush():
        nonlocal cur_type, cur_lines
        if cur_type:
            blocks.append((cur_type, cur_lines))
        cur_type, cur_lines = None, []

    for raw in lines[body_start:]:
        s = raw.strip()
        if s.startswith(":::"):
            token = s[3:].strip()
            if cur_type is None:
                cur_type = token or "para"
                cur_lines = []
            else:
                flush()
            continue
        if cur_type is None:
            if s.startswith("# "):
                flush()
                blocks.append(("h2", [s[2:].strip()]))
                continue
            if s.lower().startswith("hint:"):
                blocks.append(("hint", [s[5:].strip()]))
                continue
            if not s:
                continue
            blocks.append(("p", [s]))
        else:
            if s:
                cur_lines.append(s)
    flush()
    return front, blocks


def render_body(blocks):
    out, sec_no, sent_no, para_no = [], 0, 0, 0
    for kind, items in blocks:
        if kind == "h2":
            sec_no += 1
            para_no = 0
            out.append('<h2 class="sec"><span class="no">{:02d}</span>{}</h2>'.format(sec_no, items[0]))
        elif kind == "hint":
            out.append('<p class="hint">{}</p>'.format(items[0]))
        elif kind == "p":
            out.append("<p>{}</p>".format(bold(items[0])))
        elif kind == "para":
            para_no += 1
            en = zh = ""
            for it in items:
                if it.startswith("EN:"):
                    en = it[3:].strip()
                elif it.startswith("ZH:"):
                    zh = it[3:].strip()
            out.append(
                '<div class="para"><div class="en"><span class="num">{}</span>{}</div>'
                '<div class="zh"><b>译</b>　{}</div></div>'.format(para_no, en, zh)
            )
        elif kind == "vocab":
            rows = []
            for it in items:
                c = [x.strip() for x in it.split("|")]
                c += [""] * (6 - len(c))
                rows.append(
                    "<tr><td><span class=\"w\">{}</span><span class=\"ipa\">{}</span></td>"
                    "<td class=\"pos\">{}</td><td>{}</td>"
                    "<td>{}{}</td></tr>".format(c[0], c[1], c[2], bold(c[3]), badge_html(c[4]), c[5])
                )
            out.append(
                "<table><thead><tr>"
                '<th style="width:19%">单词 / 音标</th><th style="width:7%">词性</th>'
                '<th style="width:23%">中文释义</th><th style="width:51%">例句</th>'
                "</tr></thead><tbody>{}</tbody></table>".format("".join(rows))
            )
        elif kind == "sent":
            sent_no += 1
            sid, src, main, trans, ana = "", "", "", "", []
            for it in items:
                if it.startswith("ID:"):
                    sid = it[3:].strip()
                elif it.startswith("SRC:"):
                    src = it[4:].strip()
                elif it.startswith("MAIN:"):
                    main = it[5:].strip()
                elif it.startswith("TRANS:"):
                    trans = it[6:].strip()
                elif it.startswith("A:"):
                    c = [x.strip() for x in it[2:].split("|")]
                    c += [""] * (3 - len(c))
                    ana.append('<li><span class="tag {}">{}</span>{}</li>'.format(c[0], c[1], bold(c[2])))
            if not sid:
                sid = "S{}".format(sent_no)
            out.append(
                '<div class="sent"><span class="idx">{}</span>'
                '<div class="src">{}</div>'
                '<div class="analysis"><span class="tag t-main">主干</span>{}<ul>{}</ul></div>'
                '<div class="trans"><b>译文</b>　{}</div></div>'.format(
                    sid, src, bold(main), "".join(ana), trans
                )
            )
        elif kind == "facts":
            cells = []
            for it in items:
                c = [x.strip() for x in it.split("|")]
                c += [""] * (2 - len(c))
                cells.append('<div class="fact"><div class="k">{}</div><div class="v">{}</div></div>'.format(c[0], c[1]))
            out.append('<div class="grid">{}</div>'.format("".join(cells)))
        elif kind == "callout":
            title, para, bullets, info = "", "", [], False
            for it in items:
                if it.startswith("TITLE:"):
                    title = it[6:].strip()
                    if title.startswith("!"):
                        info, title = True, title[1:].strip()
                elif it.startswith("P:"):
                    para = it[2:].strip()
                elif it.startswith("INFO"):
                    info = True
                elif it.startswith("-"):
                    bullets.append(it[1:].strip())
                else:
                    bullets.append(it)
            cls = "callout info" if info else "callout"
            inner = "<h4>{}</h4>".format(title) if title else ""
            if para:
                inner += "<p>{}</p>".format(bold(para))
            if bullets:
                inner += "<ul>{}</ul>".format("".join("<li>{}</li>".format(bold(b)) for b in bullets))
            out.append('<div class="{}">{}</div>'.format(cls, inner))
        elif kind == "phrases":
            cells = []
            for it in items:
                if "::" not in it:
                    continue
                a, b = it.split("::", 1)
                cells.append('<div class="it"><div class="en2">{}</div><div class="cn2">{}</div></div>'.format(a.strip(), b.strip()))
            out.append('<div class="phr">{}</div>'.format("".join(cells)))
        elif kind == "quiz":
            rows = []
            for it in items:
                c = [x.strip() for x in it.split("|")]
                c += [""] * (2 - len(c))
                rows.append('<div class="q">{} <span>{}</span></div>'.format(bold(c[0]), c[1]))
            out.append('<div class="quiz">{}</div>'.format("".join(rows)))
        elif kind == "pagebreak":
            out.append('<div class="page-break"></div>')
    return "".join(out)


def build_html(front, body_html):
    css = open(CSS_PATH, encoding="utf-8").read()
    title = front.get("title", [""])[0]
    kicker = front.get("kicker", [""])[0]
    deck = front.get("deck", [""])[0]
    metas = "".join(
        "<span><b>{}</b> {}</span>".format(*m.split("|", 1)) if "|" in m else "<span>{}</span>".format(m)
        for m in front.get("meta", [])
    )
    footer = front.get("footer", [""])[0]
    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        "<title>{}</title><style>{}</style></head><body><div class=\"page\">"
        '<div class="masthead"><div class="kicker">{}</div><h1>{}</h1>{}'
        '<div class="meta">{}</div></div>{}'
        "<footer>{}</footer></div></body></html>"
    ).format(
        title, css, kicker, title,
        '<div class="deck">{}</div>'.format(deck) if deck else "",
        metas, body_html,
        footer,
    )


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) < 2:
        raise SystemExit(__doc__)
    src, dest = args[0], os.path.abspath(args[1])
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)

    with open(src, encoding="utf-8") as f:
        front, blocks = parse(f.read())

    tmpdir = tempfile.mkdtemp(prefix="lecture_")
    tmp_html = os.path.join(tmpdir, "lecture.html")
    tmp_pdf = os.path.join(tmpdir, "lecture.pdf")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(build_html(front, render_body(blocks)))

    browser = find_browser()
    # Windows 路径必须先转成正斜杠，否则反斜杠会被编码成 %5C 导致 ERR_INVALID_URL
    url = "file:///" + urllib.parse.quote(tmp_html.replace("\\", "/"), safe="/:")
    proc = run_browser(browser, url, tmp_pdf)
    if not os.path.exists(tmp_pdf) or os.path.getsize(tmp_pdf) == 0:
        sys.stderr.write("浏览器: {}\n".format(browser))
        sys.stderr.write((proc.stdout[-2000:] if proc else "") + (proc.stderr[-2000:] if proc else ""))
        raise SystemExit("PDF 生成失败")

    os.replace(tmp_pdf, dest)
    size = os.path.getsize(dest)
    print("PDF 已生成: {} ({:.0f} KB)".format(dest, size / 1024))

    if "--keep-html" in flags:
        kept = os.path.splitext(dest)[0] + ".html"
        shutil.copy(tmp_html, kept)
        print("已保留中间 HTML:", kept)

    if "--preview" in flags:
        try:
            import pymupdf
            d = pymupdf.open(dest)
            base = os.path.splitext(dest)[0]
            for i, p in enumerate(d):
                p.get_pixmap(matrix=pymupdf.Matrix(1.35, 1.35)).save("{}.pv{}.png".format(base, i))
            print("预览图: {} 张 → {}*.pvN.png".format(d.page_count, os.path.basename(base)))
        except ImportError:
            print("未安装 pymupdf，跳过预览")

    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()

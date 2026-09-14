#!/usr/bin/env python
"""从 GitHub 真题仓库下载考研英语真题 PDF，抽取纯文本，建立本地语料库。

输出:
  corpus/pdf/            原始 PDF
  corpus/text/<year>_<vol>.txt   逐年纯文本
"""
import json
import os
import re
import urllib.parse
import urllib.request

import pymupdf

REPO = "Fantasia1999/kaoyanzhenti"
BASE = "https://raw.githubusercontent.com/{}/HEAD/".format(REPO)
# 语料库根目录：优先读环境变量 KAOYAN_CORPUS，否则用当前工作目录下的 corpus/
ROOT = os.environ.get("KAOYAN_CORPUS") or os.path.join(os.getcwd(), "corpus")
PDF_DIR = os.path.join(ROOT, "pdf")
TXT_DIR = os.path.join(ROOT, "text")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def list_targets():
    tree = fetch_json("https://api.github.com/repos/{}/git/trees/HEAD?recursive=1".format(REPO))
    targets = []
    for x in tree["tree"]:
        if x["type"] != "blob":
            continue
        p = x["path"]
        if not p.endswith(".pdf") or "/英语" not in p:
            continue
        m = re.search(r"(\d{4})年考研英语([一二])真题", p)
        if not m:
            continue
        year, vol = int(m.group(1)), (1 if m.group(2) == "一" else 2)
        # 只看正文年期卷（排除合集）
        targets.append((year, vol, p))
    # 去重（同一年同卷可能有多份）
    seen, out = set(), []
    for y, v, p in sorted(targets):
        if (y, v) in seen:
            continue
        seen.add((y, v))
        out.append((y, v, p))
    return out


def download(src_path, dest):
    url = BASE + urllib.parse.quote(src_path)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        f.write(r.read())


def clean(text):
    text = text.replace("\u00ad", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def main():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(TXT_DIR, exist_ok=True)
    targets = list_targets()
    print("targets:", len(targets), flush=True)
    for year, vol, path in targets:
        tag = "{}_{}".format(year, vol)
        pdf_path = os.path.join(PDF_DIR, tag + ".pdf")
        txt_path = os.path.join(TXT_DIR, tag + ".txt")
        if os.path.exists(txt_path):
            print("skip", tag, flush=True)
            continue
        try:
            if not os.path.exists(pdf_path):
                download(path, pdf_path)
            doc = pymupdf.open(pdf_path)
            txt = clean("\n".join(pg.get_text() for pg in doc))
            doc.close()
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt)
            print("ok", tag, "chars", len(txt), flush=True)
        except Exception as e:
            print("FAIL", tag, repr(e)[:160], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()

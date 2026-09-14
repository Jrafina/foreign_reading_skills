#!/usr/bin/env python
"""模糊检索真题原句（容忍 OCR 错字）。

用法: python search_fuzzy.py [word1 word2 ...]
"""
import os
import re
import sys

TXT_DIR = os.environ.get("KAOYAN_CORPUS_TXT") or os.path.join(os.getcwd(), "corpus", "text")

# 目标词 -> 需匹配的屈折形式（小写）
TARGETS = {
    "implore": ["implore", "implored", "implores", "imploring"],
    "legislature": ["legislature", "legislatures", "legislative", "legislator", "legislators"],
    "enact": ["enact", "enacts", "enacted", "enacting", "enactment"],
    "provisional": ["provisional", "provisionally"],
    "unanimous": ["unanimous", "unanimously"],
    "paralysis": ["paralysis", "paralysed", "paralyzed", "paralysing"],
    "dilemma": ["dilemma", "dilemmas"],
    "eye-watering": ["eye", "watering"],
    "enrolment": ["enrolment", "enrollment", "enrol", "enroll", "enrolled", "enrolling"],
    "fraught": ["fraught"],
    "pare back": ["pare", "pared", "paring", "pares"],
    "remedy": ["remedy", "remedies", "remedied", "remedying", "remedial"],
    "guarantee": ["guarantee", "guarantees", "guaranteed", "guaranteeing"],
    "eligible": ["eligible", "eligibility", "ineligible"],
    "specify": ["specify", "specifies", "specified", "specifying", "specification"],
    "aide": ["aide", "aides"],
    "placement": ["placement", "placements"],
    "envisage": ["envisage", "envisaged", "envisages", "envisaging", "envision"],
    "shoulder": ["shoulder", "shoulders", "shouldered", "shouldering"],
    "authorise": ["authorise", "authorised", "authorises", "authorize", "authorized", "authorizes"],
    "amount to": ["amount", "amounts", "amounted", "amounting"],
    "think-tank": ["tank"],
    "foot the bill": ["foot", "footed", "footing"],
    "provoke": ["provoke", "provokes", "provoked", "provoking", "provocative"],
    "revenue": ["revenue", "revenues"],
    "balanced-budget": ["balanced", "budget", "budgets"],
    "strain": ["strain", "strains", "strained", "straining"],
    "swell": ["swell", "swells", "swelled", "swollen", "swelling"],
    "designate": ["designate", "designated", "designates", "designating", "designation"],
    "concerted": ["concerted"],
    "plug": ["plug", "plugs", "plugged", "plugging"],
    "earmark": ["earmark", "earmarks", "earmarked", "earmarking"],
    "mandate": ["mandate", "mandates", "mandated", "mandating"],
    "arbitrarily": ["arbitrary", "arbitrarily", "arbitrariness"],
    "litigation": ["litigation", "litigate", "litigants", "litigious"],
    "overhaul": ["overhaul", "overhauls", "overhauled", "overhauling"],
    "calibrate": ["calibrate", "calibrated", "calibration", "calibrating"],
    "severity": ["severity", "severe", "severely", "severities"],
    "shortfall": ["shortfall", "shortfalls"],
    "aisle": ["aisle", "aisles"],
    "pony up": ["pony", "ponied"],
    "oblige": ["oblige", "obliged", "obliges", "obliging", "obligation", "obligations"],
    "dismantle": ["dismantle", "dismantled", "dismantles", "dismantling"],
    "withhold": ["withhold", "withholds", "withholding", "withheld"],
    "wary": ["wary", "wariness", "warily"],
}


def lev(a, b, cap=2):
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
        if min(prev) > cap:
            return cap + 1
    return prev[-1]


def load():
    if not os.path.isdir(TXT_DIR):
        raise SystemExit(
            "找不到真题语料库目录: {}\n"
            "请先运行 assets/build_kaoyan_corpus.py 建库，"
            "或设环境变量 KAOYAN_CORPUS_TXT 指向 corpus/text。".format(TXT_DIR)
        )
    docs = []
    for fn in sorted(os.listdir(TXT_DIR)):
        if not fn.endswith(".txt"):
            continue
        tag = fn[:-4]
        raw = open(os.path.join(TXT_DIR, fn), encoding="utf-8").read()
        flat = re.sub(r"\s+", " ", raw)
        sents = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"(])", flat)
        docs.append((tag, sents))
    return docs


def noise(s):
    return ("[A]" in s) or ("ANSWER" in s.upper()) or ("[B]" in s) or ("[C]" in s) or ("[D]" in s)


def parse_spec(a):
    """把一条参数解析成 (目标词, [屈折形式...])。

    支持两种写法：
      word                -> 用脚本内置 TARGETS 里的词形
      word=form1,form2    -> 现场指定词形（换文章时不必改脚本）
    """
    if "=" in a:
        w, forms = a.split("=", 1)
        forms = [f.strip().lower() for f in forms.split(",") if f.strip()]
        return w.strip(), forms
    if a in TARGETS:
        return a, TARGETS[a]
    raise KeyError(a)


def load_specs(args):
    """展开参数：@file.txt 表示从文件读（每行一条，支持 # 注释与空行）。"""
    out = []
    for a in args:
        if a.startswith("@"):
            with open(a[1:], encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        out.append(line)
        else:
            out.append(a)
    return out


def main(args):
    docs = load()
    # 建立 小写词 -> 句子位置 索引
    index = {}
    for ti, (tag, sents) in enumerate(docs):
        for si, s in enumerate(sents):
            for tok in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", s.lower()):
                index.setdefault(tok, set()).add((ti, si))

    print("corpus files:", len(docs), flush=True)
    for a in args:
        try:
            w, want = parse_spec(a)
        except KeyError:
            print("\n### {}   跳过：不在内置词表中，请改用 word=form1,form2 指定词形".format(a), flush=True)
            continue
        found = {}
        for q in want:
            cap = 1 if len(q) >= 6 else 0
            for tok in index:
                if lev(q, tok, cap) <= cap:
                    for ti, si in index[tok]:
                        tag, sents = docs[ti]
                        found.setdefault((tag, si), (sents[si], tok))
        items = sorted(found.items(), key=lambda kv: (noise(kv[1][0]), len(kv[1][0])))
        items = [it for it in items if len(it[1][0]) <= 300]
        print("\n" + "=" * 76, flush=True)
        print("### {}   hits={}".format(w.upper(), len(items)), flush=True)
        for (tag, si), (s, tok) in items[:6]:
            print("[{}]{} {}".format(tag, "" if tok in want else " (fuzzy:%s)" % tok, s), flush=True)


if __name__ == "__main__":
    args = load_specs(sys.argv[1:])
    main(args if args else list(TARGETS))

#!/usr/bin/env python
"""外刊 PDF 取文本 / 渲染图片助手（配合 economist-intensive-reading skill 使用）。

用法:
    python extract.py text   <article.pdf> [page_index]
    python extract.py render <article.pdf> <out_prefix> [page_index] [zoom]

- text   : 打印该页文本长度；>0 直接输出正文，==0 表示扫描/图片版，需改用 render。
- render : 输出整页高分辨率 PNG + 左右分栏裁切 PNG，供多模态"看图转录"。

依赖: pymupdf  (pip install pymupdf)
"""
import sys
import pymupdf


def do_text(pdf_path: str, page_index: int = 0) -> None:
    doc = pymupdf.open(pdf_path)
    print("pages:", doc.page_count)
    print("title:", doc.metadata.get("title"))
    page = doc[page_index]
    text = page.get_text()
    print(f"textlen(page {page_index}):", len(text))
    if not text.strip():
        print(">> 无文本层（扫描版/图片版）：请改用 render 后看图转录。")
    else:
        print("---- text ----")
        print(text)


def do_render(pdf_path: str, out_prefix: str, page_index: int = 0, zoom: float = 3.0) -> None:
    doc = pymupdf.open(pdf_path)
    page = doc[page_index]
    full = f"{out_prefix}_full.png"
    page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(full)
    print("saved", full)

    # 双栏杂志排版：左右分栏 × 纵向 4 段，覆盖整页（含报头与页脚），放大后更清晰。
    # 注意：分栏边界不能"刚好"切在栏间——必须给左右两栏各留 6pt 重叠，
    # 否则右栏最左侧字符会被裁掉（实测 22.pdf 就出现此问题）。
    rect = page.rect
    mid_x = rect.width * 0.515
    ov = 6.0  # 栏间重叠量（pt）
    y_edges = [0.05, 0.29, 0.53, 0.77, 1.0]
    for ci, (x0f, x1f) in enumerate([
        (0.04, mid_x + ov),
        (mid_x - ov, 0.99),
    ]):
        for bi in range(len(y_edges) - 1):
            clip = pymupdf.Rect(x0f, rect.height * y_edges[bi],
                                x1f, rect.height * y_edges[bi + 1])
            name = f"{out_prefix}_c{ci}_b{bi}.png"
            page.get_pixmap(matrix=pymupdf.Matrix(5, 5), clip=clip).save(name)
            print("saved", name)


if __name__ == "__main__":
    mode = sys.argv[1]
    path = sys.argv[2]
    if mode == "text":
        do_text(path, int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    elif mode == "render":
        prefix = sys.argv[3]
        idx = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        z = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
        do_render(path, prefix, idx, z)
    else:
        print(__doc__)

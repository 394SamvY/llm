"""
将结构化的 JSONL 词典条目转换为纯文本，便于程序员查看/调试/检索。

默认输出为单个 .txt 文件，其中每条记录用分隔线分开。

用法示例：
  python3 jsonl_to_text.py --in dyhdc.parsed.fixed.v2.jsonl --out out.txt --limit 100
  python3 jsonl_to_text.py --in dyhdc.sample100.v3.jsonl --out dyhdc.sample100.v3.txt

可选：
  --include-meta    包含元信息行（headword 以 # 开头）
  --max-examples    每个义项最多输出的例证条数（默认 5）
  --limit           仅处理前 N 条
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional


def norm(s: Optional[str]) -> str:
    if not s:
        return ""
    # 规范化空白
    return " ".join(str(s).split())


def join_list(items: Iterable[str], sep: str = "；") -> str:
    items = [norm(x) for x in items if norm(x)]
    return sep.join(items)


def format_yinyun(yinyun: Any) -> List[str]:
    lines: List[str] = []
    if not isinstance(yinyun, list):
        return lines
    for yy in yinyun:
        if not isinstance(yy, dict):
            continue
        text = norm(yy.get("text"))
        books = yy.get("books") or []
        books_str = join_list(books, sep="；")
        if text and books_str:
            lines.append(f"- 音韵：{text}（来源：{books_str}）")
        elif text:
            lines.append(f"- 音韵：{text}")
    return lines


def format_cross_refs(refs: Any, label: str = "交叉引用") -> List[str]:
    lines: List[str] = []
    if not isinstance(refs, list):
        return lines
    items: List[str] = []
    for r in refs:
        if not isinstance(r, dict):
            continue
        text = norm(r.get("text"))
        target = norm(r.get("target"))
        if text and target:
            items.append(f"{text} -> {target}")
        elif target:
            items.append(target)
    if items:
        lines.append(f"- {label}：{join_list(items, sep='；')}")
    return lines


def format_examples(ex_list: Any, max_examples: int = 5) -> List[str]:
    lines: List[str] = []
    if not isinstance(ex_list, list):
        return lines
    if not ex_list:
        return lines
    lines.append("- 例证：")
    for i, ex in enumerate(ex_list[: max_examples]):
        if not isinstance(ex, dict):
            continue
        books = join_list(ex.get("books") or [])
        quotes = join_list(ex.get("quotes") or [])
        notes_list = ex.get("notes") or []
        notes_texts = []
        for n in notes_list:
            if isinstance(n, dict):
                t = norm(n.get("text"))
                if t:
                    notes_texts.append(t)
        notes = join_list(notes_texts)
        u_texts = join_list(ex.get("u_texts") or [])
        # 构造一条例证
        buf_parts: List[str] = []
        if books:
            buf_parts.append(f"出处：{books}")
        if quotes:
            buf_parts.append(f"引文：{quotes}")
        if u_texts:
            buf_parts.append(f"标注：{u_texts}")
        if notes:
            buf_parts.append(f"注：{notes}")
        ex_line = f"  · {'；'.join(buf_parts)}" if buf_parts else None
        if ex_line:
            lines.append(ex_line)
    return lines


def format_sense(sense: Dict[str, Any], max_examples: int = 5) -> List[str]:
    lines: List[str] = []
    mean = norm(sense.get("mean"))
    if mean:
        lines.append(f"释义：{mean}")
    # see / see_refs
    see = join_list(sense.get("see") or [])
    if see:
        lines.append(f"参见：{see}")
    see_refs = format_cross_refs(sense.get("see_refs") or [], label="参见链接")
    lines.extend(see_refs)
    # examples
    lines.extend(format_examples(sense.get("examples") or [], max_examples=max_examples))
    return lines


def entry_to_text(obj: Dict[str, Any], *, max_examples: int = 5) -> str:
    head = norm(obj.get("headword"))
    hw = norm(obj.get("hw"))
    simp = norm(obj.get("simp"))
    pron = norm(obj.get("pron"))

    title_parts = [p for p in [hw or head, simp and f"[{simp}]", pron and f"/{pron}/"] if p]
    header = " ".join(title_parts) if title_parts else head

    out_lines: List[str] = []
    out_lines.append(header)

    # 音韵
    out_lines.extend(format_yinyun(obj.get("yinyun")))

    # 义项
    senses = obj.get("senses") or []
    if isinstance(senses, list) and senses:
        for idx, s in enumerate(senses, 1):
            if not isinstance(s, dict):
                continue
            out_lines.append(f"{idx}. ")
            out_lines.extend(format_sense(s, max_examples=max_examples))
    # 交叉引用 / 重定向 / 异体
    out_lines.extend(format_cross_refs(obj.get("cross_refs") or [], label="交叉引用"))
    redirect_to = norm(obj.get("redirect_to"))
    if redirect_to:
        out_lines.append(f"- 重定向：{redirect_to}")
    variant_of = join_list(obj.get("variant_of") or [])
    if variant_of:
        out_lines.append(f"- 异体：{variant_of}")

    return "\n".join(out_lines).rstrip()


def main() -> None:
    ap = argparse.ArgumentParser(description="将 JSONL 词典转换为纯文本")
    ap.add_argument("--in", dest="in_path", required=True, help="输入 JSONL 路径")
    ap.add_argument("--out", dest="out_path", required=True, help="输出 TXT 路径")
    ap.add_argument("--include-meta", dest="include_meta", action="store_true", help="包含元信息行（#name/#description）")
    ap.add_argument("--max-examples", dest="max_examples", type=int, default=5, help="每义项最多输出例证条数，默认 5")
    ap.add_argument("--limit", dest="limit", type=int, default=None, help="仅处理前 N 条")
    args = ap.parse_args()

    if not os.path.exists(args.in_path):
        print(f"[Error] 未找到输入文件: {args.in_path}")
        sys.exit(1)

    total = 0
    written = 0
    with open(args.in_path, "r", encoding="utf-8", errors="ignore") as fin, \
         open(args.out_path, "w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            if args.limit is not None and written >= args.limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            total += 1
            head = obj.get("headword")
            if isinstance(head, str) and head.startswith("#") and not args.include_meta:
                continue

            block = entry_to_text(obj, max_examples=args.max_examples)
            if not block:
                continue
            if written:
                fout.write("\n\n" + ("-" * 40) + "\n\n")
            fout.write(block + "\n")
            written += 1

    print(f"[Done] 转换完成：共读取 {total} 行，写出 {written} 条 -> {args.out_path}")


if __name__ == "__main__":
    main()


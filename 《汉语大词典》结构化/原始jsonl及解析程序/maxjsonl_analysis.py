"""
将 JSONL 词典条目（含自定义 HTML 结构）解析为更结构化、可读性更好的 JSONL：
- 清理不适合人类阅读的部分（如 <script>、<link> 等）
- 按标签解析出词头、读音、音韵、释义、参见、例句等字段

默认：
  输入: dyhdc.jsonl
  输出: dyhdc.parsed.jsonl

用法：
  python3 maxjsonl_analysis.py                                # 解析全量（可能耗时）
  python3 maxjsonl_analysis.py --in dyhdc.head200.jsonl        # 解析样本
  python3 maxjsonl_analysis.py --out parsed.jsonl --limit 5000 # 解析前 5000 条
  python3 maxjsonl_analysis.py --keep-html                     # 保留清理后的 html_clean 字段
  python3 maxjsonl_analysis.py --no-skip-meta                  # 包含以 # 开头的元信息行
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple


def strip_unreadable_html(html: str) -> str:
    """去除不适合人类阅读的部分：脚本与样式引入等。

    - 移除所有 <script>...</script>
    - 移除所有 <link ...>
    - 可按需扩展（如移除内联样式），这里保留标签语义供解析
    """
    # 移除 script
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html)
    # 移除 link
    html = re.sub(r"(?is)<link[^>]*>", "", html)
    return html.strip()


def text_of(elem: Optional[ET.Element]) -> str:
    if elem is None:
        return ""
    # 归一化空白
    txt = "".join(elem.itertext())
    return " ".join(txt.split())


def inner_html(elem: Optional[ET.Element]) -> str:
    """返回元素的内部 HTML（不包含外层标签）。

    优先采用序列化后截取方式，避免手动拼接 child.tail 造成的重复。
    如失败，则退回到手动拼接（尽量不空）。
    """
    if elem is None:
        return ""
    try:
        s = ET.tostring(elem, encoding="unicode")
        i = s.find('>')
        j = s.rfind('</')
        if i != -1 and j != -1 and j > i:
            return s[i+1:j].strip()
    except Exception:
        pass
    # 回退：保守拼接
    parts: List[str] = []
    if elem.text:
        parts.append(elem.text)
    for ch in list(elem):
        parts.append(ET.tostring(ch, encoding="unicode"))
        if ch.tail:
            parts.append(ch.tail)
    return "".join(parts).strip()


def collect_cross_refs(elem: Optional[ET.Element]) -> List[Dict[str, str]]:
    refs: List[Dict[str, str]] = []
    if elem is None:
        return refs
    for a in elem.findall('.//a'):
        href = a.attrib.get('href', '')
        if href.startswith('bword://'):
            refs.append({'text': text_of(a), 'target': href[len('bword://'):]})
    return refs


def collect_images(elem: Optional[ET.Element]) -> List[str]:
    imgs: List[str] = []
    if elem is None:
        return imgs
    for img in elem.findall('.//img'):
        src = img.attrib.get('src')
        if src:
            imgs.append(src)
    return imgs


def parse_example_node(ex: ET.Element) -> Dict[str, Any]:
    """解析单个 <example> 节点，尽可能保留信息。"""
    ex_obj: Dict[str, Any] = {
        'books': [],
        'quotes': [],
        'notes': [],  # 每项: {text, html}
        'u_texts': [],
        'cross_refs': [],
        'images': [],
        'text': text_of(ex),
        'html': inner_html(ex),
    }
    for b in ex.findall('book'):
        t = text_of(b)
        if t:
            ex_obj['books'].append(t)
    for q in ex.findall('quote'):
        t = text_of(q)
        if t:
            ex_obj['quotes'].append(t)
    for n in ex.findall('note'):
        nt = text_of(n)
        nh = inner_html(n)
        if nt or nh:
            ex_obj['notes'].append({'text': nt, 'html': nh})
    # 收集所有 <u> 文本
    for u in ex.findall('.//u'):
        ut = text_of(u)
        if ut:
            ex_obj['u_texts'].append(ut)
    ex_obj['cross_refs'] = collect_cross_refs(ex)
    ex_obj['images'] = collect_images(ex)
    return ex_obj


def parse_entry_html(html: str) -> Dict[str, Any]:
    """解析单条条目的 HTML，提取结构化字段。

    返回字段包含（尽力提取，字段可能为空）：
      - hw: 词头（优先 div.hw）
      - pron: 读音
      - yinyun: 音韵列表，每项为纯文本（含来源）
      - senses: 义项列表，每项包含：
          - mean: 释义文本
          - see: 参见列表（从 <see> 中提取）
          - examples: 例句列表，每项包含 book, quote, note（若存在）
      - source_class: 顶层 <hdcs> 的 class（如 xml）
    """
    result: Dict[str, Any] = {
        "hw": "",
        "pron": "",
        "yinyun": [],
        "senses": [],
        "source_class": "",
        "images": [],
        "cross_refs": [],
        "redirect_to": None,
        "variant_of": [],
    }

    cleaned = strip_unreadable_html(html)
    if not cleaned:
        return result

    # ElementTree 解析（数据基本是类 XML 结构）
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError:
        # 解析失败则仅返回清理后的 HTML 文本内容作为备选
        result["hw"] = ""
        result["pron"] = ""
        result["yinyun"] = []
        result["senses"] = [{"mean": re.sub(r"<[^>]+>", " ", cleaned)}]
        return result

    # 顶层类名
    if root.tag.lower() == "hdcs":
        result["source_class"] = root.attrib.get("class", "")

    # 词头与音读信息块
    hm = root.find(".//hm")
    if hm is not None:
        # div.hw
        hw_div = None
        for child in hm.findall("div"):
            if child.attrib.get("class") == "hw":
                hw_div = child
                break
        if hw_div is not None:
            result["hw"] = text_of(hw_div)
        # pron
        pron = hm.find("pron")
        result["pron"] = text_of(pron)
        # 简体词头（若存在）
        simp = hm.find("simp")
        if simp is not None:
            result["simp"] = text_of(simp)
        # yinyun（可能多个），保留来源 book
        yinyun_nodes = hm.findall("yinyun")
        yinyun_list: List[Dict[str, Any]] = []
        for yy in yinyun_nodes:
            books = [text_of(b) for b in yy.findall("book")]
            yinyun_list.append({
                "text": text_of(yy),
                "books": [b for b in books if b],
            })
        result["yinyun"] = yinyun_list

    # 图片收集（全局）
    result["images"] = collect_images(root)
    # 收集全局交叉引用（bword://）
    result["cross_refs"] = collect_cross_refs(root)

    # 义项（<item>）
    for item in root.findall(".//item"):
        sense: Dict[str, Any] = {"mean": "", "see": [], "see_refs": [], "examples": [], "highlights": []}
        mean = item.find("mean")
        if mean is not None:
            # 参见（see）
            see_terms: List[str] = []
            see_refs: List[Dict[str, str]] = []
            for see in mean.findall(".//see"):
                see_txt = text_of(see)
                if see_txt:
                    see_terms.append(see_txt)
                # 参见中的链接
                for a in see.findall('.//a'):
                    href = a.attrib.get('href', '')
                    if href.startswith('bword://'):
                        see_refs.append({'text': text_of(a), 'target': href[len('bword://'):]})
            sense["see"] = see_terms
            sense["see_refs"] = see_refs
            # 释义文本（移除 see 标签后整体文本）
            # 直接取整块文本（包含 see 文本），通常对人类仍可读
            sense["mean"] = text_of(mean)

            # 高亮（如<u>专名号</u>）
            highlights = [text_of(u) for u in mean.findall('.//u')]
            if highlights:
                sense["highlights"] = [h for h in highlights if h]

        # 例句（examples / example）
        examples = item.find("examples")
        # 解析 examples 容器，尽可能保留所有内容
        if examples is not None:
            sense.setdefault("examples_rich", {
                'html': inner_html(examples),
                'segments': []  # 依顺序：text/inline/example/node
            })

            # 先处理容器开头的 text
            if examples.text and examples.text.strip():
                sense["examples_rich"]["segments"].append({
                    'type': 'text',
                    'text': " ".join(examples.text.split()),
                })

            for child in list(examples):
                tag = (child.tag or '').lower()
                if tag == 'example':
                    ex_obj = parse_example_node(child)
                    sense.setdefault("examples", []).append({
                        # 保留之前的简化接口，同时增加更全的数据
                        'books': ex_obj['books'],
                        'quotes': ex_obj['quotes'],
                        'notes': ex_obj['notes'],
                        'u_texts': ex_obj['u_texts'],
                        'cross_refs': ex_obj['cross_refs'],
                        'images': ex_obj['images'],
                        'text': ex_obj['text'],
                        'html': ex_obj['html'],
                    })
                    sense["examples_rich"]["segments"].append({
                        'type': 'example',
                        'data': ex_obj,
                    })
                elif tag == 'a':
                    href = child.attrib.get('href', '')
                    seg = {
                        'type': 'anchor',
                        'text': text_of(child),
                        'href': href,
                        'html': ET.tostring(child, encoding='unicode'),
                    }
                    if href.startswith('bword://'):
                        seg['target'] = href[len('bword://'):]
                    sense["examples_rich"]["segments"].append(seg)
                else:
                    # 其它直接子节点（极少数情形）
                    sense["examples_rich"]["segments"].append({
                        'type': 'node',
                        'tag': tag,
                        'text': text_of(child),
                        'html': ET.tostring(child, encoding='unicode'),
                    })

                # 处理每个子节点后的 tail 文本
                if child.tail and child.tail.strip():
                    sense["examples_rich"]["segments"].append({
                        'type': 'text',
                        'text': " ".join(child.tail.split()),
                    })
            # 如果 mean 为空，尝试用 examples 中的普通文本作为补充定义
            if not sense.get("mean"):
                fallback_texts: List[str] = []
                for seg in sense["examples_rich"]["segments"]:
                    if seg.get('type') == 'text':
                        t = seg.get('text', '').strip()
                        if not t:
                            continue
                        # 过滤明显的参见提示词
                        if re.fullmatch(r"[参阅参见见详见又并及、，。；:：\s]+", t):
                            continue
                        if t in ("参阅", "参见", "见"):
                            continue
                        fallback_texts.append(t)
                if fallback_texts:
                    sense["mean"] = " ".join(fallback_texts)
        else:
            # 没有 <examples> 容器，回退收集散落的 <example>
            for ex in item.findall('.//example'):
                ex_obj = parse_example_node(ex)
                sense.setdefault("examples", []).append({
                    'books': ex_obj['books'],
                    'quotes': ex_obj['quotes'],
                    'notes': ex_obj['notes'],
                    'u_texts': ex_obj['u_texts'],
                    'cross_refs': ex_obj['cross_refs'],
                    'images': ex_obj['images'],
                    'text': ex_obj['text'],
                    'html': ex_obj['html'],
                })

        # 仅在有内容时加入
        if any([
            sense.get("mean"),
            sense.get("see"),
            sense.get("examples"),
            sense.get("examples_rich"),
        ]):
            result["senses"].append(sense)

    # 解析重定向与异体字提示（基于常见文本模式）
    def detect_redirect_and_variants(senses: List[Dict[str, Any]]) -> Tuple[Optional[str], List[str]]:
        redirect_to: Optional[str] = None
        variants: List[str] = []
        if not senses:
            return None, []
        s0 = senses[0]
        mean0 = s0.get('mean', '')
        # 亦作“X” 或 “同‘X’” 等
        # 匹配所有引号包裹的词头
        for pat in [r"亦作[“\"]([^”\"]+)[”\"]", r"同[“\"]([^”\"]+)[”\"]"]:
            for m in re.finditer(pat, mean0):
                word = m.group(1).strip()
                if word and word not in variants:
                    variants.append(word)
        # 如果只有参见且首义项是“同X”之类，则视为重定向
        if s0.get('see_refs'):
            txt = re.sub(r"\s+", "", mean0)
            if txt.startswith('同') and len(senses) == 1:
                redirect_to = s0['see_refs'][0]['target']
        return redirect_to, variants

    redirect_to, variants = detect_redirect_and_variants(result["senses"])
    result["redirect_to"] = redirect_to
    if variants:
        result["variant_of"] = variants

    return result


def process_jsonl(
    in_path: str,
    out_path: str,
    keep_html: bool = False,
    skip_meta: bool = True,
    limit: Optional[int] = None,
) -> int:
    """流式读取 JSONL，解析并另存为结构化 JSONL。

    返回写入的条数。
    """
    count_out = 0
    with open(in_path, "r", encoding="utf-8", errors="ignore") as fin, \
         open(out_path, "w", encoding="utf-8", newline="\n") as fout:
        for i, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            head = obj.get("headword")
            if skip_meta and isinstance(head, str) and head.startswith("#"):
                continue

            # 兼容两类输入：原始 JSONL(有 html) 与已解析 JSONL(有 html_clean)
            html = obj.get("html") or obj.get("html_clean", "")
            # 若 html 不含结构，但 alts 中包含结构化片段（少数异常行），尝试回退
            if (not html or ('<hdc' not in html and '<hdcs' not in html)) and isinstance(obj.get('alts'), list):
                for alt in obj['alts']:
                    if isinstance(alt, str) and ('<hdc' in alt or '<hdcs' in alt):
                        html = alt
                        break
            parsed = parse_entry_html(html)
            out_obj: Dict[str, Any] = {
                "headword": head,
                **parsed,
            }
            # 传递上游的 alts（如果 jsonl 中存在）
            if "alts" in obj and isinstance(obj["alts"], list):
                out_obj["alts"] = obj["alts"]
            if keep_html:
                out_obj["html_clean"] = strip_unreadable_html(html)

            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            count_out += 1
            if limit is not None and count_out >= limit:
                break
    return count_out


def main():
    parser = argparse.ArgumentParser(description="解析 JSONL 词典条目为更结构化的 JSONL")
    parser.add_argument("--in", dest="in_path", default="dyhdc.jsonl", help="输入 JSONL 路径")
    parser.add_argument("--out", dest="out_path", default="dyhdc.parsed.jsonl", help="输出 JSONL 路径")
    parser.add_argument("--limit", type=int, default=None, help="最多处理条数（默认全量）")
    parser.add_argument("--keep-html", dest="keep_html", action="store_true", help="在输出中保留清理后的 html_clean")
    parser.add_argument("--no-skip-meta", dest="skip_meta", action="store_false", help="包含以 # 开头的元信息行")
    args = parser.parse_args()

    in_path = os.path.abspath(args.in_path)
    out_path = os.path.abspath(args.out_path)
    if not os.path.exists(in_path):
        print(f"[Error] 未找到输入文件: {in_path}")
        sys.exit(1)

    written = process_jsonl(
        in_path=in_path,
        out_path=out_path,
        keep_html=args.keep_html,
        skip_meta=args.skip_meta,
        limit=args.limit,
    )
    print(f"[Done] 写入 {written} 行 -> {out_path}")


if __name__ == "__main__":
    main()

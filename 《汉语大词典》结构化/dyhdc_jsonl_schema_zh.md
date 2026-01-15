# 汉语大词典 JSONL 解析说明（供网站使用）

本说明面向 Web 程序员，介绍如何使用本仓库生成的 JSONL 词典数据进行渲染与检索。

- 数据文件：`dyhdc.parsed.fixed.v2.jsonl`（UTF-8，按行存放 JSON 对象，体量较大）
- 行粒度：一行即一条记录；少量为“元信息行”（如字典名称与描述），大多数为“词条行”。
- 清理策略：已去除 `<script>` 与 `<link>` 等不适合阅读的部分；尽可能保留结构化信息。

---

## 快速上手

- 逐行读取（JSONL），避免一次性加载全文件。
- 将 `headword` 用作主键，`hw` 用作展示词头，`simp`（若存在）可用于简繁检索。

示例（Python 伪代码）：

```python
import json
with open('dyhdc.parsed.fixed.v2.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        # 略过元信息行
        if isinstance(obj.get('headword'), str) and obj['headword'].startswith('#'):
            continue
        # 使用结构化字段渲染/索引
        term = obj.get('hw') or obj.get('headword')
        simp = obj.get('simp')
        pron = obj.get('pron')
        senses = obj.get('senses', [])
```

---

## 顶层字段（每行对象）

| 字段         | 类型           | 说明                                                                            |
| ------------ | -------------- | ------------------------------------------------------------------------------- |
| headword     | string         | 原始词头（主键）。元信息行以 `#` 开头（如 `#name`、`#description`）。           |
| hw           | string         | 展示用词头，从结构 `<hm><div class="hw">` 提取，常与 `headword` 相同。          |
| simp         | string?        | 简体词头（若 `<hm><simp>` 存在）。                                              |
| pron         | string?        | 读音文本，从 `<pron>` 提取。                                                    |
| yinyun       | array<object>  | 音韵信息数组；每项 `{ text, books[] }`，`text` 为全文，`books[]` 为来源书名。   |
| senses       | array<object>  | 义项数组（见下节“义项对象”）。                                                  |
| images       | array<string>  | 词条内出现的所有图片 `src`。                                                    |
| cross_refs   | array<object>  | 全文内的交叉引用链接 `{ text, target }`，来源于 `bword://...`。                 |
| redirect_to  | string         | null                                                                            | 若该词条为“同X”等纯重定向，给出目标词头。 |
| variant_of   | array<string>  | 解析“亦作‘X’”等模式得到的相关词头。                                             |
| source_class | string         | 根容器 `<hdcs>` 的 `class`（如 `xml`），信息性字段。                            |
| alts         | array<string>? | 源数据中的“别名/附加内容”。个别行含结构化片段（已用于回退解析），请勿直接渲染。 |
| html_clean   | string?        | 清理后的原始 HTML（无脚本/外链），可直接用于接近源样式的渲染。                  |

---

## 义项对象（senses[]）

| 字段          | 类型           | 说明                                                                              |
| ------------- | -------------- | --------------------------------------------------------------------------------- |
| mean          | string         | 释义文本。若 `<mean>` 为空，已从 `<examples>` 中的普通文本片段回补。              |
| see           | array<string>  | `<see>` 中的参见文本（纯文本）。                                                  |
| see_refs      | array<object>  | `<see>` 中的结构化链接 `{ text, target }`，其中 `target` 去除了 `bword://` 前缀。 |
| examples      | array<object>  | 解析后的例证列表（见下节“例证对象”）。                                            |
| examples_rich | object?        | 保真容器，完整保留 `<examples>` 内部 HTML 与顺序片段。结构见下。                  |
| highlights    | array<string>? | `<u>` 标签中的高亮词（如专名号内容）。                                            |

### examples_rich 结构

- `html`: `<examples>` 节点的内部 HTML（不含外层标签）。
- `segments`: 有序片段数组，用于完整再现内容与顺序；每个片段包含：
  - `type=example`：`data` 为“例证对象”完整结构。
  - `type=anchor`：直接子级超链接片段；包含 `text`、`href`、可选 `target`（若 `bword://`）。
  - `type=text`：普通游离文本片段，字段 `text`。
  - `type=node`：其它直接子节点，包含 `tag`、`text`、`html`。

---

## 例证对象（senses[].examples[] 或 segments[type=example].data）

| 字段       | 类型          | 说明                                                   |
| ---------- | ------------- | ------------------------------------------------------ |
| books      | array<string> | 书名/出处（可能多个）。                                |
| quotes     | array<string> | 引文文本（可能多个）。                                 |
| notes      | array<object> | 注释列表，每项 `{ text, html }`。                      |
| u_texts    | array<string> | 例证内部所有 `<u>` 文本（常为朝代、人名、地名等）。    |
| cross_refs | array<object> | 例证内部的 `bword://` 链接 `{ text, target }`。        |
| images     | array<string> | 例证内部图片 `src`。                                   |
| text       | string        | 例证的纯文本描述（合并了书名、引文等），空白已规范化。 |
| html       | string        | 例证的内部 HTML（不含外层 `<example>` 标签）。         |

---

## 元信息行

- `headword = "#name"`：字典名称，值在 `html`/`html_clean` 中。
- `headword = "#description"`：字典的描述、来源、更新历史等（HTML）。
- 处理建议：
  - 检索与索引时跳过；
  - 可用于“关于/说明”页面展示（注意 HTML 安全）。

---

## 渲染建议

有两种典型路径：

1) 结构化渲染（推荐）：
- 标题：`hw`（可同时展示 `simp`、`pron`）。
- 音韵：`yinyun[].text`，并在悬浮/次要信息中展示 `books[]` 来源。
- 义项：
  - 主释义：`mean`
  - 参见：`see` 与 `see_refs`（将 `target` 作为站内跳转目标）
  - 例证：用 `quotes` + `books`（如需最大保真，可使用 `examples_rich`）
- 链接：
  - 词条级 `cross_refs`/义项级 `see_refs` → 站内跳转（`bword://<目标词>` 去前缀）。
  - 若 `redirect_to` 存在，优先渲染重定向提示并跳转/合并目标词内容。

2) HTML 渲染（快速）：
- 直接使用 `html_clean`，配合样式将 `<hdcs>/<hdc>/<hm>/<item>` 等映射为合适的块级元素。
- 仍需对 HTML 进行安全过滤（虽然已移除脚本/外链）。

---

## 索引与搜索建议

- 主键/检索键：`headword`、`hw`、`simp`。
- 同义/别名与关系：`alts`、`variant_of`、`redirect_to`。
- 全文检索字段：`mean`、`yinyun[].text`、`examples[].quotes`、`examples[].text`。
- 关联图谱：`see_refs[].target`、`cross_refs[].target`。
- 分面/排序：义项数、例证数、是否具有 `simp`、是否重定向等。

---

## 链接与图片

- `bword://目标词` → 去前缀得到 `target`，作为站内词条路由参数。
- 图片 `images`/例证图片：路径可能相对，请根据部署环境映射至静态资源/CDN。

---

## 边界与兼容性

- 可选字段：`simp`、`pron`、`images`、`see_refs`、`examples_rich` 等并非所有词条都存在。
- 回退逻辑：
  - 当 `<mean>` 为空，已从 `<examples>` 的普通片段补充 `mean`（保留人类可读信息）。
  - 极少数源数据行的结构化 HTML 位于 `alts` 中，已在解析时用于回退提取结构。
- 去重处理：已修复例证 HTML 中偶发的“全角冒号重复（：：）”与片段重复问题。

---

## 版本与生成流程（概述）

- 源：MDict `.mdx`
- 转：PyGlossary → CSV → JSONL（每行 `{ headword, html[, alts] }`）
- 解析：本仓库脚本进行结构化提取，得到 `dyhdc.parsed.fixed.v2.jsonl`
  - 去除脚本/外链、结构化拆分、关系抽取（redirect/variant/links）、
  - 例证保真（`examples_rich`）、义项补全（从 examples 回补）。

---

## 附：最小样例（示意）

```json
{
  "headword": "樗雞",
  "hw": "樗雞",
  "simp": "樗鸡",
  "pron": "chū jī",
  "yinyun": [
    { "text": "《集韵》…", "books": ["《集韵》"] }
  ],
  "senses": [
    {
      "mean": "虫名。居樗树上，翅有彩纹。",
      "see": [],
      "see_refs": [],
      "examples": [
        {
          "books": ["《尔雅·释虫》"],
          "quotes": [],
          "notes": [{"text": "晋郭璞注：…", "html": "<u>晋</u><u>郭璞</u>注：…"}],
          "u_texts": ["晋", "郭璞"],
          "text": "《尔雅·释虫》…晋郭璞注：…",
          "html": "<book>《尔雅·释虫》</book>…"
        }
      ],
      "examples_rich": { "html": "<example>…</example>", "segments": [ { "type": "example", "data": { "books": ["…"] } } ] }
    }
  ],
  "images": [],
  "cross_refs": [],
  "redirect_to": null,
  "variant_of": [],
  "source_class": "xml",
  "html_clean": "<hdcs class=\"xml\">…</hdcs>"
}
```

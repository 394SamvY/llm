# 工具层API文档

> **负责人**: 成员C  
> **完成日期**: 2026-01-17  
> **状态**: ✅ 已完成并接入真实数据

---

## 📋 目录

1. [快速开始](#快速开始)
2. [前置条件：构建索引文件](#前置条件构建索引文件)
3. [语义查询工具 (semantic_tool.py)](#语义查询工具-semantic_toolpy)
4. [文献检索工具 (textual_tool.py)](#文献检索工具-textual_toolpy)
5. [训式识别工具 (pattern_tool.py)](#训式识别工具-pattern_toolpy)
6. [集成使用示例](#集成使用示例)
7. [常见问题](#常见问题)

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 构建索引文件（必须！）

在使用工具之前，必须先构建词典索引文件：

```bash
# 方法1: 使用便捷脚本
python check_and_build_index.py

# 方法2: 直接运行构建器
python -c "from src.data.dyhdc_index_builder import build_dyhdc_index; build_dyhdc_index()"
```

索引文件将生成在：`data/processed/dyhdc_index.json`（约24.5MB）

### 3. 使用工具

```python
from src.tools import query_word_meaning, search_textual_evidence, identify_pattern

# 语义查询
result = query_word_meaning("崇")
print(result["本义"])

# 文献检索
evidence = search_textual_evidence("崇", "終", context="崇朝其雨")
print(evidence["有佐证"])

# 训式识别
pattern = identify_pattern("崇，讀為終")
print(pattern["暗示类型"])  # "假借"
```

---

## 前置条件：构建索引文件

### 为什么需要索引文件？

《汉语大词典》JSONL文件约1.9GB，直接遍历查询非常慢。索引文件记录了每个字在JSONL文件中的位置（偏移量），可以快速定位和读取。

### 如何构建索引

**步骤1：检查索引文件是否存在**

```python
from pathlib import Path
from src.config import get_settings

settings = get_settings()
index_path = settings.data_processed_dir / "dyhdc_index.json"

if not index_path.exists():
    print("索引文件不存在，需要构建")
else:
    print(f"索引文件已存在: {index_path}")
```

**步骤2：构建索引**

```python
from src.data.dyhdc_index_builder import build_dyhdc_index

# 自动使用默认路径
build_dyhdc_index()

# 或指定路径
build_dyhdc_index(
    jsonl_path="《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl",
    output_path="data/processed/dyhdc_index.json"
)
```

**构建时间**：约1-3分钟（取决于磁盘速度）

**输出**：
- `data/processed/dyhdc_index.json` - 索引文件（约24.5MB）
- 包含408,931条词条，27,678个首字

---

## 语义查询工具 (semantic_tool.py)

### 功能说明

查询汉字的本义、义项、例句、假借标注等语义信息。

**数据源**：《汉语大词典》，通过`DYHDCIndexLoader`查询

### 使用方式

#### 方式1：函数式接口（推荐）

```python
from src.tools import query_word_meaning

# 查询单个字
result = query_word_meaning("崇")

print(result["字"])          # "崇"
print(result["本义"])        # "高；高大。"
print(result["义项"])        # ["高；高大。", "尊崇", "充实", ...]
print(result["例句"])        # [{"quote": "崇山峻岭"}, ...]
print(result["假借标注"])    # ["12通"終"。终尽。参见"崇朝"。"]
```

#### 方式2：类式接口

```python
from src.tools import SemanticTool

tool = SemanticTool()
word_meaning = tool.query("崇")

print(word_meaning.char)              # "崇"
print(word_meaning.primary_meaning)   # "高；高大。"
print(word_meaning.meanings)          # ["高；高大。", "尊崇", ...]
print(word_meaning.jiajie_notes)      # ["12通"終"。终尽。参见"崇朝"。"]
```

### 返回数据格式

**函数式接口返回**：
```python
{
    "字": "崇",
    "本义": "高；高大。",
    "义项": [
        "高；高大。",
        "尊崇",
        "充实",
        ...
    ],
    "例句": [
        {"quote": "崇山峻岭"},
        ...
    ],
    "假借标注": [
        "12通"終"。终尽。参见"崇朝"。"
    ]
}
```

**类式接口返回**：`WordMeaning` 对象
```python
@dataclass
class WordMeaning:
    char: str                    # 汉字
    primary_meaning: str          # 本义
    meanings: List[str]          # 所有义项
    examples: List[Dict]         # 例句
    jiajie_notes: List[str]      # 假借标注
    raw_data: Optional[Dict]    # 原始数据
```

### 注意事项

1. **繁简体问题**：词典使用繁体字索引，查询"终"需用"終"
2. **未收录处理**：如果字不在词典中，返回`"本义": "未收录"`
3. **首次加载**：首次查询会加载索引（约1秒），后续查询很快

### 错误处理

```python
result = query_word_meaning("崇")
if result["本义"] == "未收录":
    print("该字未收录在词典中")
elif result["本义"] == "未加载":
    print("索引文件未加载，请检查索引文件是否存在")
```

---

## 文献检索工具 (textual_tool.py)

### 功能说明

检索两个字之间的文献佐证，包括：
- 假借记录（词典中的假借标注）
- 异文（不同版本的字形差异）
- 平行文本（相似用法的文本）

**数据源**：《汉语大词典》的假借标注和例句

### 使用方式

#### 方式1：函数式接口（推荐）

```python
from src.tools import search_textual_evidence

# 检索两个字之间的佐证
result = search_textual_evidence(
    char_a="崇",      # 被释字
    char_b="終",      # 释字
    context="崇朝其雨"  # 上下文（可选）
)

print(result["有佐证"])      # True/False
print(result["假借记录"])    # [...]
print(result["异文"])        # [...]
print(result["总结"])        # "找到2处假借记录"
```

#### 方式2：类式接口

```python
from src.tools import TextualTool

tool = TextualTool()
evidence = tool.search("崇", "終", context="崇朝其雨")

print(evidence.has_evidence)      # True
print(evidence.jiajie_records)    # [...]
print(evidence.variant_texts)     # [...]
print(evidence.summary)           # "找到2处假借记录"
```

### 返回数据格式

**函数式接口返回**：
```python
{
    "有佐证": True,
    "假借记录": [
        {
            "type": "jiajie",
            "source": "《毛传》",
            "text": "崇，終也",
            "note": "词典中标注：崇与終的假借关系"
        }
    ],
    "异文": [
        {
            "type": "variant",
            "source": "《汉语大词典》例句",
            "text": "崇朝 vs 終朝",
            "note": "例句中包含相关用字"
        }
    ],
    "平行文本": [],
    "总结": "找到2处假借记录；找到1处异文"
}
```

**类式接口返回**：`TextualEvidence` 对象
```python
@dataclass
class TextualEvidence:
    has_evidence: bool                    # 是否找到佐证
    variant_texts: List[Dict[str, str]]   # 异文
    parallel_texts: List[Dict[str, str]]  # 平行文本
    jiajie_records: List[Dict[str, str]]  # 假借记录
    summary: str                          # 总结说明
```

### 检索逻辑

1. **假借标注检索**：
   - 从被释字的假借标注中查找是否包含释字
   - 从释字的假借标注中查找是否包含被释字（反向）

2. **异文检索**：
   - 如果提供了上下文，在例句中查找包含上下文的例子
   - 查找例句中同时包含两个字的情况

3. **义项检索**：
   - 在义项中查找包含"通"、"读为"、"读曰"、"假借"等术语的条目

### 注意事项

1. **上下文的作用**：提供上下文可以提高检索精度
2. **繁简体**：建议使用繁体字查询，匹配更准确
3. **空结果**：如果未找到佐证，`has_evidence`为`False`，但这是正常情况

---

## 训式识别工具 (pattern_tool.py)

### 功能说明

识别训诂句的格式，判断使用了什么训释术语，并推断暗示的类型（假借/语义解释/以声通义）。

**数据源**：内置的训式规则表（正则表达式）

### 使用方式

#### 方式1：函数式接口（推荐）

```python
from src.tools import identify_pattern

# 识别训诂句格式
result = identify_pattern("崇，讀為終")

print(result["格式"])          # "读为"
print(result["被释字"])        # "崇"
print(result["释字"])          # "終"
print(result["暗示类型"])      # "假借"
print(result["置信度"])        # "高"
print(result["可直接判定"])    # True
print(result["说明"])          # "郑玄《礼》注，破字/改读术语"
```

#### 方式2：类式接口

```python
from src.tools import PatternTool

tool = PatternTool()
pattern = tool.identify("崇，終也")

print(pattern.pattern_name)      # "A也"
print(pattern.char_a)            # "崇"
print(pattern.char_b)            # "終"
print(pattern.implied_type)      # "不确定"
print(pattern.confidence)        # "低"
print(pattern.can_direct_judge)  # False
```

### 返回数据格式

**函数式接口返回**：
```python
{
    "格式": "读为",
    "被释字": "崇",
    "释字": "終",
    "暗示类型": "假借",
    "置信度": "高",
    "可直接判定": True,
    "说明": "郑玄《礼》注，破字/改读术语"
}
```

**类式接口返回**：`PatternResult` 对象
```python
@dataclass
class PatternResult:
    pattern_name: str        # 格式名称
    char_a: str             # 被释字
    char_b: str             # 释字
    implied_type: str       # 暗示类型
    confidence: str         # 置信度
    can_direct_judge: bool  # 是否可直接判定
    source: str            # 来源说明
```

### 支持的训式类型

#### A类：直接判假借（高置信度）
- `读为`、`读曰`、`读当为`、`当为`、`当作`
- `通`、`古字通`、`假借字`、`借字也`、`借为`

#### B类：可能假借（中置信度）
- `读若`、`读如`、`或作`、`亦作`、`本作`、`声近`

#### C类：以声通义
- `之言`、`之为言`

#### D类：直接判语义解释
- `犹也`、`犹言`、`谓之`、`之貌`、`之称`、`貌`、`所以`

#### E类：不确定（低置信度）
- `者也`、`即`、`A也`（基本格式）

### 示例

```python
# 假借类
identify_pattern("崇，讀為終")      # 类型: "假借", 置信度: "高"
identify_pattern("正，讀為征")      # 类型: "假借", 置信度: "高"
identify_pattern("崇與終通")        # 类型: "假借", 置信度: "高"

# 语义解释类
identify_pattern("夭夭，盛也")      # 类型: "语义解释", 置信度: "高"
identify_pattern("硕，大貌")        # 类型: "语义解释", 置信度: "高"
identify_pattern("鉴，所以察形也")  # 类型: "语义解释", 置信度: "高"

# 以声通义
identify_pattern("海之言晦也")      # 类型: "以声通义", 置信度: "中"

# 不确定
identify_pattern("崇，終也")        # 类型: "不确定", 置信度: "低"
identify_pattern("政者，正也")      # 类型: "不确定", 置信度: "低"
```

### 注意事项

1. **标点符号**：支持中文和英文标点（，,）
2. **繁简体**：自动处理繁简体
3. **优先级**：按A类→B类→C类→D类→E类的顺序匹配，先匹配到就返回
4. **低置信度**：对于"不确定"类型，需要结合其他工具综合判断

---

## 集成使用示例

### 完整分析流程

```python
from src.tools import (
    query_word_meaning,
    search_textual_evidence,
    identify_pattern
)

# 分析训诂句："崇，終也"
xungu_sentence = "崇，終也"
char_a = "崇"
char_b = "終"
context = "崇朝其雨"

print("=" * 60)
print(f"分析训诂句: {xungu_sentence}")
print("=" * 60)

# 步骤1: 语义分析
print("\n[1] 语义分析:")
meaning_a = query_word_meaning(char_a)
meaning_b = query_word_meaning(char_b)
print(f"  {char_a}的本义: {meaning_a['本义']}")
print(f"  {char_b}的本义: {meaning_b['本义']}")
print(f"  语义关系: {'义近' if meaning_a['本义'] != '未收录' and meaning_b['本义'] != '未收录' else '未知'}")

# 步骤2: 文献检索
print("\n[2] 文献检索:")
evidence = search_textual_evidence(char_a, char_b, context)
print(f"  有佐证: {evidence['有佐证']}")
if evidence['假借记录']:
    print(f"  假借记录: {len(evidence['假借记录'])}条")
    print(f"  第一条: {evidence['假借记录'][0]['text']}")

# 步骤3: 训式识别
print("\n[3] 训式识别:")
pattern = identify_pattern(xungu_sentence)
print(f"  格式: {pattern['格式']}")
print(f"  暗示类型: {pattern['暗示类型']}")
print(f"  置信度: {pattern['置信度']}")
print(f"  可直接判定: {pattern['可直接判定']}")

# 综合判断
print("\n[4] 综合判断:")
if pattern['可直接判定']:
    if pattern['暗示类型'] == '假借':
        print("  → 判断为: 假借说明")
    elif pattern['暗示类型'] == '语义解释':
        print("  → 判断为: 语义解释")
else:
    print("  → 需要结合其他信息综合判断")
```

### 批量处理测试集

```python
from src.evaluation import load_test_dataset
from src.tools import query_word_meaning, search_textual_evidence, identify_pattern

# 加载测试集
dataset = load_test_dataset("data/test/test_dataset.json")

# 分析每个测试用例
for case in dataset:
    print(f"\n{'='*60}")
    print(f"ID: {case.id}")
    print(f"训诂句: {case.xungu_sentence}")
    print(f"期望: {case.expected_label}")
    
    # 使用三个工具分析
    meaning_a = query_word_meaning(case.char_a)
    meaning_b = query_word_meaning(case.char_b)
    evidence = search_textual_evidence(case.char_a, case.char_b, case.context)
    pattern = identify_pattern(case.xungu_sentence)
    
    print(f"语义: {meaning_a['本义'][:30]}...")
    print(f"佐证: {evidence['有佐证']}")
    print(f"格式: {pattern['格式']}, 类型: {pattern['暗示类型']}")
```

---

## 常见问题

### Q1: 查询返回"未收录"怎么办？

**原因**：
1. 索引文件不存在（最常见）
2. 使用了简体字，但词典使用繁体字索引

**解决方法**：
```python
# 1. 检查索引文件是否存在
from src.config import get_settings
settings = get_settings()
index_path = settings.data_processed_dir / "dyhdc_index.json"
print(f"索引文件存在: {index_path.exists()}")

# 2. 如果不存在，构建索引
if not index_path.exists():
    from src.data.dyhdc_index_builder import build_dyhdc_index
    build_dyhdc_index()

# 3. 使用繁体字查询
result = query_word_meaning("終")  # 使用繁体
```

### Q2: 索引文件构建失败？

**可能原因**：
1. JSONL文件路径不正确
2. 磁盘空间不足
3. 文件权限问题

**解决方法**：
```python
# 检查JSONL文件
from src.config import get_settings
settings = get_settings()
jsonl_path = settings.dyhdc_path
print(f"JSONL文件: {jsonl_path}")
print(f"存在: {jsonl_path.exists() if jsonl_path else False}")

# 手动指定路径构建
from src.data.dyhdc_index_builder import DYHDCIndexBuilder
builder = DYHDCIndexBuilder("《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl")
builder.build_index("data/processed/dyhdc_index.json")
```

### Q3: 如何给其他成员提供接口？

**方式1：直接导入函数（推荐）**

```python
# 在Agent或其他模块中
from src.tools import (
    query_word_meaning,      # 语义查询
    search_textual_evidence, # 文献检索
    identify_pattern         # 训式识别
)

# 直接使用
result = query_word_meaning("崇")
```

**方式2：使用类接口**

```python
from src.tools import SemanticTool, TextualTool, PatternTool

semantic = SemanticTool()
textual = TextualTool()
pattern = PatternTool()

# 使用
meaning = semantic.query("崇")
evidence = textual.search("崇", "終")
pattern_result = pattern.identify("崇，終也")
```

**方式3：在Agent中集成**

```python
# 在 xungu_agent.py 中
from src.tools import SemanticTool, TextualTool, PatternTool

class XunguAgent:
    def __init__(self):
        self.semantic_tool = SemanticTool()
        self.textual_tool = TextualTool()
        self.pattern_tool = PatternTool()
    
    def analyze(self, sentence, char_a, char_b, context=None):
        # 步骤1: 语义分析
        meaning_a = self.semantic_tool.query(char_a)
        meaning_b = self.semantic_tool.query(char_b)
        
        # 步骤2: 文献检索
        evidence = self.textual_tool.search(char_a, char_b, context)
        
        # 步骤3: 训式识别
        pattern = self.pattern_tool.identify(sentence)
        
        return {
            "semantic": {"a": meaning_a, "b": meaning_b},
            "evidence": evidence,
            "pattern": pattern
        }
```

### Q4: 性能优化建议

1. **单例模式**：工具类已实现单例，多次调用不会重复加载索引
2. **批量查询**：如果需要查询多个字，可以复用同一个工具实例
3. **索引缓存**：索引文件只需构建一次，后续直接使用

```python
# 好的做法：复用工具实例
tool = SemanticTool()
results = [tool.query(char) for char in ["崇", "終", "海", "晦"]]

# 避免：每次都创建新实例（虽然单例模式已处理，但显式复用更清晰）
```

---

## 📞 技术支持

如有问题，请：
1. 检查索引文件是否存在
2. 查看错误信息
3. 参考本文档的常见问题部分
4. 联系成员C或成员E

---

*最后更新：2026-01-17*

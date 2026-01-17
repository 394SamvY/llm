# 工具层快速参考

> 给其他成员（成员B/D）的快速使用指南

---

## 🚀 快速开始（3步）

### 步骤1：构建索引（必须！）

```bash
# 方法1: 使用便捷脚本
python check_and_build_index.py

# 方法2: 直接运行
python -c "from src.data.dyhdc_index_builder import build_dyhdc_index; build_dyhdc_index()"
```

**输出**：`data/processed/dyhdc_index.json`（约24.5MB，只需构建一次）

### 步骤2：导入工具

```python
from src.tools import (
    query_word_meaning,      # 语义查询
    search_textual_evidence, # 文献检索
    identify_pattern         # 训式识别
)
```

### 步骤3：使用

```python
# 语义查询
result = query_word_meaning("崇")
print(result["本义"])  # "高；高大。"

# 文献检索
evidence = search_textual_evidence("崇", "終", context="崇朝其雨")
print(evidence["有佐证"])  # True

# 训式识别
pattern = identify_pattern("崇，讀為終")
print(pattern["暗示类型"])  # "假借"
```

---

## 📖 三个工具详解

### 1. 语义查询 (query_word_meaning)

**功能**：查询汉字的本义、义项、例句、假借标注

```python
result = query_word_meaning("崇")

# 返回字段
result["字"]          # "崇"
result["本义"]        # "高；高大。"
result["义项"]        # ["高；高大。", "尊崇", ...]
result["例句"]        # [{"quote": "..."}, ...]
result["假借标注"]    # ["12通"終"。终尽。参见"崇朝"。"]
```

**注意**：使用繁体字查询（"終"而不是"终"）

---

### 2. 文献检索 (search_textual_evidence)

**功能**：检索两个字之间的文献佐证

```python
evidence = search_textual_evidence(
    char_a="崇",      # 被释字
    char_b="終",      # 释字
    context="崇朝其雨"  # 上下文（可选）
)

# 返回字段
evidence["有佐证"]      # True/False
evidence["假借记录"]    # [{"type": "jiajie", "text": "...", ...}, ...]
evidence["异文"]        # [{"type": "variant", "text": "...", ...}, ...]
evidence["总结"]        # "找到2处假借记录"
```

---

### 3. 训式识别 (identify_pattern)

**功能**：识别训诂句格式，判断暗示类型

```python
pattern = identify_pattern("崇，讀為終")

# 返回字段
pattern["格式"]          # "读为"
pattern["被释字"]        # "崇"
pattern["释字"]          # "終"
pattern["暗示类型"]      # "假借" / "语义解释" / "以声通义" / "不确定"
pattern["置信度"]        # "高" / "中" / "低"
pattern["可直接判定"]    # True/False
pattern["说明"]          # "郑玄《礼》注，破字/改读术语"
```

**支持的训式**：
- **假借类**：`读为`、`读曰`、`通`、`假借字`等 → `暗示类型: "假借"`
- **语义类**：`犹也`、`谓之`、`之貌`等 → `暗示类型: "语义解释"`
- **以声通义**：`之言`、`之为言` → `暗示类型: "以声通义"`
- **不确定**：`A也`、`者也`等 → `暗示类型: "不确定"`

---

## 💡 在Agent中使用

### 示例：五步分析流程

```python
from src.tools import (
    query_word_meaning,
    search_textual_evidence,
    identify_pattern
)

def analyze_xungu(sentence, char_a, char_b, context=None):
    """分析训诂句"""
    
    # 步骤1: 语义分析
    meaning_a = query_word_meaning(char_a)
    meaning_b = query_word_meaning(char_b)
    
    # 步骤2: 音韵分析（需要成员D的工具）
    # phonology_result = query_phonology(char_a, char_b)
    
    # 步骤3: 文献检索
    evidence = search_textual_evidence(char_a, char_b, context)
    
    # 步骤4: 训式识别
    pattern = identify_pattern(sentence)
    
    # 步骤5: 语境分析（需要成员D的工具）
    # context_result = analyze_context(sentence, context)
    
    # 综合判断
    if pattern["可直接判定"]:
        if pattern["暗示类型"] == "假借":
            return "假借说明"
        elif pattern["暗示类型"] == "语义解释":
            return "语义解释"
    
    # 需要综合判断...
    return "不确定"
```

---

## ⚠️ 常见问题

### Q: 查询返回"未收录"？

**原因**：索引文件不存在或使用了简体字

**解决**：
1. 检查索引文件：`data/processed/dyhdc_index.json` 是否存在
2. 如果不存在，运行构建命令
3. 使用繁体字查询：`query_word_meaning("終")` 而不是 `query_word_meaning("终")`

### Q: 如何检查索引文件是否存在？

```python
from pathlib import Path
from src.config import get_settings

settings = get_settings()
index_path = settings.data_processed_dir / "dyhdc_index.json"
print(f"索引文件存在: {index_path.exists()}")
```

### Q: 索引文件在哪里？

- **路径**：`data/processed/dyhdc_index.json`
- **大小**：约24.5MB
- **构建时间**：1-3分钟（只需一次）

---

## 📚 完整文档

详细文档请参考：`docs/TOOLS_API.md`

---

*最后更新：2026-01-17*

# 成员E - 数据工程接口文档

> **负责人**: 成员E  
> **完成日期**: 2026-01-17  
> **状态**: ✅ 全部完成并测试通过

---

## 📁 文件位置总览

```
llm25/
├── data/
│   ├── processed/
│   │   ├── phonology_unified.json    # 音韵数据索引 (13,666字)
│   │   └── dyhdc_index.json          # 词典偏移量索引 (24.5MB)
│   └── test/
│       └── test_dataset.json         # 测试数据集 (60条)
│
└── src/
    ├── data/
    │   ├── __init__.py
    │   ├── phonology_parser.py       # 音韵数据解析器
    │   └── dyhdc_index_builder.py    # 词典索引构建器
    └── evaluation/
        ├── __init__.py
        ├── metrics.py                # 评估指标计算
        ├── test_dataset.py           # 测试数据集类
        └── error_analysis.py         # 错误分析模块
```

---

## 🎯 接口1: 音韵数据查询 (给成员D - 音韵工具开发)

### 任务内容
提供上古音韵数据的查询和比较功能，支持判断两字是否"音近"。

### 数据来源
- 潘悟云《汉语古音手册》: 13,445 字
- 白一平-沙加尔上古音: 4,056 字
- 整合后共: **13,666** 个字

### 使用方式

```python
from src.data import load_phonology_data, compare_phonology

# 1. 加载音韵数据
phonology_data = load_phonology_data("data/processed/phonology_unified.json")

# 2. 查询单个字的音韵信息
char_info = phonology_data.get("崇")
# 返回:
# {
#     "字": "崇",
#     "潘悟云": {
#         "韵部": "終",
#         "上古音": "*dzruŋ",
#         "声母": "崇",
#         "韵": "鍾",
#         "声调": "平"
#     },
#     "白一平沙加尔": {
#         "上古音": "*[dz]<r>uŋ",
#         "中古音": "dzywng",
#         "释义": "high; lofty"
#     }
# }

# 3. 比较两字的音韵关系
result = compare_phonology("海", "晦", phonology_data)
# 返回:
# {
#     "char_a": "海",
#     "char_b": "晦",
#     "found_a": True,
#     "found_b": True,
#     "音近": True,           # 综合判断结果
#     "韵部相同": True,       # 韵部是否相同
#     "声母相近": True,       # 声母是否相近
#     "详情": {
#         "潘悟云": {
#             "韵部_A": "之", "韵部_B": "之",
#             "声母_A": "曉", "声母_B": "曉",
#             "上古音_A": "m̥ʰɯ̠ʔ", "上古音_B": "m̥ʰɯ̠s"
#         }
#     }
# }
```

### ⚠️ 注意事项
1. **繁简体问题**: 音韵数据使用繁体字索引，如查"终"需用"終"
2. **缺失数据**: 若字不在数据库中，`found_a/found_b`会返回`False`
3. **音近判断**: 韵部相同或声母相近，则综合判断为"音近"

---

## 🎯 接口2: 词典语义查询 (给成员C - 语义工具开发)

### 任务内容
提供《汉语大词典》的快速查询功能，支持查询字的本义、义项、假借标注等。

### 数据规模
- 词条总数: 408,931 条
- 首字数: 27,678 个
- 索引大小: 24.5 MB

### 使用方式

```python
from src.data import DYHDCIndexLoader

# 1. 初始化加载器
loader = DYHDCIndexLoader(
    jsonl_path="《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl",
    index_path="data/processed/dyhdc_index.json"
)

# 2. 查询单个字的语义信息
result = loader.query_single_char("崇")
# 返回:
# {
#     "字": "崇",
#     "简体": "",
#     "读音": "chóng",
#     "本义": "1高；高大。",
#     "义项": [
#         "高；高大",
#         "尊崇",
#         "充实",
#         ...
#     ],  # 最多10个义项
#     "例句": [
#         "崇山峻岭",
#         ...
#     ],  # 最多5个例句
#     "假借标注": [
#         "12通"終"。终尽。参见"崇朝"。"
#     ]  # 词典中标注的假借/通假信息
# }
```

### ⚠️ 注意事项
1. **繁体字**: 词典使用繁体字，查"终"需用"終"
2. **首次加载**: 首次查询会加载索引（约1秒）
3. **假借标注**: `假借标注`字段包含词典中"读为"、"通"等假借说明

---

## 🎯 接口3: 测试数据集 (给成员B - Agent开发)

### 任务内容
提供标注好的训诂句测试集，用于评估Agent的分类准确率。

### 数据统计
- 总样本: 60 条
- 假借说明: 17 条 (28.3%)
- 语义解释: 43 条 (71.7%)
- 有上下文: 30 条
- 无上下文: 30 条

### 使用方式

```python
from src.evaluation import load_test_dataset, get_dataset_statistics

# 1. 加载测试数据集
dataset = load_test_dataset("data/test/test_dataset.json")

# 2. 查看数据集统计
stats = get_dataset_statistics(dataset)
# 返回:
# {
#     "total": 60,
#     "label_distribution": {"假借说明": 17, "语义解释": 43},
#     "with_context": 30,
#     "without_context": 30,
#     "source_distribution": {...}
# }

# 3. 遍历测试用例
for case in dataset:
    print(f"ID: {case.id}")
    print(f"训诂句: {case.xungu_sentence}")
    print(f"被释字: {case.beishi_char}")
    print(f"释字: {case.shi_char}")
    print(f"上下文: {case.context}")
    print(f"出处: {case.source}")
    print(f"正确答案: {case.expected_label}")
    print(f"备注: {case.notes}")
```

### 测试用例数据结构 (JSON)

```json
{
    "id": 1,
    "训诂句": "崇，终也",
    "被释字": "崇",
    "释字": "终",
    "上下文": "崇朝其雨",
    "出处": "《诗·邶风·简兮》《毛传》",
    "正确答案": "假借说明",
    "备注": "有异文《小雅·采绿》作'终朝'..."
}
```

### 标签说明
| 标签 | 含义 | 特征 |
|------|------|------|
| `假借说明` | 借字与正字的关系 | 义远音近，有"读为/读曰"等术语 |
| `语义解释` | 通过声音解释语义/语源 | 义近音近，有"之为言"等术语 |

---

## 🎯 接口4: 评估指标计算 (给成员B - Agent开发)

### 任务内容
计算分类任务的各项评估指标，包括准确率、精确率、召回率、F1值、混淆矩阵。

### 使用方式

```python
from src.evaluation import (
    calculate_metrics,
    build_confusion_matrix,
    print_confusion_matrix,
    evaluate_results,
    print_evaluation_report
)

# 方式1: 直接计算指标
predictions = ["假借说明", "语义解释", "语义解释", ...]
labels = ["假借说明", "假借说明", "语义解释", ...]

metrics = calculate_metrics(predictions, labels)
# 返回:
# {
#     "accuracy": 0.833,           # 准确率
#     "correct": 5,                # 正确数
#     "total": 6,                  # 总数
#     "precision_假借": 0.667,     # 假借精确率
#     "recall_假借": 1.0,          # 假借召回率
#     "f1_假借": 0.8,              # 假借F1
#     "precision_语义": 1.0,       # 语义精确率
#     "recall_语义": 0.75,         # 语义召回率
#     "f1_语义": 0.857,            # 语义F1
#     "macro_f1": 0.829            # 宏平均F1
# }

# 方式2: 生成混淆矩阵
cm = build_confusion_matrix(predictions, labels)
print_confusion_matrix(cm)
# 输出:
# 混淆矩阵:
#              │   假借说明   │   语义解释   │
# ------------------------------------------------
#  假借说明    │      2      │      0      │
#  语义解释    │      1      │      3      │

# 方式3: 完整评估Agent结果
agent_results = [
    {
        "classification": "假借说明",
        "final_reasoning": "...",
        "step1": {...},  # 五步分析结果
        ...
    },
    ...
]

report = evaluate_results(agent_results, dataset)
print_evaluation_report(report)
```

---

## 🎯 接口5: 错误分析 (给成员B - Agent开发)

### 任务内容
分析Agent的错误案例，找出错误模式和改进建议。

### 使用方式

```python
from src.evaluation import ErrorAnalyzer, save_error_report

# 1. 创建分析器
analyzer = ErrorAnalyzer()

# 2. 添加错误案例 (从evaluate_results的report["errors"]获取)
analyzer.add_errors(report["errors"])

# 3. 执行分析
analysis = analyzer.analyze_all()
# 返回:
# {
#     "total_errors": 3,
#     "error_type_distribution": {
#         "假借误判为语义": 2,
#         "语义误判为假借": 1
#     },
#     "step_error_analysis": {
#         "step_issues": {"step1_语义误判": 2, ...},
#         "most_problematic_step": "step1"
#     },
#     "pattern_analysis": [...],
#     "suggestions": [...]
# }

# 4. 打印报告
analyzer.print_report()

# 5. 保存报告
report = analyzer.generate_report()
save_error_report(report, "data/processed/error_analysis.json")
```

### 错误模式类型
| 模式 | 描述 |
|------|------|
| `假借术语未识别` | 含"读为/读曰"等术语但未判断为假借 |
| `语义相近假借误判` | 表面语义相近的假借被误判为语义解释 |
| `音韵数据缺失` | 字的音韵数据缺失导致判断不准 |
| `缺少语境信息` | 无上下文影响判断准确性 |

---

## 📋 Agent输出格式建议 (给成员A - 架构设计)

建议Agent的分析结果采用以下统一格式，便于评估和错误分析：

```python
{
    "classification": "假借说明" | "语义解释",
    "confidence": 0.0 - 1.0,
    "final_reasoning": "综合判断理由...",
    
    # 五步分析结果
    "step1": {  # 语义分析
        "relation": "义近" | "义远",
        "confidence": 0.8,
        "meaning_a": "高大",
        "meaning_b": "终结",
        "reasoning": "..."
    },
    "step2": {  # 音韵分析
        "relation": "音近" | "音远",
        "韵部相同": True,
        "声母相近": False,
        "confidence": 0.9
    },
    "step3": {  # 异文/文例佐证
        "has_evidence": True,
        "evidence": "《小雅·采绿》作'终朝'"
    },
    "step4": {  # 术语/训式分析
        "matched_pattern": "A也" | "读为" | "之为言" | ...,
        "direct_judge": True | False,
        "implied_type": "假借说明" | "语义解释" | "不确定"
    },
    "step5": {  # 语境分析
        "conclusion": "支持假借" | "支持语义" | "不确定",
        "beishi_fit": False,
        "shi_fit": True,
        "reasoning": "..."
    }
}
```

---

## 🔧 快速开始示例

```python
"""完整使用示例"""
from src.data import load_phonology_data, compare_phonology, DYHDCIndexLoader
from src.evaluation import load_test_dataset, evaluate_results, print_evaluation_report

# 1. 加载所有数据
phonology = load_phonology_data("data/processed/phonology_unified.json")
dict_loader = DYHDCIndexLoader(
    "《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl",
    "data/processed/dyhdc_index.json"
)
test_dataset = load_test_dataset("data/test/test_dataset.json")

# 2. 使用数据 (示例: 分析"崇，终也")
beishi, shi = "崇", "終"

# 查音韵
phonetic_result = compare_phonology(beishi, shi, phonology)
print(f"音近: {phonetic_result['音近']}")

# 查语义
semantic_a = dict_loader.query_single_char(beishi)
semantic_b = dict_loader.query_single_char(shi)
print(f"崇的本义: {semantic_a['本义']}")
print(f"終的本义: {semantic_b['本义']}")
print(f"假借标注: {semantic_a.get('假借标注', [])}")

# 3. 评估Agent (假设有agent_results)
# report = evaluate_results(agent_results, test_dataset)
# print_evaluation_report(report)
```

---

## 📞 联系方式

如有接口使用问题，请联系成员E。

# 🏗️ 系统架构设计

> 本文档详细说明系统的整体架构、模块划分和数据流

---

## 📊 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                用户接口层                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   CLI 命令行    │  │   Python API    │  │   Web UI (可选)  │             │
│  │  python -m src  │  │  agent.analyze() │  │   Gradio/Flask  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Agent 核心层                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        XunguAgent                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   预处理器   │  │   推理引擎   │  │   结果整合   │              │   │
│  │  │ Preprocessor │  │   Reasoner   │  │   Integrator │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                          │                                           │   │
│  │                    ┌─────┴─────┐                                     │   │
│  │                    │   LLM     │   ← Claude/GPT-4                    │   │
│  │                    │  (可选)   │                                     │   │
│  │                    └───────────┘                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                             工具调用接口                                     │
│                                    │                                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐                  │
│  │Step1工具 │Step2工具 │Step3工具 │Step4工具 │Step5工具 │                  │
│  │ Semantic │ Phonology│ Textual  │ Pattern  │ Context  │                  │
│  │   Tool   │   Tool   │   Tool   │   Tool   │   Tool   │                  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              知识库层                                        │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │
│  │   《汉语大词典》     │  │     上古音数据       │  │   训式规则库       │  │
│  │ dyhdc.parsed.*.jsonl│  │  潘悟云/白沙系统     │  │  XUNSHI_PATTERNS   │  │
│  │       1.9GB         │  │      TXT/XLSX       │  │       Python       │  │
│  └─────────────────────┘  └─────────────────────┘  └────────────────────┘  │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │
│  │  《王力古汉语字典》  │  │     测试数据集       │  │    参考资料库      │  │
│  │     MDX (可选)      │  │       JSON          │  │       TXT          │  │
│  └─────────────────────┘  └─────────────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              输出层                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  {                                                                   │   │
│  │    "classification": "假借说明",                                     │   │
│  │    "confidence": 0.95,                                               │   │
│  │    "reasoning": {                                                    │   │
│  │      "step1": {...}, "step2": {...}, "step3": {...},                │   │
│  │      "step4": {...}, "step5": {...}                                  │   │
│  │    },                                                                │   │
│  │    "final_judgment": "义远+音近+有异文+语境支持假借"                 │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
src/
├── __init__.py
├── main.py                      # 主入口
│
├── agent/                       # Agent 核心
│   ├── __init__.py
│   ├── xungu_agent.py          # 主Agent类
│   └── prompts.py              # LLM Prompt 模板
│
├── tools/                       # 工具函数（五步推理）
│   ├── __init__.py
│   ├── semantic_tool.py        # Step1: 语义分析
│   ├── phonology_tool.py       # Step2: 语音分析
│   ├── textual_tool.py         # Step3: 异文检索
│   ├── pattern_tool.py         # Step4: 训式识别 ✅
│   └── context_tool.py         # Step5: 语境分析
│
├── knowledge/                   # 知识库管理
│   ├── __init__.py
│   ├── dictionary_loader.py    # 字典数据加载
│   └── phonology_loader.py     # 音韵数据加载
│
├── evaluation/                  # 评估模块
│   ├── __init__.py
│   ├── test_dataset.py         # 测试数据集
│   └── metrics.py              # 评估指标
│
├── config/                      # 配置
│   ├── __init__.py
│   └── settings.py             # 全局设置
│
└── data/                        # 数据处理
    └── __init__.py
```

---

## 🔄 数据流

### 单次分析流程

```
输入: "崇，终也"
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 预处理 (Preprocessor)                                     │
│    - 解析训诂句格式                                          │
│    - 提取被释字(崇)和释字(终)                                │
│    - 标准化输入                                              │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Step 1: 语义分析                                          │
│    - 调用 semantic_tool.query_meaning("崇")                  │
│    - 调用 semantic_tool.query_meaning("终")                  │
│    - 判断: 义近/义远                                         │
│    → 结果: 义远                                              │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Step 2: 语音分析                                          │
│    - 调用 phonology_tool.query_phonology("崇")               │
│    - 调用 phonology_tool.query_phonology("终")               │
│    - 比较声母、韵部                                          │
│    → 结果: 音近 (东部)                                       │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Step 3: 异文检索                                          │
│    - 调用 textual_tool.search_evidence("崇", "终")           │
│    - 查找异文、假借标注                                      │
│    → 结果: 有佐证 (《小雅》异文)                             │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Step 4: 训式识别                                          │
│    - 调用 pattern_tool.identify_pattern("崇，终也")          │
│    - 正则匹配训释格式                                        │
│    → 结果: "A也" 格式，置信度低，需综合判断                  │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Step 5: 语境分析                                          │
│    - 获取原文语境 "崇朝其雨"                                 │
│    - 崇(高大)代入 → 不通                                     │
│    - 终(整个)代入 → 通顺                                     │
│    → 结果: 支持假借                                          │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. 综合判定 (Integrator)                                     │
│    - 义远 + 音近 + 有异文 + 语境支持假借                     │
│    - 应用判定规则                                            │
│    → 最终: 假借说明 (置信度: 0.95)                           │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
输出: { classification: "假借说明", confidence: 0.95, ... }
```

---

## 🧩 核心模块详解

### 1. XunguAgent (agent/xungu_agent.py)

主Agent类，协调整个分析流程：

```python
class XunguAgent:
    """训诂分类智能体"""
    
    def __init__(self, config=None):
        self.config = config or {}
        # 初始化工具
        self.semantic_tool = SemanticTool()
        self.phonology_tool = PhonologyTool()
        self.textual_tool = TextualTool()
        self.pattern_tool = PatternTool()
        self.context_tool = ContextTool()
    
    def analyze(self, xungu_sentence: str, context: str = None) -> dict:
        """执行完整的五步分析"""
        # 1. 预处理
        beishi, shi = self._preprocess(xungu_sentence)
        
        # 2. 五步推理
        step1 = self._step1_semantic(beishi, shi)
        step2 = self._step2_phonetic(beishi, shi)
        step3 = self._step3_textual(beishi, shi)
        step4 = self._step4_pattern(xungu_sentence)
        step5 = self._step5_context(beishi, shi, context)
        
        # 3. 综合判定
        result = self._integrate(step1, step2, step3, step4, step5)
        
        return result
```

### 2. 工具模块 (tools/)

每个工具负责一个步骤的判断：

| 工具 | 文件 | 输入 | 输出 |
|------|------|------|------|
| SemanticTool | semantic_tool.py | 字符 | 本义、义项列表 |
| PhonologyTool | phonology_tool.py | 字符 | 声母、韵部、拟音 |
| TextualTool | textual_tool.py | 字符对 | 异文、假借标注 |
| PatternTool | pattern_tool.py | 训诂句 | 格式、类型、置信度 |
| ContextTool | context_tool.py | 字符+语境 | 适配度判断 |

### 3. 知识库模块 (knowledge/)

负责加载和查询各类数据：

```python
# dictionary_loader.py
class DictionaryLoader:
    def __init__(self, jsonl_path: str):
        self.data = self._load_jsonl(jsonl_path)
        self.index = self._build_index()
    
    def query(self, char: str) -> dict:
        """查询单字的所有义项"""
        return self.index.get(char, {})

# phonology_loader.py  
class PhonologyLoader:
    def __init__(self, data_dir: str):
        self.data = self._load_all_sources(data_dir)
    
    def query(self, char: str) -> dict:
        """查询单字的上古音"""
        return {
            "声母": ...,
            "韵部": ...,
            "拟音": ...
        }
```

### 4. 评估模块 (evaluation/)

负责测试和评估：

```python
# test_dataset.py
class TestDataset:
    def __init__(self):
        self.cases = self._load_cases()
    
    def __iter__(self):
        for case in self.cases:
            yield case

# metrics.py
def calculate_metrics(predictions, labels):
    return {
        "accuracy": ...,
        "precision_假借": ...,
        "recall_假借": ...,
        "f1_假借": ...,
        "precision_语义": ...,
        "recall_语义": ...,
        "f1_语义": ...,
        "macro_f1": ...
    }
```

---

## 🔌 接口定义

### 工具函数接口

每个工具都应实现统一的接口：

```python
class BaseTool:
    """工具基类"""
    
    def __init__(self, config: dict = None):
        """初始化工具"""
        pass
    
    def execute(self, *args, **kwargs) -> dict:
        """执行工具功能，返回结构化结果"""
        raise NotImplementedError
```

### SemanticTool 接口

```python
class SemanticTool(BaseTool):
    def query_meaning(self, char: str) -> dict:
        """
        查询字的语义信息
        
        Returns:
            {
                "char": "崇",
                "found": True,
                "meanings": [
                    {"义项": "高大", "type": "本义"},
                    {"义项": "尊崇", "type": "引申义"},
                    ...
                ],
                "primary_meaning": "高大"
            }
        """
        pass
    
    def compare_semantics(self, char_a: str, char_b: str) -> dict:
        """
        比较两字语义关联性
        
        Returns:
            {
                "char_a": "崇",
                "char_b": "终",
                "meaning_a": "高大",
                "meaning_b": "终结",
                "relation": "义远",  # 义近/义远
                "confidence": 0.9,
                "reasoning": "高大与终结无语义关联链条"
            }
        """
        pass
```

### PhonologyTool 接口

```python
class PhonologyTool(BaseTool):
    def query_phonology(self, char: str) -> dict:
        """
        查询字的上古音
        
        Returns:
            {
                "char": "崇",
                "found": True,
                "声母": "禅",
                "韵部": "东",
                "拟音": "*dzruŋ",
                "source": "潘悟云《汉语古音手册》"
            }
        """
        pass
    
    def compare_phonology(self, char_a: str, char_b: str) -> dict:
        """
        比较两字语音关系
        
        Returns:
            {
                "char_a": "崇",
                "char_b": "终",
                "relation": "音近",  # 音近/音远
                "details": {
                    "韵部": "相同（东部）",
                    "声母": "不同但相近（禅/章）"
                },
                "confidence": 0.85
            }
        """
        pass
```

### PatternTool 接口

```python
class PatternTool(BaseTool):
    def identify_pattern(self, sentence: str) -> dict:
        """
        识别训诂句的训式格式
        
        Returns:
            {
                "sentence": "崇，终也",
                "matched_pattern": "A也",
                "implied_type": "不确定",  # 假借/语义/不确定
                "direct_judge": False,
                "confidence": "低",  # 高/中/低
                "source": "基本训式，需综合判断"
            }
        """
        pass
```

### ContextTool 接口

```python
class ContextTool(BaseTool):
    def analyze_context(
        self, 
        beishi: str, 
        shi: str, 
        context: str,
        meaning_beishi: str = None,
        meaning_shi: str = None
    ) -> dict:
        """
        分析语境适配度
        
        Returns:
            {
                "beishi": "崇",
                "shi": "终",
                "context": "崇朝其雨",
                "analysis": {
                    "beishi_fit": False,  # 被释字本义是否通顺
                    "shi_fit": True,      # 释字本义是否通顺
                    "beishi_substituted": "高大早晨下雨",
                    "shi_substituted": "整个早晨下雨"
                },
                "conclusion": "支持假借",  # 支持假借/支持语义/不确定
                "reasoning": "借字本义不通，正字本义通顺"
            }
        """
        pass
```

---

## 🗃️ 数据格式

### 《汉语大词典》JSONL 格式

```json
{
    "headword": "崇",
    "pronunciations": [...],
    "senses": [
        {
            "sense_num": "1",
            "definition": "高大。",
            "examples": [...]
        }
    ],
    "cross_refs": [...]
}
```

详见 `《汉语大词典》结构化/dyhdc_jsonl_schema_zh.md`

### 上古音数据格式

潘悟云《汉语古音手册》TXT格式：
```
字	聲母	韻部	拟音
崇	禅	东	*dzruŋ
终	章	东	*tuŋ
```

### 测试数据集格式

```json
{
    "id": "test_001",
    "xungu_sentence": "崇，终也",
    "beishi_char": "崇",
    "shi_char": "终",
    "source": "《诗·邶风·简兮》毛传",
    "context": "崇朝其雨",
    "expected_label": "假借说明",
    "explanation": "义远音近，有异文佐证"
}
```

---

## 🔧 配置说明

### 环境变量 (.env)

```bash
# LLM API 配置
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=xxx

# 模型选择
LLM_PROVIDER=anthropic  # openai / anthropic
LLM_MODEL=claude-3-5-sonnet-20241022

# 数据路径
DYHDC_PATH=./《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl
PHONOLOGY_PATH=./音韵数据/上古音/

# 日志级别
LOG_LEVEL=INFO
```

### settings.py

```python
class Settings:
    # 路径配置
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_ROOT = PROJECT_ROOT / "data"
    
    # 模型配置
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
    LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    
    # 工具配置
    USE_MOCK_DATA = True  # 是否使用模拟数据
    
    # 评估配置
    TEST_DATA_PATH = DATA_ROOT / "test" / "test_dataset.json"
```

---

## 📦 数据资源利用方案

### MDX资源处理策略

项目涉及多种MDX格式的古汉语词典资源：
- 《王力古汉语字典》（5.5MB）
- 上古音MDX数据

**采用的方案：预处理+索引**

```
原始资源                    预处理                      运行时检索
────────────────────────────────────────────────────────────────────
《汉语大词典》JSONL ──────→ dyhdc_index.json ────────→ 偏移量快速定位
      (1.9GB)                (27,678首字)               O(1)查询

潘悟云TXT/白一平XLSX ─────→ phonology_unified.json ──→ 字典直接查询
     (多文件)                (13,666字)                 O(1)查询
```

**为什么不直接解析MDX？**

1. **性能考虑**：MDX是压缩格式，每次查询都解压效率低
2. **已有替代**：《汉语大词典》已有JSONL格式，数据更完整
3. **简化依赖**：避免引入MDX解析库的兼容性问题

**MDX可扩展方案**：

如需支持MDX直接查询，可安装 `readmdict` 库并实现 `src/data/mdx_parser.py`：

```python
# 预留接口
from readmdict import MDX
def query_mdx(mdx_path: str, keyword: str) -> str:
    mdx = MDX(mdx_path)
    return mdx.lookup(keyword)
```

---

## 🔍 检索架构设计

### 精确索引 vs 向量检索

本系统采用**基于索引的精确检索**而非向量检索：

| 特性 | 精确索引（本项目） | 向量检索 |
|------|-------------------|----------|
| 查询方式 | 字→偏移量→条目 | 语义相似度匹配 |
| 适用场景 | 单字/词精确查询 | 模糊语义检索 |
| 查询速度 | O(1)，毫秒级 | 较慢，需计算相似度 |
| 资源占用 | 索引文件~50MB | 需要向量数据库 |
| 准确性 | 100%精确 | 可能有误差 |

**选择精确索引的理由：**

1. **场景适配**：训诂分析是单字查询，不需要语义搜索
2. **性能优先**：1.9GB词典通过索引实现毫秒级查询
3. **简化部署**：无需额外的向量数据库服务

### 索引结构

```json
// dyhdc_index.json 结构
{
  "stats": {
    "total_chars": 27678,
    "total_entries": 408931
  },
  "index": {
    "崇": [
      {"headword": "崇", "offset": 12345, "length": 2048},
      {"headword": "崇拜", "offset": 14393, "length": 1024}
    ],
    "终": [...]
  }
}
```

### 向量检索扩展（预留）

如需支持语义检索，可引入 ChromaDB：

```python
# 预留接口 - src/knowledge/vector_store.py
import chromadb

class VectorStore:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("xungu")
    
    def search(self, query: str, top_k: int = 5):
        """语义检索相关训诂案例"""
        return self.collection.query(query_texts=[query], n_results=top_k)
```

---

## 📊 系统性能评估

### 评估结果摘要

| 指标 | 数值 |
|------|------|
| 测试数据集 | 60条 |
| **准确率** | **86.67%** |
| **宏平均F1** | **84.60%** |
| 假借说明F1 | 78.95% |
| 语义解释F1 | 90.24% |

### 资源覆盖率

| 资源 | 条目数 | 覆盖率 |
|------|--------|--------|
| 《汉语大词典》索引 | 408,931条 | >99%字覆盖 |
| 音韵数据 | 13,666字 | >95%常用字 |
| 训式规则 | 25+种模式 | 覆盖主要训式 |

详细评估报告见 [EVALUATION_REPORT.md](EVALUATION_REPORT.md)

---

## 🔗 相关文档

- [快速开始](QUICK_START.md)
- [评估报告](EVALUATION_REPORT.md)
- [任务要求](TASK_REQUIREMENTS.md)
- [实现指南](IMPLEMENTATION_GUIDE.md)
- [开发计划](DEVELOPMENT_PLAN.md)

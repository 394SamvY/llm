# API 文档

> 训诂句类型智能判断系统 - 完整接口文档

本文档列出了 `src/data/`、`src/evaluation/`、`src/knowledge/`、`src/tools/` 四个模块中所有可用的接口。

---

## 目录

- [Agent 核心模块 (agent/)](#agent-核心模块-agent)
- [数据处理模块 (data/)](#数据处理模块-data)
- [评估模块 (evaluation/)](#评估模块-evaluation)
- [知识库模块 (knowledge/)](#知识库模块-knowledge)
- [工具模块 (tools/)](#工具模块-tools)

---

## Agent 核心模块 (agent/)

### `xungu_agent.py`

#### `AnalysisResult`

**功能**: 分析结果数据类

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `xungu_sentence` | str | 训诂句，如"崇，终也" |
| `char_a` | str | 被释字 |
| `char_b` | str | 释字 |
| `context` | Optional[str] | 上下文，如"崇朝其雨" |
| `source` | Optional[str] | 出处，如"《毛传》" |
| `classification` | str | 分类结果："假借说明" 或 "语义解释" |
| `confidence` | float | 置信度 (0.0-1.0) |
| `step1_semantic` | Dict | 第一步：语义查询结果 |
| `step2_phonetic` | Dict | 第二步：音韵查询结果 |
| `step3_textual` | Dict | 第三步：文献检索结果 |
| `step4_pattern` | Dict | 第四步：训式识别结果 |
| `step5_context` | Dict | 第五步：语境分析结果 |
| `final_reasoning` | str | 最终推理说明 |

**方法**:

##### `to_dict() -> Dict`

转换为字典格式

**返回**: `Dict` - 包含所有字段的字典

**示例**:
```python
result_dict = analysis_result.to_dict()
```

##### `to_json(indent: int = 2) -> str`

转换为JSON字符串

**参数**:
- `indent` (int): JSON缩进空格数

**返回**: `str` - JSON格式字符串

**示例**:
```python
json_str = analysis_result.to_json()
print(json_str)
```

---

#### `XunguAgent`

**功能**: 基于LangChain的训诂分类Agent核心类

**方法**:

##### `__init__(llm_provider: Optional[str] = None, verbose: bool = True, max_iterations: int = 15, max_execution_time: Optional[int] = None) -> None`

初始化Agent

**参数**:
- `llm_provider` (str, optional): LLM提供商，"openai" 或 "anthropic"，默认从配置自动选择
- `verbose` (bool): 是否输出详细日志，默认 True
- `max_iterations` (int): 最大迭代次数（工具调用次数），默认 15
- `max_execution_time` (int, optional): 最大执行时间（秒），默认无限制

**示例**:
```python
from src.agent import XunguAgent

# 使用默认配置
agent = XunguAgent(verbose=True)

# 指定提供商
agent = XunguAgent(llm_provider="openai", verbose=True)

# 设置时间限制
agent = XunguAgent(max_execution_time=60)
```

---

##### `analyze(xungu_sentence: str, context: Optional[str] = None, source: Optional[str] = None) -> AnalysisResult`

分析训诂句，执行完整的五步推理流程

**参数**:
- `xungu_sentence` (str): 训诂句，如 "崇，终也"
- `context` (str, optional): 上下文，如 "崇朝其雨"
- `source` (str, optional): 出处，如 "《毛传》"

**返回**: `AnalysisResult` - 完整的分析结果

**五步推理流程**:
1. **语义查询** - 查询被释字和释字的本义，判断义近/义远
2. **音韵查询** - 查询上古音信息，判断音近关系
3. **文献检索** - 检索异文、假借记录等佐证
4. **训式识别** - 识别训诂句的格式，判断直接暗示
5. **语境分析** - 分析语境适配度，判断本义代入后是否通顺

**示例**:
```python
from src.agent import XunguAgent

agent = XunguAgent(verbose=True)

# 基础分析
result = agent.analyze("崇，终也")
print(f"分类: {result.classification}")  # "假借说明"
print(f"置信度: {result.confidence}")    # 0.85

# 带上下文分析
result = agent.analyze(
    xungu_sentence="崇，终也",
    context="崇朝其雨",
    source="《毛传》"
)
print(result.to_json())

# 查看详细推理过程
print(result.step1_semantic)   # 第一步语义分析
print(result.step2_phonetic)   # 第二步音韵分析
print(result.step3_textual)    # 第三步文献分析
print(result.step4_pattern)    # 第四步训式分析
print(result.step5_context)    # 第五步语境分析
```

---

### `llm_client.py`

#### `get_llm(provider: Optional[str] = None) -> Union[ChatOpenAI, ChatAnthropic]`

获取LLM客户端

**参数**:
- `provider` (str, optional): "openai" 或 "anthropic"，默认从配置自动选择

**返回**: LLM客户端实例

**异常**:
- `ValueError`: 如果API Key未设置或provider无效

**支持的LLM**:
- OpenAI GPT-4 系列
- Anthropic Claude 系列

**示例**:
```python
from src.agent.llm_client import get_llm

# 使用默认配置（从env或.env读取）
llm = get_llm()

# 指定OpenAI
llm = get_llm(provider="openai")

# 指定Anthropic
llm = get_llm(provider="anthropic")
```

**环境变量要求**:
- OpenAI: `OPENAI_API_KEY`、`LLM_MODEL`（可选）
- Anthropic: `ANTHROPIC_API_KEY`

---

### `tool_wrappers.py`

#### `get_all_tools() -> List[StructuredTool]`

获取所有包装后的工具列表

**返回**: `List[StructuredTool]` - LangChain格式的工具列表

**包含的工具**:
1. `query_word_meaning` - 语义查询工具
2. `query_phonology` - 音韵查询工具
3. `check_phonetic_relation` - 音韵关系判断工具
4. `search_textual_evidence` - 文献检索工具
5. `identify_pattern` - 训式识别工具
6. `analyze_context` - 语境分析工具

**示例**:
```python
from src.agent.tool_wrappers import get_all_tools

tools = get_all_tools()
print(f"可用工具数量: {len(tools)}")
for tool in tools:
    print(f"- {tool.name}: {tool.description[:50]}...")
```

---

### `prompts.py`

#### `SYSTEM_PROMPT`

**类型**: str

**说明**: Agent的系统提示词，定义了Agent的角色、任务、五步推理流程等

**包含内容**:
- Agent角色定义
- 五步推理流程说明
- 工具使用指引
- 输出格式要求

**示例**:
```python
from src.agent.prompts import SYSTEM_PROMPT

print(SYSTEM_PROMPT)
```

---

#### `REASONING_PROMPT`

**类型**: str

**说明**: 推理提示词，用于引导Agent进行深度分析

**示例**:
```python
from src.agent.prompts import REASONING_PROMPT

print(REASONING_PROMPT)
```

---

### 便捷函数

#### `analyze(xungu_sentence: str, context: Optional[str] = None, source: Optional[str] = None, llm_provider: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]`

分析训诂句的便捷函数（直接返回字典）

**参数**:
- `xungu_sentence` (str): 训诂句
- `context` (str, optional): 上下文
- `source` (str, optional): 出处
- `llm_provider` (str, optional): LLM提供商
- `verbose` (bool): 是否输出详细日志，默认 False

**返回**: `Dict[str, Any]` - 分析结果字典

**示例**:
```python
from src.agent import analyze

# 简单使用
result = analyze("崇，终也", context="崇朝其雨")
print(result["classification"])
print(result["confidence"])
print(result["final_reasoning"])

# 批量处理
results = []
for sentence in ["崇，终也", "鬼，隐也"]:
    result = analyze(sentence)
    results.append(result)
```

---

### 导出接口

从 `src.agent` 模块可以直接导入以下内容：

```python
from src.agent import (
    # 核心类
    XunguAgent,
    AnalysisResult,
    
    # 便捷函数
    analyze,
    
    # Prompt
    SYSTEM_PROMPT,
    REASONING_PROMPT,
    
    # 工具相关
    get_llm,
    get_all_tools,
)
```

---

## 完整使用示例

### 最简单的用法

```python
from src.agent import analyze

result = analyze("崇，终也", context="崇朝其雨")
print(result["classification"])  # "假借说明"
```

### 完整的用法

```python
from src.agent import XunguAgent

# 创建Agent
agent = XunguAgent(llm_provider="openai", verbose=True)

# 分析
result = agent.analyze(
    xungu_sentence="崇，终也",
    context="崇朝其雨",
    source="《毛传》"
)

# 访问结果
print(f"分类: {result.classification}")
print(f"置信度: {result.confidence:.0%}")

# 查看五步推理
print(f"第一步语义: {result.step1_semantic}")
print(f"第二步音韵: {result.step2_phonetic}")
print(f"第三步文献: {result.step3_textual}")
print(f"第四步训式: {result.step4_pattern}")
print(f"第五步语境: {result.step5_context}")

# 导出为JSON
json_output = result.to_json()
print(json_output)
```

---

## 数据处理模块 (data/)

### `dyhdc_index_builder.py`

#### `DYHDCIndexBuilder`

**功能**: 构建《汉语大词典》索引

**方法**:

##### `build_index(output_path: str = None) -> Dict`

构建偏移量索引

**参数**:
- `output_path` (str, optional): 索引输出路径，默认不保存

**返回**: `Dict` - 索引字典，格式为 `{首字: [{"headword": "...", "offset": int, "length": int}, ...]}`

**示例**:
```python
from src.data.dyhdc_index_builder import DYHDCIndexBuilder

builder = DYHDCIndexBuilder("path/to/dyhdc.jsonl")
index = builder.build_index("path/to/index.json")
```

##### `build_sqlite_db(db_path: str) -> None`

构建SQLite数据库

**参数**:
- `db_path` (str): 数据库输出路径

**返回**: `None`

**示例**:
```python
builder.build_sqlite_db("data/processed/dyhdc.db")
```

---

#### `DYHDCIndexLoader`

**功能**: 使用预构建索引快速查询词典

**方法**:

##### `load_index() -> bool`

加载索引文件

**返回**: `bool` - 是否加载成功

**示例**:
```python
from src.data.dyhdc_index_builder import DYHDCIndexLoader

loader = DYHDCIndexLoader("path/to/dyhdc.jsonl", "path/to/index.json")
loader.load_index()
```

##### `query(char: str) -> List[Dict]`

查询单个汉字的所有词条

**参数**:
- `char` (str): 要查询的汉字

**返回**: `List[Dict]` - 该字开头的所有词条列表（原始JSON格式）

**示例**:
```python
entries = loader.query("崇")
```

##### `query_single_char(char: str) -> Optional[Dict]`

查询单个字的详细信息（格式化）

**参数**:
- `char` (str): 单个汉字

**返回**: `Optional[Dict]` - 格式化后的字典条目，格式：
```python
{
    "字": "崇",
    "简体": "崇",
    "读音": "chóng",
    "本义": "高大、尊崇",
    "义项": ["高大", "尊崇", ...],
    "例句": ["例句1", "例句2", ...],
    "假借标注": ["读为终", ...]
}
```

**示例**:
```python
result = loader.query_single_char("崇")
print(result["本义"])  # "高大、尊崇"
```

---

#### `DYHDCSQLiteLoader`

**功能**: 使用SQLite数据库查询

**方法**:

##### `connect() -> bool`

连接数据库

**返回**: `bool` - 是否连接成功

##### `query(char: str) -> Optional[Dict]`

查询单个字

**参数**:
- `char` (str): 要查询的汉字

**返回**: `Optional[Dict]` - 字典条目

##### `close() -> None`

关闭数据库连接

---

#### 便捷函数

##### `build_dyhdc_index(jsonl_path: str = None, output_path: str = None, build_sqlite: bool = False) -> Dict`

构建《汉语大词典》索引的便捷函数

**参数**:
- `jsonl_path` (str, optional): JSONL文件路径，默认使用项目配置
- `output_path` (str, optional): 索引输出路径，默认使用项目配置
- `build_sqlite` (bool): 是否同时构建SQLite数据库

**返回**: `Dict` - 索引字典

**示例**:
```python
from src.data.dyhdc_index_builder import build_dyhdc_index

index = build_dyhdc_index(build_sqlite=True)
```

---

### `phonology_parser.py`

#### `parse_panwuyun_txt(filepath: str) -> Dict[str, Dict[str, Any]]`

解析潘悟云《汉语古音手册》TXT文件

**参数**:
- `filepath` (str): TXT文件路径

**返回**: `Dict[str, Dict]` - 格式：`{"崇": {"字": "崇", "上古韵部": "东", "上古音": "*dzruŋ", ...}, ...}`

**示例**:
```python
from src.data.phonology_parser import parse_panwuyun_txt

data = parse_panwuyun_txt("path/to/汉语古音手册.txt")
```

---

#### `parse_baxter_sagart_xlsx(filepath: str) -> Dict[str, Dict[str, Any]]`

解析白一平-沙加尔上古音数据

**参数**:
- `filepath` (str): XLSX文件路径

**返回**: `Dict[str, Dict]` - 格式：`{"崇": {"字": "崇", "上古音": "*[dz]<r>uŋ", ...}, ...}`

**示例**:
```python
from src.data.phonology_parser import parse_baxter_sagart_xlsx

data = parse_baxter_sagart_xlsx("path/to/BaxterSagartOC2015-10-13.xlsx")
```

---

#### `unify_phonology_data(panwuyun_data: Dict, baxter_data: Dict) -> Dict[str, Dict]`

整合多源音韵数据为统一格式

**参数**:
- `panwuyun_data` (Dict): 潘悟云数据
- `baxter_data` (Dict): 白一平-沙加尔数据

**返回**: `Dict[str, Dict]` - 统一格式，包含两个数据源的信息

**示例**:
```python
from src.data.phonology_parser import unify_phonology_data

unified = unify_phonology_data(pan_data, bs_data)
```

---

#### `compare_phonology(char_a: str, char_b: str, data: Dict) -> Dict[str, Any]`

比较两个字的音韵关系

**参数**:
- `char_a` (str): 第一个字
- `char_b` (str): 第二个字
- `data` (Dict): 统一的音韵数据

**返回**: `Dict` - 格式：
```python
{
    "char_a": "崇",
    "char_b": "终",
    "found_a": True,
    "found_b": True,
    "音近": True,
    "韵部相同": True,
    "声母相近": False,
    "详情": {
        "潘悟云": {
            "韵部_A": "东",
            "韵部_B": "东",
            "声母_A": "禅",
            "声母_B": "章",
            ...
        }
    }
}
```

**示例**:
```python
from src.data.phonology_parser import compare_phonology

result = compare_phonology("崇", "终", unified_data)
print(result["音近"])  # True
```

---

#### `build_phonology_index(panwuyun_path: str = None, baxter_path: str = None, output_path: str = None) -> Dict`

构建完整的音韵索引

**参数**:
- `panwuyun_path` (str, optional): 潘悟云数据路径
- `baxter_path` (str, optional): 白一平-沙加尔数据路径
- `output_path` (str, optional): 输出路径

**返回**: `Dict` - 统一的音韵数据

**示例**:
```python
from src.data.phonology_parser import build_phonology_index

data = build_phonology_index()
```

---

#### `save_phonology_data(data: Dict, output_path: str) -> None`

保存音韵数据到JSON文件

**参数**:
- `data` (Dict): 音韵数据
- `output_path` (str): 输出路径

---

#### `load_phonology_data(filepath: str) -> Dict`

从JSON文件加载音韵数据

**参数**:
- `filepath` (str): JSON文件路径

**返回**: `Dict` - 音韵数据

---

## 评估模块 (evaluation/)

### `metrics.py`

#### `load_test_dataset(filepath: str) -> List[TestCase]`

从JSON文件加载测试数据集

**参数**:
- `filepath` (str): JSON文件路径

**返回**: `List[TestCase]` - 测试用例列表

**TestCase 结构**:
```python
@dataclass
class TestCase:
    id: int
    xungu_sentence: str
    beishi_char: str
    shi_char: str
    context: Optional[str]
    source: str
    expected_label: str
    notes: str = ""
```

**示例**:
```python
from src.evaluation.metrics import load_test_dataset

cases = load_test_dataset("data/test/test_dataset.json")
```

---

#### `calculate_metrics(predictions: List[str], labels: List[str]) -> Dict[str, float]`

计算分类指标

**参数**:
- `predictions` (List[str]): 预测标签列表
- `labels` (List[str]): 真实标签列表

**返回**: `Dict` - 格式：
```python
{
    "accuracy": 0.85,
    "precision_假借": 0.90,
    "recall_假借": 0.80,
    "f1_假借": 0.85,
    "precision_语义": 0.80,
    "recall_语义": 0.90,
    "f1_语义": 0.85,
    "macro_f1": 0.85,
    "tp_假借": 18,
    "fp_假借": 2,
    "fn_假借": 4,
    ...
}
```

**示例**:
```python
from src.evaluation.metrics import calculate_metrics

metrics = calculate_metrics(predictions, labels)
print(f"准确率: {metrics['accuracy']:.2%}")
```

---

#### `build_confusion_matrix(predictions: List[str], labels: List[str], label_names: List[str] = None) -> Dict`

构建混淆矩阵

**参数**:
- `predictions` (List[str]): 预测标签列表
- `labels` (List[str]): 真实标签列表
- `label_names` (List[str], optional): 标签名称列表，默认 `["假借说明", "语义解释"]`

**返回**: `Dict` - 格式：
```python
{
    "matrix": [[18, 4], [2, 16]],  # [[TP, FN], [FP, TN]]
    "labels": ["假借说明", "语义解释"],
    "normalized": [[0.82, 0.18], [0.11, 0.89]]  # 归一化矩阵
}
```

**示例**:
```python
from src.evaluation.metrics import build_confusion_matrix, print_confusion_matrix

cm = build_confusion_matrix(predictions, labels)
print_confusion_matrix(cm)
```

---

#### `evaluate_results(results: List[Dict], dataset: List[TestCase]) -> Dict`

评估Agent的分析结果

**参数**:
- `results` (List[Dict]): Agent返回的结果列表，每个结果包含 `classification` 字段
- `dataset` (List[TestCase]): 测试数据集

**返回**: `Dict` - 评估报告，包含指标、混淆矩阵、错误案例等

**示例**:
```python
from src.evaluation.metrics import evaluate_results, print_evaluation_report

report = evaluate_results(agent_results, test_dataset)
print_evaluation_report(report)
```

---

#### `print_evaluation_report(report: Dict) -> None`

打印评估报告

**参数**:
- `report` (Dict): `evaluate_results` 返回的报告

---

#### `save_evaluation_report(report: Dict, filepath: str) -> None`

保存评估报告到JSON文件

**参数**:
- `report` (Dict): 评估报告
- `filepath` (str): 输出路径

---

#### `get_dataset_statistics(dataset: List[TestCase]) -> Dict`

获取数据集统计信息

**参数**:
- `dataset` (List[TestCase]): 测试数据集

**返回**: `Dict` - 格式：
```python
{
    "total": 100,
    "label_distribution": {"假借说明": 50, "语义解释": 50},
    "source_distribution": {"《毛传》": 30, ...},
    "with_context": 80,
    "without_context": 20
}
```

---

#### `quick_evaluate(predictions: List[str], labels: List[str]) -> None`

快速评估并打印结果

**参数**:
- `predictions` (List[str]): 预测标签列表
- `labels` (List[str]): 真实标签列表

---

### `test_dataset.py`

#### `TestDataset`

**功能**: 测试数据集管理类

**方法**:

##### `load(json_path: str) -> None`

从JSON文件加载测试数据

**参数**:
- `json_path` (str): JSON文件路径

**示例**:
```python
from src.evaluation.test_dataset import TestDataset

dataset = TestDataset()
dataset.load("data/test/test_dataset.json")
```

##### `save(json_path: str) -> None`

保存测试数据到JSON文件

**参数**:
- `json_path` (str): JSON文件路径

##### `__len__() -> int`

返回数据集大小

##### `__iter__() -> Iterator[TestCase]`

迭代测试用例

##### `__getitem__(idx) -> TestCase`

通过索引获取测试用例

---

#### `load_test_dataset(path: Optional[str] = None) -> TestDataset`

加载测试数据集的便捷函数

**参数**:
- `path` (str, optional): JSON文件路径，如果为None则加载预设数据

**返回**: `TestDataset`

**示例**:
```python
from src.evaluation.test_dataset import load_test_dataset

dataset = load_test_dataset("data/test/test_dataset.json")
```

---

### `error_analysis.py`

#### `ErrorAnalyzer`

**功能**: 错误分析器

**方法**:

##### `add_errors(errors: List[Dict]) -> None`

添加错误案例

**参数**:
- `errors` (List[Dict]): 错误案例列表，每个字典包含：
  - `id`: 案例ID
  - `训诂句`: 训诂句
  - `被释字`: 被释字
  - `释字`: 释字
  - `预测`: 预测结果
  - `正确`: 正确答案
  - `推理`: 推理过程
  - `五步分析`: 五步分析结果

**示例**:
```python
from src.evaluation.error_analysis import ErrorAnalyzer

analyzer = ErrorAnalyzer()
analyzer.add_errors(error_list)
```

##### `analyze_all() -> Dict`

执行全面错误分析

**返回**: `Dict` - 分析结果，包含错误类型分布、步骤错误分析、错误模式等

##### `generate_report() -> Dict`

生成完整的错误分析报告

**返回**: `Dict` - 完整的错误分析报告

##### `print_report() -> None`

打印错误分析报告

**示例**:
```python
analyzer = ErrorAnalyzer()
analyzer.add_errors(errors)
analyzer.print_report()
```

---

#### `save_error_report(report: Dict, filepath: str) -> None`

保存错误分析报告

**参数**:
- `report` (Dict): 错误分析报告
- `filepath` (str): 输出路径

---

## 知识库模块 (knowledge/)

### `dictionary_loader.py`

#### `DictionaryLoader`

**功能**: 汉语大词典数据加载器

**方法**:

##### `load(max_entries: Optional[int] = None) -> None`

加载全部数据到内存

**参数**:
- `max_entries` (int, optional): 最多加载多少条（用于测试）

**警告**: 完整加载会占用大量内存！

##### `load_lazy() -> None`

延迟加载模式 - 只在查询时才读取

##### `query(char: str) -> Optional[Dict]`

查询单个汉字

**参数**:
- `char` (str): 要查询的汉字

**返回**: `Optional[Dict]` - 格式：
```python
{
    "字": "崇",
    "本义": "高大",
    "义项": ["高大", "尊崇", ...],
    "例句": [{"source": "...", "quote": "..."}, ...],
    "假借标注": ["读为终", ...]
}
```

**示例**:
```python
from src.knowledge.dictionary_loader import DictionaryLoader

loader = DictionaryLoader()
loader.load_lazy()
result = loader.query("崇")
```

---

#### `load_dyhdc(path: Optional[str] = None) -> DictionaryLoader`

获取字典加载器单例

**参数**:
- `path` (str, optional): JSONL文件路径

**返回**: `DictionaryLoader`

---

### `phonology_loader.py`

#### `PhonologyLoader`

**功能**: 音韵数据加载器

**方法**:

##### `load() -> None`

加载所有音韵数据

##### `query(char: str) -> Optional[PhonologyEntry]`

查询单个汉字的音韵信息

**参数**:
- `char` (str): 要查询的汉字

**返回**: `Optional[PhonologyEntry]` - 音韵条目，包含：
```python
@dataclass
class PhonologyEntry:
    char: str          # 汉字
    shengmu: str       # 声母
    yunbu: str         # 韵部
    reconstruction: str # 上古音拟音
    middle_chinese: Optional[str]  # 中古音
    source: str        # 数据来源
```

**示例**:
```python
from src.knowledge.phonology_loader import PhonologyLoader

loader = PhonologyLoader()
loader.load()
entry = loader.query("崇")
print(f"{entry.shengmu}母 {entry.yunbu}部")
```

##### `is_same_yunbu(char1: str, char2: str) -> bool`

判断两个字是否同韵部

**参数**:
- `char1` (str): 第一个字
- `char2` (str): 第二个字

**返回**: `bool`

##### `is_same_shengmu(char1: str, char2: str) -> bool`

判断两个字是否同声母

**参数**:
- `char1` (str): 第一个字
- `char2` (str): 第二个字

**返回**: `bool`

---

#### `load_phonology(data_dir: Optional[str] = None) -> PhonologyLoader`

获取音韵加载器单例

**参数**:
- `data_dir` (str, optional): 音韵数据目录

**返回**: `PhonologyLoader`

---

#### `query_phonology_entry(char: str) -> Optional[Dict]`

便捷查询函数

**参数**:
- `char` (str): 要查询的汉字

**返回**: `Optional[Dict]` - 格式：
```python
{
    "字": "崇",
    "声母": "禅",
    "韵部": "东",
    "上古拟音": "*dzruŋ",
    "来源": "白一平-沙加尔汉语拟音"
}
```

---

## 工具模块 (tools/)

### `semantic_tool.py` - 第一步：语义查询

#### `SemanticTool`

**功能**: 语义查询工具类

**方法**:

##### `load() -> None`

加载字典索引

##### `query(char: str) -> WordMeaning`

查询单个汉字的语义信息

**参数**:
- `char` (str): 要查询的汉字（支持繁简体）

**返回**: `WordMeaning` - 包含本义、义项、例句等信息

**WordMeaning 结构**:
```python
@dataclass
class WordMeaning:
    char: str
    primary_meaning: str
    meanings: List[str]
    examples: List[Dict[str, str]]
    jiajie_notes: List[str]
    raw_data: Optional[Dict] = None
```

**示例**:
```python
from src.tools.semantic_tool import SemanticTool

tool = SemanticTool()
tool.load()
result = tool.query("崇")
print(result.primary_meaning)  # "高大"
```

---

#### `query_word_meaning(char: str) -> Dict[str, Any]`

查询汉字语义信息的函数式接口

**参数**:
- `char` (str): 要查询的汉字

**返回**: `Dict` - 格式：
```python
{
    "字": "崇",
    "本义": "高大",
    "义项": ["高大", "尊崇", ...],
    "例句": [{"source": "...", "quote": "..."}, ...],
    "假借标注": ["读为终", ...]
}
```

**示例**:
```python
from src.tools.semantic_tool import query_word_meaning

result = query_word_meaning("崇")
print(result["本义"])
```

---

### `phonology_tool.py` - 第二步：音韵查询

#### `PhonologyTool`

**功能**: 音韵查询工具类

**方法**:

##### `load() -> None`

加载音韵数据

##### `query(char: str) -> PhonologyInfo`

查询单字音韵信息（含繁简转换）

**参数**:
- `char` (str): 要查询的汉字

**返回**: `PhonologyInfo` - 音韵信息

**PhonologyInfo 结构**:
```python
@dataclass
class PhonologyInfo:
    char: str              # 输入字 (简体)
    char_trad: str         # 索引字 (繁体)
    shengmu: str           # 声母 (潘)
    yunbu: str             # 韵部 (潘)
    pan_reconstruction: str # 拟音 (潘)
    bs_reconstruction: str  # 拟音 (BS)
```

##### `is_phonetically_close(char1: str, char2: str) -> Dict[str, Any]`

判断音近逻辑

**参数**:
- `char1` (str): 第一个字
- `char2` (str): 第二个字

**返回**: `Dict` - 格式：
```python
{
    "is_close": True,  # 是否音近
    "same_yunbu": True,  # 是否同韵部
    "same_shengmu": False,  # 是否同声母
    "char1_info": {
        "繁体": "崇",
        "声母": "禅",
        "韵部": "东",
        "上古音": "*dzruŋ",
        "上古音来源": "白一平-沙加尔汉语拟音"
    },
    "char2_info": {...},
    "analysis": "✅ 【叠韵】(均为东部)；参考: 崇[*dzruŋ] vs 终[*tuŋ]"
}
```

**示例**:
```python
from src.tools.phonology_tool import PhonologyTool

tool = PhonologyTool()
tool.load()
result = tool.is_phonetically_close("崇", "终")
print(result["is_close"])  # True
```

---

#### `query_phonology(char: str) -> Dict[str, Any]`

查询单字音韵信息的函数式接口

**参数**:
- `char` (str): 要查询的汉字

**返回**: `Dict` - 格式：
```python
{
    "字": "崇",
    "声母": "禅",
    "韵部": "东",
    "上古音": "*dzruŋ",
    "上古音来源": "白一平-沙加尔汉语拟音"
}
```

**示例**:
```python
from src.tools.phonology_tool import query_phonology

result = query_phonology("崇")
print(result["韵部"])  # "东"
```

---

#### `check_phonetic_relation(char1: str, char2: str) -> Dict[str, Any]`

判断两个字音近关系的函数式接口

**参数**:
- `char1` (str): 第一个字
- `char2` (str): 第二个字

**返回**: `Dict` - 同 `is_phonetically_close` 的返回格式

**示例**:
```python
from src.tools.phonology_tool import check_phonetic_relation

result = check_phonetic_relation("崇", "终")
print(result["is_close"])  # True
```

---

### `textual_tool.py` - 第三步：文献检索

#### `TextualTool`

**功能**: 文献检索工具类

**方法**:

##### `load() -> None`

加载词典索引

##### `search(char_a: str, char_b: str, context: Optional[str] = None) -> TextualEvidence`

检索两个字之间的文献佐证

**参数**:
- `char_a` (str): 被释字
- `char_b` (str): 释字
- `context` (str, optional): 上下文（可选，用于精确匹配）

**返回**: `TextualEvidence` - 文献佐证信息

**TextualEvidence 结构**:
```python
@dataclass
class TextualEvidence:
    has_evidence: bool  # 是否找到佐证
    variant_texts: List[Dict[str, str]]  # 异文
    parallel_texts: List[Dict[str, str]]  # 平行文本
    jiajie_records: List[Dict[str, str]]  # 假借记录
    summary: str  # 总结说明
```

**示例**:
```python
from src.tools.textual_tool import TextualTool

tool = TextualTool()
tool.load()
result = tool.search("崇", "终", context="崇朝其雨")
print(result.has_evidence)  # True
```

---

#### `search_textual_evidence(char_a: str, char_b: str, context: Optional[str] = None) -> Dict[str, Any]`

检索文献佐证的函数式接口

**参数**:
- `char_a` (str): 被释字
- `char_b` (str): 释字
- `context` (str, optional): 上下文

**返回**: `Dict` - 格式：
```python
{
    "有佐证": True,
    "异文": [
        {
            "type": "variant",
            "source": "《汉语大词典》例句",
            "text": "...",
            "note": "..."
        }
    ],
    "平行文本": [],
    "假借记录": [
        {
            "type": "jiajie",
            "source": "《毛传》",
            "text": "读为终",
            "note": "..."
        }
    ],
    "总结": "找到1处异文；找到1处假借记录"
}
```

**示例**:
```python
from src.tools.textual_tool import search_textual_evidence

result = search_textual_evidence("崇", "终")
print(result["有佐证"])  # True
```

---

### `pattern_tool.py` - 第四步：训式识别

#### `PatternTool`

**功能**: 训式识别工具类

**方法**:

##### `identify(sentence: str) -> PatternResult`

识别训诂句的格式

**参数**:
- `sentence` (str): 训诂句，如 "崇，终也"

**返回**: `PatternResult` - 识别结果

**PatternResult 结构**:
```python
@dataclass
class PatternResult:
    pattern_name: str       # 格式名称，如"读为"、"犹也"
    char_a: str            # 被释字
    char_b: str            # 释字
    implied_type: str      # 暗示类型：假借/语义解释/以声通义/不确定
    confidence: str        # 置信度：高/中/低
    can_direct_judge: bool  # 是否可以直接判定
    source: str            # 该训式的来源说明
```

**示例**:
```python
from src.tools.pattern_tool import PatternTool

tool = PatternTool()
result = tool.identify("崇，读为终")
print(result.pattern_name)  # "读为"
print(result.implied_type)  # "假借"
print(result.can_direct_judge)  # True
```

---

#### `identify_pattern(sentence: str) -> Dict[str, Any]`

识别训诂句格式的函数式接口

**参数**:
- `sentence` (str): 训诂句

**返回**: `Dict` - 格式：
```python
{
    "格式": "读为",
    "被释字": "崇",
    "释字": "终",
    "暗示类型": "假借",
    "置信度": "极高",
    "可直接判定": True,
    "说明": "郑玄《礼》注，破字/改读术语"
}
```

**示例**:
```python
from src.tools.pattern_tool import identify_pattern

result = identify_pattern("崇，终也")
print(result["格式"])  # "A也"
print(result["暗示类型"])  # "不确定"
```

---

### `context_tool.py` - 第五步：语境分析

#### `ContextTool`

**功能**: 语境分析工具类

**方法**:

##### `analyze(original_sentence: str, char_a: str, char_b: str, meaning_a: str, meaning_b: str) -> ContextAnalysis`

分析语境适配度

**参数**:
- `original_sentence` (str): 原始句子
- `char_a` (str): 被释字
- `char_b` (str): 释字
- `meaning_a` (str): A的本义
- `meaning_b` (str): B的本义

**返回**: `ContextAnalysis` - 分析结果

**ContextAnalysis 结构**:
```python
@dataclass
class ContextAnalysis:
    char_a_fits: bool  # 被释字本义代入是否通顺
    char_b_fits: bool  # 释字本义代入是否通顺
    char_a_interpretation: str  # 用A本义的解释
    char_b_interpretation: str  # 用B本义的解释
    conclusion: str  # 结论：支持假借/支持语义/不确定
    reasoning: str  # 推理说明
```

**示例**:
```python
from src.tools.context_tool import ContextTool

tool = ContextTool(auto_init=True)  # 自动初始化LLM客户端
result = tool.analyze(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="终",
    meaning_a="高大",
    meaning_b="终结、整个"
)
print(result.conclusion)  # "支持假借"
```

---

#### `analyze_context(original_sentence: str, char_a: str, char_b: str, meaning_a: str, meaning_b: str, llm_client=None) -> Dict[str, Any]`

语境分析的函数式接口

**参数**:
- `original_sentence` (str): 原始句子
- `char_a` (str): 被释字
- `char_b` (str): 释字
- `meaning_a` (str): A的本义
- `meaning_b` (str): B的本义
- `llm_client`: LLM客户端（可选）

**返回**: `Dict` - 格式：
```python
{
    "A本义通顺": False,
    "B本义通顺": True,
    "A解释": "'高大早晨下雨'，语义不通",
    "B解释": "'整个早晨下雨'，语义通顺",
    "结论": "支持假借",
    "理由": "被释字'崇'的本义'高大'代入原句不通顺，而释字'终'的本义'终结、整个'代入后通顺，符合假借特征"
}
```

**示例**:
```python
from src.tools.context_tool import analyze_context

result = analyze_context(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="终",
    meaning_a="高大",
    meaning_b="终结、整个"
)
print(result["结论"])  # "支持假借"
```

---

## 使用示例

### 完整五步推理流程

```python
from src.tools import (
    query_word_meaning,
    check_phonetic_relation,
    search_textual_evidence,
    identify_pattern,
    analyze_context
)

# 输入
xungu_sentence = "崇，终也"
context = "崇朝其雨"
char_a = "崇"
char_b = "终"

# Step 1: 语义查询
meaning_a = query_word_meaning(char_a)
meaning_b = query_word_meaning(char_b)
print(f"Step 1: {char_a}本义={meaning_a['本义']}, {char_b}本义={meaning_b['本义']}")

# Step 2: 音韵查询
phonetic = check_phonetic_relation(char_a, char_b)
print(f"Step 2: 音近={phonetic['is_close']}, 韵部相同={phonetic['same_yunbu']}")

# Step 3: 文献检索
textual = search_textual_evidence(char_a, char_b, context)
print(f"Step 3: 有佐证={textual['有佐证']}")

# Step 4: 训式识别
pattern = identify_pattern(xungu_sentence)
print(f"Step 4: 格式={pattern['格式']}, 暗示类型={pattern['暗示类型']}")

# Step 5: 语境分析
context_result = analyze_context(
    original_sentence=context,
    char_a=char_a,
    char_b=char_b,
    meaning_a=meaning_a['本义'],
    meaning_b=meaning_b['本义']
)
print(f"Step 5: 结论={context_result['结论']}")
```

---

## 注意事项

1. **数据文件路径**: 大部分工具使用项目配置中的默认路径，如需自定义请查看 `src/config/settings.py`
2. **索引文件**: 使用 `DYHDCIndexLoader` 前需要先构建索引，运行 `build_dyhdc_index()`
3. **音韵数据**: 使用 `PhonologyTool` 前需要先运行 `build_phonology_index()` 生成统一数据
4. **LLM客户端**: `ContextTool` 需要LLM客户端，可通过 `auto_init=True` 自动初始化
5. **繁简转换**: `PhonologyTool` 和 `PatternTool` 支持繁简自动转换

---

*文档最后更新: 2025-01-XX*

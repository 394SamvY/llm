# Agent模块使用说明

> 基于LangChain框架的训诂分类Agent实现
> 
> 负责人：成员B

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [安装与配置](#安装与配置)
- [核心类与接口](#核心类与接口)
- [五步推理流程](#五步推理流程)
- [工具系统](#工具系统)
- [高级用法](#高级用法)
- [常见问题](#常见问题)

---

## 概述

**XunguAgent** 是基于LangChain 1.0+框架实现的训诂分类系统核心。它使用大语言模型（LLM）按照五步推理流程自动分析训诂句，判断其属于"假借说明"还是"语义解释"。

### 主要特性

- ✅ **完整的五步推理** - 语义→音韵→文献→训式→语境
- ✅ **模块化工具系统** - 6个独立的工具函数，可灵活组合
- ✅ **双LLM支持** - OpenAI GPT-4 和 Anthropic Claude
- ✅ **自适应执行** - 自动迭代调用工具，智能决策
- ✅ **详细推理链** - 完整保留每一步的分析过程
- ✅ **错误容错** - 自动处理工具调用失败，继续推理

### 系统架构

```
┌─────────────────────────┐
│   输入：训诂句 + 上下文   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    XunguAgent 核心      │
├─────────────────────────┤
│ • 提示词构建            │
│ • 工具绑定              │
│ • 推理执行              │
│ • 结果解析              │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│      SimpleAgentExecutor 执行器     │
│  （替代已废弃的LangChain Executor） │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│  LLM    │    │ Tool 工具集  │
│ (GPT-4/ │    │  (6个工具)   │
│ Claude) │    └──────────────┘
└─────────┘
    │
    └─→ 迭代调用工具 →┐
                      │
    ┌─────────────────┘
    │
    ▼
┌──────────────────┐
│  AnalysisResult  │
│  (完整分析结果)   │
└──────────────────┘
```

---

## 快速开始

### 最简单的用法

```python
from src.agent import analyze

# 一行代码分析训诂句
result = analyze("崇，终也", context="崇朝其雨")
print(result["classification"])  # "假借说明"
print(result["confidence"])      # 0.85
```

### 完整的用法

```python
from src.agent import XunguAgent

# 创建Agent实例
agent = XunguAgent(
    llm_provider="openai",      # 或 "anthropic"
    verbose=True,               # 输出详细日志
    max_iterations=15,          # 最大工具调用次数
    max_execution_time=60       # 最大执行时间（秒）
)

# 分析训诂句
result = agent.analyze(
    xungu_sentence="崇，终也",
    context="崇朝其雨",         # 可选
    source="《毛传》"           # 可选
)

# 查看分类结果
print(f"分类: {result.classification}")      # "假借说明" 或 "语义解释"
print(f"置信度: {result.confidence:.0%}")    # 0-100%
print(f"最终判断: {result.final_reasoning}")

# 查看五步推理过程
print(f"\n第一步-语义查询:\n{result.step1_semantic}")
print(f"\n第二步-音韵查询:\n{result.step2_phonetic}")
print(f"\n第三步-文献检索:\n{result.step3_textual}")
print(f"\n第四步-训式识别:\n{result.step4_pattern}")
print(f"\n第五步-语境分析:\n{result.step5_context}")

# 导出为JSON
json_output = result.to_json()
print(json_output)
```

---

## 安装与配置

### 系统要求

- Python 3.8+
- LangChain 1.0+
- LLM API Key（OpenAI 或 Anthropic）

### 安装依赖

```bash
# 从requirements.txt安装
pip install -r requirements.txt

# 或手动安装关键依赖
pip install langchain langchain-openai langchain-anthropic
```

### 环境配置

在项目根目录创建 `.env` 文件：

```bash
# 必选：LLM API Key 二选一

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4-turbo

# 或 Anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# 可选：其他配置
OPENAI_BASE_URL=https://api.openai.com/v1  # 自定义API端点
LLM_PROVIDER=openai                         # 默认LLM提供商
```

### 验证安装

```python
# 测试LLM连接
from src.agent.llm_client import get_llm

llm = get_llm()
print("✅ LLM连接成功")

# 测试工具系统
from src.agent.tool_wrappers import get_all_tools

tools = get_all_tools()
print(f"✅ 工具系统就绪，共{len(tools)}个工具")

# 测试Agent
from src.agent import XunguAgent

agent = XunguAgent(verbose=False)
result = agent.analyze("正，读为征")
print(f"✅ Agent可用，分类结果: {result.classification}")
```

---

## 核心类与接口

### AnalysisResult（分析结果类）

代表Agent的完整分析输出。

**关键字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `classification` | str | 分类结果："假借说明" 或 "语义解释" |
| `confidence` | float | 置信度 (0.0-1.0) |
| `step1_semantic` | Dict | 第一步：语义查询结果 |
| `step2_phonetic` | Dict | 第二步：音韵查询结果 |
| `step3_textual` | Dict | 第三步：文献检索结果 |
| `step4_pattern` | Dict | 第四步：训式识别结果 |
| `step5_context` | Dict | 第五步：语境分析结果 |
| `final_reasoning` | str | 最终推理说明 |

**常用方法**:

```python
# 转换为字典
result_dict = result.to_dict()

# 转换为JSON字符串
json_str = result.to_json(indent=2)

# 访问字段
print(result.classification)
print(result.step1_semantic)
```

### XunguAgent（Agent类）

系统的核心推理引擎。

**初始化参数**:

```python
agent = XunguAgent(
    llm_provider="openai",          # LLM提供商：openai 或 anthropic
    verbose=True,                   # 是否输出详细日志
    max_iterations=15,              # 最大迭代次数
    max_execution_time=60           # 最大执行时间（秒）
)
```

**核心方法**:

```python
# 分析训诂句
result = agent.analyze(
    xungu_sentence="崇，终也",      # 必需：训诂句
    context="崇朝其雨",             # 可选：上下文
    source="《毛传》"               # 可选：出处
)
```

---

## 五步推理流程

Agent按照以下五步自动分析训诂句：

### 第一步：语义查询

**工具**: `query_word_meaning()`

**功能**: 查询被释字和释字的本义，判断义近/义远

**输出示例**:
```json
{
    "字": "崇",
    "本义": "高大",
    "义项": ["高大", "尊崇", "崇拜"],
    "例句": ["..."]
}
```

**判断依据**:
- 🟢 义近 → 支持"语义解释"
- 🔴 义远 → 支持"假借说明"

---

### 第二步：音韵查询

**工具**: `query_phonology()` + `check_phonetic_relation()`

**功能**: 查询上古音，判断两字是否音近

**输出示例**:
```json
{
    "is_close": true,
    "same_yunbu": true,        # 同韵部
    "same_shengmu": false,     # 不同声母
    "char1_info": {...},
    "char2_info": {...}
}
```

**判断依据**:
- 🟢 音近 + 义远 → 支持"假借说明"
- 🔴 音近 + 义近 → 可能"以声通义"（特殊的语义解释）

---

### 第三步：文献检索

**工具**: `search_textual_evidence()`

**功能**: 检索词典中的异文、假借标注等佐证

**输出示例**:
```json
{
    "有佐证": true,
    "异文": [...],
    "假借记录": [
        {
            "source": "《毛传》",
            "text": "读为终"
        }
    ]
}
```

**判断依据**:
- 🟢 有假借记录 → 强烈支持"假借说明"
- 🟡 有异文但无假借记录 → 中等支持

---

### 第四步：训式识别

**工具**: `identify_pattern()`

**功能**: 识别训诂句的格式（如"读为"、"犹也"等），判断是否直接暗示假借

**支持的格式**:
- `读为` → 极强暗示"假借"
- `谓之` / `之谓` → 可能"假借"或"语义"
- `犹` / `犹也` → 中等暗示"语义解释"
- `正` / `为` → 弱暗示"语义解释"
- 其他格式 → 弱暗示

**输出示例**:
```json
{
    "格式": "读为",
    "暗示类型": "假借",
    "置信度": "极高",
    "可直接判定": true
}
```

**判断依据**:
- 🟢 格式直接暗示 → 可直接判定
- 🟡 格式弱暗示 → 需要结合其他步骤

---

### 第五步：语境分析

**工具**: `analyze_context()`

**功能**: 分析语境，判断被释字/释字的本义代入后是否通顺

**输出示例**:
```json
{
    "A本义通顺": false,
    "B本义通顺": true,
    "结论": "支持假借",
    "理由": "A的本义代入不通，B的本义代入通顺"
}
```

**判断依据**:
- 🟢 A义代入不通，B义代入通顺 → 支持"假借说明"
- 🟡 A义代入通顺，B义代入也通顺 → 支持"语义解释"

---

## 工具系统

### 6个内置工具

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `query_word_meaning` | 查询字义 | 单个汉字 | 本义、义项、例句 |
| `query_phonology` | 查询音韵 | 单个汉字 | 声母、韵部、拟音 |
| `check_phonetic_relation` | 比较音韵 | 两个汉字 | 音近、韵部、声母 |
| `search_textual_evidence` | 检索文献 | 两个汉字+上下文 | 异文、假借记录 |
| `identify_pattern` | 识别训式 | 训诂句字符串 | 格式、暗示类型 |
| `analyze_context` | 分析语境 | 句子、两个字、两个义项 | 通顺性、结论 |

### 工具调用方式

```python
# 直接调用工具函数
from src.tools import query_word_meaning, check_phonetic_relation

meaning = query_word_meaning("崇")
phonetic = check_phonetic_relation("崇", "终")

# 或在Agent中自动调用
agent = XunguAgent(verbose=True)  # verbose=True时可看到工具调用过程
result = agent.analyze("崇，终也")  # Agent会自动决定调用哪些工具
```

---

## 高级用法

### 批量分析

```python
from src.agent import XunguAgent
import json

agent = XunguAgent(verbose=False)

# 批量分析
sentences = [
    {"text": "崇，终也", "context": "崇朝其雨"},
    {"text": "正，读为征", "context": None},
    {"text": "鬼，隐也", "context": "鬼在暗处"},
]

results = []
for item in sentences:
    result = agent.analyze(
        xungu_sentence=item["text"],
        context=item.get("context")
    )
    results.append(result.to_dict())

# 保存结果
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

### 自定义LLM模型

```python
from src.agent import XunguAgent
from src.agent.llm_client import get_llm

# 使用Anthropic Claude
agent = XunguAgent(llm_provider="anthropic", verbose=True)
result = agent.analyze("崇，终也")

# 或手动创建LLM并传入
from src.config import get_settings
settings = get_settings()
# ... 自定义LLM配置
```

### 调整推理参数

```python
# 调整迭代次数和超时时间
agent = XunguAgent(
    max_iterations=20,          # 增加工具调用次数
    max_execution_time=120      # 增加超时时间（秒）
)

# 快速模式
fast_agent = XunguAgent(
    max_iterations=5,           # 快速模式：少次迭代
    max_execution_time=30       # 快速模式：30秒超时
)
```

### 集成到其他系统

```python
# Flask Web应用
from flask import Flask, request, jsonify
from src.agent import XunguAgent

app = Flask(__name__)
agent = XunguAgent(verbose=False)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    result = agent.analyze(
        xungu_sentence=data.get("sentence"),
        context=data.get("context")
    )
    return jsonify(result.to_dict())

# FastAPI应用
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
agent = XunguAgent(verbose=False)

class XunguRequest(BaseModel):
    sentence: str
    context: str = None

@app.post("/analyze")
async def analyze(req: XunguRequest):
    result = agent.analyze(req.sentence, context=req.context)
    return result.to_dict()
```

---

## 常见问题

### Q: 如何设置API Key？

**A**: 在项目根目录创建 `.env` 文件：

```bash
OPENAI_API_KEY=sk-xxx
# 或
ANTHROPIC_API_KEY=sk-ant-xxx
```

### Q: Agent分析很慢，如何加快？

**A**: 

1. 减少 `max_iterations`：
```python
agent = XunguAgent(max_iterations=10)  # 默认15
```

2. 减少 `max_execution_time`：
```python
agent = XunguAgent(max_execution_time=30)  # 默认无限制
```

3. 使用 `verbose=False` 关闭日志输出

### Q: 如何只使用某些工具？

**A**: 目前Agent自动选择工具。如需手动控制，可直接调用工具函数：

```python
from src.tools import identify_pattern, check_phonetic_relation

# 只识别训式和音韵
pattern = identify_pattern("崇，终也")
phonetic = check_phonetic_relation("崇", "终")
```

### Q: Agent返回结果错误，怎么办？

**A**:

1. 检查API Key是否正确设置
2. 启用 `verbose=True` 查看推理过程
3. 检查被分析的训诂句格式是否正确
4. 检查是否需要构建词典索引

### Q: 如何扩展Agent功能？

**A**: 在 `tool_wrappers.py` 中添加新工具：

```python
from langchain_core.tools import StructuredTool

def new_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=your_function,
        name="tool_name",
        description="Tool description"
    )

# 在 get_all_tools() 中添加
def get_all_tools():
    return [
        # ... 现有工具
        new_tool(),  # 新工具
    ]
```

---

## 更多资源

- **详细API文档**: 见 [`docs/API.md`](../docs/API.md)
- **完整实现代码**: 见 [`xungu_agent.py`](xungu_agent.py)
- **项目完成度**: 见 [`docs/COMPLETION.md`](../docs/COMPLETION.md)
- **开发指南**: 见 [`AGENT_DEVELOPMENT_GUIDE.md`](AGENT_DEVELOPMENT_GUIDE.md)

---

*文档最后更新: 2026年1月18日*


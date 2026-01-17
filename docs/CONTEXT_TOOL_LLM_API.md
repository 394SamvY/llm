# Context Tool LLM API 使用说明

> **负责人**: 成员D  
> **完成日期**: 2026-01-17  
> **状态**: ✅ 已接入 LLM API

---

## 📋 快速开始

### 前置条件

1. **安装依赖**
   ```bash
   pip install openai
   ```

2. **API配置**（已内置，无需额外配置）
   - API Key: `sk-0d73949767524be2989b35415d2ccbe0`
   - Base URL: `https://api.tokenpony.cn/v1`
   - Model: `qwen3-coder-480b`

### 最简单的使用方式

```python
from openai import OpenAI
from src.tools.context_tool import analyze_context

# 1. 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 2. 调用函数（传入llm_client）
result = analyze_context(
    original_sentence="崇朝其雨",  # 原始句子
    char_a="崇",                    # 被释字
    char_b="終",                    # 释字
    meaning_a="高；高大",           # A的本义
    meaning_b="终结、整个",         # B的本义
    llm_client=llm_client           # 传入LLM客户端
)

# 3. 查看结果
print(f"结论: {result['结论']}")        # "支持假借"
print(f"A本义通顺: {result['A本义通顺']}")  # False
print(f"B本义通顺: {result['B本义通顺']}")  # True
print(f"理由: {result['理由']}")
```

---

## 🔧 三种使用方式

### 方式1：函数式接口（最简单，推荐）

**适用场景**：快速调用，不需要复用工具实例

```python
from openai import OpenAI
from src.tools.context_tool import analyze_context

# 创建客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 直接调用
result = analyze_context(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个",
    llm_client=llm_client
)

print(result["结论"])  # "支持假借"
```

**优点**：
- 代码简洁
- 适合一次性调用
- 自动管理工具实例

---

### 方式2：类式接口（适合批量调用）

**适用场景**：需要多次调用，复用工具实例

```python
from openai import OpenAI
from src.tools.context_tool import ContextTool

# 1. 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 2. 创建工具实例（只需创建一次）
tool = ContextTool(llm_client=llm_client)

# 3. 多次调用（复用同一个实例）
result1 = tool.analyze(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个"
)

result2 = tool.analyze(
    original_sentence="瞻卬昊天，云如何崇",
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个"
)

print(result1.conclusion)  # "支持假借"
print(result2.conclusion)  # "支持语义"
```

**优点**：
- 可以复用工具实例
- 适合批量处理
- 更灵活的控制

---

### 方式3：自动初始化（使用内置配置）

**适用场景**：不想手动创建客户端，使用默认配置

```python
from src.tools.context_tool import ContextTool

# 使用 auto_init=True，自动创建客户端（使用内置API配置）
tool = ContextTool(auto_init=True)

# 使用工具
result = tool.analyze(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个"
)

print(result.conclusion)  # "支持假借"
```

**注意**：此方式使用代码中硬编码的API配置，适合快速测试。

---

## 📖 完整使用示例

### 示例1：在Agent中使用

```python
from openai import OpenAI
from src.agent.xungu_agent import XunguAgent

# 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 创建Agent（会自动使用LLM进行语境分析）
agent = XunguAgent(llm_client=llm_client)

# 分析训诂句（第五步会自动调用context_tool）
result = agent.analyze(
    xungu_sentence="崇，終也",
    context="崇朝其雨"
)

print(f"分类: {result.classification}")
print(f"第五步结论: {result.step5_context['结论']}")
```

### 示例2：单独使用语境分析

```python
from openai import OpenAI
from src.tools.context_tool import analyze_context
from src.tools.semantic_tool import query_word_meaning

# 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 1. 先查询两个字的本义
meaning_a = query_word_meaning("崇")
meaning_b = query_word_meaning("終")

# 2. 进行语境分析
result = analyze_context(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="終",
    meaning_a=meaning_a["本义"],
    meaning_b=meaning_b["本义"],
    llm_client=llm_client
)

# 3. 输出结果
print("=" * 60)
print("语境分析结果")
print("=" * 60)
print(f"原句: 崇朝其雨")
print(f"用'崇'本义理解: {result['A解释']}")
print(f"用'終'本义理解: {result['B解释']}")
print(f"结论: {result['结论']}")
print(f"理由: {result['理由']}")
```

### 示例3：批量处理测试集

```python
from openai import OpenAI
from src.tools.context_tool import ContextTool
from src.evaluation.test_dataset import load_test_dataset
from src.tools.semantic_tool import query_word_meaning

# 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 创建工具实例（复用）
tool = ContextTool(llm_client=llm_client)

# 加载测试集
dataset = load_test_dataset("data/test/test_dataset.json")

# 批量分析
results = []
for case in dataset:
    if case.context:  # 只分析有上下文的案例
        # 查询本义
        meaning_a = query_word_meaning(case.char_a)
        meaning_b = query_word_meaning(case.char_b)
        
        # 语境分析
        result = tool.analyze(
            original_sentence=case.context,
            char_a=case.char_a,
            char_b=case.char_b,
            meaning_a=meaning_a["本义"],
            meaning_b=meaning_b["本义"]
        )
        
        results.append({
            "id": case.id,
            "context": case.context,
            "conclusion": result.conclusion,
            "expected": case.expected_label
        })

# 统计
print(f"共分析 {len(results)} 个案例")
for r in results[:5]:
    print(f"ID {r['id']}: {r['conclusion']} (期望: {r['expected']})")
```

---

## 📊 返回数据格式

### 函数式接口返回

```python
{
    "A本义通顺": False,              # 被释字本义代入是否通顺
    "B本义通顺": True,               # 释字本义代入是否通顺
    "A解释": "用'高；高大'理解：'高大早晨下雨'，语义不通",
    "B解释": "用'终结、整个'理解：'整个早晨下雨'，语义通顺",
    "结论": "支持假借",              # "支持假借" / "支持语义" / "不确定"
    "理由": "被释字'崇'的本义'高；高大'代入原句不通顺，而释字'終'的本义'终结、整个'代入后通顺，符合假借特征"
}
```

### 类式接口返回

```python
ContextAnalysis(
    char_a_fits=False,              # bool
    char_b_fits=True,              # bool
    char_a_interpretation="...",  # str
    char_b_interpretation="...",  # str
    conclusion="支持假借",         # str
    reasoning="..."                # str
)
```

---

## 🔍 工作原理

### 工作流程

```
用户调用 analyze()
    ↓
检查是否有 llm_client?
    ├─ 有 → _analyze_with_llm()  ← 使用真实LLM API
    │         ↓
    │     1. 构建提示词 (_build_prompt)
    │     2. 调用LLM API (chat.completions.create)
    │     3. 解析JSON响应 (_parse_response)
    │     4. 返回 ContextAnalysis
    │
    └─ 无 → _analyze_mock()  ← 使用模拟数据
              ↓
          返回预设的模拟结果
```

### LLM提示词示例

工具会构建如下提示词发送给LLM：

```
你是一位古汉语专家。请分析以下句子中，用不同字义代入后的语义通顺度。

原句：崇朝其雨

分析任务：
1. 将"崇"按其本义"高；高大"理解，判断句子是否通顺
2. 将"崇"理解为"終"（本义：终结、整个），判断句子是否通顺

请按以下JSON格式输出：
{
    "char_a_fits": true/false,
    "char_b_fits": true/false,
    "char_a_interpretation": "用A本义的句子解释",
    "char_b_interpretation": "用B本义的句子解释",
    "conclusion": "支持假借/支持语义/不确定",
    "reasoning": "判断理由"
}
```

---

## ⚙️ 配置说明

### API配置位置

代码中已内置API配置（`src/tools/context_tool.py` 第62-64行）：

```python
api_key = "sk-0d73949767524be2989b35415d2ccbe0"
base_url = "https://api.tokenpony.cn/v1"
model = "qwen3-coder-480b"
```

### 环境变量配置（可选）

也可以通过环境变量覆盖：

```bash
export OPENAI_API_KEY="sk-0d73949767524be2989b35415d2ccbe0"
export OPENAI_BASE_URL="https://api.tokenpony.cn/v1"
export LLM_MODEL="qwen3-coder-480b"
```

然后在代码中使用：

```python
from src.tools.context_tool import ContextTool

# 使用 auto_init=True，会自动读取环境变量
tool = ContextTool(auto_init=True)
```

---

## 🧪 测试验证

### 运行测试

```bash
# 测试LLM API接入
python tests/test_context_tool.py
```

### 测试内容

测试文件会验证：
1. ✅ LLM客户端创建
2. ✅ API调用成功
3. ✅ JSON响应解析
4. ✅ 结果格式正确
5. ✅ 多个测试用例

### 预期输出

```
============================================================
测试语境分析工具 (context_tool.py) - 使用LLM API
============================================================

[1] 假借案例：崇借为终
    原句: 崇朝其雨
    被释字: 崇 (本义: 高；高大)
    释字: 終 (本义: 终结、整个)
    期望结论: 支持假借
    实际结论: 支持假借
    A本义通顺: False
    B本义通顺: True
    ✓ 结论匹配期望
```

---

## ⚠️ 注意事项

### 1. API调用失败处理

如果LLM API调用失败，工具会自动回退到Mock模式：

```python
# 如果API调用失败，会看到警告
⚠️  LLM调用失败: ...，使用模拟结果
```

### 2. 无上下文的情况

如果没有提供上下文，工具无法进行语境分析：

```python
result = tool.analyze(
    original_sentence="",  # 空字符串
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个"
)
# 结论会是"不确定"
```

### 3. 成本考虑

每次调用都会消耗API额度，建议：
- 批量处理时复用工具实例
- 测试时可以使用Mock模式（不传llm_client）

### 4. 响应时间

LLM API调用需要1-3秒，请耐心等待。

---

## 🔗 与其他工具配合使用

### 完整五步分析流程

```python
from openai import OpenAI
from src.tools import (
    query_word_meaning,      # 第一步：语义查询
    query_phonology,         # 第二步：音韵分析
    search_textual_evidence, # 第三步：文献检索
    identify_pattern,        # 第四步：训式识别
    analyze_context          # 第五步：语境分析
)

# 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 分析训诂句："崇，終也"，上下文："崇朝其雨"
xungu_sentence = "崇，終也"
context = "崇朝其雨"
char_a = "崇"
char_b = "終"

# 第一步：语义分析
meaning_a = query_word_meaning(char_a)
meaning_b = query_word_meaning(char_b)

# 第二步：音韵分析
phonology = query_phonology(char_a, char_b)

# 第三步：文献检索
evidence = search_textual_evidence(char_a, char_b, context)

# 第四步：训式识别
pattern = identify_pattern(xungu_sentence)

# 第五步：语境分析（使用LLM）
context_result = analyze_context(
    original_sentence=context,
    char_a=char_a,
    char_b=char_b,
    meaning_a=meaning_a["本义"],
    meaning_b=meaning_b["本义"],
    llm_client=llm_client
)

# 综合判断
print("=" * 60)
print("五步分析结果")
print("=" * 60)
print(f"语义: {meaning_a['本义']} vs {meaning_b['本义']}")
print(f"音韵: {phonology['音近']}")
print(f"文献: {evidence['有佐证']}")
print(f"训式: {pattern['暗示类型']}")
print(f"语境: {context_result['结论']}")
```

---

## 📞 常见问题

### Q1: 如何知道是否使用了LLM？

**A**: 检查返回结果的详细程度：
- **使用LLM**：`reasoning`字段会有详细的分析说明
- **使用Mock**：`reasoning`字段是预设的简短说明

### Q2: API调用失败怎么办？

**A**: 工具会自动回退到Mock模式，不会报错。检查：
1. API key是否正确
2. 网络连接是否正常
3. API服务是否可用

### Q3: 如何减少API调用次数？

**A**: 
1. 批量处理时复用工具实例
2. 测试时使用Mock模式（不传llm_client）
3. 缓存已分析的结果

### Q4: 可以自定义模型吗？

**A**: 可以，创建客户端时指定：

```python
client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
client._model = "your-model-name"  # 自定义模型
```

---

## 📚 相关文档

- **工具API文档**: `docs/TOOLS_API_C.md`
- **快速参考**: `docs/TOOLS_QUICK_C_REFERENCE.md`
- **测试文件**: `tests/test_context_tool.py`

---

## ✅ 总结

**使用LLM API的步骤**：

1. ✅ 安装 `openai` 库：`pip install openai`
2. ✅ 创建LLM客户端（使用您的API配置）
3. ✅ 调用 `analyze_context()` 或 `ContextTool.analyze()`
4. ✅ 传入 `llm_client` 参数
5. ✅ 获取分析结果

**关键点**：
- 必须传入 `llm_client` 才会使用真实LLM API
- 不传 `llm_client` 会使用Mock数据
- API调用失败会自动回退到Mock模式

---

*最后更新：2026-01-17*

## 🧪 测试验证

运行测试文件验证LLM API接入：

```bash
python tests/test_context_tool.py
```

测试会：
1. 创建LLM客户端
2. 调用真实的LLM API
3. 解析返回的JSON响应
4. 验证分析结果

## ⚙️ 配置说明

### API配置位置

代码中已硬编码您的API配置（第62-64行）：

```python
api_key = settings.openai_api_key or "sk-0d73949767524be2989b35415d2ccbe0"
base_url = settings.openai_base_url or "https://api.tokenpony.cn/v1"
model = settings.llm_model or "qwen3-coder-480b"
```

### 环境变量配置（可选）

也可以通过环境变量配置：

```bash
export OPENAI_API_KEY="sk-0d73949767524be2989b35415d2ccbe0"
export OPENAI_BASE_URL="https://api.tokenpony.cn/v1"
export LLM_MODEL="qwen3-coder-480b"
```

## 📝 使用示例

### 示例1：基本使用

```python
from openai import OpenAI
from src.tools.context_tool import ContextTool

# 创建客户端
client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
client._model = "qwen3-coder-480b"

# 创建工具
tool = ContextTool(llm_client=client)

# 分析
result = tool.analyze(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个"
)

print(f"结论: {result.conclusion}")
print(f"理由: {result.reasoning}")
```

### 示例2：在Agent中使用

```python
from openai import OpenAI
from src.agent.xungu_agent import XunguAgent

# 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 创建Agent（会自动使用LLM进行语境分析）
agent = XunguAgent(llm_client=llm_client)

# 分析训诂句
result = agent.analyze("崇，終也", context="崇朝其雨")
```

## ✅ 接入状态总结

| 功能 | 状态 | 说明 |
|------|:----:|------|
| LLM API调用 | ✅ 已实现 | `_analyze_with_llm()` 方法 |
| 响应解析 | ✅ 已实现 | `_parse_response()` 方法 |
| 错误处理 | ✅ 已实现 | 失败时回退到mock |
| 自动初始化 | ✅ 已实现 | `auto_init=True` 参数 |
| API配置 | ✅ 已配置 | 硬编码了您的API key和base_url |
| 测试文件 | ✅ 已创建 | `tests/test_context_tool.py` |

## 🎯 关键代码位置

- **LLM调用**：第124-129行
- **响应解析**：第142-200行
- **客户端创建**：第53-75行
- **提示词构建**：第202-233行

---

*最后更新：2026-01-17*

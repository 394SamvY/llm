# Context Tool LLM API 接入说明

## 📋 概述

`context_tool.py` 已经**完全接入 LLM API**，可以通过以下方式使用：

## 🔧 接入方式

### 方式1：手动创建客户端（推荐）

```python
from openai import OpenAI
from src.tools.context_tool import ContextTool

# 创建LLM客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 创建工具实例（传入llm_client）
tool = ContextTool(llm_client=llm_client)

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

### 方式2：自动初始化（使用内置配置）

```python
from src.tools.context_tool import ContextTool

# 使用 auto_init=True，会自动从配置创建客户端
tool = ContextTool(auto_init=True)

# 使用工具
result = tool.analyze(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="終",
    meaning_a="高；高大",
    meaning_b="终结、整个"
)
```

### 方式3：函数式接口

```python
from openai import OpenAI
from src.tools.context_tool import analyze_context

# 创建客户端
llm_client = OpenAI(
    base_url="https://api.tokenpony.cn/v1",
    api_key="sk-0d73949767524be2989b35415d2ccbe0"
)
llm_client._model = "qwen3-coder-480b"

# 直接调用函数
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

## 🔍 代码实现说明

### 1. LLM API 调用实现

在 `_analyze_with_llm()` 方法中（第107-140行）：

```python
def _analyze_with_llm(self, ...) -> ContextAnalysis:
    """使用LLM进行分析"""
    prompt = self._build_prompt(...)
    
    # 调用LLM API
    response = self.llm_client.chat.completions.create(
        model=getattr(self.llm_client, '_model', 'qwen3-coder-480b'),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )
    
    # 解析响应
    content = response.choices[0].message.content
    return self._parse_response(content, ...)
```

### 2. 自动客户端创建

在 `_create_client_from_config()` 方法中（第53-75行）：

```python
def _create_client_from_config(self):
    """从配置创建LLM客户端"""
    from openai import OpenAI
    
    # 使用硬编码的API配置（已包含您的API key）
    api_key = "sk-0d73949767524be2989b35415d2ccbe0"
    base_url = "https://api.tokenpony.cn/v1"
    model = "qwen3-coder-480b"
    
    client = OpenAI(base_url=base_url, api_key=api_key)
    client._model = model
    return client
```

### 3. 智能回退机制

在 `analyze()` 方法中（第77-105行）：

```python
def analyze(self, ...) -> ContextAnalysis:
    """分析语境适配度"""
    if self.llm_client is not None:
        # 有LLM客户端 → 使用LLM API
        return self._analyze_with_llm(...)
    else:
        # 无LLM客户端 → 使用模拟数据
        return self._analyze_mock(...)
```

## 📊 工作流程

```
用户调用 analyze()
    ↓
检查是否有 llm_client?
    ├─ 有 → _analyze_with_llm()
    │         ↓
    │     构建提示词 (_build_prompt)
    │         ↓
    │     调用LLM API (chat.completions.create)
    │         ↓
    │     解析响应 (_parse_response)
    │         ↓
    │     返回 ContextAnalysis
    │
    └─ 无 → _analyze_mock()
              ↓
          返回预设的模拟结果
```

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

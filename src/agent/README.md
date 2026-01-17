# Agent模块使用说明

## 概述

Agent模块提供了两种实现方式：

1. **原版Agent** (`XunguAgent`) - 直接调用工具函数的实现
2. **LangChain Agent** (`XunguLangChainAgent`) - 基于LangChain框架的实现

## 快速开始

### 使用LangChain Agent（推荐）

```python
from src.agent import XunguLangChainAgent

# 初始化Agent（自动从环境变量读取API Key）
agent = XunguLangChainAgent(
    llm_provider="openai",  # 或 "anthropic"
    verbose=True
)

# 分析训诂句
result = agent.analyze(
    xungu_sentence="崇，终也",
    context="崇朝其雨",
    source="《毛传》"
)

# 查看结果
print(f"分类: {result.classification}")
print(f"置信度: {result.confidence:.0%}")
print(f"推理过程: {result.final_reasoning}")
```

### 使用原版Agent

```python
from src.agent import XunguAgent

agent = XunguAgent(verbose=True)
result = agent.analyze("崇，终也", context="崇朝其雨")
print(result.classification)
```

## 环境配置

### 设置API Key

在项目根目录创建 `.env` 文件：

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
LLM_MODEL=gpt-4-turbo

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxx

# 选择LLM提供商
LLM_PROVIDER=openai  # 或 anthropic
```

### 安装依赖

```bash
pip install langchain langchain-openai langchain-anthropic
```

## 文件说明

- `langchain_agent.py` - LangChain Agent实现
- `xungu_agent.py` - 原版Agent实现（保留用于对比）
- `tool_wrappers.py` - 工具包装器（将工具函数包装为LangChain Tool）
- `llm_client.py` - LLM客户端封装
- `prompts.py` - Prompt模板定义

## 工具说明

Agent可以调用以下工具：

1. `query_word_meaning` - 查询汉字语义
2. `query_phonology` - 查询汉字音韵
3. `check_phonetic_relation` - 比较两字音韵关系
4. `search_textual_evidence` - 检索文献佐证
5. `identify_pattern` - 识别训诂句格式
6. `analyze_context` - 分析语境适配度

## 注意事项

1. **API Key**: 必须设置OPENAI_API_KEY或ANTHROPIC_API_KEY
2. **索引文件**: 使用工具前需要先构建词典索引（见工具文档）
3. **性能**: LangChain Agent可能需要多次工具调用，耗时较长
4. **错误处理**: Agent会自动处理工具调用失败的情况

## 示例

完整示例见 `AGENT_DEVELOPMENT_GUIDE.md`


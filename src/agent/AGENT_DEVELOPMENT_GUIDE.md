# Agent开发指导文档

> **负责人**: 成员B（Agent开发）  
> **更新日期**: 2026-01-17  
> **状态**: 开发中

---

## 📋 目录

1. [项目概述](#项目概述)
2. [项目结构](#项目结构)
3. [已完成功能](#已完成功能)
4. [Agent开发任务](#agent开发任务)
5. [技术实现指南](#技术实现指南)
6. [接口规范](#接口规范)
7. [预期效果](#预期效果)
8. [开发步骤](#开发步骤)
9. [测试与调试](#测试与调试)
10. [常见问题](#常见问题)

---

## 项目概述

### 核心目标

开发一个基于**LangChain框架**的智能Agent，能够：

1. **自动分类**：判断训诂句属于"假借说明"还是"语义解释"
2. **五步推理**：执行完整的五步分析流程
3. **工具调用**：自主调用外部工具获取知识
4. **推理链输出**：提供完整的推理过程和证据

### 系统架构

```
用户输入（训诂句）
    ↓
LangChain Agent
    ├── LLM核心（Claude/GPT-4）
    ├── 工具调用系统
    │   ├── 语义查询工具
    │   ├── 音韵查询工具
    │   ├── 文献检索工具
    │   ├── 训式识别工具
    │   └── 语境分析工具
    └── 推理链管理
    ↓
输出（分类结果 + 推理过程）
```

---

## 项目结构

### 当前目录结构

```
src/
├── agent/                          # Agent核心模块
│   ├── __init__.py                 # ✅ 已存在
│   ├── xungu_agent.py              # ⚠️ 基础框架完成，需重构为LangChain
│   ├── prompts.py                  # ⚠️ 基础Prompt，需优化
│   └── AGENT_DEVELOPMENT_GUIDE.md  # 📄 本文档
│
├── tools/                          # 工具层（已完成）
│   ├── semantic_tool.py           # ✅ 语义查询工具
│   ├── phonology_tool.py           # ✅ 音韵查询工具
│   ├── textual_tool.py            # ✅ 文献检索工具
│   ├── pattern_tool.py            # ✅ 训式识别工具
│   └── context_tool.py            # ⚠️ 框架完成，LLM调用待实现
│
├── config/                         # 配置模块
│   └── settings.py                # ✅ 全局配置
│
└── main.py                         # ✅ 主入口
```

### 需要新增的文件

```
src/agent/
├── langchain_agent.py              # 🆕 LangChain Agent实现
├── tool_wrappers.py                # 🆕 工具包装器（LangChain格式）
├── chains.py                       # 🆕 推理链定义
└── llm_client.py                   # 🆕 LLM客户端封装
```

---

## 已完成功能

### ✅ 数据工程（成员E）

- **词典索引**：`data/processed/dyhdc_index.json`（24.5MB）
- **音韵数据**：`data/processed/phonology_unified.json`
- **测试数据集**：`data/test/test_dataset.json`（60条）
- **评估模块**：`src/evaluation/metrics.py`

### ✅ 工具层（成员C/D）

#### 1. 语义查询工具 (`semantic_tool.py`)

**状态**：✅ 已完成并接入真实数据

**接口**：
```python
from src.tools import query_word_meaning

result = query_word_meaning("崇")
# 返回: {
#     "字": "崇",
#     "本义": "高；高大。",
#     "义项": ["高；高大。", "尊崇", ...],
#     "例句": [...],
#     "假借标注": [...]
# }
```

**使用示例**：
```python
from src.tools import SemanticTool

tool = SemanticTool()
word_meaning = tool.query("崇")
print(word_meaning.primary_meaning)  # "高；高大。"
```

#### 2. 音韵查询工具 (`phonology_tool.py`)

**状态**：✅ 已完成并接入真实数据

**接口**：
```python
from src.tools import query_phonology, check_phonetic_relation

# 查询单字音韵
result = query_phonology("崇")
# 返回: {
#     "字": "崇",
#     "声母": "禅",
#     "韵部": "东",
#     "上古音": "*dzruŋ",
#     "上古音来源": "潘悟云《汉语古音手册》"
# }

# 比较两字音韵关系
relation = check_phonetic_relation("崇", "终")
# 返回: {
#     "is_close": True,
#     "same_yunbu": True,
#     "same_shengmu": False,
#     "analysis": "✅ 【叠韵】(均为东部)"
# }
```

#### 3. 文献检索工具 (`textual_tool.py`)

**状态**：✅ 已完成并接入真实数据

**接口**：
```python
from src.tools import search_textual_evidence

result = search_textual_evidence("崇", "終", context="崇朝其雨")
# 返回: {
#     "有佐证": True,
#     "假借记录": [...],
#     "异文": [...],
#     "总结": "找到2处假借记录"
# }
```

#### 4. 训式识别工具 (`pattern_tool.py`)

**状态**：✅ 已完成（50+训式规则）

**接口**：
```python
from src.tools import identify_pattern

result = identify_pattern("崇，讀為終")
# 返回: {
#     "格式": "读为",
#     "被释字": "崇",
#     "释字": "終",
#     "暗示类型": "假借",
#     "置信度": "极高",
#     "可直接判定": True
# }
```

#### 5. 语境分析工具 (`context_tool.py`)

**状态**：⚠️ 框架完成，LLM调用待实现

**接口**：
```python
from src.tools import analyze_context

result = analyze_context(
    original_sentence="崇朝其雨",
    char_a="崇",
    char_b="终",
    meaning_a="高大",
    meaning_b="终结、整个",
    llm_client=llm_client  # 需要传入LLM客户端
)
# 返回: {
#     "A本义通顺": False,
#     "B本义通顺": True,
#     "结论": "支持假借",
#     "理由": "..."
# }
```

**注意**：当前使用Mock数据，需要实现LLM调用。

### ⚠️ Agent基础框架（成员B）

**状态**：基础框架完成，需要重构为LangChain

**当前实现**：`src/agent/xungu_agent.py`

- ✅ 五步推理流程框架
- ✅ 工具调用接口
- ✅ 结果整合逻辑
- ⚠️ 未使用LangChain框架
- ⚠️ LLM调用未实现
- ⚠️ Prompt需要优化

---

## Agent开发任务

### 核心任务清单

#### 1. LangChain Agent实现 ⭐⭐⭐

**文件**：`src/agent/langchain_agent.py`

**任务**：
- [ ] 创建LangChain Agent类
- [ ] 集成OpenAI/Anthropic LLM
- [ ] 实现工具调用机制
- [ ] 实现五步推理流程
- [ ] 实现综合判断逻辑

**技术要求**：
- 使用 `langchain.agents` 模块
- 支持OpenAI和Anthropic两种LLM
- 工具调用使用 `@tool` 装饰器或 `StructuredTool`

#### 2. 工具包装器 ⭐⭐⭐

**文件**：`src/agent/tool_wrappers.py`

**任务**：
- [ ] 将现有工具函数包装为LangChain Tool
- [ ] 实现工具描述和参数定义
- [ ] 处理工具返回格式

**技术要求**：
- 使用 `langchain.tools` 或 `langchain_core.tools`
- 每个工具需要清晰的描述，供LLM理解何时调用

#### 3. LLM客户端封装 ⭐⭐

**文件**：`src/agent/llm_client.py`

**任务**：
- [ ] 封装OpenAI客户端
- [ ] 封装Anthropic客户端
- [ ] 统一接口，支持切换
- [ ] 实现错误处理和重试

**技术要求**：
- 使用 `langchain-openai` 和 `langchain-anthropic`
- 从 `src.config.settings` 读取配置

#### 4. 推理链定义 ⭐⭐

**文件**：`src/agent/chains.py`

**任务**：
- [ ] 定义五步推理链
- [ ] 实现步骤间的数据传递
- [ ] 实现条件分支逻辑

**技术要求**：
- 使用 `langchain.chains` 或 `langchain.expression_language`
- 支持顺序执行和条件判断

#### 5. Prompt优化 ⭐⭐

**文件**：`src/agent/prompts.py`

**任务**：
- [ ] 优化系统Prompt
- [ ] 优化各步骤Prompt
- [ ] 实现Prompt模板管理
- [ ] 支持多语言（中文）

**技术要求**：
- 使用 `langchain.prompts`
- Prompt需要清晰指导LLM如何调用工具
- 包含示例（Few-shot learning）

#### 6. 语境分析LLM集成 ⭐

**文件**：`src/tools/context_tool.py`

**任务**：
- [ ] 实现 `_analyze_with_llm()` 方法
- [ ] 调用LLM进行语境分析
- [ ] 解析LLM返回结果

**技术要求**：
- 使用统一的LLM客户端
- 实现JSON格式输出解析

---

## 技术实现指南

### 1. LangChain Agent基础结构

```python
# src/agent/langchain_agent.py

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool

from ..tools import (
    query_word_meaning,
    query_phonology,
    check_phonetic_relation,
    search_textual_evidence,
    identify_pattern,
    analyze_context,
)
from .tool_wrappers import (
    semantic_query_tool,
    phonology_query_tool,
    textual_search_tool,
    pattern_identify_tool,
    context_analyze_tool,
)
from .prompts import SYSTEM_PROMPT
from .llm_client import get_llm


class XunguLangChainAgent:
    """基于LangChain的训诂分类Agent"""
    
    def __init__(self, llm_provider: str = "openai", verbose: bool = True):
        """
        初始化Agent
        
        Args:
            llm_provider: "openai" 或 "anthropic"
            verbose: 是否输出详细日志
        """
        self.llm = get_llm(llm_provider)
        self.verbose = verbose
        
        # 创建工具列表
        self.tools = [
            semantic_query_tool,
            phonology_query_tool,
            textual_search_tool,
            pattern_identify_tool,
            context_analyze_tool,
        ]
        
        # 创建Agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
        )
    
    def _create_agent(self):
        """创建LangChain Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        return agent
    
    def analyze(
        self,
        xungu_sentence: str,
        context: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析训诂句
        
        Args:
            xungu_sentence: 训诂句，如"崇，终也"
            context: 上下文，如"崇朝其雨"
            source: 出处，如"《毛传》"
            
        Returns:
            dict: 分析结果
        """
        # 构建输入
        input_text = self._build_input(xungu_sentence, context, source)
        
        # 执行Agent
        result = self.agent_executor.invoke({"input": input_text})
        
        # 解析结果
        return self._parse_result(result)
    
    def _build_input(self, xungu_sentence: str, context: str, source: str) -> str:
        """构建Agent输入"""
        parts = [f"请分析以下训诂句：{xungu_sentence}"]
        if context:
            parts.append(f"上下文：{context}")
        if source:
            parts.append(f"出处：{source}")
        parts.append("\n请按照五步法进行分析，并给出最终判断。")
        return "\n".join(parts)
    
    def _parse_result(self, result: Dict) -> Dict[str, Any]:
        """解析Agent返回结果"""
        # TODO: 实现结果解析
        return result
```

### 2. 工具包装器实现

```python
# src/agent/tool_wrappers.py

from langchain_core.tools import StructuredTool
from typing import Dict, Any, Optional

from ..tools import (
    query_word_meaning,
    query_phonology,
    check_phonetic_relation,
    search_textual_evidence,
    identify_pattern,
    analyze_context,
)


def semantic_query_tool() -> StructuredTool:
    """语义查询工具包装器"""
    return StructuredTool.from_function(
        func=query_word_meaning,
        name="query_word_meaning",
        description="""查询汉字的本义、义项、例句等信息。
        
        使用场景：
        - 需要了解某个字的本义时
        - 需要比较两个字是否义近时
        
        输入：单个汉字（支持繁简体）
        输出：包含本义、义项、例句、假借标注的字典
        
        示例：
        - query_word_meaning("崇") -> 返回"崇"的语义信息
        """,
    )


def phonology_query_tool() -> StructuredTool:
    """音韵查询工具包装器"""
    return StructuredTool.from_function(
        func=query_phonology,
        name="query_phonology",
        description="""查询汉字的上古音信息（声母、韵部、拟音）。
        
        使用场景：
        - 需要了解某个字的上古音时
        - 需要判断两个字是否音近时
        
        输入：单个汉字
        输出：包含声母、韵部、上古音拟音的字典
        
        示例：
        - query_phonology("崇") -> 返回"崇"的音韵信息
        """,
    )


def phonetic_relation_tool() -> StructuredTool:
    """音韵关系比较工具包装器"""
    return StructuredTool.from_function(
        func=check_phonetic_relation,
        name="check_phonetic_relation",
        description="""比较两个字的音韵关系，判断是否音近。
        
        使用场景：
        - 需要判断两个字是否音近时（用于假借或声训判断）
        
        输入：两个字（char1, char2）
        输出：包含is_close、same_yunbu、analysis的字典
        
        示例：
        - check_phonetic_relation("崇", "终") -> 返回音韵关系分析
        """,
    )


def textual_search_tool() -> StructuredTool:
    """文献检索工具包装器"""
    return StructuredTool.from_function(
        func=search_textual_evidence,
        name="search_textual_evidence",
        description="""检索两个字之间的文献佐证（异文、假借记录等）。
        
        使用场景：
        - 需要查找是否有异文佐证时
        - 需要查找词典中的假借标注时
        
        输入：两个字（char_a, char_b）和可选的上下文
        输出：包含是否有佐证、假借记录、异文的字典
        
        示例：
        - search_textual_evidence("崇", "終", context="崇朝其雨")
        """,
    )


def pattern_identify_tool() -> StructuredTool:
    """训式识别工具包装器"""
    return StructuredTool.from_function(
        func=identify_pattern,
        name="identify_pattern",
        description="""识别训诂句的格式，判断使用了什么训释术语。
        
        使用场景：
        - 需要识别训诂句格式时
        - 需要判断训式是否直接暗示假借或语义时
        
        输入：训诂句字符串
        输出：包含格式、被释字、释字、暗示类型、置信度的字典
        
        示例：
        - identify_pattern("崇，讀為終") -> 返回格式识别结果
        """,
    )


def context_analyze_tool() -> StructuredTool:
    """语境分析工具包装器"""
    return StructuredTool.from_function(
        func=analyze_context,
        name="analyze_context",
        description="""分析语境适配度，判断将被释字/释字的本义代入原句后是否通顺。
        
        使用场景：
        - 需要判断语境是否支持假借时
        - 需要判断语境是否支持语义解释时
        
        输入：原句、被释字、释字、两个字的本义
        输出：包含A/B本义通顺性、结论、理由的字典
        
        示例：
        - analyze_context("崇朝其雨", "崇", "终", "高大", "终结、整个")
        """,
    )
```

### 3. LLM客户端封装

```python
# src/agent/llm_client.py

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from ..config import get_settings


def get_llm(provider: str = "openai") -> ChatOpenAI | ChatAnthropic:
    """
    获取LLM客户端
    
    Args:
        provider: "openai" 或 "anthropic"
        
    Returns:
        LLM客户端实例
    """
    settings = get_settings()
    
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,  # 降低随机性，提高一致性
        )
    
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.1,
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

### 4. Prompt优化示例

```python
# src/agent/prompts.py

SYSTEM_PROMPT = """你是一位精通古汉语训诂学的AI专家。你的任务是判断给定的训诂句属于"假借说明"还是"语义解释"（以声通义）。

## 背景知识

训诂学中，声训法分为两大类：

1. **以声通义法（语义解释）**：利用声音相近的词解释词义，揭示语源。特点是"音近义近"。
   - 例："海，晦也"——海因其色黑而晦得名，海和晦音近且义相关。

2. **揭明正借字法（假借说明）**：指出文献中某字是另一字的假借。特点是"音近义远"。
   - 例："崇，终也"——崇是终的借字，两字音近但本义无关。

## 分析流程（五步法）

请按照以下步骤进行分析：

### 第一步：语义关联性分析
1. 使用 `query_word_meaning` 工具查询被释字和释字的本义
2. 判断两字本义是否有语义关联（义近/义远）

### 第二步：语音对应分析
1. 使用 `query_phonology` 工具查询两字的上古音
2. 使用 `check_phonetic_relation` 工具判断是否音近

### 第三步：异文与文例佐证
1. 使用 `search_textual_evidence` 工具检索是否有异文、假借记录等佐证

### 第四步：训诂术语识别
1. 使用 `identify_pattern` 工具识别训诂句格式
2. 判断该格式是否直接暗示假借或语义

### 第五步：语境适配度分析
1. 如果有上下文，使用 `analyze_context` 工具分析语境适配度
2. 判断哪个本义代入原句更通顺

## 判断规则

- **假借说明**：义远 + 音近 + (有异文 OR 训式暗示假借 OR 语境支持假借)
- **语义解释**：义近 + 音近 + (训式暗示语义 OR 语境支持语义)

## 输出格式

请按以下JSON格式输出最终结果：

{
    "classification": "假借说明" 或 "语义解释",
    "confidence": 0.0-1.0,
    "reasoning": {
        "step1": "语义分析结果",
        "step2": "音韵分析结果",
        "step3": "文献佐证结果",
        "step4": "训式识别结果",
        "step5": "语境分析结果"
    },
    "final_judgment": "综合判断理由"
}
"""

# 各步骤的详细Prompt可以单独定义
STEP1_PROMPT = """请分析"{char_a}"和"{char_b}"的语义关联性。

请使用以下工具：
1. query_word_meaning("{char_a}") - 查询被释字的本义
2. query_word_meaning("{char_b}") - 查询释字的本义

然后判断：这两个字的本义是否有语义关联？
- 如果本义属于同一语义场、有引申关系、或存在语源关系 → 义近
- 如果本义完全无关 → 义远
"""
```

---

## 接口规范

### Agent接口

```python
class XunguLangChainAgent:
    def analyze(
        self,
        xungu_sentence: str,
        context: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析训诂句
        
        Returns:
            {
                "input": {
                    "训诂句": "...",
                    "被释字": "...",
                    "释字": "...",
                    "上下文": "...",
                    "出处": "..."
                },
                "classification": "假借说明" 或 "语义解释",
                "confidence": 0.0-1.0,
                "reasoning": {
                    "step1_semantic": {...},
                    "step2_phonetic": {...},
                    "step3_textual": {...},
                    "step4_pattern": {...},
                    "step5_context": {...}
                },
                "final_judgment": "..."
            }
        """
```

### 工具接口规范

所有工具必须：
1. 返回字典格式
2. 包含清晰的错误处理
3. 支持繁简体输入
4. 提供详细的工具描述（供LLM理解）

---

## 预期效果

### 功能效果

1. **自动工具调用**：Agent能够根据分析需要，自主调用合适的工具
2. **完整推理链**：输出五步分析的详细过程和结果
3. **准确分类**：在测试集上达到较高准确率（目标：>80%）
4. **可解释性**：每个判断都有清晰的证据和理由

### 性能指标

- **准确率**：>80%
- **F1分数**：>0.75
- **推理时间**：单条分析 < 30秒
- **工具调用成功率**：>95%

### 输出示例

```json
{
    "input": {
        "训诂句": "崇，终也",
        "被释字": "崇",
        "释字": "终",
        "上下文": "崇朝其雨",
        "出处": "《毛传》"
    },
    "classification": "假借说明",
    "confidence": 0.95,
    "reasoning": {
        "step1_semantic": {
            "结论": "义远",
            "A本义": "高；高大。",
            "B本义": "终结、完整",
            "分析": "高大与终结无语义关联链条"
        },
        "step2_phonetic": {
            "结论": "音近",
            "A音韵": {"声母": "禅", "韵部": "东", "上古音": "*dzruŋ"},
            "B音韵": {"声母": "章", "韵部": "东", "上古音": "*tjuŋ"},
            "分析": "✅ 【叠韵】(均为东部)"
        },
        "step3_textual": {
            "结论": "有佐证",
            "假借记录": ["12通\"終\"。终尽。参见\"崇朝\"。"],
            "分析": "找到1处假借记录"
        },
        "step4_pattern": {
            "结论": "不确定",
            "格式": "A也",
            "置信度": "低",
            "分析": "基本训式，需综合判断"
        },
        "step5_context": {
            "结论": "支持假借",
            "A本义通顺": false,
            "B本义通顺": true,
            "分析": "借字本义不通，正字本义通顺"
        }
    },
    "final_judgment": "义远+音近+有异文+语境支持假借 → 判定为【假借说明】"
}
```

---

## 开发步骤

### Phase 1: 基础搭建（1-2天）

1. **环境配置**
   ```bash
   pip install langchain langchain-openai langchain-anthropic
   ```

2. **创建基础文件**
   - `src/agent/langchain_agent.py`
   - `src/agent/tool_wrappers.py`
   - `src/agent/llm_client.py`

3. **实现LLM客户端**
   - 测试OpenAI和Anthropic连接
   - 验证API Key配置

### Phase 2: 工具集成（1-2天）

1. **包装现有工具**
   - 将5个工具函数包装为LangChain Tool
   - 编写清晰的工具描述

2. **测试工具调用**
   - 单独测试每个工具
   - 验证工具返回格式

### Phase 3: Agent实现（2-3天）

1. **创建Agent**
   - 使用 `create_openai_tools_agent` 或 `create_anthropic_tools_agent`
   - 配置Prompt

2. **实现五步推理**
   - 在Prompt中指导LLM按步骤调用工具
   - 实现结果解析

3. **实现综合判断**
   - 在Agent中实现判断逻辑
   - 或让LLM根据规则自行判断

### Phase 4: 优化与测试（2-3天）

1. **Prompt优化**
   - 根据测试结果调整Prompt
   - 添加Few-shot示例

2. **错误处理**
   - 处理工具调用失败
   - 处理LLM解析错误

3. **性能优化**
   - 减少不必要的工具调用
   - 优化Prompt长度

### Phase 5: 集成测试（1-2天）

1. **运行测试集**
   ```python
   from src.evaluation import load_test_dataset
   from src.agent import XunguLangChainAgent
   
   dataset = load_test_dataset()
   agent = XunguLangChainAgent()
   
   for case in dataset:
       result = agent.analyze(
           case.xungu_sentence,
           case.context,
           case.source
       )
       # 评估结果
   ```

2. **错误分析**
   - 分析分类错误的案例
   - 找出问题原因（工具错误/LLM错误/逻辑错误）

3. **迭代优化**
   - 根据错误分析调整Prompt和逻辑
   - 重新测试

---

## 测试与调试

### 单元测试

```python
# tests/test_langchain_agent.py

def test_agent_basic():
    """测试Agent基本功能"""
    agent = XunguLangChainAgent(verbose=False)
    result = agent.analyze("崇，终也", context="崇朝其雨")
    
    assert "classification" in result
    assert result["classification"] in ["假借说明", "语义解释"]
    assert "reasoning" in result

def test_tool_calling():
    """测试工具调用"""
    # 测试每个工具是否能被正确调用
    pass
```

### 调试技巧

1. **启用详细日志**
   ```python
   agent = XunguLangChainAgent(verbose=True)
   ```

2. **检查工具调用**
   - 查看Agent的 `agent_scratchpad` 了解工具调用过程

3. **测试单个工具**
   ```python
   from src.agent.tool_wrappers import semantic_query_tool
   tool = semantic_query_tool()
   result = tool.invoke({"char": "崇"})
   print(result)
   ```

---

## 常见问题

### Q1: LangChain版本兼容性问题

**问题**：不同版本的LangChain API可能不同

**解决**：
- 使用 `langchain>=0.1.0`
- 参考官方文档：https://python.langchain.com/

### Q2: 工具调用失败

**问题**：Agent无法正确调用工具

**解决**：
1. 检查工具描述是否清晰
2. 检查工具参数格式是否正确
3. 在Prompt中添加工具使用示例

### Q3: LLM返回格式不一致

**问题**：LLM返回的JSON格式不规范

**解决**：
1. 使用 `output_parser` 解析结果
2. 在Prompt中明确要求JSON格式
3. 实现容错解析逻辑

### Q4: 推理时间过长

**问题**：单条分析耗时过长

**解决**：
1. 优化Prompt，减少不必要的工具调用
2. 并行调用不相关的工具
3. 缓存工具查询结果

### Q5: 准确率不高

**问题**：测试集准确率低于预期

**解决**：
1. 分析错误案例，找出问题模式
2. 优化Prompt，添加更多示例
3. 调整判断规则
4. 考虑使用更强的LLM模型

---

## 参考资料

### LangChain文档

- 官方文档：https://python.langchain.com/
- Agent教程：https://python.langchain.com/docs/modules/agents/
- 工具调用：https://python.langchain.com/docs/modules/tools/

### 项目文档

- `docs/ARCHITECTURE.md` - 系统架构
- `docs/TOOLS_API_C.md` - 工具API文档
- `docs/IMPLEMENTATION_GUIDE.md` - 实现指南

### 代码参考

- `src/agent/xungu_agent.py` - 当前Agent实现（可参考）
- `src/tools/` - 工具层实现（需要包装）

---

## 开发时间表

| 阶段 | 任务 | 预估时间 | 状态 |
|------|------|:--------:|:----:|
| Phase 1 | 基础搭建 | 1-2天 | 📋 |
| Phase 2 | 工具集成 | 1-2天 | 📋 |
| Phase 3 | Agent实现 | 2-3天 | 📋 |
| Phase 4 | 优化与测试 | 2-3天 | 📋 |
| Phase 5 | 集成测试 | 1-2天 | 📋 |
| **总计** | | **7-12天** | |

---

## 联系方式

如有问题，请联系：
- 成员B（Agent开发）
- 成员C/D（工具层）
- 成员E（数据工程）

---

*本文档将随开发进展持续更新*


"""
Agent模块 - 核心推理引擎

负责人：成员D（原版）、成员B（LangChain版）
"""

from .xungu_agent import XunguAgent, AnalysisResult
from .langchain_agent import XunguLangChainAgent, analyze_with_langchain
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT
from .llm_client import get_llm
from .tool_wrappers import get_all_tools

__all__ = [
    # 原版Agent
    "XunguAgent",
    "AnalysisResult",
    # LangChain版Agent
    "XunguLangChainAgent",
    "analyze_with_langchain",
    # Prompt
    "SYSTEM_PROMPT",
    "REASONING_PROMPT",
    # 工具
    "get_llm",
    "get_all_tools",
]

"""
Agent模块 - 核心推理引擎

负责人：成员B（LangChain版）
"""

from .xungu_agent import XunguAgent, AnalysisResult, analyze
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT
from .llm_client import get_llm
from .tool_wrappers import get_all_tools

__all__ = [
    # Agent核心类
    "XunguAgent",
    "AnalysisResult",
    "analyze",
    # Prompt
    "SYSTEM_PROMPT",
    "REASONING_PROMPT",
    # 工具
    "get_llm",
    "get_all_tools",
]

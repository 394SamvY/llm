"""
工具模块 - 提供Agent调用的各种工具函数

包含五个核心工具，对应五步推理：
1. semantic_tool: 语义查询工具（第一步：语义关联性）
2. phonology_tool: 音韵查询工具（第二步：语音对应）
3. textual_tool: 文献检索工具（第三步：异文佐证）
4. pattern_tool: 训式识别工具（第四步：训诂术语）
5. context_tool: 语境分析工具（第五步：语境适配度）
"""

from .semantic_tool import query_word_meaning, SemanticTool
from .phonology_tool import query_phonology, PhonologyTool
from .textual_tool import search_textual_evidence, TextualTool
from .pattern_tool import identify_pattern, PatternTool
from .context_tool import analyze_context, ContextTool

__all__ = [
    # 函数式接口
    "query_word_meaning",
    "query_phonology", 
    "search_textual_evidence",
    "identify_pattern",
    "analyze_context",
    # 类式接口
    "SemanticTool",
    "PhonologyTool",
    "TextualTool",
    "PatternTool",
    "ContextTool",
]

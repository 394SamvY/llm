"""
工具包装器 - 将现有工具函数包装为LangChain Tool格式

这些工具将被LangChain Agent调用
"""
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
- query_word_meaning("崇") -> 返回"崇"的语义信息，包括本义"高；高大。"
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
- query_phonology("崇") -> 返回"崇"的音韵信息，包括声母"禅"、韵部"东"、上古音"*dzruŋ"
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
输出：包含is_close、same_yunbu、same_shengmu、analysis的字典

示例：
- check_phonetic_relation("崇", "终") -> 返回音韵关系分析，判断是否音近
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

输入：两个字（char_a, char_b）和可选的上下文（context）
输出：包含是否有佐证、假借记录、异文的字典

示例：
- search_textual_evidence("崇", "終", context="崇朝其雨") -> 返回文献佐证信息
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
- identify_pattern("崇，讀為終") -> 返回格式识别结果，暗示类型为"假借"
""",
    )


def context_analyze_tool() -> StructuredTool:
    """语境分析工具包装器"""
    # 创建一个包装函数，忽略llm_client参数（在LangChain中通过其他方式处理）
    def analyze_context_wrapper(
        original_sentence: str,
        char_a: str,
        char_b: str,
        meaning_a: str,
        meaning_b: str
    ) -> Dict[str, Any]:
        """包装函数，调用analyze_context但忽略llm_client"""
        return analyze_context(
            original_sentence=original_sentence,
            char_a=char_a,
            char_b=char_b,
            meaning_a=meaning_a,
            meaning_b=meaning_b,
            llm_client=None  # LangChain Agent会通过其他方式处理LLM调用
        )
    
    return StructuredTool.from_function(
        func=analyze_context_wrapper,
        name="analyze_context",
        description="""分析语境适配度，判断将被释字/释字的本义代入原句后是否通顺。
        
使用场景：
- 需要判断语境是否支持假借时
- 需要判断语境是否支持语义解释时

输入参数：
- original_sentence: 原始句子（字符串）
- char_a: 被释字（字符串）
- char_b: 释字（字符串）
- meaning_a: 被释字的本义（字符串）
- meaning_b: 释字的本义（字符串）

输出：包含A/B本义通顺性、结论、理由的字典

示例：
- analyze_context("崇朝其雨", "崇", "终", "高大", "终结、整个") -> 返回语境分析结果
""",
    )


# 获取所有工具的列表
def get_all_tools() -> list[StructuredTool]:
    """获取所有工具列表"""
    return [
        semantic_query_tool(),
        phonology_query_tool(),
        phonetic_relation_tool(),
        textual_search_tool(),
        pattern_identify_tool(),
        context_analyze_tool(),
    ]


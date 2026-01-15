"""
语境分析工具 - 第五步：语境适配度分析

功能：判断将被释字/释字的本义代入原句后是否通顺
实现：调用LLM进行语义分析
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class ContextAnalysis:
    """语境分析结果"""
    char_a_fits: bool  # 被释字本义代入是否通顺
    char_b_fits: bool  # 释字本义代入是否通顺
    char_a_interpretation: str  # 用A本义的解释
    char_b_interpretation: str  # 用B本义的解释
    conclusion: str  # 结论：支持假借/支持语义/不确定
    reasoning: str  # 推理说明


class ContextTool:
    """
    语境分析工具类
    
    负责人：成员D（Agent开发者，因为需要调用LLM）
    
    使用方法：
        tool = ContextTool(llm_client)
        result = tool.analyze(
            original_sentence="崇朝其雨",
            char_a="崇",
            char_b="终",
            meaning_a="高大",
            meaning_b="终结、整个"
        )
        print(result.conclusion)  # "支持假借"
    """
    
    def __init__(self, llm_client=None):
        """
        初始化工具
        
        Args:
            llm_client: LLM客户端（OpenAI/Anthropic），如果不提供则使用模拟
        """
        self.llm_client = llm_client
    
    def analyze(
        self,
        original_sentence: str,
        char_a: str,
        char_b: str,
        meaning_a: str,
        meaning_b: str
    ) -> ContextAnalysis:
        """
        分析语境适配度
        
        Args:
            original_sentence: 原始句子
            char_a: 被释字
            char_b: 释字
            meaning_a: A的本义
            meaning_b: B的本义
            
        Returns:
            ContextAnalysis: 分析结果
        """
        if self.llm_client is not None:
            return self._analyze_with_llm(
                original_sentence, char_a, char_b, meaning_a, meaning_b
            )
        else:
            return self._analyze_mock(
                original_sentence, char_a, char_b, meaning_a, meaning_b
            )
    
    def _analyze_with_llm(
        self,
        original_sentence: str,
        char_a: str,
        char_b: str,
        meaning_a: str,
        meaning_b: str
    ) -> ContextAnalysis:
        """
        使用LLM进行分析
        
        TODO: 实现此方法
        """
        prompt = self._build_prompt(
            original_sentence, char_a, char_b, meaning_a, meaning_b
        )
        
        # ===== TODO: 调用LLM =====
        # response = self.llm_client.chat.completions.create(
        #     model="gpt-4-turbo",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return self._parse_response(response.choices[0].message.content)
        
        # 临时返回模拟结果
        return self._analyze_mock(
            original_sentence, char_a, char_b, meaning_a, meaning_b
        )
    
    def _build_prompt(
        self,
        original_sentence: str,
        char_a: str,
        char_b: str,
        meaning_a: str,
        meaning_b: str
    ) -> str:
        """构建LLM提示词"""
        return f"""你是一位古汉语专家。请分析以下句子中，用不同字义代入后的语义通顺度。

原句：{original_sentence}

分析任务：
1. 将"{char_a}"按其本义"{meaning_a}"理解，判断句子是否通顺
2. 将"{char_a}"理解为"{char_b}"（本义：{meaning_b}），判断句子是否通顺

请按以下JSON格式输出：
{{
    "char_a_fits": true/false,  // A的本义代入是否通顺
    "char_b_fits": true/false,  // B的本义代入是否通顺
    "char_a_interpretation": "用A本义的句子解释",
    "char_b_interpretation": "用B本义的句子解释",
    "conclusion": "支持假借/支持语义/不确定",
    "reasoning": "判断理由"
}}

注意：
- 如果A的本义不通、B的本义通顺，则"支持假借"
- 如果A和B都通顺，则"支持语义"
- 其他情况为"不确定"
"""
    
    def _analyze_mock(
        self,
        original_sentence: str,
        char_a: str,
        char_b: str,
        meaning_a: str,
        meaning_b: str
    ) -> ContextAnalysis:
        """
        模拟分析（用于测试）
        
        基于预设的一些案例返回结果
        """
        # 预设案例
        mock_cases = {
            ("崇朝其雨", "崇", "终"): ContextAnalysis(
                char_a_fits=False,
                char_b_fits=True,
                char_a_interpretation="'高大早晨下雨'，语义不通",
                char_b_interpretation="'整个早晨下雨'，语义通顺",
                conclusion="支持假借",
                reasoning="被释字'崇'的本义'高大'代入原句不通顺，而释字'终'的本义'终结、整个'代入后通顺，符合假借特征"
            ),
            ("瞻卬昊天，云如何崇", "崇", "终"): ContextAnalysis(
                char_a_fits=True,
                char_b_fits=False,
                char_a_interpretation="'仰望苍天，云是多么高啊'，语义通顺",
                char_b_interpretation="'仰望苍天，云是多么终结'，语义不通",
                conclusion="支持语义",
                reasoning="这里'崇'用的是本义'高大'，不是假借为'终'"
            ),
        }
        
        key = (original_sentence, char_a, char_b)
        if key in mock_cases:
            return mock_cases[key]
        
        # 默认返回不确定
        return ContextAnalysis(
            char_a_fits=True,
            char_b_fits=True,
            char_a_interpretation=f"用'{meaning_a}'理解：待分析",
            char_b_interpretation=f"用'{meaning_b}'理解：待分析",
            conclusion="不确定",
            reasoning="需要更多上下文信息或专业判断"
        )


# ===== 函数式接口 =====

_tool_instance: Optional[ContextTool] = None


def analyze_context(
    original_sentence: str,
    char_a: str,
    char_b: str,
    meaning_a: str,
    meaning_b: str,
    llm_client=None
) -> Dict[str, Any]:
    """
    语境分析的函数式接口
    
    Args:
        original_sentence: 原始句子
        char_a: 被释字
        char_b: 释字
        meaning_a: A的本义
        meaning_b: B的本义
        llm_client: LLM客户端（可选）
        
    Returns:
        dict: {
            "A本义通顺": True/False,
            "B本义通顺": True/False,
            "A解释": "...",
            "B解释": "...",
            "结论": "支持假借/支持语义/不确定",
            "理由": "..."
        }
        
    Example:
        >>> result = analyze_context("崇朝其雨", "崇", "终", "高大", "终结")
        >>> print(result["结论"])
        "支持假借"
    """
    global _tool_instance
    if _tool_instance is None or llm_client is not None:
        _tool_instance = ContextTool(llm_client)
    
    analysis = _tool_instance.analyze(
        original_sentence, char_a, char_b, meaning_a, meaning_b
    )
    
    return {
        "A本义通顺": analysis.char_a_fits,
        "B本义通顺": analysis.char_b_fits,
        "A解释": analysis.char_a_interpretation,
        "B解释": analysis.char_b_interpretation,
        "结论": analysis.conclusion,
        "理由": analysis.reasoning
    }


# ===== 测试代码 =====
if __name__ == "__main__":
    result = analyze_context(
        original_sentence="崇朝其雨",
        char_a="崇",
        char_b="终",
        meaning_a="高大",
        meaning_b="终结、整个"
    )
    print("语境分析结果:")
    for k, v in result.items():
        print(f"  {k}: {v}")

"""
训诂分类Agent - 核心类

负责人：成员D

功能：
- 接收训诂句输入
- 调用五个工具进行五步分析
- 整合结果，输出分类和推理链
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json

from ..tools import (
    query_word_meaning,
    query_phonology,
    search_textual_evidence,
    identify_pattern,
    analyze_context,
)
from ..tools.phonology_tool import check_phonetic_relation
from .prompts import SYSTEM_PROMPT, REASONING_PROMPT


@dataclass
class AnalysisResult:
    """分析结果"""
    # 输入
    xungu_sentence: str
    char_a: str
    char_b: str
    context: Optional[str] = None
    source: Optional[str] = None
    
    # 分类结果
    classification: str = ""  # "假借说明" 或 "语义解释"
    confidence: float = 0.0
    
    # 五步推理
    step1_semantic: Dict = field(default_factory=dict)
    step2_phonetic: Dict = field(default_factory=dict)
    step3_textual: Dict = field(default_factory=dict)
    step4_pattern: Dict = field(default_factory=dict)
    step5_context: Dict = field(default_factory=dict)
    
    # 最终判断
    final_reasoning: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "input": {
                "训诂句": self.xungu_sentence,
                "被释字": self.char_a,
                "释字": self.char_b,
                "上下文": self.context,
                "出处": self.source
            },
            "classification": self.classification,
            "confidence": self.confidence,
            "reasoning": {
                "step1_semantic": self.step1_semantic,
                "step2_phonetic": self.step2_phonetic,
                "step3_textual": self.step3_textual,
                "step4_pattern": self.step4_pattern,
                "step5_context": self.step5_context
            },
            "final_reasoning": self.final_reasoning
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class XunguAgent:
    """
    训诂分类Agent
    
    使用方法：
        agent = XunguAgent()
        result = agent.analyze("崇，终也", context="崇朝其雨")
        print(result.classification)  # "假借说明"
    """
    
    def __init__(self, llm_client=None, verbose: bool = True):
        """
        初始化Agent
        
        Args:
            llm_client: LLM客户端（OpenAI/Anthropic），用于第五步和综合判断
            verbose: 是否输出详细日志
        """
        self.llm_client = llm_client
        self.verbose = verbose
    
    def analyze(
        self,
        xungu_sentence: str,
        context: Optional[str] = None,
        source: Optional[str] = None
    ) -> AnalysisResult:
        """
        分析训诂句
        
        Args:
            xungu_sentence: 训诂句，如"崇，终也"
            context: 上下文/原句，如"崇朝其雨"
            source: 出处，如"《毛传》"
            
        Returns:
            AnalysisResult: 完整的分析结果
        """
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"开始分析: {xungu_sentence}")
            print(f"{'='*50}")
        
        # 第0步：识别训诂句格式，提取被释字和释字
        pattern_result = identify_pattern(xungu_sentence)
        char_a = pattern_result["被释字"]
        char_b = pattern_result["释字"]
        
        if self.verbose:
            print(f"\n[预处理] 被释字: {char_a}, 释字: {char_b}")
        
        # 创建结果对象
        result = AnalysisResult(
            xungu_sentence=xungu_sentence,
            char_a=char_a,
            char_b=char_b,
            context=context,
            source=source
        )
        
        # 五步分析
        result.step1_semantic = self._step1_semantic(char_a, char_b)
        result.step2_phonetic = self._step2_phonetic(char_a, char_b)
        result.step3_textual = self._step3_textual(char_a, char_b)
        result.step4_pattern = self._step4_pattern(xungu_sentence, pattern_result)
        result.step5_context = self._step5_context(
            context, char_a, char_b,
            result.step1_semantic.get("A本义", ""),
            result.step1_semantic.get("B本义", "")
        )
        
        # 综合判断
        result.classification, result.confidence, result.final_reasoning = \
            self._final_judgment(result)
        
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"最终判断: {result.classification} (置信度: {result.confidence})")
            print(f"{'='*50}")
        
        return result
    
    def _step1_semantic(self, char_a: str, char_b: str) -> Dict:
        """第一步：语义关联性分析"""
        if self.verbose:
            print(f"\n[Step 1] 语义关联性分析...")
        
        meaning_a = query_word_meaning(char_a)
        meaning_b = query_word_meaning(char_b)
        
        # 简单判断：如果本义完全不相关，则认为义远
        # TODO: 可以用LLM做更精细的判断
        primary_a = meaning_a.get("本义", "")
        primary_b = meaning_b.get("本义", "")
        
        # 简单启发式：检查是否有相同的字
        is_related = any(c in primary_b for c in primary_a if c not in "的之也")
        
        result = {
            "结论": "义近" if is_related else "义远",
            "A本义": primary_a,
            "B本义": primary_b,
            "A义项": meaning_a.get("义项", []),
            "B义项": meaning_b.get("义项", []),
            "分析": f"'{char_a}'本义'{primary_a}'与'{char_b}'本义'{primary_b}'"
                    + ("有语义关联" if is_related else "无明显语义关联")
        }
        
        if self.verbose:
            print(f"    {char_a}本义: {primary_a}")
            print(f"    {char_b}本义: {primary_b}")
            print(f"    结论: {result['结论']}")
        
        return result
    
    def _step2_phonetic(self, char_a: str, char_b: str) -> Dict:
        """第二步：语音对应分析"""
        if self.verbose:
            print(f"\n[Step 2] 语音对应分析...")
        
        relation = check_phonetic_relation(char_a, char_b)
        
        result = {
            "结论": "音近" if relation["is_close"] else "音远",
            "A音韵": relation["char1_info"],
            "B音韵": relation["char2_info"],
            "同韵部": relation["same_yunbu"],
            "同声母": relation["same_shengmu"],
            "分析": relation["analysis"]
        }
        
        if self.verbose:
            print(f"    {char_a}: {relation['char1_info']}")
            print(f"    {char_b}: {relation['char2_info']}")
            print(f"    结论: {result['结论']} ({result['分析']})")
        
        return result
    
    def _step3_textual(self, char_a: str, char_b: str) -> Dict:
        """第三步：异文与文例佐证"""
        if self.verbose:
            print(f"\n[Step 3] 异文与文例检索...")
        
        evidence = search_textual_evidence(char_a, char_b)
        
        result = {
            "结论": "有佐证" if evidence["有佐证"] else "无佐证",
            "异文": evidence.get("异文", []),
            "假借记录": evidence.get("假借记录", []),
            "分析": evidence.get("总结", "")
        }
        
        if self.verbose:
            print(f"    结论: {result['结论']}")
            print(f"    详情: {result['分析']}")
        
        return result
    
    def _step4_pattern(self, sentence: str, pattern_result: Dict) -> Dict:
        """第四步：训诂术语识别"""
        if self.verbose:
            print(f"\n[Step 4] 训式识别...")
        
        result = {
            "结论": pattern_result["暗示类型"],
            "格式": pattern_result["格式"],
            "置信度": pattern_result["置信度"],
            "可直接判定": pattern_result["可直接判定"],
            "分析": pattern_result["说明"]
        }
        
        if self.verbose:
            print(f"    格式: {result['格式']}")
            print(f"    暗示类型: {result['结论']} (置信度: {result['置信度']})")
        
        return result
    
    def _step5_context(
        self,
        context: Optional[str],
        char_a: str,
        char_b: str,
        meaning_a: str,
        meaning_b: str
    ) -> Dict:
        """第五步：语境适配度分析"""
        if self.verbose:
            print(f"\n[Step 5] 语境适配度分析...")
        
        if not context:
            result = {
                "结论": "不确定",
                "分析": "未提供上下文，无法进行语境分析"
            }
        else:
            analysis = analyze_context(
                context, char_a, char_b, meaning_a, meaning_b,
                llm_client=self.llm_client
            )
            result = {
                "结论": analysis["结论"],
                "A通顺": analysis["A本义通顺"],
                "B通顺": analysis["B本义通顺"],
                "A解释": analysis["A解释"],
                "B解释": analysis["B解释"],
                "分析": analysis["理由"]
            }
        
        if self.verbose:
            print(f"    结论: {result['结论']}")
            print(f"    分析: {result.get('分析', '')}")
        
        return result
    
    def _final_judgment(self, result: AnalysisResult) -> tuple:
        """
        综合五步结果，做出最终判断
        
        Returns:
            (classification, confidence, reasoning)
        """
        # 提取各步结论
        semantic = result.step1_semantic.get("结论", "")
        phonetic = result.step2_phonetic.get("结论", "")
        textual = result.step3_textual.get("结论", "")
        pattern = result.step4_pattern.get("结论", "")
        pattern_direct = result.step4_pattern.get("可直接判定", False)
        context = result.step5_context.get("结论", "")
        
        # 判断逻辑
        classification = "不确定"
        confidence = 0.5
        reasons = []
        
        # 规则1：训式可以直接判定
        if pattern_direct:
            if pattern == "假借":
                classification = "假借说明"
                confidence = 0.9
                reasons.append(f"训式'{result.step4_pattern.get('格式')}'直接暗示假借")
            elif pattern == "语义解释":
                classification = "语义解释"
                confidence = 0.9
                reasons.append(f"训式'{result.step4_pattern.get('格式')}'直接暗示语义解释")
        
        # 规则2：义远 + 音近 + 有佐证 → 假借
        if semantic == "义远" and phonetic == "音近":
            if textual == "有佐证":
                classification = "假借说明"
                confidence = max(confidence, 0.95)
                reasons.append("义远+音近+有异文佐证")
            elif context == "支持假借":
                classification = "假借说明"
                confidence = max(confidence, 0.85)
                reasons.append("义远+音近+语境支持")
        
        # 规则3：义近 + 音近 → 可能是以声通义
        if semantic == "义近" and phonetic == "音近":
            if pattern == "以声通义":
                classification = "语义解释"
                confidence = max(confidence, 0.85)
                reasons.append("义近+音近+训式暗示以声通义")
            elif context == "支持语义":
                classification = "语义解释"
                confidence = max(confidence, 0.8)
                reasons.append("义近+音近+语境支持")
        
        # 规则4：默认处理
        if classification == "不确定":
            if pattern in ["假借", "可能假借"]:
                classification = "假借说明"
                confidence = 0.6
                reasons.append("训式倾向假借，但证据不足")
            elif pattern in ["语义解释", "以声通义"]:
                classification = "语义解释"
                confidence = 0.6
                reasons.append("训式倾向语义，但证据不足")
            else:
                # 默认偏向语义解释（更保守的判断）
                classification = "语义解释"
                confidence = 0.5
                reasons.append("证据不充分，保守判断为语义解释")
        
        reasoning = "；".join(reasons)
        
        return classification, confidence, reasoning


# ===== 便捷函数 =====

def analyze(
    xungu_sentence: str,
    context: Optional[str] = None,
    source: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    分析训诂句的便捷函数
    
    Args:
        xungu_sentence: 训诂句
        context: 上下文
        source: 出处
        verbose: 是否输出详细日志
        
    Returns:
        dict: 分析结果
        
    Example:
        >>> result = analyze("崇，终也", context="崇朝其雨")
        >>> print(result["classification"])
        "假借说明"
    """
    agent = XunguAgent(verbose=verbose)
    result = agent.analyze(xungu_sentence, context, source)
    return result.to_dict()


# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试Agent
    agent = XunguAgent(verbose=True)
    
    # 测试案例1：假借
    result = agent.analyze(
        "崇，终也",
        context="崇朝其雨",
        source="《毛传》"
    )
    print("\n" + "=" * 50)
    print("完整结果:")
    print(result.to_json())
    
    # 测试案例2：语义解释
    print("\n" + "=" * 70)
    result2 = agent.analyze(
        "海，晦也",
        context="海，晦也，主承秽浊，其色黑而晦也",
        source="《释名》"
    )
    print("\n完整结果:")
    print(result2.to_json())

"""
基于LangChain的训诂分类Agent

将原有的XunguAgent重构为使用LangChain框架实现
"""
from typing import Dict, Any, Optional
import json
import re

from langchain.agents import AgentExecutor, create_openai_tools_agent, create_anthropic_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from .llm_client import get_llm
from .tool_wrappers import get_all_tools
from .prompts import SYSTEM_PROMPT
from .xungu_agent import AnalysisResult


class XunguLangChainAgent:
    """
    基于LangChain的训诂分类Agent
    
    使用方法：
        agent = XunguLangChainAgent(llm_provider="openai", verbose=True)
        result = agent.analyze("崇，终也", context="崇朝其雨")
        print(result.classification)  # "假借说明"
    """
    
    def __init__(
        self, 
        llm_provider: Optional[str] = None,
        verbose: bool = True,
        max_iterations: int = 15,
        max_execution_time: Optional[int] = None
    ):
        """
        初始化Agent
        
        Args:
            llm_provider: "openai" 或 "anthropic"，如果为None则从配置自动选择
            verbose: 是否输出详细日志
            max_iterations: 最大迭代次数（工具调用次数）
            max_execution_time: 最大执行时间（秒）
        """
        self.llm = get_llm(llm_provider)
        self.verbose = verbose
        self.llm_provider = llm_provider or "openai"
        
        # 创建工具列表
        self.tools = get_all_tools()
        
        # 创建Agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            max_execution_time=max_execution_time,
        )
    
    def _create_agent(self):
        """创建LangChain Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 根据provider选择不同的agent创建函数
        if self.llm_provider == "anthropic":
            agent = create_anthropic_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt,
            )
        else:
            # 默认使用OpenAI
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
    ) -> AnalysisResult:
        """
        分析训诂句
        
        Args:
            xungu_sentence: 训诂句，如"崇，终也"
            context: 上下文，如"崇朝其雨"
            source: 出处，如"《毛传》"
            
        Returns:
            AnalysisResult: 完整的分析结果
        """
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"开始分析: {xungu_sentence}")
            if context:
                print(f"上下文: {context}")
            if source:
                print(f"出处: {source}")
            print(f"{'='*50}")
        
        # 构建Agent输入
        input_text = self._build_input(xungu_sentence, context, source)
        
        # 执行Agent
        try:
            result = self.agent_executor.invoke({"input": input_text})
            output = result.get("output", "")
        except Exception as e:
            if self.verbose:
                print(f"Agent执行出错: {e}")
            output = f"分析过程中出现错误: {str(e)}"
        
        # 解析结果
        analysis_result = self._parse_result(
            xungu_sentence, context, source, output
        )
        
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"最终判断: {analysis_result.classification} (置信度: {analysis_result.confidence:.0%})")
            print(f"{'='*50}")
        
        return analysis_result
    
    def _build_input(
        self, 
        xungu_sentence: str, 
        context: Optional[str], 
        source: Optional[str]
    ) -> str:
        """构建Agent输入"""
        parts = [
            f"请分析以下训诂句：{xungu_sentence}",
            "",
            "请按照五步法进行分析：",
            "",
            "第一步：语义关联性分析",
            "- 使用 query_word_meaning 工具查询被释字和释字的本义",
            "- 判断两字本义是否有语义关联（义近/义远）",
            "",
            "第二步：语音对应分析",
            "- 使用 query_phonology 工具查询两字的上古音",
            "- 使用 check_phonetic_relation 工具判断是否音近",
            "",
            "第三步：异文与文例佐证",
            "- 使用 search_textual_evidence 工具检索是否有异文、假借记录等佐证",
            "",
            "第四步：训诂术语识别",
            "- 使用 identify_pattern 工具识别训诂句格式",
            "- 判断该格式是否直接暗示假借或语义",
            "",
            "第五步：语境适配度分析",
        ]
        
        if context:
            parts.append(f"- 使用 analyze_context 工具分析语境适配度（上下文：{context}）")
        else:
            parts.append("- 如果没有上下文，可以跳过此步")
        
        parts.extend([
            "",
            "最后，请根据五步分析结果，给出最终判断：",
            "- 分类：假借说明 或 语义解释",
            "- 置信度：0.0-1.0",
            "- 理由：简要说明判断依据",
            "",
            "请以JSON格式输出最终结果，格式如下：",
            "{",
            '  "classification": "假借说明" 或 "语义解释",',
            '  "confidence": 0.0-1.0,',
            '  "reasoning": {',
            '    "step1_semantic": "...",',
            '    "step2_phonetic": "...",',
            '    "step3_textual": "...",',
            '    "step4_pattern": "...",',
            '    "step5_context": "..."',
            '  },',
            '  "final_judgment": "综合判断理由"',
            "}"
        ])
        
        if source:
            parts.insert(1, f"出处：{source}")
        
        return "\n".join(parts)
    
    def _parse_result(
        self,
        xungu_sentence: str,
        context: Optional[str],
        source: Optional[str],
        output: str
    ) -> AnalysisResult:
        """解析Agent返回结果"""
        # 首先尝试从输出中提取被释字和释字
        pattern_result = self._extract_chars(xungu_sentence)
        char_a = pattern_result.get("char_a", "")
        char_b = pattern_result.get("char_b", "")
        
        # 创建结果对象
        result = AnalysisResult(
            xungu_sentence=xungu_sentence,
            char_a=char_a,
            char_b=char_b,
            context=context,
            source=source
        )
        
        # 尝试从输出中解析JSON
        json_data = self._extract_json(output)
        
        if json_data:
            # 解析JSON结果
            result.classification = json_data.get("classification", "不确定")
            result.confidence = float(json_data.get("confidence", 0.5))
            result.final_reasoning = json_data.get("final_judgment", "")
            
            # 解析五步推理
            reasoning = json_data.get("reasoning", {})
            result.step1_semantic = self._parse_step_result(reasoning.get("step1_semantic", ""))
            result.step2_phonetic = self._parse_step_result(reasoning.get("step2_phonetic", ""))
            result.step3_textual = self._parse_step_result(reasoning.get("step3_textual", ""))
            result.step4_pattern = self._parse_step_result(reasoning.get("step4_pattern", ""))
            result.step5_context = self._parse_step_result(reasoning.get("step5_context", ""))
        else:
            # 如果无法解析JSON，使用简单解析
            result.classification = self._extract_classification(output)
            result.confidence = self._extract_confidence(output)
            result.final_reasoning = output[:200]  # 截取前200字符作为理由
        
        return result
    
    def _extract_chars(self, sentence: str) -> Dict[str, str]:
        """从训诂句中提取被释字和释字"""
        from ..tools import identify_pattern
        
        pattern_result = identify_pattern(sentence)
        return {
            "char_a": pattern_result.get("被释字", ""),
            "char_b": pattern_result.get("释字", "")
        }
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON"""
        # 尝试找到JSON块
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # 如果找不到完整的JSON，尝试找到包含关键字段的部分
        return None
    
    def _parse_step_result(self, step_text: str) -> Dict[str, Any]:
        """解析单步结果文本为字典"""
        if not step_text:
            return {}
        
        # 简单解析：提取关键信息
        result = {"分析": step_text}
        
        # 尝试提取结论
        if "义近" in step_text or "义远" in step_text:
            result["结论"] = "义近" if "义近" in step_text else "义远"
        elif "音近" in step_text or "音远" in step_text:
            result["结论"] = "音近" if "音近" in step_text else "音远"
        elif "有佐证" in step_text or "无佐证" in step_text:
            result["结论"] = "有佐证" if "有佐证" in step_text else "无佐证"
        elif "支持假借" in step_text or "支持语义" in step_text:
            result["结论"] = "支持假借" if "支持假借" in step_text else "支持语义"
        
        return result
    
    def _extract_classification(self, text: str) -> str:
        """从文本中提取分类结果"""
        if "假借说明" in text or "假借" in text:
            return "假借说明"
        elif "语义解释" in text or "语义" in text:
            return "语义解释"
        return "不确定"
    
    def _extract_confidence(self, text: str) -> float:
        """从文本中提取置信度"""
        # 查找数字
        confidence_pattern = r'0\.\d+|0\.\d+%|\d+%'
        matches = re.findall(confidence_pattern, text)
        
        for match in matches:
            try:
                conf = float(match.replace('%', ''))
                if conf > 1.0:
                    conf = conf / 100.0
                return min(max(conf, 0.0), 1.0)
            except ValueError:
                continue
        
        # 根据关键词判断
        if "高" in text and "置信" in text:
            return 0.8
        elif "中" in text and "置信" in text:
            return 0.6
        elif "低" in text and "置信" in text:
            return 0.4
        
        return 0.5


# ===== 便捷函数 =====

def analyze_with_langchain(
    xungu_sentence: str,
    context: Optional[str] = None,
    source: Optional[str] = None,
    llm_provider: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    使用LangChain Agent分析训诂句的便捷函数
    
    Args:
        xungu_sentence: 训诂句
        context: 上下文
        source: 出处
        llm_provider: LLM提供商
        verbose: 是否输出详细日志
        
    Returns:
        dict: 分析结果
        
    Example:
        >>> result = analyze_with_langchain("崇，终也", context="崇朝其雨")
        >>> print(result["classification"])
        "假借说明"
    """
    agent = XunguLangChainAgent(llm_provider=llm_provider, verbose=verbose)
    result = agent.analyze(xungu_sentence, context, source)
    return result.to_dict()


# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试LangChain Agent
    print("测试LangChain Agent...")
    
    try:
        agent = XunguLangChainAgent(verbose=True)
        
        # 测试案例1：假借
        result = agent.analyze(
            "崇，终也",
            context="崇朝其雨",
            source="《毛传》"
        )
        print("\n" + "=" * 50)
        print("完整结果:")
        print(result.to_json())
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("请确保已设置OPENAI_API_KEY或ANTHROPIC_API_KEY环境变量")


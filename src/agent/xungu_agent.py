"""
基于LangChain的训诂分类Agent

这是系统的核心Agent，使用LangChain框架实现五步推理流程。
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json
import re
import time

# LangChain 1.0.0+ 版本中，AgentExecutor已被deprecate，需要自己实现executor
try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
    from langchain_core.runnables import Runnable
except ImportError as e:
    raise ImportError(
        f"LangChain导入失败: {e}\n"
        "请安装LangChain: pip install langchain langchain-openai langchain-anthropic"
    )

from .llm_client import get_llm
from .tool_wrappers import get_all_tools
from .prompts import SYSTEM_PROMPT


@dataclass
class AnalysisResult:
    """分析结果数据类"""
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


class SimpleAgentExecutor:
    """
    简单的Agent执行器，替代已废弃的AgentExecutor
    
    在LangChain 1.0+中，AgentExecutor已被废弃，我们实现一个简单的executor
    来处理工具调用循环。
    """
    
    def __init__(
        self,
        agent: Runnable,
        tools: List,
        verbose: bool = False,
        max_iterations: int = 15,
        max_execution_time: Optional[int] = None,
        handle_parsing_errors: bool = True
    ):
        """
        初始化执行器
        
        Args:
            agent: LangChain agent (Runnable)
            tools: 工具列表
            verbose: 是否输出详细日志
            max_iterations: 最大迭代次数
            max_execution_time: 最大执行时间（秒）
            handle_parsing_errors: 是否处理解析错误
        """
        self.agent = agent
        self.tools = {tool.name: tool for tool in tools}  # 转换为字典便于查找
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.handle_parsing_errors = handle_parsing_errors
    
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Agent
        
        Args:
            input_data: 输入数据，包含"input"键
            
        Returns:
            包含"output"键的字典
        """
        input_text = input_data.get("input", "")
        messages = [HumanMessage(content=input_text)]
        
        start_time = time.time()
        iterations = 0
        
        while iterations < self.max_iterations:
            # 检查执行时间
            if self.max_execution_time and (time.time() - start_time) > self.max_execution_time:
                if self.verbose:
                    print(f"达到最大执行时间限制: {self.max_execution_time}秒")
                break
            
            try:
                # 调用agent，传入messages
                response = self.agent.invoke({"messages": messages})
                
                # 处理响应
                if isinstance(response, dict) and "messages" in response:
                    messages = response["messages"]
                elif isinstance(response, list):
                    messages = response
                elif hasattr(response, 'messages'):
                    messages = response.messages
                else:
                    # 如果返回的是单个消息，转换为列表
                    if hasattr(response, 'content'):
                        messages.append(response)
                    else:
                        # 无法解析响应，退出循环
                        if self.verbose:
                            print(f"[警告] 无法解析agent响应: {type(response)}")
                        break
                
                # 检查最后一条消息
                last_message = messages[-1] if messages else None
                
                # 如果是AIMessage且包含tool_calls，执行工具
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    tool_results = []
                    for tool_call in last_message.tool_calls:
                        tool_name = tool_call.get("name", "")
                        tool_args = tool_call.get("args", {})
                        
                        if tool_name in self.tools:
                            try:
                                if self.verbose:
                                    print(f"[工具调用] {tool_name}({tool_args})")
                                
                                tool_result = self.tools[tool_name].invoke(tool_args)
                                tool_results.append(ToolMessage(
                                    content=str(tool_result) if not isinstance(tool_result, str) else tool_result,
                                    tool_call_id=tool_call.get("id", "")
                                ))
                            except Exception as e:
                                if self.verbose:
                                    print(f"[工具错误] {tool_name}: {e}")
                                tool_results.append(ToolMessage(
                                    content=f"错误: {str(e)}",
                                    tool_call_id=tool_call.get("id", "")
                                ))
                        else:
                            if self.verbose:
                                print(f"[警告] 未知工具: {tool_name}")
                            tool_results.append(ToolMessage(
                                content=f"未知工具: {tool_name}",
                                tool_call_id=tool_call.get("id", "")
                            ))
                    
                    # 添加工具结果到消息列表
                    messages.extend(tool_results)
                    iterations += 1
                    continue
                else:
                    # 没有工具调用，返回最终结果
                    break
                    
            except Exception as e:
                if self.handle_parsing_errors:
                    if self.verbose:
                        print(f"[解析错误] {e}")
                    # 添加错误消息并继续
                    messages.append(AIMessage(content=f"解析错误: {str(e)}，请重试。"))
                    iterations += 1
                    continue
                else:
                    raise
        
        # 提取最终输出
        output = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                output = msg.content
                break
        
        if not output:
            output = "未能生成有效输出"
        
        return {"output": output}


class XunguAgent:
    """
    基于LangChain的训诂分类Agent
    
    这是系统的核心Agent类，使用LangChain框架实现五步推理流程。
    所有工具调用都通过LangChain的Tool系统，确保模块化和可扩展性。
    
    使用方法：
        agent = XunguAgent(llm_provider="openai", verbose=True)
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
        
        # 创建工具列表（通过tool_wrappers模块获取，确保模块化）
        self.tools = get_all_tools()
        
        # 创建Agent
        self.agent = self._create_agent()
        # 使用SimpleAgentExecutor替代已废弃的AgentExecutor
        self.agent_executor = SimpleAgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=max_iterations,
            max_execution_time=max_execution_time,
        )
    
    def _create_agent(self):
        """创建LangChain Agent"""
        # 使用bind_tools将工具绑定到LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 创建prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # 创建agent chain
        agent = prompt | llm_with_tools
        
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
        
        # 执行Agent（所有工具调用由LangChain自动处理）
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
        """构建Agent输入提示词"""
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
        # 使用tools模块的identify_pattern函数（这是辅助功能，不是通过LangChain工具调用）
        from ..tools import identify_pattern
        
        pattern_result = identify_pattern(sentence)
        return {
            "char_a": pattern_result.get("被释字", ""),
            "char_b": pattern_result.get("释字", "")
        }
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON"""
        # 尝试找到JSON块（支持嵌套）
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # 如果找不到完整的JSON，返回None
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
        # 查找数字（支持0.85、85%、0.85%等格式）
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

def analyze(
    xungu_sentence: str,
    context: Optional[str] = None,
    source: Optional[str] = None,
    llm_provider: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    分析训诂句的便捷函数
    
    Args:
        xungu_sentence: 训诂句
        context: 上下文
        source: 出处
        llm_provider: LLM提供商
        verbose: 是否输出详细日志
        
    Returns:
        dict: 分析结果
        
    Example:
        >>> result = analyze("崇，终也", context="崇朝其雨")
        >>> print(result["classification"])
        "假借说明"
    """
    agent = XunguAgent(llm_provider=llm_provider, verbose=verbose)
    result = agent.analyze(xungu_sentence, context, source)
    return result.to_dict()


# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试Agent
    print("测试训诂分类Agent...")
    
    try:
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
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("请确保已设置OPENAI_API_KEY或ANTHROPIC_API_KEY环境变量")

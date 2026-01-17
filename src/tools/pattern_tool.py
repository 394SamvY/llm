"""
训式识别工具 - 第四步：训诂术语与训式识别

功能：识别训诂句的格式，判断使用了什么训释术语
数据源：训式规则表（正则表达式）
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class PatternResult:
    """训式识别结果"""
    pattern_name: str  # 格式名称，如"读为"、"犹也"
    char_a: str  # 被释字
    char_b: str  # 释字
    implied_type: str  # 暗示类型：假借/语义解释/以声通义/不确定
    confidence: str  # 置信度：高/中/低
    can_direct_judge: bool  # 是否可以直接判定
    source: str  # 该训式的来源说明


# ===== 训式规则表 =====
# 这是本工具的核心！根据参考资料整理
# 负责人：成员C

XUNSHI_PATTERNS = {
    # ===== A类：直接判假借（高置信度）=====
    "读为": {
        "regex": r"(.+)[，,]\s*读为\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "郑玄《礼》注，破字/改读术语"
    },
    "读曰": {
        "regex": r"(.+)[，,]\s*读曰\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "郑玄《礼》注"
    },
    "读当为": {
        "regex": r"(.+)[，,]\s*读当为\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "「读为」舒缓形式"
    },
    "当为": {
        "regex": r"(.+)[，,]\s*当为\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "训诂通用"
    },
    "当作": {
        "regex": r"(.+)[，,]\s*当作\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "训诂通用"
    },
    "通": {
        "regex": r"(.+)[与與](.+)通$",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "段玉裁等"
    },
    "古字通": {
        "regex": r"(.+)[、,，]\s*(.+)[，,]?\s*古字通",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "何晏《论语集解》"
    },
    "假借字": {
        "regex": r"(.+)[，,]\s*假借字",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "直接标注"
    },
    "借字也": {
        "regex": r"(.+)[，,]\s*(.+)借字也",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "清代训诂"
    },
    "借为": {
        "regex": r"(.+)[，,]\s*借为\s*(.+)",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "训诂通用"
    },
    
    # ===== B类：可能假借（中置信度）=====
    "读若": {
        "regex": r"(.+)[，,]\s*读若\s*(.+)",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "《说文》标音，有时暗示假借"
    },
    "读如": {
        "regex": r"(.+)[，,]\s*读如\s*(.+)",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "《周礼》注等"
    },
    "或作": {
        "regex": r"(.+)[，,]\s*或作\s*(.+)",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "异体/通假"
    },
    "亦作": {
        "regex": r"(.+)[，,]\s*亦作\s*(.+)",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "异体/通假"
    },
    "本作": {
        "regex": r"(.+)[，,]\s*本作\s*(.+)",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "暗示原字"
    },
    "声近": {
        "regex": r"(.+)[，,]\s*声近\s*(.+)",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "音近通假"
    },
    
    # ===== C类：以声通义 =====
    "之言": {
        "regex": r"(.+)之言\s*(.+)也?",
        "type": "以声通义",
        "confidence": "中",
        "direct_judge": False,
        "source": "《尚书大传》等，揭示语源"
    },
    "之为言": {
        "regex": r"(.+)之为言\s*(.+)也?",
        "type": "以声通义",
        "confidence": "中",
        "direct_judge": False,
        "source": "《孟子》《礼记》等"
    },
    
    # ===== D类：直接判语义解释 =====
    "犹也": {
        "regex": r"(.+)[，,]\s*犹(.+)也",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "比况训法"
    },
    "犹言": {
        "regex": r"(.+)[，,]\s*犹言\s*(.+)",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "比况训法"
    },
    "谓之": {
        "regex": r"(.+)[，,]\s*谓之\s*(.+)",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "命名式训释"
    },
    "之貌": {
        "regex": r"(.+)[，,]\s*(.+)之貌",
        "type": "语义解释",
        "confidence": "极高",
        "direct_judge": True,
        "source": "形容词训法"
    },
    "之称": {
        "regex": r"(.+)[，,]\s*(.+)之称",
        "type": "语义解释",
        "confidence": "极高",
        "direct_judge": True,
        "source": "称谓训法"
    },
    "貌": {
        "regex": r"(.+)[，,]\s*(.+)貌$",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "形容词训法"
    },
    "所以": {
        "regex": r"(.+)[，,]\s*所以(.+)也?",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "释用处训法"
    },
    
    # ===== E类：不确定（低置信度）=====
    "者也": {
        "regex": r"(.+)者[，,]?\s*(.+)也",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False,
        "source": "基本训式，需综合判断"
    },
    "即": {
        "regex": r"(.+)[，,]\s*即\s*(.+)",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False,
        "source": "可能是假借也可能是语义"
    },
    "A也": {
        "regex": r"^(.)[，,]\s*(.+)也$",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False,
        "source": "最基本训式A，B也"
    },
}


class PatternTool:
    """
    训式识别工具类
    
    负责人：成员C
    
    使用方法：
        tool = PatternTool()
        result = tool.identify("崇，读为终")
        print(result.implied_type)  # "假借"
    """
    
    def __init__(self):
        """初始化，编译正则表达式"""
        self.patterns = {}
        for name, config in XUNSHI_PATTERNS.items():
            self.patterns[name] = {
                "compiled": re.compile(config["regex"]),
                **config
            }
    
    def identify(self, sentence: str) -> PatternResult:
        """
        识别训诂句的格式
        
        Args:
            sentence: 训诂句，如"崇，终也"
            
        Returns:
            PatternResult: 识别结果
        """
        sentence = sentence.strip()
        
        # 按优先级顺序匹配（先匹配特定格式，最后匹配通用格式）
        # 优先级：A类 > B类 > C类 > D类 > E类
        priority_order = [
            # A类
            "读为", "读曰", "读当为", "当为", "当作", "通", "古字通", 
            "假借字", "借字也", "借为",
            # B类
            "读若", "读如", "或作", "亦作", "本作", "声近",
            # C类
            "之言", "之为言",
            # D类
            "犹也", "犹言", "谓之", "之貌", "之称", "貌", "所以",
            # E类（最后）
            "者也", "即", "A也"
        ]
        
        for name in priority_order:
            if name not in self.patterns:
                continue
            
            config = self.patterns[name]
            # 使用search而不是match，因为有些模式可能不在开头
            match = config["compiled"].search(sentence)
            
            if match:
                groups = match.groups()
                char_a = groups[0].strip() if len(groups) > 0 else ""
                char_b = groups[1].strip() if len(groups) > 1 else ""
                
                # 清理提取的字符
                char_a = self._clean_char(char_a)
                char_b = self._clean_char(char_b)
                
                # 对于"A也"格式，需要特殊处理
                if name == "A也":
                    # 提取第一个字作为被释字
                    if not char_a:
                        char_a = self._extract_first_char(sentence)
                    # 提取"也"前面的内容作为释字
                    if not char_b:
                        # 匹配"X，Y也"格式
                        match_a_ye = re.search(r"^([^，,]+)[，,]\s*(.+?)也$", sentence)
                        if match_a_ye:
                            char_a = match_a_ye.group(1).strip()
                            char_b = match_a_ye.group(2).strip()
                
                return PatternResult(
                    pattern_name=name,
                    char_a=char_a,
                    char_b=char_b,
                    implied_type=config["type"],
                    confidence=config["confidence"],
                    can_direct_judge=config["direct_judge"],
                    source=config["source"]
                )
        
        # 未匹配到任何格式
        return PatternResult(
            pattern_name="未知",
            char_a=self._extract_first_char(sentence),
            char_b="",
            implied_type="不确定",
            confidence="低",
            can_direct_judge=False,
            source="未识别的格式"
        )
    
    def _clean_char(self, text: str) -> str:
        """清理提取的字符，去除标点等"""
        # 去除常见标点
        for punct in "。，、；：""''「」『』【】《》（）()":
            text = text.replace(punct, "")
        return text.strip()
    
    def _extract_first_char(self, sentence: str) -> str:
        """从句子中提取第一个汉字"""
        for char in sentence:
            if '\u4e00' <= char <= '\u9fff':
                return char
        return ""


# ===== 函数式接口 =====

_tool_instance: Optional[PatternTool] = None


def identify_pattern(sentence: str) -> Dict[str, Any]:
    """
    识别训诂句格式的函数式接口
    
    Args:
        sentence: 训诂句，如"崇，终也"或"崇，读为终"
        
    Returns:
        dict: {
            "格式": "读为",
            "被释字": "崇",
            "释字": "终",
            "暗示类型": "假借",
            "置信度": "高",
            "可直接判定": True,
            "说明": "..."
        }
        
    Example:
        >>> result = identify_pattern("崇，读为终")
        >>> print(result["暗示类型"])
        "假借"
    """
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = PatternTool()
    
    result = _tool_instance.identify(sentence)
    
    return {
        "格式": result.pattern_name,
        "被释字": result.char_a,
        "释字": result.char_b,
        "暗示类型": result.implied_type,
        "置信度": result.confidence,
        "可直接判定": result.can_direct_judge,
        "说明": result.source
    }


# ===== 测试代码 =====
if __name__ == "__main__":
    test_cases = [
        "崇，终也",
        "崇，读为终",
        "正，读为征",
        "夭夭，盛也",
        "海之言晦也",
        "鉴，所以察形也",
        "硕，大貌",
        "崇与终通",
    ]
    
    print("=" * 50)
    print("训式识别测试")
    print("=" * 50)
    
    for sentence in test_cases:
        result = identify_pattern(sentence)
        print(f"\n输入: {sentence}")
        print(f"格式: {result['格式']}")
        print(f"被释字: {result['被释字']}, 释字: {result['释字']}")
        print(f"暗示类型: {result['暗示类型']} (置信度: {result['置信度']})")
        print(f"可直接判定: {result['可直接判定']}")

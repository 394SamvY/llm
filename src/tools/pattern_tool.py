"""
训式识别工具 - 第四步：训诂术语与训式识别

功能：识别训诂句的格式，判断使用了什么训释术语
数据源：训式规则表（正则表达式），基于郑玄注、《说文》及《声训法》参考资料
实现者：成员D
"""
import re
from typing import Dict, Optional, Any
from dataclasses import dataclass
# ===== 繁简转换工具 =====
try:
    from opencc import OpenCC
    cc = OpenCC('t2s') # 繁转简
except:
    cc = None

@dataclass
class PatternResult:
    """训式识别结果"""
    pattern_name: str       # 格式名称，如"读为"、"犹也"
    char_a: str            # 被释字
    char_b: str            # 释字
    implied_type: str      # 暗示类型：假借/语义解释/以声通义/不确定
    confidence: str        # 置信度：高/中/低
    can_direct_judge: bool # 是否可以直接判定
    source: str            # 该训式的来源说明

# ===== 训式规则表 =====
# 核心知识库：定义了如何用正则捕捉训诂术语
# 优化点：使用 (.+?) 非贪婪匹配，避免吞噬逗号
XUNSHI_PATTERNS = {
    # ===== A类：直接判假借（高置信度 - 铁证）=====
    "读为": {
        "regex": r"^(.+?)[，,]\s*读为\s*(.+?)[。？]?$",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "郑玄《礼》注，破字/改读术语"
    },
    "读曰": {
        "regex": r"^(.+?)[，,]\s*读曰\s*(.+?)[。？]?$",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "郑玄《礼》注，假借铁证"
    },
    "读当为": {
        "regex": r"^(.+?)[，,]\s*读?当为\s*(.+?)[。？]?$",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "「读为」舒缓形式"
    },
    "当为": {
        "regex": r"^(.+?)[，,]\s*当为\s*(.+?)[。？]?$",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "训诂通用"
    },
    "当作": {
        "regex": r"^(.+?)[，,]\s*当作\s*(.+?)[。？]?$",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "训诂通用，指明正字"
    },
    "通": {
        "regex": r"^(.+?)[与与跟](.+?)通$",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "段玉裁等，通用字"
    },
    "古字通": {
        "regex": r"^(.+?)[、,，]\s*(.+?)[，,]?\s*古字通[。？]?$",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True,
        "source": "何晏《论语集解》"
    },
    "假借字": {
        "regex": r"^(.+?)[，,]\s*.*假借字.*",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "直接标注"
    },
    "借为": {
        "regex": r"^(.+?)[，,]\s*借为\s*(.+?)[。？]?$",
        "type": "假借",
        "confidence": "极高",
        "direct_judge": True,
        "source": "训诂通用"
    },

    # ===== B类：可能假借（中置信度 - 需结合音韵）=====
    "读若": {
        "regex": r"^(.+?)[，,]\s*读若\s*(.+?)[。？]?$",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "《说文》标音，有时暗示假借，有时仅标音"
    },
    "读如": {
        "regex": r"^(.+?)[，,]\s*读如\s*(.+?)[。？]?$",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "《周礼》注等"
    },
    "或作": {
        "regex": r"^(.+?)[，,]\s*或作\s*(.+?)[。？]?$",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "异体/通假"
    },
    "声近": {
        "regex": r"^(.+?)[，,]\s*.*声近.*",
        "type": "可能假借",
        "confidence": "中",
        "direct_judge": False,
        "source": "音近通假"
    },

    # ===== C类：以声通义（声训特有格式）=====
    "之言": {
        # 注意：这里不能太严格限制逗号，因为可能是 "海之言晦也"（无逗号）
        "regex": r"^(.+?)之(?:为)?言\s*(.+?)也?[。？]?$",
        "type": "以声通义",
        "confidence": "高",
        "direct_judge": False,
        "source": "《尚书大传》等，揭示语源（音近义通）"
    },
    
    # ===== D类：直接判语义解释（义训）=====
    "犹": {
        "regex": r"^(.+?)[，,]\s*犹\s*(.+?)[也。？]?$",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "比况训法"
    },
    "犹言": {
        "regex": r"^(.+?)[，,]\s*犹言\s*(.+?)[。？]?$",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "比况训法"
    },
    "谓之": {
        "regex": r"^(.+?)[，,]\s*谓之\s*(.+?)[。？]?$",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "命名式训释"
    },
    "之貌": {
        "regex": r"^(.+?)[，,]\s*(.+?)之貌[。？]?$",
        "type": "语义解释",
        "confidence": "极高",
        "direct_judge": True,
        "source": "形容词训法"
    },
    "貌": {
        "regex": r"^(.+?)[，,]\s*(.+?)貌[。？]?$",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "形容词训法"
    },
    "所以": {
        "regex": r"^(.+?)[，,]\s*所以(.+)也?[。？]?$",
        "type": "语义解释",
        "confidence": "高",
        "direct_judge": True,
        "source": "释用处训法"
    },

    # ===== E类：不确定（最常见的 A，B也）=====
    "者也": {
        "regex": r"^(.+?)者[，,]?\s*(.+?)也[。？]?$",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False,
        "source": "基本训式，需综合判断"
    },
    "即": {
        "regex": r"^(.+?)[，,]\s*即\s*(.+?)[。？]?$",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False,
        "source": "可能是假借也可能是语义"
    },
    "A也": {
        # 这是兜底规则，必须非常小心，只匹配简单的 A,B也
        "regex": r"^([^，,]+?)[，,]\s*([^，,]+?)也[。？]?$",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False,
        "source": "最基本训式A，B也"
    },
}

class PatternTool:
    """
    训式识别工具类
    """
    
    def __init__(self):
        """初始化，编译正则表达式"""
        self.patterns = {}
        # 预编译所有正则
        for name, config in XUNSHI_PATTERNS.items():
            try:
                self.patterns[name] = {
                    "compiled": re.compile(config["regex"]),
                    **config
                }
            except re.error as e:
                print(f"[PatternTool] Error compiling regex for {name}: {e}")

    def identify(self, sentence: str) -> PatternResult:
        """
        识别训诂句的格式（核心逻辑）
        """
        # 自动归一化为简体
        if cc:
            sentence = cc.convert(sentence)
        sentence = sentence.strip()
        
        # 定义匹配优先级：A类(假借铁证) > C类(声训) > D类(义训) > B类(疑似) > E类(通用)
        # 这个顺序非常重要，避免"读为"被"A也"抢先匹配
        priority_order = [
            # 1. 强假借
            "读为", "读曰", "读当为", "当为", "当作", "通", "古字通", 
            "假借字", "借为",
            # 2. 强语义/声训
            "之言", "谓之", "之貌", "貌", "所以", "犹", "犹言",
            # 3. 弱假借
            "读若", "读如", "或作", "声近",
            # 4. 兜底/通用
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
                # 大多数正则有2个分组(被释字, 释字)，有的可能只有1个或更多
                char_a = groups[0] if len(groups) > 0 else ""
                char_b = groups[1] if len(groups) > 1 else ""
                
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
        if not text: return ""
        # 去除常见标点
        for punct in "。，、；：""''「」『』【】《》（）()":
            text = text.replace(punct, "")
        return text.strip()
    
    def _extract_first_char(self, sentence: str) -> str:
        """兜底：从句子中提取第一个汉字"""
        for char in sentence:
            if '\u4e00' <= char <= '\u9fff':
                return char
        return ""


# ===== 函数式接口 (保持不变) =====

_tool_instance: Optional[PatternTool] = None

def identify_pattern(sentence: str) -> Dict[str, Any]:
    """
    识别训诂句格式的函数式接口
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
        "崇，终也",           # 期望：A也 (不确定)
        "崇，读为终",         # 期望：读为 (假借)
        "正，读为征",         # 期望：读为 (假借)
        "夭夭，盛也",         # 期望：A也 (不确定)
        "海之言晦也",         # 期望：之言 (以声通义)
        "鉴，所以察形也",     # 期望：所以 (语义)
        "硕，大貌",           # 期望：貌 (语义)
        "崇与终通",           # 期望：通 (假借)
        "共，读曰恭",         # 期望：读曰 (假借)
    ]
    
    print("=" * 60)
    print(f"{'输入句子':<15} | {'识别格式':<6} | {'类型':<6} | {'置信度':<6} | {'被释字'} -> {'释字'}")
    print("-" * 60)
    
    for sentence in test_cases:
        res = identify_pattern(sentence)
        print(f"{sentence:<15} | {res['格式']:<8} | {res['暗示类型']:<6} | {res['置信度']:<6} | {res['被释字']} -> {res['释字']}")
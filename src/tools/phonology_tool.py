"""
音韵查询工具 - 第二步：语音对应分析

功能：查询汉字的上古音信息（声母、韵部、拟音）
数据源：潘悟云《汉语古音手册》、白一平-沙加尔拟音等
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PhonologyInfo:
    """音韵信息"""
    char: str  # 汉字
    shengmu: str  # 声母
    yunbu: str  # 韵部
    reconstruction: str  # 上古音拟音
    middle_chinese: Optional[str] = None  # 中古音（可选）
    source: str = ""  # 数据来源


class PhonologyTool:
    """
    音韵查询工具类
    
    负责人：成员B
    
    使用方法：
        tool = PhonologyTool()
        result = tool.query("崇")
        print(result.yunbu)  # "东"
    """
    
    def __init__(self, phonology_path: Optional[str] = None):
        """
        初始化工具
        
        Args:
            phonology_path: 音韵数据文件路径
        """
        self.phonology_path = phonology_path
        self._index: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> None:
        """
        加载音韵数据
        
        TODO: 实现此方法
        - 解析潘悟云《汉语古音手册》TXT文件
        - 或解析白一平-沙加尔Excel数据
        - 建立 字 -> 音韵 的索引
        """
        if self._loaded:
            return
        
        # ===== TODO: 实现数据加载 =====
        # from src.knowledge.phonology_loader import load_phonology
        # self._index = load_phonology(self.phonology_path)
        
        # 临时：使用假数据
        self._index = self._get_mock_data()
        self._loaded = True
    
    def query(self, char: str) -> PhonologyInfo:
        """
        查询单个汉字的音韵信息
        
        Args:
            char: 要查询的汉字
            
        Returns:
            PhonologyInfo: 包含声母、韵部、拟音等信息
        """
        if not self._loaded:
            self.load()
        
        if char in self._index:
            data = self._index[char]
            return PhonologyInfo(
                char=char,
                shengmu=data.get("shengmu", "未知"),
                yunbu=data.get("yunbu", "未知"),
                reconstruction=data.get("reconstruction", "未知"),
                middle_chinese=data.get("middle_chinese"),
                source=data.get("source", "")
            )
        else:
            return PhonologyInfo(
                char=char,
                shengmu="未收录",
                yunbu="未收录",
                reconstruction="未收录"
            )
    
    def is_phonetically_close(self, char1: str, char2: str) -> Dict[str, Any]:
        """
        判断两个字是否音近
        
        Args:
            char1: 第一个字
            char2: 第二个字
            
        Returns:
            dict: {
                "is_close": True/False,
                "same_yunbu": True/False,
                "same_shengmu": True/False,
                "analysis": "分析说明"
            }
        """
        p1 = self.query(char1)
        p2 = self.query(char2)
        
        same_yunbu = p1.yunbu == p2.yunbu
        same_shengmu = p1.shengmu == p2.shengmu
        
        # 判断是否音近（同韵部或同声母都算音近）
        is_close = same_yunbu or same_shengmu
        
        analysis_parts = []
        if same_yunbu:
            analysis_parts.append(f"韵部相同（{p1.yunbu}部）")
        else:
            analysis_parts.append(f"韵部不同（{p1.yunbu} vs {p2.yunbu}）")
        
        if same_shengmu:
            analysis_parts.append(f"声母相同（{p1.shengmu}母）")
        else:
            analysis_parts.append(f"声母不同（{p1.shengmu} vs {p2.shengmu}）")
        
        return {
            "is_close": is_close,
            "same_yunbu": same_yunbu,
            "same_shengmu": same_shengmu,
            "char1_info": {"声母": p1.shengmu, "韵部": p1.yunbu, "拟音": p1.reconstruction},
            "char2_info": {"声母": p2.shengmu, "韵部": p2.yunbu, "拟音": p2.reconstruction},
            "analysis": "；".join(analysis_parts)
        }
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """
        返回测试用的假数据
        
        基于白一平-沙加尔和王力的上古音系统
        """
        return {
            "崇": {
                "shengmu": "禅",  # 或写作 dz-
                "yunbu": "东",
                "reconstruction": "*dzruŋ",
                "middle_chinese": "dʐuŋ",
                "source": "白一平-沙加尔"
            },
            "终": {
                "shengmu": "章",  # 或写作 t-
                "yunbu": "东",
                "reconstruction": "*tuŋ",
                "middle_chinese": "tɕuŋ",
                "source": "白一平-沙加尔"
            },
            "海": {
                "shengmu": "匣",
                "yunbu": "之",
                "reconstruction": "*hmˤəʔ",
                "source": "白一平-沙加尔"
            },
            "晦": {
                "shengmu": "匣",
                "yunbu": "微",
                "reconstruction": "*m̥ˤuj",
                "source": "白一平-沙加尔"
            },
            "祈": {
                "shengmu": "群",
                "yunbu": "微",
                "reconstruction": "*gə",
                "source": "白一平-沙加尔"
            },
            "求": {
                "shengmu": "群",
                "yunbu": "幽",
                "reconstruction": "*gu",
                "source": "白一平-沙加尔"
            },
            "山": {
                "shengmu": "生",
                "yunbu": "元",
                "reconstruction": "*sren",
                "source": "白一平-沙加尔"
            },
            "产": {
                "shengmu": "初",
                "yunbu": "元",
                "reconstruction": "*srjenʔ",
                "source": "白一平-沙加尔"
            },
        }


# ===== 函数式接口 =====

_tool_instance: Optional[PhonologyTool] = None


def query_phonology(char: str) -> Dict[str, Any]:
    """
    查询汉字音韵信息的函数式接口
    
    Args:
        char: 要查询的汉字
        
    Returns:
        dict: {
            "字": "崇",
            "声母": "禅",
            "韵部": "东",
            "上古拟音": "*dzruŋ"
        }
        
    Example:
        >>> result = query_phonology("崇")
        >>> print(result["韵部"])
        "东"
    """
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = PhonologyTool()
    
    info = _tool_instance.query(char)
    
    return {
        "字": info.char,
        "声母": info.shengmu,
        "韵部": info.yunbu,
        "上古拟音": info.reconstruction,
        "中古音": info.middle_chinese
    }


def check_phonetic_relation(char1: str, char2: str) -> Dict[str, Any]:
    """
    检查两个字的音韵关系
    
    Args:
        char1: 第一个字
        char2: 第二个字
        
    Returns:
        dict: 音韵对比分析结果
    """
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = PhonologyTool()
    
    return _tool_instance.is_phonetically_close(char1, char2)


# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试单字查询
    print(query_phonology("崇"))
    print(query_phonology("终"))
    
    # 测试音近判断
    result = check_phonetic_relation("崇", "终")
    print(f"崇-终 音近判断: {result}")

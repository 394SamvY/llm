"""
语义查询工具 - 第一步：语义关联性分析

功能：查询汉字的本义、义项、例句等信息
数据源：《汉语大词典》JSONL
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class WordMeaning:
    """字词义项信息"""
    char: str  # 汉字
    primary_meaning: str  # 本义/主要义项
    meanings: List[str]  # 所有义项
    examples: List[Dict[str, str]]  # 例句 [{"source": "出处", "quote": "引文"}]
    jiajie_notes: List[str]  # 假借相关注释
    raw_data: Optional[Dict] = None  # 原始数据


class SemanticTool:
    """
    语义查询工具类
    
    负责人：成员B
    
    使用方法：
        tool = SemanticTool()
        result = tool.query("崇")
        print(result.primary_meaning)  # "高大"
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        """
        初始化工具
        
        Args:
            dictionary_path: 汉语大词典JSONL文件路径，默认从配置读取
        """
        self.dictionary_path = dictionary_path
        self._index: Dict[str, Any] = {}  # 字 -> 条目的索引
        self._loaded = False
    
    def load(self) -> None:
        """
        加载字典数据并建立索引
        
        TODO: 实现此方法
        - 读取JSONL文件
        - 建立 字 -> 条目 的索引
        - 考虑内存优化（延迟加载/分块加载）
        """
        if self._loaded:
            return
        
        # ===== TODO: 实现数据加载 =====
        # from src.knowledge.dictionary_loader import load_dyhdc
        # self._index = load_dyhdc(self.dictionary_path)
        
        # 临时：使用假数据
        self._index = self._get_mock_data()
        self._loaded = True
    
    def query(self, char: str) -> WordMeaning:
        """
        查询单个汉字的语义信息
        
        Args:
            char: 要查询的汉字
            
        Returns:
            WordMeaning: 包含本义、义项、例句等信息
        """
        if not self._loaded:
            self.load()
        
        if char in self._index:
            data = self._index[char]
            return WordMeaning(
                char=char,
                primary_meaning=data.get("primary_meaning", "未知"),
                meanings=data.get("meanings", []),
                examples=data.get("examples", []),
                jiajie_notes=data.get("jiajie_notes", []),
                raw_data=data
            )
        else:
            return WordMeaning(
                char=char,
                primary_meaning="未收录",
                meanings=[],
                examples=[],
                jiajie_notes=[]
            )
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """
        返回测试用的假数据
        
        开发时使用，正式版本删除此方法
        """
        return {
            "崇": {
                "primary_meaning": "高大",
                "meanings": ["高大", "尊崇", "充满", "终（假借）"],
                "examples": [
                    {"source": "《说文》", "quote": "崇，嵬高也"},
                    {"source": "《诗·大雅·云汉》", "quote": "瞻卬昊天，云如何崇"},
                ],
                "jiajie_notes": ["崇朝，终朝也。——《诗·邶风》毛传"]
            },
            "终": {
                "primary_meaning": "终结",
                "meanings": ["终结", "完整", "最终", "整个"],
                "examples": [
                    {"source": "《说文》", "quote": "终，絿丝也"},
                    {"source": "《诗·小雅·采绿》", "quote": "终朝采绿"},
                ],
                "jiajie_notes": []
            },
            "海": {
                "primary_meaning": "大海",
                "meanings": ["大海", "大湖", "众多"],
                "examples": [
                    {"source": "《释名》", "quote": "海，晦也，主承秽浊，其色黑而晦也"},
                ],
                "jiajie_notes": []
            },
            "晦": {
                "primary_meaning": "昏暗",
                "meanings": ["昏暗", "月末", "隐晦"],
                "examples": [],
                "jiajie_notes": []
            },
            "祈": {
                "primary_meaning": "祈求",
                "meanings": ["祈求", "祈祷"],
                "examples": [],
                "jiajie_notes": []
            },
            "求": {
                "primary_meaning": "寻求",
                "meanings": ["寻求", "请求", "探求"],
                "examples": [],
                "jiajie_notes": []
            },
        }


# ===== 函数式接口（方便直接调用）=====

_tool_instance: Optional[SemanticTool] = None


def query_word_meaning(char: str) -> Dict[str, Any]:
    """
    查询汉字语义信息的函数式接口
    
    Args:
        char: 要查询的汉字
        
    Returns:
        dict: {
            "字": "崇",
            "本义": "高大",
            "义项": ["高大", "尊崇", ...],
            "例句": [...],
            "假借标注": [...]
        }
        
    Example:
        >>> result = query_word_meaning("崇")
        >>> print(result["本义"])
        "高大"
    """
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = SemanticTool()
    
    word_meaning = _tool_instance.query(char)
    
    return {
        "字": word_meaning.char,
        "本义": word_meaning.primary_meaning,
        "义项": word_meaning.meanings,
        "例句": word_meaning.examples,
        "假借标注": word_meaning.jiajie_notes
    }


# ===== 测试代码 =====
if __name__ == "__main__":
    # 简单测试
    result = query_word_meaning("崇")
    print(f"查询结果: {result}")
    
    result = query_word_meaning("终")
    print(f"查询结果: {result}")

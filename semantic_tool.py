"""
语义查询工具 - 第一步：语义关联性分析

功能：查询汉字的本义、义项、例句等信息
数据源：《汉语大词典》JSONL，使用DYHDCIndexLoader
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


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
    
    使用DYHDCIndexLoader查询《汉语大词典》
    
    使用方法：
        tool = SemanticTool()
        result = tool.query("崇")
        print(result.primary_meaning)  # "高；高大。"
    """
    
    def __init__(self, jsonl_path: Optional[str] = None, index_path: Optional[str] = None):
        """
        初始化工具
        
        Args:
            jsonl_path: 汉语大词典JSONL文件路径，默认从配置读取
            index_path: 索引文件路径，默认从配置读取
        """
        from ..data.dyhdc_index_builder import DYHDCIndexLoader
        from ..config import get_settings
        
        settings = get_settings()
        
        # 设置默认路径
        if jsonl_path is None:
            jsonl_path = str(settings.dyhdc_path)
        
        if index_path is None:
            index_path = str(settings.data_processed_dir / "dyhdc_index.json")
        
        self.jsonl_path = jsonl_path
        self.index_path = index_path
        self._loader: Optional[DYHDCIndexLoader] = None
        self._loaded = False
    
    def load(self) -> None:
        """
        加载字典索引
        
        首次调用时会加载索引（约1秒）
        
        注意：如果索引文件不存在，会提示用户先构建索引
        """
        if self._loaded:
            return
        
        from ..data.dyhdc_index_builder import DYHDCIndexLoader
        from pathlib import Path
        
        # 检查索引文件是否存在
        index_path_obj = Path(self.index_path)
        if not index_path_obj.exists():
            raise FileNotFoundError(
                f"索引文件不存在: {self.index_path}\n"
                f"请先运行以下命令构建索引：\n"
                f"  python -c \"from src.data.dyhdc_index_builder import build_dyhdc_index; build_dyhdc_index()\"\n"
                f"或运行: python check_and_build_index.py"
            )
        
        self._loader = DYHDCIndexLoader(self.jsonl_path, self.index_path)
        if not self._loader.load_index():
            raise RuntimeError(
                f"索引加载失败。请检查：\n"
                f"  1. 索引文件是否存在: {self.index_path}\n"
                f"  2. JSONL文件是否存在: {self.jsonl_path}\n"
                f"  3. 索引文件格式是否正确"
            )
        self._loaded = True
    
    def query(self, char: str) -> WordMeaning:
        """
        查询单个汉字的语义信息
        
        Args:
            char: 要查询的汉字（支持繁简体）
            
        Returns:
            WordMeaning: 包含本义、义项、例句等信息
        """
        if not self._loaded:
            self.load()
        
        if self._loader is None:
            return WordMeaning(
                char=char,
                primary_meaning="未加载",
                meanings=[],
                examples=[],
                jiajie_notes=[]
            )
        
        # 查询词典
        result = self._loader.query_single_char(char)
        
        if result is None:
            return WordMeaning(
                char=char,
                primary_meaning="未收录",
                meanings=[],
                examples=[],
                jiajie_notes=[]
            )
        
        # 转换例句格式
        examples = []
        for ex in result.get("例句", []):
            if isinstance(ex, str):
                # 如果是字符串，尝试解析
                examples.append({"quote": ex})
            elif isinstance(ex, dict):
                examples.append(ex)
        
        return WordMeaning(
            char=result.get("字", char),
            primary_meaning=result.get("本义", "未知"),
            meanings=result.get("义项", []),
            examples=examples,
            jiajie_notes=result.get("假借标注", []),
            raw_data=result
        )


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

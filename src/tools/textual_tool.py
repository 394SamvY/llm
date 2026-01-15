"""
文献检索工具 - 第三步：异文与文例佐证

功能：检索文献中是否存在异文、平行文本等佐证
数据源：《汉语大词典》例句、其他文献数据库
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class TextualEvidence:
    """文献佐证信息"""
    has_evidence: bool  # 是否找到佐证
    variant_texts: List[Dict[str, str]]  # 异文 [{"source": "出处", "text": "内容", "note": "说明"}]
    parallel_texts: List[Dict[str, str]]  # 平行文本
    jiajie_records: List[Dict[str, str]]  # 假借记录（词典中的标注）
    summary: str  # 总结说明


class TextualTool:
    """
    文献检索工具类
    
    负责人：成员C（或成员B）
    
    使用方法：
        tool = TextualTool()
        result = tool.search("崇", "终", context="崇朝其雨")
        print(result.has_evidence)  # True
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        """
        初始化工具
        
        Args:
            dictionary_path: 词典数据路径
        """
        self.dictionary_path = dictionary_path
        self._loaded = False
        self._evidence_db: Dict[str, List[Dict]] = {}
    
    def load(self) -> None:
        """
        加载数据
        
        TODO: 实现此方法
        - 从《汉语大词典》提取假借/异文相关记录
        - 建立检索索引
        """
        if self._loaded:
            return
        
        # ===== TODO: 实现数据加载 =====
        
        # 临时：使用预设的异文数据
        self._evidence_db = self._get_mock_data()
        self._loaded = True
    
    def search(
        self, 
        char_a: str, 
        char_b: str, 
        context: Optional[str] = None
    ) -> TextualEvidence:
        """
        检索两个字之间的文献佐证
        
        Args:
            char_a: 被释字
            char_b: 释字
            context: 上下文（可选，用于精确匹配）
            
        Returns:
            TextualEvidence: 检索到的佐证信息
        """
        if not self._loaded:
            self.load()
        
        # 构建检索键
        key = f"{char_a}-{char_b}"
        reverse_key = f"{char_b}-{char_a}"
        
        variant_texts = []
        parallel_texts = []
        jiajie_records = []
        
        # 查找正向和反向的记录
        for k in [key, reverse_key]:
            if k in self._evidence_db:
                records = self._evidence_db[k]
                for record in records:
                    if record["type"] == "variant":
                        variant_texts.append(record)
                    elif record["type"] == "parallel":
                        parallel_texts.append(record)
                    elif record["type"] == "jiajie":
                        jiajie_records.append(record)
        
        has_evidence = len(variant_texts) > 0 or len(jiajie_records) > 0
        
        # 生成总结
        summary_parts = []
        if variant_texts:
            summary_parts.append(f"找到{len(variant_texts)}处异文")
        if parallel_texts:
            summary_parts.append(f"找到{len(parallel_texts)}处平行文本")
        if jiajie_records:
            summary_parts.append(f"找到{len(jiajie_records)}处假借记录")
        if not summary_parts:
            summary_parts.append("未找到相关佐证")
        
        return TextualEvidence(
            has_evidence=has_evidence,
            variant_texts=variant_texts,
            parallel_texts=parallel_texts,
            jiajie_records=jiajie_records,
            summary="；".join(summary_parts)
        )
    
    def _get_mock_data(self) -> Dict[str, List[Dict]]:
        """
        返回测试用的假数据
        """
        return {
            "崇-终": [
                {
                    "type": "variant",
                    "source": "《诗·邶风·简兮》与《小雅·采绿》",
                    "text": "崇朝 vs 终朝",
                    "note": "同一词义，不同字形，直接证明正借关系"
                },
                {
                    "type": "jiajie",
                    "source": "《毛传》",
                    "text": "崇，终也",
                    "note": "训诂家直接标注"
                }
            ],
            "高-膏": [
                {
                    "type": "jiajie",
                    "source": "《黄帝内经》王冰注",
                    "text": "高，膏也",
                    "note": "高梁之变→膏粱之变"
                }
            ],
            "虹-江": [
                {
                    "type": "jiajie",
                    "source": "《诗·邶风·泉水》《毛传》",
                    "text": "虹，江也（以正字义释借字）",
                    "note": "实虹小子→实江小子"
                }
            ],
        }


# ===== 函数式接口 =====

_tool_instance: Optional[TextualTool] = None


def search_textual_evidence(
    char_a: str, 
    char_b: str, 
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    检索文献佐证的函数式接口
    
    Args:
        char_a: 被释字
        char_b: 释字
        context: 上下文（可选）
        
    Returns:
        dict: {
            "有佐证": True/False,
            "异文": [...],
            "假借记录": [...],
            "总结": "..."
        }
        
    Example:
        >>> result = search_textual_evidence("崇", "终")
        >>> print(result["有佐证"])
        True
    """
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = TextualTool()
    
    evidence = _tool_instance.search(char_a, char_b, context)
    
    return {
        "有佐证": evidence.has_evidence,
        "异文": evidence.variant_texts,
        "平行文本": evidence.parallel_texts,
        "假借记录": evidence.jiajie_records,
        "总结": evidence.summary
    }


# ===== 测试代码 =====
if __name__ == "__main__":
    result = search_textual_evidence("崇", "终")
    print(f"崇-终 佐证: {result}")
    
    result = search_textual_evidence("海", "晦")
    print(f"海-晦 佐证: {result}")

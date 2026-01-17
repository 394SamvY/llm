"""
文献检索工具 - 第三步：异文与文例佐证

功能：检索文献中是否存在异文、平行文本等佐证
数据源：《汉语大词典》例句、假借标注
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


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
    
    从《汉语大词典》提取假借标注和例句作为佐证
    
    使用方法：
        tool = TextualTool()
        result = tool.search("崇", "终", context="崇朝其雨")
        print(result.has_evidence)  # True
    """
    
    def __init__(self, jsonl_path: Optional[str] = None, index_path: Optional[str] = None):
        """
        初始化工具
        
        Args:
            jsonl_path: 词典JSONL文件路径
            index_path: 索引文件路径
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
        加载词典索引
        
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
    
    def search(
        self, 
        char_a: str, 
        char_b: str, 
        context: Optional[str] = None
    ) -> TextualEvidence:
        """
        检索两个字之间的文献佐证
        
        从词典中提取假借标注和例句
        
        Args:
            char_a: 被释字
            char_b: 释字
            context: 上下文（可选，用于精确匹配）
            
        Returns:
            TextualEvidence: 检索到的佐证信息
        """
        if not self._loaded:
            self.load()
        
        if self._loader is None:
            return TextualEvidence(
                has_evidence=False,
                variant_texts=[],
                parallel_texts=[],
                jiajie_records=[],
                summary="词典未加载"
            )
        
        variant_texts = []
        parallel_texts = []
        jiajie_records = []
        
        # 查询两个字的词典条目
        entry_a = self._loader.query_single_char(char_a)
        entry_b = self._loader.query_single_char(char_b)
        
        # 从被释字的假借标注中查找
        if entry_a:
            jiajie_notes = entry_a.get("假借标注", [])
            for note in jiajie_notes:
                # 检查是否包含释字
                if char_b in note:
                    # 提取出处信息
                    source = self._extract_source(note)
                    jiajie_records.append({
                        "type": "jiajie",
                        "source": source,
                        "text": note,
                        "note": f"词典中标注：{char_a}与{char_b}的假借关系"
                    })
        
        # 从释字的假借标注中查找（反向）
        if entry_b:
            jiajie_notes = entry_b.get("假借标注", [])
            for note in jiajie_notes:
                if char_a in note:
                    source = self._extract_source(note)
                    jiajie_records.append({
                        "type": "jiajie",
                        "source": source,
                        "text": note,
                        "note": f"词典中标注：{char_b}与{char_a}的假借关系"
                    })
        
        # 从例句中查找异文（如果上下文提供）
        if context:
            # 在例句中查找包含上下文的例子
            if entry_a:
                examples = entry_a.get("例句", [])
                for ex in examples:
                    ex_text = ex if isinstance(ex, str) else ex.get("text", "")
                    if context in ex_text or char_b in ex_text:
                        variant_texts.append({
                            "type": "variant",
                            "source": "《汉语大词典》例句",
                            "text": ex_text,
                            "note": f"例句中包含相关用字"
                        })
        
        # 检查是否有"通"、"读为"等假借术语
        if entry_a:
            meanings = entry_a.get("义项", [])
            for meaning in meanings:
                # 查找包含假借术语的义项
                if any(term in meaning for term in ["通", "读为", "读曰", "假借"]):
                    if char_b in meaning:
                        source = self._extract_source(meaning)
                        jiajie_records.append({
                            "type": "jiajie",
                            "source": source or "《汉语大词典》",
                            "text": meaning,
                            "note": f"义项中标注假借关系"
                        })
        
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
    
    def _extract_source(self, text: str) -> str:
        """从文本中提取出处信息"""
        # 尝试提取《书名》格式的出处
        pattern = r"《[^》]+》"
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
        return ""


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

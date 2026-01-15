"""
字典数据加载器 - 加载《汉语大词典》JSONL数据

负责人：成员B

数据文件：《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl
文件大小：1.9GB
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, Iterator
from dataclasses import dataclass


@dataclass
class DictionaryEntry:
    """词典条目"""
    headword: str  # 词头
    simplified: str  # 简体
    pronunciations: list  # 读音
    senses: list  # 义项
    examples: list  # 例句
    cross_refs: list  # 交叉引用
    raw: dict  # 原始数据


class DictionaryLoader:
    """
    汉语大词典数据加载器
    
    负责人：成员B
    
    使用方法：
        loader = DictionaryLoader("path/to/dyhdc.jsonl")
        loader.load()  # 或 loader.load_lazy() 延迟加载
        entry = loader.query("崇")
    
    注意：
        - 文件很大(1.9GB)，建议使用延迟加载或只加载索引
        - 可以先用 build_index() 建立索引文件，加速后续查询
    """
    
    def __init__(self, jsonl_path: Optional[str] = None):
        """
        初始化加载器
        
        Args:
            jsonl_path: JSONL文件路径，默认使用配置中的路径
        """
        if jsonl_path is None:
            from ..config import get_settings
            jsonl_path = str(get_settings().dyhdc_path)
        
        self.jsonl_path = Path(jsonl_path)
        self._index: Dict[str, Any] = {}  # 字 -> 条目
        self._loaded = False
    
    def load(self, max_entries: Optional[int] = None) -> None:
        """
        加载全部数据到内存
        
        Args:
            max_entries: 最多加载多少条（用于测试）
        
        警告：完整加载会占用大量内存！
        """
        if self._loaded:
            return
        
        if not self.jsonl_path.exists():
            print(f"警告: 数据文件不存在: {self.jsonl_path}")
            return
        
        print(f"正在加载字典数据: {self.jsonl_path}")
        count = 0
        
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if max_entries and count >= max_entries:
                    break
                
                try:
                    entry = json.loads(line.strip())
                    self._process_entry(entry)
                    count += 1
                    
                    if count % 10000 == 0:
                        print(f"  已加载 {count} 条...")
                        
                except json.JSONDecodeError:
                    continue
        
        print(f"加载完成，共 {count} 条")
        self._loaded = True
    
    def load_lazy(self) -> None:
        """
        延迟加载模式 - 只在查询时才读取
        
        适用于内存有限或只需要查询少量字的场景
        """
        self._loaded = True  # 标记为已初始化，查询时动态加载
    
    def _process_entry(self, entry: dict) -> None:
        """处理单条数据，加入索引"""
        # 提取词头
        headword = entry.get("headword", "") or entry.get("hw", "")
        if not headword:
            return
        
        # 提取第一个字作为索引键
        first_char = headword[0] if headword else ""
        
        # 存入索引
        if first_char not in self._index:
            self._index[first_char] = []
        self._index[first_char].append(entry)
    
    def query(self, char: str) -> Optional[Dict[str, Any]]:
        """
        查询单个汉字
        
        Args:
            char: 要查询的汉字
            
        Returns:
            dict: 包含本义、义项、例句等信息
        """
        if not self._loaded:
            self.load_lazy()
        
        # 从索引查找
        if char in self._index:
            entries = self._index[char]
            # 返回处理后的结果
            return self._format_result(char, entries)
        
        # 延迟加载模式：动态搜索文件
        if self.jsonl_path.exists():
            return self._search_in_file(char)
        
        return None
    
    def _search_in_file(self, char: str) -> Optional[Dict[str, Any]]:
        """在文件中搜索指定字（延迟加载模式）"""
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    headword = entry.get("headword", "") or entry.get("hw", "")
                    if headword and headword[0] == char:
                        return self._format_result(char, [entry])
                except:
                    continue
        return None
    
    def _format_result(self, char: str, entries: list) -> Dict[str, Any]:
        """格式化查询结果"""
        if not entries:
            return {
                "字": char,
                "本义": "未收录",
                "义项": [],
                "例句": [],
                "假借标注": []
            }
        
        # 取第一个条目作为主条目
        main_entry = entries[0]
        
        # 提取义项
        senses = main_entry.get("senses", [])
        meanings = []
        examples = []
        jiajie_notes = []
        
        for sense in senses:
            # 提取释义
            mean = sense.get("mean", "")
            if mean:
                meanings.append(mean)
            
            # 提取例句
            for ex in sense.get("examples", []):
                examples.append({
                    "source": ex.get("source", ""),
                    "quote": ex.get("quote", "")
                })
            
            # 检查是否有假借标注
            if "读为" in mean or "读曰" in mean or "通" in mean or "假借" in mean:
                jiajie_notes.append(mean)
        
        # 确定本义（第一个义项）
        primary_meaning = meanings[0] if meanings else "未知"
        
        return {
            "字": char,
            "本义": primary_meaning,
            "义项": meanings,
            "例句": examples[:5],  # 只返回前5个例句
            "假借标注": jiajie_notes,
            "raw": main_entry  # 保留原始数据
        }
    
    def build_index_file(self, output_path: str) -> None:
        """
        构建索引文件，加速后续查询
        
        TODO: 实现此方法
        - 遍历JSONL，为每个字建立偏移量索引
        - 保存为JSON文件
        """
        pass


# ===== 便捷函数 =====

_loader: Optional[DictionaryLoader] = None


def load_dyhdc(path: Optional[str] = None) -> DictionaryLoader:
    """获取字典加载器单例"""
    global _loader
    if _loader is None:
        _loader = DictionaryLoader(path)
    return _loader


def query_dyhdc(char: str) -> Optional[Dict[str, Any]]:
    """便捷查询函数"""
    loader = load_dyhdc()
    return loader.query(char)


# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试加载器
    loader = DictionaryLoader()
    
    # 尝试延迟加载模式
    loader.load_lazy()
    
    # 查询测试
    result = loader.query("崇")
    if result:
        print(f"查询结果: {result}")
    else:
        print("未找到或数据文件不存在")

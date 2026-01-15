"""
音韵数据加载器 - 加载上古音数据

负责人：成员B

数据来源：
1. 潘悟云《汉语古音手册》
2. 白一平-沙加尔拟音
3. 斯塔罗斯金汉语拟音
"""
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PhonologyEntry:
    """音韵条目"""
    char: str  # 汉字
    shengmu: str  # 声母
    yunbu: str  # 韵部
    reconstruction: str  # 上古音拟音
    middle_chinese: Optional[str] = None  # 中古音
    source: str = ""  # 数据来源


class PhonologyLoader:
    """
    音韵数据加载器
    
    负责人：成员B
    
    使用方法：
        loader = PhonologyLoader()
        loader.load()
        entry = loader.query("崇")
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化加载器
        
        Args:
            data_dir: 音韵数据目录
        """
        if data_dir is None:
            from ..config import get_settings
            settings = get_settings()
            data_dir = str(settings.project_root / "音韵数据" / "上古音")
        
        self.data_dir = Path(data_dir)
        self._index: Dict[str, PhonologyEntry] = {}
        self._loaded = False
    
    def load(self) -> None:
        """加载所有音韵数据"""
        if self._loaded:
            return
        
        # 尝试加载各个数据源
        self._load_pan_wuyun()
        # self._load_baxter_sagart()  # TODO
        # self._load_starostin()  # TODO
        
        self._loaded = True
        print(f"音韵数据加载完成，共 {len(self._index)} 条")
    
    def _load_pan_wuyun(self) -> None:
        """
        加载潘悟云《汉语古音手册》数据
        
        TODO: 实现实际的解析逻辑
        数据格式需要根据实际文件确定
        """
        txt_path = self.data_dir / "潘悟云《汉语古音手册》" / "汉语古音手册.txt"
        
        if not txt_path.exists():
            print(f"潘悟云数据文件不存在: {txt_path}")
            return
        
        # TODO: 解析TXT文件
        # 这里需要根据实际的文件格式来实现
        # 暂时使用预设数据
        self._load_preset_data()
    
    def _load_preset_data(self) -> None:
        """加载预设的音韵数据（用于测试和演示）"""
        preset = [
            # (字, 声母, 韵部, 拟音, 来源)
            ("崇", "禅", "东", "*dzruŋ", "白一平-沙加尔"),
            ("终", "章", "东", "*tuŋ", "白一平-沙加尔"),
            ("海", "匣", "之", "*hmˤəʔ", "白一平-沙加尔"),
            ("晦", "匣", "微", "*m̥ˤuj", "白一平-沙加尔"),
            ("祈", "群", "微", "*gə", "白一平-沙加尔"),
            ("求", "群", "幽", "*gu", "白一平-沙加尔"),
            ("山", "生", "元", "*sren", "白一平-沙加尔"),
            ("产", "初", "元", "*srjenʔ", "白一平-沙加尔"),
            ("政", "章", "耕", "*teŋs", "白一平-沙加尔"),
            ("正", "章", "耕", "*teŋʔ", "白一平-沙加尔"),
            ("征", "章", "耕", "*teŋ", "白一平-沙加尔"),
            ("流", "来", "幽", "*ru", "白一平-沙加尔"),
            ("坤", "溪", "文", "*kʰˤun", "白一平-沙加尔"),
            ("顺", "船", "文", "*luns", "白一平-沙加尔"),
            ("辰", "禅", "文", "*dən", "白一平-沙加尔"),
            ("震", "章", "文", "*tərʔ", "白一平-沙加尔"),
        ]
        
        for char, shengmu, yunbu, recon, source in preset:
            self._index[char] = PhonologyEntry(
                char=char,
                shengmu=shengmu,
                yunbu=yunbu,
                reconstruction=recon,
                source=source
            )
    
    def query(self, char: str) -> Optional[PhonologyEntry]:
        """
        查询单个汉字的音韵信息
        
        Args:
            char: 要查询的汉字
            
        Returns:
            PhonologyEntry: 音韵信息
        """
        if not self._loaded:
            self.load()
        
        return self._index.get(char)
    
    def is_same_yunbu(self, char1: str, char2: str) -> bool:
        """判断两个字是否同韵部"""
        e1 = self.query(char1)
        e2 = self.query(char2)
        if e1 and e2:
            return e1.yunbu == e2.yunbu
        return False
    
    def is_same_shengmu(self, char1: str, char2: str) -> bool:
        """判断两个字是否同声母"""
        e1 = self.query(char1)
        e2 = self.query(char2)
        if e1 and e2:
            return e1.shengmu == e2.shengmu
        return False


# ===== 便捷函数 =====

_loader: Optional[PhonologyLoader] = None


def load_phonology(data_dir: Optional[str] = None) -> PhonologyLoader:
    """获取音韵加载器单例"""
    global _loader
    if _loader is None:
        _loader = PhonologyLoader(data_dir)
    return _loader


def query_phonology_entry(char: str) -> Optional[Dict[str, Any]]:
    """便捷查询函数"""
    loader = load_phonology()
    entry = loader.query(char)
    if entry:
        return {
            "字": entry.char,
            "声母": entry.shengmu,
            "韵部": entry.yunbu,
            "上古拟音": entry.reconstruction,
            "来源": entry.source
        }
    return None


# ===== 测试代码 =====
if __name__ == "__main__":
    loader = PhonologyLoader()
    loader.load()
    
    for char in ["崇", "终", "海", "晦"]:
        entry = loader.query(char)
        if entry:
            print(f"{char}: {entry.shengmu}母 {entry.yunbu}部 {entry.reconstruction}")
        else:
            print(f"{char}: 未收录")

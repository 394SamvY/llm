"""
音韵查询工具 (Phonology Tool) 
功能：
1. 读取 data/processed/phonology_unified.json 
2. 提供繁简转换 (OpenCC)
3. 动态展示拟音来源 (白一平/潘悟云)
4. 实现声训判定的核心逻辑

实现者：成员D
"""
import json
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass

# === 1. 第三方库引用 ===
try:
    from opencc import OpenCC
except ImportError:
    print("⚠️ 警告: 未安装 opencc-python-reimplemented。无法查询繁体索引。")
    print("👉 请运行: pip install opencc-python-reimplemented")
    OpenCC = None

# === 2. 路径配置 ===
# 当前文件: src/tools/phonology_tool.py
# 目标文件: data/processed/phonology_unified.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 向上两层找到根目录，再进 data/processed
DATA_FILE_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "../../data/processed/phonology_unified.json"))


@dataclass
class PhonologyInfo:
    """音韵信息实体类"""
    char: str              # 输入字 (简体)
    char_trad: str         # 索引字 (繁体)
    shengmu: str           # 声母 (潘)
    yunbu: str             # 韵部 (潘)
    pan_reconstruction: str # 拟音 (潘)
    bs_reconstruction: str  # 拟音 (BS)

class PhonologyTool:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path if data_path else DATA_FILE_PATH
        self._index: Dict[str, Any] = {}
        self._loaded = False
        self.cc = OpenCC('s2t') if OpenCC else None

    def load(self) -> None:
        """加载 JSON 数据"""
        if self._loaded:
            return
        
        print(f"[PhonologyTool] 正在加载数据: {self.data_path}")
        
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
                print(f"[PhonologyTool] ✅ 加载成功，共 {len(self._index)} 条数据。")
                self._loaded = True
            except Exception as e:
                print(f"[PhonologyTool] ❌ 加载失败: {e}")
                self._index = {}
        else:
            print(f"[PhonologyTool] ⚠️ 文件不存在: {self.data_path}")
            print("👉 请先让成员 E 运行数据处理脚本生成 json")
            self._index = self._get_mock_data() # 兜底
            self._loaded = True

    def query(self, char: str) -> PhonologyInfo:
        """查询单字 (含繁简转换)"""
        if not self._loaded:
            self.load()

        # 1. 繁简转换
        if self.cc:
            char_trad = self.cc.convert(char)
        else:
            char_trad = char
            
        # 2. 查询
        data = self._index.get(char_trad)
        
        # 兜底：查不到繁体查简体
        if not data:
            data = self._index.get(char)
            if data:
                char_trad = char

        if data:
            # 解析嵌套结构 (适配成员 E 的数据格式)
            pan = data.get("潘悟云", {})
            bs = data.get("白一平沙加尔", {})
            
            return PhonologyInfo(
                char=char,
                char_trad=char_trad,
                shengmu=pan.get("声母", "未知"),
                yunbu=pan.get("韵部", "未知"),
                pan_reconstruction=pan.get("上古音", "未知"),
                bs_reconstruction=bs.get("上古音", "未知")
            )
        else:
            return PhonologyInfo(
                char=char,
                char_trad=char_trad,
                shengmu="未收录",
                yunbu="未收录",
                pan_reconstruction="未收录",
                bs_reconstruction="未收录"
            )

    def is_phonetically_close(self, char1: str, char2: str) -> Dict[str, Any]:
        """
        判断音近逻辑 - 最终精简版
        逻辑标准：
        1. 【金标准】韵部相同 (叠韵) -> 直接判定 True
        2. 【银标准】拟音相似度 > 0.75 (发音极像) -> 判定 True
        3. 其他情况 -> False
        """
        p1 = self.query(char1)
        p2 = self.query(char2)

        # 1. 检查数据缺失
        if p1.yunbu == "未收录" or p2.yunbu == "未收录":
            return {
                "is_close": False, # 缺数据不敢乱说是
                "analysis": f"数据缺失：未收录 '{char1}' 或 '{char2}'",
                "char1_info": self._format_info(p1),
                "char2_info": self._format_info(p2)
            }

        # === 核心判定逻辑 ===
        
        is_close = False
        reasons = []

        # 判定 1: 韵部相同 (叠韵) - 这是声训最核心的依据
        same_yunbu = (p1.yunbu == p2.yunbu) and (p1.yunbu != "未知")
        
        if same_yunbu:
            is_close = True
            reasons.append(f"✅ 【叠韵】(均为{p1.yunbu}部)")
        
        # 判定 2: 拟音相似度 (兜底逻辑)
        # 即使韵部不同，如果发音高度相似 (比如同部位旁转)，也算音近
        recon1 = self._clean_ipa(p1.bs_reconstruction if p1.bs_reconstruction != "未知" else p1.pan_reconstruction)
        recon2 = self._clean_ipa(p2.bs_reconstruction if p2.bs_reconstruction != "未知" else p2.pan_reconstruction)
        
        sim_score = self._calculate_similarity(recon1, recon2)
        
        if not is_close and sim_score >= 0.75: # 相似度门槛
            is_close = True
            reasons.append(f"✅ 【音极近】(拟音相似度{int(sim_score*100)}%)")
        
        # 辅助信息：双声 (仅作为补充描述，不单独作为True的依据，除非结合拟音相似)
        same_shengmu = (p1.shengmu == p2.shengmu) and (p1.shengmu != "未知")
        if same_shengmu:
            reasons.append(f"【双声】({p1.shengmu}母)")

        # 生成分析结论
        if not is_close:
            reasons.append("❌ 音韵差异较大")

        # 补充拟音展示
        analysis_str = "；".join(reasons)
        analysis_str += f"；参考: {p1.char}[{recon1}] vs {p2.char}[{recon2}]"

        return {
            "is_close": is_close,  # 最终结论：True / False
            "same_yunbu": same_yunbu,
            "same_shengmu": same_shengmu,
            "char1_info": self._format_info(p1),
            "char2_info": self._format_info(p2),
            "analysis": analysis_str
        }

    # === 判断音近的两个辅助小函数 ===
    def _clean_ipa(self, ipa: str) -> str:
        """清洗拟音，只保留核心字母，去掉符号干扰"""
        if not ipa or ipa == "未知": return ""
        import re
        # 去掉 *, [], (), <>, - 和空格
        return re.sub(r'[\*\[\]\(\)\<\>\-\s]', '', ipa)

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度 (0~1)"""
        if not s1 or not s2: return 0.0
        if s1 == s2: return 1.0
        import difflib
        return difflib.SequenceMatcher(None, s1, s2).ratio()
    # ==============================

    def _get_best_recon(self, p: PhonologyInfo):
        """辅助函数：获取最佳拟音和来源"""
        if p.bs_reconstruction != "未知":
            return p.bs_reconstruction, "白一平-沙加尔汉语拟音"
        elif p.pan_reconstruction != "未知":
            return p.pan_reconstruction, "潘悟云《汉语古音手册》"
        else:
            return "未知", "无数据"

    def _format_info(self, p: PhonologyInfo) -> Dict[str, str]:
        recon, source = self._get_best_recon(p)
        return {
            "繁体": p.char_trad,
            "声母": p.shengmu,
            "韵部": p.yunbu,
            "上古音": recon,
            "上古音来源": source
        }
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Mock 数据"""
        return {
            "崇": {
                "潘悟云": {"声母": "崇", "韵部": "東", "上古音": "*dzruŋ"},
                "白一平沙加尔": {"上古音": "*[dz]<r>uŋ"}
            },
            "終": {
                "潘悟云": {"声母": "章", "韵部": "東", "上古音": "*tjuŋ"},
                "白一平沙加尔": {"上古音": "*tuŋ"}
            }
        }


# ===== 单例与接口 =====
_tool_instance: Optional[PhonologyTool] = None

def _get_tool() -> PhonologyTool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = PhonologyTool()
    return _tool_instance

def query_phonology(char: str) -> Dict[str, Any]:
    tool = _get_tool()
    info = tool.query(char)
    
    # 动态判断来源
    if info.bs_reconstruction != "未知":
        display_recon = info.bs_reconstruction
        display_source = "白一平-沙加尔汉语拟音"
    elif info.pan_reconstruction != "未知":
        display_recon = info.pan_reconstruction
        display_source = "潘悟云《汉语古音手册》"
    else:
        display_recon = "未知"
        display_source = "未知"

    return {
        "字": info.char,
        "声母": info.shengmu,
        "韵部": info.yunbu,
        "上古音": display_recon,
        "上古音来源": display_source  # 这里会根据实际展示的数据变化
    }

def check_phonetic_relation(char1: str, char2: str) -> Dict[str, Any]:
    tool = _get_tool()
    return tool.is_phonetically_close(char1, char2)


# ===== 测试代码 =====
if __name__ == "__main__":
    print(f">>> 🚀 测试音韵工具 (路径: {DATA_FILE_PATH})")
    
    try:
        # 测试 1: 查询
        c = "终"
        print(f"\n[1] 查询 '{c}':")
        print(query_phonology(c))

        # 测试 2: 比较
        print(f"\n[2] 比较 '崇' vs '终':")
        print(check_phonetic_relation("崇", "终"))
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
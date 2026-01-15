# 🛠️ 实现指南

> 本文档详细说明各模块的具体实现方法和代码示例

---

## 📋 实现优先级

```
P0 - 核心必须（Week 1-2）
├── ✅ 项目骨架搭建
├── ✅ 训式识别工具（Step 4）
├── ⏳ 字义查询工具（Step 1）
├── ⏳ 音韵查询工具（Step 2）
└── ⏳ 五步推理流程

P1 - 重要功能（Week 3）
├── ⏳ 异文检索工具（Step 3）
├── ⏳ 语境分析工具（Step 5）
├── ⏳ 测试数据集构建
└── ⏳ 评估报告

P2 - 增强功能（Week 4）
├── ⏳ 接入 LLM API
├── ⏳ 优化提示词
├── ⏳ 向量检索
└── ⏳ 可视化界面
```

---

## 🔧 Step 1: 语义分析工具

### 目标

查询《汉语大词典》获取字的本义和义项，判断两字是否"义近"或"义远"。

### 数据源

`《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl` (1.9GB)

### 数据结构

```json
{
  "headword": "崇",
  "pronunciations": [
    {
      "pinyin": "chóng",
      "phonology": {"声母": "船", "韵母": "东合三平", "声调": "平"}
    }
  ],
  "senses": [
    {
      "sense_num": "1",
      "definition": "高大。",
      "examples": [
        {"source": "《说文》", "quote": "崇，嵬高也。"}
      ]
    },
    {
      "sense_num": "2", 
      "definition": "尊崇，崇敬。",
      "examples": [...]
    }
  ]
}
```

### 实现代码

```python
# src/knowledge/dictionary_loader.py

import json
from pathlib import Path
from typing import Dict, List, Optional


class DictionaryLoader:
    """《汉语大词典》数据加载器"""
    
    def __init__(self, jsonl_path: str):
        self.jsonl_path = Path(jsonl_path)
        self.index: Dict[str, dict] = {}
        self._loaded = False
    
    def load(self, lazy: bool = True):
        """
        加载数据
        
        Args:
            lazy: True=按需加载，False=全部加载到内存
        """
        if lazy:
            # 构建行号索引，按需读取
            self._build_line_index()
        else:
            # 全部加载（需要大内存）
            self._load_all()
        self._loaded = True
    
    def _build_line_index(self):
        """构建 headword -> 行号 的索引"""
        self._line_positions = {}
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            position = 0
            for line in f:
                try:
                    data = json.loads(line.strip())
                    headword = data.get('headword', '')
                    if headword:
                        self._line_positions[headword] = position
                except:
                    pass
                position = f.tell()
    
    def query(self, char: str) -> Optional[dict]:
        """
        查询单字信息
        
        Args:
            char: 要查询的字
            
        Returns:
            字典条目或 None
        """
        if not self._loaded:
            self.load()
        
        # 先查内存缓存
        if char in self.index:
            return self.index[char]
        
        # 按需从文件读取
        if hasattr(self, '_line_positions') and char in self._line_positions:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                f.seek(self._line_positions[char])
                line = f.readline()
                data = json.loads(line.strip())
                self.index[char] = data  # 缓存
                return data
        
        return None
    
    def get_primary_meaning(self, char: str) -> str:
        """获取字的本义/首要义项"""
        data = self.query(char)
        if not data:
            return "未收录"
        
        senses = data.get('senses', [])
        if senses:
            # 返回第一个义项（通常是本义）
            return senses[0].get('definition', '未知')
        return "未知"
```

```python
# src/tools/semantic_tool.py

from typing import Dict, Tuple
from ..knowledge.dictionary_loader import DictionaryLoader


class SemanticTool:
    """语义分析工具 - Step 1"""
    
    def __init__(self, dictionary_path: str = None):
        if dictionary_path:
            self.dictionary = DictionaryLoader(dictionary_path)
        else:
            self.dictionary = None
    
    def query_meaning(self, char: str) -> dict:
        """查询字的语义信息"""
        if self.dictionary:
            data = self.dictionary.query(char)
            if data:
                return {
                    "char": char,
                    "found": True,
                    "meanings": data.get('senses', []),
                    "primary_meaning": self.dictionary.get_primary_meaning(char)
                }
        
        # 返回未找到
        return {
            "char": char,
            "found": False,
            "meanings": [],
            "primary_meaning": "未收录"
        }
    
    def compare_semantics(self, char_a: str, char_b: str) -> dict:
        """
        比较两字语义关联性
        
        核心逻辑：
        - 如果两字本义属于同一语义场 → 义近
        - 如果两字本义完全无关 → 义远
        """
        meaning_a = self.query_meaning(char_a)
        meaning_b = self.query_meaning(char_b)
        
        # 简化判断逻辑（后续可接入LLM增强）
        # 这里使用规则判断，实际应用中可用LLM
        
        primary_a = meaning_a.get("primary_meaning", "")
        primary_b = meaning_b.get("primary_meaning", "")
        
        # 简单规则：如果定义中包含对方字，可能义近
        is_related = (
            char_b in primary_a or 
            char_a in primary_b or
            self._check_semantic_field(primary_a, primary_b)
        )
        
        return {
            "char_a": char_a,
            "char_b": char_b,
            "meaning_a": primary_a,
            "meaning_b": primary_b,
            "relation": "义近" if is_related else "义远",
            "confidence": 0.7 if is_related else 0.8,
            "reasoning": self._generate_reasoning(primary_a, primary_b, is_related)
        }
    
    def _check_semantic_field(self, meaning_a: str, meaning_b: str) -> bool:
        """检查是否属于同一语义场（简化实现）"""
        # 定义一些语义场关键词
        semantic_fields = [
            ["高", "大", "崇", "巨", "伟"],
            ["终", "末", "尽", "完", "毕", "结"],
            ["暗", "黑", "晦", "昏", "暝"],
            ["明", "亮", "光", "辉", "皎"],
            ["行", "走", "道", "路", "径"],
            # ... 可扩展
        ]
        
        for field in semantic_fields:
            if any(w in meaning_a for w in field) and any(w in meaning_b for w in field):
                return True
        return False
    
    def _generate_reasoning(self, meaning_a: str, meaning_b: str, is_related: bool) -> str:
        if is_related:
            return f"'{meaning_a}'与'{meaning_b}'存在语义关联"
        else:
            return f"'{meaning_a}'与'{meaning_b}'语义无关联"
```

---

## 🔧 Step 2: 语音分析工具

### 目标

查询上古音数据，判断两字是否"音近"。

### 数据源

1. `音韵数据/上古音/潘悟云《汉语古音手册》/汉语古音手册.txt`
2. `音韵数据/上古音/斯塔罗斯金汉语拟音/Chinese-characters.txt`
3. `音韵数据/上古音/白一平-沙加尔的汉语拟音体系/BaxterSagartOC2015-10-13.xlsx`

### 实现代码

```python
# src/knowledge/phonology_loader.py

import re
from pathlib import Path
from typing import Dict, Optional


class PhonologyLoader:
    """上古音数据加载器"""
    
    def __init__(self, data_dir: str = None):
        self.data: Dict[str, dict] = {}
        if data_dir:
            self._load_from_dir(Path(data_dir))
    
    def _load_from_dir(self, data_dir: Path):
        """从目录加载所有数据源"""
        # 1. 加载潘悟云数据
        pan_path = data_dir / "潘悟云《汉语古音手册》" / "汉语古音手册.txt"
        if pan_path.exists():
            self._load_pan_wuyun(pan_path)
        
        # 2. 加载斯塔罗斯金数据
        sta_path = data_dir / "斯塔罗斯金汉语拟音" / "Chinese-characters.txt"
        if sta_path.exists():
            self._load_starostin(sta_path)
    
    def _load_pan_wuyun(self, path: Path):
        """加载潘悟云《汉语古音手册》"""
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析格式（需根据实际格式调整）
                parts = line.split('\t')
                if len(parts) >= 4:
                    char = parts[0]
                    self.data[char] = {
                        "声母": parts[1] if len(parts) > 1 else "",
                        "韵部": parts[2] if len(parts) > 2 else "",
                        "拟音": parts[3] if len(parts) > 3 else "",
                        "source": "潘悟云《汉语古音手册》"
                    }
    
    def _load_starostin(self, path: Path):
        """加载斯塔罗斯金拟音数据"""
        # 类似处理，根据实际格式调整
        pass
    
    def query(self, char: str) -> Optional[dict]:
        """查询单字的上古音"""
        return self.data.get(char)
```

```python
# src/tools/phonology_tool.py

from typing import Dict
from ..knowledge.phonology_loader import PhonologyLoader


# 韵部相近关系表
YUNBU_GROUPS = {
    # 阴声韵
    "之": ["之", "职", "蒸"],
    "支": ["支", "锡", "耕"],
    "鱼": ["鱼", "铎", "阳"],
    "侯": ["侯", "屋", "东"],
    "宵": ["宵", "药", "觉"],
    "幽": ["幽", "觉", "冬"],
    "微": ["微", "物", "文"],
    "歌": ["歌", "月", "元"],
    # 入声韵
    "职": ["职", "之", "蒸"],
    "锡": ["锡", "支", "耕"],
    "铎": ["铎", "鱼", "阳"],
    "屋": ["屋", "侯", "东"],
    "药": ["药", "宵", "觉"],
    "物": ["物", "微", "文"],
    "月": ["月", "歌", "元"],
    # 阳声韵
    "蒸": ["蒸", "之", "职"],
    "耕": ["耕", "支", "锡"],
    "阳": ["阳", "鱼", "铎"],
    "东": ["东", "侯", "屋"],
    "冬": ["冬", "幽", "觉"],
    "文": ["文", "微", "物"],
    "元": ["元", "歌", "月"],
    "真": ["真", "谆", "臻"],
    "谈": ["谈", "盐", "添"],
    "侵": ["侵", "覃", "谈"],
}

# 声母相近关系表
SHENGMU_GROUPS = {
    "帮": ["帮", "滂", "并", "明"],  # 唇音
    "滂": ["帮", "滂", "并", "明"],
    "并": ["帮", "滂", "并", "明"],
    "明": ["帮", "滂", "并", "明"],
    
    "端": ["端", "透", "定", "泥"],  # 舌头音
    "透": ["端", "透", "定", "泥"],
    "定": ["端", "透", "定", "泥"],
    "泥": ["端", "透", "定", "泥"],
    
    "精": ["精", "清", "从", "心", "邪"],  # 齿头音
    "清": ["精", "清", "从", "心", "邪"],
    "从": ["精", "清", "从", "心", "邪"],
    "心": ["精", "清", "从", "心", "邪"],
    "邪": ["精", "清", "从", "心", "邪"],
    
    "章": ["章", "昌", "船", "书", "禅"],  # 正齿音
    "昌": ["章", "昌", "船", "书", "禅"],
    "船": ["章", "昌", "船", "书", "禅"],
    "书": ["章", "昌", "船", "书", "禅"],
    "禅": ["章", "昌", "船", "书", "禅"],
    
    "见": ["见", "溪", "群", "疑"],  # 牙音
    "溪": ["见", "溪", "群", "疑"],
    "群": ["见", "溪", "群", "疑"],
    "疑": ["见", "溪", "群", "疑"],
    
    "影": ["影", "晓", "匣", "喻"],  # 喉音
    "晓": ["影", "晓", "匣", "喻"],
    "匣": ["影", "晓", "匣", "喻"],
    "喻": ["影", "晓", "匣", "喻"],
    
    "来": ["来"],  # 半舌音
    "日": ["日"],  # 半齿音
}


class PhonologyTool:
    """语音分析工具 - Step 2"""
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.loader = PhonologyLoader(data_dir)
        else:
            self.loader = None
    
    def query_phonology(self, char: str) -> dict:
        """查询字的上古音"""
        if self.loader:
            data = self.loader.query(char)
            if data:
                return {
                    "char": char,
                    "found": True,
                    **data
                }
        
        return {
            "char": char,
            "found": False,
            "声母": "未收录",
            "韵部": "未收录",
            "拟音": "未收录"
        }
    
    def compare_phonology(self, char_a: str, char_b: str) -> dict:
        """比较两字语音关系"""
        phon_a = self.query_phonology(char_a)
        phon_b = self.query_phonology(char_b)
        
        # 判断韵部是否相近
        yunbu_a = phon_a.get("韵部", "")
        yunbu_b = phon_b.get("韵部", "")
        yunbu_close = self._is_yunbu_close(yunbu_a, yunbu_b)
        
        # 判断声母是否相近
        shengmu_a = phon_a.get("声母", "")
        shengmu_b = phon_b.get("声母", "")
        shengmu_close = self._is_shengmu_close(shengmu_a, shengmu_b)
        
        # 综合判断：韵部相同或相近 + 声母相近 = 音近
        is_close = yunbu_close and shengmu_close
        
        details = []
        if yunbu_a == yunbu_b:
            details.append(f"韵部相同（{yunbu_a}部）")
        elif yunbu_close:
            details.append(f"韵部相近（{yunbu_a} / {yunbu_b}）")
        else:
            details.append(f"韵部不同（{yunbu_a} / {yunbu_b}）")
        
        if shengmu_a == shengmu_b:
            details.append(f"声母相同（{shengmu_a}母）")
        elif shengmu_close:
            details.append(f"声母相近（{shengmu_a} / {shengmu_b}）")
        else:
            details.append(f"声母不同（{shengmu_a} / {shengmu_b}）")
        
        return {
            "char_a": char_a,
            "char_b": char_b,
            "phon_a": phon_a,
            "phon_b": phon_b,
            "relation": "音近" if is_close else "音远",
            "details": "；".join(details),
            "confidence": 0.9 if is_close else 0.85
        }
    
    def _is_yunbu_close(self, yunbu_a: str, yunbu_b: str) -> bool:
        """判断韵部是否相近"""
        if yunbu_a == yunbu_b:
            return True
        
        group_a = YUNBU_GROUPS.get(yunbu_a, [yunbu_a])
        return yunbu_b in group_a
    
    def _is_shengmu_close(self, shengmu_a: str, shengmu_b: str) -> bool:
        """判断声母是否相近"""
        if shengmu_a == shengmu_b:
            return True
        
        group_a = SHENGMU_GROUPS.get(shengmu_a, [shengmu_a])
        return shengmu_b in group_a
```

---

## 🔧 Step 3: 异文检索工具

### 目标

从词典中检索异文记录、假借标注等佐证材料。

### 实现代码

```python
# src/tools/textual_tool.py

import re
from typing import List, Dict
from ..knowledge.dictionary_loader import DictionaryLoader


class TextualTool:
    """异文与文例检索工具 - Step 3"""
    
    def __init__(self, dictionary_path: str = None):
        if dictionary_path:
            self.dictionary = DictionaryLoader(dictionary_path)
        else:
            self.dictionary = None
    
    def search_evidence(self, char_a: str, char_b: str) -> dict:
        """
        检索两字的正借替代关系证据
        
        检索内容：
        1. 词典中的异文记录
        2. 词典中的假借标注
        3. 例句中两字互现
        """
        evidence = {
            "异文": [],
            "假借标注": [],
            "相关例句": []
        }
        
        if self.dictionary:
            # 查询两字的词条
            data_a = self.dictionary.query(char_a)
            data_b = self.dictionary.query(char_b)
            
            # 1. 检查假借标注
            if data_a:
                jiajie = self._find_jiajie_annotation(data_a, char_b)
                if jiajie:
                    evidence["假借标注"].extend(jiajie)
            
            if data_b:
                jiajie = self._find_jiajie_annotation(data_b, char_a)
                if jiajie:
                    evidence["假借标注"].extend(jiajie)
            
            # 2. 检查例句中的异文
            if data_a:
                yiwen = self._find_yiwen(data_a, char_b)
                if yiwen:
                    evidence["异文"].extend(yiwen)
        
        # 判断是否有佐证
        has_evidence = (
            len(evidence["异文"]) > 0 or
            len(evidence["假借标注"]) > 0
        )
        
        return {
            "char_a": char_a,
            "char_b": char_b,
            "has_evidence": has_evidence,
            "evidence": evidence,
            "summary": self._generate_summary(evidence)
        }
    
    def _find_jiajie_annotation(self, data: dict, target_char: str) -> List[str]:
        """在词条中查找假借标注"""
        results = []
        
        # 检查义项中是否有假借说明
        for sense in data.get('senses', []):
            definition = sense.get('definition', '')
            
            # 常见假借标注模式
            patterns = [
                rf"通[「「"]?{target_char}[」」"]?",
                rf"假借[为為]?[「「"]?{target_char}[」」"]?",
                rf"读[为為]?[「「"]?{target_char}[」」"]?",
                rf"与[「「"]?{target_char}[」」"]?通",
            ]
            
            for pattern in patterns:
                if re.search(pattern, definition):
                    results.append(definition[:100])
                    break
        
        return results
    
    def _find_yiwen(self, data: dict, target_char: str) -> List[str]:
        """在例句中查找异文"""
        results = []
        
        for sense in data.get('senses', []):
            for example in sense.get('examples', []):
                quote = example.get('quote', '')
                source = example.get('source', '')
                
                # 检查是否提到异文
                if target_char in quote or "异文" in quote or "一作" in quote:
                    results.append(f"{source}: {quote[:50]}")
        
        return results
    
    def _generate_summary(self, evidence: dict) -> str:
        """生成证据摘要"""
        parts = []
        
        if evidence["异文"]:
            parts.append(f"找到{len(evidence['异文'])}处异文")
        
        if evidence["假借标注"]:
            parts.append(f"找到{len(evidence['假借标注'])}处假借记录")
        
        if parts:
            return "；".join(parts)
        else:
            return "未找到相关佐证"
```

---

## 🔧 Step 4: 训式识别工具

### 状态：✅ 已实现

见 `src/tools/pattern_tool.py`，包含 50+ 训释格式的正则匹配。

### 核心代码片段

```python
# 已实现的训式模式（部分）
XUNSHI_PATTERNS = {
    # ===== A类：直接判假借 =====
    "读为": {
        "regex": r"(.+)[，,]\s*读为\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True
    },
    "读曰": {
        "regex": r"(.+)[，,]\s*读曰\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True
    },
    "当为": {
        "regex": r"(.+)[，,]\s*当为\s*(.+)",
        "type": "假借",
        "confidence": "高",
        "direct_judge": True
    },
    
    # ===== B类：直接判语义 =====
    "犹...也": {
        "regex": r"(.+)[，,]\s*犹\s*(.+)\s*也",
        "type": "语义",
        "confidence": "高",
        "direct_judge": True
    },
    
    # ===== C类：需综合判断 =====
    "A也": {
        "regex": r"(.+)[，,]\s*(.+)也$",
        "type": "不确定",
        "confidence": "低",
        "direct_judge": False
    }
}
```

---

## 🔧 Step 5: 语境分析工具

### 目标

将本义代入原句，判断语义是否通顺。

### 实现代码

```python
# src/tools/context_tool.py

from typing import Optional


class ContextTool:
    """语境适配度分析工具 - Step 5"""
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM客户端，用于语义分析
        """
        self.llm = llm_client
    
    def analyze_context(
        self,
        beishi: str,
        shi: str,
        context: str,
        meaning_beishi: str = None,
        meaning_shi: str = None
    ) -> dict:
        """
        分析语境适配度
        
        核心逻辑：
        - 将被释字的本义代入原句，检查是否通顺
        - 将释字的本义代入原句，检查是否通顺
        - 借字本义不通 + 正字本义通顺 = 支持假借
        """
        if not context:
            return {
                "beishi": beishi,
                "shi": shi,
                "context": None,
                "conclusion": "无语境",
                "reasoning": "未提供原文语境，无法进行适配度分析"
            }
        
        # 如果有LLM，使用LLM分析
        if self.llm:
            return self._analyze_with_llm(
                beishi, shi, context, meaning_beishi, meaning_shi
            )
        
        # 否则使用规则判断（简化版）
        return self._analyze_with_rules(
            beishi, shi, context, meaning_beishi, meaning_shi
        )
    
    def _analyze_with_llm(
        self,
        beishi: str,
        shi: str,
        context: str,
        meaning_beishi: str,
        meaning_shi: str
    ) -> dict:
        """使用LLM分析语境适配度"""
        
        prompt = f"""你是一位古汉语专家，请分析以下语境适配度：

原文：{context}
被释字：{beishi}，本义：{meaning_beishi}
释字：{shi}，本义：{meaning_shi}

请判断：
1. 将"{beishi}"的本义"{meaning_beishi}"代入原句"{context}"，语义是否通顺？
2. 将"{shi}"的本义"{meaning_shi}"代入原句，语义是否通顺？

请按以下格式回答：
被释字代入: [通顺/不通顺]
释字代入: [通顺/不通顺]
结论: [支持假借/支持语义/不确定]
分析: [简要说明]
"""
        
        # 调用LLM
        response = self.llm.generate(prompt)
        
        # 解析响应
        return self._parse_llm_response(response, beishi, shi, context)
    
    def _analyze_with_rules(
        self,
        beishi: str,
        shi: str,
        context: str,
        meaning_beishi: str,
        meaning_shi: str
    ) -> dict:
        """使用规则分析（简化版，作为备选）"""
        
        # 简单替换检查
        substituted_beishi = context.replace(beishi, f"({meaning_beishi})")
        substituted_shi = context.replace(beishi, f"({meaning_shi})")
        
        return {
            "beishi": beishi,
            "shi": shi,
            "context": context,
            "analysis": {
                "beishi_substituted": substituted_beishi,
                "shi_substituted": substituted_shi
            },
            "conclusion": "不确定",
            "reasoning": "需要人工判断或LLM辅助分析"
        }
    
    def _parse_llm_response(self, response: str, beishi: str, shi: str, context: str) -> dict:
        """解析LLM响应"""
        # 简化解析逻辑
        conclusion = "不确定"
        
        if "支持假借" in response:
            conclusion = "支持假借"
        elif "支持语义" in response:
            conclusion = "支持语义"
        
        return {
            "beishi": beishi,
            "shi": shi,
            "context": context,
            "conclusion": conclusion,
            "reasoning": response
        }
```

---

## 🔧 接入 LLM API

### Anthropic Claude

```python
# src/llm/claude_client.py

import os
from anthropic import Anthropic


class ClaudeClient:
    def __init__(self, api_key: str = None):
        self.client = Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-3-5-sonnet-20241022"
    
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
```

### OpenAI GPT

```python
# src/llm/openai_client.py

import os
from openai import OpenAI


class OpenAIClient:
    def __init__(self, api_key: str = None):
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-4-turbo-preview"
    
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
```

---

## 📊 测试数据集构建

### 从参考资料提取

```python
# scripts/extract_test_cases.py

import re

def extract_jiajie_examples(text: str) -> list:
    """从参考资料中提取假借示例"""
    examples = []
    
    # 匹配模式：X，读为/读曰/当为 Y
    patterns = [
        r"[「「](.+)[，,]\s*读为\s*(.+)[」」]",
        r"[「「](.+)[，,]\s*读曰\s*(.+)[」」]",
        r"例如.+?[「「](.+)[，,]\s*(.+)也[」」].+?假借",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            examples.append({
                "xungu_sentence": f"{match[0]}，{match[1]}",
                "beishi_char": match[0],
                "shi_char": match[1],
                "expected_label": "假借说明"
            })
    
    return examples
```

---

## 🔗 相关文档

- [快速开始](QUICK_START.md)
- [任务要求](TASK_REQUIREMENTS.md)
- [架构设计](ARCHITECTURE.md)
- [开发计划](DEVELOPMENT_PLAN.md)

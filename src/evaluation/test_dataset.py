"""
测试数据集管理

负责人：成员E（或成员C）

数据来源：从参考资料中提取已标注的训诂句
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TestCase:
    """测试用例"""
    id: int
    xungu_sentence: str  # 训诂句
    char_a: str  # 被释字
    char_b: str  # 释字
    context: Optional[str]  # 上下文
    source: Optional[str]  # 出处
    expected_label: str  # 期望标签：假借说明/语义解释
    note: str = ""  # 备注


class TestDataset:
    """
    测试数据集
    
    负责人：成员E
    
    使用方法：
        dataset = TestDataset()
        dataset.load("data/test/test_dataset.json")
        for case in dataset:
            print(case.xungu_sentence, case.expected_label)
    """
    
    def __init__(self):
        self.cases: List[TestCase] = []
    
    def load(self, json_path: str) -> None:
        """从JSON文件加载测试数据"""
        path = Path(json_path)
        if not path.exists():
            print(f"测试数据文件不存在: {path}")
            # 使用预设数据
            self._load_preset_data()
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            self.cases.append(TestCase(
                id=item.get("id", 0),
                xungu_sentence=item["训诂句"],
                char_a=item.get("被释字", ""),
                char_b=item.get("释字", ""),
                context=item.get("上下文"),
                source=item.get("出处"),
                expected_label=item["正确答案"],
                note=item.get("备注", "")
            ))
        
        print(f"加载了 {len(self.cases)} 条测试数据")
    
    def _load_preset_data(self) -> None:
        """
        加载预设的测试数据
        
        来源：参考资料2/3/4中的训诂句示例
        """
        preset = [
            # 假借类
            {
                "id": 1,
                "训诂句": "崇，终也",
                "被释字": "崇",
                "释字": "终",
                "上下文": "崇朝其雨",
                "出处": "《诗·邶风·简兮》《毛传》",
                "正确答案": "假借说明",
                "备注": "有异文《小雅·采绿》作'终朝'"
            },
            {
                "id": 2,
                "训诂句": "正，读为征",
                "被释字": "正",
                "释字": "征",
                "上下文": "正其货贿",
                "出处": "《周礼·地官·司门》郑玄注",
                "正确答案": "假借说明",
                "备注": "读为是假借的标准术语"
            },
            {
                "id": 3,
                "训诂句": "累，倮也",
                "被释字": "累",
                "释字": "倮",
                "上下文": "为大夫累之",
                "出处": "《礼记·曲礼上》郑玄注",
                "正确答案": "假借说明",
                "备注": "以正字释借字"
            },
            {
                "id": 4,
                "训诂句": "高，膏也",
                "被释字": "高",
                "释字": "膏",
                "上下文": "高梁之变",
                "出处": "《黄帝内经》王冰注",
                "正确答案": "假借说明",
                "备注": ""
            },
            {
                "id": 5,
                "训诂句": "虹，江也",
                "被释字": "虹",
                "释字": "江",
                "上下文": "彼童而角，实虹小子",
                "出处": "《诗·邶风·泉水》《毛传》",
                "正确答案": "假借说明",
                "备注": "以正字义释借字"
            },
            
            # 语义解释类（以声通义）
            {
                "id": 6,
                "训诂句": "海，晦也",
                "被释字": "海",
                "释字": "晦",
                "上下文": "海，晦也，主承秽浊，其色黑而晦也",
                "出处": "《释名·释天》",
                "正确答案": "语义解释",
                "备注": "以声通义，揭示语源"
            },
            {
                "id": 7,
                "训诂句": "山，产也",
                "被释字": "山",
                "释字": "产",
                "上下文": "山，产也，产生物也",
                "出处": "《释名·释山》",
                "正确答案": "语义解释",
                "备注": "以声通义"
            },
            {
                "id": 8,
                "训诂句": "阳，扬也",
                "被释字": "阳",
                "释字": "扬",
                "上下文": "阳，扬也，气在外发扬也",
                "出处": "《释名·释天》",
                "正确答案": "语义解释",
                "备注": "以声通义"
            },
            {
                "id": 9,
                "训诂句": "祈，求也",
                "被释字": "祈",
                "释字": "求",
                "上下文": "祈，求也。求中以辞尔爵也",
                "出处": "《礼记·射义》",
                "正确答案": "语义解释",
                "备注": "双声为训，音近义近"
            },
            {
                "id": 10,
                "训诂句": "夭夭，盛也",
                "被释字": "夭夭",
                "释字": "盛",
                "上下文": "桃之夭夭",
                "出处": "《诗·周南·桃夭》《毛传》",
                "正确答案": "语义解释",
                "备注": "描述形态，语义解释"
            },
            {
                "id": 11,
                "训诂句": "逑，匹也",
                "被释字": "逑",
                "释字": "匹",
                "上下文": "窈窕淑女，君子好逑",
                "出处": "《诗·周南·关雎》《毛传》",
                "正确答案": "语义解释",
                "备注": "同义互训"
            },
            {
                "id": 12,
                "训诂句": "政者，正也",
                "被释字": "政",
                "释字": "正",
                "上下文": "",
                "出处": "《论语·颜渊》",
                "正确答案": "语义解释",
                "备注": "以得声字通形声字音义"
            },
        ]
        
        for item in preset:
            self.cases.append(TestCase(**item))
        
        print(f"加载了 {len(self.cases)} 条预设测试数据")
    
    def save(self, json_path: str) -> None:
        """保存测试数据到JSON文件"""
        data = []
        for case in self.cases:
            data.append({
                "id": case.id,
                "训诂句": case.xungu_sentence,
                "被释字": case.char_a,
                "释字": case.char_b,
                "上下文": case.context,
                "出处": case.source,
                "正确答案": case.expected_label,
                "备注": case.note
            })
        
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"保存了 {len(data)} 条测试数据到 {path}")
    
    def __len__(self) -> int:
        return len(self.cases)
    
    def __iter__(self):
        return iter(self.cases)
    
    def __getitem__(self, idx) -> TestCase:
        return self.cases[idx]


def load_test_dataset(path: Optional[str] = None) -> TestDataset:
    """加载测试数据集"""
    dataset = TestDataset()
    if path:
        dataset.load(path)
    else:
        dataset._load_preset_data()
    return dataset


# ===== 测试代码 =====
if __name__ == "__main__":
    dataset = load_test_dataset()
    
    print("\n测试数据集预览:")
    print("-" * 60)
    for case in dataset:
        print(f"[{case.id}] {case.xungu_sentence}")
        print(f"    期望: {case.expected_label}")
        print(f"    出处: {case.source}")
        print()

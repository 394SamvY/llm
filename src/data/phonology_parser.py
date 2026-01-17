"""
音韵数据解析器

负责人：成员E（数据工程）

解析多种音韵数据源：
1. 潘悟云《汉语古音手册》TXT
2. 白一平-沙加尔 XLSX
3. 整合为统一格式
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from html.parser import HTMLParser


class PanwuyunHTMLParser(HTMLParser):
    """解析潘悟云数据中的HTML表格"""
    
    def __init__(self):
        super().__init__()
        self.current_tag = None
        self.current_th = None
        self.data = {}
        self.in_table = False
        self.in_h1 = False
        self.char = None
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == 'table':
            self.in_table = True
        elif tag == 'h1':
            self.in_h1 = True
    
    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'h1':
            self.in_h1 = False
        self.current_tag = None
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        
        if self.in_h1:
            self.char = data
        elif self.in_table:
            if self.current_tag == 'th':
                self.current_th = data
            elif self.current_tag == 'td' and self.current_th:
                self.data[self.current_th] = data
                self.current_th = None


def parse_panwuyun_txt(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    解析潘悟云《汉语古音手册》TXT文件
    
    Args:
        filepath: TXT文件路径
    
    Returns:
        Dict[str, Dict]: { "崇": {"韵部": "东", "上古音": "*dzruŋ", ...}, ... }
    """
    result = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按 </> 分割记录
    records = content.split('</>')
    
    for record in records:
        record = record.strip()
        if not record:
            continue
        
        # 分离字和HTML内容
        lines = record.split('\n', 1)
        if len(lines) < 2:
            continue
        
        char = lines[0].strip()
        html_content = lines[1].strip() if len(lines) > 1 else ""
        
        # 跳过无效字符
        if not char or len(char) > 2:
            continue
        
        # 解析HTML
        parser = PanwuyunHTMLParser()
        try:
            parser.feed(html_content)
        except:
            continue
        
        # 提取关键字段
        entry = {
            "字": char,
            "上古韵部": parser.data.get("上古韻部", ""),
            "上古音": parser.data.get("上古音", ""),
            "声母": parser.data.get("聲母", ""),
            "韵": parser.data.get("韻", ""),
            "开合": parser.data.get("開合", ""),
            "等": parser.data.get("等", ""),
            "声调": parser.data.get("聲調", ""),
            "反切": parser.data.get("反切", ""),
        }
        
        # 清理韵部编号（如 "30-月e" -> "月"）
        yunbu = entry["上古韵部"]
        if yunbu and '-' in yunbu:
            yunbu = yunbu.split('-')[1]
            # 移除末尾的字母标记（如 "歌a" -> "歌"）
            yunbu = re.sub(r'[a-z]$', '', yunbu)
            entry["上古韵部"] = yunbu
        
        # 如果该字已存在，可能是异读，暂时用第一个
        if char not in result:
            result[char] = entry
    
    return result


def parse_baxter_sagart_xlsx(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    解析白一平-沙加尔上古音数据
    
    Args:
        filepath: XLSX文件路径
    
    Returns:
        Dict[str, Dict]: { "崇": {"OC": "*[d]roŋ", "MC": "...", ...}, ... }
    """
    try:
        import pandas as pd
    except ImportError:
        print("警告: pandas未安装，无法解析XLSX文件")
        return {}
    
    result = {}
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        print(f"读取XLSX文件失败: {e}")
        return {}
    
    for _, row in df.iterrows():
        char = str(row.get('zi', '')).strip()
        if not char or len(char) > 2:
            continue
        
        entry = {
            "字": char,
            "拼音": str(row.get('py', '')),
            "中古音": str(row.get('MC', '')),
            "上古音": str(row.get('OC', '')),
            "释义": str(row.get('gloss', '')),
            "GSR": str(row.get('GSR', '')),
        }
        
        # 清理nan值
        for k, v in entry.items():
            if v == 'nan':
                entry[k] = ''
        
        if char not in result:
            result[char] = entry
    
    return result


def unify_phonology_data(
    panwuyun_data: Dict[str, Dict],
    baxter_data: Dict[str, Dict]
) -> Dict[str, Dict[str, Any]]:
    """
    整合多源音韵数据为统一格式
    
    Args:
        panwuyun_data: 潘悟云数据
        baxter_data: 白一平-沙加尔数据
    
    Returns:
        统一格式的音韵数据
    """
    result = {}
    
    # 获取所有字符
    all_chars = set(panwuyun_data.keys()) | set(baxter_data.keys())
    
    for char in all_chars:
        entry = {"字": char}
        
        # 添加潘悟云数据
        if char in panwuyun_data:
            pan = panwuyun_data[char]
            entry["潘悟云"] = {
                "韵部": pan.get("上古韵部", ""),
                "上古音": pan.get("上古音", ""),
                "声母": pan.get("声母", ""),
                "韵": pan.get("韵", ""),
                "声调": pan.get("声调", ""),
            }
        
        # 添加白一平-沙加尔数据
        if char in baxter_data:
            bax = baxter_data[char]
            entry["白一平沙加尔"] = {
                "上古音": bax.get("上古音", ""),
                "中古音": bax.get("中古音", ""),
                "释义": bax.get("释义", ""),
            }
        
        result[char] = entry
    
    return result


def compare_phonology(
    char_a: str,
    char_b: str,
    data: Dict[str, Dict]
) -> Dict[str, Any]:
    """
    比较两个字的音韵关系
    
    Args:
        char_a: 第一个字
        char_b: 第二个字
        data: 统一的音韵数据
    
    Returns:
        比较结果，包含是否音近的判断
    """
    result = {
        "char_a": char_a,
        "char_b": char_b,
        "found_a": char_a in data,
        "found_b": char_b in data,
        "音近": False,
        "韵部相同": False,
        "声母相近": False,
        "详情": {}
    }
    
    if char_a not in data or char_b not in data:
        result["详情"]["error"] = "缺少音韵数据"
        return result
    
    data_a = data[char_a]
    data_b = data[char_b]
    
    # 比较潘悟云数据
    if "潘悟云" in data_a and "潘悟云" in data_b:
        pan_a = data_a["潘悟云"]
        pan_b = data_b["潘悟云"]
        
        yunbu_a = pan_a.get("韵部", "")
        yunbu_b = pan_b.get("韵部", "")
        
        shengmu_a = pan_a.get("声母", "")
        shengmu_b = pan_b.get("声母", "")
        
        result["详情"]["潘悟云"] = {
            "韵部_A": yunbu_a,
            "韵部_B": yunbu_b,
            "声母_A": shengmu_a,
            "声母_B": shengmu_b,
            "上古音_A": pan_a.get("上古音", ""),
            "上古音_B": pan_b.get("上古音", ""),
        }
        
        # 判断韵部是否相同
        if yunbu_a and yunbu_b and yunbu_a == yunbu_b:
            result["韵部相同"] = True
        
        # 判断声母是否相近（简化判断：相同则相近）
        if shengmu_a and shengmu_b:
            # 声母相近规则（可扩展）
            similar_shengmu = [
                {"端", "透", "定", "泥"},  # 舌头音
                {"知", "彻", "澄", "娘"},  # 舌上音
                {"精", "清", "从", "心", "邪"},  # 齿头音
                {"庄", "初", "崇", "山"},  # 正齿音
                {"章", "昌", "常", "书", "船"},  # 正齿音
                {"见", "溪", "群", "疑"},  # 牙音
                {"帮", "滂", "並", "明"},  # 唇音
                {"非", "敷", "奉", "微"},  # 轻唇音
                {"影", "晓", "匣", "喻", "云"},  # 喉音
                {"来", "日"},  # 半舌半齿
            ]
            
            for group in similar_shengmu:
                if shengmu_a in group and shengmu_b in group:
                    result["声母相近"] = True
                    break
            
            if shengmu_a == shengmu_b:
                result["声母相近"] = True
    
    # 综合判断是否音近
    if result["韵部相同"] or result["声母相近"]:
        result["音近"] = True
    
    return result


def save_phonology_data(data: Dict, output_path: str) -> None:
    """保存音韵数据到JSON文件"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"音韵数据已保存到: {path}")
    print(f"共 {len(data)} 个字")


def load_phonology_data(filepath: str) -> Dict:
    """从JSON文件加载音韵数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# ===== 主函数 =====

def build_phonology_index(
    panwuyun_path: str = None,
    baxter_path: str = None,
    output_path: str = None
) -> Dict[str, Dict]:
    """
    构建完整的音韵索引
    
    Args:
        panwuyun_path: 潘悟云数据路径
        baxter_path: 白一平-沙加尔数据路径
        output_path: 输出路径
    
    Returns:
        统一的音韵数据
    """
    # 默认路径
    project_root = Path(__file__).parent.parent.parent
    
    if panwuyun_path is None:
        panwuyun_path = project_root / "音韵数据/上古音/潘悟云《汉语古音手册》/汉语古音手册.txt"
    
    if baxter_path is None:
        baxter_path = project_root / "音韵数据/上古音/白一平-沙加尔的汉语拟音体系/BaxterSagartOC2015-10-13.xlsx"
    
    if output_path is None:
        output_path = project_root / "data/processed/phonology_unified.json"
    
    print("=" * 50)
    print("构建音韵数据索引")
    print("=" * 50)
    
    # 解析潘悟云数据
    print(f"\n[1/3] 解析潘悟云数据: {panwuyun_path}")
    panwuyun_data = {}
    if Path(panwuyun_path).exists():
        panwuyun_data = parse_panwuyun_txt(str(panwuyun_path))
        print(f"  → 解析了 {len(panwuyun_data)} 个字")
    else:
        print(f"  → 文件不存在，跳过")
    
    # 解析白一平-沙加尔数据
    print(f"\n[2/3] 解析白一平-沙加尔数据: {baxter_path}")
    baxter_data = {}
    if Path(baxter_path).exists():
        baxter_data = parse_baxter_sagart_xlsx(str(baxter_path))
        print(f"  → 解析了 {len(baxter_data)} 个字")
    else:
        print(f"  → 文件不存在，跳过")
    
    # 整合数据
    print(f"\n[3/3] 整合数据...")
    unified_data = unify_phonology_data(panwuyun_data, baxter_data)
    print(f"  → 整合了 {len(unified_data)} 个字")
    
    # 保存
    save_phonology_data(unified_data, str(output_path))
    
    return unified_data


# ===== 测试代码 =====

if __name__ == "__main__":
    # 构建索引
    data = build_phonology_index()
    
    # 测试查询
    print("\n" + "=" * 50)
    print("测试音韵查询")
    print("=" * 50)
    
    test_chars = ["崇", "终", "海", "晦", "山", "产"]
    for char in test_chars:
        if char in data:
            print(f"\n【{char}】")
            entry = data[char]
            if "潘悟云" in entry:
                pan = entry["潘悟云"]
                print(f"  潘悟云: 韵部={pan.get('韵部')}, 上古音={pan.get('上古音')}, 声母={pan.get('声母')}")
            if "白一平沙加尔" in entry:
                bax = entry["白一平沙加尔"]
                print(f"  白一平: 上古音={bax.get('上古音')}")
    
    # 测试比较
    print("\n" + "=" * 50)
    print("测试音韵比较")
    print("=" * 50)
    
    comparisons = [("崇", "终"), ("海", "晦"), ("山", "产")]
    for char_a, char_b in comparisons:
        result = compare_phonology(char_a, char_b, data)
        print(f"\n【{char_a}】vs【{char_b}】")
        print(f"  音近: {result['音近']}")
        print(f"  韵部相同: {result['韵部相同']}")
        print(f"  声母相近: {result['声母相近']}")

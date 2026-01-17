"""
《汉语大词典》索引构建器

负责人：成员E（数据工程）

解决1.9GB大文件的快速查询问题：
1. 构建字→文件偏移量索引
2. 支持按需加载单个字的条目
3. 可选：构建SQLite数据库
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time


@dataclass
class IndexEntry:
    """索引条目"""
    char: str
    offset: int  # 文件偏移量
    length: int  # 行长度
    headword: str  # 完整词头


class DYHDCIndexBuilder:
    """
    汉语大词典索引构建器
    
    使用方法：
        builder = DYHDCIndexBuilder("path/to/dyhdc.jsonl")
        builder.build_index("path/to/index.json")
    """
    
    def __init__(self, jsonl_path: str):
        self.jsonl_path = Path(jsonl_path)
        self.index: Dict[str, List[Dict]] = {}  # 字 -> [偏移量列表]
    
    def build_index(self, output_path: str = None) -> Dict:
        """
        构建偏移量索引
        
        遍历JSONL文件，记录每个字的文件偏移位置
        """
        if not self.jsonl_path.exists():
            print(f"错误: 文件不存在: {self.jsonl_path}")
            return {}
        
        print(f"正在构建索引: {self.jsonl_path}")
        print(f"文件大小: {self.jsonl_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        start_time = time.time()
        count = 0
        offset = 0
        
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                
                line_length = len(line.encode('utf-8'))
                
                try:
                    entry = json.loads(line.strip())
                    headword = entry.get("headword", "") or entry.get("hw", "")
                    
                    # 跳过元信息行
                    if headword and not headword.startswith('#'):
                        # 提取第一个字作为索引键
                        first_char = headword[0]
                        
                        if first_char not in self.index:
                            self.index[first_char] = []
                        
                        self.index[first_char].append({
                            "headword": headword,
                            "offset": offset,
                            "length": line_length
                        })
                        
                        count += 1
                        
                        if count % 50000 == 0:
                            elapsed = time.time() - start_time
                            print(f"  已处理 {count} 条... ({elapsed:.1f}s)")
                
                except json.JSONDecodeError:
                    pass
                
                offset += line_length
        
        elapsed = time.time() - start_time
        print(f"索引构建完成: {count} 条词条, {len(self.index)} 个首字")
        print(f"耗时: {elapsed:.1f}s")
        
        # 保存索引
        if output_path:
            self._save_index(output_path)
        
        return self.index
    
    def _save_index(self, output_path: str):
        """保存索引到JSON文件"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        stats = {
            "source": str(self.jsonl_path),
            "total_chars": len(self.index),
            "total_entries": sum(len(v) for v in self.index.values()),
            "build_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        output_data = {
            "stats": stats,
            "index": self.index
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False)
        
        file_size = path.stat().st_size / 1024 / 1024
        print(f"索引已保存到: {path} ({file_size:.1f} MB)")
    
    def build_sqlite_db(self, db_path: str):
        """
        构建SQLite数据库（可选）
        
        适用于需要更复杂查询的场景
        """
        if not self.jsonl_path.exists():
            print(f"错误: 文件不存在: {self.jsonl_path}")
            return
        
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 删除已有数据库
        if path.exists():
            path.unlink()
        
        print(f"正在构建SQLite数据库: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headword TEXT NOT NULL,
                first_char TEXT NOT NULL,
                simplified TEXT,
                pronunciation TEXT,
                primary_meaning TEXT,
                senses_json TEXT,
                raw_json TEXT
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_headword ON entries(headword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_first_char ON entries(first_char)')
        
        start_time = time.time()
        count = 0
        batch = []
        batch_size = 1000
        
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    headword = entry.get("headword", "") or entry.get("hw", "")
                    
                    if not headword or headword.startswith('#'):
                        continue
                    
                    first_char = headword[0]
                    simplified = entry.get("simp", "")
                    pronunciation = entry.get("pron", "")
                    
                    # 提取第一个义项作为主要释义
                    senses = entry.get("senses", [])
                    primary_meaning = ""
                    if senses:
                        primary_meaning = senses[0].get("mean", "")[:500]  # 限制长度
                    
                    senses_json = json.dumps(senses, ensure_ascii=False)
                    raw_json = line.strip()
                    
                    batch.append((
                        headword,
                        first_char,
                        simplified,
                        pronunciation,
                        primary_meaning,
                        senses_json,
                        raw_json
                    ))
                    
                    count += 1
                    
                    if len(batch) >= batch_size:
                        cursor.executemany('''
                            INSERT INTO entries 
                            (headword, first_char, simplified, pronunciation, primary_meaning, senses_json, raw_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', batch)
                        conn.commit()
                        batch = []
                        
                        if count % 50000 == 0:
                            elapsed = time.time() - start_time
                            print(f"  已处理 {count} 条... ({elapsed:.1f}s)")
                
                except json.JSONDecodeError:
                    continue
        
        # 插入剩余数据
        if batch:
            cursor.executemany('''
                INSERT INTO entries 
                (headword, first_char, simplified, pronunciation, primary_meaning, senses_json, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conn.commit()
        
        conn.close()
        
        elapsed = time.time() - start_time
        db_size = path.stat().st_size / 1024 / 1024
        print(f"数据库构建完成: {count} 条")
        print(f"耗时: {elapsed:.1f}s, 大小: {db_size:.1f} MB")


class DYHDCIndexLoader:
    """
    汉语大词典索引加载器
    
    使用预构建的索引快速查询
    """
    
    def __init__(self, jsonl_path: str, index_path: str = None):
        self.jsonl_path = Path(jsonl_path)
        self.index_path = Path(index_path) if index_path else None
        self.index: Dict[str, List[Dict]] = {}
        self._loaded = False
    
    def load_index(self) -> bool:
        """加载索引"""
        if self._loaded:
            return True
        
        if self.index_path and self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.index = data.get("index", {})
                self._loaded = True
                print(f"已加载索引: {len(self.index)} 个首字")
                return True
        
        return False
    
    def query(self, char: str) -> List[Dict]:
        """
        查询单个汉字的词条
        
        Args:
            char: 要查询的汉字
        
        Returns:
            该字开头的所有词条列表
        """
        if not self._loaded:
            self.load_index()
        
        if char not in self.index:
            return []
        
        results = []
        entries_info = self.index[char]
        
        # 使用二进制模式读取，因为offset是字节偏移
        with open(self.jsonl_path, 'rb') as f:
            for info in entries_info:
                # 跳过复合词，只返回单字
                if len(info["headword"]) == 1:
                    f.seek(info["offset"])
                    line_bytes = f.read(info["length"])
                    try:
                        line = line_bytes.decode('utf-8')
                        entry = json.loads(line.strip())
                        results.append(entry)
                    except:
                        pass
        
        return results
    
    def query_single_char(self, char: str) -> Optional[Dict]:
        """
        查询单个字的详细信息
        
        Args:
            char: 单个汉字
        
        Returns:
            格式化后的字典条目
        """
        entries = self.query(char)
        
        if not entries:
            return None
        
        # 找到最匹配的条目
        for entry in entries:
            headword = entry.get("headword", "") or entry.get("hw", "")
            if headword == char:
                return self._format_entry(entry)
        
        # 如果没有精确匹配，返回第一个
        return self._format_entry(entries[0])
    
    def _format_entry(self, entry: Dict) -> Dict:
        """格式化词条"""
        headword = entry.get("headword", "") or entry.get("hw", "")
        simplified = entry.get("simp", "")
        pronunciation = entry.get("pron", "")
        
        senses = entry.get("senses", [])
        meanings = []
        examples = []
        jiajie_notes = []
        
        for sense in senses:
            mean = sense.get("mean", "")
            if mean:
                meanings.append(mean)
                
                # 检查假借标注
                if any(kw in mean for kw in ["读为", "读曰", "通", "假借", "读如"]):
                    jiajie_notes.append(mean)
            
            # 提取例句
            for ex in sense.get("examples", []):
                text = ex.get("text", "")
                if text:
                    examples.append(text[:200])  # 限制长度
        
        return {
            "字": headword,
            "简体": simplified,
            "读音": pronunciation,
            "本义": meanings[0] if meanings else "",
            "义项": meanings[:10],  # 限制数量
            "例句": examples[:5],
            "假借标注": jiajie_notes,
        }


class DYHDCSQLiteLoader:
    """
    使用SQLite数据库查询
    """
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        if not self.db_path.exists():
            print(f"数据库不存在: {self.db_path}")
            return False
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return True
    
    def query(self, char: str) -> Optional[Dict]:
        """查询单个字"""
        if not self.conn:
            if not self.connect():
                return None
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM entries 
            WHERE headword = ? OR first_char = ?
            LIMIT 1
        ''', (char, char))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "字": row["headword"],
            "简体": row["simplified"],
            "读音": row["pronunciation"],
            "本义": row["primary_meaning"],
            "义项": json.loads(row["senses_json"]) if row["senses_json"] else [],
        }
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# ===== 便捷函数 =====

def build_dyhdc_index(
    jsonl_path: str = None,
    output_path: str = None,
    build_sqlite: bool = False
) -> Dict:
    """
    构建《汉语大词典》索引
    
    Args:
        jsonl_path: JSONL文件路径
        output_path: 索引输出路径
        build_sqlite: 是否同时构建SQLite数据库
    """
    project_root = Path(__file__).parent.parent.parent
    
    if jsonl_path is None:
        jsonl_path = project_root / "《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl"
    
    if output_path is None:
        output_path = project_root / "data/processed/dyhdc_index.json"
    
    builder = DYHDCIndexBuilder(str(jsonl_path))
    index = builder.build_index(str(output_path))
    
    if build_sqlite:
        db_path = project_root / "data/processed/dyhdc.db"
        builder.build_sqlite_db(str(db_path))
    
    return index


# ===== 测试代码 =====

if __name__ == "__main__":
    import sys
    
    project_root = Path(__file__).parent.parent.parent
    jsonl_path = project_root / "《汉语大词典》结构化/dyhdc.parsed.fixed.v2.jsonl"
    index_path = project_root / "data/processed/dyhdc_index.json"
    
    # 检查是否需要构建索引
    if not index_path.exists():
        print("索引不存在，开始构建...")
        build_dyhdc_index()
    else:
        print(f"索引已存在: {index_path}")
    
    # 测试查询
    print("\n" + "=" * 50)
    print("测试词典查询")
    print("=" * 50)
    
    loader = DYHDCIndexLoader(str(jsonl_path), str(index_path))
    
    test_chars = ["崇", "终", "海", "晦", "山", "产"]
    for char in test_chars:
        result = loader.query_single_char(char)
        if result:
            print(f"\n【{char}】")
            print(f"  本义: {result['本义'][:50]}..." if len(result['本义']) > 50 else f"  本义: {result['本义']}")
            if result['假借标注']:
                print(f"  假借标注: {result['假借标注']}")
        else:
            print(f"\n【{char}】未找到")

"""
工具函数测试

运行方法：
    pytest tests/test_tools.py -v
"""
import pytest
from src.tools import (
    query_word_meaning,
    query_phonology,
    search_textual_evidence,
    identify_pattern,
    analyze_context,
)
from src.tools.phonology_tool import check_phonetic_relation


class TestSemanticTool:
    """测试语义查询工具"""
    
    def test_query_word_meaning(self):
        result = query_word_meaning("崇")
        assert result["字"] == "崇"
        assert "本义" in result
        assert "义项" in result
    
    def test_unknown_char(self):
        result = query_word_meaning("龘")  # 生僻字
        assert result["字"] == "龘"


class TestPhonologyTool:
    """测试音韵查询工具"""
    
    def test_query_phonology(self):
        result = query_phonology("崇")
        assert result["字"] == "崇"
        assert "声母" in result
        assert "韵部" in result
    
    def test_phonetic_relation(self):
        result = check_phonetic_relation("崇", "终")
        assert "is_close" in result
        assert "same_yunbu" in result


class TestPatternTool:
    """测试训式识别工具"""
    
    def test_identify_jiajie_pattern(self):
        result = identify_pattern("崇，读为终")
        assert result["格式"] == "读为"
        assert result["暗示类型"] == "假借"
        assert result["可直接判定"] == True
    
    def test_identify_basic_pattern(self):
        result = identify_pattern("崇，终也")
        assert result["被释字"] == "崇"
        assert result["释字"] == "终"
    
    def test_identify_semantic_pattern(self):
        result = identify_pattern("夭夭，盛貌")
        assert result["暗示类型"] == "语义解释"


class TestTextualTool:
    """测试文献检索工具"""
    
    def test_search_evidence(self):
        result = search_textual_evidence("崇", "终")
        assert "有佐证" in result
        assert "异文" in result


class TestContextTool:
    """测试语境分析工具"""
    
    def test_analyze_context(self):
        result = analyze_context(
            "崇朝其雨",
            "崇", "终",
            "高大", "终结"
        )
        assert "结论" in result
        assert result["结论"] in ["支持假借", "支持语义", "不确定"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

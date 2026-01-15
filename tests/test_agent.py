"""
Agent测试

运行方法：
    pytest tests/test_agent.py -v
"""
import pytest
from src.agent import XunguAgent


class TestXunguAgent:
    """测试训诂分类Agent"""
    
    @pytest.fixture
    def agent(self):
        return XunguAgent(verbose=False)
    
    def test_analyze_jiajie(self, agent):
        """测试假借案例"""
        result = agent.analyze(
            "崇，终也",
            context="崇朝其雨",
            source="《毛传》"
        )
        assert result.classification == "假借说明"
        assert result.confidence > 0.5
    
    def test_analyze_semantic(self, agent):
        """测试语义解释案例"""
        result = agent.analyze(
            "海，晦也",
            context="海，晦也，主承秽浊，其色黑而晦也",
            source="《释名》"
        )
        # 这个案例可能被判为语义解释或假借
        assert result.classification in ["语义解释", "假借说明"]
    
    def test_analyze_with_pattern(self, agent):
        """测试带明确训式的案例"""
        result = agent.analyze(
            "正，读为征",
            context="正其货贿"
        )
        assert result.classification == "假借说明"
        assert result.step4_pattern["格式"] == "读为"
    
    def test_result_structure(self, agent):
        """测试返回结果的结构"""
        result = agent.analyze("崇，终也")
        
        # 检查基本字段
        assert hasattr(result, "classification")
        assert hasattr(result, "confidence")
        assert hasattr(result, "step1_semantic")
        assert hasattr(result, "step2_phonetic")
        assert hasattr(result, "step3_textual")
        assert hasattr(result, "step4_pattern")
        assert hasattr(result, "step5_context")
    
    def test_to_dict(self, agent):
        """测试转换为字典"""
        result = agent.analyze("崇，终也")
        d = result.to_dict()
        
        assert "classification" in d
        assert "confidence" in d
        assert "reasoning" in d
    
    def test_to_json(self, agent):
        """测试转换为JSON"""
        result = agent.analyze("崇，终也")
        j = result.to_json()
        
        import json
        parsed = json.loads(j)
        assert "classification" in parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

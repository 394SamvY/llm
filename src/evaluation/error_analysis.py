"""
错误分析模块

负责人：成员E（数据工程）

功能：
1. 分析错误案例的模式
2. 识别哪一步推理出错
3. 区分数据问题和推理问题
4. 生成错误分析报告
"""
import json
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ErrorCase:
    """错误案例"""
    id: int
    xungu_sentence: str
    beishi_char: str
    shi_char: str
    context: Optional[str]
    source: str
    predicted: str
    expected: str
    reasoning: str
    step_results: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ErrorPattern:
    """错误模式"""
    pattern_type: str
    description: str
    cases: List[ErrorCase]
    frequency: int
    suggestions: List[str]


class ErrorAnalyzer:
    """
    错误分析器
    
    分析Agent推理过程中的错误，找出错误模式和改进建议
    """
    
    def __init__(self):
        self.errors: List[ErrorCase] = []
        self.patterns: List[ErrorPattern] = []
    
    def add_errors(self, errors: List[Dict[str, Any]]) -> None:
        """添加错误案例"""
        for err in errors:
            case = ErrorCase(
                id=err.get("id", 0),
                xungu_sentence=err.get("训诂句", ""),
                beishi_char=err.get("被释字", ""),
                shi_char=err.get("释字", ""),
                context=err.get("上下文"),
                source=err.get("出处", ""),
                predicted=err.get("预测", ""),
                expected=err.get("正确", ""),
                reasoning=err.get("推理", ""),
                step_results=err.get("五步分析", {})
            )
            self.errors.append(case)
    
    def analyze_all(self) -> Dict[str, Any]:
        """执行全面错误分析"""
        if not self.errors:
            return {"message": "没有错误案例需要分析"}
        
        analysis = {
            "total_errors": len(self.errors),
            "error_type_distribution": self._analyze_error_types(),
            "step_error_analysis": self._analyze_step_errors(),
            "pattern_analysis": self._identify_patterns(),
            "source_analysis": self._analyze_by_source(),
            "context_analysis": self._analyze_context_impact(),
            "suggestions": self._generate_suggestions()
        }
        
        return analysis
    
    def _analyze_error_types(self) -> Dict[str, Any]:
        """分析错误类型分布"""
        # 假借误判为语义 vs 语义误判为假借
        jiajie_to_yuyi = sum(1 for e in self.errors 
                            if e.expected == "假借说明" and e.predicted == "语义解释")
        yuyi_to_jiajie = sum(1 for e in self.errors
                            if e.expected == "语义解释" and e.predicted == "假借说明")
        
        return {
            "假借误判为语义": jiajie_to_yuyi,
            "语义误判为假借": yuyi_to_jiajie,
            "比例": {
                "假借误判率": jiajie_to_yuyi / len(self.errors) if self.errors else 0,
                "语义误判率": yuyi_to_jiajie / len(self.errors) if self.errors else 0
            }
        }
    
    def _analyze_step_errors(self) -> Dict[str, Any]:
        """分析各步骤的错误贡献"""
        step_issues = defaultdict(int)
        step_contributions = defaultdict(list)
        
        for err in self.errors:
            steps = err.step_results
            if not steps:
                continue
            
            # 分析每一步的问题
            # Step 1: 语义分析
            if "语义" in steps:
                semantic = steps["语义"]
                if err.expected == "假借说明":
                    # 假借案例，语义应该是"义远"
                    if semantic.get("relation") == "义近":
                        step_issues["step1_语义误判"] += 1
                        step_contributions["step1"].append(err.id)
            
            # Step 2: 音韵分析
            if "音韵" in steps:
                phonetic = steps["音韵"]
                # 无论假借还是语义，很多情况下应该是音近
                if phonetic.get("relation") == "音远":
                    step_issues["step2_音韵数据缺失或误判"] += 1
                    step_contributions["step2"].append(err.id)
            
            # Step 4: 术语分析
            if "术语" in steps:
                pattern = steps["术语"]
                if pattern.get("direct_judge"):
                    # 如果术语直接判断但结果错误
                    step_issues["step4_术语判断失误"] += 1
                    step_contributions["step4"].append(err.id)
            
            # Step 5: 语境分析
            if "语境" in steps:
                context = steps["语境"]
                if err.context and context.get("conclusion") != "不确定":
                    # 有语境但结论与预期不符
                    if err.expected == "假借说明" and context.get("conclusion") != "支持假借":
                        step_issues["step5_语境分析失误"] += 1
                        step_contributions["step5"].append(err.id)
                    elif err.expected == "语义解释" and context.get("conclusion") != "支持语义":
                        step_issues["step5_语境分析失误"] += 1
                        step_contributions["step5"].append(err.id)
        
        return {
            "step_issues": dict(step_issues),
            "step_contributions": {k: len(v) for k, v in step_contributions.items()},
            "most_problematic_step": max(step_contributions.keys(), 
                                         key=lambda k: len(step_contributions[k])) if step_contributions else None
        }
    
    def _identify_patterns(self) -> List[Dict[str, Any]]:
        """识别常见错误模式"""
        patterns = []
        
        # 模式1: 术语导向错误 - "读为/读曰"等术语没有被正确识别
        pattern1_cases = []
        for err in self.errors:
            if err.expected == "假借说明":
                keywords = ["读为", "读曰", "读如", "通"]
                if any(kw in err.xungu_sentence for kw in keywords):
                    pattern1_cases.append(err)
        
        if pattern1_cases:
            patterns.append({
                "pattern_type": "假借术语未识别",
                "description": "训诂句中包含'读为/读曰/读如/通'等假借专用术语，但未被正确判断为假借",
                "frequency": len(pattern1_cases),
                "case_ids": [e.id for e in pattern1_cases],
                "suggestions": [
                    "加强Pattern Tool对假借术语的识别规则",
                    "提高假借术语的判断权重"
                ]
            })
        
        # 模式2: 语义相近误判 - 被释字和释字语义接近但实际是假借
        pattern2_cases = []
        for err in self.errors:
            if err.expected == "假借说明" and err.predicted == "语义解释":
                # 这些案例可能是语义看起来相近但实际是假借
                pattern2_cases.append(err)
        
        if pattern2_cases:
            patterns.append({
                "pattern_type": "语义相近假借误判",
                "description": "被释字与释字表面语义相近，但实际是假借关系，被误判为语义解释",
                "frequency": len(pattern2_cases),
                "case_ids": [e.id for e in pattern2_cases],
                "suggestions": [
                    "需要更深入的语义分析，区分'表面语义'和'本义'",
                    "增加异文佐证的权重"
                ]
            })
        
        # 模式3: 音韵数据缺失
        pattern3_cases = []
        for err in self.errors:
            steps = err.step_results
            if "音韵" in steps:
                phonetic = steps["音韵"]
                if not phonetic.get("found_a") or not phonetic.get("found_b"):
                    pattern3_cases.append(err)
        
        if pattern3_cases:
            patterns.append({
                "pattern_type": "音韵数据缺失",
                "description": "被释字或释字的音韵数据缺失，导致音韵判断不准确",
                "frequency": len(pattern3_cases),
                "case_ids": [e.id for e in pattern3_cases],
                "suggestions": [
                    "扩充音韵数据库",
                    "对于缺失数据的字，使用相近字的音韵特征"
                ]
            })
        
        # 模式4: 无语境依赖
        pattern4_cases = []
        for err in self.errors:
            if not err.context:
                pattern4_cases.append(err)
        
        if pattern4_cases:
            patterns.append({
                "pattern_type": "缺少语境信息",
                "description": "测试案例缺少上下文语境，影响判断准确性",
                "frequency": len(pattern4_cases),
                "case_ids": [e.id for e in pattern4_cases],
                "suggestions": [
                    "补充测试案例的语境信息",
                    "对于无语境案例，增加其他步骤的判断权重"
                ]
            })
        
        self.patterns = patterns
        return patterns
    
    def _analyze_by_source(self) -> Dict[str, Any]:
        """按来源分析错误"""
        source_errors = defaultdict(list)
        for err in self.errors:
            # 提取主要来源
            source = err.source
            if '》' in source:
                source = source.split('》')[0] + '》'
            source_errors[source].append(err.id)
        
        return {
            "source_distribution": {k: len(v) for k, v in source_errors.items()},
            "most_error_source": max(source_errors.keys(), 
                                     key=lambda k: len(source_errors[k])) if source_errors else None
        }
    
    def _analyze_context_impact(self) -> Dict[str, Any]:
        """分析语境对准确率的影响"""
        with_context = [e for e in self.errors if e.context]
        without_context = [e for e in self.errors if not e.context]
        
        return {
            "有语境错误数": len(with_context),
            "无语境错误数": len(without_context),
            "有语境错误ID": [e.id for e in with_context],
            "无语境错误ID": [e.id for e in without_context]
        }
    
    def _generate_suggestions(self) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        error_types = self._analyze_error_types()
        
        if error_types["假借误判为语义"] > error_types["语义误判为假借"]:
            suggestions.append("建议1: 加强假借类型的识别能力，特别关注以下特征：")
            suggestions.append("  - '读为/读曰/读如'等专用术语")
            suggestions.append("  - 义远但音近的字对")
            suggestions.append("  - 有异文佐证的案例")
        else:
            suggestions.append("建议1: 加强语义解释类型的识别能力，特别关注：")
            suggestions.append("  - 双声叠韵且义近的字对")
            suggestions.append("  - '之为言'等语源训释术语")
        
        # 根据步骤分析
        step_analysis = self._analyze_step_errors()
        problematic_step = step_analysis.get("most_problematic_step")
        if problematic_step:
            step_names = {
                "step1": "语义分析",
                "step2": "音韵分析", 
                "step3": "异文佐证",
                "step4": "术语识别",
                "step5": "语境分析"
            }
            suggestions.append(f"建议2: 重点优化{step_names.get(problematic_step, problematic_step)}模块")
        
        # 数据建议
        suggestions.append("建议3: 数据层面改进：")
        suggestions.append("  - 扩充音韵数据库的覆盖范围")
        suggestions.append("  - 增加词典中假借标注的提取")
        suggestions.append("  - 补充测试案例的语境信息")
        
        return suggestions
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整的错误分析报告"""
        analysis = self.analyze_all()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_errors": len(self.errors),
                "error_types": analysis["error_type_distribution"]
            },
            "detailed_analysis": {
                "step_errors": analysis["step_error_analysis"],
                "patterns": analysis["pattern_analysis"],
                "source_analysis": analysis["source_analysis"],
                "context_impact": analysis["context_analysis"]
            },
            "suggestions": analysis["suggestions"],
            "error_cases": [
                {
                    "id": e.id,
                    "训诂句": e.xungu_sentence,
                    "被释字": e.beishi_char,
                    "释字": e.shi_char,
                    "预测": e.predicted,
                    "正确": e.expected,
                    "推理": e.reasoning
                }
                for e in self.errors
            ]
        }
        
        return report
    
    def print_report(self) -> None:
        """打印错误分析报告"""
        analysis = self.analyze_all()
        
        print("\n" + "=" * 70)
        print("错误分析报告")
        print("=" * 70)
        
        print(f"\n📊 错误概览")
        print(f"  总错误数: {len(self.errors)}")
        
        error_types = analysis["error_type_distribution"]
        print(f"\n📋 错误类型分布")
        print(f"  假借误判为语义: {error_types['假借误判为语义']}")
        print(f"  语义误判为假借: {error_types['语义误判为假借']}")
        
        step_analysis = analysis["step_error_analysis"]
        print(f"\n🔍 步骤错误分析")
        for step, count in step_analysis.get("step_issues", {}).items():
            print(f"  {step}: {count}")
        if step_analysis.get("most_problematic_step"):
            print(f"  最需改进的步骤: {step_analysis['most_problematic_step']}")
        
        print(f"\n📝 错误模式")
        for pattern in analysis.get("pattern_analysis", []):
            print(f"\n  [{pattern['pattern_type']}] (出现{pattern['frequency']}次)")
            print(f"    描述: {pattern['description']}")
            print(f"    建议: {', '.join(pattern['suggestions'][:2])}")
        
        print(f"\n💡 改进建议")
        for suggestion in analysis.get("suggestions", []):
            print(f"  {suggestion}")
        
        print("\n" + "=" * 70)


def save_error_report(report: Dict[str, Any], filepath: str) -> None:
    """保存错误分析报告"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"错误分析报告已保存到: {filepath}")


# ===== 测试代码 =====

if __name__ == "__main__":
    # 模拟一些错误案例
    mock_errors = [
        {
            "id": 1,
            "训诂句": "崇，终也",
            "被释字": "崇",
            "释字": "终",
            "上下文": "崇朝其雨",
            "出处": "《诗·邶风·简兮》《毛传》",
            "预测": "语义解释",
            "正确": "假借说明",
            "推理": "崇与终语义相关，故判断为语义解释",
            "五步分析": {
                "语义": {"relation": "义近"},
                "音韵": {"relation": "音近", "found_a": True, "found_b": True},
                "术语": {"direct_judge": False},
                "语境": {"conclusion": "不确定"}
            }
        },
        {
            "id": 2,
            "训诂句": "正，读为征",
            "被释字": "正",
            "释字": "征",
            "上下文": "正其货贿",
            "出处": "《周礼·地官·司门》郑玄注",
            "预测": "语义解释",
            "正确": "假借说明",
            "推理": "正与征存在语义关联",
            "五步分析": {
                "语义": {"relation": "义近"},
                "音韵": {"relation": "音近", "found_a": True, "found_b": True},
                "术语": {"direct_judge": True, "pattern": "读为"},
                "语境": {"conclusion": "支持假借"}
            }
        },
        {
            "id": 3,
            "训诂句": "政，正也",
            "被释字": "政",
            "释字": "正",
            "上下文": None,
            "出处": "《广雅·释诂》",
            "预测": "假借说明",
            "正确": "语义解释",
            "推理": "政与正同音，可能是假借",
            "五步分析": {
                "语义": {"relation": "义近"},
                "音韵": {"relation": "音近", "found_a": True, "found_b": True},
                "术语": {"direct_judge": False},
                "语境": {"conclusion": "不确定"}
            }
        }
    ]
    
    # 创建分析器
    analyzer = ErrorAnalyzer()
    analyzer.add_errors(mock_errors)
    
    # 打印报告
    analyzer.print_report()
    
    # 生成并保存报告
    report = analyzer.generate_report()
    
    # 保存示例
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data/processed/error_analysis_sample.json"
    save_error_report(report, str(output_path))

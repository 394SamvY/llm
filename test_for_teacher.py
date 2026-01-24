#!/usr/bin/env python3
"""
训诂句类型智能判断系统 - 教师测试脚本

使用方法：
方式1：使用外部JSON文件（推荐）
    python test_for_teacher.py my_test.json

方式2：使用内置示例
    python test_for_teacher.py

JSON文件格式示例：
[
    {"训诂句": "崇，终也", "上下文": "崇朝其雨", "出处": "《毛传》"},
    {"训诂句": "海，晦也", "上下文": null, "出处": "《释名》"}
]
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from src.agent import XunguAgent


# 内置示例（无参数时使用）
DEFAULT_CASES = [
    {"训诂句": "崇，终也", "上下文": "崇朝其雨", "出处": "《毛传》"},
    {"训诂句": "海，晦也", "上下文": "海，晦也，主承秽浊，其色黑而晦也", "出处": "《释名》"},
    {"训诂句": "正，读为征", "上下文": "正其货贿", "出处": "《周礼》郑注"},
]


def load_test_cases(filepath: str = None):
    """加载测试用例"""
    if filepath:
        path = Path(filepath)
        if not path.exists():
            print(f"错误: 文件不存在 - {filepath}")
            sys.exit(1)
        
        with open(path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        print(f"已加载外部测试集: {filepath} ({len(cases)} 条)")
        return cases
    else:
        print(f"使用内置示例数据 ({len(DEFAULT_CASES)} 条)")
        return DEFAULT_CASES


def run_test(cases):
    print("=" * 70)
    print("训诂句类型智能判断系统 - 教师测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试数量: {len(cases)} 条")
    print("=" * 70)
    
    agent = XunguAgent(verbose=False)
    results = []
    
    for i, case in enumerate(cases, 1):
        xungu = case["训诂句"]
        context = case.get("上下文")
        source = case.get("出处")
        
        print(f"\n[{i}/{len(cases)}] 分析: {xungu}")
        if context:
            print(f"    上下文: {context[:30]}..." if len(str(context)) > 30 else f"    上下文: {context}")
        if source:
            print(f"    出处: {source}")
        
        try:
            result = agent.analyze(xungu, context, source)
            
            print(f"    ✓ 分类: {result.classification}")
            print(f"    ✓ 置信度: {result.confidence:.0%}")
            print(f"    ✓ 理由: {result.final_reasoning[:50]}..." if len(result.final_reasoning) > 50 else f"    ✓ 理由: {result.final_reasoning}")
            
            results.append({
                "训诂句": xungu,
                "上下文": context,
                "出处": source,
                "分类结果": result.classification,
                "置信度": result.confidence,
                "推理过程": result.to_dict()["reasoning"],
                "综合判断": result.final_reasoning,
            })
        except Exception as e:
            print(f"    ✗ 错误: {str(e)[:50]}")
            results.append({
                "训诂句": xungu,
                "错误": str(e),
            })
    
    # 保存结果
    output_file = f"teacher_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(f"测试完成！结果已保存到: {output_file}")
    print("=" * 70)
    
    # 打印汇总
    print("\n结果汇总:")
    print("-" * 70)
    for r in results:
        if "错误" in r:
            print(f"  {r['训诂句']}: ✗ 错误")
        else:
            print(f"  {r['训诂句']}: {r['分类结果']} (置信度 {r['置信度']:.0%})")
    print("-" * 70)


def print_usage():
    print("""
训诂句类型智能判断系统 - 教师测试脚本

用法:
    python test_for_teacher.py [测试文件.json]

参数:
    测试文件.json    可选，包含测试用例的JSON文件
                    如果不提供，将使用内置的3条示例

JSON文件格式:
    [
        {
            "训诂句": "崇，终也",
            "上下文": "崇朝其雨",   (可选，可为null)
            "出处": "《毛传》"      (可选，可为null)
        },
        ...
    ]

示例:
    python test_for_teacher.py                    # 使用内置示例
    python test_for_teacher.py my_test.json       # 使用自定义测试集
    python test_for_teacher.py --help             # 显示帮助
""")


if __name__ == "__main__":
    # 处理帮助参数
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)
    
    # 加载测试用例
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    cases = load_test_cases(filepath)
    
    # 运行测试
    run_test(cases)

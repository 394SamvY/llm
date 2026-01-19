#!/usr/bin/env python3
"""
训诂句类型智能判断系统 - 教师测试脚本

使用方法：
1. 确保已配置 .env 文件（API Key）
2. 修改下方 TEST_CASES 列表，添加要测试的训诂句
3. 运行：python test_for_teacher.py
"""

# ==================== 在这里添加测试用例 ====================
TEST_CASES = [
    {
        "训诂句": "崇，终也",
        "上下文": "崇朝其雨",  # 可选，没有则填 None
        "出处": "《毛传》",     # 可选，没有则填 None
    },
    {
        "训诂句": "海，晦也",
        "上下文": "海，晦也，主承秽浊，其色黑而晦也",
        "出处": "《释名》",
    },
    {
        "训诂句": "正，读为征",
        "上下文": "正其货贿",
        "出处": "《周礼》郑注",
    },
    # 添加更多测试用例...
    # {
    #     "训诂句": "xxx，xxx也",
    #     "上下文": "原文上下文",
    #     "出处": "出处",
    # },
]
# ============================================================

import json
from datetime import datetime
from src.agent import XunguAgent


def run_test():
    print("=" * 70)
    print("训诂句类型智能判断系统 - 教师测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试数量: {len(TEST_CASES)} 条")
    print("=" * 70)
    
    agent = XunguAgent(verbose=False)
    results = []
    
    for i, case in enumerate(TEST_CASES, 1):
        xungu = case["训诂句"]
        context = case.get("上下文")
        source = case.get("出处")
        
        print(f"\n[{i}/{len(TEST_CASES)}] 分析: {xungu}")
        if context:
            print(f"    上下文: {context[:30]}...")
        if source:
            print(f"    出处: {source}")
        
        try:
            result = agent.analyze(xungu, context, source)
            
            print(f"    ✓ 分类: {result.classification}")
            print(f"    ✓ 置信度: {result.confidence:.0%}")
            print(f"    ✓ 理由: {result.final_reasoning[:50]}...")
            
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
    
    # 打印详细结果
    print("\n详细结果:")
    print("-" * 70)
    for r in results:
        if "错误" in r:
            print(f"  {r['训诂句']}: 错误 - {r['错误']}")
        else:
            print(f"  {r['训诂句']}: {r['分类结果']} (置信度 {r['置信度']:.0%})")
    print("-" * 70)


if __name__ == "__main__":
    run_test()

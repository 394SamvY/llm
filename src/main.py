"""
训诂句类型智能判断系统 - 主入口

使用方法：
    # 单条分析
    python -m src.main --input "崇，终也" --context "崇朝其雨"
    
    # 交互模式
    python -m src.main --interactive
    
    # 批量处理
    python -m src.main --batch data/test/test_dataset.json --output results.json
    
    # 运行评估
    python -m src.main --evaluate
"""
import argparse
import json
from typing import Optional

from .agent import XunguAgent
from .evaluation import load_test_dataset, evaluate_results, print_evaluation_report


def analyze_single(
    xungu_sentence: str,
    context: Optional[str] = None,
    source: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """分析单条训诂句"""
    agent = XunguAgent(verbose=verbose)
    result = agent.analyze(xungu_sentence, context, source)
    return result.to_dict()


def interactive_mode():
    """交互模式"""
    print("\n" + "=" * 60)
    print("训诂句类型智能判断系统")
    print("=" * 60)
    print("输入训诂句进行分析，输入 'quit' 退出\n")
    
    agent = XunguAgent(verbose=True)
    
    while True:
        try:
            xungu_sentence = input("请输入训诂句: ").strip()
            if xungu_sentence.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if not xungu_sentence:
                continue
            
            context = input("请输入上下文（可选，直接回车跳过）: ").strip() or None
            source = input("请输入出处（可选，直接回车跳过）: ").strip() or None
            
            result = agent.analyze(xungu_sentence, context, source)
            
            print("\n" + "-" * 40)
            print("分析结果:")
            print(f"  分类: {result.classification}")
            print(f"  置信度: {result.confidence:.0%}")
            print(f"  理由: {result.final_reasoning}")
            print("-" * 40 + "\n")
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


def batch_process(input_file: str, output_file: str):
    """批量处理"""
    print(f"从 {input_file} 加载数据...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    agent = XunguAgent(verbose=False)
    results = []
    
    for i, item in enumerate(data):
        print(f"处理 {i+1}/{len(data)}: {item.get('训诂句', '')[:20]}...")
        
        result = agent.analyze(
            item.get("训诂句", ""),
            item.get("上下文"),
            item.get("出处")
        )
        results.append(result.to_dict())
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到 {output_file}")


def run_evaluation():
    """运行评估"""
    print("加载测试数据集...")
    dataset = load_test_dataset()
    
    print(f"共 {len(dataset)} 条测试数据")
    
    agent = XunguAgent(verbose=False)
    results = []
    
    for i, case in enumerate(dataset):
        print(f"评估 {i+1}/{len(dataset)}: {case.xungu_sentence[:20]}...")
        
        result = agent.analyze(
            case.xungu_sentence,
            case.context,
            case.source
        )
        results.append(result.to_dict())
    
    # 计算指标
    report = evaluate_results(results, dataset)
    print_evaluation_report(report)
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="训诂句类型智能判断系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.main --input "崇，终也" --context "崇朝其雨"
  python -m src.main --interactive
  python -m src.main --evaluate
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="要分析的训诂句"
    )
    parser.add_argument(
        "--context", "-c",
        type=str,
        help="上下文/原句"
    )
    parser.add_argument(
        "--source", "-s",
        type=str,
        help="出处"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式"
    )
    parser.add_argument(
        "--batch", "-b",
        type=str,
        help="批量处理的输入文件"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="results.json",
        help="批量处理的输出文件"
    )
    parser.add_argument(
        "--evaluate", "-e",
        action="store_true",
        help="运行评估"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.batch:
        batch_process(args.batch, args.output)
    elif args.evaluate:
        run_evaluation()
    elif args.input:
        result = analyze_single(
            args.input,
            args.context,
            args.source,
            verbose=args.verbose
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 默认运行演示
        print("运行演示...")
        demo()


def demo():
    """演示函数"""
    print("\n" + "=" * 60)
    print("训诂句类型智能判断系统 - 演示")
    print("=" * 60)
    
    test_cases = [
        ("崇，终也", "崇朝其雨", "《毛传》"),
        ("海，晦也", "海，晦也，主承秽浊，其色黑而晦也", "《释名》"),
        ("正，读为征", "正其货贿", "《周礼》郑注"),
    ]
    
    agent = XunguAgent(verbose=True)
    
    for xungu, context, source in test_cases:
        print(f"\n{'='*60}")
        print(f"分析: {xungu}")
        print(f"{'='*60}")
        
        result = agent.analyze(xungu, context, source)
        
        print(f"\n最终结果:")
        print(f"  分类: {result.classification}")
        print(f"  置信度: {result.confidence:.0%}")
        print(f"  理由: {result.final_reasoning}")


if __name__ == "__main__":
    main()

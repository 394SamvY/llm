"""
评估指标计算

负责人：成员E
"""
from typing import List, Dict, Any, Tuple
from collections import Counter


def calculate_metrics(
    predictions: List[str],
    labels: List[str]
) -> Dict[str, float]:
    """
    计算分类指标
    
    Args:
        predictions: 预测标签列表
        labels: 真实标签列表
        
    Returns:
        dict: {
            "accuracy": 准确率,
            "precision_假借": 假借的精确率,
            "recall_假借": 假借的召回率,
            "f1_假借": 假借的F1,
            "precision_语义": 语义的精确率,
            "recall_语义": 语义的召回率,
            "f1_语义": 语义的F1,
            "macro_f1": 宏平均F1
        }
    """
    assert len(predictions) == len(labels), "预测和标签数量不一致"
    
    n = len(predictions)
    if n == 0:
        return {"accuracy": 0.0}
    
    # 准确率
    correct = sum(p == l for p, l in zip(predictions, labels))
    accuracy = correct / n
    
    # 分类别统计
    results = {}
    for label_type in ["假借说明", "语义解释"]:
        tp = sum(1 for p, l in zip(predictions, labels) if p == label_type and l == label_type)
        fp = sum(1 for p, l in zip(predictions, labels) if p == label_type and l != label_type)
        fn = sum(1 for p, l in zip(predictions, labels) if p != label_type and l == label_type)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        short_name = "假借" if "假借" in label_type else "语义"
        results[f"precision_{short_name}"] = precision
        results[f"recall_{short_name}"] = recall
        results[f"f1_{short_name}"] = f1
    
    # 宏平均F1
    macro_f1 = (results.get("f1_假借", 0) + results.get("f1_语义", 0)) / 2
    
    return {
        "accuracy": accuracy,
        **results,
        "macro_f1": macro_f1
    }


def evaluate_results(
    results: List[Dict[str, Any]],
    dataset
) -> Dict[str, Any]:
    """
    评估Agent的分析结果
    
    Args:
        results: Agent返回的结果列表
        dataset: 测试数据集
        
    Returns:
        dict: 评估报告
    """
    predictions = []
    labels = []
    errors = []
    
    for result, case in zip(results, dataset):
        pred = result.get("classification", "")
        label = case.expected_label
        
        predictions.append(pred)
        labels.append(label)
        
        if pred != label:
            errors.append({
                "id": case.id,
                "训诂句": case.xungu_sentence,
                "预测": pred,
                "正确": label,
                "推理": result.get("final_reasoning", "")
            })
    
    metrics = calculate_metrics(predictions, labels)
    
    return {
        "metrics": metrics,
        "total": len(predictions),
        "correct": sum(p == l for p, l in zip(predictions, labels)),
        "errors": errors
    }


def print_evaluation_report(report: Dict[str, Any]) -> None:
    """打印评估报告"""
    print("\n" + "=" * 60)
    print("评估报告")
    print("=" * 60)
    
    metrics = report["metrics"]
    print(f"\n总样本数: {report['total']}")
    print(f"正确数: {report['correct']}")
    print(f"准确率: {metrics['accuracy']:.2%}")
    
    print(f"\n假借说明:")
    print(f"  精确率: {metrics.get('precision_假借', 0):.2%}")
    print(f"  召回率: {metrics.get('recall_假借', 0):.2%}")
    print(f"  F1: {metrics.get('f1_假借', 0):.2%}")
    
    print(f"\n语义解释:")
    print(f"  精确率: {metrics.get('precision_语义', 0):.2%}")
    print(f"  召回率: {metrics.get('recall_语义', 0):.2%}")
    print(f"  F1: {metrics.get('f1_语义', 0):.2%}")
    
    print(f"\n宏平均F1: {metrics.get('macro_f1', 0):.2%}")
    
    if report["errors"]:
        print(f"\n错误案例 ({len(report['errors'])} 个):")
        print("-" * 60)
        for err in report["errors"][:5]:  # 只显示前5个
            print(f"[{err['id']}] {err['训诂句']}")
            print(f"    预测: {err['预测']}, 正确: {err['正确']}")
            print(f"    原因: {err['推理']}")
            print()


# ===== 测试代码 =====
if __name__ == "__main__":
    # 测试指标计算
    predictions = ["假借说明", "假借说明", "语义解释", "语义解释", "假借说明"]
    labels = ["假借说明", "语义解释", "语义解释", "语义解释", "假借说明"]
    
    metrics = calculate_metrics(predictions, labels)
    print("测试指标计算:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.2%}")

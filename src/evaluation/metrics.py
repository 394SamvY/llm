"""
评估指标计算

负责人：成员E（数据工程）

功能：
1. 计算准确率、精确率、召回率、F1值
2. 生成混淆矩阵
3. 错误分析报告
4. 支持从JSON文件加载测试集
"""
import json
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TestCase:
    """测试用例"""
    id: int
    xungu_sentence: str
    beishi_char: str
    shi_char: str
    context: Optional[str]
    source: str
    expected_label: str
    notes: str = ""


def load_test_dataset(filepath: str) -> List[TestCase]:
    """
    从JSON文件加载测试数据集
    
    Args:
        filepath: JSON文件路径
    
    Returns:
        TestCase列表
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cases = []
    for item in data:
        case = TestCase(
            id=item.get("id", 0),
            xungu_sentence=item.get("训诂句", ""),
            beishi_char=item.get("被释字", ""),
            shi_char=item.get("释字", ""),
            context=item.get("上下文"),
            source=item.get("出处", ""),
            expected_label=item.get("正确答案", ""),
            notes=item.get("备注", "")
        )
        cases.append(case)
    
    return cases


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
        results[f"tp_{short_name}"] = tp
        results[f"fp_{short_name}"] = fp
        results[f"fn_{short_name}"] = fn
    
    # 宏平均F1
    macro_f1 = (results.get("f1_假借", 0) + results.get("f1_语义", 0)) / 2
    
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": n,
        **results,
        "macro_f1": macro_f1
    }


def build_confusion_matrix(
    predictions: List[str],
    labels: List[str],
    label_names: List[str] = None
) -> Dict[str, Any]:
    """
    构建混淆矩阵
    
    Args:
        predictions: 预测标签列表
        labels: 真实标签列表
        label_names: 标签名称列表
    
    Returns:
        {
            "matrix": [[TP, FN], [FP, TN]],
            "labels": ["假借说明", "语义解释"],
            "normalized": [[...], [...]]  # 归一化后的矩阵
        }
    """
    if label_names is None:
        label_names = ["假借说明", "语义解释"]
    
    n_labels = len(label_names)
    matrix = [[0] * n_labels for _ in range(n_labels)]
    
    label_to_idx = {name: i for i, name in enumerate(label_names)}
    
    for pred, label in zip(predictions, labels):
        if pred in label_to_idx and label in label_to_idx:
            i = label_to_idx[label]  # 真实标签
            j = label_to_idx[pred]    # 预测标签
            matrix[i][j] += 1
    
    # 归一化
    normalized = []
    for row in matrix:
        row_sum = sum(row)
        if row_sum > 0:
            normalized.append([x / row_sum for x in row])
        else:
            normalized.append([0.0] * n_labels)
    
    return {
        "matrix": matrix,
        "labels": label_names,
        "normalized": normalized
    }


def print_confusion_matrix(cm: Dict[str, Any]) -> None:
    """打印混淆矩阵"""
    labels = cm["labels"]
    matrix = cm["matrix"]
    
    # 计算列宽
    max_label_len = max(len(l) for l in labels)
    col_width = max(max_label_len + 2, 8)
    
    print("\n混淆矩阵:")
    print("-" * (col_width * (len(labels) + 1) + 10))
    
    # 标题行
    header = " " * (max_label_len + 2) + "│"
    for label in labels:
        header += f" {label:^{col_width}} │"
    print(header)
    print("-" * (col_width * (len(labels) + 1) + 10))
    
    # 数据行
    for i, label in enumerate(labels):
        row = f" {label:<{max_label_len}} │"
        for j in range(len(labels)):
            row += f" {matrix[i][j]:^{col_width}} │"
        print(row)
    
    print("-" * (col_width * (len(labels) + 1) + 10))
    
    # 打印归一化矩阵
    print("\n归一化混淆矩阵 (按行):")
    normalized = cm["normalized"]
    for i, label in enumerate(labels):
        row = f" {label:<{max_label_len}} │"
        for j in range(len(labels)):
            row += f" {normalized[i][j]:^{col_width}.2%} │"
        print(row)


def evaluate_results(
    results: List[Dict[str, Any]],
    dataset: List[TestCase]
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
                "被释字": case.beishi_char,
                "释字": case.shi_char,
                "上下文": case.context,
                "出处": case.source,
                "预测": pred,
                "正确": label,
                "推理": result.get("final_reasoning", ""),
                "五步分析": {
                    "语义": result.get("step1", {}),
                    "音韵": result.get("step2", {}),
                    "异文": result.get("step3", {}),
                    "术语": result.get("step4", {}),
                    "语境": result.get("step5", {})
                }
            })
    
    metrics = calculate_metrics(predictions, labels)
    confusion = build_confusion_matrix(predictions, labels)
    
    return {
        "metrics": metrics,
        "confusion_matrix": confusion,
        "total": len(predictions),
        "correct": sum(p == l for p, l in zip(predictions, labels)),
        "predictions": predictions,
        "labels": labels,
        "errors": errors
    }


def print_evaluation_report(report: Dict[str, Any]) -> None:
    """打印评估报告"""
    print("\n" + "=" * 60)
    print("训诂分类评估报告")
    print("=" * 60)
    
    metrics = report["metrics"]
    print(f"\n📊 总体指标")
    print(f"  总样本数: {report['total']}")
    print(f"  正确数: {report['correct']}")
    print(f"  准确率: {metrics['accuracy']:.2%}")
    print(f"  宏平均F1: {metrics.get('macro_f1', 0):.2%}")
    
    print(f"\n📗 假借说明")
    print(f"  精确率: {metrics.get('precision_假借', 0):.2%}")
    print(f"  召回率: {metrics.get('recall_假借', 0):.2%}")
    print(f"  F1: {metrics.get('f1_假借', 0):.2%}")
    print(f"  TP/FP/FN: {metrics.get('tp_假借', 0)}/{metrics.get('fp_假借', 0)}/{metrics.get('fn_假借', 0)}")
    
    print(f"\n📘 语义解释")
    print(f"  精确率: {metrics.get('precision_语义', 0):.2%}")
    print(f"  召回率: {metrics.get('recall_语义', 0):.2%}")
    print(f"  F1: {metrics.get('f1_语义', 0):.2%}")
    print(f"  TP/FP/FN: {metrics.get('tp_语义', 0)}/{metrics.get('fp_语义', 0)}/{metrics.get('fn_语义', 0)}")
    
    # 混淆矩阵
    if "confusion_matrix" in report:
        print_confusion_matrix(report["confusion_matrix"])
    
    # 错误案例
    if report["errors"]:
        print(f"\n❌ 错误案例 ({len(report['errors'])} 个)")
        print("-" * 60)
        for err in report["errors"][:10]:  # 显示前10个
            print(f"\n[案例 {err['id']}] {err['训诂句']}")
            print(f"  被释字: {err['被释字']}, 释字: {err['释字']}")
            if err.get('上下文'):
                print(f"  上下文: {err['上下文']}")
            print(f"  出处: {err['出处']}")
            print(f"  预测: {err['预测']} ✗ → 正确: {err['正确']} ✓")
            if err.get('推理'):
                print(f"  推理: {err['推理'][:100]}...")


def save_evaluation_report(report: Dict[str, Any], filepath: str) -> None:
    """保存评估报告到JSON文件"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 移除不可序列化的部分
    output = {
        "metrics": report["metrics"],
        "confusion_matrix": report["confusion_matrix"],
        "total": report["total"],
        "correct": report["correct"],
        "error_count": len(report.get("errors", [])),
        "errors": report.get("errors", [])[:20]  # 只保存前20个错误
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n评估报告已保存到: {filepath}")


def get_dataset_statistics(dataset: List[TestCase]) -> Dict[str, Any]:
    """获取数据集统计信息"""
    label_counts = Counter(case.expected_label for case in dataset)
    source_counts = Counter(case.source.split('》')[0] + '》' if '》' in case.source else case.source for case in dataset)
    
    return {
        "total": len(dataset),
        "label_distribution": dict(label_counts),
        "source_distribution": dict(source_counts.most_common(10)),
        "with_context": sum(1 for case in dataset if case.context),
        "without_context": sum(1 for case in dataset if not case.context)
    }


def print_dataset_statistics(stats: Dict[str, Any]) -> None:
    """打印数据集统计信息"""
    print("\n" + "=" * 60)
    print("测试数据集统计")
    print("=" * 60)
    
    print(f"\n总样本数: {stats['total']}")
    print(f"\n标签分布:")
    for label, count in stats['label_distribution'].items():
        pct = count / stats['total'] * 100
        print(f"  {label}: {count} ({pct:.1f}%)")
    
    print(f"\n上下文情况:")
    print(f"  有上下文: {stats['with_context']}")
    print(f"  无上下文: {stats['without_context']}")
    
    print(f"\n主要来源 (前10):")
    for source, count in list(stats['source_distribution'].items())[:10]:
        print(f"  {source}: {count}")


# ===== 便捷函数 =====

def quick_evaluate(predictions: List[str], labels: List[str]) -> None:
    """快速评估并打印结果"""
    metrics = calculate_metrics(predictions, labels)
    cm = build_confusion_matrix(predictions, labels)
    
    print(f"准确率: {metrics['accuracy']:.2%}")
    print(f"宏平均F1: {metrics['macro_f1']:.2%}")
    print_confusion_matrix(cm)


# ===== 测试代码 =====

if __name__ == "__main__":
    # 测试数据集加载
    project_root = Path(__file__).parent.parent.parent
    test_file = project_root / "data/test/test_dataset.json"
    
    if test_file.exists():
        print("加载测试数据集...")
        dataset = load_test_dataset(str(test_file))
        stats = get_dataset_statistics(dataset)
        print_dataset_statistics(stats)
    
    # 测试指标计算
    print("\n" + "=" * 60)
    print("测试指标计算")
    print("=" * 60)
    
    predictions = ["假借说明", "假借说明", "语义解释", "语义解释", "假借说明", "语义解释"]
    labels = ["假借说明", "语义解释", "语义解释", "语义解释", "假借说明", "语义解释"]
    
    metrics = calculate_metrics(predictions, labels)
    print("\n指标结果:")
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.2%}")
        else:
            print(f"  {k}: {v}")
    
    # 测试混淆矩阵
    cm = build_confusion_matrix(predictions, labels)
    print_confusion_matrix(cm)

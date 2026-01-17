"""
评估模块 - 测试和评估系统性能

负责人：成员E（数据工程）

包含：
- 评估指标计算 (metrics)
- 测试数据集 (test_dataset)
- 错误分析 (error_analysis)
"""

from .metrics import (
    calculate_metrics,
    evaluate_results,
    print_evaluation_report,
    save_evaluation_report,
    load_test_dataset,
    get_dataset_statistics,
    print_dataset_statistics,
    build_confusion_matrix,
    print_confusion_matrix,
    quick_evaluate,
    TestCase,
)

from .test_dataset import TestDataset

from .error_analysis import (
    ErrorAnalyzer,
    ErrorCase,
    ErrorPattern,
    save_error_report,
)

__all__ = [
    # 评估指标
    "calculate_metrics",
    "evaluate_results",
    "print_evaluation_report",
    "save_evaluation_report",
    "build_confusion_matrix",
    "print_confusion_matrix",
    "quick_evaluate",
    # 测试数据集
    "TestDataset",
    "TestCase",
    "load_test_dataset",
    "get_dataset_statistics",
    "print_dataset_statistics",
    # 错误分析
    "ErrorAnalyzer",
    "ErrorCase",
    "ErrorPattern",
    "save_error_report",
]

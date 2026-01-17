"""
数据处理模块

负责人：成员E（数据工程）

包含：
- 音韵数据解析器 (phonology_parser)
- 《汉语大词典》索引构建器 (dyhdc_index_builder)
"""

from .phonology_parser import (
    parse_panwuyun_txt,
    parse_baxter_sagart_xlsx,
    unify_phonology_data,
    compare_phonology,
    build_phonology_index,
    load_phonology_data,
    save_phonology_data,
)

from .dyhdc_index_builder import (
    DYHDCIndexBuilder,
    DYHDCIndexLoader,
    DYHDCSQLiteLoader,
    build_dyhdc_index,
)

__all__ = [
    # 音韵解析
    "parse_panwuyun_txt",
    "parse_baxter_sagart_xlsx",
    "unify_phonology_data",
    "compare_phonology",
    "build_phonology_index",
    "load_phonology_data",
    "save_phonology_data",
    # 词典索引
    "DYHDCIndexBuilder",
    "DYHDCIndexLoader",
    "DYHDCSQLiteLoader",
    "build_dyhdc_index",
]

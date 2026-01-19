"""
全局配置管理
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# 尝试加载 .env 文件（override=True 强制覆盖系统环境变量）
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


@dataclass
class Settings:
    """项目配置"""
    
    # ===== 项目路径 =====
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    # ===== LLM 配置 =====
    llm_provider: str = "openai"  # openai 或 anthropic
    llm_model: str = "gpt-4-turbo"
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # ===== 数据路径 =====
    dyhdc_path: Optional[Path] = None  # 汉语大词典
    phonology_path: Optional[Path] = None  # 音韵数据
    
    # ===== 运行配置 =====
    debug: bool = False
    log_level: str = "INFO"
    
    def __post_init__(self):
        """从环境变量加载配置"""
        # LLM配置
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", self.openai_base_url)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", self.anthropic_api_key)
        self.llm_model = os.getenv("LLM_MODEL", self.llm_model)
        
        # 根据API Key自动选择provider
        if self.anthropic_api_key and not self.openai_api_key:
            self.llm_provider = "anthropic"
        
        # 数据路径
        if os.getenv("DYHDC_PATH"):
            self.dyhdc_path = self.project_root / os.getenv("DYHDC_PATH")
        else:
            # 默认路径
            self.dyhdc_path = self.project_root / "《汉语大词典》结构化" / "dyhdc.parsed.fixed.v2.jsonl"
        
        if os.getenv("PHONOLOGY_PATH"):
            self.phonology_path = self.project_root / os.getenv("PHONOLOGY_PATH")
        else:
            self.phonology_path = self.project_root / "音韵数据" / "上古音" / "潘悟云《汉语古音手册》" / "汉语古音手册.txt"
        
        # 运行配置
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
    
    @property
    def data_raw_dir(self) -> Path:
        return self.project_root / "data" / "raw"
    
    @property
    def data_processed_dir(self) -> Path:
        return self.project_root / "data" / "processed"
    
    @property
    def data_test_dir(self) -> Path:
        return self.project_root / "data" / "test"


# 单例模式
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

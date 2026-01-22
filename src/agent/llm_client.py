    """
    LLM客户端封装

    支持OpenAI和Anthropic两种LLM提供商
    """
    from typing import Union, Optional
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from ..config import get_settings


    def get_llm(provider: Optional[str] = None) -> Union[ChatOpenAI, ChatAnthropic]:
        """
        获取LLM客户端
        
        Args:
            provider: "openai" 或 "anthropic"，如果为None则从配置自动选择
            
        Returns:
            LLM客户端实例
            
        Raises:
            ValueError: 如果API Key未设置或provider无效
        """
        settings = get_settings()
        
        # 如果没有指定provider，从配置自动选择
        if provider is None:
            provider = settings.llm_provider
        
        if provider == "openai":
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Please set it in environment variable or .env file."
                )
            
            return ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                temperature=0.1,  # 降低随机性，提高一致性
            )
        
        elif provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Please set it in environment variable or .env file."
                )
            
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                api_key=settings.anthropic_api_key,
                temperature=0.1,
            )
        
        else:
            raise ValueError(f"Unknown provider: {provider}. Supported: 'openai', 'anthropic'")


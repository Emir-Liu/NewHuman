"""
公共模块 配置基类
提供配置管理的通用功能
"""

from dotenv import load_dotenv

class BaseConfig:
    """
    配置基类
    """
    def __init__(self, config_path: str | None = None) -> None:
        # 加载.env系统环境变量
        if config_path is None:
            config_path = ".env"
        bool_load_env: bool = load_dotenv(dotenv_path=config_path)

    def show_config(self) -> None:
        """
        显示所有配置信息,并打印出来
        """
        print("=" * 50)
        print("配置信息:")
        print("=" * 50)
        for attr, value in self.__dict__.items():
            if not attr.startswith('_'):
                print(f"{attr}: {value}")
        print("=" * 50)
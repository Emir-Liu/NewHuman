import json
import sys
from pathlib import Path

from loguru import logger


class LoguruOperator:    
    def __init__(self, 
                 name: str = "default",
                 level: str = "DEBUG",
                 log_dir: str | Path | None = None):
        """
        :param name: 日志器名称（用于区分不同模块）
        :param level: 全局日志级别
        :param log_dir: 日志文件目录，None则不写文件
        """
        self.name = name
        self.level = level
        self.log_dir = Path(log_dir) if log_dir else None
        
        # 创建独立 logger 实例（避免污染全局）
        self._logger = logger.bind(logger_name=name)
        
        # 存储所有 handler_id，方便后续移除
        self._handlers = []
        
        # 初始化默认配置
        self._setup_defaults()
    
    def _setup_defaults(self):
        """配置默认输出（控制台 + 文件）"""
        # 移除所有默认 handler
        self._logger.remove()
        
        # 1. 控制台输出（彩色）
        self.add_console_handler()
        
        # 2. 文件输出（如果指定目录）
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.add_file_handler()
    
    def add_console_handler(self, 
                           level: str | None = None,
                           format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                           colorize: bool = True,
                           **kwargs) -> int:
        """添加控制台输出"""
        handler_id = self._logger.add(
            sys.stderr,
            level=level or self.level,
            format=format,
            colorize=colorize,
            **kwargs
        )
        self._handlers.append(handler_id)
        return handler_id
    
    def add_file_handler(self,
                        filename: str | None = None,
                        level: str | None = None,
                        rotation: str = "100 MB",
                        retention: str = "10 days",
                        compression: str = "zip",
                        format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                        serialize: bool = False,
                        **kwargs) -> int:
        """
        添加文件输出（自动日志轮转）
        
        :param filename: 日志文件名，默认按 logger_name 生成
        :param rotation: 轮转条件（时间/大小）
        :param retention: 保留时长
        :param compression: 压缩格式
        :param serialize: 是否输出为JSON结构化日志
        """
        if not self.log_dir and not filename:
            raise ValueError("必须指定 log_dir 或 filename")
        
        log_file = filename or self.log_dir / f"{self.name}.log"
        
        handler_id = self._logger.add(
            log_file,
            level=level or self.level,
            format=format,
            rotation=rotation,
            retention=retention,
            compression=compression,
            serialize=serialize,
            encoding="utf-8",
            **kwargs
        )
        self._handlers.append(handler_id)
        return handler_id
    
    def add_json_handler(self, 
                        filename: str,
                        level: str | None = None,
                        **kwargs) -> int:
        """快速添加JSON结构化日志"""
        return self.add_file_handler(
            filename=filename,
            level=level,
            format="{time} {level} {message} {extra}",
            serialize=True,
            **kwargs
        )
    
    def remove_handler(self, handler_id: int):
        """移除指定 handler"""
        self._logger.remove(handler_id)
        self._handlers.remove(handler_id)
    
    def clear_handlers(self):
        """清除所有 handlers"""
        for hid in self._handlers[:]:
            self.remove_handler(hid)
    
    def get_logger(self):
        """获取原生 loguru logger 实例"""
        return self._logger
    
    # 保留原生 logger 的所有方法
    def __getattr__(self, name):
        return getattr(self._logger, name)
    
    # ==================== 便捷方法 ====================
    
    @classmethod
    def init_app(cls, 
                 name: str = "app",
                 log_dir: str = "logs",
                 console_level: str = "INFO",
                 file_level: str = "DEBUG") -> "LoguruManager":
        """
        快速初始化项目日志（推荐）
        
        用法：
        log = LoguruManager.init_app(name="my_service", log_dir="logs")
        log.info("服务启动")
        """
        manager = cls(name=name, level=file_level, log_dir=log_dir)
        
        # 控制台只显示INFO及以上
        manager.clear_handlers()
        manager.add_console_handler(level=console_level)
        
        # 文件记录详细日志
        manager.add_file_handler(
            filename=manager.log_dir / f"{name}.log",
            level=file_level,
            rotation="200 MB",
            retention="30 days"
        )
        
        # 错误日志单独文件
        manager.add_file_handler(
            filename=manager.log_dir / f"{name}.error.log",
            level="ERROR",
            rotation="100 MB"
        )
        
        return manager

# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 方式1：快速初始化（推荐）
    from config.config import Config

    config = Config()

    logger = LoguruOperator.init_app(
        name="user_service",
        log_dir="./logs",
        console_level="INFO"
    )

    # 使用体验与原生 loguru 完全一致
    print("用户 {} 登录成功", "Alice")
    logger.debug("调试信息: {}", {"key": "value"})

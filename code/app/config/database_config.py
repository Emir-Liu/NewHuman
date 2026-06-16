"""
关系数据库配置
管理 SQLite / PostgreSQL / MySQL 的持久化设置
"""

import os
from typing import Optional

from dotenv import load_dotenv
from utils.base_config import BaseConfig


class DatabaseConfig(BaseConfig):
    """
    关系数据库配置类

    支持数据库类型：
    - sqlite (默认)
    - postgresql
    - mysql
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        super().__init__(config_path)

        self.config_path: str = config_path

        # 数据库类型 (sqlite / postgresql / mysql)
        self.db_type: str = os.getenv('DATABASE_TYPE', 'sqlite')

        # SQLite 模式下的数据库文件路径
        self.sqlite_db_path: str = os.getenv(
            'SQLITE_DB_PATH',
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "data", "knowledge_base.db"
            )
        )

        # 通用数据库连接 URL (用于 PostgreSQL / MySQL)
        # 格式: postgresql://user:pass@host:port/dbname
        #       mysql://user:pass@host:port/dbname
        self.database_url: str = os.getenv('DATABASE_URL', '')

        # 分离参数（用于手动拼接连接，备用）
        self.db_host: str = os.getenv('DB_HOST', 'localhost')
        self.db_port: int = int(os.getenv('DB_PORT', '5432'))
        self.db_user: str = os.getenv('DB_USER', '')
        self.db_password: str = os.getenv('DB_PASSWORD', '')
        self.db_name: str = os.getenv('DB_NAME', 'knowledge_base')

        # 连接池配置
        self.pool_size: int = int(os.getenv('DB_POOL_SIZE', '5'))
        self.pool_max_overflow: int = int(os.getenv('DB_POOL_MAX_OVERFLOW', '10'))

        # 其他配置
        self.echo_sql: bool = os.getenv('DB_ECHO_SQL', 'false').lower() == 'true'

    def get_sqlalchemy_url(self) -> str:
        """
        根据配置构建 SQLAlchemy 连接 URL。

        优先级: DATABASE_URL > 分离参数拼接
        """
        if self.database_url:
            return self.database_url

        db_type = self.db_type.lower()

        if db_type == "sqlite":
            return f"sqlite:///{self.sqlite_db_path}"

        elif db_type == "postgresql":
            return (
                f"postgresql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        elif db_type == "mysql":
            return (
                f"mysql+pymysql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")


if __name__ == '__main__':
    db_config: DatabaseConfig = DatabaseConfig()
    db_config.show_config()

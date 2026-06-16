"""
SQLAlchemy 引擎 & Session 管理

支持 SQLite / PostgreSQL / MySQL 三种关系数据库，
根据 DatabaseConfig 自动构建连接 URL 并创建引擎。
"""

import os
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

from config.database_config import DatabaseConfig

# 声明式基类，所有 ORM 模型继承自此
Base = declarative_base()

# 全局引擎 & session 工厂
_engine: Optional[Engine] = None
_SessionLocal: Optional[scoped_session] = None
_db_config: Optional[DatabaseConfig] = None


def _build_url(config: DatabaseConfig) -> str:
    """
    根据配置构建 SQLAlchemy 数据库连接 URL。

    优先级：DATABASE_URL 环境变量 > 分离参数拼接
    """
    if config.database_url:
        return config.database_url

    db_type = config.db_type.lower()

    if db_type == "sqlite":
        db_path = config.sqlite_db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        return f"sqlite:///{db_path}"

    elif db_type == "postgresql":
        return (
            f"postgresql://{config.db_user}:{config.db_password}"
            f"@{config.db_host}:{config.db_port}/{config.db_name}"
        )

    elif db_type == "mysql":
        return (
            f"mysql+pymysql://{config.db_user}:{config.db_password}"
            f"@{config.db_host}:{config.db_port}/{config.db_name}"
        )

    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")


def _on_sqlite_connect(dbapi_connection, connection_record):
    """SQLite 连接事件：启用 WAL 模式和外键约束"""
    dbapi_connection.execute("PRAGMA journal_mode=WAL")
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


def init_engine(config: Optional[DatabaseConfig] = None) -> Engine:
    """
    初始化数据库引擎（单例）。

    Args:
        config: 数据库配置，不传则使用默认 DatabaseConfig()

    Returns:
        SQLAlchemy Engine 实例
    """
    global _engine, _SessionLocal, _db_config

    if _engine is not None:
        return _engine

    _db_config = config or DatabaseConfig()
    db_url = _build_url(_db_config)

    connect_args = {}
    if _db_config.db_type.lower() == "sqlite":
        connect_args["check_same_thread"] = False

    _engine = create_engine(
        db_url,
        echo=_db_config.echo_sql,
        pool_size=_db_config.pool_size if _db_config.db_type.lower() != "sqlite" else 0,
        max_overflow=_db_config.pool_max_overflow if _db_config.db_type.lower() != "sqlite" else 0,
        connect_args=connect_args,
    )

    # SQLite 专属事件
    if _db_config.db_type.lower() == "sqlite":
        event.listen(_engine, "connect", _on_sqlite_connect)

    # 创建线程安全的 session 工厂
    _SessionLocal = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    )

    return _engine


def get_session() -> scoped_session:
    """
    获取当前线程的数据库 Session。

    首次调用时自动初始化引擎。

    Returns:
        scoped_session 实例（线程安全）
    """
    global _SessionLocal

    if _SessionLocal is None:
        init_engine()

    return _SessionLocal()


def init_db(config: Optional[DatabaseConfig] = None):
    """
    初始化数据库：创建引擎 + 自动建表。

    生产环境建议使用 Alembic 管理迁移，
    此处 create_all 仅用于开发/测试阶段。

    Args:
        config: 数据库配置
    """
    engine = init_engine(config)
    # 导入所有模型，确保 Base.metadata 包含全部表
    import database.orm.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_engine() -> Engine:
    """获取当前引擎实例"""
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def reset_engine():
    """重置引擎（测试或重新配置时使用）"""
    global _engine, _SessionLocal, _db_config
    if _SessionLocal is not None:
        _SessionLocal.remove()
    _engine = None
    _SessionLocal = None
    _db_config = None

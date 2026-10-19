# 文件路径：app/database.py
# SQLite 连接：默认文件位于项目 data/，相对路径不随启动目录变化。
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

database_url = make_url(os.getenv("DATABASE_URL") or "sqlite:///data/homeplate.db")
if database_url.drivername not in ("sqlite", "sqlite+pysqlite"):
    raise ValueError("第一版使用 SQLite；请移除旧 DATABASE_URL 或改为 sqlite:///data/homeplate.db。")
if not database_url.database or database_url.database == ":memory:":
    raise ValueError("请配置 SQLite 数据库文件路径，以便重启后保留数据。")

database_path = Path(database_url.database)
if not database_path.is_absolute():
    database_path = BASE_DIR / database_path
database_path = database_path.resolve()
database_path.parent.mkdir(parents=True, exist_ok=True)
database_url = database_url.set(database=database_path.as_posix())

engine = create_engine(
    database_url,
    # SELECT 不保留读事务，避免现有“读取后更新”接口发生锁升级冲突。
    # DML 仍由短写事务保护，写入者通过 timeout 等待前一事务提交。
    # 需要跨多次查询的一致性快照时，应显式开启事务。
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
        "autocommit": sqlite3.LEGACY_TRANSACTION_CONTROL,
    },
)


@event.listens_for(engine, "connect")
def configure_sqlite(connection, _record):
    connection.execute("PRAGMA foreign_keys=ON").close()


# 保留默认回滚日志模式；短事务写入等待最多 30 秒。
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 所有模型的基类
Base = declarative_base()


def get_db():
    """FastAPI 依赖：每个请求一个数据库会话，请求结束自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

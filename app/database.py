# 文件路径：app/database.py
# 数据库连接配置：从 .env 读取 DATABASE_URL（MySQL）
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 读取项目根目录的 .env 文件
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "未找到 DATABASE_URL 配置。"
        "请复制 .env.example 为 .env，并填入你的 MySQL 连接信息。"
    )

# SQLAlchemy 引擎；pool_pre_ping 防止 MySQL 连接闲置断开后报错
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 会话工厂：每个请求开一个会话，用完即关
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

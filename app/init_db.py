# 文件路径：app/init_db.py
# 初始化 SQLite 数据表，重复执行保留现有数据。
# 运行方式：.venv/Scripts/python.exe -m app.init_db
from app import models  # noqa: F401  导入以注册所有模型
from app.database import Base, engine


def initialize_database():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print(f"数据库表已就绪：{engine.url.database}")

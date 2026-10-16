# 文件路径：app/init_db.py
# 初始化数据库表（需要 .env 里已配好 MySQL 连接，且 homeplate 库已创建）
# 运行方式：.venv/Scripts/python.exe -m app.init_db
from app import models  # noqa: F401  导入以注册所有模型
from app.database import Base, engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成 ✓")

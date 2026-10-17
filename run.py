# 文件路径：run.py
# 本地启动入口：PyCharm 里直接右键 Run 'run' 即可启动服务
# 也可以命令行跑：.venv/Scripts/python.exe run.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",   # FastAPI 应用位置
        host="127.0.0.1",  # 只监听本机（以后给家人用再改 0.0.0.1）
        port=8000,
        reload=True,       # 改代码自动重启，开发期开着很爽
    )

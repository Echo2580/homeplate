# 文件路径：run.py
# 本地启动入口：PyCharm 里直接右键 Run 'run' 即可启动服务
# 也可以命令行跑：.venv/Scripts/python.exe run.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",   # FastAPI 应用位置
        host="0.0.0.0",    # 0.0.0.0 = 局域网内设备（手机）可访问；只想本机用改回 127.0.0.1
        port=8001,         # 8000 常被本机其他项目占用，项目固定用 8001（Tailscale Serve 已同步指向）
        reload=True,       # 改代码自动重启，开发期开着很爽
    )

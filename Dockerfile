FROM python:3.10-slim

WORKDIR /app

# 复制项目文件
COPY . /app

# 安装依赖
RUN pip install --upgrade pip && pip install -r requirements.txt

# 暴露端口
EXPOSE 8000

# 启动服务（如用 Uvicorn）
CMD ["python", "mcp_server.py"]
# API Integration MCP Server

基于 FastMCP 框架的 API 集成 MCP 服务器，通过 YAML 配置文件集成多个外部 API，为 AI 助手提供标准化工具接口。

## 🚀 功能特性

- ✅ 基于 FastMCP 框架构建
- ✅ YAML 配置文件管理 API 集成
- ✅ 支持多个外部 API 统一管理
- ✅ 自动工具发现和注册
- ✅ 标准化响应格式
- ✅ 类型安全的参数验证
- ✅ 异步 HTTP 请求处理

## 📁 项目结构

```
/
├── .vscode/
│   ├── settings.json          # VSCode 配置
│   └── launch.json           # 调试配置
├── config/
│   └── api_config.yaml       # API 配置文件
├── schemas/
│   └── models.py            # 数据模型
├── clients/
│   └── api_client.py        # API 客户端
├── utils/
│   └── config_loader.py     # 配置加载器
├── mcp_server.py           # 主服务器文件
├── test_mcp.py            # 测试脚本
├── requirements.txt        # 依赖文件
└── README.md              # 项目说明
```

## 🛠️ 创建虚拟项目

```bash
python -m venv .venv
```

## 🛠️ 安装依赖

```bash
pip install -r requirements.txt
```

## ⚙️ 配置说明

编辑 `config/api_config.yaml` 文件来配置 API 集成：

```yaml
server:
  name: "API Integration MCP Server"
  version: "1.0.0"
  description: "集成多个外部API的MCP服务器"
  host: "localhost"
  port: 8000
  mcp_path: "/mcp"

apis:
  - name: "json_placeholder_api"
    base_url: "http://localhost:5678/api"
    headers:
      X-N8N-API-KEY: "your-api-key"
    endpoints:
      - name: "get_users"
        path: "/v1/users"
        method: "GET"
        description: "获取所有用户信息"
        tool_name: "get_all_users"
        headers:
          Content-Type: "application/json"

```

## 🚀 启动服务器

```bash
python mcp_server.py
```

服务器将在 `http://localhost:8000/mcp` 启动

## 🧪 运行测试

```bash
python test_mcp.py
```

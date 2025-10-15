# 快速启动指南

## 🚀 一键启动（虚拟环境）

### Windows PowerShell
```powershell
# 1. 进入项目目录
cd C:\AgentGithub\financial-agent

# 2. 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 3. 启动服务
.\.venv\Scripts\uvicorn.exe app.server:app --host 0.0.0.0 --port 8000
```

### 访问地址
- 🌐 **主页**: http://localhost:8000
- 💬 **交互界面**: http://localhost:8000/agent/playground/
- 📋 **API文档**: http://localhost:8000/docs

## 🔑 环境变量配置

确保 `.env` 文件包含以下配置：
```properties
# 必需 - Gitee AI API密钥
GITEE_API_KEY="your_gitee_api_key_here"

# 必需 - Polygon金融数据API密钥  
POLYGON_API_KEY="your_polygon_api_key_here"

# 可选 - OpenAI密钥（当前未使用）
OPENAI_API_KEY=""
```

## ⚡ 测试示例

在交互界面输入：
```
苹果公司最近一个季度的营收增长率是多少？
```

预期获得详细的财务分析报告。

## 🛠 故障排除

### 端口占用问题
```powershell
# 查看端口占用
netstat -ano | findstr :8000

# 使用其他端口
.\.venv\Scripts\uvicorn.exe app.server:app --host 0.0.0.0 --port 8001
```

### API密钥问题
- 确认Gitee AI账户余额
- 验证API密钥格式正确
- 检查网络连接

## 📱 功能测试

项目支持以下功能：
- ✅ 股票价格查询
- ✅ 财务指标计算
- ✅ 公司财报分析  
- ✅ 投资建议生成
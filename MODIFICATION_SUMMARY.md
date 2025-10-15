# 金融代理项目修改总结

## 📋 项目概览
本文档总结了将原始financial-agent项目从OpenAI GPT-4模型迁移到Gitee AI DeepSeek-V3模型的所有修改内容。

---

## 🔄 主要修改内容

### 1. 模型替换
- **原模型**: OpenAI GPT-4-0125-preview
- **新模型**: Gitee AI DeepSeek-V3
- **修改原因**: 支持国产大模型，降低成本，提高可控性

### 2. 核心文件修改

#### 2.1 `app/agent.py` - 智能代理核心文件

**主要修改点:**

1. **导入增强**:
```python
# 新增导入
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.messages.utils import convert_to_messages
```

2. **自定义DeepSeek包装类**:
```python
class DeepSeekChatOpenAI(ChatOpenAI):
    def _convert_input(self, input):
        """重写输入转换方法，处理LangChain消息格式兼容性"""
        if isinstance(input, list):
            converted_messages = []
            for msg in input:
                if hasattr(msg, 'content'):
                    converted_messages.append(msg)
                elif isinstance(msg, dict):
                    content = msg.get('content', '')
                    msg_type = msg.get('type', 'human')
                    
                    if msg_type == 'human':
                        converted_messages.append(HumanMessage(content=content))
                    elif msg_type == 'ai':
                        converted_messages.append(AIMessage(content=content))
                    elif msg_type == 'system':
                        converted_messages.append(SystemMessage(content=content))
                    else:
                        converted_messages.append(HumanMessage(content=content))
                else:
                    converted_messages.append(msg)
            
            return super()._convert_input(converted_messages)
        return super()._convert_input(input)
```

3. **模型配置更新**:
```python
model = DeepSeekChatOpenAI(
    model="DeepSeek-V3",  # 模型名称
    base_url="https://ai.gitee.com/v1",  # API端点
    api_key=os.getenv("GITEE_API_KEY"),  # API密钥
    streaming=True,
    max_tokens=1024,
    temperature=0.6,
    model_kwargs={
        "top_p": 0.8,
        "extra_body": {
            "top_k": 20,
        },
        "frequency_penalty": 1.1,
    }
)
```

4. **错误处理增强**:
```python
def call_model(state):
    messages = state['messages']
    try:
        # 详细的消息格式转换和调试信息
        formatted_messages = []
        for msg in messages:
            # ... 格式转换逻辑
        
        response = model.invoke(formatted_messages)
        return {"messages": [response]}
        
    except Exception as e:
        print(f"ERROR in call_model: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = AIMessage(content=f"抱歉，处理您的请求时遇到错误：{str(e)}")
        return {"messages": [error_response]}
```

#### 2.2 `.env` - 环境变量配置

**修改内容:**
```properties
# Polygon API key for financial data (获取地址: https://polygon.io/)
POLYGON_API_KEY="EyY8a4iXeWn0HnelWFDWkUcJmglVwpPa"

# OpenAI API key (保留为空，当前使用DeepSeek-V3)
OPENAI_API_KEY=""

# Gitee AI API key for DeepSeek-V3 model (获取地址: https://ai.gitee.com/)
GITEE_API_KEY="1NJHGJ7C6C3DL4HKVFQQ655TX0ARTHRUYGTW1TWQ"
```

#### 2.3 `.env.example` - 环境变量模板

**新增内容:**
```properties
POLYGON_API_KEY=""
OPENAI_API_KEY=""
GITEE_API_KEY=""  # 新增
```

---

## 🔧 技术架构更新

### API兼容性解决方案

**问题**: DeepSeek-V3 API期望OpenAI格式的消息（包含'role'字段），但LangChain发送的是包含'type'字段的消息。

**解决方案**: 
1. 创建自定义`DeepSeekChatOpenAI`类
2. 重写`_convert_input`方法
3. 实现自动消息格式转换

### 消息格式转换流程

```
LangChain消息格式 → 自定义转换器 → OpenAI格式 → DeepSeek-V3 API
{'type': 'human', 'content': '...'}  →  {'role': 'user', 'content': '...'}
```

---

## 🚀 部署和运行说明

### 环境要求
- Python 3.10+
- Poetry 或 pip
- 网络连接（访问Gitee AI API）

### 安装步骤

#### 方法1: 使用Poetry（推荐）
```bash
# 1. 克隆项目
git clone <repository-url>
cd financial-agent

# 2. 安装Poetry
pip install poetry

# 3. 安装依赖
poetry install

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入API密钥

# 5. 启动服务
poetry run uvicorn app.server:app --host 0.0.0.0 --port 8000
```

#### 方法2: 使用虚拟环境
```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件

# 5. 启动服务
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

### 启动命令选项

```bash
# 基本启动
uvicorn app.server:app --host 0.0.0.0 --port 8000

# 开发模式（热重载）
uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload

# 虚拟环境中直接启动
.\.venv\Scripts\uvicorn.exe app.server:app --host 0.0.0.0 --port 8000
```

### 访问地址
- **主页**: http://localhost:8000
- **交互界面**: http://localhost:8000/agent/playground/
- **API文档**: http://localhost:8000/docs

---

## 🔑 API密钥配置

### 必需的API密钥

1. **Gitee AI API Key**
   - 获取地址: https://ai.gitee.com/
   - 用途: DeepSeek-V3模型调用
   - 配置: `GITEE_API_KEY`

2. **Polygon API Key**
   - 获取地址: https://polygon.io/
   - 用途: 获取实时金融数据
   - 配置: `POLYGON_API_KEY`

### 配置步骤
1. 注册相应平台账户
2. 获取API密钥
3. 在`.env`文件中配置
4. 重启服务

---

## ⚡ 功能特性

### 核心功能
- ✅ 智能金融分析对话
- ✅ 实时股票数据查询
- ✅ 财务指标计算（ROE、ROIC、DCF等）
- ✅ 股票新闻获取
- ✅ 财务报表分析

### 支持的财务计算
1. **ROE (净资产收益率)**
2. **ROIC (投资资本回报率)**
3. **Owner Earnings (股东收益)**
4. **DCF (现金流折现估值)**

### 数据源
- **实时数据**: Polygon API
- **AI分析**: DeepSeek-V3模型

---

## 🐛 故障排除

### 常见问题

1. **模型调用失败**
   - 检查GITEE_API_KEY是否正确
   - 检查网络连接
   - 查看终端调试信息

2. **Polygon API错误**
   - 验证POLYGON_API_KEY
   - 检查API配额限制

3. **端口占用**
   - 使用不同端口: `--port 8001`
   - 检查占用进程: `netstat -ano | findstr :8000`

4. **虚拟环境问题**
   - 重新创建: `python -m venv .venv`
   - 重新安装依赖: `pip install -r requirements.txt`

### 调试模式
项目已添加详细的调试信息，启动后可在终端查看：
```
DEBUG: Calling model with messages: [...]
DEBUG: Processing message: {...}
DEBUG: Model response: {...}
```

---

## 📈 性能优化

### 推荐配置
- **max_tokens**: 1024（适中的响应长度）
- **temperature**: 0.6（平衡创造性和准确性）
- **top_p**: 0.8（控制输出多样性）
- **streaming**: True（流式响应，提升用户体验）

### 扩展建议
1. 添加缓存机制
2. 实现负载均衡
3. 增加错误重试逻辑
4. 添加API速率限制

---

## 📊 测试验证

### 测试用例
```
输入: "苹果公司最近一个季度的营收增长率是多少"
预期: 详细的财务分析报告，包含具体数据和背景信息
```

### 验证标准
- ✅ 模型能正确响应中文查询
- ✅ 返回结构化的财务数据
- ✅ 包含数据来源和时间信息
- ✅ 提供背景分析和解释

---

## 📝 更新日志

### v2.0.0 (2024-10-15)
- 🔄 替换模型: GPT-4 → DeepSeek-V3
- 🆕 新增Gitee AI集成
- 🐛 修复消息格式兼容性问题
- 📚 完善错误处理和调试信息
- 🚀 优化虚拟环境部署流程

### v1.0.0 (原始版本)
- 基础GPT-4集成
- Polygon API集成
- 财务计算工具
- LangGraph工作流

---

## 🤝 贡献指南

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 本地测试
4. 提交Pull Request

### 代码规范
- 遵循PEP 8
- 添加类型注解
- 编写测试用例
- 更新文档

---

## 📄 许可证
本项目基于原始许可证继续开发，请参考LICENSE文件。

---

## 🆘 技术支持

### 联系方式
- GitHub Issues: 项目仓库issues页面
- 文档: 本README和相关文档

### 相关资源
- [Gitee AI官方文档](https://ai.gitee.com/)
- [Polygon API文档](https://polygon.io/docs)
- [LangChain官方文档](https://langchain.readthedocs.io/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
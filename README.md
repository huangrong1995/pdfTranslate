# PDF 翻译工具

基于本地 LLM 或云端 API 的 PDF 文档翻译工具，支持英译汉和汉译英。

## 功能特性

- PDF 文件上传（拖拽或选择）
- 英译汉 / 汉译英两种翻译方向
- 原文与译文对比查看
- 翻译结果下载

## 技术栈

- **后端**: FastAPI + pdfminer.six + httpx
- **前端**: HTML + Vanilla JS（无框架依赖）
- **翻译引擎**: Ollama 本地模型 或 阿里云百炼 API（可选）

## 环境要求

- Python 3.9+
- 翻译后端（二选一）：
  - **方案 A**：Ollama（本地 LLM），内存 8GB+
  - **方案 B**：阿里云百炼 API（DashScope）

## 快速开始

### 方案 A：使用 Ollama 本地模型

#### 1. 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 下载安装包 https://ollama.com/download
```

#### 2. 下载翻译模型

```bash
ollama pull qwen2.5:7b-instruct-q4_0
```

模型大小约 4GB，INT4 量化，内存占用低。

#### 3. 启动服务

```bash
# 启动 Ollama 服务（后台运行）
ollama serve

# 启动 FastAPI 服务
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

或者直接运行启动脚本：

```bash
chmod +x start.sh
./start.sh
```

---

### 方案 B：使用阿里云百炼 API

#### 1. 获取 API Key

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 开通百炼服务
3. 创建 API Key

#### 2. 设置环境变量

```bash
export DASHSCOPE_API_KEY='your-api-key-here'
```

#### 3. 启动服务

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 4. 开始使用

打开浏览器访问：http://localhost:8000

## 项目结构

```
pdfTranslate/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── translator.py        # 翻译逻辑（支持 Ollama/百炼）
│   ├── pdf_processor.py     # PDF 文本提取
│   └── requirements.txt     # Python 依赖
├── frontend/
│   └── index.html           # 前端页面
├── uploads/                  # 上传文件目录
├── translated/              # 译文文件目录
└── start.sh                 # 启动脚本
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/api/translate` | POST | 翻译 PDF 文件 |
| `/api/download/{filename}` | GET | 下载翻译结果 |

## 注意事项

- 优先使用 Ollama 本地模型（免费），不可用时自动切换到阿里云百炼 API
- 阿里云百炼 API 按量计费，价格参考官方文档
- 大文件翻译时间较长，请耐心等待

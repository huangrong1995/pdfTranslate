# PDF 翻译工具

基于本地 LLM 的 PDF 文档翻译工具，支持英译汉和汉译英。

## 功能特性

- PDF 文件上传（拖拽或选择）
- 英译汉 / 汉译英两种翻译方向
- 原文与译文对比查看
- 翻译结果下载

## 技术栈

- **后端**: FastAPI + pdfminer.six + httpx
- **前端**: HTML + Vanilla JS（无框架依赖）
- **翻译引擎**: Ollama + Qwen2.5-7B-Instruct（本地部署，完全免费）

## 环境要求

- Python 3.9+
- Ollama（本地 LLM 运行时）
- 内存 8GB+（推荐）

## 快速开始

### 1. 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 下载安装包 https://ollama.com/download
```

### 2. 下载翻译模型

```bash
ollama pull qwen2.5:7b-instruct-q4_0
```

模型大小约 4GB，INT4 量化，内存占用低。

### 3. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动服务

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

### 5. 开始使用

打开浏览器访问：http://localhost:8000

## 项目结构

```
pdfTranslate/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── translator.py        # Ollama 翻译逻辑
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

- 翻译过程在本地完成，无需上传到云端，保护隐私
- 首次翻译需要加载模型，可能需要等待几秒
- 大文件翻译时间较长，请耐心等待

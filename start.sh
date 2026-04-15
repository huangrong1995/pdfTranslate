#!/bin/bash

# PDF 翻译工具启动脚本

set -e

echo "=== PDF 翻译工具 ==="
echo ""

# 加载 .env 文件
if [ -f .env ]; then
    echo "加载 .env 配置..."
    export $(grep -v '^#' .env | xargs)
fi

# 检查翻译后端
USE_OLLAMA=false
USE_DASHSCOPE=false

# 检查 Ollama 是否运行
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    if ollama list | grep -q "qwen2.5:7b-instruct-q4_0"; then
        echo "✓ 使用 Ollama 本地模型"
        USE_OLLAMA=true
    fi
fi

# 检查阿里云百炼 API
if [ -n "$DASHSCOPE_API_KEY" ]; then
    echo "✓ 使用阿里云百炼 API"
    USE_DASHSCOPE=true
fi

if [ "$USE_OLLAMA" = false ] && [ "$USE_DASHSCOPE" = false ]; then
    echo ""
    echo "⚠ 警告：未检测到可用翻译后端"
    echo "  - Ollama 服务未运行或模型未安装"
    echo "  - DASHSCOPE_API_KEY 环境变量未设置"
    echo ""
    echo "请选择以下方案之一："
    echo "  1. 安装并启动 Ollama: ollama serve && ollama pull qwen2.5:7b-instruct-q4_0"
    echo "  2. 设置阿里云百炼 API Key: export DASHSCOPE_API_KEY='your-api-key'"
    echo ""
    echo "继续启动服务，但翻译功能可能不可用..."
    echo ""
fi

# 安装 Python 依赖
echo "安装 Python 依赖..."
cd backend
pip install -r requirements.txt -q
cd ..

# 启动服务
echo ""
echo "启动服务..."
echo "打开 http://localhost:8000 开始使用"
echo "按 Ctrl+C 停止服务"
echo ""

cd /home/workspace/code/github/pdfTranslate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

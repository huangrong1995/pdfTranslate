#!/bin/bash

# PDF 翻译工具启动脚本

set -e

echo "=== PDF 翻译工具 ==="
echo ""

# 检查 Ollama 是否运行
echo "检查 Ollama 服务..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama 服务正在运行"
else
    echo "✗ Ollama 服务未运行"
    echo "请先启动 Ollama: ollama serve"
    exit 1
fi

# 检查模型是否存在
echo "检查翻译模型..."
if ollama list | grep -q "qwen2.5:7b-instruct-q4_0"; then
    echo "✓ 模型已安装"
else
    echo "✗ 模型未安装"
    echo "请先安装模型: ollama pull qwen2.5:7b-instruct-q4_0"
    exit 1
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

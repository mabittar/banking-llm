#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=========================================="
echo " LangChain Pix Environment - Start"
echo "=========================================="

# 1. Check Docker services
echo "[1/3] Verificando infraestrutura Docker..."
if ! docker compose ps --status running | grep -q "langchain-pix-postgres"; then
    echo "  PostgreSQL não está rodando. Subindo infraestrutura..."
    docker compose up -d postgres redis
    echo "  Aguardando serviços ficarem healthy..."
    sleep 5
else
    echo "  Infraestrutura já está rodando."
fi

# 2. Activate virtualenv
echo "[2/3] Ativando virtualenv..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "  ❌ Virtualenv não encontrado. Execute ./scripts/setup.sh primeiro."
    exit 1
fi

# 3. Start server
echo "[3/3] Iniciando servidor FastAPI..."
echo ""
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

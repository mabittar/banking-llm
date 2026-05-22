#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=========================================="
echo " LangChain Pix Environment - Setup"
echo "=========================================="

# 1. Create virtualenv if not exists
if [ ! -d ".venv" ]; then
    echo "[1/4] Criando virtualenv..."
    python -m venv .venv
else
    echo "[1/4] Virtualenv já existe."
fi

# 2. Activate virtualenv
echo "[2/4] Ativando virtualenv..."
source .venv/bin/activate

# 3. Install dependencies
echo "[3/4] Instalando dependências..."
pip install -e ".[dev]" --quiet

# 4. Create .env if not exists
if [ ! -f ".env" ]; then
    echo "[4/4] Criando .env a partir do .env.example..."
    cp .env.example .env
    echo "  ⚠️  Edite o arquivo .env com suas credenciais."
else
    echo "[4/4] Arquivo .env já existe."
fi

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Próximos passos:"
echo "  1. Suba a infra:       docker compose up -d"
echo "  2. Ative o venv:       source .venv/bin/activate"
echo "  3. Rode o servidor:    make server"
echo ""

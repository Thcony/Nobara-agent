#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Instalador do Agente Nobara ==="

if ! command -v python3 >/dev/null; then
    echo "ERRO: python3 não encontrado. Instale com: sudo dnf install python3"
    exit 1
fi

echo "[1/5] Instalando dependências de sistema (dnf)..."
if command -v dnf >/dev/null; then
    sudo dnf install -y python3-pip portaudio-devel ffmpeg || \
        echo "AVISO: não foi possível instalar todos os pacotes de sistema. Verifique portaudio-devel."
fi

echo "[2/5] Criando o ambiente virtual (.venv)..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "[3/5] Configurando a chave de API..."
if [ ! -f .env ]; then
    cp .env.example .env
fi
read -r -p "Cole sua GEMINI_API_KEY (obtida em https://aistudio.google.com): " KEY
if [ -n "$KEY" ]; then
    sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$KEY|" .env
    echo "Chave salva em .env"
fi

echo "[4/5] Configurando MCP (opcional)..."
mkdir -p ~/.config/nobara-agent
if [ ! -f ~/.config/nobara-agent/mcp_servers.json ] && [ -f mcp_servers.example.json ]; then
    cp mcp_servers.example.json ~/.config/nobara-agent/mcp_servers.json
    echo "Exemplo copiado para ~/.config/nobara-agent/mcp_servers.json (edite se quiser usar MCP)."
fi

echo "[5/5] Criando o comando global 'nobara-agent'..."
mkdir -p ~/.local/bin
cat > ~/.local/bin/nobara-agent <<EOF
#!/usr/bin/env bash
cd "$(pwd)"
source .venv/bin/activate
exec python -m nobara_agent "\$@"
EOF
chmod +x ~/.local/bin/nobara-agent
chmod +x run.sh

if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Adicionei ~/.local/bin ao PATH (reabra o terminal para valer)."
fi

echo ""
echo "=== Instalação concluída! ==="
echo "Uso:"
echo "  nobara-agent          # modo voz (microfone + alto-falante)"
echo "  nobara-agent --texto  # modo texto, para testar sem microfone"

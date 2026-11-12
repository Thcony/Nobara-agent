#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   🤖  INSTALADOR DO AGENTE NOBARA        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if ! command -v python3 >/dev/null; then
    echo "ERRO: python3 não encontrado. Instale com: sudo dnf install python3"
    exit 1
fi

echo "[1/5] Instalando dependências de sistema (pedirá sua senha)..."
if command -v dnf >/dev/null; then
    sudo dnf install -y python3-pip portaudio-devel || \
        echo "AVISO: não foi possível instalar todos os pacotes de sistema. Verifique portaudio-devel."
fi

echo "[2/5] Criando o ambiente virtual (.venv) e instalando pacotes Python..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt

echo "[3/5] Preparando configuração..."
if [ ! -f .env ]; then
    cp .env.example .env
fi
mkdir -p ~/.config/nobara-agent
if [ ! -f ~/.config/nobara-agent/mcp_servers.json ] && [ -f mcp_servers.example.json ]; then
    cp mcp_servers.example.json ~/.config/nobara-agent/mcp_servers.json
fi

echo "[4/5] Criando o comando global 'nobara-agent'..."
mkdir -p ~/.local/bin
cat > ~/.local/bin/nobara-agent <<EOF
#!/usr/bin/env bash
cd "$PROJECT_DIR"
exec .venv/bin/python -m nobara_agent "\$@"
EOF
chmod +x ~/.local/bin/nobara-agent

if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "  → Adicionei ~/.local/bin ao PATH (reabra o terminal para valer)."
fi

echo "[5/5] Criando lançador 'Agente Nobara' no menu de aplicativos..."
mkdir -p ~/.local/share/applications
mkdir -p "$HOME/Desktop" 2>/dev/null || true
cat > ~/.local/share/applications/nobara-agent.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Agente Nobara
Comment=Assistente de IA com voz e visão de tela
Exec=bash -c 'cd "$PROJECT_DIR" && exec .venv/bin/python -m nobara_agent'
Terminal=true
Icon=utilities-terminal
Categories=Utility;Development;
EOF
if [ -d "$HOME/Desktop" ]; then
    cp ~/.local/share/applications/nobara-agent.desktop "$HOME/Desktop/" 2>/dev/null || true
    chmod +x "$HOME/Desktop/nobara-agent.desktop" 2>/dev/null || true
fi

echo ""
echo "✔ Instalação concluída!"
echo ""
echo "  • Menu de aplicativos: procure 'Agente Nobara'"
echo "  • Terminal: nobara-agent"
echo ""
echo "Abrindo o menu do agente..."
sleep 2
exec .venv/bin/python -m nobara_agent

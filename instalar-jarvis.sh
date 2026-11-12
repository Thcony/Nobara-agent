#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

URL="https://github.com/isair/jarvis/releases/latest/download/Jarvis-Linux-x64.tar.gz"
DEST="$HOME/jarvis"
APP_DIR="$DEST/Jarvis"
BIN="$APP_DIR/Jarvis"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   🤖  INSTALADOR DO JARVIS (isair)       ║"
echo "║   Assistente de desktop local, ~400 MB   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if ! command -v curl >/dev/null; then
    echo "Instalando curl..."
    sudo dnf install -y curl
fi
if ! command -v tar >/dev/null; then
    sudo dnf install -y tar
fi

echo "[1/4] Baixando o Jarvis para Linux (release mais recente)..."
mkdir -p "$DEST"
TMP=$(mktemp /tmp/jarvis-XXXXXX.tar.gz)
curl -L --progress-bar -o "$TMP" "$URL"

echo "[2/4] Extraindo em ~/jarvis..."
tar -xzf "$TMP" -C "$DEST"
rm -f "$TMP"

if [ ! -f "$BIN" ]; then
    BIN=$(find "$DEST" -type f -name Jarvis | head -1)
    if [ -z "$BIN" ]; then
        echo "ERRO: binário Jarvis não encontrado após extração. Veja o conteúdo de ~/jarvis."
        exit 1
    fi
fi
APP_DIR=$(dirname "$BIN")
chmod +x "$BIN"

echo "[3/4] Configurando o Gemini como cérebro do Jarvis (opcional)..."
KEY=""
if [ -f .env ]; then
    KEY=$(grep -E '^GEMINI_API_KEY=' .env | cut -d= -f2- | tr -d '"' || true)
fi
if [ -n "$KEY" ] && [[ "$KEY" != *"cole-sua-chave"* ]]; then
    read -r -p "Usar sua chave do Gemini (do .env do Agente Nobara) no Jarvis? [S/n] " RESP
    if [[ ! "$RESP" =~ ^[nN] ]]; then
        mkdir -p ~/.config/jarvis
        if [ -f ~/.config/jarvis/config.json ]; then
            echo "  ~/.config/jarvis/config.json já existe — não vou sobrescrever."
            echo "  Edite manualmente seguindo o JARVIS-DESKTOP.md se quiser usar o Gemini."
        else
            cat > ~/.config/jarvis/config.json <<EOF
{
  "llm_provider": "openai_compatible",
  "llm_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
  "llm_api_key": "$KEY",
  "llm_chat_model": "gemini-3.1-flash"
}
EOF
            echo "  ✔ Jarvis configurado para usar o Gemini (modelo gemini-3.1-flash)."
            echo "  Obs: a memória semântica pode precisar do Ollama; sem ele o Jarvis"
            echo "  usa busca por palavras-chave (funciona normal)."
        fi
    fi
else
    echo "  Pulado: sem chave no .env. No primeiro uso, o assistente de configuração"
    echo "  do Jarvis vai te guiar (Ollama local ou servidor compatível com OpenAI —"
    echo "  veja o JARVIS-DESKTOP.md para usar o Gemini)."
fi

echo "[4/4] Criando lançador 'Jarvis' no menu de aplicativos..."
mkdir -p ~/.local/share/applications
ICON=$(find "$APP_DIR" -iname "*.png" | head -1)
cat > ~/.local/share/applications/jarvis-desktop.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Jarvis
Comment=Assistente de IA local com voz e memória
Exec="$BIN"
Terminal=false
${ICON:+Icon=$ICON}
Categories=Utility;Development;
EOF

echo ""
echo "✔ Jarvis instalado!"
echo ""
echo "  • Menu de aplicativos: procure 'Jarvis' (ou rode: $BIN)"
echo "  • No primeiro uso, siga o assistente: escolha microfone, modelo e voz."
echo "  • Guia completo em português: JARVIS-DESKTOP.md nesta pasta."
echo ""

# 🤖 Jarvis para Nobara Linux

Em vez de construir um assistente do zero, usamos o **[Jarvis do isair](https://github.com/isair/jarvis)**
(2.2k+ ⭐): um assistente de desktop **local-first** com voz contínua, memória
pessoal (diário + grafo de conhecimento), OCR de tela, ditado e **MCP**.

⚠️ **Não precisa "clonar de Windows"**: o projeto já publica build nativo pra
Linux x64. Este guia cobre as diferenças e configurações no Nobara.

## Instalação (automática)

```bash
cd Nobara-agent
chmod +x instalar-jarvis.sh
./instalar-jarvis.sh
```

O script baixa a release mais recente (~400 MB), extrai em `~/jarvis`,
configura o Gemini como cérebro (usando a chave do `.env` do Agente Nobara)
e cria o lançador **Jarvis** no menu de aplicativos.

## Primeiro uso

1. Abra **Jarvis** pelo menu de aplicativos
2. O assistente de configuração pede:
   - **Microfone**: permita o acesso
   - **Reconhecimento de fala**: ele baixa um modelo **Whisper** local
     (recomendo `small` ou `medium` — bons em pt-BR com gíria; `large-v3-turbo`
     se tiver GPU com VRAM de sobra)
   - **Modelo de chat**: se o `instalar-jarvis.sh` já configurou o Gemini,
     ele deve detectar; senão, escolha **OpenAI-compatible** e use:

| Campo | Valor |
|-------|-------|
| Base URL | `https://generativelanguage.googleapis.com/v1beta/openai` |
| API key | sua chave do Google AI Studio |
| Chat model | `gemini-3.1-flash` |

3. Quando ele avisar que está *Listening*, teste: **"Jarvis, me ajuda a pensar no meu dia."**

## Diferenças no Linux (o que "mudou do Windows")

| Recurso | Windows | Nobara (Linux) |
|---------|---------|----------------|
| Voz (conversa contínua) | ✔ | ✔ via PipeWire/PulseAudio |
| Ditado (segurar tecla e colar) | ✔ Ctrl+Win | ⚠️ requer **X11**; Wayland tem suporte limitado |
| Hotkey do ditado | Ctrl+Win | Ctrl+Alt |
| OCR de tela / screenshots | ✔ | ✔ |
| MCP | ✔ | ✔ |
| Memória semântica | ✔ | precisa de embeddings: ou via Gemini/Ollama, ou cai pra busca por palavra-chave |

Se o microfone não for capturado: **Configurações do sistema → Som** confira o
dispositivo de entrada; no Jarvis, escolha o microfone (não um "monitor de
saída") em Settings. Para diagnóstico, rode com `JARVIS_VOICE_DEBUG=1`.

## Configuração manual

Arquivo: `~/.config/jarvis/config.json`

```json
{
  "llm_provider": "openai_compatible",
  "llm_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
  "llm_api_key": "SUA_CHAVE",
  "llm_chat_model": "gemini-3.1-flash"
}
```

### Totalmente local (sem nuvem)

Instale o [Ollama](https://ollama.com/download) e aponte o Jarvis pra ele no
assistente de configuração — nada sai da sua máquina.

## MCP (Roblox Studio etc.)

Em **Settings → MCP** adicione os servidores. Para o Roblox Studio, instale o
plugin-ponte da comunidade (`roblox-studio-mcp` no GitHub) e registre o
servidor MCP dele lá.

## Atualizar

```bash
./instalar-jarvis.sh
```

(baixa a release nova e extrai por cima; sua config em `~/.config/jarvis/` fica intacta)

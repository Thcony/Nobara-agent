# Agente Nobara 🎙️🤖

Assistente de IA com **voz** (você fala, ele responde falando), **visão de tela**
e **MCP** para o Nobara Linux, usando a API do Gemini — com menu visual no terminal.

> **Quer um Jarvis pronto, estilo assistente de verdade?** Este repo também
> traz um instalador do [Jarvis](https://github.com/isair/jarvis) (2.2k+ ⭐),
> assistente de desktop com voz contínua, memória pessoal e MCP, já com build
> nativo pra Linux e configurado pra usar o Gemini. Veja o
> [JARVIS-DESKTOP.md](JARVIS-DESKTOP.md).

## Instalação

```bash
git clone https://github.com/Thcony/Nobara-agent.git
cd Nobara-agent
./install.sh
```

> Se der "permissão negada", rode `chmod +x install.sh` antes.
> Arquivos `.sh` não abrem com duplo clique no gerenciador de arquivos —
> rode pelo terminal, ou use o lançador **"Agente Nobara"** que a instalação
> cria no menu de aplicativos e na sua Área de Trabalho.

O instalador faz tudo: dependências do sistema, venv, pacotes Python —
e **abre o menu do agente** no final.

## O menu

| Opção | O que faz |
|-------|-----------|
| 🔑 Configurar chave de API | cola sua chave do [Google AI Studio](https://aistudio.google.com) (grátis) e salva no `.env` |
| 🎙️ Escolher a voz | lista de vozes do Gemini (Aoede, Puck, Charon, Kore...) com descrição |
| 🔊 Testar a voz | gera e toca uma frase de amostra com a voz escolhida |
| 💬 Conversar por voz | **ENTER** para gravar → transcreve pt-BR (com gírias) → Gemini responde → fala com a voz escolhida |
| ⌨️ Conversar por texto | chat escrito, com `tela` para anexar screenshot |
| ⚙️ Configurações | troca modelos, confirmação de comandos, etc. |

Na conversa por voz: digite um texto em vez de dar ENTER para enviar escrito,
` tela` faz ele olhar sua tela na hora, `sair` volta ao menu.

## O que o agente sabe fazer

- **Ouvir você** (transcrição em português fluentes e gírias) e **responder falando**
- **Ver sua tela** (digite `tela` ou peça "olha minha tela")
- **Executar comandos** — somente-leitura rodam direto; destrutivos pedem confirmação
- **Diagnosticar o Nobara**: `journalctl`, `dmesg`, `dnf`, logs do Steam/Proton
- **Conectar em servidores MCP** via `~/.config/nobara-agent/mcp_servers.json`
  (inclusive Roblox Studio, com plugin-ponte da comunidade)

## Uso avançado (terminal)

```bash
nobara-agent --texto       # abre direto no chat de texto
nobara-agent --voz         # abre direto no chat de voz
nobara-agent --tempo-real  # modo Live API experimental (áudio contínuo)
```

## Configuração (`.env`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `GEMINI_API_KEY` | — | chave do Google AI Studio |
| `GEMINI_TEXT_MODEL` | `gemini-3.1-flash` | texto e transcrição |
| `GEMINI_TTS_MODEL` | `gemini-2.5-flash-preview-tts` | voz do agente |
| `GEMINI_LIVE_MODEL` | `gemini-3.1-flash-live-preview` | modo tempo real |
| `GEMINI_VOICE` | `Aoede` | voz selecionada |
| `CONFIRM_DANGEROUS` | `1` | confirmar comandos de escrita |

Os nomes de modelo mudam com frequência; confira em
[ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs).

## Segurança

- Comandos destrutivos (`rm`, `dnf remove`, `dd`, `sudo`...) **sempre** pedem
  confirmação, com `CONFIRM_DANGEROUS=1` (padrão).
- A chave fica só no `.env` local (ignorado pelo git). Não compartilhe.
- A tela só é capturada quando você pede.

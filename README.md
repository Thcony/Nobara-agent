# Agente Nobara 🎙️🤖

Assistente de IA com **voz em tempo real** e **visão de tela** para o Nobara Linux,
usando a Gemini Live API (Google). Executa comandos, diagnostica erros do sistema
e conecta em servidores MCP (inclusive Roblox Studio via ponte da comunidade).

## Instalação

```bash
cd nobara-agent
chmod +x install.sh run.sh
./install.sh
```

O instalador cria o `.venv`, instala tudo, pede sua chave de API
([pegue grátis no Google AI Studio](https://aistudio.google.com/)) e cria o
comando global `nobara-agent`.

## Uso

```bash
nobara-agent          # modo voz: fale no microfone, ele responde falando
nobara-agent --texto  # modo texto, para testar sem microfone
```

Comandos durante a sessão (digite no terminal):

| Digite   | Efeito                                        |
|----------|-----------------------------------------------|
| `tela`   | envia um screenshot da sua tela para o agente |
| `sair`   | encerra                                       |

No modo voz, você também pode pedir: *"olha o que aparece na minha tela"* —
ele captura e lê sozinho.

## O que o agente sabe fazer

- **Ver sua tela** (ferramenta `ver_tela`, sob demanda)
- **Executar comandos** (`rodar_comando`) — comandos somente-leitura rodam
  direto; qualquer coisa destrutiva pede sua confirmação no terminal
- **Diagnosticar o Nobara**: `journalctl`, `dmesg`, `dnf`, logs do Steam/Proton
- **Conectar em servidores MCP**

## MCP

Edite `~/.config/nobara-agent/mcp_servers.json` (um exemplo é criado na
instalação):

```json
{
  "meus-arquivos": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/voce/Projetos"]
  }
}
```

Cada chave vira um servidor MCP; as ferramentas dele ficam disponíveis
automaticamente para o agente.

### Roblox Studio

O Studio não fala MCP nativamente. Instale no Studio um plugin-ponte da
comunidade (procure por `roblox-studio-mcp` no GitHub), que expõe um servidor
HTTP local, e registre o servidor MCP correspondente no JSON acima.

## Atalho de teclado

Nas configurações do KDE/GNOME (Teclado → Atalhos → Personalizado), crie um
atalho que roda:

```bash
bash -c 'cd ~/nobara-agent && ./run.sh'
```

Ajuste o caminho para onde você colocou a pasta.

## Configuração (`.env`)

| Variável            | Padrão                        | Descrição                        |
|---------------------|-------------------------------|----------------------------------|
| `GEMINI_API_KEY`    | —                             | sua chave do Google AI Studio    |
| `GEMINI_LIVE_MODEL` | `gemini-3.1-flash-live-preview` | modelo do modo voz            |
| `GEMINI_TEXT_MODEL` | `gemini-3.1-flash`            | modelo do modo texto             |
| `GEMINI_VOICE`      | (vazio = voz padrão)          | nome da voz, ex.: `Aoede`, `Puck`|
| `CONFIRM_DANGEROUS` | `1`                           | pedir confirmação p/ comandos de escrita |

Os nomes de modelo mudam com frequência; confira os atuais em
[ai.google.dev/gemini-api/docs/live](https://ai.google.dev/gemini-api/docs/live).

## Segurança

- Comandos destrutivos (`rm`, `dnf remove`, `dd`, `sudo`...) **sempre** pedem
  confirmação, com `CONFIRM_DANGEROUS=1` (padrão).
- A chave de API fica só no `.env` local. Não compartilhe a pasta com o `.env`.
- A tela só é capturada quando você pede (`tela`) ou quando o agente usa a
  ferramenta `ver_tela` — nada é enviado sem motivo.

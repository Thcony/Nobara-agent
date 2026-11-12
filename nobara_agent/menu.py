import asyncio
import os

import questionary
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .agent import SYSTEM, make_client, rodar_comando_tool
from .config import cfg
from .mcp_client import open_mcp_sessions
from .screenshot import capture_screen
from .speech import VOICES, record_until_silence, speak, transcribe

console = Console()
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

STYLE = questionary.Style([
    ("qmark", "fg:cyan bold"),
    ("question", "bold"),
    ("answer", "fg:cyan bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green bold"),
])


def save_env(key: str, value: str) -> None:
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            break
    else:
        lines.append(f"{key}={value}\n")
    with open(ENV_PATH, "w") as f:
        f.writelines(lines)
    os.environ[key] = value


def key_ok() -> bool:
    return bool(cfg.api_key) and "cole-sua-chave" not in cfg.api_key


def configure_key():
    console.print(Panel(
        "Cole sua chave do Google AI Studio.\n"
        "[bold cyan]https://aistudio.google.com[/bold cyan] → Get API key (grátis)",
        title="🔑 Chave de API", border_style="cyan"))
    key = questionary.password("GEMINI_API_KEY:", style=STYLE).ask()
    if key and key.strip():
        save_env("GEMINI_API_KEY", key.strip())
        cfg.api_key = key.strip()
        console.print("[bold green]✔ Chave salva no .env![/bold green]")
        questionary.press_any_key_to_continue(style=STYLE).ask()


def choose_voice():
    choices = [questionary.Choice(f"🗣️  {name} — {desc}", value=name)
               for name, desc in VOICES.items()]
    voice = questionary.select("Escolha a voz do agente:", choices=choices,
                               default=cfg.voice if cfg.voice in VOICES else "Aoede",
                               style=STYLE).ask()
    if voice:
        save_env("GEMINI_VOICE", voice)
        cfg.voice = voice
        console.print(f"[bold green]✔ Voz definida: {voice}[/bold green]")
        if key_ok():
            test_voice(quiet=True)
        questionary.press_any_key_to_continue(style=STYLE).ask()


def test_voice(quiet: bool = False):
    if not key_ok():
        console.print("[red]Configure a chave de API primeiro.[/red]")
        return
    client = make_client()
    frase = ("E aí! Aqui é o seu agente no Nobara. Se essa voz te agrada, "
             "a gente vai conversar bastante junto!")
    try:
        with console.status("🔊 gerando e tocando amostra de voz..."):
            speak(client, frase, cfg.voice or "Aoede")
        if not quiet:
            console.print("[bold green]✔ Se você ouviu a frase, a voz está funcionando![/bold green]")
    except Exception as e:
        console.print(f"[red]Erro ao gerar voz: {e}[/red]")
        console.print("[dim]Dica: confira o GEMINI_TTS_MODEL no menu de configurações.[/dim]")
    if not quiet:
        questionary.press_any_key_to_continue(style=STYLE).ask()


async def voice_chat():
    if not key_ok():
        configure_key()
        if not key_ok():
            return
    client = make_client()
    voice = cfg.voice or "Aoede"
    async with open_mcp_sessions() as mcp_sessions:
        chat = client.aio.chats.create(
            model=cfg.text_model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                tools=[rodar_comando_tool, *mcp_sessions],
            ),
        )
        console.print(Panel(
            f"Voz atual: [bold cyan]{voice}[/bold cyan]\n\n"
            "[bold]ENTER[/bold] sozinho = 🎤 gravar (fale e faça uma pausa)\n"
            "Digite um texto = envia escrito\n"
            "[bold]tela[/bold] = ele olha sua tela agora\n"
            "[bold]sair[/bold] = volta ao menu",
            title="💬 Conversa por voz", border_style="green"))
        while True:
            try:
                entrada = await asyncio.to_thread(input, "\n🎤 ")
            except (EOFError, KeyboardInterrupt):
                return
            low = entrada.strip().lower()
            if low in ("sair", "exit", "quit", "menu"):
                return
            if low == "tela":
                path = await asyncio.to_thread(capture_screen)
                if not path:
                    console.print("[red]Falha ao capturar a tela.[/red]")
                    continue
                with open(path, "rb") as f:
                    img = f.read()
                with console.status("🤖 olhando sua tela..."):
                    res = await chat.send_message([
                        types.Part.from_bytes(data=img, mime_type="image/png"),
                        "Veja minha tela e me ajude com o que aparece nela.",
                    ])
                resposta = res.text or "(sem resposta)"
                console.print(f"[bold green]agente>[/bold green] {resposta}")
                with console.status("🔊 falando..."):
                    await asyncio.to_thread(speak, client, resposta, voice)
                continue
            if entrada.strip():
                pergunta = entrada.strip()
            else:
                console.print("[dim]🎤 gravando... fale e faça uma pausa[/dim]")
                wav = await asyncio.to_thread(record_until_silence)
                if not wav:
                    console.print("[red]Nada gravado. Tente de novo.[/red]")
                    continue
                with console.status("🧠 entendendo o que você falou..."):
                    pergunta = await asyncio.to_thread(transcribe, client, wav)
                if not pergunta:
                    console.print("[red]Não entendi. Tente falar mais perto do microfone.[/red]")
                    continue
                console.print(f"[bold blue]você>[/bold blue] {pergunta}")
            with console.status("🤖 pensando..."):
                res = await chat.send_message(pergunta)
            resposta = res.text or "(sem resposta)"
            console.print(f"[bold green]agente>[/bold green] {resposta}")
            with console.status("🔊 falando..."):
                await asyncio.to_thread(speak, client, resposta, voice)


async def text_chat():
    if not key_ok():
        configure_key()
        if not key_ok():
            return
    client = make_client()
    async with open_mcp_sessions() as mcp_sessions:
        chat = client.aio.chats.create(
            model=cfg.text_model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                tools=[rodar_comando_tool, *mcp_sessions],
            ),
        )
        console.print(Panel(
            "[bold]tela[/bold] = anexa screenshot da sua tela\n"
            "[bold]sair[/bold] = volta ao menu",
            title="⌨️ Conversa por texto", border_style="blue"))
        pending_image = None
        while True:
            try:
                q = (await asyncio.to_thread(input, "\nvocê> ")).strip()
            except (EOFError, KeyboardInterrupt):
                return
            low = q.lower()
            if low in ("sair", "exit", "quit", "menu"):
                return
            if low == "tela":
                path = await asyncio.to_thread(capture_screen)
                if path:
                    pending_image = path
                    console.print("[dim]screenshot será anexado à próxima mensagem[/dim]")
                else:
                    console.print("[red]Falha ao capturar a tela.[/red]")
                continue
            if not q:
                continue
            parts = []
            if pending_image:
                with open(pending_image, "rb") as f:
                    parts.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))
                pending_image = None
            parts.append(types.Part.from_text(text=q))
            with console.status("🤖 pensando..."):
                res = await chat.send_message(parts)
            console.print(f"[bold green]agente>[/bold green] {res.text or '(sem resposta)'}")


def settings_menu():
    campos = [
        ("GEMINI_TEXT_MODEL", "Modelo de texto/transcrição", cfg.text_model,
         lambda v: setattr(cfg, "text_model", v)),
        ("GEMINI_TTS_MODEL", "Modelo de voz (TTS)", cfg.tts_model,
         lambda v: setattr(cfg, "tts_model", v)),
        ("GEMINI_LIVE_MODEL", "Modelo Live (tempo real)", cfg.model,
         lambda v: setattr(cfg, "model", v)),
        ("CONFIRM_DANGEROUS", "Confirmar comandos perigosos (1=sim, 0=não)", cfg.confirm_dangerous,
         lambda v: setattr(cfg, "confirm_dangerous", v == "1")),
    ]
    while True:
        tabela = Table(title="⚙️ Configurações atuais", border_style="yellow")
        tabela.add_column("Variável", style="cyan")
        tabela.add_column("Valor", style="bold")
        tabela.add_row("GEMINI_TEXT_MODEL", cfg.text_model)
        tabela.add_row("GEMINI_TTS_MODEL", cfg.tts_model)
        tabela.add_row("GEMINI_LIVE_MODEL", cfg.model)
        tabela.add_row("GEMINI_VOICE", cfg.voice or "Aoede")
        tabela.add_row("CONFIRM_DANGEROUS", "1" if cfg.confirm_dangerous else "0")
        console.print(tabela)
        escolha = questionary.select(
            "O que configurar?",
            choices=[questionary.Choice(label, value=key) for key, label, _, _ in campos]
            + [questionary.Choice("← Voltar", value=None)],
            style=STYLE).ask()
        if escolha is None:
            return
        campo = next(c for c in campos if c[0] == escolha)
        novo = questionary.text(f"{campo[1]} ({campo[0]}):", default=str(campo[2]),
                                style=STYLE).ask()
        if novo is not None and novo.strip():
            save_env(escolha, novo.strip())
            campo[3](novo.strip())
            console.print("[bold green]✔ Salvo![/bold green]")


def painel_status():
    tabela = Table(show_header=False, box=None, padding=(0, 2))
    tabela.add_column(style="bold")
    tabela.add_column()
    tabela.add_row("🔑 Chave de API",
                   "[green]✔ configurada[/green]" if key_ok() else "[red]✘ não configurada[/red]")
    tabela.add_row("🗣️ Voz", cfg.voice or "Aoede")
    tabela.add_row("🧠 Modelo texto", cfg.text_model)
    tabela.add_row("🔊 Modelo voz", cfg.tts_model)
    console.print(tabela)
    console.print()


def main_menu():
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w") as f:
            f.write("GEMINI_API_KEY=\n")
    while True:
        console.clear()
        console.print(Panel(
            Text("🤖 A G E N T E   N O B A R A", justify="center", style="bold cyan"),
            subtitle="voz + visão de tela + MCP", border_style="cyan"))
        painel_status()
        if not key_ok():
            console.print("[yellow]⚠ Configure sua chave de API para começar.[/yellow]\n")
        escolha = questionary.select(
            "O que você quer fazer?",
            choices=[
                questionary.Choice("🔑  Configurar chave de API", value="key"),
                questionary.Choice("🎙️  Escolher a voz do agente", value="voice"),
                questionary.Choice("🔊  Testar a voz", value="test_voice"),
                questionary.Choice("💬  Conversar por voz (fale, ele responde falando)",
                                   value="voice_chat"),
                questionary.Choice("⌨️   Conversar por texto", value="text_chat"),
                questionary.Choice("⚙️   Modelos e configurações", value="settings"),
                questionary.Choice("🚪  Sair", value="exit"),
            ],
            style=STYLE).ask()
        if escolha is None or escolha == "exit":
            console.print("[bold cyan]Até logo! 👋[/bold cyan]")
            return
        try:
            if escolha == "key":
                configure_key()
            elif escolha == "voice":
                choose_voice()
            elif escolha == "test_voice":
                test_voice()
            elif escolha == "voice_chat":
                console.clear()
                asyncio.run(voice_chat())
            elif escolha == "text_chat":
                console.clear()
                asyncio.run(text_chat())
            elif escolha == "settings":
                console.clear()
                settings_menu()
        except KeyboardInterrupt:
            console.print("\n[dim]voltando ao menu...[/dim]")

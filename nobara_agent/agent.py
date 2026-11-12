import asyncio
import json

import numpy as np
from google import genai
from google.genai import types

from .config import cfg
from .mcp_client import open_mcp_sessions
from .screenshot import capture_screen
from .tools import handle_shell, is_readonly

SYSTEM = (
    "Você é o assistente pessoal do usuário no Nobara Linux. "
    "Responda sempre em português brasileiro, de forma rápida, direta e informal. "
    "Você pode ver a tela do usuário com a ferramenta ver_tela e executar comandos "
    "no sistema com rodar_comando. Diagnostique erros do sistema usando journalctl, "
    "dmesg e dnf. Antes de qualquer comando destrutivo (rm, dnf remove, dd, mkfs, "
    "ou qualquer sudo que altere o sistema), explique o que vai fazer e espere o "
    "usuário confirmar."
)

TOOLS_DECL = [
    types.Tool(function_declarations=[
        {
            "name": "rodar_comando",
            "description": "Executa um comando shell no Linux e retorna stdout e stderr",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "cmd": {"type": "STRING", "description": "O comando a executar"}
                },
                "required": ["cmd"],
            },
        },
        {
            "name": "ver_tela",
            "description": "Captura um screenshot da tela do usuário para ver o que ele está vendo agora",
            "parameters": {"type": "OBJECT", "properties": {}},
        },
    ])
]


def make_client() -> genai.Client:
    return genai.Client(api_key=cfg.api_key or None)


async def ask_confirmation(cmd: str) -> bool:
    print(f"\n[confirmação] o agente quer executar: {cmd}")
    answer = await asyncio.to_thread(input, "Permitir? [s/N] ")
    return answer.strip().lower() in ("s", "sim", "y", "yes")


async def execute_function(session, name: str, args: dict, mcp_sessions: list) -> dict:
    if name == "rodar_comando":
        cmd = args.get("cmd", "")
        if not is_readonly(cmd) and cfg.confirm_dangerous and not await ask_confirmation(cmd):
            return {"result": "Comando negado pelo usuário."}
        return await asyncio.to_thread(handle_shell, cmd)

    if name == "ver_tela":
        path = await asyncio.to_thread(capture_screen)
        if not path:
            return {"result": "Falha ao capturar a tela."}
        with open(path, "rb") as f:
            await session.send(input=types.Blob(data=f.read(), mime_type="image/png"))
        return {"result": "Imagem da tela capturada e enviada para você."}

    for label, mcp_session in mcp_sessions:
        try:
            res = await mcp_session.call_tool(name, args or {})
            texts = [c.text for c in res.content if hasattr(c, "text")]
            return {"result": texts or "sem conteúdo"}
        except Exception:
            continue
    return {"error": f"Ferramenta desconhecida: {name}"}


async def mic_loop(session, mic):
    loop = asyncio.get_running_loop()
    while True:
        data, _ = await loop.run_in_executor(None, mic.read, 2048)
        await session.send(input=types.Blob(
            data=data.tobytes(), mime_type="audio/pcm;rate=16000"
        ))


async def receive_loop(session, speaker, mcp_sessions: list):
    async for resp in session.receive():
        sc = resp.server_content
        if sc and sc.interrupted:
            speaker.abort()
            speaker.start()
        audio = resp.data
        if audio:
            speaker.write(np.frombuffer(audio, dtype=np.int16))
        if resp.tool_call and resp.tool_call.function_calls:
            for fc in resp.tool_call.function_calls:
                result = await execute_function(
                    session, fc.name, dict(fc.args or {}), mcp_sessions
                )
                await session.send_tool_response(function_responses=[
                    types.FunctionResponse(id=fc.id, name=fc.name, response=result)
                ])


async def stdin_loop(session, stop: asyncio.Event):
    while True:
        line = await asyncio.to_thread(input)
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if low in ("sair", "exit", "quit"):
            stop.set()
            return
        if low in ("tela", "screen"):
            path = await asyncio.to_thread(capture_screen)
            if path:
                with open(path, "rb") as f:
                    await session.send(input=types.Blob(
                        data=f.read(), mime_type="image/png"))
                print("[tela enviada ao agente]")
            else:
                print("[falha ao capturar a tela]")
            continue
        await session.send(input=line)


async def live_mode():
    try:
        import sounddevice as sd
    except OSError as e:
        print(f"ERRO: áudio indisponível ({e})")
        print("No Nobara, instale com: sudo dnf install portaudio-devel e recrie o venv.")
        raise SystemExit(1)

    async with open_mcp_sessions() as mcp_sessions:
        client = make_client()
        speech = None
        if cfg.voice:
            speech = types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=cfg.voice)))
        config_kwargs = {
            "response_modalities": ["AUDIO"],
            "system_instruction": SYSTEM,
            "tools": TOOLS_DECL,
        }
        if speech:
            config_kwargs["speech_config"] = speech
        config = types.LiveConnectConfig(**config_kwargs)

        async with client.aio.live.connect(model=cfg.model, config=config) as session:
            mic = sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=2048)
            speaker = sd.OutputStream(samplerate=24000, channels=1, dtype="int16")
            mic.start()
            speaker.start()
            print("Agente pronto. Fale no microfone ou digite:")
            print("  tela = enviar screenshot agora | sair = encerrar\n")
            stop = asyncio.Event()
            tasks = [
                asyncio.create_task(mic_loop(session, mic)),
                asyncio.create_task(receive_loop(session, speaker, mcp_sessions)),
                asyncio.create_task(stdin_loop(session, stop)),
            ]
            try:
                await stop.wait()
            finally:
                for t in tasks:
                    t.cancel()
                mic.stop()
                speaker.stop()


async def rodar_comando_tool(cmd: str) -> str:
    """Executa um comando shell no Linux e retorna a saída."""
    if not is_readonly(cmd) and cfg.confirm_dangerous and not await ask_confirmation(cmd):
        return "Comando negado pelo usuário."
    return json.dumps(await asyncio.to_thread(handle_shell, cmd))


async def text_mode():
    async with open_mcp_sessions() as mcp_sessions:
        client = make_client()
        chat = client.aio.chats.create(
            model=cfg.text_model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                tools=[rodar_comando_tool, *mcp_sessions],
            ),
        )
        print("Modo texto. 'tela' anexa screenshot à próxima mensagem | 'sair' encerra.\n")
        pending_image = None
        while True:
            q = (await asyncio.to_thread(input, "você> ")).strip()
            if q.lower() in ("sair", "exit", "quit"):
                break
            if q.lower() == "tela":
                path = await asyncio.to_thread(capture_screen)
                if path:
                    pending_image = path
                    print("[screenshot será anexado à próxima mensagem]")
                else:
                    print("[falha ao capturar a tela]")
                continue
            if not q:
                continue
            parts = []
            if pending_image:
                with open(pending_image, "rb") as f:
                    parts.append(types.Part.from_bytes(
                        data=f.read(), mime_type="image/png"))
                pending_image = None
            parts.append(types.Part.from_text(text=q))
            res = await chat.send_message(parts)
            print(f"agente> {res.text or '(sem resposta de texto)'}\n")

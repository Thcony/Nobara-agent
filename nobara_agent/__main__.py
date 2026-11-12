import argparse
import asyncio

from .agent import live_mode, text_mode
from .config import cfg


def main():
    parser = argparse.ArgumentParser(description="Agente Nobara — voz + visão de tela")
    parser.add_argument("--texto", action="store_true",
                        help="modo texto, sem microfone (útil para testar)")
    args = parser.parse_args()

    if not cfg.api_key or "cole-sua-chave" in cfg.api_key:
        print("ERRO: GEMINI_API_KEY não configurada.")
        print("Edite o arquivo .env na pasta do projeto e cole sua chave do Google AI Studio.")
        raise SystemExit(1)

    try:
        asyncio.run(text_mode() if args.texto else live_mode())
    except KeyboardInterrupt:
        print("\nAté logo!")


if __name__ == "__main__":
    main()

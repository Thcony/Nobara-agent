import argparse
import asyncio


def main():
    parser = argparse.ArgumentParser(description="Agente Nobara — voz + visão de tela")
    parser.add_argument("--texto", action="store_true",
                        help="abre direto no chat de texto")
    parser.add_argument("--voz", action="store_true",
                        help="abre direto no chat de voz")
    parser.add_argument("--tempo-real", action="store_true",
                        help="modo Live API experimental (áudio contínuo)")
    args = parser.parse_args()

    try:
        if args.tempo_real:
            from .agent import live_mode
            asyncio.run(live_mode())
        elif args.texto:
            from .menu import text_chat
            asyncio.run(text_chat())
        elif args.voz:
            from .menu import voice_chat
            asyncio.run(voice_chat())
        else:
            from .menu import main_menu
            main_menu()
    except KeyboardInterrupt:
        print("\nAté logo!")


if __name__ == "__main__":
    main()

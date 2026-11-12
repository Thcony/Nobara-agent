import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model: str = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview")
    text_model: str = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.1-flash")
    voice: str = os.getenv("GEMINI_VOICE", "")
    confirm_dangerous: bool = os.getenv("CONFIRM_DANGEROUS", "1") == "1"


cfg = Config()

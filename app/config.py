import os
import re
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = field(default="", repr=False)
    service_api_key: str = field(default="", repr=False)
    model: str = "gemini-3.8-flash"
    max_image_bytes: int = 5 * 1024 * 1024
    max_request_bytes: int = 6 * 1024 * 1024
    timeout_seconds: float = 45.0

    @property
    def configured(self) -> bool:
        return bool(
            self.gemini_api_key.strip()
            and len(self.service_api_key) >= 32
            and re.fullmatch(r"[a-zA-Z0-9_.-]+", self.model)
        )


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        service_api_key=os.getenv("IA_SERVICE_API_KEY", "").strip(),
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip(),
    )

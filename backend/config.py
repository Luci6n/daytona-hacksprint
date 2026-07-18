from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ROOT_DIR / ".env.local"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    demo_mode: bool = True

    daytona_api_key: str | None = None
    daytona_api_url: str = "https://app.daytona.io/api"
    daytona_target: str = "us"
    moonshot_api_key: str | None = None
    kimi_base_url: str = "https://api.moonshot.ai/v1"
    kimi_model: str = "kimi-k2.6"
    nosana_api_key: str | None = None
    nosana_base_url: str = "https://dashboard.k8s.prd.nos.ci/api"
    nosana_tts_url: str | None = None
    nosana_tts_bearer_token: str | None = None
    tts_model: str = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
    tts_language: str = "English"
    tts_voice_description: str = (
        "Deep, smooth, mature American male voice with a low warm baritone. "
        "Confident, unhurried, luxurious, subtly flirtatious, playful, and "
        "indulgent, like a charming silver-fox handyman. Reassuring and "
        "authoritative during safety instructions. Natural and never cartoonish."
    )
    tts_timeout_seconds: float = 120
    oxylabs_username: str | None = None
    oxylabs_password: str | None = None
    oxylabs_ai_studio_api_key: str | None = None
    oxylabs_mode: Literal["residential_proxy", "web_scraper_api"] = (
        "web_scraper_api"
    )
    oxylabs_realtime_url: str = "https://realtime.oxylabs.io/v1/queries"
    oxylabs_proxy_url: str = "http://pr.oxylabs.io:7777"
    oxylabs_proxy_country: str = "US"
    doubleword_api_key: str | None = None
    doubleword_base_url: str = "https://api.doubleword.ai/v1"
    doubleword_model: str = "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8"
    aiand_api_key: str | None = None
    aiand_base_url: str | None = None
    aiand_model: str | None = "qwen/qwen3.6-27b"

    def provider_readiness(self) -> dict[str, bool]:
        return {
            "daytona": bool(self.daytona_api_key),
            "kimi": bool(self.moonshot_api_key),
            "nosana": bool(self.nosana_api_key),
            "nosanaTts": bool(self.nosana_tts_url),
            "oxylabs": bool(self.oxylabs_username and self.oxylabs_password),
            "doubleword": bool(self.doubleword_api_key),
            "aiand": bool(
                self.aiand_api_key and self.aiand_base_url and self.aiand_model
            ),
        }


settings = Settings()

"""환경변수·.env 로딩 및 검증 (설계 §5.3). python-dotenv으로 .env를 읽고, 없으면 무시한다."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_NVIDIA_MODELS_URL = "https://integrate.api.nvidia.com/v1/models"
DEFAULT_BUILD_MODELS_URL = "https://build.nvidia.com/models"
DEFAULT_THRESHOLD_DAYS = 7
DEFAULT_HEARTBEAT_DAYS = 30


@dataclass(frozen=True)
class Config:
    nvidia_models_url: str
    build_models_url: str
    countdown_threshold_days: int
    heartbeat_days: int
    enable_tier2: bool
    dry_run: bool
    telegram_bot_token: str | None
    telegram_chat_id: str | None


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip() == "1"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"환경변수 {name}이(가) 정수가 아닙니다: {raw!r}") from None


def load() -> Config:
    """환경변수(.env 포함)를 읽어 Config를 만든다. TELEGRAM_*은 알림 전송 시점(M4)에 검증한다."""
    load_dotenv()
    return Config(
        nvidia_models_url=os.environ.get("NVIDIA_MODELS_URL", DEFAULT_NVIDIA_MODELS_URL).strip(),
        build_models_url=os.environ.get("BUILD_MODELS_URL", DEFAULT_BUILD_MODELS_URL).strip(),
        countdown_threshold_days=_env_int("COUNTDOWN_THRESHOLD_DAYS", DEFAULT_THRESHOLD_DAYS),
        heartbeat_days=_env_int("HEARTBEAT_DAYS", DEFAULT_HEARTBEAT_DAYS),
        enable_tier2=_env_flag("ENABLE_TIER2", True),
        dry_run=_env_flag("DRY_RUN", False),
        telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None,
        telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip() or None,
    )

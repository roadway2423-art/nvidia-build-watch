"""Telegram sendMessage 클라이언트. devlog 수정 #2: 429 소진 시 예외, 빈 텍스트 가드."""

import time

import httpx

API_BASE = "https://api.telegram.org/bot"
CHUNK_LIMIT = 4000
DEFAULT_TIMEOUT = 20.0
RETRY_ATTEMPTS = 3


def split_message(text: str, limit: int = CHUNK_LIMIT) -> list[str]:
    """Telegram 한도(4096)보다 안전한 크기로 분할한다. 빈 텍스트는 빈 리스트(수정 #2 가드)."""
    if not text:
        return []
    return [text[i : i + limit] for i in range(0, len(text), limit)]


def send_message(
    text: str,
    *,
    token: str,
    chat_id: str,
    dry_run: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> int:
    """청크 단위로 전송하고 성공 청크 수를 반환한다. DRY_RUN이면 표준출력으로 출력한다."""
    chunks = split_message(text)
    if not chunks:
        return 0
    sent = 0
    for chunk in chunks:
        if dry_run:
            print(chunk)
            print("---")
            sent += 1
            continue
        for attempt in range(RETRY_ATTEMPTS):
            response = httpx.post(
                f"{API_BASE}{token}/sendMessage",
                data={"chat_id": chat_id, "text": chunk},
                timeout=timeout,
            )
            if response.status_code == 429:
                retry_after = int(response.json().get("parameters", {}).get("retry_after", 5))
                if attempt + 1 < RETRY_ATTEMPTS:
                    time.sleep(retry_after)
                    continue
                raise RuntimeError(f"Telegram 429 — 재시도 {RETRY_ATTEMPTS}회 소진")
            response.raise_for_status()
            sent += 1
            break
    return sent

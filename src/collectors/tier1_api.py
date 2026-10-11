"""Tier 1: integrate.api.nvidia.com/v1/models JSON 수집기 (타임아웃 20초, 429/5xx만 2회 재시도)."""

import time

import httpx

DEFAULT_MODELS_URL = "https://integrate.api.nvidia.com/v1/models"
_TIMEOUT = 20.0
_RETRIES = 2


def parse_models(data: object) -> dict[str, dict]:
    """/v1/models 응답을 {모델ID: 레코드}로 변환한다. 구조가 예상과 다르면 ValueError를 던진다."""
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise ValueError("예상과 다른 응답 구조: {\"data\": [ ... ]} 리스트가 없음")
    models: dict[str, dict] = {}
    for item in data["data"]:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        model_id = str(item["id"])
        models[model_id] = {
            "id": model_id,
            "owner": str(item.get("owned_by", "") or ""),
            "in_api_list": True,
        }
    return models


def fetch_models(
    url: str = DEFAULT_MODELS_URL,
    *,
    timeout: float = _TIMEOUT,
    retries: int = _RETRIES,
) -> dict:
    """GET 결과 {"ok", "error", "models"}를 반환. 예외 발생 대신 오류를 담는다(부분 실패 허용)."""
    for attempt in range(retries + 1):
        try:
            response = httpx.get(url, timeout=timeout)
        except httpx.TransportError as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}", "models": {}}

        if response.status_code == 429 or response.status_code >= 500:
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            error = f"HTTP {response.status_code} (재시도 {retries}회 소진)"
            return {"ok": False, "error": error, "models": {}}
        if not response.is_success:
            return {"ok": False, "error": f"HTTP {response.status_code}", "models": {}}
        try:
            models = parse_models(response.json())
        except ValueError as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}", "models": {}}
        return {"ok": True, "error": None, "models": models}
    return {"ok": False, "error": "재시도 소진", "models": {}}

"""변경 감지 엔진 (설계 §6 + devlog 수정 #3·#4)."""

from datetime import date


def detect(
    prev: dict,
    new: dict,
    *,
    threshold_days: int = 7,
    today: str | None = None,
) -> list[dict]:
    """(이전 상태, 새 상태)를 비교해 이벤트 리스트를 반환한다.

    - 수정 #3: 새 상태가 tier1 실패이거나 in_api_list=true 모델이 0건이면 빈 결과(오탐 방지).
    - 수정 #4: API 등장은 new_model, free_badge 전환은 new_free로 분리 판정한다.
    - 첫 실행(이전 상태에 모델 없음)은 기준선 수집이므로 이벤트를 만들지 않는다.
    - 카운트다운은 임계값 이하인 날 매일 발생하되 last_notified로 같은 날 중복을 막는다.
    """
    today = today or date.today().isoformat()
    prev_models = prev.get("models", {})
    new_models = new.get("models", {})

    if not new.get("tier1_ok"):
        return []
    if not any(m.get("in_api_list") for m in new_models.values()):
        return []
    if not prev_models:
        return []

    last_countdown = new.get("last_notified", {}).get("countdown", {})
    events: list[dict] = []

    for model_id in sorted(set(prev_models) | set(new_models)):
        p = prev_models.get(model_id, {})
        n = new_models.get(model_id, {})
        p_api = bool(p.get("in_api_list"))
        n_api = bool(n.get("in_api_list"))
        p_free = p.get("free_badge")
        n_free = n.get("free_badge")

        if n_api and not p_api:
            events.append({"type": "new_model", "model_id": model_id})
        if p_api and not n_api:
            events.append({"type": "removed", "model_id": model_id})
        if p and p_free is not True and n_free is True:
            events.append({"type": "new_free", "model_id": model_id})
        if p_free is True and n_free is False:
            events.append({"type": "free_to_paid", "model_id": model_id})

        deadline_new_fired = False
        if p and p.get("deadline") is None and n.get("deadline") is not None:
            events.append(
                {"type": "deadline_new", "model_id": model_id, "deadline": n["deadline"]}
            )
            deadline_new_fired = True

        days_left = n.get("days_left")
        if (
            days_left is not None
            and 0 <= days_left <= threshold_days
            and not deadline_new_fired
            and last_countdown.get(model_id) != today
        ):
            events.append({"type": "countdown", "model_id": model_id, "days_left": days_left})

    return events


def apply_last_notified(state: dict, events: list[dict], *, today: str | None = None) -> dict:
    """카운트다운 이벤트를 오늘 알림 처리한다. 알림 전송 성공 후에 호출한다."""
    today = today or date.today().isoformat()
    countdown = state.setdefault("last_notified", {}).setdefault("countdown", {})
    for event in events:
        if event.get("type") == "countdown":
            countdown[event["model_id"]] = today
    return state

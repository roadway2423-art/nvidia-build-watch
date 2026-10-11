"""Tier1/Tier2 결과를 모델 ID 기준으로 병합해 새 state를 만든다 (설계 §5.1, §5.2)."""

from datetime import date, datetime

from .store import SCHEMA_VERSION


def build_state(
    prev: dict,
    tier1: dict,
    tier2: dict | None = None,
    *,
    today: str | None = None,
    now: datetime | None = None,
) -> dict:
    """prev와 수집 결과를 병합한다. first_seen 유지, 미검출 모델은 in_api_list=false로 남는다.

    관측 규칙: Tier 2가 오늘 본 모델은 오늘 값을, 못 본 모델은 prev 값을 유지한다(최신 관측 승리).
    days_left가 없으면 deadline에서 재계산한다 — Tier 2 결함 시 재알림/오판을 방지한다.
    """
    today = today or date.today().isoformat()
    now = now or datetime.now().astimezone()

    t1 = tier1.get("models", {}) if tier1 else {}
    t2 = tier2.get("models", {}) if tier2 else {}
    old = prev.get("models", {})

    models: dict[str, dict] = {}
    for model_id in sorted(set(t1) | set(t2) | set(old)):
        prev_rec = old.get(model_id, {})
        t1_rec = t1.get(model_id)
        seen_t2 = model_id in t2
        source = t2[model_id] if seen_t2 else prev_rec

        deadline = source.get("deadline")
        days_left = source.get("days_left")
        if days_left is None and deadline:
            try:
                days_left = (date.fromisoformat(deadline) - date.fromisoformat(today)).days
            except ValueError:
                days_left = None

        models[model_id] = {
            "id": model_id,
            "owner": (t1_rec or prev_rec).get("owner", ""),
            "name": source.get("name"),
            "first_seen": prev_rec.get("first_seen") or today,
            "last_seen": today if (t1_rec or seen_t2) else prev_rec.get("last_seen"),
            "in_api_list": t1_rec is not None,
            "free_badge": source.get("free_badge"),
            "deadline": deadline,
            "deadline_source": source.get("deadline_source"),
            "days_left": days_left,
            "notes": list(source.get("notes", [])),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now.astimezone().isoformat(timespec="seconds"),
        "tier1_ok": bool(tier1 and tier1.get("ok")),
        "tier2_ok": bool(tier2 and tier2.get("ok")),
        "models": models,
        "last_notified": prev.get("last_notified", {}),
    }

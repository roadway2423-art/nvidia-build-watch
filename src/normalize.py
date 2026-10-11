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
    """prev와 수집 결과를 병합한다. first_seen 유지, 미검출 모델은 in_api_list=false로 남는다."""
    today = today or date.today().isoformat()
    now = now or datetime.now().astimezone()

    t1 = tier1.get("models", {}) if tier1 else {}
    t2 = tier2.get("models", {}) if tier2 else {}
    old = prev.get("models", {})

    models: dict[str, dict] = {}
    for model_id in sorted(set(t1) | set(t2) | set(old)):
        prev_rec = old.get(model_id, {})
        t1_rec = t1.get(model_id)
        t2_rec = t2.get(model_id, {})
        models[model_id] = {
            "id": model_id,
            "owner": (t1_rec or prev_rec).get("owner", ""),
            "name": t2_rec.get("name"),
            "first_seen": prev_rec.get("first_seen") or today,
            "last_seen": today if (t1_rec or t2_rec) else prev_rec.get("last_seen"),
            "in_api_list": t1_rec is not None,
            "free_badge": t2_rec.get("free_badge"),
            "deadline": t2_rec.get("deadline"),
            "deadline_source": t2_rec.get("deadline_source"),
            "days_left": t2_rec.get("days_left"),
            "notes": list(t2_rec.get("notes", [])),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now.astimezone().isoformat(timespec="seconds"),
        "tier1_ok": bool(tier1 and tier1.get("ok")),
        "tier2_ok": bool(tier2 and tier2.get("ok")),
        "models": models,
        "last_notified": prev.get("last_notified", {}),
    }

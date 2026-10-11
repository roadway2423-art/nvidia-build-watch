"""텔레그램 메시지 빌더 (설계 §7.2 고정 포맷)."""

from datetime import date

SECTION_ORDER = [
    ("신규", ("new_model", "new_free")),
    ("종료 예고", ("deadline_new", "countdown")),
    ("제거", ("removed",)),
    ("무료→유료", ("free_to_paid",)),
]
TYPE_TO_SECTION = {event_type: label for label, types in SECTION_ORDER for event_type in types}


def _line(event: dict, state: dict) -> str:
    model_id = event["model_id"]
    record = state.get("models", {}).get(model_id, {})
    event_type = event["type"]
    if event_type == "new_free":
        return f"• {model_id}  (무료 배지)"
    if event_type == "new_model":
        suffix = "  (무료 배지)" if record.get("free_badge") is True else ""
        return f"• {model_id}{suffix}"
    if event_type == "deadline_new":
        return f"• {model_id} — 종료일 {event['deadline']}"
    if event_type == "countdown":
        deadline = record.get("deadline") or "?"
        return f"• {model_id} — {event['days_left']}일 남음 ({deadline})"
    return f"• {model_id}"


def build(events: list[dict], state: dict, *, today: str | None = None) -> str:
    """§7.2 고정 포맷 메시지를 만든다. 이벤트가 없으면 '변경 없음' 상태 메시지를 반환한다."""
    today = today or date.today().isoformat()
    in_api = sum(1 for m in state.get("models", {}).values() if m.get("in_api_list"))
    tier2 = "정상" if state.get("tier2_ok") else "비활성/실패"
    header = f"🆕 NVIDIA Build 무료 엔드포인트 변경 ({today})"
    footer = f"총 {in_api}개 모델 / 변경 {len(events)}건 · Tier2 상태: {tier2}"

    grouped: dict[str, list[str]] = {}
    for event in events:
        label = TYPE_TO_SECTION[event["type"]]
        grouped.setdefault(label, []).append(_line(event, state))

    if not grouped:
        return f"{header}\n\n변경 없음\n\n{footer}"

    lines = [header, ""]
    for label, _ in SECTION_ORDER:
        items = grouped.pop(label, [])
        if not items:
            continue
        lines.append(f"[{label}] {len(items)}건")
        lines.extend(items)
        lines.append("")
    lines.append(footer)
    return "\n".join(lines)

"""메시지 빌더 테스트 — §7.2 포맷 스냅샷 + 빈 이벤트 + Tier2 상태 (네트워크 없음)."""

from src import message

TODAY = "2026-10-11"


def _state(models: dict, tier2: bool = True) -> dict:
    return {
        "schema_version": 1,
        "updated_at": f"{TODAY}T09:00:00+09:00",
        "tier1_ok": True,
        "tier2_ok": tier2,
        "models": models,
        "last_notified": {"countdown": {}},
    }


def test_format_snapshot():
    state = _state({
        "moonshotai/kimi-k2-instruct": {"in_api_list": True, "free_badge": True},
        "qwen/qwen3-coder-480b-a35b-instruct": {"in_api_list": True, "free_badge": None},
        "meta/llama-3.3-70b-instruct": {"in_api_list": True, "free_badge": True,
                                        "deadline": "2026-10-17"},
        "01-ai/yi-large": {"in_api_list": False, "free_badge": None},
    })
    events = [
        {"type": "new_model", "model_id": "moonshotai/kimi-k2-instruct"},
        {"type": "new_model", "model_id": "qwen/qwen3-coder-480b-a35b-instruct"},
        {"type": "new_free", "model_id": "writer/palmyra-med-70b"},
        {"type": "countdown", "model_id": "meta/llama-3.3-70b-instruct", "days_left": 6},
        {"type": "removed", "model_id": "01-ai/yi-large"},
        {"type": "free_to_paid", "model_id": "adept/fuyu-8b"},
    ]
    text = message.build(events, state, today=TODAY)
    assert text == (
        "🆕 NVIDIA Build 무료 엔드포인트 변경 (2026-10-11)\n"
        "\n"
        "[신규] 3건\n"
        "• moonshotai/kimi-k2-instruct  (무료 배지)\n"
        "• qwen/qwen3-coder-480b-a35b-instruct\n"
        "• writer/palmyra-med-70b  (무료 배지)\n"
        "\n"
        "[종료 예고] 1건\n"
        "• meta/llama-3.3-70b-instruct — 6일 남음 (2026-10-17)\n"
        "\n"
        "[제거] 1건\n"
        "• 01-ai/yi-large\n"
        "\n"
        "[무료→유료] 1건\n"
        "• adept/fuyu-8b\n"
        "\n"
        "총 3개 모델 / 변경 6건 · Tier2 상태: 정상"
    )


def test_empty_events_status_message():
    state = _state({"a/b": {"in_api_list": True, "free_badge": None}})
    text = message.build([], state, today=TODAY)
    assert text == (
        "🆕 NVIDIA Build 무료 엔드포인트 변경 (2026-10-11)\n"
        "\n"
        "변경 없음\n"
        "\n"
        "총 1개 모델 / 변경 0건 · Tier2 상태: 정상"
    )


def test_deadline_new_line_and_tier2_status():
    state = _state({"a/b": {"in_api_list": True}}, tier2=False)
    events = [{"type": "deadline_new", "model_id": "a/b", "deadline": "2026-10-25"}]
    text = message.build(events, state, today=TODAY)
    assert "[종료 예고] 1건" in text
    assert "• a/b — 종료일 2026-10-25" in text
    assert "Tier2 상태: 비활성/실패" in text

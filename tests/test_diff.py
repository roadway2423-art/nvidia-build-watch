"""diff 엔진 테스트 — §6 이벤트 규칙 + 수정 #3·#4 가드 (픽스처 기반, 네트워크 없음)."""

import json
from pathlib import Path

from src import diff

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = "2026-10-11"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _state(models: dict, **overrides) -> dict:
    state = {
        "schema_version": 1,
        "updated_at": "2026-10-11T09:00:12+09:00",
        "tier1_ok": True,
        "tier2_ok": False,
        "models": models,
        "last_notified": {"countdown": {}},
    }
    state.update(overrides)
    return state


def _rec(
    in_api: bool = True,
    free: object = None,
    deadline: str | None = None,
    days: int | None = None,
) -> dict:
    return {
        "id": "x/y",
        "owner": "x",
        "name": None,
        "first_seen": "2026-09-01",
        "last_seen": "2026-10-11",
        "in_api_list": in_api,
        "free_badge": free,
        "deadline": deadline,
        "deadline_source": None if deadline is None else "banner_text",
        "days_left": days,
        "notes": [],
    }


def test_fixture_scenario():
    events = diff.detect(
        _load("state_prev_sample.json"), _load("state_new_sample.json"), today=TODAY
    )
    assert events == [
        {"type": "removed", "model_id": "a/alpha"},
        {"type": "new_free", "model_id": "b/beta"},
        {"type": "countdown", "model_id": "c/gamma", "days_left": 7},
        {"type": "new_model", "model_id": "d/delta"},
    ]


def test_new_model_fires_on_api_list_transition():
    prev = _state({"a/b": _rec(in_api=False), "z/z": _rec()})
    new = _state({"a/b": _rec(), "z/z": _rec(), "c/d": _rec()})
    assert diff.detect(prev, new, today=TODAY) == [
        {"type": "new_model", "model_id": "a/b"},
        {"type": "new_model", "model_id": "c/d"},
    ]


def test_removed():
    prev = _state({"a/b": _rec(), "z/z": _rec()})
    new = _state({"a/b": _rec(in_api=False), "z/z": _rec()})
    assert diff.detect(prev, new, today=TODAY) == [{"type": "removed", "model_id": "a/b"}]


def test_new_free_requires_existing_prev_record():
    prev = _state({"a/b": _rec(free=False), "z/z": _rec()})
    new = _state({"a/b": _rec(free=True), "z/z": _rec()})
    assert diff.detect(prev, new, today=TODAY) == [{"type": "new_free", "model_id": "a/b"}]


def test_brand_new_model_gets_single_new_model_event():
    prev = _state({"z/z": _rec()})
    new = _state({"z/z": _rec(), "a/b": _rec(free=True)})
    assert diff.detect(prev, new, today=TODAY) == [{"type": "new_model", "model_id": "a/b"}]


def test_free_to_paid_requires_explicit_false():
    prev = _state({"a/b": _rec(free=True), "z/z": _rec()})
    to_false = _state({"a/b": _rec(free=False), "z/z": _rec()})
    assert diff.detect(prev, to_false, today=TODAY) == [
        {"type": "free_to_paid", "model_id": "a/b"}
    ]
    to_null = _state({"a/b": _rec(free=None), "z/z": _rec()})
    assert diff.detect(prev, to_null, today=TODAY) == []


def test_deadline_new_fires_for_existing_model():
    prev = _state({"a/b": _rec(), "z/z": _rec()})
    new = _state({"a/b": _rec(deadline="2026-10-25", days=14), "z/z": _rec()})
    assert diff.detect(prev, new, today=TODAY) == [
        {"type": "deadline_new", "model_id": "a/b", "deadline": "2026-10-25"}
    ]


def test_countdown_suppressed_when_deadline_new_fires():
    prev = _state({"a/b": _rec(), "z/z": _rec()})
    new = _state({"a/b": _rec(deadline="2026-10-15", days=4), "z/z": _rec()})
    assert diff.detect(prev, new, today=TODAY) == [
        {"type": "deadline_new", "model_id": "a/b", "deadline": "2026-10-15"}
    ]


def test_countdown_daily_and_dedup():
    prev = _state({"a/b": _rec(deadline="2026-10-16", days=6)})
    new = _state({"a/b": _rec(deadline="2026-10-16", days=5)})
    assert diff.detect(prev, new, today=TODAY) == [
        {"type": "countdown", "model_id": "a/b", "days_left": 5}
    ]

    already = _state(
        {"a/b": _rec(deadline="2026-10-16", days=6)},
        last_notified={"countdown": {"a/b": TODAY}},
    )
    already_new = _state(
        {"a/b": _rec(deadline="2026-10-16", days=5)},
        last_notified={"countdown": {"a/b": TODAY}},
    )
    assert diff.detect(already, already_new, today=TODAY) == []


def test_countdown_threshold_and_expired():
    above = diff.detect(
        _state({"a/b": _rec(deadline="2026-11-01", days=21)}),
        _state({"a/b": _rec(deadline="2026-10-31", days=20)}),
        today=TODAY,
    )
    assert above == []

    expired = diff.detect(
        _state({"a/b": _rec(deadline="2026-10-05", days=-6)}),
        _state({"a/b": _rec(deadline="2026-10-05", days=-6)}),
        today=TODAY,
    )
    assert expired == []


def test_new_model_with_low_days_left_fires_both():
    prev = _state({"z/z": _rec()})
    new = _state({"z/z": _rec(), "a/b": _rec(deadline="2026-10-14", days=3)})
    assert diff.detect(prev, new, today=TODAY) == [
        {"type": "new_model", "model_id": "a/b"},
        {"type": "countdown", "model_id": "a/b", "days_left": 3},
    ]


def test_guard_skips_when_tier1_failed():
    prev = _state({"a/b": _rec()})
    new = _state({"a/b": _rec(in_api=False)}, tier1_ok=False)
    assert diff.detect(prev, new, today=TODAY) == []


def test_guard_skips_when_no_in_api_models():
    prev = _state({"a/b": _rec()})
    new = _state({"a/b": _rec(in_api=False)})
    assert diff.detect(prev, new, today=TODAY) == []


def test_baseline_first_run_emits_nothing():
    prev = _state({})
    new = _state({"a/b": _rec(), "c/d": _rec()})
    assert diff.detect(prev, new, today=TODAY) == []


def test_apply_last_notified_marks_countdown_only():
    state = _state({"a/b": _rec()}, last_notified={"countdown": {}})
    events = [
        {"type": "new_model", "model_id": "z/z"},
        {"type": "countdown", "model_id": "a/b", "days_left": 5},
    ]
    diff.apply_last_notified(state, events, today=TODAY)
    assert state["last_notified"]["countdown"] == {"a/b": TODAY}

"""normalize 테스트 — 병합, first_seen 유지, 관측 보존, days_left 재계산."""

from src import normalize

TODAY = "2026-10-11"


def _tier1(model_ids: list[str]) -> dict:
    return {
        "ok": True,
        "error": None,
        "models": {
            mid: {"id": mid, "owner": mid.split("/")[0], "in_api_list": True} for mid in model_ids
        },
    }


def _tier2(model_id: str, **fields) -> dict:
    return {"ok": True, "error": None, "models": {model_id: fields}}


def _prev_ab() -> dict:
    return {
        "models": {"a/b": {"first_seen": "2026-09-01", "last_seen": "2026-10-10", "owner": "a"}}
    }


def test_first_run_creates_records():
    state = normalize.build_state({}, _tier1(["moonshotai/kimi-k2-instruct"]), today=TODAY)
    rec = state["models"]["moonshotai/kimi-k2-instruct"]
    assert rec["first_seen"] == TODAY
    assert rec["last_seen"] == TODAY
    assert rec["in_api_list"] is True
    assert rec["owner"] == "moonshotai"
    assert state["tier1_ok"] is True
    assert state["tier2_ok"] is False


def test_first_seen_is_preserved():
    state = normalize.build_state(_prev_ab(), _tier1(["a/b"]), today=TODAY)
    rec = state["models"]["a/b"]
    assert rec["first_seen"] == "2026-09-01"
    assert rec["last_seen"] == TODAY


def test_model_missing_today_stays_with_false():
    state = normalize.build_state(_prev_ab(), _tier1(["c/d"]), today=TODAY)
    gone = state["models"]["a/b"]
    assert gone["in_api_list"] is False
    assert gone["last_seen"] == "2026-10-10"
    assert "c/d" in state["models"]


def test_last_notified_carried_over():
    prev = {"last_notified": {"countdown": {"a/b": "2026-10-01"}}}
    state = normalize.build_state(prev, _tier1(["a/b"]), today=TODAY)
    assert state["last_notified"] == {"countdown": {"a/b": "2026-10-01"}}


def test_tier2_fields_merged():
    t2 = _tier2(
        "moonshotai/kimi-k2-instruct",
        name="Kimi K2 Instruct",
        free_badge=True,
        deadline="2026-10-25",
        deadline_source="banner_text",
        days_left=14,
    )
    state = normalize.build_state({}, _tier1(["moonshotai/kimi-k2-instruct"]), t2, today=TODAY)
    rec = state["models"]["moonshotai/kimi-k2-instruct"]
    assert rec["name"] == "Kimi K2 Instruct"
    assert rec["free_badge"] is True
    assert rec["deadline"] == "2026-10-25"
    assert rec["deadline_source"] == "banner_text"
    assert rec["days_left"] == 14
    assert state["tier2_ok"] is True


def test_prev_fields_preserved_when_tier2_blind():
    prev = {
        "models": {
            "a/b": {
                "first_seen": "2026-09-01",
                "last_seen": "2026-10-10",
                "owner": "a",
                "free_badge": True,
                "deadline": "2026-10-25",
                "deadline_source": "banner_text",
            }
        }
    }
    state = normalize.build_state(prev, _tier1(["a/b"]), None, today=TODAY)
    rec = state["models"]["a/b"]
    assert rec["free_badge"] is True
    assert rec["deadline"] == "2026-10-25"
    assert rec["days_left"] == 14


def test_days_left_recomputed_from_deadline():
    prev = {
        "models": {
            "a/b": {
                "first_seen": "2026-09-01",
                "last_seen": "2026-10-09",
                "owner": "a",
                "deadline": "2026-10-14",
            }
        }
    }
    state = normalize.build_state(prev, _tier1(["a/b"]), None, today=TODAY)
    assert state["models"]["a/b"]["days_left"] == 3

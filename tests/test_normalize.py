"""normalize 테스트 — 병합, first_seen 유지, 미검출 모델 in_api_list=false."""

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
    prev = _prev_ab()
    state = normalize.build_state(prev, _tier1(["a/b"]), today=TODAY)
    rec = state["models"]["a/b"]
    assert rec["first_seen"] == "2026-09-01"
    assert rec["last_seen"] == TODAY


def test_model_missing_today_stays_with_false():
    prev = _prev_ab()
    state = normalize.build_state(prev, _tier1(["c/d"]), today=TODAY)
    gone = state["models"]["a/b"]
    assert gone["in_api_list"] is False
    assert gone["last_seen"] == "2026-10-10"
    assert "c/d" in state["models"]


def test_last_notified_carried_over():
    prev = {"last_notified": {"countdown": {"a/b": "2026-10-01"}}}
    state = normalize.build_state(prev, _tier1(["a/b"]), today=TODAY)
    assert state["last_notified"] == {"countdown": {"a/b": "2026-10-01"}}

"""store(state.json 읽기/쓰기) 테스트."""

import pytest

from src import store


def test_load_missing_returns_default(tmp_path):
    state = store.load_state(tmp_path / "missing.json")
    assert state == store.default_state()


def test_roundtrip_and_no_tmp_left(tmp_path):
    path = tmp_path / "state.json"
    state = store.default_state()
    state["models"]["a/b"] = {"id": "a/b", "in_api_list": True}
    store.save_state(state, path)
    assert store.load_state(path) == state
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_corrupt_raises(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError):
        store.load_state(path)


def test_load_schema_mismatch_raises(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"schema_version": 99, "models": {}}', encoding="utf-8")
    with pytest.raises(ValueError):
        store.load_state(path)

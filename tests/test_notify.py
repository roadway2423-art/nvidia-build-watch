"""notify 순수 로직 테스트 — 분할·빈 텍스트 가드·429 소진 (네트워크 없음)."""

import pytest

from src import notify


def test_split_message_chunks():
    chunks = notify.split_message("x" * 9000)
    assert len(chunks) == 3
    assert chunks[0] == "x" * 4000
    assert chunks[1] == "x" * 4000
    assert chunks[2] == "x" * 1000


def test_split_message_short_text_single_chunk():
    assert notify.split_message("hello") == ["hello"]


def test_split_message_empty_returns_no_chunks():
    assert notify.split_message("") == []


def test_split_message_custom_limit():
    assert notify.split_message("abcdef", limit=2) == ["ab", "cd", "ef"]


def test_send_message_empty_guard(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("빈 텍스트에서는 httpx.post을 호출하면 안 된다")

    monkeypatch.setattr(notify.httpx, "post", fail)
    assert notify.send_message("", token="t", chat_id="c") == 0


def test_send_message_dry_run_prints(capsys):
    sent = notify.send_message("미리보기 텍스트", token="t", chat_id="c", dry_run=True)
    assert sent == 1
    assert "미리보기 텍스트" in capsys.readouterr().out


def test_send_message_raises_after_429_exhaustion(monkeypatch):
    class FakeResponse:
        status_code = 429

        def json(self):
            return {"parameters": {"retry_after": 0}}

    monkeypatch.setattr(notify.httpx, "post", lambda *a, **k: FakeResponse())
    monkeypatch.setattr(notify.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError):
        notify.send_message("text", token="t", chat_id="c")

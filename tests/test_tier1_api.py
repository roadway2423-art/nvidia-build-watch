"""Tier 1 수집기 파싱 테스트 (픽스처 기반 — 네트워크 없음)."""

import json
from pathlib import Path

import pytest

from src.collectors import tier1_api

FIXTURE = Path(__file__).parent / "fixtures" / "models_api_sample.json"


def _data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_parse_models_from_real_fixture():
    models = tier1_api.parse_models(_data())
    assert len(models) == 80


def test_parse_models_record_fields():
    models = tier1_api.parse_models(_data())
    assert models["01-ai/yi-large"] == {
        "id": "01-ai/yi-large",
        "owner": "01-ai",
        "in_api_list": True,
    }


@pytest.mark.parametrize("bad", [{}, {"data": "x"}, {"data": None}, []])
def test_parse_models_rejects_bad_structure(bad):
    with pytest.raises(ValueError):
        tier1_api.parse_models(bad)

"""data/state.json 읽기/쓰기 (스키마: 설계 §5.2)."""

import json
import os
from pathlib import Path

SCHEMA_VERSION = 1

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = ROOT / "data" / "state.json"


def default_state() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": None,
        "tier1_ok": None,
        "tier2_ok": None,
        "models": {},
        "last_notified": {},
    }


def load_state(path: Path = DEFAULT_STATE_PATH) -> dict:
    """state.json을 읽는다. 없으면 초기 상태, 손상·불일치는 예외(조용한 실패 금지)."""
    if not path.exists():
        return default_state()
    with path.open(encoding="utf-8") as f:
        state = json.load(f)
    if state.get("schema_version") != SCHEMA_VERSION:
        found = state.get("schema_version")
        raise ValueError(f"state.json schema_version 불일치: {found!r} (기대 {SCHEMA_VERSION})")
    return state


def save_state(state: dict, path: Path = DEFAULT_STATE_PATH) -> None:
    """임시파일에 쓴 뒤 원자적으로 치환해 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)

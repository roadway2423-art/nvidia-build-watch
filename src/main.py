"""오케스트레이션: 수집 → 정규화 → diff → 알림 → 저장. CLI: --collect-only, --force-notify."""

import argparse
import sys

from . import config, diff, message, normalize, notify, store
from .collectors import tier1_api


def _force_utf8_streams() -> None:
    """파이프/캡처 환경(UTF-8 소비자)에서 cp949 한글 출력이 깨지는 것을 방지한다."""
    for stream in (sys.stdout, sys.stderr):
        if stream is None or stream.isatty():
            continue
        if stream.encoding and stream.encoding.lower() != "utf-8":
            stream.reconfigure(encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NVIDIA Build 무료 엔드포인트 감시 봇")
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="수집 결과 요약만 출력하고 저장하지 않는다",
    )
    parser.add_argument(
        "--force-notify",
        action="store_true",
        help="변경이 없어도 상태 메시지를 만들어 전송한다",
    )
    return parser.parse_args(argv)


def _event_detail(event: dict) -> str:
    if event["type"] == "countdown":
        return f" — {event['days_left']}일 남음"
    if event["type"] == "deadline_new":
        return f" — 종료일 {event['deadline']}"
    return ""


def main(argv: list[str] | None = None) -> int:
    _force_utf8_streams()
    args = parse_args(argv)
    cfg = config.load()

    tier1 = tier1_api.fetch_models(cfg.nvidia_models_url)
    if not tier1["ok"]:
        print(f"[오류] Tier 1 수집 실패: {tier1['error']}", file=sys.stderr)
        print("[오류] state.json을 저장하지 않고 종료한다 (devlog 수정 #3 가드)", file=sys.stderr)
        return 1
    if not tier1["models"]:
        print("[오류] Tier 1 모델 0건 — 이상 응답으로 판단, 저장하지 않는다", file=sys.stderr)
        return 1
    print(f"[tier1] 모델 {len(tier1['models'])}개 수집 완료")

    if cfg.enable_tier2:
        print("[경고] Tier 2 렌더링은 M5에서 구현한다 — Tier 1만으로 진행", file=sys.stderr)

    if args.collect_only:
        return 0

    prev = store.load_state()
    new_state = normalize.build_state(prev, tier1)
    events = diff.detect(prev, new_state, threshold_days=cfg.countdown_threshold_days)
    if events:
        print(f"[diff] 변경 {len(events)}건 감지")
        for event in events:
            print(f"  [{event['type']}] {event['model_id']}{_event_detail(event)}")
    else:
        print("[diff] 변경 없음")

    if events or args.force_notify:
        text = message.build(events, new_state)
        if cfg.dry_run:
            print("[알림] DRY_RUN — 전송 대신 미리보기:")
            print(text)
        elif not (cfg.telegram_bot_token and cfg.telegram_chat_id):
            print("[오류] TELEGRAM_BOT_TOKEN/CHAT_ID 미설정 — 전송 불가", file=sys.stderr)
            print("[오류] DRY_RUN=1으로 미리보기하거나 .env을 채우세요", file=sys.stderr)
            return 1
        else:
            try:
                sent = notify.send_message(
                    text,
                    token=cfg.telegram_bot_token,
                    chat_id=cfg.telegram_chat_id,
                )
            except Exception as e:
                print(f"[오류] 텔레그램 전송 실패: {type(e).__name__}: {e}", file=sys.stderr)
                print("[오류] state.json 미저장 종료 — 다음 실행에서 재시도", file=sys.stderr)
                return 1
            print(f"[알림] 텔레그램 전송 완료 ({sent}청크)")
            diff.apply_last_notified(new_state, events)

    if cfg.dry_run:
        print("[정보] DRY_RUN — state.json을 저장하지 않고 종료한다")
        return 0

    store.save_state(new_state)
    print(f"[저장] state.json 갱신 완료: 모델 {len(new_state['models'])}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())

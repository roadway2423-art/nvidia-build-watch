# nvidia-build-watch

build.nvidia.com 무료 엔드포인트의 신규 등록·제거·무료 종료 카운트다운을 매일 1회 감시해
텔레그램으로 알리는 봇.

- 설계: [docs/design.md](docs/design.md) (2026-10-11 원본 스냅샷)
- 변경 기록: [docs/devlog.md](docs/devlog.md) — 무엇을 어디에 어떻게 고쳤는지 전부 기록
- 원본 설계서(저장소 밖): `../nvidia-build-watch-design.md`

## 구조

```
nvidia-build-watch/
├─ .github/workflows/watch.yml   # 매일 09:00 KST(00:00 UTC) 예약 실행
├─ .env.example                  # 환경변수 템플릿 (복사해서 .env로 사용)
├─ requirements.txt              # 런타임 의존성
├─ requirements-dev.txt          # 개발 의존성 (pytest, ruff)
├─ pyproject.toml                # ruff / pytest 설정
├─ data/state.json               # 직전 스냅샷 (매 실행 후 커밋)
├─ docs/                         # 설계 스냅샷(design.md) + 변경 기록(devlog.md)
├─ logs/                         # 실행 로그 (logs/*.log는 git 제외)
├─ src/
│  ├─ main.py                    # 오케스트레이션 (수집→비교→알림→저장)
│  ├─ config.py                  # 환경변수 로딩·검증
│  ├─ collectors/
│  │  ├─ tier1_api.py            # /v1/models JSON 수집
│  │  └─ tier2_render.py         # Playwright 렌더링·배너 추출
│  ├─ normalize.py               # 두 소스 병합 → 표준 레코드
│  ├─ diff.py                    # 변경 감지 규칙
│  ├─ message.py                 # 텔레그램 메시지 빌더
│  ├─ notify.py                  # Telegram Bot API 클라이언트
│  └─ store.py                   # state.json 읽기/쓰기
└─ tests/                        # 픽스처 기반 테스트 (네트워크 불필요)
```

## 셋업 (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1     # 정책 오류 시: Set-ExecutionPolicy -Scope Process RemoteSigned
pip install -r requirements-dev.txt
playwright install chromium
Copy-Item .env.example .env      # 값을 채운다 (토큰은 절대 커밋 금지)
```

Linux/macOS:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && playwright install chromium
cp .env.example .env
```

## 실행 / 테스트 (PowerShell)

```powershell
pytest -q                                             # 픽스처 기반 로직 테스트
$env:DRY_RUN="1"; python -m src.main --collect-only  # 수집만 확인 (저장·알림 없음)
$env:DRY_RUN="1"; python -m src.main --force-notify   # 메시지 미리보기 (M3에서 추가)
python -m src.main                                    # 실행 (텔레그램 전송은 M4부터)
```

## 롤백 (git)

```powershell
git log --oneline          # 이력 확인
git revert <hash>          # 되돌리기 (기록 유지)
git reset --hard <hash>    # 이후 커밋 전부 삭제 (주의)
```

## GitHub Actions 주의사항

- `schedule`은 저장소 **기본 브랜치**에 있는 워크플로에서만 동작한다.
- 정각(00:00 UTC) cron은 수 분~수십 분 지연될 수 있다. "09:00 KST"는 목표치.
- 60일간 저장소 활동이 없으면 예약 워크플로가 자동 비활성화된다 → 매일 `state.json` 커밋으로 방지됨.
- CI 기본값은 `ENABLE_TIER2=0`(Tier 1 전용). M5 완료 후 워크플로 내 주석 참고.
- 저장소 secrets에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 등록 필요.

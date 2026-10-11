# 개발 로그 (devlog)

> **기록 규칙**: 코드·설계·설정을 고치면 날짜 섹션 아래에 **어디에(파일/모듈) → 무엇을 → 어떻게**를 기록한다.
> 설계와 달라지는 모든 결정이 이 파일에 남아야 한다. 원본 설계서: `docs/design.md`(2026-10-11 스냅샷).

---

## 2026-10-11 — 프로젝트 스캐폴드 + 설계 검토 오류 11건 반영

### 배경
설계 검토에서 design.md의 오류/빈틈 11건을 발견했다. 7건은 이번 스캐폴드에 즉시 반영했고,
로직 4건은 구현 단계(M2~M5)에서 적용하도록 아래 체크리스트로 남겼다.
실측(§3)은 검토 시점에 재호출로 재검증했다: `/v1/models` 200·80개·키 불필요 OK,
`/models` HTML 474,751B·"free" 0건·모델 데이터 없음 — 설계 근거는 그대로 유효.

### 즉시 반영 완료

| # | 설계서의 문제 | 어디에 | 어떻게 고쳤는지 |
|---|---|---|---|
| 5 | `ENABLE_TIER2`를 §8 각주에서 사용하지만 §5.3 환경변수 표에 없음. heartbeat 주기도 미정의 | `.env.example` | `ENABLE_TIER2`(기본 1), `HEARTBEAT_DAYS`(기본 30)를 환경변수로 추가·주석 문서화 |
| 6 | 워크플로 YAML에 Playwright 설치 단계가 없어 CI에서 Tier 2가 매일 실패 | `.github/workflows/watch.yml` | CI 기본 `ENABLE_TIER2=0`(Tier 1 전용)으로 설정하고, M5 완료 후 켜는 방법을 YAML 주석에 명시 |
| 7 | schedule의 기본 브랜치 전용 동작·정각 지연 미언급 | `README.md` | GitHub Actions 주의사항 섹션에 명시 |
| 8 | Windows에서 `DRY_RUN=1 python ...`(bash 문법) 동작 안 함 | `README.md` | PowerShell 문법 `$env:DRY_RUN="1"; python -m src.main` 병기 |
| 9 | `.env.example`은 있지만 .env를 읽을 방법(python-dotenv)이 의존성에 없음 | `requirements.txt`, `src/config.py`(스텁) | `python-dotenv` 추가 — M1에서 `config.py`가 `load_dotenv()`로 로드(파일 없으면 무시) |
| 10 | requirements.txt에 pytest(런타임 불필요) 포함, ruff 누락 — "의존성 3개" 불일치 | `requirements.txt`, `requirements-dev.txt` | 런타임(httpx, playwright, python-dotenv)과 개발(pytest, ruff) 분리 |
| 11 | §12 "render_js 계열"은 실존하지 않는 용어 | 이 문서에서 정정 | 의미는 "Playwright 헤드리스 렌더링" — 이후 문서·코드에서 이 용어를 쓰지 않는다 |

### 구현 단계에서 적용할 수정 (완료 시 ☐ → ☑)

| # | 설계서의 문제 | 적용 위치(예정) | 어떻게 고칠 것인가 | 상태 |
|---|---|---|---|---|
| 1 | §6 `parse_countdown` 4번째 패턴(`available until <날짜>`)의 캡처 그룹이 날짜 문자열이라 `isdigit()`에서 항상 버려짐 — 작동하지 않는 죽은 코드. `from datetime import date`도 미사용 | `src/collectors/tier2_render.py` (M5) | 날짜 패턴은 별도 분기에서 `datetime.strptime`으로 파싱 후 `(deadline - today).days`를 반환 | ☐ |
| 2 | Appendix B: (1) 429 재시도 3회 소진 후 조용히 종료(알림 유실) (2) 빈 텍스트일 때 `or [""]`가 빈 메시지를 그대로 전송(400 에러) | `src/notify.py` (M4) | 재시도 소진 시 예외 발생(실패를 드러냄), 빈 텍스트는 진입부에서 가드(전송 스킵) | ☐ |
| 3 | Tier 1 실패·빈 응답 시 diff 엔진이 "전 모델 제거"로 오판 | `src/diff.py` (M2) | `tier1_ok=false`이거나 수집된 모델이 0건이면 diff를 스킵하고 오류 알림만 보낸다 | ☐ |
| 4 | §6 "신규 무료 모델"을 `in_api_list` false→true로 판정 — §3.1("이 응답에 무료 여부가 없다")과 자기모순 | `src/diff.py` (M2) | 이벤트 명칭을 "신규 모델 등록"으로 변경. "신규 무료"는 `free_badge` false→true로만 판정 | ☐ |

### 이 커밋에서 만든 것
- 폴더 구조 전체 (설계 §9 + `docs/`, `logs/`)
- 설정: `.gitignore`, `.env.example`, `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `.github/workflows/watch.yml`, `README.md`
- 모듈 스텁: `src/*`, `tests/*` (로직은 M1부터 — design.md §10.2 프롬프트 순서대로)
- `data/state.json` 초기 스키마 (§5.2)
- 픽스처: `tests/fixtures/models_api_sample.json` — **당일 실제 `/v1/models` 응답(80개) 그대로**
- 픽스처: `tests/fixtures/rendered_cards_sample.html` — 합성 샘플, M5에서 실제 렌더링 결과로 교체

### 환경 특이사항
- 개발 머신에 git이 설치되어 있지 않았음 → Git for Windows 2.55를 winget으로 설치했다.
- 신규 설치라 커밋 작성자 정보가 없어 저장소 로컬에 임시로 `user <user@local>` 설정.
  실명으로 바꾸려면: `git config user.name "이름"`, `git config user.email "메일"` (이 저장소에만 적용됨).
- Python은 PATH의 `python`이 아니라 `py` 런처 기반(Python 3.14.7) → README 셋업 명령은 `py` 사용.

### 다음 단계
M1 — Tier 1 수집기 + 상태 저장 (design.md §10.2 1단계 프롬프트 그대로 진행)

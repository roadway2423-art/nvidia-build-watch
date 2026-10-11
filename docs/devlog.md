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
| 2 | Appendix B: (1) 429 재시도 3회 소진 후 조용히 종료(알림 유실) (2) 빈 텍스트일 때 `or [""]`가 빈 메시지를 그대로 전송(400 에러) | `src/notify.py` (M3) | 재시도 소진 시 예외 발생(실패를 드러냄), 빈 텍스트는 진입부에서 가드(전송 스킵) | ☑ M3 적용 |
| 3 | Tier 1 실패·빈 응답 시 diff 엔진이 "전 모델 제거"로 오판 | `src/main.py`(M1 1차 방어), `src/diff.py`(M2 이중 방어) | `tier1_ok=false`이거나 수집된 모델이 0건이면 diff를 스킵하고 오류 알림만 보낸다 | ☑ 완료(M1+M2) |
| 4 | §6 "신규 무료 모델"을 `in_api_list` false→true로 판정 — §3.1("이 응답에 무료 여부가 없다")과 자기모순 | `src/diff.py` (M2) | 이벤트 명칭을 "신규 모델 등록"으로 변경. "신규 무료"는 `free_badge` false→true로만 판정 | ☑ M2 적용 |

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

---

## 2026-10-11 — M1: Tier 1 수집기 + 상태 저장 구현

### 구현한 것
| 파일 | 내용 |
|---|---|
| `src/config.py` | .env/환경변수 로딩·검증(python-dotenv). TELEGRAM_*은 알림 전송 시점(M4)에만 필요하므로 load 시 필수 아님 — 수정 #9 적용 완료 |
| `src/collectors/tier1_api.py` | GET /v1/models, 타임아웃 20초, 429/5xx만 2회 재시도(1s→2s), 응답 구조 검증, 예외 대신 결과 객체 반환 |
| `src/store.py` | state.json 읽기/쓰기 — 임시파일→원자 치환 저장, schema_version 검증, 손상 시 예외 |
| `src/normalize.py` | Tier1(+Tier2 예정) 병합 → 표준 레코드. first_seen 유지, 미검출 모델 in_api_list=false 유지 |
| `src/main.py` | 수집→정규화→저장 파이프라인, `--collect-only`, 종료코드 1=수집 실패 |

### 내린 결정 (설계에 명시되지 않은 것)
1. **Tier 1 실패·모델 0건이면 state.json을 저장하지 않는다** — 수정 #3의 1차 방어.
   실패한 날의 빈 목록이 스냅샷을 오염시켜 다음 날 오판을 유발하는 것을 원천 차단한다.
   diff 레벨 가드는 M2에서 이중 방어로 추가한다.
2. `--collect-only`는 저장도 하지 않는 순수 확인 모드. `--force-notify` 플래그는 M3(메시지 빌더)에서 추가.
3. 오류의 텔레그램 전송은 M4부터 — M1에서는 stderr + 종료코드로 알린다.
4. ENABLE_TIER2 기본값은 1(설계)이지만 Tier 2 미구현(M5) — 경고 출력 후 Tier 1만으로 진행(부분 실패 허용).
5. **콘솔 인코딩 방어**(main.py `_force_utf8_streams`): 개발 머신이 cp949(한글 Windows)인데
   Kilo/CI 캡처 환경은 UTF-8로 디코딩해 한글 로그가 깨졌다. 파이프(비-tty) 스트림만 UTF-8로
   재구성하고 대화형 콘솔은 건드리지 않는다.

### 구조 추가 (§9 대비)
- `tests/test_tier1_api.py`, `tests/test_store.py` — 파싱·저장 회귀 테스트 (픽스처 기반, 네트워크 없음)

### 검증 결과
- `pytest`: 16개 전부 통과 / `ruff check .`: 클린
- 실측: `--collect-only`로 80개 수집 확인, 정상 실행으로 state.json에 80개 레코드 저장 확인
  (tier1_ok=true, updated_at KST) → **M1 완료 기준 충족**
- 개발 머신 venv: Python 3.14.7. `playwright install chromium`(브라우저)은 M5 전까지 불필요하여 미실행.

### 다음 단계
M2 — diff 엔진 + 테스트 (수정 #3 이중 방어, #4 이벤트 명칭 정정 포함)

---

## 2026-10-11 — M2: diff 엔진 + normalize 관측 보존 규칙

### 구현한 것
| 파일 | 내용 |
|---|---|
| `src/diff.py` | `detect()` — §6 이벤트 감지(수정 #4 반영), `apply_last_notified()` — 카운트다운 중복 알림 갱신(전송 성공 후 호출 규약) |
| `src/normalize.py` | 관측 보존 규칙 — Tier 2가 오늘 못 본 모델은 prev의 free_badge·deadline 유지, days_left는 deadline에서 자동 재계산 |
| `src/main.py` | diff 연결 — 변경 시 이벤트 출력 후 state 저장 |
| `tests/test_diff.py` | 15개 케이스 (픽스처 시나리오 + 전이별 단위 + 가드 3종 + dedup) |
| `tests/fixtures/state_prev_sample.json`·`state_new_sample.json` | 상태 스냅샷 픽스처 (제거/신규 무료/카운트다운 진입/신규 4종 시나리오) |

### 이벤트 6종 (수정 #4 — 설계의 "신규 무료 모델" 1행을 2종으로 분리)
`new_model`(신규 모델 등록: in_api_list 전이) · `new_free`(free_badge→true) · `removed` ·
`deadline_new`(deadline 첫 등장) · `countdown`(days_left ≤ 임계값, 매일) · `free_to_paid`

### 내린 결정
1. 브랜드뉴 모델은 `new_model` 하나로 — `new_free`/`deadline_new`는 prev 레코드가 있을 때만 발사 (중복 억제)
2. `free_to_paid`는 true→명시적 false만 판정. true→null(관측 없음)은 무시 — Tier 2 실패일 오판 방지
3. `deadline_new`가 발사한 실행일엔 `countdown` 생략(중복). 다음 날부터 매일 알림
4. days_left < 0(이미 만료)는 countdown 미발사 — 제거 이벤트가 뒤따름
5. 첫 실행(이전 상태에 모델 0건)은 기준선 수집 — 이벤트 없음 (첫 알림이 80건 스팸 되는 것 방지)
6. 수정 #3 이중 방어 완료: diff가 `tier1_ok=false` 또는 in_api 모델 0건이면 빈 결과.
   "잔여 전원 동시 제거" 같은 극단 케이스도 이상 응답으로 취급해 스킵하는 트레이드오프
7. normalize 관측 보존: Tier 2 결함으로 하루 배지를 못 읽어도 유료 전환/deadline 재등장 오판 없음 (M5 대비)
8. dedup 확인 경로: detect는 새 상태의 last_notified를 읽는다 — normalize가 prev의 last_notified를
   그대로 전달하므로 "전송 → apply_last_notified → 저장 → 다음 실행" 순서로 같은 날 중복이 차단된다

### 검증 결과
- `pytest`: 33개 전부 통과 / `ruff check .`: 클린
- 실측: 연속 2회 실행 → 모두 "변경 없음"(이벤트 0건) — 기준선 대비 diff 정상 동작 확인

### 다음 단계
M3 — 메시지 빌더 + 텔레그램 전송 (`--force-notify` 추가, apply_last_notified 연결)

---

## 2026-10-11 — M3: 메시지 빌더 + 텔레그램 전송 (수정 #2 적용 완료)

### 구현한 것
| 파일 | 내용 |
|---|---|
| `src/message.py` | §7.2 고정 포맷 빌더 — 신규/종료 예고/제거/무료→유료 순서, "(무료 배지)" 주석, 이벤트 없으면 '변경 없음' 상태 메시지 |
| `src/notify.py` | sendMessage 클라이언트 — 4000자 분할, 429 retry_after 대기 후 3회 재시도, 소진 시 RuntimeError(수정 #2-1), 빈 텍스트 가드(수정 #2-2), DRY_RUN 표준출력 전환 |
| `src/main.py` | 알림 연결 — detect → build → send → apply_last_notified → save (§4 순서). `--force-notify` 추가 |
| `tests/test_message.py`·`tests/test_notify.py` | 포맷 스냅샷 3건 + 분할·가드·429 소진 7건 (네트워크 없음, monkeypatch) |

### 내린 결정
1. **전송 실패 시 state 미저장** — 다음 실행에서 같은 이벤트가 재감지·재전송된다(at-least-once).
   `apply_last_notified`는 전송 성공 후에만 호출한다 (M2 규약 준수)
2. **DRY_RUN은 부작용 0** — 미리보기만 하고 state.json을 저장하지 않는다.
   미리보기 실행이 실제 이벤트를 삼켜 알림을 유실시키는 사고를 원천 방지
3. TELEGRAM_* 미설정 + 전송 필요 → 종료코드 1 (조용한 실패 금지). DRY_RUN이면 토큰 없이 미리보기
4. 푸터 "총 N개 모델"은 in_api_list=true 개수 기준 — 제거 이력이 카운트를 부풀리지 않게
5. new_model의 "(무료 배지)" 주석은 새 상태의 free_badge=true일 때만 표시 (§7.2 예시 형식 준수)

### 검증 결과
- `pytest`: 42개 전부 통과 / `ruff check .`: 클린
- DRY_RUN `--force-notify` 미리보기: §7.2 포맷 정확히 일치 확인
- **실전 테스트**: state.json에서 `z-ai/glm-5.3`을 의도 삭제 후 실제 실행 →
  `[new_model]` 이벤트 감지 → 실제 텔레그램 전송(1청크) → state가 80개로 자동 복구됨.
  텔레그램 수신 메시지가 §7.2 포맷과 일치 → **M3 완료 기준 충족**

### 다음 단계
M4 — GitHub Actions 연결 (워크플로 수동 실행 → state 커밋·push 확인)

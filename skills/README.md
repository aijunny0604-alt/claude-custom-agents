# J-AGENTS Skills v1.8.0

Claude Code 전용 **26개 커스텀 QA/보안/테스트/검증/기획/디자인 에이전트** 모음입니다.
**시나리오 매트릭스 + 영향도 맵 + 체크리스트** 기반 PDCA 사이클로 자동 반복 개선합니다.

> **v1.8.0 신규**: `/끝판왕` (`/mega-audit`) — 5-Phase 오케스트레이터로 전체 에이전트를 한 번에 자동 실행 + 자동 수정 + 재검증.

---

## 한 줄 설치 (플러그인 방식 - 권장)

```bash
curl -sSL https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/install.sh | bash
```

설치 후 Claude Code 재시작하면 자동 적용됩니다. `autoUpdate: true`라 이후 업데이트는 세션 시작 시 자동 반영됩니다.

---

## v1.8.0 핵심 강화 사항

모든 에이전트에 공통 적용 (기존 v1.6.0 항목 + v1.8.0 신규):

1. **영향도 맵 (Impact Map)** — 점검 전 코드 연쇄 관계 시각화로 누락 방지
2. **시나리오 매트릭스 (3축)** — 변수 조합으로 테스트 시나리오 자동 도출
3. **마스터 체크리스트** — 실행 가능한 체크 항목 + 커버리지 추적
4. **교차 검증 (Cross-Validation)** — 팀 간 결과 대조로 모순/누락 탐지
5. **영향도 역추적** — FAIL 시 역방향 파급 범위 확인
6. **Playwright 직접 실행** — 서브에이전트 불가, 메인 대화에서 실 브라우저 검증
7. **★ 끝판왕 오케스트레이터 (v1.8.0)** — `/끝판왕` 한 번으로 5-Phase 전체 자동 실행
8. **★ 파싱 안전성 점검 (v1.8.0)** — JSON.parse, `new Date(string)`, parseInt NaN 등 P1~P13 패턴 grep 전수조사 + 런타임 콘솔 에러 분류
9. **★ 메뉴/연관성 자동 검증 (v1.8.0)** — 사이드바/네비/버튼 자동 발견 → Playwright 클릭 시뮬레이션 → 영향도 맵의 cascade 효과까지 검증

---

## 에이전트 목록 (26개)

### ★ 끝판왕 (전체 오케스트레이터)

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/끝판왕` (`/mega-audit`) | O | 5-Phase | 정적+E2E+DB+UX+보안 가중평균 + 자동 수정 + 재검증 (max 5회). 메뉴/파싱/연관성 일괄 |

### 기능 검증 & 테스트

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/flow-check` | O | 6팀 | 전체 플로우 엔드투엔드 검증 |
| `/full-test` | O | 4팀 | 대규모 통합 테스트 (로컬+프로덕션) |
| `/change-verify` | O | 4팀 | 변경사항 정밀 검증 (수정 후 필수) |
| `/ux-flow` | O | 2팀 | UX 시나리오 E2E Playwright 검증 |
| `/playwright-report` | O | 1인 | Playwright 검증 + PDCA 보고서 + 제안/건의/의견 |
| `/test-guide` | O | 1인 | 수동 테스트 가이드 (이슈 종합 + 시나리오 + Step-by-Step 점검법) |

### 보안

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/security-team` | O | 3팀 | OWASP Top 10 보안 풀 스캔 |
| `/security-quick` | O | 1인 | 경량 보안 점검 (5분) |

### UI/UX & 디자인

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/design-sense` | O | 3팀 | 감각적 디자인 감성 점검 (375/768/1440 3해상도) + 2026 트렌드 |
| `/design-review` | O | 3팀 | 구조/디자인 리뷰 + 아이디어 도출 |
| `/mobile-audit` | O | 4팀 | 모바일 UI/UX 최적화 점검 |
| `/responsive-check` | O | 3해상도 | 멀티 해상도 반응형 점검 |
| `/a11y-check` | O | 2팀 | WCAG 2.1 접근성 점검 |

### 성능 & DB

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/perf-audit` | O | 3팀 | Core Web Vitals + 번들 + API |
| `/db-health` | O | 2팀 | Prisma 스키마 + 쿼리 최적화 |

### 코드 품질

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/code-health` | O | 3팀 | 중복/복잡도/미사용 코드 관리 |

### 배포 & 버그

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/pre-deploy` | O | 1인 | 배포 전 자동 체크리스트 (빌드+타입+DB+환경+Playwright) |
| `/quick-fix` | O | 1인 | 빠른 버그 수정 (영향도 추적 포함) |

### 문서 & 기획

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/doc-sync` | O | 2팀 | 코드 변경 → 문서 자동 최신화 |
| `/doc-organize` | O | 2팀 | CLAUDE.md 분할 + 체계화 |
| `/app-plan` | - | 1인 | 앱 기획 인터뷰 |

### 기타

| 명령 | 설명 |
|------|------|
| `/check-pos` | POS Calculator 앱 전용 점검 |
| `/update` | 에이전트 수동 업데이트 |
| `/help` | 에이전트 목록 + 사용법 표시 |

---

## PDCA 사이클

```
Plan(영향도맵+시나리오) -> Do(에이전트 팀 동시 투입) -> Check(점수+교차검증) -> Act(수정+재검증)
    ^                                                                          |
    +-------------- 90점 미만이면 자동 반복 (최대 3회) -----------------------+
```

## 사용 예시

```bash
/끝판왕                       # 전체 자동 (활성 프로젝트 자동 감지)
/끝판왕 . --dry-run           # 현재 폴더, 보고만
/mega-audit pos-calculator-web --threshold=90 --max-iter=3
/flow-check                  # 전체 플로우 엔드투엔드
/full-test 예약 기능          # 특정 기능 대규모 테스트
/change-verify auto          # git diff로 변경사항 자동 감지 후 검증
/design-sense                # 디자인 감성 점검 + 트렌드 추천
/playwright-report 이번주     # 이번 주 변경분 Playwright + 보고서
/security-team               # 전체 보안 점검
/mobile-audit                # 모바일 최적화 점검
/pre-deploy production       # 배포 전 체크리스트
/quick-fix 로그인 안됨        # 빠른 버그 수정
```

## 추천 워크플로우

```
한 방에 전체   -> /끝판왕 (전체 자동) → 결과 보고서만 확인
코드 수정 후   -> /change-verify -> /pre-deploy -> 배포
수동 테스트    -> /test-guide -> 직접 브라우저 점검 -> /change-verify
신규 기능 후   -> /full-test -> /security-quick -> /playwright-report -> /pre-deploy
디자인 리뉴얼  -> /design-sense -> /responsive-check -> /a11y-check
정기 점검     -> /끝판왕 (모든 점검 통합) 또는 /security-team -> /perf-audit -> /code-health -> /db-health
문서 정리     -> /doc-sync -> /doc-organize
```

## 파일 위치

- **플러그인 방식** (권장): 설치 스크립트가 자동으로 `~/.claude/settings.json` 등록
- **수동 설치**: `~/.claude/commands/` 에 `*.md` 복사

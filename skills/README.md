# Claude Code 커스텀 에이전트 v2.1

Claude Code에서 사용할 �� 있는 **시나리오 매트릭스 + 영향도 맵 + 체크리스트** 기반 PDCA 커스텀 에이전트 모음입니다.

## 한 줄 설치

```bash
# Windows (Git Bash) / Mac / Linux
git clone https://github.com/aijunny0604-alt/claude-commands.git /tmp/cc && mkdir -p ~/.claude/commands && cp /tmp/cc/*.md ~/.claude/commands/ && rm -rf /tmp/cc && echo "설치 완료! Claude Code에서 /help 로 확인하세요"
```

## 업데이트

```bash
git clone https://github.com/aijunny0604-alt/claude-commands.git /tmp/cc && cp /tmp/cc/*.md ~/.claude/commands/ && rm -rf /tmp/cc && echo "���데이트 완료!"
```

## 또는 install.sh 사용

```bash
curl -sL https://raw.githubusercontent.com/aijunny0604-alt/claude-commands/master/install.sh | bash
```

---

## v2.1 신규 — Codex 대조 검증 게이트

모든 19개 실행 에이전트에 **Codex 대조 검증 게이트** 가 공통 추가되었습니다.

- 사이클 마지막에 클로드 1차 결과 ↔ Codex 2차 의견 합치표 자동 생성
- Codex CLI가 없으면 자동 스킵 → 클로드 단독 환경에서도 100% 동일 동작
- 합치 항목은 자동 진행 / 충돌 항목은 `AskUserQuestion` 으로 사용자 결정
- 1분 타임아웃으로 Codex가 멈춰도 메인 흐름이 막히지 않음
- 결과는 REPORT 보고서에 "Codex 대조 검증 결과" 섹션으로 1단락 기록

→ 더블체크가 필요한 분석/리뷰/구현/QA 전 작업에서 단일 모델 편향을 완화합니다.

---

## v2.0 핵심 강화 사항

모든 에이전트에 공통 적용:

1. **영향도 맵 (Impact Map)** — 점검 전 코드 연쇄 관계 시각화로 누락 방지
2. **시나리오 매트릭스 (3축)** — 변수 조합으로 테스트 시나리오 자동 도출
3. **마스터 체크리스트** — 실행 가능한 체크 항목 + 커버리지 추적
4. **교차 검증 (Cross-Validation)** — 팀 간 결과 대조로 모순/누락 탐지
5. **영향도 역추적** — FAIL 시 역방향 파급 범위 확인

---

## 에이전트 목록 (15개)

### 테스트 & QA

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/full-test` | O | 4팀 | 대규모 통합 테스트 (로컬+프로덕션) |
| `/change-verify` | O | 4팀 | 변경사항 정밀 검증 (수정 후 필수) |
| `/ux-flow` | O | 2팀 | UX 시나리오 E2E Playwright 검증 |

### 보안

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/security-team` | O | 3팀 | OWASP Top 10 보안 풀 스캔 |
| `/security-quick` | O | 1인 | 경량 보안 점검 (5분) |

### UI/UX

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/mobile-audit` | O | 4팀 | 모바일 UI/UX 최적화 점검 |
| `/responsive-check` | O | 3해상도 | 멀티 해��도 반응형 점검 |
| `/a11y-check` | O | 2팀 | WCAG 2.1 접근성 점검 |

### 성능 & DB

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/perf-audit` | O | 3팀 | Core Web Vitals + 번들 + API |
| `/db-health` | O | 2팀 | Prisma 스키마 + 쿼리 최적화 |

### 코드 품질

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/code-health` | O | 3팀 | 중복/���잡도/미사용 코드 관리 |

### 배포 & 버그

| 명령 | PDCA | 에이전트 | 설명 |
|------|:----:|:--------:|------|
| `/pre-deploy` | O | 1인 | 배포 전 자동 체크리스트 (19항목) |
| `/quick-fix` | O | 1인 | 빠른 버그 수정 (영향도 추적 포함) |

### 기타

| 명령 | 설명 |
|------|------|
| `/check-pos` | POS Calculator 앱 전용 점검 |
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
/full-test 예약 기능        # 특정 기능 대규모 테스트
/change-verify auto         # git diff로 변경사항 자동 감지 후 검증
/security-team              # 전체 보안 점검
/mobile-audit               # 모바일 최적화 점검
/pre-deploy production      # 배포 전 체크리스트
/quick-fix 로그인 안됨      # 빠른 버그 수정
```

## 추천 워크플로우

```
코드 수정 후 -> /change-verify -> /pre-deploy -> 배포
신규 기능 후 -> /full-test -> /security-quick -> /pre-deploy -> 배포
정기 점검   -> /security-team -> /perf-audit -> /code-health -> /db-health
```

## 파일 위치

- **모든 프로젝트**: `~/.claude/commands/` 에 설치
- **특정 프로젝트만**: `프로젝트/.claude/commands/` 에 복사

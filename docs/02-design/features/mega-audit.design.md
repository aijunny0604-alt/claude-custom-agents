# Design: /끝판왕 (mega-audit)

> Feature ID: `mega-audit` (파일명) / Command: `/끝판왕`
> 작성일: 2026-04-30
> Plan 참조: [mega-audit.plan.md](../../01-plan/features/mega-audit.plan.md)

---

## 0. 미결정 사항 확정 (Plan Q1~Q5)

| # | 항목 | 확정안 | 근거 |
|---|------|--------|------|
| Q1 | 명령어 이름 | **`/끝판왕`** (사용자 지정) + alias `/mega-audit` | 사용자 친화 + 영문 alias로 호환 |
| Q2 | 사용자 확인 시점 | **시작 시 1회만** (백업 브랜치 자동 생성) | 자동화 극대화, 안전성은 git 브랜치로 보장 |
| Q3 | 통과율 계산식 | **가중 평균** (가중치 아래 표) | Phase 중요도 차이 반영 |
| Q4 | 리포트 포맷 | **Markdown 기본** + `--html` 옵션 | 기존 PDCA 리포트와 호환 |
| Q5 | GitHub 동기화 | **`j-agents` 단일 push** (마켓플레이스 소스) | 한 곳에 푸시 → 자동 업데이트, 중복 제거 |

### 통과율 가중치 (Phase별)

| Phase | 영역 | 가중치 |
|-------|------|--------|
| 1 | 정적 분석 | 15% |
| 2 | E2E 전수조사 | 25% |
| 3 | DB 무결성 | 20% |
| 4 | UX/성능 | 15% |
| 5 | 보안 | 25% |
| **합계** | | **100%** |

> 보안과 E2E를 가장 무겁게. 정적 분석은 빠지면 큰 일이지만 자동 수정이 쉬워 가중치 낮춤.

---

## 1. 아키텍처 개요 (Architecture Overview)

```
┌──────────────────────────────────────────────────────────┐
│                   /끝판왕 [project] [opts]                │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  Pre-Flight Check        │  ← git 상태, 백업 브랜치
              │  (사용자 확인 1회)        │
              └────────────┬─────────────┘
                           │
        ┌──────────────────▼───────────────────┐
        │           Iteration Loop             │
        │           (max 5회)                  │
        │  ┌─────────────────────────────────┐ │
        │  │ Phase 1: Static Analysis (병렬) │ │
        │  │ Phase 2: E2E Sweep (순차)       │ │
        │  │ Phase 3: DB Health (단독)        │ │
        │  │ Phase 4: UX/Perf (병렬)         │ │
        │  │ Phase 5: Security (단독)         │ │
        │  └─────────────────────────────────┘ │
        │              │                        │
        │              ▼                        │
        │  ┌─────────────────────────────────┐ │
        │  │  Issue Aggregator                │ │
        │  │  - JSON 포맷 통합                │ │
        │  │  - 우선순위 분류                  │ │
        │  └─────────────────────────────────┘ │
        │              │                        │
        │              ▼                        │
        │  ┌─────────────────────────────────┐ │
        │  │  Auto-Fix Engine                 │ │
        │  │  - /quick-fix 호출                │ │
        │  │  - Critical/Major 우선             │ │
        │  └─────────────────────────────────┘ │
        │              │                        │
        │              ▼                        │
        │  ┌─────────────────────────────────┐ │
        │  │  Score Calculator (가중 평균)     │ │
        │  │  - 임계값 ≥ 95% ?                  │ │
        │  └─────────────────────────────────┘ │
        │              │                        │
        │       Yes ◄──┴──► No (loop)          │
        └──────────────┬───────────────────────┘
                       │
                       ▼
              ┌──────────────────────────┐
              │  Report Generator         │
              │  docs/04-report/...       │
              └──────────────────────────┘
```

---

## 2. 컴포넌트 분해 (Components)

### 2.1 Skill 파일 구조

```
claude-custom-agents/
├── skills/
│   ├── 끝판왕.md          ← 메인 스킬 (한글 명령어)
│   ├── mega-audit.md      ← 영문 alias (동일 내용)
│   └── lib/
│       ├── orchestrator.md       ← 5-Phase 실행 로직
│       ├── score-calculator.md   ← 가중 평균 계산
│       ├── auto-fix-engine.md    ← /quick-fix 연동
│       └── report-template.md    ← 리포트 포맷
└── docs/
    ├── 01-plan/features/mega-audit.plan.md
    ├── 02-design/features/mega-audit.design.md
    └── 03-analysis/mega-audit/   ← 실행 결과 누적
```

### 2.2 핵심 컴포넌트

| 컴포넌트 | 책임 | 입력 | 출력 |
|---------|------|------|------|
| **Orchestrator** | 5-Phase 순서 제어, 병렬/순차 분기 | 옵션, 프로젝트 경로 | Phase별 결과 JSON |
| **Issue Aggregator** | 각 에이전트 결과를 표준 JSON으로 통합 | Phase 결과 | 통합 이슈 목록 |
| **Auto-Fix Engine** | Critical/Major 자동 수정 | 이슈 목록 | 수정된 파일 + 미수정 잔여 |
| **Score Calculator** | 가중 평균 통과율 계산 | Phase별 점수 | 종합 점수 + 임계값 통과 여부 |
| **Iteration Controller** | 반복 종료 조건 판단 | 점수, 반복 횟수 | continue / stop |
| **Report Generator** | 통합 리포트 생성 | 모든 반복 결과 | markdown 파일 |
| **Backup Manager** | git 백업 브랜치 관리 | git 상태 | 백업 브랜치 명 |

---

## 3. 인터페이스 설계 (Interface)

### 3.1 명령어 시그니처

```bash
/끝판왕 [project] [options]
/mega-audit [project] [options]   # alias

# Options
--only=<domains>      # code,e2e,db,perf,mobile,a11y,security (콤마 구분)
--threshold=<n>       # 통과 임계값 (기본 95)
--max-iter=<n>        # 최대 반복 (기본 5)
--mode=<full|fast|deep>   # 점검 강도 (기본 full)
--dry-run             # 자동 수정 안 함, 보고만
--no-backup           # 백업 브랜치 생성 안 함 (위험)
--html                # 리포트 HTML로 추가 생성
--skip-confirm        # 시작 시 사용자 확인 생략 (CI용)
```

### 3.2 표준 결과 JSON 스키마

각 Phase가 반환해야 하는 표준 포맷:

```json
{
  "phase": "static-analysis",
  "agent": "code-health",
  "score": 87,
  "issues": [
    {
      "id": "lint-001",
      "severity": "major",
      "file": "src/App.jsx",
      "line": 142,
      "message": "Unused variable 'x'",
      "fix_hint": "remove",
      "auto_fixable": true
    }
  ],
  "metadata": {
    "duration_ms": 3245,
    "files_scanned": 87
  }
}
```

### 3.3 종합 점수 계산식

```
final_score = Σ (phase_score_i × weight_i)
where
  weight: { static: 0.15, e2e: 0.25, db: 0.20, ux: 0.15, security: 0.25 }
  threshold = 95
  pass = final_score >= threshold
```

> Phase가 스킵된 경우(`--only`)는 가중치를 정규화 (남은 Phase 합 = 1.0).

---

## 4. 데이터 흐름 (Data Flow)

```
[사용자 입력]
   │
   ▼
[옵션 파싱] ─── .mega-audit.json 프로젝트 설정 병합
   │
   ▼
[Pre-Flight]
   ├── git status 확인
   ├── 백업 브랜치 생성: mega-audit-backup-{ISO8601}
   └── 사용자 확인 (1회) ── --skip-confirm 시 생략
   │
   ▼
[Iteration N=1]
   ├── Phase 1 (병렬): code-health + lint + tsc
   ├── Phase 2 (순차): full-test → flow-check → ux-flow
   ├── Phase 3 (단독): db-health
   ├── Phase 4 (병렬): perf-audit + mobile-audit + responsive-check + a11y-check
   └── Phase 5 (단독): security-quick
   │
   ▼
[Issue Aggregator]
   ├── 표준 JSON 변환
   └── 우선순위: Critical(score 0-50) / Major(50-80) / Minor(80+)
   │
   ▼
[조건 분기]
   ├── score >= threshold → [Report] (종료)
   ├── N >= max_iter      → [Report + 미통과 경고]
   └── 그 외 → [Auto-Fix Engine]
   │
   ▼
[Auto-Fix Engine]
   ├── auto_fixable=true 항목만 처리
   ├── /quick-fix를 이슈별 호출
   └── 수정 후 git diff 캡처
   │
   ▼
[Iteration N+1]  (영향받은 Phase만 재실행)
   │
   ...
   │
   ▼
[Report Generator]
   └── docs/04-report/끝판왕-{date}.report.md
```

---

## 5. 핵심 알고리즘

### 5.1 영향받은 Phase 재실행 판단

```
fix_files = [수정된 파일 경로]

if any(f matches src/db/* or *.sql) → re-run Phase 3
if any(f matches src/components/* or pages/*) → re-run Phase 2, 4
if any(f matches src/lib/auth*, *.env*) → re-run Phase 5
always → re-run Phase 1 (정적 분석은 항상)
```

### 5.2 무한 반복 방지

```
이전 반복의 이슈 ID 집합 = prev_issue_ids
현재 반복의 이슈 ID 집합 = curr_issue_ids

if (curr_issue_ids ∩ prev_issue_ids).size / curr_issue_ids.size > 0.7
  → "동일 이슈 반복 발생" 경고 + 종료
```

### 5.3 회귀 감지 + 롤백

```
if iteration_score < (prev_iteration_score - 5)
  → "회귀 발생" 경고
  → 자동 롤백: git reset --hard {prev_iteration_commit}
  → 종료
```

---

## 6. 에러 처리 (Error Handling)

| 상황 | 처리 |
|------|------|
| Phase 실행 중 에이전트 실패 | 해당 Phase 점수 = 0, 다음 Phase 진행, 리포트에 명시 |
| git uncommitted changes 존재 | 사용자 확인 단계에서 stash 제안 |
| 백업 브랜치 생성 실패 | 즉시 중단 (안전 우선) |
| /quick-fix 실패 | 해당 이슈 미수정 처리, 다음 이슈 진행 |
| max-iter 도달 | 미통과 상태로 리포트 생성 |
| Playwright 타임아웃 | Phase 2 부분 점수 + 경고 |
| 사용자 Ctrl+C | 백업 브랜치 안내 + 종료 |

---

## 7. 리포트 포맷 (Report Format)

### 7.1 헤더
```markdown
# 끝판왕 Audit Report
- 프로젝트: pos-calculator-web
- 실행 시각: 2026-04-30T18:55:00+09:00
- 종합 점수: **96/100** ✅ 임계값 통과
- 반복 횟수: 2/5
- 백업 브랜치: mega-audit-backup-20260430-185500
```

### 7.2 Phase별 결과
```markdown
## Phase 결과 요약

| Phase | 영역 | 점수 | 가중치 | 기여도 |
|-------|------|------|--------|--------|
| 1 | 정적 분석 | 100 | 15% | 15.0 |
| 2 | E2E | 92 | 25% | 23.0 |
| 3 | DB | 95 | 20% | 19.0 |
| 4 | UX/성능 | 90 | 15% | 13.5 |
| 5 | 보안 | 100 | 25% | 25.0 |
| **합계** | | | | **95.5** |
```

### 7.3 반복별 추이
```markdown
## 반복 추이
- N=1: 78점 (이슈 23건 발견, 18건 자동 수정)
- N=2: 96점 (이슈 5건 잔여, 모두 Minor)
```

### 7.4 잔여 이슈
```markdown
## 미수정 이슈 (사용자 검토 필요)
- [Minor] src/App.jsx:142 - 사용자 결정 필요한 디자인 변경
- ...
```

### 7.5 추천 후속 명령어
```markdown
## 추천 후속
- /pre-deploy production (배포 게이트)
- /security-team (보안 심층)
- /design-sense (감성 점검)
```

---

## 8. 구현 순서 (Implementation Order)

| # | 작업 | 파일 | 의존 |
|---|------|------|------|
| 1 | 표준 JSON 결과 포맷 정의 | `lib/result-schema.md` | - |
| 2 | Orchestrator 5-Phase 골격 | `skills/mega-audit.md` | 1 |
| 3 | Phase 1 구현 (정적 분석) | orchestrator | 2 |
| 4 | Phase 2 구현 (E2E) | orchestrator | 2 |
| 5 | Phase 3 구현 (DB) | orchestrator | 2 |
| 6 | Phase 4 구현 (UX/성능) | orchestrator | 2 |
| 7 | Phase 5 구현 (보안) | orchestrator | 2 |
| 8 | Issue Aggregator | `lib/aggregator.md` | 3-7 |
| 9 | Score Calculator | `lib/score-calculator.md` | 8 |
| 10 | Auto-Fix Engine (/quick-fix 연동) | `lib/auto-fix-engine.md` | 8 |
| 11 | Iteration Controller | orchestrator | 9, 10 |
| 12 | Backup Manager | `lib/backup-manager.md` | 2 |
| 13 | Report Generator | `lib/report-template.md` | 9 |
| 14 | 한글 명령어 wrapper | `skills/끝판왕.md` | 2 |
| 15 | `.mega-audit.json` 프로젝트 설정 지원 | orchestrator | 2 |
| 16 | README + 사용 예시 | `README.md` 갱신 | 14 |
| 17 | 실제 프로젝트 검증 | (테스트) | 16 |

---

## 9. 안전장치 상세 (Safety in Detail)

### 9.1 백업 브랜치 라이프사이클

```
실행 시작 → mega-audit-backup-{ts} 브랜치 생성 (현재 브랜치에서 분기)
         → 작업 브랜치로 복귀
         → 자동 수정마다 작업 브랜치에 커밋 (mega-audit: fix #N)
         → 종료 시
            ├── 통과: 백업 브랜치 유지 (사용자가 직접 정리)
            └── 회귀 감지: git reset --hard {iteration_N_commit}
```

### 9.2 dry-run 모드 동작

- Phase 1~5 모두 실행
- Issue Aggregator까지 동작
- Auto-Fix Engine은 **호출 안 함**
- Report에 "수정안만 표시"

### 9.3 .mega-audit.json (프로젝트별 설정)

```json
{
  "threshold": 95,
  "weights": {
    "static": 0.15,
    "e2e": 0.25,
    "db": 0.20,
    "ux": 0.15,
    "security": 0.25
  },
  "skip_phases": [],
  "playwright_routes": ["/", "/login", "/dashboard"],
  "supabase_project": "jubzppndcclhnvgbvrxr",
  "auto_fix": {
    "enabled": true,
    "max_severity": "major"
  }
}
```

---

## 10. 다른 PC 동기화 전략 (Q5 확정안)

```
[작업] claude-custom-agents/ 에서 수정
    │
    ▼
[push] aijunny0604-alt/j-agents (master) 에만 push
    │
    ▼
[Claude Code 마켓플레이스] autoUpdate=true 설정으로 다른 PC 자동 동기화
    │
    ▼
[claude-custom-agents 레포] 미러로 별도 push 가능 (선택)
```

> 단일 진실의 원천(SSOT)은 **`aijunny0604-alt/j-agents`**.
> `claude-custom-agents` 레포는 백업/이력 용도로만 유지.

---

## 11. 검증 계획 (Validation Plan)

| 검증 항목 | 방법 | 통과 기준 |
|----------|------|----------|
| 5-Phase 모두 호출 | 단순 프로젝트에 `/끝판왕` 실행 | 모든 Phase 결과 JSON 출력 |
| 가중 평균 계산 정확성 | 점수 수동 계산 vs 출력 비교 | 100% 일치 |
| 자동 수정 동작 | 의도적 lint 에러 삽입 후 실행 | 자동 제거 |
| 회귀 시 롤백 | 수정 후 점수 하락 시뮬레이션 | git reset 자동 동작 |
| 무한 반복 방지 | 수정 불가 이슈 시뮬레이션 | 3회 반복 후 종료 |
| 한글 명령어 동작 | `/끝판왕` 호출 | mega-audit 본체 실행 |
| 리포트 가독성 | 실제 점검 결과 검토 | 사용자 확인 |

---

## 12. Do 단계 진입 체크리스트

- [x] Q1~Q5 결정 완료
- [x] 가중치 확정
- [x] JSON 스키마 정의
- [x] 구현 순서 정의 (17단계)
- [x] 안전장치 명세
- [ ] 첫 구현 대상: 표준 JSON 결과 포맷 + Orchestrator 골격

---

```bash
/pdca do mega-audit    # 구현 시작
```

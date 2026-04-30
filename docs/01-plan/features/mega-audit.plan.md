# Plan: mega-audit (끝판왕 자동화 에이전트)

> 가칭. 최종 명령어 이름 후보: `/mega-audit`, `/auto-doctor`, `/final-boss`, `/끝판왕`, `/omni-check`
> Feature ID: `mega-audit`
> 작성일: 2026-04-30
> 작성자: aijunny0604

---

## 1. 개요 (Overview)

프로그램 전체를 자동 순회하며 **전수조사 → 플로우 검증 → 버그 발견 → 자동 수정 → 재검증**을 임계값 도달까지 반복하는 J-AGENTS 오케스트레이터 에이전트.

기존 J-AGENTS 24개 에이전트(/full-test, /flow-check, /change-verify, /code-health, /db-health, /perf-audit, /mobile-audit, /a11y-check, /security-quick 등)를 **순차 + 병렬 조합**으로 한 번에 돌리고, 발견된 이슈를 **PDCA iterate 방식**으로 자동 수정 후 재검증하는 메가 에이전트.

---

## 2. 목표 (Goals)

| 번호 | 목표 |
|------|------|
| G1 | "한 번 실행하면 모든 점검이 끝나는" 단일 진입점 제공 |
| G2 | 발견된 버그/이슈를 자동 수정하여 사용자 개입 최소화 |
| G3 | 임계값(기본 95%)에 도달할 때까지 자동 반복 |
| G4 | 모든 결과를 통합 리포트로 정리하여 한눈에 파악 가능 |
| G5 | J-AGENTS 24개 자산을 재활용하여 중복 구현 방지 |

---

## 3. 사용자 시나리오 (User Scenarios)

### 시나리오 A: 배포 직전 최종 점검
```
사용자: /mega-audit pos-calculator-web
  → 정적 분석 (lint/type/unused) 통과
  → 전체 페이지 E2E 자동 순회 (Playwright)
  → DB 무결성 + 쿼리 점검
  → 성능/모바일/반응형/접근성 점검
  → 발견된 8개 이슈 자동 수정
  → 재검증 → 통과율 96% (임계값 도달)
  → 통합 리포트 생성 + 추천 명령어 출력
```

### 시나리오 B: 정기 헬스체크
```
사용자: /mega-audit (인자 없음 → 활성 프로젝트 자동 감지)
  → 현재 디렉터리 또는 메모리 기반 프로젝트 추론
  → 기본 모드 (전 영역 점검) 실행
```

### 시나리오 C: 특정 영역만
```
사용자: /mega-audit auto-shop-manager --only=db,perf
  → DB 무결성 + 성능만 집중 점검
  → 자동 수정 + 재검증 반복
```

---

## 4. 기능 요구사항 (Functional Requirements)

### FR-1. 단일 진입점 (Orchestrator)
- 명령어: `/mega-audit [project] [options]`
- 인자
  - `[project]`: 대상 프로젝트 경로/이름. 생략 시 현재 디렉터리 또는 활성 프로젝트
  - `--only=<domains>`: 특정 영역만 (`code,e2e,db,perf,mobile,a11y,security`)
  - `--threshold=<n>`: 통과 임계값 (기본 95)
  - `--max-iter=<n>`: 최대 반복 횟수 (기본 5)
  - `--mode=<full|fast|deep>`: 점검 강도

### FR-2. 단계별 점검 파이프라인 (Phase 1~5)

| Phase | 단계 | 호출 에이전트 | 병렬/순차 |
|-------|------|--------------|----------|
| **1. 정적 분석** | lint/type/import/dead code | `/code-health`, lint/tsc 직접 호출 | 병렬 |
| **2. E2E 전수조사** | 모든 페이지/라우트 자동 순회 | `/full-test`, `/flow-check`, `/ux-flow` | 순차 |
| **3. DB 점검** | 스키마/쿼리/RLS/인덱스 | `/db-health` | 단독 |
| **4. UX/성능** | 성능/모바일/반응형/접근성 | `/perf-audit`, `/mobile-audit`, `/responsive-check`, `/a11y-check` | 병렬 |
| **5. 보안** | 취약점/의존성 | `/security-quick` | 단독 |

### FR-3. 자동 수정 루프 (PDCA iterate 패턴)
1. 모든 Phase 결과 수집 → 이슈 목록 생성
2. 우선순위별 분류 (Critical / Major / Minor)
3. **`/quick-fix` 자동 호출**로 Critical/Major 수정
4. 수정 후 영향 받은 Phase만 재실행
5. 통과율 계산 → 임계값 미달 시 반복
6. 임계값 도달 또는 max-iter 도달 시 종료

### FR-4. 통합 리포트 생성
- 출력 위치: `docs/04-report/{feature}-{date}.report.md`
- 포함 내용
  - 전체 통과율 (Phase별 + 종합)
  - 발견 이슈 목록 (수정됨/미수정)
  - 자동 수정 diff 요약
  - 반복 횟수 + 각 반복별 통과율 추이
  - 추천 후속 명령어 (예: `/security-team` 심층, `/pre-deploy production`)

### FR-5. 안전장치 (Safety)
- **Git 커밋 확인**: 자동 수정 전 uncommitted changes 있으면 경고
- **백업 브랜치**: 자동 수정 시작 시 `mega-audit-backup-{timestamp}` 브랜치 생성
- **dry-run 모드**: `--dry-run` 옵션으로 수정 안 하고 보고만
- **롤백 지원**: 반복 후 결과 나빠지면 직전 커밋으로 자동 복원

### FR-6. 진행 상황 표시 (UX)
- Phase별 진행률 표시 (예: `[Phase 2/5] E2E 진행 중... 12/45 페이지`)
- 발견 이슈 실시간 출력
- 반복 횟수 실시간 표시

---

## 5. 비기능 요구사항 (Non-Functional Requirements)

| 항목 | 요구사항 |
|------|---------|
| **실행 시간** | 중규모 프로젝트(10K LOC) 기준 30분 이내 (1회 반복) |
| **확장성** | 새 J-AGENTS 추가 시 mega-audit이 자동 인식 (config 기반) |
| **재사용성** | 각 Phase는 독립 호출 가능 (`/mega-audit --only=db`) |
| **가시성** | 모든 Phase 로그를 `docs/03-analysis/mega-audit/`에 보존 |
| **결정성** | 같은 코드 + 같은 옵션이면 같은 결과 (Playwright 시드 고정) |

---

## 6. 범위 (Scope)

### 포함 (In Scope)
- ✅ 코드 정적 분석 (ESLint, TypeScript, dead code, unused import)
- ✅ 전체 페이지/라우트 E2E (Playwright)
- ✅ DB 무결성 + 쿼리 + RLS 점검 (Supabase)
- ✅ 성능/모바일/반응형/접근성
- ✅ 자동 수정 + 재검증 반복
- ✅ 통합 리포트
- ✅ 기존 J-AGENTS 24개 오케스트레이션

### 제외 (Out of Scope)
- ❌ 신규 기능 개발 (개선만)
- ❌ 인프라 변경 (Vercel/Supabase 설정 변경)
- ❌ 외부 API 키 자동 발급
- ❌ AI 의존도 100% 코드 (사용자 검토 필요한 변경은 PR로 분리 옵션)

---

## 7. 성공 기준 (Success Criteria)

| 기준 | 측정 방법 |
|------|----------|
| SC1: 단일 명령으로 모든 J-AGENTS 자산 활용 | `/mega-audit` 실행 시 24개 중 90% 이상 자동 호출됨 |
| SC2: 자동 수정으로 통과율 향상 | 1회 반복 후 통과율 +20%p 이상 |
| SC3: 임계값 도달률 | 일반 프로젝트 80% 이상이 5회 이내 95% 도달 |
| SC4: 사용자 개입 최소화 | 시작 후 종료까지 사용자 입력 0회 (dry-run 제외) |
| SC5: 안전성 | 자동 수정으로 인한 회귀 0건 (백업 브랜치로 복원 가능) |

---

## 8. 위험 요소 (Risks)

| 위험 | 영향 | 대응 |
|------|------|------|
| R1: 자동 수정이 회귀 발생 | High | 백업 브랜치 + dry-run + 롤백 |
| R2: Playwright 점검에 시간 과다 소요 | Med | `--mode=fast`로 핵심 라우트만 |
| R3: 임계값 영원히 미달 (무한 반복) | Med | max-iter 강제, 같은 이슈 3회 발생 시 중단 |
| R4: 기존 J-AGENTS와 호출 규약 불일치 | Med | 호출 결과 파싱 표준 정의 (JSON 출력 강제) |
| R5: 프로젝트별 환경 차이 | Med | 프로젝트별 config (`.mega-audit.json`) 지원 |

---

## 9. 일정 (Timeline)

| 단계 | 작업 | 예상 |
|------|------|------|
| Plan | 이 문서 (현재) | 0.5일 |
| Design | 상세 설계 + 호출 시퀀스 | 1일 |
| Do (MVP) | Phase 1+2만 + 단순 반복 | 1일 |
| Do (Full) | Phase 3~5 + 자동 수정 + 리포트 | 2일 |
| Check | 실제 프로젝트 3개에 적용 검증 | 1일 |
| Act | 발견된 이슈 개선 | 0.5일 |
| Report | 완료 보고서 | 0.5일 |

**총: 약 6.5일**

---

## 10. 의존성 (Dependencies)

- ✅ J-AGENTS v1.7.0 (24개 에이전트 모두 사용 가능)
- ✅ Playwright (전체 E2E)
- ✅ Supabase MCP (DB 점검)
- ✅ Git (백업 브랜치)
- ⏳ **결정 필요**: 표준 결과 포맷 (각 J-AGENTS가 JSON 출력 가능한지)

---

## 11. 미결정 사항 (Open Questions)

> Design 단계에서 결정 필요

| 번호 | 질문 |
|------|------|
| Q1 | 최종 명령어 이름은? (`/mega-audit` vs `/auto-doctor` vs `/끝판왕`) |
| Q2 | 자동 수정 시 어느 시점에 사용자 확인을 받을 것인가? (현재안: 시작 시 1회만) |
| Q3 | 통과율 계산식은? (Phase별 가중치? 단순 평균?) |
| Q4 | 결과 리포트 포맷은 markdown vs HTML 대시보드? |
| Q5 | 다른 PC와 동기화 시 GitHub 어느 레포로? (`j-agents` vs `claude-custom-agents` 양쪽?) |

---

## 12. 다음 단계

```bash
/pdca design mega-audit    # 상세 설계 시작
```

---

*본 Plan은 사용자 인터뷰(2026-04-30) 기반 작성. 4가지 핵심 결정사항 확정:*
- *추가 위치: J-AGENTS 플러그인*
- *통합 방식: 오케스트레이터*
- *자동화 수준: 발견 + 자동 수정 + 재검증 반복*
- *조사 범위: 코드 정적분석 + E2E + DB + 성능/모바일/a11y*

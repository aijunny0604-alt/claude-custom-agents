# J-AGENTS v1.8.0

Claude Code 전용 **26개 QA/보안/테스트/검증/기획/디자인 에이전트 플러그인**

> **★ v1.8.0 신규**: `/끝판왕` (`/mega-audit`) — 전체 에이전트를 5-Phase로 묶어서 한 번에 자동 점검 + 자동 수정 + 재검증 반복하는 **오케스트레이터**.

---

## 설치 (원클릭)

```bash
curl -sSL https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/install.sh | bash
```

설치 후 **Claude Code 재시작**하면 자동 적용됩니다.

---

## 설치 내용

| 항목 | 내용 |
|------|------|
| 플러그인 | 26개 스킬 자동 로드 |
| Hooks | SessionStart (프로젝트 상태 점검) + PostToolUse (추천) + SessionEnd |
| 메모리 | 에이전트 추천 규칙 + bkit 리포트 규칙 |
| **전역 CLAUDE.md** | `global/CLAUDE.md` → `~/.claude/CLAUDE.md` 자동 설치 (모든 세션 강제 규칙) |
| 자동 업데이트 | 매 세션 시작 시 최신 버전 자동 반영 |

---

## 스킬 목록 (26개)

### ★ 끝판왕 (전체 자동 오케스트레이터)

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/끝판왕` (`/mega-audit`) | 5-Phase | 정적+E2E+DB+UX+보안 가중평균 + 자동 수정 반복. 메뉴/파싱/연관성까지 한 번에 |

### 기능 검증

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/flow-check` | 6팀 | 전체 플로우 엔드투엔드 검증 |
| `/full-test` | 4팀 | 로컬+프로덕션 API 통합 테스트 |
| `/change-verify` | 4팀 | 수정 후 정밀 검증 (영향도 역추적) |
| `/ux-flow` | 2팀 | Playwright 사용자 흐름 E2E |
| `/playwright-report` | 1인 | Playwright 검증 + PDCA 보고서 + 제안서/건의/의견 |
| `/test-guide` | 1인 | 수동 테스트 가이드 (이슈 종합 + 시나리오 + Step-by-Step) |

### 보안

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/security-quick` | 1인 | 경량 보안 점검 (5분) |
| `/security-team` | 3팀 | OWASP Top 10 풀 스캔 |

### UI/UX

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/mobile-audit` | 4팀 | 모바일 UI/UX 최적화 |
| `/responsive-check` | 3해상도 | 멀티 해상도 자동 스크린샷 |
| `/a11y-check` | 2팀 | WCAG 2.1 접근성 검증 |
| `/design-sense` | 3팀 | 감각적 디자인 감성 점검 (375/768/1440 3해상도) + 2026 트렌드 |

### 성능 / DB

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/perf-audit` | 3팀 | Core Web Vitals + 번들 + API |
| `/db-health` | 2팀 | Prisma 스키마 + 쿼리 최적화 |

### 코드 / 배포 / 기획

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/code-health` | 3팀 | 중복/복잡도/미사용 코드 |
| `/pre-deploy` | 1인 | 빌드+타입+DB+환경변수+Playwright 배포 |
| `/quick-fix` | 1인 | 원인 추적 → 수정 → 검증 |
| `/app-plan` | 1인 | 앱 기획 인터뷰 |
| `/design-review` | 1인 | 디자인/구조 리뷰 |

### 문서

| 명령어 | 설명 |
|--------|------|
| `/doc-sync` | 코드 변경 → 문서 자동 최신화 |
| `/doc-organize` | CLAUDE.md 분할 + 체계화 |

### 기타

| 명령어 | 설명 |
|--------|------|
| `/check-pos` | POS Calculator 앱 전용 |
| `/update` | 에이전트 수동 업데이트 |
| `/help` | 전체 목록 보기 |

---

## 카테고리별 추천

| 상황 | 추천 순서 |
|------|----------|
| **전체 자동 (한 방)** | `/끝판왕` (또는 `/mega-audit`) — 모든 점검 + 자동 수정 + 재검증 |
| 기능 검증 | `/flow-check` → `/full-test` → `/change-verify` → `/playwright-report` |
| 보안 | `/security-quick` → `/security-team` |
| UI/UX | `/design-sense` → `/mobile-audit` → `/responsive-check` → `/a11y-check` |
| 성능 | `/perf-audit` → `/db-health` |
| 코드 관리 | `/code-health` |
| 배포 | `/pre-deploy` |
| 긴급 수정 | `/quick-fix` |
| 수동 테스트 준비 | `/test-guide` |

---

## Hooks 동작

### SessionStart (세션 시작 시)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📋 프로젝트 상태 점검
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📁 프로젝트: my-app (master)
  🔄 git pull... ✅ 최신 상태
  📝 미커밋 파일: 0개
  📋 최근 커밋:
     abc1234 feat: 새 기능 추가
  📦 패키지: my-app
  🔑 환경변수: 설정됨
  🗄️ DB 모델: 20개
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### PostToolUse (자동 추천)
```
코드 수정 (Edit)     → /change-verify | /quick-fix
git commit          → /pre-deploy | /doc-sync
git push            → /pre-deploy | /full-test
빌드 (next build)   → /pre-deploy | /security-quick
DB 작업 (prisma)    → /db-health | /security-quick
```

---

## 수동 설치 (install.sh 대신)

settings.json에 직접 추가:

```json
{
  "enabledPlugins": {
    "j-agents@j-agents-marketplace": true
  },
  "extraKnownMarketplaces": {
    "j-agents-marketplace": {
      "source": { "source": "github", "repo": "aijunny0604-alt/j-agents" },
      "autoUpdate": true
    }
  }
}
```

---

## 프로젝트 구조

```
j-agents/
  ├── .claude-plugin/
  │   ├── plugin.json          ← 버전 + 스킬 목록
  │   └── marketplace.json     ← 마켓플레이스 메타정보
  ├── skills/                  ← 26개 스킬 (.md)
  ├── hooks/                   ← SessionStart hook
  ├── memory/                  ← 공통 피드백 메모리
  ├── install.sh               ← 원클릭 설치
  ├── HANDOFF.md               ← AI 핸드오프 문서
  └── README.md                ← 이 파일
```

---

## 핵심 특징

- **Playwright 직접 검증**: `/flow-check`, `/change-verify`, `/pre-deploy` 등에서 실제 브라우저로 UI 검증
- **PDCA 자동 반복**: 90점 미만 시 수정 → 재검증 자동 반복 (최대 3회)
- **영향도 맵**: 변경 파일 기반 연쇄 관계 추적 → 누락 방지
- **교차 검증**: 팀 간 결과 대조로 모순/누락 탐지
- **자동 업데이트**: `autoUpdate: true` → 매 세션 최신 버전 자동 반영

# J AGENTS v1.4.0

Claude Code에서 사용하는 **20개 커스텀 QA/보안/테스트/검증/기획 에이전트** 플러그인입니다.

---

## 설치 방법

### 방법 1: 플러그인으로 설치 (추천)

`~/.claude/settings.json`에 추가:

```json
"enabledPlugins": {
  "j-agents@j-agents-marketplace": true
},
"extraKnownMarketplaces": {
  "j-agents-marketplace": {
    "source": {
      "source": "github",
      "repo": "aijunny0604-alt/claude-custom-agents"
    },
    "autoUpdate": true
  }
}
```

Claude Code 실행하면 자동으로 20개 에이전트가 설치됩니다.

### 방법 2: 수동 설치

```bash
git clone https://github.com/aijunny0604-alt/claude-custom-agents.git /tmp/cc
mkdir -p ~/.claude/commands
cp /tmp/cc/skills/*.md ~/.claude/commands/
rm -rf /tmp/cc
```

---

## 에이전트 목록 (20개)

### 기획

| 명령어 | 설명 |
|--------|------|
| `/app-plan` | 새 프로젝트 기획 인터뷰 (기능 중심 질문 → 기술 스택 도출) |

### 테스트 & QA

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/full-test` | 4팀 병렬 | 대규모 통합 테스트 (로컬+프로덕션) |
| `/change-verify` | 4팀 병렬 | 변경사항 정밀 검증 (수정 후 필수) |
| `/ux-flow` | 2팀 | UX 시나리오 E2E Playwright 검증 |
| `/responsive-check` | 3해상도 | 멀티 해상도 반응형 점검 |
| `/check-pos` | 1인 | POS Calculator 앱 전용 점검 |

### 보안

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/security-team` | 3팀 병렬 | OWASP Top 10 보안 풀 스캔 |
| `/security-quick` | 1인 | 경량 보안 점검 (5분) |

### 품질

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/code-health` | 3팀 | 중복/복잡도/미사용 코드 관리 |
| `/perf-audit` | 3팀 | Core Web Vitals + 번들 + API |
| `/a11y-check` | 2팀 | WCAG 2.1 접근성 점검 |
| `/mobile-audit` | 4팀 | 모바일 UI/UX 최적화 점검 |

### 운영

| 명령어 | 에이전트 | 설명 |
|--------|:--------:|------|
| `/pre-deploy` | 1인 | 배포 전 자동 체크리스트 (19항목) |
| `/db-health` | 2팀 | Prisma 스키마 + 쿼리 최적화 |
| `/quick-fix` | 1인 | 빠른 버그 수정 (PDCA 경량 사이클) |

### 문서

| 명령어 | 설명 |
|--------|------|
| `/doc-sync` | 코드-문서 동기화 |
| `/doc-organize` | 문서 정리/분류 |
| `/design-review` | 디자인/구조 리뷰 |

### 메타

| 명령어 | 설명 |
|--------|------|
| `/help` | 에이전트 목록 + 사용법 표시 |

---

## 추천 워크플로우

```
새 프로젝트      → /app-plan → 기획 구체화 → 개발 시작
코드 수정 후     → /change-verify auto → /pre-deploy → 배포
신규 기능 완료   → /full-test → /security-quick → /pre-deploy → 배포
정기 점검       → /security-team → /perf-audit → /code-health → /db-health
```

---

## PDCA 사이클

모든 에이전트는 PDCA 기반:

```
Plan(영향도맵+시나리오)
  → Do(에이전트 팀 동시 투입)
    → Check(점수+교차검증)
      → Act(수정+재검증, 90점 미만 시 최대 3회 반복)
```

---

## 업데이트

플러그인 폴더에서 수정 후 push하면 다른 PC에 자동 반영:

```bash
cd ~/claude-custom-agents
# 파일 수정 후
git add -A && git commit -m "update" && git push
```

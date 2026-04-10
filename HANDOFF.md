# AI 핸드오프 문서 — J AGENTS 플러그인 v1.6.0

> 이 문서는 다른 AI 세션이 이 프로젝트를 이해하기 위한 핸드오프 문서입니다.

---

## 이 저장소가 뭔가?

MOVEAM 사용자의 **Claude Code 커스텀 에이전트 24개**를 플러그인으로 패키징한 저장소입니다.
`install.sh` 한 줄 실행 또는 `settings.json` 등록으로 자동 설치됩니다.
`autoUpdate: true` 설정으로 세션 시작 시 최신 버전 자동 반영됩니다.

---

## 저장소 구조

```
j-agents/
├── .claude-plugin/
│   ├── marketplace.json    ← 마켓플레이스 등록 정보 (v1.6.0)
│   └── plugin.json         ← 플러그인 설정 (24개 스킬 목록)
├── skills/                 ← 24개 커스텀 에이전트 (핵심)
│   ├── flow-check.md        (기능 검증)
│   ├── full-test.md
│   ├── change-verify.md
│   ├── ux-flow.md
│   ├── playwright-report.md (★ 신규 v1.6.0)
│   ├── security-team.md     (보안)
│   ├── security-quick.md
│   ├── design-sense.md      (★ 신규 v1.6.0, UI/UX)
│   ├── design-review.md
│   ├── mobile-audit.md
│   ├── responsive-check.md
│   ├── a11y-check.md
│   ├── perf-audit.md        (성능/DB)
│   ├── db-health.md
│   ├── code-health.md       (코드 품질)
│   ├── pre-deploy.md        (배포/버그)
│   ├── quick-fix.md
│   ├── doc-sync.md          (문서)
│   ├── doc-organize.md
│   ├── app-plan.md          (기획)
│   ├── check-pos.md         (기타)
│   ├── update.md
│   ├── help.md
│   └── README.md
├── hooks/
│   └── session-start.sh    ← 세션 시작 시 프로젝트 상태 점검 + 메모리/전역 CLAUDE.md 자동 설치
├── memory/                 ← 공통 피드백 메모리 (에이전트 추천 규칙 등)
├── global/
│   └── CLAUDE.md           ← 전역 강제 규칙 (모든 PC 동기화)
├── install.sh              ← 원클릭 설치 (Windows/Mac/Linux)
├── HANDOFF.md              ← 이 파일
└── README.md               ← 사용자용 메인 문서
```

---

## 핵심 아키텍처

### 플러그인 자동 동기화 구조

```
~/.claude/settings.json  (enabledPlugins + extraKnownMarketplaces)
          ↓ autoUpdate: true
https://github.com/aijunny0604-alt/j-agents  (원격 master)
          ↓ 세션 시작 시 자동 pull
Claude Code 커맨드에 즉시 반영
```

**수정은 로컬 `j-agents/skills/`에서 편집 → git push.**
다른 PC는 세션 시작 시 `autoUpdate`로 최신 버전을 받아옵니다.

### 다른 PC 설치 (원클릭)

```bash
curl -sSL https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/install.sh | bash
```

또는 `~/.claude/settings.json`에 아래 전체를 추가:

```json
"enabledPlugins": {
  "j-agents@j-agents-marketplace": true
},
"extraKnownMarketplaces": {
  "j-agents-marketplace": {
    "source": {
      "source": "github",
      "repo": "aijunny0604-alt/j-agents"
    },
    "autoUpdate": true
  }
},
"hooks": {
  "SessionEnd": [
    { "hooks": [{ "type": "command", "command": "echo '[J AGENTS] 추천: /change-verify auto | /full-test 전체 | /security-quick | /pre-deploy | /help'" }] }
  ],
  "PostToolUse": [
    {
      "matcher": "Edit",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] 코드 수정 감지 -> /change-verify auto | /quick-fix | /code-health'" }]
    },
    {
      "matcher": "Write",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] 파일 생성 감지 -> /change-verify auto | /security-quick | /doc-sync'" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] 커밋 완료 -> /pre-deploy production | /change-verify auto | /doc-sync'", "if": "Bash(git commit*)" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] 푸시 감지 -> /pre-deploy production | /full-test 전체 | /security-team'", "if": "Bash(git push*)" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] Next.js 빌드 완료 -> /pre-deploy production | /security-quick | /perf-audit'", "if": "Bash(npx next build*)" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] Vite 빌드 완료 -> /pre-deploy production | /responsive-check | /mobile-audit'", "if": "Bash(npx vite build*)" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] DB 작업 감지 -> /db-health | /security-quick | /change-verify auto'", "if": "Bash(npx prisma*)" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] 배포 감지 -> /full-test 전체 | /security-team | /pre-deploy production'", "if": "Bash(*deploy*)" }]
    },
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "echo '[HOOK] npm 패키지 변경 -> /security-quick | /change-verify auto'", "if": "Bash(npm install*)" }]
    }
  ]
}
```

> **참고**: 이미 settings.json에 `hooks` 키가 있으면 병합해야 합니다. 중복 키는 마지막 값만 적용됩니다.

---

## bkit 플러그인과의 관계

```
bkit 플러그인 (외부)          → /pdca, /code-review 등 PDCA 프레임워크
커스텀 에이전트 플러그인 (이것) → /change-verify, /full-test 등 실전 테스트

서로 독립적. 이름 충돌 없음. 같이 사용 가능.
```

---

## hooks 연동 (settings.json)

코드 수정/빌드/커밋 등 이벤트 발생 시 적절한 에이전트를 추천하는 훅이 설정되어 있습니다:

| 이벤트 | 추천 에이전트 |
|--------|--------------|
| 코드 수정 (Edit) | /change-verify, /quick-fix, /code-health |
| 파일 생성 (Write) | /change-verify, /security-quick, /doc-sync |
| git commit | /pre-deploy, /change-verify, /doc-sync |
| git push | /pre-deploy, /full-test, /security-team |
| Next.js 빌드 | /pre-deploy, /security-quick, /perf-audit |
| Vite 빌드 | /pre-deploy, /responsive-check, /mobile-audit |
| Prisma DB 작업 | /db-health, /security-quick, /change-verify |
| 배포 | /full-test, /security-team, /pre-deploy |
| npm install | /security-quick, /change-verify |

---

## 에이전트 수정/추가 방법

### 기존 에이전트 수정

```bash
cd C:/Users/ROSSA/j-agents
# skills/change-verify.md 등 수정
git add -A && git commit -m "update: 설명" && git push
```

다른 PC는 다음 세션 시작 시 autoUpdate로 자동 반영됩니다.

### 새 에이전트 추가 (체크리스트)

```bash
# 1. skills/ 폴더에 새 .md 파일 생성 (예: skills/new-agent.md)
# 2. .claude-plugin/plugin.json의 skills 배열에 경로 추가
# 3. .claude-plugin/marketplace.json version bump
# 4. skills/README.md에 에이전트 추가
# 5. skills/help.md에 에이전트 추가
# 6. README.md 에이전트 개수 + 카테고리 업데이트
# 7. HANDOFF.md 버전 히스토리 추가
# 8. git commit + push
```

### 에이전트 삭제

```bash
# 1. skills/ 폴더에서 .md 파일 삭제
# 2. .claude-plugin/plugin.json의 skills 배열에서 제거
# 3. README.md / skills/README.md / help.md 동기화
# 4. git push
```

---

## 주의사항

1. **파일명 = 명령어명**: `change-verify.md` → `/change-verify`로 호출
2. **bkit과 이름 충돌 금지**: bkit 스킬 이름과 겹치면 안 됨
3. **plugin.json 동기화 필수**: 파일 추가/삭제 시 반드시 plugin.json도 업데이트
4. **문서 3종 동기화**: README.md / skills/README.md / skills/help.md 함께 업데이트
5. **인자 전달**: `$ARGUMENTS`로 사용자 인자를 받음 (예: `/full-test 예약 기능`)
6. **Playwright 직접 실행**: 서브에이전트는 Playwright MCP 접근 불가. 반드시 메인 대화에서 실행
7. **CRLF 경고 무시**: Windows에서 git 커밋 시 CRLF 경고는 정상 (core.autocrlf 설정)

---

## 관련 프로젝트

| 프로젝트 | 경로 | 설명 |
|---------|------|------|
| pos-calculator-web | C:\Users\MOVEAM_PC\pos-calculator-web | 메인 POS (Vite+React) |
| pos-calculator | C:\Users\MOVEAM_PC\pos-calculator | 구버전 POS (모바일용) |
| auto-shop-manager | D:\auto-shop-manager | 정비소 관리 (Next.js) |

---

## 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
| 1.0.0 | 2026-04-06 | 플러그인 초기 생성, 19개 에이전트 |
| 1.2.0 | 2026-04-06 | 파일명 원복, 심볼릭 링크 구조 확립 |
| 1.3.0 | 2026-04-06 | 레포명 claude-custom-agents → j-agents |
| 1.4.0 | 2026-04-07 | SessionStart hook 추가 - 세션 시작 시 프로젝트 상태 자동 점검 |
| 1.5.0 | 2026-04-08 | Playwright 필수 + flow-check + 공통 메모리 (총 22개) |
| 1.6.0 | 2026-04-10 | /design-sense + /playwright-report 추가 (총 24개), 전역 CLAUDE.md 자동 설치, install.sh Windows 호환성 |

# AI 핸드오프 문서 — J AGENTS 플러그인

> 이 문서는 다른 AI 세션이 이 프로젝트를 이해하기 위한 핸드오프 문서입니다.

---

## 이 저장소가 뭔가?

MOVEAM 사용자의 **Claude Code 커스텀 에이전트 19개**를 플러그인으로 패키징한 저장소입니다.
다른 PC에서 settings.json 등록만 하면 자동 설치됩니다.

---

## 저장소 구조

```
claude-custom-agents/
├── .claude-plugin/
│   ├── marketplace.json    ← 마켓플레이스 등록 정보
│   └── plugin.json         ← 플러그인 설정 (스킬 목록)
├── skills/                 ← 19개 커스텀 에이전트 (핵심)
│   ├── change-verify.md
│   ├── full-test.md
│   ├── security-team.md
│   ├── ... (19개)
│   └── README.md
├── HANDOFF.md              ← 이 파일
└── README.md (없음, skills/README.md가 메인)
```

---

## 핵심 아키텍처

### 심볼릭 링크 구조 (현재 PC)

```
C:\Users\MOVEAM_PC\.claude\commands\  (심볼릭 링크)
          ↓ 연결
C:\Users\MOVEAM_PC\claude-custom-agents\skills\  (원본)
          ↓ git push
https://github.com/aijunny0604-alt/claude-custom-agents  (원격)
          ↓ 플러그인 자동 다운로드
다른 PC의 Claude Code
```

**수정은 `claude-custom-agents/skills/`에서만 하면 됩니다.**
심볼릭 링크로 글로벌 commands에 자동 반영되고, git push로 다른 PC에도 반영됩니다.

### 다른 PC 설치 (복사 붙여넣기용)

`~/.claude/settings.json`에 아래 전체를 추가하면 **플러그인 + hooks + 자동 업데이트** 한번에 설치됩니다:

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
# 1. 파일 수정 (심볼릭 링크라 글로벌에 자동 반영)
cd C:\Users\MOVEAM_PC\claude-custom-agents
# skills/change-verify.md 등 수정

# 2. GitHub에 push
git add -A && git commit -m "update: 설명" && git push
```

### 새 에이전트 추가

```bash
# 1. skills/ 폴더에 새 .md 파일 생성
# 2. .claude-plugin/plugin.json의 skills 배열에 경로 추가
# 3. git push
```

### 에이전트 삭제

```bash
# 1. skills/ 폴더에서 .md 파일 삭제
# 2. .claude-plugin/plugin.json의 skills 배열에서 제거
# 3. git push
```

---

## 주의사항

1. **파일명 = 명령어명**: `change-verify.md` → `/change-verify`로 호출
2. **심볼릭 링크 주의**: `~/.claude/commands/`는 심볼릭 링크임. 이 폴더를 삭제하면 원본은 유지되지만 링크가 끊김
3. **bkit과 이름 충돌 금지**: bkit 스킬 이름과 겹치면 안 됨
4. **plugin.json 동기화**: 파일 추가/삭제 시 반드시 plugin.json도 업데이트
5. **인자 전달**: `$ARGUMENTS`로 사용자 인자를 받음 (예: `/full-test 예약 기능`)

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

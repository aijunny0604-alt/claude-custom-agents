#!/bin/bash
# ============================================================
# J AGENTS 설치 스크립트
# 플러그인 + hooks + autoUpdate 한방 설치
# ============================================================

echo ""
echo "=============================="
echo "  J AGENTS Installer v1.5.0"
echo "=============================="
echo ""

SETTINGS_DIR="$HOME/.claude"
SETTINGS_FILE="$SETTINGS_DIR/settings.json"

# .claude 디렉토리 생성
mkdir -p "$SETTINGS_DIR"

# settings.json 없으면 생성
if [ ! -f "$SETTINGS_FILE" ]; then
  echo "{}" > "$SETTINGS_FILE"
  echo "[+] settings.json 생성됨"
fi

# 백업
cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"
echo "[+] 기존 설정 백업: settings.json.backup"

# node로 JSON 병합 (jq 없어도 동작)
node -e "
const fs = require('fs');
const path = '$SETTINGS_FILE'.replace(/\\\\/g, '/');
let settings = {};
try { settings = JSON.parse(fs.readFileSync(path, 'utf8')); } catch(e) { settings = {}; }

// 플러그인 등록
if (!settings.enabledPlugins) settings.enabledPlugins = {};
settings.enabledPlugins['j-agents@j-agents-marketplace'] = true;

// 마켓플레이스 등록
if (!settings.extraKnownMarketplaces) settings.extraKnownMarketplaces = {};
settings.extraKnownMarketplaces['j-agents-marketplace'] = {
  source: { source: 'github', repo: 'aijunny0604-alt/j-agents' },
  autoUpdate: true
};

// hooks 등록
if (!settings.hooks) settings.hooks = {};

// 세션 시작 시 프로젝트 상태 점검
settings.hooks.UserPromptSubmit = [
  { hooks: [{ type: 'command', command: 'bash ~/.claude/hooks/session-start.sh' }] }
];

settings.hooks.SessionEnd = [
  { hooks: [{ type: 'command', command: \"echo '[J AGENTS] 추천: /change-verify auto | /full-test 전체 | /security-quick | /pre-deploy | /help'\" }] }
];

settings.hooks.PostToolUse = [
  { matcher: 'Edit', hooks: [{ type: 'command', command: \"echo '[HOOK] 코드 수정 감지 -> /change-verify auto | /quick-fix | /code-health'\" }] },
  { matcher: 'Write', hooks: [{ type: 'command', command: \"echo '[HOOK] 파일 생성 감지 -> /change-verify auto | /security-quick | /doc-sync'\" }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] 커밋 완료 -> /pre-deploy production | /change-verify auto | /doc-sync'\", if: 'Bash(git commit*)' }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] 푸시 감지 -> /pre-deploy production | /full-test 전체 | /security-team'\", if: 'Bash(git push*)' }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] Next.js 빌드 완료 -> /pre-deploy production | /security-quick | /perf-audit'\", if: 'Bash(npx next build*)' }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] Vite 빌드 완료 -> /pre-deploy production | /responsive-check | /mobile-audit'\", if: 'Bash(npx vite build*)' }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] DB 작업 감지 -> /db-health | /security-quick | /change-verify auto'\", if: 'Bash(npx prisma*)' }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] 배포 감지 -> /full-test 전체 | /security-team | /pre-deploy production'\", if: 'Bash(*deploy*)' }] },
  { matcher: 'Bash', hooks: [{ type: 'command', command: \"echo '[HOOK] npm 패키지 변경 -> /security-quick | /change-verify auto'\", if: 'Bash(npm install*)' }] }
];

fs.writeFileSync(path, JSON.stringify(settings, null, 2));
console.log('[+] 플러그인 등록 완료');
console.log('[+] hooks 설정 완료');
console.log('[+] autoUpdate 활성화');
"

# hooks 스크립트 설치
HOOKS_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOKS_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/hooks" ]; then
  cp "$SCRIPT_DIR/hooks"/*.sh "$HOOKS_DIR/" 2>/dev/null
  chmod +x "$HOOKS_DIR"/*.sh 2>/dev/null
  echo "[+] hook 스크립트 설치됨"
else
  # curl 설치 시 GitHub에서 직접 다운로드
  curl -sSL "https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/hooks/session-start.sh" -o "$HOOKS_DIR/session-start.sh" 2>/dev/null
  chmod +x "$HOOKS_DIR/session-start.sh" 2>/dev/null
  echo "[+] hook 스크립트 다운로드됨"
fi

echo ""
echo "=============================="
echo "  설치 완료!"
echo "=============================="
echo ""
echo "  포함 항목:"
echo "    [v] J AGENTS 플러그인 (22개 에이전트)"
echo "    [v] SessionStart hook (프로젝트 상태 자동 점검)"
echo "    [v] PostToolUse hooks (9개 자동 추천)"
echo "    [v] SessionEnd hook (종료 시 추천)"
echo "    [v] autoUpdate (자동 업데이트)"
echo ""
echo "  Claude Code를 재시작하면 적용됩니다."
echo "  /help 로 에이전트 목록을 확인하세요."
echo ""

#!/bin/bash
# ============================================================
# J AGENTS 설치 스크립트 v1.6.0
# 플러그인 + hooks + autoUpdate + 메모리 한방 설치
# Windows (Git Bash/MSYS2) / macOS / Linux 모두 지원
# ============================================================

echo ""
echo "=============================="
echo "  J AGENTS Installer v1.6.0"
echo "=============================="
echo ""

# ── OS 감지 및 경로 설정 ──
detect_claude_dir() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
      # Windows: Git Bash / MSYS2 / Cygwin
      if [ -n "$USERPROFILE" ]; then
        # USERPROFILE을 Unix 경로로 변환
        CLAUDE_DIR="$(cygpath -u "$USERPROFILE")/.claude"
      else
        CLAUDE_DIR="$HOME/.claude"
      fi
      OS_TYPE="windows"
      ;;
    Darwin*)
      CLAUDE_DIR="$HOME/.claude"
      OS_TYPE="macos"
      ;;
    *)
      CLAUDE_DIR="$HOME/.claude"
      OS_TYPE="linux"
      ;;
  esac
}

detect_claude_dir
echo "[*] OS: $OS_TYPE"
echo "[*] Claude 경로: $CLAUDE_DIR"

SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# .claude 디렉토리 생성
mkdir -p "$CLAUDE_DIR"

# settings.json 없으면 생성
if [ ! -f "$SETTINGS_FILE" ]; then
  echo "{}" > "$SETTINGS_FILE"
  echo "[+] settings.json 생성됨"
fi

# 백업
cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"
echo "[+] 기존 설정 백업: settings.json.backup"

# ── node.js로 JSON 병합 ──
# 핵심: 경로를 node.js에 환경변수로 전달 (쉘 변수 치환 문제 회피)
CLAUDE_SETTINGS_PATH="$SETTINGS_FILE" node -e '
const fs = require("fs");
const path = require("path");

// 환경변수에서 경로를 받아 절대경로로 변환
let settingsPath = process.env.CLAUDE_SETTINGS_PATH;

// Windows Git Bash 경로(/c/Users/...) → 네이티브 경로(C:\Users\...) 변환
if (settingsPath.match(/^\/[a-zA-Z]\//)) {
  const drive = settingsPath[1].toUpperCase();
  settingsPath = drive + ":" + settingsPath.slice(2);
}
// 슬래시 통일 (Windows에서도 동작)
settingsPath = path.resolve(settingsPath);

let settings = {};
try {
  settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
} catch(e) {
  settings = {};
}

// 플러그인 등록
if (!settings.enabledPlugins) settings.enabledPlugins = {};
settings.enabledPlugins["j-agents@j-agents-marketplace"] = true;

// 마켓플레이스 등록
if (!settings.extraKnownMarketplaces) settings.extraKnownMarketplaces = {};
settings.extraKnownMarketplaces["j-agents-marketplace"] = {
  source: { source: "github", repo: "aijunny0604-alt/j-agents" },
  autoUpdate: true
};

// hooks 등록
if (!settings.hooks) settings.hooks = {};

settings.hooks.UserPromptSubmit = [
  { hooks: [{ type: "command", command: "bash ~/.claude/hooks/session-start.sh" }] }
];

settings.hooks.SessionEnd = [
  { hooks: [{ type: "command", command: "echo \"[J AGENTS] 추천: /change-verify auto | /full-test 전체 | /security-quick | /pre-deploy | /help\"" }] }
];

settings.hooks.PostToolUse = [
  { matcher: "Edit", hooks: [{ type: "command", command: "echo \"[HOOK] 코드 수정 감지 -> /change-verify auto (변경 검증) | /quick-fix (버그면) | /code-health (품질 점검)\"" }] },
  { matcher: "Write", hooks: [{ type: "command", command: "echo \"[HOOK] 파일 생성 감지 -> /change-verify auto (변경 검증) | /security-quick (보안) | /doc-sync (문서 동기화)\"" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] 커밋 완료 -> /pre-deploy production (배포 점검) | /change-verify auto (변경 검증) | /doc-sync (문서 동기화)\"", if: "Bash(git commit*)" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] 푸시 감지 -> /pre-deploy production (배포 게이트) | /full-test 전체 (통합 테스트) | /security-team (보안 팀)\"", if: "Bash(git push*)" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] Next.js 빌드 완료 -> /pre-deploy production (배포) | /security-quick (보안) | /perf-audit (성능)\"", if: "Bash(npx next build*)" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] Vite 빌드 완료 -> /pre-deploy production (배포) | /responsive-check (반응형) | /mobile-audit (모바일)\"", if: "Bash(npx vite build*)" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] DB 작업 감지 -> /db-health (DB 점검) | /security-quick (보안) | /change-verify auto (변경 검증)\"", if: "Bash(npx prisma*)" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] 배포 감지 -> /full-test 전체 (통합 테스트) | /security-team (보안 팀) | /pre-deploy production (최종 점검)\"", if: "Bash(*deploy*)" }] },
  { matcher: "Bash", hooks: [{ type: "command", command: "echo \"[HOOK] npm 패키지 변경 -> /security-quick (의존성 보안) | /change-verify auto (변경 검증)\"", if: "Bash(npm install*)" }] }
];

fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
console.log("[+] 플러그인 등록 완료");
console.log("[+] hooks 설정 완료");
console.log("[+] autoUpdate 활성화");
'

# 결과 확인
if [ $? -ne 0 ]; then
  echo "[!] settings.json 업데이트 실패 - 수동 설정이 필요할 수 있습니다"
  echo "[!] 파일 경로: $SETTINGS_FILE"
  echo "[!] 파일 존재 여부: $([ -f "$SETTINGS_FILE" ] && echo "있음" || echo "없음")"
else
  echo "[+] settings.json 업데이트 성공"
fi

# ── hooks 스크립트 설치 ──
HOOKS_DIR="$CLAUDE_DIR/hooks"
mkdir -p "$HOOKS_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/hooks" ] && [ "$(ls -A "$SCRIPT_DIR/hooks" 2>/dev/null)" ]; then
  cp "$SCRIPT_DIR/hooks"/*.sh "$HOOKS_DIR/" 2>/dev/null
  chmod +x "$HOOKS_DIR"/*.sh 2>/dev/null
  echo "[+] hook 스크립트 설치됨 (로컬)"
else
  curl -sSL "https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/hooks/session-start.sh" -o "$HOOKS_DIR/session-start.sh" 2>/dev/null
  chmod +x "$HOOKS_DIR/session-start.sh" 2>/dev/null
  echo "[+] hook 스크립트 다운로드됨 (GitHub)"
fi

# ── 메모리 설치 (공통 피드백 규칙) ──
echo "[+] 공통 메모리 설치 중..."
PROJECTS_DIR="$CLAUDE_DIR/projects"
if [ -d "$PROJECTS_DIR" ]; then
  for proj_dir in "$PROJECTS_DIR"/*/; do
    if [ -d "$proj_dir" ]; then
      MEMORY_DIR="${proj_dir}memory"
      mkdir -p "$MEMORY_DIR"
      # feedback 메모리 다운로드
      curl -sSL "https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/memory/feedback_recommend_agents.md" -o "$MEMORY_DIR/feedback_recommend_agents.md" 2>/dev/null
      curl -sSL "https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/memory/feedback_bkit_report.md" -o "$MEMORY_DIR/feedback_bkit_report.md" 2>/dev/null
      # MEMORY.md 인덱스에 추가 (중복 방지)
      if [ -f "$MEMORY_DIR/MEMORY.md" ]; then
        grep -q "feedback_recommend_agents" "$MEMORY_DIR/MEMORY.md" 2>/dev/null || echo "- [에이전트 추천 규칙](feedback_recommend_agents.md) — 매 응답 끝에 상황 맞는 다음 에이전트 명령어 자동 추천" >> "$MEMORY_DIR/MEMORY.md"
        grep -q "feedback_bkit_report" "$MEMORY_DIR/MEMORY.md" 2>/dev/null || echo "- [bkit 리포트 필수](feedback_bkit_report.md) — bkit Feature Usage 리포트 + 추천 명령어 둘 다 매 응답에 포함" >> "$MEMORY_DIR/MEMORY.md"
      else
        curl -sSL "https://raw.githubusercontent.com/aijunny0604-alt/j-agents/master/memory/MEMORY.md" -o "$MEMORY_DIR/MEMORY.md" 2>/dev/null
      fi
    fi
  done
fi
echo "[+] 메모리 설치 완료"

# ── 설치 검증 ──
echo ""
echo "── 설치 검증 ──"
PASS=true
[ -f "$SETTINGS_FILE" ] && echo "  ✅ settings.json" || { echo "  ❌ settings.json 없음"; PASS=false; }
[ -f "$CLAUDE_DIR/hooks/session-start.sh" ] && echo "  ✅ session-start.sh" || { echo "  ❌ session-start.sh 없음"; PASS=false; }
grep -q "j-agents" "$SETTINGS_FILE" 2>/dev/null && echo "  ✅ 플러그인 등록됨" || { echo "  ❌ 플러그인 미등록"; PASS=false; }
grep -q "PostToolUse" "$SETTINGS_FILE" 2>/dev/null && echo "  ✅ hooks 등록됨" || { echo "  ❌ hooks 미등록"; PASS=false; }

echo ""
echo "=============================="
if [ "$PASS" = true ]; then
  echo "  ✅ 설치 완료!"
else
  echo "  ⚠️ 설치 완료 (일부 경고)"
fi
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

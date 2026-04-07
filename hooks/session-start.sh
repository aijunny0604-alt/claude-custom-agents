#!/bin/bash
# J-AGENTS 세션 시작 Hook - 프로젝트 상태 자동 점검
# SessionStart > UserPromptSubmit 에서 실행

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📋 프로젝트 상태 점검"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Git 레포인지 확인
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "  ⚠️ Git 레포가 아닙니다"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
fi

# 프로젝트명
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)")
BRANCH=$(git branch --show-current 2>/dev/null)
echo "  📁 프로젝트: $PROJECT ($BRANCH)"
echo ""

# 최신 코드 가져오기
echo "  🔄 git pull..."
PULL_RESULT=$(git pull --quiet 2>&1)
if echo "$PULL_RESULT" | grep -q "Already up to date"; then
  echo "  ✅ 최신 상태"
elif echo "$PULL_RESULT" | grep -q "error\|fatal\|CONFLICT"; then
  echo "  ❌ pull 실패: $PULL_RESULT"
else
  echo "  📥 업데이트 완료"
fi
echo ""

# 미커밋 파일 확인
UNCOMMITTED=$(git status --short 2>/dev/null)
if [ -n "$UNCOMMITTED" ]; then
  COUNT=$(echo "$UNCOMMITTED" | wc -l | tr -d ' ')
  echo "  📝 미커밋 파일: ${COUNT}개"
  echo "$UNCOMMITTED" | head -5 | while read line; do
    echo "     $line"
  done
  if [ "$COUNT" -gt 5 ]; then
    echo "     ... 외 $((COUNT - 5))개"
  fi
else
  echo "  ✅ 미커밋 파일 없음"
fi
echo ""

# 최근 커밋 3개
echo "  📋 최근 커밋:"
git log --oneline -3 2>/dev/null | while read line; do
  echo "     $line"
done
echo ""

# 프로젝트 타입 감지 + 상태
if [ -f "package.json" ]; then
  # Node.js 프로젝트
  PKG_NAME=$(node -e "try{console.log(require('./package.json').name||'')}catch{}" 2>/dev/null)
  if [ -n "$PKG_NAME" ]; then
    echo "  📦 패키지: $PKG_NAME"
  fi

  # node_modules 확인
  if [ ! -d "node_modules" ]; then
    echo "  ⚠️ node_modules 없음 (npm install 필요)"
  fi

  # .env 확인
  if [ -f ".env.local" ] || [ -f ".env" ]; then
    echo "  🔑 환경변수: 설정됨"
  else
    echo "  ⚠️ 환경변수: .env 파일 없음"
  fi
fi

# Prisma 확인
if [ -f "prisma/schema.prisma" ]; then
  MODEL_COUNT=$(grep -c "^model " prisma/schema.prisma 2>/dev/null || echo 0)
  echo "  🗄️ DB 모델: ${MODEL_COUNT}개"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

---
name: 에이전트 추천은 hooks가 담당
description: 에이전트 추천은 settings.json hooks로 자동 표시. AI가 별도로 추천 블록 넣지 말 것.
type: feedback
---

에이전트 추천은 hooks가 자동 처리한다. AI가 응답에 별도 추천 블록을 넣지 말 것.

**Why:** 메모리 규칙으로 추천하면 포맷이 불안정하고 빠지거나 깨짐. hooks는 시스템이 100% 실행.

**How to apply:**
- PostToolUse hooks → 코드 수정/빌드/커밋 등 상황별 추천 자동 표시
- SessionEnd hook → 대화 종료 시 J AGENTS 추천 자동 표시
- AI는 추천 명령어를 별도로 넣지 않아도 됨

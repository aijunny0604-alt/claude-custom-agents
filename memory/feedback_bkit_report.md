---
name: bkit Feature Usage 리포트
description: 매 응답 끝에 bkit Feature Usage 리포트만 포함. 추천 명령어는 hooks가 처리.
type: feedback
---

매 응답 끝에 bkit Feature Usage 리포트를 포함한다.

**Why:** bkit 플러그인 규칙. 추천 명령어는 hooks(SessionEnd, PostToolUse)가 자동으로 처리하므로 리포트에 넣지 않는다.

**How to apply:** 모든 응답 끝에 아래 형식:
```
─────────────────────────────────────────────────
📊 bkit Feature Usage
─────────────────────────────────────────────────
✅ Used: [사용한 bkit 기능]
⏭️ Not Used: [미사용 주요 기능] (이유)
💡 Recommended: [다음 PDCA 단계 또는 적합한 bkit 기능]
─────────────────────────────────────────────────
```

주의: 추천 명령어 별도 블록 추가 금지. hooks가 알아서 표시함.

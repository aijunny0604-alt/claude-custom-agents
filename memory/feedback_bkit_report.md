---
name: bkit Feature Usage 리포트 필수
description: 매 응답 끝에 bkit Feature Usage 리포트 포함. 추천 명령어는 Recommended 줄에 통합.
type: feedback
---

매 응답 끝에 bkit Feature Usage 리포트를 포함한다.
추천 명령어는 별도 블록 없이 💡 Recommended 줄에 통합한다.

**Why:** 추천 명령어가 따로 나오면 구분선과 겹쳐서 지저분해 보임.

**How to apply:** 모든 응답 끝에 아래 형식 필수:
```
─────────────────────────────────────────────────
📊 bkit Feature Usage
─────────────────────────────────────────────────
✅ Used: [사용한 bkit 기능]
⏭️ Not Used: [미사용 주요 기능] (이유)
💡 Recommended: /명령어 (설명), /명령어 (설명)
─────────────────────────────────────────────────
```

주의: 💡 Recommended 아래에 별도 "추천 다음 명령어:" 블록을 추가하지 말 것.

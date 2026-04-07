---
name: 상황별 에이전트 추천 규칙
description: 작업 상황에 맞는 J AGENTS 명령어를 bkit 리포트의 Recommended 줄에 추천
type: feedback
---

bkit 리포트의 💡 Recommended 줄에 현재 상황에 맞는 에이전트를 추천한다.

**Why:** 사용자가 어떤 에이전트를 써야 하는지 매번 물어보지 않아도 되게 하기 위함.

**How to apply:**
- 코드 수정 후 → `/change-verify auto`, `/flow-check`
- 배포 후 → `/mobile-audit`, `/responsive-check`
- 버그 발견 시 → `/quick-fix`
- 새 기능 시작 → `/app-plan`, `/pdca plan {feature}`
- 보안 점검 필요 → `/security-quick`
- 문서 업데이트 필요 → `/doc-sync`

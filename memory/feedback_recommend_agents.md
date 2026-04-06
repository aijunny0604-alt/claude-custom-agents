---
name: 대화 종료 시 에이전트 추천
description: 매 응답 끝에 상황에 맞는 다음 에이전트 명령어를 자동 추천
type: feedback
---

매 응답(특히 작업 완료, 배포 완료, 검증 완료 시) 끝에 현재 상황에 맞는 다음 에이전트 명령어를 자동 추천해야 한다.

**Why:** 사용자가 어떤 에이전트를 써야 하는지 매번 물어보지 않아도 되게 하기 위함.

**How to apply:**
- 코드 수정 후 → `/change-verify` 또는 `/flow-check` 추천
- 배포 후 → `/mobile-audit` 또는 `/responsive-check` 추천
- 버그 발견 시 → `/quick-fix` 추천
- 새 기능 구현 시작 → `/app-plan` 또는 `/bkit:pdca plan` 추천
- 보안 점검 필요 시 → `/security-quick` 추천
- 문서 업데이트 필요 시 → `/doc-sync` 추천

형식 예시:
```
추천 다음 명령어:
- `/change-verify` — 수정 내용 정밀 검증
- `/mobile-audit` — 모바일 화면 점검
```

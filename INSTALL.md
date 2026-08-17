# J-AGENTS 다른 PC 설치 가이드

이 문서대로 하면 **어느 PC에서도** 매장 PC와 동일한 품질(블로그·검색광고·영상 스킬)로 쓸 수 있습니다.

## 0. 전제 — 모델을 Opus로
품질 차이의 절반은 모델입니다. Claude Code에서 `/model` 또는 `/config`로 **Opus(4.8 이상)** 로 맞추세요. (Sonnet·`/fast`·구버전은 결과 깊이가 떨어집니다.)

## 1. 플러그인 설치 (스킬·스크립트·로고 전부 포함)
Claude Code에서:
```
/plugin marketplace add aijunny0604-alt/j-agents
/plugin install j-agents@j-agents-marketplace
```
- 이 한 번으로 **모든 스킬 + `scripts/` 16개 + `assets/fervid_logo.png`** 가 함께 설치됩니다.
- 설치 위치는 `${CLAUDE_PLUGIN_ROOT}` (플러그인 루트)로, 스킬 안에서 자동 참조됩니다.

## 2. 전역 규칙 (CLAUDE.md) — 선택
매장 PC의 응답 규칙(bkit 리포트·추천 명령어 등)을 그대로 쓰려면 `~/.claude/CLAUDE.md`를 복사해 넣으세요. (없어도 스킬은 동작)

## 3. 네이버 검색광고/키워드 키 (`/네이버키워드`·`/검색광고점검` 쓸 때만)
키는 보안상 깃에 없습니다. 다른 PC에서 광고/키워드 스킬을 쓰려면 **직접** 생성:
```
경로: ~/.secrets/naver_searchad.json
{ "API_KEY":"...", "SECRET_KEY":"...", "CUSTOMER_ID":"1541160" }
```
- 발급: searchad.naver.com → 도구 → API 사용 관리. (블로그·영상 스킬은 키 없이 동작)

## 4. 경로 호환 (자동)
스킬 문서에 `C:\Users\MOVEAM_PC\claude-custom-agents\scripts\...` 로 적힌 경로는 **개발 PC 기준 예시**입니다. 다른 PC에서는 Claude가 자동으로 `${CLAUDE_PLUGIN_ROOT}\scripts\...`(플러그인 설치 위치)로 대체해 실행합니다. (각 스킬 상단 "경로 호환" 규칙 참조)
- 사진 입력 폴더(`...\Downloads\...`)는 각 PC의 실제 폴더 경로를 그대로 쓰면 됩니다.

## 5. 확인
```
/help          → 설치된 스킬 목록 확인
/팀퍼비드블로그  → 블로그 자동작성 (키 불필요)
/네이버키워드    → 키워드 조회 (3번 키 필요)
```

---
문의: 매장 PC(메인)에서 모든 게 세팅돼 있으니, 실작업은 매장 PC를, 다른 PC는 조회·백업용으로 쓰는 걸 권장합니다.

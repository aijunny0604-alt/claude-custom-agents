---
description: 무브모터스 무비(Moobie) 유튜브 쇼츠 제작 에이전트 (영어 alias) — `/무비`와 동일 동작. 블로그/사진 → 키컷 선정 → 8씬 → Higgsfield Seedance 2.0 한글 멀티샷 프롬프트(≤3000자, 일본어음성 차단) → 클로바 다인 나레이션 → 업로드 패키지.
argument-hint: <블로그 URL 또는 이미지 폴더 경로> (예: "https://blog.naver.com/move_am/222884497227")
---

# /moobie — 무브모터스 무비 쇼츠 제작 에이전트 (영어 alias)

`/무비`의 영어 alias. **모든 동작과 절차는 `무비.md`와 100% 동일**.

호출 시 즉시 `무비.md`의 절차를 따라 실행한다:

1. 사전 점검 + EP 셋업 (AskUserQuestion: EP번호·차종·제품/작업·색상·씬개수)
2. 소스 수집 (블로그 URL → Playwright PostView 렌더링 + 사진 다운로드 / 폴더 → 번호순)
3. 키컷 선정 (전부 X, 주요 씬만 — 컨택트시트 시각 확인 후 컨펌)
4. 8씬 구조 배정 (8/8/15/15/15/15/15초, 구도 매 씬 다르게)
5. Seedance 2.0 한글 멀티샷 프롬프트 (씬별, ≤3000자, AUDIO 차단블록, ref ID)
6. 클로바 다인 나레이션 대본 (씬별 톤)
7. 업로드 패키지 (제목·설명글·해시태그·고정댓글·썸네일 가이드)
8. CapCut 합성 안내 + `docs/무비_EP[N]_[차종].md` 저장

## 절대 원칙 (무비.md와 동일)
- 무비 캐릭터 고정: chibi SD 2-3등신, royal blue 단발+사이드포니, Move Motors 점프수트, ref `@dc42431d-bee7-42d4-bd26-852f693aecaf` (Slot 1)
- 일본 스튜디오명 금지(일본어 음성 차단), AUDIO 차단블록 필수, Generate Audio OFF
- Seedance 프롬프트 ≤3000자, 변화씬 First/Last Frame, 그린스크린 #00FF00 엔딩
- 구도 매 씬 다르게, 이미지 순서대로 매핑

## 출력 직후 필수
사용자 전역 CLAUDE.md 규칙대로 응답 말미에 bkit Feature Usage 블록 + 추천 명령어 줄 포함.

---
**🎬 무브모터스 × 무비 | 부산 전문 튜닝샵 | 📞 010-5858-6046**

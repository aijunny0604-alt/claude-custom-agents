# 🎬 무브모터스 × 무비 마스터 템플릿 v2.0

**최종 업데이트**: 2026년 4월 · **버전**: v2.0 · **기반**: EP.1(아반떼N 번웨이), EP.2(벤츠 CLA45 AMG)

> ⭐ 이 문서는 `/무비` 에이전트의 정본(canonical) 레퍼런스다. 프롬프트 양식·캐릭터·스타일·연출·설정 모두 여기에 맞춘다.

## 🏢 프로젝트
- 무브모터스: 부산 전문 튜닝샵 / blog.naver.com/move_am / insta @move_automotive / youtube @IMOVEAutomotive
- 마스코트 "무비(Moobie)" = Move + Movie. 치비(SD) 2-3등신 귀여운 마스코트. 튜닝 안내 역할.
- 시리즈명: "무비의 튜닝 일기 🎬"

## 🎭 캐릭터 고정 (모든 씬 필수)
```
chibi SD anime girl Moobie with super-deformed proportions
(2-3 head tall, oversized head, small body), royal blue short
bob hair with side ponytail in red band, large expressive
brown eyes taking up half the face, white Move Motors racing
jumpsuit with red stripes, black fingerless gloves, black
work boots, cute mascot style
```
- Higgsfield Reference ID: `@dc42431d-bee7-42d4-bd26-852f693aecaf` → 항상 **Slot 1**
- ❌ 금지: "6-7 head proportions", "realistic anime proportions", "mature/tall/adult" → 성인 체형 유발
- ✅ 필수: "chibi SD anime girl", "super-deformed proportions", "2-3 head tall", "oversized head, small body", "large expressive brown eyes taking up half the face", "cute mascot style"
- 외형: 로열블루 보브+오른쪽 사이드포니(빨간끈) / 갈색 큰 눈(얼굴 절반) / 흰색 Move Motors 점프수트+빨간 줄무늬 / 검은 핑거리스 글러브 / 검은 워크부츠

## 🏆 황금 공식
**입 움직임 공식 (EP.1 검증):**
```
Natural expressive facial animation: mouth moves with lively
talking-style motion, [씬별 감정 키워드], animated emotion
throughout. Not specific lip sync, just natural animated expression.
```
씬별 감정 키워드: 인사="smiling with excited greeting energy" / 설명="thoughtful explaining expression" / 놀람="amazed star-eyed excitement" / 작업="focused concentration" / 성공="joyful amazed cheering with star eyes" / 엔딩="warm farewell expression"

**오디오 공식 (일본어 방지):**
```
AUDIO: [환경음 설명]. NO dialogue, NO voices, NO music.

NO subtitles, NO text.
```

## 🎨 스타일
기본: `Korean webtoon chibi style, cel-shaded, teal-orange grading, smooth 60fps animation`
- 옵션 A 기본 웹툰(정비 씬): `Korean webtoon style, cel-shaded, teal-orange grading`
- 옵션 B 큐티 광고(제품/변신): `Korean webtoon chibi kawaii style, cute commercial aesthetic, cel-shaded, pastel colors with sparkles`
- 옵션 C 시네마틱 리얼(완성/엔딩): `Korean webtoon style, cel-shaded, cinematic automotive photography aesthetic, natural lighting`
- 옵션 D 하이브리드(추천): 큐티 시작 + 리얼 엔딩 (EP.2 성공)

큐티 강도 3단계: 은은(gentle sparkle/soft pastel/subtle blush, 진행 씬) / 기본(pastel+sparkles/blush, 작업·제품 씬) / 폭발(rainbow confetti/hearts everywhere/magical burst, **클라이맥스만 1~2회**). 과한 파스텔 지양, 톤 통일.

## 📝 프롬프트 구조 (영어, 900~980자 최적)
```
[Vertical 9:16 composition. 또는 16:9 cinematic composition.]
Setting: [배경/환경/분위기]
[캐릭터 동작] Moobie [포즈]: [치비 풀 스펙]
Natural expressive facial animation: mouth moves with [감정]. Not specific lip sync, just natural animated expression.
Character fully integrated: [조명/그림자 매칭]
Camera: [카메라 워크 — 씬마다 다르게]
Korean webtoon [chibi/cute commercial] style, cel-shaded, [그레이딩], smooth 60fps animation, [9:16 vertical 또는 16:9].
8 seconds, 60fps, [9:16 vertical 또는 16:9].
AUDIO: [환경음]. NO dialogue, NO voices, NO music.

NO subtitles, NO text.
@dc42431d-bee7-42d4-bd26-852f693aecaf
```
길이: 800~1000자(최적 900~980). 500자 미만=디테일 부족, 1200자 초과=AI 혼동.

## ⚡ 연출 기법
1. 분할구도(split screen): 리액션+상황 동시. "Anime split screen composition with dynamic diagonal divide… LEFT SIDE:… RIGHT SIDE:…"
2. 플래시 프레임: "Bright white flash frame filling entire screen for split-second, then radiating outward with rainbow energy burst."
3. 치비 변형(SD mode): "Brief chibi transformation moment when she celebrates - instantly becomes tiny chibi form doing happy dance."
4. 스피드 라인: "Manga-style speed lines radiating outward, motion blur on movement."
5. First/Last Frame(Seedance 2.0): 시작/끝 이미지 → 변화 자동 생성 (탈거·장착)
6. 언박싱 🎁: 박스등장→플랩→뽁뽁이→공개. "Chibi Moobie opens cardboard shipping box, pulls back bubble wrap and tissue paper, the [제품] is revealed with dramatic reveal moment. Star-eyed amazed reaction."

## ⚙️ Seedance 설정
- Model: Seedance 2.0 Pro / Frame Rate: 60fps / Motion: 7-9 / Duration: 8s per scene
- 세로 쇼츠(기본): 9:16, 1080×1920 / 가로 롱폼: 16:9, 1920×1080
- 시드: 씬1 만족 시 기록 → 나머지 동일 시드. 양식 "EP.[N]_[차량]_[날짜]_[시드]"
- 레퍼런스 순서 고정: Slot1 무비시트 / Slot2~ 씬별 이미지

## 🎯 엘리멘트
특정 제품 고정 참조(여러 씬 동일 재현). Higgsfield→Element→Create→이미지 업로드→이름 `[제품]_[용도]`→ID 기록. 프롬프트: `The [제품] (@element_name - use exact design from element reference: [핵심 특징])…`. 등록 추천: 다운파이프·범퍼·휠·로고·간판·공구.

## ⚠️ 일본어 방지
❌ 금지: MAPPA / Ufotable / Japanese animation / premium anime / sakuga / otaku → 일본어 성우 자동 생성
✅ 안전: anime girl / Korean webtoon style / cel-shaded / Korean manhwa / animated expression / 2D illustration / chibi style / kawaii cute commercial style
핵폭탄(최후): `AUDIO: Character is COMPLETELY SILENT - NO speech in ANY language (no Japanese, no Korean, no English voice acting). NO dubbing. NO vocalizations. Environmental sounds only.`
Seedance "Generate Audio"/"Native Audio" 옵션 → **반드시 OFF**

## 🎬 편집 & 업로드
- TTS: Naver Clova Dubbing "다인"(밝고 친근 20대 여성). 씬별 감정/속도: 오프닝 밝게1.0x / 설명 0.95x / 감탄 1.0x / 작업 0.95x / 성공 1.05x / 엔딩 0.95x
- CapCut: 세로 1080×1920 60fps. 오디오밸런스 나레이션100%/BGM20%/환경음30-40%. 전환 0.3초 크로스페이드, 스타일전환 0.5초 화이트플래시, 엔딩 페이드아웃.
- 자막: 세로=나눔스퀘어 Round Bold 80-100px 중앙하단 흰색+아웃라인 / 가로=60-80px 하단.
- 제목: 롱폼 `EP[N] - 귀염뽀짝 무비의 [차종] [작업명] ✨ #무브모터스` / 쇼츠 `[차종] [작업] [초]초 변신! #shorts`
- 설명: 인사/작업포인트/효과/매장정보/링크/해시태그. 재생목록 "무비의 튜닝 일기 🎬".
- 썸네일: BEFORE/AFTER 대비 + 무비 + 큰 텍스트 + 포인트컬러(빨강/파랑/핑크).

## 📚 EP 히스토리
- EP.1 아반떼N 번웨이 다운파이프: 가로16:9/24fps/56초(8×7). 심플 프롬프트·Korean webtoon·일본어없음 검증. ✅
- EP.2 벤츠 CLA45 AMG룩 바디킷: 세로9:16/60fps/48초(8×6). 큐티1-4+리얼5-6 하이브리드, 엘리멘트, First/Last, 언박싱(씬3). 치비 2-3등신 명시 필수, 스타일 강도조절 중요.

## 💡 핵심 교훈
"심플한 게 최고" — 검증된 공식만, 실험은 한 요소씩, 성공 패턴은 고정. 치비 2-3등신 고정 / Korean webtoon 명시 / 입움직임·AUDIO 공식 그대로 / 60fps / 엘리먼트·시드·레퍼런스순서 고정.

**© 2026 Move Motors | 부산 전문 튜닝샵 | 📞 010-5858-6046**

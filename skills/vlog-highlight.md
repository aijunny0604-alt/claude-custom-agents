---
description: 단일 긴 영상 → 자동 STT(음성→텍스트) → 대화 하이라이트 자동 선별 → B-roll(이동/풍경) 자동 끼워넣기 → 자연스러운 유튜브 브이로그 완성. 30분~2시간 원본도 한 번에. 2026-05-21 사장님(태욱이 형) 영상 42분 → 19분 브이로그 작업에서 검증된 패턴.
argument-hint: <영상 파일 절대경로> (예: "C:\Users\MOVEAM_PC\Downloads\원본.mp4")
---

# /vlog-highlight — 단일 영상 자동 하이라이트 브이로그 편집 (v1.0)

긴 원본 영상(30분~2시간)을 자동으로 듣고 → 대화 하이라이트 찾아내 → B-roll 사이사이 끼워서 자연스러운 유튜브 브이로그로 만들어주는 에이전트.

`/auto-vlog`(여러 클립 합치기)와 구별: 이건 **단일 긴 영상**에서 하이라이트 컷만 뽑는 시나리오.

## 핵심 원칙 (절대 위반 금지)

1. **원본 오디오 그대로 보존** — 대화가 핵심. `anullsrc` 무음 강제 금지.
2. **대화만 잘라 붙이지 마라** — 토킹헤드 느낌 남. B-roll(이동/풍경/행사장) 25~35% 비중으로 섞어야 브이로그 흐름.
3. **시간순 유지** — 하이라이트만 골라도 원본 시간 순서대로 배치 (브이로그는 스토리).
4. **컷 시작/끝은 대화 호흡 단위** — 문장 중간에서 자르면 어색. STT 세그먼트 경계 기준.
5. **B-roll은 짧게** — 한 컷당 15~40초. 너무 길면 지루.

## 사용자 인자

- **$ARGUMENTS**: 영상 파일 절대 경로
  - 큰따옴표 유무 모두 허용
  - 공백·한글·특수문자 포함 경로 정상 처리

## 사전 환경 (1회 설치 후 영구)

```bash
# faster-whisper + GPU 라이브러리 (Windows + NVIDIA GPU 가정)
python -m pip install faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"
```

설치 확인:
```bash
python -c "from faster_whisper import WhisperModel; print('OK')"
```

GPU 없으면 자동 CPU fallback (medium 모델, 42분 영상 약 15~17분 소요).

## 실행 절차 (반드시 순서대로)

### 0. 사전 점검

1. `$ARGUMENTS` 비었으면 → 파일 경로 1회 묻기
2. 파일 존재 확인:
   ```bash
   ls -la "<경로>"
   ```
3. 영상 메타:
   ```bash
   ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,channels:format=duration,size -of default=nw=1 "<경로>"
   ```
4. ffmpeg + Python + faster-whisper 모두 OK 확인

### 1. 작업 디렉토리 + 오디오 추출

```bash
WORK="/c/tmp/vlog_highlight"
mkdir -p "$WORK/cuts" "$WORK/preview"

# 16kHz mono WAV (Whisper 표준)
ffmpeg -y -i "<영상>" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$WORK/audio.wav"
```

42분 영상 → 약 80MB WAV. 추출 자체는 30초 이내 (실시간 ×1000 속도).

### 2. STT 실행 (헬퍼 스크립트 권장)

```bash
python C:\Users\MOVEAM_PC\claude-custom-agents\scripts\video_stt.py "$WORK/audio.wav" \
  --output "$WORK" \
  --model medium \
  --language ko
```

출력:
- `$WORK/segments.json` — 구간별 (start, end, text)
- `$WORK/transcript.txt` — 사람 읽기 좋은 타임스탬프 텍스트

처리 시간 가이드:
- GPU large-v3: 약 2~3분 (42분 영상)
- GPU medium: 약 1~2분
- CPU medium: 약 15~17분
- CPU small: 약 5~7분

### 3. 트랜스크립트 분석 → 하이라이트 후보 자동 선별

**Read 도구로 transcript.txt 전체 읽기** (큰 영상은 sed -n으로 부분 나눠 읽기).

다음 패턴을 하이라이트 후보로 마킹:

| 패턴 | 예시 |
|------|------|
| **명언/철학** | "제일 중요한 거지", "이런 모습 보여야 돼", "원산지보다 제조사가 중요해" |
| **유머/리액션** | 욕섬, 너스레, "야 형", 의외의 답변 ("담배") |
| **인물 등장** | 새 사람 인사, 이름 부르기, 대화 turn-taking |
| **결과/이벤트** | "꼴찌 했어", "1등 떨렸어", "트로피", 경기 결과 |
| **자기소개/일정** | "오늘은 어디 가서 뭐 합니다" |
| **마무리 CTA** | "수고하셨어요", "감사합니다" |

**제외 패턴:**
- 단순 반복 ("담배. 담배. 담배.")
- 의미 없는 단발 ("어." "응.")
- 통화/안 들리는 부분 (STT 결과 짧고 끊김)

### 4. B-roll 후보 자동 식별

STT 세그먼트에서 **30초 이상 침묵 구간** = B-roll 후보.

```bash
python C:\Users\MOVEAM_PC\claude-custom-agents\scripts\broll_detect.py "$WORK/segments.json" --min-gap 25
```

출력: `$WORK/broll_candidates.json` — 침묵 시작/끝 시간 + 추정 카테고리

**B-roll 프레임 미리보기 (필수)** — 각 후보의 중간 프레임 추출해 Read로 시각 확인:

```bash
for t in $(jq -r '.[] | .midpoint' "$WORK/broll_candidates.json"); do
  ffmpeg -y -ss $t -i "<영상>" -vframes 1 -vf "scale=480:-1" "$WORK/preview/t${t}.jpg" 2>/dev/null
done
```

확인 항목:
- 이동 풍경인가? (차 안, 길)
- 행사장 분위기인가? (사람·차들·부스)
- 액션 장면인가? (배틀·드리프트·트랙)
- 정적 장면인가? (포디움·시상)

부적합한 후보(검은 화면, 흔들림, 사장님 클로즈업만)는 제외.

### 5. 사용자 인터뷰 (AskUserQuestion)

다음 4개를 한 번에:

1. **목표 길이**: 5분 / 10분 / 15분 / 20분 이상
2. **출력 비율**: 가로 16:9 / 세로 9:16(쇼츠) / 둘 다
3. **하이라이트 관점** (multiSelect): 재미있는 대화 / 명언·특이행동 / 작업·이동 장면 / 주제 설명
4. **B-roll 비중**: 적게 (15%) / 적당히 (25%, 권장) / 많이 (35%) / 없음

### 6. 컷 구성안 자동 생성 + 사용자 컨펌

표 형식 구성안:

| # | 영상 시간 | 길이 | 타입 | 내용 |
|---|-----------|------|------|------|
| 1 | 0:05~0:40 | 35s | 🗣️ | 인트로 |
| 2 | 0:40~1:15 | 35s | 🎬 | B-roll: 이동 풍경 |
| 3 | 3:09~4:40 | 91s | 🗣️ | 핵심 대화 1 |
| ... | | | | |

배치 규칙:
- **시간순** 유지 (브이로그 흐름)
- 대화 컷 사이에 B-roll 1~2개 (전환 + 호흡)
- 인트로/아웃트로 명시 (셀카 멘트 또는 인사)
- 각 컷 길이: 대화 30~120초, B-roll 15~40초
- 총합이 목표 길이 ±10% 이내

**반드시 사용자 컨펌**: "이대로 진행할까요? 수정할 컷이나 추가/제외할 구간 있으면 알려주세요."

### 7. 컷 일괄 렌더링

```bash
SRC="<원본>"
OUT="$WORK/cuts"

render_cut() {
  local idx=$1 start=$2 dur=$3
  ffmpeg -y -ss "$start" -i "$SRC" -t "$dur" \
    -vf "scale=1920:1080" \
    -c:v libx264 -preset superfast -crf 21 -pix_fmt yuv420p -r 24 \
    -c:a aac -b:a 192k -ar 44100 -ac 2 \
    "$OUT/cut$(printf '%02d' $idx).mp4"
}

render_cut 1 5 35
render_cut 2 40 35
...
```

**주의:**
- `-ss` before `-i`: fast seek (keyframe, 약간 부정확하지만 빠름) — 브이로그 컷에는 충분
- 정확한 seek 필요하면 `-ss` after `-i` (느림)
- `-preset superfast` — 화질 약간 양보하고 속도 4~5배. 브이로그 OK
- 모든 컷 동일 사양 (1920×1080, 24fps, AAC 44100 stereo) — concat 호환

### 8. concat 합본

```bash
cd "$WORK" && ls cuts/ | sort | awk '{print "file '"'"'cuts/"$1"'"'"'"}' > concat.txt
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy "<출력경로>"
```

**Non-monotonous DTS 경고**: concat 시 발생할 수 있지만 재생 무관. 무시.

### 9. 검증 (필수)

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,channels:format=duration,size -of default=nw=1 "<출력>"
```

체크 항목:
- ✅ duration이 목표 길이 ±5초 이내
- ✅ video 1920×1080 (또는 1080×1920)
- ✅ **audio stream 존재** (size > 컷 개수 × 100KB)
- ✅ 컷 경계 5~7개 프레임 추출해 자막 잘 박혔는지/끊김 없는지 시각 확인

```bash
# 검증용 프레임 (각 컷 중간 시점)
for t in 20 100 300 500 800 1100; do
  ffmpeg -y -ss $t -i "<출력>" -vframes 1 -vf "scale=480:-1" "$WORK/preview/check_t${t}.jpg" 2>/dev/null
done
```

### 10. 결과 보고 + 후속 제안

**필수 보고:**
- 출력 절대 경로
- 길이/해상도/용량/오디오 트랙 유무
- 컷 구성 요약 (대화 N개 + B-roll M개)
- 핵심 컷 시간대 미리보기

**후속 제안:**
- 시청 후 컷 시간 미세 조정 → 해당 컷만 재렌더 + 재합본 (3분)
- 자막 추가 → STT segments.json 그대로 활용 가능
- 썸네일 후보 (가장 임팩트 있는 컷 시점)
- 쇼츠 버전 추가 (특정 컷만 1080×1920로 재가공)
- BGM 입히기 (대화 위주라면 BGM은 0.1~0.15 volume 권장)

## 자주 발생하는 함정 (이번 사장님 영상 작업에서 검증)

| 함정 | 증상 | 해결 |
|------|------|------|
| `cublas64_12.dll not found` | GPU STT 실행 실패 | `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12>=9` |
| Python 3.13에 faster-whisper 호환성 이슈 | 패키지 설치 에러 | Python 3.10 사용 권장 |
| CPU large-v3 모델 너무 느림 | 42분 영상 1시간+ | CPU는 medium + int8 + cpu_threads=8 |
| 대화만 잘라 붙임 | 토킹헤드, 브이로그 느낌 X | B-roll 25% 이상 필수 |
| 컷 중간이 문장 중간에서 끊김 | 어색한 편집 | STT 세그먼트 경계 기준 컷 |
| 시간순 무시하고 주제별 묶기 | 스토리 흐름 깨짐 | 무조건 시간순 |
| B-roll 후보를 시각 확인 없이 사용 | 검은 화면/흔들림 포함 | 프레임 미리보기 Read 필수 |
| -ss after -i 사용 | 4GB 영상에서 컷당 30초+ | -ss before -i (keyframe seek, 충분) |
| 컷별 다른 코덱/sample_rate | concat 실패 또는 동기화 깨짐 | 모든 컷 통일 사양 (h264, aac 44100 stereo) |
| 사용자 피드백 없이 완성 보고 | 시청 후 수정 요청 폭주 | 1차 시청 → 컷 조정 사이클 명시 |

## 헬퍼 스크립트

- `C:\Users\MOVEAM_PC\claude-custom-agents\scripts\video_stt.py` — 영상/오디오 → STT 자동 (GPU↔CPU fallback)
- `C:\Users\MOVEAM_PC\claude-custom-agents\scripts\broll_detect.py` — STT segments → B-roll 후보 자동 식별

## 금지 사항

- **GPU 라이브러리 설치 없이 CUDA 강제 시도 X** — `cublas64_12.dll` 에러 → 사용자에게 설치 안내 후 CPU fallback
- **인라인 STT 코드 작성 X** — `video_stt.py` 헬퍼 사용 (재사용 + 일관성)
- **B-roll 자동 선별 결과를 시각 확인 없이 채택 X** — 부적합 컷 섞이면 영상 망함
- **대화 컷 100%로 채우지 마라** — 단조로움. B-roll 비중 사용자가 0% 명시한 경우 외 필수
- **사용자 컨펌 없이 18컷 이상 렌더링하지 마라** — 시간/디스크 낭비. 구성안 컨펌 후 진행

## 출력 직후 필수

사용자 전역 CLAUDE.md 규칙대로 응답 말미에 bkit Feature Usage 블록 + 추천 명령어 줄 포함.

상황별 추천 명령어:
- 영상 완성 직후 → `/test-guide` (시청 체크), `/quick-fix` (컷 미세 조정)
- 자막 추가 필요 → 같은 폴더로 `/vlog-highlight` 재호출하면서 자막 옵션 켜기
- 쇼츠 버전 필요 → `/auto-vlog`로 핵심 컷만 골라 9:16 가공


---

## Phase X+1: Codex 대조 검증 게이트 (자동 — 선택 사항)

> 이 게이트는 v2.1부터 모든 J-AGENTS 에이전트에 공통 적용됩니다. **Codex CLI가 없으면 자동 스킵** 되므로 클로드 단독 환경에서도 그대로 동작합니다.

### 게이트 1단계: Codex 가용성 자동 체크

```bash
codex --version >/dev/null 2>&1 && echo "codex-ready" || echo "codex-missing"
```

- `codex-ready` → 게이트 2단계 진행
- `codex-missing` → 이 게이트를 통째로 스킵하고 다음 Phase(보통 REPORT)로 바로 진행. 사용자에게 "Codex 비활성 → 클로드 단독 결과만 보고합니다" 한 줄만 안내.

### 게이트 2단계: Codex에 2차 의견 요청 (대조 검증)

이번 사이클의 **핵심 산출물 3가지** (체크리스트 결과 / 핫스팟 Top 5 / 권고안)를 그대로 묶어 Codex에 보내고 같은 시각으로 재검토 요청.

- 호출: `Skill codex:rescue` 사용. 프롬프트 예시:
  > "방금 클로드가 [에이전트명] 에이전트로 도출한 아래 결과를 같은 기준으로 한 번 더 검토해줘.
  > - 누락된 항목 있는지
  > - 우선순위가 잘못 매겨진 항목 있는지
  > - 더 안전하거나 더 효율적인 대안이 있는지
  > 짧게 답변 (불릿 5개 이내)."

- Codex 응답이 1분 안에 안 오면 → 타임아웃 처리, "Codex 응답 없음 — 클로드 단독 권고로 진행" 명시 후 다음 Phase로.

### 게이트 3단계: 두 의견 합치표 (필수)

| 항목 | 클로드 1차 결과 | Codex 2차 의견 | 합치 / 충돌 | 최종 권고 |
|---|---|---|---|---|
| 핫스팟 #1 | ... | ... | ✅ 합치 | 클로드 권고 그대로 진행 |
| 핫스팟 #2 | ... | ... | ⚠️ 충돌 | 사용자에게 둘 중 선택 요청 |
| 누락 발견 | (없음) | Codex가 추가 항목 1개 제시 | ➕ 보강 | 보강안 함께 보고 |

- **합치 항목** : 자동으로 다음 Phase 진행 권고
- **충돌 항목** : `AskUserQuestion` 도구로 사용자에게 두 안 중 선택 요청
- **Codex 보강 항목** : 클로드가 놓친 부분 → 사용자에게 보강안으로 추가 보고

### 게이트 4단계: 최종 보고에 반영

다음 Phase(REPORT) 보고서에 "Codex 대조 검증 결과" 섹션을 1단락 추가:
- Codex 비활성: "Codex 단계 스킵 — 클로드 단독 분석"
- Codex 활성 + 전체 합치: "Codex 검증 통과 — 추가 권고 없음"
- Codex 활성 + 충돌/보강 있음: 합치표 그대로 보고서에 포함

### 핵심 원칙

1. **Codex 부재 = 무조건 스킵**. 패치 이후에도 클로드 단독 동작 100% 보장.
2. **Codex 의견은 권고일 뿐 자동 적용 금지**. 충돌 시 항상 사용자 결정 우선.
3. **타임아웃 1분**. Codex가 멈춰도 메인 에이전트가 막히지 않도록.
4. **대조 결과는 반드시 보고서에 기록**. 추적 가능성 유지.

---

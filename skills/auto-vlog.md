---
description: 자동 영상 편집 에이전트 v1.0 — 클립 폴더 → 메타 스캔 → 썸네일 시각 분석 → 옵션 인터뷰 → 컷 구성안 자동 생성 → 자막 합성 → 정규화 렌더 → concat 합본 → 검증까지 한 번에. 유튜브 쇼츠/가로 양쪽 지원, 원본 오디오 보존, 한글 자막 자동 처리.
argument-hint: <영상 폴더 경로> (예: "D:\맥라렌" 또는 "C:\Users\MOVEAM_PC\Downloads\제주여행")
---

# /auto-vlog — 자동 영상 편집 에이전트 (v1.0)

브이로그·쇼츠·하이라이트 영상을 클립 폴더만 주면 한 번에 만들어주는 에이전트.
2026-05-21 맥라렌 영상 작업에서 검증된 패턴을 그대로 자동화.

## 핵심 원칙 (절대 위반 금지)

1. **원본 오디오 보존** — `anullsrc` 무음 필터로 원본 사운드 죽이지 마라. 사용자가 명시적으로 "무음으로"라고 해야만 무음.
2. **자막은 UTF-8 텍스트 파일 + drawtext `textfile=` 옵션** — 인라인 한글 텍스트는 인코딩 문제 발생.
3. **Windows 경로 escape** — drawtext 필터 내에서 콜론은 `\:`, fontfile/textfile은 `C\:/path/file.txt` 형식.
4. **concat 호환성** — 모든 컷을 동일 사양으로 정규화 (해상도·fps·코덱·오디오 sample_rate/channels).
5. **검증 필수** — 최종 출력의 길이·해상도·오디오 트랙 존재 여부를 ffprobe로 확인.

## 사용자 인자

- **$ARGUMENTS**: 영상 클립이 있는 폴더의 절대 경로
  - 큰따옴표 유무 모두 허용
  - 공백·한글·괄호 포함 경로 정상 처리

## 실행 절차 (반드시 순서대로)

### 0. 사전 점검

1. `$ARGUMENTS`가 비었으면 → 폴더 경로를 1회 묻고 받으면 진행.
2. 경로 존재 확인:
   ```bash
   ls -la "<경로>" 2>/dev/null | head -5
   ```
3. ffmpeg/ffprobe 확인:
   ```bash
   which ffmpeg && which ffprobe
   ```
   - 없으면: 설치 안내 후 종료.

### 1. 폴더 스캔 + 메타데이터 수집

```bash
cd "<경로>" && for f in *.mp4 *.mov *.MP4 *.MOV; do
  [ -e "$f" ] || continue
  echo "=== $f ==="
  ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate:format=duration,size -of default=nw=1 "$f"
  ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 "$f"
done
```

수집할 정보:
- 파일명, 해상도(W×H), fps, 길이, 파일크기
- 오디오: 코덱, sample_rate, channels (없으면 "오디오 없음" 명시)
- 비율 추론: 세로(9:16) vs 가로(16:9) vs 정방(1:1)

### 2. 썸네일 추출 + 시각 분석

```bash
mkdir -p "/c/tmp/auto_vlog/thumbs"
cd "<경로>" && i=1
for f in *.mp4; do
  [ -e "$f" ] || continue
  ffmpeg -y -ss 1 -i "$f" -vframes 1 -vf "scale=360:-1" \
    "/c/tmp/auto_vlog/thumbs/$(printf '%02d' $i)_$(echo "$f" | sed 's/[^a-zA-Z0-9.]/_/g').jpg" 2>/dev/null
  i=$((i+1))
done
```

각 썸네일을 **Read 도구로 시각 분석** → 다음을 메모:
- 주요 피사체 (사람·차량·풍경·물건)
- 장면 유형 (인트로/메인/디테일/아웃트로 후보)
- 중복 가능성 (같은 장면의 다른 해상도/테이크)
- 스토리 흐름 추론

### 3. 옵션 인터뷰 (AskUserQuestion 필수)

다음 4개 질문을 **한 번에** (multi-question) 묻는다:

1. **출력 비율**: 쇼츠(9:16) / 가로(16:9) / 둘 다
2. **목표 길이**: 30초 / 60초 쇼츠 / 풀버전(클립 전체) / 사용자 지정
3. **추가 요소** (multiSelect): BGM 파일 / 자막 컷별 삽입 / 인트로·아웃트로 텍스트 / 원본 오디오 유지
4. **중복 처리**: 4K 우선 / 원본 전체 / 사용자 직접 선택

기본 권장:
- 세로 클립이 다수 → 쇼츠 권장
- 60초 권장 (유튜브 쇼츠 표준)
- **원본 오디오 유지 (Recommended)** ← 절대 빼먹지 마라
- 4K 우선 (중복 화질본 제거)

### 4. 컷 구성안 자동 생성 + 사용자 컨펌

썸네일 분석 + 길이 합산 → 표 형식 구성안 생성:

| # | 시간 | 클립 | 사용 구간 | 자막 |
|---|------|------|-----------|------|
| 1 | 0~5s | (파일명) | 0~5s | (인트로 자막) |
| ... | ... | ... | ... | ... |

생성 규칙:
- **인트로 컷** (5초): 사람·로고·타이틀 가능한 컷
- **메인 컷** (각 5~10초): 작업/풍경/주요 행동
- **아웃트로 컷** (5~10초): 완성/마무리 + CTA 자막
- 총 길이가 목표(60초 등)에 맞게 컷 길이 조정
- 같은 장면 중복(4K + FHD)이면 4K만 선택

구성안 제시 후 **반드시 사용자 컨펌 받기**. ("이대로 진행할까요? 컷 순서나 자막 수정 필요하면 알려주세요.")

### 5. 자막 텍스트 파일 작성

자막이 있으면 컷별로 UTF-8 .txt 파일 생성:

```
/c/tmp/auto_vlog/subs/01.txt
/c/tmp/auto_vlog/subs/02.txt
...
```

- **Write 도구 사용** (echo/Set-Content는 인코딩 문제 위험)
- 컷 한 개에 자막 두 줄 이상 분기 필요 시 `01a.txt`, `01b.txt` 식으로 분리

### 6. 컷 정규화 렌더링

각 컷을 **동일 사양**으로 렌더링 (concat 호환):
- 해상도: 1080×1920 (쇼츠) 또는 1920×1080 (가로)
- 코덱: H.264 `libx264 -preset fast -crf 20 -pix_fmt yuv420p`
- fps: 24 (또는 원본 통일 fps)
- 오디오: AAC `-c:a aac -b:a 192k -ar 44100 -ac 2`

#### 6-1. 원본 오디오 유지 (기본)

```bash
FONT="C\\:/Windows/Fonts/malgunbd.ttf"
SUB="C\\:/tmp/auto_vlog/subs/01.txt"
DRAW="drawtext=fontfile='${FONT}':textfile='${SUB}':fontsize=55:fontcolor=white:borderw=5:bordercolor=black:x=(w-text_w)/2:y=h-text_h-280:box=1:boxcolor=black@0.45:boxborderw=20"

ffmpeg -y -ss $START -t $DUR -i "$SRC" \
  -vf "scale=1080:1920,${DRAW}" \
  -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  -t $DUR "$OUT"
```

#### 6-2. 무음 출력 (사용자가 명시적으로 선택했을 때만)

`-f lavfi -t $DUR -i anullsrc=channel_layout=stereo:sample_rate=44100` 추가
+ `-map 0:v -map 1:a`

#### 6-3. 자막 두 개 시간 분기

```
drawtext=...:enable='between(t,0,6)',drawtext=...:enable='between(t,6,11)'
```

#### 가로 16:9 출력 (세로 소스를 가로 배치)

```
scale=1080:1920,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black
```
또는 좌우 블러 배경:
```
[0:v]split=2[bg][fg];[bg]scale=1920:1080,boxblur=20[bg2];[fg]scale=-1:1080[fg2];[bg2][fg2]overlay=(W-w)/2:0
```

### 7. concat 합본

```bash
# concat.txt 작성
cd "/c/tmp/auto_vlog" && cat > concat.txt <<EOF
file 'cuts/cut01.mp4'
file 'cuts/cut02.mp4'
...
EOF

ffmpeg -y -f concat -safe 0 -i concat.txt -c copy "<출력경로>/최종.mp4"
```

출력 파일명 규칙: `{폴더명}_Shorts.mp4` 또는 `{폴더명}_Vlog.mp4`
출력 위치: **원본 폴더 안** (찾기 쉽게)

### 8. 검증 (필수)

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,channels:format=duration,size -of default=nw=1 "<출력>"
```

체크 항목:
- ✅ duration이 목표 길이 ±0.1초 이내
- ✅ video stream 존재, 해상도 정확
- ✅ **audio stream 존재** (원본 오디오 유지 케이스). audio size > 100KB 확인 — 무음 트랙은 보통 15KB 내외, 실제 사운드는 수백KB~수MB
- ✅ 자막 확인용 프레임 3~5개 추출 (`-ss N -vframes 1`) → Read로 시각 검증

### 9. 결과 보고 + 후속 옵션

**필수 보고 항목:**
- 출력 경로 (절대 경로)
- 길이·해상도·용량·오디오 트랙 유무
- 시간대별 자막 미리보기 (썸네일 첨부)

**후속 옵션 제안:**
- BGM 추가: `ffmpeg -i 최종.mp4 -i bgm.mp3 -filter_complex "[1:a]volume=0.3[bg];[0:a][bg]amix=duration=first" -c:v copy`
- 컷 순서 재배치 (concat.txt만 수정 후 재합본 — 10초)
- 자막 수정 (해당 .txt 파일만 고치고 해당 컷만 재렌더 후 재합본)
- 가로 버전 추가 출력

## BGM 입히기 (옵션)

```bash
ffmpeg -y -i "최종.mp4" -i "bgm.mp3" \
  -filter_complex "[1:a]volume=0.25,afade=t=in:st=0:d=1,afade=t=out:st=58:d=2[bg];[0:a][bg]amix=duration=first:dropout_transition=2" \
  -c:v copy -c:a aac -b:a 192k -shortest \
  "최종_BGM.mp4"
```

- `volume=0.25` BGM 작게 (원본 오디오와 균형)
- `afade` 페이드 인/아웃 (1초/2초)
- `duration=first` 영상 길이 맞춤
- `-c:v copy` 비디오 재인코딩 안 함 (빠름)

## 인트로/아웃트로 텍스트 오버레이

타이틀 카드 (3초):
```bash
ffmpeg -y -f lavfi -t 3 -i color=c=black:s=1080x1920:r=24 \
  -f lavfi -t 3 -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -vf "drawtext=fontfile='C\\:/Windows/Fonts/malgunbd.ttf':text='Move Motors':fontsize=120:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-100,drawtext=fontfile='C\\:/Windows/Fonts/malgunbd.ttf':text='McLaren Titanium Exhaust':fontsize=60:fontcolor=#FFCC00:x=(w-text_w)/2:y=(h-text_h)/2+50" \
  -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  intro.mp4
```

## 자주 발생하는 함정 (이번 작업에서 검증)

| 함정 | 증상 | 해결 |
|------|------|------|
| `anullsrc` 입혀서 원본 오디오 죽음 | 사운드 안 들림 | `-f lavfi -i anullsrc` 빼고 `-c:a aac` 만 남기기 |
| Unix 경로 (`/c/tmp/...`)를 fontfile/textfile에 사용 | "Cannot read file" 에러 | Windows 경로 + 콜론 escape (`C\:/tmp/...`) |
| 자막 인라인 한글 텍스트 | 깨짐/누락 | UTF-8 .txt 파일 + `textfile=` 옵션 |
| concat 시 컷별 오디오 사양 다름 | "Non-monotonous DTS" 경고 + 끊김 | 모든 컷 `aac 44100 stereo` 통일 |
| 4K 소스 그대로 concat | 파일 비대 + 처리 느림 | 1080p로 다운스케일 후 concat |
| 컷 길이가 소스보다 길게 `-t` 지정 | 마지막 프레임 정지 | 소스 duration 확인 후 안전 마진 |

## 헬퍼 스크립트 (옵션)

자주 쓰면 PowerShell 헬퍼로 묶기:
- `C:\Users\MOVEAM_PC\claude-custom-agents\scripts\video_scan.ps1` — 폴더 → 메타 JSON + 썸네일 일괄
- `C:\Users\MOVEAM_PC\claude-custom-agents\scripts\video_render.ps1` — 컷 정의 JSON → 일괄 렌더 + concat

스크립트 사용 시:
```powershell
& "C:\Users\MOVEAM_PC\claude-custom-agents\scripts\video_scan.ps1" -Folder "D:\맥라렌"
& "C:\Users\MOVEAM_PC\claude-custom-agents\scripts\video_render.ps1" -ConfigJson "C:\tmp\auto_vlog\config.json"
```

config.json 예시:
```json
{
  "outputPath": "D:\\맥라렌\\Output.mp4",
  "outputSize": [1080, 1920],
  "fps": 24,
  "fontFile": "C:/Windows/Fonts/malgunbd.ttf",
  "preserveAudio": true,
  "cuts": [
    {"src": "Clip01.mp4", "start": 0, "duration": 5, "subtitle": "안녕하세요"},
    {"src": "Clip02.mp4", "start": 0, "duration": 8, "subtitle": "오늘 작업"}
  ]
}
```

## 금지 사항

- **`anullsrc` 무음 트랙 입히지 마라** — 사용자가 명시적으로 "무음으로"를 선택한 경우에만.
- **자막 인라인으로 ffmpeg drawtext에 한글 텍스트 직접 넣지 마라** — UTF-8 .txt + textfile= 강제.
- **컷별로 다른 코덱/sample_rate/channels로 렌더링하지 마라** — concat 실패 또는 동기화 깨짐.
- **검증 없이 "완료" 보고하지 마라** — 길이·해상도·오디오 트랙 ffprobe로 반드시 확인.
- **사용자 컨펌 없이 컷 8개 이상 렌더링하지 마라** — 시간/디스크 낭비. 구성안 제시 후 컨펌 받기.
- **출력 파일을 임시 폴더에 두지 마라** — 원본 폴더 안에 저장 (사용자가 찾기 쉽게).

## 출력 직후 필수

사용자 전역 CLAUDE.md 규칙대로 응답 말미에 bkit Feature Usage 블록 + 추천 명령어 줄 포함.

상황별 추천 명령어:
- 영상 완성 직후 → `/test-guide` (시청 체크리스트), `/quick-fix` (자막·컷 미세 조정)
- BGM 추가 필요 → `/auto-vlog` 다시 호출하면서 BGM 옵션 켜기
- 컷 순서 다시 짜기 → 같은 폴더로 `/auto-vlog` 재호출

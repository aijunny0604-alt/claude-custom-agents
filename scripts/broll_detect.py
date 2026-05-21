"""
broll_detect.py
STT segments.json → 침묵 구간(B-roll 후보) 자동 식별

Usage:
  python broll_detect.py <segments.json> [--min-gap 25] [--output broll.json]

기준:
- 인접 세그먼트 사이 gap이 min-gap초 이상이면 B-roll 후보
- 단발 단어만 있는 구간(텍스트 짧고 sparse)도 B-roll 후보
- 시작/끝 buffer 0.5초 여유 (말꼬리 자르지 않게)

출력 JSON 형식:
[
  {
    "start": 165.0,
    "end": 189.0,
    "duration": 24.0,
    "midpoint": 177.0,
    "type": "silent_gap" | "sparse_chatter",
    "context_before": "직전 세그먼트 텍스트",
    "context_after": "직후 세그먼트 텍스트"
  },
  ...
]

2026-05-21 사장님 영상 작업에서 검증된 패턴.
"""
import argparse
import json
import sys
from pathlib import Path

# Windows 콘솔 한글 출력 깨짐 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def detect_silent_gaps(segments: list, min_gap: float, buffer: float = 0.5):
    """인접 세그먼트 사이 침묵 구간 감지"""
    candidates = []
    for i in range(len(segments) - 1):
        cur = segments[i]
        nxt = segments[i + 1]
        gap = nxt["start"] - cur["end"]
        if gap >= min_gap:
            start = round(cur["end"] + buffer, 2)
            end = round(nxt["start"] - buffer, 2)
            duration = round(end - start, 2)
            if duration < 5:
                continue
            candidates.append({
                "start": start,
                "end": end,
                "duration": duration,
                "midpoint": round((start + end) / 2, 2),
                "type": "silent_gap",
                "context_before": cur["text"][:80],
                "context_after": nxt["text"][:80],
            })
    return candidates


def detect_sparse_chatter(segments: list, window: float = 30.0, max_words: int = 8):
    """짧고 sparse한 구간 (배틀 관전 중 단발 리액션 등)"""
    candidates = []
    if not segments:
        return candidates

    i = 0
    while i < len(segments):
        win_start = segments[i]["start"]
        win_end = win_start + window
        total_words = 0
        last_idx = i
        for j in range(i, len(segments)):
            if segments[j]["start"] > win_end:
                break
            total_words += len(segments[j]["text"].split())
            last_idx = j

        actual_end = segments[last_idx]["end"]
        if last_idx > i and total_words <= max_words and (actual_end - win_start) >= 20:
            candidates.append({
                "start": round(win_start, 2),
                "end": round(actual_end, 2),
                "duration": round(actual_end - win_start, 2),
                "midpoint": round((win_start + actual_end) / 2, 2),
                "type": "sparse_chatter",
                "context_before": segments[i]["text"][:80],
                "context_after": segments[last_idx]["text"][:80],
            })
            i = last_idx + 1
        else:
            i += 1

    return candidates


def merge_overlapping(candidates: list):
    """시간 겹치는 후보 병합"""
    if not candidates:
        return []
    candidates.sort(key=lambda c: c["start"])
    merged = [candidates[0]]
    for c in candidates[1:]:
        last = merged[-1]
        if c["start"] <= last["end"]:
            last["end"] = max(last["end"], c["end"])
            last["duration"] = round(last["end"] - last["start"], 2)
            last["midpoint"] = round((last["start"] + last["end"]) / 2, 2)
            if c["type"] != last["type"]:
                last["type"] = "mixed"
        else:
            merged.append(c)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segments", help="segments.json 경로")
    ap.add_argument("--min-gap", type=float, default=25.0,
                    help="최소 침묵 길이(초). 기본 25초")
    ap.add_argument("--max-sparse-words", type=int, default=8,
                    help="30초 윈도우 내 단어 수 이 이하면 sparse")
    ap.add_argument("--output", default=None,
                    help="결과 저장 경로 (기본: segments.json 옆 broll_candidates.json)")
    args = ap.parse_args()

    seg_path = Path(args.segments).resolve()
    if not seg_path.exists():
        print(f"[error] 파일 없음: {seg_path}", file=sys.stderr)
        sys.exit(1)

    segments = json.loads(seg_path.read_text(encoding="utf-8"))
    if not isinstance(segments, list) or not segments:
        print("[error] 빈 segments", file=sys.stderr)
        sys.exit(1)

    print(f"[scan] {len(segments)}개 세그먼트 분석 중...", flush=True)

    silent = detect_silent_gaps(segments, args.min_gap)
    sparse = detect_sparse_chatter(segments, max_words=args.max_sparse_words)
    candidates = merge_overlapping(silent + sparse)

    out_path = Path(args.output).resolve() if args.output else seg_path.parent / "broll_candidates.json"
    out_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[result] B-roll 후보 {len(candidates)}개 (침묵 {len(silent)}, sparse {len(sparse)})", flush=True)
    print(f"[result] 저장: {out_path}", flush=True)

    for c in candidates:
        print(f"  {c['start']:7.1f}~{c['end']:7.1f}s ({c['duration']:5.1f}s) [{c['type']:14}] "
              f"midpoint={c['midpoint']:7.1f}s")
        print(f"    이전: {c['context_before']}")
        print(f"    이후: {c['context_after']}")


if __name__ == "__main__":
    main()

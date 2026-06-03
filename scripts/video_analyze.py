# -*- coding: utf-8 -*-
r"""
Team FERVID 블로그용 영상(배기음 등) 분석 스크립트.

사용법:
    python video_analyze.py <video_path>

동작:
- 같은 폴더의 `_video\<영상명>\` 에 균등 간격 프레임(frame_NN.jpg) 추출 (시각 분석용)
- 오디오 음압/주파수 특성 분석 → analysis.json 저장 + stdout JSON 출력
  · overall_mean_db / overall_max_db : 전체 평균·피크 음압
  · low_band_mean_db (≤250Hz) vs high_band_mean_db (≥2kHz) : 저음/고음 강조 판단
  · segment_mean_db : 영상 3등분 구간별 평균 음압(공회전→가속 변화 추정)

주의: 이 스크립트는 '소리의 크기/대역'을 수치로만 뽑는다. 실제 청취 감상이 아니다.
본문은 이 수치 + 프레임 화면을 근거로 쓰되, 들어본 척 과장하지 말 것.
"""

import json
import os
import re
import subprocess
import sys


def sh(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="ignore")


def vol(path, af=None, ss=None, t=None):
    cmd = ["ffmpeg"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    if t is not None:
        cmd += ["-t", str(t)]
    cmd += ["-i", path]
    cmd += ["-af", (af + ",volumedetect") if af else "volumedetect"]
    cmd += ["-f", "null", "-"]
    out = sh(cmd).stderr or ""
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out)
    x = re.search(r"max_volume:\s*(-?[\d.]+) dB", out)
    return (float(m.group(1)) if m else None, float(x.group(1)) if x else None)


def main():
    if len(sys.argv) < 2:
        print("Usage: python video_analyze.py <video_path>")
        sys.exit(1)
    video = sys.argv[1]
    if not os.path.exists(video):
        print(json.dumps({"error": "no file", "video": video}, ensure_ascii=False))
        sys.exit(1)

    folder = os.path.dirname(video)
    name = os.path.splitext(os.path.basename(video))[0]
    outdir = os.path.join(folder, "_video", name)
    os.makedirs(outdir, exist_ok=True)

    # duration
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video])
    try:
        dur = float((r.stdout or "0").strip())
    except ValueError:
        dur = 0.0

    # frames: 최대 8장 균등 간격
    n = 8
    fps = max(0.2, min(1.0, n / dur)) if dur > 0 else 0.5
    sh(["ffmpeg", "-y", "-i", video, "-vf", f"fps={fps}", "-frames:v", str(n),
        "-q:v", "3", os.path.join(outdir, "frame_%02d.jpg")])
    frames = sorted(os.path.join(outdir, f) for f in os.listdir(outdir) if f.startswith("frame_"))

    overall_mean, overall_max = vol(video)
    low_mean, _ = vol(video, af="lowpass=f=250")
    high_mean, _ = vol(video, af="highpass=f=2000")

    segs = []
    if dur > 3:
        third = dur / 3.0
        for i in range(3):
            m, _ = vol(video, ss=i * third, t=third)
            segs.append(m)

    result = {
        "video": video,
        "duration_sec": round(dur, 1),
        "frame_count": len(frames),
        "frames": frames,
        "overall_mean_db": overall_mean,
        "overall_max_db": overall_max,
        "low_band_mean_db": low_mean,
        "high_band_mean_db": high_mean,
        "segment_mean_db": segs,
        "hint": "low>high면 저음 강조, high>low면 고음 강조. segment가 뒤로 갈수록 크면 가속 시 음압 상승.",
    }
    with open(os.path.join(outdir, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

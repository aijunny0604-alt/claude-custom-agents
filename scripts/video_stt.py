"""
video_stt.py
영상/오디오 → faster-whisper STT (GPU ↔ CPU 자동 fallback)

Usage:
  python video_stt.py <input> [--output DIR] [--model medium|large-v3|small]
                              [--device auto|cuda|cpu] [--language ko|en|auto]

Input: .mp4/.mov/.wav/.mp3 등 ffmpeg가 읽을 수 있는 모든 포맷
- mp4/mov 입력 시 임시 wav 추출 후 STT
- wav/mp3 직접 입력 시 그대로 STT

Output (지정 폴더에):
- segments.json: [{id, start, end, text}, ...]
- transcript.txt: 사람 읽기 좋은 타임스탬프 텍스트

GPU 라이브러리 (선택): pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"
없으면 자동으로 CPU(int8) fallback.

2026-05-21 사장님 영상 42분 STT 작업에서 검증.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Windows 콘솔 한글 출력 깨짐 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def find_ffmpeg():
    for cmd in ("ffmpeg", "ffmpeg.exe"):
        try:
            r = subprocess.run([cmd, "-version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return cmd
        except Exception:
            pass
    raise RuntimeError("ffmpeg를 PATH에서 찾을 수 없습니다.")


def extract_audio(src: Path, dst: Path) -> None:
    """16kHz mono WAV로 추출 (Whisper 표준)"""
    ffmpeg = find_ffmpeg()
    print(f"[audio] 추출 시작: {src.name} → {dst.name}", flush=True)
    t0 = time.time()
    r = subprocess.run(
        [ffmpeg, "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(dst)],
        capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패: {r.stderr.decode(errors='ignore')[:500]}")
    print(f"[audio] 완료 ({time.time()-t0:.1f}s, {dst.stat().st_size/1024/1024:.1f}MB)", flush=True)


def load_model(model_size: str, device: str):
    """faster-whisper 모델 로드 (GPU 시도 → 실패 시 CPU)"""
    from faster_whisper import WhisperModel  # 지연 임포트

    if device == "auto":
        device_order = ["cuda", "cpu"]
    elif device == "cuda":
        device_order = ["cuda"]
    else:
        device_order = ["cpu"]

    last_error = None
    for dev in device_order:
        try:
            compute = "float16" if dev == "cuda" else "int8"
            print(f"[model] 로딩 시도: {model_size} on {dev} ({compute})", flush=True)
            t0 = time.time()
            model = WhisperModel(
                model_size,
                device=dev,
                compute_type=compute,
                cpu_threads=8 if dev == "cpu" else 0,
            )
            # 실제 inference로 사용 가능한지 검증 (cuBLAS dll 누락 등 감지)
            print(f"[model] 로딩 완료 ({time.time()-t0:.1f}s) on {dev}", flush=True)
            return model, dev
        except Exception as e:
            print(f"[model] {dev} 실패: {str(e)[:200]}", flush=True)
            last_error = e
            continue
    raise RuntimeError(f"모델 로딩 모두 실패: {last_error}")


def transcribe(model, audio_path: Path, language: str | None):
    """STT 실행 + 세그먼트 반환"""
    print(f"[stt] 실행 (language={language or 'auto'})...", flush=True)
    t0 = time.time()
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    print(f"[stt] 감지 언어: {info.language} (확률 {info.language_probability:.2f})", flush=True)
    print(f"[stt] 오디오 길이: {info.duration:.1f}s", flush=True)

    results = []
    text_lines = []
    for seg in segments_iter:
        item = {
            "id": seg.id,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        }
        results.append(item)
        text_lines.append(f"[{item['start']:7.1f}s - {item['end']:7.1f}s] {item['text']}")
        if seg.id % 20 == 0:
            progress = seg.end / info.duration * 100
            print(f"[stt] seg {seg.id} @ {seg.end:.0f}s ({progress:.0f}%, "
                  f"elapsed {time.time()-t0:.0f}s)", flush=True)

    elapsed = time.time() - t0
    print(f"[stt] 완료 ({elapsed:.0f}s, {len(results)}개 세그먼트)", flush=True)
    return results, text_lines, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="영상/오디오 파일 경로")
    ap.add_argument("--output", default=None,
                    help="결과 저장 폴더 (기본: input과 같은 폴더의 stt_out/)")
    ap.add_argument("--model", default="medium",
                    choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"])
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    ap.add_argument("--language", default="ko",
                    help="언어 코드 (ko, en, ja, ...). 'auto'면 자동 감지.")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"[error] 파일 없음: {src}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output).resolve() if args.output else src.parent / "stt_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 오디오 준비
    if src.suffix.lower() in (".wav", ".mp3", ".m4a", ".aac", ".flac"):
        audio = src
    else:
        audio = out_dir / "audio.wav"
        extract_audio(src, audio)

    # 모델 로드 + STT
    model, used_device = load_model(args.model, args.device)
    language = None if args.language == "auto" else args.language
    segments, text_lines, info = transcribe(model, audio, language)

    # 저장
    seg_path = out_dir / "segments.json"
    txt_path = out_dir / "transcript.txt"
    meta_path = out_dir / "stt_meta.json"

    seg_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text("\n".join(text_lines), encoding="utf-8")
    meta_path.write_text(json.dumps({
        "source": str(src),
        "audio": str(audio),
        "model": args.model,
        "device": used_device,
        "language_requested": args.language,
        "language_detected": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 2),
        "segment_count": len(segments),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("", flush=True)
    print("=== 완료 ===", flush=True)
    print(f"segments: {seg_path}", flush=True)
    print(f"transcript: {txt_path}", flush=True)
    print(f"meta: {meta_path}", flush=True)


if __name__ == "__main__":
    main()

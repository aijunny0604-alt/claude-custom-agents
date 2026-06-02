r"""
Team FERVID 블로그 사진 좌상단 로고 워터마크 일괄 합성 스크립트.

사용법:
    python logo_watermark.py <logo_png> <targets_json>

targets_json 형식:
    [
      {"path": "<원본/모자이크 이미지 절대경로>", "out": "<출력 절대경로>"},
      ...
    ]
- out을 생략하면 같은 폴더의 _logo\ 하위에 원본 파일명으로 저장.
- 로고는 사진 좌상단에 RATIO 비율로 합성. 밝은 배경에서도 보이게 약한 그림자(drop shadow) 추가.
- 원본은 보존, 합성본만 별도 저장.
"""

import json
import os
import sys

from PIL import Image, ImageFilter, ImageOps

RATIO = 0.24          # 로고 폭 = 사진 가로의 24%
MARGIN_X = 0.025      # 좌측 여백 (사진 가로 대비 비율)
MARGIN_Y = 0.025      # 상단 여백 (사진 가로 대비 비율 — 가로 기준으로 통일해 좌우상하 균형)
SHADOW = True         # 밝은 배경 대비용 그림자
SHADOW_BLUR = 9
SHADOW_ALPHA = 120    # 그림자 진하기 0~255
SHADOW_OFFSET = 5     # 그림자 오프셋(px, 사진 4000px 기준)


def make_shadow(logo):
    """로고 alpha 채널로부터 부드러운 검은 그림자를 만든다."""
    alpha = logo.split()[3]
    pad = SHADOW_BLUR * 3
    canvas = Image.new("RGBA", (logo.width + pad * 2, logo.height + pad * 2), (0, 0, 0, 0))
    black = Image.new("RGBA", logo.size, (0, 0, 0, SHADOW_ALPHA))
    shadow_layer = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    shadow_layer = Image.composite(black, shadow_layer, alpha)
    canvas.paste(shadow_layer, (pad, pad), shadow_layer)
    canvas = canvas.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    return canvas, pad


def process_one(item, logo):
    src = item["path"]
    if not os.path.exists(src):
        return f"SKIP (no file): {src}"

    out = item.get("out")
    if not out:
        folder = os.path.dirname(src)
        out_dir = os.path.join(folder, "_logo")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, os.path.basename(src))
    else:
        os.makedirs(os.path.dirname(out), exist_ok=True)

    base = ImageOps.exif_transpose(Image.open(src)).convert("RGBA")
    W, H = base.size

    # 로고 크기: 사진 가로의 RATIO 비율 폭, 가로 기준 스케일에 맞춘 오프셋
    scale = W / 4000.0
    lw = max(1, int(W * RATIO))
    lh = max(1, int(logo.height * lw / logo.width))
    lg = logo.resize((lw, lh), Image.LANCZOS)

    x = int(W * MARGIN_X)
    y = int(W * MARGIN_Y)

    if SHADOW:
        shadow, pad = make_shadow(lg)
        off = int(SHADOW_OFFSET * scale)
        base.alpha_composite(shadow, (x - pad + off, y - pad + off))

    base.alpha_composite(lg, (x, y))
    base.convert("RGB").save(out, quality=92, optimize=True)
    return f"OK ({W}x{H}): {out}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python logo_watermark.py <logo_png> <targets_json>")
        sys.exit(1)

    logo = Image.open(sys.argv[1]).convert("RGBA")
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"Logo: {sys.argv[1]} ({logo.width}x{logo.height})  Total: {len(targets)}")
    for item in targets:
        print(process_one(item, logo))


if __name__ == "__main__":
    main()

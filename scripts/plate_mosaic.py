r"""
Team FERVID 블로그 사진 번호판 모자이크 일괄 처리 스크립트 (재사용 가능 버전).

사용법:
    python plate_mosaic.py <targets_json_path>

targets_json_path 의 JSON 형식:
    [
      {
        "path": "C:\\Users\\MOVEAM_PC\\Downloads\\작업 (1)\\6-25.ad순정형가변\\20250422_124248.jpg",
        "boxes": [[0.43, 0.65, 0.85, 0.83]]
      }
    ]

- 좌표는 (left, top, right, bottom) 비율(0~1). EXIF transpose 적용 후 정상 방향 기준.
- 원본은 그대로 두고, 같은 폴더 안 _mosaic 하위 폴더에 처리본 저장.
- 모자이크 강도: 다운스케일 1/50 + 가우시안 블러 80 2회 (글자 잔흔 완전 제거).
"""

import json
import os
import sys

from PIL import Image, ImageFilter, ImageOps

BLUR_RADIUS = 80
PIXEL_DIVIDER = 50


def process_one(item):
    src_path = item["path"]
    boxes = item.get("boxes", [])
    if not os.path.exists(src_path):
        return f"SKIP (no file): {src_path}"
    if not boxes:
        return f"SKIP (no boxes): {src_path}"

    folder_path = os.path.dirname(src_path)
    file_name = os.path.basename(src_path)
    out_dir = os.path.join(folder_path, "_mosaic")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_name)

    img = Image.open(src_path)
    img = ImageOps.exif_transpose(img).convert("RGB")
    W, H = img.size

    for box in boxes:
        lx, ty, rx, by = box
        left = max(0, int(W * lx))
        top = max(0, int(H * ty))
        right = min(W, int(W * rx))
        bottom = min(H, int(H * by))
        if right <= left or bottom <= top:
            continue
        region = img.crop((left, top, right, bottom))
        small = region.resize(
            (max(1, (right - left) // PIXEL_DIVIDER),
             max(1, (bottom - top) // PIXEL_DIVIDER)),
            Image.NEAREST,
        )
        mosaic = small.resize((right - left, bottom - top), Image.NEAREST)
        mosaic = mosaic.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
        mosaic = mosaic.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
        img.paste(mosaic, (left, top, right, bottom))

    img.save(out_path, quality=92, optimize=True)
    return f"OK ({W}x{H}): {out_path}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python plate_mosaic.py <targets_json_path>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        targets = json.load(f)

    print(f"Total items: {len(targets)}")
    for item in targets:
        print(process_one(item))


if __name__ == "__main__":
    main()

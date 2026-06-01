r"""
Team FERVID 블로그 사진 번호판 모자이크 일괄 처리 스크립트 (재사용 가능 버전 v2).

사용법:
    python plate_mosaic.py <targets_json_path>

targets_json_path 의 JSON 형식 (boxes / quads 둘 다 지원, 한 항목에 섞어 써도 됨):
    [
      {
        "path": "C:\\...\\20250422_124248.jpg",
        "quads": [
          [[0.42, 0.66], [0.86, 0.63], [0.87, 0.80], [0.43, 0.83]]
        ]
      },
      {
        "path": "C:\\...\\rear.jpg",
        "boxes": [[0.30, 0.55, 0.68, 0.68]]
      }
    ]

- quads(권장): 번호판 네(이상) 모서리 점을 시계방향/반시계방향으로 [[x,y],...] (비율 0~1).
  번호판이 기울어지거나 원근이 있어도 그 다각형 윤곽에만 모자이크가 들어가고, 가장자리는
  부드럽게(feather) 처리되어 자연스럽다.
- boxes(하위호환): 축 정렬 직사각형 (left, top, right, bottom) 비율(0~1).
- 좌표는 EXIF transpose 적용 후 정상 방향 기준.
- 원본은 그대로 두고, 같은 폴더 안 _mosaic 하위 폴더에 처리본 저장.
- 모자이크 강도: 다운스케일 1/PIXEL_DIVIDER + 가우시안 블러 2회 (글자 잔흔 완전 제거).
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageOps

BLUR_RADIUS = 80
BLOCKS_X = 7             # 모자이크 블록 수(가로 기준). 작을수록 강하게 뭉갠다.
SUPERSAMPLE = 4          # 다각형 마스크 안티앨리어싱 배율 (계단 현상 제거)
FEATHER_RATIO = 0.04     # 마스크 가장자리 페더 강도 (짧은 변 대비 비율)


def _mosaic_region(img, left, top, right, bottom):
    """주어진 직사각형 영역을 모자이크 처리한 패치(이미지)를 돌려준다.

    번호판처럼 '흰 바탕 + 검은 글자' 대비가 강한 영역은 단순 블러만으로는
    회색 글자 흔적이 남는다. 그래서 영역을 가로 BLOCKS_X개의 큰 블록으로
    평균색 다운샘플(BOX 필터)한 뒤 다시 키워(픽셀화) 글자 형태를 완전히
    뭉개고, 마지막에 가우시안 블러로 블록 경계를 부드럽게 만든다.
    """
    w, h = right - left, bottom - top
    region = img.crop((left, top, right, bottom))
    bx = max(3, BLOCKS_X)
    by = max(2, int(round(BLOCKS_X * h / w)))
    # 다운샘플은 BOX(평균) → 글자색이 바탕에 녹아 흔적이 남지 않음
    small = region.resize((bx, by), Image.BOX)
    mosaic = small.resize((w, h), Image.NEAREST)
    mosaic = mosaic.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    mosaic = mosaic.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    return mosaic


def _clamp_box(W, H, lx, ty, rx, by):
    left = max(0, int(round(W * lx)))
    top = max(0, int(round(H * ty)))
    right = min(W, int(round(W * rx)))
    bottom = min(H, int(round(H * by)))
    return left, top, right, bottom


def _apply_quad(img, result, W, H, poly):
    """poly: [[x,y],...] 비율좌표. 다각형 모양으로만 모자이크를 합성한다."""
    pts_px = [(x * W, y * H) for x, y in poly]
    xs = [p[0] for p in pts_px]
    ys = [p[1] for p in pts_px]
    left = max(0, int(round(min(xs))))
    top = max(0, int(round(min(ys))))
    right = min(W, int(round(max(xs))))
    bottom = min(H, int(round(max(ys))))
    if right <= left or bottom <= top:
        return result

    bw, bh = right - left, bottom - top

    # bbox 영역만 모자이크 (메모리 안전)
    mosaic_patch = _mosaic_region(img, left, top, right, bottom)

    # bbox 로컬 좌표로 다각형 마스크 생성 (supersample 후 축소 → 안티앨리어싱)
    local_pts = [((x * W - left) * SUPERSAMPLE, (y * H - top) * SUPERSAMPLE)
                 for x, y in poly]
    mask_big = Image.new("L", (bw * SUPERSAMPLE, bh * SUPERSAMPLE), 0)
    ImageDraw.Draw(mask_big).polygon(local_pts, fill=255)
    mask = mask_big.resize((bw, bh), Image.LANCZOS)

    # 가장자리 페더 (딱딱한 경계 제거)
    feather = max(1, int(round(min(bw, bh) * FEATHER_RATIO)))
    mask = mask.filter(ImageFilter.GaussianBlur(feather))

    base_crop = result.crop((left, top, right, bottom))
    blended = Image.composite(mosaic_patch, base_crop, mask)
    result.paste(blended, (left, top))
    return result


def process_one(item):
    src_path = item["path"]
    boxes = item.get("boxes", [])
    quads = item.get("quads", [])
    if not os.path.exists(src_path):
        return f"SKIP (no file): {src_path}"
    if not boxes and not quads:
        return f"SKIP (no boxes/quads): {src_path}"

    folder_path = os.path.dirname(src_path)
    file_name = os.path.basename(src_path)
    out_dir = os.path.join(folder_path, "_mosaic")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_name)

    img = Image.open(src_path)
    img = ImageOps.exif_transpose(img).convert("RGB")
    W, H = img.size
    result = img.copy()

    # 1) 다각형(quad) — 번호판 윤곽 정밀 처리 (권장)
    for poly in quads:
        if len(poly) >= 3:
            result = _apply_quad(img, result, W, H, poly)

    # 2) 축 정렬 박스(box) — 하위호환. 가장자리만 살짝 페더해서 자연스럽게.
    for box in boxes:
        left, top, right, bottom = _clamp_box(W, H, *box)
        if right <= left or bottom <= top:
            continue
        mosaic_patch = _mosaic_region(img, left, top, right, bottom)
        bw, bh = right - left, bottom - top
        mask = Image.new("L", (bw, bh), 255)
        feather = max(1, int(round(min(bw, bh) * FEATHER_RATIO)))
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
        base_crop = result.crop((left, top, right, bottom))
        blended = Image.composite(mosaic_patch, base_crop, mask)
        result.paste(blended, (left, top))

    result.save(out_path, quality=92, optimize=True)
    n = len(quads) + len(boxes)
    return f"OK ({W}x{H}, {n} region): {out_path}"


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

r"""
폴더 안의 사진을 EXIF DateTimeOriginal 우선 + 파일명 fallback 으로 정렬해
JSON 으로 출력하는 헬퍼.

사용법:
    python sort_photos.py "<폴더 경로>"

출력: stdout 으로 JSON 배열
    [
      {
        "file": "20250422_124248.jpg",
        "path": "C:\\...\\20250422_124248.jpg",
        "shot_at": "2025-04-22T12:42:48",   # EXIF 없으면 null
        "sort_key": "2025-04-22T12:42:48",  # 정렬에 실제로 사용된 키
        "source": "exif"                    # 또는 "filename"
      }
    ]

정렬 규칙:
  1. EXIF DateTimeOriginal 이 있으면 그 시각으로 정렬
  2. EXIF 없으면 파일명을 sort key 로 사용 (촬영 시각 패턴이면 시간 순과 동일)
  3. 두 경우 다 같으면 마지막에 파일명 tiebreak
"""

import json
import os
import sys
from datetime import datetime

from PIL import Image, ExifTags

PHOTO_EXTS = {".jpg", ".jpeg", ".png"}
DATETIME_TAG = next(
    (tag for tag, name in ExifTags.TAGS.items() if name == "DateTimeOriginal"),
    36867,
)


def read_shot_at(path: str):
    try:
        with Image.open(path) as img:
            exif = img._getexif()
        if not exif:
            return None
        raw = exif.get(DATETIME_TAG)
        if not raw:
            return None
        # EXIF DateTimeOriginal 형식: "YYYY:MM:DD HH:MM:SS"
        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def collect(folder: str):
    items = []
    for name in os.listdir(folder):
        ext = os.path.splitext(name)[1].lower()
        if ext not in PHOTO_EXTS:
            continue
        full = os.path.join(folder, name)
        shot = read_shot_at(full)
        if shot is not None:
            items.append({
                "file": name,
                "path": full,
                "shot_at": shot.isoformat(),
                "sort_key": shot.isoformat(),
                "source": "exif",
            })
        else:
            items.append({
                "file": name,
                "path": full,
                "shot_at": None,
                "sort_key": name,
                "source": "filename",
            })
    items.sort(key=lambda x: (x["sort_key"], x["file"]))
    return items


def main():
    if len(sys.argv) < 2:
        print("Usage: python sort_photos.py <folder>")
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}", file=sys.stderr)
        sys.exit(1)
    items = collect(folder)
    print(json.dumps(items, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

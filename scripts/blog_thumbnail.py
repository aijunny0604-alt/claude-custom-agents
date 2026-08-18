# -*- coding: utf-8 -*-
"""팀퍼비드/무브모터스 블로그 썸네일 생성기.
양식: 차량 사진(상단) + FERVID 로고 흰밴드 + 차종(검정,동그라미) + 작업명 2줄(흰글씨 검정외곽선, 큰 동그라미).
usage: python blog_thumbnail.py <photo> <out.png> <로고png> "<차종>" "<작업명1줄>" "<작업명2줄(선택)>"
"""
import sys
from PIL import Image, ImageDraw, ImageFont

photo_path, out_path, logo_path = sys.argv[1], sys.argv[2], sys.argv[3]
brand = sys.argv[4] if len(sys.argv) > 4 else "BMW X5M"
line1 = sys.argv[5] if len(sys.argv) > 5 else ""
line2 = sys.argv[6] if len(sys.argv) > 6 else ""

W, H = 800, 820
PHOTO_H = 340
FONT = "C:/Windows/Fonts/malgunbd.ttf"

cv = Image.new("RGB", (W, H), (255, 255, 255))
dr = ImageDraw.Draw(cv)

# 1) 상단 차량 사진 (width 맞추고 상단 크롭)
p = Image.open(photo_path).convert("RGB")
scale = W / p.width
p = p.resize((W, int(p.height * scale)), Image.LANCZOS)
top = max(0, int(p.height * 0.10))
p = p.crop((0, top, W, top + PHOTO_H)) if p.height >= top + PHOTO_H else p.crop((0, 0, W, min(PHOTO_H, p.height)))
cv.paste(p, (0, 0))

# 2) 로고 흰 밴드 + FERVID 로고 (사진 하단/흰영역 경계에 걸치게)
band_y0 = PHOTO_H - 70
dr.rectangle([0, band_y0, W, band_y0 + 120], fill=(255, 255, 255))
logo = Image.open(logo_path).convert("RGBA")
lw = 420
logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
cv.paste(logo, ((W - lw) // 2, band_y0 + 8 + (120 - logo.height)//2), logo)

def center_text(y, text, size, fill, stroke=0, stroke_fill=(0,0,0)):
    f = ImageFont.truetype(FONT, size)
    bb = dr.textbbox((0, 0), text, font=f, stroke_width=stroke)
    w = bb[2] - bb[0]
    x = (W - w) // 2 - bb[0]
    dr.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return w

def hand_oval(cx, cy, rx, ry):
    for dx, dy in [(0, 0), (5, -4), (-4, 5)]:
        dr.ellipse([cx-rx+dx, cy-ry+dy, cx+rx+dx, cy+ry+dy], outline=(20, 20, 20), width=4)

# 3) 차종 (검정) + 동그라미
by = PHOTO_H + 90
bw = center_text(by, brand, 54, (25, 25, 25))
hand_oval(W//2, by + 34, bw//2 + 40, 46)

# 4) 작업명 2줄 (흰 글씨 + 검정 외곽선)
ty = by + 100
sizes = 112 if len(line1) <= 6 else 96
center_text(ty, line1, sizes, (255, 255, 255), stroke=11, stroke_fill=(15, 15, 15))
if line2:
    ty2 = ty + int(sizes * 1.15)
    s2 = 112 if len(line2) <= 6 else 96
    center_text(ty2, line2, s2, (255, 255, 255), stroke=11, stroke_fill=(15, 15, 15))
    # 큰 동그라미 (작업명 2줄 감싸기)
    hand_oval(W//2, ty + int(sizes*1.05), W//2 - 20, int(sizes*1.25))

cv.save(out_path, quality=95)
print("OK 썸네일 저장:", out_path)

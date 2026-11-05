"""PNG 여러 장 → 한 장 (축소 격자). 사용: python3 hil_ui_sheet.py out.png cols scale a.png b.png ..."""
import sys

from PIL import Image, ImageDraw, ImageFont

out, cols, scale, files = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4:]
ims = [Image.open(f).convert("RGB") for f in files]
w, h = int(ims[0].width * scale), int(ims[0].height * scale)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 30) + 8), (255, 255, 255))
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicCodingBold.ttf", 16)
for i, (im, fn) in enumerate(zip(ims, files)):
    x, y = 8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 30)
    sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y + 22))
    d.text((x, y), fn.split("/")[-1].replace(".png", ""), font=f, fill=(0, 0, 0))
sheet.save(out, optimize=True)
print(out, sheet.size)

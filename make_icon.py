# -*- coding: utf-8 -*-
"""生成应用图标 app.png / app.ico。"""
from PIL import Image, ImageDraw
from pathlib import Path

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 背景：深蓝圆角方块（科研蓝）
d.rounded_rectangle([8, 8, S - 8, S - 8], radius=52, fill=(30, 64, 128, 255))
# 顶部高光
d.rounded_rectangle([8, 8, S - 8, 96], radius=52, fill=(52, 92, 170, 90))

# 文档：白色圆角矩形 + 折角
doc = [56, 44, 200, 212]
d.rounded_rectangle(doc, radius=14, fill=(255, 255, 255, 255))
# 折角三角
d.polygon([(200, 44), (200, 84), (160, 44)], fill=(210, 220, 235, 255))
d.polygon([(160, 44), (200, 84), (160, 84)], fill=(255, 255, 255, 255))

# 文字行
for y in (100, 126, 152, 178):
    d.rounded_rectangle([76, y, 128 if y != 178 else 156, y + 10], radius=5, fill=(150, 165, 190, 255))
d.rounded_rectangle([76, 178, 156, 188], radius=5, fill=(150, 165, 190, 255))

# 绿色对勾（右下）
d.line([(150, 140), (165, 158), (196, 120)], fill=(46, 180, 110, 255), width=16, joint="curve")
d.ellipse([142, 132, 204, 168], outline=(46, 180, 110, 255), width=12)

img.save(str(Path(__file__).resolve().parent / "app.png"))
img.save(str(Path(__file__).resolve().parent / "app.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon ok")

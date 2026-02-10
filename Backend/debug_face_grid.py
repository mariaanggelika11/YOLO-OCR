from PIL import Image, ImageDraw

# ganti ke path foto DL ASLI (bukan face.jpg)
IMG_PATH = "Maryland.jpg"

img = Image.open(IMG_PATH).convert("RGB")
w, h = img.size

draw = ImageDraw.Draw(img)

# gambar grid 10%
for i in range(1, 10):
    x = int(w * i / 10)
    y = int(h * i / 10)

    draw.line((x, 0, x, h), fill="red", width=1)
    draw.line((0, y, w, y), fill="red", width=1)

    draw.text((x + 2, 2), f"x={i*10}%", fill="red")
    draw.text((2, y + 2), f"y={i*10}%", fill="red")

img.save("dl_with_grid.jpg")
print("OK! dl_with_grid.jpg dibuat")

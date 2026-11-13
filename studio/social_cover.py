"""Compose the 1200x630 social preview from the harbor still. Needs Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 1200, 630
still = Image.open(ROOT / 'studio/out/harbor_hero.png').convert('RGB')
scale = H / still.height * 1.22
still = still.resize((round(still.width * scale), round(still.height * scale)), Image.LANCZOS)
canvas = Image.new('RGB', (W, H), '#f7f2e7')
canvas.paste(still, (W - still.width + 230, -round(still.height * 0.13)))
# cream haze from the left so the words sit on paper
fade = Image.new('L', (W, 1))
for x in range(W):
    t = min(1.0, max(0.0, (x - 470) / 380))
    fade.putpixel((x, 0), round(255 * (1 - t * t * (3 - 2 * t))))
canvas.paste(Image.new('RGB', (W, H), '#f7f2e7'), (0, 0), fade.resize((W, H)))
draw = ImageDraw.Draw(canvas)
sans = lambda size, weight=1: ImageFont.truetype(str(ROOT / f'assets/font-{weight}.ttf'), size)
serif = ImageFont.truetype(str(ROOT / 'assets/font-4.ttf'), 62)
ink, sea, coral, muted = '#17302c', '#1c7f86', '#ec6c4b', '#66766f'
draw.ellipse((70, 76, 82, 88), fill=coral)
draw.text((96, 70), 'SHENGBO JIANG', font=sans(19, 2), fill=ink)
draw.text((68, 232), 'Making intelligence', font=sans(64, 1), fill=ink)
draw.text((68, 306), 'an instrument of discovery', font=serif, fill=sea)
draw.text((70, 408), 'Eight projects, eight small islands,', font=sans(25, 0), fill=muted)
draw.text((70, 442), 'and a boat to take you to each.', font=sans(25, 0), fill=muted)
draw.text((70, 540), 'shengbojiang.me', font=sans(20, 1), fill=ink)
canvas.save(ROOT / 'assets/social-cover.png', optimize=True)
print('wrote assets/social-cover.png')

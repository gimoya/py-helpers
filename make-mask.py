#!/usr/bin/env python3
"""PNG masks: transparent inner shape, black border. Border = 50% of inner width.
   Plus outline PNGs: exact mask edges, 5px white line, sharp corners, transparent bg.
   SCALE multiplies all dimensions; ratios preserved."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "Pillow"])
    from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).parent
SCALE = 5  # resolution multiplier (base ~200px → 1000px)
BORDER_FRAC = 1.5  # border = 50% * 3 (outer portion 3x bigger)
INNER_SIZE = 200 * SCALE
INNER_H_RECT = 120 * SCALE
STROKE = 5 * SCALE
PARA_SKEW = 20 * SCALE
PARA_WIDTH_FRAC = 0.85  # parallelogram a tad less wide than full INNER_SIZE

# (0) Square
border = int(INNER_SIZE * BORDER_FRAC)
tw = th = INNER_SIZE + 2 * border
img = Image.new("RGBA", (tw, th), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)
draw.rectangle([border, border, border + INNER_SIZE, border + INNER_SIZE], fill=(0, 0, 0, 0))
img.save(OUT_DIR / "mask_square.png")

# (1) Circle
img = Image.new("RGBA", (tw, th), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)
draw.ellipse([border, border, border + INNER_SIZE, border + INNER_SIZE], fill=(0, 0, 0, 0))
img.save(OUT_DIR / "mask_circle.png")

# (2) Rhomboid
cx, cy = tw // 2, th // 2
r = INNER_SIZE // 2
inner_verts_rhomb = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
img = Image.new("RGBA", (tw, th), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)
draw.polygon(inner_verts_rhomb, fill=(0, 0, 0, 0))
img.save(OUT_DIR / "mask_rhomboid.png")

# (3) Rectangle
inner_h = INNER_H_RECT
border_y = int(inner_h * BORDER_FRAC)
tw_r = INNER_SIZE + 2 * border
th_r = inner_h + 2 * border_y
rect_bbox = [border, border_y, border + INNER_SIZE, border_y + inner_h]
img = Image.new("RGBA", (tw_r, th_r), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)
draw.rectangle(rect_bbox, fill=(0, 0, 0, 0))
img.save(OUT_DIR / "mask_rectangle.png")

# (5) Parallelogram (top/bottom horizontal, sides slanted)
para_w = int(INNER_SIZE * PARA_WIDTH_FRAC)
para_margin = (INNER_SIZE - para_w) // 2
para_verts = [(border + para_margin, border_y), (border + para_margin + para_w, border_y),
              (border + para_margin + para_w - PARA_SKEW, border_y + inner_h), (border + para_margin - PARA_SKEW, border_y + inner_h)]
img = Image.new("RGBA", (tw_r, th_r), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)
draw.polygon(para_verts, fill=(0, 0, 0, 0))
img.save(OUT_DIR / "mask_parallelogram.png")

# --- Outline PNGs (transparent bg, 5px white, sharp corners) ---
def outline_rect(draw, bbox, w):
    draw.rectangle(bbox, outline=(255, 255, 255, 255), width=w)

def outline_polygon(draw, verts, w):
    draw.polygon(verts, outline=(255, 255, 255, 255), width=w)

def outline_ellipse(draw, bbox, w):
    draw.ellipse(bbox, outline=(255, 255, 255, 255), width=w)

# Square outline
img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
bbox_sq = [border, border, border + INNER_SIZE, border + INNER_SIZE]
outline_rect(draw, bbox_sq, STROKE)
img.save(OUT_DIR / "outline_square.png")

# Circle outline
img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
outline_ellipse(draw, [border, border, border + INNER_SIZE, border + INNER_SIZE], STROKE)
img.save(OUT_DIR / "outline_circle.png")

# Rhomboid outline
img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
outline_polygon(draw, inner_verts_rhomb, STROKE)
img.save(OUT_DIR / "outline_rhomboid.png")

# Rectangle outline
img = Image.new("RGBA", (tw_r, th_r), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
outline_rect(draw, rect_bbox, STROKE)
img.save(OUT_DIR / "outline_rectangle.png")

# Parallelogram outline
img = Image.new("RGBA", (tw_r, th_r), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
outline_polygon(draw, para_verts, STROKE)
img.save(OUT_DIR / "outline_parallelogram.png")

print("Masks: mask_square, mask_circle, mask_rhomboid, mask_rectangle, mask_parallelogram")
print("Outlines: outline_square, outline_circle, outline_rhomboid, outline_rectangle, outline_parallelogram")

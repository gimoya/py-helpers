#!/usr/bin/env python3
"""Frame clip + stroke overlay. Resize to max side (default 630 px), output DPI (default 200)."""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MM_PER_INCH = 25.4
DEFAULT_STROKE_MM = 2.0
DEFAULT_INCLINATION_DEG = 5.0
DEFAULT_DPI = 200
DEFAULT_MAX_SIDE = 630
DEFAULT_STROKE_COLOR = "255,255,255"
DEFAULT_OUTPUT_SUBDIR = "framed"

def mm_to_px(mm: float, dpi: float) -> int:
    """Convert mm to pixels using dpi (pixels per inch)."""
    return max(1, int(round((mm / MM_PER_INCH) * dpi)))


def frame_polygon(frame_type: int, w: int, h: int, inclination_deg: float) -> list[tuple[int, int]]:
    """Return polygon points in content coords (0..w, 0..h). 0=rect, 1=trapezoid top narrow, 2=trapezoid bottom narrow, 3=diamond, 4=octagon."""
    inset = int(h * math.tan(math.radians(inclination_deg))) if inclination_deg else 0
    if frame_type == 0:
        return [(0, 0), (w, 0), (w, h), (0, h)]
    if frame_type == 1:
        return [(inset, 0), (w - inset, 0), (w, h), (0, h)]
    if frame_type == 2:
        return [(0, 0), (w, 0), (w - inset, h), (inset, h)]
    if frame_type == 3:
        return [(w // 2, 0), (w, h // 2), (w // 2, h), (0, h // 2)]
    if frame_type == 4:
        if inset <= 0:
            cut = max(1, min(w, h) // 10)
            a, b = cut, cut
        else:
            a = max(1, min(int(inset * 0.5), w // 6, h // 6))
            b = max(1, int(a * h / inset))
        return [
            (a, 0), (w - a, 0), (w, b), (w, h - b),
            (w - a, h), (a, h), (0, h - b), (0, b),
        ]
    return [(0, 0), (w, 0), (w, h), (0, h)]


def parse_stroke_color(s: str):
    """Parse 'r,g,b' string to Wand Color. Raises ValueError if invalid."""
    parts = [x.strip() for x in s.split(",")]
    if len(parts) != 3:
        raise ValueError("stroke color must be 'r,g,b' e.g. '255,255,255'")
    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
        raise ValueError("r,g,b must be 0-255")
    return Color("rgb(%s,%s,%s)" % (r, g, b))


def process(img_path: Path, out_path: Path, stroke_mm: float, inclination_deg: float, dpi: float, max_side: int | None, frame_type: int, stroke_color) -> None:
    with WandImage(filename=str(img_path)) as src:
        w, h = src.width, src.height
        if max_side and max(w, h) > max_side:
            if w >= h:
                nw, nh = max_side, max(1, int(round(h * max_side / w)))
            else:
                nw, nh = max(1, int(round(w * max_side / h))), max_side
            src.resize(nw, nh)
            w, h = nw, nh
        stroke_px = mm_to_px(stroke_mm, dpi)
        pad = stroke_px
        polygon_content = frame_polygon(frame_type, w, h, inclination_deg)

        with WandImage(width=w, height=h, background=Color("black")) as mask_img:
            with Drawing() as draw:
                draw.stroke_antialias = False
                draw.fill_color = Color("white")
                draw.polygon(points=polygon_content)
                draw(mask_img)
            mask_img.threshold(0.5, channel="default_channels")
            mask_img.alpha_channel = "copy"
            src.alpha_channel = "activate"
            src.composite_channel("alpha", mask_img, "copy_alpha", 0, 0)

        out_w, out_h = w + 2 * pad, h + 2 * pad
        polygon_out = [(x + pad, y + pad) for x, y in polygon_content]
        with WandImage(width=out_w, height=out_h, background=Color("transparent")) as out:
            out.resolution = (dpi, dpi)
            out.units = "pixelsperinch"
            out.composite(src, pad, pad, "over")
            with Drawing() as draw:
                draw.stroke_color = stroke_color
                draw.stroke_width = stroke_px
                draw.fill_opacity = 0
                draw.polygon(points=polygon_out)
                draw(out)
            out.format = "png"
            out.save(filename=str(out_path))
    print(out_path)


try:
    from wand.image import Image as WandImage
    from wand.drawing import Drawing
    from wand.color import Color
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Wand"])
    from wand.image import Image as WandImage
    from wand.drawing import Drawing
    from wand.color import Color


def main():
    p = argparse.ArgumentParser(
        description="Clip images to a frame shape, draw a stroke, resize to max side, write PNGs. Default: output into subfolder 'framed'; 630 px max side, 200 DPI (~8 cm on 200 DPI print), white stroke.",
        epilog="""
Examples (input defaults to current dir, output to ./framed unless -o set):

  %(prog)s
  %(prog)s -f 1
  %(prog)s -f 1 -s 1
  %(prog)s -f 4 -c 0,0,0
  %(prog)s C:\\path\\to\\images
  %(prog)s C:\\path\\to\\images -o .
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("folder", type=Path, nargs="?", default=Path("."), metavar="DIR",
                    help="Input folder (default: current directory).")
    p.add_argument("-o", "--output", type=Path, default=None, metavar="DIR",
                    help="Output folder (default: <input>/%s). Use . for same as input." % DEFAULT_OUTPUT_SUBDIR)
    p.add_argument("-s", "--stroke", type=float, default=DEFAULT_STROKE_MM, metavar="MM",
                    help="Frame stroke width in mm (default: %s)" % DEFAULT_STROKE_MM)
    p.add_argument("-c", "--stroke-color", type=str, default=DEFAULT_STROKE_COLOR, metavar="R,G,B",
                    help="Stroke color as R,G,B 0-255 (default: %s)" % DEFAULT_STROKE_COLOR)
    p.add_argument("-f", "--frame", type=int, choices=[0, 1, 2, 3, 4], default=0, metavar="N",
                    help="0=rectangle, 1=trapezoid (top narrow), 2=trapezoid (bottom narrow), 3=diamond, 4=octagon (default: 0)")
    p.add_argument("-i", "--inclination", type=float, default=DEFAULT_INCLINATION_DEG, metavar="DEG",
                    help="Side inclination in degrees for frame 1,2,4 (default: %s)" % DEFAULT_INCLINATION_DEG)
    p.add_argument("-m", "--max-side", type=int, default=DEFAULT_MAX_SIDE, metavar="PX",
                    help="Resize so longest side is PX pixels (default: %s)" % DEFAULT_MAX_SIDE)
    p.add_argument("--dpi", type=float, default=DEFAULT_DPI, metavar="DPI",
                    help="Output PNG DPI and for stroke mm->px (default: %s)" % DEFAULT_DPI)
    args = p.parse_args()
    try:
        stroke_color = parse_stroke_color(args.stroke_color)
    except ValueError as e:
        p.error(str(e))
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        p.error("Not a directory: %s" % folder)
    if args.output is None:
        out_dir = folder / DEFAULT_OUTPUT_SUBDIR
    elif args.output == Path("."):
        out_dir = folder
    else:
        out_dir = Path(args.output).resolve()
    if not out_dir.exists():
        out_dir.mkdir(parents=True)
    color_suffix = args.stroke_color.replace(",", "-")
    name_suffix = "_f%d_s%s_%s" % (args.frame, args.stroke, color_suffix)
    count = 0
    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.suffix.lower() not in EXTS:
            continue
        out_path = out_dir / (f.stem + name_suffix + ".png")
        process(f, out_path, args.stroke, args.inclination, args.dpi, args.max_side, args.frame, stroke_color)
        count += 1
    if count == 0:
        sys.stderr.write("No image files (jpg, png, webp, bmp) in %s\n" % folder)


if __name__ == "__main__":
    main()

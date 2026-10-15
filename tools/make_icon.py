"""Erzeugt das Anwendungssymbol `assets/projecthq.ico`.

Gezeichnet statt gemalt: ein Pixel-Totenkopf in Phosphorgruen auf dunklem
Grund, mit Scanlines und weichem Schein wie auf einer Roehre. Alles wird
bei 1024 px gerendert und danach auf die Symbolgroessen heruntergerechnet,
damit auch das 16-px-Symbol in der Taskleiste sauber bleibt.

Aufruf (nur noetig, wenn sich das Symbol aendern soll):

    py -3.12 tools/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

# Renderaufloesung. Hoch genug, dass das 16er Symbol aus vielen Pixeln
# gemittelt wird statt aus wenigen.
SIZE = 1024

BG = (5, 11, 5, 255)
GREEN = (51, 255, 102, 255)
DIM = (31, 138, 61, 255)

# Groessen im .ico. Windows sucht sich je nach Ansicht die passende heraus.
ICON_SIZES = (256, 128, 64, 48, 32, 24, 16)

# 16x16-Raster des Totenkopfs, '#' ist gesetzt. Symmetrisch, damit er in
# jeder Groesse gerade wirkt.
SKULL = (
    "................",
    "....########....",
    "..############..",
    ".##############.",
    "################",
    "################",
    "##..######..####",
    "#....####....###",
    "#....####....###",
    "##..######..####",
    "################",
    ".##############.",
    ".#.##.####.##.#.",
    "..#.#.####.#.#..",
    "....########....",
    "................",
)

CORNER = int(SIZE * 0.18)


def _plate() -> Image.Image:
    """Dunkles, abgerundetes Quadrat mit Phosphorrahmen."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=CORNER, fill=BG)
    draw.rounded_rectangle(
        [SIZE * 0.035, SIZE * 0.035, SIZE * 0.965, SIZE * 0.965],
        radius=int(CORNER * 0.85),
        outline=DIM,
        width=int(SIZE * 0.022),
    )
    return img


def _skull() -> Image.Image:
    """Nur der Totenkopf, freigestellt auf durchsichtigem Grund."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    padding = SIZE * 0.16
    cell = (SIZE - 2 * padding) / len(SKULL)
    for row, line in enumerate(SKULL):
        for col, char in enumerate(line):
            if char != "#":
                continue
            x = padding + col * cell
            y = padding + row * cell
            # +1, damit zwischen benachbarten Zellen keine Fuge bleibt.
            draw.rectangle([x, y, x + cell + 1, y + cell + 1], fill=GREEN)
    return img


def _glow(shape: Image.Image) -> Image.Image:
    """Weicher Schein um die Form, wie ihn Phosphor wirft."""
    blurred = shape.filter(ImageFilter.GaussianBlur(int(SIZE * 0.035)))
    alpha = blurred.split()[3].point(lambda v: int(v * 170 / 255))
    blurred.putalpha(alpha)
    return blurred


def _scanlines(img: Image.Image) -> Image.Image:
    """Waagerechte Abdunklung, an den Ecken auf die Plattenform beschnitten."""
    step = int(SIZE * 0.035)
    lines = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(lines)
    for y in range(0, SIZE, step):
        draw.rectangle([0, y, SIZE, y + step // 2], fill=(0, 0, 0, 42))

    plate = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(plate).rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=CORNER, fill=255
    )
    empty = Image.new("L", (SIZE, SIZE), 0)
    lines.putalpha(Image.composite(lines.split()[3], empty, plate))
    return Image.alpha_composite(img, lines)


def render() -> Image.Image:
    shape = _skull()
    img = Image.alpha_composite(_plate(), _glow(shape))
    img = Image.alpha_composite(img, shape)
    return _scanlines(img)


def main() -> None:
    target = Path(__file__).resolve().parent.parent / "assets" / "projecthq.ico"
    target.parent.mkdir(exist_ok=True)
    image = render()
    image.save(target, sizes=[(s, s) for s in ICON_SIZES])
    image.resize((256, 256), Image.LANCZOS).save(target.with_suffix(".png"))
    print(f"geschrieben: {target}")


if __name__ == "__main__":
    main()

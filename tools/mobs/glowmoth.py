"""Glowmoth: a moth as big as a cat. A fluffy cream body and head with a pale-yellow ruff, big dark
eyes, feathery gold antennae and four broad luna-moth wings: mint green with a rosy leading edge,
long trailing tails on the hindwings and eye-spots and veins that glow faintly at night.
The wings are zero-thickness planes hinged at the body; the code flaps them around z."""
import math
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Glowmoth'
LOOT = []
TAGS = ['fall_damage_immune']


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0):
        self.items.append((part, origin, size, paint, mirror, share, inflate))

    def apply(self):
        def dims(size):
            w, h, d = (int(math.ceil(s)) for s in size)
            return 2 * d + 2 * w, d + h
        keys, order = {}, []
        for i, it in enumerate(self.items):
            k = it[5] or ("#", i)
            if k not in keys:
                keys[k] = None
                order.append((k, dims(it[2])))
        order.sort(key=lambda kv: (-kv[1][1], -kv[1][0]))
        shelves, y_next = [], 0
        for k, (w, h) in order:
            for s in shelves:
                if h <= s[1] and s[2] + w <= self.m.tex_w:
                    keys[k] = (s[2], s[0])
                    s[2] += w
                    break
            else:
                if y_next + h > self.m.tex_h or w > self.m.tex_w:
                    raise ValueError(f"{self.m.id}: texture too small for {k} {w}x{h}")
                shelves.append([y_next, h, w])
                keys[k] = (0, y_next)
                y_next += h
        for i, (part, origin, size, paint, mirror, share, inflate) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, mirror=mirror, inflate=inflate)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def soft_glow(c, x, y, col, k):
    """Paint col on the base texture, and a dimmed copy (k = brightness) on the emissive layer, so the
    pixel only glows faintly at night instead of shining at full strength."""
    if not c.inside(x, y):
        return
    c.set(x, y, col)
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), shade(col, k))


# -- palette -----------------------------------------------------------------------------------------
CREAM = ["#f4ecd2", "#efe5c4", "#f7f0da", "#ece0bb"]
CREAM_SH = ["#d8c99f", "#d2c294"]
RUFF = ["#f7e7a6", "#f3df98", "#f9ecb4"]
EYE = "#2a2233"
EYE_2 = "#3a3046"
EYE_HI = "#f2f0ff"
ANT = "#dcbc78"
ANT_DK = "#a8853f"
LEG = ["#d58ea6", "#cd859e"]

MINT = ["#a9e5c4", "#a2dfbd", "#afe9c9", "#9fdbb9"]
WING_BASE = "#eef5e0"
MARGIN = ["#d4efb4", "#cdeaad"]
COSTA = ["#a8566f", "#b0607a"]
VEIN = "#c2efd5"
SPOT_RING = "#b45574"
SPOT_RING2 = "#d77f98"
SPOT_CORE = "#f4d46c"
SPOT_HI = "#fff2c0"

SIDES = ("front", "back", "left", "right")


def fuzz(pal=None, shade_pal=None, top=1.04):
    """Soft fur: cream noise, side faces darken toward the bottom, a few lighter tufts."""
    pal = pal or CREAM
    shade_pal = shade_pal or CREAM_SH

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(pal)
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.03 - 0.16 * y / (c.h - 1))
                    if y == c.h - 1:
                        col = mix(col, c.pick(shade_pal), 0.5)
                elif c.face == "top":
                    col = shade(col, top)
                elif c.face == "bottom":
                    col = c.pick(shade_pal)
                c.set(x, y, col)
        for _ in range(c.w * c.h // 6):          # tufts: a lighter pixel over a slightly darker one
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, shade(c.get(x, y), 1.05))
            if c.inside(x, y + 1) and c.face in SIDES:
                c.set(x, y + 1, shade(c.get(x, y + 1), 0.92))
    return p


def ruff_overlay(c):
    """Inflated shell over the thorax: half its pixels cut out, so the outline looks fluffy."""
    for y in range(c.h):
        for x in range(c.w):
            edge = x in (0, c.w - 1) or y in (0, c.h - 1)
            keep = c.rng.random() < (0.55 if edge else 0.4)
            if c.face == "bottom":
                keep = c.rng.random() < 0.25
            if keep:
                col = c.pick(RUFF)
                if c.face in SIDES:
                    col = shade(col, 1.02 - 0.14 * y / max(1, c.h - 1))
                c.set(x, y, col)
            else:
                c.clear(x, y)


def abdomen_fur(c):
    fuzz()(c)
    # soft pale-yellow bands across the abdomen
    if c.face in ("top", "bottom"):
        for y in range(1, c.h, 2):
            for x in range(c.w):
                c.set(x, y, mix(c.get(x, y), c.pick(RUFF), 0.55))
    elif c.face in ("left", "right"):
        for x in range(1, c.w, 2):
            for y in range(c.h):
                c.set(x, y, mix(c.get(x, y), c.pick(RUFF), 0.55))
    elif c.face == "back":
        c.set(c.w // 2, c.h // 2, shade(CREAM[0], 0.85))


def head_front(c):
    fuzz()(c)
    for x in range(c.w):
        c.set(x, 0, c.pick(RUFF))
    c.set(c.w // 2, c.h - 2, shade(CREAM_SH[0], 0.92))       # tiny mouth tuft


def eye(c):
    c.fill(EYE)
    if c.face == "front":
        c.set(0, 0, EYE_HI)
        c.set(1, 0, EYE_2)
        c.set(0, 1, EYE_2)
    elif c.face == "right":                                  # seen from the side: shine at the front
        c.set(c.w - 1, 0, EYE_2)
    elif c.face == "top":
        c.fill(EYE_2)


def tuft(c):
    c.noise(RUFF)
    if c.face in SIDES:
        c.clear(0, 0) if c.w > 2 else None
        c.clear(c.w - 1, 0) if c.w > 2 else None


FEATHER = [
    ".s.",
    "bsb",
    ".s.",
    "bsb",
    ".s.",
    "bsb",
]


def antenna(c):
    for y in range(c.h):
        for x in range(c.w):
            ch = FEATHER[y][x]
            if ch == ".":
                c.clear(x, y)
            elif ch == "s":
                c.set(x, y, ANT_DK)
            else:
                c.set(x, y, shade(ANT, 1.0 + 0.06 * ((x + y) % 2)))


def leg(c):
    c.noise(LEG)
    if c.face in SIDES:
        c.set(0, c.h - 1, shade(LEG[0], 0.75))


# -- wings: pure functions of (x, y), so the top and bottom planes match pixel for pixel -------------
def _h(x, y, salt):
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


def _line(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    return {(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)}


def wing(mask, spot, veins, salt, costa=False, tail=()):
    """mask: rows from the BACK edge (row 0) to the leading edge, column 0 = the wing tip (the mob's
    right side, as the right wing sees it). spot: {(x, y): 'r' ring | 'R' light ring | 'c' core |
    'h' highlight}. veins: set of pixels that glow very faintly."""
    h, w = len(mask), len(mask[0])

    def solid(x, y):
        if x >= w:
            return True                       # the wing root, joined to the body
        return 0 <= x and 0 <= y < h and mask[y][x] != "."

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if not solid(x, y):
                    c.clear(x, y)
                    continue
                r = _h(x, y, salt)
                col = MINT[int(r * len(MINT)) % len(MINT)]
                t = x / (w - 1)                                  # 0 at the tip, 1 at the root
                if t > 0.62:
                    col = mix(col, WING_BASE, min(1.0, (t - 0.62) * 1.9))   # pale furry root
                edge = not all(solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    col = MARGIN[int(r * 7) % 2]
                    if not solid(x, y - 1) and not solid(x - 1, y):
                        col = shade(col, 0.95)
                if costa and y == h - 1 and x >= 1:
                    col = COSTA[int(r * 5) % 2]
                elif costa and y == h - 2 and x <= 1:
                    col = COSTA[0]
                if (x, y) in tail:
                    col = mix(col, SPOT_RING2, 0.6)               # rosy tail tips
                if (x, y) in veins and (x, y) not in spot and not (costa and y == h - 1):
                    soft_glow(c, x, y, mix(col, VEIN, 0.5), 0.18)
                    continue
                k = spot.get((x, y))
                if k == "r":
                    col = SPOT_RING
                elif k == "R":
                    col = SPOT_RING2
                elif k == "c":
                    soft_glow(c, x, y, SPOT_CORE, 0.45)
                    continue
                elif k == "h":
                    soft_glow(c, x, y, SPOT_HI, 0.6)
                    continue
                c.set(x, y, col)
    return p


FORE_MASK = [
    ".......www",
    ".....wwwww",
    "....wwwwww",
    "...wwwwwww",
    "..wwwwwwww",
    ".wwwwwwwww",
    "wwwwwwwwww",
    "wwwwwwwwww",
    ".wwwwwwwww",
]
FORE_SPOT = {(4, 3): "r", (5, 3): "r",
             (3, 4): "r", (4, 4): "h", (5, 4): "c", (6, 4): "r",
             (3, 5): "r", (4, 5): "c", (5, 5): "c", (6, 5): "r",
             (4, 6): "r", (5, 6): "r"}
FORE_VEINS = (_line((9, 7), (2, 7)) | _line((8, 3), (5, 1)) | _line((9, 2), (8, 0))) - {(9, 7), (8, 3), (9, 2)}

HIND_MASK = [
    "..ww....",
    "..ww....",
    "...ww...",
    "...ww...",
    "...www..",
    "...wwww.",
    "..wwwwww",
    ".wwwwwww",
    "wwwwwwww",
    "wwwwwwww",
    "wwwwwwww",
    ".wwwwwww",
    "..wwwwww",
]
HIND_SPOT = {(3, 7): "r", (4, 7): "r",
             (2, 8): "r", (3, 8): "h", (4, 8): "c", (5, 8): "r",
             (2, 9): "r", (3, 9): "c", (4, 9): "c", (5, 9): "r",
             (3, 10): "r", (4, 10): "r"}
HIND_VEINS = (_line((7, 11), (1, 11)) | _line((6, 6), (4, 2))) - {(7, 11), (6, 6)}
HIND_TAIL = {(2, 0), (3, 0), (2, 1), (3, 1)}


def build():
    m = Model("glowmoth", 64, 64, seed=1313)
    pk = Pack(m)

    # body = the thorax, hovering: pivot y 17. The fluffy ruff is an inflated, half-cut-out shell.
    body = m.part("body", (0, 17, 0))
    pk.add(body, (-2.5, -2.5, -2.5), (5, 5, 5), faces(fuzz()))
    pk.add(body, (-2.5, -2.5, -2.5), (5, 5, 5), faces(ruff_overlay), inflate=0.5)

    abdomen = body.part("abdomen", (0, 0.5, 2), (-0.4, 0, 0))
    pk.add(abdomen, (-2, -2, 0), (4, 4, 6), faces(abdomen_fur))
    pk.add(abdomen, (-1, -1, 6), (2, 2, 1), faces(abdomen_fur))

    head = body.part("head", (0, -0.5, -2.5))
    pk.add(head, (-2.5, -2, -4), (5, 4, 4), faces(fuzz(), front=head_front))
    pk.add(head, (-2, -3, -3.5), (4, 1, 3), faces(tuft))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        pk.add(head, (-3.5 if sx < 0 else 1.5, -1.5, -4.5), (2, 3, 2), None if left else faces(eye),
               mirror=left, share="eye")
        a = head.part(side + "_antenna", (1.2 * sx, -2.5, -3), (0.35, 0.2 * sx, 0.4 * sx))
        pk.add(a, (-1.5, -6, 0), (3, 6, 0), None if left else faces(antenna), mirror=left, share="antenna")

    # wings: zero-thickness planes on the shoulders, raised in a V at rest. Right wings extend to -x,
    # so +z rotation lifts the right wings and -z lifts the left ones.
    fore = wing(FORE_MASK, FORE_SPOT, FORE_VEINS, 1, costa=True)
    hind = wing(HIND_MASK, HIND_SPOT, HIND_VEINS, 2, tail=HIND_TAIL)
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        fw = body.part(side + "_wing", (1.8 * sx, -2, -0.5), (0, 0.12 * -sx, 0.5 * -sx))
        pk.add(fw, (-10 if sx < 0 else 0, 0, -4), (10, 0, 9), None if left else faces(fore),
               mirror=left, share="forewing")
        hw = body.part(side + "_hindwing", (1.8 * sx, -1.4, 1.5), (0, 0.3 * -sx, 0.36 * -sx))
        pk.add(hw, (-8 if sx < 0 else 0, 0, -3), (8, 0, 13), None if left else faces(hind),
               mirror=left, share="hindwing")

    legs = body.part("legs", (0, 2.5, 0))
    for z in (-2, -0.5, 1):
        pk.add(legs, (-2, 0, z), (1, 2, 1), faces(leg), share="leg")
        pk.add(legs, (1, 0, z), (1, 2, 1), None, mirror=True, share="leg")

    pk.apply()
    m.save()
    spawn_egg("glowmoth", "#f2ead0", "#a6e2c0", accent="#b45574")


if __name__ == "__main__":
    build()

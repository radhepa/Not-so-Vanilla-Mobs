"""Mossback Tortoise: a big, slow, gentle tortoise with a little garden growing on its domed shell
(moss, grass tufts and a couple of flowers). The `garden` part holds every plant cube so the code
can hide it when the tortoise is sheared; the plated shell underneath is finished on its own."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Mossback Tortoise'
LOOT = [item("moss_carpet", 0, 1)]
TAGS = []


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None):
        self.items.append((part, origin, size, paint, mirror, share))

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
        for i, (part, origin, size, paint, mirror, share) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def seams(w, n):
    return {int(math.floor((i + 1) * (w - 1) / (n + 1) + 0.5)) for i in range(n)}


# -- palette -----------------------------------------------------------------------------------------
SH = ["#6a5733", "#62502f", "#715d37", "#665331", "#6d5935"]
RING = "#a88e55"
SEAM = "#3a311d"
PLAS = ["#b9a873", "#ae9e6a", "#c0b07c"]
PSEAM = "#857547"
SKIN = ["#7f8b66", "#78845f", "#86926d", "#727e5a"]
SCALE = "#606b4b"
SCALE_LIGHT = "#9ba57e"
NAIL = "#d8d0ad"
MOSS = ["#4e7a2b", "#588732", "#466f27", "#5f8f37", "#41662a"]
MOSS_LIGHT = ["#74a442", "#6c9c3d"]
GRASS = ["#5e9c36", "#6aac3e", "#55902f"]


def gshade(yw):
    """Shell light: bright at the crown (y 10), darker down at the rim (y 20)."""
    return 1.12 - 0.34 * (yw - 10) / 10


def grid(xs=(), ys=(), ytop=10, pal=SH, ring=RING, seam=SEAM, bottom=0.62):
    """Scute plates: seam lines at columns xs / rows ys, each plate with a pale growth ring."""
    def p(c):
        cx = sorted(set(xs) | {-1, c.w})
        cy = sorted(set(ys) | {-1, c.h})
        for y in range(c.h):
            if c.face == "top":
                f = gshade(ytop) * 1.04
            elif c.face == "bottom":
                f = bottom
            else:
                f = gshade(ytop + y + 0.5)
            dy = min(abs(y - s) for s in cy)
            for x in range(c.w):
                dx = min(abs(x - s) for s in cx)
                d = min(dx, dy)
                col = c.pick(pal)
                if d == 0:
                    col = seam
                elif d == 2:
                    col = mix(col, ring, 0.7)
                elif d >= 3:
                    col = shade(col, 1.07)
                c.set(x, y, shade(col, f))
    return p


def shell_cube(w, d, ytop, n_side, n_front, top_seams=True):
    """Painters for one tier of the shell (w wide, d long)."""
    sx, sz = seams(w, n_front), seams(d, n_side)
    return faces(
        front=grid(sx, (), ytop), back=grid(sx, (), ytop),
        right=grid(sz, (), ytop), left=grid(sz, (), ytop),
        top=ledge(ytop),
        bottom=grid((), (), ytop, pal=PLAS, ring="#c8b987", seam=PSEAM, bottom=0.8))


def ledge(ytop):
    """Top of a shell tier: only a thin ring shows around the tier above, kept plain and light."""
    def p(c):
        f = gshade(ytop) * 1.08
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(SH), f))
    return p


def plastron(c):
    """Belly plates, pale yellow."""
    ys = seams(c.h, 4)
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(PLAS)
            if y in ys or x == c.w // 2:
                col = PSEAM
            if x in (0, c.w - 1) or y in (0, c.h - 1):
                col = shade(col, 0.82)
            c.set(x, y, col)


def cap_top(c):
    """The crown of the shell (seen when the garden is sheared): two vertebral scutes."""
    grid((), seams(c.h, 1), 10)(c)
    for y in range(c.h):     # soft dark outline so the crown reads as a raised plate
        c.set(0, y, shade(c.get(0, y), 0.8))
        c.set(c.w - 1, y, shade(c.get(c.w - 1, y), 0.8))


# -- skin ------------------------------------------------------------------------------------------
def skin(grad=0.22, scales=0.18, light=0.07):
    def p(c):
        for y in range(c.h):
            if c.face == "top":
                f = 1.06
            elif c.face == "bottom":
                f = 0.72
            else:
                f = 1.0 - grad * (y / max(1, c.h - 1))
            for x in range(c.w):
                col = c.pick(SKIN)
                r = c.rng.random()
                if (x + y) % 2 == 0 and r < scales:
                    col = SCALE
                elif r > 1 - light:
                    col = SCALE_LIGHT
                c.set(x, y, shade(col, f))
    return p


def head_side(c):
    skin()(c)
    e0, e1 = fx(c, 1), fx(c, 2)       # eye sits one pixel back from the snout
    c.set(e1, 1, "#e9e6cf")
    c.set(e0, 1, "#17150f")
    c.set(e0, 2, "#17150f")
    c.set(e1, 2, "#2a271c")
    c.set(fx(c, 0), 3, "#4c5438")     # corner of the beak
    for i in range(c.w):              # lower jaw a touch paler
        c.set(i, 4, shade(mix(c.get(i, 4), "#a8a77f", 0.45), 1.0))


def head_front(c):
    skin(scales=0.1)(c)
    c.set(0, 1, "#17150f"); c.set(0, 2, "#17150f")            # eyes wrap round the corners
    c.set(c.w - 1, 1, "#17150f"); c.set(c.w - 1, 2, "#17150f")
    c.set(2, 1, "#4a5236"); c.set(3, 1, "#4a5236")            # nostrils
    for x in range(1, c.w - 1):                                # beak line, a small smile
        c.set(x, 3, "#3f4630")
    c.set(1, 3, "#555e41"); c.set(c.w - 2, 3, "#555e41")
    for x in range(c.w):
        c.set(x, 4, mix(c.pick(SKIN), "#b0ad84", 0.5))
    for x in (0, c.w - 1):
        c.set(x, 3, shade(c.pick(SKIN), 0.85))


def head_top(c):
    skin(scales=0.0, light=0.0)(c)
    # big head scutes, outlined
    for y in range(c.h):
        for x in range(c.w):
            if y in (1, 3) or (x in (1, c.w - 2) and y > 0):
                c.set(x, y, shade(SCALE, 1.05))
            elif 1 < x < c.w - 2 and y in (2, 4):
                c.set(x, y, SCALE_LIGHT)


def neck(c):
    skin(scales=0.1)(c)
    if c.face in ("right", "left", "top", "bottom"):
        for y in range(c.h):
            for x in range(c.w):
                col_i = x if c.face in ("top", "bottom") else (c.w - 1 - x if c.face == "right" else x)
                if col_i % 2 == 1 and c.rng.random() < 0.8:      # wrinkles across the neck
                    c.set(x, y, shade(c.get(x, y), 0.85))


def leg_side(c):
    skin(grad=0.25, scales=0.25, light=0.12)(c)
    for x in range(c.w):
        if x % 2 == 0:
            c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.85))
    if c.face in ("right", "left"):
        c.set(fx(c, 0), c.h - 1, NAIL)
    if c.face == "front":
        for x in (0, 2, 4):
            c.set(x, c.h - 1, NAIL)


def sole(c):
    c.noise(["#4f573f", "#555e44", "#4a523a"])


def tail_paint(c):
    skin(grad=0.3)(c)
    if c.face == "back":
        c.fill(shade(SKIN[0], 0.82))


# -- garden ------------------------------------------------------------------------------------------
def moss(top=1.0, drip=False):
    def p(c):
        for y in range(c.h):
            f = top * (1.08 if c.face == "top" else 0.78 if c.face == "bottom" else 1.0 - 0.18 * y)
            for x in range(c.w):
                col = c.pick(MOSS_LIGHT) if c.rng.random() < 0.14 else c.pick(MOSS)
                c.set(x, y, shade(col, f))
        if drip and c.face in ("front", "back", "left", "right"):
            for x in range(c.w):
                if c.rng.random() < 0.35:
                    c.clear(x, c.h - 1)
    return p


def mat_top(c):
    moss()(c)
    for _ in range(6):          # tiny bright sprigs on the mat
        c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), "#8cbc52")


def sprite(rows, pal):
    """A flat cut-out (grass tuft, flower) from a little character map; '.' is transparent."""
    def p(c):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == ".":
                    c.clear(x, y)
                else:
                    v = pal[ch]
                    c.set(x, y, c.pick(v) if isinstance(v, list) else v)
    return faces(front=p, back=p)


TUFT = sprite([
    ".g...",
    ".g.g.",
    "gG.gG",
    "GGgGG",
], {"g": GRASS, "G": ["#4b8229", "#538c2d"]})

TUFT_SMALL = sprite([
    "g..g",
    "gGgG",
    "GGGG",
], {"g": GRASS, "G": ["#4b8229", "#538c2d"]})

PINK = sprite([
    ".p.",
    "pyp",
    ".p.",
    ".G.",
    "GG.",
], {"p": ["#e88ab8", "#de7cad"], "y": "#f6d65a", "G": ["#4e8a2c", "#5a9a33"]})

DANDELION = sprite([
    "yYy",
    ".y.",
    ".G.",
    ".GG",
], {"y": ["#f5d03c", "#f0c22e"], "Y": "#fbe27a", "G": ["#4e8a2c", "#5a9a33"]})


def crossed(parent, pk, name, pivot, size, paint, share, yaw=0.0):
    """Two flat planes crossed at 90 degrees, Minecraft-plant style."""
    w, h = size
    for i, ang in enumerate((math.pi / 4 + yaw, -math.pi / 4 + yaw)):
        p = parent.part(f"{name}_{'ab'[i]}", pivot, (0, ang, 0))
        pk.add(p, (-w / 2, -h, 0), (w, h, 0), paint if i == 0 else None, share=share)


def build():
    m = Model("mossback_tortoise", 128, 64, seed=8080)
    pk = Pack(m)

    # body = shell; pivot at y 17, cubes stacked into a dome (rim y 18-20 ... crown y 10-11)
    body = m.part("body", (0, 17, 0))
    pk.add(body, (-9, 1, -10), (18, 2, 20), {**shell_cube(18, 20, 18, 4, 4), "bottom": plastron})
    pk.add(body, (-8, -3, -9), (16, 4, 18), shell_cube(16, 18, 14, 2, 2))
    pk.add(body, (-6.5, -6, -7.5), (13, 3, 15), shell_cube(13, 15, 11, 2, 2))
    pk.add(body, (-4.5, -7, -5.5), (9, 1, 11), {**shell_cube(9, 11, 10, 1, 1), "top": cap_top})

    # head + neck, child of root so the code can turn it (and pull it into the shell)
    head = m.part("head", (0, 17, -8))
    pk.add(head, (-2, -2, -4), (4, 4, 5), faces(neck))
    pk.add(head, (-3, -5, -9), (6, 5, 6), faces(skin(), front=head_front, right=head_side,
                                                   left=head_side, top=head_top))

    # stumpy elephant legs (one texture, left ones mirrored)
    legp = faces(leg_side, bottom=sole, top=skin())
    for name, x, z in (("right_front_leg", -6, -6), ("left_front_leg", 6, -6),
                       ("right_hind_leg", -6, 6.5), ("left_hind_leg", 6, 6.5)):
        leg = m.part(name, (x, 19, z))
        left = name.startswith("left")
        pk.add(leg, (-2.5, 0, -2.5), (5, 5, 5), None if left else legp, mirror=left, share="leg")

    tail = m.part("tail", (0, 18.5, 9.5), (-0.55, 0, 0))
    pk.add(tail, (-1, -1, -1), (2, 2, 4), faces(tail_paint))

    # garden: everything green on top of the shell (hidden when sheared)
    garden = body.part("garden", (0, -7, 0))
    pk.add(garden, (-5, -1, -6), (10, 1, 12), faces(moss(drip=True), top=mat_top))
    pk.add(garden, (-4, -2, -0.5), (6, 1, 6), faces(moss(1.05, drip=True), top=mat_top))
    # moss creeping over the edge of the dome on the left, a smaller patch on the right
    pk.add(garden, (4.5, 0, -3), (3, 1, 5), faces(moss(), top=mat_top))
    pk.add(garden, (6.5, 1, -3), (1, 2, 5), faces(moss(0.95, drip=True)))
    pk.add(garden, (-7.5, 0, 2), (3, 1, 4), faces(moss(), top=mat_top))
    pk.add(garden, (-7.5, 1, 2), (1, 2, 4), faces(moss(0.95, drip=True)))
    crossed(garden, pk, "tuft1", (-2, -2, 2), (5, 4), TUFT, "tuft")
    crossed(garden, pk, "tuft2", (3, -1, -3.5), (4, 3), TUFT_SMALL, "tuft_small", 0.3)
    crossed(garden, pk, "tuft3", (-3, -1, -4), (4, 3), None, "tuft_small", -0.2)
    crossed(garden, pk, "flower1", (1, -2, 3), (3, 5), PINK, "pink")
    crossed(garden, pk, "flower2", (-0.5, -1, -2.5), (3, 4), DANDELION, "dandelion", 0.4)

    pk.apply()
    m.save()
    spawn_egg("mossback_tortoise", "#6b5d37", "#5a8a33", accent="#e88ab8")


if __name__ == "__main__":
    build()

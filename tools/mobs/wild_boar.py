"""Wild Boar: a bristly wild pig of the forests and taigas, chunkier and darker than a farm pig. Coarse
grizzled brown-grey fur, heavy high shoulders that fall away to a smaller rump, and a crest of stiff
dark bristles (light-tipped) from between the ears down the spine, tallest over the shoulders. A
big wedge-shaped head steps down to a long snout ending in a flat pinkish-grey nose disc with two
dark nostrils; curved ivory tusks curl up out of the lower jaw on each side. Small dark eyes, short
pointed hairy ears, a thin tail with a dark tuft and short sturdy legs on dark cloven hooves.

`wild_boar_piglet` is the striped boarlet on the same geometry (the game draws it at half scale):
warm brown with bold cream stripes running lengthwise along the back and sides, a soft short mane
and no tusks (those cubes are left empty in its texture)."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Wild Boar"
LOOT = [item("porkchop", 1, 3), item("leather", 0, 1)]
TAGS = []


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    """Shelf packer. pad=True keeps a transparent 1 px gutter left and right of a cube's texture:
    flat bristle planes (and cubes the piglet leaves empty) would otherwise pick up a hairline of
    the neighbouring texels along their cut-out edges."""
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0, pad=False):
        self.items.append((part, origin, size, paint, mirror, share, inflate, pad))

    def apply(self):
        def dims(size, pad):
            w, h, d = (int(math.ceil(s)) for s in size)
            return 2 * d + 2 * w + (2 if pad else 0), d + h
        keys, order, pads = {}, [], {}
        for i, it in enumerate(self.items):
            k = it[5] or ("#", i)
            if k not in keys:
                keys[k] = None
                pads[k] = it[7]
                order.append((k, dims(it[2], it[7])))
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
        for i, (part, origin, size, paint, mirror, share, inflate, pad) in enumerate(self.items):
            k = share or ("#", i)
            u, v = keys[k]
            part.cube((u + (1 if pads[k] else 0), v), origin, size, paint, inflate=inflate, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position (so both faces of a flat plane get the same pixels)."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


SIDES = ("front", "back", "left", "right")

# -- palettes ----------------------------------------------------------------------------------------
ADULT = dict(
    kind="adult",
    fur=["#4a3b30", "#463729", "#4a3b30", "#45372c"],
    fleck=["#6b5a4a", "#574638", "#655444"],
    fleck_dk=["#3d3028", "#382c25"],
    dark=["#30261f", "#2c231d"],
    belly=["#3a2e26", "#352a22"],
    cheek=["#5e4d3f", "#655343", "#594839"],
    bristle=["#2a211b", "#2f251e", "#251d18"],
    bristle_tip=["#6b5a4a", "#5c4b3d", "#7a6858"],
    snout=["#4f4038", "#4a3c34", "#55453c"],
    disc=["#8c6f68", "#866962", "#917470"],
    disc_rim="#6e5550",
    nostril="#2a1e1c",
    eye="#0d0907", eye_ring="#1d1511", brow="#6b5a4a",
    ear_in=["#6e5550", "#6a514b"],
    tusk="#efe6cf", tusk_sh="#d8ceb3", tusk_root="#c4b593",
    hoof=["#2a2420", "#25201c"], hoof_hi="#3d3530",
    tuft=["#2a211b", "#241c17"],
)
PIGLET = dict(
    kind="piglet",
    fur=["#a0724a", "#9a6c45", "#a77a50"],
    cream=["#e2c58c", "#dcbd82", "#e8cd96"],
    stripe=["#6b4a2e", "#654529", "#714f33"],
    belly=["#b38a62", "#ad845c"],
    head=["#9a6c45", "#a0724a", "#94683f"],
    cheek=["#b08257", "#aa7c52"],
    bristle=["#7a5536", "#73502f"],
    bristle_tip=["#a0724a", "#94683f"],
    snout=["#a57a55", "#9f7550"],
    disc=["#b78f84", "#b0887d"],
    disc_rim="#94706a",
    nostril="#4a302a",
    eye="#120c08", eye_ring="#4a3220", brow="#b08257",
    ear_in=["#b78f84", "#ad877c"],
    hoof=["#4a3a2e", "#43352a"], hoof_hi="#5e4b3c",
    tuft=["#6b4a2e", "#5e4128"],
)


def fur(P, top=1.08, grad=0.26, bottom=0.8, flecks=0.07, strokes=0.09, y0=0, span=None, spine=False):
    """Coarse grizzled fur: noisy brown-grey with paler flecks and short vertical hair strokes. Sides
    darken downward (y0/span place a face on a body-wide gradient); the top is lit, the belly dark."""
    def p(c):
        sp = span or c.h
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    col, f = c.pick(P["belly"]), bottom
                else:
                    col = c.pick(P["fur"])
                    r = c.rng.random()
                    if r < flecks:
                        col = c.pick(P["fleck"])
                    elif r < flecks * 2 and "fleck_dk" in P:
                        col = c.pick(P["fleck_dk"])
                    f = top if c.face == "top" else 1.06 - grad * ((y0 + y + 0.5) / sp)
                c.set(x, y, shade(col, f))
        if c.face == "top" and spine:                 # darker fur down the spine, under the mane
            for y in range(c.h):
                for x in (c.w // 2 - 1, c.w // 2):
                    if c.rng.random() < 0.75:
                        c.set(x, y, shade(c.pick(P["dark"]), 1.1))
        if c.face in ("top", "bottom"):
            return
        for _ in range(int(c.w * c.h * strokes)):     # bristly strokes, 2 px long, darker or paler
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            k = 0.88 if c.rng.random() < 0.7 else 1.12
            for yy in (y, y + 1):
                if c.inside(x, yy):
                    c.set(x, yy, shade(c.get(x, yy), k))
    return p


# piglet stripes: by world height on the sides, by distance from the spine on the back
SIDE_STRIPES = {8: "fur", 9: "cream", 10: "stripe", 11: "fur", 12: "cream", 13: "stripe", 14: "fur",
                15: "cream", 16: "belly", 17: "belly"}


def stripes(P, ytop, top_pattern):
    """The boarlet's lengthwise stripes. ytop: world y of this cube's top (side rows follow world
    height so stripes run on unbroken from shoulders to rump); top_pattern: one band per column of
    the top face, mob's right to left."""
    def band(c, name, f=1.0):
        if name == "cream" and c.rng.random() < 0.12:
            name = "fur"                               # the pale stripes break up here and there
        col = c.pick(P[name])
        if name == "fur" and c.rng.random() < 0.15:
            col = shade(col, 0.9)
        return shade(col, f)

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = band(c, top_pattern[x] if x < len(top_pattern) else "fur", 1.06)
                elif c.face == "bottom":
                    col = shade(c.pick(P["belly"]), 0.88)
                elif c.face in ("left", "right"):
                    col = band(c, SIDE_STRIPES.get(ytop + y, "belly"), 1.04 - 0.12 * y / max(1, c.h - 1))
                else:                                  # chest and rump: plain warm brown
                    col = shade(c.pick(P["fur"]), 1.02 - 0.15 * y / max(1, c.h - 1))
                    if ytop + y >= 16:
                        col = shade(c.pick(P["belly"]), 0.95)
                c.set(x, y, col)
    return p


def body_paint(P, ytop, top_pattern, y0):
    if P["kind"] == "piglet":
        return faces(stripes(P, ytop, top_pattern))
    return faces(fur(P, y0=y0, span=10, spine=True))


# -- bristles ----------------------------------------------------------------------------------------
JAG = (0, 1, 0, 2, 0, 1, 1, 0)


def bristles(P, tips, inside, soft_row=None, seed=0):
    """A flat bristle plane (x size 0). tips[i]: the row of the tallest bristle in column i (i counted
    from the front); a jagged comb of 1 px spikes cuts the top, each spike light-tipped. Rows >= inside
    are buried in the body. Both faces are painted from the same position hash, so the cutout reads
    the same from either side. soft_row: the piglet's short fuzz (nothing above that row)."""
    def p(c):
        for x in range(c.w):
            i = fx(c, x)
            t = tips[min(i, len(tips) - 1)] + JAG[(i + seed) % len(JAG)]
            if soft_row is not None:
                t = max(t, soft_row + (1 if hsh(i, seed, 7) < 0.4 else 0))
            for y in range(c.h):
                r = hsh(i, y, seed)
                if y < t:
                    c.clear(x, y)
                    continue
                if y == t:
                    col = P["bristle_tip"][int(r * len(P["bristle_tip"]))]
                elif y == t + 1 and r < 0.5:
                    col = mix(P["bristle_tip"][0], P["bristle"][0], 0.5)
                else:
                    col = P["bristle"][int(r * len(P["bristle"]))]
                    if r > 0.85:                       # a few paler strands down the comb
                        col = shade(col, 1.35)
                if y >= inside:
                    col = shade(col, 0.8)
                c.set(x, y, col)
    return p


def crest(P):
    """The solid ridge the bristles grow from: dark roots in vertical strands, pale tips on top.
    The piglet has no ridge (left empty): its soft mane is just the short fuzz of the combs."""
    def p(c):
        if P["kind"] == "piglet":
            for y in range(c.h):
                for x in range(c.w):
                    c.clear(x, y)
            return
        base = P["bristle"]
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(base)
                if c.face == "top":
                    if c.rng.random() < 0.4:
                        col = c.pick(P["bristle_tip"])
                elif c.face in SIDES:
                    if y == 0 and c.rng.random() < 0.5:
                        col = mix(c.pick(P["bristle_tip"]), col, 0.4)
                    elif x % 2 == 1:
                        col = shade(col, 0.85)
                c.set(x, y, col)
    return p


# -- head --------------------------------------------------------------------------------------------
def head_fur(P, light=0.0, top=1.08, grad=0.22):
    """Head fur: like the body's, a little greyer (light > 0 mixes in the pale cheek grizzle)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["head"] if "head" in P else P["fur"])
                if "fleck" in P and c.rng.random() < 0.14:
                    col = c.pick(P["fleck"])
                if light and c.rng.random() < light:
                    col = c.pick(P["cheek"])
                if c.face == "top":
                    f = top
                elif c.face == "bottom":
                    f = 0.78
                else:
                    f = 1.05 - grad * (y / max(1, c.h - 1))
                c.set(x, y, shade(col, f))
    return p


def skull_side(P):
    def p(c):
        head_fur(P, light=0.0)(c)
        for y in range(3, c.h):                        # grizzled grey jowls low on the cheek
            for x in range(c.w):
                if fx(c, x) <= 3 and c.rng.random() < 0.45:
                    c.set(x, y, shade(c.pick(P["cheek"]), 1.0 - 0.04 * y))
        e0, e1 = fx(c, 1), fx(c, 2)                    # a small dark eye under a pale brow
        c.set(e0, 2, P["eye"])
        c.set(e1, 2, P["eye_ring"])
        c.set(e0, 1, shade(P["brow"], 1.1))
        c.set(e1, 1, P["brow"])
        c.set(fx(c, 0), 2, shade(P["brow"], 0.9))
        c.set(e0, 3, shade(P["brow"], 0.85))
    return p


def skull_front(P):
    def p(c):
        head_fur(P, light=0.15)(c)
        for x in (0, c.w - 1):                         # the eyes just wrap the front corners
            c.set(x, 2, P["eye_ring"])
            c.set(x, 1, P["brow"])
    return p


def face_paint(P):
    """The block between skull and snout: grizzled grey, darker toward the snout."""
    def p(c):
        head_fur(P, light=0.3)(c)
        if c.face in ("right", "left"):
            for y in range(c.h):
                c.set(fx(c, 0), y, shade(c.get(fx(c, 0), y), 0.85))
    return p


def snout_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["snout"])
                if c.face == "top":
                    col = shade(col, 1.08)
                    if y >= c.h - 1:                   # wrinkled skin just behind the disc
                        col = mix(col, P["disc_rim"], 0.4)
                elif c.face == "bottom":
                    col = shade(col, 0.75)
                else:
                    col = shade(col, 1.04 - 0.12 * y)
                c.set(x, y, col)
        if c.face in ("right", "left"):                # the corner of the lip, under the disc
            c.set(fx(c, 0), c.h - 1, shade(c.pick(P["snout"]), 0.7))
            c.set(fx(c, 1), c.h - 1, shade(c.pick(P["snout"]), 0.78))
    return p


def disc(P):
    """The flat nose disc: pinkish-grey, a darker rim, two dark nostrils on the front."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["disc"])
                if c.face == "front":
                    if x in (0, c.w - 1) or y in (0, c.h - 1):
                        col = mix(col, P["disc_rim"], 0.6)
                elif c.face == "top":
                    col = shade(col, 1.06)
                else:
                    col = mix(col, P["disc_rim"], 0.5)
                c.set(x, y, col)
        if c.face == "front":                          # 4 x 3: nostrils in the middle row
            c.set(0, 0, mix(P["disc_rim"], "#000000", 0.2)); c.set(c.w - 1, 0, mix(P["disc_rim"], "#000000", 0.2))
            c.set(0, c.h - 1, mix(P["disc_rim"], "#000000", 0.2))
            c.set(c.w - 1, c.h - 1, mix(P["disc_rim"], "#000000", 0.2))
            c.set(1, 1, P["nostril"]); c.set(2, 1, P["nostril"])
            c.set(1, 0, shade(P["disc"][0], 1.1))      # a wet highlight over the left nostril
    return p


def jaw(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["snout"])
                c.set(x, y, shade(col, 0.72 if c.face == "bottom" else 0.85))
        if c.face == "front":
            for x in range(c.w):
                c.set(x, 0, shade(c.pick(P["snout"]), 0.6))   # the mouth line
    return p


def tusk(P, seg):
    """Ivory tusk segments: seg 'root' comes out of the jaw, 'mid' rises, 'tip' curls back.
    The piglet has no tusks: its root is a little nub of snout skin, the rest is left empty."""
    def p(c):
        if P["kind"] == "piglet":
            if seg == "root":
                c.noise(P["snout"])
            else:
                for y in range(c.h):
                    for x in range(c.w):
                        c.clear(x, y)
            return
        for y in range(c.h):
            for x in range(c.w):
                if c.face in ("top", "front", "right"):  # lit faces ("right" is the outer side;
                    col = P["tusk"]                       # the mirrored left tusk shows it outside too)
                else:
                    col = P["tusk_sh"]
                if seg == "root":
                    col = mix(col, P["tusk_root"], 0.55)
                if c.face == "bottom":
                    col = shade(P["tusk_sh"], 0.9)
                c.set(x, y, col)
        if seg == "tip" and c.face == "top":
            c.set(0, 0, "#fbf7ea")
    return p


def ear(P, part):
    def p(c):
        if part == "base" and c.face == "front":       # the hairy inner ear, facing forward
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, c.pick(P["ear_in"]) if y > 0 else c.pick(P["fur"]))
            c.set(0, 0, shade(c.pick(P["fur"]), 1.1))
            return
        head_fur(P, grad=0.1)(c)
        if part == "tip":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, shade(c.get(x, y), 0.8))
    return p


# -- legs, tail --------------------------------------------------------------------------------------
def leg(P):
    """Short sturdy leg: fur darkening down to a 2 px cloven hoof (a dark split up the front, a
    dewclaw at the back)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if y >= c.h - 2:
                    col = c.pick(P["hoof"])
                    if y == c.h - 2 and c.face in SIDES:
                        col = mix(col, P["hoof_hi"], 0.6)
                elif c.face == "top":
                    col = c.pick(P["fur"])
                else:
                    col = shade(c.pick(P["fur"] if P["kind"] == "piglet" else P["fur"] + P["dark"]),
                                1.04 - 0.3 * y / max(1, c.h - 3))
                    if P["kind"] == "piglet" and y >= c.h - 4:
                        col = shade(col, 0.82)
                c.set(x, y, col)
        if c.face == "front":
            c.set(c.w // 2, c.h - 1, shade(P["hoof"][0], 0.6))
            c.set(c.w // 2, c.h - 2, shade(P["hoof"][0], 0.75))
        elif c.face == "back":
            c.set(c.w // 2, c.h - 3, P["hoof_hi"])
    return p


def sole(P):
    def p(c):
        c.noise(P["hoof"])
        c.set(c.w // 2, c.h // 2, shade(P["hoof"][0], 0.6))
    return p


def tail_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(P["fur"]), 1.0 - 0.15 * y / max(1, c.h - 1)))
    return p


def tuft(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["tuft"])
                if c.rng.random() < 0.2:
                    col = c.pick(P["bristle_tip"])
                c.set(x, y, col)
    return p


# -- the model ---------------------------------------------------------------------------------------
SHOULDER_TOP = ["fur", "cream", "fur", "cream", "stripe", "stripe", "cream", "fur", "cream", "fur"]
RUMP_TOP = ["cream", "fur", "cream", "stripe", "stripe", "cream", "fur", "cream"]


def make(texture_id, P):
    """Build the boar with the given palette. Geometry is identical for adult and piglet."""
    m = Model("wild_boar", 64, 64, seed=5151, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot (0, 13, 2). Shoulders x -5..5, y 8..18, z -7..0; the smaller rump x -4..4,
    # y 9..18, z 0..7.
    body = m.part("body", (0, 13, 2))
    pk.add(body, (-5, -5, -9), (10, 10, 7), body_paint(P, 8, SHOULDER_TOP, 0))
    pk.add(body, (-4, -4, -2), (8, 9, 7), body_paint(P, 9, RUMP_TOP, 1))

    # mane: a solid dark ridge over the shoulders, then two flat combs of bristles along the spine,
    # tallest over the shoulders and dwindling to the rump. Pivot on the shoulder top (world y 8).
    mane = body.part("mane", (0, -5, -5))
    pk.add(mane, (-1, -1.4, -3.5), (2, 2, 7), faces(crest(P)), pad=True)
    soft = P["kind"] == "piglet"
    pk.add(mane, (0, -6.5, -4), (0, 7, 7),
           faces(bristles(P, (3, 2, 1, 1, 1, 2, 3), 5, soft_row=5 if soft else None, seed=1)), pad=True)
    pk.add(mane, (0, -4.5, 3), (0, 6, 7),
           faces(bristles(P, (1, 1, 2, 2, 3, 3, 4), 5, soft_row=4 if soft else None, seed=4)), pad=True)

    # head: child of root, pivot at the neck, nose tipped down a little. Wedge in three steps:
    # skull (y 9..16), a narrower face block (y 11..16), then the snout (y 13..16) and its disc.
    head = m.part("head", (0, 12, -6), (0.2, 0, 0))
    pk.add(head, (-3.5, -3, -6), (7, 7, 6),
           faces(head_fur(P, light=0.1), front=skull_front(P), right=skull_side(P), left=skull_side(P)))
    pk.add(head, (-2.5, -1, -8), (5, 5, 2), faces(face_paint(P)))
    # a short tuft of bristles on the crown, between the ears, running back to meet the mane
    pk.add(head, (0, -6, -5), (0, 4, 4),
           faces(bristles(P, (2, 1, 1, 0), 3, soft_row=2 if soft else None, seed=9)), pad=True)
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        e = head.part(name, (2.5 * sx, -3, -2.5), (-0.2, 0, 0.45 * sx))
        left = sx > 0
        pk.add(e, (-1, -3, -0.5), (2, 3, 1), None if left else faces(ear(P, "base")), mirror=left, share="ear")
        pk.add(e, (0 if left else -1, -4, -0.5), (1, 1, 1), None if left else faces(ear(P, "tip")),
               mirror=left, share="ear_tip")

    snout = head.part("snout", (0, 1, -8))
    pk.add(snout, (-2, 0, -4), (4, 3, 4), faces(snout_paint(P)))
    pk.add(snout, (-2, 0, -4.5), (4, 3, 1), faces(disc(P)), inflate=0.15)
    pk.add(snout, (-1.5, 3, -3.5), (3, 1, 3), faces(jaw(P)))
    # tusks: up out of the lower jaw, outward and back along the sides of the snout
    for sx in (-1, 1):
        left = sx > 0
        pk.add(snout, (1.5 if left else -2.5, 2.5, -3.5), (1, 1, 1), None if left else faces(tusk(P, "root")),
               mirror=left, share="tusk_root")
        pk.add(snout, (2 if left else -3, 1, -3.25), (1, 2, 1), None if left else faces(tusk(P, "mid")),
               mirror=left, share="tusk_mid", pad=True)
        pk.add(snout, (2.25 if left else -3.25, 0, -2.75), (1, 1, 1), None if left else faces(tusk(P, "tip")),
               mirror=left, share="tusk_tip", pad=True)

    # tail: from the top of the rump, hanging and swung back a little, with a dark tuft
    tail = body.part("tail", (0, -3, 5), (0.3, 0, 0))
    pk.add(tail, (-0.5, 0, 0), (1, 4, 1), faces(tail_paint(P)))
    pk.add(tail, (-1, 3.5, -0.5), (2, 2, 2), faces(tuft(P)))

    # legs: pivot at the top (y 18), 1 px tucked into the body, hooves on the ground at y 24
    legp = faces(leg(P), bottom=sole(P))
    for name, x, z in (("right_front_leg", -2.5, -4), ("left_front_leg", 2.5, -4),
                       ("right_hind_leg", -2.4, 4.5), ("left_hind_leg", 2.4, 4.5)):
        lg = m.part(name, (x, 18, z))
        left = name.startswith("left")
        pk.add(lg, (-1.5, -1, -1.5), (3, 7, 3), None if left else legp, mirror=left, share="leg")

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("wild_boar_piglet", PIGLET).save(geometry=False)
    spawn_egg("wild_boar", "#4a3b30", "#efe6cf", accent="#8c6f68")


if __name__ == "__main__":
    build()

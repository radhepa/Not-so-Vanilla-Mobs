"""Deer: a slender forest deer. A tawny-brown coat, darker and greyer along the spine and lighter on
the flanks, a cream-white belly, a white throat patch, a white band behind a dark wet nose and a white
chin, big dark eyes with a pale ring and a dark gland at the front corner, large ears (pale inside,
dark-rimmed), a white rump patch and a short broad tail that is brown above and white beneath (the
code raises it in alarm to flash the white). Long thin legs with a backward hock on the hind legs,
lighter lower legs and dark hooves. Grown stags carry branching antlers (the `antlers` part; the
code hides it on does and fawns).

`deer_fawn` is the fawn on the same geometry (drawn at half scale): a warmer, redder brown with rows
of white spots along the back and flanks."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Deer"
LOOT = [item("leather", 0, 1)]
TAGS = []


# -- texture packing (as in otter.py): biggest cubes first, a 1 px clear margin round every cube ----
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0):
        self.items.append((part, origin, size, paint, mirror, share, inflate))

    @staticmethod
    def cells(size):
        w, h, d = (int(math.ceil(s)) for s in size)
        rects = [(d, 0, w, d), (d + w, 0, w, d), (0, d, d, h), (d, d, w, h), (d + w, d, d, h),
                 (2 * d + w, d, w, h)]
        px = {(x + i, y + j) for (x, y, rw, rh) in rects if rw > 0 and rh > 0
              for i in range(rw) for j in range(rh)}
        margin = {(x + dx, y + dy) for (x, y) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - px
        return px, margin

    def apply(self):
        tw, th = self.m.tex_w, self.m.tex_h
        keys, order = {}, []
        for i, it in enumerate(self.items):
            k = it[5] or ("#", i)
            if k not in keys:
                keys[k] = None
                px, margin = self.cells(it[2])
                order.append((k, px, margin))
        order.sort(key=lambda o: (-max(y for _, y in o[1]), -len(o[1])))
        used = {}
        for k, px, margin in order:
            mw, mh = max(x for x, _ in px) + 1, max(y for _, y in px) + 1
            spot = None
            for v in range(th - mh + 1):
                for u in range(tw - mw + 1):
                    if all((u + x, v + y) not in used for (x, y) in px) and \
                            all(used.get((u + x, v + y)) != "px" for (x, y) in margin):
                        spot = (u, v)
                        break
                if spot:
                    break
            if spot is None:
                raise ValueError(f"{self.m.id}: texture too small for {k}")
            keys[k] = spot
            for (x, y) in px:
                used[(spot[0] + x, spot[1] + y)] = "px"
            for (x, y) in margin:
                used.setdefault((spot[0] + x, spot[1] + y), "margin")
        for i, (part, origin, size, paint, mirror, share, inflate) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def front_dist(c, x, y):
    """How far a pixel of a side/top/bottom face is from the cube's front edge."""
    if c.face in ("top", "bottom"):
        return c.h - 1 - y
    return c.w - 1 - x if c.face == "right" else x


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position (spot patterns that line up across faces)."""
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
    coat=["#9c6b3f", "#a07043", "#96663b", "#a57548", "#9a6a40"],
    back=["#7f5a3a", "#85603f", "#795536", "#8a6442"],       # greyer brown along the spine
    hi=["#b68757", "#bb8c5c", "#b0814f"],
    belly=["#ece3d0", "#e4d9c3", "#f0e8d8"],
    white=["#f4efe6", "#ece5d8", "#f7f3ec"],
    white_sh=["#d6ccbb", "#cfc4b1"],
    leg=["#a77a50", "#ad7f55", "#a2754b"],
    leg_dk=["#6f4b2e", "#74502f"],
    hoof=["#2a2421", "#312a26"], hoof_hi="#58504a",
    nose="#1b1513", nose_hi="#5a4d47", nostril="#0c0908",
    eye="#100b09", glint="#f8f5ee", ring=["#efe7d6", "#e6dcc8"], gland="#3e2b1e",
    brow=["#8a603b", "#80583a"],
    ear_in=["#e0c7b6", "#d9bfac", "#e6d0c0"], ear_rim="#3f2c1e", ear_hair="#f4eee4",
    tail_rim=["#5e3f27", "#563a24"],
)
FAWN = dict(
    ADULT,
    kind="fawn",
    coat=["#b8763f", "#bd7c45", "#b2703b", "#c3834b"],
    back=["#9e5f30", "#a46535", "#985a2d"],
    hi=["#cc9058", "#d0955d"],
    leg=["#bf834f", "#c4884f"],
    leg_dk=["#8e5a32", "#94603a"],
    spot=["#f5eee2", "#efe5d2", "#faf5ec"],
)
ANTLER = ["#6c573f", "#8f775a", "#ad9670", "#c9b58f", "#e3d6b7", "#f3ecda"]


def coat(P, top=1.08, grad=0.3, belly_rows=0, strokes=0.12, dorsal=True, y0=0, span=None):
    """Short glossy deer hair: tawny with fine darker strokes, lit on top with a greyer band down the
    spine, darkening down the sides and turning cream in the last belly_rows. y0/span put a face on a
    body-wide gradient."""
    def p(c):
        sp = span or c.h
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["coat"])
                if c.face == "top":
                    f = top
                    if dorsal:
                        d = abs(x - (c.w - 1) / 2) / max(1.0, c.w / 2)   # 0 on the spine
                        col = mix(c.pick(P["back"]), col, min(1.0, d * 1.6))
                elif c.face == "bottom":
                    col, f = c.pick(P["belly"]), 0.94
                else:
                    t = (y0 + y + 0.5) / sp
                    f = 1.08 - grad * t
                    if c.face in ("left", "right") and y0 + y < 1:
                        col = mix(col, c.pick(P["back"]), 0.5)          # the top of the flank greys
                    if belly_rows and y >= c.h - belly_rows and c.face in ("left", "right"):
                        k = 0.85 if y == c.h - 1 else 0.45
                        col, f = mix(col, c.pick(P["belly"]), k), 1.0
                c.set(x, y, shade(col, f))
        if c.face in ("left", "right", "front", "back"):        # fine hair strokes, 2 px long
            for _ in range(int(c.w * c.h * strokes)):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                k = 0.9 if c.rng.random() < 0.65 else 1.08
                for yy in (y, y + 1):
                    if c.inside(x, yy) and not (belly_rows and yy >= c.h - belly_rows):
                        c.set(x, yy, shade(c.get(x, yy), k))
        if c.face == "top":                                      # a few sunlit hairs
            for _ in range(int(c.w * c.h * 0.06) + 1):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, mix(c.get(x, y), c.pick(P["hi"]), 0.6))
    return p


def spots(P, rows, faces_=("top", "left", "right"), seed=0, every=3):
    """The fawn's white spots: lines of single spots (sometimes doubled) along the given rows. On the
    top face rows are columns either side of the spine; on the sides they are pixel rows."""
    def p(c):
        if P["kind"] != "fawn" or c.face not in faces_:
            return
        if c.face == "top":
            cols = [r for r in rows if 0 <= r < c.w] + [c.w - 1 - r for r in rows if 0 <= c.w - 1 - r < c.w]
            for x in cols:
                for y in range(c.h):
                    if (y + x + seed) % every == 0 and hsh(x, y, seed) < 0.85:
                        c.set(x, y, c.pick(P["spot"]))
        else:
            for r in rows:
                if not 0 <= r < c.h:
                    continue
                for x in range(c.w):
                    i = fx(c, x)
                    if (i + r + seed) % every == 0 and hsh(i, r, seed) < 0.85:
                        c.set(x, r, c.pick(P["spot"]))
                        if hsh(i, r, seed, 3) < 0.25 and c.inside(x, r + 1):
                            c.set(x, r + 1, shade(c.pick(P["spot"]), 0.95))
    return p


def chain(*ps):
    def run(c):
        for p in ps:
            p(c)
    return run


# -- body --------------------------------------------------------------------------------------------
def chest_front(P):
    """The front of the chest, under the neck: brown, a little darker in the middle, cream below."""
    def p(c):
        coat(P, grad=0.25)(c)
        for y in range(c.h):
            for x in range(c.w):
                if y >= c.h - 2:
                    c.set(x, y, mix(c.get(x, y), c.pick(P["belly"]), 0.5 if y == c.h - 2 else 0.8))
                elif 1 <= x <= c.w - 2 and y >= 1:
                    c.set(x, y, shade(c.get(x, y), 0.93))
    return p


def rump_back(P):
    """The rump seen from behind: a white patch under the tail (the hanging tail hides most of it;
    raised in alarm it shows), tapering at the bottom, edged with darker hair."""
    def p(c):
        coat(P, grad=0.2)(c)
        for y in range(1, c.h):
            for x in range(c.w):
                inner = 1 <= x <= c.w - 2
                if y < c.h - 1 and inner:
                    c.set(x, y, c.pick(P["white"]) if y < c.h - 2 else c.pick(P["white_sh"]))
                elif y == c.h - 1 and 2 <= x <= c.w - 3:
                    c.set(x, y, c.pick(P["white_sh"]))
                elif y < c.h - 1:
                    c.set(x, y, mix(c.get(x, y), c.pick(P["tail_rim"]), 0.45))
    return p


def body_top(P, rows):
    return chain(coat(P), spots(P, rows, ("top",), seed=1))


def body_side(P, ytop, seed):
    """Flanks: world rows 8..12 carry the fawn's spot lines, the bottom row turns cream."""
    return chain(coat(P, y0=ytop - 7, span=7, belly_rows=1),
                 spots(P, [8 - ytop, 10 - ytop], ("left", "right"), seed=seed))


def withers(P):
    return chain(coat(P, grad=0.15), spots(P, [1], ("top",), seed=5))


# -- head --------------------------------------------------------------------------------------------
def skull_side(P):
    """4 deep x 4 tall. A big dark eye near the front with a white glint and a faint pale ring, the
    dark gland streak running forward from its front corner, the jaw paler below."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["coat"])
                if y == 0:
                    col = mix(col, c.pick(P["brow"]), 0.6)
                elif y == c.h - 1:
                    col = mix(col, c.pick(P["belly"]), 0.4)
                c.set(x, y, shade(col, 1.04 - 0.04 * y))
        ring = lambda k: mix(c.pick(P["ring"]), c.pick(P["coat"]), k)
        e0, e1 = fx(c, 1), fx(c, 2)
        c.set(e0, 1, P["glint"]); c.set(e1, 1, P["eye"])
        c.set(e0, 2, P["eye"]); c.set(e1, 2, shade(P["eye"], 0.8))
        c.set(e0, 0, ring(0.45)); c.set(e1, 0, ring(0.6))
        c.set(fx(c, 3), 1, ring(0.55)); c.set(fx(c, 3), 2, ring(0.7))
        c.set(e0, 3, ring(0.35)); c.set(e1, 3, ring(0.5))
        c.set(fx(c, 0), 2, P["gland"])                       # the preorbital gland
        c.set(fx(c, 0), 3, mix(P["gland"], c.pick(P["coat"]), 0.5))
        c.set(fx(c, 0), 1, ring(0.6))
    return p


def skull_front(P):
    """5 wide x 4 tall; the snout covers columns 1-3 of rows 1-3. A dark brow, the eye rings just
    reaching round the front corners."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["brow"]) if y == 0 else c.pick(P["coat"])
                c.set(x, y, shade(col, 1.03 - 0.04 * y))
        for x in (0, c.w - 1):
            c.set(x, 1, mix(c.pick(P["ring"]), c.pick(P["coat"]), 0.55))
            c.set(x, 3, mix(c.pick(P["belly"]), c.pick(P["coat"]), 0.5))
        c.set(c.w // 2, 0, shade(c.pick(P["brow"]), 0.85))  # a dark forehead whorl
    return p


def skull_top(P):
    def p(c):
        coat(P, top=1.05, dorsal=False)(c)
        for y in range(c.h):
            c.set(c.w // 2, y, mix(c.get(c.w // 2, y), c.pick(P["brow"]), 0.7))
    return p


def skull_bottom(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(P["white"]) if y >= c.h - 2 else c.pick(P["belly"]))
    return p


def skull_back(P):
    return coat(P, grad=0.2, dorsal=False)


def band_of(P):
    """The pale band just behind the nose: creamy, not stark white, so it doesn't read as eyes."""
    return lambda c: mix(c.pick(P["white"]), c.pick(P["coat"]), 0.38)


def snout(P):
    """3 x 3 x 3 between the eyes and the nose: a darker bridge on top, brown cheeks, the white band
    just behind the nose wrapping round the front column, white lips and chin below."""
    band = band_of(P)

    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(P["coat"]), 1.02 - 0.05 * y)
                if f == "top":
                    d = c.h - 1 - y                           # 0 at the front
                    col = band(c) if d == 0 else shade(c.pick(P["brow"]), 1.06 - 0.04 * d)
                elif f == "bottom":
                    col = c.pick(P["white"]) if y >= 1 else c.pick(P["white_sh"])
                elif f in ("left", "right"):
                    i = fx(c, x)
                    if i == 0:
                        col = band(c) if y < c.h - 1 else c.pick(P["white"])
                    elif y == c.h - 1:
                        col = c.pick(P["white"]) if i == 1 else mix(c.pick(P["white"]), c.pick(P["coat"]), 0.4)
                c.set(x, y, col)
        if f in ("left", "right"):
            c.set(fx(c, 1), c.h - 1, mix(c.pick(P["white"]), "#000000", 0.5))   # the corner of the mouth
    return p


def nose(P):
    """3 x 2 x 1: the glossy black nose with two nostrils above a white upper lip (split by the dark
    philtrum)."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = P["nose"]
                if f == "bottom":
                    col = c.pick(P["white"])
                elif f in ("front", "left", "right") and y == c.h - 1:
                    lip = mix(c.pick(P["white"]), c.pick(P["coat"]), 0.25)
                    col = lip if not (f == "front" and x == 1) else shade(P["nose"], 1.6)
                c.set(x, y, col)
        if f == "front":
            c.set(0, 0, P["nostril"]); c.set(c.w - 1, 0, P["nostril"])
            c.set(1, 0, P["nose_hi"])                         # a wet highlight
        elif f == "top":
            c.set(1, 0, P["nose_hi"])
    return p


def ear_paint(P):
    """4 long x 3 tall x 1, pointing out and up. The front face is the inside of the ear: pale
    pinkish, white hairs along the lower edge, a thin dark rim round the tip; the back is brown,
    darker at the tip."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "front":
                    i = c.w - 1 - x                           # 0 by the head, 3 at the tip
                    if i == c.w - 1:
                        col = P["ear_rim"]
                    elif y == 0:
                        col = mix(c.pick(P["coat"]), P["ear_rim"], 0.5 if i >= 2 else 0.2)
                    elif y == c.h - 1:
                        col = P["ear_hair"] if hsh(x, 5) > 0.3 else c.pick(P["ear_in"])
                    elif i == 0:
                        col = shade(c.pick(P["ear_in"]), 0.85)
                    else:
                        col = c.pick(P["ear_in"]) if hsh(x, y, 7) > 0.25 else P["ear_hair"]
                elif f == "back":
                    col = shade(c.pick(P["coat"]), 1.02 - 0.06 * y)
                    if x == 0:
                        col = mix(col, P["ear_rim"], 0.6)
                elif f == "top":
                    col = shade(c.pick(P["coat"]), 1.05)
                elif f == "bottom":
                    col = P["ear_hair"]
                else:
                    col = P["ear_rim"] if f == "right" else c.pick(P["coat"])
                c.set(x, y, col)
    return p


def neck_paint(P):
    """The neck leans forward, so its front face is the throat: a white patch just under the jaw,
    then brown down to the chest."""
    def p(c):
        coat(P, grad=0.15, dorsal=False)(c)
        if c.face == "front":
            for y in range(c.h):
                for x in range(c.w):
                    if y <= 2 and (0 < x < c.w - 1 or y <= 1):
                        c.set(x, y, c.pick(P["white"]) if y <= 1 else c.pick(P["white_sh"]))
                    elif y >= 3:
                        c.set(x, y, shade(c.get(x, y), 0.92))
        elif c.face in ("left", "right"):
            for y in (0, 1):                                  # the throat patch wraps round a little
                c.set(fx(c, 0), y, c.pick(P["white_sh"]))
            for y in range(c.h):
                c.set(fx(c, c.w - 1), y, mix(c.get(fx(c, c.w - 1), y), c.pick(P["back"]), 0.5))
        elif c.face == "back":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, mix(c.get(x, y), c.pick(P["back"]), 0.55))
        if P["kind"] == "fawn" and c.face in ("left", "right"):
            for y in (2, 4):
                c.set(fx(c, 2), y, c.pick(P["spot"]))
    return p


# -- tail ----------------------------------------------------------------------------------------------
def tail_paint(P):
    """Points backward in its own space and hangs down at rest. The top is brown with a dark rim, the
    underside and the edges white: raised in alarm, the white flag shows."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "top":
                    col = c.pick(P["coat"])
                    if x in (0, c.w - 1):
                        col = c.pick(P["white"])              # white fringe either side
                    elif front_dist(c, x, y) == c.h - 1:
                        col = c.pick(P["tail_rim"])           # a dark tip
                elif f == "bottom":
                    col = c.pick(P["white"])
                elif f == "back":
                    col = c.pick(P["white"]) if x in (0, c.w - 1) else c.pick(P["tail_rim"])
                elif f in ("left", "right"):
                    col = shade(c.pick(P["coat"]), 0.9)
                else:
                    col = c.pick(P["coat"])
                c.set(x, y, col)
    return p


# -- legs ------------------------------------------------------------------------------------------------
def upper_leg(P, hind=False):
    """Forearm / thigh: body brown, a white inner side (the face toward the other leg), a white back
    edge on the hind thighs (the rump patch runs down them)."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(P["coat"]), 1.04 - 0.16 * y / max(1, c.h - 1))
                if f == "left":                               # the right leg's inner face
                    col = mix(col, c.pick(P["belly"]), 0.55 if y > 0 else 0.3)
                elif f == "back" and hind and x == 0 and 0 < y < c.h - 2:
                    col = mix(col, c.pick(P["belly"]), 0.4)
                elif f == "top":
                    col = c.pick(P["coat"])
                elif f == "bottom":
                    col = shade(c.pick(P["coat"]), 0.8)
                c.set(x, y, col)
        if hind and f == "right":                             # the back edge of the outer thigh whitens
            for y in range(1, c.h - 1):
                c.set(fx(c, c.w - 1), y, mix(c.get(fx(c, c.w - 1), y), c.pick(P["belly"]), 0.3))
        if P["kind"] == "fawn" and hind and f == "right":
            for i, y in ((1, 1), (2, 3)):
                c.set(fx(c, i), y, c.pick(P["spot"]))
    return p


def lower_leg(P):
    """Cannon bone: lighter tan stockings, a dark stripe down the front, pale inside."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(P["leg"]), 1.03 - 0.1 * y / max(1, c.h - 1))
                if f == "front":
                    col = mix(col, c.pick(P["leg_dk"]), 0.55 if x == 0 else 0.35)
                elif f == "left":
                    col = mix(col, c.pick(P["belly"]), 0.5)
                elif f == "back":
                    col = shade(col, 0.92)
                c.set(x, y, col)
        if f in ("left", "right", "back") and c.h >= 3:       # a pale ring above the hoof
            for x in range(c.w):
                c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(P["white"]), 0.5))
    return p


def gaskin(P):
    """The hind leg between stifle and hock: brown, the hock's back edge darker."""
    def p(c):
        upper_leg(P)(c)
        if c.face == "back":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, shade(c.pick(P["coat"]), 0.85))
    return p


def hoof(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["hoof"])
                if c.face in SIDES and y == 0:
                    col = mix(col, P["hoof_hi"], 0.5)
                c.set(x, y, col)
        if c.face == "front":
            c.set(c.w // 2, 0, shade(P["hoof"][0], 0.6))      # the cleft between the toes
        if c.face == "top":
            for x in range(c.w):
                for y in range(c.h):
                    c.set(x, y, shade(c.pick(P["leg"]), 0.8))
    return p


# -- antlers -------------------------------------------------------------------------------------------
def antler(y_lo, y_hi):
    """An antler segment spanning heights y_lo..y_hi above the burr (0 = burr, 9 = highest tip):
    dark and ridged at the base, bleaching to ivory at the tips. Lit on top and on the outer side."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    hgt = y_hi
                elif c.face == "bottom":
                    hgt = y_lo
                else:
                    hgt = y_hi - (y_hi - y_lo) * (y / max(1, c.h - 1))
                k = min(len(ANTLER) - 1, max(0, int(hgt / 9.0 * (len(ANTLER) - 1) + 0.5)))
                col = ANTLER[k]
                if c.face in ("left", "back", "bottom"):
                    col = shade(col, 0.86)
                elif c.face == "top":
                    col = shade(col, 1.06)
                if hgt < 2.5 and hsh(x, y, c.x0, c.y0) < 0.35:
                    col = shade(col, 0.82)                    # the knobbly burr
                c.set(x, y, col)
    return p


def build_antler(pk, part, left):
    """One antler, built for the right side (-x is outward) and mirrored for the left: a knobbly
    burr, the main beam running forward from just behind it, three tines rising from the beam (the
    front one is the beam's upturned tip) and a short brow tine over the burr. Each cube: origin,
    size, and the heights (0 = burr, 9 = top) it spans, for the base-to-tip colour ramp."""
    segs = [
        ((-0.5, -2, -0.5), (1, 2, 1), 0, 2, "burr"),
        ((-1.5, -3, -4), (1, 1, 5), 2, 3, "beam"),
        ((-1.5, -6, 0), (1, 3, 1), 3, 6.5, "tine_back"),
        ((-1.5, -7, -2), (1, 4, 1), 3, 9, "tine_mid"),
        ((-1.5, -5, -4), (1, 2, 1), 3, 5.5, "tine_tip"),
        ((-0.5, -4, -1), (1, 2, 1), 2, 4.5, "brow"),
    ]
    for (ox, oy, oz), size, lo, hi, name in segs:
        if left:
            ox = -(ox + size[0])
        pk.add(part, (ox, oy, oz), size, None if left else faces(antler(lo, hi)),
               mirror=left, share="antler_" + name, inflate=0.15 if name == "burr" else -0.08)


# -- the model -------------------------------------------------------------------------------------------
def make(texture_id, P):
    """Build the deer with the given palette. Geometry is identical for adult and fawn."""
    m = Model("deer", 64, 64, seed=2626, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot (0, 10, 0). Chest x -3..3, y 7..14, z -8..-1, a little withers hump on top; the
    # barrel and rump x -3..3, y 7..13 (the belly tucks up), z -1..7.
    body = m.part("body", (0, 10, 0))
    pk.add(body, (-3, -3, -8), (6, 7, 7),
           faces(body_side(P, 7, 0), top=body_top(P, [1]), front=chest_front(P), back=coat(P)))
    pk.add(body, (-3, -3, -1), (6, 6, 8),
           faces(body_side(P, 7, 1), top=body_top(P, [1]), back=rump_back(P), front=coat(P)))
    pk.add(body, (-2, -4, -7), (4, 1, 4), faces(withers(P)))

    # neck: from the top front of the chest, leaning forward (x rotation 0.6); throat patch on its
    # front face
    neck = body.part("neck", (0, -1, -7), (0.6, 0, 0))
    pk.add(neck, (-1.5, -6.5, -2.5), (3, 7, 4), faces(neck_paint(P)))

    # head: on top of the neck, turned back level. Skull 5 wide, the muzzle 3 wide stepping down
    # and forward.
    head = neck.part("head", (0, -6, -0.5), (-0.6, 0, 0))
    pk.add(head, (-2.5, -2.5, -3.5), (5, 4, 4),
           faces(skull_back(P), front=skull_front(P), right=skull_side(P), left=skull_side(P),
                 top=skull_top(P), bottom=skull_bottom(P)))
    pk.add(head, (-1.5, -1.5, -6.5), (3, 3, 3), faces(snout(P)))
    pk.add(head, (-1.5, -1.5, -7.5), (3, 2, 1), faces(nose(P)))
    # big ears out to the sides, raised and swept back
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        left = sx > 0
        e = head.part(name, (2 * sx, -2.0, 0), (0, -0.45 * sx, 0.75 * -sx))
        pk.add(e, (-4 if not left else 0, -1.5, -0.5), (4, 3, 1), None if left else faces(ear_paint(P)),
               mirror=left, share="ear")

    # antlers (grown stags only; the code hides the part): two racks leaning out and back
    antlers = head.part("antlers", (0, -2.5, -1.5))
    for name, sx in (("right_antler", -1), ("left_antler", 1)):
        a = antlers.part(name, (1.25 * sx, 0, 0), (-0.15, 0.3 * sx, 0.45 * sx))
        build_antler(pk, a, sx > 0)

    # tail: from the top of the rump, pointing back in its own space, hanging down at rest
    tail = body.part("tail", (0, -2.5, 7), (-1.4, 0, 0))
    pk.add(tail, (-2, -0.5, 0), (4, 1, 4), faces(tail_paint(P)))

    # legs on the root. Front: forearm, thin cannon, hoof. Hind: a big ham tucked into the rump, the
    # gaskin slanting back to the hock, then the cannon and hoof. Hooves rest on y 24.
    for name, sx, z in (("right_front_leg", -1, -5.5), ("left_front_leg", 1, -5.5)):
        lg = m.part(name, (1.75 * sx, 13, z))
        left = sx > 0
        pk.add(lg, (-1, -1, -1), (2, 6, 2), None if left else faces(upper_leg(P)), mirror=left,
               share="forearm", inflate=0.2)
        pk.add(lg, (-1, 5, -1), (2, 6, 2), None if left else faces(lower_leg(P)), mirror=left,
               share="cannon", inflate=-0.15)
        pk.add(lg, (-1, 10, -1), (2, 1, 2), None if left else faces(hoof(P)), mirror=left,
               share="hoof")
    for name, sx in (("right_hind_leg", -1), ("left_hind_leg", 1)):
        lg = m.part(name, (1.75 * sx, 12, 5))
        left = sx > 0
        pk.add(lg, (-1.5, -2, -2.5), (3, 7, 4), None if left else faces(upper_leg(P, hind=True)),
               mirror=left, share="ham")
        pk.add(lg, (-1, 4, -0.5), (2, 4, 2), None if left else faces(gaskin(P)), mirror=left,
               share="gaskin", inflate=0.1)
        pk.add(lg, (-1, 7, -1), (2, 5, 2), None if left else faces(lower_leg(P)), mirror=left,
               share="hind_cannon", inflate=-0.15)
        pk.add(lg, (-1, 11, -1), (2, 1, 2), None if left else faces(hoof(P)), mirror=left,
               share="hoof")

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("deer_fawn", FAWN).save(geometry=False)
    spawn_egg("deer", "#9c6b3f", "#f0e8d8", accent="#3e2b1e")


if __name__ == "__main__":
    build()

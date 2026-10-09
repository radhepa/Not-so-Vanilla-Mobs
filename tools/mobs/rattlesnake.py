"""Rattlesnake: a heavy-bodied western diamondback. Sandy-tan keeled scales with a chain of
cream-edged dark-brown diamonds down the back and dark blotches along the flanks, a pale belly of
broad scutes, a dark coontail of bands near the end and a cream, ringed rattle. The head is broad and
triangular, darker than the body, with overhanging brow scales, slit-pupil yellow eyes, a pale stripe
behind each eye, heat pits and a black forked tongue that flicks out.

The body is a chain of five segments (body1 at the front, each next one a child of the previous) so
the code can send yaw waves down it. body1's pivot is at its BACK end (the joint with body2), with
body1 reaching forward to the head: tipping body1 up rears the head while body2 counter-rotates to
stay on the ground. Every segment overlaps the next by a pixel, so bends don't open gaps."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Rattlesnake"
LOOT = []
TAGS = []


# -- texture packing: cubes are collected first, then placed biggest-first at the first spot where
# their face rectangles fit, so small cubes nest in the empty corners of the big box-UV layouts.
# Every cube keeps a 1 px clear margin, so no face edge ever picks up a neighbour's pixels.
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
        used = {}                                   # (x, y) -> "px" or "margin"
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


# -- palette -----------------------------------------------------------------------------------------
TAN = ["#bfa070", "#bb9c6b", "#c3a475", "#b6976a", "#bd9e6e"]
TAN_LT = ["#ccb084", "#d0b589"]
DIA = ["#62452f", "#5c412c", "#674932"]              # the diamonds
DIA_IN = ["#977652", "#92714f"]                      # their lighter centres
EDGE = ["#e0cc9e", "#dbc898", "#e4d1a5"]             # pale outlines
BLOTCH = ["#8f7150", "#8a6c4c"]                      # flank blotches between the diamonds
BELLY = ["#efe4c6", "#ebdfbf", "#f2e8cf"]
SCUTE = "#d8c9a4"                                    # the line between belly scutes
HEAD = ["#5d4734", "#57422f", "#634b37", "#5a4431"]
HEAD_LT = "#7a6048"
HEAD_DK = "#3e2e21"
EYE = "#e7bf36"
EYE_LT = "#fde894"
EYE_DK = "#b98d1f"
PUPIL = "#120b07"
LIP = ["#e4d4ad", "#ddcca3"]
MOUTH = "#d88a8c"
MOUTH_DK = "#b8666c"
TONGUE = "#2c1418"
TONGUE_LT = "#5b2a33"
RATTLE = ["#e6d5ab", "#e1cfa3"]
RATTLE_LT = "#f3e7c8"
RATTLE_DK = "#a99470"
BAND_DK = ["#3c2b20", "#41301f"]

SIDES = ("front", "back", "left", "right")
PERIOD = 5


def scales(col, x, y, c):
    """Keeled scales: a faint staggered highlight lattice over the base colour."""
    if (x + 2 * (y % 2)) % 4 == 0 and c.rng.random() < 0.7:
        return shade(col, 1.07)
    if (x + 2 * (y % 2)) % 4 == 2 and c.rng.random() < 0.35:
        return shade(col, 0.94)
    return col


def diamond_row(k, w):
    """One row of the diamond chain across a top face w wide (k = position in the 4-row period)."""
    if w >= 4:
        rows = [".cc.", "cDDc", "DddD", "DddD", "cDDc"]
    elif w == 3:
        rows = [".c.", "cDc", "DdD", "DdD", "cDc"]
    else:
        rows = ["c" * w, "D" * w, "d" * w, "d" * w, "D" * w]
    r = rows[k % PERIOD]
    pad = (w - len(r)) // 2
    return "." * pad + r + "." * (w - len(r) - pad)


def ink(c, ch):
    if ch == "D":
        return c.pick(DIA)
    if ch == "d":
        return c.pick(DIA_IN)
    if ch == "c":
        return c.pick(EDGE)
    return None


def segment(front, depth, banded=False):
    """Skin for one body segment. front = distance of the cube's front edge from the neck, so the
    diamond chain (or the coontail bands) runs on unbroken from one segment to the next."""
    def along(c, x, y):
        """Distance from the neck of this pixel's row (top/bottom) or column (sides)."""
        if c.face in ("top", "bottom"):
            return front + (depth - 1 - y)
        if c.face in ("left", "right"):
            return front + (c.w - 1 - x if c.face == "right" else x)
        return front if c.face == "front" else front + depth - 1

    def band(d):
        return (d - front) % 3 < 2 if banded else False

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                d = along(c, x, y)
                k = d % PERIOD
                if c.face == "bottom":
                    col = c.pick(BELLY)
                    if y % 2 == 0:
                        col = mix(col, SCUTE, 0.7)     # broad belly scutes, one per two rows
                    if x in (0, c.w - 1):
                        col = shade(col, 0.93)
                    c.set(x, y, col)
                    continue
                if banded:
                    col = c.pick(BAND_DK) if band(d) else c.pick(EDGE)
                    if c.face in SIDES and c.h > 1:
                        col = shade(col, 1.04 - 0.14 * y / (c.h - 1))
                    if c.face == "top":
                        col = shade(col, 1.05)
                    c.set(x, y, col)
                    continue
                if c.face == "top":
                    ch = diamond_row(k, c.w)[x]
                    col = ink(c, ch) or shade(c.pick(TAN), 0.95 if x in (0, c.w - 1) else 1.0)
                    c.set(x, y, scales(shade(col, 1.04), x, y, c) if ch in ".c" else shade(col, 1.04))
                    continue
                # side, front and back faces: the diamond points wrap over the top edge, blotches
                # sit low on the flanks between them, and the pale belly shows along the bottom row
                col = scales(c.pick(TAN), x, y, c)
                if c.face in ("left", "right"):
                    if y == 0:
                        top_ch = "D" if k in (2, 3) else ("c" if k in (1, 4) else ".")
                        col = ink(c, top_ch) or c.pick(TAN_LT)
                    elif y == 1 and c.h > 2:
                        col = c.pick(EDGE) if k in (2, 3) else (c.pick(BLOTCH) if k == 0 else col)
                    if c.h > 2 and y == c.h - 2 and k == 0:
                        col = mix(col, c.pick(BLOTCH), 0.5)
                elif y == 0:
                    col = ink(c, diamond_row(k, c.w)[x]) or col
                if y == c.h - 1:
                    col = mix(col, c.pick(BELLY), 0.7)
                elif c.h > 1:
                    col = shade(col, 1.03 - 0.1 * y / (c.h - 1))
                c.set(x, y, col)
    return p


# -- head --------------------------------------------------------------------------------------------
def mottle(c, x, y, k=1.0):
    col = shade(c.pick(HEAD), k)
    if (x * 3 + y * 5) % 7 == 0 and c.rng.random() < 0.6:
        col = shade(col, 1.15)
    return col


def skull_top(c):
    # 6 wide x 4 deep, row 0 = back: dark mottled crown, pale lines along the temples, a darker
    # band across the front where the eyes are
    for y in range(c.h):
        for x in range(c.w):
            col = mottle(c, x, y, 1.08)
            if y == c.h - 1:
                col = shade(col, 0.8)
            elif x in (0, c.w - 1):
                col = mix(col, c.pick(LIP), 0.35)          # the pale temple stripe seen from above
            c.set(x, y, col)
    c.set(c.w // 2, 0, HEAD_LT)
    c.set(c.w // 2 - 1, 1, HEAD_LT)


def skull_side(c):
    # 4 deep x 2 tall: the slit-pupil eye fills the three front columns, a pale stripe runs back
    # from below it to the angle of the jaw
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mottle(c, x, y, 0.95 - 0.06 * y))
    c.set(fx(c, 0), 0, EYE_LT)                            # glint
    c.set(fx(c, 1), 0, PUPIL)
    c.set(fx(c, 2), 0, EYE)
    c.set(fx(c, 0), 1, EYE)
    c.set(fx(c, 1), 1, PUPIL)
    c.set(fx(c, 2), 1, EYE_DK)
    c.set(fx(c, 3), 1, c.pick(LIP))                       # the postocular stripe
    c.set(fx(c, 3), 0, shade(HEAD[0], 0.8))


def skull_front(c):
    # 6 x 2; the 4-wide muzzle covers the middle, so only the outer columns show: the front of each
    # eye, wrapping round the corner
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mottle(c, x, y, 0.85))
    for x in (0, c.w - 1):
        c.set(x, 0, EYE)
        c.set(x, 1, EYE_DK)


def skull_back(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mottle(c, x, y, 0.82))


def skull_bottom(c):
    # pale lip scales round the edge, the pink roof of the mouth inside (seen when it gapes)
    for y in range(c.h):
        for x in range(c.w):
            inner = 1 < x < c.w - 2 and y > 0
            c.set(x, y, (MOUTH_DK if y == 1 else MOUTH) if inner else c.pick(LIP))


def muzzle_top(c):
    # 4 x 3, row 2 = the tip: large plate scales, the front corners darkened so the snout reads
    # round, a lighter canthus line along each edge leading to the eyes
    for y in range(c.h):
        for x in range(c.w):
            col = mottle(c, x, y, 1.05)
            if x in (0, c.w - 1):
                col = mix(col, c.pick(LIP), 0.25)
            c.set(x, y, col)
    c.set(0, c.h - 1, HEAD_DK)
    c.set(c.w - 1, c.h - 1, HEAD_DK)
    c.set(1, c.h - 1, shade(HEAD[0], 1.15))


def muzzle_front(c):
    # 4 x 2: nostrils high on the corners, the pale upper lip with a notch for the tongue
    for x in range(c.w):
        c.set(x, 0, mottle(c, x, 0, 1.0))
        c.set(x, 1, c.pick(LIP))
    c.set(0, 0, HEAD_DK)
    c.set(c.w - 1, 0, HEAD_DK)
    c.set(1, 0, shade(HEAD[0], 1.12))
    c.set(c.w // 2, 1, shade(LIP[0], 0.8))


def muzzle_side(c):
    # 3 deep x 2: dark above with the heat pit between nostril and eye, pale lip below
    for x in range(c.w):
        c.set(x, 0, mottle(c, x, 0, 0.92))
        c.set(x, 1, c.pick(LIP))
    c.set(fx(c, 1), 0, HEAD_DK)                           # the heat pit
    c.set(fx(c, 0), 1, shade(LIP[0], 0.9))


def muzzle_bottom(c):
    c.noise(LIP)


def jaw(c):
    if c.face == "top":                                   # inside the mouth
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, MOUTH_DK if x in (c.w // 2 - 1, c.w // 2) and y > 0 else MOUTH)
        return
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LIP)
            if c.face in ("left", "right"):
                col = shade(col, 0.94)
            elif c.face == "bottom":
                col = shade(col, 1.0 if x in (c.w // 2 - 1, c.w // 2) else 0.92)
            c.set(x, y, col)


def brow(c):
    # the overhanging scale above each eye: dark, lit along the top
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top":
                col = shade(c.pick(HEAD), 1.2)
            elif c.face == "bottom":
                col = HEAD_DK
            else:
                col = shade(c.pick(HEAD), 0.9)
            c.set(x, y, col)


def tongue(c):
    # a flat plane (top and bottom painted alike), 3 wide x 4 long, row 0 = back: a single dark
    # stem that forks at the tip; everything else is cut out
    rows = [".s.", ".s.", "t.t", "t.t"]
    for y in range(c.h):
        for x in range(c.w):
            ch = rows[y][x]
            if ch == ".":
                c.clear(x, y)
            else:
                c.set(x, y, TONGUE if ch == "s" else TONGUE_LT)


# -- rattle ------------------------------------------------------------------------------------------
def rattle_seg(shade_k):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(RATTLE), shade_k)
                if c.face in ("left", "right", "front", "back"):
                    col = shade(col, 1.08 - 0.2 * y / max(1, c.h - 1))
                    if y == 0:
                        col = mix(col, RATTLE_LT, 0.5)
                elif c.face == "top":
                    col = mix(col, RATTLE_LT, 0.35)
                else:
                    col = shade(col, 0.85)
                if c.face in ("front", "back") and (x in (0, c.w - 1) or y in (0, c.h - 1)):
                    col = mix(col, RATTLE_DK, 0.55)         # the ring's rim
                c.set(x, y, col)
    return p


def build():
    m = Model("rattlesnake", 64, 64, seed=3434)
    pk = Pack(m)

    # body1 hangs off the root at the neck-to-body joint (y 22.5 is the middle of a 3-high body
    # lying on the ground); its cube reaches 4 px forward to the head and 1 px back into body2.
    # Pivots sit on the joints; each segment's cube runs one pixel past its joint into the next.
    py = 22.5

    def seg(part, w, h, length, infl, front, bottom=24.0, banded=False):
        depth = length + 1
        y0 = bottom - py - h - infl
        pk.add(part, (-w / 2, y0, 0 if part.name != "body1" else -length), (w, h, depth),
               faces(segment(front, depth, banded)), inflate=infl)

    # at rest it lies in a loose S
    body1 = m.part("body1", (0, py, -6))
    seg(body1, 3, 3, 4, -0.1, 0)
    body2 = body1.part("body2", (0, 0, 0), (0, 0.3, 0))
    seg(body2, 4, 3, 5, 0.15, 4)
    body3 = body2.part("body3", (0, 0, 5), (0, -0.45, 0))
    seg(body3, 4, 3, 5, 0.05, 9, bottom=23.95)
    body4 = body3.part("body4", (0, 0, 5), (0, 0.45, 0))
    seg(body4, 3, 2, 5, 0.2, 14)
    body5 = body4.part("body5", (0, 0, 5), (0, -0.35, 0))
    seg(body5, 2, 2, 4, 0.05, 19, bottom=23.95, banded=True)

    # the rattle: ringed segments, each a little smaller, ending in the button
    rattle = body5.part("rattle", (0, 0.2, 4), (0, 0.15, 0))
    for i, (infl, k) in enumerate(((0.2, 1.0), (0.1, 0.92), (0.0, 1.0), (-0.15, 0.9))):
        pk.add(rattle, (-1, -1, -0.2 + i * 0.9), (2, 2, 1), faces(rattle_seg(k)), inflate=infl)

    # head: pivot at the front of body1, level with the body's middle. A flat skull 6 wide at the
    # jaw angles, narrowing to a 4-wide blunt muzzle (a broad triangle from above), over a narrower
    # lower jaw; overhanging brow scales above the eyes.
    head = body1.part("head", (0, 0, -4))
    pk.add(head, (-3, -1.5, -3), (6, 2, 4), faces(skull_back, top=skull_top, right=skull_side,
                                                  left=skull_side, front=skull_front,
                                                  bottom=skull_bottom))
    pk.add(head, (-2, -1.5, -6), (4, 2, 3), faces(muzzle_side, top=muzzle_top, front=muzzle_front,
                                                  bottom=muzzle_bottom))
    for sx in (-1, 1):
        pk.add(head, (2.8 * sx - 0.5, -2.0, -3), (1, 1, 3), faces(brow), inflate=-0.15,
               mirror=sx > 0, share="brow")
    jw = head.part("jaw", (0, 0.5, 0.5))
    pk.add(jw, (-2, 0, -6), (4, 1, 6), faces(jaw), inflate=-0.03)
    # the forked tongue waits inside the head; the code slides it out through the lip notch
    tg = head.part("tongue", (0, 0.35, 0))
    pk.add(tg, (-1.5, 0, -4), (3, 0, 4), faces(tongue))

    pk.apply()
    m.save()
    spawn_egg("rattlesnake", "#bfa070", "#62452f", accent="#e2cfa0")


if __name__ == "__main__":
    build()

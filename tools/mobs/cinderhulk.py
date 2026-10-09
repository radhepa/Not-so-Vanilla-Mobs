"""Cinderhulk: a hulking gorilla-built brute of the Basalt Deltas. It knuckle-walks on two huge
blackstone fists at the end of long, thick arms; enormous shoulders and a deep chest lean forward over
short, thick legs, and a small head sits sunk low between the shoulders, pushed forward. Its hide is
dark basalt (vertical column striations, lighter on top) split by molten magma cracks that glow
orange and yellow across the chest, arms, legs and back. A furnace-mouth vent burns in its chest
under a slab of pectoral rock, framed by basalt jambs and a sill. Two small ember eyes glow under a
heavy brow and a glowing grin smoulders in the jaw. The fists are blackstone with gilded-blackstone
gold flecks, the toes blackstone too. A jagged crown of basalt column spikes rises from the shoulders
and runs down the spine.

The trunk leans forward inside the `trunk` decoration part, so every contract part rests at rotation
0: arms hang straight down, xRot -2.9 holds them straight overhead."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Cinderhulk"
LOOT = [item("magma_cream", 1, 3), item("basalt", 2, 4), item("gold_nugget", 3, 8), item("netherite_scrap", chance=0.03, looting=False, player_only=True)]
TAGS = ["freeze_hurts_extra_types"]


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


def rx(p, a):
    """Rotate a point about the x axis like ModelPart.xRot."""
    x, y, z = p
    ca, sa = math.cos(a), math.sin(a)
    return (x, y * ca - z * sa, y * sa + z * ca)


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
BAS = ["#2b2b2f", "#36363b", "#424248"]          # basalt column tones: dark, mid, light
BAS_TOP = ["#46464d", "#4f4f56", "#4a4a51", "#57575f"]
BAS_DK = ["#222226", "#26262a", "#1f1f23"]
SEAM = "#1c1c20"
CRUST = ["#3d1a10", "#46200f", "#33170f"]        # heat-darkened rock round a crack (no glow)
EMBER = "#5a1a08"                                # dim base under every glowing pixel
ORANGE, AMBER, YELLOW = "#ff6a1a", "#ffa31a", "#ffd23f"
SOOT = ["#151214", "#191517"]
BLK = ["#1c1a1f", "#2a2530", "#231f27"]          # blackstone
BLK_HI = ["#38323f", "#332d39"]
BLK_DK = "#141216"
GOLD, GOLD_DK, GOLD_HI = "#e8b531", "#a87a22", "#ffe27a"


def hot(c, x, y, col):
    """A glowing pixel: the emissive colour on a dim ember base (the glow is added on top)."""
    if c.inside(x, y):
        c.glow(x, y, col)
        c.set(x, y, EMBER)


# -- basalt ------------------------------------------------------------------------------------------
def basalt(t0=1.06, t1=0.9, top=1.0, seams=0.3):
    """Basalt hide: vertical columns of three close greys with dark seams and joints on the sides,
    getting darker downward (t0 at the top row, t1 at the bottom); pale cut ends on top, dark below."""
    def p(c):
        if c.face == "top":
            for y in range(c.h):
                for x in range(c.w):
                    col = c.pick(BAS_TOP)
                    if c.rng.random() < 0.1:
                        col = BAS[2]
                    c.set(x, y, shade(col, top))
            return
        if c.face == "bottom":
            c.noise(BAS_DK)
            return
        bands, prev, x = [], -1, 0
        while x < c.w:
            bw = c.rng.choice((2, 2, 3, 3, 4))
            t = c.rng.choice([i for i in range(3) if i != prev])
            prev = t
            for i in range(bw):
                bands.append((t, i == 0))
            x += bw
        for x in range(c.w):
            t, first = bands[x]
            seam = first and x > 0 and c.rng.random() < seams
            for y in range(c.h):
                f = t0 + (t1 - t0) * (y / max(1, c.h - 1))
                f = round(f * 16) / 16
                if seam and c.rng.random() < 0.8:
                    c.set(x, y, shade(SEAM, f))
                    continue
                tt = t
                r = c.rng.random()
                if r < 0.12:
                    tt = max(0, t - 1)
                elif r < 0.2:
                    tt = min(2, t + 1)
                c.set(x, y, shade(BAS[tt], f))
        for _ in range(max(1, c.w * c.h // 45)):        # joints across the columns
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, SEAM)
            if c.inside(x + 1, y) and c.rng.random() < 0.5:
                c.set(x + 1, y, SEAM)
    return p


# -- magma cracks ------------------------------------------------------------------------------------
def walk(rng, x, y, ang, n, wander=0.45):
    """A jagged 4-connected path of about n steps from (x, y), heading `ang` (radians, y down)."""
    pts = [(x, y)]
    fxp, fyp, d = x + 0.5, y + 0.5, 0.0
    for _ in range(n):
        d = max(-0.9, min(0.9, d + rng.uniform(-wander, wander)))
        fxp += math.cos(ang + d)
        fyp += math.sin(ang + d)
        nx, ny = int(math.floor(fxp)), int(math.floor(fyp))
        cx, cy = pts[-1]
        if nx != cx and ny != cy:
            pts.append((nx, cy) if rng.random() < 0.5 else (cx, ny))
        if (nx, ny) != pts[-1]:
            pts.append((nx, ny))
    return pts


def draw_veins(c, veins):
    """veins: list of (x, y, angle, steps, heat). Each vein is hottest in its middle and cools to dark
    crust at its ends; short cooler branches fork off it; crust darkens the rock round every crack."""
    heat = {}

    def lay(pts, hmax):
        n = len(pts)
        for i, q in enumerate(pts):
            t = i / max(1, n - 1)
            h = hmax * (1 - abs(2 * t - 1)) ** 0.6
            heat[q] = max(heat.get(q, 0.0), h)

    for (x, y, ang, steps, hmax) in veins:
        pts = walk(c.rng, x, y, ang, steps)
        lay(pts, hmax)
        for i in range(2, len(pts) - 2):
            if c.rng.random() < 0.1:
                bx, by = pts[i]
                side = c.rng.choice((-1, 1))
                lay(walk(c.rng, bx, by, ang + side * c.rng.uniform(0.9, 1.4), c.rng.randint(2, 4), 0.3),
                    hmax * 0.5 * (1 - abs(2 * i / len(pts) - 1)) + 0.15)
        for i in range(1, len(pts) - 1):              # thicken the hot middle here and there
            q = pts[i]
            if heat.get(q, 0) > 0.6 and c.rng.random() < 0.18:
                ox, oy = c.rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                r = (q[0] + ox, q[1] + oy)
                heat[r] = max(heat.get(r, 0.0), 0.3)
    for (x, y) in list(heat):
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + ox, y + oy)
            if q not in heat and c.inside(*q) and c.rng.random() < 0.4:
                c.set(q[0], q[1], c.pick(CRUST))
    for (x, y), h in heat.items():
        if not c.inside(x, y):
            continue
        r = c.rng.random()
        if h > 0.72:
            col = YELLOW if r < 0.55 else AMBER
        elif h > 0.4:
            col = AMBER if r < 0.55 else ORANGE
        elif h > 0.12:
            col = ORANGE
        else:
            c.set(x, y, c.pick(CRUST))
            continue
        hot(c, x, y, col)


def cracked(base, spec):
    """Basalt (or any base painter) plus magma veins per face: spec = {face: [(x, y, ang, n, heat)]},
    coordinates as fractions of the face (0..1) so one spec fits any size."""
    def p(c):
        base(c)
        vs = spec.get(c.face)
        if vs:
            draw_veins(c, [(int(fx_ * (c.w - 1)), int(fy_ * (c.h - 1)), a, n, h) for (fx_, fy_, a, n, h) in vs])
    return p


DOWN, UP, RIGHT, LEFT = math.pi / 2, -math.pi / 2, 0.0, math.pi


# -- blackstone --------------------------------------------------------------------------------------
def blackstone(c, t0=1.08, t1=0.9):
    for y in range(c.h):
        f = 1.15 if c.face == "top" else (0.85 if c.face == "bottom" else t0 + (t1 - t0) * y / max(1, c.h - 1))
        for x in range(c.w):
            col = c.pick(BLK)
            r = c.rng.random()
            if r < 0.08:
                col = c.pick(BLK_HI)
            elif r < 0.13:
                col = BLK_DK
            c.set(x, y, shade(col, round(f * 16) / 16))


def flecks(c, n, area=None):
    """Gilded-blackstone gold: small clusters, bright centre, darker rim."""
    x0, y0, w, h = area or (0, 0, c.w, c.h)
    for _ in range(n):
        x, y = x0 + c.rng.randrange(w), y0 + c.rng.randrange(h)
        c.set(x, y, GOLD)
        c.set(x + c.rng.choice((-1, 1)), y, GOLD_DK)
        if c.rng.random() < 0.5:
            c.set(x, y + 1, GOLD_DK)
        if c.rng.random() < 0.4:
            c.set(x, y, GOLD_HI)


# -- painters per piece ------------------------------------------------------------------------------
def ribs_front(c):
    basalt(1.0, 0.9)(c)
    # the furnace mouth, recessed between the jambs, under the pec slab and over the sill
    # (cols 3-12, rows 2-6): soot under the lintel, flame tongues, a bed of coals
    rows = ["kkrkkkkrkk",
            "krokrkrokr",
            "roaorroaor",
            "oayaooayao",
            "yacyyyycay"]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            x, y = 3 + i, 2 + j
            if ch == "k":
                c.set(x, y, c.pick(SOOT))
            elif ch == "c":
                c.set(x, y, "#2a1712")                # a lump of coal in the coal bed
            elif ch == "r":
                c.glow(x, y, "#7a2208")
                c.set(x, y, "#2a0e06")
            else:
                hot(c, x, y, {"o": ORANGE, "a": AMBER, "y": YELLOW}[ch])


def pecs(c):
    if c.face == "bottom":                            # the lintel over the furnace: lit from below
        for y in range(c.h):
            for x in range(c.w):
                mid = 3 <= x <= 13
                col = mix(c.pick(BAS), "#7a3010", 0.5 if mid else 0.15)
                c.set(x, y, col)
        return
    basalt(1.14, 0.98)(c)
    if c.face == "front":
        for x in range(c.w):                          # lit top edge of each pec, a dark cleft between
            c.set(x, 0, shade(c.pick(BAS_TOP), 1.05))
        for y in range(c.h):
            c.set(c.w // 2, y, "#1d1d21")
        for x in range(c.w):                          # the heavy lower edge of the pecs
            c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.8))
        draw_veins(c, [(c.w // 2, 1, DOWN, c.h - 2, 1.0),
                       (2, 2, RIGHT, 5, 0.75), (c.w - 3, 4, LEFT, 5, 0.75)])


def jamb(c):
    basalt(1.0, 0.86)(c)
    if c.face == "left":                              # inner face, lit by the furnace
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, mix(c.get(x, y), "#8a3a12", 0.35 + 0.15 * y / c.h))


def sill(c):
    basalt(1.0, 0.9)(c)
    if c.face == "top":                               # embers spilled on the sill
        for x in range(3, 13):
            if x in (4, 7, 8, 11):
                hot(c, x, c.h - 1, AMBER if x in (7, 8) else ORANGE)
            else:
                c.set(x, c.h - 1, mix(c.get(x, c.h - 1), "#8a3a12", 0.4))


def column(t0=1.1, t1=0.86, cap=True):
    """A basalt column spike: striped sides, a pale cut end on top."""
    def p(c):
        if c.face == "top":
            c.noise(["#5c5c64", "#55555c", "#62626a"])
            return
        if c.face == "bottom":
            c.noise(BAS_DK)
            return
        for x in range(c.w):
            t = (x + (1 if c.face in ("left", "back") else 0)) % 3
            for y in range(c.h):
                f = t0 + (t1 - t0) * y / max(1, c.h - 1)
                col = BAS[min(2, t + (1 if c.rng.random() < 0.15 else 0))]
                if x == 0 and c.w > 2 and c.rng.random() < 0.5:
                    col = SEAM
                c.set(x, y, shade(col, round(f * 16) / 16))
            if cap:
                c.set(x, 0, shade(c.pick(BAS_TOP), 1.08))
    return p


def skull(c):
    basalt(1.1, 0.92)(c)
    if c.face == "front":
        # rows 0 (behind the brow) and 3-4 show; the brow covers 1-2, the jaw 5-7
        for x in range(c.w):
            c.set(x, 3, "#141416")                    # deep shadow under the brow
            c.set(x, 4, shade(c.pick(BAS), 0.85))
        for (a, b) in ((1, 2), (7, 6)):               # ember eyes: outer amber, inner yellow
            hot(c, a, 3, AMBER)
            hot(c, b, 3, YELLOW)
        c.set(4, 4, shade(BAS[2], 1.05))              # flat nose ridge and nostrils
        c.set(3, 4, "#121214"); c.set(5, 4, "#121214")
        # rows 5-7 hide behind the jaw; when it drops open they show the burning maw
        for x in range(c.w):
            c.set(x, 5, "#1a1a1d" if x % 2 else c.pick(BAS_TOP))   # upper teeth
            hot(c, x, 6, AMBER if 2 <= x <= 6 else ORANGE)
            hot(c, x, 7, YELLOW if 3 <= x <= 5 else AMBER)
    elif c.face == "top":
        draw_veins(c, [(2, c.h - 1, UP, 4, 0.6)])


def brow(c):
    basalt(1.15, 0.95)(c)
    if c.face == "bottom":                            # in shadow, warmed over the eyes
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(["#18181b", "#1d1d20"])
                if y == c.h - 1 and x in (2, 3, 6, 7):
                    col = "#4a1c0c"
                c.set(x, y, col)
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(BAS_TOP), 1.12))
            c.set(x, 1, shade(c.pick(BAS), 0.9))
        c.set(4, 1, "#1d1d21"); c.set(5, 1, "#1d1d21")  # a deep scowl between the brows


def jaw(c):
    basalt(1.0, 0.85)(c)
    if c.face == "front":
        grin = ["........",
                ".odaado.",
                "..aYYa..",
                "........"]
        for y, row in enumerate(grin):
            for x, ch in enumerate(row):
                if ch == "d":
                    c.set(x, y, "#1a1a1d")
                elif ch in "oaY":
                    hot(c, x, y, {"o": ORANGE, "a": AMBER, "Y": YELLOW}[ch])
        for x in range(c.w):
            c.set(x, 0, shade(c.get(x, 0), 0.8))
    elif c.face in ("left", "right"):
        hot(c, fx(c, 0), 1, ORANGE)
    elif c.face == "top":                             # inside the jaw: lower teeth, then embers
        for y in range(c.h):
            for x in range(c.w):
                if y == c.h - 1:
                    c.set(x, y, c.pick(BAS_TOP) if x % 2 == 0 else "#1a1a1d")
                else:
                    hot(c, x, y, ORANGE if (x + y) % 3 else AMBER)


def fist(c):
    """Blackstone fist, knuckles forward: back of the hand, a knuckle ridge, four curled fingers in
    front; worn finger backs underneath (it walks on them); a curled thumb on the inner face."""
    blackstone(c)
    fingers = [0, 1, 3, 4, 6, 7, 9, 10]
    if c.face == "front":
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(BLK_HI), 1.1))
            gap = x not in fingers
            c.set(x, 3, BLK_DK if gap else shade(c.pick(BLK_HI), 1.15))
            for y in range(4, c.h):
                if gap:
                    c.set(x, y, BLK_DK)
                elif y == c.h - 1:
                    c.set(x, y, shade(c.pick(BLK), 0.8))
        flecks(c, 3, (0, 0, c.w, 3))
        flecks(c, 1, (0, 4, c.w, 3))
    elif c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                if y >= c.h // 2:                     # finger backs (row 0 is the back edge)
                    col = BLK_DK if x not in fingers else shade(c.pick(BLK_HI), 0.95)
                else:
                    col = shade(c.pick(BLK), 0.8)
                c.set(x, y, col)
    elif c.face == "left":                            # inner face: the thumb curled over the fingers
        for y in range(3, 7):
            c.set(1, y, BLK_DK)
        for x in range(1, 6):
            c.set(x, 6, BLK_DK)
        for y in range(3, 6):
            for x in range(0, 1):
                c.set(x, y, shade(c.pick(BLK_HI), 1.05))
        flecks(c, 2)
    else:
        flecks(c, 3)




def finger(c):
    """A curled blackstone finger: a pale knuckle on top, the nail-dark tip on the ground."""
    blackstone(c, 1.05, 0.85)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(BLK_HI), 1.2))
            c.set(x, c.h - 1, BLK_DK)
    elif c.face == "top":
        c.noise([shade(BLK_HI[0], 1.25), shade(BLK_HI[1], 1.2)])


def thumb(c):
    blackstone(c, 1.05, 0.88)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(BLK_HI), 1.15))
    if c.face == "left":
        c.set(1, 1, GOLD)
        c.set(2, 1, GOLD_DK)


def foot(c):
    """Flat basalt foot: three blunt toes split by dark gaps, black toenails at the front."""
    basalt(0.92, 0.82, top=0.98)(c)
    toes = [0, 1, 2, 4, 5, 7, 8]
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                if x not in toes:
                    c.set(x, y, "#18181b")
                elif y == c.h - 1:
                    c.set(x, y, c.pick(BLK))
                elif y == 0:
                    c.set(x, y, shade(c.pick(BAS_TOP), 0.95))
    elif c.face == "top":
        for x in range(c.w):
            for y in range(c.h - 3, c.h):
                if x not in toes:
                    c.set(x, y, "#1d1d21")
            if x in toes:
                c.set(x, c.h - 1, c.pick(BLK_HI))
        draw_veins(c, [(4, 1, DOWN, 5, 0.6)])


# -- the model ---------------------------------------------------------------------------------------
LEAN = 0.4                        # the trunk's forward lean (inside the `trunk` decoration part)
BODY = (0, 10, 1)                 # waist pivot: 14 px above the ground
SHOULDER = (12.5, -25, -1)        # in trunk space; the arm pivots sit where the lean puts this
NECK = (0, -24, -9)


def spike(parent, pk, name, pivot, rot, tiers, key, mirror=False):
    """A jagged basalt column: stacked tiers (width, height), each narrower than the one below,
    rooted 1 px into its parent. Spikes of one shape share a texture."""
    s = parent.part(name, pivot, rot)
    y = 1
    for i, (w, h) in enumerate(tiers):
        first = i == 0
        pk.add(s, (-w / 2, y - h - (1 if first else 0), -w / 2), (w, h + (1 if first else 0), w),
               None if mirror else faces(column(1.0 + 0.08 * i, 0.86 + 0.08 * i)),
               mirror=mirror, share=f"{key}_{i}")
        y -= h + (1 if first else 0)
    return s


CROWN = [(5, 4), (3, 3), (1, 3)]      # the big central spike
TALL = [(4, 4), (2, 4)]
MID = [(3, 3), (1, 3)]
SMALL = [(3, 2), (1, 2)]


def make():
    m = Model("cinderhulk", 128, 128, seed=4242)
    pk = Pack(m)

    body = m.part("body", BODY)
    trunk = body.part("trunk", (0, 0, 0), (LEAN, 0, 0))

    # trunk, waist up: pelvis, belly, ribcage, a broad shoulder girdle, a hump over the neck.
    # It tapers from the shoulders down so the arms hang clear of it.
    pk.add(trunk, (-6, -5, -5), (12, 7, 10), faces(cracked(basalt(0.86, 0.78), {
        "back": [(0.3, 0.0, DOWN, 6, 0.8)], "front": [(0.75, 0.0, DOWN, 5, 0.6)]})))
    pk.add(trunk, (-7, -13, -6), (14, 9, 12), faces(cracked(basalt(0.94, 0.86), {
        "front": [(0.3, 0.0, DOWN, 8, 0.8)],
        "back": [(0.5, 0.0, DOWN, 9, 1.0)],
        "right": [(0.6, 0.0, DOWN, 8, 0.8)], "left": [(0.4, 0.0, DOWN, 8, 0.8)]})))
    pk.add(trunk, (-8, -22, -7.5), (16, 10, 14), faces(cracked(basalt(1.0, 0.9), {
        "back": [(0.5, 0.0, DOWN, 11, 1.0), (0.2, 0.3, DOWN, 6, 0.7)],
        "right": [(0.35, 0.0, DOWN, 10, 1.0)], "left": [(0.65, 0.0, DOWN, 10, 1.0)]}), front=ribs_front))
    pk.add(trunk, (-10.5, -29, -8), (21, 8, 15), faces(cracked(basalt(1.1, 1.0), {
        "back": [(0.5, 0.0, DOWN, 9, 1.0), (0.15, 0.1, DOWN, 7, 0.8), (0.85, 0.2, DOWN, 7, 0.8)],
        "right": [(0.3, 0.0, DOWN, 8, 0.9), (0.8, 0.1, DOWN, 7, 0.7)],
        "left": [(0.7, 0.0, DOWN, 8, 0.9), (0.2, 0.1, DOWN, 7, 0.7)],
        "top": [(0.15, 0.3, RIGHT, 5, 0.6), (0.85, 0.6, LEFT, 5, 0.6)],
        "bottom": [(0.2, 0.5, RIGHT, 5, 0.5)]})))
    pk.add(trunk, (-6.5, -31, -4), (13, 3, 9), faces(cracked(basalt(1.14, 1.06, top=1.06), {
        "back": [(0.3, 0.0, DOWN, 4, 0.8)], "top": [(0.5, 1.0, UP, 7, 0.8)]})))
    # pectoral slab; under it the furnace mouth, framed by two jambs and a sill
    pk.add(trunk, (-8.5, -28, -10), (17, 8, 3), faces(pecs))
    for sx in (-1, 1):
        pk.add(trunk, (-7 if sx < 0 else 5, -20, -9.5), (2, 5, 2), None if sx > 0 else faces(jamb),
               mirror=sx > 0, share="jamb")
    pk.add(trunk, (-7, -15, -9.5), (14, 1, 2), faces(sill))

    # basalt column spikes: a jagged crown over the shoulders and a ridge down the spine
    spike(trunk, pk, "spine_spike_1", (0, -30.5, 0), (-0.45, 0, 0), CROWN, "crown")
    spike(trunk, pk, "spine_spike_2", (0, -30, 4.5), (-0.95, 0, 0), TALL, "tall")
    spike(trunk, pk, "spine_spike_3", (0, -24, 7), (-1.2, 0, 0), TALL, "tall")
    spike(trunk, pk, "spine_spike_4", (0, -17, 6.5), (-1.4, 0, 0), MID, "mid")
    spike(trunk, pk, "spine_spike_5", (0, -9, 6), (-1.5, 0, 0), SMALL, "small")
    for side, sx in (("right", -1), ("left", 1)):
        spike(trunk, pk, side + "_shoulder_spike", (5.5 * sx, -30, 0.5), (-0.5, 0.15 * sx, 0.45 * sx), TALL,
              "tall", mirror=sx > 0)
        spike(trunk, pk, side + "_shoulder_spike_2", (9 * sx, -28.5, 2), (-0.6, 0, 0.8 * sx), MID,
              "mid", mirror=sx > 0)

    # head: small, sunk low between the shoulders and pushed forward
    head = body.part("head", rx(NECK, LEAN))
    pk.add(head, (-4.5, -7, -7), (9, 8, 8), faces(skull))
    pk.add(head, (-5, -6, -8.5), (10, 2, 3), faces(brow))
    jw = head.part("jaw", (0, -2, -5))
    pk.add(jw, (-4, 0, -4), (8, 4, 4), faces(jaw))

    # arms: hanging straight down at rest, blackstone fists just off the ground
    sh = rx(SHOULDER, LEAN)
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        arm = body.part(side + "_arm", (sh[0] * sx, sh[1], sh[2]))
        pk.add(arm, (-6, -5, -6), (12, 9, 12), None if left else faces(cracked(basalt(1.12, 0.98, top=1.08), {
            "right": [(0.4, 0.0, DOWN, 8, 0.9)], "front": [(0.7, 0.1, DOWN, 6, 0.6)],
            "top": [(0.2, 0.5, RIGHT, 4, 0.5)]})),
            mirror=left, share="cap")
        pk.add(arm, (-4, 3, -4), (8, 11, 8), None if left else faces(cracked(basalt(1.0, 0.92), {
            "right": [(0.5, 0.0, DOWN, 10, 0.9)], "front": [(0.5, 0.1, DOWN, 8, 0.8)]})),
            mirror=left, share="upper")
        pk.add(arm, (-4.5, 13, -4.5), (9, 13, 9), None if left else faces(cracked(basalt(0.98, 0.86), {
            "right": [(0.3, 0.0, DOWN, 12, 1.0), (0.8, 0.4, DOWN, 7, 0.7)],
            "front": [(0.6, 0.0, DOWN, 11, 0.9)], "back": [(0.4, 0.2, DOWN, 9, 0.8)],
            "left": [(0.5, 0.3, DOWN, 7, 0.6)]})), mirror=left, share="fore")
        fist_y = 21.3 - sh[1] - BODY[1] - 8
        pk.add(arm, (-5.5, fist_y, -6), (11, 8, 11), None if left else faces(fist), mirror=left, share="fist")
        # four curled fingers knuckling the ground in front, a thumb folded on the inner side
        for i in range(4):
            pk.add(arm, (-5.25 + i * 2.75, fist_y + 4, -8), (2, 4, 2), None if (left or i) else faces(finger),
                   mirror=left, share="finger")
        pk.add(arm, ((5 if sx < 0 else -7), fist_y + 3.5, -5), (2, 3, 4), None if left else faces(thumb),
               mirror=left, share="thumb")
        spike(arm, pk, side + "_arm_spike", (4 * sx, -5, 0.5), (-0.2, 0, 0.9 * sx), SMALL, "small",
              mirror=left)

    # legs: short and thick, flat basalt feet
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        leg = m.part(side + "_leg", (4.5 * sx, 10, 2))
        pk.add(leg, (-4, -2, -4.5), (8, 8, 9), None if left else faces(cracked(basalt(0.92, 0.84), {
            "front": [(0.5, 0.2, DOWN, 7, 0.9)], "right": [(0.6, 0.0, DOWN, 7, 0.8)]})),
            mirror=left, share="thigh")
        pk.add(leg, (-3.5, 5, -3.5), (7, 7, 7), None if left else faces(cracked(basalt(0.86, 0.8), {
            "front": [(0.4, 0.0, DOWN, 5, 0.6)]})), mirror=left, share="shin")
        pk.add(leg, (-4.5, 11, -6.5), (9, 3, 11), None if left else faces(foot), mirror=left, share="foot")

    pk.apply()
    return m


def build():
    m = make()
    m.save()
    spawn_egg("cinderhulk", "#2b2b2f", "#ff6a1a", accent="#ffd23f")


if __name__ == "__main__":
    build()

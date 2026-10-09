"""Griffin: a rideable flying mount. The front half is an eagle: a white-feathered head with a heavy
grey brow over fierce amber eyes, a hooked golden beak with a yellow cere, a white neck ruff over a
golden-brown feathered breast, and scaly yellow forelegs with feathered "trousers" and black talons.
The back half is a tawny lion: short golden fur with a darker spine, a cream belly, muscular
haunches, padded paws and a long tail ending in a dark tuft. Two great brown wings: rows of
pale-fringed coverts, then dark flight feathers barred with pale bands, the primaries splayed into
fingers at the tip.
The wings are authored spread (span along x, chord back along z): the inner wing + `*_wing_tip`.
Their rest rotation folds them flat along the flanks with the wing tips crossing up over the rump;
the code spreads and beats them in flight. The back is flat at the rider's seat height (passenger
attachment 1.45 blocks = model y 0.8); `saddle` (child of body: cloth, seat, pommel, cantle,
stirrups) shows only when saddled.
`griffin_chick` shares the geometry: fluffy white down in front, buff behind, stubby downy wings
(the flight feathers are cut away), pale legs and beak (the game draws it at half scale)."""
import math
import os
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Griffin"
LOOT = [item("feather", 1, 3)]
TAGS = ["can_equip_saddle", "fall_damage_immune"]

# Debug only: GRIFFIN_POSE=spread previews the wings open (=up / =down mid-beat), =walk a stride.
POSE = os.environ.get("GRIFFIN_POSE", "")


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


def _h(x, y, salt):
    """A stable random number per pixel, so both faces of a plane match exactly."""
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


def _pick(pal, x, y, salt):
    return pal[int(_h(x, y, salt) * len(pal)) % len(pal)]


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
WHITE = ["#f2f0ea", "#e9e6de", "#f6f4ef", "#ece9e2"]
WHITE_SH = ["#d2cdc2", "#c8c2b6", "#dbd6cc"]
BROW = "#8d877d"
BROW_DK = "#6b665e"
FEATHER = ["#6a4a2e", "#735034", "#5f4229", "#6e4d31"]        # golden-brown eagle plumage
FEATHER_DK = ["#563c26", "#513823", "#5a3f28"]
FRINGE = ["#b08a5c", "#bb9566", "#a78253"]
FRINGE_LT = ["#cdb083", "#d4b98d"]
FLIGHT = ["#3a281b", "#33231a", "#3f2c1e", "#36261b"]          # flight feathers
BAR = ["#8c714f", "#957955", "#86694a"]                        # their pale bars
FUR = ["#c99a58", "#d1a35f", "#c19152", "#cc9e5b"]             # tawny lion
FUR_LT = ["#dcb579", "#e2bd82"]
FUR_DK = ["#a87a3e", "#9f733a", "#b0823f"]
BELLY = ["#e6cc98", "#ead2a1", "#dfc48f"]
TUFT = ["#3f2a1b", "#4a3221", "#36241a"]
BEAK = ["#e8b62e", "#efc23f", "#e2ad28"]
BEAK_DK = "#b98b1c"
BEAK_TIP = ["#4f4336", "#5a4c3c"]
CERE = "#f1cf55"
IRIS = "#e8a12c"
IRIS_DK = "#c27a17"
PUPIL = "#110b07"
SHINE = "#fffbf0"
SCALE = ["#e9c23c", "#e1b733", "#efca48"]
SCALE_DK = "#d3a92e"
TALON = ["#171315", "#211b1d"]
PAD = ["#5a4a44", "#4f403b"]
CLOTH = ["#2c4174", "#33497f", "#283b69"]
GOLD = ["#d9b24a", "#e3bf5a"]
LEATHER = ["#6e4428", "#784a2c", "#653e24"]
LEATHER_DK = ["#4f301b", "#55341e"]
LEATHER_HI = "#93603a"
STITCH = "#caa46e"
IRON = ["#9a9a9c", "#a9a9ab"]
IRON_HI = "#dadadc"


# -- body ----------------------------------------------------------------------------------------------
def scallop_rows(c, x0, x1, base, edge, dark, step=2):
    """Rows of overlapping feathers on a side face: every other row a broken line of pale fringes
    (the feather tips), staggered like roof tiles."""
    for y in range(c.h):
        k = y % step
        off = (y // step) % 3
        for x in range(x0, x1):
            if k == step - 1:
                col = c.pick(edge) if (x + off) % 3 != 2 else c.pick(dark)
            else:
                col = c.pick(base) if (x + off) % 3 != 1 else shade(c.pick(base), 0.9)
            c.set(x, y, shade(col, 1.04 - 0.14 * y / max(1, c.h - 1)))


def fur(c, x0, x1, top_dark=True):
    """Short lion fur: tawny noise, a darker line along the top, small vertical hair strokes, the
    cream belly in the bottom row."""
    for y in range(c.h):
        for x in range(x0, x1):
            col = shade(c.pick(FUR), 1.05 - 0.15 * y / max(1, c.h - 1))
            c.set(x, y, col)
    for _ in range(max(1, (x1 - x0) * c.h // 5)):
        x, y = c.rng.randrange(x0, x1), c.rng.randrange(c.h - 1)
        c.set(x, y, c.pick(FUR_DK) if c.rng.random() < 0.5 else c.pick(FUR_LT))
        if c.inside(x, y + 1) and y + 1 < c.h - 1:
            c.set(x, y + 1, shade(c.get(x, y + 1), 0.95))
    if top_dark:
        for x in range(x0, x1):
            c.set(x, 0, mix(c.get(x, 0), c.pick(FUR_DK), 0.5))
    for x in range(x0, x1):
        c.set(x, c.h - 1, mix(c.pick(BELLY), c.pick(FUR), 0.35))


def torso_side(c):
    """19 long x 9 tall. Feathers over the front 8 columns, then a ragged edge where the feathers
    overlap the lion fur, then fur back to the rump."""
    edge = 8
    fur(c, 0, c.w)
    for y in range(c.h):
        reach = edge + (1 if y % 3 == 1 else 0) - (1 if y % 3 == 2 else 0)
        for i in range(reach):
            x = fx(c, i)
            col = c.pick(FEATHER) if (i + y) % 3 else c.pick(FEATHER_DK)
            if y % 2 == 1 and (i + y // 2) % 3 != 2:
                col = c.pick(FRINGE)
            c.set(x, y, shade(col, 1.04 - 0.14 * y / (c.h - 1)))
        c.set(fx(c, reach), y, shade(c.pick(FRINGE), 0.9))        # the last feather tips over the fur


def torso_top(c):
    """10 wide x 19 long (row 0 = back): feathers over the shoulders, fur from the saddle back, a
    darker spine line."""
    for y in range(c.h):
        front = c.h - 1 - y
        for x in range(c.w):
            if front < 7 or (front == 7 and x % 2):
                col = c.pick(FEATHER)
                if (front + x) % 3 == 0:
                    col = c.pick(FRINGE)
                elif (front + x) % 3 == 1:
                    col = shade(col, 1.08)
            else:
                col = shade(c.pick(FUR), 1.07)
                if x in (c.w // 2 - 1, c.w // 2):
                    col = mix(col, c.pick(FUR_DK), 0.45)            # the spine
                elif c.rng.random() < 0.15:
                    col = c.pick(FUR_LT)
            c.set(x, y, col)


def torso_front(c):
    scallop_rows(c, 0, c.w, FEATHER, FRINGE, FEATHER_DK)


def torso_back(c):
    fur(c, 0, c.w)


def torso_bottom(c):
    """Row 0 = back: a cream lion belly, then pale feathers under the chest."""
    for y in range(c.h):
        for x in range(c.w):
            if y < c.h - 8:
                col = c.pick(BELLY)
            else:
                col = mix(c.pick(FRINGE), c.pick(FEATHER), 0.3) if (x + y) % 2 else c.pick(FRINGE_LT)
            if x in (0, c.w - 1):
                col = shade(col, 0.88)
            c.set(x, y, col)


def chest(c):
    """The deep eagle breast: golden-brown feathers in rows with pale tips."""
    if c.face in ("front", "left", "right"):
        scallop_rows(c, 0, c.w, FEATHER, FRINGE, FEATHER_DK)
        if c.face == "front":
            for y in range(c.h):
                c.set(0, y, shade(c.get(0, y), 0.9))
                c.set(c.w - 1, y, shade(c.get(c.w - 1, y), 0.9))
    elif c.face == "bottom":
        c.noise(FRINGE)
    else:
        c.noise(FEATHER)


def belly(c):
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(BELLY) if y < c.h - 3 else c.pick(FRINGE))
    elif c.face in ("left", "right"):
        for x in range(c.w):
            i = c.w - 1 - x if c.face == "right" else x
            c.set(x, 0, c.pick(FRINGE) if i < 3 else c.pick(BELLY))
    else:
        c.noise(BELLY if c.face == "back" else FRINGE)


def shoulders(c):
    """A rise of feathers over the shoulders, in front of the saddle."""
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(FRINGE) if (x + y) % 3 == 0 else shade(c.pick(FEATHER), 1.1))
    else:
        c.noise(FEATHER)


def rump(c):
    if c.face == "back":
        fur(c, 0, c.w)
        for y in range(c.h):                         # rounded haunches either side of the tail
            c.set(c.w // 2, y, shade(c.get(c.w // 2, y), 0.9))
    else:
        c.noise(FUR)


# -- neck and head -----------------------------------------------------------------------------------
def white_feathers(c, shadow=True):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(WHITE)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.0 - 0.08 * y / (c.h - 1))
            elif c.face == "bottom":
                col = c.pick(WHITE_SH)
            c.set(x, y, col)
    if shadow:
        for _ in range(c.w * c.h // 6):              # soft feather lines
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, c.pick(WHITE_SH))


def neck_paint(c):
    white_feathers(c)
    if c.face in SIDES:                              # feathers lie down the neck in short rows
        for y in range(1, c.h, 2):
            for x in range(c.w):
                if (x + y) % 3 == 0:
                    c.set(x, y, shade(c.pick(WHITE_SH), 0.97))


def ruff_core(c):
    white_feathers(c)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(WHITE_SH))


def ruff_shell(c):
    """An inflated shell around the ruff, mostly cut away: a fringe of loose white feather tips that
    spill down over the brown breast."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face in SIDES:
                keep = (y == c.h - 1 and (x + (c.face in ("left", "back"))) % 2 == 0) or \
                       (y == c.h - 2 and c.rng.random() < 0.45) or (y < c.h - 2 and c.rng.random() < 0.18)
            elif c.face == "top":
                keep = c.rng.random() < 0.3 and (x in (0, c.w - 1) or y in (0, c.h - 1))
            else:
                keep = c.rng.random() < 0.25
            if not keep:
                c.clear(x, y)
                continue
            c.set(x, y, c.pick(WHITE) if c.rng.random() < 0.75 else c.pick(WHITE_SH))


def head_side(c):
    """6 long x 5 tall. A heavy grey brow overhangs a big amber eye with a black pupil and a glint;
    the yellow gape runs back under the eye."""
    white_feathers(c, shadow=False)
    for i, y in ((0, 1), (1, 1), (2, 1), (3, 1), (4, 0)):
        c.set(fx(c, i), y, BROW_DK if i in (1, 2) else BROW)       # the scowling brow ridge
    c.set(fx(c, 1), 2, SHINE)
    c.set(fx(c, 2), 2, PUPIL)
    c.set(fx(c, 1), 3, IRIS)
    c.set(fx(c, 2), 3, IRIS_DK)
    c.set(fx(c, 3), 2, IRIS)
    c.set(fx(c, 3), 3, mix(IRIS, WHITE[0], 0.5))
    c.set(fx(c, 0), 3, CERE)                                       # the gape, under the eye
    c.set(fx(c, 0), 4, BEAK_DK)
    c.set(fx(c, 1), 4, mix(CERE, WHITE[0], 0.4))
    for i in range(4, 6):                                          # feathers lie back on the cheek
        c.set(fx(c, i), 3, c.pick(WHITE_SH))


def head_front(c):
    white_feathers(c, shadow=False)
    for x in range(c.w):
        c.set(x, 1, BROW if x in (0, 1, c.w - 2, c.w - 1) else c.pick(WHITE))   # brows meeting over the beak
    c.set(0, 2, IRIS); c.set(c.w - 1, 2, IRIS)                     # the eyes peek round the corners


def head_top(c):
    white_feathers(c)
    for x in range(c.w):
        c.set(x, c.h - 1, BROW)                                    # the brow line, at the front edge


def beak_upper(c):
    """Golden upper beak: a yellow cere and nostril at the base, a ridge catching the light."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BEAK)
            if c.face in ("left", "right") and c.h > 1:
                col = shade(col, 1.04 - 0.12 * y / (c.h - 1))
            elif c.face == "bottom":
                col = BEAK_DK
            c.set(x, y, col)
    if c.face == "top":                                            # row 0 = back = the cere
        for x in range(c.w):
            c.set(x, 0, CERE)
        c.set(c.w // 2, 1, shade(BEAK[0], 1.12))                   # the ridge
        c.set(c.w // 2, 2, shade(BEAK[0], 1.12))
    elif c.face in ("left", "right"):
        c.set(fx(c, c.w - 1), 0, CERE)
        c.set(fx(c, c.w - 1), 1, CERE)
        c.set(fx(c, c.w - 2), 0, "#5a4320")                        # nostril
        c.set(fx(c, 0), c.h - 1, BEAK_DK)


def beak_hook(c):
    """The hook: golden at the top, curling down to a dark horn tip."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BEAK) if y < c.h - 1 else c.pick(BEAK_TIP)
            if y == c.h - 2:
                col = mix(c.pick(BEAK), BEAK_TIP[0], 0.45)
            if c.face == "back":
                col = BEAK_DK
            c.set(x, y, col)
    if c.face == "top":
        c.noise(BEAK)


def beak_lower(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BEAK), 0.85))
    if c.face == "top":
        c.noise(["#7a3a2a", "#6e3426"])                           # the inside of the mouth


# -- wings (authored spread: on top/bottom faces column 0 is the wing tip, row 0 the trailing edge) --
def wing_arm(c):
    """The leading edge: small brown coverts with pale tips."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FEATHER)
            if c.face in ("top", "bottom"):
                if y == c.h - 1:
                    col = shade(col, 1.12)                         # the very edge catches the light
                elif (x + y) % 3 == 0:
                    col = c.pick(FRINGE)
            elif c.face == "front":
                col = shade(col, 1.1)
            c.set(x, y, col)


def wing_coverts(c):
    """Greater coverts: a row of brown feathers, each ending in a pale fringe toward the trailing
    edge (row 0)."""
    if c.face in ("top", "bottom"):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FEATHER)
                if y == 0:
                    col = c.pick(FRINGE_LT) if x % 2 == 0 else c.pick(FRINGE)
                elif y == 1 and x % 2 == 1:
                    col = c.pick(FEATHER_DK)                       # the gap between two feathers
                elif y == c.h - 1 and (x + 1) % 3 == 0:
                    col = c.pick(FRINGE)
                c.set(x, y, col)
    elif c.face == "back":
        for x in range(c.w):
            c.set(x, 0, c.pick(FRINGE_LT) if x % 2 == 0 else c.pick(FRINGE))
    else:
        c.noise(FEATHER)


SEC_DEPTH = [5, 4, 5, 5, 4, 5, 5, 4, 5, 5]     # rows of visible depth per column (col 0 = tip end)


def secondaries(c):
    """Flight feathers of the inner wing, dark with pale bars across them, ending in a serrated
    trailing edge (a zero-thickness plane: both faces painted alike)."""
    for y in range(c.h):
        for x in range(c.w):
            depth = SEC_DEPTH[x % len(SEC_DEPTH)]
            if y < c.h - depth:
                c.clear(x, y)
                continue
            col = _pick(FLIGHT, x, y, 11)
            if (c.h - 1 - y) % 2 == 1:
                col = _pick(BAR, x, y, 12)                          # the pale bars
            if x % 2 == 1:
                col = shade(col, 0.88)                              # overlapping feathers
            if y == c.h - depth:
                col = shade(col, 1.15)                              # feather tips
            c.set(x, y, col)


TIP_MASK = [          # row 0 = trailing edge .. row 8 = leading; col 0 = the outermost tip
    ".....#####",
    "...#######",
    "......####",     # slot
    "..########",
    ".#########",
    ".....#####",     # slot
    ".#########",
    "##########",
    "..########",
]


def primaries(c):
    """The splayed primary 'fingers' at the wing tip, barred like the secondaries."""
    h, w = len(TIP_MASK), len(TIP_MASK[0])

    def solid(x, y):
        if x >= w:
            return True
        return 0 <= x and 0 <= y < h and TIP_MASK[y][x] == "#"

    for y in range(c.h):
        for x in range(c.w):
            if not solid(x, y):
                c.clear(x, y)
                continue
            col = _pick(FLIGHT, x, y, 23)
            if x % 3 == 1 and x < 7:
                col = _pick(BAR, x, y, 24)                          # bars across the fingers
            if not solid(x - 1, y):
                col = shade(col, 1.15)                              # rounded finger tips
            elif not solid(x, y + 1) or not solid(x, y - 1):
                col = shade(col, 0.8)                               # each finger's dark edge
            c.set(x, y, col)


def tip_coverts(c):
    if c.face in ("top", "bottom"):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FEATHER)
                if y == 0:
                    col = c.pick(FRINGE)
                elif (x + y) % 3 == 0:
                    col = c.pick(FEATHER_DK)
                c.set(x, y, col)
    else:
        c.noise(FEATHER)


# -- tail -------------------------------------------------------------------------------------------
def tail_paint(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FUR)
            if c.face == "bottom":
                col = c.pick(FUR_LT)
            elif c.face == "top":
                col = mix(col, c.pick(FUR_DK), 0.3)
            c.set(x, y, col)


def tuft_core(c):
    c.noise(TUFT)
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, mix(TUFT[0], FUR[0], 0.4))


def tuft_shell(c):
    for y in range(c.h):
        for x in range(c.w):
            if c.rng.random() < 0.6:
                c.clear(x, y)
            else:
                c.set(x, y, c.pick(TUFT))


# -- legs ----------------------------------------------------------------------------------------------
def trousers(c):
    """Feathered thighs of the eagle legs: brown above, white feather tips spilling over the scales."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FEATHER) if y < c.h - 2 else c.pick(FRINGE)
            if y == c.h - 1:
                col = c.pick(WHITE) if (x + (c.face in ("left", "back"))) % 2 == 0 else c.pick(FRINGE_LT)
            elif (x + y) % 3 == 0:
                col = c.pick(FRINGE)
            c.set(x, y, col)


def tarsus(c):
    """Scaly yellow eagle shank: big scutes down the front, small scales on the sides."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SCALE)
            if c.face == "front":
                col = SCALE_DK if y % 2 == 0 else shade(c.pick(SCALE), 1.08)
            elif c.face in ("left", "right", "back") and (x + y) % 2 == 0:
                col = shade(col, 0.95)
            c.set(x, y, col)


def toes(c):
    if c.face == "top":                                  # row 0 = back: three scaly toes
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, SCALE_DK if y % 2 == 0 else c.pick(SCALE))
    else:
        c.noise(SCALE)
        if c.face in SIDES:
            for x in range(c.w):
                c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.85))


def talons(c):
    """Three hooked black talons, cut apart."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face in ("front", "back", "top", "bottom") and x % 2 == 1:
                c.clear(x, y)
            else:
                c.set(x, y, c.pick(TALON))
    if c.face == "top":
        for x in range(0, c.w, 2):
            c.set(x, 0, "#3a3134")


def hind_toe(c):
    c.noise(SCALE)
    if c.face == "back":
        c.noise(TALON)


def haunch(c):
    """The lion's muscular thigh: tawny fur shaded round, darker behind."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FUR)
            if c.face in ("left", "right"):
                i = c.w - 1 - x if c.face == "right" else x            # 0 = front
                col = shade(col, 1.08 - 0.18 * abs(i - (c.w - 1) * 0.4) / c.w - 0.1 * y / c.h)
            elif c.face == "back":
                col = shade(col, 0.9)
            c.set(x, y, col)
    for _ in range(c.w * c.h // 6):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        c.set(x, y, c.pick(FUR_DK) if c.rng.random() < 0.5 else c.pick(FUR_LT))


def shank(c):
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(FUR), 1.0 - 0.08 * y / c.h)
            if c.face == "back":
                col = shade(col, 0.88)
            c.set(x, y, col)


def paw(c):
    """A big padded paw: pale fur, dark lines between the toes, dark pads underneath."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(FUR_LT))
    if c.face == "front":
        for y in range(c.h):
            c.set(1, y, c.pick(FUR_DK))
            c.set(c.w - 2, y, c.pick(FUR_DK))
    elif c.face == "top":
        for y in range(c.h - 2, c.h):
            c.set(1, y, c.pick(FUR_DK))
            c.set(c.w - 2, y, c.pick(FUR_DK))
    elif c.face == "bottom":
        c.noise(PAD)


# -- saddle ------------------------------------------------------------------------------------------
def leather(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LEATHER)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.0 - 0.15 * y / (c.h - 1))
            elif c.face == "bottom":
                col = c.pick(LEATHER_DK)
            c.set(x, y, col)


def blanket(c):
    """A deep blue saddle cloth with a gold border."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CLOTH)
            if c.face == "top" and (x in (0, c.w - 1) or y in (0, c.h - 1)):
                col = c.pick(GOLD)
            c.set(x, y, col)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, c.pick(GOLD))


def seat(c):
    leather(c)
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                if x in (0, c.w - 1) or y in (0, c.h - 1):
                    c.set(x, y, c.pick(LEATHER_DK))
                elif (x in (1, c.w - 2) or y in (1, c.h - 2)) and (x + y) % 3 == 0:
                    c.set(x, y, mix(STITCH, LEATHER[0], 0.35))
                elif 1 < x < c.w - 2 and 1 < y < c.h - 2:
                    c.set(x, y, mix(c.pick(LEATHER), LEATHER_HI, 0.3))
    elif c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, mix(LEATHER_HI, LEATHER[0], 0.4))


def rim(c):
    leather(c)
    if c.face == "top":
        c.noise([LEATHER_HI, shade(LEATHER_HI, 0.9)])


def strap(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, LEATHER_DK[0] if y % 3 else LEATHER[0])


def stirrup(c):
    c.noise(IRON)
    if c.face == "top":
        c.noise([IRON_HI])


ADULT = dict(
    torso=faces(torso_back, top=torso_top, right=torso_side, left=torso_side, front=torso_front,
                bottom=torso_bottom),
    chest=faces(chest), belly=faces(belly), shoulders=faces(shoulders), rump=faces(rump),
    neck=faces(neck_paint), ruff=faces(ruff_core), ruff_shell=faces(ruff_shell),
    head=faces(white_feathers, right=head_side, left=head_side, front=head_front, top=head_top),
    beak=faces(beak_upper), hook=faces(beak_hook), lower_beak=faces(beak_lower),
    arm=faces(wing_arm), coverts=faces(wing_coverts), secondaries=faces(secondaries),
    tip_arm=faces(wing_arm), tip_coverts=faces(tip_coverts), primaries=faces(primaries),
    tail=faces(tail_paint), tuft=faces(tuft_core), tuft_shell=faces(tuft_shell),
    trousers=faces(trousers), tarsus=faces(tarsus), toes=faces(toes), talons=faces(talons),
    hind_toe=faces(hind_toe),
    haunch=faces(haunch), shank=faces(shank), paw=faces(paw),
    blanket=faces(blanket), seat=faces(seat), rim=faces(rim), strap=faces(strap), stirrup=faces(stirrup),
)

# -- chick ---------------------------------------------------------------------------------------------
DOWN = ["#f1eee6", "#e8e4da", "#f5f2ec"]
DOWN_SH = ["#d6d0c3", "#cdc6b8"]
BUFF = ["#d9bd8c", "#e0c596", "#d2b483"]
BUFF_DK = ["#bf9f6c", "#b8986a"]


def fluff(pal, top=1.06, bottom=0.84, wisp=None):
    def p(c):
        for y in range(c.h):
            f = top if c.face == "top" else bottom if c.face == "bottom" else top - (top - bottom) * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(pal), f))
        for _ in range(c.w * c.h // 7):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, shade(c.pick(wisp or DOWN), 1.02 if c.face == "top" else 0.97))
    return p


def c_torso_side(c):
    fluff(BUFF, wisp=BUFF + DOWN[:1])(c)
    for y in range(c.h):
        for i in range(7 + (y % 2)):
            c.set(fx(c, i), y, shade(c.pick(DOWN), 1.0 - 0.1 * y / c.h))


def c_torso_top(c):
    fluff(BUFF, wisp=BUFF + DOWN[:1])(c)
    for y in range(c.h - 7, c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(DOWN))


def c_head_side(c):
    fluff(DOWN, wisp=DOWN_SH)(c)
    c.set(fx(c, 1), 2, SHINE)
    c.set(fx(c, 2), 2, PUPIL)
    c.set(fx(c, 1), 3, "#5a3b1c")
    c.set(fx(c, 2), 3, "#3d2812")
    c.set(fx(c, 0), 3, "#f0dc8a")


def c_clear(c):
    for y in range(c.h):
        for x in range(c.w):
            c.clear(x, y)


def c_stub(c):
    """Stubby downy flight feathers: only the first row or two survive at the wing's root half."""
    for y in range(c.h):
        for x in range(c.w):
            if y >= c.h - 2 and x >= c.w // 2:
                c.set(x, y, _pick(DOWN_SH, x, y, 3))
            else:
                c.clear(x, y)


def c_beak(c):
    c.noise(["#efd98f", "#e8cf80"])


CHICK = dict(
    torso=faces(fluff(BUFF, wisp=BUFF + DOWN[:1]), top=c_torso_top, right=c_torso_side, left=c_torso_side,
                front=fluff(DOWN, wisp=DOWN_SH)),
    chest=faces(fluff(DOWN, wisp=DOWN_SH)), belly=faces(fluff(DOWN, wisp=DOWN_SH)),
    shoulders=faces(fluff(DOWN, wisp=DOWN_SH)), rump=faces(fluff(BUFF)),
    neck=faces(fluff(DOWN, wisp=DOWN_SH)), ruff=faces(fluff(DOWN, wisp=DOWN_SH)), ruff_shell=faces(c_clear),
    head=faces(fluff(DOWN, wisp=DOWN_SH), right=c_head_side, left=c_head_side),
    beak=faces(c_beak), hook=faces(c_beak), lower_beak=faces(c_beak),
    arm=faces(fluff(DOWN, wisp=DOWN_SH)), coverts=faces(fluff(BUFF)), secondaries=faces(c_stub),
    tip_arm=faces(fluff(BUFF)), tip_coverts=faces(c_clear), primaries=faces(c_clear),
    tail=faces(fluff(BUFF)), tuft=faces(fluff(BUFF_DK)), tuft_shell=faces(c_clear),
    trousers=faces(fluff(DOWN, wisp=DOWN_SH)), tarsus=faces(lambda c: c.noise(["#efd98f", "#e6cd7c"])),
    toes=faces(lambda c: c.noise(["#efd98f", "#e6cd7c"])), talons=faces(lambda c: c.noise(["#8a7f74"])),
    hind_toe=faces(lambda c: c.noise(["#efd98f"])),
    haunch=faces(fluff(BUFF)), shank=faces(fluff(BUFF)), paw=faces(fluff(BUFF, wisp=DOWN)),
    # chicks are never saddled, but the sheet keeps the same layout
    blanket=faces(blanket), seat=faces(seat), rim=faces(rim), strap=faces(strap), stirrup=faces(stirrup),
)

WING_FOLD = (0.0, math.pi / 2, math.pi / 2)   # right wing; the left mirrors y and z
TIP_FOLD = (0.0, -0.12, 0.16)                 # right tip: a touch up and in, crossing over the rump


def make(texture_id, skin):
    """Build the griffin with the given painters. Geometry is identical for adult and chick."""
    m = Model("griffin", 128, 128, seed=6161, texture_id=texture_id)
    pk = Pack(m)
    s = skin

    # body: pivot y 6. A long torso y 2-11 (its flat top is the rider's seat height), a deep eagle
    # breast in front, a belly, a rise of feathers over the shoulders, round lion haunches behind.
    body = m.part("body", (0, 6, 0))
    pk.add(body, (-5, -4, -8), (10, 9, 19), s["torso"])
    pk.add(body, (-4.5, -3, -10), (9, 9, 2), s["chest"])
    pk.add(body, (-4, 5, -6), (8, 1, 9), s["belly"])
    pk.add(body, (-4, -5, -8), (8, 1, 3), s["shoulders"])
    pk.add(body, (-4.5, -3, 11), (9, 7, 1), s["rump"])

    # neck: white, rising forward from the breast inside a fluffy ruff; the head level on top
    neck = body.part("neck", (0, -2, -9), (0.5, 0, 0))
    pk.add(neck, (-2.5, -7, -2.5), (5, 8, 5), s["neck"])
    pk.add(neck, (-3.5, -2, -3.5), (7, 4, 7), s["ruff"])
    pk.add(neck, (-3.5, -2, -3.5), (7, 4, 7), s["ruff_shell"], inflate=0.5)
    head = neck.part("head", (0, -7, 0), (-0.5, 0, 0))
    pk.add(head, (-2.5, -4, -3.5), (5, 5, 6), s["head"])
    pk.add(head, (-1.5, -2.5, -6.5), (3, 2, 3), s["beak"])
    pk.add(head, (-1.5, -2, -7.5), (3, 3, 1), s["hook"])
    pk.add(head, (-1, -0.5, -5.5), (2, 1, 2), s["lower_beak"])

    # wings: authored spread out sideways (span along x, chord back along z): a 2 px leading edge,
    # a row of coverts and a plane of barred secondaries; the tip carries its own coverts and the
    # splayed primaries. The rest rotations fold them along the flanks.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        o = lambda x0, wd: x0 if not left else -x0 - wd      # mirror an x origin for the left side
        w = body.part(f"{side}_wing", (6.1 * sx, -4.5, -5), (WING_FOLD[0], WING_FOLD[1] * -sx, WING_FOLD[2] * -sx))
        pk.add(w, (o(-10, 10), -1, 0), (10, 2, 2), None if left else s["arm"], mirror=left, share="arm")
        pk.add(w, (o(-10, 10), -0.5, 2), (10, 1, 3), None if left else s["coverts"], mirror=left, share="coverts")
        pk.add(w, (o(-10, 10), 0, 5), (10, 0, 5), None if left else s["secondaries"], mirror=left,
               share="secondaries")
        t = w.part(f"{side}_wing_tip", (10 * sx, 0, 0),
                   (TIP_FOLD[0], TIP_FOLD[1] * -sx, TIP_FOLD[2] * -sx))
        pk.add(t, (o(-5, 5), -0.5, 0), (5, 1, 2), None if left else s["tip_arm"], mirror=left, share="tip_arm")
        pk.add(t, (o(-5, 5), -0.5, 2), (5, 1, 3), None if left else s["tip_coverts"], mirror=left,
               share="tip_coverts")
        pk.add(t, (o(-10, 10), 0, 1), (10, 0, 9), None if left else s["primaries"], mirror=left,
               share="primaries")

    # tail: a long lion tail drooping from the rump, ending in a dark tuft
    tail = body.part("tail", (0, -3, 11.5), (-0.9, 0, 0))
    pk.add(tail, (-1, -1, 0), (2, 2, 10), s["tail"])
    tuft = tail.part("tail_tuft", (0, 0, 10), (0.5, 0, 0))
    pk.add(tuft, (-1.5, -1.5, -0.5), (3, 3, 4), s["tuft"])
    pk.add(tuft, (-1.5, -1.5, -0.5), (3, 3, 4), s["tuft_shell"], inflate=0.4)

    # saddle: a gold-trimmed cloth on the flat back, the seat, pommel and cantle, and stirrups hanging
    # on straps down the flanks (tucked under the folded wings, just showing below them)
    saddle = body.part("saddle", (0, 0, 0))
    pk.add(saddle, (-5.5, -5, -5), (11, 1, 10), s["blanket"])
    pk.add(saddle, (-3.5, -6, -4), (7, 1, 8), s["seat"])
    pk.add(saddle, (-1, -7, -5), (2, 2, 1), s["rim"])
    pk.add(saddle, (-3, -7, 4), (6, 1, 1), s["rim"], share="cantle")
    for sx in (-1, 1):
        left = sx > 0
        pk.add(saddle, (4.5 if left else -5.5, -4.5, -0.5), (1, 9, 1), None if left else s["strap"], mirror=left,
               share="strap")
        pk.add(saddle, (4.5 if left else -6.5, 4.5, -1), (2, 1, 2), None if left else s["stirrup"], mirror=left,
               share="stirrup")

    # legs: children of root. Eagle forelegs (feathered thighs, scaly shanks, three toes and a hind
    # toe, black talons); lion hind legs (a big haunch, the shank set back at the hock, a padded paw).
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        o = lambda x0, wd: x0 if not left else -x0 - wd
        fl = m.part(f"{side}_front_leg", (3 * sx, 10, -6.5))
        pk.add(fl, (o(-1.5, 3), -1, -1.5), (3, 6, 3), None if left else s["trousers"], mirror=left, share="trousers")
        pk.add(fl, (o(-1, 2), 5, -1), (2, 8, 2), None if left else s["tarsus"], mirror=left, share="tarsus")
        pk.add(fl, (o(-1.5, 3), 13, -3.5), (3, 1, 3), None if left else s["toes"], mirror=left, share="toes")
        pk.add(fl, (o(-1.5, 3), 13, -4.5), (3, 1, 1), None if left else s["talons"], mirror=left, share="talons")
        pk.add(fl, (o(-0.5, 1), 13, 1), (1, 1, 2), None if left else s["hind_toe"], mirror=left, share="hind_toe")
        hl = m.part(f"{side}_hind_leg", (3 * sx, 9, 7.5))
        pk.add(hl, (o(-1.8, 4), 0, -3), (4, 7, 6), None if left else s["haunch"], mirror=left, share="haunch")
        pk.add(hl, (o(-1.5, 3), 7, 0), (3, 6, 3), None if left else s["shank"], mirror=left, share="shank")
        pk.add(hl, (o(-2, 4), 13, -1.5), (4, 2, 4), None if left else s["paw"], mirror=left, share="paw")

    if POSE.startswith("spread"):
        flap = {"spread": 0.1, "spreadup": 0.75, "spreaddown": -0.55}.get(POSE, 0.1)
        tipf = {"spread": 0.05, "spreadup": 0.35, "spreaddown": -0.4}.get(POSE, 0.05)
        m.preview = {"right_wing": [0, 0.1, flap], "left_wing": [0, -0.1, -flap],
                     "right_wing_tip": [0, 0.15, tipf], "left_wing_tip": [0, -0.15, -tipf],
                     "right_front_leg": [1.1, 0, 0], "left_front_leg": [1.1, 0, 0],
                     "right_hind_leg": [1.2, 0, 0], "left_hind_leg": [1.2, 0, 0],
                     "tail": [-0.2, 0, 0], "neck": [0.85, 0, 0], "head": [-0.85, 0, 0]}
    elif POSE == "walk":
        m.preview = {"right_front_leg": [-0.5, 0, 0], "left_hind_leg": [-0.5, 0, 0],
                     "left_front_leg": [0.5, 0, 0], "right_hind_leg": [0.5, 0, 0]}

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("griffin_chick", CHICK).save(geometry=False)
    spawn_egg("griffin", "#c99a58", "#f2f0ea", accent="#6a4a2e")


if __name__ == "__main__":
    build()

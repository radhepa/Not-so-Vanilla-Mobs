"""Stormcaller: an illager storm mystic, drawn on the vanilla illager body (the game uses vanilla
IllagerModel and its animations, so the head, hat, nose, body, robe, crossed arms, legs and arms
are vanilla's parts, pivots, cubes and sizes exactly; only the texture layout is our own).

Pale grey-green illager skin, the big illager nose and one heavy scowling brow, and eyes that burn
a pale electric blue. Dark slate hair streaked with grey is swept back from the face, with grey
stubble and a short goatee. A copper circlet gone green with verdigris rings the brow, with a
copper plate set with a crackling blue spark and a short upright lightning rod rising from it.

A long storm-grey / slate-blue robe under a dark navy mantle with a high standing collar flared
behind the head. Hem, mantle edge, collar rim and cuffs are trimmed with old copper, mostly
verdigris with a few un-oxidised orange glints. A jagged lightning bolt is embroidered down the
front of the robe from chest to hem in faintly glowing pale cyan thread on a navy panel: the
lower half shows below its crossed arms, the whole bolt when it raises its arms to cast. Tiny
static sparks crackle on its sleeves.

The hat part (which the game always hides) and the body cube (always inside the robe) share one
texture region that is left transparent."""
import math

from mobkit import Model, faces, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Stormcaller"
LOOT = [item("emerald", 0, 2), item("copper_ingot", 1, 3), item("wind_charge", 1, 3, chance=0.35)]
TAGS = ["illager", "raiders"]

# skin and hair
SKIN = ["#a5afa6", "#99a49b", "#8f9a91", "#a0aaa1"]
SKIN_LIGHT = "#b3bcb3"
SKIN_DARK = "#7b857d"
SKIN_DEEP = "#626b64"
BROW = "#353a39"
BROW_HI = "#4a504e"
MOUTH = "#3d3838"
STUBBLE = ["#6f7773", "#666d69", "#767e7a"]
GOATEE = ["#59605d", "#525855", "#5f6663"]
HAIR = ["#5d646a", "#565c62", "#646b71"]
HAIR_DARK = "#41464c"
STREAK = ["#8d949a", "#9ea5aa", "#878e94"]
EYE_BASE = "#162433"          # dim base under the glow (the glow layer is added on top)
EYE = "#bfe6ff"
EYE_DIM = "#6fc3ff"
# robe, mantle and collar
ROBE = ["#4c5a6e", "#56677d", "#4c5a6e", "#3e4a5c", "#526278"]
ROBE_LIGHT = "#62748b"
ROBE_FOLD = "#36414f"
NAVY = ["#232b3c", "#1e2534", "#283246"]
NAVY_LIGHT = "#323e55"
NAVY_DEEP = "#171c28"
LINING = ["#3a4658", "#343f50"]
# copper gone to verdigris
VERD = ["#3fa58f", "#4fc0a4", "#3fa58f", "#2d7f6b"]
VERD_LIGHT = "#6fd6b9"
VERD_DEEP = "#22604f"
COPPER = ["#c26d3f", "#b5623a", "#d07c4a"]
# the embroidered bolt and static sparks
SIGIL_BASE = "#1d3348"
SIGIL = "#dff6ff"
SIGIL_DIM = "#9fdcf6"
SPARK = "#bfe6ff"
SPARK_DIM = "#6fc3ff"
# boots
BOOT = ["#3b3533", "#332e2c", "#413a37"]
BOOT_HI = "#57504c"
SOLE = ["#252120", "#1f1c1b"]
SIDES = ("front", "back", "left", "right")


# -- texture packing ---------------------------------------------------------------------------------
class Pack:
    """Face-level packer. Each cube's six box-UV face rectangles go at the first spot (row by row)
    where none of them touches a used texel, so small cubes nest in the empty corners of big ones.
    share= gives several cubes one region (mirrored limbs, or parts that are never seen); a region
    whose cubes are all unpainted stays transparent. pad=True keeps a 1 px empty gutter round the
    cube's faces (for cut-out pixels)."""

    def __init__(self, model):
        self.m, self.items, self.pins = model, [], {}

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0, pad=False, at=None):
        self.items.append((part, origin, size, paint, mirror, share, inflate, pad))
        if at:
            self.pins[share or ("#", len(self.items) - 1)] = at

    @staticmethod
    def rects(size):
        w, h, d = (int(math.ceil(s)) for s in size)
        out = [(d, 0, w, d), (d + w, 0, w, d), (0, d, d, h), (d, d, w, h), (d + w, d, d, h), (2 * d + w, d, w, h)]
        return [r for r in out if r[2] > 0 and r[3] > 0]

    def apply(self):
        W, H = self.m.tex_w, self.m.tex_h
        groups, order = {}, []
        for i, it in enumerate(self.items):
            k = it[5] or ("#", i)
            if k not in groups:
                groups[k] = [set(), False]
                order.append(k)
            groups[k][0].update(self.rects(it[2]))
            groups[k][1] = groups[k][1] or it[7]

        def bbox(k):
            rs = groups[k][0]
            return max(x + w for x, y, w, h in rs), max(y + h for x, y, w, h in rs)

        order.sort(key=lambda k: (k not in self.pins, -bbox(k)[0] * bbox(k)[1], -bbox(k)[1]))
        used = [[False] * W for _ in range(H)]
        pos = {}
        for k in order:
            rs, pad = groups[k]
            bw, bh = bbox(k)
            g = 1 if pad else 0
            cells = sorted({(xx, yy) for (x, y, w, h) in rs
                            for yy in range(y - g, y + h + g) for xx in range(x - g, x + w + g)})
            found = self.pins.get(k)
            for v in ([] if found else range(0, H - bh + 1)):
                for u in range(0, W - bw + 1):
                    if all(not (0 <= u + xx < W and 0 <= v + yy < H) or not used[v + yy][u + xx]
                           for (xx, yy) in cells):
                        found = (u, v)
                        break
                if found:
                    break
            if not found:
                raise ValueError(f"{self.m.id}: no texture room for {k} {bw}x{bh}")
            pos[k] = found
            for (xx, yy) in cells:
                if 0 <= found[0] + xx < W and 0 <= found[1] + yy < H:
                    used[found[1] + yy][found[0] + xx] = True
        for i, (part, origin, size, paint, mirror, share, inflate, pad) in enumerate(self.items):
            part.cube(pos[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


# -- shared helpers ----------------------------------------------------------------------------------
def tone(c, y, col, k=0.16):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k - 0.06
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def back_col(c, i=0):
    """Column i counted from the back edge of a right/left side face."""
    return i if c.face == "right" else c.w - 1 - i


def verd(c, orange=0.12):
    """Verdigris copper: teal-green, now and then a glint of un-oxidised orange."""
    r = c.rng.random()
    if r < orange:
        return c.pick(COPPER)
    return c.pick(VERD)


def glow_on(c, x, y, col, base=SIGIL_BASE):
    """A glowing pixel on a dim base, so the additive glow layer keeps its colour."""
    c.glow(x, y, col)
    c.set(x, y, base)


def spark(c, x, y, diag=1):
    """A two-pixel static spark: a bright point and a dimmer tail."""
    glow_on(c, x, y, SPARK, EYE_BASE)
    glow_on(c, x + diag, y + 1, SPARK_DIM, EYE_BASE)


# -- head --------------------------------------------------------------------------------------------
def skin_px(c, y, k=0.08):
    return tone(c, y, c.pick(SKIN), k)


def hair_px(c, y, streak=0.0, k=0.08):
    col = c.pick(STREAK) if c.rng.random() < streak else c.pick(HAIR)
    return tone(c, y, col, k)


def lanes(c, n):
    """Strand types for n parallel strands of swept-back hair: 0 dark, 1 plain, 2 grey streak."""
    return [c.rng.choice((0, 1, 1, 1, 2, 2)) for _ in range(n)]


def strand(c, lane, t):
    """Colour of a hair pixel t pixels along a strand of the given type."""
    if lane == 2 and t % 4 != 3:
        return c.pick(STREAK)
    if lane == 0 and t % 3:
        return HAIR_DARK
    return c.pick(HAIR)


def face(c):
    """8x10 face: hair, (circlet), forehead, the heavy brow, glowing eyes, nose bridge, mouth, goatee."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, skin_px(c, y, 0.06))
    for x in range(8):                                   # hairline with receding temples
        c.set(x, 0, hair_px(c, 0))
        if x not in (2, 5):
            c.set(x, 1, hair_px(c, 1))
    for x in range(8):                                   # skin under the circlet, shadowed
        c.set(x, 2, shade(c.pick(SKIN), 0.84))
    c.set(0, 3, SKIN_DARK); c.set(7, 3, SKIN_DARK)
    c.set(1, 3, BROW_HI); c.set(6, 3, BROW_HI)           # one heavy brow, raised at its ends ...
    for x in range(1, 7):                                # ... and pulled down into a scowl
        c.set(x, 4, BROW)
    c.set(0, 4, SKIN_DEEP); c.set(7, 4, SKIN_DEEP)
    c.set(3, 5, SKIN_DEEP); c.set(4, 5, SKIN_DEEP)       # deep frown over the bridge of the nose
    glow_on(c, 1, 5, EYE_DIM, EYE_BASE); glow_on(c, 2, 5, EYE, EYE_BASE)     # eyes: bright inner pixel
    glow_on(c, 5, 5, EYE, EYE_BASE); glow_on(c, 6, 5, EYE_DIM, EYE_BASE)
    c.set(0, 5, SKIN_DARK); c.set(7, 5, SKIN_DARK)
    for x in (1, 2, 5, 6):                               # hollow under the eyes
        c.set(x, 6, SKIN_DARK)
    c.set(3, 6, SKIN_LIGHT); c.set(4, 6, SKIN_LIGHT)     # top of the nose bridge
    c.set(0, 6, SKIN_DEEP); c.set(7, 6, SKIN_DEEP)
    c.set(1, 7, SKIN_DARK); c.set(6, 7, SKIN_DARK)       # gaunt cheeks
    for x in (2, 5):
        c.set(x, 7, c.pick(SKIN))
    for x in range(2, 6):                                # grim mouth (the nose hides its middle)
        c.set(x, 8, MOUTH)
    c.set(1, 8, c.pick(STUBBLE)); c.set(6, 8, c.pick(STUBBLE))
    c.set(0, 8, c.pick(STUBBLE) if c.rng.random() < 0.5 else SKIN_DARK)
    c.set(7, 8, c.pick(STUBBLE) if c.rng.random() < 0.5 else SKIN_DARK)
    for x in range(8):                                   # goatee and stubble on the chin
        c.set(x, 9, c.pick(GOATEE) if 2 <= x <= 5 else c.pick(STUBBLE))
    c.set(0, 7, c.pick(STUBBLE)); c.set(7, 7, c.pick(STUBBLE))


def head_side(c):
    """Side of the head: skin at the front, steel-grey hair swept back over the rear half."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, skin_px(c, y))
    ln = lanes(c, c.h)
    for x in range(c.w):
        b = x if c.face == "right" else c.w - 1 - x     # 0 at the back edge
        depth = 7 if b <= 3 else (6 if b == 4 else (5 if b == 5 else 1))
        if b <= 3 and c.rng.random() < 0.5:
            depth += 1                                   # ragged ends of the swept-back hair
        for y in range(depth):
            c.set(x, y, tone(c, y, strand(c, ln[y], 7 - b), 0.08))
        if b <= 5:
            c.set(x, depth, tone(c, depth, HAIR_DARK))
        c.set(x, 2, shade(c.get(x, 2), 0.84))           # under the circlet
        if b >= 4:
            c.set(x, 9, c.pick(STUBBLE))                 # stubbled jaw
            if b >= 6:
                c.set(x, 8, c.pick(STUBBLE) if c.rng.random() < 0.6 else SKIN_DARK)


def head_back(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, skin_px(c, y))
    ln = lanes(c, c.w)
    for x in range(c.w):
        depth = 8 + (1 if c.rng.random() < 0.35 else 0)
        for y in range(depth):
            c.set(x, y, tone(c, y, strand(c, ln[x], y), 0.12))
        c.set(x, depth - 1, tone(c, depth - 1, HAIR_DARK))
        c.set(x, depth, SKIN_DEEP)                       # nape in shadow
    for x in range(c.w):
        c.set(x, 2, shade(c.get(x, 2), 0.86))


def head_top(c):
    """Hair swept back from the brow: strands run front to back (row 7 is the front edge)."""
    ln = lanes(c, c.w)
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(strand(c, ln[x], 7 - y), 1.08))


def head_bottom(c):
    """Under the jaw: the neck in shadow, goatee and stubble along the front (last rows)."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(SKIN), 0.7))
    for x in range(c.w):
        c.set(x, 7, c.pick(GOATEE) if 2 <= x <= 5 else c.pick(STUBBLE))
        if 2 <= x <= 5:
            c.set(x, 6, shade(c.pick(GOATEE), 0.9))
        elif c.rng.random() < 0.5:
            c.set(x, 6, shade(c.pick(STUBBLE), 0.85))


def nose(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SKIN)
            if c.face == "top":
                col = SKIN_LIGHT
            elif c.face == "bottom":
                col = SKIN_DEEP if x == y else SKIN_DARK
            elif c.face in SIDES:
                col = tone(c, y, col, 0.2)
                if c.face in ("left", "right"):
                    col = shade(col, 0.9)
            c.set(x, y, col)
    if c.face == "front":
        c.set(0, 0, SKIN_LIGHT); c.set(1, 0, c.pick(SKIN))
        c.set(0, 3, SKIN_DARK); c.set(1, 3, SKIN_DARK)


# -- circlet and lightning rod -----------------------------------------------------------------------
def band(c):
    """A bar of the circlet ring: verdigris links, an orange glint here and there."""
    for y in range(c.h):
        for x in range(c.w):
            col = verd(c, 0.1)
            if c.face in SIDES and c.w > 2 and x % 3 == 2:
                col = VERD_DEEP                          # joins between the links
            if c.face == "top":
                col = shade(col, 1.1)
            elif c.face == "bottom":
                col = shade(col, 0.7)
            c.set(x, y, col)


def plate(c):
    """The brow plate: a 3x2 copper setting holding a crackling spark."""
    for y in range(c.h):
        for x in range(c.w):
            col = verd(c, 0.0)
            if c.face == "top":
                col = VERD_LIGHT if x != 1 else c.pick(VERD)
            elif c.face == "bottom":
                col = VERD_DEEP
            c.set(x, y, col)
    if c.face == "front":
        c.set(0, 0, COPPER[0]); c.set(2, 0, c.pick(VERD))
        c.set(0, 1, VERD_DEEP); c.set(2, 1, VERD_DEEP)
        glow_on(c, 1, 0, SPARK_DIM, EYE_BASE)
        glow_on(c, 1, 1, SPARK, EYE_BASE)


def rod(c):
    for y in range(c.h):
        for x in range(c.w):
            col = (VERD[1], COPPER[0], VERD[0])[y % 3] if c.face in SIDES else VERD_LIGHT
            if c.face in ("right", "back"):
                col = shade(col, 0.82)
            c.set(x, y, col)


def knob(c):
    """The rod's knob, charged: verdigris with an orange glint and a spark on top."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(VERD)
            if c.face == "top":
                col = VERD_LIGHT
            elif c.face == "bottom":
                col = VERD_DEEP
            elif y == 1:
                col = shade(col, 0.82)
            c.set(x, y, col)
    if c.face == "top":
        glow_on(c, 1, 0, SPARK, EYE_BASE)
    elif c.face == "front":
        c.set(0, 0, COPPER[2])
    elif c.face == "left":
        c.set(1, 0, COPPER[0])


# -- robe --------------------------------------------------------------------------------------------
# The bolt down the front of the robe (front-face pixels): leading edge bright, trailing edge dimmer.
BOLT_TOP = 5
BOLT_ART = [            # B bright core, d dim edge; rows 5-8 hide behind the crossed arms
    "....dB..",
    "...dB...",
    "..dB....",
    "..BBBBd.",
    "....Bd..",
    "...Bd...",
    "..Bd....",
    ".dBBBB..",
    "....Bd..",
    "...Bd...",
    "...B....",
    "..d.....",
]
BOLT_PX = {(x, BOLT_TOP + y): ch == "B" for y, row in enumerate(BOLT_ART) for x, ch in enumerate(row) if ch != "."}


def robe_px(c, y, k=0.2):
    col = c.pick(ROBE)
    if c.rng.random() < 0.05:
        col = ROBE_LIGHT
    return tone(c, y, col, k)


def hem(c, y0):
    """Copper hem trim: a dark stitch line, then two rows of verdigris."""
    for x in range(c.w):
        c.set(x, y0 - 1, tone(c, y0 - 1, ROBE_FOLD, 0.2))
        c.set(x, y0, tone(c, y0, verd(c), 0.1))
        col = verd(c, 0.18)
        c.set(x, y0 + 1, tone(c, y0 + 1, shade(col, 0.82), 0.1))


def robe(c):
    """8x20x6 robe (inflated): slate-blue cloth with folds, copper hem, the bolt panel down the front."""
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                c.set(x, y, shade(c.pick(NAVY), 1.05))
        return
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                edge = x in (0, w - 1) or y in (0, h - 1)
                c.set(x, y, shade(c.pick(VERD), 0.6) if edge else NAVY_DEEP)
        return
    for y in range(h):
        for x in range(w):
            c.set(x, y, robe_px(c, y))
    if c.face == "front":
        for y in range(4, 18):                           # navy panel behind the bolt
            for x in range(2, 6):
                c.set(x, y, tone(c, y, c.pick(NAVY), 0.12))
        for y in range(5, 18):                           # folds either side of it
            c.set(1, y, tone(c, y, ROBE_FOLD, 0.15))
            c.set(6, y, tone(c, y, ROBE_FOLD, 0.15))
        for (x, y), bright in BOLT_PX.items():
            glow_on(c, x, y, SIGIL if bright else SIGIL_DIM)
    elif c.face == "back":
        for y in range(5, 18):
            c.set(3, y, tone(c, y, c.pick(NAVY), 0.12))   # back seam with a navy band
            c.set(4, y, tone(c, y, c.pick(NAVY), 0.12))
        for y in range(7, 17, 3):
            c.set(1, y, tone(c, y, ROBE_FOLD))
            c.set(6, y + 1, tone(c, y + 1, ROBE_FOLD))
    else:
        for y in range(6, 18):                           # a long fold down each side
            c.set(back_col(c, 2), y, tone(c, y, ROBE_FOLD, 0.15))
            if y > 11:
                c.set(back_col(c, 4), y, tone(c, y, ROBE_FOLD, 0.15))
    hem(c, h - 2)


# -- mantle and collar -------------------------------------------------------------------------------
def navy_px(c, y, k=0.18):
    col = c.pick(NAVY)
    if c.rng.random() < 0.06:
        col = NAVY_LIGHT
    return tone(c, y, col, k)


def mantle(c):
    """One half (5x5x9) of the shoulder mantle, mirrored for the other: dark navy, a verdigris edge
    along the bottom, half of the clasp at the throat. Column 0 of the top/bottom/front faces is the
    outer edge, the last column the middle; on the back face column 0 is the middle."""
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                c.set(x, y, shade(c.pick(NAVY), 1.18 if x == 0 else 1.08))
        return
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                edge = x == 0 or y in (0, h - 1)
                c.set(x, y, shade(c.pick(VERD), 0.62) if edge else NAVY_DEEP)
        return
    for y in range(h):
        for x in range(w):
            c.set(x, y, navy_px(c, y))
    for x in range(w):
        c.set(x, 0, shade(c.get(x, 0), 1.14))           # light catching the shoulder
        c.set(x, h - 1, tone(c, h - 1, verd(c, 0.14), 0.08))
    if c.face == "front":
        c.set(4, 1, VERD_LIGHT); c.set(4, 2, COPPER[0])  # the clasp
        c.set(3, 1, c.pick(VERD)); c.set(3, 2, NAVY_DEEP)
        c.set(4, 3, NAVY_DEEP)                           # the mantle parts below it
    elif c.face == "back":
        for y in range(1, h - 1):
            c.set(0, y, tone(c, y, NAVY_DEEP))
            c.set(2, y, tone(c, y, NAVY_LIGHT) if y > 1 else c.get(2, y))


def collar(c):
    """Standing collar behind the head (mirrored halves; each half a 4x5x1 plate with a 2x1x1 step on
    top): navy outside, slate lining inside (facing the head), a verdigris rim along the top."""
    w, h = c.w, c.h
    if c.face == "top":
        for x in range(w):
            c.set(x, 0, shade(verd(c, 0.15), 1.08))
        return
    if c.face == "bottom":
        c.noise([NAVY_DEEP])
        return
    inner = c.face == "front"
    for y in range(h):
        for x in range(w):
            col = c.pick(LINING) if inner or c.face == "left" else c.pick(NAVY)
            c.set(x, y, tone(c, y, col, 0.2))
    for x in range(w):
        c.set(x, 0, verd(c, 0.15))
        if c.face == "back" and h > 2:
            c.set(x, 1, shade(c.pick(VERD), 0.7) if x % 2 == 0 else c.get(x, 1))


def side_collar(c):
    """Side wings of the collar: like the back piece. The inner face is the 'left' region
    (mirrored onto the other wing, where it again faces in)."""
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                c.set(x, y, shade(verd(c, 0.15), 1.08))
        return
    if c.face == "bottom":
        c.noise([NAVY_DEEP])
        return
    inner = c.face == "left"
    for y in range(h):
        for x in range(w):
            col = c.pick(LINING) if inner else c.pick(NAVY)
            c.set(x, y, tone(c, y, col, 0.2))
    for x in range(w):
        c.set(x, 0, verd(c, 0.15))


# -- arms and legs -----------------------------------------------------------------------------------
def sleeve_px(c, y, k=0.16):
    col = c.pick(ROBE)
    if c.rng.random() < 0.04:
        col = ROBE_LIGHT
    return tone(c, y, col, k)


def shoulder(c):
    """Crossed-arms pose, upper arm (4x8x4): sleeve, with static sparks on the outer face."""
    for y in range(c.h):
        for x in range(c.w):
            col = sleeve_px(c, y)
            if c.face == "top":
                col = shade(col, 1.06)
            c.set(x, y, col)
    if c.face == "right":                                # outer face (mirrored onto the left arm)
        spark(c, 1, 2)
        c.set(0, 6, ROBE_FOLD); c.set(3, 5, ROBE_FOLD)
    elif c.face == "front":
        c.set(1, 4, ROBE_FOLD); c.set(2, 6, ROBE_FOLD)
    elif c.face == "bottom":
        c.noise([shade(x, 0.6) for x in NAVY])


def crossed(c):
    """Crossed forearms (8x4x4): sleeves meeting in the middle, verdigris cuffs, grey hands at the
    ends tucked against the opposite elbows."""
    w, h = c.w, c.h
    for y in range(h):
        for x in range(w):
            col = sleeve_px(c, y, 0.12)
            if c.face == "top":
                col = shade(col, 1.06)
            elif c.face == "bottom":
                col = shade(c.pick(ROBE), 0.68)
            c.set(x, y, col)
    if c.face in ("front", "top", "bottom"):
        for y in range(h):
            for (x, cuff) in ((0, False), (1, True), (6, True), (7, False)):
                if cuff:
                    col = verd(c, 0.2)
                else:
                    col = c.pick(SKIN) if c.face != "bottom" else SKIN_DARK
                c.set(x, y, tone(c, y, col, 0.12) if c.face == "front" else col)
    if c.face == "front":
        for y in range(h):                               # where the two sleeves cross
            c.set(3 if y < 2 else 4, y, tone(c, y, ROBE_FOLD, 0.1))
        c.set(0, 3, SKIN_DARK); c.set(7, 3, SKIN_DARK)  # fingers in shadow
        spark(c, 5, 0, -1)


def arm(c):
    """Free arm (4x12x4), shown when casting: sleeve, verdigris cuff, grey hand, sparks outside."""
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                c.set(x, y, shade(c.pick(ROBE), 1.06))
        return
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                c.set(x, y, SKIN_DARK if (x + y) % 3 else SKIN_DEEP)
        return
    for y in range(h):
        for x in range(w):
            if y < 8:
                col = sleeve_px(c, y, 0.12)
            elif y == 8:
                col = verd(c, 0.2)
            elif y == 9:
                col = shade(verd(c, 0.1), 0.8)
            else:
                col = c.pick(SKIN)
                if y == 11:
                    col = SKIN_DARK
            c.set(x, y, col)
    if c.face == "right":                                # outer face (mirrored onto the left arm)
        spark(c, 1, 2)
        spark(c, 2, 5, -1)
        c.set(0, 7, ROBE_FOLD)
    elif c.face == "front":
        c.set(1, 3, ROBE_FOLD); c.set(2, 6, ROBE_FOLD)
        c.set(1, 10, SKIN_LIGHT)
    elif c.face == "back":
        spark(c, 1, 3)


def leg(c):
    """4x12x4 leg: only the bottom rows show below the robe: slate trousers, then old boots."""
    w, h = c.w, c.h
    if c.face == "top":
        c.noise(NAVY)
        return
    if c.face == "bottom":
        c.noise(SOLE)
        return
    for y in range(h):
        for x in range(w):
            if y < 9:
                col = tone(c, y, c.pick(NAVY), 0.1)
            elif y == 9:
                col = shade(c.pick(BOOT), 1.2)           # boot cuff
            else:
                col = c.pick(BOOT)
                if y == 11:
                    col = shade(col, 0.82)
            c.set(x, y, col)
    if c.face == "front":
        c.set(1, 10, BOOT_HI); c.set(2, 11, verd(c, 0.3))           # a copper toe cap gone green
        c.set(1, 11, shade(c.pick(VERD), 0.75))


def build():
    m = Model("stormcaller", 64, 64, seed=6107)
    pk = Pack(m)

    # vanilla IllagerModel layout (names, pivots, cubes, sizes exactly as the game's), at vanilla's
    # own texture spots; the hat (hidden by the game) and the body cube (always inside the robe)
    # share one unpainted region, so the old body region is free for the mantle and collar
    head = m.part("head")
    pk.add(head, (-4, -10, -4), (8, 10, 8), faces(head_side, front=face, back=head_back,
                                                      top=head_top, bottom=head_bottom), at=(0, 0))
    hat = head.part("hat")
    pk.add(hat, (-4, -10, -4), (8, 12, 8), None, inflate=0.45, share="unseen", at=(32, 0))
    nose_p = head.part("nose", (0, -2, 0))
    pk.add(nose_p, (-1, -1, -6), (2, 4, 2), faces(nose), at=(24, 0))
    body = m.part("body")
    pk.add(body, (-4, 0, -3), (8, 12, 6), None, share="unseen")
    pk.add(body, (-4, 0, -3), (8, 20, 6), faces(robe), inflate=0.5, at=(0, 38))
    arms = m.part("arms", (0, 3, -1), (-0.75, 0, 0))
    pk.add(arms, (-8, -2, -2), (4, 8, 4), faces(shoulder), share="shoulder", at=(44, 22))
    pk.add(arms, (-4, 2, -2), (8, 4, 4), faces(crossed), at=(40, 38))
    pk.add(arms.part("left_shoulder"), (4, -2, -2), (4, 8, 4), None, mirror=True, share="shoulder")
    pk.add(m.part("right_leg", (-2, 12, 0)), (-2, 0, -2), (4, 12, 4), faces(leg), share="leg", at=(0, 22))
    pk.add(m.part("left_leg", (2, 12, 0)), (-2, 0, -2), (4, 12, 4), None, mirror=True, share="leg")
    pk.add(m.part("right_arm", (-5, 2, 0)), (-3, -2, -2), (4, 12, 4), faces(arm), share="arm", at=(40, 46))
    pk.add(m.part("left_arm", (5, 2, 0)), (-1, -2, -2), (4, 12, 4), None, mirror=True, share="arm")

    # copper circlet round the brow, a brow plate and a short lightning rod (children of head, not of
    # the hidden hat). The ring is four 1x1 bars half sunk into the head: front and back share one
    # region, the side bars are mirrored; they butt end to end, so no two faces lie on each other.
    circlet = head.part("circlet")
    pk.add(circlet, (-4.5, -8, -4.5), (9, 1, 1), faces(band), share="band_fb", at=(28, 20))
    pk.add(circlet, (-4.5, -8, 3.5), (9, 1, 1), None, share="band_fb")
    pk.add(circlet, (-4.5, -8, -3.5), (1, 1, 7), faces(band), share="band_side", at=(28, 56))
    pk.add(circlet, (3.5, -8, -3.5), (1, 1, 7), None, mirror=True, share="band_side")
    pk.add(circlet, (-1.5, -9.25, -5), (3, 2, 1), faces(plate), at=(0, 0))
    lrod = circlet.part("lightning_rod", (0, -9.25, -4.5))
    pk.add(lrod, (-0.5, -3, -0.5), (1, 3, 1), faces(rod), at=(56, 0))
    pk.add(lrod, (-1, -5, -1), (2, 2, 2), faces(knob), at=(0, 3))

    # navy mantle over the shoulders and a high collar flaring behind the head (mirrored halves)
    mant = body.part("mantle")
    pk.add(mant, (-5, -1, -4.5), (5, 5, 9), faces(mantle), share="mantle", at=(16, 24))
    pk.add(mant, (0, -1, -4.5), (5, 5, 9), None, mirror=True, share="mantle")
    cb = body.part("collar_back", (0, 0.5, 4), (-0.36, 0, 0))
    pk.add(cb, (-4, -5.5, 0), (4, 5, 1), faces(collar), share="collar", at=(16, 18))
    pk.add(cb, (0, -5.5, 0), (4, 5, 1), None, mirror=True, share="collar")
    pk.add(cb, (-2, -6.5, 0), (2, 1, 1), faces(collar), share="collar_top", at=(0, 18))
    pk.add(cb, (0, -6.5, 0), (2, 1, 1), None, mirror=True, share="collar_top")
    cr = body.part("collar_right", (-4.5, 0.5, 1.2), (0, 0, -0.28))
    pk.add(cr, (-0.5, -4.5, -2), (1, 4, 5), faces(side_collar), share="collar_side", at=(28, 44))
    cl = body.part("collar_left", (4.5, 0.5, 1.2), (0, 0, 0.28))
    pk.add(cl, (-0.5, -4.5, -2), (1, 4, 5), None, mirror=True, share="collar_side")

    pk.apply()
    # the previewer draws every part: show the free arms raised as when casting (the game shows
    # either these or the crossed arms, never both, and always hides the hat)
    m.preview = {"right_arm": [0, 0, 2.3562], "left_arm": [0, 0, -2.3562]}
    m.save()
    spawn_egg("stormcaller", "#4c5a6e", "#3fa58f", accent="#bfe6ff")


if __name__ == "__main__":
    build()

"""Rimewraith: a floating spectre of ice and snow haunting frozen peaks. A deep cowl of packed snow
(white to pale blue) with real depth: walls, a brim and a ceiling round a pit of darkness, at the back
of which two slanted, piercing ice-blue eyes glow over a faint jaw of frost. Under a snowy mantle the
torso is a ribcage of blue glacial ice (three rib hoops, a sternum and a spine, white frost cracks)
around a faintly glowing pale core. Jagged ice crystals grow up from both shoulders and from the back
of the hood like a crown of icicles. Long thin arms of ice hang at its sides, a spur at each elbow,
ending in long pale icicle claws. From a frosted sash hangs a tattered frost-white robe with pale blue
folds, hollow and dark inside, its hem cut into long pointed wisps, with a trailing tail of wisps
streaming down and back. No legs: it floats, the hem a hand's breadth off the ground."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix, hexc
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Rimewraith"
LOOT = [item("snowball", 1, 4), item("packed_ice", 0, 2), item("blue_ice", chance=0.15, looting=False, player_only=True)]
TAGS = ["undead", "freeze_immune_entity_types", "fall_damage_immune"]


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    """Shelf packer. pad=True keeps a transparent 1 px gutter round a cube's texture (cut-out planes
    would otherwise pick up a hairline of the neighbouring texels along their cut edges)."""
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0, pad=False):
        self.items.append((part, origin, size, paint, mirror, share, inflate, pad))

    def apply(self):
        def dims(size, pad):
            w, h, d = (int(math.ceil(s)) for s in size)
            return 2 * d + 2 * w + (2 if pad else 0), d + h + (1 if pad else 0)
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


def glow_px(c, x, y, base, glow):
    """A glowing pixel: a dim base colour plus the bright colour on the additive emissive layer."""
    if not c.inside(x, y):
        return
    c.set(x, y, base)
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), hexc(glow))


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
SNOW = ["#f2f8fb", "#eaf4f9", "#e2f0f7"]
SNOW_BLUE = ["#d8ecf7", "#cfe6f3"]
SNOW_SH = "#bcd9ea"
SNOW_DK = "#a3c6dc"
DARK = ["#0e1a26", "#122130", "#142434"]
DARK_RIM = "#2a4256"
ICE = ["#5aa9d6", "#52a2d1", "#4b9acb"]
ICE_DK = ["#3f8fc0", "#3784b6"]
ICE_LT = "#8cc8ea"
ICE_HI = "#c6e7f7"
CRACK = "#eef9fe"
CORE = ["#24516e", "#285a79"]
CORE_GLOW = "#bff4ff"
CORE_GLOW_DIM = "#4fa6c4"
EYE_BASE = "#1a3a4a"
EYE_GLOW = "#7fe6ff"
EYE_CORE = "#c8f6ff"
ROBE = ["#e8f2f8", "#e1edf5", "#d9e8f2"]
ROBE_MID = ["#cfe2ee", "#c7dcea"]
ROBE_SH = ["#b4d0e2", "#aac9dd"]
ROBE_DK = "#8fb3cc"
CLAW = ["#e6f5fc", "#d6eef8"]
CLAW_SH = "#9fd3ec"


# -- snow (hood, mantle) -----------------------------------------------------------------------------
def snow(c, x, y, grad=0.25):
    """Packed snow: near-white noise with a few blue pixels; sides fall to a pale blue shadow."""
    col = c.pick(SNOW)
    r = c.rng.random()
    if r < 0.12:
        col = c.pick(SNOW_BLUE)
    elif r < 0.15:
        col = "#ffffff"
    if c.face in SIDES and c.h > 1:
        t = y / (c.h - 1)
        if t > 0.55:
            col = mix(col, SNOW_SH, (t - 0.55) * grad * 4)
    elif c.face == "bottom":
        col = mix(col, SNOW_DK, 0.6)
    return col


def snow_paint(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, snow(c, x, y))


def dark(c, x, y):
    return c.pick(DARK)


def hood_wall(c):
    """A side wall of the cowl (painted as the right wall, mirrored for the left): snow outside, the
    inner face ('left') falls from a frosted rim at the front into darkness."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "left":                          # inner face, column 0 at the front
                i = fx(c, x)
                col = c.pick(DARK)
                if i == 0:
                    col = mix(SNOW_SH, DARK_RIM, 0.5)
                elif i == 1:
                    col = DARK_RIM
                elif i == 2:
                    col = mix(DARK_RIM, DARK[0], 0.55)
                c.set(x, y, col)
            elif c.face == "front":                       # the rim of the opening
                col = snow(c, x, y, grad=0.1)
                if x == c.w - 1:                          # inner column, in the cowl's shadow
                    col = mix(col, SNOW_SH, 0.6)
                c.set(x, y, col)
            else:
                c.set(x, y, snow(c, x, y))
    if c.face == "right":                                 # a fold running down the outside
        for y in range(1, c.h):
            c.set(fx(c, 3 + (y // 3) % 2), y, mix(c.get(fx(c, 3 + (y // 3) % 2), y), SNOW_SH, 0.6))


def hood_top(c):
    """The crown of the cowl: snow on top and outside, the ceiling inside dark, with a lit brim."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "bottom":                        # row h-1 is the front (the brim)
                f = c.h - 1 - y
                if f == 0:
                    col = mix(c.pick(SNOW_BLUE), SNOW_SH, 0.5)
                elif f == 1:
                    col = DARK_RIM
                else:
                    col = c.pick(DARK)
                c.set(x, y, col)
            elif c.face == "top":
                col = c.pick(SNOW)
                if c.rng.random() < 0.1:
                    col = c.pick(SNOW_BLUE)
                c.set(x, y, col)
            else:
                c.set(x, y, snow(c, x, y, grad=0.15))
    if c.face == "front":                                 # the brim's drooping edge
        for x in range(c.w):
            if x % 3 == 1:
                c.set(x, c.h - 1, SNOW_SH)


FACE_EYES = (((0, 3), EYE_GLOW), ((1, 3), EYE_CORE), ((1, 4), None),
             ((5, 3), EYE_GLOW), ((4, 3), EYE_CORE), ((4, 4), None))


def hood_face(c):
    """The back of the cowl. Front face: the darkness, with two slanted glowing eyes and the faint
    frost-white jaw of something under them."""
    if c.face != "front":
        for y in range(c.h):
            for x in range(c.w):
                col = snow(c, x, y) if c.face != "top" else c.pick(DARK)
                if c.face == "back" and x in (1, c.w - 2) and y > 1:
                    col = mix(col, SNOW_SH, 0.65)         # folds where the cowl gathers
                c.set(x, y, col)
        return
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(DARK)
            if y == 0:
                col = shade(DARK[0], 0.85)
            c.set(x, y, col)
    for (x, y), g in FACE_EYES:
        if g is None:                                     # a dim glint under the inner corner
            glow_px(c, x, y, "#132a36", "#1f5a6e")
        else:
            glow_px(c, x, y, EYE_BASE, g)
    for x in range(1, c.w - 1):                           # a jaw of frost in the shadow
        c.set(x, 6, "#2a4458" if x % 2 else "#18293a")
    c.set(2, 7, "#1d3346")
    c.set(3, 7, "#1d3346")


def hood_peak(c):
    """The drooping point at the front of the cowl: snow, shadowed underneath."""
    for y in range(c.h):
        for x in range(c.w):
            col = snow(c, x, y, grad=0.3)
            if c.face == "bottom":
                col = mix(SNOW_SH, DARK_RIM, 0.4)
            c.set(x, y, col)


# -- torso -------------------------------------------------------------------------------------------
def ice(c, x, y, top=1.1):
    col = c.pick(ICE)
    if c.rng.random() < 0.15:
        col = c.pick(ICE_DK)
    if c.face == "top":
        col = mix(col, ICE_LT, 0.45)
    elif c.face == "bottom":
        col = c.pick(ICE_DK)
    elif c.face in SIDES and c.h > 2:
        col = shade(col, 1.05 - 0.15 * y / (c.h - 1))
    return col


def cracks(c, n):
    """Short white frost cracks: a few 2-3 px zigzags."""
    for _ in range(n):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        for i in range(c.rng.randint(2, 3)):
            if c.inside(x, y):
                c.set(x, y, CRACK)
            x += c.rng.choice((-1, 1))
            y += 1


def rib(c):
    for y in range(c.h):
        for x in range(c.w):
            col = ice(c, x, y)
            if c.face in SIDES and c.rng.random() < 0.25:
                col = mix(col, ICE_LT, 0.5)
            c.set(x, y, col)
    if c.face in ("front", "back", "left", "right"):
        for x in range(c.w):
            if c.rng.random() < 0.2:
                c.set(x, 0, CRACK)
    if c.face == "top":
        cracks(c, 2)


def core(c):
    """The heart behind the ribs, seen through the gaps: dim blue with a pale glow in the middle
    (rows 0, 2, 4 and 6 of the front show between the ribs)."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(CORE))
    if c.face == "front":
        mid = (c.w // 2 - 1, c.w // 2)
        for y in (2, 4):
            for x in mid:
                glow_px(c, x, y, "#2c6a88", CORE_GLOW)
            glow_px(c, mid[0] - 1, y, "#24516e", CORE_GLOW_DIM)
            glow_px(c, mid[1] + 1, y, "#24516e", CORE_GLOW_DIM)
        for y in (0, 6):
            for x in mid:
                glow_px(c, x, y, "#24516e", CORE_GLOW_DIM)


def spine(c):
    for y in range(c.h):
        for x in range(c.w):
            col = ice(c, x, y)
            if y % 2 == 0:
                col = mix(col, ICE_LT, 0.45)              # vertebrae
            c.set(x, y, col)


def sternum(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(ice(c, x, y), ICE_LT, 0.35))
    if c.face == "front":
        cracks(c, 1)


def sash(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SNOW_BLUE)
            if c.face in SIDES and (x + y) % 4 == 0:
                col = SNOW_SH
            if c.face == "bottom":
                col = SNOW_DK
            c.set(x, y, col)
    if c.face == "front":                                 # a knot of frost at the front
        c.set(c.w // 2, 0, "#ffffff")
        c.set(c.w // 2 - 1, 0, SNOW[0])


def mantle(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, snow(c, x, y, grad=0.35))
    if c.face in SIDES:                                   # frost hanging off the lower edge
        for x in range(c.w):
            if hsh(x, 5, c.w) < 0.35:
                c.set(x, c.h - 1, ICE_HI)


# -- robe --------------------------------------------------------------------------------------------
def robe_px(c, x, y, ytop, span):
    """Frost-white cloth: vertical folds every 3 columns, shading toward the hem by world height."""
    col = c.pick(ROBE)
    if c.rng.random() < 0.1:
        col = c.pick(ROBE_MID)
    if c.face in SIDES:
        if x % 3 == 2:
            col = c.pick(ROBE_SH)
        elif x % 3 == 0:
            col = mix(col, "#f6fbfd", 0.4)
        t = (ytop + y) / span
        col = mix(col, ROBE_DK, max(0.0, t - 0.45) * 0.7)
    elif c.face == "top":
        col = c.pick(ROBE_MID)
    else:
        col = ROBE_DK
    return col


def robe_paint(ytop, span):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, robe_px(c, x, y, ytop, span))
        for _ in range(max(1, c.w * c.h // 30)):          # frost glints in the weave
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, "#ffffff")
    return p


def void(c):
    """The darkness inside the hollow robe."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(DARK))


def wisps(seed, long_every=3, stub=3):
    """A tattered hem on a flat plane: every few columns a long wisp tapering to a single-pixel
    point, ragged short columns between. A pure function of position so both faces match."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                u = c.w - 1 - x if c.face in ("back", "right") else x
                k = (u + seed) % long_every
                if k == 0:
                    length = c.h - int(hsh(u, seed) * 2)
                else:
                    length = max(1, c.h - stub - int(hsh(u, seed, 3) * 3))
                if y >= length:
                    c.clear(x, y)
                    continue
                r = hsh(u, y, seed)
                col = ROBE[int(r * 3)] if r < 0.8 else ROBE_MID[int(r * 7) % 2]
                if (u + seed) % 3 == 2:
                    col = ROBE_SH[int(r * 2)]
                t = y / max(1, c.h - 1)
                col = mix(col, ROBE_DK, 0.45 * t)
                if y == length - 1:
                    col = mix(col, "#f6fbfd", 0.55)       # frosted tips
                c.set(x, y, col)
    return p


# -- arms --------------------------------------------------------------------------------------------
def arm(c):
    for y in range(c.h):
        for x in range(c.w):
            col = ice(c, x, y)
            if c.face in SIDES and c.h > 2 and y > c.h * 0.6:
                col = mix(col, ICE_LT, 0.25)              # paler, frostier toward the hand
            c.set(x, y, col)
    if c.face in ("front", "right"):
        cracks(c, 1)
    if c.face in SIDES:                                   # a frosted joint at the elbow
        for x in range(c.w):
            c.set(x, 6, ICE_LT)


def hand(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(ice(c, x, y), ICE_HI, 0.35))


def claw(c):
    """Long pale icicle fingers: bright on the lit side, a blue shadow on the other."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CLAW)
            if c.face in ("back", "left") or (c.face in SIDES and y == c.h - 1):
                col = mix(col, CLAW_SH, 0.5)
            c.set(x, y, col)


def claw_tip(c):
    c.noise(["#ffffff", "#eef9fe"])
    if c.face in ("back", "left"):
        c.fill(mix(CLAW[1], CLAW_SH, 0.4))


def spur(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, ICE_LT if c.face != "bottom" else ICE[0])
    if c.face == "back":
        c.fill(ICE_HI)


# -- crystals ----------------------------------------------------------------------------------------
def crystal(c):
    """Glacial crystal shaft: lit edge column, a darker side, pale toward the tip (row 0 is the top
    on the side faces)."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(ICE)
            if c.face in ("front", "right"):
                col = mix(col, ICE_LT, 0.35)
            elif c.face in ("back", "left"):
                col = c.pick(ICE_DK)
            if c.face in SIDES and c.h > 1:
                col = mix(col, ICE_HI, 0.5 * (1 - y / (c.h - 1)) ** 2)
            if c.face == "top":
                col = ICE_HI
            c.set(x, y, col)
    if c.face in ("front", "right") and c.w > 1:
        for y in range(c.h):
            c.set(0, y, mix(c.get(0, y), CRACK, 0.6))     # the bright facet edge


def crystal_tip(c):
    for y in range(c.h):
        for x in range(c.w):
            col = ICE_HI if c.face in ("front", "right", "top") else ICE_LT
            if y == 0 or c.face == "top":
                col = "#ffffff"
            c.set(x, y, col)


def add_crystal(pk, parent, name, pivot, rot, h, w=2, t=3):
    """A jagged crystal growing from its pivot along local -y: a shaft and a thinner pointed tip."""
    cr = parent.part(name, pivot, rot)
    pk.add(cr, (-w / 2, -h, -w / 2), (w, h, w), faces(crystal), share=f"cry{w}_{h}")
    pk.add(cr, (-0.5, -h - t + 1, -0.5), (1, t, 1), faces(crystal_tip), share=f"tip{t}", inflate=-0.15)
    return cr


def build():
    m = Model("rimewraith", 128, 64, seed=8484)
    pk = Pack(m)

    # body: pivot at the chest/waist (world y 6). Snow mantle y -2..1; three ice rib hoops y 2-3,
    # 4-5, 6-7 round a glowing core (y 1-8) with a spine behind and a sternum in front; a frosted
    # sash at the waist (y 7.5-8.5) where the robe hangs from.
    body = m.part("body", (0, 6, 0))
    pk.add(body, (-7, -8, -3.5), (14, 3, 7), faces(mantle))
    for i, y in enumerate((2, 4, 6)):
        pk.add(body, (-4, y - 6, -2.5), (8, 1, 5), faces(rib), share="rib")
    pk.add(body, (-3, -5, -1.5), (6, 7, 3), faces(core))
    pk.add(body, (-1, -5, 1), (2, 7, 2), faces(spine))
    pk.add(body, (-1, -5, -3), (2, 5, 1), faces(sternum))
    pk.add(body, (-4.5, 1.5, -3), (9, 1, 6), faces(sash))

    # head: the cowl, pivot at the neck (world y -2). Crown y -11..-9 with a 1 px brim, side walls
    # and the back of the hood round a 6 x 8 opening 3 px deep; the darkness and the eyes are on
    # the front of the back block.
    head = body.part("head", (0, -8, 0))
    pk.add(head, (-5, -9, -6), (10, 2, 11), faces(hood_top))
    for sx in (-1, 1):
        pk.add(head, (-5 if sx < 0 else 3, -7, -5), (2, 8, 10), None if sx > 0 else faces(hood_wall),
               mirror=sx > 0, share="hood_wall")
    pk.add(head, (-3, -7, -2), (6, 8, 7), faces(hood_face))
    pk.add(head, (-4, -10, -4.5), (8, 1, 9), faces(hood_top))                 # rounded crown (y -12)
    pk.add(head, (-1.5, -9.5, -7), (3, 3, 2), faces(hood_peak))               # the cowl's peak
    # the crown of icicles growing out of the back of the hood, raking back
    for name, pivot, rot, h, w, t in (
            ("crown1", (-2.5, -8, 3.5), (-0.5, 0, -0.3), 6, 2, 3),
            ("crown2", (1.5, -8.5, 3.5), (-0.4, 0, 0.25), 7, 2, 3),
            ("crown3", (0, -7, 4.5), (-0.95, 0, 0.05), 5, 2, 2),
            ("crown4", (-4, -6, 3), (-0.6, 0, -0.75), 4, 1, 2),
            ("crown5", (4, -6.5, 3), (-0.55, 0, 0.8), 4, 1, 2)):
        add_crystal(pk, head, name, pivot, rot, h, w, t)

    # shoulder crystals, jutting up and out of the mantle
    for name, pivot, rot, h, w, t in (
            ("shard_r1", (-5, -8, 0.5), (0.15, 0, -0.5), 6, 2, 3),
            ("shard_r2", (-5.5, -8, 2.5), (-0.35, 0, -0.95), 4, 2, 2),
            ("shard_r3", (-4.5, -8, -2), (0.4, 0, -0.3), 3, 1, 2),
            ("shard_l1", (5, -8, 0), (0.1, 0, 0.55), 7, 2, 3),
            ("shard_l2", (5.5, -8, 2.5), (-0.4, 0, 0.9), 4, 2, 2),
            ("shard_l3", (4.5, -8, -2), (0.35, 0, 0.25), 3, 1, 2)):
        add_crystal(pk, body, name, pivot, rot, h, w, t)

    # arms: pivot at the shoulders (world y -0.5), hanging down, a little forward and out.
    # Arm y -1..11, hand 11..13, icicle fingers 13..17 with pointed tips; a spur at the elbow.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        a = body.part(side + "_arm", (6.5 * sx, -6, 0), (-0.15, 0, -0.12 * sx))
        pk.add(a, (-1, -1, -1), (2, 12, 2), None if left else faces(arm), mirror=left, share="arm")
        pk.add(a, (-0.5, 5, 1), (1, 1, 3), faces(spur), share="spur")
        pk.add(a, (-1.5, 11, -1.5), (3, 2, 3), None if left else faces(hand), mirror=left, share="hand")
        for (x, z, length) in ((-1.5, -1.5, 5), (0.5, -1.5, 5), (-0.5, 0.5, 3)):
            fxo = -x - 1 if left else x                   # mirror the finger across the arm
            pk.add(a, (fxo, 13, z), (1, length, 1), faces(claw), share=f"claw{length}")
            pk.add(a, (fxo, 12.5 + length, z), (1, 2, 1), faces(claw_tip), share="claw_tip", inflate=-0.2)

    # robe: pivot at the waist (world y 8). Upper robe y 8.5-14.5, the flared lower robe y 14-20
    # (hollow, darkness inside), and four tattered hem planes flaring out from y 18 to the wisp tips
    # near y 24. robe_tail: long wisps streaming down and back.
    robe = body.part("robe", (0, 2, 0))
    pk.add(robe, (-5.5, 0.5, -3.5), (11, 6, 7), faces(robe_paint(0, 12), bottom=None))
    pk.add(robe, (-6.5, 6, -4.5), (13, 6, 9), faces(robe_paint(6, 12), bottom=None))
    pk.add(robe, (-5.5, 6.5, -3.5), (11, 5, 7), faces(void))
    for name, pivot, yaw, w, seed in (("hem_front", (0, 10, -4.75), 0.0, 13, 0),
                                      ("hem_right", (-6.75, 10, 0), math.pi / 2, 9, 1),
                                      ("hem_back", (0, 10, 4.75), math.pi, 13, 2),
                                      ("hem_left", (6.75, 10, 0), -math.pi / 2, 9, 3)):
        hm = robe.part(name, pivot, (-0.1 if w > 10 else 0.0, round(yaw, 5), 0))
        pk.add(hm, (-w / 2, 0, 0), (w, 6, 0), faces(wisps(seed)), share=name, pad=True)
    # robe_tail: a fan of long wisps streaming down and back from the back of the robe: a centre
    # sheet and two side sheets turned outward (so the fan shows from the sides too)
    tail = robe.part("robe_tail", (0, 7, 4.75), (0.4, 0, 0))
    pk.add(tail, (-3, 0, 0), (6, 11, 0), faces(wisps(5, long_every=2, stub=4)), share="tail_c", pad=True)
    for side, sx in (("right", -1), ("left", 1)):
        tw = tail.part(f"robe_tail_{side}", (2.5 * sx, 0, 0.25), (0.08, -0.5 * sx, 0.12 * sx))
        pk.add(tw, (-2.5, 0, 0), (5, 9, 0), faces(wisps(7 + sx, long_every=2, stub=3)), share=f"tail_{side}",
               pad=True)

    pk.apply()
    m.save()
    spawn_egg("rimewraith", "#d8ecf7", "#5aa9d6", accent="#7fe6ff")


if __name__ == "__main__":
    build()

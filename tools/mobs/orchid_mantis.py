"""Orchid Mantis: a giant orchid mantis, about knee-high. A pearly white body blushing to rose pink,
four walking legs with broad petal-shaped lobes, an abdomen curled up like a petal, a triangular head
with two big green compound eyes and fine antennae, spiked raptorial forelegs folded under its chest,
and pink wings folded flat on its back (the hindwings hide a green eye-spot for the threat display).

From above and at a distance it should read as a pink-white blossom: the four lobes splay round the
body like petals and the abdomen curls up behind like a lip petal. Up close it is all mantis.
Petal lobes, wings, the abdomen flange and the foreleg spines are zero-thickness planes painted with
pure functions of (x, y), so both faces of each plane match pixel for pixel. The threat display
(raised wings, fanned hindwings with their eye-spots facing forward) is posed by the model code."""
import math
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import item

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Orchid Mantis"
LOOT = [item("pink_petals", 1, 3)]
TAGS = ["arthropod", "fall_damage_immune"]


# -- texture packing: every cube gets a box with a 1 px empty border (cutout planes need it) ------------
class Pack:
    def __init__(self, model, margin=1):
        self.m, self.items, self.margin = model, [], margin

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0):
        self.items.append((part, origin, size, paint, mirror, share, inflate))

    def apply(self):
        mg = self.margin

        def dims(size):
            w, h, d = (int(math.ceil(s)) for s in size)
            return 2 * d + 2 * w + 2 * mg, d + h + 2 * mg
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
                    keys[k] = (s[2] + mg, s[0] + mg)
                    s[2] += w
                    break
            else:
                if y_next + h > self.m.tex_h or w > self.m.tex_w:
                    raise ValueError(f"{self.m.id}: texture too small for {k} {w}x{h}")
                shelves.append([y_next, h, w])
                keys[k] = (mg, y_next + mg)
                y_next += h
        for i, (part, origin, size, paint, mirror, share, inflate) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, mirror=mirror, inflate=inflate)


# -- palette -------------------------------------------------------------------------------------------
PEARL = ["#fbf5f6", "#f8f0f2", "#faf3f5", "#f5ecef"]
SHEEN = ["#f3ebf8", "#fdfafb", "#eef5f3"]           # pearly glints: lilac, white, a breath of mint
BLUSH = ["#f6d4e0", "#f3c8d7", "#f5cedb"]
PINK = ["#eeb0c6", "#eaa4bd", "#ecaac1"]
ROSE = "#d97c9d"
ROSE_DK = "#bd5d81"
ROSE_DEEP = "#9a4767"
UNDER = ["#e9b5c7", "#e4abc0", "#e7b0c4"]

EYE_LT = "#bfe98f"
EYE = "#8fd267"
EYE_DK = "#5fa84a"
EYE_RIM = "#4c8a3d"
PUPIL = "#2c5a2b"
GLINT = "#f6ffec"

SIDES = ("front", "back", "left", "right")


def _h(x, y, salt):
    """Deterministic noise in 0..1 (planes must paint both faces identically)."""
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


def pick(pal, x, y, salt):
    return pal[int(_h(x, y, salt) * len(pal)) % len(pal)]


# -- solid painters ----------------------------------------------------------------------------------
def pearl(blush_from=0.45, top=1.02, belly=None, sheen=0.08):
    """Pearly white that blushes pink toward the underside; a darker last row, the odd pearly glint."""
    belly = belly or UNDER

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(PEARL)
                if c.face in SIDES:
                    t = y / max(1, c.h - 1)
                    if t > blush_from:
                        col = mix(col, c.pick(BLUSH), min(1.0, (t - blush_from) / max(0.01, 1 - blush_from)) * 0.9)
                    if y == c.h - 1 and c.h > 1:
                        col = mix(col, c.pick(PINK), 0.55)
                    col = shade(col, 1.01 - 0.05 * t)
                elif c.face == "top":
                    col = shade(col, top)
                elif c.face == "bottom":
                    col = c.pick(belly)
                if c.face != "bottom" and c.rng.random() < sheen:
                    col = c.pick(SHEEN)
                c.set(x, y, col)
    return p


def thorax_paint(c):
    pearl()(c)
    if c.face == "top":
        for y in range(c.h):                      # faint rose midline down the back
            c.set(c.w // 2 - 1, y, mix(c.get(c.w // 2 - 1, y), PINK[0], 0.35))
        for x in range(c.w):                      # the meso/metathorax join
            c.set(x, c.h // 2, mix(c.get(x, c.h // 2), BLUSH[1], 0.6))
    elif c.face in ("left", "right"):
        for y in range(c.h):
            c.set(c.w // 2, y, mix(c.get(c.w // 2, y), BLUSH[1], 0.5))


def prothorax_paint(c):
    pearl(blush_from=0.3)(c)
    if c.face == "top":
        for y in range(c.h):
            c.set(c.w // 2, y, mix(c.get(c.w // 2, y), PINK[1], 0.4))
    if c.face in ("left", "right"):              # fine rose edge along the flanks
        for x in range(c.w):
            c.set(x, 0, mix(c.get(x, 0), PINK[0], 0.3))


def collar_paint(c):
    pearl(blush_from=0.2)(c)
    if c.face in ("left", "right", "front", "back"):
        for x in range(c.w):
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), ROSE, 0.4))


def head_paint(c):
    pearl(blush_from=0.5, top=1.04)(c)
    if c.face == "front":
        cx = c.w // 2
        # the frons: a little rose shield between the eyes, and three tiny ocelli above it
        c.set(cx - 1, c.h - 1, mix(c.get(cx - 1, c.h - 1), PINK[0], 0.6))
        c.set(cx, c.h - 1, mix(c.get(cx, c.h - 1), PINK[0], 0.6))
        c.set(cx - 1, 0, "#e7a0b9")
        c.set(cx, 0, "#e7a0b9")
        c.set(cx - 1, 1, shade(PEARL[0], 1.02))
        c.set(cx, 1, shade(PEARL[0], 1.02))


def face_lower(c):
    pearl(blush_from=0.0)(c)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), ROSE, 0.45))


def mouth(c):
    c.fill(ROSE_DK)
    if c.face == "front":
        c.set(0, 0, ROSE)
    if c.face == "bottom":
        c.fill(ROSE_DEEP)


def crown(c):
    pearl(blush_from=0.6, top=1.05)(c)
    if c.face == "front" and c.w >= 2:
        c.set(c.w // 2, 0, "#fffafc")


def eye(c):
    """A big green compound eye: pale on top, deepening below, a white glint up at the outer corner and
    a dark pseudopupil low on the inner side, so it seems to watch you."""
    for y in range(c.h):
        for x in range(c.w):
            t = y / max(1, c.h - 1)
            col = mix(EYE_LT, EYE, min(1.0, t * 1.6)) if t < 0.6 else mix(EYE, EYE_DK, (t - 0.6) / 0.4)
            if _h(x, y, 77) < 0.2:
                col = shade(col, 1.05)        # facets
            c.set(x, y, col)
    if c.face == "top":
        c.fill(EYE_LT)
    elif c.face == "bottom":
        c.fill(EYE_RIM)
    elif c.face == "front":
        # right eye's front face: column 0 is the outer edge, the last column faces the head
        c.set(0, 0, GLINT)
        c.set(c.w - 1, c.h - 2, PUPIL)
    elif c.face == "right":
        c.set(c.w - 1, 0, GLINT)                # the outer side: shine toward the front
        c.set(c.w - 1, 1, mix(EYE_LT, GLINT, 0.4))
        c.set(c.w // 2 - 1 if c.w > 1 else 0, c.h - 2, mix(PUPIL, EYE_DK, 0.4))
    elif c.face == "left":
        c.fill(EYE_DK)                          # against the head: barely seen
    elif c.face == "back":
        for x in range(c.w):
            c.set(x, c.h - 1, EYE_RIM)


def eye_tip(c):
    """The pointed top of each eye cone blushes pink, as on the real insect."""
    c.fill("#f4d3de" if c.face == "top" else "#a8dd7c")
    if c.face == "bottom":
        c.fill(EYE)


# -- limbs ---------------------------------------------------------------------------------------------
def leg_paint(c):
    for y in range(c.h):
        for x in range(c.w):
            t = y / max(1, c.h - 1)
            col = mix(c.pick(PEARL), c.pick(BLUSH), 0.35 + 0.45 * t) if c.face in SIDES else c.pick(BLUSH)
            c.set(x, y, col)
    if c.face in SIDES and c.h > 3:
        c.set(0, 0, mix(c.get(0, 0), ROSE, 0.35))            # the knee
        c.set(0, c.h - 1, ROSE)                                # the foot


def femur_paint(c):
    pearl(blush_from=0.35)(c)
    if c.face == "bottom":
        c.fill(BLUSH[1])


def foot_paint(c):
    c.fill(PINK[1])
    if c.face == "bottom":
        c.fill(ROSE)
    if c.face in ("right", "left", "front", "back"):
        c.set(0, 0, ROSE)


def coxa_paint(c):
    pearl(blush_from=0.4)(c)


def raptor_femur(c):
    """The spiked forefemur: pearl outside, a rose row of spines down its inner edge."""
    pearl(blush_from=0.25)(c)
    if c.face == "front":
        for y in range(1, c.h, 2):
            c.set(0, y, ROSE)
    elif c.face in ("left", "right"):
        edge = c.w - 1 if c.face == "right" else 0
        for y in range(1, c.h, 2):
            c.set(edge, y, mix(ROSE, PINK[0], 0.4))


def raptor_tibia(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(c.pick(BLUSH), c.pick(PINK), y / max(1, c.h - 1)))
    if c.face in SIDES:
        c.set(0, c.h - 1, ROSE)                    # the hooked tip
        if c.w > 1:
            c.set(c.w - 1, c.h - 1, ROSE)


def spine_plane(fn):
    """A vertical plane (x size 0) painted as fn(i, y), i counted from the plane's front edge."""
    def p(c):
        for y in range(c.h):
            for i in range(c.w):
                x = c.w - 1 - i if c.face == "right" else i
                col = fn(i, y, c.w, c.h)
                if col is None:
                    c.clear(x, y)
                else:
                    c.set(x, y, col)
    return p


def spines(i, y, w, h):
    # teeth hanging along the femur's front: alternating long (2 px) and short spines
    if i == w - 1:
        return ROSE_DK if y % 2 == 0 else None
    return None


def antenna_paint(c):
    """A fine pale hair that blushes rose toward its tip (the front end)."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face in ("top", "bottom"):
                t = 1.0 - y / max(1, c.h - 1)               # rows run from the back (base) to the tip
            elif c.face in ("right", "left"):
                t = (c.w - 1 - x if c.face == "right" else x) / max(1, c.w - 1)
                t = 1.0 - t
            else:
                t = 1.0 if c.face == "front" else 0.0
            c.set(x, y, mix("#f6e2e9", "#e294b0", t))


# -- planes: petal lobes, wings ------------------------------------------------------------------------
def petal(w, d, salt):
    """A femoral lobe: a broad rounded petal with the femur as its midrib (the middle row). Columns run
    from the knee (col 0, the outer end) to the hip. White along the midrib, blushing to pink, with a
    rose rim and faint veins fanning out."""
    mid = (d - 1) / 2.0

    def reach(x):
        u = x / max(1, w - 1)                       # 0 at the knee, 1 at the hip
        f = (u - 0.42) / 0.64
        return (d / 2.0) * math.sqrt(max(0.0, 1.0 - f * f)) + 0.3

    def inside(x, y):
        return 0 <= x < w and 0 <= y < d and abs(y - mid) < reach(x)

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if not inside(x, y):
                    c.clear(x, y)
                    continue
                r = abs(y - mid) / max(0.5, d / 2.0 - 0.5)      # 0 at the midrib, 1 at the rim
                col = mix(pick(PEARL, x, y, salt), pick(BLUSH, x, y, salt + 1), min(1.0, r * 1.1))
                if r > 0.6:
                    col = mix(col, pick(PINK, x, y, salt + 2), min(1.0, (r - 0.6) * 1.5))
                edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    col = mix(col, ROSE, 0.55)
                elif r < 0.3:
                    col = mix(col, "#fffbfc", 0.5)              # the pale midrib
                elif (x + int(round(abs(y - mid)))) % 3 == 0:
                    col = mix(col, "#efbccd", 0.4)              # veins fanning toward the rim
                elif _h(x, y, salt + 3) < 0.15:
                    col = shade(col, 1.04)
                c.set(x, y, col)
    return p


FORE_MASK = [          # row 0 = the wing's back (tip) end, last row = the root; col 0 = the hinge side
    "..ww.",
    ".wwww",
    "wwwww",
    "wwwww",
    "wwwww",
    "wwwww",
    "wwwww",
    "wwww.",
]

HIND_MASK = [
    "..ww.",
    ".wwww",
    "wwwww",
    "wwwww",
    "wwwww",
    "wwwww",
    "wwwww",
    "wwww.",
]
# the eye-spot on the hindwing: o = dark plum ring, g = green iris, d = deep green, h = glint,
# p = the pale halo round it
HIND_SPOT = {
    (1, 0): "p", (2, 0): "p", (3, 0): "p",
    (0, 1): "p", (1, 1): "o", (2, 1): "o", (3, 1): "o", (4, 1): "p",
    (0, 2): "o", (1, 2): "h", (2, 2): "g", (3, 2): "g", (4, 2): "o",
    (0, 3): "o", (1, 3): "g", (2, 3): "d", (3, 3): "g", (4, 3): "o",
    (0, 4): "p", (1, 4): "o", (2, 4): "o", (3, 4): "o", (4, 4): "p",
    (1, 5): "p", (2, 5): "p", (3, 5): "p",
}


def wing(mask, salt, spot=None, fore=True):
    """A folded wing plane. mask rows run from the tip (row 0) to the root; col 0 is the hinge side
    (the outer edge when folded). Forewing: pearly pink with a rose costal margin and one soft vein.
    Hindwing (seen only in the threat display): rose with radiating veins and the green eye-spot."""
    h, w = len(mask), len(mask[0])

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and mask[y][x] != "."

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if not solid(x, y):
                    c.clear(x, y)
                    continue
                r = _h(x, y, salt)
                t = y / max(1, h - 1)                       # 0 at the tip, 1 at the root
                edge = not all(solid(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if fore:
                    col = mix("#f7dde6", "#fbeef2", t * 0.8)          # blush at the tip, pearly at the root
                    col = shade(col, 1.0 + (r - 0.5) * 0.04)
                    if r < 0.1:
                        col = pick(SHEEN, x, y, salt)
                    if x == 0:
                        col = mix(col, ROSE, 0.3)                     # the rose costal margin
                    elif x == 2 and 0 < y < h - 1:
                        col = mix(col, "#efc3d2", 0.3)                # one soft vein
                    elif edge:
                        col = mix(col, PINK[0], 0.35)
                else:
                    col = mix("#eea6bf", "#f5c6d6", t * 0.7)
                    if (x + y) % 3 == 0:
                        col = mix(col, "#dc88a6", 0.35)               # radiating veins
                    if edge:
                        col = mix(col, ROSE, 0.5)
                k = (spot or {}).get((x, y))
                if k == "o":
                    col = "#5a2a43"
                elif k == "g":
                    col = "#71c65a"
                elif k == "d":
                    col = "#3f8c3b"
                elif k == "h":
                    col = "#e6ffd2"
                elif k == "p":
                    col = mix(col, "#fbe3ec", 0.7)
                c.set(x, y, col)
    return p


# -- abdomen -------------------------------------------------------------------------------------------
def abdomen_paint(c):
    """Broad petal-like segments: pearl on top with rose bands, pink underneath."""
    pearl(blush_from=0.0, belly=PINK)(c)
    if c.face == "top":
        for y in range(c.h):
            if y % 2 == 1:
                for x in range(c.w):
                    c.set(x, y, mix(c.get(x, y), BLUSH[0], 0.6))
        for y in range(c.h):
            c.set(c.w // 2, y, mix(c.get(c.w // 2, y), "#fffafc", 0.6))   # the pale keel
    elif c.face == "bottom":
        for y in range(c.h):
            if y % 2 == 0:
                for x in range(c.w):
                    c.set(x, y, mix(c.get(x, y), ROSE, 0.3))
    elif c.face in ("left", "right"):
        for x in range(c.w):
            if x % 2 == 1:
                for y in range(c.h):
                    c.set(x, y, mix(c.get(x, y), PINK[0], 0.4))


def abdomen_tip_paint(c):
    """The upturned end of the abdomen: pinker, like the lip of a petal, with a rose rim."""
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(BLUSH), c.pick(PINK), 0.35)
            if c.face == "top":
                col = mix(c.pick(PEARL), c.pick(BLUSH), 0.6)
            edge = x in (0, c.w - 1) or (c.face in ("top", "bottom", "back") and y in (0, c.h - 1))
            if edge and c.face != "front":
                col = mix(col, ROSE, 0.4)
            c.set(x, y, col)


def flange(w, d, salt):
    """The thin petal-edged flaps along the abdomen's sides (a plane under the wings)."""
    def inside(x, y):
        if x < 0 or x >= w or y < 0 or y >= d:
            return False
        if x in (0, w - 1) and y in (0, d - 1):
            return False
        return True

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if not inside(x, y):
                    c.clear(x, y)
                    continue
                col = mix(pick(BLUSH, x, y, salt), pick(PINK, x, y, salt + 1), 0.4)
                if x in (0, w - 1):
                    col = mix(col, ROSE, 0.45)
                c.set(x, y, col)
    return p


# -- geometry ------------------------------------------------------------------------------------------
def rot(v, r):
    """Rotate v by a part rotation (x, y, z), applied like ModelPart: Z * Y * X."""
    x, y, z = v
    rx, ry, rz = r
    cy_, sy_ = math.cos(rx), math.sin(rx)
    y, z = y * cy_ - z * sy_, y * sy_ + z * cy_
    c, s = math.cos(ry), math.sin(ry)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(rz), math.sin(rz)
    x, y = x * c - y * s, x * s + y * c
    return (x, y, z)


def world_bounds(m):
    """Model-space bounding box of every part's cubes (rest pose), for checking feet and height."""
    chain = {}

    def to_world(part, p):
        while part is not None:
            q = rot(p, part.rotation)
            p = (q[0] + part.pivot[0], q[1] + part.pivot[1], q[2] + part.pivot[2])
            part = part.parent
        return p

    out = {}
    for part in m.parts:
        pts = []
        for cb in part.cubes:
            (ox, oy, oz), (sx, sy, sz), g = cb.origin, cb.size, cb.inflate
            for dx in (ox - g, ox + sx + g):
                for dy in (oy - g, oy + sy + g):
                    for dz in (oz - g, oz + sz + g):
                        pts.append(to_world(part, (dx, dy, dz)))
        if pts:
            out[part.name] = tuple((min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3))
    return out


PRO_PIVOT = (0, -0.6, -1.5)
PRO_PITCH = -0.8
PRO_TIP = (0, -0.5, -5)       # the head's seat on the prothorax, in prothorax space


def build(report=False):
    m = Model("orchid_mantis", 64, 64, seed=5454)
    pk = Pack(m)

    # body = the thorax (where the walking legs join), pivot mid-body
    body = m.part("body", (0, 19, 0))
    pk.add(body, (-2, -1.5, -2), (4, 3, 6), faces(thorax_paint))

    # the prothorax: the long raised "neck" carrying the raptorial forelegs. The head is a child of
    # body sitting on the prothorax tip (so it turns about the vertical); the code moves its pivot
    # with the prothorax (OrchidMantisModel.TIP_Y / TIP_Z must match PRO_TIP here).
    pro = body.part("prothorax", PRO_PIVOT, (PRO_PITCH, 0, 0))
    pk.add(pro, (-1, -1, -5), (2, 2, 5), faces(prothorax_paint))
    pk.add(pro, (-1.5, -0.5, -4.6), (3, 1, 2), faces(collar_paint), inflate=0.05)

    # the head: a triangle, wide across the conical eyes, narrowing to the mouth
    tip = rot(PRO_TIP, (PRO_PITCH, 0, 0))
    head = body.part("head", (0, PRO_PIVOT[1] + tip[1], PRO_PIVOT[2] + tip[2]), (PRO_PITCH + 0.95, 0, 0))
    pk.add(head, (-2, -2, -1.5), (4, 2, 2), faces(head_paint))
    pk.add(head, (-1, 0, -1.4), (2, 1, 2), faces(face_lower))
    pk.add(head, (-0.5, 1, -1.3), (1, 1, 1), faces(mouth), inflate=-0.1)
    pk.add(head, (-1, -2.8, -1), (2, 1, 1), faces(crown))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        pk.add(head, (-3.2 if not left else 1.2, -2.5, -1.6), (2, 3, 2), None if left else faces(eye),
               mirror=left, share="eye")
        pk.add(head, (-3.2 if not left else 2.2, -3.5, -1.1), (1, 1, 1), None if left else faces(eye_tip),
               mirror=left, share="eye_tip")
        a = head.part(side + "_antenna", (0.6 * sx, -2.6, -1.2), (-0.75, -0.4 * sx, 0))
        pk.add(a, (-0.5, -0.5, -6), (1, 1, 6), None if left else faces(antenna_paint),
               mirror=left, share="antenna", inflate=-0.36)

        # raptorial foreleg: coxa (right_arm) > spiked femur (right_claw) > folded tibia (right_hook)
        arm = pro.part(side + "_arm", (0.85 * sx, 1.0, -3.8), (0.45, 0, 0.12 * -sx))
        pk.add(arm, (-0.5, 0, -0.5), (1, 3, 1), None if left else faces(coxa_paint), mirror=left, share="coxa")
        claw = arm.part(side + "_claw", (0, 3, 0), (0.6, 0, 0))
        pk.add(claw, (-0.5, -5, -0.5), (1, 5, 1), None if left else faces(raptor_femur), mirror=left,
               share="rfemur", inflate=0.12)
        pk.add(claw, (0, -5, -1.6), (0, 5, 1), None if left else faces(spine_plane(spines)), mirror=left,
               share="rspines")
        hook = claw.part(side + "_hook", (0, -5, -1), (0, 0, 0))
        pk.add(hook, (-0.5, 0, -0.5), (1, 4, 1), None if left else faces(raptor_tibia), mirror=left,
               share="rtibia", inflate=-0.05)

    # the abdomen: a broad flat petal, rising, its tip curled up
    ab = body.part("abdomen", (0, -0.8, 3.8), (0.15, 0, 0))
    pk.add(ab, (-3, 0, 0), (6, 2, 3), faces(abdomen_paint))
    pk.add(ab, (-4, 1, 0.5), (8, 0, 2), faces(flange(8, 2, 31)))
    tip = ab.part("abdomen_tip", (0, 0, 3), (0.35, 0, 0))
    pk.add(tip, (-3, 0, 0), (6, 2, 2), faces(abdomen_paint))
    pk.add(tip, (-2, 0.15, 2), (4, 2, 2), faces(abdomen_tip_paint), inflate=-0.15)
    curl = tip.part("abdomen_curl", (0, 0.2, 3.8), (0.45, 0, 0))
    pk.add(curl, (-1.5, 0, 0), (3, 1, 2), faces(abdomen_tip_paint), inflate=0.15)

    # wings: planes hinged at the thorax sides and folded inward over the back, the left pair on top;
    # the eye-spotted hindwing lies exactly under each forewing until the code flares them
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        fw = body.part(side + "_wing", (1.8 * sx, -1.7 - (0.25 if left else 0.0), -0.5), (0.2, 0, 0))
        pk.add(fw, (0 if not left else -5, 0, 0), (5, 0, 8), None if left else faces(wing(FORE_MASK, 41)),
               mirror=left, share="forewing")
        hw = fw.part(side + "_hindwing", (0, 0.12, 0), (0, 0, 0))
        pk.add(hw, (0 if not left else -5, 0, 0), (5, 0, 8), None if left else faces(wing(HIND_MASK, 43, HIND_SPOT, fore=False)),
               mirror=left, share="hindwing")

    # walking legs: femur out and up to a raised knee, its petal lobe (a child, <leg>_lobe, tilted up
    # and away from the body), then the tibia (a child, <leg>_lower) back down to the ground
    def leg(name, sx, z, yaw, raise_, splay, femur, lobe, tibia, cup, share, hip_y):
        left = sx > 0
        lg = body.part(name, (1.8 * sx, hip_y, z), (0, yaw * -sx, raise_ * -sx))
        pk.add(lg, (-femur if not left else 0, -0.5, -0.5), (femur, 1, 1), None if left else faces(femur_paint),
               mirror=left, share=share + "_femur", inflate=-0.1)
        lw, ld = lobe
        lp = lg.part(name + "_lobe", (0, 0, 0), (cup, 0, 0))
        pk.add(lp, (-lw - 0.2 if not left else 0.2, 0, -ld / 2.0), (lw, 0, ld),
               None if left else faces(petal(lw, ld, 50 + femur)), mirror=left, share=share + "_lobe")
        low = lg.part(name + "_lower", (femur * sx, 0, 0), (0, 0, (raise_ - splay) * sx))
        pk.add(low, (-0.5, -0.3, -0.5), (1, tibia, 1), None if left else faces(leg_paint), mirror=left,
               share=share + "_tibia", inflate=-0.2)
        pk.add(low, (-1.3 if not left else -0.7, tibia - 0.9, -0.5), (2, 1, 1),
               None if left else faces(foot_paint), mirror=left, share=share + "_foot", inflate=-0.25)
        return lg

    for side, sx in (("right", -1), ("left", 1)):
        leg(side + "_leg1", sx, -0.7, -0.6, 0.5, 0.12, 4, (5, 6), 6, -0.3, "mid", 0.87)
        leg(side + "_leg2", sx, 2.7, 0.7, 0.45, 0.15, 5, (6, 7), 6, 0.3, "hind", 0.96)

    pk.apply()
    m.save()
    spawn_egg("orchid_mantis", "#f7e4eb", "#e99db8", accent="#7fcf62")
    if report:
        for name, b in world_bounds(m).items():
            print(f"{name:16s} x {b[0][0]:6.2f}..{b[0][1]:6.2f}  y {b[1][0]:6.2f}..{b[1][1]:6.2f}  z {b[2][0]:6.2f}..{b[2][1]:6.2f}")


if __name__ == "__main__":
    build(report=True)

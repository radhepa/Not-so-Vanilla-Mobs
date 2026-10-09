"""Vulture: a big, scruffy desert vulture that is always on the wing. A chunky sooty-brown body flying
level, broad plank wings spread flat for gliding (lighter brown edges on the coverts, darker flight
feathers with a serrated trailing edge) that end in four separated "finger" primaries (cut-out gaps),
and a short wedge tail. A bald, wrinkled, pinkish-red head on a bare pinkish-grey neck pokes out of a
big fluffy cream ruff; it has a heavy ivory hooked beak with a dark tip and small dark eyes with a
pale ring. Grey-pink scaly legs with dark talons are tucked back under the tail.
The wings are thin cubes plus zero-thickness feather planes; the code flaps them around z
(+zRot raises the right wing, -zRot the left one)."""
import math
import os
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Vulture"
LOOT = [item("feather", 0, 2), item("bone", 0, 1)]
TAGS = ["fall_damage_immune"]

# Debug only: VULTURE_POSE=flap previews the wings raised mid-beat, =down lowered.
POSE = os.environ.get("VULTURE_POSE", "")


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
            part.cube(keys[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def _h(x, y, salt):
    """A stable random number per pixel, so the top and bottom of a feather plane match exactly."""
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
PLUME = ["#3b2a22", "#4a3528", "#2e211b", "#423026"]
PLUME_DK = ["#2e211b", "#281d18", "#33251e"]
EDGE = ["#6e5038", "#7a5a40", "#684b33"]          # light edges of the coverts
EDGE_LT = ["#8a6a4c", "#937355"]
FLIGHT = ["#2e211b", "#2a1e19", "#33251f", "#30231c"]
FLIGHT_EDGE = "#4a382c"
UNDER = ["#56402f", "#5e4735", "#503c2c"]          # underwing coverts
UNDER_PALE = ["#9c8566", "#a88f6e", "#927b5d"]
FLIGHT_UNDER = ["#3e3431", "#463b37", "#383030"]   # flight feathers seen from below: sooty grey
RUFF = ["#e6dccb", "#ece3d4", "#ddd2bf"]
RUFF_SH = ["#cfc3ad", "#c6b9a2"]
RUFF_DK = "#ab9e86"
SKIN = ["#c45a4a", "#d97a66", "#cd6855", "#d3705d"]
WRINKLE = "#a1453a"
WRINKLE_DK = "#86362d"
DOWN = ["#e9dfd2", "#d8cdbf"]                      # sparse pale fuzz on the crown
NECK = ["#b9958f", "#ae8a84", "#c29f98"]
NECK_DK = "#94736d"
BEAK = ["#d9c48a", "#e0cd96", "#d2bc80"]
BEAK_DK = "#b49d65"
CERE = ["#8a7a72", "#7f6f68"]
HOOK = ["#4b4745", "#3e3a38"]
HOOK_DK = "#2b2827"
EYE = "#140e0c"
EYE_RING = "#f0e2c8"
LEG = ["#9c8682", "#917b77", "#a58f8a"]
LEG_DK = "#76605c"
TALON = ["#2a2422", "#352d2a"]


# -- body plumage --------------------------------------------------------------------------------------
def plumage(grad=0.3, top=1.06, bottom=0.8, scallop=True):
    """Sooty-brown feathers. Side faces darken downward; the top gets staggered rows of feathers with
    light back edges (row 0 of a top face is the back edge, where feather tips point)."""
    def p(c):
        for y in range(c.h):
            if c.face == "top":
                f = top
            elif c.face == "bottom":
                f = bottom
            else:
                f = 1.04 - grad * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(PLUME), f))
        if not scallop:
            return
        if c.face == "top":
            for y in range(0, c.h, 3):
                off = (y // 3) % 2 * 2
                for x in range(c.w):
                    k = (x + off) % 4
                    if k in (0, 1) and c.rng.random() < 0.75:
                        c.set(x, y, shade(c.pick(EDGE), 0.92))
                    elif k == 2 and c.inside(x, y + 1):
                        c.set(x, y + 1, shade(c.pick(PLUME_DK), 1.0))
        elif c.face in ("left", "right"):
            # flank feathers lie back along the body: short pale streaks along their edges
            for _ in range(c.w * c.h // 9):
                x, y = c.rng.randrange(c.w), c.rng.randrange(max(1, c.h - 1))
                c.set(x, y, shade(c.pick(EDGE), 0.85 - 0.2 * y / max(1, c.h - 1)))
        elif c.face == "bottom":
            for _ in range(c.w * c.h // 8):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, shade(c.pick(PLUME_DK), 0.85))
    return p


def belly(c):
    plumage(bottom=0.74)(c)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(PLUME), 0.72))


# -- ruff ------------------------------------------------------------------------------------------
def ruff_core(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(RUFF)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.02 - 0.12 * y / (c.h - 1))
                if y == c.h - 1:
                    col = c.pick(RUFF_SH)
            elif c.face == "bottom":
                col = c.pick(RUFF_SH)
            c.set(x, y, col)
    for _ in range(c.w * c.h // 5):          # soft down: a darker dent under a lighter tuft
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        c.set(x, y, c.pick(RUFF_SH))
        if c.inside(x, y - 1):
            c.set(x, y - 1, shade(c.pick(RUFF), 1.04))
    if c.face == "front":                    # a shadowed hollow where the bare neck comes out
        cx = c.w // 2
        for x, y, col in ((cx - 1, 2, RUFF_SH[0]), (cx, 2, RUFF_SH[1]), (cx - 1, 3, RUFF_DK),
                          (cx, 3, RUFF_DK), (cx - 2, 3, RUFF_SH[0]), (cx + 1, 3, RUFF_SH[1])):
            c.set(x, y, col)
    elif c.face == "back":                   # the brown back plumage overlaps the bottom of the ruff
        for x in range(c.w):
            if c.rng.random() < 0.5:
                c.set(x, c.h - 1, c.pick(EDGE))


def ruff_shell(c):
    """An inflated shell over the ruff with most pixels cut out, so its outline looks fluffy: a
    thick fringe of tufts along the top edge, a ragged hem along the bottom, sparse fluff between."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face in SIDES:
                if y == 0:
                    keep = c.rng.random() < 0.7
                elif y == c.h - 1:
                    keep = (x + (c.face in ("left", "back"))) % 2 == 0 or c.rng.random() < 0.2
                else:
                    keep = c.rng.random() < 0.3
                if c.face in ("left", "right") and x == fx(c, c.w - 1) and y < c.h - 1:
                    keep = True                       # closed at the back: hides the gap behind the core
            elif c.face == "top":
                keep = y == 0 or c.rng.random() < (0.55 if y == c.h - 1 or x in (0, c.w - 1) else 0.35)
            else:
                keep = c.rng.random() < 0.3
            if not keep:
                c.clear(x, y)
                continue
            col = c.pick(RUFF)
            if c.face in SIDES:
                col = shade(col, 1.04 - 0.16 * y / max(1, c.h - 1))
                if y == c.h - 1:
                    col = c.pick(RUFF_SH)
            elif c.face == "bottom":
                col = c.pick(RUFF_SH)
            c.set(x, y, col)


# -- head and neck ----------------------------------------------------------------------------------
def wrinkled(c, top_down=True):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SKIN)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.03 - 0.1 * y / (c.h - 1))
            elif c.face == "bottom":
                col = shade(col, 0.86)
            c.set(x, y, col)
    # wrinkles: short darker dashes, offset row to row
    for y in range(c.h):
        for x in range(c.w):
            if (x + 2 * y) % 4 == 0 and c.rng.random() < 0.55:
                c.set(x, y, WRINKLE if c.rng.random() < 0.75 else WRINKLE_DK)
    if top_down and c.face == "top":
        for _ in range(3):
            c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(DOWN))


def head_side(c):
    wrinkled(c)
    e = fx(c, 1)
    c.set(e, 1, EYE)
    c.set(fx(c, 0), 1, EYE_RING)
    c.set(fx(c, 2), 1, EYE_RING)
    c.set(e, 0, shade(EYE_RING, 0.9))
    c.set(e, 2, shade(EYE_RING, 0.82))
    c.set(fx(c, 2), 0, WRINKLE_DK)                 # a heavy brow over the eye
    c.set(fx(c, 0), 0, WRINKLE)
    for y in range(c.h):                            # pale down creeping up the back of the head
        if c.rng.random() < 0.5:
            c.set(fx(c, c.w - 1), y, c.pick(DOWN))


def head_front(c):
    wrinkled(c)
    for x in (0, c.w - 1):                          # eyes peek round the corners
        c.set(x, 1, EYE_RING)
    c.set(1, 0, WRINKLE_DK); c.set(c.w - 2, 0, WRINKLE_DK)


def head_back(c):
    wrinkled(c)
    for x in range(c.w):
        if c.rng.random() < 0.6:
            c.set(x, c.rng.randrange(c.h), c.pick(DOWN))


def neck_paint(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(NECK)
            if c.face in SIDES and c.h > 1:
                col = mix(col, c.pick(SKIN), 0.35 * (1 - y / (c.h - 1)))   # pinker toward the head
            c.set(x, y, col)
    for _ in range(c.w * c.h // 6):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        c.set(x, y, NECK_DK if c.rng.random() < 0.6 else c.pick(DOWN))


def beak_upper(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BEAK)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.04 - 0.12 * y / (c.h - 1))
            elif c.face == "bottom":
                col = c.pick([BEAK_DK, shade(BEAK_DK, 0.92)])
            c.set(x, y, col)
    if c.face in ("left", "right"):                 # grey cere at the base, a nostril slit
        for y in range(c.h):
            c.set(fx(c, c.w - 1), y, c.pick(CERE))
        c.set(fx(c, c.w - 2), 0, shade(CERE[0], 0.8))
        c.set(fx(c, 0), c.h - 1, BEAK_DK)
    elif c.face == "top":
        for x in range(c.w):
            c.set(x, 0, c.pick(CERE))                # row 0 = back edge
        c.set(0, 1, shade(CERE[0], 0.75)); c.set(c.w - 1, 1, shade(CERE[0], 0.75))


def beak_hook(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(HOOK)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.08 - 0.25 * y / (c.h - 1))
            c.set(x, y, col)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, c.h - 1, HOOK_DK)
    if c.face == "front":                            # ivory ridge fading into the dark hook
        for x in range(c.w):
            c.set(x, 0, c.pick(BEAK))
            c.set(x, 1, mix(c.pick(BEAK), HOOK[0], 0.6))
    elif c.face == "top":
        c.noise([mix(b, HOOK[0], 0.3) for b in BEAK])
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, mix(BEAK[0], HOOK[0], 0.4))
    if c.face == "back":                             # the hook curls back under the upper bill
        for x in range(c.w):
            c.set(x, 0, mix(BEAK[0], HOOK[0], 0.5))


def beak_lower(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BEAK), 0.86))
    if c.face in ("left", "right"):
        c.set(fx(c, c.w - 1), 0, c.pick(CERE))
    if c.face == "top":
        c.noise(["#6e3530", "#7a3c35"])              # inside of the mouth


# -- wings -------------------------------------------------------------------------------------------
def wing_arm(c):
    """Leading edge of the inner wing (marginal coverts). Column 0 of top/bottom is the wing tip."""
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(UNDER)
                if y == 0 and c.rng.random() < 0.5:
                    col = c.pick(UNDER_PALE)
                c.set(x, y, col)
        return
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(PLUME)
            if c.face == "top":
                col = shade(col, 1.05 if y == 0 else 0.9)    # front row darker (the leading edge)
                if y == 0 and (x % 3 == 1) and c.rng.random() < 0.8:
                    col = shade(c.pick(EDGE), 0.95)
            elif c.face in SIDES:
                col = shade(col, 0.95 - 0.12 * y)
            c.set(x, y, col)


def wing_coverts(c):
    """Greater coverts: rows of brown feathers with light back edges (row 0 of top = back edge)."""
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(UNDER)
                if y in (1, 2) and c.rng.random() < (0.75 if y == 2 else 0.45):
                    col = c.pick(UNDER_PALE)                     # the pale underwing bar
                elif y == 0:
                    col = shade(c.pick(UNDER), 0.85)
                c.set(x, y, col)
        return
    if c.face == "back":
        for x in range(c.w):
            c.set(x, 0, c.pick(EDGE_LT) if x % 2 == 0 else c.pick(EDGE))
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(PLUME), 1.04 if c.face == "top" else 0.95))
    if c.face == "top":
        # two staggered rows of covert feathers; each feather's back edge (its tip) is light brown
        for y, off, pal in ((0, 0, EDGE_LT), (2, 1, EDGE)):
            for x in range(c.w):
                if (x + off) % 3 != 2:
                    c.set(x, y, c.pick(pal))
                else:
                    c.set(x, y, c.pick(PLUME_DK))
                    if c.inside(x, y + 1):
                        c.set(x, y + 1, c.pick(PLUME_DK))       # the gap between two feathers


# Feather planes are zero-thickness: their top and bottom faces are coplanar, so both are painted
# with the same pure function of (x, y) (no z-fighting, matching cut-outs).

# secondaries: rows of visible depth per column (col 0 = the wing tip end). Row 4 sits inside the
# coverts cube; rows 0-3 show behind it as a serrated trailing edge.
SEC_DEPTH = [5, 4, 5, 5, 4, 5, 4, 5, 5, 4, 3]


def secondaries(c):
    for y in range(c.h):
        for x in range(c.w):
            if y < c.h - SEC_DEPTH[x]:
                c.clear(x, y)
                continue
            r = _h(x, y, 11)
            col = FLIGHT[int(r * len(FLIGHT)) % len(FLIGHT)]
            if x % 2 == 1:
                col = shade(col, 0.86)                    # overlapping feathers, 2 px each
            if y == c.h - SEC_DEPTH[x]:
                col = shade(col, 1.14)                   # the tip of each feather catches light
            elif y == c.h - 2:
                col = mix(col, EDGE[0], 0.3)              # just behind the coverts
            c.set(x, y, col)


TIP_MASK = [          # row 0 = trailing (back) edge, row 10 = leading edge; col 0 = the wing tip
    ".....#####",     # finger D (innermost primary)
    "....######",
    ".......###",     # slot
    "..########",     # finger C
    ".#########",
    "......####",     # slot
    ".#########",     # finger B (the longest)
    "##########",
    "......####",     # slot
    "..########",     # finger A (leading edge)
    "...#######",
]


def primaries(c):
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
            r = _h(x, y, 23)
            col = FLIGHT[int(r * len(FLIGHT)) % len(FLIGHT)]
            if not solid(x - 1, y):
                col = shade(col, 1.12)                               # rounded finger tip
            elif not solid(x, y + 1) or not solid(x, y - 1):
                col = shade(col, 0.8)                                # dark edge along each finger
            elif x >= 6:
                col = mix(col, EDGE[0], 0.2)                         # the base of the hand
            c.set(x, y, col)


def tip_coverts(c):
    """Primary coverts on the hand. Column 0 of top/bottom = the wing tip, row 0 = back."""
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(UNDER)
                if y >= c.h - 2:
                    col = shade(col, 0.9)
                elif y in (2, 3) and c.rng.random() < 0.5:
                    col = c.pick(UNDER_PALE)
                c.set(x, y, col)
        return
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(PLUME)
            if c.face == "top":
                col = shade(col, 1.0)
                if y == c.h - 1:
                    col = shade(col, 0.88)
            else:
                col = shade(col, 0.9)
            c.set(x, y, col)
    if c.face == "top":
        for y in range(0, c.h - 1, 2):
            for x in range(c.w):
                if (x + y // 2) % 2 == 0:
                    c.set(x, y, c.pick(EDGE) if y else c.pick(EDGE_LT))
    if c.face == "back":
        for x in range(c.w):
            c.set(x, 0, c.pick(EDGE))


# -- tail and legs -----------------------------------------------------------------------------------
TAIL_MASK = [         # row 0 = the back tip; a short wedge of separate feathers
    "..#.#..",
    ".#####.",
    "#######",
    "#######",
    ".#####.",
    ".#####.",
]


def tail_fan(c):
    for y in range(c.h):
        for x in range(c.w):
            if TAIL_MASK[y][x] != "#":
                c.clear(x, y)
                continue
            r = _h(x, y, 31)
            col = FLIGHT[int(r * len(FLIGHT)) % len(FLIGHT)]
            if x % 2 == 0:
                col = shade(col, 0.9)
            if y == 0 or TAIL_MASK[y - 1][x] != "#":
                col = shade(col, 1.15)
            c.set(x, y, col)


def tail_base(c):
    plumage(grad=0.1, top=1.0, scallop=False)(c)
    if c.face == "top":
        for x in range(c.w):
            if x % 2 == 0:
                c.set(x, 0, c.pick(EDGE))               # covert tips over the tail feathers
    elif c.face == "bottom":
        c.noise([shade(p, 0.8) for p in PLUME])


def leg_paint(c):
    """The leg hangs along +y in its own space (swung back flat by the part rotation): feathered
    dark "trousers" at the top, bare grey-pink scaly shank below."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LEG)
            if (x + y) % 2 == 0 and c.rng.random() < 0.5:
                col = LEG_DK                            # scales
            c.set(x, y, col)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, c.pick(PLUME))
            c.set(x, 1, c.pick(PLUME) if c.rng.random() < 0.7 else shade(c.pick(PLUME), 1.2))
    if c.face == "top":
        c.noise(PLUME)
    elif c.face == "bottom":                            # the heel, trailing behind
        c.noise([LEG_DK, shade(LEG_DK, 0.88)])


def toes(c):
    """Toes curled down under the heel, dark hooked talons."""
    c.noise([LEG_DK, shade(LEG_DK, 1.1)])
    if c.face in ("front", "bottom"):
        c.noise(TALON)
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, c.pick(TALON))
        c.set(fx(c, 1), 0, c.pick(LEG))


WING_REST = (0, 0.06, 0.08)   # right wing (x, y, z): spread flat, swept back a touch, a slight dihedral
TIP_REST = (0, 0.12, 0.1)     # the left side mirrors y and z


def build():
    m = Model("vulture", 64, 64, seed=3117)
    pk = Pack(m)

    # body: pivot y 17, flying level. A deep chest (y 14-20, z -6..2) tapering into a shallower rump
    # (y 14-18, z 2..6) so the belly line rises toward the tail, plus a rounder belly underneath.
    body = m.part("body", (0, 17, 0))
    pk.add(body, (-3.5, -3, -6), (7, 6, 8), faces(plumage()))
    pk.add(body, (-3, -3, 2), (6, 4, 4), faces(plumage(grad=0.24), front=None))
    pk.add(body, (-3, 3, -5), (6, 1, 6), faces(belly))

    # ruff: a cream collar round the neck base, straddling the front-top edge of the body
    # (a solid core + a fluffy, mostly cut-out shell)
    ruff = body.part("ruff", (0, -3, -6.25))
    pk.add(ruff, (-4, -2, -1.5), (8, 4, 3), faces(ruff_core))
    pk.add(ruff, (-4, -2, -1.5), (8, 4, 3), faces(ruff_shell), inflate=0.5)

    # neck: from inside the ruff, angled forward-up; the head is levelled again on top of it
    neck = body.part("neck", (0, -1.5, -6.5), (1.05, 0, 0))
    pk.add(neck, (-1.5, -5, -1.5), (3, 5, 3), faces(neck_paint))
    head = neck.part("head", (0, -5, 0), (-1.05, 0, 0))
    pk.add(head, (-2, -3, -3.5), (4, 4, 5), faces(wrinkled, front=head_front, right=head_side,
                                                   left=head_side, back=head_back))
    pk.add(head, (-1, -1.5, -6.5), (2, 2, 3), faces(beak_upper))
    pk.add(head, (-1, -1.5, -7.5), (2, 3, 1), faces(beak_hook))
    pk.add(head, (-1, 0.5, -5.5), (2, 1, 2), faces(beak_lower))

    # wings: shoulders at the top of the body. Each spans outward along x with its chord running back
    # along z: a 2 px leading edge, 1 px coverts, then a feather plane with a serrated trailing edge.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        o = lambda x0, wd: x0 if not left else -x0 - wd      # mirror an x origin for the left side
        w = body.part(f"{side}_wing", (3 * sx, -2.5, -0.5), (0, WING_REST[1] * -sx, WING_REST[2] * -sx))
        pk.add(w, (o(-11, 11), -1, -4), (11, 2, 2), None if left else faces(wing_arm),
               mirror=left, share="arm")
        pk.add(w, (o(-11, 11), -0.5, -2), (11, 1, 5), None if left else faces(wing_coverts, front=None),
               mirror=left, share="coverts")
        pk.add(w, (o(-11, 11), 0, 2), (11, 0, 5), None if left else faces(secondaries),
               mirror=left, share="secondaries")
        t = w.part(f"{side}_wing_tip", (11 * sx, 0, 0), (0, TIP_REST[1] * -sx, TIP_REST[2] * -sx))
        pk.add(t, (o(-4, 4), -0.5, -4), (4, 1, 6), None if left else faces(tip_coverts),
               mirror=left, share="tipcov")
        pk.add(t, (o(-10, 10), 0, -4), (10, 0, 11), None if left else faces(primaries),
               mirror=left, share="primaries")

    # tail: a short wedge fan at the rear, drooping a little
    tail = body.part("tail", (0, -1.5, 5.5), (-0.18, 0, 0))
    pk.add(tail, (-2.5, -0.5, 0), (5, 1, 4), faces(tail_base))
    pk.add(tail, (-3.5, 0, 1), (7, 0, 6), faces(tail_fan))

    # legs: out of the underside of the rump, swung back flat so the feet trail under the tail; the
    # toes curl down
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        lg = body.part(f"{side}_leg", (1.5 * sx, 0.5, 3), (1.45, 0, 0))
        pk.add(lg, (-1, -0.5, -1), (2, 4, 2), None if left else faces(leg_paint), mirror=left, share="leg")
        pk.add(lg, (-1, 2.5, -3), (2, 1, 2), None if left else faces(toes), mirror=left, share="toes")

    if POSE == "flap":
        m.preview = {"right_wing": [0, 0.06, 0.8], "left_wing": [0, -0.06, -0.8],
                     "right_wing_tip": [0, 0.12, 0.5], "left_wing_tip": [0, -0.12, -0.5]}
    elif POSE == "down":
        m.preview = {"right_wing": [0, 0.06, -0.6], "left_wing": [0, -0.06, 0.6],
                     "right_wing_tip": [0, 0.12, -0.3], "left_wing_tip": [0, -0.12, 0.3]}

    pk.apply()
    m.save()
    spawn_egg("vulture", "#3b2a22", "#d97a66", accent="#e6dccb")


if __name__ == "__main__":
    build()

"""Brineclaw: a giant armoured shore crab that comes up onto beaches at night. A wide, heavy, stepped
carapace (28 px across at the lateral rim, 9 px tall) in thick rust-red to deep crimson, darker at the
edges, rough with tubercles and crusted with off-white barnacles clustered toward the back and sides;
strands of dark green seaweed drape over the rear edge and hang down behind it. The front edge is a
thick scarred armour wall: two brow plates and a toothed rostrum with stalked, glossy black eyes in
the notches between them under heavy angled brow ridges, and lateral teeth along the rim. One HUGE,
darker, spiny crusher claw on its right (black-tipped fingers with pale molars) and a much smaller
cutter claw on its left, both held up across the front like a guard. Eight banded, spiky legs (red
with pale joints, dark pointed tips) splay out and down from under the rim. Cream underside with a
tucked abdominal apron, mouthparts under the brow with a few bubbles."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Brineclaw"
LOOT = [item("bone_meal", 1, 4), item("kelp", 0, 3), item("nautilus_shell", chance=0.12, looting=False, player_only=True)]
TAGS = ["arthropod", "can_breathe_under_water", "sensitive_to_impaling"]


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    """Shelf packer. pad=True keeps a transparent 1 px gutter left and right of a cube's texture
    (cut-out seaweed planes would otherwise pick up a hairline of the neighbouring texels)."""
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


def end_dist(c, x, end):
    """Distance in columns from the cube's min-x or max-x end on a face that runs along x (front,
    back, top, bottom); 0 for the end face itself, None for the opposite end face."""
    if c.face in ("front", "top", "bottom"):
        return x if end == "min" else c.w - 1 - x
    if c.face == "back":
        return c.w - 1 - x if end == "min" else x
    if (c.face == "right") == (end == "min"):
        return 0
    return None


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
RED = ["#a8321f", "#a2301d", "#ad3520", "#9a2c1b"]
RED_LT = "#c0452a"
RED_HI = "#d4603e"
DEEP = "#741f13"
EDGE = "#5e1a10"
CLAW = ["#7a2214", "#74210f", "#80241a"]
CLAW_LT = "#b5402a"
CLAW_PALE = ["#d9967a", "#cf8a6c", "#dea283"]
BLACK = ["#1c1210", "#251714", "#1f1411"]
BLACK_HI = "#4a2e26"
CREAM = ["#e8dcc0", "#e2d5b6", "#d6c8a6"]
CREAM_DK = "#bba981"
BARN = ["#d9d4c4", "#cfc9b8", "#bfb9a6"]
BARN_LT = "#ebe7da"
BARN_DK = "#9b9584"
BARN_HOLE = ["#3b322b", "#2e2722"]
WEED = ["#3c6b2f", "#2f5626", "#35612a"]
WEED_LT = "#4c8239"
WEED_DK = "#24441e"
JOINT = ["#e3a582", "#d9967a"]
TIP = ["#2a1410", "#341912"]
EYE = "#121012"
EYE_HI = "#eef4f6"
EYE_SHEEN = "#474c5c"
BUBBLE = ["#e2f4fa", "#d2ecf5"]
BUBBLE_RIM = "#9fd0e2"

# seaweed strands draped over the rear edge: (world x of the left-most column, width, length)
WEED_STRANDS = ((-9, 3, 10), (-2, 2, 7), (4, 3, 11))


# -- carapace ----------------------------------------------------------------------------------------
def bumps(c, density, light=RED_HI, dark=DEEP):
    """Tubercles: a lit pixel with a shadow pixel under it."""
    for _ in range(max(1, int(c.w * c.h * density))):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        c.set(x, y, mix(c.get(x, y), light, 0.45))
        if c.inside(x, y + 1):
            c.set(x, y + 1, mix(c.get(x, y + 1), dark, 0.5))


def weed_px(c, x, y, seed):
    r = hsh(x, y, seed)
    return WEED_LT if r < 0.18 else WEED[int(r * 3) % 3]


def shell(kind, wx0=0):
    """Carapace plates. kind: dome, main or rim. wx0: world x of the cube's min-x edge (to drape the
    seaweed strands over the right columns of the top face)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(RED)
                if c.face in SIDES:
                    t = y / (c.h - 1) if c.h > 1 else 0.0
                    col = shade(col, 1.05 - 0.3 * t)
                    if y == 0:
                        col = mix(col, RED_LT, 0.5)
                    if y == c.h - 1 and c.h > 2:
                        col = mix(col, EDGE, 0.55)
                    if kind == "rim":
                        col = mix(col, EDGE, 0.25)
                elif c.face == "top":
                    col = shade(col, 1.07)
                    d = min(x, c.w - 1 - x, y, c.h - 1 - y)
                    if d == 0:
                        col = mix(col, EDGE, 0.5 if kind != "dome" else 0.35)
                    elif d == 1 and kind == "dome":
                        col = mix(col, RED_LT, 0.25)
                else:
                    col = c.pick(CREAM)
                c.set(x, y, col)
        if c.face == "bottom":
            underside(c, kind)
            return
        bumps(c, 0.03)
        if c.face == "top" and kind == "dome":
            # the grooves that split a crab's carapace into regions, an H across the middle
            for x in range(5, c.w - 5):
                c.set(x, 7, mix(c.get(x, 7), DEEP, 0.55))
            for y in range(2, c.h - 3):
                for x in (5, c.w - 6):
                    c.set(x, y, mix(c.get(x, y), DEEP, 0.55))
            for x in (c.w // 2 - 1, c.w // 2):          # the cardiac bulge behind the groove
                c.set(x, 9, mix(c.get(x, 9), RED_HI, 0.4))
                c.set(x, 4, mix(c.get(x, 4), RED_HI, 0.4))
        if c.face == "top":
            # barnacle scars and grime on the back half (row 0 is the back edge)
            for y in range(c.h // 2):
                for x in range(c.w):
                    if c.rng.random() < 0.035:
                        c.set(x, y, mix(c.get(x, y), c.pick(BARN), 0.6))
            # seaweed draped over the rear edge, plus a few loose clumps
            if kind in ("main", "dome"):
                for sx0, w, _ in WEED_STRANDS:
                    for wx in range(sx0, sx0 + w):
                        x = wx - wx0
                        if not c.inside(x, 0):
                            continue
                        depth = 2 + int(hsh(wx, 3) * 2) if kind == "main" else 0
                        for y in range(depth):
                            c.set(x, y, weed_px(c, wx, y, 11))
                clumps = ((3, 1), (c.w - 6, 2)) if kind == "dome" else ((2, 3), (c.w - 4, 4))
                for (x, y) in clumps:
                    for dx, dy in ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1)):
                        if c.rng.random() < 0.85:
                            c.set(x + dx, y + dy, c.pick(WEED + [WEED_DK]))
        if c.face == "back" and kind == "main":
            for sx0, w, _ in WEED_STRANDS:                # the strands run over the edge
                for wx in range(sx0, sx0 + w):
                    x = (wx0 + c.w) - 1 - wx
                    for y in range(2):
                        c.set(x, y, weed_px(c, wx, y + 5, 11))
        if c.face in ("left", "right") and kind in ("main", "rim"):
            # a few flat barnacles toward the back of the flanks
            for i in range(3):
                x = fx(c, c.w - 3 - i * 4 - c.rng.randrange(2))
                y = 1 + c.rng.randrange(max(1, c.h - 2))
                c.set(x, y, c.pick(BARN))
                if c.inside(x + 1, y):
                    c.set(x + 1, y, BARN_DK)
    return p


def underside(c, kind):
    """Cream underside; the main shell's shows a red margin round the belly plate."""
    if kind == "main":
        for y in range(c.h):
            for x in range(c.w):
                d = min(x, c.w - 1 - x, y, c.h - 1 - y)
                if d <= 2:
                    c.set(x, y, shade(c.pick(RED), 0.7 if d else 0.55))
                else:
                    c.set(x, y, shade(c.pick(CREAM), 0.9))
    elif kind == "belly":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CREAM)
                if y % 3 == 2:
                    col = mix(col, CREAM_DK, 0.5)            # sternal sutures
                c.set(x, y, col)
        # the abdominal apron folded under the back (row 0 = back edge)
        x0, x1 = c.w // 2 - 4, c.w // 2 + 3
        for y in range(0, 8):
            half = 4 - y // 3
            for x in range(c.w // 2 - half, c.w // 2 + half):
                c.set(x, y, shade(c.pick(CREAM), 1.04))
            c.set(c.w // 2 - half, y, CREAM_DK)
            c.set(c.w // 2 + half - 1, y, CREAM_DK)
        for y in (2, 4, 6):
            for x in range(x0 + 1, x1):
                if c.get(x, y)[0] > 200:
                    c.set(x, y, mix(c.get(x, y), CREAM_DK, 0.45))
    else:
        c.noise([shade(col, 0.8) for col in RED])


def belly(c):
    if c.face == "bottom":
        underside(c, "belly")
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(c.pick(CREAM), EDGE, 0.35) if c.face in SIDES else c.pick(CREAM))


def armour(scar=(), teeth=False):
    """The thick front armour: darker plate with a bright worn top edge, a serrated lower edge on the
    front face and pale battle scars (scar: (x, y) starts of short diagonal scratches)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(RED), 0.94)
                if c.face in SIDES:
                    t = y / (c.h - 1) if c.h > 1 else 0.0
                    col = shade(col, 1.06 - 0.32 * t)
                    if y == 0:
                        col = mix(col, RED_HI, 0.55)
                    elif y == 1:
                        col = mix(col, RED_LT, 0.3)
                elif c.face == "top":
                    col = shade(col, 1.1)
                    if y == c.h - 1:
                        col = mix(col, RED_HI, 0.45)      # the front lip catches the light
                    elif y == 0:
                        col = mix(col, EDGE, 0.4)
                else:
                    col = shade(col, 0.6)
                c.set(x, y, col)
        bumps(c, 0.04)
        if c.face == "front":
            for x in range(c.w):
                if teeth:
                    c.set(x, c.h - 1, EDGE if x % 2 else mix(RED_HI, CREAM[0], 0.35))
                else:
                    c.set(x, c.h - 1, mix(c.get(x, c.h - 1), EDGE, 0.6))
            for (sx, sy) in scar:
                for i in range(3):
                    if c.inside(sx + i, sy + i):
                        c.set(sx + i, sy + i, "#d98a6c")
                        if c.inside(sx + i, sy + i + 1):
                            c.set(sx + i, sy + i + 1, mix(c.get(sx + i, sy + i + 1), EDGE, 0.5))
    return p


def horn(c):
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(RED), 1.0 if c.face != "bottom" else 0.65)
            if c.face == "top":
                col = mix(col, RED_HI, 0.3)
            c.set(x, y, col)
    if c.face == "front":
        c.set(0, 0, mix(RED_HI, CREAM[0], 0.4))
        c.set(c.w - 1, 0, mix(RED_HI, CREAM[0], 0.4))


def lateral_tooth(c):
    """A spike sticking out of the rim: pale at the outer point ('right' is the outer end)."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(RED)
            if c.face == "bottom":
                col = shade(col, 0.65)
            c.set(x, y, col)
    d_tip = None
    for x in range(c.w):
        d_tip = end_dist(c, x, "min")
        if d_tip == 0:
            for y in range(c.h):
                c.set(x, y, mix(RED_HI, CREAM[0], 0.45))
        elif d_tip == 1:
            for y in range(c.h):
                c.set(x, y, RED_HI)


# -- eyes, mouth -------------------------------------------------------------------------------------
def stalk(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick([RED_LT, shade(RED_LT, 0.92)])
            if c.face in SIDES and y == c.h - 1:
                col = shade(col, 0.75)
            c.set(x, y, col)
    if c.face in SIDES:
        c.set(0, 1, mix(RED_LT, CREAM[0], 0.5))           # a pale ring


def eye(c):
    c.fill(EYE)
    if c.face == "front":
        c.set(0, 0, EYE_HI)
        c.set(1, 1, EYE_SHEEN)
    elif c.face == "top":
        c.set(0, 1, EYE_SHEEN)
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, EYE_SHEEN)


def brow_ridge(c):
    """The heavy ridge over each eye: dark armour with a worn bright top edge."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(RED), 0.85)
            if c.face == "top":
                col = mix(shade(c.pick(RED), 1.05), RED_HI, 0.3)
            elif c.face == "bottom":
                col = shade(c.pick(RED), 0.5)
            elif y == 0:
                col = mix(col, RED_HI, 0.5)
            elif y == c.h - 1:
                col = mix(col, EDGE, 0.6)
            c.set(x, y, col)


def mouthparts(c):
    """Maxillipeds: pale and red plates side by side, a dark slit down the middle."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "front":
                col = c.pick(CREAM) if x in (1, 4) else c.pick(RED)
                if x in (2, 3):
                    col = shade(c.pick(RED), 0.8)
                col = shade(col, 1.0 - 0.12 * y)
            elif c.face == "bottom":
                col = shade(c.pick(CREAM), 0.8)
            else:
                col = shade(c.pick(RED), 0.85)
            c.set(x, y, col)
    if c.face == "front":
        for y in range(c.h):
            c.set(c.w // 2 - 1 + (y % 2), y, EDGE)


def bubble(c):
    c.noise(BUBBLE)
    if c.face in ("front", "top", "right", "left", "back") and c.w > 1:
        c.set(0, 0, "#ffffff")
        c.set(c.w - 1, c.h - 1, BUBBLE_RIM)
    elif c.face == "bottom":
        c.fill(BUBBLE_RIM)


# -- barnacles, seaweed ------------------------------------------------------------------------------
def barnacle(c):
    """Off-white plated cone: ridged sides darkening down, a dark opening in the top."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BARN)
            if c.face in SIDES:
                if x % 2:
                    col = shade(col, 0.92)
                if y == 0:
                    col = mix(col, BARN_LT, 0.6)
                if y == c.h - 1:
                    col = mix(col, BARN_DK, 0.7)
            elif c.face == "top":
                col = mix(col, BARN_LT, 0.3)
            c.set(x, y, col)
    if c.face == "top":
        if c.w >= 3:
            c.set(c.w // 2, c.h // 2, BARN_HOLE[0])
            c.set(c.w // 2, c.h // 2 - 1, mix(BARN_HOLE[1], BARN[2], 0.4))
        else:
            c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), BARN_HOLE[0])


def weed_plane(seed):
    """A hanging seaweed strand on a flat plane: ragged blade ends and leafy gaps, a pure function of
    position so both faces match. u counts columns the same way on both faces."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                u = c.w - 1 - x if c.face in ("back", "right") else x
                edge = u in (0, c.w - 1) and c.w > 2
                length = c.h - (1 + int(hsh(u, seed) * 3) if edge else int(hsh(u, seed, 1) * 2))
                if y >= length or (edge and y > 1 and (y + u + seed) % 4 == 0):
                    c.clear(x, y)
                    continue
                col = weed_px(c, u, y, seed)
                col = shade(col, 1.0 - 0.18 * y / max(1, c.h - 1))
                if y == length - 1:
                    col = mix(col, WEED_LT, 0.5)
                c.set(x, y, col)
    return p


# -- claws -------------------------------------------------------------------------------------------
def claw_paint(tip=None, gap=None, tiplen=3, knobs=0.08, spiny=False):
    """Claw shell, darker than the carapace. tip: the 'min'/'max' x end blackened over tiplen
    columns. gap: 'top'/'bottom', the side facing the gap between the fingers (pale molars)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CLAW)
                if c.face in SIDES:
                    t = y / (c.h - 1) if c.h > 1 else 0.0
                    col = shade(col, 1.08 - 0.12 * t)
                    if y == 0:
                        col = mix(col, CLAW_LT, 0.5)
                    # two-tone like a real crab claw: the lower part of the shell pales to salmon
                    if c.h >= 4 and y >= c.h - max(1, c.h // 3):
                        col = mix(c.pick(CLAW_PALE), col, 0.3 if y == c.h - max(1, c.h // 3) else 0.0)
                elif c.face == "top":
                    col = mix(shade(col, 1.08), CLAW_LT, 0.2)
                else:
                    col = shade(c.pick(CLAW_PALE), 0.85)
                c.set(x, y, col)
        if c.face != "bottom":
            bumps(c, knobs, light=CLAW_LT, dark=EDGE)
        if spiny and c.face in ("top", "front", "back"):
            for x in range(1, c.w - 1, 2):                  # a row of pale spine bases on the top edge
                y = 0 if c.face != "top" else c.h // 2
                c.set(x, y, mix(CLAW_LT, CREAM[0], 0.35))
        if gap:
            row = 0 if gap == "top" else c.h - 1
            if c.face in ("front", "back"):
                for x in range(c.w):
                    c.set(x, row, c.pick(CREAM) if x % 2 == 0 else shade(c.pick(CREAM), 0.75))
            elif c.face == gap:
                for y in range(c.h):
                    for x in range(c.w):
                        c.set(x, y, c.pick(CREAM) if (x + y) % 3 else CREAM_DK)
        if tip:
            for x in range(c.w):
                d = end_dist(c, x, tip)
                if d is None:
                    continue
                for y in range(c.h):
                    if d < tiplen:
                        col = c.pick(BLACK)
                        if c.face in SIDES and y == 0 and d > 0:
                            col = BLACK_HI
                        c.set(x, y, col)
                    elif d == tiplen:
                        c.set(x, y, mix(c.get(x, y), BLACK[0], 0.5))
    return p


def hand_paint(slot_rows=(), slot_face=None):
    """The crusher's palm: big, knobbly, with rows of pale tubercles and a dark slot where the
    fingers part (slot_face: the end face the fingers come out of)."""
    base = claw_paint(knobs=0.1, spiny=True)

    def p(c):
        base(c)
        if c.face in ("front", "back"):
            for y in range(2, c.h - 1, 3):                  # rows of tubercles across the palm
                for x in range((y // 3) % 2, c.w, 3):
                    c.set(x, y, mix(CLAW_LT, CREAM[0], 0.25))
                    if c.inside(x, y + 1):
                        c.set(x, y + 1, EDGE)
        if c.face == slot_face:
            for y in slot_rows:
                for x in range(1, c.w - 1):
                    c.set(x, y, BLACK[0])
    return p


def spike(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CLAW)
            if c.face == "top" or (c.face in SIDES and y == 0):
                col = mix(CLAW_LT, CREAM[0], 0.45)
            c.set(x, y, col)


# -- legs --------------------------------------------------------------------------------------------
def leg_upper(c):
    """Merus of a right leg (runs along -x: the min-x end is the knee). Pale joints at both ends, a
    darker band, pale spines along the top."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(RED)
            if c.face in SIDES:
                col = shade(col, 1.06 - 0.25 * y / max(1, c.h - 1))
                if y == 0:
                    col = mix(col, RED_LT, 0.4)
            elif c.face == "top":
                col = shade(col, 1.08)
            else:
                col = shade(col, 0.72)
            c.set(x, y, col)
    for x in range(c.w):
        d = end_dist(c, x, "min")
        if d is None:
            continue
        for y in range(c.h):
            if d == 0 or d == c.w - 1:
                c.set(x, y, c.pick(JOINT) if c.face != "bottom" else shade(c.pick(JOINT), 0.8))
            elif d in (3, 4):
                c.set(x, y, mix(c.get(x, y), DEEP, 0.45))
        if c.face == "top" and d % 3 == 1 and 0 < d < c.w - 1:
            c.set(x, c.h - 1, mix(JOINT[0], CREAM[0], 0.4))      # spines along the front edge


def leg_lower(c):
    """Lower leg, hanging down from the knee: pale knee joint on top, a pale band, darkening down."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(RED)
            if c.face in SIDES:
                col = shade(col, 1.05 - 0.3 * y / max(1, c.h - 1))
                if y == 1:
                    col = c.pick(JOINT)
                elif y == 0:
                    col = mix(col, JOINT[0], 0.5)
                elif y == c.h // 2:
                    col = mix(col, JOINT[1], 0.65)
                elif y == c.h // 2 + 1:
                    col = mix(col, DEEP, 0.4)
                if y == c.h - 1:
                    col = mix(col, TIP[0], 0.5)
            elif c.face == "top":
                col = c.pick(JOINT)
            else:
                col = c.pick(TIP)
            c.set(x, y, col)


def leg_tip(c):
    c.noise(TIP)
    if c.face in SIDES:
        c.set(0, 0, shade(TIP[0], 1.5))


def knee_spike(c):
    c.noise([RED_LT, RED_HI])
    if c.face == "top":
        c.fill(mix(JOINT[0], CREAM[0], 0.4))


# -- kinematics: where a point in a part ends up in model space (ModelPart order: X, then Y, then Z) ---
def _rot(p, r):
    x, y, z = p
    rx, ry, rz = r
    c, s = math.cos(rx), math.sin(rx)
    y, z = y * c - z * s, y * s + z * c
    c, s = math.cos(ry), math.sin(ry)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(rz), math.sin(rz)
    x, y = x * c - y * s, x * s + y * c
    return (x, y, z)


def _apply(p, chain):
    """chain: [(pivot, rotation), ...] from the innermost part out to the root."""
    for pivot, rot in chain:
        p = _rot(p, rot)
        p = (p[0] + pivot[0], p[1] + pivot[1], p[2] + pivot[2])
    return p


def build():
    m = Model("brineclaw", 128, 128, seed=7311)
    pk = Pack(m)

    # body: pivot at the carapace centre (world y 14). Stepped carapace: dome y 9-11, main shell
    # y 11-17 (26 x 18), lateral rim y 13-16 (28 x 16, the widest point), cream belly plate y 17-18.
    body = m.part("body", (0, 14, 0))
    pk.add(body, (-10, -5, -7), (20, 2, 14), faces(shell("dome", -10)))
    pk.add(body, (-13, -3, -9), (26, 6, 18), faces(shell("main", -13)))
    pk.add(body, (-14, -1, -8), (28, 3, 16), faces(shell("rim", -14)))
    pk.add(body, (-10, 3, -7), (20, 1, 14), faces(belly))

    # the armoured front: two brow plates and a toothed rostrum (y 10-14, 2-4 px proud of the shell),
    # with the eye notches between them, and a forward horn at each outer corner
    pk.add(body, (-12, -4, -11), (6, 4, 3), faces(armour(scar=((1, 0),))))
    pk.add(body, (6, -4, -11), (6, 4, 3), faces(armour(scar=((2, 1),))))
    pk.add(body, (-3, -4, -12), (6, 4, 4), faces(armour(teeth=True)))
    for sx in (-1, 1):
        pk.add(body, (-13.5 if sx < 0 else 11.5, -3, -13), (2, 2, 3), faces(horn), share="horn")
    # lateral teeth along the rim, toward the front
    for sx in (-1, 1):
        for z in (-6.5, -3.5, -0.5):
            pk.add(body, (-16.5 if sx < 0 else 13.5, 0, z), (3, 1, 1), faces(lateral_tooth),
                   mirror=sx > 0, share="tooth")

    # mouthparts under the rostrum, with a few bubbles
    mouth = body.part("mouth", (0, 1, -9))
    pk.add(mouth, (-3, 0, -1.5), (6, 3, 2), faces(mouthparts))
    pk.add(mouth, (1.5, 0.5, -3), (2, 2, 2), faces(bubble), share="bubble2")
    pk.add(mouth, (-3.5, 2, -2.5), (1, 1, 1), faces(bubble), share="bubble1")
    pk.add(mouth, (3.5, -1.5, -2.5), (1, 1, 1), faces(bubble), share="bubble1")

    # eyes: stalks rising out of the notches, glossy black eyes under heavy angled brow ridges
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        # stalk y 11-13 out of the notch, eye y 9-11 just proud of the brow plates
        e = body.part(side + "_eye", (4.5 * sx, -1, -10), (0, 0, 0.1 * sx))
        pk.add(e, (-0.5, -2, -0.5), (1, 2, 1), None if left else faces(stalk), mirror=left, share="stalk")
        pk.add(e, (-1, -4, -1), (2, 2, 2), None if left else faces(eye), mirror=left, share="eye")
        # the heavy ridge over each eye: the thickened front of the dome (y 8-10), sloping down
        # toward the middle; decoration, child of body so it stays put while the eyes twitch
        br = body.part(side + "_brow", (4.5 * sx, -5, -8.5), (0, 0, -0.2 * sx))
        pk.add(br, (-3.5, -1, -2), (7, 2, 4), None if left else faces(brow_ridge), mirror=left, share="brow")

    # barnacles: clustered toward the back and the sides, each sunk 1 px into the shell
    for (x, y, z, s) in ((-8.5, -6, 3.5, 3), (-4.5, -6, 4.5, 2), (6.5, -6, 2.5, 2), (7.5, -6, 4.5, 3),
                         (1.5, -6, 4.5, 2), (-12.5, -4, 4.5, 3), (-11.5, -4, 0.5, 2), (10.5, -4, 6.5, 3),
                         (10.5, -4, 0.5, 2), (-1.5, -4, 7.5, 2), (-7.5, -4, 7.5, 2), (4.5, -4, 7.5, 3)):
        pk.add(body, (x, y, z), (s, 2, s), faces(barnacle, bottom=None), share=f"barn{s}")

    # seaweed: strands hanging off the rear edge (trailing back), and two off the rear of the rim
    for i, (x0, w, length) in enumerate(WEED_STRANDS, start=1):
        wd = body.part(f"weed{i}", (x0 + w / 2, -3, 9.5), (0.3 + 0.05 * i, 0, 0.04 * (i - 2)))
        pk.add(wd, (-w / 2, -0.5, 0), (w, length, 0), faces(weed_plane(i)), share=f"weed{i}", pad=True)
    for i, (sx, z, length) in enumerate(((-1, 5.5, 8), (1, 3.5, 6)), start=4):
        wd = body.part(f"weed{i}", (14.5 * sx, -1, z), (0, 0, -0.25 * sx))
        pk.add(wd, (0, -0.5, -1.5), (0, length, 3), faces(weed_plane(i)), share=f"weed{i}", pad=True)

    # -- claws: both held up in front like a guard. In each claw's own frame the arm (merus) runs
    # forward (-z) from the shoulder and the hand lies across the front with the fingers pointing
    # inward (+x for the right claw, -x for the left); the claw's yaw swings the elbow out and turns
    # the hand to point forward-inward. right_pincer / left_pincer are the movable upper fingers,
    # hinged at the top of the palm's inner end.
    rc = body.part("right_claw", (-11.5, 2, -7), (-0.2, 0.55, 0))
    crusher = claw_paint(knobs=0.1, spiny=True)
    pk.add(rc, (-2, -2, -5), (4, 4, 6), faces(crusher))                        # merus  z -5..1
    pk.add(rc, (-3, -3, -9), (6, 6, 5), faces(crusher))                        # carpus z -9..-4
    pk.add(rc, (-3, -5.5, -15), (9, 10, 7), faces(hand_paint((4, 5), "left")))  # the huge palm
    pk.add(rc, (5, 0, -14), (6, 3, 5), faces(claw_paint(tip="max", gap="top", tiplen=3)))     # fixed finger
    pk.add(rc, (10, 0.5, -13), (3, 2, 3), faces(claw_paint(tip="max", tiplen=4)))            # its tip
    for (x, y, z) in ((-1, -6.5, -12.5), (1.5, -6.5, -13.5), (4, -6.5, -11.5), (-1, -4, -7.5), (-0.5, -3, -3)):
        pk.add(rc, (x, y, z), (1, 2, 1), faces(spike), share="spike")
    pk.add(rc, (-2.5, -6.5, -10.5), (2, 2, 2), faces(barnacle, bottom=None), share="barn2")
    rp = rc.part("right_pincer", (5, -1, -11.5))
    pk.add(rp, (0, -3, -2.5), (6, 3, 5), faces(claw_paint(tip="max", gap="bottom", tiplen=3, spiny=True)))
    pk.add(rp, (5, -1.5, -2), (3, 2, 4), faces(claw_paint(tip="max", tiplen=4)))

    lc = body.part("left_claw", (11, 1.5, -7), (-0.35, -0.6, 0))
    cutter = claw_paint(knobs=0.08)
    pk.add(lc, (-1.5, -1.5, -5), (3, 3, 6), faces(cutter))                     # merus  z -5..1
    pk.add(lc, (-2, -2, -8), (4, 4, 4), faces(cutter))                         # carpus z -8..-4
    pk.add(lc, (-5, -2.5, -11), (6, 5, 4), faces(hand_paint((2,), "right")))   # palm
    pk.add(lc, (-9, 0, -10.5), (5, 2, 3), faces(claw_paint(tip="min", gap="top", tiplen=2)))  # fixed finger
    pk.add(lc, (-11, 0.5, -10), (2, 1, 2), faces(claw_paint(tip="min", tiplen=3)))
    pk.add(lc, (-2.5, -3.5, -6.5), (1, 2, 1), faces(spike), share="spike")
    lp = lc.part("left_pincer", (-4, -1, -9))
    pk.add(lp, (-5, -2, -1.5), (5, 2, 3), faces(claw_paint(tip="min", gap="bottom", tiplen=2)))
    pk.add(lp, (-7, -0.5, -1), (2, 1, 2), faces(claw_paint(tip="min", tiplen=3)))

    # -- legs: merus out from under the rim, knee raised, lower leg down to a pointed tip on the
    # ground. Yaw fans them front to back; roll lifts the knee; the lower leg's roll is solved so the
    # tip lands on y 24.
    UPPER, LOWER, ROLL = 9, 12, 0.25
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        for i, (z, yaw) in enumerate(((-5, -0.6), (-1.5, -0.18), (2, 0.22), (5.5, 0.62)), start=1):
            pivot = (12.5 * sx, 1.5, z)
            rot = (0, yaw if sx < 0 else -yaw, ROLL if sx < 0 else -ROLL)
            knee = ((UPPER - 0.5) * sx, 0, 0)
            body_chain = [((0, 14, 0), (0, 0, 0))]
            foot = (0, LOWER + 1, 0)

            def tip_y(r):                           # r > 0 leans the foot outward on either side
                return _apply(foot, [(knee, (0, 0, -r * sx)), (pivot, rot)] + body_chain)[1]
            lo, hi = -ROLL, 1.4
            for _ in range(60):
                mid = (lo + hi) / 2
                if tip_y(mid) > 24.0:
                    lo = mid
                else:
                    hi = mid
            rz = round(-lo * sx, 4)
            lg = body.part(f"{side}_leg{i}", pivot, rot)
            pk.add(lg, (-UPPER if sx < 0 else 0, -1.5, -1), (UPPER, 3, 2), None if left else faces(leg_upper),
                   mirror=left, share="leg_upper")
            pk.add(lg, ((UPPER - 2.5) * sx - 0.5, -3, -0.5), (1, 2, 1), faces(knee_spike), share="knee_spike")
            lo_part = lg.part(f"{side}_leg{i}_lower", knee, (0, 0, rz))
            pk.add(lo_part, (-1, -1, -1), (2, LOWER, 2), None if left else faces(leg_lower),
                   mirror=left, share="leg_lower")
            pk.add(lo_part, (-0.5, LOWER - 1, -0.5), (1, 2, 1), faces(leg_tip), share="leg_tip")

    pk.apply()
    m.save()
    spawn_egg("brineclaw", "#a8321f", "#d9d4c4", accent="#3c6b2f")


if __name__ == "__main__":
    build()

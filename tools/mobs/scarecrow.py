"""Scarecrow: a field scarecrow that climbs down off its pole at night. Its head is a stuffed burlap
sack (pale woven burlap, darker seams) cinched at the neck with rope, with two sewn-on button eyes
that glow a dim ember orange and a wide jagged grin stitched in dark thread. A battered wide-brimmed
straw hat sits on top: golden woven straw, a faded red band, a bite out of the brim and a frayed hole.
It wears a faded, patched plaid flannel shirt (a denim patch on the chest, an olive one on the left
elbow and the back, a rip in its side), a rope belt and baggy patched olive-brown trousers over old
boots. Yellow straw bursts out of the collar, the cuffs, the trouser hems and the rip, and its hands
are bundles of straw tied off with twine. By day the game freezes it in its scarecrow T-pose (arms
straight out, head slumped); the preview shows that pose."""
import math
import random

from mobkit import Model, faces, humanoid, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Scarecrow"
LOOT = [item("wheat", 0, 3), item("stick", 0, 2), item("hay_block", chance=0.05, looting=False, player_only=True)]
TAGS = []

# burlap sack
BURLAP_A = ["#cdb68a", "#c9b285", "#d2bc90"]      # one set of threads in the weave
BURLAP_B = ["#bea677", "#b9a172", "#c2aa7b"]      # the crossing set
SLUB = ["#a58d61", "#9d865b"]                     # thick dark fibres
BURLAP_LIGHT = "#dccb9f"
SEAM = "#6a5435"
TWINE = "#e6d8ad"
STENCIL = ["#8f7f62", "#94846a"]                  # an old feed-sack print, nearly washed out
THREAD = "#24180f"
THREAD_HI = "#4a3424"
EMBER = "#ff9a3c"
EMBER_DIM = "#c8641e"
EMBER_HOT = "#ffaa4a"
EMBER_BASE = "#4a1c08"     # what the eye looks like under the glow layer (the glow is added on top)
# flannel shirt
RED = ["#8a3b2e", "#843729", "#8f4031"]
CHECK = ["#5f3a2b", "#5a3628", "#633d2d"]
CROSS = ["#3f2a20", "#3a271d"]
FADE = "#b48a72"
PATCH_STITCH = "#e3d6b0"
DENIM = ["#4f6a8f", "#486285", "#557299"]
DENIM_DARK = "#3a4f6d"
OLIVE = ["#6d7342", "#666c3d", "#747a48"]
OLIVE_DARK = "#4f5530"
BUTTON = "#d9caa1"
# trousers and boots
TROUSER = ["#6b5b3a", "#635436", "#716140", "#5e5033"]
TROUSER_DARK = "#4a3f28"
TROUSER_INSIDE = "#2f281a"
BURLAP_PATCH = ["#b49c6c", "#ab9365", "#bba375"]
BOOT = ["#4d3627", "#463123", "#543c2c"]
BOOT_HI = "#6e503a"
SOLE = ["#2b211b", "#261d18", "#30251e"]
# rope and straw
ROPE = ["#8f7546", "#866d40", "#977c4c"]
ROPE_DARK = "#5a482a"
ROPE_LIGHT = "#b39864"
HEMP = ["#c4a86c", "#b89c62", "#cbb075"]          # the paler hemp rope of the belt
HEMP_DARK = "#7d6640"
HEMP_LIGHT = "#dcc58e"
STRAW = ["#e0bf55", "#d8b44a", "#e5c75f"]
STRAW_LIGHT = ["#eed67e", "#f1db88"]
STRAW_DARK = ["#b8902f", "#ad872c"]
STRAW_DEEP = "#7e601f"
STRAW_TIP = "#f7e8a8"
# straw hat
HAT = ["#d6ae4c", "#d1a948", "#dbb553"]
HAT_DARK = ["#bf9539", "#b88f36"]
HAT_LIGHT = "#ebd07a"
HAT_UNDER = ["#8a6828", "#826226", "#8f6c2b"]
HAT_FRAY = "#9a7630"
BAND = ["#9b4a3b", "#914437", "#a35243"]
BAND_DARK = "#73362b"
FEATHER = ["#1c1c22", "#23232b", "#202027"]       # a crow feather tucked in the band
FEATHER_SHEEN = "#3a4466"
FEATHER_SHAFT = "#5c5a5e"
SIDES = ("front", "back", "left", "right")


# -- texture packing: cubes are collected, then shelf-packed tallest-first into free texture areas ----
class Pack:
    def __init__(self, model, areas):
        self.m, self.areas, self.items = model, areas, []

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
        shelves, tops = [], [a[1] for a in self.areas]
        for k, (w, h) in order:
            for s in shelves:                       # s = [y, height, next x, right edge]
                if h <= s[1] and s[2] + w <= s[3]:
                    keys[k] = (s[2], s[0])
                    s[2] += w
                    break
            else:
                for i, (ax, ay, aw, ah) in enumerate(self.areas):
                    if w <= aw and tops[i] + h <= ay + ah:
                        shelves.append([tops[i], h, ax + w, ax + aw])
                        keys[k] = (ax, tops[i])
                        tops[i] += h
                        break
                else:
                    raise ValueError(f"{self.m.id}: no texture room for {k} {w}x{h}")
        for i, (part, origin, size, paint, mirror, share, inflate) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


# -- shared helpers ---------------------------------------------------------------------------------
def tone(c, y, col, k=0.14):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def ring_u(c, w, d):
    """Column offset of a side face when walking round a box, so patterns continue round corners."""
    return {"front": 0, "left": w, "back": w + d, "right": w + d + w}.get(c.face, 0)


def back_col(c, i=0):
    """Column i counted from the back edge of a right/left side face."""
    return i if c.face == "right" else c.w - 1 - i


def stitched_patch(c, x0, y0, w, h, pal, k=0.12, stitch=PATCH_STITCH):
    """A sewn-on square patch: its own cloth, dashed stitches along its top and bottom seams."""
    for yy in range(h):
        for xx in range(w):
            col = c.pick(pal)
            if (yy == 0 and xx % 2 == 1) or (yy == h - 1 and xx % 2 == 0):
                col = stitch
            elif xx == w - 1 or yy == h - 1:
                col = shade(col, 0.84)                    # the patch's lower/right edge in shadow
            c.set(x0 + xx, y0 + yy, tone(c, y0 + yy, col, k))


def rope_px(c, x, y, hemp=False):
    """Twisted rope: a diagonal twist every third pixel."""
    k = (x + y) % 3
    if hemp:
        col = HEMP_LIGHT if k == 0 else (c.pick(HEMP) if k == 1 else HEMP_DARK)
    else:
        col = ROPE_LIGHT if k == 0 else (c.pick(ROPE) if k == 1 else ROPE_DARK)
    if c.face == "bottom":
        col = shade(col, 0.82)
    return col


def rope(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, rope_px(c, x, y))


def hemp(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, rope_px(c, x, y, hemp=True))


# -- straw sprites ----------------------------------------------------------------------------------
def tuft(w, h, seed, root="top", full=1, lean=0.3, edges=None):
    """A straw tuft as a pixel grid [row][col] (None = cut out). Straws grow from the `root` edge
    ('top', 'bottom', 'left' or 'right'); each is one pixel wide with its own length, darker at the
    root and pale at the tip, some leaning sideways. `full` rows next to the root are always filled.
    `edges` caps the length of the two outermost straws."""
    rng = random.Random(seed)
    across, along = (w, h) if root in ("top", "bottom") else (h, w)
    g = [[None] * across for _ in range(along)]
    for a in range(across):
        length = rng.randint(min(full, along), along)
        if edges is not None and a in (0, across - 1):
            length = rng.randint(0, edges)
        light = rng.random() < 0.4
        step = rng.choice((-1, 1)) if rng.random() < lean else 0
        x = a
        for i in range(length):
            if step and i and i % 2 == 0:
                x += step
            if not 0 <= x < across:
                break
            if i == length - 1 and length > 1:
                col = STRAW_TIP if rng.random() < 0.6 else rng.choice(STRAW_LIGHT)
            elif i == 0:
                col = rng.choice(STRAW_DARK)
            else:
                col = rng.choice(STRAW_LIGHT if light else STRAW)
            g[i][x] = col
    if root == "top":
        return g
    if root == "bottom":
        return g[::-1]
    if root == "left":
        return [[g[c][r] for c in range(along)] for r in range(across)]
    return [[g[along - 1 - c][r] for c in range(along)] for r in range(across)]


def fan(w, h, seed, n=5, spread=1.0, root="top"):
    """A spray of straws fanning out from the middle of the `root` edge: pixel grid [row][col]."""
    rng = random.Random(seed)
    across, along = (w, h) if root in ("top", "bottom") else (h, w)
    g = [[None] * across for _ in range(along)]
    mid = (across - 1) / 2
    for i in range(n):
        t = (i / (n - 1) - 0.5) * 2 if n > 1 else 0.0
        x0 = mid + t * 0.7
        x1 = mid + t * mid * spread + rng.uniform(-0.6, 0.6)
        length = max(2, round(along * rng.uniform(0.6, 1.0)))
        light = rng.random() < 0.45
        for a in range(length):
            x = round(x0 + (x1 - x0) * a / max(1, along - 1))
            if not 0 <= x < across:
                break
            if a == length - 1:
                col = STRAW_TIP if rng.random() < 0.6 else rng.choice(STRAW_LIGHT)
            elif a == 0:
                col = rng.choice(STRAW_DARK)
            else:
                col = rng.choice(STRAW_LIGHT if light else STRAW)
            g[a][x] = col
    if root == "top":
        return g
    if root == "bottom":
        return g[::-1]
    if root == "left":
        return [[g[c][r] for c in range(along)] for r in range(across)]
    return [[g[along - 1 - c][r] for c in range(along)] for r in range(across)]


def sprite(grid, f=1.0):
    """Paints a pixel grid on a flat plane: the far side is mirrored so both faces match exactly."""
    def p(c):
        mirror = c.face in ("back", "left")
        for y in range(min(c.h, len(grid))):
            row = grid[y]
            for x in range(c.w):
                col = row[c.w - 1 - x if mirror else x]
                if col is not None:
                    c.set(x, y, shade(col, f))
    return p


def straw_ring(seed):
    """Side faces of a ring of straw hanging out from under a hem: ragged, with gaps and pale tips."""
    def p(c):
        if c.face not in SIDES:
            return
        rng = random.Random(seed + SIDES.index(c.face))
        for x in range(c.w):
            length = rng.choice((0, 0, 1, 1, 2, 2, 3))
            light = rng.random() < 0.4
            for y in range(min(length, c.h)):
                if y == length - 1 and length > 1:
                    col = STRAW_TIP if rng.random() < 0.5 else rng.choice(STRAW_LIGHT)
                elif y == 0:
                    col = rng.choice(STRAW_DARK)
                else:
                    col = rng.choice(STRAW_LIGHT if light else STRAW)
                c.set(x, y, col)
    return p


# -- burlap sack head -------------------------------------------------------------------------------
def burlap_px(c, x, y, k=0.1):
    """Woven burlap: two thread colours crossing in a 1-px checker, the odd thick dark slub."""
    r = c.rng.random()
    if r < 0.06:
        col = c.pick(SLUB)
    elif r < 0.09:
        col = BURLAP_LIGHT
    else:
        col = c.pick(BURLAP_A if (x + y) % 2 == 0 else BURLAP_B)
    return tone(c, y, col, k)


def seam_line(c, x, y0, y1):
    """A sewn seam: a dark fold with pale twine stitches crossing it."""
    for y in range(y0, y1):
        c.set(x, y, tone(c, y, SEAM))
        if y % 2 == 0:
            c.set(x - 1, y, tone(c, y, TWINE, 0.2))
        else:
            c.set(x + 1, y, tone(c, y, TWINE, 0.2))


def sack(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, burlap_px(c, x, y))
    for x in range(c.w):                                  # the hat's shadow on the crown of the sack
        c.set(x, 0, shade(c.get(x, 0), 0.82))
    for x in range(0, c.w, 2):                            # gathered where the rope cinches it
        c.set(x, 6, shade(c.get(x, 6), 0.84))
    if c.face in ("left", "right"):
        seam_line(c, back_col(c, 2), 1, 7)
        if c.face == "left":                              # a darned hole
            c.set(2, 3, SEAM); c.set(3, 3, THREAD_HI); c.set(2, 4, THREAD_HI)
    elif c.face == "back":
        seam_line(c, 4, 0, 7)
        for x in (0, 1, 6, 7):                            # the washed-out stripes of an old feed-sack print
            c.set(x, 2, tone(c, 2, c.pick(STENCIL)))
            if x in (1, 6):
                c.set(x, 3, tone(c, 3, c.pick(STENCIL)))


def sack_face(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, burlap_px(c, x, y, 0.06))
    for x in range(c.w):
        c.set(x, 0, shade(c.get(x, 0), 0.8))              # shadow under the brim
    # sewn-on button eyes, glowing like embers, with an angry stitch over each
    def ember(x, y, col):
        c.glow(x, y, col)
        c.set(x, y, EMBER_BASE)          # the glow layer is added on top: keep the sum ember orange
    for (x0, mirror) in ((1, False), (5, True)):
        a, b = (x0, x0 + 1) if not mirror else (x0 + 1, x0)    # a = outer column, b = inner
        ember(a, 2, EMBER_DIM); ember(b, 2, EMBER)
        ember(a, 3, EMBER); ember(b, 3, EMBER_HOT)
        c.set(b, 1, THREAD)                               # inner end of the brow, pulled down
        c.set(a, 1, THREAD_HI)
        c.set(a - 1 if not mirror else a + 1, 0, shade(THREAD_HI, 1.1))
    # a wide jagged grin stitched in dark thread
    for (x, y) in ((0, 4), (7, 4), (1, 5), (3, 5), (4, 5), (6, 5), (2, 6), (5, 6)):
        c.set(x, y, THREAD)
    c.set(0, 5, THREAD_HI); c.set(7, 5, THREAD_HI)        # loose thread ends


def sack_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, burlap_px(c, x, y))
    seam_line(c, 4, 0, c.h)


def sack_bottom(c):
    """The open mouth of the sack, stuffed with straw."""
    for y in range(c.h):
        for x in range(c.w):
            edge = x in (0, c.w - 1) or y in (0, c.h - 1)
            if edge:
                col = shade(c.pick(BURLAP_B), 0.75)
            elif c.rng.random() < 0.2:
                col = STRAW_DEEP
            else:
                col = shade(c.pick(STRAW + STRAW_DARK), 0.85)
            c.set(x, y, col)


def neck_rope(c):
    """Ring of rope round the bottom of the sack; only its edge shows above and below."""
    for y in range(c.h):
        for x in range(c.w):
            edge = x in (0, c.w - 1) or y in (0, c.h - 1)
            if c.face in ("top", "bottom") and not edge:
                c.set(x, y, shade(c.pick(STRAW), 0.7) if c.face == "bottom" else None)
                continue
            c.set(x, y, rope_px(c, x, y))


# -- straw hat --------------------------------------------------------------------------------------
def weave(c, x, y, f=1.0):
    """Plaited straw: a diagonal twill of darker strands."""
    col = c.pick(HAT_DARK) if (x - y) % 3 == 0 else c.pick(HAT)
    if c.rng.random() < 0.08:
        col = HAT_LIGHT
    return shade(col, f)


def crown(c):
    """8x3x8 crown (inflated): plaited straw, a faded red band round its base."""
    if c.face == "bottom":
        c.noise([shade(h, 0.7) for h in HAT_UNDER])
        return
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, weave(c, x, y, 1.06))
        return
    for y in range(c.h):
        for x in range(c.w):
            if y == c.h - 1:
                col = c.pick(BAND)
                if x % 3 == 0:
                    col = BAND_DARK
            else:
                col = weave(c, x, y, 1.04 if y == 0 else 0.94)
            c.set(x, y, col)
    if c.face == "left":                                  # the band has torn and been knotted
        c.set(2, 2, c.pick(HAT_DARK)); c.set(3, 1, BAND_DARK); c.set(4, 1, c.pick(BAND))
    if c.face == "front":
        c.set(5, 1, HAT_FRAY); c.set(6, 0, HAT_FRAY)      # a crushed dent


def dome(c):
    """The rounded top of the crown."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top":
                r = int(max(abs(x - (c.w - 1) / 2), abs(y - (c.h - 1) / 2)))
                col = c.pick(HAT) if r % 2 == 0 else c.pick(HAT_DARK)
                if c.rng.random() < 0.1:
                    col = HAT_LIGHT
                c.set(x, y, shade(col, 1.08))
            elif c.face == "bottom":
                c.set(x, y, c.pick(HAT_UNDER))
            else:
                c.set(x, y, weave(c, x, y, 1.0))
    if c.face == "top":
        c.set(2, 2, HAT_FRAY); c.set(3, 2, HAT_DARK[0])  # a pinch in the crown


def brim_holes():
    """Brim pixels (top-face coordinates, row 13 = front edge) that are missing: rounded corners,
    a frayed rim, a bite out of the front and a frayed hole near the back."""
    rng = random.Random(77)
    n = 14
    miss = set()
    for (x, y) in ((0, 0), (1, 0), (0, 1), (n - 1, 0), (n - 2, 0), (n - 1, 1),
                   (0, n - 1), (1, n - 1), (0, n - 2), (n - 1, n - 1), (n - 2, n - 1), (n - 1, n - 2)):
        miss.add((x, y))
    for i in range(2, n - 2):                             # frayed rim
        for (x, y) in ((i, 0), (i, n - 1), (0, i), (n - 1, i)):
            if rng.random() < 0.14:
                miss.add((x, y))
    for (x, y) in ((8, 13), (9, 13), (10, 13), (11, 13), (9, 12), (10, 12)):   # the bite
        miss.add((x, y))
    for (x, y) in ((3, 2), (4, 2), (3, 3)):               # the hole
        miss.add((x, y))
    return miss


BRIM_MISS = brim_holes()
BRIM_FRAY = {(x + dx, y + dy) for (x, y) in BRIM_MISS for dx in (-1, 0, 1) for dy in (-1, 0, 1)}


def brim(c):
    """14x1x14 brim: woven in rings round the crown, darker underneath, frayed and bitten."""
    n = 14
    if c.face in ("top", "bottom"):
        for y in range(c.h):
            for x in range(c.w):
                if (x, y) in BRIM_MISS:
                    continue
                r = int(max(abs(x - 6.5), abs(y - 6.5)))
                col = c.pick(HAT) if r % 2 == 0 else c.pick(HAT_DARK)
                if x in (y, n - 1 - y) and r > 4:
                    col = HAT_DARK[1]                     # seams where the straw plait is sewn
                if (x, y) in BRIM_FRAY and c.rng.random() < 0.6:
                    col = HAT_FRAY
                if c.face == "top":
                    if r == 6 and c.rng.random() < 0.3:
                        col = HAT_LIGHT
                    c.set(x, y, col)
                else:
                    c.set(x, y, shade(col, 0.66))
        return
    # 1-px edge strips, cut where the rim above them is missing
    for x in range(c.w):
        if c.face == "front":
            pos = (x, n - 1)
        elif c.face == "back":
            pos = (n - 1 - x, 0)
        elif c.face == "right":
            pos = (0, x)
        else:
            pos = (n - 1, n - 1 - x)
        if pos in BRIM_MISS:
            continue
        c.set(x, 0, HAT_FRAY if c.rng.random() < 0.4 else c.pick(HAT_DARK))


# -- shirt ------------------------------------------------------------------------------------------
def plaid(c, u, v, fade=0.06):
    """Muted red/brown flannel check: 2-px brown bands crossing on red, darkest where they cross."""
    bu, bv = u % 4 < 2, v % 4 < 2
    if bu and bv:
        col = c.pick(CROSS)
    elif bu or bv:
        col = c.pick(CHECK)
    else:
        col = c.pick(RED)
    if c.rng.random() < fade:
        col = mix(col, FADE, 0.35)
    return col


def trouser_px(c, y, k=0.12):
    return tone(c, y, c.pick(TROUSER), k)


def shirt_body(c):
    """8x12x4 torso: flannel shirt (rows 0-7) tucked into the trousers (rows 8-11, belt at 8)."""
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                c.set(x, y, plaid(c, x, y, 0.2))
        return
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                c.set(x, y, trouser_px(c, y))
        return
    u0 = ring_u(c, 8, 4)
    for y in range(h):
        for x in range(w):
            if y >= 8:
                col = trouser_px(c, y)
            else:
                col = tone(c, y, plaid(c, u0 + x, y, 0.1 if y < 3 else 0.05))
            c.set(x, y, col)
    if c.face == "front":
        c.set(3, 0, c.pick(STRAW_LIGHT)); c.set(4, 0, c.pick(STRAW))      # straw in the open collar
        c.set(3, 1, c.pick(STRAW_DARK)); c.set(2, 0, CROSS[0]); c.set(5, 0, CROSS[0])
        for y in range(2, 8):                                             # button placket
            c.set(3, y, shade(c.get(3, y), 0.8))
        c.set(3, 3, BUTTON); c.set(3, 6, shade(BUTTON, 0.85))
        stitched_patch(c, 4, 3, 4, 3, DENIM)                              # denim patch on the chest
        for x in range(w):
            c.set(x, 9, shade(c.get(x, 9), 0.88))             # waistband shadow
        c.set(3, 10, TROUSER_DARK); c.set(3, 11, TROUSER_DARK)            # fly
    elif c.face == "back":
        stitched_patch(c, 4, 1, 3, 3, OLIVE)                              # olive patch, high on the back
        c.set(1, 5, CROSS[0]); c.set(2, 6, CROSS[1])                      # a small tear
        c.set(2, 5, c.pick(STRAW))
        for x in (1, 2, 5, 6):
            c.set(x, 10, tone(c, 10, TROUSER_DARK))                       # back pockets
    elif c.face == "left":
        # a rip in the side with straw bursting out of it (rows 3-6)
        for (x, y) in ((1, 3), (2, 3), (0, 4), (3, 4), (0, 5), (3, 5), (1, 6), (2, 6)):
            c.set(x, y, tone(c, y, c.pick(CROSS)))
        for (x, y) in ((1, 4), (2, 4), (1, 5), (2, 5)):
            c.set(x, y, c.pick(STRAW + STRAW_LIGHT))


def sleeve(patch=False):
    """Baggy 4x8x4 sleeve overlay: flannel, a frayed cuff, maybe an elbow patch (on the outer face)."""
    def p(c):
        if c.face == "bottom":
            c.noise([shade(x, 0.55) for x in CHECK])
            return
        u0 = ring_u(c, 4, 4)
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, plaid(c, u0 + x, y, 0.12 if y < 3 else 0.05), 0.16))
        if c.face == "top":
            return
        for x in range(c.w):                              # frayed cuff
            r = c.rng.random()
            if r < 0.3:
                c.clear(x, c.h - 1)
            elif r < 0.55:
                c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.75))
        if patch and c.face == "right":                   # outer face (mirrored onto the left arm)
            stitched_patch(c, 0, 4, 3, 3, OLIVE, 0.16)
    return p


# -- straw hands, trousers, boots --------------------------------------------------------------------
def arm_base(c):
    """4x12x4 arm: shirt (hidden under the sleeve), then a bundle of straw tied off at the wrist."""
    if c.face == "top":
        c.noise(RED)
        return
    if c.face == "bottom":                                # cut ends of the straw bundle
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(STRAW_LIGHT) if (x * 3 + y) % 4 else STRAW_DEEP)
        return
    u0 = ring_u(c, 4, 4)
    for y in range(c.h):
        for x in range(c.w):
            if y < 8:
                col = tone(c, y, plaid(c, u0 + x, y), 0.1)
            elif y == 9:
                col = rope_px(c, x, y)                    # twine round the wrist
            else:
                strand = (u0 + x) % 3
                col = c.pick(STRAW_LIGHT) if strand == 0 else (c.pick(STRAW) if strand == 1 else c.pick(STRAW_DARK))
                if y == 8 and c.rng.random() < 0.3:
                    col = STRAW_DEEP
                col = shade(col, 1.04 if y == 11 else 1.0)
            c.set(x, y, col)


def leg_base(c):
    """4x12x4 leg: trouser (under the overlay), a straw-stuffed hem, then an old boot."""
    if c.face == "top":
        c.noise(TROUSER)
        return
    if c.face == "bottom":
        c.noise(SOLE)
        return
    for y in range(c.h):
        for x in range(c.w):
            if y < 8:
                col = trouser_px(c, y)
            elif y == 8:
                col = c.pick(STRAW + STRAW_DARK)
            elif y == 9:
                col = shade(c.pick(BOOT), 1.15)           # slouched boot cuff
            elif y == 11:
                col = c.pick(SOLE) if c.rng.random() < 0.5 else shade(c.pick(BOOT), 0.8)
            else:
                col = c.pick(BOOT)
            c.set(x, y, col)
    if c.face == "front":
        c.set(1, 10, BOOT_HI); c.set(2, 9, BOOT_HI)       # scuffs
    elif c.face == "right":
        c.set(1, 10, BOOT_HI)


def trousers(patch):
    """Baggy 4x8x4 trouser overlay with a frayed hem; patch: 'knee', 'seat' or None."""
    def p(c):
        if c.face == "bottom":
            c.fill(TROUSER_INSIDE)
            return
        for y in range(c.h):
            for x in range(c.w):
                col = trouser_px(c, y, 0.16)
                if c.rng.random() < 0.05:
                    col = tone(c, y, TROUSER_DARK)
                c.set(x, y, col)
        if c.face == "top":
            return
        if c.face == "right":                             # outer seam (outer face on both legs)
            for y in range(c.h - 1):
                c.set(1, y, tone(c, y, TROUSER_DARK, 0.16))
        if c.face == "front":
            c.set(2, 2, tone(c, 2, TROUSER_DARK)); c.set(1, 3, tone(c, 3, TROUSER_DARK))   # creases
        if patch == "knee" and c.face == "front":
            stitched_patch(c, 0, 3, 3, 3, BURLAP_PATCH, 0.16, stitch="#5b4a30")
        if patch == "seat" and c.face == "back":
            stitched_patch(c, 1, 1, 3, 3, DENIM, 0.16)
        if patch == "seat" and c.face == "front":
            c.set(2, 5, TROUSER_INSIDE); c.set(1, 6, TROUSER_INSIDE)                     # a hole
            c.set(2, 6, c.pick(STRAW))
        for x in range(c.w):                              # frayed hem
            r = c.rng.random()
            if r < 0.3:
                c.clear(x, c.h - 1)
            elif r < 0.6:
                c.set(x, c.h - 1, tone(c, c.h - 1, TROUSER_DARK, 0.16))
    return p


def boot_toe(hole=False):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(BOOT)
                if c.face == "top":
                    col = shade(col, 1.12)
                elif c.face == "bottom" or y == c.h - 1:
                    col = c.pick(SOLE)
                c.set(x, y, col)
        if c.face == "front":
            c.set(1, 0, BOOT_HI)
            if hole:                                      # worn through: straw pokes out of the toe
                c.set(2, 0, STRAW_DEEP); c.set(3, 0, c.pick(STRAW_LIGHT))
    return p


def build():
    m = Model("scarecrow", 128, 64, seed=3113)
    head, body = humanoid(m, {
        "head": faces(sack, front=sack_face, top=sack_top, bottom=sack_bottom),
        "body": faces(shirt_body),
        "arm": faces(arm_base),
        "leg": faces(leg_base),
    })
    ra, la, rl, ll = (m.get(n) for n in ("right_arm", "left_arm", "right_leg", "left_leg"))
    pk = Pack(m, [(64, 0, 64, 64), (0, 32, 64, 32), (56, 16, 8, 16), (32, 11, 32, 5)])

    # battered straw hat, tipped a little: crown on the free hat-layer UV, a rounded top, a wide brim
    hat = m.get("hat").part("straw_hat", (0, -8, 0), (-0.04, 0, -0.07))
    hat.cube((32, 0), (-4, -3.7, -4), (8, 3, 8), faces(crown), inflate=0.5)
    pk.add(hat, (-3, -4.9, -3), (6, 1, 6), faces(dome))
    pk.add(hat, (-7, -0.5, -7), (14, 1, 14), faces(brim))
    f0, f1 = FEATHER[0], FEATHER[1]
    feather = [[None, f0, None],
               [f1, FEATHER_SHEEN, f0],
               [f0, FEATHER_SHAFT, f1],
               [f1, FEATHER_SHAFT, FEATHER[2]],
               [None, FEATHER_SHAFT, f0],
               [None, FEATHER_SHAFT, None]]
    quill = hat.part("hat_feather", (4.6, -0.8, 1.6), (-0.6, 0, 0.22))
    pk.add(quill, (0, -6, -1.5), (0, 6, 3), faces(sprite(feather)))

    # rope cinching the sack at the neck, knotted on its left side with a loose end
    neck = head.part("neck_rope")
    pk.add(neck, (-4, -1, -4), (8, 1, 8), faces(neck_rope), inflate=0.3)
    pk.add(neck, (4.1, -1.8, 0.4), (1, 2, 2), faces(rope))
    end = neck.part("neck_rope_end", (4.6, 0, 1.4), (0.2, 0, -0.3))
    pk.add(end, (-0.5, -0.2, -0.5), (1, 3, 1), faces(rope))

    # rope belt knotted on the right hip
    belt = body.part("rope_belt")
    pk.add(belt, (-4, 7.5, -2), (8, 1, 4), faces(hemp), inflate=0.35)
    pk.add(belt, (-3.5, 7, -3.2), (2, 2, 1), faces(hemp))
    bends = belt.part("belt_rope_ends", (-2.5, 9, -2.7), (0.2, 0, 0.12))
    pk.add(bends, (-1, -0.2, -0.5), (1, 3, 1), faces(hemp))
    pk.add(bends, (0, -0.2, -0.5), (1, 2, 1), faces(hemp))

    # straw bursting out of the collar (front corners, back, beside the neck) and out of the rip in
    # the left side
    for name, pivot, rot, (w, h), root, seed in (
            ("collar_straw_right", (-2.6, 0.3, -2.2), (-0.5, 0, 0.55), (4, 4), "top", 11),
            ("collar_straw_left", (2.6, 0.3, -2.2), (-0.5, 0, -0.55), (4, 4), "top", 12),
            ("collar_straw_back", (0, 0.3, 2.2), (0.75, 0, 0), (6, 4), "top", 13),
            ("shoulder_straw_right", (-4.6, 0.6, 0.3), (0, 0, -0.45), (4, 4), "bottom", 14),
            ("shoulder_straw_left", (4.6, 0.6, -0.3), (0, 0, 0.45), (4, 4), "bottom", 15)):
        t = body.part(name, pivot, rot)
        y0 = -0.5 if root == "top" else 0.5 - h
        pk.add(t, (-w / 2, y0, 0), (w, h, 0), faces(sprite(fan(w, h, seed, n=w - 1, root=root))))
    rip = body.part("rip_straw", (4, 5, -0.3), (0, 0.3, 0.35))
    pk.add(rip, (-0.5, -2.5, 0), (5, 5, 0), faces(sprite(fan(5, 5, 21, n=5, root="left"))))
    pk.add(rip, (-0.5, 0, -2.5), (5, 0, 5), faces(sprite(fan(5, 5, 22, n=4, root="left"))))

    # baggy sleeves (an olive elbow patch on the left one) and straw hands bursting from the cuffs
    pk.add(ra.part("right_sleeve"), (-3, -2, -2), (4, 8, 4), faces(sleeve()), inflate=0.3)
    pk.add(la.part("left_sleeve"), (-1, -2, -2), (4, 8, 4), faces(sleeve(patch=True)), inflate=0.3,
           mirror=True)
    hand_z = faces(sprite(tuft(6, 6, 31, "top", full=3, edges=3)))
    hand_x = faces(sprite(tuft(6, 6, 32, "top", full=3, edges=3)))
    for arm, sx in ((ra, -1), (la, 1)):
        side = "right" if sx < 0 else "left"
        h = arm.part(side + "_hand_straw", (sx, 9, 0))
        pk.add(h, (-3, -2, 0), (6, 6, 0), hand_z if sx < 0 else None, mirror=sx > 0, share="hand_z")
        pk.add(h, (0, -2, -3), (0, 6, 6), hand_x if sx < 0 else None, mirror=sx > 0, share="hand_x")

    # baggy trousers (shifted outward so the two legs never overlap), straw at the hems, old boots
    hem = faces(straw_ring(41), left=None)               # inner face left open (sits between the legs)
    for leg, sx, patch in ((rl, -1, "knee"), (ll, 1, "seat")):
        side = "right" if sx < 0 else "left"
        ox = -2.4 if sx < 0 else -1.6
        pk.add(leg.part(side + "_trousers"), (ox, 0, -2), (4, 8, 4), faces(trousers(patch)), inflate=0.25,
               mirror=sx > 0)
        pk.add(leg.part(side + "_hem_straw"), (-2.6 if sx < 0 else -1.4, 7.8, -2), (4, 3, 4),
               hem if sx < 0 else None, inflate=0.35, mirror=sx > 0, share="hem")
        pk.add(leg.part(side + "_boot_toe"), (-2.15 if sx < 0 else -1.85, 10, -3.1), (4, 2, 1),
               faces(boot_toe(hole=sx < 0)),
               mirror=sx > 0)

    pk.apply()
    m.preview = {"right_arm": [0, 0, 1.5708], "left_arm": [0, 0, -1.5708], "head": [0, 0, 0.2]}
    m.save()
    spawn_egg("scarecrow", "#c9a96b", "#8a3b2e", accent="#ff9a3c")


if __name__ == "__main__":
    build()

"""Crag Troll: a mountain troll of the windswept hills and stony peaks. Lanky and hunched: the back
curves over a big pot belly, so the small head juts forward lower than the shoulders. Very long
arms end in enormous hands with chunky block fingers; short bowed legs stand on big flat feet with
yellowed toenails. Its hide is grey-green and stony, speckled with pale lichen, with green moss
grown over the shoulders, the crown and the upper back, where grey cobblestone and andesite rocks
are embedded so that, hunched over, it looks like part of the mountain. The head has a heavy brow
over small deep-set glowing yellow eyes, a long droopy warty nose, big pointed ears, a jutting
underbite lower jaw with two upward yellowed tusks, and a few tufts of coarse dark hair. It wears a
crude hide loincloth on a leather belt, with a lumpy leather toll purse that shows a glint of
emerald.

The hunch lives in the `trunk` and `upper_trunk` decoration parts, so the contract parts rest at
rotation 0: the arms hang straight down and xRot -2.9 holds them overhead, where they grip the
`boulder` (hidden by the code except during the throw wind-up). `jaw` opens with +xRot."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Crag Troll"
LOOT = [item("emerald", 1, 3), item("flint", 0, 3), item("mossy_cobblestone", 1, 3)]
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


def rx(p, a):
    """Rotate a point about the x axis like ModelPart.xRot."""
    x, y, z = p
    ca, sa = math.cos(a), math.sin(a)
    return (x, y * ca - z * sa, y * sa + z * ca)


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position (so both faces of a flat plane get the same pixels)."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
SKIN = ["#6b7564", "#5d6757", "#7b8573", "#656f5e"]
SKIN_LT = ["#7b8573", "#848e7b", "#77816f"]
SKIN_DK = ["#4f584a", "#4a5245", "#535c4d"]
CRACK = "#454d40"
LICHEN = ["#b7c48a", "#a9b67c"]
LICHEN_DK = "#8e9a68"
MOSS = ["#4e7a3a", "#3f6530", "#46703a"]
MOSS_LT = ["#5b8c45", "#62944a"]
ROCK = ["#7d7d7d", "#686868", "#747474", "#828282"]
ROCK_LT = ["#8f8f8f", "#999999"]
ROCK_DK = ["#595959", "#505050"]
MORTAR = "#4a4a4a"
HAIR = ["#2b2620", "#3a3229", "#241f1a"]
HAIR_LT = "#4a4034"
EYE, EYE_DIM, EYE_BASE = "#ffd84a", "#e8b531", "#3a3008"
SOCKET = "#262b22"
TUSK = ["#e6d9a8", "#ddcf98"]
TUSK_SH = "#c9b77e"
TUSK_ROOT = "#a8955e"
TUSK_TIP = "#f3ecd0"
TOOTH = "#d8c890"
GUM = "#4a3a34"
MOUTH = ["#2e2220", "#35282a"]
NAIL = ["#c9b77e", "#b8a46a"]
HIDE = ["#8a6a48", "#7d5f3f", "#94744f"]
HIDE_DK = ["#6a5034", "#5f472e"]
HIDE_FUR = ["#a88a64", "#b39570"]
LEATHER = ["#5a4330", "#4a3626", "#543f2c"]
LEATHER_LT = "#6e5540"
STITCH = "#c9b58a"
EMERALD, EMERALD_LT, EMERALD_DK = "#17b85a", "#7dffb0", "#0d7a3a"
DIRT = ["#6b4a2e", "#5a3d26", "#634429"]
ROOT = "#8a6a44"


def tone(c, y, col, t0=1.06, t1=0.84):
    if c.face in SIDES:
        f = t0 + (t1 - t0) * y / max(1, c.h - 1)
    elif c.face == "top":
        f = 1.1
    else:
        f = 0.78
    return shade(col, round(f * 16) / 16)


# -- stony hide ----------------------------------------------------------------------------------------
def hide(t0=1.06, t1=0.84, lichen=1, cracks=1, moss_top=False, moss_rows=0, seed=0):
    """Grey-green stony hide: blotchy 2 px patches of three close greens (like andesite), darker
    downward; a few hairline cracks; about `lichen` small pale clusters per 140 px. moss_top grows moss over
    the top face, spilling moss_rows down the sides in a ragged edge."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                r = hsh(x // 2, y // 2, c.w * 31 + c.h * 7 + seed)
                base = SKIN[0] if r < 0.55 else (SKIN[1] if r < 0.8 else SKIN[2])
                if c.rng.random() < 0.22:
                    base = c.pick(SKIN)
                if c.face == "top":
                    base = mix(base, SKIN_LT[0], 0.4)
                elif c.face == "bottom":
                    base = c.pick(SKIN_DK)
                c.set(x, y, tone(c, y, base, t0, t1))
        if c.face != "bottom":
            for _ in range(cracks if c.w * c.h > 20 else 0):
                x, y = c.rng.randrange(c.w), c.rng.randrange(max(1, c.h - 1))
                for _ in range(c.rng.randint(2, 4)):      # a short stony crack, lit just below it
                    c.set(x, y, tone(c, y, CRACK, t0, t1))
                    if c.inside(x, y + 1):
                        c.set(x, y + 1, tone(c, y + 1, SKIN[2], t0, t1))
                    x += c.rng.choice((-1, 1))
                    y += c.rng.choice((0, 0, 1))
                    if not c.inside(x, y):
                        break
            expect = lichen * c.w * c.h / 140
            for _ in range(int(expect) + (1 if c.rng.random() < expect % 1 else 0)):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                for (dx, dy) in ((0, 0), (1, 0), (0, 1), (-1, 0))[:c.rng.randint(1, 4)]:
                    if c.inside(x + dx, y + dy):
                        c.set(x + dx, y + dy, LICHEN[0] if (dx, dy) == (0, 0) else c.pick(LICHEN + [LICHEN_DK]))
        if moss_top:
            if c.face == "top":
                moss_patch(c, 0.85)
            elif c.face in SIDES and moss_rows:
                for x in range(c.w):
                    n = moss_rows - (1 if c.rng.random() < 0.35 else 0) + (1 if c.rng.random() < 0.2 else 0)
                    for y in range(min(c.h, n)):
                        c.set(x, y, c.pick(MOSS) if y else c.pick(MOSS_LT + MOSS))
    return p


def moss_patch(c, cover=0.8, x0=0, y0=0, w=None, h=None):
    """Moss: dark and mid greens with bright tufts, ragged at the edge of the patch."""
    w = c.w if w is None else w
    h = c.h if h is None else h
    cx, cy = x0 + (w - 1) / 2, y0 + (h - 1) / 2
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            d = max(abs(x - cx) / max(1, w / 2), abs(y - cy) / max(1, h / 2))
            if d < cover or (d < 1.05 and c.rng.random() < 0.45):
                r = c.rng.random()
                c.set(x, y, c.pick(MOSS_LT) if r < 0.22 else c.pick(MOSS))


# -- rocks -------------------------------------------------------------------------------------------
def cobble(c, pal, light, dark, mortar, t0=1.06, t1=0.86, cell=3.2):
    """Cobblestone: irregular stones (nearest of scattered seeds), each lit along its top edge and
    shaded along its bottom, dark mortar between them."""
    n = max(2, int(c.w * c.h / (cell * cell)))
    seeds = [(c.rng.uniform(-0.5, c.w - 0.5), c.rng.uniform(-0.5, c.h - 0.5), c.rng.randrange(len(pal)))
             for _ in range(n)]

    def owner(x, y):
        return min(range(n), key=lambda i: (x - seeds[i][0]) ** 2 + 1.3 * (y - seeds[i][1]) ** 2)
    own = [[owner(x, y) for x in range(c.w)] for y in range(c.h)]
    for y in range(c.h):
        for x in range(c.w):
            k = own[y][x]
            col = pal[seeds[k][2]]
            if c.rng.random() < 0.2:
                col = c.pick(pal)
            if y > 0 and own[y - 1][x] != k:
                col = c.pick(light)                       # lit top edge of a stone
            if y + 1 < c.h and own[y + 1][x] != k:
                col = c.pick(dark)                        # shaded bottom edge
            if x + 1 < c.w and own[y][x + 1] != k and y + 1 < c.h and own[y + 1][x] != k:
                col = mortar
            elif x + 1 < c.w and own[y][x + 1] != k and c.rng.random() < 0.6:
                col = mortar
            c.set(x, y, tone(c, y, col, t0, t1))


def rock(moss=0.0, lichen=1):
    """A cobblestone / andesite chunk, lit on top, moss growing over the top."""
    def p(c):
        if c.face == "bottom":
            c.noise(ROCK_DK)
            return
        cobble(c, ROCK, ROCK_LT, ROCK_DK, MORTAR, 1.08 if c.face == "top" else 1.04, 0.86)
        for _ in range(lichen if c.w * c.h > 9 else 0):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, LICHEN[0])
            if c.inside(x + 1, y):
                c.set(x + 1, y, LICHEN_DK)
        if moss and c.face == "top":
            moss_patch(c, moss)
        elif moss and c.face in SIDES:
            for x in range(c.w):
                if c.rng.random() < moss:
                    c.set(x, 0, c.pick(MOSS))
                    if c.rng.random() < 0.3 and c.h > 2:
                        c.set(x, 1, c.pick(MOSS))
    return p


# -- body pieces -------------------------------------------------------------------------------------
def belly(c):
    """The pot belly: paler, a sagging fold over the belt, a navel."""
    hide(1.1, 0.88, lichen=0, seed=3)(c)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, c.h - 2, tone(c, c.h - 2, SKIN_DK[0]))   # the fold where it hangs over the belt
            if 1 <= x <= c.w - 2:
                c.set(x, c.h - 3, tone(c, c.h - 3, SKIN[2]))
        for x in range(2, c.w - 2):                       # the lit curve of the belly
            if c.rng.random() < 0.5:
                c.set(x, 1, tone(c, 1, SKIN_LT[1]))
    elif c.face == "back":
        moss_patch(c, 0.6, 2, 0, c.w - 4, 4)
    elif c.face == "bottom":
        c.noise(SKIN_DK)


def pot(c):
    """The roundest part of the pot belly: pale, smooth, lit on top, shaded underneath."""
    for y in range(c.h):
        for x in range(c.w):
            r = hsh(x // 2, y // 2, 77)
            col = SKIN_LT[0] if r < 0.5 else (SKIN[2] if r < 0.85 else SKIN_LT[1])
            if c.face == "bottom":
                col = c.pick(SKIN_DK)
            c.set(x, y, tone(c, y, col, 1.08, 0.88))
    if c.face == "front":
        c.set(c.w // 2, c.h - 3, SKIN_DK[1])           # the navel
        c.set(c.w // 2, c.h - 2, CRACK)
        for x in (0, c.w - 1):
            for y in range(c.h):
                c.set(x, y, shade(c.get(x, y), 0.9))   # the curve falls away at the sides


def chest(c):
    hide(1.08, 0.94, lichen=2, moss_top=True, moss_rows=2, seed=5)(c)
    if c.face == "back":                              # moss creeps down the hunched back
        moss_patch(c, 0.65, 1, 0, c.w - 2, c.h - 5)
    elif c.face == "front":
        for (x, y) in ((4, 5), (5, 6), (9, 5), (8, 7), (6, 8)):
            c.set(x, y, c.pick(HAIR))                 # coarse chest hair


def belt(c):
    if c.face in ("top", "bottom"):
        c.noise(LEATHER)
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, LEATHER_LT if y == 0 else c.pick(LEATHER))
    for x in range(1, c.w, 3):
        c.set(x, c.h - 1, STITCH)
    if c.face == "front":                             # a bone toggle for a buckle
        c.set(c.w // 2, 0, "#e0d4b0"); c.set(c.w // 2 - 1, 1, "#e0d4b0"); c.set(c.w // 2, 1, "#c4b48a")


def pouch(c):
    """The toll purse: lumpy leather, a drawstring, a green glint of emerald peeking out on top."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(HIDE if c.face == "top" else HIDE_DK)
            c.set(x, y, tone(c, y, col, 1.1, 0.86))
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, STITCH if x % 2 == 0 else LEATHER_LT)
    if c.face == "top":
        c.set(1, 0, EMERALD); c.set(1, 1, EMERALD_DK); c.set(2, 0, EMERALD_LT)
    if c.face == "front":
        c.set(1, 1, EMERALD_LT); c.set(2, 1, EMERALD)


def flap(seed):
    """Hide loincloth flap (a flat plane): mottled hide, a pale fur edge at the top, a ragged hem
    cut out at the bottom. Both faces painted alike."""
    def p(c):
        mirror = c.face == "back"
        for y in range(c.h):
            for x in range(c.w):
                u = c.w - 1 - x if mirror else x
                cut = y >= c.h - 1 - int(hsh(u, seed) * 2.6)
                if cut:
                    c.clear(x, y)
                    continue
                r = hsh(u, y, seed)
                col = HIDE[int(r * len(HIDE))]
                if r > 0.86:
                    col = HIDE_DK[0]
                if y == 0:
                    col = HIDE_FUR[int(r * 2)]
                elif u in (0, c.w - 1):
                    col = shade(col, 0.85)
                elif u % 3 == 1 and y > 2:
                    col = shade(col, 0.9)                 # stiff hanging folds
                c.set(x, y, shade(col, 1.0 - 0.12 * y / c.h))
    return p


# -- head ----------------------------------------------------------------------------------------------
def cranium(c):
    hide(1.06, 0.9, lichen=1, moss_top=True, moss_rows=1, seed=9)(c)
    if c.face == "front":
        # rows: 0 forehead (behind the brow at 1-2), 3 eyes, 4-5 cheeks, 6-7 upper lip (the jaw
        # juts out in front of row 7)
        for x in range(c.w):
            c.set(x, 3, SOCKET)
            c.set(x, 4, shade(c.get(x, 4), 0.85))
            c.set(x, 6, mix(c.pick(SKIN), GUM, 0.3))
            c.set(x, 7, GUM)
        for (o, i) in ((1, 2), (8, 7)):               # small deep-set glowing eyes
            c.glow(i, 3, EYE)
            c.set(i, 3, EYE_BASE)
            c.glow(o, 3, "#6a5410")
            c.set(o, 3, SOCKET)
        for x in (3, 6):                              # cheekbones under the eyes
            c.set(x, 4, SKIN[2])
    elif c.face == "bottom":                          # the roof of the mouth, seen when it roars
        for y in range(2, c.h):
            for x in range(1, c.w - 1):
                c.set(x, y, MOUTH[(x + y) % 2])
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 3, SOCKET)
        for y in range(3, c.h):                       # tufts of dark hair on the jowls
            if c.rng.random() < 0.45:
                c.set(fx(c, c.w - 3), y, c.pick(HAIR))
            if c.rng.random() < 0.3:
                c.set(fx(c, c.w - 2), y, c.pick(HAIR))


def brow(c):
    hide(1.12, 0.96, lichen=0, cracks=0, moss_top=True, moss_rows=0, seed=11)(c)
    if c.face == "bottom":
        c.noise([SOCKET, "#2c3227"])
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.8))
        c.set(4, 1, CRACK)
        c.set(3, 0, SKIN_LT[0]); c.set(5, 0, SKIN_LT[0])


NOSE = ["#6f6a5a", "#665f50", "#77705f"]


def nose(c):
    """Long droopy nose: a warmer, browner grey-green than the face, with warts."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, tone(c, y, c.pick(NOSE), 1.1, 0.86))
    for _ in range(2):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        c.set(x, y, "#8e8a72")
        if c.inside(x, y + 1):
            c.set(x, y + 1, "#4e4a3e")


def nose_tip(c):
    nose(c)
    if c.face == "bottom":                            # nostrils under the bulb
        c.set(1, 1, "#2a2420"); c.set(2, 1, "#2a2420")
    elif c.face == "front":
        c.set(1, 0, "#a29c82")                        # a shiny wart on the tip
        c.set(2, c.h - 1, "#4e4a3e")


def wart(c):
    c.noise(["#8a8670", "#7e7a66"])
    if c.face == "top":
        c.set(0, 0, "#a29c82")


def jaw(c):
    hide(1.0, 0.82, lichen=1, cracks=0, seed=13)(c)
    if c.face == "top":                               # lower teeth along the front, gums, a mouth
        for y in range(c.h - 2):
            for x in range(1, c.w - 1):
                c.set(x, y, MOUTH[(x * 3 + y) % 2])
        for x in range(2, c.w - 2):                   # the tongue
            for y in range(2, c.h - 3):
                c.set(x, y, "#7a4a44" if (x + y) % 3 else "#6a3e3a")
        for x in range(c.w):
            c.set(x, c.h - 1, TOOTH if x % 2 == 0 else "#b8a878")
            c.set(x, c.h - 2, GUM)
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, 0, mix(c.get(x, 0), GUM, 0.35))
        for (x, y) in ((3, 2), (5, 2), (4, 1), (2, 2), (6, 1)):   # stubbly chin hairs
            c.set(x, y, c.pick(HAIR))


def tusk(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(TUSK) if c.face in ("front", "top", "right") else TUSK_SH
            if y == c.h - 1 and c.face in SIDES and c.h > 1:
                col = TUSK_ROOT
            c.set(x, y, col)
    if c.face == "top":
        c.set(0, 0, TUSK_TIP)


def ear(part):
    """Big pointed ear in steps: grey-green, a dark fleshy hollow on the front, hairy at the point."""
    def p(c):
        hide(1.06, 0.92, lichen=0, cracks=0, seed=17)(c)
        if c.face == "front" and part in ("base", "mid"):   # the hollow of the ear
            for y in range(1, c.h - 1):
                for x in range(c.w):
                    edge = (part == "base" and x == 0)
                    c.set(x, y, c.get(x, y) if edge else mix(c.get(x, y), "#4e3e3a", 0.5 + 0.1 * (y % 2)))
        if c.face == "top":
            for x in range(c.w):
                c.set(x, c.h - 1, SKIN_LT[0])         # a lit rim along the top of the ear
        if part in ("tip", "point"):
            for y in range(c.h):
                for x in range(c.w):
                    if c.rng.random() < 0.45:
                        c.set(x, y, c.pick(HAIR))     # a hairy ear tip
    return p


def tuft(seed):
    """Coarse dark hair on a flat cut-out plane: single strands of different lengths with gaps,
    fanning out; both faces alike."""
    def p(c):
        mirror = c.face == "back"
        for x in range(c.w):
            u = c.w - 1 - x if mirror else x
            edge = u in (0, c.w - 1)
            length = 0 if (hsh(u, seed) < 0.25 and not edge) else int(1 + hsh(u, seed, 3) * (c.h - (3 if edge else 1)))
            for y in range(c.h):
                if y < c.h - length:
                    c.clear(x, y)
                else:
                    r = hsh(u, y, seed + 1)
                    col = HAIR[int(r * len(HAIR))]
                    if y == c.h - length and r > 0.5:
                        col = HAIR_LT
                    c.set(x, y, col)
    return p


# -- limbs -------------------------------------------------------------------------------------------
def palm(c):
    hide(1.02, 0.86, lichen=1, cracks=1, seed=19)(c)
    if c.face == "bottom":
        c.noise(SKIN_DK)
    elif c.face in SIDES:                             # knuckles along the bottom edge
        for x in range(c.w):
            if x % 3 == 1:
                c.set(x, c.h - 1, shade(c.pick(SKIN_LT), 1.0))
            elif x % 3 == 2:
                c.set(x, c.h - 1, CRACK)


def finger(c):
    hide(1.02, 0.86, lichen=0, cracks=0, seed=23)(c)
    if c.face == "bottom":
        c.noise(NAIL)                                 # thick yellowed nails
    elif c.face in SIDES:
        c.set(0, 1, CRACK)                            # a knuckle crease
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(NAIL))


def foot(c):
    hide(0.98, 0.84, lichen=1, cracks=1, seed=29)(c)
    if c.face == "bottom":
        c.noise(SKIN_DK)


def toe(c):
    """A blunt toe with a thick yellowed nail on top of its tip."""
    hide(1.0, 0.86, lichen=0, cracks=0, seed=31)(c)
    if c.face == "front":
        c.set(0, 0, NAIL[0]); c.set(1, 0, NAIL[1])
    elif c.face == "top":
        c.set(0, c.h - 1, NAIL[0]); c.set(1, c.h - 1, NAIL[0])


# -- boulder -------------------------------------------------------------------------------------------
def boulder_paint(moss=0.0, dirt=False):
    """Cobblestone with mossy-cobblestone moss on top; dirt and roots underneath where it was torn
    out of the hillside."""
    def p(c):
        rock(moss=moss, lichen=1)(c)
        if not dirt:
            return
        if c.face == "bottom":
            for y in range(c.h):
                for x in range(c.w):
                    col = c.pick(DIRT)
                    if hsh(x, y, 5) < 0.12:
                        col = ROOT
                    c.set(x, y, col)
        elif c.face in SIDES:
            for x in range(c.w):
                n = 1 + (1 if c.rng.random() < 0.4 else 0)
                for y in range(c.h - n, c.h):
                    c.set(x, y, c.pick(DIRT))
                if c.rng.random() < 0.15 and c.h > 3:
                    c.set(x, c.h - n - 1, ROOT)
    return p


# -- the model ---------------------------------------------------------------------------------------
BODY = (0, 8, 1)                  # hip pivot: 16 px above the ground
LEAN_LOW, LEAN_HIGH = 0.2, 0.6    # the belly leans a little, the chest a lot more (a curved hunch)
UPPER = (0, -11, 0)               # where the upper trunk bends, in trunk space
SHOULDER = (9, -10.5, 0.5)      # in upper-trunk space
NECK = (0, -11, -6)               # in upper-trunk space: the front of the short neck
ARM_GRIP = -2.9                   # arms raised overhead to hold the boulder
PALM_MID = 25.5                     # arm-space y of the middle of the palm


def to_body(p):
    """Upper-trunk space -> body space through both lean rotations."""
    q = rx(p, LEAN_HIGH)
    q = (q[0] + UPPER[0], q[1] + UPPER[1], q[2] + UPPER[2])
    return rx(q, LEAN_LOW)


def make():
    m = Model("crag_troll", 128, 128, seed=7171)
    pk = Pack(m)

    body = m.part("body", BODY)
    trunk = body.part("trunk", (0, 0, 0), (LEAN_LOW, 0, 0))
    pk.add(trunk, (-5.5, -4, -4.5), (11, 6, 9), faces(hide(0.92, 0.82, seed=1)))
    pk.add(trunk, (-6.5, -12, -8), (13, 9, 11), faces(belly))
    pk.add(trunk, (-5.5, -11, -10), (11, 7, 2), faces(pot))      # the pot of the belly
    pk.add(trunk, (-5.5, -3.4, -4.5), (11, 2, 9), faces(belt), inflate=0.35)
    pk.add(trunk, (-5.8, -2.6, -6.4), (3, 3, 2), faces(pouch))
    for name, piv, rot, org, size, moss in (                       # rocks low on the back too
            ("low_back_rock_1", (2, -8, 3), (0.1, -0.3, 0.15), (-2.5, -2, -1), (5, 4, 3), 0.4),
            ("low_back_rock_2", (-3, -4.5, 3), (-0.2, 0.2, -0.3), (-1.5, -1.5, -1), (3, 3, 2), 0.0)):
        pk.add(trunk.part(name, piv, rot), org, size, faces(rock(moss=moss)))

    upper = trunk.part("upper_trunk", UPPER, (LEAN_HIGH, 0, 0))
    pk.add(upper, (-7, -13, -3.5), (14, 13, 8), faces(chest))
    pk.add(upper, (-5.5, -15, -1.5), (11, 3, 5), faces(hide(1.12, 1.02, moss_top=True, moss_rows=2, seed=7)))
    pk.add(upper, (-2.5, -12, -6.5), (5, 4, 4), faces(hide(1.0, 0.86, lichen=0, seed=8)))   # short neck

    # rocks grown into the back and shoulders: part of the mountain
    for name, piv, rot, org, size, moss in (
            ("back_rock_1", (-2.5, -9.5, 4.5), (0.2, 0.3, 0.1), (-3, -2.5, -1.5), (6, 5, 4), 0.5),
            ("back_rock_2", (3, -5, 4.5), (-0.1, -0.2, 0.2), (-2.5, -2, -1.5), (5, 4, 4), 0.35),
            ("back_rock_3", (-1.5, -1, 4), (-0.2, 0.1, -0.2), (-2, -2, -1.5), (4, 3, 3), 0.0),
            ("shoulder_rock_1", (4, -14.5, 1.5), (0.1, 0.4, 0.2), (-2.5, -2, -2), (5, 3, 4), 0.6),
            ("shoulder_rock_2", (-4, -14.5, 2.5), (0.3, -0.3, -0.2), (-2, -2.5, -2), (4, 4, 4), 0.5)):
        r = upper.part(name, piv, rot)
        pk.add(r, org, size, faces(rock(moss=moss)))

    # loincloth flaps hang straight down from the belt (children of body, so they stay vertical)
    pk.add(body.part("loincloth_front", rx((0, -1.5, -4.9), LEAN_LOW)), (-3.5, 0, 0), (7, 8, 0), faces(flap(3)))
    pk.add(body.part("loincloth_back", rx((0, -1.5, 5.6), LEAN_LOW)), (-4, 0, 0), (8, 7, 0), faces(flap(8)))

    # head: small, jutting forward lower than the shoulders
    head = body.part("head", to_body(NECK))
    pk.add(head, (-5, -5, -7), (10, 8, 8), faces(cranium))
    pk.add(head, (-5.5, -4, -8.5), (11, 2, 2), faces(brow))
    ns = head.part("nose", (0, -2, -7.5), (0.7, 0, 0))
    pk.add(ns, (-1, -0.5, -4), (2, 3, 5), faces(nose))
    pk.add(ns, (-1.5, 0.5, -6.5), (3, 3, 3), faces(nose_tip))
    pk.add(ns, (0.6, -1, -2.5), (1, 1, 1), faces(wart))
    pk.add(ns, (-1.9, 0.6, -5.5), (1, 1, 1), faces(wart), share="wart_b")
    jw = head.part("jaw", (0, 3, -1))
    pk.add(jw, (-5, 0, -9), (10, 3, 9), faces(jaw))
    for sx in (-1, 1):                                # tusks rising from the corners of the underbite
        left = sx > 0
        pk.add(jw, (-5 if sx < 0 else 3, -2, -9.5), (2, 2, 2), None if left else faces(tusk),
               mirror=left, share="tusk")
        pk.add(jw, (-5 if sx < 0 else 4, -3, -9), (1, 1, 1), None if left else faces(tusk),
               mirror=left, share="tusk_tip")
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        e = head.part(side + "_ear", (5 * sx, -2, -3.5), (0, 0.35 * -sx, 0.18 * -sx))
        for key, x0, y0, size in (("ear_base", -4, -2.5, (4, 5, 1)), ("ear_mid", -7, -2.5, (3, 4, 1)),
                                  ("ear_tip", -9, -2.8, (2, 2, 1)), ("ear_point", -10, -3.3, (1, 1, 1))):
            pk.add(e, (x0 if sx < 0 else -x0 - size[0], y0, -0.5), size, None if left else faces(ear(key[4:])),
                   mirror=left, share=key)
    for i, yaw in enumerate((0.785, -0.785)):         # a tuft of coarse hair on the crown
        hair = head.part("crown_hair_" + "ab"[i], (0, -5, -3), (-0.25, yaw, 0))
        pk.add(hair, (-3, -5, 0), (6, 5, 0), None if i else faces(tuft(5)), share="tuft")

    # arms: very long and thin, hanging straight down; enormous hands with block fingers
    sh = to_body(SHOULDER)
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        arm = body.part(side + "_arm", (sh[0] * sx, sh[1], sh[2]))
        pk.add(arm, (-2.5, -2.5, -2.5), (5, 5, 5), None if left else faces(hide(1.1, 0.96, moss_top=True, moss_rows=2, seed=41)),
               mirror=left, share="cap")
        pk.add(arm, (-1.5, 2, -1.5), (3, 12, 3), None if left else faces(hide(1.0, 0.9, seed=42)), mirror=left,
               share="upper_arm")
        pk.add(arm, (-2, 13, -2), (4, 10, 4), None if left else faces(hide(0.98, 0.86, seed=43)), mirror=left,
               share="forearm")
        pk.add(arm, (-4, 22, -4.5), (8, 7, 9), None if left else faces(palm), mirror=left, share="palm")
        rk = arm.part(side + "_arm_rock", (1.5 * sx, -2.5, 0.5), (0.2, 0.4 * sx, 0.3 * sx))
        pk.add(rk, (-2, -2, -2), (4, 3, 4), None if left else faces(rock(moss=0.5)), mirror=left, share="arm_rock")
        fg = arm.part(side + "_fingers", (1.5 * -sx, 28.5, 0), (0, 0, 0.35 * sx))
        for i, z in enumerate((-4, -1, 2)):
            pk.add(fg, (-1, -0.5, z), (2, 5, 2), None if (left or i) else faces(finger), mirror=left, share="finger")
        th = arm.part(side + "_thumb", (2 * -sx, 24, -4.5), (-0.35, 0, 0.2 * sx))
        pk.add(th, (-1, -0.5, -1), (2, 4, 2), None if left else faces(finger), mirror=left, share="thumb")

    # legs: short and bowed (thigh out, shin back in), big flat feet with yellow toenails
    a = 0.2
    fy = 8 + 7 * math.cos(a) + 6.5 * math.cos(a)      # world y of the foot pivot
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        leg = m.part(side + "_leg", (4.5 * sx, 8, 2))
        thigh = leg.part(side + "_thigh", (0, 0, 0), (0, 0, -a * sx))
        pk.add(thigh, (-2.5, -1, -3), (5, 8, 6), None if left else faces(hide(0.94, 0.84, seed=51)), mirror=left,
               share="thigh")
        shin = thigh.part(side + "_shin", (0, 7, 0), (0, 0, 2 * a * sx))
        pk.add(shin, (-2, -0.5, -2.5), (4, 7, 5), None if left else faces(hide(0.92, 0.82, seed=52)), mirror=left,
               share="shin")
        ft = shin.part(side + "_foot", (0, 6.5, 0), (0, 0, -a * sx))
        pk.add(ft, (-4, 24 - fy - 3, -8), (8, 3, 12), None if left else faces(foot), mirror=left, share="foot")
        for i, x in enumerate((-3.5, -1, 1.5)):
            pk.add(ft, (x, 24 - fy - 2, -10), (2, 2, 2), None if (left or i) else faces(toe), mirror=left,
                   share="toe")

    # the boulder, held overhead between both hands when the arms are raised to ARM_GRIP
    gy = sh[1] + BODY[1] + PALM_MID * math.cos(ARM_GRIP)
    gz = sh[2] + BODY[2] + PALM_MID * math.sin(ARM_GRIP)
    bd = m.part("boulder", (0, round(gy, 2), round(gz, 2)))
    pk.add(bd, (-7, -7, -6.5), (14, 12, 13), faces(boulder_paint(moss=0.75), bottom=boulder_paint(dirt=True)))
    pk.add(bd, (-4.5, -9, -4), (9, 3, 8), faces(boulder_paint(moss=0.9)))
    pk.add(bd, (-4, -4, -8), (8, 7, 2), faces(boulder_paint(moss=0.3)))
    pk.add(bd, (-3, -3, 6), (6, 6, 2), faces(boulder_paint()))
    pk.add(bd, (-5, 4, -4.5), (10, 2, 9), faces(boulder_paint(dirt=True)))

    pk.apply()
    return m


def build():
    m = make()
    m.save()
    spawn_egg("crag_troll", "#6b7564", "#4e7a3a", accent="#e8c547")


if __name__ == "__main__":
    build()

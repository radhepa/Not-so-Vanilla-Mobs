"""Cinder Newt: a Nether newt. Soft charcoal-black skin with a fine warm grain, two rows of glowing
orange-yellow spots down the back and tail and a scatter along the flanks, a glowing ember-orange
belly and throat that creeps up the lower flanks, bulging gold eyes on the corners of a broad flat
head with a wide smile, a tall paddle-flat tail, and short sturdy legs splayed out to the sides with
spread toes.

Glow: every glowing pixel has a dim ember base on the texture and the bright colour on the emissive
layer, so the spots shine in the dark without washing out to white by day. Legs are children of the
body and stick straight out sideways, so the code can sweep them in yaw for a lizard walk."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Cinder Newt"
LOOT = [item("magma_cream", 0, 1)]
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
SKIN = ["#2b2523", "#2e2826", "#272120", "#312a27", "#29231f"]
SKIN_LT = ["#3e3430", "#43372f"]                 # warm grain catching the lava light
SKIN_DK = "#1b1615"
# glowing colours: (dim base on the texture, bright colour on the glow layer). The glow layer is
# added on top, so base + glow is what you see by day and the glow alone in the dark.
SPOT = ("#5a2a0c", "#e8761a")                    # orange spots
SPOT_HOT = ("#6a400f", "#f2b232")                # their yellow-hot centres
EMBER = ("#3a1a0a", "#8a3a0c")                   # small dim specks
BELLY = ("#4a1c0a", "#d9581a")                   # ember-orange belly
BELLY_DIM = ("#33160a", "#7a2e0c")               # where the belly fades into the flanks
EYE = "#e9b531"
EYE_LT = "#ffe98a"
EYE_DK = "#a8771a"
PUPIL = "#120b08"
MOUTH = "#120d0c"

SIDES = ("front", "back", "left", "right")


def hot(c, x, y, pair, k=1.0):
    """A glowing pixel: dim base colour on the texture, the bright one on the emissive layer."""
    if not c.inside(x, y):
        return
    base, glow = pair
    c.set(x, y, shade(base, k))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), shade(glow, k))


def skin(c, x, y, top=False):
    col = c.pick(SKIN)
    r = c.rng.random()
    if r < (0.16 if top else 0.1):
        col = c.pick(SKIN_LT)                    # granular skin: warm light flecks
    elif r > 0.9:
        col = SKIN_DK
    return col


def spotted(spots, belly_rows=0, under=False):
    """Charcoal skin with glowing spots at the given face pixels; belly_rows = how many bottom rows of a
    side face are lit by the orange belly; under = the face is the glowing belly itself."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if under or c.face == "bottom" and belly_rows:
                    # the belly: ember orange, a few dark blotches like a fire-bellied newt
                    if c.rng.random() < 0.12 or x in (0, c.w - 1) and c.rng.random() < 0.5:
                        c.set(x, y, shade(SKIN[0], 1.1))
                    else:
                        hot(c, x, y, BELLY, 0.92 + 0.12 * c.rng.random())
                    continue
                col = skin(c, x, y, c.face == "top")
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.08 - 0.12 * y / (c.h - 1))
                c.set(x, y, col)
                if c.face in ("left", "right") and belly_rows:
                    if y == c.h - 1:
                        hot(c, x, y, BELLY if c.rng.random() < 0.6 else BELLY_DIM, 0.9)
                    elif y == c.h - 2 and belly_rows > 1 and c.rng.random() < 0.25:
                        hot(c, x, y, BELLY_DIM, 0.8)
        rows = spots.get(c.face)
        if rows:
            for y, row in enumerate(rows):
                for i, ch in enumerate(row):
                    x = c.w - 1 - i if c.face == "right" else i   # side maps run front to back
                    if ch in GLOWS:
                        hot(c, x, y, GLOWS[ch], 0.92 + 0.1 * c.rng.random())
    return p


GLOWS = {"o": SPOT, "y": SPOT_HOT, "e": EMBER}

# spot maps per face ('.' skin, 'o' orange, 'y' yellow-hot, 'e' a dim ember speck). Top faces run
# row 0 = back; side faces are written front-to-back for both sides (the right face is flipped).
BODY_SPOTS = {
    # 5 wide x 9 deep; the middle three columns sit under the ridge, so the spots here are the
    # dorsolateral rows along each edge of the back
    "top": ["o....",
            "....y",
            ".....",
            "y...o",
            ".....",
            "....o",
            "o....",
            "y...e",
            "....."],
    # 9 deep x 3 tall: a scatter high on the flanks
    "right": ["..o....y.",
              "..y...e..",
              "........."],
    "left": [".y.....o.",
             "..e...y..",
             "........."],
}
RIDGE_SPOTS = {
    # 3 wide x 8 deep: a few blotches down the spine
    "top": ["...",
            ".o.",
            ".y.",
            "...",
            "...",
            "oy.",
            "...",
            ".e."],
    "right": ["..o..y..", "........"][:1],
    "left": [".y...o..", "........"][:1],
}
HEAD_SPOTS = {
    # 6 wide x 5 deep: the glowing glands behind the eyes
    "top": ["oy..yo",
            ".o..o.",
            "......",
            "......",
            "......"],
}
TAIL_SPOTS = {
    "top": ["..", ".o", "..", "y.", "..", ".e"],
    "right": ["..y..o", ".o....", "......"],
    "left": [".o...y", "..y...", "......"],
}
TIP_SPOTS = {
    "top": [".", "y", ".", ".", "o", "."],
    "right": ["..o..e", "......"],
    "left": [".e..o.", "......"],
}


# -- head --------------------------------------------------------------------------------------------
def skull_front(c):
    # 6 x 2: a broad rounded snout, two nostrils, the corners shaded round
    for y in range(c.h):
        for x in range(c.w):
            col = skin(c, x, y)
            if x in (0, c.w - 1):
                col = shade(col, 0.78)
            c.set(x, y, col)
    c.set(1, 0, SKIN_DK)
    c.set(c.w - 2, 0, SKIN_DK)
    c.set(2, 0, shade(SKIN_LT[0], 1.1))


def skull_side(c):
    # 5 deep x 2: the long smile along the bottom row, curling up at the corner of the mouth
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(skin(c, x, y), 1.04 - 0.08 * y))
    for i in range(c.w - 1):
        c.set(fx(c, i), 1, shade(c.get(fx(c, i), 1), 0.7))
    c.set(fx(c, c.w - 1), 1, MOUTH)
    c.set(fx(c, c.w - 2), 0, shade(SKIN[0], 0.8))


def skull_top(c):
    spotted(HEAD_SPOTS)(c)
    for x in range(c.w):                         # the snout end rounds off
        c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.9))
    c.set(0, c.h - 1, shade(SKIN[0], 0.75))
    c.set(c.w - 1, c.h - 1, shade(SKIN[0], 0.75))


def jaw(c):
    if c.face == "top":
        c.fill("#5a2418")                        # inside of the mouth
        return
    if c.face == "bottom":                       # the glowing throat
        for y in range(c.h):
            for x in range(c.w):
                hot(c, x, y, BELLY, 0.85 + 0.1 * c.rng.random())
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(skin(c, x, y), 0.85))
    if c.face in ("left", "right", "front"):
        for x in range(c.w):
            if c.rng.random() < 0.5:
                hot(c, x, c.h - 1, BELLY_DIM)


def eye(c):
    # a bulging 2x2 eye on each top corner of the head, overhanging the side: dark lid on top, a gold
    # iris with a black pupil and a glint on the outer side, gold peeking over the brow in front
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(SKIN), 1.18 if c.face == "top" else 0.95))
    if c.face == "front":
        c.set(0, 0, EYE)
        c.set(1, 0, EYE_DK)
        c.set(0, 1, EYE_DK)
        c.set(1, 1, EYE_DK)
    elif c.face == "right":                      # the outer side (the left eye mirrors this face)
        c.set(fx(c, 0), 0, EYE_LT)
        c.set(fx(c, 1), 0, EYE)
        c.set(fx(c, 0), 1, EYE)
        c.set(fx(c, 1), 1, PUPIL)
        c.set(fx(c, 0), 1, PUPIL)
        c.set(fx(c, 1), 1, EYE_DK)
    elif c.face == "top":
        c.set(0, c.h - 1, shade(EYE_DK, 0.8))


# -- legs --------------------------------------------------------------------------------------------
def limb(c):
    for y in range(c.h):
        for x in range(c.w):
            col = skin(c, x, y, c.face == "top")
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.05 - 0.15 * y / (c.h - 1))
            c.set(x, y, col)
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                hot(c, x, y, BELLY_DIM)


def foot(c):
    # 3 x 3 pad, row 0 = back: four splayed toes, their tips a dusky orange
    if c.face in ("top", "bottom"):
        rows = ["s.s", "sss", "tst"] if c.face == "top" else ["sss", "sss", "sss"]
        for y in range(c.h):
            for x in range(c.w):
                ch = rows[y][x]
                col = shade(c.pick(SKIN), 1.1) if ch == "s" else (shade(c.pick(SKIN), 0.75) if ch == "." else "#7a3c1a")
                c.set(x, y, col)
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, "#6a3418" if c.face == "front" and x % 2 == 0 else shade(c.pick(SKIN), 0.9))


def build():
    m = Model("cinder_newt", 64, 64, seed=6161)
    pk = Pack(m)

    # body: pivot at the middle of the torso (y 20.5); torso 5 wide x 3 tall x 9 long, belly at y 22,
    # with a low ridge down the back to round it off
    body = m.part("body", (0, 20.5, 0))
    pk.add(body, (-2.5, -1.5, -4.5), (5, 3, 9), faces(spotted(BODY_SPOTS, belly_rows=2)))
    pk.add(body, (-1.5, -2.5, -4), (3, 1, 8), faces(spotted(RIDGE_SPOTS)))

    # head: broad, flat and round-snouted, a lower jaw underneath with the glowing throat, and big
    # eyes bulging from its top corners
    head = body.part("head", (0, -0.5, -4.5))
    pk.add(head, (-3, -1.5, -5), (6, 2, 5), faces(spotted({}), top=skull_top, front=skull_front,
                                                  right=skull_side, left=skull_side))
    jw = head.part("jaw", (0, 0.5, 0))
    pk.add(jw, (-2.5, 0, -4.5), (5, 1, 5), faces(jaw), inflate=-0.03)
    for sx in (-1, 1):
        pk.add(head, (-3.6 if sx < 0 else 1.6, -2.6, -4.2), (2, 2, 2), faces(eye), inflate=-0.1,
               mirror=sx > 0, share="eye")

    # tail: tall and paddle-flat, drooping to the ground; the tip is thinner still
    tail = body.part("tail", (0, -0.3, 4.5), (-0.18, 0, 0))
    pk.add(tail, (-1, -1.2, -0.5), (2, 3, 6), faces(spotted(TAIL_SPOTS, belly_rows=1)))
    tip = tail.part("tail_tip", (0, 0.3, 5.5), (-0.12, 0, 0))
    pk.add(tip, (-0.5, -1.1, -0.5), (1, 2, 6), faces(spotted(TIP_SPOTS, belly_rows=1)))

    # legs: from the sides of the torso straight out, then down to a spread foot on the ground
    # (front feet turned a little forward, hind feet back, in a lizard's sprawl)
    for name, x, z, yaw in (("right_front_leg", -2.5, -3.0, -0.35), ("left_front_leg", 2.5, -3.0, 0.35),
                            ("right_hind_leg", -2.5, 3.0, 0.35), ("left_hind_leg", 2.5, 3.0, -0.35)):
        sx = -1 if name.startswith("right") else 1
        mir = sx > 0
        lg = body.part(name, (x, 0.5, z), (0, yaw, 0))
        pk.add(lg, (-1.7 if sx < 0 else -0.3, -0.5, -1), (2, 2, 2), None if mir else faces(limb),
               mirror=mir, share="upper", inflate=0.0)
        pk.add(lg, (-3.2 if sx < 0 else 1.2, 0.8, -1), (2, 2, 2), None if mir else faces(limb),
               mirror=mir, share="lower", inflate=-0.1)
        pk.add(lg, (-4.5 if sx < 0 else 1.5, 2.25, -2.2), (3, 1, 3), None if mir else faces(foot),
               mirror=mir, share="foot", inflate=-0.25)

    pk.apply()
    m.save()
    spawn_egg("cinder_newt", "#2b2523", "#ff9a2a", accent="#ffd64a")


if __name__ == "__main__":
    build()

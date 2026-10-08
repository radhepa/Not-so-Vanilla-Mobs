"""Hermit Crab: a small reddish-orange crab living in a borrowed shell. The coiled shell (`shell`) sits
on the ground behind it and is always visible; everything that ducks inside when the crab hides is
under `body`: the front of the carapace, a big right claw and a small left one, eyes on stalks and
three striped legs a side. Three shells share one geometry and differ only in paint: a pink conch
(the default texture), a sandy spiral whelk and a weathered blue snail shell."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Hermit Crab'
LOOT = []
TAGS = ['arthropod']


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None):
        self.items.append((part, origin, size, paint, mirror, share))

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
        for i, (part, origin, size, paint, mirror, share) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


SIDES = ("front", "back", "left", "right")

# -- the crab ----------------------------------------------------------------------------------------
CRAB = ["#d65a2f", "#cf532a", "#db6336", "#c94d27"]
CRAB_LT = "#f08a55"
CRAB_DK = "#9a3519"
TIP = ["#4e2016", "#5c2819"]
BAND = ["#f2d2b0", "#ecc8a2"]
SPOT = "#f4b98a"
EYE = "#15101a"
EYE_HI = "#f4f0ea"


def carapace(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CRAB)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.06 - 0.25 * y / (c.h - 1))
                if y == 0:
                    col = mix(col, CRAB_LT, 0.4)
            elif c.face == "bottom":
                col = shade(col, 0.72)
            c.set(x, y, col)
    c.speckle([SPOT], 0.08)
    if c.face == "front":                                # mouthparts
        cx = c.w // 2
        c.set(cx, c.h - 1, CRAB_DK)
        c.set(cx - 1, c.h - 1, shade(CRAB[0], 0.8)); c.set(cx + 1, c.h - 1, shade(CRAB[0], 0.8))
        c.set(cx, c.h - 2, shade(CRAB[0], 0.85))


def stalk(c):
    c.noise([CRAB_LT, shade(CRAB_LT, 0.92)])


def eye(c):
    c.fill(EYE)
    if c.face == "front":
        c.set(0, 0, EYE_HI)
    elif c.face == "right":
        c.set(c.w - 1, 0, "#3a3040")
    elif c.face == "left":
        c.set(0, 0, "#3a3040")


def claw_arm(c):
    carapace(c)


def claw_hand(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CRAB)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.08 - 0.25 * y / (c.h - 1))
            elif c.face == "top":
                col = mix(col, CRAB_LT, 0.3)
            elif c.face == "bottom":
                col = shade(col, 0.75)
            c.set(x, y, col)
    c.speckle([SPOT, shade(SPOT, 0.9)], 0.18)            # knobbly claw
    # the pincer: a dark gap across the front splits it into two fingers with darker tips
    mid = c.h // 2
    if c.face == "front":
        for x in range(c.w):
            for y in range(c.h):
                c.set(x, y, mix(c.get(x, y), TIP[1], 0.35))
            c.set(x, mid, TIP[0])
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), mid, TIP[0])
        for y in range(c.h):
            if y != mid:
                c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), TIP[1], 0.35))


def leg(c):
    """A right leg runs along -x: column 0 is the foot on the long faces."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CRAB)
            if c.face == "bottom":
                col = shade(col, 0.75)
            c.set(x, y, col)
    if c.face in ("top", "bottom", "front", "back"):
        for x in (c.w // 2,):                           # a pale joint band
            for y in range(c.h):
                c.set(x, y, c.pick(BAND))
        for y in range(c.h):
            c.set(0, y, c.pick(TIP))
    elif c.face == "right":
        c.noise(TIP)


# -- the shells --------------------------------------------------------------------------------------
CONCH = dict(style="conch",
             base=["#efa996", "#ea9f8c", "#f2b3a1", "#e6a390"], light="#fde0cf", dark="#b86c5e",
             band="#df9784", lip=["#f7a3ae", "#f294a3"], inner="#c9626f", deep="#5a2a33",
             knob=["#fbe8da", "#f6dccb"])
WHELK = dict(style="whelk",
             base=["#dfc9a0", "#d7c096", "#e5d0aa", "#dbc49a"], light="#f2e6c9", dark="#a78a5e",
             band="#8d6842", lip=["#f0d9b4", "#e9cfa6"], inner="#c49a6c", deep="#4a3726",
             knob=["#f0e2c2", "#e8d7b3"])
SNAIL = dict(style="snail",
             base=["#7d9db2", "#7696ab", "#85a4b8", "#7191a6"], light="#b4cad7", dark="#4e697e",
             band="#5a768e", lip=["#c7d5de", "#bccbd5"], inner="#6c8597", deep="#222d38",
             knob=["#e6dfca", "#d9d1ba"], moss=["#7d9867", "#8aa572"])


def shell_paint(pal, kind):
    """kind: whorl1 (the big body whorl), whorl2, whorl3, apex, lip, knob."""
    style = pal["style"]

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(pal["base"])
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.08 - 0.3 * y / (c.h - 1))
                    if y == 0:
                        col = mix(col, pal["light"], 0.35)
                elif c.face in SIDES:
                    col = shade(col, 0.98)
                elif c.face == "top":
                    col = shade(col, 1.06)
                    if x in (0, c.w - 1) or y in (0, c.h - 1):
                        col = mix(col, pal["light"], 0.5)            # the rounded shoulder
                elif c.face == "bottom":
                    col = shade(col, 0.66)
                c.set(x, y, col)

        if c.face in ("left", "right", "back", "front") and kind != "knob":
            if style == "conch":       # fine growth lines across the whorl
                for x in range(1, c.w, 2):
                    for y in range(c.h):
                        if c.rng.random() < 0.55:
                            c.set(x, y, mix(c.get(x, y), pal["dark"], 0.18))
            elif style == "whelk":     # zigzag lightning streaks running down the whorl
                for x0 in range(c.rng.randrange(3), c.w + c.h, 3):
                    for y in range(c.h):
                        xx = x0 - y // 2 - (1 if y % 4 == 3 else 0)
                        if c.inside(xx, y):
                            c.set(xx, y, mix(c.get(xx, y), pal["band"], 0.6))
            elif style == "snail":     # a dark spiral band and pale weathered patches
                if c.h >= 3:
                    yb = c.h // 2 - 1
                    for x in range(c.w):
                        c.set(x, yb, mix(c.get(x, yb), pal["band"], 0.8))
                for _ in range(max(1, c.w * c.h // 9)):
                    x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                    c.set(x, y, mix(c.get(x, y), pal["light"], 0.55))
                    if c.inside(x + 1, y):
                        c.set(x + 1, y, mix(c.get(x + 1, y), pal["light"], 0.35))
                if kind == "whorl1":
                    for x in range(c.w):                             # algae near the sand
                        if c.rng.random() < 0.35:
                            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(pal["moss"]), 0.7))
        if c.face == "top" and style == "snail":
            for _ in range(max(1, c.w * c.h // 8)):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, mix(c.get(x, y), pal["light"], 0.45))

        # suture: the seam where a whorl comes out of the bigger one in front of it
        if kind in ("whorl2", "whorl3", "apex") and c.face in ("left", "right"):
            for y in range(c.h):
                c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), pal["dark"], 0.6))
        if kind in ("whorl2", "whorl3", "apex") and c.face == "top":
            for x in range(c.w):
                c.set(x, c.h - 1, mix(c.get(x, c.h - 1), pal["dark"], 0.45))
        if kind == "apex" and c.face == "back":
            c.set(c.w // 2, c.h // 2, pal["dark"])

        if kind == "whorl1" and c.face == "front":
            aperture(c, pal)
        elif kind == "lip":
            if c.face in ("front", "top", "left"):
                for y in range(c.h):
                    for x in range(c.w):
                        col = c.pick(pal["lip"])
                        if c.face == "front" and c.h > 1:
                            col = shade(col, 1.04 - 0.12 * y / (c.h - 1))
                        c.set(x, y, col)
            elif c.face == "right":                                   # the outer flare: ridged
                for y in range(c.h):
                    c.set(c.w - 1, y, mix(c.get(c.w - 1, y), pal["lip"][0], 0.6))
        elif kind == "knob":
            c.noise(pal["knob"])
            if c.face in ("front", "back", "left", "right"):
                c.set(0, c.h - 1, shade(c.pick(pal["knob"]), 0.85))
    return p


APERTURE = [          # column 0 is the mob's right, where the flared lip is
    "LLLbbbb",
    "LldLbbb",
    "LdDdLbb",
    "LdDDdLb",
    "LdDDDdL",
]


def aperture(c, pal):
    """The shell's mouth on the front of the body whorl: a glossy lip round a dark hollow; the crab
    sits in it, and it is what you see when the crab has ducked inside."""
    for y in range(c.h):
        for x in range(c.w):
            ch = APERTURE[min(y, len(APERTURE) - 1)][min(x, c.w - 1)] if x < len(APERTURE[0]) else "b"
            if ch == "L":
                c.set(x, y, shade(c.pick(pal["lip"]), 1.0 - 0.05 * y))
            elif ch == "l":
                c.set(x, y, mix(pal["lip"][0], pal["inner"], 0.5))
            elif ch == "d":
                c.set(x, y, pal["inner"] if y < 2 else mix(pal["inner"], pal["deep"], 0.45))
            elif ch == "D":
                c.set(x, y, shade(pal["deep"], 1.0 - 0.06 * y))


def make(texture_id, pal):
    """Build the hermit crab with the given shell palette. Geometry is identical for every shell."""
    m = Model("hermit_crab", 64, 64, seed=1414, texture_id=texture_id)
    pk = Pack(m)

    # shell: child of root, lying on the ground like an empty seashell (pivot at y 24), so it looks
    # right on its own. The coil runs back and up: each whorl is smaller, higher, further back and a
    # little further left, ending in the apex; a flared lip on the right of the mouth and knobs on
    # the shoulder make it read as a conch.
    shell = m.part("shell", (0, 24, 0))
    pk.add(shell, (-3.5, -5, -2), (7, 5, 4), faces(shell_paint(pal, "whorl1")))
    pk.add(shell, (-2.5, -6, -2), (5, 1, 4), faces(shell_paint(pal, "cap")))
    pk.add(shell, (-4.5, -4.5, -2.5), (1, 4.5, 3.5), faces(shell_paint(pal, "lip")))
    for x, z in ((-3, -1), (2, 0.5)):
        pk.add(shell, (x, -6, z), (1, 1, 1), faces(shell_paint(pal, "knob")), share="knob")
    # the spire: each whorl is its own child part, rolled a little further round the coil axis and
    # tipped up a little more, so the stack twists like a real spiral instead of a tidy staircase
    w2 = shell.part("shell_whorl2", (0.75, -4.5, 3), (0.12, 0, -0.15))
    pk.add(w2, (-2.75, -2.5, -1.5), (5.5, 5, 3), faces(shell_paint(pal, "whorl2")))
    pk.add(w2, (-3, -3, 0), (1, 1, 1), faces(shell_paint(pal, "knob")), share="knob")
    pk.add(w2, (2, -3, 0), (1, 1, 1), faces(shell_paint(pal, "knob")), share="knob")
    w3 = shell.part("shell_whorl3", (1.25, -6.75, 5.25), (0.25, 0, -0.3))
    pk.add(w3, (-2, -1.75, -1.25), (4, 3.5, 2.5), faces(shell_paint(pal, "whorl3")))
    ap = shell.part("shell_apex", (1.6, -8.9, 6.4), (0.4, 0, -0.45))
    pk.add(ap, (-1, -1, -0.75), (2, 2, 1.5), faces(shell_paint(pal, "apex")))

    # body: the part of the crab that sticks out of the shell's mouth
    body = m.part("body", (0, 21.5, -1.5))
    pk.add(body, (-2.5, -1.5, -2.5), (5, 3, 4), faces(carapace))

    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        e = body.part(side + "_eye", (1 * sx, -1.5, -2), (0.1, 0, 0.18 * sx))
        pk.add(e, (-0.5, -2, -0.5), (1, 2, 1), None if left else faces(stalk), mirror=left, share="stalk")
        pk.add(e, (-0.75, -3.5, -0.75), (1.5, 1.5, 1.5), None if left else faces(eye), mirror=left, share="eye")

    # claws: the right one is much bigger (like a real hermit crab), both held up in front
    rc = body.part("right_claw", (-2, 0.5, -2.5), (0, -0.3, 0))
    pk.add(rc, (-0.75, -0.5, -1.5), (1.5, 1, 1.5), faces(claw_arm))
    pk.add(rc, (-2, -1.75, -4.5), (3, 3, 3), faces(claw_hand))
    lc = body.part("left_claw", (2, 0.8, -2.5), (0, 0.3, 0))
    pk.add(lc, (-0.5, -0.5, -1.5), (1, 1, 1.5), faces(claw_arm))
    pk.add(lc, (-0.75, -1, -3.5), (2, 2, 2), faces(claw_hand))

    # legs: yaw fans them front-to-back, roll tips the feet down to y 24
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        for i, (z, yaw) in enumerate(((-2.4, -0.55), (-1.3, -0.1), (-0.4, 0.4)), start=1):
            L, py = 4.5, 22
            drop = 24 - py - 0.5
            roll = math.asin(min(1.0, drop / (L * math.cos(yaw))))
            lg = body.part(f"{side}_leg{i}", (2.3 * sx, 0.5, z),
                           (0, yaw if sx < 0 else -yaw, -roll if sx < 0 else roll))
            pk.add(lg, (-4.5 if sx < 0 else 0, -0.5, -0.5), (4.5, 1, 1), None if left else faces(leg),
                   mirror=left, share="leg")

    pk.apply()
    return m


def build():
    make(None, CONCH).save()
    make("hermit_crab_whelk", WHELK).save(geometry=False)
    make("hermit_crab_snail", SNAIL).save(geometry=False)
    spawn_egg("hermit_crab", "#d65a2f", "#f1b6a4", accent="#fde3d3")


if __name__ == "__main__":
    build()

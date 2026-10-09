"""Hummingbird: a tiny hummingbird, smaller than a parrot, hovering with its body tilted head-up. A
little teardrop body, a round head with a long needle bill held level, a bright iridescent throat
patch (gorget), a white chest, black bead eyes with a white spot behind, long narrow wings (the code
beats them so fast they blur) and a small forked tail.
Three colourways share the geometry:
  hummingbird          ruby-throated: emerald back and crown, ruby-red throat, white chest
  hummingbird_violet   violet-crowned: bronze-green back, violet cap, white throat, red bill
  hummingbird_rufous   rufous: orange-copper all over, orange-red throat, a white bib
The wings are zero-thickness planes hinged at the shoulders; the code flaps them round z."""
import math
import os
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Hummingbird"
LOOT = []
TAGS = ["fall_damage_immune"]

# Debug only: HUMMINGBIRD_POSE=perch previews the wings folded back.
POSE = os.environ.get("HUMMINGBIRD_POSE", "")


# -- texture packing (as in otter.py): biggest cubes first, each with a 1 px clear margin -------------
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
        used = {}
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
    """A stable random number per pixel, so the top and bottom of a plane match exactly."""
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


SIDES = ("front", "back", "left", "right")

# -- palettes ----------------------------------------------------------------------------------------
RUBY = dict(
    back=["#2f9a52", "#279049", "#36a85c", "#2b934e"],
    sheen=["#5fd486", "#7be39c", "#4cc277"],          # iridescent glints
    crown=["#2a8a49", "#309552", "#25803f"],
    belly=["#f2f1ea", "#ebe9e1", "#f6f5ef"],
    flank=["#a9b8a0", "#9fb095", "#b4c2aa"],          # greenish-grey flanks
    throat=["#d0173a", "#c0122f", "#dc1f45"],
    throat_hi=["#ff4d6d", "#ff6f86"],
    throat_dk="#7d0b20",
    wing=["#3b3a40", "#34333a", "#403f46"],
    wing_edge="#5c5b63",
    tail=["#2a3a30", "#24332a"],
    tail_tip=["#1b221d"],
    bill="#18171a",
    bill_tip="#2c2a2e",
    eye="#0c0a0b",
    spot="#ffffff",
)

VIOLET = dict(
    back=["#7c8a3c", "#73823a", "#869447", "#6f7d34"],  # bronze-green
    sheen=["#a8b85c", "#b9c56a", "#9aab50"],
    crown=["#7b3bd2", "#8a4be3", "#6c2fc0"],          # violet cap
    belly=["#f5f4f0", "#eeede8", "#faf9f6"],
    flank=["#c9c6b8", "#bfbcad", "#d2cfc2"],
    throat=["#f8f7f3", "#f1f0eb", "#fbfbf8"],          # white throat
    throat_hi=["#ffffff"],
    throat_dk="#d8d6cf",
    wing=["#3d3a35", "#36332f", "#44413b"],
    wing_edge="#5f5b54",
    tail=["#6a6c48", "#5f613f"],
    tail_tip=["#3e3f2c"],
    bill="#d8392c",                                    # red bill with a dark tip
    bill_tip="#2b1d1b",
    eye="#0c0a0b",
    spot="#ffffff",
    cap_hi=["#a776f5", "#b88cff"],
)

RUFOUS = dict(
    back=["#c96a28", "#bf6123", "#d3762f", "#c56726"],
    sheen=["#e8914a", "#f0a25a", "#dc8340"],
    crown=["#b65c22", "#c0652a", "#ad541e"],
    belly=["#f1e6d8", "#eadccb", "#f5ece0"],            # the white bib, warming down the belly
    flank=["#d98a4b", "#e09656", "#d07f40"],
    throat=["#f05a1c", "#e44f16", "#fa6a26"],
    throat_hi=["#ffb04a", "#ffc266"],
    throat_dk="#9e3410",
    wing=["#4a3a33", "#42332d", "#523f37"],
    wing_edge="#6e5446",
    tail=["#d0702b", "#c56628"],
    tail_tip=["#3a2a22"],
    bill="#18171a",
    bill_tip="#2c2a2e",
    eye="#0c0a0b",
    spot="#ffffff",
)


# -- body --------------------------------------------------------------------------------------------
def body_paint(P):
    """Back colour with iridescent glints on top, white chest and belly underneath, the flanks
    grading from the back colour into the belly down the sides."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = c.pick(P["back"])
                    if c.rng.random() < 0.18:
                        col = c.pick(P["sheen"])
                elif c.face == "bottom":
                    col = c.pick(P["belly"])
                    if y == 0:
                        col = mix(col, c.pick(P["flank"]), 0.5)       # row 0 = the vent (back)
                elif c.face == "front":
                    col = c.pick(P["belly"])
                elif c.face == "back":
                    col = c.pick(P["back"]) if y == 0 else mix(c.pick(P["back"]), c.pick(P["flank"]), 0.5)
                else:
                    if y == 0:
                        col = c.pick(P["back"])
                        if c.rng.random() < 0.25:
                            col = c.pick(P["sheen"])
                    elif y == 1:
                        col = mix(c.pick(P["back"]), c.pick(P["flank"]), 0.6)
                    else:
                        col = c.pick(P["flank"]) if fx(c, 0) != x else c.pick(P["belly"])
                c.set(x, y, col)
    return p


# -- head --------------------------------------------------------------------------------------------
def head_paint(P):
    cap = P.get("cap_hi")

    def crown(c):
        col = c.pick(P["crown"])
        if cap and c.rng.random() < 0.3:
            col = c.pick(cap)
        elif not cap and c.rng.random() < 0.2:
            col = c.pick(P["sheen"])
        return col

    def p(c):
        if c.face == "top":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, crown(c))
        elif c.face == "bottom":                  # the gorget under the chin
            for y in range(c.h):
                for x in range(c.w):
                    col = c.pick(P["throat"])
                    if (x + y) % 2 == 0 and c.rng.random() < 0.5:
                        col = c.pick(P["throat_hi"])
                    c.set(x, y, col)
            for x in range(c.w):
                c.set(x, 0, P["throat_dk"])           # row 0 = the back edge, into the chest
        elif c.face == "front":
            # 3 x 3: crown on top, the bill base in the middle, the gorget below
            for x in range(c.w):
                c.set(x, 0, crown(c))
                c.set(x, 1, c.pick(P["back"]) if not cap else crown(c))
                c.set(x, 2, c.pick(P["throat_hi"]) if x == 1 else c.pick(P["throat"]))
            c.set(1, 1, mix(c.get(1, 1), P["bill"], 0.5))
        elif c.face == "back":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, crown(c) if y == 0 else c.pick(P["back"]))
        else:
            # sides: crown on top; a black bead eye at the front of the middle row with a white
            # spot just behind it; the gorget wraps round the bottom row
            for x in range(c.w):
                c.set(x, 0, crown(c))
                c.set(x, 1, c.pick(P["back"]) if not cap else mix(c.pick(P["back"]), crown(c), 0.4))
                col = c.pick(P["throat"])
                if fx(c, x) == c.w - 1:
                    col = mix(col, P["throat_dk"], 0.5)
                elif c.rng.random() < 0.35:
                    col = c.pick(P["throat_hi"])
                c.set(x, 2, col)
            c.set(fx(c, 0), 1, P["eye"])
            c.set(fx(c, 1), 1, mix(c.get(fx(c, 1), 1), P["spot"], 0.55))
            c.set(fx(c, 0), 0, mix(crown(c), P["eye"], 0.35))
    return p


def bill_paint(P):
    def p(c):
        c.fill(P["bill"])
        if c.face == "front":
            c.fill(P["bill_tip"])
        elif c.face in ("left", "right", "top", "bottom") and c.w * c.h > 1:
            # the far (front) end darkens to the tip; row 0 of top/bottom is the back
            for x in range(c.w):
                for y in range(c.h):
                    along = (x if c.face == "right" else c.w - 1 - x) / max(1, c.w - 1) \
                        if c.face in ("left", "right") else y / max(1, c.h - 1)
                    if along > 0.6:
                        c.set(x, y, P["bill_tip"])
    return p


# -- wings and tail ----------------------------------------------------------------------------------
# Wing plane, 6 long x 2 wide: column 0 = the wing tip (it reaches toward -x on the right wing);
# row 0 = the trailing edge (top faces put the back edge on row 0), row 1 = the leading edge.
WING_MASK = [
    "..####",
    ".#####",
]


def wing_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if WING_MASK[y][x] != "#":
                    c.clear(x, y)
                    continue
                r = _h(x, y, 17)
                col = P["wing"][int(r * len(P["wing"])) % len(P["wing"])]
                if y == 1:
                    col = mix(col, P["wing_edge"], 0.6)              # the stiff leading edge
                if x >= c.w - 1:
                    col = mix(col, P["back"][0], 0.5)               # shoulder coverts
                c.set(x, y, col)
    return p


# Tail plane, 4 wide x 3 long; row 0 = the tip (the back). A shallow fork.
TAIL_MASK = [
    "#..#",
    "####",
    ".##.",
]


def tail_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if TAIL_MASK[y][x] != "#":
                    c.clear(x, y)
                    continue
                r = _h(x, y, 29)
                col = P["tail"][int(r * len(P["tail"])) % len(P["tail"])]
                if y == 0 or TAIL_MASK[y - 1][x] != "#":
                    col = P["tail_tip"][0]
                c.set(x, y, col)
    return p


def rump_paint(P):
    def p(c):
        c.noise(P["back"])
        if c.face == "bottom":
            c.noise(P["flank"])
        elif c.face == "top" and c.rng.random() < 0.5:
            c.set(0, 0, c.pick(P["sheen"]))
    return p


BODY_TILT = -0.5     # head-up hovering posture; the head, wings and tail level themselves again


def make(texture_id, P):
    m = Model("hummingbird", 32, 32, seed=3030, texture_id=texture_id)
    pk = Pack(m)

    # body: a small 3 x 3 x 4 teardrop, pivot at its middle, tilted head-up. A narrower rump behind
    # carries the tail.
    body = m.part("body", (0, 20, 0), (BODY_TILT, 0, 0))
    pk.add(body, (-1.5, -1.5, -2), (3, 3, 5), faces(body_paint(P)))
    pk.add(body, (-1, -1, 3), (2, 2, 1), faces(rump_paint(P)))

    # head: on the front-top of the body, turned level again; the needle bill runs straight forward
    head = body.part("head", (0, -0.6, -1.7), (-BODY_TILT, 0, 0))
    pk.add(head, (-1.5, -2, -2.5), (3, 3, 3), faces(head_paint(P)))
    pk.add(head, (-0.5, -0.5, -6.5), (1, 1, 4), faces(bill_paint(P)), inflate=-0.25)

    # wings: long narrow blades from the shoulders, spread level (mid-beat) at rest
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        w = body.part(f"{side}_wing", (1.4 * sx, -1.4, -0.5), (-BODY_TILT, 0.25 * -sx, 0.1 * -sx))
        pk.add(w, (-6 if not left else 0, 0, -1), (6, 0, 2), None if left else faces(wing_paint(P)),
               mirror=left, share="wing")

    # tail: a small forked fan behind the rump, held out straight (pointing down with the body)
    tail = body.part("tail", (0, 0, 3.5), (0.15, 0, 0))
    pk.add(tail, (-2, 0, 0), (4, 0, 3), faces(tail_paint(P)))

    if POSE == "perch":
        m.preview = {"body": [-0.15, 0, 0], "head": [0.15, 0, 0],
                     "right_wing": [0.15, 1.35, -0.2], "left_wing": [0.15, -1.35, 0.2]}

    pk.apply()
    return m


def build():
    make(None, RUBY).save()
    make("hummingbird_violet", VIOLET).save(geometry=False)
    make("hummingbird_rufous", RUFOUS).save(geometry=False)
    spawn_egg("hummingbird", "#2f9a52", "#f2f1ea", accent="#d0173a")


if __name__ == "__main__":
    build()

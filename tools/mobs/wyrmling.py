"""Wyrmling: a cat-sized ember-red dragon. Cream belly and throat, little bone horns, big golden
eyes (emissive), membrane wings held half-open over its back, a spiked tail ending in a spade."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Wyrmling'
LOOT = []
TAGS = ['fall_damage_immune']


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


# -- palette -----------------------------------------------------------------------------------------
RED = ["#b8331f", "#b2301d", "#bd3621", "#ae2f1c"]
RED_DARK = "#7e2013"
RED_LIGHT = "#d6532d"
CREAM = ["#f1dba8", "#e9d09a", "#f4e2b4"]
CREAM_DARK = "#d1b37b"
HORN = ["#efe3c4", "#e7d9b5"]
HORN_BASE = "#b99d74"
MEMB = ["#f08a4b", "#ea7f43", "#f39556"]
VEIN = "#b8442a"
GOLD = "#ffc83a"
GOLD_HI = "#ffe68c"
PUPIL = "#3a1806"


def scales(grad=0.26, top=1.06, bottom=0.78, belly=False):
    """Ember scales: staggered highlights, darker toward the bottom; belly=True gives a cream
    bottom row on side faces."""
    def p(c):
        for y in range(c.h):
            if c.face == "top":
                f = top
            elif c.face == "bottom":
                f = bottom
            else:
                f = 1.06 - grad * (y / max(1, c.h - 1))
            for x in range(c.w):
                col = c.pick(RED)
                if (x + 2 * (y % 2)) % 4 == 0 and c.rng.random() < 0.6:
                    col = mix(col, RED_LIGHT, 0.3)
                c.set(x, y, shade(col, f))
        if belly and c.face in ("left", "right", "front", "back"):
            for x in range(c.w):
                c.set(x, c.h - 1, shade(c.pick(CREAM), 0.9))
    return p


def belly_plates(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CREAM)
            if y % 2 == 0:
                col = mix(col, CREAM_DARK, 0.6)
            if x in (0, c.w - 1):
                col = shade(col, 0.9)
            c.set(x, y, col)


def chest(c):
    scales()(c)
    for y in range(2, c.h):
        for x in range(1, c.w - 1):
            if y == 2 and x in (1, c.w - 2):
                continue                                 # rounded top corners
            col = c.pick(CREAM)
            if y % 2 == 1:
                col = mix(col, CREAM_DARK, 0.5)
            c.set(x, y, col)


def throat(c):
    """Front of the neck: cream plates with a red edge."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CREAM)
            if y % 2 == 0:
                col = mix(col, CREAM_DARK, 0.55)
            c.set(x, y, col)
    for y in range(c.h):
        c.set(0, y, c.pick(RED)); c.set(c.w - 1, y, c.pick(RED))


def skull_side(c):
    scales(grad=0.2)(c)
    for i in range(c.w):
        c.set(i, 0, shade(c.get(i, 0), 0.82))          # brow ridge
    a, b = fx(c, 0), fx(c, 1)
    c.glow(b, 1, GOLD_HI)
    c.glow(b, 2, GOLD)
    c.glow(a, 1, GOLD)
    c.set(a, 2, PUPIL)
    c.set(fx(c, 2), 1, RED_DARK)                       # a little eyeliner behind the eye
    c.set(fx(c, 0), 3, shade(c.pick(RED), 0.8))


def skull_front(c):
    scales(grad=0.2)(c)
    for x in range(c.w):
        c.set(x, 0, shade(c.get(x, 0), 0.85))
    for x in (0, c.w - 1):
        c.glow(x, 1, GOLD)
        c.set(x, 2, PUPIL)
    c.set(2, 1, shade(c.pick(RED), 0.9))


def skull_top(c):
    scales(top=1.04)(c)
    for y in range(c.h):                                # a darker ridge down the middle
        c.set(c.w // 2, y, shade(c.pick(RED), 0.85))


def snout(c):
    scales(grad=0.1)(c)
    if c.face == "top":
        c.set(0, c.h - 1, RED_DARK); c.set(c.w - 1, c.h - 1, RED_DARK)   # nostrils
    if c.face == "front":
        c.set(0, 0, RED_DARK); c.set(c.w - 1, 0, RED_DARK)
    if c.face == "bottom":
        c.noise(["#5a1a12", "#64201a"])                                 # roof of the mouth
        c.set(0, c.h - 1, "#f6ecd6"); c.set(c.w - 1, c.h - 1, "#f6ecd6")  # tiny fangs


def jaw(c):
    if c.face == "top":                                  # inside of the mouth
        c.noise(["#6e2219", "#7a2a1e"])
        for x in range(c.w):
            c.set(x, c.h - 1, "#f6ecd6" if x % 2 == 0 else "#7a2a1e")
        c.set(1, 1, "#c45a54"); c.set(1, 0, "#c45a54")  # tongue
        return
    if c.face == "bottom" or c.face == "front":
        c.noise(CREAM)
        return
    scales(grad=0.0)(c)
    c.set(fx(c, 0), 0, shade(c.pick(CREAM), 0.92))


def horn(c):
    for y in range(c.h):
        for x in range(c.w):
            t = y / max(1, c.h - 1)
            c.set(x, y, mix(c.pick(HORN), HORN_BASE, t * 0.8))
    if c.face == "top":
        c.fill("#fbf3dc")


def neck(c):
    scales(grad=0.15)(c)


def leg(c):
    scales(grad=0.35)(c)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, c.h - 1, "#f3e7c8")                 # claws
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), c.h - 1, "#f3e7c8")
    if c.face == "bottom":
        c.noise(["#6d1c11", "#5e180f"])


def spike(c):
    c.noise(HORN)
    if c.face in ("front", "back", "left", "right"):
        for x in range(c.w):
            c.set(x, c.h - 1, HORN_BASE)


def bone(c):
    scales(grad=0.3)(c)
    if c.face == "top":
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(RED), 1.05))


# -- membranes: top/bottom of a flat plane. column 0 = the wing's outer end, row 0 = trailing edge.
def membrane(depths, veins, outer_claw=False):
    def p(c):
        dark = 0.94 if c.face == "top" else 1.0     # the bottom face is the one seen from outside at rest
        for x in range(c.w):
            keep = depths[x]
            for y in range(c.h):
                if y < c.h - keep:
                    c.clear(x, y)
                    continue
                col = c.pick(MEMB)
                if x in veins:
                    col = VEIN
                elif y == c.h - keep:
                    col = mix(col, VEIN, 0.35)            # darker rim on the scalloped edge
                elif y == c.h - 1:
                    col = shade(col, 1.06)
                c.set(x, y, shade(col, dark))
    return faces(top=p, bottom=p)


SPADE = [
    "..#..",
    ".###.",
    "#####",
    ".###.",
    "..#..",
]


def spade(c):
    for y, row in enumerate(SPADE):
        for x, ch in enumerate(row):
            if ch == ".":
                c.clear(x, y)
            else:
                col = c.pick(RED)
                if x == 2 or y == 2:
                    col = RED_DARK if (x == 2 and y == 2) else shade(col, 0.88)
                if abs(x - 2) + abs(y - 2) == 2:
                    col = mix(col, RED_LIGHT, 0.5)
                c.set(x, y, col)


WING_REST = (0, 1.2, 1.9)    # right wing (x, y, z), folded along the flank; the left wing mirrors y and z
TIP_REST = (0, 0.5, 0)


def build():
    m = Model("wyrmling", 64, 64, seed=2026)
    pk = Pack(m)

    # body: pivot y 18.5; cube y 16-21, z -4..4
    body = m.part("body", (0, 18.5, 0))
    pk.add(body, (-3, -2.5, -4), (6, 5, 8), faces(scales(), front=chest, bottom=belly_plates))
    for i, z in enumerate((-2.5, 0, 2.5)):            # little spines down the back
        pk.add(body, (-0.5, -3.5, z - 0.5), (1, 1, 1), faces(spike) if i == 0 else None, share="spike")

    # neck -> head -> jaw
    neck_p = body.part("neck", (0, -1.5, -3.5), (0.55, 0, 0))
    pk.add(neck_p, (-1.5, -3.5, -1.5), (3, 4, 3), faces(neck, front=throat))
    pk.add(neck_p, (-0.5, -3, 1), (1, 1, 1), None, share="spike")
    head = neck_p.part("head", (0, -3, -0.5), (-0.55, 0, 0))
    pk.add(head, (-2.5, -4, -3), (5, 4, 5), faces(scales(), front=skull_front, right=skull_side,
                                                   left=skull_side, top=skull_top))
    pk.add(head, (-1.5, -2, -6), (3, 1, 3), faces(snout))
    jaw_p = head.part("jaw", (0, -1, -3))
    pk.add(jaw_p, (-1.5, 0, -3), (3, 1, 3), faces(jaw))
    for name, x, rz in (("right_horn", -1.5, -0.3), ("left_horn", 1.5, 0.3)):
        hp = head.part(name, (x, -3.5, 1), (-0.8, 0, rz))
        left = name.startswith("left")
        pk.add(hp, (-0.5, -3, -0.5), (1, 3, 1), None if left else faces(horn), mirror=left, share="horn")

    # wings: hinge along the top edge of the body; each spans outward along x with its chord running
    # back along z. At rest they are raised over the back (z rotation); the code flaps around z.
    for side, sx in (("right", -1), ("left", 1)):
        left = side == "left"
        w = body.part(f"{side}_wing", (3 * sx, -2.5, -2.5), (0, WING_REST[1] * -sx, WING_REST[2] * -sx))
        o = lambda x0, wd: x0 if not left else -x0 - wd      # mirror an x origin for the left side
        pk.add(w, (o(-4, 4), -0.5, -0.5), (4, 1, 1), None if left else faces(bone), mirror=left, share="wbone")
        pk.add(w, (o(-4, 4), 0, 0.5), (4, 0, 5),
               None if left else membrane([5, 3, 4, 4], {0}), mirror=left, share="wmemb")
        t = w.part(f"{side}_wing_tip", (4 * sx, 0, 0), (0, TIP_REST[1] * -sx, TIP_REST[2] * -sx))
        pk.add(t, (o(-5, 5), -0.5, -0.5), (5, 1, 1), None if left else faces(bone), mirror=left, share="tbone")
        pk.add(t, (o(-5, 5), 0, 0.5), (5, 0, 5),
               None if left else membrane([2, 3, 5, 3, 5], {2, 4}), mirror=left, share="tmemb")
        pk.add(t, (o(-0.5, 1), -1.5, -0.5), (1, 1, 1), None, share="spike")   # wrist claw

    # tail -> tail_tip with spines and a spade
    tail = body.part("tail", (0, -1, 3.5), (-0.3, 0, 0))
    pk.add(tail, (-1, -1, 0), (2, 2, 5), faces(scales(grad=0.2), bottom=belly_plates))
    pk.add(tail, (-0.5, -2, 1.5), (1, 1, 1), None, share="spike")
    tip = tail.part("tail_tip", (0, 0, 4.5), (0.45, 0, 0))
    pk.add(tip, (-0.5, -0.5, 0), (1, 1, 5), faces(scales(grad=0.2)))
    pk.add(tip, (0, -2.5, 3), (0, 5, 5), faces(right=spade, left=spade))

    # legs: front slim, hind a bit deeper
    for name, x, z, size, org in (("right_front_leg", -2, -2.5, (2, 4, 2), (-1, 0, -1)),
                                  ("left_front_leg", 2, -2.5, (2, 4, 2), (-1, 0, -1)),
                                  ("right_hind_leg", -2, 2.5, (2, 4, 3), (-1, 0, -1.5)),
                                  ("left_hind_leg", 2, 2.5, (2, 4, 3), (-1, 0, -1.5))):
        lg = body.part(name, (x, 1.5, z))
        left = name.startswith("left")
        pk.add(lg, org, size, None if left else faces(leg), mirror=left, share=name.split("_", 1)[1])

    pk.apply()
    m.save()
    spawn_egg("wyrmling", "#b8331f", "#f1dba8", accent="#ffc83a")


if __name__ == "__main__":
    build()

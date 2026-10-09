"""Otter: a sleek river otter that can be tamed as a pet. A long, low body in glossy dark
chocolate-brown fur with a lighter sheen down the back, a short broad flat-topped head with small
round ears, bright little black eyes with a white glint, a dark button nose and pale whiskers, a
cream face, chin, throat and chest, short dark webbed paws and a long thick tail that tapers and
darkens toward the tip. Head, legs and tail hang off the body, so the code can roll the whole otter
onto its back (body zRot = pi) to float belly-up; the belly is painted for that."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Otter"
LOOT = []
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
FUR = ["#5a3a26", "#5a3a26", "#573825", "#5d3c28", "#4e3221", "#63412b"]
SHEEN = ["#6e4a31", "#734e35", "#694630"]
FUR_DK = ["#3f2819", "#442b1c", "#3a2516"]
BELLY = ["#7c5b3f", "#836246", "#76563b"]
CREAM = ["#d8c2a0", "#cdb592", "#dcc8a8"]
CREAM_SH = ["#bea583", "#b69d7b"]
NOSE = "#1a1210"
NOSE_HI = "#4d3d36"
MOUTH = "#6b5340"
EYE = "#0d0907"
SHINE = "#fbfbf6"
EAR_IN = "#2e1d12"
PAW = ["#3a261a", "#33221a", "#402a1d"]
TOE = "#5c4433"
WHISKER = "#efe7d8"
PAD = "#ad9474"

SIDES = ("front", "back", "left", "right")


def fur(top=1.08, grad=0.24, sheen=0.12, belly_rows=0, under=None):
    """Glossy sleek fur: lighter on top with streaks of sheen running along the body, darker down
    the sides, short darker hair strokes. under = palette for the bottom face."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = shade(c.pick(FUR), top)
                elif c.face == "bottom":
                    col = c.pick(under or FUR_DK)
                else:
                    col = shade(c.pick(FUR), 1.06 - grad * (y / max(1, c.h - 1)))
                    if belly_rows and y >= c.h - belly_rows:
                        col = mix(col, c.pick(under or BELLY), 0.55)
                c.set(x, y, col)
        if c.face == "top":                    # sheen: short streaks running front to back
            for _ in range(int(c.w * c.h * sheen / 2) + 1):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                for yy in (y, y + 1):
                    if c.inside(x, yy):
                        c.set(x, yy, c.pick(SHEEN))
        elif c.face in ("left", "right") and c.h > 1:   # sleek hair lies along the body: dashes
            for _ in range(int(c.w * c.h * 0.04) + 1):
                x, y = c.rng.randrange(c.w), c.rng.randrange(1, c.h)
                for xx in (x, x + 1):
                    if c.inside(xx, y):
                        c.set(xx, y, shade(c.get(xx, y), 0.9))
            if c.h > 2:                        # glossy highlight along the top edge
                for x in range(c.w):
                    if c.rng.random() < sheen * 4:
                        c.set(x, 0, c.pick(SHEEN))
    return p


def back_top(c):
    fur(top=1.1, sheen=0.25)(c)
    for y in range(c.h):                       # a glossy line down the spine
        if c.rng.random() < 0.75:
            c.set(c.w // 2, y, c.pick(SHEEN))


def belly(c):
    """Underside of the torso, seen when the otter floats on its back: light brown belly, a cream
    chest at the front (row 0 is the back edge)."""
    for y in range(c.h):
        for x in range(c.w):
            t = y / (c.h - 1)
            if t > 0.7:
                col = c.pick(CREAM)
            elif t > 0.58:
                col = mix(c.pick(BELLY), c.pick(CREAM), 0.5)
            else:
                col = c.pick(BELLY)
            if x in (0, c.w - 1):
                col = shade(col, 0.9)
            c.set(x, y, col)
    for y in range(0, int(c.h * 0.6), 2):      # a soft fur pattern down the middle
        c.set(c.w // 2, y, shade(c.get(c.w // 2, y), 1.06))


def torso_side(c):
    fur(belly_rows=1)(c)
    for i in range(3):                         # the cream chest wraps a little round the front
        for y in (c.h - 2, c.h - 1):
            if i < 2 or y == c.h - 1:
                c.set(fx(c, i), y, mix(c.get(fx(c, i), y), c.pick(CREAM), 0.75 if i < 2 else 0.4))


def torso_front(c):
    fur()(c)
    for y in range(2, c.h):                    # the throat, under the head
        for x in range(c.w):
            c.set(x, y, c.pick(CREAM) if 0 < x < c.w - 1 or y > 2 else mix(c.pick(CREAM), c.pick(FUR), 0.4))


def torso_back(c):
    fur(grad=0.3)(c)


def chest(c):
    if c.face in ("front", "bottom"):
        c.noise(CREAM)
        if c.face == "front":
            for x in range(c.w):
                c.set(x, c.h - 1, c.pick(CREAM_SH))
    elif c.face in ("left", "right"):
        c.noise(CREAM_SH)
    else:
        c.noise(CREAM)


# -- head --------------------------------------------------------------------------------------------
def skull_front(c):
    # 5 x 4: brown forehead with the eyes on the corners of rows 0-1, cream cheeks below (the muzzle
    # covers the middle of rows 2-3)
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(FUR), 1.05) if y < 2 else c.pick(CREAM)
            c.set(x, y, col)
    for x in (0, c.w - 1):                     # little eyes on the front corners, wrapping round
        c.set(x, 0, EYE)                       # to the sides where the glint sits
        c.set(x, 1, EYE)
    for x in range(1, c.w - 1):
        c.set(x, 1, shade(c.pick(FUR), 1.1))   # a lighter brow running into the muzzle


def skull_side(c):
    for y in range(c.h):
        for x in range(c.w):
            if y < 2:
                col = shade(c.pick(FUR), 1.04 - 0.05 * y)
            else:
                col = c.pick(CREAM) if y == 2 else c.pick(CREAM_SH)
            c.set(x, y, col)
    c.set(fx(c, 0), 0, SHINE)                  # the eye wraps round the corner: glint on top
    c.set(fx(c, 0), 1, EYE)
    c.set(fx(c, 1), 0, shade(c.pick(FUR), 0.8))
    c.set(fx(c, 1), 1, shade(c.pick(FUR), 0.85))
    c.set(fx(c, 1), 2, shade(c.pick(CREAM), 1.0))
    for i in range(1, c.w):                    # the cream cheek curves up behind the eye
        if i >= 2:
            c.set(fx(c, i), 2, mix(c.pick(CREAM), c.pick(FUR), 0.25 * (i - 1)))
            c.set(fx(c, i), 3, mix(c.pick(CREAM_SH), c.pick(FUR), 0.2 * (i - 1)))


def skull_top(c):
    fur(top=1.12, sheen=0.3)(c)


def skull_back(c):
    fur(grad=0.25)(c)


def skull_bottom(c):
    c.noise(CREAM_SH)


def muzzle_front(c):
    # 4 x 2: a dark button nose on top between the whisker pads, a cream lip with a tiny mouth
    rows = [
        "pNNp",
        "cmmc",
    ]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "N":
                col = NOSE
            elif ch == "m":
                col = mix(c.pick(CREAM), MOUTH, 0.55)
            elif ch == "p":
                col = PAD                              # whisker pads, dotted
            else:
                col = c.pick(CREAM)
            c.set(x, y, col)


def muzzle_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(FUR), 1.1))
    c.set(1, c.h - 1, NOSE_HI); c.set(2, c.h - 1, NOSE)   # top of the nose (with a glint)


def muzzle_side(c):
    c.noise(CREAM)
    c.set(fx(c, 0), 0, PAD)
    c.set(fx(c, 1), 0, mix(c.pick(CREAM), c.pick(FUR), 0.7))
    c.set(fx(c, 1), 1, MOUTH)                  # the corner of the mouth


def whiskers(c):
    """Two-pixel pale whiskers sticking out beside the muzzle (a flat plane, front and back alike)."""
    for x in range(c.w):
        c.set(x, 0, WHISKER)
    outer = 0 if c.face == "front" else c.w - 1   # painted for the right side; the left mirrors it
    c.set(outer, 0, shade(WHISKER, 0.9))


def muzzle_bottom(c):
    c.noise(CREAM_SH)


def ear(c):
    c.set(0, 0, shade(c.pick(FUR), 0.88 if c.face != "top" else 1.08))
    if c.face == "front":
        c.set(0, 0, shade(FUR[0], 0.68))      # the shadowed inner ear


# -- legs and tail -----------------------------------------------------------------------------------
def leg(c):
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(FUR), c.pick(PAW), min(1.0, y / max(1, c.h - 1) * 1.3))
            c.set(x, y, col)
    if c.face == "front":
        c.set(0, c.h - 1, TOE); c.set(1, c.h - 1, shade(TOE, 0.85))


def foot(c):
    c.noise(PAW)
    if c.face == "front":
        c.set(0, 0, TOE); c.set(1, 0, shade(TOE, 0.85))
    if c.face == "top":
        c.set(0, c.h - 1, TOE)


def sole(c):
    """Underside of a paw (it faces up when the otter floats): dark pads, lighter toe tips in front."""
    c.noise(["#2a1c13", "#30201a"])
    if c.h >= 2:
        c.set(0, c.h - 1, TOE); c.set(c.w - 1, c.h - 1, shade(TOE, 0.9))


def tail_fur(t0, t1):
    """Tail fur that darkens from t0 at the base to t1 at the tip (0 = body colour, 1 = darkest)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face in ("left", "right"):
                    along = (c.w - 1 - x if c.face == "right" else x) / max(1, c.w - 1)  # 0 front
                elif c.face in ("top", "bottom"):
                    along = 1 - y / max(1, c.h - 1)                               # row 0 = back
                elif c.face == "front":
                    along = 0.0
                else:
                    along = 1.0
                t = t0 + (t1 - t0) * along
                col = mix(c.pick(FUR), c.pick(FUR_DK), t)
                if c.face == "top":
                    col = shade(col, 1.1)
                    if c.rng.random() < 0.2:
                        col = mix(col, c.pick(SHEEN), 0.6)
                elif c.face == "bottom":
                    col = shade(col, 0.85)
                elif c.face in ("left", "right") and y == c.h - 1:
                    col = shade(col, 0.88)
                c.set(x, y, col)
    return p


def build():
    m = Model("otter", 64, 64, seed=8181)
    pk = Pack(m)

    # body: pivot at the centre of the torso (y 18.5) so the code can roll it onto its back.
    # torso x -2.5..2.5, y 16-21 (belly at 21), z -5.5..5.5; a 3-wide ridge arches the back and a
    # cream chest bulges under the chin.
    body = m.part("body", (0, 18.5, 0))
    pk.add(body, (-2.5, -2.5, -5.5), (5, 5, 11), faces(fur(), top=fur(top=1.06), right=torso_side,
                                                       left=torso_side, front=torso_front,
                                                       back=torso_back, bottom=belly))
    pk.add(body, (-1.5, -3.5, -4.5), (3, 1, 9), faces(fur(grad=0.1), top=back_top))
    pk.add(body, (-2, 0.5, -6.5), (4, 2, 1), faces(chest))

    # head: pivot at the neck; skull x -2.5..2.5, y 15-19 (flat top level with the back), z -9..-5,
    # the muzzle sticks out 2 more; tiny round ears on the sides at the top
    head = body.part("head", (0, -1.5, -5))
    pk.add(head, (-2.5, -2, -4), (5, 4, 4), faces(skull_back, front=skull_front, right=skull_side,
                                                  left=skull_side, top=skull_top, bottom=skull_bottom))
    pk.add(head, (-2, 0, -6), (4, 2, 2), faces(muzzle_side, front=muzzle_front, top=muzzle_top,
                                               bottom=muzzle_bottom))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        for wy in (0.6, 1.4):                  # two hair-thin whiskers a side
            pk.add(head, (-5 if sx < 0 else 2, wy, -5.5), (3, 0.4, 0),
                   None if left else faces(whiskers), mirror=left, share="whiskers")
        e = head.part(side + "_ear", (2.5 * sx, -2, -0.5))
        pk.add(e, (-1 if sx < 0 else 0, -0.5, -0.5), (1, 1, 1), None if left else faces(ear),
               mirror=left, share="ear")

    # legs: short, set under the corners of the torso, reaching y 24; webbed toes poke forward
    for name, x, z in (("right_front_leg", -1.5, -3.5), ("left_front_leg", 1.5, -3.5),
                       ("right_hind_leg", -1.5, 3.5), ("left_hind_leg", 1.5, 3.5)):
        lg = body.part(name, (x, 2.5, z))
        left = name.startswith("left")
        pk.add(lg, (-1, 0, -1), (2, 3, 2), None if left else faces(leg, bottom=sole), mirror=left,
               share="leg")
        pk.add(lg, (-1, 2, -2), (2, 1, 1), None if left else faces(foot, bottom=sole), mirror=left,
               share="toes")

    # tail: thick at the base, flattening and darkening toward the tip, drooping toward the ground
    tail = body.part("tail", (0, -1, 5.5), (-0.3, 0, 0))
    pk.add(tail, (-1.5, -1, 0), (3, 2, 4), faces(tail_fur(0.0, 0.35)))
    tip = tail.part("tail_tip", (0, 0, 4), (0.12, 0, 0))
    pk.add(tip, (-1, -0.5, 0), (2, 1, 4), faces(tail_fur(0.4, 0.9)))

    pk.apply()
    m.save()
    spawn_egg("otter", "#5a3a26", "#d8c2a0", accent="#1a1210")


if __name__ == "__main__":
    build()

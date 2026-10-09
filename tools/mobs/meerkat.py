"""Meerkat: a slim sandy desert lookout that lives in groups. Tan-fawn fur with faint darker bands
across the back, a pale cream belly and chest, a narrow pointed face with a pale muzzle and a dark
nose tip, dark "sunglasses" patches round shiny black eyes, small round dark ears set low on the
sides of the head, little dark-clawed paws and a thin pointed tail with a dark tip.

Rig: `body` pivots at the hips, so the code can swing it straight up (xRot -pi/2) into the sentry
pose; the head, front legs and tail ride on the body and the hind legs stay on the root. Haunches on
the rear of the body make the standing meerkat pear-shaped. The preview shows that sentry pose (the
game ignores it)."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Meerkat"
LOOT = []
TAGS = []

# Sentry pose, preview only: body straight up, head level again, forepaws dangling in front of the
# chest, tail swung down and back onto the ground as a prop.
SENTRY = {"body": [-math.pi / 2, 0, 0], "head": [math.pi / 2, 0, 0],
          "right_front_leg": [1.0, 0, 0], "left_front_leg": [1.0, 0, 0],
          "tail": [1.14, 0, 0]}


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


def zb(c, x, y):
    """Distance from the mob's back edge for a pixel on a top/bottom/right/left face."""
    if c.face in ("top", "bottom"):
        return y
    return x if c.face == "right" else c.w - 1 - x


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
FUR = ["#c9a46c", "#bd9860", "#d4b07a", "#c4a067"]
BAND = ["#a8834f", "#a07b48"]
BELLY = ["#e8d6b0", "#e2cfa6", "#ecdcb9"]
FACE = ["#e6d3ab", "#dfcba1", "#ead9b4"]
CROWN = ["#b8996a", "#b09163", "#bfa071"]
PATCH = ["#3a2a1c", "#33251a"]
EYE = "#0b0806"
SHINE = "#fbfaf4"
NOSE = ["#1f160f", "#261b12"]
NOSE_HI = "#5a4636"
EAR = ["#4a3624", "#523c28"]
EAR_IN = "#2e2116"
CLAW = "#4a3626"
TOE = ["#ad8a59", "#a68353"]
TIP = ["#3a2a1c", "#2f2216"]


def fur(top=1.05, grad=0.2, band_rows=(), belly_rows=0, streaks=0.06):
    """Sandy fur. Side faces darken downward (turning cream in the last belly_rows); band_rows lists
    the distances-from-the-back that carry a faint darker band across the back (top face and the
    upper rows of the side faces)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FUR)
                if c.face == "top":
                    f = top
                elif c.face == "bottom":
                    col, f = c.pick(BELLY), 0.92
                else:
                    f = 1.04 - grad * (y / max(1, c.h - 1))
                    if belly_rows and y >= c.h - belly_rows and c.face in ("left", "right", "front"):
                        col, f = mix(col, c.pick(BELLY), 0.75), 0.97
                c.set(x, y, shade(col, f))
        if band_rows and c.face in ("top", "left", "right"):
            for y in range(c.h if c.face == "top" else 2):
                for x in range(c.w):
                    if zb(c, x, y) in band_rows and c.rng.random() < 0.8:
                        k = 0.7 if (c.face == "top" or y == 0) else 0.4
                        c.set(x, y, mix(c.get(x, y), c.pick(BAND), k))
        if c.face != "bottom":                         # short darker hair strokes
            for _ in range(int(c.w * c.h * streaks)):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, shade(c.get(x, y), 0.9))
    return p


def body_front(c):
    """Chest: tan at the top (under the head), cream below."""
    for y in range(c.h):
        for x in range(c.w):
            if y >= 2:
                col = shade(c.pick(BELLY), 1.0 - 0.04 * (y - 2))
            elif y == 1:
                col = mix(c.pick(FUR), c.pick(BELLY), 0.5)
            else:
                col = c.pick(FUR)
            c.set(x, y, col)


def body_back(c):
    fur(grad=0.18)(c)
    for x in range(c.w):
        c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(BELLY), 0.6))


def belly(c):
    """Pale cream underside (the front of the column when standing up): a little shading at the rims."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BELLY)
            if x in (0, c.w - 1):
                col = mix(col, c.pick(FUR), 0.3)
            if y == 0:
                col = shade(col, 0.92)           # the groin, between the haunches
            c.set(x, y, col)


def haunch(c):
    """The thighs: only thin rims show beside the body. Kept tan all round (pale belly fur would
    read as stripes beside the belly when the meerkat stands up)."""
    fur(grad=0.2, streaks=0.1)(c)
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(mix(c.pick(FUR), c.pick(BELLY), 0.3), 0.95))


# -- head --------------------------------------------------------------------------------------------
def skull_front(c):
    """4 wide x 4 tall; the muzzle covers columns 1-2 of rows 2-3. The eyes wrap the front corners:
    here only their black edge shows, which reads as the meerkat's dark 'sunglasses'."""
    for y in range(c.h):
        for x in range(c.w):
            if y == 0:
                col = mix(c.pick(CROWN), c.pick(FACE), 0.35)
            else:
                col = shade(c.pick(FACE), 1.04 - 0.03 * y)
            c.set(x, y, col)
    for x in (0, c.w - 1):
        c.set(x, 1, EYE)
        c.set(x, 2, EYE)
        c.set(x, 3, mix(c.pick(PATCH), c.pick(FACE), 0.25))
    for x in (1, 2):                             # the pale bridge of the nose
        c.set(x, 1, shade(c.pick(FACE), 1.07))


def skull_side(c):
    for y in range(c.h):
        for x in range(c.w):
            if y == 0:
                col = c.pick(CROWN)
            elif y == 1:
                col = mix(c.pick(FUR), c.pick(FACE), 0.3)
            else:
                col = shade(c.pick(FACE), 1.0 - 0.05 * y)
            c.set(x, y, col)
    # a 2x2 shiny black eye in the front corner, glint at its upper front, ringed by the dark patch
    c.set(fx(c, 0), 1, SHINE)
    c.set(fx(c, 1), 1, EYE)
    c.set(fx(c, 0), 2, EYE)
    c.set(fx(c, 1), 2, EYE)
    c.set(fx(c, 0), 3, c.pick(PATCH))
    c.set(fx(c, 1), 3, mix(c.pick(PATCH), c.pick(FACE), 0.25))
    c.set(fx(c, 2), 2, mix(c.pick(PATCH), c.pick(FACE), 0.35))
    c.set(fx(c, 2), 1, mix(c.pick(PATCH), c.pick(FUR), 0.55))


def skull_top(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CROWN)
            if y == c.h - 1:
                col = mix(col, c.pick(FACE), 0.4)  # the brow, paling into the face
            c.set(x, y, shade(col, 1.04))
    for _ in range(3):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h - 1)
        c.set(x, y, c.pick(BAND))


def skull_back(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CROWN) if y < 2 else c.pick(FUR)
            c.set(x, y, shade(col, 1.0 - 0.05 * y))


def skull_bottom(c):
    c.noise([shade(b, 0.92) for b in BELLY])


def muzzle(c):
    """The pale, pointed muzzle: paler and cooler toward the tip, a dark mouth corner."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FACE)
            if c.face == "top":
                col = shade(mix(col, c.pick(CROWN), 0.3 if y < c.h - 1 else 0.0), 1.04)
            elif c.face == "bottom":
                col = shade(col, 0.88)
            else:
                col = shade(col, 1.02 - 0.06 * y)
            c.set(x, y, col)
    if c.face in ("right", "left"):
        c.set(fx(c, 0), 1, mix(c.pick(PATCH), c.pick(FACE), 0.4))   # the corner of the mouth
    elif c.face == "front":
        c.set(0, 1, shade(c.get(0, 1), 0.92)); c.set(1, 1, shade(c.get(1, 1), 0.92))


def nose(c):
    c.noise(NOSE)
    if c.face == "top":
        c.set(0, c.h - 1, NOSE_HI)
    elif c.face == "front":
        c.set(0, 0, shade(NOSE_HI, 0.8))


def ear(c):
    c.noise(EAR)
    if c.face in ("right", "left"):              # outer face: a round dark ear hole under a soft rim
        c.set(fx(c, 0), 1, EAR_IN)
        c.set(fx(c, 1), 1, shade(EAR_IN, 1.2))
        c.set(fx(c, 1), 0, mix(c.pick(EAR), c.pick(FUR), 0.35))


# -- legs and tail -----------------------------------------------------------------------------------
def leg(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FUR)
            if c.face in ("back", "left"):
                col = shade(col, 0.95)
            c.set(x, y, shade(col, 1.02 - 0.12 * (y / max(1, c.h - 1))))
    if c.face in SIDES:                           # a dusky paw, tiny black claws at the front
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(TOE))
        if c.face == "front":                    # (a 1 px wide forepaw gets a softer claw tip)
            for x in range(c.w):
                c.set(x, c.h - 1, CLAW if c.w > 1 else mix(CLAW, c.pick(TOE), 0.45))
        elif c.face in ("right", "left"):
            c.set(fx(c, 0), c.h - 1, shade(CLAW, 1.6))


def sole(c):
    c.noise(["#9a7a4e", "#92744a"])


def tail_paint(tip=False):
    """Tan, a shade darker on top and paler underneath; the tip segment darkens to black-brown over
    its last two pixels (the back end of the cube)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FUR)
                if c.face == "top":
                    col = shade(col, 0.95)
                elif c.face == "bottom":
                    col = mix(col, c.pick(BELLY), 0.4)
                if tip:
                    k = zb(c, x, y) if c.face in ("top", "bottom", "right", "left") else (0 if c.face == "back" else 9)
                    if k <= 1:
                        col = c.pick(TIP)
                    elif k == 2:
                        col = mix(col, c.pick(TIP), 0.5)
                c.set(x, y, col)
    return p


def build():
    m = Model("meerkat", 64, 64, seed=3131)
    pk = Pack(m)

    # body: pivot at the hips. Quadruped: x -2..2, y 16..20, z -3..4 (the rump runs 1.5 px past the
    # hip joint so the standing column comes down onto the hind legs).
    body = m.part("body", (0, 19.5, 2.5))
    pk.add(body, (-2, -3.5, -5.5), (4, 4, 7),
           faces(fur(band_rows=(0, 2, 4), belly_rows=1), front=body_front, back=body_back, bottom=belly))
    # haunches: a little wider over the hind legs (the pear shape when standing), set just inside
    # the rump, back and belly so no faces lie flush
    pk.add(body, (-2.5, -2.75, -1.75), (5, 3, 3), faces(haunch))

    # head: on the body's front top, pivot at the neck. Narrow skull, a 2x2 pale muzzle with a
    # dark nose tip poking out of it, small round ears set low and far back.
    head = body.part("head", (0, -2.5, -5.5))
    pk.add(head, (-2, -3.5, -3.5), (4, 4, 4),
           faces(skull_side, front=skull_front, top=skull_top, back=skull_back, bottom=skull_bottom))
    pk.add(head, (-1, -1.5, -5.5), (2, 2, 2), faces(muzzle))
    pk.add(head, (-0.5, -1.5, -6), (1, 1, 1), faces(nose), inflate=0.1)
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        e = head.part(name, (2 * sx, -1.25, 0))
        left = sx > 0
        pk.add(e, (-0.5, -1, -1), (1, 2, 2), None if left else faces(ear), mirror=left, share="ear",
               inflate=-0.2)

    # front legs: thin (1 px inflated to 1.5), pivot at the shoulder on the belly line
    for name, sx in (("right_front_leg", -1), ("left_front_leg", 1)):
        lg = body.part(name, (1.15 * sx, 0.5, -4.75))
        left = sx > 0
        pk.add(lg, (-0.5, -1.25, -0.5), (1, 5, 1), None if left else faces(leg, bottom=sole),
               mirror=left, share="fleg", inflate=0.25)

    # hind legs: on the root under the hips (2 px, shrunk a hair so they don't touch each other)
    for name, sx in (("right_hind_leg", -1), ("left_hind_leg", 1)):
        lg = m.part(name, (1.0 * sx, 20, 2.5))
        left = sx > 0
        pk.add(lg, (-1, -0.9, -1), (2, 5, 2), None if left else faces(leg, bottom=sole),
               mirror=left, share="hleg", inflate=-0.1)

    # tail: from the top of the rump, back and a little down; thin, tapering, dark-tipped
    tail = body.part("tail", (0, -2, 1.5), (-0.35, 0, 0))
    pk.add(tail, (-0.5, -0.5, 0), (1, 1, 4), faces(tail_paint()), inflate=0.2)
    pk.add(tail, (-0.5, -0.5, 4), (1, 1, 3), faces(tail_paint(tip=True)))

    pk.apply()
    m.preview = dict(SENTRY)
    m.save()
    spawn_egg("meerkat", "#c9a46c", "#3a2a1c", accent="#e8d6b0")


if __name__ == "__main__":
    build()

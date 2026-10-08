"""Dune Scorpion: a sandy-gold armoured scorpion. Plated body, two big pincers, six splayed legs and
a four-segment tail that curls up and forward over the back, ending in a dark stinger."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Dune Scorpion'
LOOT = [item("string", 0, 2), item("spider_eye", 0, 1, player_only=True)]
TAGS = ['arthropod']

GOLD = ["#d6ae64", "#cda45a", "#d9b36a", "#c99f56"]
GOLD_LT = "#ebcd8a"
SEAM = "#8e6832"
BELLY = ["#e4d09c", "#dac58e", "#e8d6a6"]
TIP = ["#4a3326", "#3e2b20"]
STING = ["#2e211b", "#3a2a22"]
EYE = "#121010"

SIDES = ("front", "back", "left", "right")


def plate(seam_every=0, ridge=False, belly=False):
    """Armour: gold noise, light top edge and dark bottom on sides, seams across the segments.
    seam_every: a dark seam line every N pixels along the body's length (rows on top/bottom,
    columns on left/right faces), with a highlight just behind it."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(GOLD)
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.06 - 0.24 * y / (c.h - 1))
                    if y == 0:
                        col = mix(col, GOLD_LT, 0.5)
                if c.face == "top" and x in (0, c.w - 1):
                    col = shade(col, 0.88)
                if c.face == "top" and ridge and x in (c.w // 2 - (1 - c.w % 2), c.w // 2):
                    col = mix(col, GOLD_LT, 0.55)
                if c.face == "bottom":
                    col = c.pick(BELLY) if belly else shade(col, 0.75)
                c.set(x, y, col)
        if seam_every:
            if c.face in ("top", "bottom"):
                for y in range(seam_every - 1, c.h - 1, seam_every):
                    for x in range(c.w):
                        c.set(x, y, SEAM if c.face == "top" else shade(c.pick(BELLY), 0.8))
                        if c.face == "top" and c.inside(x, y + 1):
                            c.set(x, y + 1, mix(c.get(x, y + 1), GOLD_LT, 0.35))
            elif c.face in ("left", "right"):
                for x in range(seam_every - 1, c.w - 1, seam_every):
                    for y in range(c.h):
                        c.set(x, y, shade(SEAM, 1.1))
        c.speckle([shade(GOLD[0], 0.85)], 0.05)
    return p


def head_front(c):
    plate()(c)
    c.set(1, 0, EYE); c.set(c.w - 2, 0, EYE)            # lateral eyes
    for x in (2, 3):                                     # chelicerae
        c.set(x, c.h - 1, TIP[0])
        c.set(x, c.h - 2, shade(GOLD[1], 0.75))


def head_top(c):
    plate()(c)
    cx = c.w // 2
    c.set(cx - 1, c.h - 1, EYE); c.set(cx, c.h - 1, EYE)  # the pair of median eyes, at the front edge
    c.set(cx - 1, 0, mix(GOLD[0], GOLD_LT, 0.5)); c.set(cx, 0, mix(GOLD[0], GOLD_LT, 0.5))


def tail_seg(c):
    plate()(c)
    if c.face in ("top", "bottom"):
        for x in range(c.w):
            c.set(x, 0, SEAM)                            # joint ring at the far end
    elif c.face in ("left", "right"):
        col = 0 if c.face == "right" else c.w - 1
        for y in range(c.h):
            c.set(col, y, SEAM)
    elif c.face == "back":
        c.fill(shade(GOLD[0], 0.7))


def tail_end(c):
    tail_seg(c)
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(c.get(x, y), "#8a5a2e", 0.35))


def stinger(c):
    c.noise(STING)
    if c.face == "top":
        c.set(0, c.h - 1, "#5a3e2c")


def needle(c):
    c.noise(["#1a1210", "#221815"])
    if c.face in SIDES:
        c.set(0, c.h - 1, "#0c0806")


def claw_arm(c):
    plate()(c)


def hand(c):
    plate(ridge=True)(c)
    if c.face in ("top", "right", "left"):               # knobbly shell bumps
        for _ in range(2):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, mix(GOLD[0], GOLD_LT, 0.6))


def finger(c):
    plate()(c)
    # darker toward the front tip: front face, and the front end of the long faces
    if c.face == "front":
        c.noise(TIP)
    elif c.face in ("top", "bottom"):
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(TIP))               # last row = front edge
            c.set(x, c.h - 2, mix(c.get(x, c.h - 2), TIP[0], 0.5))
    elif c.face == "right":
        for y in range(c.h):
            c.set(c.w - 1, y, c.pick(TIP))
    elif c.face == "left":
        for y in range(c.h):
            c.set(0, y, c.pick(TIP))


def leg(c):
    plate()(c)
    # joints along the leg; the outer end (the foot) is dark
    if c.face in ("top", "bottom", "front", "back"):
        for x in (2, 5):
            for y in range(c.h):
                c.set(x, y, SEAM)
        for y in range(c.h):
            c.set(0, y, c.pick(TIP))                      # col 0 = outer end on a right leg
    elif c.face == "right":
        c.noise(TIP)


def build():
    m = Model("dune_scorpion", 64, 64, seed=2077)

    body = m.part("body", (0, 20, 0))
    body.cube((0, 0), (-4, -2, -4), (8, 3, 9), faces(plate(seam_every=3, belly=True)))
    body.cube((0, 12), (-3.5, -3, -3.5), (7, 1, 8), faces(plate(seam_every=2, ridge=True)))

    head = body.part("head", (0, 0, -4))
    head.cube((34, 0), (-3, -2.5, -2), (6, 3, 2), faces(plate(), front=head_front, top=head_top))

    # tail: each segment runs along +z from its pivot and is tipped up around x; the chain arcs up and
    # forward over the back. Pivots sit 2.6 px apart so the joints overlap on the outside of the bend.
    t1 = body.part("tail1", (0, -2, 4.5), (0.25, 0, 0))
    t1.cube((34, 5), (-1.5, -1.5, 0), (3, 3, 3), faces(tail_seg))
    t2 = t1.part("tail2", (0, 0, 2.6), (0.85, 0, 0))
    t2.cube((34, 5), (-1.5, -1.5, 0), (3, 3, 3), faces(tail_seg))
    t3 = t2.part("tail3", (0, 0, 2.6), (0.9, 0, 0))
    t3.cube((34, 5), (-1.5, -1.5, 0), (3, 3, 3), faces(tail_seg))
    t4 = t3.part("tail4", (0, 0, 2.6), (0.8, 0, 0))
    t4.cube((46, 5), (-1, -1, 0), (2, 2, 3), faces(tail_end))
    # tail4 is turned past vertical, so its local -y is world DOWN: the barb hangs off that side
    t4.cube((56, 0), (-1, -1.5, 2.5), (2, 2, 2), faces(stinger))    # venom bulb
    t4.cube((56, 4), (-0.5, -2.5, 3.5), (1, 2, 1), faces(needle))   # the barb, hooking down

    for side, sx in (("right", -1), ("left", 1)):
        mir = sx > 0
        cl = body.part(side + "_claw", (3.5 * sx, 0.5, -3.5), (0, -0.3 * sx, 0))
        cl.cube((30, 12), (-1, -1, -2), (2, 2, 2), None if mir else faces(claw_arm), mirror=mir)
        cl.cube((40, 12), (-2.5, -1.5, -5), (5, 3, 3), None if mir else faces(hand), mirror=mir)
        # fixed finger on the inner side, movable pincer on the outer side
        cl.cube((0, 23), (0.5 if sx < 0 else -2.5, -1, -9), (2, 2, 4), None if mir else faces(finger), mirror=mir)
        pin = cl.part(side + "_pincer", (1.5 * sx, 0, -5), (0, -0.25 * sx, 0))
        pin.cube((12, 23), (-1, -1, -4), (2, 2, 4), None if mir else faces(finger), mirror=mir)

        # legs: yaw fans them front-to-back, then roll tips the outer end down to the ground
        for i, (z, yaw) in enumerate(((-2.5, -0.5), (0, 0.05), (2.5, 0.55)), start=1):
            L, py = 7.0, 20.5
            drop = 24 - py - 0.5
            roll = math.asin(min(1.0, drop / (L * math.cos(yaw))))
            lg = body.part(f"{side}_leg{i}", (4 * sx, 0.5, z), (0, yaw if sx < 0 else -yaw, -roll if sx < 0 else roll))
            lg.cube((0, 21), (-7 if sx < 0 else 0, -0.5, -0.5), (7, 1, 1), None if mir else faces(leg), mirror=mir)

    m.save()
    spawn_egg("dune_scorpion", "#d6ae64", "#8e6832", accent="#2e211b")


if __name__ == "__main__":
    build()

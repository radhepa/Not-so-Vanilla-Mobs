"""Gloomwing: a dog-sized cave bat-thing. Dusky violet fur, big ears, a pig-snout with fangs, pale
glowing eyes, and tattered membrane wings (zero-thickness planes, torn edges are cut-out texels)."""
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Gloomwing'
LOOT = [item("leather", 0, 1), item("glow_ink_sac", chance=0.25, looting=False, player_only=True)]
TAGS = ['burn_in_daylight', 'fall_damage_immune']

FUR = ["#3a3242", "#41384a", "#352d3d", "#3e3547"]
FUR_LT = ["#4f4458", "#564a60", "#4b4054"]
SKIN = ["#6a5562", "#735d6b"]
EAR_IN = ["#7d5f70", "#86677a"]
DARK = "#1f1924"
MEMB = ["#5a4862", "#614e6a", "#56445e", "#5d4a66"]
BONE = "#261e2c"
CLAW = "#cfc6b8"
EYE = "#eefaff"
EYE_RIM = "#9fd2e6"

SIDES = ("front", "back", "left", "right")


def fur(light_bottom=True, streak=True):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FUR)
                if c.face in SIDES and c.h > 1:
                    f = 1.08 - 0.22 * y / (c.h - 1)
                    col = shade(col, f)
                    if light_bottom and y == c.h - 1:
                        col = c.pick(FUR_LT)
                if c.face == "top" and (x in (0, c.w - 1)):
                    col = shade(col, 0.88)
                if c.face == "bottom":
                    col = c.pick(FUR_LT) if light_bottom else shade(col, 0.85)
                c.set(x, y, col)
        if streak:   # tufty fur: a few darker 2-px streaks
            for _ in range(c.w * c.h // 7):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, shade(c.get(x, y), 0.8))
                if c.face in SIDES and c.inside(x, y + 1):
                    c.set(x, y + 1, shade(c.get(x, y + 1), 0.85))
    return p


def face(c):
    fur(light_bottom=False)(c)
    for x in range(c.w):
        c.set(x, 0, shade(c.pick(FUR), 0.85))       # brow
    # big pale eyes, a dark socket ring under each
    for ex in (0, 4):
        c.glow(ex, 2, EYE_RIM)
        c.glow(ex + 1, 2, EYE)
        c.set(ex, 3, DARK); c.set(ex + 1, 3, DARK)
        c.set(ex, 1, shade(FUR[0], 0.7)); c.set(ex + 1, 1, shade(FUR[0], 0.7))
    c.glow(1, 2, EYE); c.glow(4, 2, EYE)
    c.glow(0, 2, EYE_RIM); c.glow(5, 2, EYE_RIM)
    for x in (2, 3):
        c.set(x, 4, shade(c.pick(FUR), 0.75))


def head_side(c):
    fur(light_bottom=False)(c)
    eye_col = c.w - 1 if c.face == "right" else 0
    c.set(eye_col, 2, DARK)


def snout(c):
    c.noise(SKIN)
    if c.face == "front":
        c.set(0, 0, DARK); c.set(2, 0, DARK)         # nostrils
        c.set(1, 0, shade(SKIN[0], 1.15))
        for x in range(c.w):
            c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.75))
    elif c.face == "bottom":
        c.fill(shade(SKIN[0], 0.7))
    elif c.face == "top":
        for x in range(c.w):
            c.set(x, 0, c.pick(FUR))


def fangs(c):
    for x in range(c.w):
        c.clear(x, 0)
    c.set(0, 0, CLAW); c.set(c.w - 1, 0, CLAW)


def ear(c):
    fur(light_bottom=False, streak=False)(c)
    if c.face == "front":
        for y in range(1, c.h):
            c.set(1, y, c.pick(EAR_IN))
        for y in range(c.h - 2, c.h):
            c.set(0, y, shade(c.pick(EAR_IN), 0.9)); c.set(2, y, shade(c.pick(EAR_IN), 0.9))
        c.set(1, 0, shade(FUR[0], 0.8))
    if c.face in ("front", "back", "left", "right"):
        c.clear(0, 0) if c.face in ("front", "back") else None    # pointed tip
        c.clear(c.w - 1, 0) if c.face in ("front", "back") else None


# -- membranes: a pure function of (x, y) so the top and bottom planes match pixel for pixel ------
def _h(x, y, salt):
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


def membrane(depth, fingers, holes, salt):
    """depth[x] = membrane rows counted from the leading (front) edge, per column. Row 0 of a top or
    bottom face is the BACK edge, so a column x is solid for rows h-depth[x]..h-1. fingers: pixels
    painted as bone; holes: torn pixels."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if y < c.h - depth[x] or (x, y) in holes:
                    c.clear(x, y)
                    continue
                r = _h(x, y, salt)
                col = MEMB[int(r * len(MEMB)) % len(MEMB)]
                edge = y == c.h - depth[x] or (x, y - 1) in holes or (x, y + 1) in holes
                if edge:
                    col = shade(col, 0.8)                 # darker frayed rim
                elif y >= c.h - 2:
                    col = shade(col, 1.08)                # near the arm bone
                if (x, y) in fingers:
                    col = BONE
                c.set(x, y, col)
    return p


def bone(c):
    c.noise([BONE, "#30273a", "#271f2d"])


def claw(c):
    c.fill("#a39a8c")


def foot(c):
    c.noise([BONE, "#30273a"])


def toe(c):
    c.noise([BONE, "#30273a"])
    if c.face == "top":
        c.set(0, c.h - 1, "#a39a8c"); c.set(c.w - 1, c.h - 1, "#a39a8c")


def build():
    m = Model("gloomwing", 64, 64, seed=404)

    body = m.part("body", (0, 18.5, 0))
    body.cube((0, 0), (-3, -2.5, -4.5), (6, 5, 9), faces(fur(), top=fur(light_bottom=False)))
    # tail membrane between the legs
    body.cube((0, 50), (-2.5, 1.5, 4.5), (5, 0, 3),
              faces(membrane([2, 3, 3, 3, 2], set(), {(2, 0)}, 3)))

    head = body.part("head", (0, -0.5, -4.5))
    head.cube((30, 0), (-3, -2.5, -5), (6, 5, 5),
              faces(fur(light_bottom=False), front=face, right=head_side, left=head_side))
    head.cube((52, 0), (-1.5, -0.5, -7), (3, 2, 2), faces(snout))
    head.cube((52, 4), (-1.5, 1.5, -6.9), (3, 1, 0), faces(fangs))
    for side, sx in (("right", -1), ("left", 1)):
        e = head.part(side + "_ear", (2 * sx, -2.5, -2), (0, -0.3 * sx, 0.3 * sx))
        e.cube((0, 14), (-1.5, -5, -0.5), (3, 5, 1), None if sx > 0 else faces(ear), mirror=sx > 0)

    # wings: leading-edge bone + a zero-thickness membrane behind it; the tip hangs off the wrist
    base_m = membrane(depth=[10, 8, 7, 8, 9, 10],
                      fingers={(0, 9), (0, 8), (1, 7), (1, 6), (1, 5), (2, 4), (2, 3)},
                      holes={(3, 5), (4, 1)}, salt=1)
    tip_m = membrane(depth=[3, 5, 8, 6, 7, 9, 10],
                     fingers={(5, 8), (5, 7), (4, 6), (4, 5), (3, 4), (3, 3), (2, 2)}
                     | {(6, y) for y in range(4, 10)} | {(5, 3), (5, 2), (5, 1)}
                     | {(4, 9), (3, 9), (2, 8), (1, 8), (0, 7)},
                     holes={(1, 7), (4, 4), (3, 7)}, salt=2)
    for side, sx in (("right", -1), ("left", 1)):
        mir = sx > 0
        w = body.part(side + "_wing", (3 * sx, -2, -1.5), (0, 0, -0.2 * sx))
        w.cube((0, 20), (-6 if sx < 0 else 0, -0.5, -0.5), (6, 1, 1), None if mir else faces(bone), mirror=mir)
        w.cube((20, 14), (-6 if sx < 0 else 0, 0, -0.5), (6, 0, 10), None if mir else faces(base_m), mirror=mir)
        t = w.part(side + "_wing_tip", (6 * sx, 0, 0), (0, -0.15 * sx, 0.35 * sx))
        t.cube((0, 22), (-7 if sx < 0 else 0, -0.5, -0.5), (7, 1, 1), None if mir else faces(bone), mirror=mir)
        t.cube((0, 24), (-7 if sx < 0 else 0, 0, -0.5), (7, 0, 10), None if mir else faces(tip_m), mirror=mir)
        t.cube((16, 22), (-0.5, -0.5, -1.5), (1, 1, 1), None if mir else faces(claw), mirror=mir)   # thumb

    feet = body.part("feet", (0, 2.5, 2.5))
    feet.cube((0, 42), (-2, 0, -0.5), (1, 2, 1), faces(foot))
    feet.cube((0, 42), (1, 0, -0.5), (1, 2, 1), None, mirror=True)
    feet.cube((8, 42), (-2.5, 2, -1.5), (2, 1, 2), faces(toe))
    feet.cube((8, 42), (0.5, 2, -1.5), (2, 1, 2), None, mirror=True)

    m.save()
    spawn_egg("gloomwing", "#3a3242", "#52435b", accent="#eefaff")


if __name__ == "__main__":
    build()

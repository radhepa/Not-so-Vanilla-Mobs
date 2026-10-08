"""Frostbitten: a zombie frozen solid. Pale icy-blue skin crusted with frost, icicles hanging from
its brow, shoulders and raised arms, a stiff frosted scarf and eyes that glow ice-blue."""
from mobkit import Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Frostbitten'
LOOT = [item("rotten_flesh", 0, 2), item("snowball", 0, 3), item("ice", chance=0.1, looting=False, player_only=True)]
TAGS = ['zombies', 'freeze_immune_entity_types']

SKIN = ["#93b3c5", "#89a9bc", "#9cbbcc", "#85a4b7", "#8faec0"]
BITE = ["#8a97be", "#7f8cb4"]                    # frostbitten purple-blue (nose, fingertips)
FROST = ["#e3f2f9", "#d2e8f2", "#f1f9fc"]
SNOW = ["#eef7fb", "#e2f0f7", "#f8fcfe", "#d6e9f2"]
SHIRT = ["#4d7277", "#45686d", "#567c81", "#3f6066"]
PANTS = ["#3c4270", "#353a63", "#434979", "#2f3459"]
SCARF = ["#8c2e35", "#7d282f", "#983439", "#72242a"]
STRIPE = ["#5c1c22", "#541a1f"]
ICE = ["#bde8fb", "#a6ddf5", "#d2f1fd"]
ICE_DEEP = "#6fb6dc"
ICE_TIP = "#86c9ea"
EYE_DARK = "#182633"
EYE_GLOW = "#48cff4"
SIDES = ("front", "back", "left", "right")


def tone(c, y, col, k=0.16):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def skin(frost=0.07):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, c.pick(FROST) if c.rng.random() < frost else c.pick(SKIN)))
    return p


def face(c):
    skin(0.04)(c)
    for x in (1, 2, 5, 6):                          # sunken sockets
        c.set(x, 3, "#7f9fb4")
    c.set(1, 4, EYE_DARK); c.set(6, 4, EYE_DARK)
    c.glow(2, 4, EYE_GLOW); c.glow(5, 4, EYE_GLOW)
    c.set(3, 5, BITE[0]); c.set(4, 5, BITE[1])     # frostbitten nose
    c.set(1, 5, "#93b0c3"); c.set(6, 6, BITE[1])
    for x in (2, 3, 4, 5):
        c.set(x, 6, "#1c2a38")
    c.set(4, 6, "#cfe3ea")                          # one tooth
    for (x, y) in ((0, 6), (0, 7), (1, 7), (7, 5), (7, 6)):   # frost creeping up the jaw
        c.set(x, y, c.pick(FROST))


def head_top(c):
    c.noise(SNOW)


def hat_frost(c):
    """Overlay layer: a cap of snow on the crown with ice dripping down the sides."""
    if c.face == "bottom":
        return
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(ICE) if c.rng.random() < 0.15 else c.pick(SNOW))
        return
    eyes = (1, 2, 5, 6) if c.face == "front" else ()
    for x in range(c.w):
        depth = 1 if c.rng.random() < 0.45 else 2
        drip = c.rng.choice((0, 0, 1, 1, 2, 3))
        if x in eyes:
            drip = min(drip, 3 - depth)
        for y in range(depth):
            c.set(x, y, c.pick(SNOW))
        for y in range(depth, depth + drip):
            c.set(x, y, ICE_TIP if y == depth + drip - 1 else c.pick(ICE))


def shirt(rip=False):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(SHIRT)
                if c.rng.random() < 0.06 + (0.25 if y < 2 else 0):
                    col = c.pick(FROST)
                c.set(x, y, tone(c, y, col))
        for x in range(c.w):                        # torn hem
            if c.rng.random() < 0.45:
                c.set(x, c.h - 1, tone(c, c.h - 1, c.pick(SKIN)))
        if rip:
            for (x, y) in ((5, 6), (6, 7), (5, 8), (6, 8)):
                c.set(x, y, tone(c, y, c.pick(SKIN)))
            c.set(6, 6, c.pick(FROST))
    return p


def body_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(SNOW) if c.rng.random() < 0.6 else c.pick(SHIRT))


def sleeve(c):
    """Arms are held out forward: their front face points UP (snow settles there) and their back
    face points DOWN (ice drips)."""
    snow = 0.38 if c.face == "front" else 0.07
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top" or y < 4 or (y == 4 and c.rng.random() < 0.5):
                col = c.pick(SHIRT)
            else:
                col = c.pick(SKIN)
            if c.rng.random() < snow:
                col = c.pick(SNOW if c.face == "front" else FROST)
            if c.face == "back" and c.rng.random() < 0.18:
                col = c.pick(ICE)
            c.set(x, y, tone(c, y, col, 0.1))
    if c.face in SIDES:                             # frostbitten fingertips
        for x in range(c.w):
            if c.rng.random() < 0.5:
                c.set(x, c.h - 1, c.pick(BITE))


def hand(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(BITE) if c.rng.random() < 0.15 else shade(c.pick(SKIN), 0.9))


def pants(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(PANTS)
            if y >= c.h - 2 or (y == c.h - 3 and c.rng.random() < 0.55):
                col = c.pick(FROST)                 # snow caked round the feet
            c.set(x, y, tone(c, y, col, 0.12))


def sole(c):
    c.noise(["#c4d9e4", "#b5ccd8", "#a9c1cf"])


# -- scarf ------------------------------------------------------------------------------------------
def knit(stripes=(), fringe=False, frost=0.14):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(STRIPE) if y in stripes else c.pick(SCARF)
                if x % 2:
                    col = shade(col, 0.88)           # knitted ribs
                if c.face == "top" or c.rng.random() < frost * (1.6 if y == 0 else 1):
                    col = c.pick(FROST) if c.rng.random() < 0.55 else col
                c.set(x, y, tone(c, y, col, 0.12))
        if fringe and c.face in SIDES:
            for x in range(0, c.w, 2):
                c.clear(x, c.h - 1)
    return p


# -- ice --------------------------------------------------------------------------------------------
def icicle_v(c):
    """Hangs straight down (+y)."""
    if c.face == "top":
        c.noise(SNOW)
    elif c.face == "bottom":
        c.fill(ICE_DEEP)
    else:
        for y in range(c.h):
            col = c.pick(FROST) if y == 0 else (ICE_TIP if y == c.h - 1 else c.pick(ICE))
            c.set(0, y, col)


def icicle_z(c):
    """Points along +z: on raised zombie arms the back face (+z) points down."""
    c.noise(ICE)
    if c.face in ("top", "bottom"):
        for x in range(c.w):
            c.set(x, 0, ICE_TIP)
    elif c.face == "right":
        c.set(0, 0, ICE_DEEP)
    elif c.face == "left":
        c.set(c.w - 1, 0, ICE_DEEP)
    elif c.face == "back":
        c.fill(ICE_DEEP)
    elif c.face == "front":
        c.fill(c.pick(FROST))


def crust(c):
    """Packed ice and snow on the shoulders."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top" or y == 0:
                col = c.pick(SNOW)
            else:
                col = c.pick(ICE) if c.rng.random() < 0.8 else c.pick(FROST)
            c.set(x, y, tone(c, y, col, 0.2))
    if c.face in SIDES:
        for x in range(c.w):
            if c.rng.random() < 0.3:
                c.set(x, c.h - 1, ICE_DEEP)


def crystal(tip=False):
    """Upright ice crystal: bright tip at the top, deep blue at the root and on its edges."""
    def p(c):
        if c.face == "top":
            c.noise(["#e9f8ff", "#d2f1fd"] if tip else ICE)
            return
        if c.face == "bottom":
            c.fill(ICE_DEEP)
            return
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(ICE)
                if x == c.w - 1 and c.w > 1:
                    col = shade(col, 0.84)
                if y == c.h - 1 and not tip:
                    col = ICE_DEEP
                if y == 0 and tip:
                    col = "#e9f8ff"
                c.set(x, y, col)
        if not tip:
            c.set(0, c.rng.randrange(1, c.h - 1), "#f4fbfe")
    return p


def build():
    m = Model("frostbitten", 64, 64, seed=4242)
    head, body = humanoid(m, {
        "head": faces(skin(), front=face, top=head_top),
        "body": faces(shirt(), front=shirt(rip=True), top=body_top, bottom=shirt()),
        "arm": faces(sleeve, bottom=hand),
        "leg": faces(pants, bottom=sole),
    })
    right_arm, left_arm = m.get("right_arm"), m.get("left_arm")

    # snow-and-icicle overlay on the hat layer (vanilla hat slot: 32,0, inflated 0.5)
    m.get("hat").cube((32, 0), (-4, -8, -4), (8, 8, 8), faces(hat_frost), inflate=0.5)

    # icicles hanging from the frozen brow, clear of the eyes
    ice_v = faces(icicle_v)
    brow = head.part("brow_icicles")
    brow.cube((34, 32), (-4, -6, -5), (1, 3, 1), ice_v)
    brow.cube((38, 32), (-1, -6, -5), (1, 2, 1), ice_v)
    brow.cube((38, 32), (3, -6, -5), (1, 2, 1), ice_v)
    brow.cube((42, 36), (0, -6, -5), (1, 1, 1), ice_v)

    # frosted scarf: a stiff ring round the neck, a tail down the chest and one frozen mid-flap
    scarf = body.part("scarf")
    scarf.cube((0, 32), (-4.5, -0.5, -2.5), (9, 3, 5), faces(knit(stripes=(1,)), bottom=knit()))
    tail = scarf.part("scarf_tail", (2, 2.5, -2.5), (-0.1, 0, 0.06))
    tail.cube((28, 32), (-1, 0, -1), (2, 7, 1), faces(knit(stripes=(2, 5), fringe=True)))
    flap = scarf.part("scarf_flap", (-2, 1, 2.5), (0.55, 0.15, 0.1))
    flap.cube((28, 40), (-1, 0, 0), (2, 5, 1), faces(knit(stripes=(2,), fringe=True)))

    # shoulder crusts with icicles; arm icicles point +z so they hang down while the arms are raised
    ice_z3, ice_z2 = faces(icicle_z), faces(icicle_z)
    for arm, sx in ((right_arm, -1), (left_arm, 1)):
        side = "right" if sx < 0 else "left"
        sh = arm.part(side + "_shoulder_ice")
        sh.cube((0, 40), (-3.5, -2.5, -2.5) if sx < 0 else (0.5, -2.5, -2.5), (3, 3, 5), faces(crust),
                mirror=sx > 0)
        ic = arm.part(side + "_arm_icicles")
        # x as on the right arm (spans -3..1); mirrored onto the left arm (spans -1..3)
        for (x, y, length) in ((-3, -1, 3), (-1, 2, 2), (0, 5, 3), (-2, 7, 2), (-3, 4, 2)):
            ox = x if sx < 0 else -x - 1
            if length == 3:
                ic.cube((42, 32), (ox, y, 2), (1, 1, 3), ice_z3)
            else:
                ic.cube((50, 32), (ox, y, 2), (1, 1, 2), ice_z2)

    # ice crystals grown out of the shoulder blades, leaning up and back
    base, tip = faces(crystal()), faces(crystal(tip=True))
    for name, pivot, rot, tall in (("back_crystal", (-2, 3, 2), (-0.55, 0.2, -0.3), True),
                                   ("back_crystal_mid", (2.2, 2.5, 2), (-0.7, -0.3, 0.35), True),
                                   ("back_crystal_small", (0.3, 6.5, 2), (-0.9, 0, 0.1), False)):
        s = body.part(name, pivot, rot)
        s.cube((16, 40), (-1, -4, -1), (2, 4, 2), base)
        if tall:
            s.cube((46, 36), (-0.5, -6, -0.5), (1, 2, 1), tip)

    m.preview = {"right_arm": [-1.45, 0, 0.06], "left_arm": [-1.6, 0, -0.05]}
    m.save()
    spawn_egg("frostbitten", "#7fa8bf", "#e8f6fc", accent="#8c2e35")


if __name__ == "__main__":
    build()

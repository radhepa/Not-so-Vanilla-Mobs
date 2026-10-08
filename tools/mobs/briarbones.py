"""Briarbones: a skeleton strangled by jungle growth. Vines wrap its ribs and limbs, thorny briars
knot its shoulders, leaves sprout from its skull and moss grows over its jaw."""
from mobkit import Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Briarbones'
LOOT = [item("bone", 0, 2), item("arrow", 0, 2), item("vine", 0, 2)]
TAGS = ['skeletons', 'burn_in_daylight']

BONE = ["#d8d4c3", "#cdc9b7", "#e2dfcf", "#c6c2b0"]
BONE_SHADOW = "#a9a592"
SOCKET = "#1a1611"
SOCKET_RIM = "#3b362b"
GAP = ["#3d382e", "#36322a", "#433e33"]
VINE = ["#3d6b22", "#47792a", "#35601d"]
VINE_DARK = "#284a15"
LEAF = ["#5a9a32", "#6cae3c", "#4e8a2b"]
LEAF_LIGHT = "#80c24a"
MOSS = ["#55803a", "#4a7334", "#618c40", "#3f6530"]
STEM = "#4f6f29"
BRIAR = ["#4b3a24", "#3f311f", "#56432a", "#3a4a22"]
THORN = "#d6c494"
THORN_TIP = "#8a3d2b"
SIDES = ("front", "back", "left", "right")
# where each side face starts when walking round a box (front -> left -> back -> right), so painted
# spirals continue across the corners
RING = {"front": 0, "left": 1, "back": 2, "right": 3}


def ring_u(c, w, d):
    return {"front": 0, "left": w, "back": w + d, "right": w + d + w}[c.face]


def tone(c, y, col, k=0.14):
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def bone(c, x, y, k=0.14):
    return tone(c, y, c.pick(BONE), k)


# -- skull ------------------------------------------------------------------------------------------
def skull(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, bone(c, x, y, 0.1))
    if c.face == "bottom":                          # mossy underside of the jaw (row h-1 = front)
        for y in range(c.h):
            for x in range(c.w):
                if c.rng.random() < 0.25 + 0.6 * (y / (c.h - 1)):
                    c.set(x, y, c.pick(MOSS))


def skull_face(c):
    skull(c)
    c.set(1, 1, BONE_SHADOW); c.set(2, 2, BONE_SHADOW)      # an old crack
    for (x0, y0) in ((1, 3), (5, 3)):
        c.rect(x0, y0, 2, 2, SOCKET)
        c.set(x0, y0, SOCKET_RIM) if x0 == 1 else c.set(x0 + 1, y0, SOCKET_RIM)
    c.set(3, 5, SOCKET_RIM); c.set(4, 5, SOCKET)            # nose hole
    for x in range(1, 7):
        c.set(x, 6, "#2a251c")
    for x in range(1, 7):                                   # lower teeth
        c.set(x, 7, c.pick(BONE) if x % 2 else "#2a251c")
    for (x, y) in ((0, 6), (0, 7), (7, 7), (7, 6), (6, 7), (1, 7)):   # moss on the jaw
        c.set(x, y, c.pick(MOSS))


def overgrowth(c):
    """Hat overlay: vines draped over the skull, leaves on the crown, a mossy beard on the jaw."""
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                near = ((x - 2) ** 2 + (y - 5) ** 2) < 7 or ((x - 6) ** 2 + (y - 2) ** 2) < 3
                if near and c.rng.random() < 0.85:
                    c.set(x, y, c.pick(LEAF) if c.rng.random() < 0.7 else c.pick(MOSS))
        for x in range(c.w):                                # a vine across the crown
            c.set(x, 3 if x < 4 else 4, c.pick(VINE))
        return
    if c.face == "bottom":
        for y in range(c.h - 2, c.h):
            for x in range(c.w):
                if c.rng.random() < 0.7:
                    c.set(x, y, c.pick(MOSS))
        return
    if c.face == "front":
        strands = ((0, 6), (7, 5))                          # (column, length) clear of the eye sockets
        for x in range(c.w):
            if c.rng.random() < 0.7:
                c.set(x, 0, c.pick(LEAF))
        for x in range(c.w):                                # mossy beard
            if c.rng.random() < 0.85:
                c.set(x, 7, c.pick(MOSS))
        for x in (0, 1, 6, 7):
            if c.rng.random() < 0.7:
                c.set(x, 6, c.pick(MOSS))
        c.set(1, 0, LEAF_LIGHT); c.set(2, 1, c.pick(LEAF))
    elif c.face == "back":
        strands = ((1, 7), (4, 4), (6, 6))
        for x in range(c.w):
            if c.rng.random() < 0.5:
                c.set(x, 0, c.pick(LEAF))
    else:
        front_col = c.w - 1 if c.face == "right" else 0
        strands = ((3, 5) if c.face == "right" else (5, 7),)
        for y in range(5, 8):                                # moss creeping back from the jaw
            for dx in range(3 - (7 - y)):
                xx = front_col - dx if c.face == "right" else front_col + dx
                c.set(xx, y, c.pick(MOSS))
        for x in range(c.w):
            if c.rng.random() < 0.45:
                c.set(x, 0, c.pick(LEAF))
    for (x, length) in strands:                             # hanging vine strands with a leaf or two
        for y in range(length):
            xx = x + (1 if (y // 3) % 2 and x < c.w - 1 else 0)
            c.set(xx, y, c.pick(VINE) if y < length - 1 else VINE_DARK)
            if y in (2, 5) and xx + 1 < c.w and c.rng.random() < 0.8:
                c.set(xx + 1 if xx < c.w - 1 else xx - 1, y, c.pick(LEAF))


# -- ribcage ----------------------------------------------------------------------------------------
def ribcage(c):
    """8x12x4 body drawn as a see-through ribcage with a vine spiralling round it."""
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                c.set(x, y, bone(c, x, y))
        return
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                c.set(x, y, shade(c.pick(BONE), 0.8))
        return
    for y in range(h):
        for x in range(w):
            solid = y == 0 or y in (2, 4, 6) or y in (10, 11)              # collarbones, ribs, pelvis
            if c.face == "front" and y == 6 and x in (0, w - 1):
                solid = False                                               # short lowest rib
            if c.face in ("front", "back") and x in (3, 4):
                solid = solid or y < (10 if c.face == "back" else 7) or y in (8, 9)   # sternum / spine
                if c.face == "front" and y == 11:
                    solid = False                                           # gap between the hips
            if c.face == "back" and y == 1:
                solid = True                                                # shoulder blades
            if c.face == "back" and y == 8:
                solid = True                                                # floating ribs
            if solid:
                col = bone(c, x, y)
                if c.face in ("left", "right") and y in (2, 4, 6):
                    col = shade(col, 0.92)
            else:
                col = tone(c, y, c.pick(GAP), 0.2)                          # shadow inside the ribcage
            c.set(x, y, col)
    # vine spiralling round the torso (continuous across the corners)
    u0 = ring_u(c, 8, 4)
    for y in range(1, h - 1):
        for x in range(w):
            k = (u0 + x + 2 * y) % 24
            if k in (0, 1):
                c.set(x, y, c.pick(VINE) if k == 0 else VINE_DARK)
            elif k == 2 and c.rng.random() < 0.35:
                c.set(x, y, c.pick(LEAF))
            elif k == 23 and y % 3 == 0:
                c.set(x, y, c.pick(LEAF))


def limb(c):
    """2x12x2 bone with a vine spiral (shoulders/hips stay clear for the briars)."""
    if c.face in ("top", "bottom"):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(BONE), 1.0 if c.face == "top" else 0.78))
        return
    u0 = ring_u(c, 2, 2)
    for y in range(c.h):
        for x in range(c.w):
            col = bone(c, x, y, 0.2)
            if y in (5, 6) and x == (1 if c.face in ("front", "left") else 0):
                col = shade(col, 0.88)                       # elbow / knee knuckle shading
            if c.face in ("front", "back") and x == (1 if c.face == "front" else 0):
                col = shade(col, 0.9)                        # inner edge, parts the arm from the ribs
            k = (u0 + x + y) % 8
            if 3 <= y <= 10 and k == 0:
                col = c.pick(VINE)
            elif 3 <= y <= 10 and k == 1 and y % 4 == 1:
                col = c.pick(LEAF)
            c.set(x, y, col)


# -- briars, thorns, plants -------------------------------------------------------------------------
def briar(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BRIAR)
            if c.rng.random() < 0.18:
                col = c.pick(VINE)
            c.set(x, y, tone(c, y, col, 0.2))
    for y in range(c.h):
        for x in range(c.w):
            if c.rng.random() < 0.16:
                c.set(x, y, THORN)
    if c.face == "top":
        c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(LEAF))


def thorn(c):
    c.fill(THORN)
    if c.face in ("top", "front"):
        c.fill(THORN_TIP)


SPROUT_S = [".L.L.",
            "LLlLL",
            ".LsL.",
            "..s..",
            "..s.."]
SPROUT_L = [".L..L.",
            "LLl.LL",
            ".LLsLl",
            "..LsL.",
            "...s..",
            "...s.."]
HANGING_VINE = [".v.",
                ".vL",
                "Lv.",
                ".v.",
                ".vl",
                "v..",
                "v..",
                "d.."]


def sprite(rows):
    def p(c):
        mirror = c.face in ("back", "left")
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                xx = len(row) - 1 - x if mirror else x
                col = {"L": c.pick(LEAF), "l": LEAF_LIGHT, "s": STEM, "v": c.pick(VINE),
                       "d": VINE_DARK}.get(ch)
                if col:
                    c.set(xx, y, col)
    return p


def build():
    m = Model("briarbones", 64, 64, seed=9001)
    head, body = humanoid(m, {
        "head": faces(skull, front=skull_face),
        "body": faces(ribcage),
        "arm": faces(limb),
        "leg": faces(limb),
    }, slim_limbs=True)

    m.get("hat").cube((32, 0), (-4, -8, -4), (8, 8, 8), faces(overgrowth), inflate=0.5)

    # leaves sprouting from the skull: crossed flat planes (each pair shares one texture block)
    small, large = faces(sprite(SPROUT_S)), faces(sprite(SPROUT_L))
    s1 = head.part("skull_sprout", (-2, -8.5, -1), (0.12, 0.785, -0.15))
    s1.cube((0, 32), (-2.5, -5, 0), (5, 5, 0), small)
    s1.cube((0, 32), (0, -5, -2.5), (0, 5, 5), small)
    s2 = head.part("skull_sprout_big", (2, -8.5, 1.5), (-0.1, 0.5, 0.22))
    s2.cube((10, 32), (-3, -6, 0), (6, 6, 0), large)
    s2.cube((10, 32), (0, -6, -3), (0, 6, 6), large)

    # thorny briars knotted round both shoulders
    for arm, sx in ((m.get("right_arm"), -1), (m.get("left_arm"), 1)):
        side = "right" if sx < 0 else "left"
        b = arm.part(side + "_briar")
        b.cube((48, 16), (-2, -2.5, -2), (4, 3, 4), faces(briar), mirror=sx > 0)
        for (x, y, z) in ((-3, -2, -0.5), (-0.5, -3.5, 0.5), (0.5, -1.5, -3), (-1.5, -0.5, 2), (-3, -0.5, 1)):
            b.cube((48, 23), (x if sx < 0 else -x - 1, y, z), (1, 1, 1), faces(thorn))

    # a vine dangling from the ribs
    hv = body.part("hanging_vine", (1, 5, -2.2))
    hv.cube((22, 32), (-1.5, 0, 0), (3, 8, 0), faces(sprite(HANGING_VINE)))

    m.save()
    spawn_egg("briarbones", "#c9c5b2", "#47792a", accent="#8a3d2b")


if __name__ == "__main__":
    build()

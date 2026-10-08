"""Soulpyre: a skeleton burned black in the Soul Sand Valley. Charred bones split by cracks that glow
pale cyan, burning eye sockets, and pale blue soul fire wreathing its skull, ribcage and shoulders.
The bow is a vanilla held item."""
from mobkit import Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Soulpyre"
LOOT = [item("bone", 0, 2), item("arrow", 0, 2), item("soul_soil", chance=0.25, looting=False)]
TAGS = ["skeletons"]

CHAR = ["#2b2725", "#24201f", "#322d2a", "#1e1b1a"]
CHAR_HI = "#4a423c"
ASH = ["#5a5550", "#4d4844"]
SOCKET = "#0c0b0b"
CRACK_DIM = "#2a9cc4"
CRACK = "#7fe8ff"
CRACK_HOT = "#c8f8ff"
# soul fire, outside to core
F_DEEP = "#11577f"
F_OUT = "#1a86c0"
F_MID = "#2fb4e6"
F_CYAN = "#5fe0ff"
F_CORE = "#c8f6ff"
GAP = ["#14171c", "#101318", "#191c22"]
FIRE = {"o": F_OUT, "d": F_DEEP, "m": F_MID, "c": F_CYAN, "w": F_CORE}
SIDES = ("front", "back", "left", "right")


def tone(c, y, col, k=0.16):
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def charred(c, y, k=0.12):
    col = c.pick(ASH) if c.rng.random() < 0.05 else c.pick(CHAR)
    return tone(c, y, col, k)


def crack(c, pts):
    """A glowing crack: hot pixels in the middle of the run, dimmer at its ends."""
    for i, (x, y) in enumerate(pts):
        end = i in (0, len(pts) - 1)
        c.glow(x, y, CRACK_DIM if end else (CRACK_HOT if i == len(pts) // 2 else CRACK))


# -- skull ------------------------------------------------------------------------------------------
def skull(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, charred(c, y, 0.08))
    if c.face == "top":
        crack(c, ((1, 1), (2, 2), (2, 3), (3, 4), (3, 5)))
    elif c.face == "left":
        crack(c, ((5, 0), (5, 1), (4, 2), (4, 3)))
    elif c.face == "right":
        crack(c, ((2, 1), (3, 2), (3, 3)))
    elif c.face == "back":
        crack(c, ((6, 0), (5, 1), (5, 2), (6, 3), (6, 4)))


def skull_face(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, charred(c, y, 0.06))
    c.set(1, 2, CHAR_HI); c.set(6, 2, CHAR_HI)        # brow ridges
    for (x0, mirror) in ((1, False), (5, True)):      # burning eye sockets
        a, b = (x0, x0 + 1) if not mirror else (x0 + 1, x0)
        c.glow(a, 3, F_OUT); c.glow(b, 3, F_CYAN)
        c.glow(a, 4, F_CYAN); c.glow(b, 4, F_CORE)
    c.set(3, 5, SOCKET); c.set(4, 5, "#161413")       # nose hole
    for x in range(1, 7):
        c.set(x, 6, SOCKET)
    for x in range(1, 7):                             # teeth, with a glow behind the gaps
        if x % 2:
            c.set(x, 7, CHAR_HI if x != 3 else c.pick(CHAR))
        else:
            c.glow(x, 7, F_DEEP)
    c.glow(3, 6, F_DEEP); c.glow(4, 6, F_OUT)         # fire showing through the jaw
    crack(c, ((6, 0), (6, 1), (7, 2)))


def fire_col(depth, length):
    """Colour of a flame tongue pixel: `depth` 0 is the tip, length-1 the base."""
    t = depth / max(1, length - 1)
    if t < 0.25:
        return F_OUT
    if t < 0.5:
        return F_MID
    if t < 0.8:
        return F_CYAN
    return F_CORE


def wreath(c):
    """Hat overlay: tongues of soul fire licking up the skull, sparse at the front so the face reads."""
    if c.face == "bottom":
        return
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                edge = x in (0, c.w - 1) or y in (0, c.h - 1)
                r = c.rng.random()
                if edge and r < 0.55:
                    c.glow(x, y, F_OUT if r < 0.3 else F_MID)
                elif not edge and r < 0.12:
                    c.glow(x, y, F_DEEP)
        return
    if c.face == "front":
        heights = [1, 0, 0, 0, 0, 0, 0, 1]
    elif c.face == "back":
        heights = [c.rng.choice((1, 2, 3, 3, 4)) for _ in range(c.w)]
    else:
        heights = [c.rng.choice((0, 0, 1, 2, 2, 3)) for _ in range(c.w)]
        front_edge = c.w - 1 if c.face == "right" else 0
        heights[front_edge] = min(heights[front_edge], 2)
    for x, hgt in enumerate(heights):
        for y in range(hgt):
            c.glow(x, y, fire_col(y, hgt + 2))


# -- ribcage and limbs ------------------------------------------------------------------------------
def ribcage(c):
    """Charred ribs with soul fire burning in the gaps between them (brighter low down)."""
    w, h = c.w, c.h
    if c.face in ("top", "bottom"):
        for y in range(h):
            for x in range(w):
                c.set(x, y, charred(c, y))
        if c.face == "top":
            c.glow(3, 1, F_MID); c.glow(4, 2, F_CYAN); c.glow(5, 1, F_OUT)
        return
    for y in range(h):
        for x in range(w):
            solid = y in (0, 2, 4, 6, 10, 11)
            if c.face in ("front", "back") and x in (3, 4):
                solid = solid or y < (10 if c.face == "back" else 8)
                if c.face == "front" and y == 11:
                    solid = False
            if c.face == "front" and y == 6 and x in (0, w - 1):
                solid = False
            if solid:
                col = charred(c, y)
                if y in (2, 4, 6) and c.rng.random() < 0.25:
                    col = CHAR_HI
                c.set(x, y, col)
            else:
                # fire inside the chest: brightest low and in the middle, so the ribs read as
                # dark bars against it
                half = (w - 1) / 2
                cx = abs(x - half) / half
                hot = y / (h - 1)
                v = (1 - 0.6 * cx) * (0.3 + 0.7 * hot) + (0.05 if (x + y) % 3 == 0 else 0)
                if v > 0.72:
                    c.glow(x, y, F_MID)
                elif v > 0.5:
                    c.glow(x, y, F_OUT)
                elif v > 0.3:
                    c.glow(x, y, F_DEEP)
                else:
                    c.set(x, y, tone(c, y, c.pick(GAP), 0.1))
    if c.face == "front":
        crack(c, ((1, 2), (2, 2)))
    if c.face == "back":
        crack(c, ((5, 4), (6, 4)))


def limb(c):
    if c.face in ("top", "bottom"):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(CHAR), 1.0 if c.face == "top" else 0.8))
        return
    for y in range(c.h):
        for x in range(c.w):
            col = charred(c, y, 0.18)
            if y in (5, 6) and x == (1 if c.face in ("front", "left") else 0):
                col = CHAR_HI                          # elbow / knee knuckle
            c.set(x, y, col)
    if c.face == "front":
        crack(c, ((0, 6), (1, 7), (1, 8)))


# -- flames -----------------------------------------------------------------------------------------
FLAME_HEAD = ["...o....",
              "..oo..o.",
              "..om.oo.",
              ".om..mo.",
              ".mm.omo.",
              "ommcmmmo",
              "mmcccmmm",
              "omcwccmo"]
FLAME_SMALL = ["..o...",
               ".oo.o.",
               ".om.o.",
               "ommmmo",
               "omccmo",
               "mcwcmm"]
FLAME_SHOULDER = ["..o..",
                  ".oo.o",
                  ".omo.",
                  "ommmo",
                  "omcmo",
                  "mcccm"]
FLAME_CHEST = ["........",
               "........",
               ".o....o.",
               ".o...om.",
               "om...m..",
               ".m...c..",
               ".c......",
               "........",
               "........"]


def sprite(rows):
    def p(c):
        mirror = c.face in ("back", "left")
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                col = FIRE.get(ch)
                if col:
                    c.glow(len(row) - 1 - x if mirror else x, y, col)
    return p


def leg(c):
    if c.face in ("top", "bottom"):
        limb(c)
        return
    for y in range(c.h):
        for x in range(c.w):
            col = charred(c, y, 0.18)
            if y in (5, 6) and x == (1 if c.face in ("front", "left") else 0):
                col = CHAR_HI
            c.set(x, y, col)
    if c.face == "front":
        c.glow(0, 3, CRACK_DIM); c.glow(1, 4, CRACK)


def build():
    m = Model("soulpyre", 64, 64, seed=6660)
    head, body = humanoid(m, {
        "head": faces(skull, front=skull_face),
        "body": faces(ribcage),
        "arm": faces(limb),
        "leg": faces(leg),
    }, slim_limbs=True)

    m.get("hat").cube((32, 0), (-4, -8, -4), (8, 8, 8), faces(wreath), inflate=0.5)

    # a crown of soul fire rising off the skull: crossed planes (each pair shares one texture block)
    big, small = faces(sprite(FLAME_HEAD)), faces(sprite(FLAME_SMALL))
    f1 = head.part("skull_flame", (0, -8, 0.5), (0, 0.785, 0))
    f1.cube((0, 32), (-4, -8, 0), (8, 8, 0), big)
    f1.cube((0, 32), (0, -8, -4), (0, 8, 8), big)
    f2 = head.part("skull_flame_back", (1.5, -7.5, 3), (-0.3, 0.3, 0.12))
    f2.cube((16, 32), (-3, -6, 0), (6, 6, 0), small)
    f2.cube((16, 32), (0, -6, -3), (0, 6, 6), small)
    f3 = head.part("skull_flame_side", (-3, -7.5, 1), (0.1, 0.5, -0.3))
    f3.cube((16, 32), (-3, -6, 0), (6, 6, 0), small)
    f3.cube((16, 32), (0, -6, -3), (0, 6, 6), small)

    # fire bursting out of the ribcage, front and back
    chest = faces(sprite(FLAME_CHEST))
    body.part("chest_flame", (0, 1, -2.3)).cube((38, 32), (-4, -2, 0), (8, 9, 0), chest)
    body.part("back_flame", (0, 1, 2.3)).cube((38, 32), (-4, -2, 0), (8, 9, 0), chest)

    # flames on both shoulders
    sh = faces(sprite(FLAME_SHOULDER))
    for arm, sx in ((m.get("right_arm"), -1), (m.get("left_arm"), 1)):
        side = "right" if sx < 0 else "left"
        f = arm.part(side + "_shoulder_flame", (0.5 * sx, -2, 0), (0, 0.785, 0.2 * sx))
        f.cube((28, 32), (-2.5, -6, 0), (5, 6, 0), sh)
        f.cube((28, 33), (0, -6, -2.5), (0, 6, 5), sh)

    m.save()
    spawn_egg("soulpyre", "#2b2725", "#5fe0ff", accent="#d8fbff")


if __name__ == "__main__":
    build()

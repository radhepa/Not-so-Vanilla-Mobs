"""Sculkbones: a skeleton that wandered into the Deep Dark and was swallowed by sculk. Its bones are a
cold blue-grey, darker than a vanilla skeleton's, and dark teal sculk (sparse bright cyan specks)
creeps over its skull, fills its ribcage and climbs its limbs; a chunky sculk mat sits on its left
shoulder and spills over the ribs, and its left foot is caked in a lump of it. It is blind: no glowing
eyes, the sockets are crusted shut with sculk. It hunts by sound with two sculk-sensor tendrils that
grow out of the top of its skull (dark teal stalks, glowing cyan tips) and a few thin cyan veins glow
in cracks on its skull and ribs. The bow is a vanilla held item."""
import math
import random

from mobkit import Cube, Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Sculkbones"
LOOT = [item("bone", 0, 2), item("arrow", 0, 2), item("sculk", chance=0.15, looting=False), item("echo_shard", chance=0.02, looting=False, player_only=True)]
TAGS = ["skeletons", "burn_in_daylight"]

BONE = ["#7f888e", "#7a8389", "#848d92", "#767f85"]
BONE_LIGHT = "#99a2a6"
BONE_SHADOW = "#5a6369"
GAP = ["#10181c", "#0d1418", "#131c21"]
SCULK = ["#0d1f26", "#0a2a33", "#11313b"]
SCULK_DEEP = "#071419"
SCULK_HI = "#185160"                  # the lit rim of a sculk lump
SPECK = "#29dfeb"                     # the tiny bright specks in sculk (not emissive)
STAIN = ["#42545a", "#3b4c52", "#495b61"]   # bone going teal where the sculk creeps onto it
CRUST = ["#11313b", "#0f2b34"]        # sculk sealing the eye sockets
CRUST_HI = "#1f5766"
VEIN = "#29dfeb"
VEIN_DIM = "#00b8c8"
VEIN_BASE = "#0a3a44"                 # under a glowing vein pixel (the glow layer is added on top)
STALK = ["#0f4652", "#0c3a44"]
STALK_HI = "#196a78"
TIP_CORE = "#a6f9ff"
SIDES = ("front", "back", "left", "right")


# -- texture packing: cubes are collected, then shelf-packed tallest-first into free texture areas ----
class Pack:
    def __init__(self, model, areas):
        self.m, self.areas, self.items = model, areas, []

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
        shelves, tops = [], [a[1] for a in self.areas]
        for k, (w, h) in order:
            for s in shelves:                       # s = [y, height, next x, right edge]
                if h <= s[1] and s[2] + w <= s[3]:
                    keys[k] = (s[2], s[0])
                    s[2] += w
                    break
            else:
                for i, (ax, ay, aw, ah) in enumerate(self.areas):
                    if w <= aw and tops[i] + h <= ay + ah:
                        shelves.append([tops[i], h, ax + w, ax + aw])
                        keys[k] = (ax, tops[i])
                        tops[i] += h
                        break
                else:
                    raise ValueError(f"{self.m.id}: no texture room for {k} {w}x{h}")
        for i, (part, origin, size, paint, mirror, share, inflate) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


# -- palette helpers --------------------------------------------------------------------------------
def tone(c, y, col, k=0.14):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def bone(c):
    """Cold bone with the odd darker pit."""
    return BONE_SHADOW if c.rng.random() < 0.025 else c.pick(BONE)


def sculk(c, specks=0.035):
    return SPECK if c.rng.random() < specks else c.pick(SCULK)


def paint_mask(c, rows, k=0.12, specks=0.035):
    """Paint a face from a character map:
    b bone, h bone highlight, d bone shadow, c teal-stained bone, s sculk (with specks), S plain sculk,
    H lit sculk rim, e crusted socket, E crust highlight, k dark gap, t tooth, v / w glowing vein
    (bright / dim), '.' leave as is (transparent on overlays)."""
    for y, row in enumerate(rows[:c.h]):
        for x, ch in enumerate(row[:c.w]):
            if ch == ".":
                continue
            if ch in "vw":
                c.glow(x, y, VEIN if ch == "v" else VEIN_DIM)
                c.set(x, y, VEIN_BASE)          # keep the glow cyan once the glow layer is added
                continue
            col = {"b": lambda: bone(c), "h": lambda: BONE_LIGHT, "d": lambda: BONE_SHADOW,
                   "c": lambda: c.pick(STAIN), "s": lambda: sculk(c, specks), "S": lambda: c.pick(SCULK),
                   "H": lambda: SCULK_HI, "e": lambda: c.pick(CRUST), "E": lambda: CRUST_HI,
                   "k": lambda: c.pick(GAP), "t": lambda: BONE_LIGHT}[ch]()
            if ch in "bhdct":
                col = tone(c, y, col, k)
            c.set(x, y, col)


# -- skull ------------------------------------------------------------------------------------------
# front: col 0 = the mob's right. Sculk creeps over the right brow; both sockets are sealed with crust.
SKULL_FRONT = ["ssscbbcb",
               "Hscbbbbb",
               "scbbbbbb",
               "bEebbEeb",
               "beebbeeb",
               "bcbkkbbb",
               "bkkkkkkb",
               "btktktkb"]
# top: row 0 = back, col 0 = the mob's right. Sculk round the tendril roots, a vein crack between them.
SKULL_TOP = ["bbbbbbbb",
             "bbcbbbcb",
             "bcSsbcsc",
             "bsSsbsSs",
             "bcssvcsc",
             "cbcbwbcb",
             "scbbbwbb",
             "sscbbbvb"]
# right side: col 0 = back, col 7 = front (continues the brow patch)
SKULL_RIGHT = ["bbbbbcss",
               "bbbbbbcs",
               "bbbbbbbc",
               "bbbbbbbb",
               "bbbbbbbb",
               "cbbbbbbb",
               "scbbbbbb",
               "Sscbbbbb"]
# back: col 0 = the mob's left. Sculk dripping down from the tendril roots.
SKULL_BACK = ["bcsscsbb",
              "bbcsSccb",
              "bbbcsbbb",
              "bbbcsbbb",
              "bbbbcbbb",
              "bbbbbbbb",
              "bbbbbbbb",
              "bbbbbbbb"]
SKULL_LEFT = ["bbbbbcSs",     # col 0 = front, col 7 = back
              "bbbbbbcs",
              "bbbbbbbc",
              "bbbbbbbb",
              "bbbbbbbb",
              "bbbbbbbb",
              "bbbbbbbb",
              "bbbbbbbb"]

# hat layer (inflated 0.5): raised crust over the sockets and lumps round the tendril roots
CRUST_FRONT = ["sS......",
               "S.......",
               "........",
               ".EH.....",
               "Hee..H..",
               ".e......",
               "........",
               "........"]
CRUST_TOP = ["........",
             "........",
             ".HS..SH.",
             ".SS..sS.",
             "..s...S.",
             "........",
             "S.......",
             "sS......"]
CRUST_RIGHT = [".......S",
               "........",
               "........",
               "........",
               "........",
               "........",
               "........",
               "........"]
CRUST_BACK = ["..HS.S..",
              "...S....",
              "........",
              "........",
              "........",
              "........",
              "........",
              "........"]


def skull_faces():
    def side(rows):
        return lambda c: paint_mask(c, rows, 0.12)
    return faces(side(SKULL_LEFT), front=side(SKULL_FRONT), top=side(SKULL_TOP), right=side(SKULL_RIGHT),
                 back=side(SKULL_BACK), bottom=lambda c: c.noise([shade(b, 0.78) for b in BONE]))


def crust_faces():
    def side(rows):
        return lambda c: paint_mask(c, rows, 0.12, specks=0.06)
    return faces(None, front=side(CRUST_FRONT), top=side(CRUST_TOP), right=side(CRUST_RIGHT),
                 back=side(CRUST_BACK))


# -- ribcage ----------------------------------------------------------------------------------------
def ribcage(c):
    """8x12x4 ribcage; the gaps between the ribs are packed with sculk, one vein glows through a rib."""
    w, h = c.w, c.h
    if c.face == "top":
        rows = ["bbbbbcss", "bbbbbcss", "bbbbbbcs", "bbbbbbcs"]
        paint_mask(c, rows)
        return
    if c.face == "bottom":
        c.noise([shade(b, 0.76) for b in BONE])
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
            if c.face == "back" and y in (1, 8):
                solid = True                                                # shoulder blades, floating ribs
            if solid:
                col = tone(c, y, bone(c))
                if y in (2, 4, 6) and c.rng.random() < 0.2:
                    col = tone(c, y, BONE_LIGHT)
                if c.face in ("left", "right") and y in (2, 4, 6):
                    col = shade(col, 0.92)
            else:
                col = sculk(c, 0.03)
                if y in (1, 3, 5, 7) and c.rng.random() < 0.15:
                    col = SCULK_DEEP
            c.set(x, y, col)
    if c.face == "front":
        # a glowing vein running down through the sculk and across a rib
        for (x, y, ch) in ((1, 3, "w"), (2, 3, "v"), (2, 4, "v"), (1, 5, "w")):
            paint_mask_px(c, x, y, ch)
        for (x, y) in ((4, 0), (5, 0), (6, 1), (5, 2), (6, 2), (7, 2)):    # sculk creeping off the mat
            c.set(x, y, c.pick(STAIN) if (x + y) % 2 else sculk(c))
    elif c.face == "back":
        for (x, y) in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 2), (0, 2)):
            c.set(x, y, sculk(c) if y < 2 else c.pick(STAIN))
        paint_mask_px(c, 4, 5, "w")
    elif c.face == "left":
        for (x, y) in ((0, 0), (1, 0), (2, 0), (3, 0), (1, 2), (2, 2)):
            c.set(x, y, sculk(c) if y == 0 else c.pick(STAIN))


def paint_mask_px(c, x, y, ch):
    if ch in "vw":
        c.glow(x, y, VEIN if ch == "v" else VEIN_DIM)
        c.set(x, y, VEIN_BASE)


# the sculk mat spilling over the left of the chest (overlay on the body, inflated 0.25)
MAT_FRONT = ["....SsHs",
             ".....sSs",
             "....Hsss",
             ".....sSs",
             "......Hs",
             ".......s",
             "........"] + ["........"] * 5
MAT_LEFT = ["sSsH", "SssS", "sSHs", "ssSs", "Hs.s", "s..S", "...s"] + ["...."] * 5   # col 0 = front
MAT_TOP = ["....sSsS", "....SHss", "....sSHs", ".....sSs"]                           # row 0 = back
MAT_BACK = ["sSsHs...", "SsSs....", "sHs.....", "s.......", "s......."] + ["........"] * 7   # col 0 = left


def mat_faces():
    def side(rows):
        return lambda c: paint_mask(c, rows, specks=0.05)
    return faces(None, front=side(MAT_FRONT), left=side(MAT_LEFT), top=side(MAT_TOP), back=side(MAT_BACK))


# -- limbs ------------------------------------------------------------------------------------------
def limb(sculk_from=None, sculk_to=None, patch=None, seed=0):
    """2x12x2 bone. Rows below `sculk_from` (feet) and above `sculk_to` (shoulder) are taken over by
    sculk, with a ragged stained edge; `patch` = (first row, last row) of a patch on the outer side."""
    def p(c):
        rng = random.Random(seed + FACES_I[c.face])
        if c.face in ("top", "bottom"):
            for y in range(c.h):
                for x in range(c.w):
                    if c.face == "bottom" and sculk_from is not None:
                        c.set(x, y, c.pick(SCULK))
                    elif c.face == "top" and sculk_to is not None:
                        c.set(x, y, sculk(c))
                    else:
                        c.set(x, y, shade(c.pick(BONE), 1.0 if c.face == "top" else 0.78))
            return
        for x in range(c.w):
            lo = None if sculk_from is None else sculk_from + rng.choice((-1, 0, 0, 1))
            hi = None if sculk_to is None else sculk_to + rng.choice((-1, 0, 0, 1))
            for y in range(c.h):
                col = tone(c, y, bone(c), 0.2)
                if y in (5, 6) and x == (1 if c.face in ("front", "left") else 0):
                    col = shade(col, 0.88)                  # elbow / knee knuckle
                if c.face in ("front", "back") and x == (1 if c.face == "front" else 0):
                    col = shade(col, 0.92)                  # inner edge, parts the limb from the ribs
                if patch and c.face in ("right", "front", "back"):
                    outer = c.face == "right" or x == (0 if c.face == "front" else 1)
                    if outer and patch[0] <= y <= patch[1]:
                        col = sculk(c, 0.06) if c.face == "right" else c.pick(STAIN)
                    elif outer and y in (patch[0] - 1, patch[1] + 1) and c.face == "right":
                        col = tone(c, y, c.pick(STAIN), 0.2)
                if lo is not None and y >= lo:
                    col = sculk(c, 0.06)
                elif lo is not None and y == lo - 1:
                    col = tone(c, y, c.pick(STAIN), 0.2)
                if hi is not None and y <= hi:
                    col = sculk(c, 0.06)
                elif hi is not None and y == hi + 1:
                    col = tone(c, y, c.pick(STAIN), 0.2)
                c.set(x, y, col)
    return p


FACES_I = {"top": 0, "bottom": 1, "right": 2, "front": 3, "left": 4, "back": 5}


def lump(c):
    """A chunky sculk growth: lit rim on top, specks, darker toward the bottom."""
    for y in range(c.h):
        for x in range(c.w):
            col = sculk(c, 0.05)
            if c.face == "top" and (x in (0, c.w - 1) or y in (0, c.h - 1)) and c.rng.random() < 0.5:
                col = SCULK_HI
            elif c.face in SIDES and y == 0 and c.rng.random() < 0.6:
                col = SCULK_HI
            elif c.face == "bottom" or (c.face in SIDES and y == c.h - 1 and c.h > 1):
                col = SCULK_DEEP if c.rng.random() < 0.5 else c.pick(SCULK)
            c.set(x, y, col)


# -- tendrils ---------------------------------------------------------------------------------------
# a wavy two-strand stalk with a glowing tip, like a sculk sensor's: C hot core, G glow, g dim glow,
# h lit stalk, s stalk, S root
TENDRIL_A = ["..C..",
             "..Gg.",
             ".gs..",
             ".hs..",
             "..sh.",
             "..s..",
             ".SS.."]
TENDRIL_B = ["..C..",
             ".gG..",
             "..sg.",
             "..sh.",
             ".hs..",
             "..s..",
             "..SS."]


def tendril(rows):
    """Crossed-plane tendril sprite (both faces mirror each other exactly)."""
    def p(c):
        mirror = c.face in ("back", "left")
        for y, row in enumerate(rows[:c.h]):
            for x in range(c.w):
                ch = row[c.w - 1 - x if mirror else x]
                if ch == "g":
                    c.glow(x, y, VEIN_DIM)
                    c.set(x, y, VEIN_BASE)
                elif ch == "G":
                    c.glow(x, y, VEIN)
                    c.set(x, y, VEIN_BASE)
                elif ch == "C":
                    c.glow(x, y, TIP_CORE)
                    c.set(x, y, VEIN_BASE)
                elif ch == "h":
                    c.set(x, y, STALK_HI)
                elif ch == "s":
                    c.set(x, y, STALK[0])
                elif ch == "S":
                    c.set(x, y, SCULK[1])
    return p


def build():
    m = Model("sculkbones", 64, 64, seed=8128)
    head, body = humanoid(m, {
        "head": skull_faces(),
        "body": faces(ribcage),
        "arm": faces(limb(patch=(6, 8), seed=10)),
        "leg": faces(limb(sculk_from=10, seed=20)),
    }, slim_limbs=True)
    # the left limbs get their own texture (more sculk on that side); still mirrored like vanilla
    la, ll = m.get("left_arm"), m.get("left_leg")
    la.cubes[0] = Cube((48, 16), (-1, -2, -1), (2, 12, 2), mirror=True, paint=faces(limb(sculk_to=1, seed=30)))
    ll.cubes[0] = Cube((56, 16), (-1, 0, -1), (2, 12, 2), mirror=True, paint=faces(limb(sculk_from=7, seed=40)))

    # hat layer: sculk crust sealing the sockets and lumps round the tendril roots
    m.get("hat").cube((32, 0), (-4, -8, -4), (8, 8, 8), crust_faces(), inflate=0.5)

    pk = Pack(m, [(0, 48, 64, 16), (40, 32, 24, 16), (0, 32, 16, 16), (8, 16, 8, 16)])
    # sculk mat over the left of the ribs: an overlay layer plus two chunky lumps
    mat = body.part("chest_sculk")
    mat.cube((16, 32), (-4, 0, -2), (8, 12, 4), mat_faces(), inflate=0.25)
    pk.add(mat, (1.5, 0.6, -3.1), (3, 3, 1), faces(lump))
    pk.add(mat, (2.4, 3.2, -2.9), (2, 2, 1), faces(lump))

    # chunky sculk mat on the left shoulder, a drip running down the arm
    sh = la.part("shoulder_sculk")
    pk.add(sh, (-2, -3, -2), (4, 2, 4), faces(lump), inflate=0.2)
    pk.add(sh, (-1.5, -3.9, -1.5), (3, 1, 3), faces(lump))
    pk.add(sh, (0.6, -1, -0.5), (1, 3, 1), faces(lump))

    # the left foot is caked in a lump of sculk
    pk.add(ll.part("foot_sculk"), (-1.5, 9.9, -1.5), (3, 2, 3), faces(lump))

    # two sculk-sensor tendrils growing out of the top of the skull (crossed planes)
    for name, sx, rows in (("right_tendril", -1, TENDRIL_A), ("left_tendril", 1, TENDRIL_B)):
        t = head.part(name, (2.5 * sx, -8, 0), (-0.15, 0, 0.3 * sx))
        spr = faces(tendril(rows))
        pk.add(t, (-2.5, -7, 0), (5, 7, 0), spr)
        pk.add(t, (0, -7, -2.5), (0, 7, 5), spr)

    pk.apply()
    m.save()
    spawn_egg("sculkbones", "#0d2a33", "#c9cfc7", accent="#29dfeb")


if __name__ == "__main__":
    build()

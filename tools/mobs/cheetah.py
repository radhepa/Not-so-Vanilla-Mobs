"""Cheetah: a lean savanna sprinter, all legs and lean lines. A deep, narrow chest under high shoulder
blades, a tucked-up waist, slim muscular haunches and very long slender legs on small neat paws. A
small round head on a slim neck: short round ears set wide (black behind, pale inside), amber eyes
under a dark brow and the black "tear lines" running from the inner corner of each eye down the
sides of the short white muzzle to the corners of the mouth, a black nose. A golden coat covered in
solid round black spots, richer gold along the spine and fading to cream down the flanks, a white
throat, chest and belly. A long tail that hangs low and curls up at the end: spotted at the base,
then ringed black and gold, with a white tip. A short spotted crest runs down the nape.

Rig: `body` (the chest) pivots on the spine in the middle of the back; `hips` (the loin and rump)
shares that pivot, so the code can flex and stretch the spine in the gallop. The front legs hang off
`body`, the hind legs and `tail` off `hips`. Front legs: the forearm, then `<leg>_lower` (wrist to
paw). Hind legs, in three angled segments: the thigh, `<leg>_lower` (the gaskin, stifle to hock) and
`right_hind_foot` / `left_hind_foot` (hock to paw). The tail is `tail` > `tail_mid` > `tail_tip`.
`neck` (with `crest`) carries `head`, which has `jaw` (with `tongue`, tucked inside the mouth; the
code shows it and pokes it out only while panting) and the two ears.

`cheetah_cub` shares the geometry (drawn at half scale): smoky grey, almost black underneath, with
a long silver-white mantle of fluff down the nape and along the back, faint spots and a dark face."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Cheetah"
LOOT = []
TAGS = ["fall_damage_immune"]


# -- texture packing (as in deer.py): biggest cubes first, a 1 px clear margin round every cube ------
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
    """Column i counted from the cube's front (-z) edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def front_dist(c, x, y):
    """How far a pixel of a side/top/bottom face is from the cube's front (-z) edge."""
    if c.face in ("top", "bottom"):
        return c.h - 1 - y
    return c.w - 1 - x if c.face == "right" else x


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position (patterns that don't change between builds)."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


def hpick(pal, *v):
    return pal[int(hsh(*v) * len(pal)) % len(pal)]


SIDES = ("front", "back", "left", "right")

# -- palettes ------------------------------------------------------------------------------------------
ADULT = dict(
    kind="adult",
    coat=["#d9a446", "#dda94d", "#d39e40", "#e0ae52", "#d6a144"],
    spine=["#c88e33", "#c38930", "#cd9438"],                 # richer gold down the back
    hi=["#ebc16c", "#efc874", "#e6ba63"],
    cream=["#ecd5a3", "#efdaab", "#e6cd98"],                  # where the gold fades into the belly
    white=["#f5efe2", "#efe8d9", "#f8f3ea"],
    white_sh=["#ddd3c0", "#d6cbb6"],
    spot=["#1c1510", "#221912", "#18120d"],
    spot_soft=["#3b2a1a", "#43301e"],                         # the edge of a bigger spot
    spot_belly=["#6b5640", "#7a644b"],                        # small faded spots on the white
    face=["#d7a24a", "#dcaa52"],
    brow="#b07c2e",
    tear="#120d0a",
    iris="#f0a218", iris_dk="#b8720f", pupil="#100b08", glint="#fffbe8",
    nose="#1d1612", nose_hi="#4a3b33",
    mouth="#3a2420", gum="#9a4a4f", tongue="#e07b86", tongue_dk="#c45f6c",
    ear_back="#1a1410", ear_in=["#efe6d4", "#e8dcc6"],
    claw="#3a3330", pad="#2a2220",
    ring="#15100c", tip=["#f6f1e6", "#efe9dc"],
    crest=["#c88e33", "#cf9739", "#c38930"],
    leg_spots=1.0,
)
CUB = dict(
    ADULT,
    kind="cub",
    coat=["#55524d", "#5b5853", "#504d49", "#5f5b55"],
    spine=["#4a4743", "#46433f"],
    hi=["#6b6761", "#706c66"],
    cream=["#3e3b38", "#423f3b"],                             # the cub's underside is darker
    white=["#dcd9d2", "#d3d0c8", "#e2dfd8"],
    white_sh=["#9a968e", "#8f8b84"],
    spot=["#3a3734", "#363330"],                              # faint spots under the smoky coat
    spot_soft=["#46433f"],
    spot_belly=["#34312e"],
    face=["#4b4844", "#504d49"],
    brow="#3a3734",
    iris="#b9a46a", iris_dk="#8a7a4c",                        # paler, greyish young eyes
    mantle=["#e4e2dc", "#d8d6cf", "#eceae5", "#cfccc4"],      # the long silver-white fluff
    mantle_sh=["#aaa79f", "#b4b1a9"],
    ring="#2e2b28", tip=["#cfccc4", "#c4c1b9"],
    crest=["#e4e2dc", "#d8d6cf", "#eceae5"],
    leg_spots=0.3,
)


# -- the coat --------------------------------------------------------------------------------------------
def spots(c, P, spacing=3, chance=0.92, big=0.3, salt=0, skip=None, pal="spot", soft=True):
    """Solid round spots on a jittered, staggered grid: one per cell, some of them two pixels wide
    (a dark core and a softer edge pixel), so the coat reads as round spots, never stripes."""
    s = spacing
    for gy in range(-1, c.h // s + 2):
        for gx in range(-1, c.w // s + 2):
            if hsh(c.x0, c.y0, gx, gy, salt) > chance:
                continue
            x = gx * s + (gy % 2) * (s // 2) + int(hsh(gx, gy, salt, c.x0, 1) * (s - 1))
            y = gy * s + int(hsh(gx, gy, salt, c.y0, 2) * (s - 1))
            if not c.inside(x, y) or (skip and skip(x, y)):
                continue
            c.set(x, y, hpick(P[pal], x, y, salt, c.x0))
            if hsh(gx, gy, salt, 3, c.y0) < big:
                nx, ny = (x + 1, y) if hsh(gx, gy, salt, 4) < 0.6 else (x, y + 1)
                if c.inside(nx, ny) and not (skip and skip(nx, ny)):
                    c.set(nx, ny, hpick(P["spot_soft"] if soft else P[pal], nx, ny, salt))


def coat(P, top=1.07, grad=0.16, belly_rows=0, y0=0, span=None, density=0.92, spine=True,
         mantle=False, spot_salt=0):
    """Short golden fur: lit on top with a richer band down the spine, a little darker down the
    sides, fading to cream and then white in the last belly_rows of a side face, covered in solid
    black spots (smaller and fainter on the white). y0/span put a face on a body-wide gradient. On a
    cub, mantle=True lays the long silver fluff over the top face and the top rows of the sides."""
    cub = P["kind"] == "cub"

    def p(c):
        sp = span or c.h
        for y in range(c.h):
            for x in range(c.w):
                col = hpick(P["coat"], x, y, c.x0, c.y0)
                if c.face == "top":
                    f = top
                    if spine:
                        d = abs(x - (c.w - 1) / 2) / max(1.0, c.w / 2)   # 0 on the spine
                        col = mix(hpick(P["spine"], x, y, 5), col, min(1.0, d * 1.5))
                elif c.face == "bottom":
                    col, f = hpick(P["white"] if not cub else P["cream"], x, y, 9), 0.95
                else:
                    t = (y0 + y + 0.5) / sp
                    f = 1.05 - grad * t
                    if belly_rows and c.face in ("left", "right", "front", "back"):
                        k = y - (c.h - belly_rows)
                        if k >= 0:
                            fade = (k + 1) / belly_rows
                            col = mix(hpick(P["cream"], x, y, 7), hpick(P["white"], x, y, 8), fade) \
                                if not cub else mix(col, hpick(P["cream"], x, y, 7), 0.4 + 0.6 * fade)
                            f = 1.0
                        elif k == -1:
                            col = mix(col, hpick(P["cream"], x, y, 7), 0.35)
                c.set(x, y, shade(col, f))
        # a few sunlit hairs on top, darker strokes on the sides
        if c.face == "top":
            for i in range(int(c.w * c.h * 0.07) + 1):
                x, y = int(hsh(c.x0, i, 11) * c.w), int(hsh(c.y0, i, 12) * c.h)
                c.set(x, y, mix(c.get(x, y), hpick(P["hi"], x, y, i), 0.6))
        elif c.face in SIDES:
            for i in range(int(c.w * c.h * 0.08)):
                x, y = int(hsh(c.x0, i, 13) * c.w), int(hsh(c.y0, i, 14) * c.h)
                if belly_rows and y >= c.h - belly_rows:
                    continue
                c.set(x, y, shade(c.get(x, y), 0.93))
        # spots: dense on the gold, small and faint on the white
        on_white = (lambda x, y: belly_rows and y >= c.h - belly_rows + (0 if c.face != "bottom" else 0))
        if c.face == "bottom":
            spots(c, P, spacing=4, chance=0.55, big=0.0, salt=spot_salt + 3, pal="spot_belly", soft=False)
        else:
            spots(c, P, spacing=3, chance=density, big=0.35 if not cub else 0.15, salt=spot_salt,
                  skip=on_white if belly_rows else None)
            if belly_rows:
                spots(c, P, spacing=3, chance=0.45, big=0.0, salt=spot_salt + 1, pal="spot_belly", soft=False,
                      skip=lambda x, y: y < c.h - belly_rows or y == c.h - 1)
        if mantle and cub:
            mantle_over(P)(c)
    return p


def mantle_over(P, rows=2):
    """The cub's mantle: silver fluff over the whole top face and the top rows of the sides, the
    lower edge ragged like long hair."""
    def p(c):
        if c.face == "top":
            for y in range(c.h):
                for x in range(c.w):
                    edge = x in (0, c.w - 1)
                    col = hpick(P["mantle"], x, y, c.x0, 21)
                    c.set(x, y, shade(col, 0.92 if edge else 1.04))
        elif c.face in ("left", "right"):
            # long strands hanging down unevenly, shadowed at their ends, a few grey hairs mixed in
            for x in range(c.w):
                depth = rows - 1 + int(hsh(x, c.x0, c.y0, 22) * 3.0)
                if hsh(x, c.y0, 23) < 0.25:
                    depth += 1
                for y in range(min(c.h, depth)):
                    col = hpick(P["mantle"], x, y, c.y0, 24)
                    if y == depth - 1 or hsh(x, y, c.x0, 27) < 0.12:
                        col = hpick(P["mantle_sh"], x, y, 25)
                    c.set(x, y, col)
        elif c.face in ("front", "back"):
            for x in range(c.w):
                for y in range(min(c.h, rows)):
                    c.set(x, y, hpick(P["mantle"], x, y, c.x0, 26))
    return p


def chain(*ps):
    def run(c):
        for p in ps:
            if p:
                p(c)
    return run


# -- body ------------------------------------------------------------------------------------------------
def chest_front(P):
    """The front of the chest under the throat: white, spotted with small dark spots near the top,
    gold at the shoulders on either side."""
    def p(c):
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                edge = x in (0, c.w - 1)
                if edge and y < c.h - 1:
                    col = hpick(P["coat"], x, y, 31)
                    if y >= c.h - 3:
                        col = mix(col, hpick(P["cream"], x, y, 30), 0.5)
                elif cub:
                    col = hpick(P["cream"], x, y, 32)
                else:
                    col = mix(hpick(P["white"], x, y, 32), hpick(P["cream"], x, y, 34), 0.35)
                    if y >= c.h - 2:
                        col = mix(col, hpick(P["white_sh"], x, y, 35), 0.5)
                c.set(x, y, col)
        spots(c, P, spacing=2, chance=0.45, big=0.0, salt=33, pal="spot" if not cub else "spot_belly", soft=False,
              skip=lambda x, y: y >= c.h - 2 or x in (0, c.w - 1))
        if cub:
            mantle_over(P, rows=1)(c)
    return p


def rump_back(P):
    """The rump seen from behind: gold and spotted, paler down between the thighs."""
    def p(c):
        coat(P, grad=0.2, belly_rows=2, spine=False, spot_salt=41)(c)
        if P["kind"] == "cub":
            mantle_over(P, rows=1)(c)
    return p


def keel(P):
    """The deepest part of the chest, between the elbows: white below, cream at the sides."""
    def p(c):
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    col = hpick(P["white_sh"] if not cub else P["cream"], x, y, 51)
                elif cub:
                    col = hpick(P["cream"], x, y, 52)
                else:
                    col = mix(hpick(P["cream"], x, y, 52), hpick(P["white_sh"], x, y, 53), 0.4)
                c.set(x, y, col)
        if c.face in ("left", "right", "bottom"):
            spots(c, P, spacing=3, chance=0.4, big=0.0, salt=54, pal="spot_belly", soft=False)
    return p


# -- neck --------------------------------------------------------------------------------------------------
def neck_paint(P):
    """The neck leans forward, so its front face is the throat (white, spotless at the top) and its
    back face the nape. The sides are gold with small spots, white along the throat edge."""
    cub = P["kind"] == "cub"

    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "front":
                    col = hpick(P["white"] if not cub else P["cream"], x, y, 61)
                    if x in (0, c.w - 1) and y >= 3:
                        col = mix(col, hpick(P["coat"], x, y, 62), 0.5)
                elif f in ("left", "right"):
                    i = fx(c, x)                          # 0 = the throat edge
                    col = shade(hpick(P["coat"], x, y, 63), 1.04 - 0.02 * i)
                    if i == 0:
                        col = mix(col, hpick(P["white"] if not cub else P["cream"], x, y, 64), 0.75)
                    elif i == 1:
                        col = mix(col, hpick(P["cream"], x, y, 65), 0.35)
                elif f == "back":
                    col = mix(hpick(P["spine"], x, y, 66), hpick(P["coat"], x, y, 67), 0.5)
                else:
                    col = hpick(P["coat"], x, y, 68)
                c.set(x, y, col)
        if f in ("left", "right"):
            spots(c, P, spacing=3, chance=0.75, big=0.0, salt=69,
                  skip=lambda x, y: fx(c, x) == 0 or y >= c.h - 1)
            if cub:
                for y in range(c.h):                      # the mantle spills down the nape side
                    i = c.w - 1
                    c.set(fx(c, i), y, hpick(P["mantle"], i, y, 70))
                    if hsh(y, c.x0, 71) < 0.5:
                        c.set(fx(c, i - 1), y, hpick(P["mantle_sh"], i, y, 72))
        elif f == "back":
            spots(c, P, spacing=3, chance=0.6, big=0.0, salt=73)
            if cub:
                for y in range(c.h):
                    for x in range(c.w):
                        c.set(x, y, hpick(P["mantle"], x, y, 74))
    return p


def crest_paint(P):
    """The short crest down the nape: darker gold with a few spots on an adult, the long silver
    mantle on a cub (the hairs hang ragged at the sides)."""
    def p(c):
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                col = hpick(P["crest"], x, y, c.x0, 81)
                if not cub and c.face in ("left", "right", "front"):
                    col = shade(col, 0.92)
                if cub and c.face in ("left", "right") and hsh(x, y, 82) < 0.3:
                    col = hpick(P["mantle_sh"], x, y, 83)
                c.set(x, y, col)
        if not cub and c.face in ("back", "top", "left", "right"):
            for y in range(c.h):
                for x in range(c.w):
                    if hsh(x, y, c.x0, 84) < 0.18:
                        c.set(x, y, hpick(P["spot"], x, y, 85))
    return p


# -- head --------------------------------------------------------------------------------------------------
def skull_front(P):
    """5 wide x 5 tall; the muzzle covers columns 1-3 of row 3 and the chin row 4. Pale fur over and
    beside the amber eyes, a small spot between the brows, and the black tear line starting under
    the inner corner of each eye; white cheeks either side of the muzzle."""
    def p(c):
        cub = P["kind"] == "cub"
        wht = P["white"] if not cub else P["white_sh"]
        for y in range(c.h):
            for x in range(c.w):
                col = hpick(P["face"], x, y, 91)
                if y == 0:
                    col = mix(col, hpick(wht, x, y, 90), 0.45) if x in (1, 3) else mix(col, P["brow"], 0.3)
                elif y == 1 and x in (0, c.w - 1):
                    col = mix(hpick(wht, x, y, 94), col, 0.3)
                elif y >= 2 and x in (0, c.w - 1):
                    col = hpick(wht, x, y, 92) if y < c.h - 1 else shade(hpick(wht, x, y, 93), 0.93)
                c.set(x, y, col)
        for ex in (1, 3):
            c.set(ex, 1, P["iris"])
            c.set(ex, 2, P["tear"])
        c.set(2, 0, hpick(P["spot_soft"], 2, 0, 95))           # a little spot between the brows
        c.set(2, 1, shade(hpick(P["face"], 2, 1, 96), 0.96))
        c.set(2, 2, shade(hpick(P["face"], 2, 2, 97), 1.03))
    return p


def skull_side(P):
    """4 deep x 5 tall. The eye at the front corner (amber, a dark rim behind it, pale fur under it),
    the tear line running down the front edge below it, one soft spot on the cheek, a white jowl
    along the bottom."""
    def p(c):
        cub = P["kind"] == "cub"
        wht = P["white"] if not cub else P["white_sh"]
        for y in range(c.h):
            for x in range(c.w):
                i = fx(c, x)                                     # 0 = front
                col = hpick(P["face"], x, y, 101)
                if y == 0:
                    col = mix(col, P["brow"], 0.3)
                elif y == c.h - 1 and i <= 2:
                    col = hpick(wht, x, y, 102)
                c.set(x, y, col)
        c.set(fx(c, 0), 1, P["iris"])                            # the eye, seen from the side
        c.set(fx(c, 1), 1, P["pupil"])                           # its dark back corner
        c.set(fx(c, 0), 0, mix(hpick(wht, 0, 0, 108), P["face"][0], 0.4))
        c.set(fx(c, 1), 2, hpick(wht, 1, 2, 104))                # pale fur under the eye
        c.set(fx(c, 0), 2, P["tear"])                            # the tear line drops from the eye
        c.set(fx(c, 0), 3, P["tear"])
        c.set(fx(c, 1), 3, mix(hpick(wht, 1, 3, 109), hpick(P["face"], 1, 3, 110), 0.5))
        c.set(fx(c, 3), 2, hpick(P["spot_soft"], 3, 2, 106))     # a cheek spot
    return p


def skull_top(P):
    def p(c):
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                col = shade(hpick(P["face"], x, y, 111), 1.06)
                if front_dist(c, x, y) == 0:
                    col = mix(col, P["brow"], 0.3)
                c.set(x, y, col)
        spots(c, P, spacing=2, chance=0.4, big=0.0, salt=112, soft=False, pal="spot_soft",
              skip=lambda x, y: front_dist(c, x, y) == 0)
        if cub:
            for y in range(c.h):                                # the mantle starts on the crown
                for x in (1, 2, 3):
                    if front_dist(c, x, y) <= 1:
                        continue
                    c.set(x, y, hpick(P["mantle"], x, y, 113))
    return p


def skull_back(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(hpick(P["coat"], x, y, 121), 0.97))
        spots(c, P, spacing=2, chance=0.5, big=0.0, salt=122, soft=False)
        if P["kind"] == "cub":
            for y in range(c.h - 1):
                for x in (1, 2, 3):
                    c.set(x, y, hpick(P["mantle"], x, y, 123))
    return p


def skull_bottom(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, hpick(P["white"] if P["kind"] == "adult" else P["white_sh"], x, y, 131))
    return p


def muzzle(P):
    """The upper muzzle, 3 wide x 1 tall x 2 deep: a tan bridge on top with the black nose at its
    front, cream lips either side of the nose, the tear line along the back edge of each side. Its
    underside is the roof of the mouth, seen when the jaw drops."""
    def p(c):
        f = c.face
        cub = P["kind"] == "cub"
        wht = P["white"] if not cub else P["white_sh"]
        for y in range(c.h):
            for x in range(c.w):
                col = hpick(wht, x, y, 141)
                if f == "top":
                    d = front_dist(c, x, y)
                    col = hpick(P["face"], x, y, 142) if d > 0 else mix(hpick(P["face"], x, y, 143), col, 0.4)
                elif f == "front":
                    col = mix(hpick(wht, x, y, 144), hpick(P["face"], x, y, 145), 0.25)
                elif f in ("left", "right"):
                    col = P["tear"] if fx(c, x) == c.w - 1 else mix(hpick(wht, x, y, 146), hpick(P["face"], x, y, 147), 0.2)
                elif f == "bottom":
                    col = P["gum"]
                c.set(x, y, col)
        if f == "front":
            c.set(1, 0, P["nose"])
        if f == "top":
            c.set(1, c.h - 1, P["nose"])
            c.set(1, c.h - 2, mix(hpick(P["face"], 1, 0, 148), P["nose_hi"], 0.3))
    return p


def jaw_paint(P):
    """The chin, 3 wide x 1 tall x 2 deep: white, the black corner of the mouth at the back of each
    side, the top (inside the mouth) dark pink."""
    def p(c):
        cub = P["kind"] == "cub"
        wht = P["white"] if not cub else P["white_sh"]
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = P["gum"]
                elif c.face in ("left", "right") and fx(c, x) == c.w - 1:
                    col = P["tear"]
                elif c.face == "front":
                    col = hpick(wht, x, y, 151) if x != 1 else shade(hpick(wht, x, y, 152), 0.9)
                else:
                    col = hpick(wht, x, y, 153)
                    if c.face == "bottom":
                        col = shade(col, 0.92)
                c.set(x, y, col)
    return p


def tongue_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = P["tongue"] if c.face != "bottom" else P["tongue_dk"]
                if c.face == "top" and x == c.w // 2:
                    col = P["tongue_dk"]                       # the groove down the middle
                c.set(x, y, col)
    return p


def ear_paint(P):
    """2 wide x 2 tall x 1 deep, short and round: black behind with a tawny rim at the base, pale fur
    inside under a dark edge."""
    def p(c):
        f = c.face
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                if f == "back":
                    col = P["ear_back"] if y == 0 else mix(P["ear_back"], hpick(P["face"], x, y, 161), 0.3)
                elif f == "front":
                    col = hpick(P["ear_in"] if not cub else P["white_sh"], x, y, 162)
                    if y == 0:
                        col = mix(col, hpick(P["face"], x, y, 164), 0.7)
                elif f == "top":
                    col = P["ear_back"]
                else:
                    col = mix(P["ear_back"], hpick(P["face"], x, y, 163), 0.25 + 0.35 * y)
                c.set(x, y, col)
    return p


# -- legs ----------------------------------------------------------------------------------------------------
def upper_leg(P, hind=False):
    """Forearm / thigh: gold with spots outside, the inner face (toward the other leg) pale cream
    with small spots, a little darker toward the bottom."""
    cub = P["kind"] == "cub"

    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(hpick(P["coat"], x, y, c.x0, 171), 1.05 - 0.12 * y / max(1, c.h - 1))
                if f == "left":                                # the right leg's inner face
                    col = mix(col, hpick(P["cream"], x, y, 172), 0.7 if not cub else 0.4)
                elif f == "back" and not hind:
                    col = mix(col, hpick(P["cream"], x, y, 173), 0.45)   # the pale back of the forearm
                elif f == "front" and hind:
                    col = mix(col, hpick(P["cream"], x, y, 174), 0.3)
                elif f == "top":
                    col = hpick(P["coat"], x, y, 175)
                elif f == "bottom":
                    col = shade(hpick(P["coat"], x, y, 176), 0.85)
                c.set(x, y, col)
        if f != "top" and f != "bottom":
            spots(c, P, spacing=3 if f != "left" else 2, chance=(0.8 if f != "left" else 0.35) * P["leg_spots"], big=0.2,
                  salt=177 + (1 if hind else 0), pal="spot" if f != "left" else "spot_belly",
                  soft=f != "left")
    return p


def lower_leg(P):
    """Wrist or hock down: slim, gold fading paler toward the paw, small spots (fewer on the inside),
    a dark streak down the back of the hind ones (the hock)."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                t = y / max(1, c.h - 1)
                col = mix(hpick(P["coat"], x, y, c.x0, 181), hpick(P["cream"], x, y, 182), 0.15 + 0.4 * t)
                if f == "left":
                    col = mix(col, hpick(P["cream"], x, y, 183), 0.5)
                elif f == "back":
                    col = shade(col, 0.9)
                c.set(x, y, col)
        if f in SIDES:
            spots(c, P, spacing=2, chance=(0.45 if f != "left" else 0.2) * P["leg_spots"], big=0.0, salt=184, soft=False)
    return p


def gaskin(P):
    """The hind leg between stifle and hock: gold with small spots, cream inside, the back edge (the
    tendon down to the hock) a shade darker."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(hpick(P["coat"], x, y, c.x0, 186), 1.02 - 0.08 * y / max(1, c.h - 1))
                if f == "left":
                    col = mix(col, hpick(P["cream"], x, y, 187), 0.6)
                elif f == "back":
                    col = shade(col, 0.86)
                elif f == "front":
                    col = mix(col, hpick(P["cream"], x, y, 188), 0.25)
                c.set(x, y, col)
        if f in SIDES:
            spots(c, P, spacing=2, chance=(0.5 if f != "left" else 0.2) * P["leg_spots"], big=0.0, salt=189, soft=False,
                  pal="spot" if f != "left" else "spot_belly")
    return p


def paw(P):
    """A small neat paw: tawny-cream on top, dark pads underneath, short dark claws showing at the
    front (a cheetah's claws never fully retract)."""
    def p(c):
        f = c.face
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                if f == "bottom":
                    col = P["pad"]
                elif f == "top":
                    col = mix(hpick(P["cream"], x, y, 191), hpick(P["coat"], x, y, 192), 0.3)
                else:
                    col = mix(hpick(P["cream"], x, y, 193), hpick(P["white"] if not cub else P["cream"], x, y, 194), 0.3)
                c.set(x, y, col)
        if f == "front":
            for x in range(c.w):
                c.set(x, 0, P["claw"])
        if f == "top":
            for x in range(c.w):                               # toe lines
                c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.85))
    return p


# -- tail ------------------------------------------------------------------------------------------------------
def tail_paint(P, start, length, total):
    """The tail points backward in its own space. This segment begins `start` px from the tail's
    root and is `length` long; `total` is the tail's whole length. Spotted for the first half, then
    the spots join into black rings, and the last two pixels are the white tip."""
    def p(c):
        f = c.face
        cub = P["kind"] == "cub"
        for y in range(c.h):
            for x in range(c.w):
                if f in ("front", "back"):
                    d = start if f == "front" else start + length - 1
                else:
                    d = start + front_dist(c, x, y)
                col = shade(hpick(P["coat"], x, y, c.x0, 201), 1.05 if f == "top" else (0.9 if f == "bottom" else 1.0))
                if f == "bottom" and not cub:
                    col = mix(col, hpick(P["cream"], x, y, 202), 0.5)
                rel = d / total
                if d >= total - 2:
                    col = hpick(P["tip"], x, y, 203)
                elif rel > 0.55:
                    k = (d - int(total * 0.55)) % 3
                    if k == 0:
                        col = P["ring"]
                    elif k == 1 and rel > 0.75:
                        col = mix(col, P["ring"], 0.25)
                c.set(x, y, col)
        if f in ("left", "right", "top"):
            # spots on the first half only, keeping clear of the rings
            spots(c, P, spacing=2, chance=0.55, big=0.0, salt=204, soft=False,
                  skip=lambda x, y: (start + front_dist(c, x, y)) / total > 0.5)
    return p


# -- the model ---------------------------------------------------------------------------------------------------
def make(texture_id, P):
    """Build the cheetah with the given palette. Geometry is identical for the adult and the cub."""
    m = Model("cheetah", 64, 64, seed=5151, texture_id=texture_id)
    pk = Pack(m)

    # body = the chest, pivot on the spine mid-back (world 0, 12, 0). Chest x -3..3, world y 10.5..16.5,
    # z -10..-1, with the keel below it between the elbows (to y 17.5) and the shoulder blades on top.
    body = m.part("body", (0, 12, 0))
    pk.add(body, (-3, -1.5, -10), (6, 6, 9),
           faces(coat(P, belly_rows=2, y0=0, span=7, mantle=True, spot_salt=1),
                 top=coat(P, mantle=True, spot_salt=2), front=chest_front(P), back=coat(P, spot_salt=3)))
    pk.add(body, (-2, 4.5, -9), (4, 1, 6), faces(keel(P)))
    pk.add(body, (-2.5, -2.5, -9.5), (5, 2, 5), faces(coat(P, grad=0.1, mantle=True, spot_salt=4)), inflate=-0.1)

    # hips = the loin and rump, same pivot. The loin is tucked up (world y 10.5..14.5), the rump deeper
    # and wider again (y 10.5..15.5).
    hips = body.part("hips", (0, 0, 0))
    pk.add(hips, (-2, -1.5, -3), (4, 4, 9),
           faces(coat(P, belly_rows=1, y0=0.5, span=5, mantle=True, spot_salt=5),
                 top=coat(P, mantle=True, spot_salt=6), front=coat(P, spot_salt=7), back=coat(P, spot_salt=8)))
    pk.add(hips, (-2.5, -1.5, 5), (5, 5, 5),
           faces(coat(P, belly_rows=1, y0=0, span=6, spot_salt=9), top=coat(P, mantle=True, spot_salt=10),
                 back=rump_back(P), front=coat(P, spot_salt=11)))

    # tail: from the top of the rump, hanging low in a long J, the ringed tip curling up. Three
    # segments: `tail`, `tail_mid`, `tail_tip`.
    tail = hips.part("tail", (0, -0.5, 9.5), (-1.3, 0, 0))
    pk.add(tail, (-1, -1, 0), (2, 2, 5), faces(tail_paint(P, 0, 5, 16)))
    mid = tail.part("tail_mid", (0, 0, 4.6), (0.55, 0, 0))
    pk.add(mid, (-1, -1, 0), (2, 2, 5), faces(tail_paint(P, 5, 5, 16)), inflate=-0.04)
    tip = mid.part("tail_tip", (0, 0, 4.6), (1.0, 0, 0))
    pk.add(tip, (-1, -1, 0), (2, 2, 6), faces(tail_paint(P, 10, 6, 16)), inflate=-0.08)

    # neck: from the top front of the chest, leaning well forward; the crest runs down its back
    neck = body.part("neck", (0, 0.5, -8.5), (1.15, 0, 0))
    pk.add(neck, (-1.5, -5.5, -2), (3, 6, 4), faces(neck_paint(P)))
    crest = neck.part("crest", (0, 0, 0))
    pk.add(crest, (-1, -5.5, 1.6), (2, 5, 1), faces(crest_paint(P)), inflate=0.05)

    # head: small and round, carried level on the end of the neck. The short muzzle (nose and upper
    # lip) over the chin (`jaw`, which drops to pant, with the `tongue` hidden inside it).
    head = neck.part("head", (0, -5, -0.5), (-1.15, 0, 0))
    pk.add(head, (-2.5, -3.5, -3), (5, 5, 4),
           faces(skull_back(P), front=skull_front(P), right=skull_side(P), left=skull_side(P),
                 top=skull_top(P), bottom=skull_bottom(P)))
    pk.add(head, (-1.5, -0.5, -5), (3, 1, 2), faces(muzzle(P)))
    jaw = head.part("jaw", (0, 0.5, -3))
    pk.add(jaw, (-1.5, 0, -2), (3, 1, 2), faces(jaw_paint(P)), inflate=-0.02)
    tongue = jaw.part("tongue", (0, 0, -1))
    pk.add(tongue, (-1, -0.5, -0.8), (2, 1, 2), faces(tongue_paint(P)), inflate=-0.2)
    # short round ears, set wide on the crown
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        left = sx > 0
        e = head.part(name, (2.0 * sx, -3.0, -0.3), (0, 0, 0.2 * sx))
        pk.add(e, (-1, -2, -0.5), (2, 2, 1), None if left else faces(ear_paint(P)), mirror=left, share="ear",
               inflate=-0.15)

    # front legs (children of body): the forearm from inside the chest, then the slim lower leg and paw
    for name, sx in (("right_front_leg", -1), ("left_front_leg", 1)):
        left = sx > 0
        lg = body.part(name, (2.0 * sx, 1, -6.5))
        pk.add(lg, (-1, -1, -1.5), (2, 7, 3), None if left else faces(upper_leg(P)), mirror=left,
               share="forearm", inflate=0.1)
        lo = lg.part(name + "_lower", (0, 6, 0.3))
        pk.add(lo, (-1, -0.5, -1), (2, 5, 2), None if left else faces(lower_leg(P)), mirror=left,
               share="front_lower", inflate=-0.2)
        pk.add(lo, (-1, 4, -2.2), (2, 1, 3), None if left else faces(paw(P)), mirror=left, share="paw")

    # hind legs (children of hips), in three angled segments: the thigh slants forward to the stifle,
    # the gaskin (`<leg>_lower`) back down to a high hock, and the long foot (`<leg>_foot`) stands
    # straight under it
    for name, sx in (("right_hind_leg", -1), ("left_hind_leg", 1)):
        left = sx > 0
        lg = hips.part(name, (2.0 * sx, 0.5, 7.5), (-0.25, 0, 0))
        pk.add(lg, (-1.5, -1, -2), (3, 6, 4), None if left else faces(upper_leg(P, hind=True)), mirror=left,
               share="thigh")
        lo = lg.part(name + "_lower", (0, 4.5, -0.3), (0.65, 0, 0))
        pk.add(lo, (-1, -0.5, -1), (2, 5, 2), None if left else faces(gaskin(P)), mirror=left,
               share="gaskin", inflate=0.05)
        ft = lo.part(name.replace("_leg", "_foot"), (0, 4.2, 0), (-0.4, 0, 0))
        pk.add(ft, (-1, -0.5, -1), (2, 3, 2), None if left else faces(lower_leg(P)), mirror=left,
               share="hind_lower", inflate=-0.2)
        pk.add(ft, (-1, 2.34, -2.4), (2, 1, 3), None if left else faces(paw(P)), mirror=left, share="paw")

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("cheetah_cub", CUB).save(geometry=False)
    spawn_egg("cheetah", "#dca94e", "#1c1510", accent="#f5efe2")


if __name__ == "__main__":
    build()

"""Raccoon: a stocky masked bandit that can be tamed as a pack-rat pet. Grizzled grey-brown fur,
darker down the spine and paler on the flanks and belly; a hunched back that rises to round,
wide hindquarters; a broad head with fluffy pale cheek ruffs, a black bandit mask across the eyes
between white brows and a white muzzle, a dark stripe down the forehead and nose bridge, a black
button nose and small round pale-rimmed ears. Dark nimble hands, long plantigrade hind feet and a
bushy tail ringed black and grey with a black tip.

Rig: `body` holds the torso, hips and `tail` (with `tail_tip`). The head, with its empty `mouth`
part just below the front of the snout (where the carried item is drawn), and all four legs hang
off the root."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Raccoon"
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


def zb(c, x, y):
    """Distance from the back edge of a top/bottom/side face (0 = the rearmost pixel)."""
    if c.face in ("top", "bottom"):
        return y
    return x if c.face == "right" else c.w - 1 - x


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
FUR = ["#756b62", "#6e655c", "#7b7167", "#685f57", "#72695f"]
FLECK = ["#a59c90", "#9b9286", "#afa699"]          # pale guard-hair tips
DARK = ["#423a35", "#4a413b", "#3b3430"]           # dark guard hairs, the spine
BELLY = ["#978d80", "#8f8578", "#9e9487"]
MASK = ["#211c1a", "#262120", "#1d1917"]
WHITE = ["#ece8df", "#e3dfd5", "#f2efe8"]
WHITE_SH = ["#cbc6bb", "#c3bdb1"]
CHEEK = ["#d9d4ca", "#cfcabf", "#e0dbd2"]
BRIDGE = ["#4a423c", "#544b44"]
NOSE = "#121010"
NOSE_HI = "#4b4442"
EYE = "#050404"
SHINE = "#eef3f6"
EAR_IN = ["#3b3431", "#433b37"]
HAND = ["#2c2725", "#332d2a", "#282321"]
FINGER = "#4d4642"
TAIL_G = ["#968c80", "#8e8479", "#9d9387"]
TAIL_D = ["#2a2522", "#302a27", "#25201e"]


def fur(top=1.07, grad=0.22, belly_rows=0, flecks=0.08, spine=False, y0=0, span=None, spine_edge=False):
    """Grizzled fur: grey-brown with pale guard-hair tips and dark flecks, lit on top and darkening
    down the sides toward a paler belly. y0/span place a face on a body-wide gradient."""
    def p(c):
        sp = span or c.h
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    col = shade(c.pick(BELLY), 0.86)
                else:
                    col = c.pick(FUR)
                    r = c.rng.random()
                    if r < flecks:
                        col = c.pick(FLECK)
                    elif r < flecks * 1.6:
                        col = c.pick(DARK)
                    f = top if c.face == "top" else 1.05 - grad * ((y0 + y + 0.5) / sp)
                    col = shade(col, f)
                    if belly_rows and y >= c.h - belly_rows and c.face in ("left", "right"):
                        col = mix(col, c.pick(BELLY), 0.55)
                c.set(x, y, col)
        if c.face == "top" and spine:              # the darker saddle down the middle of the back
            mid = (c.w - 1) / 2
            for y in range(c.h):
                for x in range(c.w):
                    d = abs(x - mid)
                    if d < 1.0 or (d < 2.0 and c.rng.random() < 0.45):
                        c.set(x, y, shade(c.pick(DARK), 1.12 if c.rng.random() < 0.3 else 1.0))
        if c.face in ("left", "right", "front", "back") and c.h > 2:
            for _ in range(int(c.w * c.h * 0.1)):   # short vertical hair strokes
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h - 1)
                k = 0.88 if c.rng.random() < 0.65 else 1.1
                for yy in (y, y + 1):
                    c.set(x, yy, shade(c.get(x, yy), k))
        if c.face in ("left", "right") and spine_edge and c.h > 3:
            for x in range(c.w):                   # the dark saddle laps over the top of the flanks
                if c.rng.random() < 0.7:
                    c.set(x, 0, mix(c.get(x, 0), c.pick(DARK), 0.55))
    return p


def belly(c):
    """Underside: pale buff-grey, a little darker toward the edges."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BELLY)
            if x in (0, c.w - 1):
                col = shade(col, 0.88)
            c.set(x, y, shade(col, 0.95))


def chest(c):
    """The front of the torso, under the chin: darker grey, shading to the throat."""
    fur(grad=0.3, flecks=0.08)(c)
    for x in range(c.w):
        c.set(x, c.h - 1, shade(c.pick(DARK), 1.05))


def rump_back(c):
    """The round hindquarters seen from behind: grizzled grey, paler low down (around the tail)."""
    fur(grad=0.1)(c)
    for y in range(c.h - 2, c.h):
        for x in range(c.w):
            c.set(x, y, mix(c.get(x, y), c.pick(BELLY), 0.35))


# -- head --------------------------------------------------------------------------------------------
# skull front, 7 wide x 5 tall (the snout covers columns 2-4 of rows 3-4):
#   G = grey crown, S = dark forehead stripe, W = white brow, g = greyer brow over the glint (so
#   the glint doesn't run into the white), M = black mask, H = eye shine, E = eye, C = white cheek
FACE = [
    "GGGSGGG",
    "WgWSWgW",
    "MHESEHM",
    "MMMMMMM",
    "CCMMMCC",
]


def skull_front(c):
    for y, row in enumerate(FACE):
        for x, ch in enumerate(row):
            col = {"G": shade(c.pick(FUR), 1.08), "S": c.pick(BRIDGE), "W": c.pick(WHITE),
                   "g": mix(c.pick(WHITE), c.pick(FUR), 0.45), "M": c.pick(MASK), "H": SHINE,
                   "E": EYE, "C": c.pick(CHEEK)}[ch]
            c.set(x, y, col)


def skull_side(c):
    """5 deep x 5 tall: the mask runs back from the eye under the ear, white brow above it at the
    front, pale cheek below, grey crown and nape."""
    for y in range(c.h):
        for x in range(c.w):
            i = fx(c, x)                           # 0 = front
            if y == 0:
                col = shade(c.pick(FUR), 1.04)
            elif y == 1:
                col = c.pick(WHITE) if i == 0 else (mix(c.pick(WHITE), c.pick(FUR), 0.5) if i == 1 else c.pick(FUR))
            elif y in (2, 3):
                if i <= 2 or (y == 3 and i == 3):
                    col = c.pick(MASK)
                elif i == 3:
                    col = mix(c.pick(MASK), c.pick(FUR), 0.45)
                else:
                    col = c.pick(FUR)
            else:
                col = c.pick(CHEEK) if i <= 2 else mix(c.pick(CHEEK), c.pick(FUR), 0.5)
            c.set(x, y, col)


def skull_top(c):
    """7 x 5 from above: grey crown, the dark stripe down the middle reaching the brow line."""
    mid = c.w // 2
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(FUR), 1.1)
            if c.rng.random() < 0.15:
                col = shade(c.pick(FLECK), 1.04)
            if x == mid and y >= c.h - 3:
                col = c.pick(BRIDGE)
            elif x == mid and c.rng.random() < 0.6:
                col = shade(c.pick(DARK), 1.1)
            c.set(x, y, col)
    for x in range(c.w):                           # the white brows show at the front edge
        if x != mid:
            c.set(x, c.h - 1, mix(c.pick(WHITE), c.pick(FUR), 0.6 if x in (0, c.w - 1) else 0.3))


def skull_back(c):
    fur(grad=0.2)(c)


def skull_bottom(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(CHEEK) if y >= c.h - 2 else shade(c.pick(BELLY), 0.92))


def ruff(c):
    """The fluffy cheek ruffs, poking out sideways under the mask: pale, with the mask's black tail
    across the top at the front."""
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(CHEEK), c.pick(FUR), 0.3)
            if c.face in ("right", "left"):
                i = fx(c, x)
                if i <= 1 and y > 0:
                    col = c.pick(CHEEK)
                if y == 0 and i <= 1:
                    col = mix(c.pick(MASK), c.pick(CHEEK), 0.25)
                elif y == c.h - 1:
                    col = c.pick(WHITE_SH)
                if i == c.w - 1:
                    col = mix(col, c.pick(FUR), 0.45)
            elif c.face == "top":
                col = mix(c.pick(MASK), c.pick(FUR), 0.5) if y >= c.h - 1 else c.pick(FUR)
            elif c.face == "bottom":
                col = c.pick(WHITE_SH)
            elif c.face == "back":
                col = mix(c.pick(CHEEK), c.pick(FUR), 0.55)
            elif c.face == "front":
                if y == 0:
                    col = c.pick(MASK)
            c.set(x, y, col)
    if c.face in ("right", "left"):                # a ragged lower edge
        for x in range(c.w):
            if c.rng.random() < 0.35:
                c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.9))


def snout(c):
    """The narrow white snout with the dark bridge line running down its top to the nose."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(WHITE)
            if c.face == "top":
                col = c.pick(BRIDGE) if y < c.h - 1 else mix(c.pick(BRIDGE), c.pick(WHITE), 0.35)
            elif c.face == "bottom":
                col = c.pick(WHITE_SH)
            elif c.face in ("right", "left"):
                col = c.pick(WHITE) if y == 0 else shade(c.pick(WHITE), 0.95)
                if fx(c, x) == c.w - 1 and y == 0:
                    col = mix(c.pick(MASK), c.pick(WHITE), 0.5)
                if y == c.h - 1 and fx(c, x) <= 1:
                    col = mix(c.pick(WHITE), "#5a504a", 0.45)   # the line of the mouth
            elif c.face == "front":
                col = c.pick(WHITE) if y < c.h - 1 else mix(c.pick(WHITE), "#5a504a", 0.4)
            c.set(x, y, col)


def nose(c):
    c.fill(NOSE)
    if c.face == "top":
        c.set(0, c.h - 1, NOSE_HI)
    elif c.face == "front":
        c.set(0, 0, shade(NOSE_HI, 0.85))


RIM = ["#bfb8ad", "#b6afa4"]


def ear_base(c):
    """The lower part of the small round ear (3 wide): a pale rim either side of the dark hollow
    in front, grey-brown behind with a dark patch at the base."""
    if c.face == "front":
        c.set(0, 0, c.pick(RIM)); c.set(1, 0, c.pick(EAR_IN)); c.set(2, 0, c.pick(RIM))
    elif c.face == "back":
        c.set(0, 0, c.pick(FUR)); c.set(1, 0, c.pick(DARK)); c.set(2, 0, c.pick(FUR))
    elif c.face == "top":
        c.set(0, 0, c.pick(RIM)); c.set(1, 0, c.pick(RIM)); c.set(2, 0, c.pick(RIM))
    elif c.face in ("right", "left"):
        c.set(0, 0, shade(c.pick(FUR), 1.05))
    else:
        c.fill(c.pick(DARK))


def ear_tip(c):
    """The rounded top of the ear (1 wide): pale rim."""
    if c.face in ("front", "top"):
        c.set(0, 0, c.pick(RIM))
    elif c.face == "back":
        c.set(0, 0, mix(c.pick(RIM), c.pick(FUR), 0.5))
    else:
        c.set(0, 0, shade(c.pick(FUR), 1.08))


WHISKER = "#efece6"


def whiskers(c):
    """Pale whiskers sticking out beside the snout (a flat plane, front and back alike)."""
    for x in range(c.w):
        c.set(x, 0, WHISKER)
    outer = 0 if c.face == "front" else c.w - 1   # painted for the right side; the left mirrors it
    c.set(outer, 0, shade(WHISKER, 0.88))


# -- legs and tail -----------------------------------------------------------------------------------
def fore_leg(c):
    """Grey upper arm into a dark wrist and a black hand with paler finger tips at the front."""
    for y in range(c.h):
        for x in range(c.w):
            if y < 2:
                col = shade(c.pick(FUR), 1.0 - 0.06 * y)
            elif y == 2:
                col = mix(c.pick(FUR), c.pick(HAND), 0.6)
            else:
                col = c.pick(HAND)
            if c.face in ("back", "left") and y < 2:
                col = shade(col, 0.92)
            c.set(x, y, col)
    if c.face == "front":                          # little fingers
        c.set(0, c.h - 1, FINGER); c.set(1, c.h - 1, shade(FINGER, 0.85))
    if c.face == "bottom":
        c.noise(["#1d1918", "#24201e"])


def thigh(c):
    fur(grad=0.25, flecks=0.1)(c)
    if c.face == "bottom":
        c.noise(BELLY)


def shin(c):
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(FUR), c.pick(HAND), min(1.0, 0.35 + 0.35 * y))
            c.set(x, y, col)


def foot(c):
    c.noise(HAND)
    if c.face == "front":
        c.set(0, 0, FINGER); c.set(1, 0, shade(FINGER, 0.85))
    elif c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, shade(FINGER, 0.9))   # toes at the front edge
    elif c.face == "bottom":
        c.noise(["#1d1918", "#24201e"])


def ring_tail(start, rings, tip=False):
    """Bushy tail fur in rings along its length. rings[i] says what the i-th pixel from the front of
    this segment is: 'g' grey, 'd' black. Black ring pixels are a touch paler on top (sheen)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face in ("top", "bottom", "right", "left"):
                    i = (c.h if c.face in ("top", "bottom") else c.w) - 1 - zb(c, x, y)
                elif c.face == "front":
                    i = 0
                else:
                    i = len(rings) - 1
                kind = rings[min(i, len(rings) - 1)]
                col = c.pick(TAIL_D) if kind == "d" else c.pick(TAIL_G)
                if kind == "g" and c.rng.random() < 0.15:
                    col = c.pick(FLECK)
                if c.face == "top":
                    col = shade(col, 1.12 if kind == "g" else 1.35)
                elif c.face == "bottom":
                    col = shade(col, 0.85)
                elif c.face in ("right", "left") and y == c.h - 1:
                    col = shade(col, 0.9)
                c.set(x, y, col)
        if tip and c.face == "back":
            c.fill(TAIL_D[0])
            c.set(1, 1, shade(TAIL_D[1], 1.3))
    return p


def build():
    m = Model("raccoon", 64, 64, seed=3737)
    pk = Pack(m)

    # body: pivot over the hips (z 2) so it can tip back to sit. The back climbs in steps from low
    # shoulders (y 15) over the loins (14) to the high, wide hindquarters (13): the hunched raccoon
    # back. Torso x -3..3, y 15..20, z -5..2; rump x -3.5..3.5, y 13..19, z -1..4.
    body = m.part("body", (0, 18, 2))
    pk.add(body, (-3, -3, -7), (6, 5, 7),
           faces(fur(belly_rows=1, y0=1, span=6, spine_edge=True), top=fur(spine=True), front=chest, bottom=belly))
    pk.add(body, (-3, -4, -5), (6, 1, 2), faces(fur(), top=fur(spine=True, top=1.09)))
    pk.add(body, (-3.5, -5, -3), (7, 6, 5),
           faces(fur(belly_rows=1, span=6, spine_edge=True), top=fur(spine=True, top=1.11), back=rump_back, bottom=belly))

    # head: pivot at the neck; skull x -3.5..3.5, y 13..18, z -9..-4; fluffy cheek ruffs stick out a
    # pixel each side; the white snout runs 3 more forward with the black nose on its tip.
    head = m.part("head", (0, 17, -4.5))
    pk.add(head, (-3.5, -3.5, -4.5), (7, 5, 5),
           faces(skull_back, front=skull_front, right=skull_side, left=skull_side, top=skull_top,
                 bottom=skull_bottom))
    pk.add(head, (-4.5, -0.5, -3.5), (9, 2, 3), faces(ruff))
    pk.add(head, (-1.5, -0.5, -7.5), (3, 2, 3), faces(snout))
    pk.add(head, (-1, -0.75, -8), (2, 1, 1), faces(nose), inflate=0.05)
    for sx in (-1, 1):
        left = sx > 0
        for wy in (0.5, 1.1):                      # two hair-thin whiskers a side
            pk.add(head, (1.5 if left else -4.5, wy, -6.5), (3, 0.4, 0), None if left else faces(whiskers),
                   mirror=left, share="whiskers")
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        e = head.part(name, (2.5 * sx, -3.5, -2))
        left = sx > 0
        pk.add(e, (-1.5, -1, -0.5), (3, 1, 1), None if left else faces(ear_base), mirror=left, share="ear")
        pk.add(e, (-0.5, -2, -0.5), (1, 1, 1), None if left else faces(ear_tip), mirror=left, share="ear_tip")
    head.part("mouth", (0, 2.0, -6.5))             # where the carried item sits, under the snout

    # front legs: grey arm, black hand
    for name, sx in (("right_front_leg", -1), ("left_front_leg", 1)):
        lg = m.part(name, (2 * sx, 19, -3.5))
        left = sx > 0
        pk.add(lg, (-1, 0, -1), (2, 5, 2), None if left else faces(fore_leg), mirror=left, share="fleg")

    # hind legs: a meaty thigh, a dark shin and a long flat foot (raccoons walk on their soles)
    for name, sx in (("right_hind_leg", -1), ("left_hind_leg", 1)):
        lg = m.part(name, (2.25 * sx, 18.5, 2.5))
        left = sx > 0
        pk.add(lg, (-1.5, -1.5, -1.5), (3, 4, 3), None if left else faces(thigh), mirror=left, share="thigh")
        pk.add(lg, (-1, 2.5, -0.75), (2, 3, 2), None if left else faces(shin), mirror=left, share="shin",
               inflate=-0.05)
        pk.add(lg, (-1, 4.5, -2.75), (2, 1, 2), None if left else faces(foot), mirror=left, share="foot")

    # tail: from the top of the rump, held out behind and drooping, bushy and ringed
    tail = body.part("tail", (0, -2.5, 2), (-0.55, 0, 0))
    pk.add(tail, (-1.5, -1.5, 0), (3, 3, 5), faces(ring_tail(0, "ggdgd")), inflate=0.35)
    tip = tail.part("tail_tip", (0, 0, 5), (0.25, 0, 0))
    pk.add(tip, (-1.5, -1.5, 0), (3, 3, 4), faces(ring_tail(5, "gdgd", tip=True)), inflate=0.2)

    pk.apply()
    m.save()
    spawn_egg("raccoon", "#878075", "#211c1a", accent="#ece8df")


if __name__ == "__main__":
    build()

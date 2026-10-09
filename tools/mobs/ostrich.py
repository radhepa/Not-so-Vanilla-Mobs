"""Ostrich: a huge, rideable bird. A big round body of loose black plumage with a glossy sheen, white
plumes on the wing tips and a white fluffy tail; a long bare pink-grey neck with sparse grey down
rising from a black feathered collar; a small head with big dark eyes under long black lashes and a
broad flat horn-pink beak; long bare pink-grey legs: muscular drumsticks, a backward heel, scaly
shanks and big two-toed feet (one long inner toe with a nail, one small outer toe).
The back is flat-topped at the rider's seat height (passenger attachment 1.2 blocks = model y 4.8);
`saddle` (child of body) is the leather saddle with skirts and stirrups, shown only when saddled.
The wings are authored spread (span along x, chord along z) and folded against the flanks by their
rest rotation, so the code can open them to glide. Legs are children of root with a `*_shin` below
the heel.
`ostrich_chick` shares the geometry: buff down striped dark brown, a pale face, grey-brown legs
(the game draws it at half scale; chicks are never saddled)."""
import math
import os
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Ostrich"
LOOT = [item("feather", 1, 3)]
TAGS = ["can_equip_saddle"]

# Debug only: OSTRICH_POSE=glide previews the wings open, =run a stride.
POSE = os.environ.get("OSTRICH_POSE", "")


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


def _h(x, y, salt):
    """A stable random number per pixel, so both faces of a plane match exactly."""
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
BLACK = ["#211d1e", "#272223", "#1b1819", "#2c2627", "#231f20"]
BLACK_DK = ["#141112", "#171415"]
SHEEN = ["#3b3436", "#433b3d", "#352f31"]
WHITE = ["#f3f1ec", "#ebe8e1", "#f7f5f1"]
WHITE_SH = ["#d3cec4", "#c9c3b8", "#dcd8cf"]
SKIN = ["#cba39b", "#d2aca4", "#c39a92", "#cea79f"]
SKIN_DK = ["#a98179", "#b08880"]
SCUTE = "#94706a"
FUZZ = ["#9f9894", "#aaa39f"]
BEAK = ["#ddb8a8", "#e4c3b4", "#d6ae9d"]
BEAK_DK = "#b58f80"
BEAK_TIP = "#9b7769"
IRIS = "#5a3520"
PUPIL = "#0e0a0a"
SHINE = "#fffaf0"
LASH = "#121011"
NAIL = "#3d3434"
LEATHER = ["#6e4428", "#784a2c", "#653e24", "#734729"]
LEATHER_DK = ["#4f301b", "#55341e"]
LEATHER_HI = "#93603a"
STITCH = "#caa46e"
IRON = ["#9a9a9c", "#a9a9ab"]
CLOTH = ["#9b2f2a", "#a5352f", "#912b26"]
TRIM = ["#e3d3a8", "#d9c79a"]
IRON_HI = "#dadadc"
IRON_DK = "#6a6a6d"


def plumage(top=1.06, bottom=0.78, grad=0.22, sheen=0.14):
    """Loose black plumage: glossy on top, side faces darkening downward, soft lighter tufts with
    dark dents under them so it reads shaggy."""
    def p(c):
        for y in range(c.h):
            f = top if c.face == "top" else bottom if c.face == "bottom" else 1.06 - grad * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(BLACK), f))
        for _ in range(int(c.w * c.h * sheen)):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            if c.face == "bottom":
                continue
            c.set(x, y, shade(c.pick(SHEEN), 1.0 if c.face == "top" else 1.0 - 0.15 * y / max(1, c.h)))
            if c.inside(x, y + 1) and c.face in SIDES:
                c.set(x, y + 1, c.pick(BLACK_DK))
    return p


def feather_rows(c, every=3):
    """Layered loose feathers on a side face: every few rows a broken line of glossy feather tips
    over a dark gap, staggered row to row, so the plumage hangs in tiers."""
    for y in range(1, c.h - 1):
        if y % every:
            continue
        off = (y // every) % 2
        for x in range(c.w):
            k = (x + off) % 3
            if k == 0:
                c.set(x, y, shade(c.pick(SHEEN), 1.05 - 0.2 * y / c.h))
            elif k == 1:
                c.set(x, y, shade(c.pick(SHEEN), 0.9 - 0.2 * y / c.h))
                if c.inside(x, y + 1):
                    c.set(x, y + 1, c.pick(BLACK_DK))


def body_side(c):
    """14 long x 8 tall: shaggy black in tiers; the lower edge breaks into loose feather tips."""
    plumage(sheen=0.06)(c)
    feather_rows(c)
    for x in range(c.w):
        c.set(x, c.h - 1, c.pick(BLACK_DK) if (x + c.rng.randrange(2)) % 2 == 0 else c.pick(SHEEN))


def body_front(c):
    plumage(grad=0.25, sheen=0.06)(c)
    feather_rows(c)


def body_back(c):
    plumage(grad=0.3, sheen=0.06)(c)
    feather_rows(c)


def hump_top(c):
    """The flat back where the rider sits: glossy black."""
    plumage(top=1.1, sheen=0.25)(c)


def plume_fluff(c, strength=1.0):
    """White plumes: soft, shaded, a few grey feather lines."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(WHITE)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.02 - 0.12 * y / (c.h - 1))
            elif c.face == "bottom":
                col = c.pick(WHITE_SH)
            c.set(x, y, col)
    for _ in range(int(c.w * c.h / 5 * strength)):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        c.set(x, y, c.pick(WHITE_SH))


def tail_core(c):
    plume_fluff(c)


def tail_shell(c):
    """An inflated shell over the tail with most pixels cut out: a fluffy outline."""
    for y in range(c.h):
        for x in range(c.w):
            keep = c.rng.random() < (0.55 if c.face in ("top", "back") else 0.35)
            if c.face in SIDES and y == c.h - 1:
                keep = c.rng.random() < 0.6
            if not keep:
                c.clear(x, y)
                continue
            col = c.pick(WHITE) if c.rng.random() < 0.7 else c.pick(WHITE_SH)
            c.set(x, y, col)


# -- wings (authored spread: on top/bottom faces column 0 is the wing tip, row 0 the trailing edge) --
def wing_surface(c):
    """Black coverts toward the leading edge, the big white plumes at the tip and along the
    trailing edge."""
    for y in range(c.h):                           # y: 0 = trailing .. h-1 = leading
        for x in range(c.w):                       # x: 0 = tip .. w-1 = shoulder
            if x <= 1 or y <= 1:
                col = c.pick(WHITE) if (x + y) % 3 else c.pick(WHITE_SH)
                if y == 1 and x > 1:
                    col = mix(col, c.pick(BLACK), 0.15)
            else:
                col = c.pick(BLACK)
                if (x + 2 * y) % 4 == 0:
                    col = c.pick(SHEEN)
                if y == c.h - 1:
                    col = shade(col, 1.15)
            c.set(x, y, col)


def wing_edge(c):
    if c.face == "front":                          # leading edge: black, white at the tip
        for x in range(c.w):
            c.set(x, 0, c.pick(BLACK) if x > 1 else c.pick(WHITE))
    elif c.face == "left":                         # the root against the body
        c.noise(BLACK)
    else:                                          # tip and trailing edge: white plumes
        c.noise(WHITE)


PLUME_MASK = [        # row 0 = the far (hanging) edge of the plume fringe; col 0 = the wing tip
    "#.#.#.#",
    "#######",
]


def plume_plane(c):
    """Loose white plume tips hanging below the folded wing (a zero-thickness plane: both faces are
    painted the same pure function of (x, y))."""
    for y in range(c.h):
        for x in range(c.w):
            if PLUME_MASK[y][x] != "#":
                c.clear(x, y)
                continue
            r = _h(x, y, 5)
            col = WHITE[int(r * len(WHITE)) % len(WHITE)]
            if y == 1:
                col = WHITE_SH[int(r * len(WHITE_SH)) % len(WHITE_SH)]
            c.set(x, y, col)


# -- neck and head -----------------------------------------------------------------------------------
def skin(c, fuzz=0.12):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SKIN)
            if c.face in ("back", "right"):
                col = shade(col, 0.93)
            c.set(x, y, col)
    for _ in range(int(c.w * c.h * fuzz) + 1):    # sparse grey down
        c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(FUZZ))


def collar(c):
    """Base of the neck: the black body plumage reaches up it, ragged at its top edge."""
    plumage(grad=0.15)(c)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, c.pick(SKIN) if (x + (c.face in ("left", "back"))) % 2 else c.pick(FUZZ))
    elif c.face == "top":
        c.noise(SKIN)


def head_side(c):
    """4 long x 3 tall: a big dark eye (2 x 2) under long black lashes, the gape under it."""
    skin(c, 0.05)
    for i in (1, 2, 3):
        c.set(fx(c, i), 0, LASH)                   # the lashes sweep back over the eye
    c.set(fx(c, 1), 1, SHINE)
    c.set(fx(c, 2), 1, PUPIL)
    c.set(fx(c, 1), 2, IRIS)
    c.set(fx(c, 2), 2, shade(IRIS, 0.7))
    c.set(fx(c, 0), 2, BEAK_DK)                    # the gape runs back under the eye
    c.set(fx(c, 3), 2, c.pick(SKIN_DK))
    c.set(fx(c, 3), 1, c.pick(FUZZ))


def head_top(c):
    skin(c, 0.4)                                   # a fuzzy crown


def head_front(c):
    skin(c, 0.05)
    c.set(0, 0, LASH); c.set(c.w - 1, 0, LASH)     # lashes peek round the corners


def beak(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BEAK)
            if c.face in ("left", "right"):
                col = shade(col, 0.95)
            elif c.face == "bottom":
                col = BEAK_DK
            c.set(x, y, col)
    if c.face == "top":                            # row 0 = back: nostrils; the rounded tip at the front
        c.set(0, 1, BEAK_DK); c.set(c.w - 1, 1, BEAK_DK)
        c.set(0, c.h - 1, BEAK_TIP); c.set(c.w - 1, c.h - 1, BEAK_TIP)
        c.set(1, c.h - 1, shade(BEAK[0], 0.92))
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, 0, BEAK_TIP if x != 1 else shade(BEAK[0], 0.9))
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, BEAK_TIP)


# -- legs ----------------------------------------------------------------------------------------------
def thigh(c):
    """The bare, muscular drumstick: rounded shading, black plumage at the top."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SKIN)
            if c.face in SIDES:
                col = shade(col, 1.06 - 0.14 * abs(x - (c.w - 1) / 2) / max(1, (c.w - 1) / 2))
            c.set(x, y, col)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, c.pick(BLACK))
            if c.rng.random() < 0.6:
                c.set(x, 1, c.pick(BLACK))
    elif c.face == "top":
        c.noise(BLACK)


def shank(c):
    """The scaly shank: a row of darker scutes down the front."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SKIN)
            if c.face in ("right", "back"):
                col = shade(col, 0.9)
            c.set(x, y, col)
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, SCUTE if y % 2 == 0 else c.pick(SKIN_DK))
    elif c.face == "top":
        c.noise(SKIN_DK)


def heel(c):
    c.noise(SKIN_DK)


def big_toe(c):
    """The long inner toe, scutes on top and a dark nail at the tip."""
    c.noise(SKIN)
    if c.face == "top":                            # row 0 = back
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, SCUTE if y % 2 else c.pick(SKIN))
        for x in range(c.w):
            c.set(x, c.h - 1, NAIL)
    elif c.face == "front":
        c.noise([NAIL])
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, NAIL)
    elif c.face == "bottom":
        c.noise(SKIN_DK)


def small_toe(c):
    c.noise(SKIN)
    if c.face == "top":
        c.set(0, c.h - 1, shade(NAIL, 1.4))
    elif c.face == "bottom":
        c.noise(SKIN_DK)


# -- saddle ------------------------------------------------------------------------------------------
def leather(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LEATHER)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.0 - 0.15 * y / (c.h - 1))
            elif c.face == "bottom":
                col = c.pick(LEATHER_DK)
            c.set(x, y, col)


def blanket(c):
    """A red saddle cloth under the seat, its edges peeking out, piped in cream."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CLOTH)
            if c.face == "top" and (x in (0, c.w - 1) or y in (0, c.h - 1)):
                col = shade(col, 0.85)
            c.set(x, y, col)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, c.pick(TRIM))


def seat(c):
    leather(c)
    if c.face == "top":                            # a dark rolled edge, stitching, a worn lighter middle
        for y in range(c.h):
            for x in range(c.w):
                if x in (0, c.w - 1) or y in (0, c.h - 1):
                    c.set(x, y, c.pick(LEATHER_DK))
                elif (x in (1, c.w - 2) or y in (1, c.h - 2)) and (x + y) % 3 == 0:
                    c.set(x, y, mix(STITCH, LEATHER[0], 0.35))
                elif 1 < x < c.w - 2 and 1 < y < c.h - 2:
                    c.set(x, y, mix(c.pick(LEATHER), LEATHER_HI, 0.3))
    elif c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, mix(LEATHER_HI, LEATHER[0], 0.4))


def rim(c):
    leather(c)
    if c.face == "top":
        c.noise([LEATHER_HI, shade(LEATHER_HI, 0.9)])


def skirt(c):
    leather(c)
    if c.face in ("left", "right"):
        for i in range(c.w):
            c.set(i, c.h - 1, c.pick(LEATHER_DK))
        for y in range(c.h - 1):
            c.set(0, y, STITCH if y % 2 == 0 else c.get(0, y))
            c.set(c.w - 1, y, STITCH if y % 2 == 0 else c.get(c.w - 1, y))


def strap(c):
    """A zero-thickness strap: both faces the same."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, LEATHER_DK[0] if y % 3 else LEATHER[0])


def stirrup(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(IRON))
    if c.face == "top":
        c.noise([IRON_HI])
    elif c.face == "bottom":
        c.noise([IRON_DK])


ADULT = dict(
    body=faces(plumage(), right=body_side, left=body_side, front=body_front, back=body_back),
    hump=faces(plumage(), top=hump_top),
    breast=faces(plumage(grad=0.3)), belly=faces(plumage(bottom=0.7)), rump=faces(plumage(grad=0.3)),
    tail=faces(tail_core), tail_shell=faces(tail_shell),
    wing=faces(wing_edge, top=wing_surface, bottom=wing_surface), plume=faces(plume_plane),
    collar=faces(collar), neck=faces(skin),
    head=faces(skin, right=head_side, left=head_side, top=head_top, front=head_front),
    beak=faces(beak),
    thigh=faces(thigh), shank=faces(shank), heel=faces(heel), big_toe=faces(big_toe), small_toe=faces(small_toe),
    seat=faces(seat), rim=faces(rim), skirt=faces(skirt), strap=faces(strap), stirrup=faces(stirrup),
    blanket=faces(blanket),
)

# -- chick ---------------------------------------------------------------------------------------------
BUFF = ["#c9a46f", "#d1ae7c", "#c09966", "#cca877"]
BUFF_LT = ["#e2c89c", "#e8d1a8"]
STRIPE = ["#5f4128", "#553a23", "#684830"]
C_LEG = ["#8e7f72", "#978879", "#857669"]


def down(stripes=True, pal=None):
    """Spiky buff down, striped lengthwise in dark brown, with pale tips."""
    base = pal or BUFF

    def p(c):
        for y in range(c.h):
            f = 1.06 if c.face == "top" else 0.84 if c.face == "bottom" else 1.04 - 0.16 * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(base), f))
        if stripes:
            if c.face == "top":                    # stripes run along the body (front to back)
                for y in range(c.h):
                    for x in range(c.w):
                        if x % 3 == 1:
                            c.set(x, y, c.pick(STRIPE))
            elif c.face in ("left", "right"):
                for x in range(c.w):
                    for y in range(c.h):
                        if y % 3 == 1 and c.rng.random() < 0.8:
                            c.set(x, y, c.pick(STRIPE))
            elif c.face in ("front", "back"):
                for y in range(c.h):
                    for x in range(c.w):
                        if x % 3 == 1 and c.rng.random() < 0.7:
                            c.set(x, y, c.pick(STRIPE))
        for _ in range(c.w * c.h // 8):
            c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(BUFF_LT))
    return p


def c_neck(c):
    down(stripes=False)(c)
    if c.face in ("left", "right", "back"):         # dark streaks down the neck
        for y in range(c.h):
            c.set(c.w // 2, y, c.pick(STRIPE) if y % 4 != 3 else c.pick(BUFF))


def c_head_side(c):
    down(stripes=False, pal=BUFF_LT)(c)
    c.set(fx(c, 1), 1, SHINE)
    c.set(fx(c, 2), 1, PUPIL)
    c.set(fx(c, 1), 2, IRIS)
    c.set(fx(c, 2), 2, shade(IRIS, 0.7))
    c.set(fx(c, 3), 0, c.pick(STRIPE))
    c.set(fx(c, 3), 1, c.pick(STRIPE))


def c_head_top(c):
    down(stripes=False)(c)
    for y in range(c.h):
        c.set(c.w // 2, y, c.pick(STRIPE))


def c_leg(c):
    c.noise(C_LEG)


CHICK = dict(
    body=faces(down()), hump=faces(down()), breast=faces(down(stripes=False, pal=BUFF_LT)),
    belly=faces(down(stripes=False, pal=BUFF_LT)), rump=faces(down()),
    tail=faces(down()), tail_shell=faces(lambda c: [c.clear(x, y) for y in range(c.h) for x in range(c.w)]),
    wing=faces(down()), plume=faces(lambda c: [c.clear(x, y) for y in range(c.h) for x in range(c.w)]),
    collar=faces(down(stripes=False)), neck=faces(c_neck),
    head=faces(down(stripes=False, pal=BUFF_LT), right=c_head_side, left=c_head_side, top=c_head_top),
    beak=faces(lambda c: c.noise(["#b49a86", "#a8907c"])),
    thigh=faces(c_leg), shank=faces(c_leg), heel=faces(c_leg), big_toe=faces(c_leg), small_toe=faces(c_leg),
    # chicks are never saddled, but the sheet keeps the same layout
    seat=faces(leather), rim=faces(leather), skirt=faces(leather), strap=faces(strap), stirrup=faces(stirrup),
    blanket=faces(blanket),
)

WING_FOLD = (0, math.pi / 2, math.pi / 2)   # right wing; the left mirrors y and z


def make(texture_id, skin_set):
    """Build the ostrich with the given painters. Geometry is identical for adult and chick."""
    m = Model("ostrich", 64, 64, seed=9091, texture_id=texture_id)
    pk = Pack(m)
    s = skin_set

    # body: pivot y 9. A big round body: main box y 5-13, z -6.5..6.5, a flat-topped hump on the
    # back (y 4, the rider's seat), a deep breast in front, a round belly and rump.
    body = m.part("body", (0, 9, 0))
    pk.add(body, (-5, -4, -6.5), (10, 8, 13), s["body"])
    pk.add(body, (-4, -5, -5), (8, 1, 10), s["hump"])
    pk.add(body, (-4, -2, -7.5), (8, 6, 1), s["breast"])
    pk.add(body, (-4, 4, -4), (8, 1, 8), s["belly"])
    pk.add(body, (-4, -3, 6.5), (8, 6, 1), s["rump"])

    # tail: a white plume cocked up at the back, with a fluffy cut-out shell
    tail = body.part("tail", (0, -3, 5.5), (0.2, 0, 0))
    pk.add(tail, (-3, -1.5, 0), (6, 4, 4), s["tail"])
    pk.add(tail, (-3, -1.5, 0), (6, 4, 4), s["tail_shell"], inflate=0.5)

    # wings: authored spread (span along x, chord back along z), folded along the flanks by the rest
    # rotation; a ragged fringe of white plume tips hangs from the trailing edge
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        w = body.part(f"{side}_wing", (5 * sx, -3, -4.5), (WING_FOLD[0], WING_FOLD[1] * -sx, WING_FOLD[2] * -sx))
        pk.add(w, (-8 if not left else 0, 0, 0), (8, 1, 5), None if left else s["wing"], mirror=left, share="wing")
        pk.add(w, (-7 if not left else 0, 0.5, 5), (7, 0, 2), None if left else s["plume"], mirror=left,
               share="plume")

    # neck: from a black feathered collar on the breast, long and bare, leaning forward a little
    neck = body.part("neck", (0, -2, -6), (0.2, 0, 0))
    pk.add(neck, (-1.5, -4, -1.5), (3, 5, 3), s["collar"])
    pk.add(neck, (-1, -11, -1), (2, 7, 2), s["neck"], inflate=0.2)
    head = neck.part("head", (0, -11, 0), (-0.2, 0, 0))
    pk.add(head, (-1.5, -2.5, -2.5), (3, 3, 4), s["head"])
    pk.add(head, (-1.5, -0.5, -5), (3, 1, 3), s["beak"])

    # saddle: on the flat back, skirts down the sides, stirrups hanging on straps outside the wings
    saddle = body.part("saddle", (0, 0, 0))
    pk.add(saddle, (-4.5, -5.5, -3.5), (9, 1, 7), s["blanket"], inflate=-0.05)
    pk.add(saddle, (-3, -6, -3), (6, 1, 6), s["seat"])
    pk.add(saddle, (-1, -7, -3.5), (2, 1, 1), s["rim"])
    pk.add(saddle, (-2, -7, 2.5), (4, 1, 1), s["rim"], share="cantle")
    for sx in (-1, 1):
        left = sx > 0
        pk.add(saddle, (4.5 if left else -5.5, -5, -2.5), (1, 2, 5), None if left else s["skirt"], mirror=left,
               share="skirt")
        pk.add(saddle, (6.5 * sx, -3, 0), (0, 5, 1), s["strap"], share="strap")
        pk.add(saddle, (6 if left else -7, 2, -0.5), (1, 1, 2), None if left else s["stirrup"], mirror=left,
               share="stirrup")

    # legs: children of root. The drumstick hangs from the hip angled back to the heel; the shank
    # drops straight to the two-toed foot.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        o = lambda x0, wd: x0 if not left else -x0 - wd
        lg = m.part(f"{side}_leg", (2.5 * sx, 12, 1), (0.3, 0, 0))
        pk.add(lg, (-1.5, 0, -1.5), (3, 6, 3), None if left else s["thigh"], mirror=left, share="thigh")
        drop = 6 * math.cos(0.3)                  # the heel's height below the hip
        sh = lg.part(f"{side}_shin", (0, 6, 0), (-0.3, 0, 0))
        foot_y = 24 - 12 - drop - 1               # top of the foot, in shin space
        pk.add(sh, (-0.5, -0.5, -0.5), (1, 1, 1), None if left else s["heel"], mirror=left, share="heel",
               inflate=0.4)
        pk.add(sh, (-1, -0.5, -1), (2, round(foot_y + 1), 2), None if left else s["shank"], mirror=left,
               share="shank")
        pk.add(sh, (o(-0.5, 2), foot_y, -3.5), (2, 1, 4), None if left else s["big_toe"], mirror=left,
               share="big_toe")
        pk.add(sh, (o(-1.5, 1), foot_y, -2.5), (1, 1, 3), None if left else s["small_toe"], mirror=left,
               share="small_toe")

    if POSE == "glide":
        m.preview = {"right_wing": [0, 0.15, 0.25], "left_wing": [0, -0.15, -0.25],
                     "right_leg": [0.9, 0, 0], "left_leg": [0.9, 0, 0], "right_shin": [0.6, 0, 0],
                     "left_shin": [0.6, 0, 0], "neck": [0.7, 0, 0], "head": [-0.7, 0, 0]}
    elif POSE == "run":
        m.preview = {"right_leg": [-0.5, 0, 0], "left_leg": [0.9, 0, 0], "left_shin": [0.6, 0, 0]}

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("ostrich_chick", CHICK).save(geometry=False)
    spawn_egg("ostrich", "#211d1e", "#f3f1ec", accent="#cba39b")


if __name__ == "__main__":
    build()

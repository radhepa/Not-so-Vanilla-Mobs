"""Goose: a Canada goose. A plump brown-grey body barred with pale feather edges, a pale buff
breast, a white belly and vent, a black tail with a white band at its base, folded wings with rows
of pale-fringed coverts and near-black primaries crossing toward the tail. A long black neck rises
from the breast with a sharp edge, to a small black head with the white chinstrap running from the
throat up behind the eye, a dark eye with a glint, and a flat black bill. Short black legs and
webbed feet.
The neck pivots at the breast, so the code can drop it forward to hiss; the wings hang along the
flanks from the shoulders (+zRot opens the right wing, -zRot the left). `mouth` is an empty part
under the bill tip, where a carried item is drawn.
`goose_gosling` shares the geometry: fluffy olive-yellow down, a darker olive back and crown, a grey
bill and grey legs (the game draws it at half scale)."""
import math
import os

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Goose"
LOOT = [item("feather", 1, 2)]
TAGS = []

# Debug only: GOOSE_POSE=hiss previews the threat display, =swim the floating pose.
POSE = os.environ.get("GOOSE_POSE", "")


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


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
BACK = ["#6f5f4f", "#76654f", "#695848", "#73614f"]        # brown-grey mantle
BACK_DK = ["#54473a", "#4d4136", "#5a4b3d"]
FRINGE = ["#b0a18a", "#b8a992", "#a89881"]                 # pale feather edges
FLANK = ["#7d6e5d", "#857563", "#766857"]
BREAST = ["#c0b39f", "#c7bba8", "#b8ab96", "#c3b6a2"]
BREAST_SH = ["#a69884", "#9d8f7b"]
WHITE = ["#f2f0ea", "#e9e6de", "#f5f3ee"]
WHITE_SH = ["#d6d2c8", "#cdc9be"]
BLACK = ["#1b1a1d", "#201e22", "#16151a", "#1d1c20"]
SHEEN = ["#2e2d34", "#34333a"]
STRAP = ["#f4f3ef", "#ebe9e3"]
STRAP_SH = "#d3d0c8"
EYE = "#07060a"
SHINE = "#f6f4ee"
BILL = ["#1d1d20", "#232326", "#19191c"]
BILL_HI = "#3b3b40"
NAIL = "#47464b"
PRIMARY = ["#2b241f", "#322a24", "#271f1b"]
PRIMARY_HI = "#4a4038"
LEG = ["#2a272b", "#302d31", "#252226"]
WEB = ["#3d393d", "#433f43"]
CLAW = "#121113"


def feathered(pal, top=1.06, bottom=0.8, grad=0.2):
    """Base plumage: lighter on top, side faces darkening downward."""
    def p(c):
        for y in range(c.h):
            if c.face == "top":
                f = top
            elif c.face == "bottom":
                f = bottom
            else:
                f = 1.04 - grad * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(pal), f))
    return p


def scallops(c, x0, y0, w, h, base, edge, dark):
    """Rows of overlapping feathers on a top face (row 0 = back edge). Every other row is the pale
    fringe at the back edge of a row of feathers, broken by a dark notch between neighbours every
    3 px; the rows are staggered like roof tiles."""
    for y in range(y0, y0 + h):
        k = (y - y0) % 2
        off = ((y - y0) // 2) % 3
        for x in range(x0, x0 + w):
            if k == 1:
                col = c.pick(edge) if (x + off) % 3 != 2 else c.pick(dark)
            else:
                col = c.pick(base) if (x + off) % 3 != 1 else shade(c.pick(base), 0.9)
            c.set(x, y, col)


# -- body ----------------------------------------------------------------------------------------------
def body_top(c):
    """7 x 11 back (row 0 = the back end): barred mantle; the white band of the uppertail coverts
    runs across the back end, just in front of the black tail."""
    scallops(c, 0, 0, c.w, c.h, BACK, FRINGE, BACK_DK)
    for x in range(c.w):
        c.set(x, 0, c.pick(WHITE))
        c.set(x, 1, mix(c.pick(WHITE), c.pick(BACK), 0.35) if x in (0, c.w - 1) else c.pick(WHITE_SH))
    for y in range(c.h - 2, c.h):                  # the front of the back fades into the breast
        for x in range(c.w):
            c.set(x, y, mix(c.get(x, y), c.pick(BREAST_SH), 0.45 if y == c.h - 1 else 0.2))


def body_side(c):
    """11 long x 5 tall. The wing covers the top 3 rows; below it the flank is barred brown-grey with
    pale edges, the breast is pale at the front and the vent white at the back."""
    for y in range(c.h):
        for x in range(c.w):
            i = c.w - 1 - x if c.face == "right" else x       # 0 = front
            t = i / (c.w - 1)
            if i < 2:
                col = mix(c.pick(BREAST), c.pick(BREAST_SH), y / (c.h - 1) * 0.6)
            elif i >= c.w - 2:
                col = shade(c.pick(WHITE), 0.97 - 0.06 * y)
            else:
                col = shade(c.pick(FLANK), 1.05 - 0.12 * y / (c.h - 1))
                if i % 2 == 0:                              # flank bars: the pale fringe of each
                    col = shade(c.pick(FRINGE), 0.97 - 0.1 * y / (c.h - 1))   # feather, in upright rows
                elif y % 2 == 1:
                    col = shade(col, 0.9)
            if i == 2:
                col = mix(col, c.pick(BREAST), 0.5)
            if y == c.h - 1:
                col = mix(col, c.pick(WHITE), 0.1 + 0.5 * t)   # whitening toward the vent
            c.set(x, y, col)
        if c.face in ("left", "right"):
            c.set(fx(c, c.w - 3), y, mix(c.get(fx(c, c.w - 3), y), c.pick(WHITE), 0.5))


def body_front(c):
    """7 x 5 breast behind the neck: pale buff with faint scallops; the black neck sits on top."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(BREAST), 1.02 - 0.1 * y / (c.h - 1))
            if x in (0, c.w - 1):
                col = shade(col, 0.9)
            if (x + y) % 3 == 0 and y > 0:
                col = shade(col, 0.94)
            c.set(x, y, col)


def body_back(c):
    """The rear: the white band at the top, white undertail below (the black tail covers the middle)."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(WHITE), 1.0 - 0.07 * y))
    for x in range(c.w):
        c.set(x, c.h - 1, c.pick(WHITE_SH))


def body_bottom(c):
    """Row 0 = back: a white vent behind the legs, a pale grey-buff belly toward the breast."""
    for y in range(c.h):
        for x in range(c.w):
            t = y / (c.h - 1)
            col = c.pick(WHITE_SH) if t < 0.45 else mix(c.pick(WHITE_SH), c.pick(BREAST_SH), (t - 0.45) * 1.8)
            if x in (0, c.w - 1):
                col = shade(col, 0.9)
            c.set(x, y, col)


def ridge(c):
    """A rounded mantle on top of the back (5 x 8)."""
    if c.face == "top":
        scallops(c, 0, 0, c.w, c.h, BACK, FRINGE, BACK_DK)
        for x in range(c.w):
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(BREAST_SH), 0.3))
    elif c.face in ("left", "right"):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(BACK), 0.98))
        for i in range(c.w):
            if i % 2 == 0:
                c.set(fx(c, i), 0, c.pick(FRINGE))
    elif c.face == "front":
        c.noise([mix(b, BREAST_SH[0], 0.5) for b in BACK])
    else:
        c.noise(BACK)
        for x in range(c.w):
            c.set(x, 0, c.pick(WHITE_SH))


def chest(c):
    """The round breast bulging out in front (6 x 4 x 1)."""
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(BREAST), 1.06 - 0.12 * y / (c.h - 1))
                if x in (0, c.w - 1):
                    col = shade(col, 0.92)
                if (x + 2 * y) % 4 == 1 and y > 0:
                    col = shade(col, 0.93)                  # faint scalloping on the breast
                c.set(x, y, col)
    elif c.face == "top":
        c.noise(BREAST)
    elif c.face == "bottom":
        c.noise(BREAST_SH)
    else:
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(BREAST), 0.96 - 0.08 * y))


def belly(c):
    """The round white belly between the legs (6 x 1 x 8)."""
    if c.face == "bottom":
        for y in range(c.h):
            for x in range(c.w):
                t = y / (c.h - 1)                            # row 0 = back
                col = c.pick(WHITE_SH) if t < 0.5 else mix(c.pick(WHITE_SH), c.pick(BREAST_SH), (t - 0.5) * 1.6)
                c.set(x, y, shade(col, 0.95 if x in (0, c.w - 1) else 1.0))
    elif c.face in ("left", "right"):
        for x in range(c.w):
            i = c.w - 1 - x if c.face == "right" else x
            c.set(x, 0, mix(c.pick(WHITE), c.pick(BREAST), max(0.0, 1 - i / 3)))
    else:
        c.noise(WHITE_SH if c.face == "back" else BREAST_SH)


def vent(c):
    c.noise(WHITE)
    if c.face in SIDES and c.face != "front":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(WHITE_SH))
    if c.face == "bottom":
        c.noise(WHITE_SH)


# -- neck and head -----------------------------------------------------------------------------------
def black(sheen=0.15, under=None):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(BLACK)
                if c.face in ("left", "right", "top") and c.rng.random() < sheen:
                    col = c.pick(SHEEN)
                c.set(x, y, col)
        if under and c.face == "bottom":
            c.noise(under)
    return p


def neck_base(c):
    """3x3 base of the neck: black down to a sharp edge with the breast."""
    black(0.12)(c)


def neck(c):
    black(0.2)(c)
    if c.face in ("left", "right"):              # a faint glossy streak down the side of the neck
        for y in range(0, c.h, 2):
            c.set(fx(c, 0), y, c.pick(SHEEN))


def head_side(c):
    """4 long x 3 tall. The eye sits in the black just in front of the white chinstrap, which runs
    from the throat up the cheek to behind the eye."""
    black(0.1)(c)
    strap = [(2, 1), (3, 1), (1, 2), (2, 2), (3, 2)]
    for (i, y) in strap:
        c.set(fx(c, i), y, c.pick(STRAP) if (i, y) != (1, 2) else STRAP_SH)
    c.set(fx(c, 1), 1, EYE)
    c.set(fx(c, 1), 0, SHINE)                    # the glint, above the dark eye
    c.set(fx(c, 2), 0, c.pick(SHEEN))


def head_front(c):
    black(0.0)(c)
    for x in range(c.w):                         # the chinstrap shows under the chin
        c.set(x, c.h - 1, mix(c.pick(BLACK), STRAP[0], 0.25) if x in (0, c.w - 1) else c.pick(BLACK))


def head_top(c):
    black(0.3)(c)


def head_bottom(c):
    """Row 0 = back: the chinstrap crosses under the throat."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(STRAP) if y in (1, 2) else c.pick(BLACK))
    c.set(0, 1, STRAP_SH); c.set(c.w - 1, 1, STRAP_SH)


def head_back(c):
    black(0.1)(c)


def bill(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(BILL))
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, BILL_HI)                # the ridge catches the light near the face
        c.set(0, 0, NAIL); c.set(c.w - 1, 0, NAIL)   # the nail at the tip (row 0 is the tip end)
        c.set(0, c.h - 2, "#0d0d0f")                  # nostrils
        c.set(c.w - 1, c.h - 2, "#0d0d0f")
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, 0, NAIL)
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, NAIL)


def lower_bill(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BILL), 0.85))
    if c.face in ("left", "right"):
        c.set(fx(c, c.w - 1), 0, "#0f0f11")          # the gape


# -- wings and tail ------------------------------------------------------------------------------------
def wing(c):
    """Right wing (the left mirrors it), 1 px thick, 3 tall, 7 long. The outside (right face) shows
    the coverts in rows along the wing, each row ending in a broken line of pale fringes, and the
    dark tertials at the back; the inside is plain."""
    if c.face == "right":
        for y in range(c.h):
            for x in range(c.w):
                i = c.w - 1 - x                       # 0 = front
                if i >= c.w - 2:
                    col = shade(c.pick(PRIMARY), 1.12 - 0.08 * y)   # tertials, darker
                    if y == 0 or (y == 1 and i == c.w - 2):
                        col = mix(col, c.pick(FRINGE), 0.3)
                elif y == 1:
                    col = c.pick(FRINGE) if (i + 1) % 3 else shade(c.pick(BACK_DK), 0.95)
                elif y == 0:
                    col = shade(c.pick(BACK), 1.1) if i % 3 else c.pick(BACK)
                else:
                    col = shade(c.pick(BACK), 0.95) if i % 3 != 2 else mix(c.pick(FRINGE), c.pick(BACK), 0.4)
                c.set(x, y, col)
        c.set(fx(c, 0), 0, shade(c.pick(BACK), 1.18))               # the shoulder
        c.set(fx(c, 0), 1, shade(c.pick(BACK), 1.05))
    elif c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(BACK), 1.12) if y > 1 else c.pick(PRIMARY))
    elif c.face == "front":
        c.noise([shade(b, 1.1) for b in BACK])
    else:
        c.noise(BACK_DK)


def wing_tip(c):
    """The folded primaries: near-black, with a paler shaft line, narrowing to the tip."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(PRIMARY), 1.04 - 0.08 * y))
    if c.face in ("left", "right"):
        for i in range(c.w - 1):
            c.set(fx(c, i), 0, PRIMARY_HI)
        c.set(fx(c, c.w - 1), c.h - 1, shade(PRIMARY[0], 0.8))
    elif c.face == "top":
        for y in range(c.h):
            c.set(0, y, PRIMARY_HI)


def tail(c):
    """The black tail; a white band of uppertail coverts at its base on top (row 0 = back)."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BLACK)
            if c.face == "top" and c.rng.random() < 0.2:
                col = c.pick(SHEEN)
            c.set(x, y, col)
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(WHITE))
            if x % 2 == 0:
                c.set(x, 0, shade(c.pick(BLACK), 1.4))       # feather tips
    elif c.face == "bottom":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(WHITE_SH))
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, c.pick(WHITE))


# -- legs ----------------------------------------------------------------------------------------------
def leg(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LEG)
            if (x + y) % 2 == 0 and c.face in SIDES:
                col = shade(col, 1.18)                      # scaly skin
            c.set(x, y, col)


def foot(c):
    """3 x 3 webbed foot: three dark toes with grey webbing between, claws at the front."""
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(LEG) if x != 1 or y == 0 else c.pick(WEB))
        for x in (0, 2):
            c.set(x, c.h - 1, CLAW)
        c.set(1, c.h - 1, c.pick(WEB))
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, 0, CLAW if x != 1 else c.pick(WEB))
    else:
        c.noise(LEG)


ADULT = dict(
    body=faces(feathered(BACK), top=body_top, right=body_side, left=body_side, front=body_front,
               back=body_back, bottom=body_bottom),
    ridge=faces(ridge), chest=faces(chest), belly=faces(belly), vent=faces(vent),
    neck_base=faces(neck_base), neck=faces(neck),
    head=faces(head_back, front=head_front, right=head_side, left=head_side, top=head_top,
               bottom=head_bottom),
    bill=faces(bill), lower_bill=faces(lower_bill),
    wing=faces(wing), wing_tip=faces(wing_tip), tail=faces(tail),
    leg=faces(leg), foot=faces(foot),
)

# -- gosling -------------------------------------------------------------------------------------------
DOWN = ["#cdbb5c", "#d6c567", "#c4b254", "#d1bf60"]
DOWN_LT = ["#e2d488", "#e8db93"]
DOWN_DK = ["#a89a48", "#9f9144"]
OLIVE = ["#8f8746", "#99904c", "#867e41"]
OLIVE_DK = ["#6f6935", "#756e38"]
G_BILL = ["#4c4b47", "#55544f"]
G_LEG = ["#5d5a52", "#66625a"]


def fluff(pal, top=1.06, bottom=0.84):
    """Soft down: noisy, side faces darken downward, scattered light wisps over darker dents."""
    def p(c):
        for y in range(c.h):
            f = top if c.face == "top" else bottom if c.face == "bottom" else top - (top - bottom) * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(pal), f))
        for _ in range(c.w * c.h // 6):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, shade(c.pick(DOWN_LT), 1.0 if c.face == "top" else 0.96))
            if c.inside(x, y + 1) and c.face in SIDES:
                c.set(x, y + 1, c.pick(DOWN_DK))
    return p


def g_back_top(c):
    fluff(OLIVE, top=1.05)(c)
    for x in range(c.w):
        for y in range(c.h):
            if x in (0, c.w - 1):
                c.set(x, y, mix(c.get(x, y), c.pick(DOWN), 0.5))


def g_side(c):
    fluff(DOWN)(c)
    for x in range(c.w):                       # the olive back comes a little way down the sides
        c.set(x, 0, mix(c.pick(OLIVE), c.pick(DOWN), 0.3))


def g_head_side(c):
    fluff(DOWN_LT + DOWN[:2], top=1.08, bottom=0.95)(c)
    for i in range(c.w):
        c.set(fx(c, i), 0, mix(c.pick(OLIVE), c.pick(DOWN), 0.4))   # an olive crown
    c.set(fx(c, 1), 1, EYE)
    c.set(fx(c, 1), 0, mix(SHINE, OLIVE[0], 0.2))
    c.set(fx(c, 2), 1, c.pick(OLIVE_DK))                              # a dark eye-stripe behind it
    c.set(fx(c, 3), 1, mix(c.pick(OLIVE_DK), c.pick(DOWN), 0.4))


def g_head_top(c):
    fluff(OLIVE, top=1.05)(c)


def g_head_front(c):
    fluff(DOWN_LT, top=1.08, bottom=0.98)(c)
    for x in range(c.w):
        c.set(x, 0, mix(c.pick(OLIVE), c.pick(DOWN), 0.4))


def g_bill(c):
    c.noise(G_BILL)
    if c.face == "top":
        c.set(0, 0, "#6c6a63"); c.set(c.w - 1, 0, "#6c6a63")


def g_wing(c):
    fluff(OLIVE if c.face in ("right", "top") else DOWN)(c)
    if c.face == "right":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(DOWN))


def g_leg(c):
    c.noise(G_LEG)


def g_foot(c):
    c.noise(G_LEG)
    if c.face == "top":
        for y in range(c.h):
            c.set(1, y, shade(c.pick(G_LEG), 1.15))


GOSLING = dict(
    body=faces(fluff(DOWN), top=g_back_top, right=g_side, left=g_side, front=fluff(DOWN_LT + DOWN[:2]),
               back=fluff(OLIVE)),
    ridge=faces(fluff(OLIVE), top=g_back_top),
    chest=faces(fluff(DOWN_LT + DOWN[:2])),
    belly=faces(fluff(DOWN_LT)),
    vent=faces(fluff(DOWN)),
    neck_base=faces(fluff(DOWN), back=fluff(OLIVE)),
    neck=faces(fluff(DOWN), back=fluff(OLIVE)),
    head=faces(fluff(DOWN), front=g_head_front, right=g_head_side, left=g_head_side, top=g_head_top,
               back=fluff(OLIVE), bottom=fluff(DOWN_LT)),
    bill=faces(g_bill), lower_bill=faces(g_bill),
    wing=faces(g_wing), wing_tip=faces(fluff(OLIVE)), tail=faces(fluff(OLIVE)),
    leg=faces(g_leg), foot=faces(g_foot),
)


def make(texture_id, skin):
    """Build the goose with the given painters. Geometry is identical for adult and gosling."""
    m = Model("goose", 64, 64, seed=2711, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot y 18. Main box y 15-20, z -5..6; a rounded mantle on top (y 14), a round breast
    # bulging forward, a white belly underneath (down to y 21) and a white vent at the back.
    body = m.part("body", (0, 18, 0))
    pk.add(body, (-3.5, -3, -5), (7, 5, 11), skin["body"])
    pk.add(body, (-2.5, -4, -3), (5, 1, 8), skin["ridge"])
    pk.add(body, (-3, -2, -6), (6, 4, 1), skin["chest"])
    pk.add(body, (-3, 2, -4), (6, 1, 8), skin["belly"])
    pk.add(body, (-2.5, -1, 6), (5, 3, 1), skin["vent"])

    # neck: pivots in the breast and rises almost upright, leaning forward a touch; a thicker base
    # sunk into the body, then the slim upper neck
    neck = body.part("neck", (0, -3, -4.5), (0.14, 0, 0))
    pk.add(neck, (-1.5, -3, -1.5), (3, 3, 3), skin["neck_base"])
    pk.add(neck, (-1, -7.5, -1), (2, 5, 2), skin["neck"], inflate=0.2)

    # head: level again on top of the neck; a flat black bill out front
    head = neck.part("head", (0, -7, 0), (-0.14, 0, 0))
    pk.add(head, (-1.5, -2.5, -2.5), (3, 3, 4), skin["head"])
    pk.add(head, (-1, -1.5, -5.5), (2, 1, 3), skin["bill"])
    pk.add(head, (-1, -0.5, -4.5), (2, 1, 2), skin["lower_bill"])
    head.part("mouth", (0, 0.5, -5.0))

    # wings: folded along the flanks from the shoulders, tips angled in toward the tail
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        o = lambda x0, wd: x0 if not left else -x0 - wd
        w = body.part(f"{side}_wing", (3.5 * sx, -3.2, -3.5), (0.1, 0.1 * -sx, 0))
        pk.add(w, (o(-1, 1), 0, 0), (1, 3, 7), None if left else skin["wing"], mirror=left, share="wing")
        pk.add(w, (o(-1, 1), 0, 7), (1, 2, 3), None if left else skin["wing_tip"], mirror=left,
               share="wing_tip")

    # tail: a short black fan cocked up at the back
    tail = body.part("tail", (0, -2, 6), (0.25, 0, 0))
    pk.add(tail, (-2.5, -1, 0), (5, 2, 3), skin["tail"])

    # legs: children of root, out of the belly; webbed feet flat on the ground, toes forward
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        lg = m.part(f"{side}_leg", (1.5 * sx, 20.5, 0.5))
        pk.add(lg, (-0.5, 0, -0.5), (1, 3, 1), None if left else skin["leg"], mirror=left, share="leg",
               inflate=0.15)
        pk.add(lg, (-1.5, 2.5, -2.5), (3, 1, 3), None if left else skin["foot"], mirror=left, share="foot")

    if POSE == "hiss":
        m.preview = {"body": [0.15, 0, 0], "neck": [1.15, 0, 0], "head": [-1.2, 0, 0],
                     "right_wing": [0, 0.35, 0.65], "left_wing": [0, -0.35, -0.65], "tail": [0.5, 0, 0]}
    elif POSE == "swim":
        m.preview = {"right_leg": [1.2, 0, 0], "left_leg": [1.2, 0, 0]}

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("goose_gosling", GOSLING).save(geometry=False)
    spawn_egg("goose", "#6f5f4f", "#1b1a1d", accent="#f2f0ea")


if __name__ == "__main__":
    build()

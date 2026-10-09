"""Penguin: a classic chunky penguin in king penguin colours. A round black-blue back and head, a big
white belly that bulges forward, a golden-orange ear patch on each side of the head that fades into
a pale-yellow upper chest, a black face with small dark shiny eyes and a long slim beak (black, with
an orange stripe along the lower mandible), stubby flippers (black outside, white underneath) and
short orange-grey webbed feet.
Everything that belly-slides is under `body` (pivot at the bottom of the body): the game tips it
forward with xRot = +pi/2 so it lies face-down, head first; the feet stay on the ground (root).
`penguin_chick` shares the geometry: a fluffy grey chick with a white face mask, a black cap, a dark
beak, grey flippers and dark feet (the game draws it at half scale)."""
import math
import os

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Penguin"
LOOT = [item("feather", 0, 1)]
TAGS = ["freeze_immune_entity_types"]

# Debug only: PENGUIN_POSE=slide previews the belly-slide (body tipped forward).
POSE = os.environ.get("PENGUIN_POSE", "")


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

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
        shelves, y_next = [], 0
        for k, (w, h) in order:
            for s in shelves:
                if h <= s[1] and s[2] + w <= self.m.tex_w:
                    keys[k] = (s[2], s[0])
                    s[2] += w
                    break
            else:
                if y_next + h > self.m.tex_h or w > self.m.tex_w:
                    raise ValueError(f"{self.m.id}: texture too small for {k} {w}x{h}")
                shelves.append([y_next, h, w])
                keys[k] = (0, y_next)
                y_next += h
        for i, (part, origin, size, paint, mirror, share, inflate) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


SIDES = ("front", "back", "left", "right")

# -- adult palette -----------------------------------------------------------------------------------
BACK = ["#1d2230", "#232a3a", "#181c27", "#1f2533"]
BACK_HI = ["#2b3346", "#283043"]
BORDER = "#10131b"
WHITE = ["#f2f2ee", "#e6e6e0", "#eeeee9"]
WHITE_SH = ["#d5d5cd", "#cdcdc5"]
ORANGE = ["#f2a63a", "#eea033"]
ORANGE_DK = "#d98a26"
YELLOW = ["#f7cf6a", "#f5c95f"]
YELLOW_PALE = ["#f8e4a6", "#f5df9c"]
EYE = "#07080b"
SHINE = "#ffffff"
EYE_RIM = "#353e52"
BILL = ["#14161c", "#191c23"]
BILL_HI = "#2c313c"
STRIPE = ["#f08a3a", "#ea8236"]
FOOT = ["#c4844c", "#b97a46", "#bf8049"]
FOOT_WEB = ["#9c7d68", "#93766a"]
FOOT_DK = ["#6e4b33", "#654530"]
NAIL = "#2a2523"


def dark(top=1.08, bottom=0.82, sheen=True):
    """Black-blue plumage with tiny noise: lighter on top, darker toward the bottom of side faces."""
    def p(c):
        for y in range(c.h):
            if c.face == "top":
                f = top
            elif c.face == "bottom":
                f = bottom
            else:
                f = top - (top - bottom) * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(BACK), f))
        if sheen and c.face == "top":
            for _ in range(c.w * c.h // 4):
                c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(BACK_HI))
        elif sheen and c.face in SIDES and c.h > 2:      # a faint glossy sheen on the upper half
            for _ in range(c.w * c.h // 8):
                x, y = c.rng.randrange(c.w), c.rng.randrange(max(1, c.h // 2))
                c.set(x, y, shade(c.pick(BACK_HI), 1.0 - 0.1 * y / c.h))
    return p


def white(c, x, y, f=1.0):
    c.set(x, y, shade(c.pick(WHITE), f))


def body_front(c):
    """7 wide: an orange-yellow upper chest just under the chin, fading into the white belly."""
    for y in range(c.h):
        for x in range(c.w):
            t = y / (c.h - 1)
            col = shade(c.pick(WHITE), 1.0 - 0.1 * t)
            if y == c.h - 1:
                col = c.pick(WHITE_SH)
            if x in (0, c.w - 1):
                col = shade(col, 0.92)                   # the belly curves away at the sides
            c.set(x, y, col)
    for x in range(c.w):
        edge = x in (0, c.w - 1)
        c.set(x, 0, c.pick(ORANGE) if edge else mix(c.pick(YELLOW), c.pick(ORANGE), 0.25))
        c.set(x, 1, mix(c.pick(YELLOW), c.pick(YELLOW_PALE), 0.3 if edge else 0.6))
        c.set(x, 2, mix(c.pick(YELLOW_PALE), c.pick(WHITE), 0.35 if 1 < x < c.w - 2 else 0.7))
    c.set(c.w // 2, 3, mix(c.pick(YELLOW_PALE), c.pick(WHITE), 0.75))


def body_side(c):
    """The white belly wraps round the front two columns, a thin black line, then the dark back."""
    dark()(c)
    for y in range(c.h):
        f = 1.0 - 0.12 * y / (c.h - 1)
        white(c, fx(c, 0), y, 0.95 * f)
        if y >= 2:
            white(c, fx(c, 1), y, 0.88 * f)
        c.set(fx(c, 2) if y >= 2 else fx(c, 1), y, BORDER)
    # the orange neck stripe running down from the ear patch to the chest
    c.set(fx(c, 0), 0, c.pick(ORANGE))
    c.set(fx(c, 1), 0, c.pick(ORANGE))
    c.set(fx(c, 0), 1, c.pick(YELLOW))
    c.set(fx(c, 2), 0, ORANGE_DK)
    c.set(fx(c, 2), 1, BORDER)
    c.set(fx(c, 0), 2, mix(c.pick(YELLOW_PALE), c.pick(WHITE), 0.4))
    c.set(fx(c, 0), c.h - 1, c.pick(WHITE_SH))
    c.set(fx(c, 1), c.h - 1, shade(c.pick(WHITE_SH), 0.92))


def body_bottom(c):
    """Row 0 = the back edge: dark at the back, white under the belly."""
    for y in range(c.h):
        for x in range(c.w):
            if y < c.h // 2:
                c.set(x, y, shade(c.pick(BACK), 0.8))
            else:
                c.set(x, y, c.pick(WHITE_SH))


def belly_bulge(c):
    if c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(WHITE), 1.02 - 0.12 * y / (c.h - 1))
                if x in (0, c.w - 1):
                    col = shade(col, 0.95)
                c.set(x, y, col)
        c.set(c.w // 2, c.h - 1, c.pick(WHITE_SH))
    elif c.face == "top":
        for x in range(c.w):
            c.set(x, 0, mix(c.pick(YELLOW_PALE), c.pick(WHITE), 0.6))
    elif c.face == "bottom":
        c.noise(WHITE_SH)
    else:
        for y in range(c.h):
            for x in range(c.w):
                white(c, x, y, 0.9 - 0.1 * y / max(1, c.h - 1))


def hips(c):
    """A band 0.5 px proud of the body's lower sides (y 18-21, z -2..2). Its side faces line up with
    the body's: white front column, the thin black line, then the dark back."""
    if c.face in ("left", "right"):
        dark(top=0.95, bottom=0.82)(c)
        for y in range(c.h):
            white(c, fx(c, 0), y, 0.86 - 0.06 * y)
            c.set(fx(c, 1), y, BORDER)
    elif c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                white(c, x, y, 0.82 - 0.06 * y)
    elif c.face in ("top", "bottom"):                     # row 0 = back edge
        f = 0.95 if c.face == "top" else 0.78
        for y in range(c.h):
            for x in range(c.w):
                if y == c.h - 1:                          # a shadowed ledge, not a white dot
                    c.set(x, y, mix(c.pick(WHITE), BACK[0], 0.45 if c.face == "top" else 0.6))
                elif y == c.h - 2:
                    c.set(x, y, BORDER)
                else:
                    c.set(x, y, shade(c.pick(BACK), f))
    else:
        dark(top=0.95, bottom=0.82)(c)


def head_front(c):
    """6x5 black face; the slim beak comes out of the middle of row 2. A small dark eye on each
    front corner (wrapping round onto the side of the head) with a white shine pixel on top, in a
    slightly lighter blue-black ring."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BACK), 1.06 - 0.06 * y))
    for ex, ix in ((0, 1), (5, 4)):
        c.set(ex, 1, SHINE)
        c.set(ex, 2, EYE)
        c.set(ix, 2, EYE_RIM)
        c.set(ex, 3, EYE_RIM)
        c.set(ex, 0, c.pick(BACK_HI))


def head_side(c):
    """5 deep x 5 tall (the bottom row is sunk into the body). An orange spoon-shaped ear patch
    behind the eye, curling down and forward into the yellow throat."""
    dark(top=1.1, bottom=0.95)(c)
    # a teardrop: wide behind the eye, narrowing as it curls down and forward to the throat
    patch = {(2, 1): "o", (3, 1): "O",
             (2, 2): "o", (3, 2): "o",
             (1, 3): "y", (2, 3): "o",
             (0, 4): "y", (1, 4): "y"}
    for (i, y), k in patch.items():
        col = {"o": c.pick(ORANGE), "O": ORANGE_DK, "y": c.pick(YELLOW)}[k]
        c.set(fx(c, i), y, col)
    c.set(fx(c, 0), 1, EYE)                             # the eye wraps round the corner
    c.set(fx(c, 0), 2, EYE)
    c.set(fx(c, 1), 1, EYE_RIM)
    c.set(fx(c, 1), 2, EYE_RIM)
    c.set(fx(c, 0), 3, EYE_RIM)


def head_top(c):
    dark(top=1.12)(c)


def bill(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(BILL))
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, BILL_HI)                     # the ridge catches the light near the face
        c.set(c.w - 1 if c.w > 1 else 0, 0, BILL_HI)


def lower_bill(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(BILL))
    if c.face in ("left", "right"):
        for i in range(c.w):
            c.set(i, 0, c.pick(STRIPE))                    # the orange plate along the mandible
        c.set(fx(c, 0), 0, BILL[0])
    elif c.face == "bottom":
        for y in range(c.h):
            if y >= 1:
                for x in range(c.w):
                    c.set(x, y, mix(c.pick(STRIPE), BILL[0], 0.5))


def flipper(c):
    """Right flipper (the left one mirrors it): black outside, white inside and underneath."""
    if c.face == "right":                                 # outside
        dark(top=1.05, bottom=0.85)(c)
        for y in range(c.h):
            c.set(fx(c, c.w - 1), y, shade(c.pick(BACK), 0.8))  # trailing edge
        c.set(fx(c, 0), c.h - 1, c.pick(WHITE_SH))           # white rim at the tip
        c.set(fx(c, 1), c.h - 1, shade(c.pick(WHITE_SH), 0.9))
    elif c.face == "left":                                # inside, against the body
        for y in range(c.h):
            for x in range(c.w):
                white(c, x, y, 0.92 - 0.1 * y / (c.h - 1))
        for x in range(c.w):
            c.set(x, 0, c.pick(BACK))
    elif c.face == "front":                               # leading edge: black, a white tip
        dark(top=1.1, bottom=0.9)(c)
        c.set(0, c.h - 1, c.pick(WHITE_SH))
    elif c.face == "bottom":
        c.noise(WHITE_SH)
    else:
        dark()(c)


def tail_paint(c):
    dark(top=1.0, bottom=0.8, sheen=False)(c)


def foot_paint(c):
    """3 wide, 4 long: three orange toes with grey webbing between and dark nails at the front."""
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FOOT) if x != 1 else c.pick(FOOT_WEB)
                if y == 0:
                    col = c.pick(FOOT_DK)                 # the heel, row 0 = back
                c.set(x, y, col)
        for x in (0, 2):
            c.set(x, c.h - 1, NAIL)
        c.set(1, c.h - 1, c.pick(FOOT_WEB))
    elif c.face == "front":
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(FOOT), 0.92) if x != 1 else c.pick(FOOT_WEB))
    elif c.face == "bottom":
        c.noise(FOOT_DK)
    else:
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(c.pick(FOOT), 0.85))
        if c.face in ("left", "right"):
            c.set(fx(c, 0), 0, NAIL)


def ankle(c):
    c.noise([shade(f, 0.86) for f in FOOT] + FOOT_WEB[:1])


ADULT = dict(
    body=faces(dark(), front=body_front, right=body_side, left=body_side, bottom=body_bottom),
    bulge=faces(belly_bulge),
    rump=faces(dark(top=1.04, bottom=0.8)),
    hips=faces(hips),
    head=faces(dark(), front=head_front, right=head_side, left=head_side, top=head_top),
    bill=faces(bill),
    lower_bill=faces(lower_bill),
    flipper=faces(flipper),
    tail=faces(tail_paint),
    foot=faces(foot_paint),
    ankle=faces(ankle),
)

# -- chick palette -----------------------------------------------------------------------------------
DOWN = ["#8c8c8c", "#9a9a98", "#7d7d7d", "#929290"]
DOWN_LT = ["#a4a4a1", "#a9a9a6"]
DOWN_DK = ["#777776", "#7b7b7a"]
MASK = ["#f2f2ee", "#e9e9e4", "#f5f5f1"]
MASK_SH = "#d2d2cc"
CAP = ["#1b1c20", "#222328", "#18191d"]
CHICK_BILL = ["#2a2a2e", "#323236"]
CHICK_FOOT = ["#3a3533", "#433d3a"]


def fluff(base=None, top=1.06, bottom=0.82):
    """Soft grey down: noisy, side faces darken downward, scattered light tufts over dark dents."""
    pal = base or DOWN

    def p(c):
        for y in range(c.h):
            if c.face == "top":
                f = top
            elif c.face == "bottom":
                f = bottom
            else:
                f = top - (top - bottom) * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(pal), f))
        for _ in range(c.w * c.h // 7):         # soft tufts: a lighter wisp over a slightly darker dent
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, shade(c.pick(DOWN_LT), 1.0 if c.face == "top" else 0.98))
            if c.inside(x, y + 1) and c.face in SIDES:
                c.set(x, y + 1, c.pick(DOWN_DK))
    return p


def chick_belly(c):
    fluff(base=DOWN_LT + DOWN[:2])(c)


def chick_head_front(c):
    """A black cap over a white face mask; the dark eyes sit on the front corners (wrapping round
    onto the cheeks), level with the beak."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(MASK), 1.0 - 0.04 * y))
    for x in range(c.w):
        c.set(x, 0, c.pick(CAP))
    for ex in (0, c.w - 1):
        c.set(ex, 2, EYE)
    c.set(1, 1, MASK_SH); c.set(c.w - 2, 1, MASK_SH)        # soft brows under the cap
    c.set(2, 3, MASK_SH); c.set(3, 3, MASK_SH)            # shadow under the beak


def chick_head_side(c):
    """The mask wraps round the cheeks at the front; the cap covers the top and back."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(CAP))
    for y in range(1, c.h):
        for i in range(3 if y < 3 else 2):
            c.set(fx(c, i), y, shade(c.pick(MASK), 0.96 - 0.04 * y))
    c.set(fx(c, 0), 2, EYE)
    for y in range(3, c.h):
        c.set(fx(c, c.w - 1), y, c.pick(DOWN))
        c.set(fx(c, c.w - 2), y, c.pick(DOWN_DK))
        c.set(fx(c, c.w - 3), y, c.pick(DOWN))


def chick_head_back(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(CAP) if y < c.h - 2 else c.pick(DOWN))


def chick_head_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(CAP), 1.1))
    for _ in range(4):
        c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), "#2e3036")


def chick_bill(c):
    c.noise(CHICK_BILL)
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, "#3c3c41")


def chick_flipper(c):
    fluff()(c)
    if c.face == "left":
        fluff(base=DOWN_LT)(c)


def chick_foot(c):
    c.noise(CHICK_FOOT)
    if c.face == "top":
        for x in (0, 2):
            c.set(x, c.h - 1, "#1f1b1a")
        for y in range(c.h):
            c.set(1, y, shade(c.pick(CHICK_FOOT), 1.15))


CHICK = dict(
    body=faces(fluff(), front=chick_belly),
    bulge=faces(chick_belly),
    rump=faces(fluff()),
    hips=faces(fluff(top=0.95, bottom=0.8)),
    head=faces(fluff(), front=chick_head_front, right=chick_head_side, left=chick_head_side,
               top=chick_head_top, back=chick_head_back, bottom=fluff()),
    bill=faces(chick_bill),
    lower_bill=faces(chick_bill),
    flipper=faces(chick_flipper),
    tail=faces(fluff()),
    foot=faces(chick_foot),
    ankle=faces(chick_foot),
)


def make(texture_id, skin):
    """Build the penguin with the given painters. Geometry is identical for adult and chick."""
    m = Model("penguin", 64, 64, seed=2233, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot at the bottom (y 22); the cube rises to y 13. A white belly bulges out front (z -4)
    # and a little rounded rump behind, so the side silhouette is a plump egg.
    body = m.part("body", (0, 22, 0))
    pk.add(body, (-3.5, -9, -3), (7, 9, 6), skin["body"])
    pk.add(body, (-2.5, -7, -4), (5, 6, 1), skin["bulge"])
    pk.add(body, (-2.5, -5, 3), (5, 4, 1), skin["rump"])
    pk.add(body, (-4, -4, -2), (8, 3, 4), skin["hips"])         # plump lower sides (y 18-21)

    # head: sits on the body with its bottom row sunk in (no neck); faces -z
    head = body.part("head", (0, -9, 0))
    pk.add(head, (-3, -4, -2.5), (6, 5, 5), skin["head"])
    # beak: long and slim, hinged at the mouth line and tipped down a touch (slightly decurved)
    beak = head.part("beak", (0, -1, -2.5), (0.15, 0, 0))
    pk.add(beak, (-0.5, -1, -4), (1, 1, 4), skin["bill"])
    pk.add(beak, (-0.5, 0, -3), (1, 1, 3), skin["lower_bill"])

    # flippers: hinged at the shoulders, hanging down the sides and angled out a little
    # (+zRot swings the right flipper out, -zRot the left one)
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        f = body.part(f"{side}_flipper", (3.5 * sx, -8.5, -0.5), (0, 0, 0.22 * -sx))
        pk.add(f, (-1 if not left else 0, 0, -1.5), (1, 7, 3), None if left else skin["flipper"],
               mirror=left, share="flipper")

    # tail: a tiny stiff black tail at the back bottom, propped down toward the ground
    tail = body.part("tail", (0, -1, 3), (-0.6, 0, 0))
    pk.add(tail, (-1.5, -0.5, 0), (3, 1, 2), skin["tail"])

    # feet: children of root, flat on the ground, toes pointing -z
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        ft = m.part(f"{side}_foot", (2 * sx, 22, 0))
        pk.add(ft, (-1, 0, -0.5), (2, 1, 2), None if left else skin["ankle"], mirror=left, share="ankle")
        pk.add(ft, (-1.5, 1, -3), (3, 1, 4), None if left else skin["foot"], mirror=left, share="foot")

    if POSE == "slide":
        m.preview = {"body": [math.pi / 2, 0, 0]}

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("penguin_chick", CHICK).save(geometry=False)
    spawn_egg("penguin", "#1d2230", "#f2f2ee", accent="#f2a63a")


if __name__ == "__main__":
    build()

"""Flamingo: an American flamingo. A soft salmon-pink egg-shaped body, deeper coral-red coverts on
the folded wings with jet-black flight feathers along their lower and rear edges, a short drooping
tail, a long slim S-curved neck, a small head with a pale yellow eye, and the famous bent bill:
pale pink at the base, then kinked sharply down and black at the tip. Long thin pink legs with a
knobbly backward "knee" (the heel) half way down, and pink webbed feet.
The wings are authored spread (span along x, chord along z) and folded against the flanks by their
rest rotation, so the code can open them fully to flutter. The neck is two segments (`neck`, then
`neck_upper`) for the S-curve. Legs are children of root, each with a `*_shin` below the heel, so the
code can fold one up to rest.
`flamingo_chick` shares the geometry: fluffy grey down, a paler face and belly, a dark grey bill
and dark grey legs (the game draws it at half scale)."""
import math
import os

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Flamingo"
LOOT = [item("feather", 0, 1)]
TAGS = ["fall_damage_immune"]

# Debug only: FLAMINGO_POSE=rest previews one leg tucked up, =flap the wings open.
POSE = os.environ.get("FLAMINGO_POSE", "")


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
PINK = ["#f29aae", "#f4a3b5", "#ef91a7", "#f19bb0"]
PINK_LT = ["#f8bfcb", "#f9c7d2", "#f6b6c4"]
PINK_DK = ["#df7b93", "#d97389", "#e3839a"]
CORAL = ["#ea5f78", "#ee6c83", "#e5566f"]          # wing coverts
CORAL_DK = ["#cf4560", "#c93f59"]
BLACK = ["#1d1a1d", "#232023", "#181518"]
BLACK_HI = "#3a3539"
LEG = ["#ea8ea3", "#e7879d", "#ee98ab"]
LEG_DK = ["#cf6c86", "#c9657f"]
JOINT = "#c25775"
BILL = ["#f2dcd4", "#ecd2c9", "#f5e2db"]
BILL_SH = "#d9b9b0"
BILL_TIP = ["#1b1719", "#221d20"]
IRIS = "#f1df72"
EYE = "#100c0e"
SHINE = "#fffdf6"
EYE_RING = "#d7798f"


def plumage(pal, top=1.06, bottom=0.82, grad=0.18, wisps=True):
    """Soft feathers: lighter on top, side faces darkening downward, faint lighter wisps."""
    def p(c):
        for y in range(c.h):
            f = top if c.face == "top" else bottom if c.face == "bottom" else 1.04 - grad * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(pal), f))
        if wisps:
            for _ in range(c.w * c.h // 7):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, shade(c.pick(PINK_LT), 1.0 if c.face == "top" else 0.97 - 0.1 * y / max(1, c.h)))
    return p


def body_side(c):
    """9 long x 5 tall; the wing covers most of it. Soft pink, the breast slightly paler, a few
    darker feather lines low on the flank."""
    plumage(PINK)(c)
    for y in range(c.h):
        c.set(fx(c, 0), y, shade(c.pick(PINK_LT), 0.98 - 0.05 * y))
    for x in range(c.w):
        if c.rng.random() < 0.4:
            c.set(x, c.h - 1, c.pick(PINK_DK))


def body_front(c):
    """The breast under the neck: pale pink, softly shaded."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(PINK_LT), 1.0 - 0.12 * y / max(1, c.h - 1))
            if x in (0, c.w - 1):
                col = shade(col, 0.93)
            c.set(x, y, col)


def body_bottom(c):
    c.noise([shade(p, 0.86) for p in PINK])


def back_top(c):
    """The back: pink with a few coral coverts showing between the wings (row 0 = back)."""
    plumage(PINK, top=1.08)(c)
    for y in range(c.h):
        for x in (0, c.w - 1):
            if c.rng.random() < 0.6:
                c.set(x, y, c.pick(CORAL))


def tail_paint(c):
    plumage(PINK, top=1.0, grad=0.25)(c)
    if c.face == "top":                            # pale feather tips at the back end (row 0)
        for x in range(c.w):
            c.set(x, 0, c.pick(PINK_LT))
    elif c.face in ("left", "right", "back"):
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(PINK_DK))


# -- wings (authored spread: on top/bottom faces column 0 is the wing tip, row 0 the trailing edge) --
def wing_surface(c):
    """Both broad faces, painted alike: coral coverts toward the leading edge, the black flight
    feathers along the trailing edge and over the outer third (the primaries)."""
    for y in range(c.h):                           # y: 0 = trailing edge .. h-1 = leading edge
        for x in range(c.w):                       # x: 0 = tip .. w-1 = shoulder
            lead = y / (c.h - 1)
            if x <= 1 or (y == 0 and x <= 6) or (y == 1 and x <= 2):
                col = c.pick(BLACK)
                if x <= 1 and y >= 2 and (x + y) % 2 == 0:
                    col = BLACK_HI                 # the shafts of the primaries
            elif y <= 1:
                col = c.pick(CORAL_DK) if (x + y) % 2 else shade(c.pick(CORAL_DK), 0.9)   # long tertials
            elif y == 2:
                col = c.pick(CORAL_DK) if x % 2 else c.pick(CORAL)   # greater coverts
            else:
                col = mix(c.pick(CORAL), c.pick(PINK), 0.15 + 0.5 * (lead - 0.6) * 2.5)
                if (x + y) % 3 == 0:
                    col = shade(col, 1.08)
            if y == c.h - 1 and x > 1:
                col = mix(col, c.pick(PINK_LT), 0.45)  # the pink leading edge (the shoulder)
            c.set(x, y, col)
    c.set(0, 0, shade(BLACK[0], 1.6))              # a ragged tip


def wing_edge(c):
    """The thin edges: black at the tip and trailing edge, pink along the leading edge."""
    if c.face == "front":                          # leading edge
        for x in range(c.w):
            c.set(x, 0, c.pick(PINK) if x > 1 else c.pick(BLACK))
    elif c.face == "left":                         # the root, against the body
        c.noise(PINK)
    else:                                          # tip and trailing edge
        c.noise(BLACK)


# -- neck and head -------------------------------------------------------------------------------------
def neck_paint(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(PINK)
            if c.face in SIDES:
                col = shade(col, 1.02 - 0.06 * (x % 2))
                if c.face == "front":
                    col = shade(c.pick(PINK_LT), 0.98)
                elif c.face == "back":
                    col = c.pick(PINK_DK)
            c.set(x, y, col)
    for _ in range(c.w * c.h // 5):
        c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(PINK_LT) if c.face != "back" else c.pick(PINK))


def head_side(c):
    """3 x 3: the pale yellow eye with a black pupil and a glint, set just behind the bill."""
    plumage(PINK, wisps=False)(c)
    c.set(fx(c, 0), 1, EYE_RING)
    c.set(fx(c, 1), 1, EYE)
    c.set(fx(c, 1), 0, mix(IRIS, SHINE, 0.6))      # glint on the top of the eye
    c.set(fx(c, 2), 1, IRIS)
    c.set(fx(c, 0), 2, c.pick(BILL))               # the pale bare skin at the gape


def head_front(c):
    plumage(PINK_LT, wisps=False)(c)


def bill_base(c):
    """Pale pink and thick, a dark slit nostril on each side."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BILL)
            if c.face in SIDES:
                col = shade(col, 1.0 - 0.08 * y)
            elif c.face == "bottom":
                col = BILL_SH
            c.set(x, y, col)
    if c.face in ("left", "right"):
        c.set(fx(c, 1), 0, "#6e5550")
        c.set(fx(c, 0), 1, mix(c.pick(BILL), BILL_TIP[0], 0.25))


def bill_tip(c):
    """The bent-down half of the bill. The cube points forward in its own space and the rest
    rotation kinks it down, so its back end is the bend (a pale band) and its front end the tip."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(BILL_TIP))
    if c.face in ("left", "right"):
        for y in range(c.h):
            c.set(fx(c, c.w - 1), y, mix(c.pick(BILL), BILL_TIP[0], 0.3))
        c.set(fx(c, 0), 0, BLACK_HI)
    elif c.face == "top":                          # row 0 = back = the bend
        for x in range(c.w):
            c.set(x, 0, mix(c.pick(BILL), BILL_TIP[0], 0.3))
            c.set(x, c.h - 1, BLACK_HI)
    elif c.face == "back":
        c.noise(BILL)


# -- legs ----------------------------------------------------------------------------------------------
def thigh(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LEG)
            if c.face in ("right", "back"):
                col = shade(col, 0.9)
            c.set(x, y, col)
    if c.face in SIDES:                            # the feathered top disappears into the belly
        c.set(0, 0, c.pick(PINK))


def shin(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(LEG)
            if c.face in ("right", "back"):
                col = shade(col, 0.9)
            if y % 2 == 0 and c.face in SIDES:
                col = shade(col, 0.95)             # faint scales
            c.set(x, y, col)


def knee(c):
    c.noise([JOINT, shade(JOINT, 1.1)])


def foot(c):
    """3 x 3 webbed foot: three pink toes with paler webbing, dark tips."""
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(LEG) if x != 1 or y == 0 else shade(c.pick(LEG), 1.08))
        for x in (0, 2):
            c.set(x, c.h - 1, c.pick(LEG_DK))
    else:
        c.noise(LEG_DK)


ADULT = dict(
    body=faces(plumage(PINK), right=body_side, left=body_side, front=body_front, bottom=body_bottom,
               top=back_top),
    back=faces(plumage(PINK), top=back_top),
    belly=faces(body_bottom, right=plumage(PINK), left=plumage(PINK), front=body_front),
    breast=faces(body_front, top=plumage(PINK_LT), bottom=body_bottom),
    tail=faces(tail_paint),
    wing=faces(wing_edge, top=wing_surface, bottom=wing_surface),
    neck=faces(neck_paint), neck_upper=faces(neck_paint),
    head=faces(plumage(PINK, wisps=False), front=head_front, right=head_side, left=head_side),
    bill=faces(bill_base), bill_tip=faces(bill_tip),
    thigh=faces(thigh), shin=faces(shin), knee=faces(knee), foot=faces(foot),
)

# -- chick ---------------------------------------------------------------------------------------------
DOWN = ["#9c9c9a", "#a6a6a3", "#929290", "#a1a19e"]
DOWN_LT = ["#bdbdb9", "#c6c6c2", "#b4b4b0"]
DOWN_DK = ["#7e7e7c", "#858583"]
C_BILL = ["#3d3b3c", "#444243"]
C_LEG = ["#56534f", "#5e5b57", "#4f4c49"]


def fluff(pal, top=1.06, bottom=0.82):
    def p(c):
        for y in range(c.h):
            f = top if c.face == "top" else bottom if c.face == "bottom" else top - (top - bottom) * y / max(1, c.h - 1)
            for x in range(c.w):
                c.set(x, y, shade(c.pick(pal), f))
        for _ in range(c.w * c.h // 7):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            c.set(x, y, shade(c.pick(DOWN_LT), 1.0 if c.face == "top" else 0.96))
            if c.inside(x, y + 1) and c.face in SIDES:
                c.set(x, y + 1, c.pick(DOWN_DK))
    return p


def c_head_side(c):
    fluff(DOWN_LT)(c)
    c.set(fx(c, 1), 1, EYE)
    c.set(fx(c, 1), 0, mix(SHINE, DOWN_LT[0], 0.3))


def c_wing(c):
    """Stubby downy wings: grey all over, a little darker toward the tip."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(DOWN), 0.9 + 0.1 * x / max(1, c.w - 1)))


def c_leg(c):
    c.noise(C_LEG)


CHICK = dict(
    body=faces(fluff(DOWN), front=fluff(DOWN_LT), bottom=fluff(DOWN_LT)),
    back=faces(fluff(DOWN)),
    belly=faces(fluff(DOWN_LT)),
    breast=faces(fluff(DOWN_LT)),
    tail=faces(fluff(DOWN)),
    wing=faces(c_wing),
    neck=faces(fluff(DOWN), front=fluff(DOWN_LT)), neck_upper=faces(fluff(DOWN), front=fluff(DOWN_LT)),
    head=faces(fluff(DOWN_LT), right=c_head_side, left=c_head_side),
    bill=faces(lambda c: c.noise(C_BILL)), bill_tip=faces(lambda c: c.noise(C_BILL)),
    thigh=faces(c_leg), shin=faces(c_leg), knee=faces(c_leg), foot=faces(c_leg),
)

WING_FOLD = (0, math.pi / 2, math.pi / 2)   # right wing; the left mirrors y and z


def make(texture_id, skin):
    """Build the flamingo with the given painters. Geometry is identical for adult and chick."""
    m = Model("flamingo", 64, 64, seed=4421, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot y 10. An egg: main box y 7-12, z -4..5, a rounded back (y 6) and belly (y 13),
    # a paler breast bulging forward under the neck.
    body = m.part("body", (0, 10, 0))
    pk.add(body, (-3, -3, -4), (6, 5, 9), skin["body"])
    pk.add(body, (-2.5, -4, -2.5), (5, 1, 6), skin["back"])
    pk.add(body, (-2.5, 2, -3), (5, 1, 7), skin["belly"])
    pk.add(body, (-2.5, -2, -5), (5, 4, 1), skin["breast"])

    # tail: short and drooping, under the crossed wing tips
    tail = body.part("tail", (0, -1.5, 5), (-0.35, 0, 0))
    pk.add(tail, (-2, -1, -0.5), (4, 2, 3), skin["tail"])

    # wings: authored spread out sideways (span along x, chord back along z, 1 px thick), folded flat
    # against the flanks by the rest rotation so the span runs back and the chord hangs down
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        w = body.part(f"{side}_wing", (3 * sx, -2.5, -3), (WING_FOLD[0], WING_FOLD[1] * -sx, WING_FOLD[2] * -sx))
        pk.add(w, (-9 if not left else 0, 0, 0), (9, 1, 5), None if left else skin["wing"], mirror=left,
               share="wing")

    # neck: an S in two segments, leaning forward from the breast, then back; the head level on top
    neck = body.part("neck", (0, -2, -4), (0.5, 0, 0))
    pk.add(neck, (-1, -4, -1), (2, 5, 2), skin["neck"])
    upper = neck.part("neck_upper", (0, -3.5, 0), (-1.0, 0, 0))
    pk.add(upper, (-1, -4, -1), (2, 4, 2), skin["neck_upper"])
    head = upper.part("head", (0, -4, 0), (0.5, 0, 0))
    pk.add(head, (-1.5, -2.5, -2), (3, 3, 3), skin["head"])
    # the bill: a thick pale base, then kinked sharply down to a black tip
    pk.add(head, (-1, -1.5, -4), (2, 2, 2), skin["bill"])
    tip = head.part("bill_tip", (0, -1.5, -4), (1.05, 0, 0))
    pk.add(tip, (-1, 0, -3), (2, 2, 3), skin["bill_tip"], inflate=-0.1)

    # legs: children of root. The upper leg hangs from the hip in the belly to the heel (the
    # backward "knee"), the shin carries on down to the webbed foot.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        lg = m.part(f"{side}_leg", (1.5 * sx, 12.5, 0.5))
        pk.add(lg, (-0.5, 0, -0.5), (1, 6, 1), None if left else skin["thigh"], mirror=left, share="thigh")
        sh = lg.part(f"{side}_shin", (0, 6, 0))
        pk.add(sh, (-0.5, -0.5, -0.5), (1, 1, 1), None if left else skin["knee"], mirror=left, share="knee",
               inflate=0.2)
        pk.add(sh, (-0.5, 0, -0.5), (1, 5, 1), None if left else skin["shin"], mirror=left, share="shin")
        pk.add(sh, (-1.5, 4.5, -2.5), (3, 1, 3), None if left else skin["foot"], mirror=left, share="foot")

    if POSE == "rest":
        m.preview = {"right_leg": [-0.9, 0, 0], "right_shin": [2.6, 0, 0]}
    elif POSE == "flap":
        m.preview = {"right_wing": [0, 0.1, 0.5], "left_wing": [0, -0.1, -0.5],
                     "right_leg": [0.9, 0, 0], "left_leg": [0.9, 0, 0]}

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("flamingo_chick", CHICK).save(geometry=False)
    spawn_egg("flamingo", "#f29aae", "#1d1a1d", accent="#ea5f78")


if __name__ == "__main__":
    build()

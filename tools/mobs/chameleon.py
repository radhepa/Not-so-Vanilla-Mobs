"""Chameleon: a veiled chameleon. A tall, flat-sided body with a serrated crest down the back, a
helmet-like casque rising from the back of the head, cone-shaped turret eyes with a pinprick pupil
at the tip, a little gular crest under the chin, thin splayed legs ending in split "mitten" feet,
and a tail that curls into a tight spiral.

The whole model is multiplied by the chameleon's camouflage colour (CritterRenderState.tint), so
the skin is painted pale and nearly neutral: the stripes, dots, pale side stripe and shading are
all in VALUE, not hue, and read in whatever colour it takes on. Only the pupils are truly dark."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Chameleon"
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


# -- palette: pale, nearly neutral greys with the faintest green, so the tint carries the colour -------
SKIN = ["#e2e7db", "#dce2d5", "#e6eae0", "#d8ded1"]
SKIN_LT = "#fbfcf7"                     # the pale side stripe, dots and highlights
SKIN_SH = "#aeb6a6"                     # stripes and shading
SKIN_DK = "#8b9385"                     # the deepest shadows
BELLY = ["#eef1e9", "#eaeee4"]
PUPIL = "#121412"
GLINT = "#fbfcf8"
MOUTH = "#6c7466"

SIDES = ("front", "back", "left", "right")


def granular(c, x, y, k=1.0):
    """Chameleon skin: fine tubercles, a lighter or darker grain here and there."""
    col = shade(c.pick(SKIN), k)
    r = c.rng.random()
    if r < 0.12:
        col = mix(col, SKIN_LT, 0.6)
    elif r > 0.9:
        col = mix(col, SKIN_SH, 0.5)
    return col


def flank(c):
    """Body sides (6 deep x 4 tall): darker vertical bands, a pale lateral stripe through the middle,
    a scatter of light dots, shading toward the belly."""
    for y in range(c.h):
        for x in range(c.w):
            i = c.w - 1 - x if c.face == "right" else x             # from the front
            col = granular(c, x, y, 1.03 - 0.1 * y / (c.h - 1))
            if i % 3 == 1 and y < c.h - 1:
                col = mix(col, SKIN_SH, 0.9)                         # the bands
            if i % 3 == 1 and y == 0:
                col = mix(col, SKIN_DK, 0.5)
            if y == 2:
                col = mix(col, SKIN_LT, 0.7)                         # pale lateral stripe
            if y == c.h - 1:
                col = mix(col, c.pick(BELLY), 0.5)
            c.set(x, y, col)
    for (i, y) in ((0, 0), (3, 1), (5, 0), (2, 3)):
        c.set(fx(c, i), y, SKIN_LT)                                  # little bright dots


def flank_low(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(granular(c, x, y, 0.95), c.pick(BELLY), 0.4))


def back_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, granular(c, x, y, 1.05))
    for y in range(0, c.h, 3):
        c.set(c.w // 2, y, mix(c.get(c.w // 2, y), SKIN_SH, 0.6))


def belly(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(BELLY) if 0 < x < c.w - 1 else mix(c.pick(BELLY), SKIN_SH, 0.3))


def body_end(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, granular(c, x, y, 0.95 - 0.08 * y / max(1, c.h - 1)))


def crest(c):
    # 1 wide x 1 tall x 5 deep: three little cones along the spine with the gaps between them cut
    # away (the crest is 5 long, so teeth at 0, 2 and 4 line up from either end on every face)
    if c.face in ("front", "back"):
        c.fill(mix(SKIN[0], SKIN_LT, 0.3))
        return
    for y in range(c.h):
        for x in range(c.w):
            i = x if c.face in ("left", "right") else y
            if i % 2 == 1:
                c.clear(x, y)
            else:
                c.set(x, y, SKIN_LT if c.face == "top" else mix(c.pick(SKIN), SKIN_LT, 0.4))


# -- head --------------------------------------------------------------------------------------------
def skull_side(c):
    # 3 deep x 3 tall: the mouth runs along the bottom row and turns up at the back in a smirk
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, granular(c, x, y, 1.02 - 0.06 * y))
    for i in range(c.w):
        c.set(fx(c, i), c.h - 1, mix(c.get(fx(c, i), c.h - 1), MOUTH, 0.55))
    c.set(fx(c, c.w - 1), c.h - 2, mix(SKIN[0], MOUTH, 0.5))
    c.set(fx(c, 0), 0, SKIN_LT)


def skull_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, granular(c, x, y, 1.05))


def skull_front(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, granular(c, x, y, 0.98))


def snout(c):
    if c.face == "front":
        # 2 x 2: blunt nose with two tiny nostrils, the lip line below
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, granular(c, x, y, 1.0))
        c.set(0, 0, SKIN_SH)
        c.set(1, 0, SKIN_SH)
        c.set(0, 1, mix(SKIN[0], MOUTH, 0.5))
        c.set(1, 1, mix(SKIN[0], MOUTH, 0.5))
    elif c.face in ("left", "right"):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, granular(c, x, y))
        c.set(0, c.h - 1, mix(SKIN[0], MOUTH, 0.55))
    else:
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, granular(c, x, y, 1.04 if c.face == "top" else 0.9))


def gular(c):
    # the throat pouch: pale with faint vertical grooves
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BELLY)
            if c.face in ("left", "right") and x % 2 == 0:
                col = mix(col, SKIN_SH, 0.4)
            c.set(x, y, col)


def casque(k=1.0):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = granular(c, x, y, k)
                if c.face == "top":
                    col = mix(col, SKIN_LT, 0.35)
                elif c.face in ("left", "right") and y == 0:
                    col = mix(col, SKIN_LT, 0.5)                    # a pale rim along the helmet edge
                elif c.face == "bottom":
                    col = shade(col, 0.88)
                c.set(x, y, col)
    return p


def turret(c):
    # the eye's scaly cone: concentric rings of value, darker toward the rim
    for y in range(c.h):
        for x in range(c.w):
            edge = x in (0, c.w - 1) or y in (0, c.h - 1)
            col = c.pick(SKIN)
            if c.face == "right":                                   # the outer face (left mirrors it)
                col = mix(col, SKIN_SH, 0.45) if edge else mix(col, SKIN_LT, 0.35)
            else:
                col = mix(col, SKIN_SH, 0.3)
            c.set(x, y, col)


def pupil(c):
    # the pinprick pupil at the tip of the cone; its rim is still eyelid
    c.fill(PUPIL if c.face == "right" else mix(SKIN[0], SKIN_SH, 0.6))


# -- legs and tail -----------------------------------------------------------------------------------
def leg(c):
    for y in range(c.h):
        for x in range(c.w):
            col = granular(c, x, y, 1.0 - 0.1 * y / max(1, c.h - 1))
            if c.face in ("left", "right") and y % 2 == 1:
                col = mix(col, SKIN_SH, 0.3)
            c.set(x, y, col)


def mitten(c):
    # 1 wide x 1 tall x 3 deep: two bundles of fused toes, front and back, gripping round a dark
    # split in the middle
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(SKIN), SKIN_SH, 0.25)
            if c.face in ("left", "right") and x == c.w // 2:
                col = SKIN_DK
            if c.face in ("top", "bottom") and y == c.h // 2:
                col = SKIN_DK
            c.set(x, y, col)


def tail_skin(c):
    for y in range(c.h):
        for x in range(c.w):
            col = granular(c, x, y, 1.02 - 0.08 * y / max(1, c.h - 1))
            along = (c.w - 1 - x if c.face == "right" else x) if c.face in ("left", "right") else (c.h - 1 - y)
            if c.face in ("left", "right", "top") and along % 3 == 2:
                col = mix(col, SKIN_SH, 0.55)                       # faint rings
            if c.face == "bottom":
                col = mix(col, c.pick(BELLY), 0.4)
            c.set(x, y, col)


def build():
    m = Model("chameleon", 64, 64, seed=2323)
    pk = Pack(m)

    # body: pivot in the middle of the torso (y 19). Flat-sided: 3 wide, 4 tall, 6 long, belly at
    # y 21 on legs 3 px long, a serrated crest along the spine.
    body = m.part("body", (0, 19, 0))
    pk.add(body, (-1.5, -2, -3), (3, 4, 6), faces(body_end, top=back_top, bottom=belly,
                                                  right=flank, left=flank))
    pk.add(body, (-0.5, -3, -2.5), (1, 1, 5), faces(crest))
    pk.add(body, (-1, 1.5, -2), (2, 1, 4), faces(belly, sides=flank_low), inflate=0.1)   # the belly's curve

    # head: a box a little lower than the shoulders, blunt snout, throat pouch, the casque rising
    # behind like a helmet
    head = body.part("head", (0, -0.5, -3))
    pk.add(head, (-1.5, -1.5, -3), (3, 3, 3), faces(skull_front, top=skull_top, right=skull_side,
                                                    left=skull_side))
    pk.add(head, (-1, -0.5, -4), (2, 2, 1), faces(snout))
    pk.add(head, (-1, 1.5, -2.5), (2, 1, 2), faces(gular), inflate=-0.1)
    # the casque climbs in steps from the crown to a peak over the nape: a helmet seen side on
    cq = head.part("casque", (0, -1.5, -1.5))
    pk.add(cq, (-1, -1, -0.5), (2, 1, 3), faces(casque(1.0)))
    pk.add(cq, (-0.5, -2, 0.5), (1, 1, 2), faces(casque(1.04)), inflate=0.05)
    pk.add(cq, (-0.5, -3, 1.5), (1, 1, 1), faces(casque(1.08)), inflate=-0.05)

    # turret eyes: a scaly cone on each side of the head with the pupil at its tip; each eye's pivot
    # is the centre of the socket so the code can swivel them separately
    for side, sx in (("right", -1), ("left", 1)):
        mir = sx > 0
        e = head.part(side + "_eye", (1.5 * sx, -0.5, -1.6), (0, 0.45 * sx, 0))   # gazing half forward
        pk.add(e, (-1 if sx < 0 else 0, -1, -1), (1, 2, 2), None if mir else faces(turret),
               mirror=mir, share="turret", inflate=0.25)
        pk.add(e, (-1.7 if sx < 0 else 0.7, -1, -1), (1, 2, 2), None if mir else faces(turret),
               mirror=mir, share="turret_tip", inflate=-0.15)
        pk.add(e, (-2.2 if sx < 0 else 1.2, -0.5, -0.5), (1, 1, 1), None if mir else faces(pupil),
               mirror=mir, share="pupil", inflate=-0.2)

    # tail: slopes back from the body, then rolls down and forward into a tight spiral with the tip
    # tucked inside. tail_curl cancels the tail's slope, so the loop is drawn level: across the top,
    # down the back, forward along the bottom, up the front and in.
    tail = body.part("tail", (0, -0.5, 3), (-0.35, 0, 0))
    pk.add(tail, (-0.5, -1, -0.5), (1, 2, 5), faces(tail_skin))
    curl = tail.part("tail_curl", (0, 0, 4.5), (0.35, 0, 0))
    pk.add(curl, (-0.5, -0.5, -0.5), (1, 1, 2), faces(tail_skin), inflate=0.08)
    pk.add(curl, (-0.5, 0, 1.5), (1, 3, 1), faces(tail_skin), inflate=0.04)
    pk.add(curl, (-0.5, 2.5, -0.5), (1, 1, 3), faces(tail_skin), inflate=0.06)
    pk.add(curl, (-0.5, 1, -1.5), (1, 2, 1), faces(tail_skin), inflate=0.02)
    pk.add(curl, (-0.5, 1, -0.5), (1, 1, 1), faces(tail_skin), inflate=-0.05)

    # legs: thin and a little splayed, ending in split mitten feet
    for name, x, z in (("right_front_leg", -1.2, -2.0), ("left_front_leg", 1.2, -2.0),
                       ("right_hind_leg", -1.2, 2.0), ("left_hind_leg", 1.2, 2.0)):
        sx = -1 if name.startswith("right") else 1
        mir = sx > 0
        lg = body.part(name, (x, 2.1, z), (0, 0, 0.28 if sx < 0 else -0.28))
        pk.add(lg, (-0.5, -0.5, -0.5), (1, 3, 1), None if mir else faces(leg), mirror=mir, share="leg")
        pk.add(lg, (-0.5, 2, -1.5), (1, 1, 3), None if mir else faces(mitten), mirror=mir, share="mitten",
               inflate=-0.05)

    pk.apply()
    m.save()
    spawn_egg("chameleon", "#7fb238", "#d6e86a", accent="#3e6b1e")


if __name__ == "__main__":
    build()

"""Hedgehog: a palm-sized pet. A round dome of brown, cream-tipped quills that flares a little at the
back, a pale cream face with a pointy snout and a shiny black button nose, small round eyes, tiny
rounded ears and four stubby feet. `ball` is the curled-up form (a spiky ball with just the nose
peeking out); the code shows it only while curled and hides body/head/legs then."""
import math
import os

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Hedgehog'
LOOT = []
TAGS = []

# Debug only: HEDGEHOG_DEBUG_BALL=1 moves the ball beside the body so the preview shows both.
DEBUG_BALL = os.environ.get("HEDGEHOG_DEBUG_BALL") == "1"


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


# -- palette -----------------------------------------------------------------------------------------
Q_DARK = ["#3d2b20", "#402d22"]
Q_MID = ["#5f4633", "#5b4331", "#614835"]
Q_LIGHT = ["#7f6147", "#7a5d44"]
Q_TIP = ["#cfba98", "#c8b291"]
Q_BRIGHT = ["#e6d7b9", "#eee2c8"]
FACE = ["#eadcc0", "#e4d5b6", "#efe3ca"]
FACE_SH = ["#d3c09e", "#cdb996"]
SKIN = ["#b7987a", "#ae9072", "#bb9d7f"]       # the soft fur under the quills
BELLY = ["#cdb898", "#c6b090"]
EAR = ["#8c6a55", "#86654f"]
EAR_IN = "#5c3f32"
LEG = ["#6b4f3c", "#654a38", "#705341"]
TOE = "#c7a888"
SOLE = ["#4a3628", "#45322a"]
EYE = "#140e0c"
SHINE = "#f6f6f2"
NOSE = "#141012"
NOSE_SHINE = "#8e8c98"


# -- quills ------------------------------------------------------------------------------------------
QUILL_BANDS = (Q_DARK, Q_MID, Q_MID, Q_LIGHT, Q_LIGHT, Q_TIP)


def band(c, ph, cream=True):
    if ph == len(QUILL_BANDS) - 1:
        if not cream:                 # only every other spine ends in a cream tip
            return c.pick(Q_LIGHT)
        if c.rng.random() < 0.25:
            return c.pick(Q_BRIGHT)
    return c.pick(QUILL_BANDS[ph])


def quill(dirn, top=1.04, bottom=0.7, jag=False, flat=None):
    """Layered quills: rows of banded spines (dark base, brown, light, cream tip) pointing along dirn,
    each row offset half a spine from the next. dirn: 'up' (tip toward row 0), 'down', 'back' (side
    faces: toward the mob's rear). Side/back/front faces darken toward the bottom; jag cuts a
    sawtooth fringe of spike tips into the bottom edge."""
    def p(c):
        period = len(QUILL_BANDS)
        offs = {}
        for y in range(c.h):
            if flat is not None:
                f = flat
            elif c.face == "top":
                f = top
            elif c.face == "bottom":
                f = bottom * 0.85
            else:
                f = top - (top - bottom) * (y / max(1, c.h - 1))
            for x in range(c.w):
                d = dirn
                if d == "back":
                    d = "up" if c.face == "top" else ("left" if c.face == "right" else
                                                       "right" if c.face == "left" else "down")
                if d == "up":
                    along, across = c.h - 1 - y, x
                elif d == "down":
                    along, across = y, x
                elif d == "left":
                    along, across = c.w - 1 - x, y
                else:
                    along, across = x, y
                if across not in offs:      # rows step diagonally, with a little wobble
                    offs[across] = (across * 2 + (1 if c.rng.random() < 0.25 else 0)) % period
                ph = (along + offs[across]) % period
                if c.rng.random() < 0.03:
                    ph = (ph + c.rng.choice((1, period - 1))) % period
                cream = ((along + offs[across]) // period + across) % 2 == 0
                c.set(x, y, shade(band(c, ph, cream), f))
        if jag and c.face in ("front", "back", "left", "right") and c.h >= 2:
            ofs = c.rng.randrange(3)
            for x in range(c.w):
                if (x + ofs) % 3 != 1:        # sawtooth: every third column reaches the bottom row
                    c.clear(x, c.h - 1)
                else:
                    c.set(x, c.h - 1, shade(c.pick(Q_MID), bottom * 0.95))
    return p


def starburst(cx=None, cy=None, r=3.4, spike=1.4, n=14, flat_bottom=False):
    """A flat quill plate cut (cutout) into a spiky disc: the silhouette of a curled hedgehog."""
    def p(c):
        x0 = (c.w - 1) / 2 if cx is None else cx
        y0 = (c.h - 1) / 2 if cy is None else cy
        rot = c.rng.random()
        for y in range(c.h):
            for x in range(c.w):
                dx, dy = x - x0, y - y0
                dist = math.hypot(dx, dy)
                a = (math.atan2(dy, dx) / (2 * math.pi) + 0.5 + rot) * n
                tri = 1 - abs((a % 1) * 2 - 1)                  # triangle wave: pointed spikes
                lim = r + spike * tri
                f = 1.0 - 0.25 * max(0.0, dy) / max(1.0, c.h - y0)
                if dist > lim + 0.35:
                    c.clear(x, y)
                elif dist > r - 0.2:                            # the spikes: brown, cream at the tip
                    tip = dist > lim - 0.5 and tri > 0.8
                    c.set(x, y, shade(c.pick(Q_TIP if tip else Q_MID if tri > 0.3 else Q_DARK), f))
                else:
                    c.set(x, y, shade(c.pick(Q_MID if (x + y) % 3 else Q_DARK), f))
    return p


def fringe(teeth_up=True, dirn="up"):
    """A flat quill plate with a ragged spiky edge (cutout) on top."""
    def p(c):
        quill(dirn, top=1.02, bottom=0.8)(c)
        ofs = c.rng.randrange(2)
        for x in range(c.w):
            hgt = 1 + ((x + ofs) % 2) + (1 if (x + ofs) % 4 == 1 else 0)   # 1..3 px tall spikes
            for y in range(c.h - hgt if teeth_up else hgt):
                c.clear(x, y if teeth_up else c.h - 1 - y)
            tip = c.h - hgt if teeth_up else hgt - 1
            c.set(x, tip, shade(c.pick(Q_TIP), 0.95))
    return p


# -- body, face, legs --------------------------------------------------------------------------------
def skin(c):
    for y in range(c.h):
        f = 1.0 - 0.22 * (y / max(1, c.h - 1)) if c.face not in ("top", "bottom") else 0.9
        for x in range(c.w):
            c.set(x, y, shade(c.pick(SKIN), f))


def belly(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BELLY), 0.82))


def face_front(c):
    # 6 wide x 4 tall. The snout covers columns 2-3 of rows 2-3.
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(FACE), 1.04 - 0.05 * y))
    for x0 in (0, 4):                 # round 2x2 eyes, light catching the top-left pixel
        c.set(x0, 1, SHINE)
        c.set(x0 + 1, 1, EYE)
        c.set(x0, 2, EYE)
        c.set(x0 + 1, 2, EYE)
    for x in (1, 4):                  # a soft shaded cheek under each eye
        c.set(x, 3, c.pick(FACE_SH))


def face_side(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(FACE), 1.0 - 0.07 * y))
    c.set(fx(c, 0), 2, EYE)           # the eye just wraps round the corner
    for y in range(c.h):              # quills creep down the back of the cheeks
        c.set(fx(c, c.w - 1), y, shade(c.pick(Q_MID), 1.0 - 0.06 * y))
    c.set(fx(c, c.w - 2), 0, shade(c.pick(Q_LIGHT), 1.0))


def face_top(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FACE) if y >= c.h - 2 else c.pick(Q_MID)
            c.set(x, y, shade(col, 1.05))


def face_bottom(c):
    c.noise([shade(b, 0.8) for b in FACE])


def snout_front(c):
    for x in range(c.w):
        c.set(x, 0, shade(c.pick(FACE), 0.98))
        c.set(x, 1, shade(c.pick(FACE_SH), 0.92))


def snout_side(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(FACE), 1.0 - 0.08 * y))
    c.set(fx(c, 0), 1, shade(c.pick(FACE_SH), 0.85))   # the corner of a small smile
    c.set(fx(c, 1), 1, shade(c.pick(FACE_SH), 0.95))


def snout_top(c):
    c.noise([shade(f, 1.06) for f in FACE])


def snout_bottom(c):
    c.noise([shade(f, 0.78) for f in FACE])


def nose(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, NOSE)
    if c.face == "top":
        c.set(0, c.h - 1, NOSE_SHINE)
    elif c.face == "front":
        c.set(0, 0, "#3a3640")


def ear(c):
    c.noise(EAR)
    if c.face in ("right", "left"):   # 2x2 outer face: a dark inner ear under a light rim
        c.set(fx(c, 0), 1, EAR_IN)
        c.set(fx(c, 1), 1, shade(EAR_IN, 1.15))
        c.set(fx(c, 0), 0, shade(c.pick(EAR), 1.12))


def leg(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(LEG), 1.0 - 0.15 * y))
    if c.face == "front":
        c.set(0, c.h - 1, TOE); c.set(1, c.h - 1, shade(TOE, 0.9))


def sole(c):
    c.noise(SOLE)


def ball_front(c):
    """Front of the curled ball: quills, with the tip of the cream face and the nose peeking out."""
    quill("down", top=1.04, bottom=0.74)(c)
    cx = c.w // 2
    for x in (cx - 1, cx):
        c.set(x, c.h - 2, shade(c.pick(FACE), 0.95))
        c.set(x, c.h - 1, NOSE)
    c.set(cx - 1, c.h - 1, NOSE_SHINE)


def build():
    m = Model("hedgehog", 64, 64, seed=1515)
    pk = Pack(m)

    # body: pivot y 21. soft core x -3..3, y 19-23, z -4..4 (only its lower edge shows under the quills)
    body = m.part("body", (0, 21, 0))
    pk.add(body, (-3, -2, -4), (6, 4, 8), faces(skin, bottom=belly))

    # quills: a dome over the core. mantle y 18-22 (spiky bottom fringe), crown y 17-18, a rounded rump,
    # a low ragged crest along the spine, and a ragged plate tilted out at the back so the rear flares
    quills = body.part("quills", (0, 0, 0))
    pk.add(quills, (-3.5, -3, -3.5), (7, 4, 8), faces(quill("back", jag=True), top=quill("up"),
                                                    front=quill("up", jag=True),
                                                    back=quill("down", jag=True)))
    pk.add(quills, (-2.5, -4, -2.5), (5, 1, 6), faces(quill("back", top=1.07, bottom=0.98),
                                                    top=quill("up", top=1.08)))
    pk.add(quills, (-2.5, -2.5, 4.5), (5, 3, 1), faces(quill("down", jag=True), top=quill("up")))
    flare = quills.part("quill_flare", (0, -1.5, 5), (-0.55, 0, 0))
    pk.add(flare, (-3, -3, 0), (6, 3, 0), faces(fringe()))
    crest = quills.part("quill_crest", (0, -4, 0), (0, 0, 0))
    pk.add(crest, (0, -1.5, -1.5), (0, 2, 6), faces(fringe(dirn="back")))

    # head: child of root, pivot at the neck (front of the quill dome); face x -3..3, y 18-22
    head = m.part("head", (0, 20, -3.5))
    pk.add(head, (-3, -2, -3), (6, 4, 3), faces(face_bottom, front=face_front, right=face_side,
                                                left=face_side, top=face_top))
    # a cap of quills over the forehead (part of the head so it turns with it)
    pk.add(head, (-3.5, -3, -1.5), (7, 2, 2), faces(quill("up", jag=True), top=quill("up"),
                                                    back=quill("down")))
    # tiny ears poking out sideways at the top of the head, just under the quill cap
    pk.add(head, (-4, -2.5, -2), (1, 2, 2), faces(ear), share="ear")
    pk.add(head, (3, -2.5, -2), (1, 2, 2), None, mirror=True, share="ear")

    snout = head.part("snout", (0, 1, -3))
    pk.add(snout, (-1, -1, -2), (2, 2, 2), faces(snout_side, front=snout_front, top=snout_top,
                                                 bottom=snout_bottom))
    pk.add(snout, (-1, -1, -2.9), (2, 1, 1), faces(nose), inflate=0.1)

    # stubby legs: y 22-24, mostly tucked under the body
    legp = faces(leg, bottom=sole)
    for name, x, z in (("right_front_leg", -2, -2), ("left_front_leg", 2, -2),
                       ("right_hind_leg", -2, 2.5), ("left_hind_leg", 2, 2.5)):
        lg = m.part(name, (x, 22, z))
        left = name.startswith("left")
        pk.add(lg, (-1, 0, -1), (2, 2, 2), None if left else legp, mirror=left, share="leg")

    # the curled-up ball: about the body's size (7 px), rounded by crossing slabs, bottom at y 24,
    # with three crossed spiky plates poking out for a bristly silhouette from any side
    ball = m.part("ball", (12 if DEBUG_BALL else 0, 21, 0))
    pk.add(ball, (-3, -3, -3), (6, 6, 6), faces(quill("back", top=1.04, bottom=0.7),
                                                top=quill("up", top=1.1)))
    pk.add(ball, (-3.5, -2, -2), (7, 4, 4), faces(quill("back", top=1.04, bottom=0.74),
                                                  top=quill("up", top=1.1)))
    pk.add(ball, (-2, -2, -3.5), (4, 4, 7), faces(quill("back", top=1.04, bottom=0.74),
                                                  front=ball_front, top=quill("up", top=1.1)))
    pk.add(ball, (-2, -4, -2), (4, 1, 4), faces(quill("up", top=1.07, bottom=0.982)))
    burst = faces(starburst(cy=3.5, r=3.4, spike=1.3, n=12))
    pk.add(ball, (0, -4.5, -4.5), (0, 8, 9), burst)
    pk.add(ball, (-4.5, -4.5, 0), (9, 8, 0), burst)
    diag = ball.part("ball_spikes", (0, 0, 0), (0, math.pi / 4, 0))
    pk.add(diag, (0, -4.5, -4.5), (0, 8, 9), burst)
    pk.add(diag, (-4.5, -4.5, 0), (9, 8, 0), burst)

    pk.apply()
    m.save()
    spawn_egg("hedgehog", "#5e4330", "#e4d4b4", accent="#141012")


if __name__ == "__main__":
    build()

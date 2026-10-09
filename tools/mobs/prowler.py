"""Prowler: a big black jungle panther that stalks through the undergrowth and pounces. A long, low,
muscular body (26 px from chest to rump) in sleek near-black fur with a glossy sheen along the back
and faint charcoal rosettes on the flanks and back that only show up close. Powerful high shoulder
blades, a narrower waist and heavy haunches; the thick upper legs bulge out past the body, thinning
to the wrist and ending in big paws with faint pale claws. A broad head on a thick neck: small
rounded ears laid a little back, a short dark-grey muzzle with a black nose and a few pale whiskers,
white fangs at the mouth corners, and big glowing emerald eyes with dark slit pupils, the only thing
you see of it at night. A long thick tail hangs down and back from the rump and curls up at the tip.

Rig: `body` pivots at the centre of the torso; `head` (with `jaw`), and the four legs hang off the
root, so the code can lower body and head into a crouch while the legs fold under them. The legs
pivot at the top, 4 px inside the body, so folding them never opens a gap. `jaw` opens with a
positive xRot. `tail` hangs off the body at the rump, `tail_tip` curls up from it."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix, hexc
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Prowler"
LOOT = [item("leather", 1, 3), item("bone", 0, 2)]
TAGS = ["fall_damage_immune"]


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    """Shelf packer. Every cube's box-UV block keeps a transparent 1 px gutter to its right and below,
    so no face edge ever samples a neighbour's texels."""
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0):
        self.items.append((part, origin, size, paint, mirror, share, inflate))

    def apply(self):
        def dims(size):
            w, h, d = (int(math.ceil(s)) for s in size)
            return 2 * d + 2 * w + 1, d + h + 1
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
            part.cube(keys[share or ("#", i)], origin, size, paint, mirror=mirror, inflate=inflate)


SIDES = ("front", "back", "left", "right")


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def light(c, x, y, col, base=0.22):
    """A pixel that IS light: full colour on the emissive layer over a dim base, so the additive glow
    shows the true colour in the dark instead of washing out to white in daylight."""
    if not c.inside(x, y):
        return
    c.set(x, y, shade(col, base))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), hexc(col))


# -- palette -----------------------------------------------------------------------------------------
FUR = ["#1b1b21", "#1c1c22", "#1a1a20", "#1c1c22"]
FUR_RARE = ["#141418", "#151519", "#202027"]
SHEEN = ["#2a2a33", "#2e2e38", "#282830"]
ROSETTE = ["#2c2c36", "#2a2a33", "#2e2e38"]
DEEP = ["#0f0f12", "#111115"]
BELLY = ["#27272e", "#2a2a31", "#25252b"]
MUZZLE = ["#2a2a31", "#2e2e35", "#27272e"]
NOSE = "#0b0b0e"
NOSE_HI = "#3a3a44"
WHISKER = ["#8e8e98", "#9c9ca6"]
FANG = "#f0ece0"
FANG_SH = "#d2ccbd"
MOUTH = ["#4a1c22", "#3f171c"]
TONGUE = ["#7a3a44", "#6e333d"]
CLAW = ["#a6a6ae", "#9a9aa3"]
PAD = ["#0c0c0f", "#101013"]
EYE_HOT = "#5cff7a"
EYE_RIM = "#1f9a3a"
PUPIL = "#04100a"


def lit(c, y, top=1.14, hi=1.04, low=0.8):
    if c.face == "top":
        return top
    if c.face == "bottom":
        return 1.0
    return hi - (hi - low) * y / max(1, c.h - 1)


RINGS = (
    (".##.", "#..#", ".##."),
    (".#.", "#.#", ".#."),
    ("##.", "#.#", ".##"),
    (".##", "#.#", "##."),
)


def rosettes(c, spacing=5, f=None):
    """Faint charcoal rosettes: small broken rings on a jittered grid (only a shade off the fur)."""
    for gy in range(-1, c.h, spacing):
        for gx in range(-1 + (gy // spacing % 2) * (spacing // 2), c.w, spacing):
            if c.rng.random() < 0.15:
                continue
            ring = c.rng.choice(RINGS)
            ox, oy = gx + c.rng.randint(0, 1), gy + c.rng.randint(0, 1)
            for ry, row in enumerate(ring):
                for rx, ch in enumerate(row):
                    x, y = ox + rx, oy + ry
                    if ch == "#" and c.inside(x, y) and c.rng.random() < 0.85:
                        c.set(x, y, shade(c.pick(ROSETTE), f(c, y) if f else 1.0))


def fur(top=1.14, hi=1.04, low=0.8, spots=True, sheen=0.08, under=BELLY, spacing=5):
    """Sleek near-black fur: lit glossy top with sheen streaks running along the body, sides
    darkening downward, a slightly lighter dark-grey underside, faint rosettes on flanks and back."""
    def f(c, y):
        return lit(c, y, top, hi, low)

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    col = c.pick(under)
                else:
                    col = c.pick(FUR_RARE) if c.rng.random() < 0.08 else c.pick(FUR)
                    col = shade(col, f(c, y))
                c.set(x, y, col)
        if spots and c.face in ("left", "right", "top") and c.w >= 4 and c.h >= 4:
            rosettes(c, spacing, f)
        if c.face == "top":                     # glossy streaks along the back (rows run front-back)
            for _ in range(int(c.w * c.h * sheen) + 1):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                for yy in (y, y + 1):
                    if c.inside(x, yy):
                        c.set(x, yy, c.pick(SHEEN))
        elif c.face in ("left", "right") and c.h > 3:   # the sheen catches the top edge of the flank
            for x in range(c.w):
                if c.rng.random() < 0.2:
                    c.set(x, 0, c.pick(SHEEN))
    return p


def back_top(c):
    """Top of the torso: a darker line down the spine between glossy shoulders."""
    fur(sheen=0.12)(c)
    mid = c.w // 2
    for y in range(c.h):
        if c.rng.random() < 0.7:
            c.set(mid - (c.w % 2 == 0), y, c.pick(DEEP))


def chest_front(c):
    """The chest under the neck: dark fur shading to the grey of the underside at the bottom."""
    fur(spots=False)(c)
    for y in range(c.h - 3, c.h):
        for x in range(1, c.w - 1):
            if c.rng.random() < 0.5 + 0.15 * (y - c.h + 3):
                c.set(x, y, c.pick(BELLY))


def flank(c):
    """Side of the body: rosettes, and the grey of the belly creeping up the bottom row."""
    fur()(c)
    for x in range(c.w):
        if c.rng.random() < 0.6:
            c.set(x, c.h - 1, shade(c.pick(BELLY), 0.85))


# -- head --------------------------------------------------------------------------------------------
def skull_front(c):
    """8 x 6: brow, two big emerald eyes (3 x 2, slit pupils) on rows 1-2, cheeks with whiskers below.
    The muzzle covers the middle of rows 3-5."""
    fur(spots=False)(c)
    for x in range(c.w):
        c.set(x, 0, shade(c.pick(FUR), 1.12))                       # brow
    for x in (3, 4):                                                # dark bridge of the nose
        for y in (1, 2):
            c.set(x, y, c.pick(DEEP))
    for x0, flip in ((0, False), (5, True)):
        cols = [0, 1, 2] if not flip else [2, 1, 0]
        o, mid, inner = (x0 + cols[0], x0 + cols[1], x0 + cols[2])
        light(c, o, 1, EYE_RIM)
        light(c, inner, 1, EYE_HOT)
        light(c, o, 2, "#2fc04f")
        light(c, inner, 2, EYE_RIM)
        c.set(mid, 1, PUPIL)                                        # the slit
        c.set(mid, 2, PUPIL)
    for y in (3, 4, 5):                                             # cheeks: a little greyer
        for x in (0, 1, 6, 7):
            c.set(x, y, shade(c.pick(MUZZLE), 0.9 - 0.04 * y))


def skull_side(c):
    fur(spots=False)(c)
    light(c, fx(c, 0), 1, EYE_RIM, base=0.3)                       # the eye wraps the corner
    c.set(fx(c, 0), 2, c.pick(DEEP))
    for y in (3, 4, 5):                                             # grey cheek toward the front
        for i in (0, 1):
            c.set(fx(c, i), y, shade(c.pick(MUZZLE), 0.9))


def skull_bottom(c):
    c.noise(BELLY)


def cheek_front(c):
    """Front of the jowls (10 x 3): grey whisker pads beside the muzzle with pale whisker roots; the
    middle is hidden behind the muzzle."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(MUZZLE) if 1 <= x <= c.w - 2 else c.pick(FUR)
            c.set(x, y, shade(col, 1.0 - 0.06 * y))
    for (x, y) in ((0, 1), (c.w - 1, 1)):                           # whiskers poking out sideways
        c.set(x, y, c.pick(WHISKER))


def cheek_side(c):
    fur(spots=False)(c)
    c.set(fx(c, 0), 1, shade(WHISKER[0], 0.85))                     # a whisker fanning back


def cheek_top(c):
    fur(spots=False, sheen=0.0)(c)


def muzzle_front(c):
    """4 x 2: the black nose (with a wet glint) over a grey lip with a dark split."""
    c.noise(MUZZLE)
    c.set(1, 0, NOSE); c.set(2, 0, NOSE)
    c.set(1, 1, shade(MUZZLE[0], 0.7)); c.set(2, 1, shade(MUZZLE[0], 0.7))


def muzzle_top(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(FUR), 1.12) if y < c.h - 1 else shade(c.pick(MUZZLE), 1.05))
    c.set(1, c.h - 1, NOSE_HI); c.set(2, c.h - 1, NOSE)


def muzzle_side(c):
    c.noise(MUZZLE)
    c.set(fx(c, 1), 0, c.pick(WHISKER))
    c.set(fx(c, 2), 0, shade(WHISKER[0], 0.8))
    c.set(fx(c, 0), 1, shade(MUZZLE[0], 0.7))                       # the corner of the lip


def mouth_roof(c):
    """Underside of the muzzle, seen when the jaw drops: dark red, small teeth along the front."""
    c.noise(MOUTH)
    for x in range(c.w):                                            # row h-1 is the front edge (lip);
        c.set(x, c.h - 1, shade(MUZZLE[0], 0.6))                    # the small teeth sit behind it
        c.set(x, c.h - 2, FANG_SH if x in (1, 2) else FANG)


def jaw_paint(c):
    if c.face == "top":                                             # the mouth: tongue, lower teeth
        c.noise(MOUTH)
        for y in range(1, c.h - 1):
            for x in (1, 2):
                c.set(x, y, c.pick(TONGUE))
        for x in range(c.w):
            c.set(x, c.h - 1, shade(MUZZLE[0], 0.6))                # the lower lip
            c.set(x, c.h - 2, FANG_SH)
        c.set(0, c.h - 2, FANG); c.set(c.w - 1, c.h - 2, FANG)      # lower fangs
        c.set(0, c.h - 3, FANG); c.set(c.w - 1, c.h - 3, FANG)
        return
    if c.face == "bottom":
        c.noise(BELLY)
        return
    c.noise(MUZZLE)
    for x in range(c.w):
        c.set(x, 0, shade(MUZZLE[0], 0.6))                         # the dark lip line


def canine(c):
    c.fill(FANG if c.face in ("front", "right") else FANG_SH)
    if c.face == "front":
        c.set(0, c.h - 1, "#ffffff")


def ear(part):
    def p(c):
        fur(spots=False, sheen=0.0)(c)
        if c.face == "front":                                       # the dark inner ear, a grey rim
            for y in range(c.h):
                for x in range(c.w):
                    edge = x in (0, c.w - 1) or (y == 0)
                    c.set(x, y, c.pick(ROSETTE) if edge else c.pick(DEEP))
    return p


# -- legs, paws, tail --------------------------------------------------------------------------------
def leg_fur(c):
    fur(top=1.1, hi=1.02, low=0.86, spacing=4)(c)


def paw(c):
    """Big paw: toes split by dark lines on the front, faint pale claws along the bottom of it."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FUR)
            if c.face == "top":
                col = shade(col, 1.1)
            elif c.face == "bottom":
                col = c.pick(PAD)
            c.set(x, y, col)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, 0, shade(c.pick(FUR), 1.08 if x % 2 == 0 else 0.75))
            c.set(x, c.h - 1, shade(c.pick(FUR), 0.85))
        c.set(0, c.h - 1, mix(c.pick(CLAW), FUR[0], 0.6))          # faint pale claw tips
        c.set(2, c.h - 1, mix(c.pick(CLAW), FUR[0], 0.68))
    elif c.face == "top":
        for x in range(1, c.w, 2):                                 # row h-1 is the toes' front edge
            c.set(x, c.h - 1, mix(c.pick(DEEP), c.get(x, c.h - 1), 0.4))
    elif c.face == "bottom":
        for x in (1, 2):
            c.set(x, c.h - 1, mix(c.pick(CLAW), PAD[0], 0.5))


def tail_fur(c):
    fur(spots=True, spacing=4, low=0.85)(c)


def tail_end(c):
    fur(spots=False, sheen=0.2)(c)


# -- the model ---------------------------------------------------------------------------------------
def build():
    m = Model("prowler", 128, 64, seed=4747)
    pk = Pack(m)

    # body: pivot at the centre of the torso, world (0, 12.5, 0). A deep chest x -4.5..4.5, y 8..17,
    # z -13..-2; a narrower, tucked-up waist (y 9..15); heavy haunches x -4..4, y 8.5..15.5,
    # z 3..13; the shoulder blades rise to y 6 over the chest.
    body = m.part("body", (0, 12.5, 0))
    pk.add(body, (-4.5, -4.5, -13), (9, 9, 11),
           faces(fur(), top=back_top, front=chest_front, right=flank, left=flank))
    pk.add(body, (-3.5, -3.5, -4), (7, 6, 9), faces(fur(), top=back_top, right=flank, left=flank))
    pk.add(body, (-4, -4, 3), (8, 7, 10), faces(fur(), top=back_top, right=flank, left=flank))
    pk.add(body, (-3.5, -6.5, -11), (7, 3, 6), faces(fur(sheen=0.15)))                 # shoulder blades

    # tail: from the top of the rump, hanging down and back, the tip curling up again
    tail = body.part("tail", (0, -2.5, 12.5), (-1.0, 0, 0))
    pk.add(tail, (-1.5, -1.5, 0), (3, 3, 9), faces(tail_fur))
    tip = tail.part("tail_tip", (0, 0, 8.5), (0.85, 0, 0))
    pk.add(tip, (-1, -1, 0), (2, 2, 6), faces(tail_fur), inflate=0.25)
    end = tip.part("tail_end", (0, 0, 5.5), (0.75, 0, 0))
    pk.add(end, (-1, -1, 0), (2, 2, 4), faces(tail_end))

    # head: child of the root, pivot at the neck in front of the shoulders, world (0, 12, -12), held
    # low under the shoulder line. A thick neck sunk into the chest, the broad skull x -4..4, y 8..14,
    # z -20..-14, wider jowls, a short muzzle (y 11..13) sticking out 2.5 px, the jaw (y 13..15).
    head = m.part("head", (0, 12, -12))
    pk.add(head, (-3, -2.5, -2.5), (6, 6, 5), faces(fur(spots=False)))
    pk.add(head, (-4, -4, -8), (8, 6, 6),
           faces(fur(spots=False), front=skull_front, right=skull_side, left=skull_side, bottom=skull_bottom))
    # broad cheeks / jowls behind the muzzle make the head wider than it is tall
    pk.add(head, (-5, -1.5, -7), (10, 3, 4), faces(fur(spots=False), front=cheek_front, top=cheek_top,
                                                    right=cheek_side, left=cheek_side, bottom=skull_bottom))
    pk.add(head, (-2, -1, -10.5), (4, 2, 3),
           faces(muzzle_side, front=muzzle_front, top=muzzle_top, bottom=mouth_roof))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        # upper fangs hang from the outer corners of the muzzle, peeking out past the lower lip
        pk.add(head, (-2.5 if sx < 0 else 1.5, 0.4, -10.3), (1, 2, 1), None if left else faces(canine),
               mirror=left, share="canine", inflate=-0.1)
        e = head.part(side + "_ear", (2.5 * sx, -4, -4.5), (-0.35, 0, 0.15 * sx))
        pk.add(e, (-1.5, -1.5, -0.5), (3, 2, 1), None if left else faces(ear("base")), mirror=left, share="ear")
        pk.add(e, (-0.5, -2.5, -0.5), (1, 2, 1), None if left else faces(ear("tip")), mirror=left, share="ear_tip",
               inflate=-0.1)

    jaw = head.part("jaw", (0, 1, -8))
    pk.add(jaw, (-2, 0, -2.5), (4, 2, 5), faces(jaw_paint), inflate=-0.05)

    # legs: children of the root, pivot at the top (y 14), 4 px inside the body, paws on the ground
    # (y 24). Front: a thick upper leg bulging past the chest, a narrower forearm, a big paw reaching
    # forward. Hind: a heavy thigh, a narrower shank set back, the same big paw.
    for name, x, z in (("right_front_leg", -3, -8.5), ("left_front_leg", 3, -8.5)):
        left = x > 0
        lg = m.part(name, (x, 14, z))
        pk.add(lg, (-2, -1, -2), (4, 6, 4), None if left else faces(leg_fur), mirror=left, share="upper")
        pk.add(lg, (-1.5, 4, -1.5), (3, 5, 3), None if left else faces(leg_fur), mirror=left, share="forearm")
        pk.add(lg, (-2, 8, -3), (4, 2, 5), None if left else faces(paw), mirror=left, share="paw")
    for name, x, z in (("right_hind_leg", -3, 9), ("left_hind_leg", 3, 9)):
        left = x > 0
        lg = m.part(name, (x, 14, z))
        pk.add(lg, (-2, -1, -2.5), (4, 7, 5), None if left else faces(leg_fur), mirror=left, share="thigh")
        pk.add(lg, (-1.5, 5, -1), (3, 4, 3), None if left else faces(leg_fur), mirror=left, share="shank")
        pk.add(lg, (-2, 8, -2.5), (4, 2, 5), None if left else faces(paw), mirror=left, share="paw")

    pk.apply()
    m.save()
    spawn_egg("prowler", "#17171c", "#3a3a44", accent="#5cff7a")


if __name__ == "__main__":
    build()

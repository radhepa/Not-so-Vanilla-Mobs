"""Skunk: a small, fat, low-slung striped skunk. Glossy blue-black fur with a soft sheen on top; a
narrow white blaze running up the middle of the face; a white cap on the crown and nape that
splits over the shoulders into two broad white stripes running down the back to the tail; a
pointed black snout with a dark nose, tiny round ears, bright little black eyes. Short legs on
black paws with pale claws, a back that rises to a high rump, and a huge bushy plume of a tail:
black, frosted with long white hairs along the top, white at the tip.

Rig: `body` holds the head and the `tail` (with its big plume `tail_tip`); the code raises the tail
straight up to warn and curls it over the back to spray. The four legs hang off the root."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Skunk"
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
BLACK = ["#1d1b21", "#211f25", "#1a181d", "#24222a"]
SHEEN = ["#3a3946", "#34333f", "#403f4d"]          # the blue gloss on top
DEEP = ["#121115", "#151318"]                      # undersides, shadow
WHITE = ["#f1efe9", "#e9e6de", "#f6f4ef"]
WHITE_SH = ["#cfccc4", "#c6c2b9"]
GREYW = ["#a9a6a4", "#9c9998"]                     # white hairs over black: the frosting
NOSE = "#0b0a0c"
NOSE_HI = "#4a4550"
EYE = "#020203"
SHINE = "#eef3f6"
CLAW = "#9d978e"


def black_fur(top=1.0, grad=0.25, sheen=0.25):
    """Glossy black fur: blue sheen streaks on top, darkening down the sides."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = c.pick(SHEEN) if c.rng.random() < sheen else shade(c.pick(BLACK), 1.25 * top)
                elif c.face == "bottom":
                    col = c.pick(DEEP)
                else:
                    col = shade(c.pick(BLACK), 1.12 - grad * (y / max(1, c.h - 1)))
                    if y == 0 and c.rng.random() < sheen:
                        col = mix(col, c.pick(SHEEN), 0.6)
                c.set(x, y, col)
        if c.face in ("left", "right") and c.h > 2:
            for _ in range(int(c.w * c.h * 0.06)):   # a few glossy hair strokes on the flanks
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h - 1)
                c.set(x, y, mix(c.get(x, y), c.pick(SHEEN), 0.5))
    return p


def white(c, x, y, edge=False):
    """A white-stripe pixel; at a stripe's edge the white hairs thin out over the black."""
    c.set(x, y, mix(c.pick(WHITE), c.pick(GREYW), 0.5) if edge and c.rng.random() < 0.5 else c.pick(WHITE))


# -- body --------------------------------------------------------------------------------------------
def torso_top(c):
    """6 x 9 from above: the two broad stripes run down the edges; over the shoulders (the front two
    rows) they join into the white of the nape."""
    black_fur()(c)
    for y in range(c.h):
        front = y >= c.h - 2
        for x in range(c.w):
            if x in (0, 1, c.w - 2, c.w - 1) or front:
                white(c, x, y, edge=x in (1, c.w - 2) and not front)


def torso_side(c):
    """The stripe laps over the top row along the whole length; at the shoulder it reaches a row
    lower. The rest is glossy black, the lowest row in shadow."""
    black_fur()(c)
    for x in range(c.w):
        i = fx(c, x)
        white(c, x, 0, edge=i > c.w - 3)
        if i <= 1:
            white(c, x, 1, edge=True)
    for x in range(c.w):
        c.set(x, c.h - 1, c.pick(DEEP))


def torso_front(c):
    """The chest under the chin: black, with the white of the nape coming down over the top row."""
    black_fur(grad=0.3)(c)
    for x in range(c.w):
        white(c, x, 0, edge=x in (0, c.w - 1))


def rump(c):
    """The back of the torso, round the tail root: black with the stripes' ends on the top row."""
    black_fur(grad=0.3)(c)
    for x in (0, 1, c.w - 2, c.w - 1):
        white(c, x, 0, edge=True)


def arch(c):
    """The rise of the back over the hips: the stripes run along both edges, black down the spine."""
    black_fur()(c)
    if c.face == "top":
        for y in range(c.h):
            white(c, 0, y); white(c, c.w - 1, y)
            if c.rng.random() < 0.3:
                white(c, 1, y, edge=True)
            if c.rng.random() < 0.3:
                white(c, c.w - 2, y, edge=True)
    elif c.face in ("left", "right"):
        for x in range(c.w):
            white(c, x, 0)
    elif c.face in ("front", "back"):
        white(c, 0, 0); white(c, c.w - 1, 0)


# -- head --------------------------------------------------------------------------------------------
def skull_front(c):
    """5 x 4: black, the white blaze up the middle (the snout covers columns 1-3 of rows 2-3), the
    little eyes on the front corners."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BLACK), 1.15))
    for y in range(3):
        white(c, 2, y)
    c.set(0, 1, EYE); c.set(c.w - 1, 1, EYE)


def skull_side(c):
    """5 x 4: black; the eye wraps round the front corner with its glint here; the white cap shows
    along the top row behind the eye."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(BLACK), 1.1 - 0.06 * y))
    c.set(fx(c, 0), 1, SHINE)
    c.set(fx(c, 0), 2, EYE)
    for x in range(c.w):
        if fx(c, x) >= c.w - 2:
            white(c, x, 0, edge=fx(c, x) == c.w - 2)


def skull_top(c):
    """5 x 4 from above: the white cap over the back of the crown, narrowing to the blaze at the
    front edge."""
    for y in range(c.h):
        for x in range(c.w):
            if y <= 1 or (y == 2 and 1 <= x <= 3) or x == 2:
                white(c, x, y, edge=(y == 2 and x != 2))
            else:
                c.set(x, y, c.pick(SHEEN) if c.rng.random() < 0.3 else shade(c.pick(BLACK), 1.25))


def skull_back(c):
    """The nape: white across the top two rows (running into the shoulders), black below."""
    for y in range(c.h):
        for x in range(c.w):
            if y <= 1:
                white(c, x, y, edge=y == 1)
            else:
                c.set(x, y, c.pick(BLACK))


def skull_bottom(c):
    c.noise(DEEP)


def snout(c):
    """The pointed black snout with the blaze running down its top to the nose."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(BLACK), 1.15)
            if c.face == "top":
                col = c.pick(WHITE) if x == c.w // 2 and y < c.h - 1 else c.pick(SHEEN)
            elif c.face == "bottom":
                col = c.pick(DEEP)
            elif c.face in ("right", "left") and y == c.h - 1 and fx(c, x) == 0:
                col = c.pick(DEEP)                  # the corner of the mouth
            c.set(x, y, col)


def nose(c):
    c.fill(NOSE)
    if c.face == "top":
        c.set(0, c.h - 1, NOSE_HI)
    elif c.face == "front":
        c.set(0, 0, shade(NOSE_HI, 0.8))


def ear(c):
    """A tiny round black ear with a pale fringe on top."""
    c.fill(shade(c.pick(BLACK), 1.2))
    if c.face == "top":
        c.set(0, 0, mix(c.pick(WHITE), c.pick(BLACK), 0.4))
    elif c.face == "front":
        c.set(0, 0, c.pick(DEEP))


# -- legs and tail -----------------------------------------------------------------------------------
def leg(c):
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(BLACK), 1.05 - 0.1 * (y / max(1, c.h - 1)))
            if c.face in ("back", "left"):
                col = shade(col, 0.9)
            c.set(x, y, col)
    if c.face == "front":                          # pale claws
        c.set(0, c.h - 1, CLAW); c.set(1, c.h - 1, shade(CLAW, 0.8))
    elif c.face == "bottom":
        c.noise(DEEP)


def plume(side_rows, top_share, tip=False):
    """Bushy tail fur in long hairs running along the tail: a mantle of white hairs over the top (the
    stripes carry on down the tail) thinning into grey streaks down the upper sides, glossy black
    below. side_rows: rows of white streaks down the sides; top_share: the white part of the top's
    width; tip=True gives the end of the plume (its back face) a white tuft."""
    def p(c):
        mid = (c.w - 1) / 2
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    d = abs(x - mid) / max(1.0, mid + 0.5)               # 0 centre .. ~1 edge
                    if d <= top_share:
                        col = c.pick(GREYW) if (y + 3 * x) % 7 == 0 else c.pick(WHITE)
                    elif d <= top_share + 0.3 and (y + x) % 3 == 0:
                        col = c.pick(GREYW)                              # a stray streak
                    else:
                        col = c.pick(SHEEN) if (y + x) % 4 == 0 else shade(c.pick(BLACK), 1.2)
                elif c.face in ("right", "left"):
                    # long hairs: each row is one streak along the tail, broken here and there
                    along = zb(c, x, y)
                    if y < side_rows:
                        col = c.pick(GREYW) if (along + 3 * y) % 6 == 0 else c.pick(WHITE)
                    elif y == side_rows:
                        col = c.pick(GREYW) if (along + 2 * y) % 5 < 2 else shade(c.pick(BLACK), 1.1)
                    else:
                        col = shade(c.pick(BLACK), 1.08 - 0.05 * y)
                        if (along + 2 * y) % 7 == 0:
                            col = mix(col, c.pick(SHEEN), 0.6)
                elif c.face == "bottom":
                    col = c.pick(DEEP)
                elif c.face == "back" and tip:
                    col = c.pick(WHITE) if y < c.h - 1 and c.rng.random() < 0.85 else c.pick(GREYW)
                    if y == c.h - 1 and x in (0, c.w - 1):
                        col = c.pick(BLACK)
                else:
                    col = c.pick(WHITE) if y < side_rows else c.pick(BLACK)
                c.set(x, y, col)
    return p


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position (so both faces of a flat plane get the same pixels)."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


def fringe(c):
    """A flat plane down the middle of the plume (both sides alike): the long hairs that stand out
    past its outline. White hair tips along the top and round the end, black ones underneath; the
    middle is hidden inside the plume."""
    for x in range(c.w):
        i = fx(c, x)                               # 0 = front of the plume
        for y in range(c.h):
            r = hsh(i, y, 5)
            if y == 0:                             # top edge: ragged white tips
                col = (WHITE[int(r * 3)] if r < 0.75 else GREYW[0]) if 1 <= i <= c.w - 2 and r > 0.3 else None
            elif y == c.h - 1:                     # underneath: ragged black tips
                col = BLACK[int(r * 4)] if 1 <= i <= c.w - 3 and r > 0.45 else None
            elif i == c.w - 1:                     # the end: a ragged white tuft
                col = (WHITE[int(r * 3)] if y < c.h - 2 else GREYW[0]) if 1 <= y <= c.h - 2 and r > 0.25 else None
            elif y == 1 or (i >= c.w - 2 and y < c.h // 2):
                col = WHITE[int(r * 3)]
            else:
                col = BLACK[int(r * 4)]
            if col is None:
                c.clear(x, y)
            else:
                c.set(x, y, col)


def build():
    m = Model("skunk", 64, 64, seed=3333)
    pk = Pack(m)

    # body: a fat, low torso x -3.5..3.5, y 16..21, z -4.5..4.5, and an arch over the hips (y 15..16,
    # z -1..4) so the back rises to a high rump
    body = m.part("body", (0, 19, 0))
    pk.add(body, (-3.5, -3, -4.5), (7, 5, 9),
           faces(black_fur(), top=torso_top, right=torso_side, left=torso_side, front=torso_front,
                 back=rump))
    pk.add(body, (-2.5, -4, -1), (5, 1, 5), faces(arch))

    # head: a child of the body, pivot at the neck, carried low. Skull x -2.5..2.5, y 16..20,
    # z -8.5..-4.5; a pointed snout 2 more forward with the nose on its tip; tiny round ears.
    head = body.part("head", (0, -0.5, -4.5))
    pk.add(head, (-2.5, -2.5, -4), (5, 4, 4),
           faces(skull_back, front=skull_front, right=skull_side, left=skull_side, top=skull_top,
                 bottom=skull_bottom))
    pk.add(head, (-1.5, -0.5, -6), (3, 2, 2), faces(snout))
    pk.add(head, (-0.5, -0.6, -6.6), (1, 1, 1), faces(nose), inflate=0.12)
    for sx in (-1, 1):
        left = sx > 0
        pk.add(head, (1.75 if left else -2.75, -3, -2.5), (1, 1, 1), None if left else faces(ear),
               mirror=left, share="ear", inflate=0.15)

    # legs: short, on black paws; the hind legs a pixel longer (they come out of the high rump)
    for name, sx, z, y, h in (("right_front_leg", -1, -3, 21, 3), ("left_front_leg", 1, -3, 21, 3),
                              ("right_hind_leg", -1, 3, 20, 4), ("left_hind_leg", 1, 3, 20, 4)):
        lg = m.part(name, (2.2 * sx, y, z))
        left = sx > 0
        share = "fleg" if h == 3 else "hleg"
        pk.add(lg, (-1, 0, -1), (2, h, 2), None if left else faces(leg), mirror=left, share=share)

    # tail: rises from the top of the rump, swelling as it goes; then the huge plume flows back,
    # rounded off at the end
    tail = body.part("tail", (0, -3, 4), (0.6, 0, 0))
    pk.add(tail, (-1.5, -1.5, 0), (3, 3, 3), faces(plume(1, 0.35)), inflate=0.25)
    pk.add(tail, (-2, -2, 2.5), (4, 4, 3), faces(plume(1, 0.45)), inflate=0.25)
    tip = tail.part("tail_tip", (0, 0, 5), (-0.5, 0, 0))
    pk.add(tip, (-2, -2, 0), (4, 4, 6), faces(plume(2, 0.95)), inflate=0.5)
    pk.add(tip, (-1.5, -1.5, 6), (3, 3, 1), faces(plume(1, 0.95, tip=True)), inflate=0.35)
    pk.add(tip, (0, -3.5, -0.5), (0, 7, 9), faces(fringe))

    pk.apply()
    m.save()
    spawn_egg("skunk", "#1f1d23", "#f1efe9", accent="#3a3946")


if __name__ == "__main__":
    build()

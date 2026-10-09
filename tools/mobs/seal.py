"""Seal: a plump grey harbour seal lying on its belly. A fat torpedo body (rounded with a ridge on
top, a belly underneath and a full chest in front) tapering to the hips, a round head with big dark
glossy eyes, a short broad muzzle with a dark V nose, spotted whisker pads and pale whiskers, short
front flippers with dark claws lying flat at the sides, and the hind flippers held together behind
as a two-lobed fan. The coat is silver-grey, darker along the back, with dark spots (some with pale
rings) and a paler, less spotted belly.
`seal_pup` shares the geometry: a fluffy white pup (lanugo) with the same big dark eyes.
`ball` is the snowball the seal balances on its nose; at rest it sits hidden inside the head and the
code moves it out onto the nose (and shows it) while the seal balances."""
import math
import os
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Seal"
LOOT = []
TAGS = ["freeze_immune_entity_types"]

# Debug only: SEAL_POSE=balance previews the head up with the ball on its nose.
POSE = os.environ.get("SEAL_POSE", "")


# -- texture packing (as in otter.py): biggest cubes first, each with a 1 px clear margin -------------
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
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


SIDES = ("front", "back", "left", "right")

# -- palettes ----------------------------------------------------------------------------------------
ADULT = dict(
    coat=["#8c9197", "#888d93", "#90959b", "#8a8f95"],
    back=["#646970", "#5f646b", "#686d74", "#62676e"],
    belly=["#bdbab1", "#c4c1b8", "#b4b1a8", "#c8c5bd"],
    spot=["#3b4046", "#42474d", "#363a40"],
    ring=["#aeb1b3", "#a7aaad"],
    face=["#9a9fa4", "#a2a6aa", "#9499a0"],
    muzzle=["#b3b2ac", "#aaa9a3", "#bab9b3"],
    pad_dot="#5d5b57",
    nose="#1d1b1c",
    nose_hi="#3d3a3b",
    mouth="#4a4644",
    eye="#0d0c0e",
    eye2="#1f1d22",
    glint="#f4f6fa",
    whisker="#ece9e0",
    flipper=["#5f646b", "#585d64", "#666b71"],
    flipper_dk=["#43474d", "#3d4146"],
    claw="#3a3631",
    spots=True,
)

PUP = dict(
    coat=["#f3f1ea", "#ece9e1", "#f7f5f0", "#e8e5dc", "#f0eee7"],
    back=["#ebe8df", "#e4e1d7", "#efece4"],
    belly=["#e2ded3", "#dcd8cc", "#e6e2d8"],
    spot=["#d3cfc3", "#cdc9bc"],                    # only soft fluff shadows, no spots
    ring=["#faf9f5"],
    face=["#f5f3ed", "#eeebe4", "#f8f7f2"],
    muzzle=["#e9e5dc", "#e2ded4"],
    pad_dot="#8f8a80",
    nose="#2a2627",
    nose_hi="#4a4546",
    mouth="#8a837a",
    eye="#0d0c0e",
    eye2="#211e24",
    glint="#ffffff",
    whisker="#d6d1c6",
    flipper=["#c9c6bd", "#c1beb4", "#d0cdc5"],
    flipper_dk=["#a9a59a", "#a29e93"],
    claw="#4a443e",
    spots=False,
)

SNOW = ["#ffffff", "#f6f9fb", "#eef3f6", "#ffffff"]
SNOW_SH = ["#d9e2e8", "#cfd9e0"]


# -- coat --------------------------------------------------------------------------------------------
def coat(P, top_pal="back", grad=0.2, belly_rows=1, spot_rate=1.0):
    """Sleek coat: the back colour on top, the coat grading darker-to-lighter down the sides into
    the pale belly; dark spots (some ringed) for the adult, soft fluffy tufts for the pup."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":
                    col = c.pick(P[top_pal])
                elif c.face == "bottom":
                    col = c.pick(P["belly"])
                else:
                    t = y / max(1, c.h - 1)
                    col = c.pick(P["coat"])
                    if t < 0.3:
                        col = mix(c.pick(P["back"]), col, t / 0.3)
                    if belly_rows and y >= c.h - belly_rows:
                        col = mix(col, c.pick(P["belly"]), 0.65)
                    col = shade(col, 1.03 - grad * 0.15 * t)
                c.set(x, y, col)
        if c.face == "bottom":
            return
        n = c.w * c.h
        if P["spots"]:
            # harbour seal: a scatter of small dark spots and softer mottling, thick along the back
            # and thinning out down the flanks; here and there a spot has a pale ring
            dark = []
            for y in range(c.h):
                fade = 1.0 if c.face == "top" else max(0.0, 1.0 - y / max(1, c.h - 1)) ** 1.3
                if c.face in ("left", "right", "front", "back") and y >= c.h - belly_rows:
                    continue
                for x in range(c.w):
                    r = c.rng.random()
                    density = 0.3 * fade * spot_rate
                    if r < density * 0.4:
                        c.set(x, y, c.pick(P["spot"]))
                        dark.append((x, y))
                    elif r < density:
                        c.set(x, y, mix(c.pick(P["spot"]), c.get(x, y), 0.6))
            for (x, y) in dark:
                if c.rng.random() < 0.3:
                    rx, ry = (x + c.rng.choice((-1, 1)), y) if c.rng.random() < 0.5 else (x, y - 1)
                    if c.inside(rx, ry) and (rx, ry) not in dark:
                        c.set(rx, ry, c.pick(P["ring"]))
        else:
            for _ in range(int(n * 0.12)):               # fluffy: soft shadow under light tufts
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, c.pick(P["spot"]))
                if c.inside(x, y - 1):
                    c.set(x, y - 1, shade(c.pick(P["coat"]), 1.03))
    return p


def ridge_paint(P):
    base = coat(P, belly_rows=0, spot_rate=1.4)

    def p(c):
        base(c)
        if c.face in SIDES:
            for x in range(c.w):
                c.set(x, 0, c.pick(P["back"]))
    return p


def belly_paint(P):
    def p(c):
        c.noise(P["belly"])
        if c.face in ("left", "right", "front", "back"):
            for x in range(c.w):
                c.set(x, 0, mix(c.pick(P["coat"]), c.pick(P["belly"]), 0.5))
        if P["spots"] and c.face == "bottom":
            for _ in range(3):
                c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), mix(c.pick(P["spot"]), c.pick(P["belly"]), 0.5))
    return p


def chest_paint(P):
    base = coat(P, grad=0.1, belly_rows=2, spot_rate=0.5)

    def p(c):
        base(c)
        if c.face == "front":                    # the throat in shadow under the chin
            for x in range(c.w):
                c.set(x, 0, shade(c.get(x, 0), 0.85))
    return p


# -- head --------------------------------------------------------------------------------------------
def head_front(P):
    """6 x 5: forehead on top, two big glossy eyes on the upper corners, cheeks either side of the
    muzzle (which covers columns 1-4 of rows 3-4)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["face"])
                if y == 0:
                    col = mix(c.pick(P["back"]), col, 0.4)
                c.set(x, y, col)
        for ex in (0, 4):
            c.set(ex, 1, P["glint"])
            c.set(ex + 1, 1, P["eye"])
            c.set(ex, 2, P["eye2"])
            c.set(ex + 1, 2, P["eye"])
        c.set(1, 0, shade(c.get(1, 0), 0.85)); c.set(4, 0, shade(c.get(4, 0), 0.85))   # brows
        for x in (2, 3):
            c.set(x, 2, shade(c.pick(P["face"]), 1.05))                # the bridge of the nose
    return p


def head_side(P):
    base = coat(P, belly_rows=1, spot_rate=0.6)

    def p(c):
        base(c)
        # the big eye wraps round the front corner
        c.set(fx(c, 0), 1, P["eye"])
        c.set(fx(c, 0), 2, P["eye"])
        c.set(fx(c, 1), 1, shade(c.get(fx(c, 1), 1), 0.85))
        c.set(fx(c, 1), 2, shade(c.get(fx(c, 1), 2), 0.9))
        c.set(fx(c, 0), 3, c.pick(P["face"]))
        c.set(fx(c, 0), 0, mix(c.pick(P["back"]), c.pick(P["face"]), 0.5))
        # the ear: just a small dark hole behind the eye
        c.set(fx(c, 3), 1, shade(c.pick(P["coat"]), 0.6))
    return p


def head_top(P):
    base = coat(P, spot_rate=0.8)

    def p(c):
        base(c)
        for x in range(c.w):                       # row h-1 = the front edge: the forehead
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(P["face"]), 0.5))
    return p


def crown_paint(P):
    """The dome of the skull: the dark back colour, spotted."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(P["back"]) if c.face == "top" else mix(c.pick(P["back"]), c.pick(P["coat"]), 0.4))
        if P["spots"] and c.face == "top":
            c.set(1, 1, c.pick(P["spot"])); c.set(2, 2, c.pick(P["ring"]))
    return p


def crown_front(P):
    def p(c):
        for x in range(c.w):
            c.set(x, 0, mix(c.pick(P["back"]), c.pick(P["face"]), 0.3))
    return p


def head_bottom(P):
    def p(c):
        c.noise(P["belly"])
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(P["muzzle"]))  # the chin, at the front
    return p


def muzzle_front(P):
    # 4 x 2: whisker pads either side of the dark V nose on top, the mouth line below
    def p(c):
        c.noise(P["muzzle"])
        c.set(1, 0, P["nose"]); c.set(2, 0, P["nose"])
        c.set(0, 0, mix(c.pick(P["muzzle"]), P["pad_dot"], 0.4))
        c.set(3, 0, mix(c.pick(P["muzzle"]), P["pad_dot"], 0.4))
        c.set(1, 1, mix(P["mouth"], c.pick(P["muzzle"]), 0.45))
        c.set(2, 1, mix(P["mouth"], c.pick(P["muzzle"]), 0.6))
        c.set(0, 1, c.pick(P["muzzle"])); c.set(3, 1, c.pick(P["muzzle"]))
    return p


def muzzle_top(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, mix(c.pick(P["face"]), c.pick(P["muzzle"]), 0.5))
        c.set(1, c.h - 1, P["nose_hi"]); c.set(2, c.h - 1, P["nose"])   # the top of the nose
    return p


def muzzle_side(P):
    def p(c):
        c.noise(P["muzzle"])
        for (i, y) in ((0, 0), (1, 1), (1, 0)):   # dotted whisker pads
            c.set(fx(c, i), y, mix(c.pick(P["muzzle"]), P["pad_dot"], 0.55))
        c.set(fx(c, 1), 1, P["mouth"])            # the corner of the mouth
    return p


def muzzle_bottom(P):
    def p(c):
        c.noise([shade(m, 0.9) for m in P["muzzle"]])
    return p


def whiskers(P):
    """Pale whiskers (a flat plane, front and back alike)."""
    def p(c):
        for x in range(c.w):
            c.set(x, 0, P["whisker"])
        outer = 0 if c.face == "front" else c.w - 1
        c.set(outer, 0, shade(P["whisker"], 0.88))
    return p


def ball_paint(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SNOW)
            if c.face == "bottom" or (c.face in SIDES and y == c.h - 1):
                col = c.pick(SNOW_SH)
            c.set(x, y, col)
    if c.face in ("front", "left"):
        c.set(0, 0, "#ffffff")


# -- flippers ----------------------------------------------------------------------------------------
def flipper_paint(P):
    """Front flipper lying flat (3 out x 1 thick x 4 long): darker grey with finger lines and small
    dark claws along the front edge."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["flipper"])
                if c.face == "bottom":
                    col = c.pick(P["flipper_dk"])
                c.set(x, y, col)
        if c.face == "top":
            # col 0 = the outer edge (the flipper reaches toward -x); row h-1 = the front edge
            for y in range(c.h):
                c.set(0, y, shade(c.get(0, y), 0.9))
            for y in range(0, c.h - 1, 2):
                c.set(1, y, c.pick(P["flipper_dk"]))   # finger lines
            c.set(0, c.h - 1, P["claw"])
            c.set(1, c.h - 1, mix(P["claw"], c.pick(P["flipper"]), 0.55))
        elif c.face == "front":
            c.set(0, 0, mix(P["claw"], c.pick(P["flipper"]), 0.3))
    return p


def hind_paint(P):
    """One lobe of the hind flippers (2 wide x 1 x 3 long): dark, webbed, with toe lines."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["flipper"])
                if c.face == "bottom":
                    col = c.pick(P["flipper_dk"])
                c.set(x, y, col)
        if c.face in ("top", "bottom"):
            for x in range(c.w):
                c.set(x, 0, c.pick(P["flipper_dk"]))     # row 0 = the trailing (back) edge
            c.set(0, 1, c.pick(P["flipper_dk"]))
        elif c.face == "back":
            c.fill(c.pick(P["flipper_dk"]))
    return p


def tail_base_paint(P):
    base = coat(P, belly_rows=0, spot_rate=0.5)

    def p(c):
        base(c)
        if c.face == "bottom":
            c.noise(P["flipper_dk"])
    return p


def make(texture_id, P):
    m = Model("seal", 64, 64, seed=3131, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot at the centre (y 20). A fat core (y 17-23, z -4.5..4.5) rounded by a ridge on top,
    # a belly underneath (touching the ground at y 24), a full chest in front and tapering hips.
    body = m.part("body", (0, 20, 0))
    pk.add(body, (-3.5, -3, -4.5), (7, 6, 9), faces(coat(P)))
    pk.add(body, (-2.5, -4, -4), (5, 1, 8), faces(ridge_paint(P)))
    pk.add(body, (-2.5, 3, -4), (5, 1, 8), faces(belly_paint(P)))
    pk.add(body, (-2.5, -2, -5.5), (5, 4, 1), faces(chest_paint(P)))
    pk.add(body, (-2.5, -1, 4.5), (5, 4, 3), faces(coat(P, grad=0.15, spot_rate=0.8)))
    pk.add(body, (-1.5, 3, 4.5), (3, 1, 2), faces(belly_paint(P)))

    # head: round, raised a little in front of the chest; the short muzzle sticks out below the eyes
    head = body.part("head", (0, -1.5, -5))
    pk.add(head, (-2, -5, -3.5), (4, 1, 4), faces(crown_paint(P), front=crown_front(P)))
    pk.add(head, (-3, -4, -4.5), (6, 5, 5), faces(coat(P, spot_rate=0.6), front=head_front(P),
                                                  right=head_side(P), left=head_side(P),
                                                  top=head_top(P), bottom=head_bottom(P)))
    pk.add(head, (-2, -1, -6.5), (4, 2, 2), faces(muzzle_side(P), front=muzzle_front(P),
                                                  top=muzzle_top(P), bottom=muzzle_bottom(P)))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        for wy in (-0.4, 0.4):
            pk.add(head, (-5 if not left else 2, wy, -5.6), (3, 0.4, 0),
                   None if left else faces(whiskers(P)), mirror=left, share="whiskers")
    # the snowball: hidden inside the head at rest (the code moves it onto the nose)
    ball = head.part("ball", (0, -1.5, -2))
    pk.add(ball, (-1, -1, -1), (2, 2, 2), faces(ball_paint), inflate=0.25)

    # front flippers: flat paddles at the sides of the chest, swept back, lying on the ground
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        f = body.part(f"{side}_flipper", (3 * sx, 2.5, -2.5), (0, 0.5 * -sx, 0.12 * sx))
        pk.add(f, (-3 if not left else 0, 0, -2), (3, 1, 4), None if left else faces(flipper_paint(P)),
               mirror=left, share="flipper")

    # tail: the hind flippers held together behind the hips, tipped up a little
    tail = body.part("tail", (0, 1.5, 7.5), (0.25, 0, 0))
    pk.add(tail, (-1.5, -0.5, 0), (3, 1, 2), faces(tail_base_paint(P)))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        pk.add(tail, (-2.5 if not left else 0.5, -0.5, 1.5), (2, 1, 3), None if left else faces(hind_paint(P)),
               mirror=left, share="hind")

    if POSE == "balance":
        m.preview = {"head": [-1.0, 0, 0]}
        m.get("ball").pivot = (0, -1.9, -7.4)

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("seal_pup", PUP).save(geometry=False)
    spawn_egg("seal", "#878c92", "#474c53", accent="#bdbab1")


if __name__ == "__main__":
    build()

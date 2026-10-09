"""Owl: a round, fluffy owl that can be tamed as a pet. A barrel body under a big wide head with a
flat facial disc: huge forward-facing eyes (a glint in each pupil), a small hooked beak between them,
pale "eyebrows" meeting in a V over the beak and a dark rim round the disc. Small feathered ear tufts
lean out from the top corners. The wings lie folded along the sides, the barred primaries crossing
over a short tail; short feathered legs end in fluffy toes with dark talons.
Two looks share the geometry: `owl` is tawny (mottled brown with buff spots and dark streaks, a buff
face, orange eyes, a pale horn beak) and `owl_snowy` is snowy (white with black flecks and bars, a
white face, yellow eyes, a black beak).
The wings hang down at rest; the code spreads them by turning them round z (+zRot lifts the right
wing out, -zRot the left one) and swings each `*_wing_tip` out to the side (xRot about -1.4)."""
import math
import os
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Owl"
LOOT = []
TAGS = ["fall_damage_immune"]

# Debug only: OWL_POSE=fly previews the wings spread.
POSE = os.environ.get("OWL_POSE", "")


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


def _h(x, y, salt):
    """A stable random number per pixel (the same pattern on every variant)."""
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


SIDES = ("front", "back", "left", "right")

# -- palettes ----------------------------------------------------------------------------------------
TAWNY = dict(
    base=["#8b5e3c", "#82573a", "#946645", "#7d5335", "#8f6140"],
    dark=["#4f331f", "#5a3b24", "#46301d"],
    light=["#c99f6f", "#d4ad7c", "#bf9566"],
    under=["#c4a074", "#bb966b", "#caa77c"],          # underwing and belly: warm buff
    chest=["#d6b789", "#dcbf92", "#cfae80", "#d9bb8d"],
    chest_mark=["#6a4428", "#5e3c23", "#77502f"],
    face=["#dcbf93", "#e3c89e", "#d6b88a"],
    face_dk=["#c09c6f", "#b8946a"],
    rim="#4a2f1c",
    rim2="#6b4527",
    brow=["#efdcb9", "#f3e3c3"],
    iris="#f0911f",
    iris_dk="#c86a12",
    pupil="#120b07",
    glint="#fffbea",
    beak="#e3cf8f",
    beak_dk="#7d6b45",
    foot=["#dcc29a", "#d2b78d", "#e4cca6"],
    talon="#1d1814",
    talon_hi="#4a423b",
    prim_light=["#c19566", "#b98d5e"],
    prim_dark=["#5c3c24", "#523520"],
    tuft_tip="#3c2617",
    marks="streaks",
)

SNOWY = dict(
    base=["#f4f4f0", "#eeeeea", "#f8f8f5", "#e9e9e4", "#f1f1ec"],
    dark=["#4b4743", "#57524d", "#433f3b"],
    light=["#ffffff", "#fbfbf9"],
    under=["#ededE9".lower(), "#e5e5e0", "#f2f2ee"],
    chest=["#f7f7f3", "#f1f1ed", "#fbfbf8", "#ececE7".lower()],
    chest_mark=["#6b6661", "#5d5853", "#77726c"],
    face=["#fbfbf9", "#f5f5f1", "#ffffff"],
    face_dk=["#e3e3de", "#dadad5"],
    rim="#c9c9c3",
    rim2="#dcdcd6",
    brow=["#ffffff", "#fdfdfb"],
    iris="#f7d21e",
    iris_dk="#d9a90f",
    pupil="#0f0f10",
    glint="#ffffff",
    beak="#e9e9e4",
    beak_dk="#1c1c1d",
    foot=["#f6f6f2", "#efefeb", "#fafaf7"],
    talon="#1a1a1b",
    talon_hi="#4a4a4c",
    prim_light=["#f2f2ee", "#e8e8e3"],
    prim_dark=["#5a5550", "#4c4843"],
    tuft_tip="#cfcfc9",
    marks="flecks",
)


# -- plumage -----------------------------------------------------------------------------------------
def plumage(P, top=1.05, grad=0.16, density=1.0, under=None):
    """Soft owl feathers. Side faces darken toward the bottom; the top is lighter. Tawny gets dark
    shaft streaks and buff spots, snowy gets small black bars (flecks) on white."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["base"])
                if c.face == "top":
                    col = shade(col, top)
                elif c.face == "bottom":
                    col = c.pick(under or P["under"])
                elif c.h > 1:
                    col = shade(col, 1.03 - grad * y / (c.h - 1))
                c.set(x, y, col)
        if c.face == "bottom":
            return
        n = c.w * c.h
        if P["marks"] == "streaks":
            for _ in range(int(n * 0.11 * density) + 1):          # dark shaft streaks, 1x2
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, c.pick(P["dark"]))
                if c.inside(x, y + 1) and c.face != "top":
                    c.set(x, y + 1, shade(c.pick(P["dark"]), 1.15))
            for _ in range(int(n * 0.07 * density) + 1):          # buff feather spots
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, c.pick(P["light"]))
        else:
            # snowy: rows of short dark bars, staggered row to row, like the barring on a snowy owl
            for y in range(1, c.h, 3):
                off = (y // 3) % 2 * 2 + c.rng.randrange(2)
                for x in range(off, c.w, 4):
                    if c.rng.random() < 0.7 * density:
                        c.set(x, y, c.pick(P["dark"]))
                        if c.inside(x + 1, y) and c.rng.random() < 0.6:
                            c.set(x + 1, y, mix(c.pick(P["dark"]), c.get(x + 1, y), 0.45))
    return p


def body_paint(P):
    base = plumage(P)

    def p(c):
        base(c)
        if c.face == "front":                    # the throat under the head: chest colour, shadowed
            for y in range(c.h):
                for x in range(c.w):
                    if 0 < x < c.w - 1:
                        c.set(x, y, shade(c.pick(P["chest"]), 0.9 if y == 0 else 0.97))
        elif c.face in ("left", "right"):        # the belly wraps a little round the front corner
            for y in range(1, c.h):
                c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), c.pick(P["chest"]), 0.6))
        elif c.face == "bottom":
            c.noise(P["under"])
            for x in range(c.w):
                c.set(x, c.h - 1, shade(c.pick(P["chest"]), 0.92))   # row h-1 = the front edge
    return p


def chest_paint(P):
    """The fluffy chest bulging out under the face: buff (or white) with vertical dark streaks
    (tawny) or sparse chevron flecks (snowy); a soft shadow under the chin."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["chest"])
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.0 - 0.1 * y / (c.h - 1))
                elif c.face == "bottom":
                    col = shade(c.pick(P["chest"]), 0.88)
                c.set(x, y, col)
        if c.face == "front":
            for x in range(c.w):
                c.set(x, 0, shade(c.pick(P["chest"]), 0.86))        # the shadow under the head
            if P["marks"] == "streaks":
                for x in (0, 2, 4):
                    for y in range(1, c.h):
                        if (y + x) % 3 != 0 or c.rng.random() < 0.3:
                            c.set(x, y, mix(c.get(x, y), c.pick(P["chest_mark"]), 0.8))
            else:                                                    # a few faint chevrons
                for (x, y) in ((1, 2), (3, 3), (0, 3)):
                    if c.inside(x, y):
                        c.set(x, y, mix(c.pick(P["chest_mark"]), c.get(x, y), 0.35))
        elif c.face in ("left", "right") and P["marks"] == "streaks":
            for y in range(1, c.h, 2):
                c.set(0, y, mix(c.get(0, y), c.pick(P["chest_mark"]), 0.5))
    return p


def rump_paint(P):
    base = plumage(P, density=0.8)

    def p(c):
        base(c)
        if c.face == "back":                     # the wingtips cross over here: darker
            for x in range(c.w):
                c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.85))
    return p


# -- head --------------------------------------------------------------------------------------------
# The facial disc, 9 x 6: two huge round eyes (an iris ring round a 2x2 pupil with a glint) with
# the beak between them. r rim, f face, F darker face, w brow, I/i iris (light/dark), p pupil,
# g glint, b behind the beak.
FACE = [
    "FffwwwffF",
    "rIIFwFIIr",
    "IgpIbIgpI",
    "IppIbIppI",
    "riiFfFiir",
    "FfffffffF",
]


def head_front(P):
    def p(c):
        for y, row in enumerate(FACE):
            for x, ch in enumerate(row):
                col = {"r": P["rim"], "R": P["rim2"], "I": P["iris"], "i": P["iris_dk"],
                       "p": P["pupil"], "g": P["glint"]}.get(ch)
                if col is None:
                    col = c.pick({"f": P["face"], "F": P["face_dk"], "w": P["brow"], "b": P["face_dk"]}[ch])
                c.set(x, y, col)
    return p


# The ruff round the facial disc, 11 x 7, a flat cut-out plane just in front of the face: an arc
# over the brow, a 1 px rim sticking out past each side of the head and rounded corners.
RUFF = [
    "...rRRRr...",
    ".r.......r.",
    "r.........r",
    "d.........d",
    "d.........d",
    "r.........r",
    ".r.......r.",
]


def ruff_paint(P):
    def p(c):
        for y, row in enumerate(RUFF):
            for x, ch in enumerate(row):
                if ch == ".":
                    c.clear(x, y)
                elif ch == "d":
                    c.set(x, y, mix(P["face_dk"][0], P["rim2"], 0.45))
                else:
                    c.set(x, y, P["rim"] if ch == "r" else P["rim2"])
    return p


def head_side(P):
    base = plumage(P, grad=0.12)

    def p(c):
        base(c)
        for y in range(c.h):                     # the disc rim curls round the front edge
            c.set(fx(c, 0), y, P["rim"] if 0 < y < c.h - 1 else P["rim2"])
            c.set(fx(c, 1), y, mix(c.get(fx(c, 1), y), c.pick(P["face_dk"]), 0.55))
    return p


def head_back(P):
    base = plumage(P, grad=0.14)

    def p(c):
        base(c)
        if P["marks"] == "streaks":              # a paler nape collar at the bottom
            for x in range(c.w):
                if (x % 2 == 0) or c.rng.random() < 0.3:
                    c.set(x, c.h - 1, c.pick(P["light"]))
    return p


def head_top(P):
    base = plumage(P, top=1.08, density=1.3)

    def p(c):
        base(c)
        for x in range(c.w):                      # row h-1 = the front edge, over the brow
            c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.92))
    return p


def head_bottom(P):
    def p(c):
        c.noise(P["face_dk"])
        for x in range(c.w):
            c.set(x, 0, c.pick(P["base"]))       # row 0 = the back edge
    return p


def crown_paint(P):
    base = plumage(P, top=1.1, density=1.2)

    def p(c):
        base(c)
        if c.face == "front":                     # the forehead above the disc: soft, a pale tuft
            for x in range(c.w):                  # in the middle where the brows meet
                c.set(x, 0, shade(c.pick(P["base"]), 0.9))
            c.set(c.w // 2, 0, c.pick(P["brow"]))
    return p


def beak_paint(P):
    def p(c):
        c.fill(P["beak"])
        if c.face == "front":
            c.set(0, 0, shade(P["beak"], 1.15) if P["marks"] == "streaks" else P["beak"])
            c.set(0, c.h - 1, P["beak_dk"])       # the hook tip
        elif c.face in ("left", "right"):
            c.set(0, c.h - 1, P["beak_dk"])
        elif c.face == "bottom":
            c.fill(P["beak_dk"])
    return p


def tuft_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["base"])
                if c.face in SIDES:
                    col = shade(col, 0.95 + 0.05 * y)
                c.set(x, y, col)
        if c.face in ("front", "back"):
            c.set(0, 0, P["tuft_tip"])            # dark feather tips; the outer edge is darker
            if c.inside(1, 1):
                c.set(1, 1, c.pick(P["light"]))
        elif c.face == "top":
            c.set(0, 0, P["tuft_tip"])
    return p


# -- wings, tail, legs -------------------------------------------------------------------------------
def wing_paint(P):
    """The folded wing, seen from outside (right face; the left wing mirrors it). Top rows are the
    shoulder: base plumage with a row of pale scapular spots; lower down the coverts carry rows of
    bars; the bottom row is the flight-feather edge. The inner face is the pale underwing."""
    def p(c):
        if c.face in ("left",):                   # inner face: the underwing (seen in flight)
            for y in range(c.h):
                for x in range(c.w):
                    col = c.pick(P["under"])
                    if (x + y) % 3 == 0:
                        col = shade(col, 0.9)
                    c.set(x, y, col)
            return
        if c.face == "bottom":                    # the trailing edge when spread
            for x in range(c.w):
                c.set(x, 0, c.pick(P["prim_dark"]) if x % 2 else c.pick(P["prim_light"]))
            return
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["base"])
                if c.face == "right" and c.h > 1:
                    col = shade(col, 1.04 - 0.12 * y / (c.h - 1))
                c.set(x, y, col)
        if c.face != "right":
            if c.face == "top":
                for x in range(c.w):
                    c.set(x, 0, c.pick(P["light"]) if x % 2 == 0 else c.pick(P["base"]))
            return
        # outer face: shoulder spots on row 1, two rows of covert bars, flight-feather edge
        for i in range(c.w):
            x = fx(c, i)
            if i % 2 == 1 and P["marks"] == "streaks":
                c.set(x, 1, c.pick(P["light"]))
            if P["marks"] == "streaks":
                c.set(x, 0, c.pick(P["dark"]) if c.rng.random() < 0.3 else c.get(x, 0))
            k = (i + 1) % 3
            c.set(x, 2, c.pick(P["dark"]) if k == 0 else c.get(x, 2))
            c.set(x, 3, c.pick(P["light"]) if k == 1 else (c.pick(P["dark"]) if k == 2 else c.get(x, 3)))
            c.set(x, c.h - 1, c.pick(P["prim_dark"]) if i % 2 == 0 else c.pick(P["prim_light"]))
        if P["marks"] == "flecks":                # snowy: white with neat rows of short bars
            for i in range(c.w):
                for y in range(c.h - 1):
                    c.set(fx(c, i), y, c.pick(P["base"]))
            for y, off in ((1, 0), (3, 2)):
                for i in range(off, c.w, 3):
                    c.set(fx(c, i), y, c.pick(P["dark"]))
                    if i + 1 < c.w:
                        c.set(fx(c, i + 1), y, mix(c.pick(P["dark"]), c.pick(P["base"]), 0.5))
    return p


def tip_paint(P):
    """Folded primaries crossing back over the tail: barred light and dark, darker at the tips
    (the back). Right face is the outside; the left wing mirrors it."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face in ("right", "left"):
                    i = c.w - 1 - x if c.face == "right" else x       # 0 = front
                    band = (i + y) % 3
                    col = c.pick(P["prim_light"]) if band == 0 else c.pick(P["prim_dark"])
                    if band == 1:
                        col = mix(col, c.pick(P["base"]), 0.5)
                    if c.face == "left":                               # the underside: paler
                        col = mix(col, c.pick(P["under"]), 0.6)
                    if i == c.w - 1:
                        col = shade(col, 0.8)                          # the tip
                elif c.face == "top":
                    col = c.pick(P["prim_dark"]) if (y % 2) else c.pick(P["prim_light"])
                elif c.face == "bottom":
                    col = c.pick(P["under"])
                elif c.face == "back":
                    col = shade(c.pick(P["prim_dark"]), 0.85)
                else:
                    col = c.pick(P["base"])
                c.set(x, y, col)
    return p


def tail_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "top":                # row 0 = the tip (back); dark bars across
                    col = c.pick(P["prim_dark"]) if y % 2 == 0 else c.pick(P["prim_light"])
                elif c.face == "bottom":
                    col = c.pick(P["under"])
                elif c.face == "back":
                    col = shade(c.pick(P["prim_dark"]), 0.9) if x % 2 else c.pick(P["prim_light"])
                else:
                    col = c.pick(P["base"])
                c.set(x, y, col)
    return p


def leg_paint(P):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["foot"])
                if c.face in SIDES:
                    col = shade(col, 0.96 - 0.06 * y)
                c.set(x, y, col)
        for _ in range(2):                         # fluffy: a few lighter tufts
            c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), shade(c.pick(P["foot"]), 1.06))
    return p


def toes_paint(P):
    """Feathered toes with dark curved talons poking out in front."""
    def p(c):
        c.noise(P["foot"])
        if c.face == "front":
            c.set(0, 0, P["talon"]); c.set(c.w - 1, 0, P["talon"])
        elif c.face == "top":                      # row h-1 = the front edge: talon tips
            c.set(0, c.h - 1, mix(c.pick(P["foot"]), P["talon"], 0.6))
            c.set(c.w - 1, c.h - 1, mix(c.pick(P["foot"]), P["talon"], 0.6))
        elif c.face == "bottom":
            c.noise([shade(f, 0.85) for f in P["foot"]])
        elif c.face in SIDES:
            for x in range(c.w):
                c.set(x, 0, shade(c.get(x, 0), 0.9))
    return p


TIP_REST = -0.35     # folded primaries slope down toward the tail


def make(texture_id, P):
    m = Model("owl", 64, 64, seed=3636, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot in the middle of the barrel (y 20). Core y 17.5-22.5, a fluffy chest bulging out
    # in front (z -4) and a rounded rump behind (z 4).
    body = m.part("body", (0, 20, 0))
    pk.add(body, (-3.5, -2.5, -3), (7, 5, 6), faces(body_paint(P)))
    pk.add(body, (-2.5, -2, -4), (5, 4, 1), faces(chest_paint(P)))
    pk.add(body, (-2.5, -2, 3), (5, 3, 1), faces(rump_paint(P)))

    # head: big and wide, no neck; pivot at its centre so it can swivel round. Head y 11.5-17.5,
    # z -4..2; a narrower crown rounds the top (y 10.5) and the hooked beak sits between the eyes.
    head = body.part("head", (0, -2.5, -1))
    pk.add(head, (-4.5, -6, -3), (9, 6, 6), faces(None, front=head_front(P), right=head_side(P),
                                                  left=head_side(P), back=head_back(P), top=head_top(P),
                                                  bottom=head_bottom(P)))
    pk.add(head, (-3.5, -7, -2.5), (7, 1, 5), faces(crown_paint(P)))
    pk.add(head, (-0.5, -4, -4), (1, 2, 1), faces(beak_paint(P)))
    pk.add(head, (-5.5, -7, -3.05), (11, 7, 0), faces(None, front=ruff_paint(P), back=ruff_paint(P)))
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        t = head.part(f"{side}_tuft", (3.2 * sx, -6.6, -1), (0.15, 0, 0.55 * sx))
        pk.add(t, (-1, -2, -0.5), (2, 2, 1), None if left else faces(tuft_paint(P)),
               mirror=left, share="tuft")

    # wings: hinged at the shoulders, hanging folded down the sides (y 18-22). Each tip (the
    # primaries) runs back from the lower rear of the wing over the tail.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        w = body.part(f"{side}_wing", (3.5 * sx, -2, -1))
        pk.add(w, (-1 if not left else 0, 0, -2), (1, 4, 6), None if left else faces(wing_paint(P)),
               mirror=left, share="wing")
        tip = w.part(f"{side}_wing_tip", (0, 3.5, 2.5), (TIP_REST, 0, 0))
        pk.add(tip, (-1 if not left else 0, -1.5, 0), (1, 2, 4), None if left else faces(tip_paint(P)),
               mirror=left, share="tip")

    # tail: short, at the back bottom, sloping down behind
    tail = body.part("tail", (0, 1, 3), (-0.6, 0, 0))
    pk.add(tail, (-2, -0.5, 0), (4, 1, 3), faces(tail_paint(P)))

    # legs: short feathered "trousers" under the belly and fluffy toes with talons on the ground
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        lg = body.part(f"{side}_leg", (1.5 * sx, 2, -0.5))
        pk.add(lg, (-1, 0, -1), (2, 1, 2), None if left else faces(leg_paint(P)), mirror=left, share="leg")
        pk.add(lg, (-1.5, 1, -2), (3, 1, 3), None if left else faces(toes_paint(P)), mirror=left, share="toes")

    if POSE == "fly":
        m.preview = {"right_wing": [0, 0, 1.45], "left_wing": [0, 0, -1.45],
                     "right_wing_tip": [-1.4, 0, 0], "left_wing_tip": [-1.4, 0, 0]}

    pk.apply()
    return m


def build():
    make(None, TAWNY).save()
    make("owl_snowy", SNOWY).save(geometry=False)
    spawn_egg("owl", "#8b5e3c", "#dcbf93", accent="#f0911f")


if __name__ == "__main__":
    build()

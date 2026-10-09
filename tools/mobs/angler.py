"""Angler: a deep-sea anglerfish that lurks in the dark of deep oceans. A big lumpy, rounded fish in
charcoal and blue-black skin with faint pale speckles and a slightly lighter belly. A huge undershot
jaw juts past the upper lip, both lined with long needle teeth around a dark red-black mouth. Small
pale milky eyes sit high on the head, the fins are ragged with lighter torn edges, and a long thin
stalk rises from the forehead and arches forward over the mouth, ending in a glowing pale-yellow
lure with a mint halo. The jaw hinges at the back of the mouth; the code drops it open (+xRot)."""
import math
import random

from mobkit import Model, faces, spawn_egg, shade, mix, hexc
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Angler"
LOOT = [item("cod", 0, 2), item("glow_ink_sac", chance=0.3, looting=False, player_only=True), item("prismarine_crystals", chance=0.1, looting=False)]
TAGS = ["can_breathe_under_water", "aquatic", "sensitive_to_impaling"]


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


def _h(a, y, salt):
    """Deterministic noise, so both faces of a flat plane get the same pixels."""
    return random.Random(a * 7919 + y * 104729 + salt * 15485863).random()


# -- palette -----------------------------------------------------------------------------------------
SKIN = ["#2a2a33", "#23232b", "#33323d", "#2a2a33", "#23232b"]
SKIN_DK = "#1b1b22"
LUMP = ["#3a3946", "#3f3e4c"]
SPECK = ["#5a596c", "#4e4d5f", "#646378"]
BELLY = ["#3b3a46", "#413f4d", "#373641"]
LIP = ["#403f4d", "#474655", "#3c3b48"]
MOUTH = ["#3a1414", "#331111", "#421818"]
THROAT = ["#1f0909", "#260b0b"]
GUM = ["#5a2226", "#4f1e20"]
TOOTH = "#e8e4d8"
TOOTH_TIP = "#f6f3ea"
TOOTH_BASE = "#c9c4b4"
EYE = "#cfd6d2"
EYE_SH = "#aab4b0"
EYE_HI = "#f2f6f3"
PUPIL = "#68736f"
SOCKET = "#121216"
FIN = ["#34333f", "#3a3946", "#302f3a"]
FIN_RAY = "#1c1c24"
FIN_EDGE = ["#5f5e73", "#6a6982", "#56556a"]
STALK = ["#3b3a48", "#363542", "#413f4e"]
LURE = "#fff6a8"
LURE_HOT = "#fffce0"
HALO = ["#b9ffcf", "#7ff7d0"]

SIDES = ("front", "back", "left", "right")

JAW_REST = 0.0       # closed at rest: the lower needles stand in front of the upper lip


def soft_glow(c, x, y, col, k):
    """col on the base texture and a dimmed copy on the emissive layer: a faint glow."""
    if not c.inside(x, y):
        return
    c.set(x, y, col)
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), shade(col, k))


def light(c, x, y, col, base=0.22):
    """A pixel that IS light: full colour on the emissive layer over a dim base, so the additive glow
    shows the true colour in the dark instead of washing out to white in daylight."""
    if not c.inside(x, y):
        return
    c.set(x, y, shade(col, base))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), hexc(col))


# -- skin --------------------------------------------------------------------------------------------
def skin(top=1.12, grad=0.3, lumps=0.06, speck=0.035, belly_rows=0):
    """Blue-black skin: lighter on top, darker down the sides, raised lumps (a lighter pixel over a
    shadow pixel), faint pale speckles. Bottom faces are the lighter belly."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    col = c.pick(BELLY)
                elif c.face == "top":
                    col = shade(c.pick(SKIN), top)
                else:
                    col = shade(c.pick(SKIN), 1.1 - grad * (y / max(1, c.h - 1)))
                    if belly_rows and y >= c.h - belly_rows:
                        col = mix(col, c.pick(BELLY), 0.7)
                c.set(x, y, col)
        for y in range(c.h):
            for x in range(c.w):
                r = c.rng.random()
                if r < lumps:
                    c.set(x, y, c.pick(LUMP))
                    if c.face in SIDES and c.inside(x, y + 1):
                        c.set(x, y + 1, SKIN_DK)
                elif r < lumps + speck:
                    c.set(x, y, c.pick(SPECK))
    return p


def eye_side(c):
    """A small milky eye at the front top corner of a side face, with a dark socket around it."""
    a, b = fx(c, 0), fx(c, 1)
    c.set(a, 0, EYE); c.set(b, 0, EYE_HI)
    c.set(a, 1, PUPIL); c.set(b, 1, EYE_SH)
    c.set(fx(c, 2), 0, SOCKET); c.set(fx(c, 2), 1, SOCKET)
    c.set(a, 2, SOCKET); c.set(b, 2, shade(SOCKET, 1.4))


def brow(c):
    if c.face == "top":
        c.noise(LUMP)
    elif c.face == "bottom":
        c.fill(SOCKET)
    else:
        c.noise([shade(s, 0.95) for s in SKIN])
        if c.face == "front":
            c.set(0, 0, c.pick(LUMP))


def lump(c):
    if c.face == "top":
        c.set(0, 0, c.pick(SPECK))
    elif c.face == "bottom":
        c.set(0, 0, SKIN_DK)
    else:
        c.set(0, 0, c.pick(LUMP) if c.rng.random() < 0.5 else c.pick(SKIN))


def head_side(c):
    skin(grad=0.32)(c)
    eye_side(c)
    for i in range(8):                      # the long mouth line running back to the hinge
        c.set(fx(c, i), c.h - 1, mix(c.pick(LIP), MOUTH[0], 0.6) if i < 7 else c.pick(LIP))


def head_front(c):
    skin(grad=0.2, lumps=0.04)(c)
    for x in (0, c.w - 1):                  # the eyes just wrap round the corners
        c.set(x, 0, EYE)
        c.set(x, 1, PUPIL)
        c.set(x, 2, SOCKET)
    c.set(1, 0, SOCKET); c.set(c.w - 2, 0, SOCKET)
    c.set(1, 1, SOCKET); c.set(c.w - 2, 1, SOCKET)
    for x in range(c.w):                    # thick upper lip over a dark mouth slit
        c.set(x, c.h - 2, c.pick(LIP))
        c.set(x, c.h - 1, c.pick(MOUTH) if 0 < x < c.w - 1 else c.pick(LIP))


def head_bottom(c):
    """Underside of the head = the roof of the mouth (rows 0-1, behind the hinge, are belly)."""
    for y in range(c.h):
        for x in range(c.w):
            if y < 2:
                col = c.pick(BELLY)
            elif x in (0, c.w - 1):
                col = c.pick(LIP)
            elif y == c.h - 1:
                col = c.pick(GUM)
            elif y < 4:
                col = c.pick(THROAT)
            else:
                col = c.pick(MOUTH)
                if x % 3 == 1 and y % 2 == 0:
                    col = shade(col, 1.25)          # ridged palate
            c.set(x, y, col)


def jaw_top(c):
    """Floor of the mouth: dark red, black down the throat, a lip rim round the front and sides."""
    for y in range(c.h):
        for x in range(c.w):
            if x in (0, c.w - 1) or y == c.h - 1:
                col = c.pick(LIP)
            elif y == c.h - 2:
                col = mix(c.pick(MOUTH), THROAT[0], 0.5)      # the dark gap behind the lower teeth
            elif y < 3:
                col = c.pick(THROAT)
            else:
                col = c.pick(MOUTH)
                if x in (1, c.w - 2):
                    col = c.pick(GUM)
            c.set(x, y, col)


def jaw_skin(c):
    skin(grad=0.35, lumps=0.05)(c)
    if c.face in ("front", "left", "right"):
        for x in range(c.w):
            c.set(x, 0, c.pick(LIP))        # a pale-ish lower lip along the top edge


def tooth_row(heights, up=True):
    """A flat plane of needle teeth (cutout). heights[i] = tooth length in column i, counted from
    the mob's right (front/back planes) or from the front (side planes)."""
    def p(c):
        n = len(heights)
        for x in range(c.w):
            if c.face in ("front", "right"):
                i = x if c.face == "front" else c.w - 1 - x
            else:
                i = c.w - 1 - x if c.face == "back" else x
            hgt = heights[i % n]
            for y in range(c.h):
                k = c.h - 1 - y if up else y          # 0 at the root of the tooth
                if k >= hgt:
                    c.clear(x, y)
                elif k == 0:
                    c.set(x, y, TOOTH_BASE)
                elif k == hgt - 1:
                    c.set(x, y, TOOTH_TIP)
                else:
                    c.set(x, y, TOOTH)
    return p


# -- fins: hand-drawn masks. '.' = cut out, '#' membrane, 'r' ray, 'e' pale ragged edge -------------
def fin(mask, salt):
    """A flat fin. mask rows top to bottom, columns from the fin's base (front) to its trailing edge.
    Works on side planes (right/left) and on top planes."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                a = c.w - 1 - x if c.face == "right" else x
                ch = mask[y][a] if y < len(mask) and a < len(mask[0]) else "."
                r = _h(a, y, salt)
                if ch == ".":
                    c.clear(x, y)
                    continue
                if ch == "r":
                    col = FIN_RAY
                elif ch == "e":
                    col = FIN_EDGE[int(r * 3) % 3]
                else:
                    col = FIN[int(r * 3) % 3]
                    if r > 0.8:
                        col = shade(col, 1.2)
                c.set(x, y, col)
    return p


PECTORAL = [
    "...e.",
    "..r#e",
    "rr#re",
    "#r#r.",
    "rr#re",
    "..e#e",
]
TAIL_FAN = [
    "....e.",
    "...e#e",
    "..e#re",
    "rr#r#e",
    "#rrree",
    "#rrre.",
    "rr#r#e",
    "..e#re",
    "...e#e",
    "....e.",
]
DORSAL = [
    ".e...",
    ".re.e",
    "err.r",
    "rr#r#",
]
FINLET_UP = [
    ".e",
    "re",
]
FINLET_DOWN = [
    "re",
    ".e",
]


# -- lure ------------------------------------------------------------------------------------------
def stalk(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(STALK)
            if c.face == "top":
                col = shade(col, 1.15)
            c.set(x, y, col)


def stalk_arm(c):
    """The arm reaching forward: the last two pixels toward the tip glow faintly."""
    stalk(c)
    if c.face in ("left", "right"):
        soft_glow(c, fx(c, 0), 0, mix(STALK[0], HALO[1], 0.55), 0.35)
        soft_glow(c, fx(c, 1), 0, mix(STALK[0], HALO[1], 0.3), 0.2)
    elif c.face in ("top", "bottom"):
        soft_glow(c, 0, c.h - 1, mix(STALK[0], HALO[1], 0.55), 0.35)
        soft_glow(c, 0, c.h - 2, mix(STALK[0], HALO[1], 0.3), 0.2)
    elif c.face == "front":
        soft_glow(c, 0, 0, mix(STALK[0], HALO[1], 0.6), 0.4)


def thread(c):
    for y in range(c.h):
        for x in range(c.w):
            light(c, x, y, mix(HALO[1], STALK[0], 0.35 - 0.3 * y / max(1, c.h - 1)), base=0.4)


def bulb(c):
    """The glowing lure: a hot pale-yellow core, yellow-mint edges, mint halo corners."""
    for y in range(c.h):
        for x in range(c.w):
            corner = x in (0, c.w - 1) and y in (0, c.h - 1)
            edge = x in (0, c.w - 1) or y in (0, c.h - 1)
            if corner:
                col = HALO[0] if c.face == "top" or (c.face != "bottom" and y == 0) else HALO[1]
            elif edge:
                col = mix(LURE, HALO[0], 0.25)
            else:
                col = LURE
            light(c, x, y, col)


def build():
    m = Model("angler", 64, 64, seed=6060)
    pk = Pack(m)

    # body: pivot y 17. Stacked slabs round it off: dome y 11, top slab y 12, the head y 13-19
    # (12 wide), a belly bulge behind the jaw and a narrower rump tapering into the tail.
    body = m.part("body", (0, 17, 0))
    pk.add(body, (-4, -6, -4), (8, 1, 6), faces(skin(top=1.16, lumps=0.1)))
    pk.add(body, (-5, -5, -5), (10, 1, 9), faces(skin(top=1.14, lumps=0.08)))
    pk.add(body, (-6, -4, -6), (12, 6, 10), faces(skin(), front=head_front, right=head_side,
                                                  left=head_side, bottom=head_bottom))
    pk.add(body, (-4, -3, 4), (8, 5, 2), faces(skin(grad=0.35)))
    pk.add(body, (-5, 2, 2), (10, 2, 3), faces(skin(grad=0.2, belly_rows=1)))
    # fat cheeks bulging over the corners of the mouth (a dark notch of mouth line shows under them)
    pk.add(body, (-7, -3, -4), (1, 4, 5), faces(skin(grad=0.3)), share="cheek")
    pk.add(body, (6, -3, -4), (1, 4, 5), None, mirror=True, share="cheek")
    # heavy brows over the eyes (they raise the head's front corners) and a few warty lumps on top
    pk.add(body, (-6, -5, -6), (2, 1, 1), faces(brow), share="brow")
    pk.add(body, (4, -5, -6), (2, 1, 1), None, mirror=True, share="brow")
    for (x, z) in ((-3, -1), (1, 0), (2, -3)):
        pk.add(body, (x, -7, z), (1, 1, 1), faces(lump), share="lump")
    # upper teeth hang from the roof of the mouth (hidden inside the jaw while it is shut)
    # (front and side rows sit between the lower teeth, so the two rows interlock when it bites)
    pk.add(body, (-5.5, 2, -5.5), (11, 3, 0),
           faces(tooth_row([2, 0, 3, 0, 0, 2, 0, 0, 3, 0, 2], up=False)))
    pk.add(body, (-5.5, 2, -5.5), (0, 3, 4), faces(tooth_row([0, 2, 0, 3], up=False)),
           share="upper_side_teeth")
    pk.add(body, (5.5, 2, -5.5), (0, 3, 4), None, mirror=True, share="upper_side_teeth")

    # jaw: hinge at the back of the mouth. 14 wide (wider than the head) and 2 px further forward,
    # with a heavy chin under it and needle teeth standing up in front of the upper lip.
    jaw = body.part("jaw", (0, 2, 2), (JAW_REST, 0, 0))
    pk.add(jaw, (-7, 0, -10), (14, 3, 10), faces(jaw_skin, top=jaw_top))
    pk.add(jaw, (-6, 3, -9), (12, 1, 8), faces(skin(grad=0.1, lumps=0.04)))
    pk.add(jaw, (-6.5, -3, -9.5), (13, 3, 0),
           faces(tooth_row([3, 0, 2, 0, 0, 3, 0, 3, 0, 0, 2, 0, 3])))
    pk.add(jaw, (-6.5, -3, -9.5), (0, 3, 4), faces(tooth_row([0, 3, 0, 2])), share="lower_side_teeth")
    pk.add(jaw, (6.5, -3, -9.5), (0, 3, 4), None, mirror=True, share="lower_side_teeth")

    # lure: a thin stalk from the forehead, leaning forward, with an arm reaching out over the mouth;
    # the bulb hangs from the tip (its rotation cancels the stalk's lean so it hangs straight)
    lean = 0.5
    stalk_p = body.part("lure_stalk", (0, -6, -3), (lean, 0, 0))
    pk.add(stalk_p, (-0.5, -6, -0.5), (1, 6, 1), faces(stalk))
    pk.add(stalk_p, (-0.5, -7, -5.5), (1, 1, 6), faces(stalk_arm))
    lure = stalk_p.part("lure", (0, -6.5, -5), (-lean, 0, 0))
    pk.add(lure, (-0.5, 0.5, -0.5), (1, 2, 1), faces(thread))
    pk.add(lure, (-1.5, 2.5, -1.5), (3, 3, 3), faces(bulb))

    # pectoral fins: ragged fans on the flanks behind the cheeks, splayed out and back
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        f = body.part(side + "_fin", (6 * sx, 0, 1.5), (0, 0.6 * sx, -0.2 * sx))
        pk.add(f, (0, -3, 0), (0, 6, 5), None if left else faces(fin(PECTORAL, 1)), mirror=left,
               share="pectoral")

    # dorsal fin on the back, behind the lure
    top = body.part("top_fin", (0, -5, 1.5), (-0.2, 0, 0))
    pk.add(top, (0, -3, 0), (0, 4, 5), faces(fin(DORSAL, 2)))

    # tail: a short tapering stem with two finlets, then a ragged vertical fan
    tail = body.part("tail", (0, -1, 6))
    pk.add(tail, (-2, -2, 0), (4, 4, 2), faces(skin(grad=0.35, lumps=0.05)))
    pk.add(tail, (0, -4, 0), (0, 2, 2), faces(fin(FINLET_UP, 3)))
    pk.add(tail, (0, 2, 0), (0, 2, 2), faces(fin(FINLET_DOWN, 4)))
    fan = tail.part("tail_fin", (0, 0, 2))
    pk.add(fan, (0, -5, 0), (0, 10, 6), faces(fin(TAIL_FAN, 5)))

    pk.apply()
    m.save()
    spawn_egg("angler", "#2a2a33", "#fff6a8", accent="#e8e4d8")


if __name__ == "__main__":
    build()

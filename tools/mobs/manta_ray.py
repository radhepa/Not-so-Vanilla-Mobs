"""Manta Ray: a great oceanic manta, almost three blocks from wingtip to wingtip. A broad, thin
diamond: inky black on top with a pale chevron patch on each shoulder (the black "T" of the head and
spine between them), a gentle dome over the body, white underneath with dark-edged wings, five gill
slits a side and a freckling of dark spots on the belly. A wide square mouth at the front, two curled
cephalic fins either side of it, small eyes behind them, a little dorsal fin and a long whip tail.

The disc is painted as one surface: every face pixel is mapped back to its point in model space, so
the chevrons and the wing margins run on unbroken from the body over the wings to the tips.
The wings are thin plates hinged at the body's edge; the code flaps them (and the tips) around z."""
import math
import random

from mobkit import Model, spawn_egg, shade, mix, hexc, FACES
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Manta Ray"
LOOT = []
TAGS = ["aquatic", "can_breathe_under_water", "sensitive_to_impaling"]


# -- texture packing (as the angler): biggest cubes first, each with a 1 px clear margin -------------
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


def _h(a, b, salt):
    """Deterministic noise from two coordinates (so faces that meet or overlap agree)."""
    return random.Random(int(a) * 7919 + int(b) * 104729 + salt * 15485863).random()


def pick(pal, a, b, salt):
    return hexc(pal[int(_h(a, b, salt) * len(pal)) % len(pal)])


# -- palette -----------------------------------------------------------------------------------------
TOP = ["#15161b", "#18191f", "#131419", "#1b1c22", "#16171d", "#191a20"]
TOP_LIGHT = ["#23262e", "#272a33", "#20232a"]     # skin texture flecks and the leading-edge sheen
PATCH = ["#d4d8dc", "#cbd0d5", "#dadde1", "#c6cbd0", "#d0d4d8"]
PATCH_EDGE = ["#9198a0", "#9aa1a8", "#878e96"]
PATCH_FADE = "#3e434b"
BELLY = ["#eef0ef", "#e8ebeb", "#f3f4f3", "#e4e8e8", "#ebeeed"]
BELLY_SH = ["#cfd4d7", "#c8cdd1", "#d4d8db"]
MARGIN = ["#4d535b", "#575d65", "#454a52"]
MARGIN_LT = ["#868d95", "#7c838b"]
FRECKLE = ["#2b2e34", "#33373e", "#24272c"]
GILL = "#8a9198"
GILL_DK = "#5d636a"
MOUTH = "#0b0c0f"
MOUTH_IN = ["#1b1d22", "#23262c", "#16181c"]
LIP = "#4a4f57"
LIP_LOW = "#70767e"
PUPIL = "#060709"
IRIS = "#4b5563"
GLINT = "#e9f1f6"
LOBE_IN = ["#aab1b8", "#b6bcc2", "#a0a7ae"]
LOBE_OUT = ["#17181d", "#1c1d23", "#141519"]
EDGE = ["#2f3239", "#34373e", "#2c2f36"]
SIDE_MID = "#5b6169"


# -- the plan (top view): u = distance from the midline, z = front (-) to back (+) -----------------
TIP = 24.0


def _s(u):
    return min(1.0, max(0.0, (u - 7.0) / (TIP - 7.0)))


def z_front(u):
    """The leading edge: the head's front, the flank, then the wing sweeping back to the tip."""
    if u <= 5.0:
        return -8.0
    if u <= 7.0:
        return -6.0
    return -6.0 + 9.0 * _s(u) ** 1.3


def z_back(u):
    """The trailing edge: straight across the body, then the concave wing edge out to the tip."""
    if u <= 7.0:
        return 7.0
    return 3.5 + 3.5 * (1.0 - _s(u)) ** 1.6


def inside(u, z, inset=0.0):
    return u <= TIP and z_front(u) + inset <= z <= z_back(u) - inset


# the chevron on each shoulder: a wedge behind the leading edge, tapering out along the wing
def patch_depth(u, z):
    """> 0 inside the pale patch (distance to its nearest border), < 0 outside. The front border
    runs a few pixels behind the leading edge, the rear one slants forward from the spine, and they
    meet in a point two thirds of the way out along the wing."""
    front = z - (-5.2 + 0.47 * (u - 2.5))
    rear = (4.2 - 0.36 * (u - 2.5)) - z
    mid = u - 2.5
    return min(front, rear, mid * 1.4)


# belly freckles (signed x, z): a loose scatter over the belly, not symmetric; 'big' ones are darker
FRECKLES = {(-1.5, -4.5): 0, (0.5, -5.5): 1, (2.5, -2.5): 0, (-2.5, -1.5): 1, (1.5, 0.5): 0,
            (-0.5, 1.5): 1, (0.5, 3.5): 0, (-1.5, 4.5): 0, (2.5, 2.5): 1, (-2.5, 5.5): 1,
            (1.5, 5.5): 1, (-0.5, -2.5): 0, (-3.5, 2.5): 1}
GILLS = (-6.5, -4.5, -2.5, -0.5, 1.5)


def top_col(X, Z):
    u = abs(X)
    a, b = math.floor(X), math.floor(Z)
    col = pick(TOP, a, b, 1)
    r = _h(a, b, 2)
    if r < 0.07:
        col = pick(TOP_LIGHT, a, b, 3)                       # skin texture
    if u < 5.0:
        col = shade(col, 1.0 + 0.16 * (1.0 - u / 5.0))     # the dome over the body catches light
    if u > 5.0 and Z - z_front(u) < 1.0:
        col = mix(col, pick(TOP_LIGHT, a, b, 4), 0.7)     # sheen along the leading edge
    d = patch_depth(u, Z)
    if d > 1.0:
        col = pick(PATCH, a, b, 5)
        if r > 0.9:
            col = shade(col, 0.9)
    elif d > 0.3:
        col = pick(PATCH_EDGE, a, b, 6)
    elif d > -0.5:
        col = mix(col, PATCH_FADE, 0.8)
    return col


def bottom_col(X, Z):
    u = abs(X)
    a, b = math.floor(X), math.floor(Z)
    col = pick(BELLY, a, b, 7)
    fr, bk = Z - z_front(u), z_back(u) - Z
    if u > 7.0:
        # the wing underside: a dark trailing margin, darker toward the tip, a grey leading edge
        tip = max(0.0, (u - 17.0) / (TIP - 17.0))
        if bk < 1.0 + 1.2 * tip:
            col = pick(MARGIN, a, b, 8)
        elif bk < 2.0 + 1.5 * tip:
            col = pick(MARGIN_LT, a, b, 9)
        elif fr < 1.0:
            col = pick(BELLY_SH, a, b, 10)
        if tip > 0.55 and _h(a, b, 11) < tip * 0.8:
            col = mix(col, MARGIN[0], 0.6)
        return col
    if fr < 1.0:
        return hexc(LIP_LOW) if u < 4.5 else pick(BELLY_SH, a, b, 12)   # under the lower jaw
    if u > 5.0 and (fr < 1.6 or bk < 1.0):
        col = pick(BELLY_SH, a, b, 13)
    # five gill slits a side: a dark inner end fading out toward the flank
    if 3.0 <= u <= 5.0:
        for g in GILLS:
            if abs(Z - g) < 0.5:
                return hexc(GILL_DK if u < 4.0 else GILL)
    if (X, Z) in FRECKLES:
        return shade(pick(FRECKLE, a, b, 14), 0.8 if FRECKLES[(X, Z)] else 1.45)
    if bk < 1.0:
        col = pick(BELLY_SH, a, b, 15)
    return col


OUTWARD = {"front": (0.0, -0.5), "back": (0.0, 0.5), "right": (-0.5, 0.0), "left": (0.5, 0.0)}


def step_col(face, X, Z, upper):
    """A step in the top (or bottom) surface carries on that surface's pattern, so the chevrons and
    margins run unbroken over the dome and the wing roots. The steps facing sideways stay black, so
    from the side the back reads dark over a white belly."""
    dx, dz = OUTWARD.get(face, (0.0, 0.0))
    if not upper:
        return shade(bottom_col(X + dx, Z + dz), 0.94)
    if face in ("right", "left"):
        return pick(TOP, math.floor(X), math.floor(Z), 42)
    return top_col(X + dx, Z + dz)


def side_col(face, X, Y, Z):
    """The edges of the body: the back's pattern above, the belly below and a slate line where
    they meet."""
    if Y < 21.0:
        return step_col(face, X, Z, True)
    if Y < 22.0:
        return hexc(SIDE_MID)
    return step_col(face, X, Z, False)


def paint3d(abs_origin, size, fn):
    """Painters for a cube resting at abs_origin (model space): each face pixel is mapped back to its
    centre point and fn(face, X, Y, Z, inward) gives its colour (None = cut out). inward is the
    point nudged half a pixel into the cube, for testing the plan outline on the side faces."""
    x0, y0, z0 = abs_origin
    w, h, d = size

    def make(face):
        def p(c):
            for r in range(c.h):
                for k in range(c.w):
                    if face == "top":
                        pt = (x0 + k + 0.5, y0, z0 + d - r - 0.5)
                        inw = pt
                    elif face == "bottom":
                        pt = (x0 + k + 0.5, y0 + h, z0 + d - r - 0.5)
                        inw = pt
                    elif face == "front":
                        pt = (x0 + k + 0.5, y0 + r + 0.5, z0)
                        inw = (pt[0], pt[1], z0 + 0.5)
                    elif face == "back":
                        pt = (x0 + w - k - 0.5, y0 + r + 0.5, z0 + d)
                        inw = (pt[0], pt[1], z0 + d - 0.5)
                    elif face == "right":
                        pt = (x0, y0 + r + 0.5, z0 + d - k - 0.5)
                        inw = (x0 + 0.5, pt[1], pt[2])
                    else:
                        pt = (x0 + w, y0 + r + 0.5, z0 + k + 0.5)
                        inw = (x0 + w - 0.5, pt[1], pt[2])
                    col = fn(face, pt[0], pt[1], pt[2], inw)
                    if col is None:
                        c.clear(k, r)
                    else:
                        c.set(k, r, col)
        return p
    return {f: make(f) for f in FACES}


# -- surface functions per kind of cube -----------------------------------------------------------
def disc(inset=0.0, hide_bottom=False, hide_top=False, step=None):
    """A slab of the disc: top and bottom follow the plan, side faces only where the outline is.
    step = "top" / "bottom": a raised layer whose edges carry on that surface's pattern."""
    def fn(face, X, Y, Z, inw):
        if not inside(abs(inw[0]), inw[2], inset):
            return None
        if face == "top":
            return None if hide_top else top_col(X, Z)
        if face == "bottom":
            return None if hide_bottom else bottom_col(X, Z)
        if step:
            return step_col(face, X, Z, step == "top")
        return side_col(face, X, Y, Z)
    return fn


def core(face, X, Y, Z, inw):
    """The body and head: plan colours on top and bottom, the mouth in front, eyes on the sides."""
    if face == "top":
        return top_col(X, Z)
    if face == "bottom":
        return bottom_col(X, Z)
    u = abs(X)
    if face == "front":
        # the wide square mouth between the cephalic fins: a slate upper lip, two rows of dark
        # gape with the gill rakers glinting inside, a pale lower jaw
        if Y < 20.0:
            return step_col(face, X, Z, True)
        if u > 4.0:
            return side_col(face, X, Y, Z) if Y > 22.0 else pick(LOBE_OUT, math.floor(X), math.floor(Y), 19)
        if Y < 21.0:
            return hexc(LIP)
        if Y < 23.0:
            raker = u < 3.5 and (math.floor(X) + math.floor(Y)) % 2 == 0
            return pick(MOUTH_IN, math.floor(X), math.floor(Y), 20) if raker else hexc(MOUTH)
        return hexc(LIP_LOW) if u < 3.5 else pick(BELLY_SH, math.floor(X), 0, 21)
    if face in ("right", "left") and -8.0 < Z < -6.0 and 20.0 < Y < 22.0:
        # a small eye behind the cephalic fin: a glint at the top front, a slate ring under it
        front = Z < -7.0
        if Y < 21.0:
            return hexc(GLINT) if front else hexc(PUPIL)
        return hexc(IRIS) if front else shade(PUPIL, 1.5)
    return side_col(face, X, Y, Z)


def lobe_wall(sx):
    """The rolled cephalic fin: black outside; the pale inner face shows only low down, inside the
    curl, and the top edge catches the light."""
    def fn(face, X, Y, Z, inw):
        inner = (face == "left") if sx < 0 else (face == "right")
        a, b = math.floor(Z), math.floor(Y)
        if face in ("right", "left"):
            if inner and Y > 21.5:
                return shade(pick(LOBE_IN, a, b, 22), 0.8)
            if Y < 21.5 and _h(a, b, 23) < 0.3:
                return pick(TOP_LIGHT, a, b, 23)
            return pick(LOBE_OUT, a, b, 24)
        if face == "bottom":
            return pick(LOBE_IN, a, 5, 25)
        if face == "front":
            return hexc("#2a2d33") if Y < 21.5 else hexc("#6d737b")
        return pick(TOP_LIGHT, a, 6, 26) if face == "top" else pick(LOBE_OUT, a, b, 27)
    return fn


def lobe_lip(upper):
    """The fin's edge rolled inward: under the fin (pale, the inside of the curl) or over its tip."""
    def fn(face, X, Y, Z, inw):
        a = math.floor(Z)
        if face == "top":
            return pick(LOBE_OUT, a, 3, 28) if upper else shade(pick(LOBE_IN, a, 3, 28), 0.75)
        if face == "bottom":
            return pick(BELLY_SH, a, 3, 29)
        if face == "front":
            return hexc("#3a3f46")
        return pick(LOBE_OUT, a, 4, 30) if upper else pick(LOBE_IN, a, 4, 30)
    return fn


def tail_fn(face, X, Y, Z, inw):
    a = math.floor(Z)
    if face == "top":
        return pick(TOP, a, 1, 30) if _h(a, 2, 31) > 0.15 else pick(TOP_LIGHT, a, 1, 32)
    if face == "bottom":
        return pick(MARGIN_LT, a, 2, 33)
    if face in ("front", "back"):
        return pick(EDGE, a, 3, 34)
    return pick(EDGE, a, 4, 35) if Y < 22.0 else hexc(SIDE_MID)


DORSAL = [          # rows top to bottom, columns front to back ('.' cut out)
    "..#",
    ".##",
    "###",
]


def dorsal_fn(face, X, Y, Z, inw):
    if face not in ("right", "left"):
        return None
    row, k = int(Y - 16.0), int(Z - 5.0)
    if not (0 <= row < 3 and 0 <= k < 3) or DORSAL[row][k] == ".":
        return None
    edge = row == 0 or k == 0 or DORSAL[row][k - 1] == "."
    return pick(TOP_LIGHT, k, row, 36) if edge else pick(TOP, k, row, 37)


def pelvic_fn(face, X, Y, Z, inw):
    a, b = math.floor(X), math.floor(Z)
    if face == "top":
        return pick(TOP, a, b, 38)
    if face == "bottom":
        return pick(BELLY_SH, a, b, 39) if Z < 8.0 else pick(MARGIN_LT, a, b, 40)
    return pick(EDGE, a, b, 41)


def rnd(v):
    return int(math.floor(v + 0.5))


def columns(pk, part, pivot_u, us, y_rel, y_abs, fn, left, tag, inset_front=lambda u: 0.0, inset_back=lambda u: 0.0):
    """One 1-px-wide cube per column of the plan, from the leading edge to the trailing edge (less
    the insets), so the outline is a closed staircase instead of a cut-out plate."""
    for u0 in us:
        uc = u0 + 0.5
        f, b = rnd(z_front(uc) + inset_front(u0)), rnd(z_back(uc) - inset_back(u0))
        if b <= f:
            continue
        ox = u0 - pivot_u if left else pivot_u - u0 - 1
        pk.add(part, (ox, y_rel, f), (1, 1, b - f),
               None if left else paint3d((-(u0 + 1), y_abs, f), (1, 1, b - f), fn),
               mirror=left, share=f"{tag}{u0}")


def slab(step=None, hide_top=False, hide_bottom=False):
    """A column of the disc: the plan's colours on top and bottom; the edges slate, or carrying on
    the surface's pattern for a raised layer."""
    def fn(face, X, Y, Z, inw):
        if face == "top":
            return None if hide_top else top_col(X, Z)
        if face == "bottom":
            return None if hide_bottom else bottom_col(X, Z)
        if step:
            return step_col(face, X, Z, step == "top")
        return pick(EDGE, math.floor(X), math.floor(Z), 16)
    return fn


def build():
    m = Model("manta_ray", 128, 64, seed=5555)
    pk = Pack(m)

    # body: pivot at the centre of the disc (y 21). The core (head and body) is 10 wide and 5 tall
    # with a gentle dome on top; the flanks taper it down toward the wings.
    BY = 21.0
    body = m.part("body", (0, BY, 0))
    pk.add(body, (-5, -2, -8), (10, 5, 15), paint3d((-5, BY - 2, -8), (10, 5, 15), core))
    pk.add(body, (-4, -3, -6), (8, 1, 11), paint3d((-4, BY - 3, -6), (8, 1, 11), disc(step="top", hide_bottom=True)))
    pk.add(body, (-7, -1, -6), (2, 3, 13), paint3d((-7, BY - 1, -6), (2, 3, 13), disc()), share="flank")
    pk.add(body, (5, -1, -6), (2, 3, 13), None, mirror=True, share="flank")
    # pelvic fins under the back edge, either side of the tail
    pk.add(body, (-3, 1, 7), (2, 1, 2), paint3d((-3, BY + 1, 7), (2, 1, 2), pelvic_fn), share="pelvic")
    pk.add(body, (1, 1, 7), (2, 1, 2), None, mirror=True, share="pelvic")

    # wings: thin plates hinged at the flank, built as one-pixel columns cut to the outline (so
    # every edge is closed), thickened toward the root by a layer above and one below. Each tip is a
    # separate part so the code can let it trail the beat.
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        ox = (lambda x0, w: x0 if not left else -x0 - w)     # a cube's x origin, mirrored for the left
        wing = body.part(side + "_wing", (7 * sx, 0.5, 0))
        tip = wing.part(side + "_wing_tip", (8 * sx, 0, 0))
        columns(pk, wing, 7, range(7, 15), -0.5, BY, slab(), left, "w")
        columns(pk, wing, 7, range(7, 10), -1.5, BY - 1,
                slab(step="top", hide_bottom=True), left, "wt", lambda u: 1.0 + 0.5 * (u - 7), lambda u: 1.6 + 0.6 * (u - 7))
        columns(pk, wing, 7, range(7, 9), 0.5, BY + 1,
                slab(step="bottom", hide_top=True), left, "wb", lambda u: 1.4, lambda u: 1.8 + 0.6 * (u - 7))
        columns(pk, tip, 15, range(15, 24), -0.5, BY, slab(), left, "t")

        # cephalic fins: rolled flaps either side of the mouth, angled in a little and tipped down
        lobe = body.part(side + "_lobe", (4.5 * sx, 0.5, -8), (0.18, 0.2 * sx, 0))
        pk.add(lobe, (-0.5, -1, -6), (1, 2, 6),
               None if left else paint3d((-5, 20.5, -14), (1, 2, 6), lobe_wall(-1)), mirror=left, share="lobe")
        pk.add(lobe, (ox(0.5, 1), 0, -6), (1, 1, 5),
               None if left else paint3d((-4, 21.5, -14), (1, 1, 5), lobe_lip(False)), mirror=left, share="lobe_lip")
        pk.add(lobe, (ox(0.5, 1), -1, -6), (1, 1, 1),
               None if left else paint3d((-4, 20.5, -14), (1, 1, 1), lobe_lip(True)), mirror=left, share="lobe_curl")

    # a small dorsal fin at the base of the tail
    fin = body.part("dorsal_fin", (0, -2, 5))
    pk.add(fin, (0, -3, 0), (0, 3, 3), paint3d((0, 16, 5), (0, 3, 3), dorsal_fn))

    # the tail: a short thick base, then a long whip that thins toward the tip
    tail = body.part("tail", (0, 1, 7))
    pk.add(tail, (-1, -0.5, 0), (2, 1, 3), paint3d((-1, 21.5, 7), (2, 1, 3), tail_fn))
    pk.add(tail, (-0.5, -0.5, 3), (1, 1, 7), paint3d((-0.5, 21.5, 10), (1, 1, 7), tail_fn))
    whip = tail.part("tail_tip", (0, 0, 10))
    pk.add(whip, (-0.5, -0.5, 0), (1, 1, 10), paint3d((-0.5, 21.5, 17), (1, 1, 10), tail_fn), inflate=-0.2)

    pk.apply()
    m.save()
    spawn_egg("manta_ray", "#1a1c22", "#e8ebeb", accent="#9aa1a9")


if __name__ == "__main__":
    build()

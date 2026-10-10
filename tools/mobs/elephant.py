"""Elephant: a savanna elephant, the biggest animal in the mod. A deep barrel body with a high
shoulder, a dip in the back and a rounded rump; a big domed head with small lashed eyes, a long
ringed trunk in three joints that hangs almost to the ground with its tip curled forward, short
ivory tusks out of lip sheaths either side of it, and a pointed lower lip. Huge fan-shaped ears
(the map-of-Africa shape, a torn nick or two in the rim) hang a little away from the shoulders:
wrinkled grey hide outside, pale pinkish-grey with dark veins inside. Four pillar legs, ringed with
creases, on round feet with pale toenails; a thin tail ending in a tuft of black wire.

The hide is grey and wrinkled all over: a fine crackle of creases, deeper folds behind the shoulder
and in front of the thigh, rings round the legs and trunk. Savanna dust lies red-brown along the
back and the top of the head and cakes the lower legs; the belly is in shadow, and so is the
shoulder under each ear.

The ears are 1 px slabs with their shape cut out; their pivot is the front edge where they meet the
head, so the code swings them out. `elephant_calf` (drawn at half scale on the same geometry) is a
fuzzy, pinker brown-grey with far fewer wrinkles, a mop of hair on its head and back, bigger eyes
and much smaller ears (cut smaller out of the same slab). The code hides its tusks."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import item

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Elephant"
LOOT = [item("leather", 1, 3)]
TAGS = []

Z0 = 5   # the whole model sits 5 px back, so the long body and head centre over the hitbox


# -- texture packing (as in yak.py): biggest cubes first, a 1 px clear margin round every cube -------
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


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


def vnoise(x, y, seed, sx, sy):
    """Smooth value noise (cells sx x sy px), 0..1: the broad mottling of the hide."""
    gx, gy = x / sx, y / sy
    x0, y0 = math.floor(gx), math.floor(gy)
    tx, ty = gx - x0, gy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a, b = hsh(x0, y0, seed, 21), hsh(x0 + 1, y0, seed, 21)
    c, d = hsh(x0, y0 + 1, seed, 21), hsh(x0 + 1, y0 + 1, seed, 21)
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


SIDES = ("front", "back", "left", "right")

# -- palettes ----------------------------------------------------------------------------------------
ADULT = dict(
    kind="adult",
    hide=["#8a8480", "#87817d", "#8d8783", "#85807c"],
    hide_hi=["#a29c97", "#9f9994"],
    crease=["#5a5451", "#5f5956"],
    dust=["#935e38", "#9b653d", "#8b5834"],          # red-brown savanna dust
    belly=["#615b58", "#5d5754", "#655f5c"],
    fuzz=None, crackle=1.0,
    ear_in=["#a69492", "#a08e8c", "#ab9997"],
    vein="#7a6462",
    eye="#160f0b", iris="#4a2f1c", glint="#f6f2ea", lash="#1e1816", socket="#5f5855",
    gland="#423b38",
    tusk=["#efe6cf", "#f3ebd8", "#ebe1c7"], tusk_sh=["#d5c8a9", "#cec09f"],
    tusk_root=["#cbb68b", "#c4ae82"],
    nail=["#ddd4c3", "#d5cbb8"], nail_sh="#a59b89",
    sole=["#4b4643", "#45403d", "#504b48"],
    lip="#8e7471", mouth="#9a5b58", tongue="#b87672",
    tuft=["#1d1a19", "#262221", "#141211"],
    nostril="#271f1d", tip=["#a08f8b", "#988783"],
)
CALF = dict(
    ADULT,
    kind="calf",
    hide=["#8e807a", "#8a7c76", "#92847e", "#877973"],
    hide_hi=["#a7988e", "#a29388"],
    crease=["#6e625d", "#72665f"],
    dust=["#93664f", "#9a6d55"],
    belly=["#6e625d", "#6a5e59"],
    fuzz=["#b4a69d", "#ab9c93", "#bdafa5", "#c4b6ab"], crackle=0.4,
    ear_in=["#b59e9a", "#af9894", "#baa39f"],
    vein="#937874",
    socket="#6c605b",
    tip=["#ae9b95", "#a7948e"],
)


# -- the hide ------------------------------------------------------------------------------------------
def cracks(x, y, seed, cw=5.0, ch=3.5):
    """How far a pixel is from the nearest crack of a crackle network (jittered cells, cw x ch px);
    small on a crack."""
    gx, gy = int(math.floor(x / cw)), int(math.floor(y / ch))
    d1 = d2 = 9.0
    for i in range(gx - 1, gx + 2):
        for j in range(gy - 1, gy + 2):
            px = (i + 0.15 + 0.7 * hsh(i, j, seed, 1)) * cw
            py = (j + 0.15 + 0.7 * hsh(i, j, seed, 2)) * ch
            d = math.hypot((x + 0.5 - px) / cw, (y + 0.5 - py) / ch)
            if d < d1:
                d1, d2 = d, d1
            elif d < d2:
                d2 = d
    return d2 - d1


def light(ay):
    """Painted top light: the back catches the sun, the belly and the legs under it sit in shadow,
    the lower legs a little brighter again out of the body's shadow, the feet darker."""
    if ay <= 5:
        return 1.1 - 0.26 * (ay + 18) / 23.0
    return 0.84 + 0.05 * min(1.0, (ay - 5) / 8.0) - 0.07 * max(0.0, (ay - 18) / 6.0)


def hide(P, top, height, seed=0, cell=(5.0, 3.5), dust=1.0, rings=0, zmin=None, folds=(), mud=True,
         shadow=None, belly_rows=0):
    """Wrinkled grey hide for one cube whose rest pose spans absolute y top..top+height, so light, dust
    and mud run on across stacked cubes. rings: a crease every `rings` px round a leg or trunk; folds:
    absolute z of deep vertical folds on the side faces, shadow: (z0, z1, y0, y1) absolute, a darker
    patch on the side faces (both need zmin, the cube's front z); belly_rows: rows darkened where the
    sides turn under."""
    def p(c):
        f = c.face
        sd = seed * 31 + c.x0 * 7 + c.y0 * 13
        thr = 0.085 * P["crackle"]

        def crease_at(x, y):
            """0 smooth, 1 a crack in the crackle, 2 one of the rings round a leg or trunk."""
            if f == "bottom":
                return 0
            if rings and f in SIDES:
                wob = 1 if vnoise(x, 0, sd, 3, 1) > 0.55 else 0
                if (top + y + wob) % rings == 0 and hsh(x, y, sd, 5) < 0.85:
                    return 2
            return 1 if cracks(x, y, sd, *cell) < thr else 0

        def az_of(x):
            return zmin + (c.w - 1 - x if f == "right" else x)

        for y in range(c.h):
            for x in range(c.w):
                ay = top if f == "top" else top + height if f == "bottom" else top + y + 0.5
                base = c.pick(P["belly"]) if f == "bottom" else c.pick(P["hide"])
                col = shade(base, 0.95 + 0.1 * vnoise(x, y, sd, 5, 4))            # broad mottling
                if hsh(x, y, sd, 6) < 0.08:
                    col = mix(col, c.pick(P["hide_hi"]), 0.5)                     # a paler fleck
                crease = crease_at(x, y)
                deep = False
                if zmin is not None and f in ("left", "right"):
                    az = az_of(x)
                    for fz in folds:
                        bend = int(round(1.2 * math.sin((top + y) * 0.45)))      # the fold wanders
                        if az == fz + bend and -13 < ay < 3:
                            deep = True
                if deep:
                    col = mix(col, c.pick(P["crease"]), 0.7)
                elif crease:
                    col = mix(col, c.pick(P["crease"]), (0.42 if crease == 1 else 0.52) * min(1.0, P["crackle"] + 0.3))
                elif f in SIDES and crease_at(x, y + 1):
                    col = mix(col, c.pick(P["hide_hi"]), 0.3)                    # the lit ridge above
                k = 1.1 if f == "top" else 0.8 if f == "bottom" else light(ay)
                col = shade(col, k)
                # dust along the back, mud on the lower legs, in blotches
                blot = 0.3 + 0.7 * vnoise(x, y, sd + 5, 3, 3) ** 1.5
                d = 0.0
                if f == "top" and top < -6:
                    d = 0.55
                elif f in SIDES:
                    d = 0.55 * max(0.0, min(1.0, (-10.0 - ay) / 6.0))
                if mud and ay > 16 and f in SIDES:
                    d = max(d, 0.5 * min(1.0, (ay - 16) / 6.0))
                d *= dust * blot
                if d > 0 and not deep:
                    col = mix(col, shade(c.pick(P["dust"]), k), d)
                if shadow and zmin is not None and f in ("left", "right"):
                    z0, z1, y0, y1 = shadow
                    az = az_of(x)
                    inside = min(az - z0, z1 - az, ay - y0, y1 - ay)
                    if inside > -0.5:
                        col = shade(col, 0.8 if inside > 1 else 0.88)
                if belly_rows and f in SIDES and y >= c.h - belly_rows:
                    t = (y - (c.h - belly_rows) + 1) / belly_rows
                    col = mix(col, c.pick(P["belly"]), 0.4 * t)
                # the calf's fuzz: thick on its back and head, a few pale hairs lower down
                if P["fuzz"] and f != "bottom":
                    chance = 0.4 if f == "top" else 0.14 if ay < -8 else 0.04
                    if hsh(x, y, sd, 12) < chance:
                        col = mix(col, c.pick(P["fuzz"]), 0.55)
                c.set(x, y, col)
    return p


def rump(P, painter):
    """The rump's back face: a shadowed groove down the middle under the tail, lit either side."""
    def p(c):
        painter(c)
        if c.face == "back":
            mid = c.w // 2
            for y in range(c.h - 3):
                for x, k in ((mid - 1, 0.82), (mid, 0.82), (mid - 2, 1.05), (mid + 1, 1.05)):
                    c.set(x, y, shade(c.get(x, y), k))
    return p


# -- head ----------------------------------------------------------------------------------------------
def cranium_side(P, top):
    """13 deep x 13 tall: a small eye in a wrinkled socket a quarter of the way back, long dark lashes
    drooping over it and a glint; the dark streak of the temporal gland behind it; the ear hinges
    behind that."""
    base = hide(P, top, 13, seed=3, cell=(3.0, 2.5), mud=False)

    def p(c):
        base(c)
        calf = P["kind"] == "calf"
        ey, ei = 7, 3                      # eye: rows 7-8, columns 3-4 from the front
        for (i, y) in ((2, 6), (3, 6), (4, 6), (5, 6), (2, 7), (5, 7), (2, 8), (5, 8), (3, 9), (4, 9)):
            c.set(fx(c, i), y, mix(c.get(fx(c, i), y), P["socket"], 0.6))     # the wrinkled socket
        c.set(fx(c, ei), ey, P["glint"])
        c.set(fx(c, ei + 1), ey, P["eye"])
        c.set(fx(c, ei), ey + 1, P["iris"])
        c.set(fx(c, ei + 1), ey + 1, P["eye"])
        if calf:                            # a calf's eye is bigger and rounder
            c.set(fx(c, ei + 2), ey, P["eye"])
            c.set(fx(c, ei + 2), ey + 1, P["iris"])
        # the upper lid, and long lashes drooping out past the eye's back corner
        c.set(fx(c, ei), ey - 1, mix(P["lash"], P["socket"], 0.45))
        c.set(fx(c, ei + 1), ey - 1, P["lash"])
        c.set(fx(c, ei + 2), ey - 1, P["lash"])
        if not calf:
            c.set(fx(c, ei + 2), ey, mix(P["lash"], P["socket"], 0.3))
        c.set(fx(c, ei + 3), ey, mix(P["lash"], c.get(fx(c, ei + 3), ey), 0.6))
        # a pale lower lid, wrinkles fanning back from the corner of the eye
        for i in range(ei, ei + 2):
            c.set(fx(c, i), ey + 2, mix(c.get(fx(c, i), ey + 2), c.pick(P["hide_hi"]), 0.6))
        c.set(fx(c, ei + 4), ey - 1, mix(c.get(fx(c, ei + 4), ey - 1), c.pick(P["crease"]), 0.5))
        if not calf:
            for y in range(ey + 1, ey + 4):                                  # temporal gland streak
                c.set(fx(c, ei + 4), y, mix(c.get(fx(c, ei + 4), y), P["gland"], 0.75))
            c.set(fx(c, ei + 5), ey + 3, mix(c.get(fx(c, ei + 5), ey + 3), P["gland"], 0.5))
        # the hollow of the temple, darker, behind and above the eye
        for i in range(6, 11):
            for y in range(1, 6):
                c.set(fx(c, i), y, shade(c.get(fx(c, i), y), 0.93))
    return p


def cranium_front(P, top):
    """A broad forehead with a few long wrinkles across it; the trunk's base covers the middle low down;
    bulges over the eyes at the outer columns."""
    base = hide(P, top, 13, seed=4, cell=(4.0, 2.5), mud=False)

    def p(c):
        base(c)
        for x in range(c.w):
            for y in (2, 4):
                if 1 <= x < c.w - 1 and hsh(x // 2, y, 41) < 0.75:
                    c.set(x, y, mix(c.get(x, y), c.pick(P["crease"]), 0.4))
        if c.h > 8:
            for y in range(6, 10):                             # brow bulges over the eyes, lit
                for x in (0, 1, c.w - 2, c.w - 1):
                    c.set(x, y, shade(c.get(x, y), 1.05 if y < 8 else 0.92))
    return p


def mouth_side(P, top):
    """The lower face, 8 deep x 3 tall: the corner of the mouth runs back from the front."""
    base = hide(P, top, 3, seed=5, cell=(3.0, 2.0), mud=False)

    def p(c):
        base(c)
        if c.face in ("left", "right"):
            for i in range(0, 4):
                c.set(fx(c, i), 2, mix(P["lip"], P["mouth"], 0.4) if i < 3 else c.pick(P["crease"]))
        if c.face == "front":
            for x in range(2, c.w - 2):
                c.set(x, 2, P["lip"])
        if c.face == "bottom":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, shade(c.pick(P["belly"]), 0.95))
    return p


def jaw(P):
    """The pointed lower lip: pinkish lip outside, the mouth and tongue on top (seen when it opens)."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "top":
                    col = P["tongue"] if 1 <= x < c.w - 1 and y >= 1 else P["mouth"]
                elif f == "bottom":
                    col = shade(c.pick(P["belly"]), 0.95)
                else:
                    col = mix(c.pick(P["hide"]), P["lip"], 0.6 if y == 0 else 0.25)
                    col = shade(col, 0.82 if y == c.h - 1 else 0.92)
                c.set(x, y, col)
    return p


# -- ears ----------------------------------------------------------------------------------------------
# rows (top to bottom) of the ear shape, as the span of columns counted back from the hinge
EAR = [(1, 10), (0, 12), (0, 13), (0, 14), (0, 14), (0, 14), (0, 14), (0, 14), (0, 13), (0, 13),
       (0, 12), (0, 12), (0, 11), (1, 10), (1, 9), (2, 8), (2, 7), (3, 6), (3, 5), (4, 4)]
EAR_NICKS = {(14, 5), (13, 9), (10, 13)}           # torn notches in the rim
CALF_EAR = [None, None, None, (1, 6), (0, 8), (0, 9), (0, 10), (0, 10), (0, 10), (0, 9), (0, 9),
            (0, 8), (1, 7), (1, 6), (2, 5), (3, 4), None, None, None, None]
EAR_L, EAR_H = 15, 20


def ear(P):
    """The ear slab (1 thick, 20 tall, 15 long back from the hinge). Outside: wrinkled hide shading down
    to a dark rim, the top edge folded back and lit; inside: pale pinkish-grey with dark veins fanning
    back from the hinge. The thin front and back edges show only where the shape touches them."""
    shape = CALF_EAR if P["kind"] == "calf" else EAR
    nicks = set() if P["kind"] == "calf" else EAR_NICKS

    def inside(i, y):
        if not (0 <= i < EAR_L and 0 <= y < EAR_H) or shape[y] is None:
            return False
        a, b = shape[y]
        return a <= i <= b and (i, y) not in nicks

    def edge(i, y):
        """0 on the free rim, 1 a pixel in, 2+ further in (the hinge edge doesn't count)."""
        for r in (0, 1):
            for di in range(-r - 1, r + 2):
                for dy in range(-r - 1, r + 2):
                    if abs(di) + abs(dy) == r + 1 and i + di >= 0 and not inside(i + di, y + dy):
                        return r
        return 2

    outer = hide(P, -18, 20, seed=8, cell=(4.0, 3.0), dust=0.5, mud=False)

    def p(c):
        f = c.face
        if f in ("top", "bottom"):
            # left open: the top and bottom strips sit side by side on the sheet, so a painted top
            # edge would bleed into the bottom one as a dotted line under the ear
            for r in range(c.h):
                c.clear(0, r)
            return
        if f in ("front", "back"):
            i = 0 if f == "front" else EAR_L - 1
            for y in range(c.h):
                if inside(i, y):
                    c.set(0, y, shade(c.pick(P["crease"]), 1.1))
                else:
                    c.clear(0, y)
            return
        # the big faces: "right" is the outside (mirrored onto the left ear's outside), "left" the inside
        if f == "right":
            outer(c)
        for y in range(c.h):
            for x in range(c.w):
                i = c.w - 1 - x if f == "right" else x
                if not inside(i, y):
                    c.clear(x, y)
                    continue
                e = edge(i, y)
                if f == "right":
                    col = c.get(x, y)
                    col = shade(col, (1.04 - 0.16 * y / EAR_H - 0.05 * i / EAR_L) * (0.9 if P["kind"] == "calf" else 1.0))
                    if y <= 2 and e > 0 and i <= 12:
                        col = mix(col, c.pick(P["hide_hi"]), 0.45 if y == 1 else 0.2)   # the fold
                    if e == 0:
                        col = mix(col, c.pick(P["crease"]), 0.75)
                    elif e == 1:
                        col = mix(col, c.pick(P["crease"]), 0.3)
                    # long wavy wrinkles running back across the ear
                    if e >= 1 and (y + int(2 * vnoise(i, 0, 9, 4, 1))) % 4 == 0 and hsh(i, y, 7) < 0.7:
                        col = mix(col, c.pick(P["crease"]), 0.3)
                    c.set(x, y, col)
                    continue
                col = c.pick(P["ear_in"])
                col = shade(col, 1.04 - 0.14 * y / EAR_H)
                if i <= 1:
                    col = shade(col, 0.84)                       # in the shadow of the head
                if e == 0:
                    col = mix(col, c.pick(P["hide"]), 0.6)       # the hide wraps round the rim
                c.set(x, y, col)
        if f == "left":
            veins(c, P, inside)
    return p


def veins(c, P, inside):
    """Dark veins branching back and down from the hinge across the inside of the ear."""
    for k, (y0, slope) in enumerate(((3, -0.15), (5, 0.1), (7, 0.35), (9, 0.6))):
        y = float(y0)
        for i in range(2, 14):
            yy = int(round(y))
            if inside(i, yy) and inside(i + 1, yy) and inside(i, yy + 1):
                c.set(i, yy, mix(c.get(i, yy), P["vein"], 0.75))
                if hsh(i, k, 3) < 0.25 and inside(i, yy - 1):
                    c.set(i, yy - 1, mix(c.get(i, yy - 1), P["vein"], 0.4))     # a side branch
            y += slope + (0.25 if hsh(i, k) < 0.3 else 0.0)


# -- trunk, tusks --------------------------------------------------------------------------------------
def trunk(P, top, height, rings=2, tip=False):
    """The trunk: close rings of wrinkles all the way down, paler and pinker on the underside (the
    back face), the tip pinkish with two nostrils at the end."""
    base = hide(P, top, height, seed=11 + rings, cell=(3.0, 2.0), dust=0.2, rings=rings, mud=False)

    def p(c):
        base(c)
        f = c.face
        if f == "back":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, mix(c.get(x, y), c.pick(P["tip"]), 0.3))
        if f == "top":
            c.fill(c.pick(P["hide"]))
        if tip and f == "bottom":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, c.pick(P["tip"]))
            c.set(0, 1, P["nostril"])
            c.set(2, 1, P["nostril"])
        if tip and f in SIDES:
            for y in (c.h - 2, c.h - 1):
                for x in range(c.w):
                    c.set(x, y, mix(c.get(x, y), c.pick(P["tip"]), 0.3 if y == c.h - 2 else 0.55))
    return p


def finger(P):
    def p(c):
        c.fill(shade(P["tip"][0], 0.92))
    return p


def tusk(P, part):
    """Ivory: a yellower root out of the lip sheath, creamy along the shaft, the tip palest."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if part == "root":
                    col = mix(c.pick(P["tusk_root"]), c.pick(P["tusk"]), min(1.0, y / max(1, c.h - 1)))
                else:
                    col = mix(c.pick(P["tusk"]), "#faf6ec", 0.5 * y / max(1, c.h - 1))
                if f in ("back", "left") or (f == "bottom" and part == "root"):
                    col = mix(col, c.pick(P["tusk_sh"]), 0.6)
                if f == "front" and x == 0:
                    col = shade(col, 1.04)
                c.set(x, y, col)
    return p


def sheath(P):
    base = hide(P, -6, 3, seed=14, cell=(2.0, 2.0), dust=0.0, mud=False)

    def p(c):
        base(c)
        if c.face == "bottom":
            c.fill(P["crease"][0])
            c.set(1, 1, P["tusk_root"][0])
    return p


# -- legs and tail -------------------------------------------------------------------------------------
def leg(P, top, height, seed, knee=None):
    """A pillar leg: the hide in loose rings, bunched into tight wrinkles at the knee (abs y)."""
    base = hide(P, top, height, seed=seed, cell=(4.0, 2.0), rings=3)

    def p(c):
        base(c)
        if knee is not None and c.face in SIDES:
            for y in range(c.h):
                ay = top + y
                if abs(ay - knee) <= 1.5 and (ay - knee) % 1 == 0:
                    for x in range(c.w):
                        if (ay + (1 if hsh(x // 2, seed) < 0.4 else 0)) % 2 == 0:
                            c.set(x, y, mix(c.get(x, y), c.pick(P["crease"]), 0.45))
    return p


def foot(P, top):
    """The round foot: hide ringed and caked with mud, and pale toenails along the front (3 in front,
    one on each side near the front)."""
    base = hide(P, top, 4, seed=21, cell=(3.0, 2.0), rings=2)

    def p(c):
        f = c.face
        if f == "bottom":
            for y in range(c.h):
                for x in range(c.w):
                    col = c.pick(P["sole"])
                    if cracks(x, y, 77, 3.0, 3.0) < 0.12:
                        col = shade(col, 0.75)
                    c.set(x, y, col)
            return
        base(c)
        if f == "front":
            for x0 in (0, 3, 6):
                for x in range(x0, x0 + 2):
                    c.set(x, 2, c.pick(P["nail"]))
                    c.set(x, 3, P["nail_sh"])
                c.set(x0, 2, shade(P["nail"][0], 1.04))
        if f in ("left", "right"):
            c.set(fx(c, 0), 2, c.pick(P["nail"]))
            c.set(fx(c, 0), 3, P["nail_sh"])
            c.set(fx(c, 3), 3, P["nail_sh"])
    return p


def tuft(P):
    """The tail's tuft of black wiry hairs, ragged at the end."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "bottom":
                    if hsh(x, y, 61) < 0.5:
                        c.clear(x, y)
                    else:
                        c.set(x, y, c.pick(P["tuft"]))
                    continue
                if f in SIDES and y == c.h - 1 and hsh(x, len(f), 62) < 0.5:
                    c.clear(x, y)
                    continue
                col = c.pick(P["tuft"])
                if hsh(x, y, len(f), 63) < 0.2:
                    col = shade(col, 1.6)
                c.set(x, y, col)
    return p


# -- the model -------------------------------------------------------------------------------------------
def make(texture_id, P):
    """Build the elephant with the given palette. Geometry is identical for adult and calf."""
    m = Model("elephant", 256, 128, seed=5252, texture_id=texture_id)
    pk = Pack(m)

    def at(pivot, origin):
        """A cube origin given in absolute (rest pose) coordinates, relative to a part's absolute pivot."""
        return tuple(o - p for o, p in zip(origin, pivot))

    def Z(x, y, z):
        return (x, y, z + Z0)

    # where each ear's shadow falls on the shoulder (absolute z0, z1, y0, y1)
    EAR_SHADOW = (-21 + Z0, -10 + Z0, -17, 0)

    # body: pivot mid-barrel. A deep barrel (y -15..1) with a high shoulder (withers to y -18), a dip
    # in the back (-16) and the hips (-17) curving down over the rump; the belly hangs to y 3; chest and
    # rump round off the ends.
    BP = Z(0, -6, 0)
    body = m.part("body", BP)
    BODY = [  # absolute origin, size, crackle cell, folds, darkened belly rows
        ((-11, -15, -15), (22, 16, 30), (5.0, 3.5), (-7, 6), 3),     # the barrel
        ((-10, -16, -15), (20, 1, 30), (5.0, 2.0), (), 0),          # the back, rounding over
        ((-9, -18, -16), (18, 2, 13), (5.0, 2.5), (), 0),           # withers
        ((-9, -17, 5), (18, 1, 10), (5.0, 2.0), (), 0),             # hips
        ((-8, -16, 15), (16, 2, 2), (3.0, 2.0), (), 0),             # the top of the rump
        ((-10, 1, -13), (20, 2, 19), (5.0, 2.0), (), 0),            # belly
        ((-9, 1, 6), (18, 1, 6), (5.0, 2.0), (), 0),                # the flank tucks up to the thighs
        ((-9, -14, -18), (18, 14, 3), (3.0, 3.0), (), 2),           # chest
        ((-9, -14, 15), (18, 13, 3), (3.0, 3.0), (), 2),            # rump
    ]
    for k, (o, s, cell, folds, belly) in enumerate(BODY):
        o = Z(*o)
        paint = hide(P, o[1], s[1], seed=k, cell=cell, zmin=o[2], folds=tuple(z + Z0 for z in folds),
                     shadow=EAR_SHADOW, belly_rows=belly)
        if k == len(BODY) - 1:
            paint = rump(P, paint)
        pk.add(body, at(BP, o), s, faces(paint))

    # tail: from the top of the rump, hanging close, ending in a tuft of black wire
    TP = Z(0, -13, 18)
    tail = body.part("tail", at(BP, TP), (0.18, 0, 0))
    pk.add(tail, (-1, 0, -1), (2, 5, 2), faces(hide(P, -13, 5, seed=30, cell=(2.0, 2.0), dust=0.5, mud=False)))
    pk.add(tail, (-0.5, 4, -0.5), (1, 7, 1), faces(hide(P, -9, 7, seed=31, cell=(2.0, 2.0), dust=0.0, mud=False)))
    pk.add(tail, (-1, 10, -1), (2, 4, 2), faces(tuft(P)))

    # head: child of body, pivot at the top of the chest. A big domed cranium (16 x 13 x 13) with
    # the forehead bulging forward, the mouth and cheeks under it, the broad base of the trunk in front
    HP = Z(0, -11, -18)
    head = body.part("head", at(BP, HP))
    pk.add(head, at(HP, Z(-8, -17, -32)), (16, 13, 13),
           faces(hide(P, -17, 13, seed=40, cell=(3.0, 2.5), mud=False), front=cranium_front(P, -17),
                 right=cranium_side(P, -17), left=cranium_side(P, -17)))
    pk.add(head, at(HP, Z(-7, -18, -31)), (14, 1, 11), faces(hide(P, -18, 1, seed=41, mud=False)))
    pk.add(head, at(HP, Z(-6, -16, -33)), (12, 6, 1), faces(cranium_front(P, -16)))
    pk.add(head, at(HP, Z(-6, -4, -31)), (12, 3, 10), faces(mouth_side(P, -4)))
    pk.add(head, at(HP, Z(-3, -13, -34)), (6, 8, 2), faces(trunk(P, -13, 8, rings=3)))
    for sx in (-1, 1):
        left = sx > 0
        pk.add(head, at(HP, Z(2 if left else -5, -6, -33)), (3, 3, 3), None if left else faces(sheath(P)),
               mirror=left, share="sheath")

    # the lower lip, pointed, under the trunk (it drops open when it trumpets)
    jw = head.part("jaw", at(HP, Z(0, -1, -25)))
    pk.add(jw, (-2.5, 0, -6), (5, 2, 6), faces(jaw(P)))

    # ears: 1 px slabs, pivot on the hinge just behind the eye; at rest they hang a little out
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        left = sx > 0
        e = head.part(name, at(HP, Z(8 * sx, -8, -22)), (0, 0.62 * sx, 0))
        pk.add(e, (0 if left else -1, -10, 0), (1, EAR_H, EAR_L), None if left else faces(ear(P)),
               mirror=left, share="ear")

    # trunk: three joints hanging from the face, the tip curled forward a few px off the ground
    t1 = head.part("trunk1", at(HP, Z(0, -8, -34)), (-0.22, 0, 0))
    pk.add(t1, (-3, -1, -3), (6, 10, 6), faces(trunk(P, -9, 10, rings=3)))
    t2 = t1.part("trunk2", (0, 9, 0), (0.18, 0, 0))
    pk.add(t2, (-2.5, -1, -2.5), (5, 11, 5), faces(trunk(P, 0, 11, rings=2)))
    t3 = t2.part("trunk3", (0, 10, 0), (-0.38, 0, 0))
    pk.add(t3, (-2, -1, -2), (4, 6, 4), faces(trunk(P, 10, 6, rings=2)))
    pk.add(t3, (-1.5, 5, -1.5), (3, 5, 3), faces(trunk(P, 15, 5, rings=2, tip=True)))
    pk.add(t3, (-0.5, 9, -2), (1, 1, 1), faces(finger(P)))       # the two fingers of the tip
    pk.add(t3, (-0.5, 9, 1), (1, 1, 1), faces(finger(P)))

    # tusks: short, out of the sheaths, down and forward with the tips turning up (hidden on calves)
    for name, sx in (("right_tusk", -1), ("left_tusk", 1)):
        left = sx > 0
        tk = head.part(name, at(HP, Z(3.5 * sx, -4, -31.5)), (-0.5, 0, -0.14 * sx))
        pk.add(tk, (-1, 0, -1), (2, 5, 2), None if left else faces(tusk(P, "root")), mirror=left, share="tusk")
        tt = tk.part(name + "_tip", (0, 4.5, -0.3), (-0.75, 0, 0))
        pk.add(tt, (-0.5, 0, -0.5), (1, 4, 1), None if left else faces(tusk(P, "tip")), mirror=left,
               share="tusk_tip", inflate=0.12)

    # legs: pillars under the body, pivot at the shoulder / hip; thick upper leg, ringed lower leg
    # bunched at the knee, a round foot on y 24
    for name, x, z in (("right_front_leg", -6.5, -10), ("left_front_leg", 6.5, -10),
                       ("right_hind_leg", -6.5, 10), ("left_hind_leg", 6.5, 10)):
        left = name.startswith("left")
        front = "front" in name
        lg = m.part(name, Z(x, -1, z))
        share = "front" if front else "hind"
        pk.add(lg, (-4, -1, -4), (8, 12, 8), None if left else faces(leg(P, -2, 12, 50 + front, None if front else 8)),
               mirror=left, share=share + "_upper")
        pk.add(lg, (-3.5, 11, -3.5), (7, 10, 7), None if left else faces(leg(P, 10, 10, 52 + front, 13 if front else None)),
               mirror=left, share=share + "_lower")
        pk.add(lg, (-4, 21, -4), (8, 4, 8), None if left else faces(foot(P, 20)), mirror=left, share=share + "_foot")

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("elephant_calf", CALF).save(geometry=False)
    spawn_egg("elephant", "#8a8480", "#9a6247", accent="#efe6cf")


if __name__ == "__main__":
    build()

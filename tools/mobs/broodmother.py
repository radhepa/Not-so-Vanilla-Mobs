"""Broodmother: a spider queen about twice the size of a vanilla spider. A huge bloated abdomen in
mottled charcoal and bruised plum-black, rounded with stepped caps, carries a bone-white skull marking
on the rear of its back and a clutch of pale, faintly veined egg sacs bulging over the front of it;
a pair of dark spinnerets sits under its tail end. The cephalothorax is a hairy dark brown-black
carapace speckled with coarse pale bristles and grooved from a dark central pit. The head wears a
cluster of EIGHT glowing red eyes (two big front eyes, six small round them, sunk in black sockets)
and two thick hairy chelicerae hang under the face, ending in big curved glossy fangs with pale tips.
Eight long, jointed, hairy legs, dark with dull red-brown bands at the joints, rise from the body's
sides to knobbly knees held high above the carapace and drop steeply to the ground; the front pairs
reach forward, the back pairs reach back.

Rig: `body` (cephalothorax) pivots at its centre 0.69 blocks up; `head` and `abdomen` hang off it,
the abdomen pivoting at the waist. Each leg is the upper segment (`right_leg1`, hip to knee) with the
lower segment (`right_leg1_lower`, knee to foot) as its child; the feet are solved to touch y 24."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix, hexc
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Broodmother"
LOOT = [item("string", 2, 5), item("spider_eye", 1, 2), item("cobweb", 0, 2), item("fermented_spider_eye", chance=0.25, looting=False, player_only=True)]
TAGS = ["arthropod"]


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


def outer(c, i):
    """Column i counted from the outer (far) end of a right leg segment, on its long faces."""
    return c.w - 1 - i if c.face == "back" else i


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


def light(c, x, y, col, base=0.24):
    """A pixel that IS light: full colour on the emissive layer over a dim base, so the additive glow
    shows the true colour in the dark instead of washing out to white in daylight."""
    if not c.inside(x, y):
        return
    c.set(x, y, shade(col, base))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), hexc(col))


def side_f(c, y, top=1.1, hi=1.05, low=0.74, bottom=0.66):
    """Light factor for a pixel: lit top, sides darkening downward, a dark underside."""
    if c.face == "top":
        return top
    if c.face == "bottom":
        return bottom
    return hi - (hi - low) * y / max(1, c.h - 1)


# -- palette -----------------------------------------------------------------------------------------
ABD = ["#2a2230", "#272029", "#2d2432", "#241d29"]          # charcoal plum-black
PLUM = ["#3d2b42", "#432f48", "#38283d"]                    # bruised plum mottles
DARKM = ["#19141c", "#1c161f"]
SPECK = ["#5d4f5e", "#544656"]
BONE = ["#d9cfc0", "#d3c8b8", "#ded5c7"]
BONE_SH = ["#b8ad9c", "#ada190"]
EGG = ["#e8dcbf", "#e2d4b3", "#ebe1c9", "#e5d8ba"]          # warmer, yellower than the bone
EGG_SH = ["#c4b08c", "#bba784"]
EGG_DK = ["#9c8a6c", "#94825f"]
VEIN = ["#c08f86", "#b3837f", "#c99a8e"]
CEPH = ["#241c18", "#2a201b", "#211915", "#271e1a"]
HAIR = ["#4e3e33", "#5a4a3c", "#6b5a48"]
HAIR_DK = ["#17110f", "#1b1411"]
LEG = ["#211a17", "#261e1a", "#1d1714"]
LEG_HAIR = ["#43352c", "#4c3d32", "#57473a"]
BAND = ["#4f2c22", "#583126", "#482820"]
CLAW = ["#0e0a09", "#120d0b"]
FANG = ["#151011", "#1c1517", "#181213"]
FANG_HI = "#3d3236"
SOCKET = "#0b0707"
EYE_DEEP = "#c0101a"
EYE_HOT = "#ff3030"


# -- abdomen -----------------------------------------------------------------------------------------
def mottle(c, density=14):
    """Charcoal plum-black with chunky bruised-plum and near-black blotches (colours, not yet lit)."""
    cols = [[c.pick(ABD) for _ in range(c.w)] for _ in range(c.h)]
    for _ in range(max(1, c.w * c.h // density)):
        cx, cy = c.rng.uniform(0, c.w), c.rng.uniform(0, c.h)
        r = c.rng.choice((0.9, 1.3, 1.7, 2.2))
        pal = PLUM if c.rng.random() < 0.62 else DARKM
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if 0 <= x < c.w and 0 <= y < c.h and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r * c.rng.uniform(0.7, 1.15):
                    cols[y][x] = c.pick(pal)
    for _ in range(max(1, c.w * c.h // 90)):              # a few pale grey-plum specks
        cols[c.rng.randrange(c.h)][c.rng.randrange(c.w)] = c.pick(SPECK)
    return cols


def abd(top=1.12, hi=1.04, low=0.72, rim=True):
    def p(c):
        cols = mottle(c)
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, shade(cols[y][x], side_f(c, y, top, hi, low, 0.62)))
        if rim and c.face in SIDES and c.h > 3:          # a soft sheen along the top edge
            for x in range(c.w):
                if c.rng.random() < 0.6:
                    c.set(x, 0, mix(c.get(x, 0), "#5a4a60", 0.35))
    return p


HOURGLASS = [
    ".######.",
    "..####..",
    "...##...",
    "...##...",
    "..####..",
    ".######.",
]


def abd_back(c):
    """The rear of the abdomen: a bone-white hourglass over the spinnerets, its lower edges shaded."""
    abd()(c)
    x0, y0 = (c.w - 8) // 2, 1
    for r, row in enumerate(HOURGLASS):
        for i, ch in enumerate(row):
            if ch == "#":
                col = c.pick(BONE)
                if r == len(HOURGLASS) - 1 or (i in (1, 6) and r in (0, 5)):
                    col = c.pick(BONE_SH)
                c.set(x0 + i, y0 + r, col)


SKULL = [
    "..######..",
    ".########.",
    "##########",
    "#oo####oo#",
    "#oo####oo#",
    "####nn####",
    ".########.",
    "..#.##.#..",
]


def abd_crown(c):
    """Top of the top cap: mottled, lit, with the bone-white skull on its rear half. Row 0 is the back
    edge; the skull's crown points forward, so it reads upright seen from behind."""
    abd(top=1.14)(c)
    if c.face != "top":
        return
    x0, y0 = (c.w - 10) // 2, 0
    for r, row in enumerate(SKULL):
        y = y0 + (len(SKULL) - 1 - r)                     # crown toward the front (higher rows)
        for i, ch in enumerate(row):
            x = x0 + i
            if ch == "#":
                col = c.pick(BONE)
                if r in (2, 6) or (r == 5 and i in (3, 6)):
                    col = c.pick(BONE_SH)
                c.set(x, y, col)
            elif ch == "o":
                c.set(x, y, shade(c.pick(DARKM), 0.8))
            elif ch == "n":
                c.set(x, y, shade(c.pick(PLUM), 0.7))


def spinneret(c):
    c.noise(DARKM + PLUM[:1])
    if c.face == "back":
        for x in range(c.w):
            c.set(x, c.h - 1, shade(c.pick(PLUM), 0.8))


def egg(c):
    """A pale silk egg sac: warm cream, lit on top, shading to a dark rim where it sits on the body,
    with faint wandering pinkish veins."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(EGG)
            if c.face == "top":
                col = shade(col, 1.04)
            elif c.face == "bottom":
                col = c.pick(EGG_DK)
            elif c.h > 2:
                t = y / (c.h - 1)
                col = c.pick(EGG_DK) if t > 0.85 else c.pick(EGG_SH) if t > 0.55 else col
            c.set(x, y, col)
    for _ in range(1 + (c.w * c.h) // 9):                 # veins: short random walks, half-mixed in
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        for _ in range(c.rng.randint(2, 4)):
            if c.inside(x, y):
                c.set(x, y, mix(c.get(x, y), c.pick(VEIN), 0.5))
            if c.rng.random() < 0.5:
                x += c.rng.choice((-1, 1))
            else:
                y += c.rng.choice((-1, 1))
    if c.face in SIDES and c.h > 2:                        # a soft highlight near the top
        c.set(c.rng.randrange(c.w), 0, "#f6efdc")


def egg_cap(c):
    """The rounded crown of an egg sac."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(EGG), 1.06 if c.face == "top" else 1.0)
            if c.rng.random() < 0.12:
                col = mix(col, c.pick(VEIN), 0.45)
            c.set(x, y, col)
    if c.face == "top":
        c.set(0, 0, "#f6efdc")


# -- cephalothorax, head, fangs ----------------------------------------------------------------------
def hairy(pal=CEPH, top=1.1, hi=1.04, low=0.72, bristles=0.15, strokes=0.1):
    """Dark hairy chitin: coarse pale bristle speckles and short vertical hair strokes on the sides."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(pal)
                r = c.rng.random()
                if r < bristles:
                    col = c.pick(HAIR)
                elif r < bristles + 0.08:
                    col = c.pick(HAIR_DK)
                c.set(x, y, shade(col, side_f(c, y, top, hi, low, 0.66)))
        if c.face in SIDES and c.h > 1:
            for _ in range(int(c.w * c.h * strokes)):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h - 1)
                k = 0.8 if c.rng.random() < 0.6 else 1.25
                for yy in (y, y + 1):
                    c.set(x, yy, shade(c.get(x, yy), k))
    return p


def carapace(c):
    """The thorax top: hairy, grooved by dark lines radiating from a dark central pit."""
    hairy(top=1.12)(c)
    if c.face != "top":
        return
    cx, cy = (c.w - 1) / 2, (c.h - 1) / 2
    for y in range(c.h):
        for x in range(c.w):
            a = math.degrees(math.atan2(y - cy, x - cx)) % 45
            if (a < 7 or a > 38) and (x - cx) ** 2 + (y - cy) ** 2 > 2:
                c.set(x, y, shade(c.pick(HAIR_DK), 1.05))
    for x, y in ((int(cx), int(cy)), (int(cx) + 1, int(cy)), (int(cx), int(cy) + 1), (int(cx) + 1, int(cy) + 1)):
        c.set(x, y, SOCKET)


def cap_top(c):
    """The raised middle of the carapace."""
    carapace(c)


EYES_BIG = ((2, 3), (6, 3))                 # top-left pixel of each 2x2 front eye
EYES_SMALL = (((3, 1), EYE_HOT), ((6, 1), EYE_HOT), ((0, 2), EYE_DEEP), ((9, 2), EYE_DEEP),
              ((1, 5), EYE_DEEP), ((8, 5), EYE_DEEP))


def face_front(c):
    """10 x 8 face: eight glowing red eyes sunk in black sockets above a hairy clypeus."""
    hairy(bristles=0.1)(c)
    for (ex, ey) in EYES_BIG:                             # sockets: a dark ring round the big eyes
        for y in range(ey - 1, ey + 3):
            for x in range(ex - 1, ex + 3):
                c.set(x, y, mix(SOCKET, c.get(x, y), 0.25))
    for (x, y), _ in EYES_SMALL:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if c.inside(x + dx, y + dy) and hsh(x, y, dx, dy) < 0.6:
                c.set(x + dx, y + dy, mix(SOCKET, c.get(x + dx, y + dy), 0.4))
    for (ex, ey) in EYES_BIG:
        light(c, ex, ey, EYE_HOT)
        light(c, ex + 1, ey, EYE_DEEP)
        light(c, ex, ey + 1, EYE_DEEP)
        light(c, ex + 1, ey + 1, "#8e0a12")
    for (x, y), col in EYES_SMALL:
        light(c, x, y, col)


def head_side(c):
    hairy()(c)
    light(c, fx(c, 0), 2, "#8e0a12")                      # the outer eyes wrap round the corners
    c.set(fx(c, 1), 2, SOCKET)


def chelicera(c):
    """Thick hairy chelicera: dark, with a fringe of pale bristles round the front."""
    hairy(bristles=0.2, low=0.6)(c)
    if c.face == "bottom":
        c.noise(FANG)
    elif c.face == "front":
        for y in range(c.h):
            for x in range(c.w):
                if (x in (0, c.w - 1) or y == 0) and c.rng.random() < 0.4:
                    c.set(x, y, c.pick(HAIR[:2]))


def fang(seg):
    """Glossy black fang with a sheen down its front edge, the tip segment fading to pale bone."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(FANG)
                if c.face in ("front", "right") and x == 0 and c.h > 1:
                    col = FANG_HI
                if seg == "tip":
                    t = y / max(1, c.h - 1)
                    if c.face == "bottom" or t > 0.6:
                        col = c.pick(BONE)
                    elif t > 0.3:
                        col = c.pick(BONE_SH)
                    elif c.face != "top":
                        col = mix(col, BONE_SH[1], 0.35)
                elif seg == "base" and y >= c.h - 1 and c.face in SIDES:
                    col = mix(col, BONE_SH[1], 0.3)
                c.set(x, y, col)
    return p


# -- legs --------------------------------------------------------------------------------------------
def leg_skin(c, bands, dark_end=0, bristles=0.11):
    """A dark hairy leg segment along x. bands: columns (counted from the outer end) in the dull
    red-brown joint colour; dark_end: that many columns at the outer end go claw-black."""
    if c.face in ("right", "left"):                       # end caps
        c.noise(CLAW if (c.face == "right" and dark_end) else LEG)
        return
    for y in range(c.h):
        for x in range(c.w):
            i = outer(c, x)
            col = c.pick(LEG)
            r = c.rng.random()
            if r < bristles:
                col = c.pick(LEG_HAIR)
            elif r < bristles + 0.1:
                col = c.pick(HAIR_DK)
            if i in bands:
                col = c.pick(BAND) if c.rng.random() < 0.8 else mix(c.pick(BAND), c.pick(HAIR), 0.4)
            if i < dark_end:
                col = c.pick(CLAW)
            c.set(x, y, shade(col, side_f(c, y, 1.12, 1.05, 0.8, 0.7)))


def femur(c):
    leg_skin(c, bands=(2,))


def knee(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BAND) if c.rng.random() < 0.5 else c.pick(LEG)
            if c.rng.random() < 0.15:
                col = c.pick(HAIR)
            c.set(x, y, shade(col, side_f(c, y, 1.15, 1.05, 0.8, 0.7)))


def shin(c):
    leg_skin(c, bands=(0, 1, c.w - 3))


def tarsus(c):
    leg_skin(c, bands=(), dark_end=2, bristles=0.08)


# -- leg geometry ------------------------------------------------------------------------------------
def _rx(v, a):
    x, y, z = v
    return (x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a))


def _ry(v, a):
    x, y, z = v
    return (x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a))


def _rz(v, a):
    x, y, z = v
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z)


def rot(v, r):
    """ModelPart rotation of a vector: X first, then Y, then Z."""
    return _rz(_ry(_rx(v, r[0]), r[1]), r[2])


def unrot(v, r):
    return _rx(_ry(_rz(v, -r[2]), -r[1]), -r[0])


def aim(d):
    """Rotation (0, yaw, roll) that turns the -x axis toward direction d (a right leg's reach)."""
    n = math.sqrt(sum(a * a for a in d))
    dx, dy, dz = (a / n for a in d)
    return (0.0, math.asin(max(-1.0, min(1.0, dz))), math.atan2(-dy, -dx))


def add(a, b):
    return tuple(p + q for p, q in zip(a, b))


def corners(cubes):
    for (o, s, g) in cubes:
        for x in (o[0] - g, o[0] + s[0] + g):
            for y in (o[1] - g, o[1] + s[1] + g):
                for z in (o[2] - g, o[2] + s[2] + g):
                    yield (x, y, z)


def solve_leg(body_y, hip, knee_dir, l1, reach, lower_cubes, ground=24.0):
    """Upper rotation aims at knee_dir; the lower segment points along the horizontal direction
    `reach` (x, z), tipped down just far enough that its lowest corner touches the ground."""
    r1 = aim(knee_dir)
    knee = add(hip, rot((-l1, 0, 0), r1))
    hx, hz = reach
    hn = math.hypot(hx, hz)
    hx, hz = hx / hn, hz / hn

    def low(e):
        d = (hx * math.cos(e), math.sin(e), hz * math.cos(e))
        r2 = aim(unrot(d, r1))
        return r2, max(body_y + knee[1] + rot(rot(p, r2), r1)[1] for p in corners(lower_cubes))

    lo, hi = 0.0, math.pi / 2
    for _ in range(60):
        mid = (lo + hi) / 2
        if low(mid)[1] < ground:
            lo = mid
        else:
            hi = mid
    return r1, low(hi)[0], knee


# -- the model ---------------------------------------------------------------------------------------
BODY_Y = 13.0
L1 = 14                                     # hip to knee
SHIN, TARS = 13, 11                         # knee to foot, in two tapering pieces
# per leg: hip z (body-local), direction from hip to knee (right side), horizontal reach of the lower
LEGS = (
    (-4.5, (-7.0, -9.0, -10.0), (-0.6, -1.0)),
    (-1.5, (-10.0, -9.5, -4.0), (-1.0, -0.4)),
    (1.5, (-10.0, -9.5, 3.5), (-1.0, 0.35)),
    (4.5, (-7.0, -9.0, 10.0), (-0.6, 1.0)),
)


def build():
    m = Model("broodmother", 128, 128, seed=6613)
    pk = Pack(m)

    # body (cephalothorax): pivot (0, 13, -4). Thorax x -6..6, y 9..16, z -10..2, with a raised
    # carapace cap (top y 8) in the middle.
    body = m.part("body", (0, BODY_Y, -4))
    pk.add(body, (-6, -4, -6), (12, 7, 12), faces(hairy(), top=carapace))
    pk.add(body, (-4, -5, -4), (8, 2, 8), faces(hairy(low=0.85), top=cap_top))

    # head: pivot at the front of the thorax; x -5..5, y 8.5..16.5, z -18..-9 (tucked into the thorax)
    head = body.part("head", (0, -1, -6))
    pk.add(head, (-5, -3.5, -8), (10, 8, 9), faces(hairy(), front=face_front, right=head_side, left=head_side))

    # fangs: thick hairy chelicerae under the face, each ending in a glossy fang that curves in and back
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        fg = head.part(side + "_fang", (2.5 * sx, 3.5, -7), (-0.15, 0, 0))
        pk.add(fg, (-2, -1, -2), (4, 3, 4), None if left else faces(chelicera), mirror=left, share="chel")
        pk.add(fg, (-1, 1.5, -1.75), (2, 2, 2), None if left else faces(fang("base")),
               mirror=left, share="fang_base")
        tip = fg.part(side + "_fang_tip", (0, 3, -0.75), (0.3, 0, 0.6 * sx))
        pk.add(tip, (-0.5, -0.5, -0.5), (1, 5, 1), None if left else faces(fang("tip")),
               mirror=left, share="fang_tip")

    # abdomen: pivot at the waist (world z 1.5, y 12). A big core box rounded off with stepped caps
    # (top, back, sides, belly), the skull on the top cap, egg sacs over the front of it.
    ab = body.part("abdomen", (0, -1, 5.5), (0.06, 0, 0))
    pk.add(ab, (-2.5, -2, -2), (5, 4, 4), faces(abd(low=0.6)))                    # waist
    pk.add(ab, (-9, -6, 1), (18, 12, 18), faces(abd()))                            # core
    pk.add(ab, (-7, -8, 3), (14, 3, 14), faces(abd(), top=abd_crown))             # top cap
    pk.add(ab, (-6, 5, 4), (12, 2, 12), faces(abd(low=0.6)))                      # belly cap
    pk.add(ab, (-7, -4, 18), (14, 8, 2), faces(abd(), back=abd_back))             # rear cap
    for sx in (-1, 1):
        left = sx > 0
        pk.add(ab, (-10 if sx < 0 else 8, -4, 3), (2, 8, 14), None if left else faces(abd()),
               mirror=left, share="side_cap")
    pk.add(ab, (-1.5, 2.5, 19.5), (3, 2, 2), faces(spinneret))

    # egg sacs: a clutch over the front of the top cap and spilling over its front edge onto the
    # waist end of the core. Pivot on the cap's top front edge (egg-local y 0 = cap top, z 0 = its
    # front; the core's top is at y 2). Each big sac gets a rounded crown; every sac overlaps its
    # neighbours or sinks into the body so no two faces lie in one plane.
    eggs = ab.part("egg_sacs", (0, -8, 3))
    for o, s, crown in (((-2.5, -4, -0.5), (5, 5, 5), True),         # the big middle sac
                        ((-6, -2.5, -0.25), (4, 4, 4), True),       # right
                        ((2, -3.5, 0.6), (4, 4, 4), True),          # left
                        ((-2.25, -1.5, -2.5), (4, 4, 3), False),    # front, over the edge
                        ((-5.75, -0.5, -1.5), (3, 3, 3), False),    # front right
                        ((2.75, -0.5, -2.25), (3, 3, 3), False),    # front left
                        ((5.5, -1.5, 2.5), (3, 4, 3), False)):      # a small one on the far left
        pk.add(eggs, o, s, faces(egg))
        if crown:
            pk.add(eggs, (o[0] + 1, o[1] - 1, o[2] + 1), (s[0] - 2, 2, s[2] - 2), faces(egg_cap))

    # legs: the upper segment rises from the thorax side to a knee above the carapace; the lower
    # segment (knee knob, shin, tarsus) drops to a foot on the ground.
    lower_cubes = [((-1.5, -1.5, -1.5), (3, 3, 3), 0.5),
                   ((-SHIN, -1, -1), (SHIN + 1, 2, 2), 0.3),
                   ((-SHIN - TARS + 1, -1, -1), (TARS, 2, 2), -0.12)]
    for i, (hz, kdir, reach) in enumerate(LEGS, start=1):
        r1, r2, _ = solve_leg(BODY_Y, (-5.0, 0.0, hz), kdir, L1, reach, lower_cubes)
        for side, sx in (("right", -1), ("left", 1)):
            left = sx > 0
            m1 = (r1[0], r1[1] * -sx, r1[2] * -sx)
            m2 = (r2[0], r2[1] * -sx, r2[2] * -sx)
            up = body.part(f"{side}_leg{i}", (5.0 * sx, 0, hz), m1)
            pk.add(up, (-L1 if sx < 0 else -2, -1.5, -1.5), (L1 + 2, 3, 3), None if left else faces(femur),
                   mirror=left, share="femur")
            lo = up.part(f"{side}_leg{i}_lower", (L1 * sx, 0, 0), m2)
            for j, ((o, s, g), paint) in enumerate(zip(lower_cubes, (knee, shin, tarsus))):
                ox = o[0] if sx < 0 else -o[0] - s[0]
                pk.add(lo, (ox, o[1], o[2]), s, None if left else faces(paint), mirror=left,
                       share=f"lower{j}", inflate=g)

    pk.apply()
    m.save()
    spawn_egg("broodmother", "#2a2230", "#d9cfc0", accent="#e0212b")


if __name__ == "__main__":
    build()

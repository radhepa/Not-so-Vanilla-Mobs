"""Kangaroo: a red kangaroo of the badlands. It sits back on its huge hind feet and thick tail, body
leaning a little forward: a pear-shaped body (broad haunches, a narrower chest), a short neck, a long
deer-like face with a big dark nose, large dark lashed eyes, tall upright ears, small forearms held in
front of the chest with dark paws, massive drumstick thighs folding into long shins, and long narrow
hind feet lying flat on the ground. The tail starts thick at the rump, curves down to rest on the
ground and tapers to a paler tip.

The buck (`kangaroo`) is rusty red with a cream belly, chest and inner legs; the doe (`kangaroo_doe`)
is a soft blue-grey with a pale belly and a pouch on her lower belly (the `pouch` part; the code shows
it only on does); the joey (`kangaroo_joey`, drawn at half scale) is pale pinkish fawn with pinker
ears. All three share the red kangaroo face: a white stripe from the corner of the mouth up toward the
eye, under a black whisker patch.

Parts (see DESIGN.md): `body` (pivot at the hips; authored upright and leaned forward by its rest
rotation) with `head` (`right_ear` / `left_ear`), `right_arm` / `left_arm` and `pouch`; `tail` (child
of root) with `tail_tip`; `right_leg` / `left_leg` (the thighs, children of root), each with a
`<side>_shin` and under it the long `<side>_foot`."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import item

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Kangaroo"
LOOT = [item("leather", 0, 2)]
TAGS = []


# -- texture packing (as in deer.py): biggest cubes first, a 1 px clear margin round every cube -----
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


def hsh(*v) -> float:
    """A repeatable 0..1 value for a position."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


def chain(*ps):
    def run(c):
        for p in ps:
            if p:
                p(c)
    return run


SIDES = ("front", "back", "left", "right")

# -- palettes ------------------------------------------------------------------------------------------
BUCK = dict(
    kind="buck",
    coat=["#ad4a2c", "#a5452a", "#b45232", "#a04128", "#ab4b2e"],
    back=["#8a3920", "#82351e", "#903d22"],
    hi=["#cf7346", "#d47b4c", "#c86c40"],
    belly=["#efe0c8", "#e8d6bd", "#f3e7d3"],
    belly_sh=["#d9c3a5", "#d2bb9b"],
    muzzle=["#d9bc9d", "#d1b392", "#dcc3a6"],
    white="#f7f2e9", white_sh="#e4dbcd",
    whisker="#1e1613", nose="#241a17", nose_hi="#665149", nostril="#0b0706",
    eye="#150d0a", iris="#4a2a18", glint="#fcf8f0", lid="#6a2f17", lash="#170e0a", ring="#e5cdb1",
    ear_in=["#e9c8b4", "#e2bfa9", "#eed3c2"], ear_rim="#4c2415", ear_hair="#f6ece0",
    paw=["#2d221e", "#352820"], claw="#100d0c",
    foot=["#d9b893", "#d0ad88", "#ddc09e"], foot_dk=["#843f22", "#7a3a1f"], sole=["#4a382f", "#523e34"],
    toe="#1c1512",
    tail_tip=["#d6b48f", "#cfab86", "#dcbf9e"],
    pouch_rim="#6a3720", pouch_in="#2c1610",
)
DOE = dict(
    BUCK,
    kind="doe",
    coat=["#7c8597", "#768092", "#838c9e", "#727b8d", "#7f889a"],
    back=["#5f677c", "#5a6276", "#646c81"],
    hi=["#99a2b3", "#a0a8b8", "#949dae"],
    belly=["#e8e4dc", "#e1ddd4", "#eeebe4"],
    belly_sh=["#cdc8be", "#c6c0b6"],
    muzzle=["#cdc8c2", "#c5c0ba", "#d3cfca"],
    lid="#4a4d58", ring="#dad6cf",
    ear_in=["#e4cdc6", "#dcc3bb", "#e9d6d0"], ear_rim="#3c3e48",
    foot=["#c7c2ba", "#bfbab2", "#cdc9c2"], foot_dk=["#60636f", "#5a5d68"],
    tail_tip=["#c9c5be", "#c1bcb4", "#d0ccc6"],
    pouch_rim="#5c5f6b", pouch_in="#24232a",
)
JOEY = dict(
    BUCK,
    kind="joey",
    coat=["#d2a98a", "#cba283", "#d8b092", "#c69d7e", "#d0a788"],
    back=["#b88d6f", "#b2876a", "#bd9274"],
    hi=["#ebd2bc", "#efd8c4", "#e7cdb6"],
    belly=["#f5ece2", "#f1e6da", "#f8f1e8"],
    belly_sh=["#e2d3c2", "#dccbb9"],
    muzzle=["#ead8c6", "#e5d1be", "#eedecd"],
    lid="#a7765a", ring="#f3e6d8",
    ear_in=["#f0c3b9", "#eab8ad", "#f4cdc4"], ear_rim="#8e5a44", ear_hair="#fbf3ea",
    paw=["#5a4038", "#634840"],
    foot=["#e6cfb8", "#dfc6ad", "#ead6c1"], foot_dk=["#b48a6d", "#ad8366"], sole=["#7d5c4c", "#86645a"],
    toe="#4a3328",
    tail_tip=["#ecd9c6", "#e6d1bc"],
    pouch_rim="#b48a6d", pouch_in="#5a3a2c",
)


# -- fur -----------------------------------------------------------------------------------------------
def strokes(c, P, density=0.14, skip=None):
    """Fine hair: 2 px streaks a little darker or lighter than what's under them."""
    for _ in range(int(c.w * c.h * density)):
        x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
        k = 0.9 if c.rng.random() < 0.6 else 1.07
        for yy in (y, y + 1):
            if c.inside(x, yy) and not (skip and skip(x, yy)):
                c.set(x, yy, shade(c.get(x, yy), k))


def torso(P, front_belly=True, y0=0, span=None, dorsal=True, bottom_dark=0.82):
    """The body, authored upright: front = chest and belly (cream), back = the back (a darker band
    down the spine), the flanks blend from the back colour at their back edge to cream at the front.
    y0/span place a face on a body-long gradient (lighter toward the shoulders)."""
    def p(c):
        sp = span or c.h
        f = c.face
        for y in range(c.h):
            t = (y0 + y + 0.5) / sp                        # 0 at the shoulders, 1 at the rump
            g = 1.06 - 0.14 * t
            for x in range(c.w):
                col = c.pick(P["coat"])
                if f == "front" and front_belly:
                    edge = min(x, c.w - 1 - x)
                    col = c.pick(P["belly"]) if edge >= 1 else mix(c.pick(P["belly"]), col, 0.45)
                    col = shade(col, 1.0 - 0.05 * t)
                elif f == "back":
                    if dorsal:
                        d = abs(x - (c.w - 1) / 2) / max(1.0, c.w / 2)
                        col = mix(c.pick(P["back"]), col, min(1.0, d * 1.7))
                    col = shade(col, g + 0.04)
                    if x in (0, c.w - 1):
                        col = shade(col, 0.9)                  # the back rounds away at its edges
                elif f in ("left", "right"):
                    i = fx(c, x)                           # 0 at the belly edge
                    j = c.w - 1 - i                        # 0 at the back edge
                    if front_belly and i == 0:
                        col = mix(c.pick(P["belly"]), col, 0.3)
                    elif front_belly and i == 1:
                        col = mix(c.pick(P["belly"]), col, 0.68)
                    elif j == 0:
                        col = mix(col, c.pick(P["back"]), 0.55)
                    col = shade(col, g)
                elif f == "top":
                    col = shade(col, 1.1)
                    if front_belly and y >= c.h - 2:        # row 0 is the back edge: the front rows are chest
                        col = mix(c.pick(P["belly"]), col, 0.15 if y == c.h - 1 else 0.5)
                    if x in (0, c.w - 1):
                        col = shade(col, 0.92)
                else:
                    col = shade(col, bottom_dark)
                c.set(x, y, col)
        if f != "bottom":
            strokes(c, P, skip=(lambda x, y: f == "front" and min(x, c.w - 1 - x) >= 1) if front_belly else None)
        if f in ("back", "top"):                           # a few sunlit hairs
            for _ in range(int(c.w * c.h * 0.05) + 1):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                c.set(x, y, mix(c.get(x, y), c.pick(P["hi"]), 0.55))
    return p


def neck_paint(P):
    """Cream throat in front, the coat round the back and sides, darker along the nape."""
    def p(c):
        torso(P, y0=0, span=12)(c)
        if c.face == "top":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, mix(c.get(x, y), c.pick(P["back"]), 0.4))
    return p


def pouch_paint(P):
    """The doe's pouch: a soft bulge of belly fur, a little warmer and shaded under its round
    bottom; the top face is the opening, a dark slit behind a pale furred lip."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["belly"])
                if f == "front":
                    edge = min(x, c.w - 1 - x)
                    if y == 0:
                        col = mix(col, P["pouch_rim"], 0.35)          # the rolled lip
                    elif y == c.h - 1:
                        col = shade(c.pick(P["belly_sh"]), 0.95)
                    if edge == 0:
                        col = mix(col, c.pick(P["belly_sh"]), 0.6)
                elif f == "top":
                    if y >= c.h - 1:
                        col = mix(col, P["pouch_rim"], 0.3)
                    else:
                        col = P["pouch_in"]
                    if x in (0, c.w - 1):
                        col = c.pick(P["belly_sh"])
                elif f == "bottom":
                    col = shade(c.pick(P["belly_sh"]), 0.85)
                elif f in ("left", "right"):
                    col = mix(c.pick(P["belly_sh"]), c.pick(P["coat"]), 0.3)
                    if y == 0:
                        col = mix(col, P["pouch_rim"], 0.3)
                c.set(x, y, col)
        if f == "front":
            strokes(c, P, 0.08)
    return p


# -- head ----------------------------------------------------------------------------------------------
def cranium(P):
    """5 wide x 4 tall x 5 deep. The face front is the forehead (the muzzle covers its lower middle);
    the sides carry the big dark lashed eye near the front, a pale ring under it, and the white cheek
    stripe running back along the bottom from the muzzle."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(P["coat"]), 1.06 - 0.05 * y)
                if f == "front":
                    if y == 0:
                        col = mix(col, c.pick(P["back"]), 0.45)
                    elif x == c.w // 2 and y == 1:
                        col = mix(col, c.pick(P["back"]), 0.6)      # a darker blaze between the eyes
                elif f == "top":
                    d = abs(x - (c.w - 1) / 2)
                    col = mix(c.pick(P["back"]), c.pick(P["coat"]), min(1.0, d / 1.5))
                    col = shade(col, 1.08)
                elif f == "bottom":
                    col = c.pick(P["belly"]) if y < c.h - 1 else c.pick(P["belly_sh"])
                elif f == "back":
                    col = shade(c.pick(P["coat"]), 0.98)
                c.set(x, y, col)
        if f in ("left", "right"):
            # the big dark eye: two rows, the front-top pixel a bright glint, the iris brown
            c.set(fx(c, 1), 1, P["glint"])
            c.set(fx(c, 2), 1, P["eye"])
            c.set(fx(c, 1), 2, P["iris"])
            c.set(fx(c, 2), 2, P["eye"])
            c.set(fx(c, 3), 1, mix(P["lid"], c.pick(P["coat"]), 0.4))
            c.set(fx(c, 1), 0, P["lash"])                   # lashes along the top lid
            c.set(fx(c, 2), 0, P["lash"])
            c.set(fx(c, 3), 0, mix(P["lash"], c.pick(P["coat"]), 0.6))
            c.set(fx(c, 0), 1, mix(P["lid"], c.pick(P["coat"]), 0.5))
            c.set(fx(c, 0), 2, P["ring"])                   # pale ring under the front of the eye
            # the white cheek stripe along the bottom, from the muzzle back under the eye
            c.set(fx(c, 0), 3, P["white"])
            c.set(fx(c, 1), 3, P["white"])
            c.set(fx(c, 2), 3, P["white_sh"])
            c.set(fx(c, 3), 3, mix(P["white_sh"], c.pick(P["coat"]), 0.55))
            c.set(fx(c, 2), 2, P["eye"])
            c.set(fx(c, 3), 2, mix(P["ring"], c.pick(P["coat"]), 0.5))
            # cheek fur behind the eye a touch lighter
            c.set(fx(c, 4), 2, mix(c.get(fx(c, 4), 2), c.pick(P["hi"]), 0.4))
    return p


def muzzle(P):
    """3 x 3 x 4: the long muzzle. The big dark nose pad wraps over the front of the top and down the
    front; a black whisker patch on each side with the white stripe under it climbing back from the
    corner of the mouth; a cream chin."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["muzzle"])
                if f == "top":
                    d = c.h - 1 - y                         # 0 at the front
                    if d == 0:
                        col = P["nose"] if 0 < x < c.w - 1 else mix(P["nose"], c.pick(P["muzzle"]), 0.4)
                    elif d == c.h - 1:
                        col = mix(c.pick(P["coat"]), c.pick(P["muzzle"]), 0.3)
                    else:
                        col = mix(c.pick(P["coat"]), c.pick(P["muzzle"]), 0.55 + 0.15 * (c.h - 1 - d))
                    col = shade(col, 1.05)
                elif f == "front":
                    if y == 0:
                        col = P["nostril"] if x in (0, c.w - 1) else P["nose_hi"]
                    elif y == 1:
                        col = P["nose"]
                    else:
                        col = mix(P["nose"], c.pick(P["muzzle"]), 0.5) if x == 1 else c.pick(P["muzzle"])
                elif f == "bottom":
                    col = c.pick(P["belly"])
                elif f in ("left", "right"):
                    i = fx(c, x)                            # 0 at the nose
                    if i == 0:
                        col = P["nose"] if y < 2 else c.pick(P["muzzle"])
                    elif y == 0:
                        col = P["whisker"] if i == 1 else mix(c.pick(P["coat"]), c.pick(P["muzzle"]), 0.5)
                    elif y == 1:
                        col = mix(P["whisker"], c.pick(P["muzzle"]), 0.35) if i == 1 else P["white"]
                    else:
                        col = P["white"] if i == 1 else c.pick(P["muzzle"])
                    if i == c.w - 1 and y == 0:
                        col = c.pick(P["coat"])
                elif f == "back":
                    col = c.pick(P["coat"])
                c.set(x, y, col)
        if f in ("left", "right"):
            c.set(fx(c, 0), 2, mix(P["nose"], c.pick(P["muzzle"]), 0.55))   # the mouth line
    return p


def ear(P, piece):
    """Tall upright ears, built as a stepped point (base 3 wide, middle 2, tip 1). The front face is
    the inside of the ear: pale with whitish hairs, a dark rim up the outer edge and over the tip; the
    back is the coat. Column 0 of the front face is the outer edge (the texture mirrors for the left
    ear)."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "front":
                    if piece == "tip":
                        col = P["ear_rim"]
                    elif x == 0:
                        col = mix(c.pick(P["coat"]), P["ear_rim"], 0.3 if piece == "base" else 0.55)
                    elif x == c.w - 1 and piece == "base":
                        col = P["ear_hair"] if y < c.h - 1 else c.pick(P["ear_in"])   # the hairy inner fold
                    else:
                        col = c.pick(P["ear_in"]) if hsh(x, y, c.x0, c.y0) > 0.3 else P["ear_hair"]
                        if piece == "base" and y == c.h - 1:
                            col = shade(col, 0.86)
                        if piece == "mid" and y == 0:
                            col = mix(col, P["ear_rim"], 0.35)
                elif f == "back":
                    col = shade(c.pick(P["coat"]), 1.03)
                    if piece == "tip" or (piece == "mid" and y == 0):
                        col = mix(col, P["ear_rim"], 0.55)
                elif f in ("left", "right"):
                    col = mix(c.pick(P["coat"]), P["ear_rim"], 0.3 if piece != "tip" else 0.7)
                elif f == "top":
                    col = mix(c.pick(P["coat"]), P["ear_rim"], 0.5)
                else:
                    col = c.pick(P["coat"])
                c.set(x, y, col)
    return p


# -- arms ----------------------------------------------------------------------------------------------
def arm_paint(P):
    """The forearm: coat on the outside, paler on the inner and front faces, lighter at the shoulder."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(P["coat"]), 1.07 - 0.12 * y / max(1, c.h - 1))
                if f in ("front", "left"):
                    col = mix(col, c.pick(P["belly"]), 0.35 if f == "front" else 0.5)
                elif f == "back":
                    col = shade(col, 0.92)
                elif f == "bottom":
                    col = c.pick(P["paw"])
                c.set(x, y, col)
        if f == "right" and P["kind"] == "buck":           # a buck's brawny forearm catches the light
            for y in (1, 2):
                c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), c.pick(P["hi"]), 0.6))
    return p


def paw_paint(P):
    """The dark hand, three black claws along the front of its underside."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["paw"])
                if f in SIDES and y == 0:
                    col = mix(col, c.pick(P["coat"]), 0.35)
                c.set(x, y, col)
        if f == "front":
            for x in range(c.w):
                c.set(x, c.h - 1, P["claw"])
        if f == "bottom":
            for x in range(c.w):
                c.set(x, 0, P["claw"])
    return p


# -- legs ----------------------------------------------------------------------------------------------
def thigh_paint(P):
    """The huge drumstick thigh. It hangs from the hip in its own space and the rest pose swings it
    forward, so its back face looks up and back (lit) and its front face down and forward (pale). The
    outer side has a sheen over the big muscle and darkens toward the knee; the inner side is pale."""
    def p(c):
        f = c.face
        cx, cy = (c.w - 1) / 2, (c.h - 1) * 0.4
        for y in range(c.h):
            for x in range(c.w):
                col = shade(c.pick(P["coat"]), 1.04 - 0.16 * y / max(1, c.h - 1))
                if f == "right":                            # outer face (mirrored for the left leg)
                    dx, dy = (x - cx) / (c.w / 2), (y - cy) / (c.h / 2)
                    if dx * dx + dy * dy < 0.35:
                        col = mix(col, c.pick(P["hi"]), 0.45)
                    if fx(c, x) == 0:
                        col = mix(col, c.pick(P["belly"]), 0.35)
                elif f == "left":                           # inner face
                    col = mix(col, c.pick(P["belly"]), 0.55)
                elif f == "front":
                    col = mix(col, c.pick(P["belly"]), 0.45 if x == c.w - 1 else 0.12)
                elif f == "back":
                    col = shade(col, 1.06)
                    if x == 0 or x == c.w - 1:
                        col = mix(col, c.pick(P["back"]), 0.3)
                elif f == "bottom":
                    col = shade(col, 0.82)
                c.set(x, y, col)
        if f in ("right", "back"):
            strokes(c, P, 0.12)
        if f == "right":                                    # a darker rim round the knee end and the back
            for x in range(c.w):
                c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.82))
            for y in range(c.h):
                i = fx(c, c.w - 1)
                c.set(i, y, shade(c.get(i, y), 0.88))
    return p


def shin_paint(P):
    """The long shin: coat at the knee, paling toward the heel, darker down its back edge."""
    def p(c):
        f = c.face
        for y in range(c.h):
            t = y / max(1, c.h - 1)
            for x in range(c.w):
                col = mix(c.pick(P["coat"]), c.pick(P["foot"]), 0.15 + 0.45 * t)
                if f == "back":
                    col = shade(col, 0.88)
                elif f == "left":
                    col = mix(col, c.pick(P["belly"]), 0.4)
                elif f == "front":
                    col = shade(col, 1.05)
                c.set(x, y, col)
    return p


def foot_paint(P):
    """The long narrow hind foot lying flat: pale tan on top, warming to the coat at the heel, a dark
    edge along the sole, black claws at the toes."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["foot"])
                if f == "top":
                    d = y                                   # 0 at the heel (back)
                    if d <= 1:
                        col = mix(c.pick(P["coat"]), col, 0.3 + 0.35 * d)
                    if x in (0, c.w - 1):
                        col = shade(col, 0.93)
                    if y >= c.h - 2 and x == c.w // 2:
                        col = mix(col, c.pick(P["foot_dk"]), 0.5)   # the long fourth toe
                elif f in ("left", "right"):
                    i = fx(c, x)                            # 0 at the toes
                    if y == c.h - 1:
                        col = c.pick(P["sole"])
                    elif i >= c.w - 2:
                        col = mix(c.pick(P["coat"]), col, 0.4)
                    col = shade(col, 0.95 if f == "left" else 1.0)
                elif f == "front":
                    col = P["toe"] if y == c.h - 1 else mix(col, c.pick(P["foot_dk"]), 0.4)
                elif f == "back":
                    col = mix(c.pick(P["coat"]), c.pick(P["sole"]), 0.3 if y == c.h - 1 else 0.0)
                else:
                    col = c.pick(P["sole"])
                c.set(x, y, col)
    return p


def toe_paint(P):
    """The big middle toe and its black claw, sticking out past the foot."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["foot"]) if f == "top" else mix(c.pick(P["foot"]), c.pick(P["foot_dk"]), 0.35)
                if f == "front" or (f == "top" and y == 0) or (f in ("left", "right") and fx(c, x) == 0):
                    col = P["toe"]
                if f == "bottom":
                    col = c.pick(P["sole"])
                c.set(x, y, col)
    return p


# -- tail ----------------------------------------------------------------------------------------------
def tail_paint(P, seg, of):
    """The thick tail points back in its own space. Coat on top with a darker line down the middle,
    paler underneath; the last segment pales toward the tip."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["coat"])
                if seg == of - 1:                           # the tip segment: pale toward the end
                    along = (c.h - 1 - y) if f in ("top", "bottom") else (fx(c, x) if f in ("left", "right") else 0)
                    if f in ("top", "bottom"):
                        t = 1.0 - y / max(1, c.h - 1)
                    elif f in ("left", "right"):
                        t = 1.0 - fx(c, x) / max(1, c.w - 1)
                    else:
                        t = 1.0 if f == "back" else 0.0
                    col = mix(col, c.pick(P["tail_tip"]), 0.15 + 0.75 * t)
                if f == "top":
                    d = abs(x - (c.w - 1) / 2) / max(1.0, c.w / 2)
                    col = shade(mix(col, c.pick(P["back"]), max(0.0, 0.6 - d)), 1.08)
                elif f == "bottom":
                    col = mix(col, c.pick(P["belly_sh"]), 0.55)
                elif f in ("left", "right"):
                    col = shade(col, 1.02 - 0.12 * y / max(1, c.h - 1))
                    if y == c.h - 1:
                        col = mix(col, c.pick(P["belly_sh"]), 0.35)
                c.set(x, y, col)
        if f in ("top", "left", "right"):
            strokes(c, P, 0.1)
    return p


# -- geometry ------------------------------------------------------------------------------------------
BODY_PIVOT = (0.0, 15.0, 2.0)
BODY_LEAN = 0.38                       # forward lean of the upright-authored body (rad)
HIP = (3.2, 15.5, 2.5)                 # thigh pivot (x is +/-)
THIGH_ROT, THIGH_LEN = -0.95, 6.0      # the thigh swings forward and down to the knee
SHIN_ROT, SHIN_LEN = 1.95, 7.0         # the shin folds back and down to the heel (relative)
TAIL_PIVOT = (0.0, 17.0, 6.5)
TAIL_ROT, TAIL_LEN = -0.78, 7.0
TIP_ROT = 0.7


def heel_world():
    """Where the heel (ankle) lands in model space at rest: (y, z)."""
    a1 = THIGH_ROT
    a2 = THIGH_ROT + SHIN_ROT
    y = HIP[1] + THIGH_LEN * math.cos(a1) + SHIN_LEN * math.cos(a2)
    z = HIP[2] + THIGH_LEN * math.sin(a1) + SHIN_LEN * math.sin(a2)
    return y, z


def make(texture_id, P):
    """Build the kangaroo with the given palette. Geometry is identical for buck, doe and joey."""
    m = Model("kangaroo", 64, 64, seed=5353, texture_id=texture_id)
    pk = Pack(m)

    # body: authored upright from the hip pivot (local -y is up), leaned forward by BODY_LEAN.
    # Haunches 8 wide, a 7-wide waist, a 6-wide chest, a short thick neck.
    body = m.part("body", BODY_PIVOT, (BODY_LEAN, 0, 0))
    pk.add(body, (-4, -7, -3), (8, 9, 7), faces(torso(P, y0=7, span=17)))
    pk.add(body, (-3.5, -5, 3.5), (7, 6, 2), faces(torso(P, front_belly=False, y0=9, span=17)), inflate=0.1)   # the round rump
    pk.add(body, (-3.5, -10.5, -2.75), (7, 4, 6), faces(torso(P, y0=4, span=17)), inflate=0.1)
    pk.add(body, (-3, -15, -2.5), (6, 6, 5), faces(torso(P, y0=0, span=17)))
    pk.add(body, (-2, -18, -2.2), (4, 3, 4), faces(neck_paint(P)), inflate=0.15)

    # the pouch: a bulge low on the belly, opening at the top
    pouch = body.part("pouch", (0, -1.5, -3))
    pk.add(pouch, (-3, -2.5, -1.6), (6, 5, 2), faces(pouch_paint(P)))

    # head on top of the neck, turned back level. A 5x4x5 skull, the long muzzle stepping down and
    # forward, tall ears.
    head = body.part("head", (0, -17.5, -1.2), (-BODY_LEAN, 0, 0))
    pk.add(head, (-2.5, -4, -2.5), (5, 4, 5), faces(cranium(P)))
    pk.add(head, (-1.5, -2.6, -6.5), (3, 3, 4), faces(muzzle(P)), inflate=0.12)
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        left = sx > 0
        e = head.part(name, (1.55 * sx, -3.6, 1.2), (-0.12, -0.3 * sx, 0.22 * sx))
        for piece, (ox, oy), size in (("base", (-1.5, -3), (3, 3, 1)), ("mid", (-1.5 + (0 if left else 1), -5), (2, 2, 1)),
                                       ("tip", (-1.5 + (0.5 if left else 1.5), -6), (1, 1, 1))):
            pk.add(e, (ox, oy, -0.5), size, None if left else faces(ear(P, piece)), mirror=left,
                   share="ear_" + piece, inflate=0.05 if piece == "base" else 0.0)

    # small forearms from the front of the chest, hanging forward with the paws loose
    for name, sx in (("right_arm", -1), ("left_arm", 1)):
        left = sx > 0
        a = body.part(name, (2.4 * sx, -13.5, -2.2), (-0.95, 0, -0.08 * sx))
        pk.add(a, (-1, -0.5, -1), (2, 5, 2), None if left else faces(arm_paint(P)), mirror=left,
               share="arm", inflate=0.1)
        pk.add(a, (-1, 4.2, -1.2), (2, 2, 2), None if left else faces(paw_paint(P)), mirror=left,
               share="paw", inflate=-0.05)

    # the tail: thick at the rump, curving down onto the ground, tapering to a pale tip
    tail = m.part("tail", TAIL_PIVOT, (TAIL_ROT, 0, 0))
    pk.add(tail, (-2, -2, -1.5), (4, 4, 8), faces(tail_paint(P, 0, 2)), inflate=0.15)
    tip = tail.part("tail_tip", (0, 0.4, TAIL_LEN), (TIP_ROT, 0, 0))
    pk.add(tip, (-1.5, -1.5, -0.5), (3, 3, 6), faces(tail_paint(P, 0, 2)), inflate=0.1)
    pk.add(tip, (-1, -1, 5), (2, 2, 4), faces(tail_paint(P, 1, 2)))

    # legs: the thigh from the hip, the shin folding back to the heel, the long foot flat on the
    # ground (its sole exactly at y 24)
    hy, hz = heel_world()
    for name, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        lg = m.part(name + "_leg", (HIP[0] * sx, HIP[1], HIP[2]), (THIGH_ROT, 0, 0))
        pk.add(lg, (-2, -2.5, -3), (4, 9, 6), None if left else faces(thigh_paint(P)), mirror=left,
               share="thigh", inflate=0.25)
        sh = lg.part(name + "_shin", (0, THIGH_LEN, 0), (SHIN_ROT, 0, 0))
        pk.add(sh, (-1, -1, -1), (2, SHIN_LEN + 1, 2), None if left else faces(shin_paint(P)), mirror=left,
               share="shin", inflate=0.05)
        ft = sh.part(name + "_foot", (0, SHIN_LEN, 0), (-(THIGH_ROT + SHIN_ROT), 0, 0))
        drop = 24.0 - hy                                  # from the heel down to the ground
        pk.add(ft, (-1.5, drop - 2, -8), (3, 2, 9), None if left else faces(foot_paint(P)), mirror=left,
               share="foot")
        pk.add(ft, (-1, drop - 1, -10), (2, 1, 2), None if left else faces(toe_paint(P)), mirror=left,
               share="toe")

    pk.apply()
    return m


def build():
    make(None, BUCK).save()
    make("kangaroo_doe", DOE).save(geometry=False)
    make("kangaroo_joey", JOEY).save(geometry=False)
    spawn_egg("kangaroo", "#b4532f", "#efe0c8", accent="#2d221e")


if __name__ == "__main__":
    build()

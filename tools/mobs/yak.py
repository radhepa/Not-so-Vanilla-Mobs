"""Yak: a huge, shaggy mountain yak. A deep barrel body with a big hump over the shoulders, all of it
under a mantle of long dark-brown hair that hangs in a ragged skirt almost to the knees, with a
fringe hanging off the chest and the rump. A heavy low-slung head with a shaggy forelock over the
eyes, small dark eyes with a glint, a pale cream muzzle with dark nostrils, small hairy ears and two
pale horns that sweep out, up and forward to darker tips. Stocky legs, dark hooves and a long
horse-like tail of hair.

The `fringe` part holds every long-hair cube (the mantle over the body and hump, the side skirts,
the chest and rump fringes). Shearing hides it and shows the short, curly, warmer-brown undercoat
painted on the body underneath. The horns are hidden on calves.

`yak_calf` is the calf on the same geometry (drawn at half scale): a lighter, warmer brown all over,
softer and fluffier, with a paler face."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Yak"
LOOT = [item("leather", 0, 2), item("beef", 1, 2)]
TAGS = ["freeze_immune_entity_types"]


# -- texture packing (as in otter.py): biggest cubes first, a 1 px clear margin round every cube ----
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
    """A repeatable 0..1 value for a position (hair lengths that match on both faces of a skirt)."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


SIDES = ("front", "back", "left", "right")

# -- palettes ----------------------------------------------------------------------------------------
ADULT = dict(
    kind="adult",
    hair=["#3b2a1f", "#3f2d21", "#36271c", "#412f23", "#3a291e"],       # the long outer coat
    strand_hi=["#5a4232", "#614736", "#553e2f"],                         # paler strands, sun-bleached
    strand_dk=["#251a13", "#2a1e16", "#22180f"],
    tip=["#6e5340", "#755a46", "#68503d"],                               # the ragged ends
    under=["#5c4130", "#634633", "#573d2c", "#684a37"],                 # short undercoat (sheared)
    under_hi=["#735440", "#785844"],
    under_dk=["#4b3524", "#503827"],
    face=["#3a2a1f", "#413024", "#36271c"],
    muzzle=["#d8cdb9", "#d1c5af", "#ded4c2"],
    muzzle_sh=["#b8ab95", "#b1a48d"],
    nose="#4a3d38", nostril="#2a201d", lip="#6f625a", pad="#8f807a",
    eye="#0e0a08", glint="#f4f1ea", eye_rim="#5a4232",
    horn=["#e9e0cb", "#e2d8c0", "#efe7d5"], horn_sh=["#c9bda2", "#c2b597"],
    horn_root=["#c4b89c", "#bcb093"], horn_tip=["#7a6f62", "#70665a"],
    ear_in="#5a4034",
    hoof=["#2a2523", "#25211f"], hoof_hi="#4a4440",
    leg=["#3a291e", "#36271c", "#3f2d21"],
)
CALF = dict(
    ADULT,
    kind="calf",
    hair=["#7a5638", "#805c3d", "#74512f", "#86613f"],
    strand_hi=["#9b7553", "#a27b58"],
    strand_dk=["#5e4029", "#63442c"],
    tip=["#b08a64", "#b8916a"],
    under=["#8a6544", "#916b49", "#84603f"],
    under_hi=["#a57e5a"],
    under_dk=["#6e4f33"],
    face=["#7a5638", "#83603f"],
    muzzle=["#e6dccb", "#ece4d6"],
    muzzle_sh=["#cbbfa9"],
    pad="#b09f98",
    leg=["#6e4f33", "#74532f"],
)


# -- hair ----------------------------------------------------------------------------------------------
def locks(n, seed):
    """Split n columns into locks of hair 2-3 px wide: for each column (lock id, position in the lock,
    lock width)."""
    out, lid, i = [], 0, 0
    while i < n + 3:
        w = 2 if hsh(lid, seed, 99) < 0.55 else 3
        for k in range(w):
            out.append((lid, k, w))
        i += w
        lid += 1
    return out


def lock_colour(P, c, lid, pos, w, y, seed):
    """One pixel of a lock: the lock has its own tone; its first column catches the light, its last
    sits in shadow; bands of a slightly different tone run down it."""
    r = hsh(lid, seed, 3)
    col = c.pick(P["hair"])
    if r < 0.25:
        col = mix(col, c.pick(P["strand_hi"]), 0.5)
    elif r > 0.8:
        col = mix(col, c.pick(P["strand_dk"]), 0.6)
    band = hsh(lid, (y + int(hsh(lid, 5) * 3)) // 3, seed, 7)  # the lock waves: lighter and
    if band < 0.3:                                          # darker stretches down its length
        col = mix(col, c.pick(P["strand_hi"]), 0.3)
    elif band > 0.8:
        col = shade(col, 0.88)
    if pos == 0:
        col = mix(col, c.pick(P["strand_hi"]), 0.25)
    elif pos == w - 1 and hsh(lid, y, seed, 8) < 0.7:
        col = shade(col, 0.86)
    if hsh(lid, pos, y, seed) < 0.03:
        col = c.pick(P["strand_dk"])                          # a stray dark hair
    return col


def long_hair(P, top=1.12, grad=0.34, seed=0, y0=0, span=None):
    """The long outer coat. Sides and ends hang in locks (light edge, dark edge, darkening downward);
    on top the hair parts along the spine and falls away to either side in short combed strokes."""
    def p(c):
        sp = span or c.h
        f = c.face
        if f == "bottom":
            for y in range(c.h):
                for x in range(c.w):
                    c.set(x, y, shade(c.pick(P["strand_dk"]), 0.85))
            return
        if f == "top":
            mid = (c.w - 1) / 2
            for y in range(c.h):
                for x in range(c.w):
                    d = abs(x - mid) / max(1.0, mid)           # 0 at the spine, 1 at the edge
                    col = c.pick(P["hair"])
                    if hsh(x // 2, y, seed, 11) < 0.3:
                        col = mix(col, c.pick(P["strand_hi"]), 0.6)   # combed strokes, across
                    if abs(x - mid) < 1:
                        col = shade(c.pick(P["strand_dk"]), 1.1)       # the parting
                    c.set(x, y, shade(col, top - 0.12 * d))
            return
        ls = locks(c.w, seed + len(f))
        for x in range(c.w):
            i = fx(c, x) if f in ("left", "right") else x
            lid, pos, w = ls[i]
            for y in range(c.h):
                col = lock_colour(P, c, lid, pos, w, y, seed)
                c.set(x, y, shade(col, 1.1 - grad * ((y0 + y + 0.5) / sp)))
    return p


def skirt(P, axis, n, seed=0, ragged=2):
    """A hanging curtain of long hair, 1 px thick, n columns long along `axis` ("z" for the side
    skirts, "x" for the chest and rump fringes), hanging in locks with ragged, paler ends. Every face
    finds a pixel's column by its position, so the inside, outside and thin edges are cut alike and
    the cut-outs see through cleanly. The bottom is left open."""
    ls = locks(n, seed)

    def strand(c, x):
        f = c.face
        if axis == "z":
            if f in ("left", "right"):
                return fx(c, x)
            return 0 if f == "front" else n - 1
        if f == "front":
            return x
        if f == "back":
            return c.w - 1 - x
        return 0 if f == "right" else n - 1

    def p(c):
        f = c.face
        if f in ("top", "bottom"):
            for y in range(c.h):
                for x in range(c.w):
                    if f == "top":
                        c.set(x, y, c.pick(P["hair"]))
                    else:
                        c.clear(x, y)
            return
        for x in range(c.w):
            i = strand(c, x)
            lid, pos, w = ls[i]
            short = int(hsh(lid, seed, 77) * (ragged + 1))   # the whole lock is cut about the same,
            if pos == w - 1 and hsh(i, seed, 78) < 0.5:       # its shadow edge sometimes a pixel more
                short += 1
            end = c.h - min(short, ragged) - 1
            for y in range(c.h):
                if y > end:
                    c.clear(x, y)
                    continue
                col = lock_colour(P, c, lid, pos, w, y, seed)
                if y >= end - 1:
                    col = mix(col, c.pick(P["tip"]), 0.55 if y == end else 0.25)
                c.set(x, y, shade(col, 1.02 - 0.2 * y / max(1, c.h - 1)))
    return p


def undercoat(P, top=1.1, grad=0.28, y0=0, span=None):
    """The short, dense, curly undercoat a sheared yak shows: warmer brown in little tufts."""
    def p(c):
        sp = span or c.h
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["under"])
                r = hsh(x, y, c.x0, c.y0)
                if r < 0.16:
                    col = c.pick(P["under_hi"])
                elif r > 0.84:
                    col = c.pick(P["under_dk"])
                if c.face == "top":
                    f = top
                elif c.face == "bottom":
                    f = 0.72
                else:
                    f = 1.06 - grad * ((y0 + y + 0.5) / sp)
                c.set(x, y, shade(col, f))
        # curls: a light pixel with a dark one under it, here and there
        for _ in range(int(c.w * c.h * 0.05)):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h - 1) if c.h > 1 else 0
            c.set(x, y, mix(c.get(x, y), c.pick(P["under_hi"]), 0.5))
            if c.inside(x, y + 1):
                c.set(x, y + 1, shade(c.get(x, y + 1), 0.85))
    return p


# -- head ----------------------------------------------------------------------------------------------
def head_hair(P, seed=3):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["face"])
                if hsh(x, y, seed) < 0.18:
                    col = c.pick(P["strand_hi"])
                f = 1.1 if c.face == "top" else (0.8 if c.face == "bottom" else 1.04 - 0.18 * y / max(1, c.h - 1))
                c.set(x, y, shade(col, f))
    return p


def skull_side(P):
    """7 tall x 6 deep. A small dark eye with a glint near the front, under the forelock's edge; the
    shaggy cheek below."""
    def p(c):
        head_hair(P)(c)
        e = fx(c, 1)
        c.set(e, 2, P["glint"]); c.set(fx(c, 2), 2, P["eye"])
        c.set(e, 3, P["eye"]); c.set(fx(c, 2), 3, shade(P["eye"], 0.8))
        c.set(e, 4, P["eye_rim"]); c.set(fx(c, 2), 4, P["eye_rim"])
        c.set(fx(c, 3), 3, P["eye_rim"])
        for y in range(4, c.h):                                # long cheek hair streaks
            for x in range(c.w):
                if hsh(fx(c, x), 31) < 0.3:
                    c.set(x, y, shade(c.get(x, y), 1.15))
        for y in range(c.h - 2, c.h):                          # the muzzle colour creeps back
            c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), c.pick(P["muzzle"]), 0.35))
    return p


def skull_front(P):
    """8 wide x 7 tall: the forelock covers the top rows, the muzzle the lower middle. The face is
    dark, a little paler between the eyes."""
    def p(c):
        head_hair(P)(c)
        for y in range(2, 5):
            for x in range(2, c.w - 2):
                c.set(x, y, mix(c.get(x, y), c.pick(P["strand_hi"]), 0.3))
    return p


def forelock(P):
    """The shaggy tuft on top of the head: long strands combed forward, the front edge ragged where
    it hangs over the brow."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f == "front" and y == c.h - 1 and hsh(x, 13) < 0.45:
                    c.clear(x, y)
                    continue
                col = c.pick(P["hair"])
                r = hsh(x, y, 17, f == "top")
                if r < 0.25:
                    col = c.pick(P["strand_hi"])
                elif r > 0.85:
                    col = c.pick(P["strand_dk"])
                if f == "front" and y == c.h - 1:
                    col = mix(col, c.pick(P["tip"]), 0.4)
                k = 1.14 if f == "top" else (0.8 if f == "bottom" else 1.04 - 0.12 * y)
                c.set(x, y, shade(col, k))
    return p


def muzzle(P):
    """The broad pale muzzle: cream, greying underneath, a dark pinkish-grey nose pad with two big
    nostrils on the front and a dark mouth line along the sides."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(P["muzzle"])
                if f == "bottom":
                    col = c.pick(P["muzzle_sh"])
                elif f in ("left", "right", "back"):
                    col = shade(col, 1.0 - 0.05 * y)
                    if y == c.h - 2 and fx(c, x) <= 1:
                        col = P["lip"]                         # the mouth line
                elif f == "top":
                    if y == 0:
                        col = mix(col, c.pick(P["face"]), 0.5)  # blending into the face
                c.set(x, y, col)
        if f == "front":                                       # 6 x 4
            for y in range(c.h):
                for x in range(c.w):
                    col = c.pick(P["muzzle"])
                    if x in (0, c.w - 1):
                        col = shade(col, 0.9)                  # rounded at the sides
                    if y == c.h - 1:
                        col = c.pick(P["muzzle_sh"])
                    c.set(x, y, col)
            for x in (1, c.w - 2):                             # two nostrils, slanting outward
                c.set(x, 1, P["nostril"])
                c.set(x, 0, mix(P["pad"], c.pick(P["muzzle"]), 0.5))
            c.set(2, 1, mix(P["pad"], c.pick(P["muzzle"]), 0.55))
            c.set(3, 1, mix(P["pad"], c.pick(P["muzzle"]), 0.55))
            for x in range(2, c.w - 2):                        # the parting of the lips
                c.set(x, 2, mix(P["lip"], c.pick(P["muzzle"]), 0.45))
        if f == "top":
            c.set(1, c.h - 1, mix(P["pad"], c.pick(P["muzzle"]), 0.5))
            c.set(c.w - 2, c.h - 1, mix(P["pad"], c.pick(P["muzzle"]), 0.5))
    return p


def ear(P):
    def p(c):
        head_hair(P, seed=21)(c)
        if c.face == "front":
            for x in range(c.w):
                c.set(x, c.h - 1, P["ear_in"])
            c.set(c.w - 1, 0, P["ear_in"])
    return p


def horn(P, part):
    """Pale ivory horns: a greyer, ridged root, smooth cream mid-sections lit on top, darkening to
    grey-brown tips."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if part == "root":
                    col = c.pick(P["horn_root"])
                    if f in SIDES and x % 2 == 1:
                        col = shade(col, 0.88)                 # growth rings
                elif part == "tip":
                    # along the tip (x on the long faces) it greys toward the point (column 0 on the
                    # right horn's front face is the outer end)
                    if f in ("front", "top", "bottom"):
                        t = 1 - x / max(1, c.w - 1)
                    elif f == "back":
                        t = x / max(1, c.w - 1)
                    else:
                        t = 1.0 if f == "right" else 0.0
                    col = mix(c.pick(P["horn"]), c.pick(P["horn_tip"]), 0.25 + 0.75 * t)
                else:
                    col = c.pick(P["horn"])
                    if f in ("bottom", "back", "left"):
                        col = c.pick(P["horn_sh"])
                    if part == "upper" and f != "bottom" and y == 0:
                        col = mix(col, c.pick(P["horn_tip"]), 0.3)
                if f == "top":
                    col = shade(col, 1.06)
                c.set(x, y, col)
    return p


# -- legs and tail --------------------------------------------------------------------------------------
def leg(P):
    """Stocky legs: shaggy dark hair, a few long strands at the top, a 2 px cloven hoof at the bottom."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if y >= c.h - 2:
                    col = c.pick(P["hoof"])
                    if y == c.h - 2 and f in SIDES:
                        col = mix(col, P["hoof_hi"], 0.5)
                else:
                    col = c.pick(P["leg"])
                    if hsh(x, y // 2, c.x0, 3) < 0.2:
                        col = c.pick(P["strand_hi"])
                    col = shade(col, 1.06 - 0.22 * y / max(1, c.h - 3))
                    if y == c.h - 3 and f in SIDES:
                        col = mix(col, c.pick(P["tip"]), 0.35)   # the fetlock hair
                c.set(x, y, col)
        if f == "front":
            c.set(c.w // 2, c.h - 1, shade(P["hoof"][0], 0.6))
            c.set(c.w // 2 - 1, c.h - 1, shade(P["hoof"][0], 0.8))
    return p


def sole(P):
    def p(c):
        c.noise(P["hoof"])
        c.set(c.w // 2, c.h // 2, shade(P["hoof"][0], 0.6))
    return p


def tail_root(P):
    def p(c):
        head_hair(P, seed=41)(c)
    return p


def tail_tuft(P):
    """The long switch of hair at the end of the tail, strands paling toward ragged ends."""
    def p(c):
        f = c.face
        for y in range(c.h):
            for x in range(c.w):
                if f in SIDES and y == c.h - 1 and hsh(x, len(f), 51) < 0.5:
                    c.clear(x, y)
                    continue
                col = c.pick(P["hair"])
                if hsh(x, y // 2, len(f), 53) < 0.25:
                    col = c.pick(P["strand_hi"])
                if y >= c.h - 2:
                    col = mix(col, c.pick(P["tip"]), 0.4)
                c.set(x, y, shade(col, 1.05 - 0.15 * y / max(1, c.h - 1)))
    return p


# -- the model -------------------------------------------------------------------------------------------
def make(texture_id, P):
    """Build the yak with the given palette. Geometry is identical for adult and calf."""
    m = Model("yak", 128, 128, seed=2828, texture_id=texture_id)
    pk = Pack(m)

    # body: pivot (0, 10, 0). Shoulders x -6..6, y 4..16, z -10..0; the hump x -4..4, y 1..4 over
    # them; the back steps down behind the hump (y 3, z -2..3) to the rear x -6..6, y 6..15, z 0..11.
    # Painted as the short undercoat.
    body = m.part("body", (0, 10, 0))
    BODY = [((-6, -6, -10), (12, 12, 10), 0, 12, 0.28),
            ((-6, -4, 0), (12, 9, 11), 2, 12, 0.28),
            ((-4, -9, -9), (8, 3, 8), 0, 3, 0.1),
            ((-5, -7, -2), (10, 3, 5), 0, 3, 0.1)]
    for origin, size, y0, span, grad in BODY:
        pk.add(body, origin, size, faces(undercoat(P, y0=y0, span=span, grad=grad)))

    # fringe: the long coat. A mantle half a pixel out over shoulders, rear and hump, then ragged
    # skirts hanging from mid-flank to the knees (y 11..21), and fringes off the chest and rump.
    fringe = body.part("fringe")
    for k, (origin, size, y0, span, grad) in enumerate(BODY):
        pk.add(fringe, origin, size, faces(long_hair(P, y0=y0, span=span, grad=grad + 0.06, seed=k + 1)),
               inflate=0.5)
    for sx in (-1, 1):
        left = sx > 0
        pk.add(fringe, (6.5 if left else -7.5, 1, -10.5), (1, 10, 22), None if left else faces(skirt(P, "z", 22, seed=4)),
               mirror=left, share="skirt")
    pk.add(fringe, (-6, -1, -11.5), (12, 10, 1), faces(skirt(P, "x", 12, seed=5)))   # chest fringe
    pk.add(fringe, (-6, 1, 11.5), (12, 9, 1), faces(skirt(P, "x", 12, seed=6)))    # rump fringe

    # tail: from the top of the rump, hanging, a long switch of hair
    tail = body.part("tail", (0, -4, 12.5), (0.12, 0, 0))
    pk.add(tail, (-1, 0, -1), (2, 4, 2), faces(tail_root(P)))
    pk.add(tail, (-1.5, 3, -1.5), (3, 8, 3), faces(tail_tuft(P)))

    # head: child of root, carried low in front of the chest. Skull 8 wide, the pale muzzle 6 wide
    # stepping down and forward, a shaggy forelock over the brow.
    head = m.part("head", (0, 9, -10))
    pk.add(head, (-4, -4, -6), (8, 7, 6),
           faces(head_hair(P), front=skull_front(P), right=skull_side(P), left=skull_side(P)))
    pk.add(head, (-3, 0, -9), (6, 4, 3), faces(muzzle(P)))
    pk.add(head, (-4.5, -5, -6.5), (9, 3, 5), faces(forelock(P)))
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        left = sx > 0
        e = head.part(name, (4 * sx, -0.5, -2.5), (0, 0, 0.35 * -sx))
        pk.add(e, (0 if left else -3, -1, -1), (3, 2, 1), None if left else faces(ear(P)), mirror=left, share="ear")

    # horns: a chain of three segments out of the top corners of the skull, each bending further
    # up, the thin tips turning forward
    for name, sx in (("right_horn", -1), ("left_horn", 1)):
        left = sx > 0
        chain = [(name, (3.5 * sx, -4, -3.5), (0, 0, 0.15 * -sx), (-3, -1, -1), (3, 2, 2), "root", 0.15),
                 (name + "_mid", (3 * sx, 0, 0), (0, 0, 0.75 * -sx), (-3, -1, -1), (3, 2, 2), "mid", 0.0),
                 (name + "_tip", (3 * sx, 0, 0), (0, 0.5 * sx, 0.55 * -sx), (-3, -0.5, -0.5), (3, 1, 1), "tip", 0.0)]
        parent = head
        for pname, pivot, rot, (ox, oy, oz), size, seg, inf in chain:
            parent = parent.part(pname, pivot, rot)
            if left:
                ox = -(ox + size[0])
            pk.add(parent, (ox, oy, oz), size, None if left else faces(horn(P, seg)), mirror=left,
                   share="horn_" + seg, inflate=inf)

    # legs: stocky, pivot under the body, hooves on y 24
    legp = faces(leg(P), bottom=sole(P))
    for name, x, z in (("right_front_leg", -3.5, -6), ("left_front_leg", 3.5, -6),
                       ("right_hind_leg", -3.5, 7), ("left_hind_leg", 3.5, 7)):
        lg = m.part(name, (x, 15, z))
        left = name.startswith("left")
        pk.add(lg, (-2, -1, -2), (4, 10, 4), None if left else legp, mirror=left, share="leg")

    pk.apply()
    return m


def build():
    make(None, ADULT).save()
    make("yak_calf", CALF).save(geometry=False)
    spawn_egg("yak", "#3b2a1f", "#d8cdb9", accent="#e9e0cb")


if __name__ == "__main__":
    build()

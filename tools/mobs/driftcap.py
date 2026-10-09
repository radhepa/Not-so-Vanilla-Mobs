"""Driftcap: a floating jellyfish made of warped fungus, drifting through the Warped Forest. A stepped
dome cap in deep warped-wart teal with darker blotches, a jelly-bright sheen and a few glowing
cyan-turquoise spots; a flared rim whose underside is a dark purple-blue gill fringe; a frilly
scalloped skirt hanging round the rim (cut-out planes); a faintly glowing teal core hanging under the
cap; and six long dangling tendrils like twisting vines (crossed cut-out planes with leafy notches)
ending in glowing cyan buds. Cutout only, so the jelly feel comes from bright colours, not alpha."""
import math
import random

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Driftcap"
LOOT = [item("twisting_vines", 0, 2), item("warped_fungus", 0, 1), item("ender_pearl", chance=0.08, looting=False, player_only=True)]
TAGS = ["fall_damage_immune"]


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0):
        self.items.append((part, origin, size, paint, mirror, share, inflate))

    def apply(self):
        def dims(size):
            w, h, d = (int(math.ceil(s)) for s in size)
            return 2 * d + 2 * w, d + h
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


def soft_glow(c, x, y, col, k):
    """Split col between the base texture (1 - k) and the additive emissive layer (k)."""
    if not c.inside(x, y):
        return
    c.set(x, y, shade(col, 1.0 - k))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), shade(col, k))


def _h(x, y, salt):
    return random.Random(x * 7919 + y * 104729 + salt * 15485863).random()


# -- palette -----------------------------------------------------------------------------------------
TEAL = ["#167e86", "#1a8f8a", "#178583"]
TEAL_DK = ["#14686e", "#0f5c5f"]
TEAL_LT = ["#24a39c", "#2bb0a7"]
SHEEN = "#5fd3c6"
SPOT = "#3ff2e0"
SPOT_HI = "#8afff0"
GILL = ["#2b1d3a", "#3a2550"]
GILL_LT = "#4a3066"
FRILL = ["#3a2550", "#432b5c", "#3e2856"]
FRILL_LT = ["#5b3d7a", "#644585"]
CORE = ["#3fbfb3", "#45c8bb", "#39b5aa"]
CORE_GLOW = "#5ff0dd"
STEM = ["#0e7e78", "#0d7570"]
LEAF = ["#15a09a", "#18aaa3"]
LEAF_LT = "#2cc4b8"


# -- the cap -----------------------------------------------------------------------------------------
def spot(c, x, y, big=False):
    """A glowing spot: a bright core, and on big ones a cross of turquoise round it."""
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            soft_glow(c, x + dx, y + dy, SPOT, 0.6)
        soft_glow(c, x, y, SPOT_HI, 0.7)
    else:
        soft_glow(c, x, y, SPOT if c.rng.random() < 0.6 else SPOT_HI, 0.65)


def wart(top=1.07, low=0.72, spots=(), big=(), sheen=(), blotch=0.12):
    """Warped-wart teal: noise, darker blotches of a few pixels, side faces darkening toward the
    bottom, a jelly-bright sheen where given and glowing spots (face-local pixel lists)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(TEAL)
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.06 - (1.06 - low) * y / (c.h - 1))
                    if y == 0:
                        col = mix(col, c.pick(TEAL_LT), 0.5)
                elif c.face == "top":
                    col = shade(col, top)
                elif c.face == "bottom":
                    col = shade(col, 0.6)
                c.set(x, y, col)
        for _ in range(max(1, int(c.w * c.h * blotch / 3))):    # darker blotches, 2-4 px each
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))[:c.rng.randint(2, 4)]:
                if c.inside(x + dx, y + dy):
                    c.set(x + dx, y + dy, mix(c.get(x + dx, y + dy), c.pick(TEAL_DK), 0.7))
        c.speckle(TEAL_LT, 0.03)
        for (x, y) in sheen:
            c.set(x, y, mix(c.get(x, y), SHEEN, 0.7))
        for (x, y) in spots:
            spot(c, x, y)
        for (x, y) in big:
            spot(c, x, y, big=True)
    return p


def rim_side(c):
    """The flared lip of the bell: a bright jelly edge over the dark gill fringe."""
    for x in range(c.w):
        c.set(x, 0, mix(c.pick(TEAL_LT), SHEEN, 0.25 if (x + c.w) % 3 else 0.0))
    if c.h > 1:
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(GILL))


def rim_top(c):
    wart(top=1.12, blotch=0.05)(c)
    for x in range(c.w):
        for y in (0, c.h - 1):
            c.set(x, y, mix(c.get(x, y), SHEEN, 0.35))
    for y in range(c.h):
        for x in (0, c.w - 1):
            c.set(x, y, mix(c.get(x, y), SHEEN, 0.35))


def gills(c):
    """Underside of the cap: radial gills in warped-stem purple round the core, a teal margin."""
    cx, cy = (c.w - 1) / 2, (c.h - 1) / 2
    for y in range(c.h):
        for x in range(c.w):
            dx, dy = x - cx, y - cy
            r = max(abs(dx), abs(dy))
            a = math.atan2(dy, dx) / (2 * math.pi) * 20
            if r >= cx - 0.1:                                   # the margin: dark teal
                col = mix(c.pick(TEAL_DK), GILL[1], 0.3)
            elif r < 2:                                         # round the core
                col = GILL[0]
            else:
                col = GILL[1] if int(math.floor(a)) % 2 else GILL[0]
                if int(math.floor(a)) % 4 == 1 and r > 3:
                    col = GILL_LT
            c.set(x, y, col)


# -- skirt and tendrils: pure functions of position, so a plane's two faces match pixel for pixel ----
SKIRT_H = 3


def frill(u, y, w):
    """Scalloped frill, 4-px lobes: row 0 solid, row 1 in 3-px lobes, row 2 only the lobe tips.
    Returns a colour, a ('glow', colour) or None for a cut-out pixel."""
    k = u % 4
    if y == 1 and k == 3:
        return None
    if y == 2 and k != 1:
        return None
    if y == 2:
        return ("glow", SPOT) if _h(u, y, 9) < 0.35 else FRILL_LT[int(_h(u, y, 3) * 2)]
    if y == 1:
        return FRILL_LT[int(_h(u, y, 4) * 2)] if k != 1 else mix(FRILL_LT[0], FRILL[0], 0.4)
    return FRILL[int(_h(u, y, 5) * 3)]


def skirt(c):
    for y in range(c.h):
        for x in range(c.w):
            u = c.w - 1 - x if c.face in ("back", "right") else x
            v = frill(u, y, c.w)
            if v is None:
                c.clear(x, y)
            elif isinstance(v, tuple) and v[0] == "glow":
                soft_glow(c, x, y, v[1], 0.6)
            else:
                c.set(x, y, v)


def vine(length, salt):
    """Twisting-vine tendril, 3 px wide: a stem down the middle, leaves alternating side to side,
    ending in a glowing cyan bud. Rows from the top (where it hangs from the cap)."""
    rows = []
    off = int(_h(salt, 0, 1) * 4)
    for y in range(length - 3):
        row = [None, ("s", STEM[int(_h(1, y, salt) * 2)]), None]
        ph = (y + off) % 4
        if y >= 1 and ph in (0, 1):
            row[0] = ("l", LEAF_LT if ph == 0 else LEAF[int(_h(0, y, salt) * 2)])
        elif y >= 1 and ph in (2, 3):
            row[2] = ("l", LEAF_LT if ph == 2 else LEAF[int(_h(2, y, salt) * 2)])
        rows.append(row)
    rows.append([("l", LEAF_LT), ("s", mix(STEM[0], SPOT, 0.5)), None])
    rows.append([None, ("g", SPOT), ("g", mix(SPOT, LEAF[0], 0.4))])
    rows.append([None, ("g", SPOT_HI), None])
    rows[0] = [None, ("s", shade(STEM[0], 0.8)), None]

    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                u = c.w - 1 - x if c.face in ("back", "right") else x
                v = rows[y][u]
                if v is None:
                    c.clear(x, y)
                elif v[0] == "g":
                    soft_glow(c, x, y, v[1], 0.65)
                else:
                    c.set(x, y, shade(v[1], 1.0 - 0.15 * y / (c.h - 1)))
    return p


# -- the core ----------------------------------------------------------------------------------------
def core(glows):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CORE)
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.08 - 0.2 * y / (c.h - 1))
                elif c.face == "bottom":
                    col = shade(col, 0.85)
                c.set(x, y, col)
        for (x, y) in glows.get(c.face, ()):
            soft_glow(c, x, y, CORE_GLOW, 0.55)
    return p


def build():
    m = Model("driftcap", 64, 64, seed=4242)
    pk = Pack(m)

    # cap: pivot y 9. Crown y 4-6, shoulder y 6-7, bell y 7-10, flared rim y 10-11 (underside = gills)
    cap = m.part("cap", (0, 9, 0))
    pk.add(cap, (-4, -5, -4), (8, 2, 8), faces(
        wart(),
        top=wart(top=1.12, spots=((1, 1), (6, 6)), big=((5, 2),),
                 sheen=((1, 5), (2, 6), (1, 6), (2, 5), (3, 6))),
        front=wart(spots=((5, 1),)), left=wart(spots=((2, 0),))))
    pk.add(cap, (-5, -3, -5), (10, 1, 10), faces(
        wart(), top=wart(top=1.1, spots=((0, 3), (9, 6), (6, 9)), sheen=((0, 7), (0, 8), (1, 9)))))
    pk.add(cap, (-6, -2, -6), (12, 3, 12), faces(
        wart(),
        front=wart(spots=((2, 1),), big=((8, 1),)),
        back=wart(spots=((8, 1),), big=((3, 1),)),
        right=wart(spots=((9, 0),), big=((4, 1),)),
        left=wart(spots=((2, 2),), big=((7, 1),)),
        top=wart(top=1.1, spots=((11, 11),))))
    pk.add(cap, (-6.5, 1, -6.5), (13, 1, 13), faces(rim_side, top=rim_top, bottom=gills))

    # frilly skirt hanging just inside the rim: four cut-out planes sharing one texture block
    # (each side is its own part hinged at its top edge and flared out a little; local -z is outward)
    for name, (px, pz), yaw in (("skirt_front", (0, -5.5), 0.0), ("skirt_right", (-5.5, 0), math.pi / 2),
                                ("skirt_back", (0, 5.5), math.pi), ("skirt_left", (5.5, 0), -math.pi / 2)):
        sk = cap.part(name, (px, 2, pz), (-0.3, round(yaw, 5), 0))
        pk.add(sk, (-5.5, 0, 0), (11, SKIRT_H, 0), faces(skirt), share="skirt")

    # the faintly glowing core hanging under the cap (y 11-14) and a small bulb below it (y 14-17)
    co = cap.part("core", (0, 2, 0))
    pk.add(co, (-2, 0, -2), (4, 3, 4), faces(core({"front": ((1, 1), (3, 2)), "back": ((2, 1),),
                                                    "left": ((0, 2), (2, 0)), "right": ((3, 1),),
                                                    "bottom": ((1, 2), (2, 1))})))
    pk.add(co, (-1, 3, -1), (2, 3, 2), faces(core({"front": ((0, 1), (1, 2)), "back": ((1, 1),),
                                                    "left": ((1, 0), (0, 2)), "right": ((0, 1),),
                                                    "bottom": ((0, 0), (1, 1))})))

    # tendrils: a ring of six round the core, each two crossed cut-out vine planes hanging from y 11
    lengths = (12, 13, 11, 13, 12, 11)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        L = lengths[k]
        t = cap.part(f"tendril{k + 1}", (round(4 * math.cos(a), 3) + 0.0, 2, round(4 * math.sin(a), 3) + 0.0),
                     (0, round(math.pi / 4 + 0.35 * k, 4), 0))
        paint = faces(vine(L, L))
        pk.add(t, (-1.5, 0, 0), (3, L, 0), paint, share=f"vine_a{L}")
        pk.add(t, (0, 0, -1.5), (0, L, 3), paint, share=f"vine_b{L}")

    pk.apply()
    m.save()
    spawn_egg("driftcap", "#167e86", "#3ff2e0", accent="#3a2550")


if __name__ == "__main__":
    build()

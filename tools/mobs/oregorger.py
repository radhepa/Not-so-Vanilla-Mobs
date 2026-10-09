"""Oregorger: a massive armoured cave beast of the deep caves, part giant pangolin or armadillo, part
boulder. It eats ore veins and stores the ore in its armour, and it curls into a ball to bowl at you.

Low, wide and heavy: a domed back of overlapping deepslate-grey shingle plates (chiselled-deepslate
tiles with lit free edges and shadowed overlaps), stepping up in four tiers to a plated crown,
studded with chunks of raw ore poking out between the plates (raw iron, raw copper, raw gold), one
cyan diamond glint and a few faintly glowing redstone flecks. A low head peers out from under a
deepslate brow shield: small deep-set glowing amber eyes in a dark slot, a blunt shovel-like snout of
tough pale tuff with a wider digging blade at its front, and a crushing lower jaw lined with flat
stone teeth. Stubby powerful legs in dark scaly hide end in thick digging claws (dark, pale-tipped,
biggest on the front feet), and a heavy plated tail droops behind.

`ball` is the curled-up form (the code shows it only while rolling and hides body/head/legs): a round
armoured boulder 22 px across, built from a core and three crossed slabs, plated and ore-studded on
every side, the tail tip curled over the tucked snout on its front. Its pivot is its centre.
The jaw hinges at the back of the mouth and opens with +xRot."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix, hexc
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Oregorger"
LOOT = [item("raw_iron", 1, 3), item("raw_copper", 2, 5), item("raw_gold", 0, 2), item("diamond", chance=0.05, looting=False, player_only=True)]
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

    # placement orders tried in turn (tallest, widest, biggest, largest outline first), filling the
    # sheet row by row and then column by column; the first that fits wins
    ORDERS = (
        lambda px: (-max(y for _, y in px), -len(px)),
        lambda px: (-max(x for x, _ in px), -len(px)),
        lambda px: (-len(px),),
        lambda px: (-max(x for x, _ in px) - max(y for _, y in px),),
    )

    def place(self, order, by_column=False):
        tw, th = self.m.tex_w, self.m.tex_h
        keys, used = {}, {}                         # used: (x, y) -> "px" or "margin"
        for k, px, margin in order:
            mw, mh = max(x for x, _ in px) + 1, max(y for _, y in px) + 1
            spots = ([(u, v) for u in range(tw - mw + 1) for v in range(th - mh + 1)] if by_column
                     else [(u, v) for v in range(th - mh + 1) for u in range(tw - mw + 1)])
            spot = None
            for (u, v) in spots:
                if all((u + x, v + y) not in used for (x, y) in px) and \
                        all(used.get((u + x, v + y)) != "px" for (x, y) in margin):
                    spot = (u, v)
                    break
            if spot is None:
                return None, k
            keys[k] = spot
            for (x, y) in px:
                used[(spot[0] + x, spot[1] + y)] = "px"
            for (x, y) in margin:
                used.setdefault((spot[0] + x, spot[1] + y), "margin")
        return keys, None

    def apply(self):
        seen, order = set(), []
        for i, it in enumerate(self.items):
            k = it[5] or ("#", i)
            if k not in seen:
                seen.add(k)
                px, margin = self.cells(it[2])
                order.append((k, px, margin))
        keys = failed = None
        for by_column in (False, True):
            for key in self.ORDERS:
                keys, failed = self.place(sorted(order, key=lambda o: key(o[1])), by_column)
                if keys:
                    break
            if keys:
                break
        else:
            raise ValueError(f"{self.m.id}: texture too small for {failed}")
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


def light(c, x, y, col, base=0.22):
    """A pixel that IS light: full colour on the emissive layer over a dim base, so the additive glow
    shows the true colour in the dark instead of washing out to white."""
    if not c.inside(x, y):
        return
    c.set(x, y, shade(col, base))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), hexc(col))


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
SLATE = ["#3d3f45", "#4a4d54", "#3d3f45", "#2f3136", "#43464c"]
SLATE_EDGE = ["#686c75", "#70747d", "#62666e"]      # the lit free edge of a plate
SLATE_SHADOW = ["#222327", "#26282c"]                # the overlap shadow under a plate's edge
SLATE_SEAM = ["#202125", "#232428"]
IRON = ["#d8af93", "#b48d72", "#c9a084"]
COPPER = ["#c26d3f", "#e0844f", "#a85a33"]
GOLD = ["#e8b531", "#ffd84a", "#c9952a"]
DIAMOND = ["#5ee3e0", "#a8fff5", "#3fb8b5"]
REDSTONE = "#ff3b2b"
TUFF = ["#8a8b85", "#7d7e78", "#959690", "#73746e"]
TUFF_DK = ["#5f605a", "#666761"]
TUFF_HI = ["#a9aaa3", "#b2b3ac"]
SKIN = ["#3a3533", "#332f2d", "#403b38", "#2f2b29"]
SKIN_DK = ["#24211f", "#282422"]
SCALE_HI = "#4e4845"
CLAW = ["#2a2826", "#24221f"]
CLAW_TIP = ["#c9c4b4", "#d8d3c4"]
TOOTH = ["#b5b5ad", "#a9a9a1", "#bebeb6"]
GUM = ["#4a2a28", "#552f2c"]
SOCKET = "#141315"
EYE = "#ffb020"
EYE_RIM = "#ff8a00"


# -- deepslate shingles ------------------------------------------------------------------------------
def shingles(row_h=4, plate_w=6, top=1.0, grad=0.16, ore=0.0, red=0.0, salt=0, one_row=False):
    """Overlapping deepslate plates in staggered rows of chiselled tiles: dark seams between plates,
    a lit bevel down each plate's left side, a darker right side, a bright free edge along each
    row's lower edge (the next row starts in its shadow). On top faces the plates point backward
    (row 0 is the back edge). one_row: side faces carry a single row of tall plates (a shell tier
    is one band of the armour). ore: chance per seam pixel of a lump of raw ore wedged in it; red:
    glowing redstone flecks per pixel."""
    def rows(c):
        return c.h if (one_row and c.face in SIDES) else row_h

    def where(c, x, y, s):
        rh = rows(c)
        yy = c.h - 1 - y if c.face == "top" else y      # top faces: free edge toward the back
        row, within = yy // rh, yy % rh
        off = (row % 2) * (plate_w // 2) + int(hsh(row, s) * 3)
        return (x + off) % plate_w, within, rh

    def p(c):
        s = salt + c.x0 * 7 + c.y0 * 131
        for y in range(c.h):
            if c.face == "top":
                f = top * 1.02
            elif c.face == "bottom":
                f = 0.7
            else:
                f = top * (1.04 - grad * y / max(1, c.h - 1))
            for x in range(c.w):
                k, within, rh = where(c, x, y, s)
                col = c.pick(SLATE)
                if k == 0:
                    col = c.pick(SLATE_SEAM)
                elif within == rh - 1:
                    col = c.pick(SLATE_EDGE)                 # the lit free edge
                elif within == 0 and rh > 3:
                    col = c.pick(SLATE_SHADOW) if c.face == "top" else mix(col, SLATE_EDGE[0], 0.25)
                elif k == 1:
                    col = mix(col, SLATE_EDGE[0], 0.35)      # chiselled bevel
                elif k == plate_w - 1:
                    col = shade(col, 0.85)
                elif rh >= 5 and within == rh // 2 and k == plate_w // 2:
                    col = c.pick(SLATE_SEAM)                 # a chisel mark in the tile
                c.set(x, y, shade(col, f))
        if ore:
            for y in range(c.h):
                for x in range(c.w):
                    k, within, rh = where(c, x, y, s)
                    if k == 0 and 0 < within < rh - 1 and hsh(x, y, s, 5) < ore:
                        chunk(c, x, y, s)
        if red:
            for y in range(c.h):
                for x in range(c.w):
                    if hsh(x, y, s, 9) < red:
                        light(c, x, y, REDSTONE, 0.3)
    return p


def chunk(c, x, y, s):
    """A little lump of raw ore wedged in a seam: iron, copper or gold, with a lit corner."""
    r = hsh(x, y, s, 3)
    pal = IRON if r < 0.42 else COPPER if r < 0.8 else GOLD
    cells = [(0, 0), (1, 0), (0, 1)] if hsh(x, s) < 0.5 else [(0, 0), (-1, 0), (0, 1), (-1, 1)]
    for i, (dx, dy) in enumerate(cells):
        if c.inside(x + dx, y + dy):
            col = pal[1] if i == 0 else pal[0] if i < 3 else pal[2]
            c.set(x + dx, y + dy, col)


def ore_stud(pal):
    """A raw-ore chunk cube poking out of the armour: lit top, darker sides, a bright glint."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = pal[0]
                if c.face == "top":
                    col = pal[1]
                elif c.face == "bottom":
                    col = shade(pal[2], 0.8)
                elif (x + y) % 2:
                    col = pal[2]
                c.set(x, y, col)
        if c.face in ("top", "front", "right") and c.w > 1:
            c.set(0, 0, pal[1])
    return p


def diamond_stud(c):
    """The one diamond: cyan facets with pale glints."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, DIAMOND[1] if (x + y) % 2 == 0 and c.face != "bottom" else DIAMOND[0])
    if c.face == "bottom":
        c.fill(DIAMOND[2])


def belly(c):
    """The soft underside of the shell, between the legs: dark folded hide."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SKIN_DK) if y % 3 == 0 else c.pick(SKIN)
            c.set(x, y, shade(col, 0.85))


def shell_tier(top=1.0, ore=0.0, red=0.0, salt=0, row_h=4, plate_w=6):
    """One tier of the dome: a single band of tall plates round its sides, rows on its top."""
    return faces(shingles(row_h, plate_w, top=top, ore=ore, red=red, salt=salt, one_row=True),
                 bottom=belly)


# -- head -----------------------------------------------------------------------------------------
def tuff(top=1.06):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(TUFF)
                r = hsh(x // 2, y // 2, c.x0, c.y0)
                if r < 0.2:
                    col = c.pick(TUFF_DK)
                elif r > 0.88:
                    col = c.pick(TUFF_HI)
                if c.face == "top":
                    col = shade(col, top)
                elif c.face == "bottom":
                    col = shade(col, 0.72)
                else:
                    col = shade(col, 1.0 - 0.12 * y / max(1, c.h - 1))
                c.set(x, y, col)
    return p


def blade(c):
    """The shovel's digging edge: pale worn tuff, brightest along its front lip."""
    tuff(1.1)(c)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, 0, c.pick(TUFF_HI))
            c.set(x, c.h - 1, c.pick(TUFF_DK))
    elif c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(TUFF_HI))        # the front edge (last row) worn bright
    elif c.face in ("left", "right"):
        c.set(fx(c, 0), 0, c.pick(TUFF_HI))


def skin(grad=0.25, scales=0.2):
    """Dark grey-brown scaly hide."""
    def p(c):
        for y in range(c.h):
            f = 1.0 - grad * y / max(1, c.h - 1) if c.face not in ("top", "bottom") else \
                (1.05 if c.face == "top" else 0.75)
            for x in range(c.w):
                col = c.pick(SKIN)
                if (x + 2 * y) % 3 == 0 and hsh(x, y, c.x0) < scales * 3:
                    col = SCALE_HI
                c.set(x, y, shade(col, f))
    return p


def skull_front(c):
    """Front of the skull: only rows 1-2 show, in the slot between brow shield and snout - a dark
    socket band with two small glowing amber eyes."""
    skin()(c)
    for x in range(c.w):
        for y in (1, 2):
            c.set(x, y, SOCKET if x not in (0, c.w - 1) else c.pick(SKIN_DK))
    for x0 in (2, c.w - 4):
        light(c, x0, 1, EYE_RIM, 0.25)
        light(c, x0 + 1, 1, EYE, 0.3)
        light(c, x0, 2, EYE, 0.3)
        light(c, x0 + 1, 2, EYE_RIM, 0.25)


def brow(c):
    """The head shield: one big deepslate plate, its front edge lit, chiselled rim."""
    shingles(row_h=8, plate_w=16, top=1.02)(c)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, 0, c.pick(SLATE_EDGE))
            c.set(x, c.h - 1, c.pick(SLATE_SHADOW))
    elif c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(SLATE_EDGE))
        for y in range(c.h):
            c.set(0, y, c.pick(SLATE_SEAM))
            c.set(c.w - 1, y, c.pick(SLATE_SEAM))


def jaw_paint(c):
    """The crushing lower jaw: tuff, its top edge a row of flat square stone teeth."""
    tuff(1.0)(c)
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                edge = x in (0, c.w - 1) or y == c.h - 1
                if edge:
                    col = c.pick(TOOTH) if (x + y) % 3 else shade(TOOTH[0], 0.7)
                else:
                    col = c.pick(GUM)
                c.set(x, y, col)
    elif c.face in ("front", "left", "right"):
        for x in range(c.w):
            col = c.pick(TOOTH) if x % 3 else shade(TOOTH[0], 0.6)   # flat teeth with dark gaps
            c.set(x, 0, col)


def snout_bottom(c):
    """The roof of the mouth under the snout: flat stone grinding teeth round a dark palate."""
    for y in range(c.h):
        for x in range(c.w):
            edge = x in (0, c.w - 1) or y == c.h - 1
            if edge:
                col = c.pick(TOOTH) if (x + y) % 3 else shade(TOOTH[0], 0.7)
            else:
                col = c.pick(GUM)
            c.set(x, y, col)


# -- legs, claws, tail -----------------------------------------------------------------------------
def leg(c):
    skin(grad=0.3)(c)
    if c.face in SIDES:                                   # knobbly scutes on the upper leg
        for x in range(0, c.w, 2):
            c.set(x, 0, mix(c.get(x, 0), SLATE_EDGE[0], 0.5))
    if c.face == "bottom":
        c.noise(SKIN_DK)


def claw(c):
    """A thick digging claw: dark horn, the front (tip) pale."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(CLAW)
            if c.face == "front":
                col = c.pick(CLAW_TIP)
            elif c.face in ("top", "bottom") and y == c.h - 1:
                col = c.pick(CLAW_TIP)                    # last row = front edge
            elif c.face in ("left", "right") and fx(c, x) == 0:
                col = c.pick(CLAW_TIP)
            elif c.face == "top":
                col = shade(col, 1.25)
            c.set(x, y, col)


def tail_paint(ore=0.0):
    return faces(shingles(row_h=3, plate_w=4, top=1.0, grad=0.22, ore=ore, salt=11, one_row=True),
                 bottom=belly)


# -- the ball --------------------------------------------------------------------------------------
def ball_shingles(salt):
    return faces(shingles(row_h=4, plate_w=5, top=1.0, grad=0.25, ore=0.06, red=0.003, salt=salt))


def tucked_snout(c):
    tuff(1.08)(c)
    if c.face == "front":
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(TUFF_HI))           # the blade edge, tucked under
        light(c, 1, 0, EYE_RIM, 0.25)                    # one eye glinting out from the curl
        light(c, c.w - 2, 0, EYE_RIM, 0.25)


def tucked_tail(c):
    """The tail tip curled over the snout: banded plates, each band's lower edge lit, outlined."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SLATE_EDGE) if y % 2 == 1 else shade(c.pick(SLATE), 1.12)
            if x in (0, c.w - 1) and c.face in ("front", "back", "top", "bottom"):
                col = c.pick(SLATE_SEAM)
            c.set(x, y, col)


def build():
    m = Model("oregorger", 128, 128, seed=7373)
    pk = Pack(m)

    # body = the domed shell; pivot (0, 12, 1). Four tiers: skirt y 13-19 (26 x 24), mid y 8-13,
    # upper y 5-8, crown y 3-5. Ore lumps are painted in the seams, plus a few 3D chunks.
    body = m.part("body", (0, 12, 1))
    pk.add(body, (-13, 1, -12), (26, 6, 24), shell_tier(top=0.98, ore=0.07, red=0.004, salt=1, plate_w=7))
    pk.add(body, (-12, -4, -11), (24, 5, 22), shell_tier(top=1.02, ore=0.08, red=0.004, salt=2))
    pk.add(body, (-10, -7, -9), (20, 3, 18), shell_tier(top=1.06, ore=0.1, salt=3, plate_w=5))
    pk.add(body, (-7, -9, -6), (14, 2, 12), shell_tier(top=1.1, ore=0.1, salt=4, row_h=3, plate_w=4))
    # raw ore chunks bursting out between the plates (half buried)
    studs = [  # (palette name, origin, size)
        ("iron", (-6, -10, -2), (3, 2, 3)), ("gold", (3, -10, 2), (2, 2, 2)),
        ("copper", (-11, -7, 3), (3, 2, 3)), ("iron", (8.5, -6, -4), (3, 3, 3)),
        ("copper", (6, -8, 6), (3, 2, 2)), ("gold", (-12.5, -2, -6), (2, 2, 2)),
        ("iron", (11.5, 0, 6), (2, 3, 3)), ("copper", (-4, -6, -10), (3, 2, 2)),
    ]
    pals = {"iron": IRON, "copper": COPPER, "gold": GOLD}
    done = set()
    for name, o, s in studs:
        key = f"{name}_{s[0]}{s[1]}{s[2]}"
        pk.add(body, o, s, None if key in done else faces(ore_stud(pals[name])), share=key)
        done.add(key)
    pk.add(body, (1, -10.5, -4), (1, 2, 1), faces(diamond_stud), share="diamond")   # the diamond

    # head: child of the body, low at the front; pivot at the neck (world 0, 15, -11)
    head = body.part("head", (0, 3, -12))
    pk.add(head, (-6, -5, -6), (12, 8, 7), faces(skin(), front=skull_front))
    pk.add(head, (-7, -7, -8), (14, 3, 9), faces(brow))
    pk.add(head, (-6, -2, -12), (12, 3, 6), faces(tuff(), bottom=snout_bottom))
    pk.add(head, (-7, -0.5, -14), (14, 2, 3), faces(blade))
    jaw = head.part("jaw", (0, 1.5, -5))
    pk.add(jaw, (-5, 0, -8), (10, 3, 7), faces(jaw_paint))

    # tail: three drooping plated segments behind the shell
    tail = body.part("tail", (0, 1, 12), (-0.35, 0, 0))
    pk.add(tail, (-4, -3, -1), (8, 6, 7), tail_paint(ore=0.15))
    pk.add(tail, (-3, -4, 0), (6, 1, 6), faces(shingles(row_h=3, plate_w=3, top=1.08, salt=21)))
    tail_mid = tail.part("tail_mid", (0, 0.5, 6), (-0.2, 0, 0))
    pk.add(tail_mid, (-3, -2.5, -1), (6, 5, 6), tail_paint())
    tail_tip = tail_mid.part("tail_tip", (0, 0, 5), (-0.05, 0, 0))
    pk.add(tail_tip, (-2, -2, -1), (4, 4, 5), tail_paint())

    # legs: children of root, pivot at the top (y 17, inside the shell skirt), feet on the ground;
    # thick digging claws poke forward, biggest on the front feet
    for name, x, z, front in (("right_front_leg", -9.5, -6, True), ("left_front_leg", 9.5, -6, True),
                              ("right_hind_leg", -9.5, 8, False), ("left_hind_leg", 9.5, 8, False)):
        lg = m.part(name, (x, 17, z))
        left = name.startswith("left")
        pk.add(lg, (-3, 0, -3), (6, 7, 6), None if left else faces(leg), mirror=left, share="leg")
        for cx in (-2.5, -0.5, 1.5):
            if front:
                pk.add(lg, (cx, 5, -5), (1, 2, 3), faces(claw), share="claw")
            else:
                pk.add(lg, (cx, 6, -4), (1, 1, 2), faces(claw), share="claw_small")

    # the ball: centre (0, 13, 0), 22 across. Three crossed 20 x 16 x 16 blocks and three crossed
    # 22 x 10 x 10 arms give it a round, four-step profile from every side (each set shares one
    # texture: the y and z copies are the x one turned). Plates and ore on every side, the tail tip
    # curled over the tucked snout on the front.
    ball = m.part("ball", (0, 13, 0))
    turns = (ball, ball.part("ball_turn_y", (0, 0, 0), (0, 0, math.pi / 2)),
             ball.part("ball_turn_z", (0, 0, 0), (0, math.pi / 2, 0)))
    for i, t in enumerate(turns):
        pk.add(t, (-10, -8, -8), (20, 16, 16), ball_shingles(31) if i == 0 else None, share="ball_block")
        pk.add(t, (-11, -5, -5), (22, 10, 10), ball_shingles(32) if i == 0 else None, share="ball_arm")
    pk.add(ball, (-4, 1, -12), (8, 4, 2), faces(tucked_snout))
    pk.add(ball, (-4, -7, -12), (6, 7, 2), faces(tucked_tail))
    for cx in (-6, 5):                                    # claw tips peeking out under the snout
        pk.add(ball, (cx, 6, -12), (1, 1, 2), faces(claw), share="claw_small")
    for name, o, s in (("gold", (-1, -12, 3), (2, 2, 2)), ("iron", (-12, 2, 2), (2, 3, 3)),
                       ("copper", (10, -3, -3), (3, 2, 3)), ("iron", (3, 2, 10), (2, 3, 3))):
        key = f"{name}_{s[0]}{s[1]}{s[2]}"
        pk.add(ball, o, s, None if key in done else faces(ore_stud(pals[name])), share=key)
        done.add(key)
    pk.add(ball, (3, -12, 3), (1, 2, 1), None, share="diamond")

    pk.apply()
    m.save()
    spawn_egg("oregorger", "#3d3f45", "#c28a5a", accent="#5ee3e0")


if __name__ == "__main__":
    build()

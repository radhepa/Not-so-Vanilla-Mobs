"""Sandmaw: a colossal desert sand worm. Only its front part ever leaves the ground: a thick segmented
column rearing about three blocks out of the sand, bent in a slight S, whose top hooks forward into a
huge eyeless maw facing forward and a little down toward its prey.

Each ring of the body is sandy ochre hide, darker toward its lower edge, with a recessed umber band
of wrinkled joint skin between rings. The front (belly) side is paler and ribbed; the back carries
rough pale sandstone armour plates with chiselled seams (a raised plate on the back whose top lip
overlaps the joint above, narrower plates on the back half of each flank and a ridge scute down the
spine), and the head wears a stepped sandstone hood. The maw is four thick stepped sandstone
petal-jaws (top, bottom, left, right) with a raised keel each, closing into a blunt four-sided beak
with dark seams between the petals and bone-white fangs at their tips; their insides are gums lined
with rows of hooked teeth, and the head's front face (only seen when they open) is a pit of
rectangular rings of inward-pointing bone-white teeth around a dark throat. Loose sand clings to the
lowest ring, heaps up round its base and trickles down its hide.

Animation contract: segment1 (pivot at ground level) > segment2 > segment3 > head > jaw_top /
jaw_bottom / jaw_left / jaw_right. Every jaw has a zero rest rotation (the closing tilt lives in its
child *_plate part), so the code can add its opening angle directly: jaw_top opens with -xRot,
jaw_bottom +xRot, jaw_right +yRot, jaw_left -yRot."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Sandmaw"
LOOT = [item("bone", 1, 3), item("gold_nugget", 2, 6), item("diamond", chance=0.06, looting=False, player_only=True)]
TAGS = ["fall_damage_immune"]


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
    """A repeatable 0..1 value for a position (so both faces of a flat plane get the same pixels)."""
    n = 0x9E3779B1
    for a in v:
        n = (n ^ (int(a) + 0x7F4A7C15 + (n << 6) + (n >> 2))) & 0xFFFFFFFF
        n = (n * 0x85EBCA6B) & 0xFFFFFFFF
        n ^= n >> 13
    return (n & 0xFFFF) / 65536.0


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
OCHRE = ["#c9a35e", "#b88f4c", "#b88f4c", "#c29b55", "#ae8646"]
OCHRE_HI = ["#d6b46e", "#d1ae68"]
UMBER = ["#7a5a2e", "#6f5129", "#84633a"]
UMBER_DK = ["#5c4322", "#533c1e"]
STONE = ["#e0c98f", "#dbc387", "#e5d09a", "#d9bf84"]
STONE_HI = ["#efe0b3", "#ece0b0"]
STONE_LN = "#b29560"          # chiselled seam
STONE_DK = ["#a48852", "#9c804b"]
BELLY = ["#dfc28a", "#d6b980", "#e3c991"]
RIB = ["#a98a50", "#b09156"]
SAND = ["#dbd0a0", "#e2d8ad", "#d3c692", "#cbbd88"]
TOOTH = "#efe6cf"
TOOTH_SH = "#c9bc9b"
TOOTH_HI = "#fbf6e8"
THROAT = ["#2a1a10", "#3b2414"]
THROAT_DK = "#170d07"
GUM = ["#6b3f2a", "#5f3725", "#764a30"]
GUM_DK = ["#4a2a1a", "#43261a"]


# -- hide ------------------------------------------------------------------------------------------
def hide(grad=0.28, belly_cols=4, sand_rows=0):
    """Ochre worm hide for a ring's flanks: lit near the top edge, darker toward the umber lower edge,
    mottled with darker blotches, pale flecks and dark pores (no grain, so it never reads as wood);
    the front columns pale into the belly. sand_rows: loose sand clinging to the bottom of the ring
    (ragged top edge)."""
    def p(c):
        salt = c.x0 * 31 + c.y0
        for y in range(c.h):
            f = 1.03 - grad * (y / max(1, c.h - 1))
            for x in range(c.w):
                col = c.pick(OCHRE)
                b = hsh(x // 2 + (y // 2) % 2, y // 2, salt)      # 2 px blotches, staggered
                if b < 0.22:
                    col = mix(col, c.pick(UMBER), 0.35)
                elif b > 0.88:
                    col = c.pick(OCHRE_HI)
                col = shade(col, f)
                if c.face in ("left", "right"):
                    i = fx(c, x)
                    if i < belly_cols:
                        col = mix(col, shade(c.pick(BELLY), f), 0.75 - 0.17 * i)
                c.set(x, y, col)
        for _ in range(int(c.w * c.h * 0.025) + 1):       # pores: a dark pit with a lit lower lip
            x, y = c.rng.randrange(c.w), c.rng.randrange(1, max(2, c.h - 2))
            c.set(x, y, mix(c.get(x, y), c.pick(UMBER_DK), 0.7))
            if c.inside(x, y + 1):
                c.set(x, y + 1, shade(c.get(x, y + 1), 1.08))
        for x in range(c.w):
            c.set(x, 0, mix(c.get(x, 0), c.pick(OCHRE_HI), 0.6))
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(UMBER), 0.7))
        if sand_rows:
            sand(c, sand_rows)
    return p


def sand(c, rows):
    """Loose sand stuck to the lowest rows of a face, its top edge ragged."""
    for x in range(c.w):
        top = c.h - rows + int(hsh(x, c.w, rows) * 3) - 1
        for y in range(max(0, top), c.h):
            col = c.pick(SAND)
            if y == top:
                col = shade(col, 1.06)
            elif y == c.h - 1:
                col = shade(col, 0.92)
            c.set(x, y, col)
        if hsh(x, 3, c.w) < 0.25 and c.inside(x, top - 1):   # a few grains above the crust
            c.set(x, top - 1, mix(c.get(x, top - 1), c.pick(SAND), 0.7))


def belly(sand_rows=0):
    """The pale ribbed underside on the front of a ring: soft folds (a shadowed groove every few
    rows that wavers and breaks), mottled like the hide."""
    def p(c):
        salt = c.x0 * 13 + c.y0
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(BELLY)
                b = hsh(x // 2, y // 2, salt)
                if b < 0.2:
                    col = mix(col, c.pick(RIB), 0.35)
                fold = (y + (1 if hsh(x // 3, salt) < 0.3 else 0)) % 4 == 3
                if fold and hsh(x, y, salt) > 0.12:
                    col = mix(col, c.pick(RIB), 0.7)
                edge = min(x, c.w - 1 - x)               # ochre flanks, pale stripe up the middle
                if edge < 3:
                    col = mix(shade(c.pick(OCHRE), 1.03 - 0.25 * y / max(1, c.h - 1)), col,
                              (0.0, 0.3, 0.65)[edge])
                c.set(x, y, col)
        for x in range(c.w):
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), c.pick(UMBER), 0.55))
        if sand_rows:
            sand(c, sand_rows)
    return p


def chin(c):
    """Underside of the head's forward hook: the pale ribbed belly runs on under the maw (row 0 is
    the back edge, so the ribs run across)."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(RIB) if y % 3 == 2 else c.pick(BELLY)
            if x in (0, c.w - 1):
                col = mix(col, c.pick(OCHRE), 0.6)
            c.set(x, y, shade(col, 0.88))


def ledge(c):
    """Top of a ring: only an outer ring shows round the joint above. Lit ochre, paler at the front
    (row 0 is the back edge), a bright rim along the outer edge."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(OCHRE), 1.1)
            if y > c.h * 0.6:
                col = mix(col, shade(c.pick(BELLY), 1.05), 0.6)
            if x in (0, c.w - 1) or y in (0, c.h - 1):
                col = mix(col, c.pick(OCHRE_HI), 0.6)
            elif x in (1, c.w - 2) or y in (1, c.h - 2):
                col = shade(col, 0.94)
            c.set(x, y, col)
    for _ in range(int(c.w * c.h * 0.02)):               # a dusting of sand
        c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(SAND))


def underside(c):
    c.noise([shade(u, 0.85) for u in UMBER])


def ring_paint(sand_rows=0):
    return faces(hide(sand_rows=sand_rows), front=belly(sand_rows), top=ledge, bottom=underside)


def collar(c):
    """The recessed joint between rings: dark umber skin in vertical creases."""
    for y in range(c.h):
        for x in range(c.w):
            if c.face in ("top", "bottom"):
                col = c.pick(UMBER_DK)
            else:
                col = c.pick(UMBER)
                if x % 3 == 0:
                    col = c.pick(UMBER_DK)
                elif x % 3 == 1 and c.rng.random() < 0.4:
                    col = shade(col, 1.1)
                if y == 0:
                    col = shade(col, 0.8)
            c.set(x, y, col)


# -- sandstone armour ------------------------------------------------------------------------------
def plate(outer, strata=3, dust=0.0):
    """Rough pale sandstone: the outer face gets a chiselled bevel (lit top/left, dark seam
    bottom/right), a soft mottle, one or two broken chiselled grooves with a lit edge under them and
    a couple of short cracks. Top faces are lit, other faces darker. dust: sand grains on the top
    face. strata: rows between grooves."""
    def p(c):
        salt = c.x0 * 17 + c.y0 * 3
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(STONE)
                b = hsh(x // 2, y // 2, salt)
                if b < 0.18:
                    col = mix(col, STONE_DK[0], 0.3)
                elif b > 0.85:
                    col = mix(col, STONE_HI[0], 0.5)
                if c.face == "top":
                    col = shade(col, 1.04)
                elif c.face == "bottom":
                    col = shade(c.pick(STONE_DK), 0.85)
                elif c.face != outer:
                    col = shade(col, 0.88 - 0.08 * y / max(1, c.h - 1))
                c.set(x, y, col)
        if c.face == "top" and dust:
            for _ in range(int(c.w * c.h * dust) + 1):
                c.set(c.rng.randrange(c.w), c.rng.randrange(c.h), c.pick(SAND))
        if c.face != outer or c.w < 3 or c.h < 3:
            return
        rows = [y for y in range(2, c.h - 2) if (y - 2) % (strata + 1) == strata // 2][:2]
        for y in rows:                                   # chiselled grooves, broken into lengths
            gap = c.rng.randrange(2, 5)
            for x in range(1, c.w - 1):
                if (x + gap) % 7 == 0:
                    continue
                c.set(x, y, mix(c.get(x, y), STONE_LN, 0.85))
                c.set(x, y + 1, mix(c.get(x, y + 1), STONE_HI[0], 0.6))
        for _ in range(max(1, c.w * c.h // 60)):         # short cracks
            x, y = c.rng.randrange(1, max(2, c.w - 2)), c.rng.randrange(1, max(2, c.h - 2))
            c.set(x, y, STONE_LN)
            c.set(x + 1, y + 1, mix(c.get(x + 1, y + 1), STONE_LN, 0.7))
        for x in range(c.w):
            c.set(x, 0, c.pick(STONE_HI))
            c.set(x, c.h - 1, c.pick(STONE_DK))
        for y in range(1, c.h - 1):
            c.set(0, y, shade(c.pick(STONE), 1.05))
            c.set(c.w - 1, y, STONE_LN)
    return p


def plate_faces(outer, dust=0.0, strata=3):
    return faces(plate(outer, strata=strata, dust=dust))


# -- the maw ---------------------------------------------------------------------------------------
def mouth(c):
    """The head's front face, hidden behind the jaws until they open: rectangular rings of bone
    teeth pointing in toward a dark throat (r = distance from the rim)."""
    for y in range(c.h):
        for x in range(c.w):
            r = min(x, y, c.w - 1 - x, c.h - 1 - y)
            p = y if r in (x, c.w - 1 - x) else x            # position along the rim
            if r == 0:
                col = c.pick(GUM_DK)
            elif r <= 3:                                      # outer ring: big fangs, 3 deep
                k = p % 4
                if k in (1, 2) and (r <= 2 or k == 1):
                    col = TOOTH_SH if r == 1 else TOOTH if r == 2 else TOOTH_HI
                else:
                    col = c.pick(GUM)
            elif r == 4:
                col = c.pick(GUM_DK)
            elif r <= 6:                                      # inner ring: small teeth
                if (p + 1) % 3 == 0:
                    col = TOOTH_SH if r == 5 else TOOTH
                else:
                    col = mix(c.pick(GUM), THROAT[1], 0.5)
            elif r == 7:
                col = c.pick(THROAT)
            else:
                col = THROAT_DK
            c.set(x, y, col)


def head_side(c):
    hide(grad=0.2, belly_cols=0)(c)
    for y in range(c.h):                                    # dark lip seam where the jaws hinge
        c.set(fx(c, 0), y, c.pick(UMBER_DK))


def petal_outer(c, row0=0):
    """Outer face of a jaw (top face in the plate's frame; row 0 = the hinge end): tough mottled
    ochre hide with a few folds across the jaw, darkening toward the tip, umber edges. row0: rows of the whole jaw
    before this slab, so the ribs run on across both slabs."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(OCHRE), 1.06 - 0.02 * (row0 + y))
            b = hsh(x // 2, (row0 + y) // 2, 77)
            if b < 0.22:
                col = mix(col, c.pick(UMBER), 0.35)
            elif b > 0.86:
                col = c.pick(OCHRE_HI)
            if (row0 + y) % 4 == 3 and 1 < x < c.w - 2:
                col = mix(col, c.pick(UMBER), 0.5)
            if x in (0, c.w - 1):
                col = mix(col, c.pick(UMBER_DK), 0.7)
            elif x in (1, c.w - 2):
                col = shade(col, 0.92)
            c.set(x, y, col)


def petal_inner(c):
    """Inside of a jaw plate (bottom face in the plate's frame; row 0 = the hinge end): gums with
    rows of hooked teeth pointing back toward the throat."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(GUM))
    for y0 in range(c.h - 1, 0, -3):
        for x in range(1, c.w - 1, 2):
            c.set(x, y0, TOOTH_SH)
            c.set(x, y0 - 1, TOOTH)
            if (x // 2) % 2 == 0 and c.inside(x, y0 - 2):
                c.set(x, y0 - 2, TOOTH_HI)


def petal_edge(c):
    """The thick edges of a jaw: dark umber hide with a gum line along the inner side."""
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(OCHRE), c.pick(UMBER), 0.6)
            if c.face in ("left", "right") and y == c.h - 1:
                col = c.pick(GUM)
            c.set(x, y, col)


def petal_tip(c):
    """The blunt tip slab: its end face is a row of bone teeth round the beak's dark slit."""
    if c.face == "front":
        for x in range(c.w):
            c.set(x, 0, c.pick(UMBER_DK))
            for y in range(1, c.h):
                c.set(x, y, TOOTH_HI if x % 2 == 0 else TOOTH)
        return
    if c.face == "top":
        petal_outer(c, row0=7)
    elif c.face == "bottom":
        petal_inner(c)
    else:
        petal_edge(c)


PETAL = faces(petal_edge, top=petal_outer, bottom=petal_inner)


def corner_web(inner_x, inner_y):
    """The webbing of dark lip flesh filling a corner between two jaws. Its front face is serrated
    with small bone teeth along the two edges that meet the jaws (inner_x: that edge's column is
    the last one, else the first; inner_y: likewise for the row)."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = mix(c.pick(UMBER), c.pick(GUM), 0.4)
                if c.face == "top":
                    col = shade(col, 1.1)
                elif c.face == "bottom":
                    col = c.pick(GUM_DK)
                c.set(x, y, col)
        if c.face != "front":
            return
        ex = c.w - 1 if inner_x else 0
        ey = c.h - 1 if inner_y else 0
        for y in range(c.h):
            c.set(ex, y, TOOTH if y % 2 == 0 else TOOTH_SH)
        for x in range(c.w):
            c.set(x, ey, TOOTH if x % 2 == 0 else TOOTH_SH)
        c.set(ex, ey, TOOTH_HI)
    return p

def lip(c):
    """The flared rim of the maw that the jaws hinge on: dark wrinkled umber flesh, gums inside."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(UMBER)
            if c.face == "top":
                col = shade(col, 1.12)
            elif c.face == "bottom":
                col = c.pick(GUM_DK)
            elif c.face == "front":
                col = mix(col, c.pick(GUM), 0.35)
                if (x + y) % 3 == 0:
                    col = c.pick(UMBER_DK)
            c.set(x, y, col)


# the mouth is the head's 20 x 18 front face, framed by a lip ring 1 px wider all round; the jaws
# hinge on the lip's outer front edge
LIP_HW, LIP_HH = 11, 10            # half width / half height of the lip ring
BEAK = 11                          # how far the closed beak reaches in front of the lip
SLIT = 1.5                         # the plates stop this far short of the middle: a blunt tip
# jaw plate slabs (all four jaws alike): (start, end) along the plate from the hinge, width, thickness
SLABS = [(0, 7, 12, 3), (7, 13, 8, 3)]
TILT_V = math.atan2(LIP_HH - SLIT, BEAK)     # top / bottom jaws
TILT_H = math.atan2(LIP_HW - SLIT, BEAK)     # right / left jaws


# -- sand ------------------------------------------------------------------------------------------
def clump(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SAND)
            if c.face == "top":
                col = shade(col, 1.06)
            elif c.face == "bottom":
                col = shade(col, 0.8)
            else:
                col = shade(col, 0.94 - 0.06 * y)
            c.set(x, y, col)


def strand(seed):
    """A flat trickle of sand running down the hide (cut out between the streams)."""
    def p(c):
        for x in range(c.w):
            # the same column index from either side, so both faces of the plane match
            i = fx(c, x) if c.face in ("left", "right") else (c.w - 1 - x if c.face == "back" else x)
            stop = int(c.h * (0.45 + 0.55 * hsh(i, seed)))
            for y in range(c.h):
                r = hsh(i, y, seed)
                if y > stop or (y > 1 and r < 0.18):
                    c.clear(x, y)
                else:
                    c.set(x, y, SAND[int(r * len(SAND))])
    return p


def heap(pk, part, x, z, w, d):
    """A little mound of sand slumped against the base of the lowest ring (two stacked slabs)."""
    pk.add(part, (x, -1, z), (w, 1, d), faces(clump))
    pk.add(part, (x + 1, -2, z + 1), (w - 2, 1, d - 2), faces(clump))


def build():
    m = Model("sandmaw", 128, 128, seed=2424)
    pk = Pack(m)

    # segment1: the lowest ring, rising 10 px out of the ground (y 24 -> 14). 24 wide, 20 deep
    # (the back plate and the spine ridge add 4 more behind). Back and flank plates stand 1 px
    # proud of the ring's top, overlapping the joint above like shingles.
    s1 = m.part("segment1", (0, 24, 0), (-0.04, 0, 0.03))
    pk.add(s1, (-12, -10, -10), (24, 10, 20), ring_paint(sand_rows=3))
    pk.add(s1, (-9, -11, 10), (18, 10, 2), plate_faces("back", dust=0.12))
    pk.add(s1, (-13, -11, 1), (1, 10, 8), plate_faces("right", dust=0.15), share="s1_flank")
    pk.add(s1, (12, -11, 1), (1, 10, 8), None, mirror=True, share="s1_flank")
    pk.add(s1, (-2, -13, 12), (4, 9, 2), plate_faces("back", strata=2))
    # loose sand: a clump on the back plate, heaps slumping round the base, trickles down the hide
    pk.add(s1, (-6, -12, 10), (3, 1, 2), faces(clump))
    heap(pk, s1, -15, -5, 4, 6)
    heap(pk, s1, -4, -13, 7, 4)
    heap(pk, s1, 11, 3, 4, 5)
    pk.add(s1, (-12.5, -9, -6), (0, 8, 3), faces(strand(1)))
    pk.add(s1, (6, -10, -10.5), (3, 9, 0), faces(strand(2)))

    # segment2: y 14 -> 5 (a 2 px joint band, then the ring). 22 x 18.
    s2 = s1.part("segment2", (0, -10, 0), (-0.14, 0, -0.06))
    pk.add(s2, (-8, -2, -7), (16, 4, 14), faces(collar), share="collar")
    pk.add(s2, (-11, -9, -9), (22, 7, 18), ring_paint())
    pk.add(s2, (-8, -10, 9), (16, 7, 2), plate_faces("back", dust=0.05))
    pk.add(s2, (-12, -10, 1), (1, 7, 7), plate_faces("right"), share="s2_flank")
    pk.add(s2, (11, -10, 1), (1, 7, 7), None, mirror=True, share="s2_flank")
    pk.add(s2, (-2, -12, 11), (4, 7, 2), plate_faces("back", strata=2))

    # segment3: y 5 -> -3. 20 x 16.
    s3 = s2.part("segment3", (0, -9, 0), (0.2, 0, 0.05))
    pk.add(s3, (-8, -2, -7), (16, 4, 14), None, share="collar")
    pk.add(s3, (-10, -8, -8), (20, 6, 16), ring_paint())
    pk.add(s3, (-7, -9, 8), (14, 6, 2), plate_faces("back"))
    pk.add(s3, (-11, -9, 1), (1, 6, 6), plate_faces("right"), share="s3_flank")
    pk.add(s3, (10, -9, 1), (1, 6, 6), None, mirror=True, share="s3_flank")
    pk.add(s3, (-2, -11, 10), (4, 6, 2), plate_faces("back", strata=2))

    # head: a neck band, then the head block hooking forward over the column (y -20..-2,
    # z -14..6 in its frame) with the 20 x 18 mouth on its front face. Its top and back are painted
    # sandstone, with a raised crown scute and crest on top and plates on the cheeks.
    head = s3.part("head", (0, -8, 0), (0.26, 0, -0.03))
    pk.add(head, (-8, -2, -7), (16, 4, 14), None, share="collar")
    pk.add(head, (-10, -20, -14), (20, 18, 20), faces(hide(grad=0.18, belly_cols=0), front=mouth,
                                                      right=head_side, left=head_side,
                                                      top=plate("top"), back=plate("back"),
                                                      bottom=chin))
    pk.add(head, (-8, -22, -6), (16, 2, 11), plate_faces("top"))
    pk.add(head, (-2, -23, -4), (4, 1, 8), faces(plate("none")))
    pk.add(head, (-11, -17, -3), (1, 11, 8), plate_faces("right"), share="cheek")
    pk.add(head, (10, -17, -3), (1, 11, 8), None, mirror=True, share="cheek")
    # the lip ring round the mouth: 1 px proud of the face, 1 px wider than the head all round
    cy = -11
    pk.add(head, (-LIP_HW, cy - LIP_HH, -15), (2 * LIP_HW, 2, 3), faces(lip), share="lip_h")
    pk.add(head, (-LIP_HW, cy + LIP_HH - 2, -15), (2 * LIP_HW, 2, 3), None, mirror=True, share="lip_h")
    pk.add(head, (-LIP_HW, cy - LIP_HH + 2, -15), (2, 2 * LIP_HH - 4, 3), faces(lip), share="lip_v")
    pk.add(head, (LIP_HW - 2, cy - LIP_HH + 2, -15), (2, 2 * LIP_HH - 4, 3), None, mirror=True,
           share="lip_v")

    # the four jaws: pivots on the outer front edge of the lip, rest rotation zero; each holds a
    # two-step sandstone plate tilted in to close the beak (rolled so its outer face points away
    # from the mouth). They meet in a "+", the toothed mouth showing in the corners between them.
    # All four plates share one texture.
    zf = -15
    jaws = {
        "jaw_top": ((0, cy - LIP_HH, zf), (TILT_V, 0, 0)),
        "jaw_bottom": ((0, cy + LIP_HH, zf), (TILT_V, 0, math.pi)),
        "jaw_right": ((-LIP_HW, cy, zf), (TILT_H, 0, -math.pi / 2)),
        "jaw_left": ((LIP_HW, cy, zf), (TILT_H, 0, math.pi / 2)),
    }
    first = True
    for name, (pivot, tilt) in jaws.items():
        jaw = head.part(name, pivot)
        plate_p = jaw.part(name + "_plate", (0, 0, 0), tilt)
        for i, (a, b, w, t) in enumerate(SLABS):
            paint = (faces(petal_tip) if i == len(SLABS) - 1 else PETAL) if first else None
            pk.add(plate_p, (-w / 2, 0, -b), (w, t, b - a), paint, share=f"petal{i}")
        first = False

    # dark lip webbing filling the four corners between the jaws, stepping in toward the beak, its
    # edges serrated with small teeth (fixed to the head: the jaws swing away from it)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x0 = -LIP_HW + 0.5 if sx < 0 else LIP_HW - 4.5
        y0 = cy - LIP_HH + 0.5 if sy < 0 else cy + LIP_HH - 4.5
        pk.add(head, (x0, y0, zf - 2), (4, 4, 2), faces(corner_web(sx < 0, sy < 0)))
        x1 = x0 + 2 if sx < 0 else x0
        y1 = y0 + 2 if sy < 0 else y0
        pk.add(head, (x1, y1, zf - 4), (2, 2, 2), faces(corner_web(sx < 0, sy < 0)))

    pk.apply()
    m.save()
    spawn_egg("sandmaw", "#c9a35e", "#7a5a2e", accent="#f0e6c8")


if __name__ == "__main__":
    build()

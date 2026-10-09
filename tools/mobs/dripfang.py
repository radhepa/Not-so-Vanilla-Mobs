"""Dripfang: a cave predator of the Dripstone Caves. Crawling, it is a low armoured stone centipede: a
back of overlapping dripstone plates (brown-tan, streaked like a dripstone block) that rises into a
ridge of three short pointed-dripstone spikes, a long tapering dripstone tail spike, a pale calcite
underside, a low wedge-shaped head with two hooked ivory fangs and four small dim amber eyes, and six
long jointed calcite legs that arch up at the knee and splay down to the ground like a spider's.
`stalactite` is the hanging form: a pointed-dripstone stalactite hanging from the ceiling, top at
the top of the hitbox, with two tiny dim amber eyes peeking out near the top; the code shows it only
while hanging and hides everything else then."""
import math
import os

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Dripfang"
LOOT = [item("pointed_dripstone", 0, 2), item("flint", 0, 1)]
TAGS = ["arthropod", "fall_damage_immune"]

# Debug only: DRIPFANG_DEBUG_HANG=1 moves the stalactite beside the crawler so a preview shows both.
DEBUG_HANG = os.environ.get("DRIPFANG_DEBUG_HANG") == "1"


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


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


def outer(c, i):
    """Column i counted from the outer (far) end of a right leg, on its long faces."""
    return c.w - 1 - i if c.face == "back" else i


def dim_glow(c, x, y, col, k):
    """Split col between the base texture (1 - k) and the additive emissive layer (k): lit, the two add
    up to col; in the dark only the faint k part glows."""
    if not c.inside(x, y):
        return
    c.set(x, y, shade(col, 1.0 - k))
    c.model.glow_image().putpixel((c.x0 + x, c.y0 + y), shade(col, k))


# -- palette -----------------------------------------------------------------------------------------
DRIP = ["#866b5c", "#8a6f5f", "#826858"]
DRIP_LT = ["#9b7f6c", "#977b69"]
DRIP_DK = ["#6f5848", "#735b4b"]
STREAK = "#b09584"
SHADOW = "#4f3d32"
PALE = "#cdb9a6"                   # the pale, worn point of a stalactite
CALC = ["#d8d3cb", "#d3cdc4", "#dcd8d0"]
CALC_DK = ["#bfb8ad", "#b9b2a6"]
CALC_SEAM = "#a39b8f"
FACE = ["#58453a", "#523f35", "#5c493d"]
SOCKET = "#1f1714"
FANG = ["#ede0c4", "#e6d8ba", "#f1e6cf"]
FANG_SH = "#cbbfa6"
FANG_TIP = ["#6b4c3a", "#5e4334"]
EYE = "#ffb347"
EYE_DIM = "#d9822b"
FOOT = ["#6c6158", "#625850"]


# -- dripstone ---------------------------------------------------------------------------------------
def drip(pale=0.0, low=0.74, top=1.08, rim=True, streaks=0.3, along_z=False):
    """Dripstone, like the vanilla block: lanes of brown-tan running down the face (neighbouring lanes
    often share a tone, so they read as bands), some carrying a long pale or dark streak. Side faces
    darken toward the bottom; pale mixes toward the worn pale point of a stalactite.
    along_z: the lanes run front-to-back on the flanks too (for a dripstone point lying flat)."""
    def p(c):
        flat = along_z and c.face in ("left", "right")
        lanes, run = (c.h, c.w) if flat else (c.w, c.h)
        prev = 0
        for b in range(lanes):
            t = prev if c.rng.random() < 0.4 else c.rng.choice((-1, 0, 0, 1))
            prev = t
            r = c.rng.random()
            kind = "light" if r < streaks else "dark" if r < streaks * 1.6 else None
            s_len = c.rng.randint(max(2, run // 2), max(2, run))
            s0 = c.rng.randrange(max(1, run - s_len + 1))
            for a in range(run):
                x, y = (a, b) if flat else (b, a)
                tt = t + (c.rng.choice((-1, 1)) if c.rng.random() < 0.1 else 0)
                col = c.pick(DRIP_DK if tt < 0 else DRIP_LT if tt > 0 else DRIP)
                if kind and s0 <= a < s0 + s_len:
                    col = mix(col, STREAK if kind == "light" else "#5e493b", 0.62 if kind == "light" else 0.5)
                if c.face in SIDES and c.h > 1:
                    f = 1.04 - (1.04 - low) * y / (c.h - 1)
                elif c.face == "top":
                    f = top
                elif c.face == "bottom":
                    f = 0.68
                else:
                    f = 1.0
                if pale:
                    col = mix(col, PALE, pale)
                c.set(x, y, shade(col, f))
        if rim and c.face in SIDES and c.h > 2:              # light rounded top edge, dark lower lip
            for x in range(c.w):
                c.set(x, 0, mix(c.get(x, 0), STREAK, 0.4))
                c.set(x, c.h - 1, mix(c.get(x, c.h - 1), "#4f3d32", 0.45))
    return p


def plate(c):
    """An armour plate: shingled like an isopod's, so each plate's rear edge is a pale worn lip and its
    front edge sits in the shadow of the plate before it."""
    drip()(c)
    if c.face == "top":                                   # row 0 is the rear edge
        for x in range(c.w):
            c.set(x, 0, mix(c.get(x, 0), STREAK, 0.45))
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), SHADOW, 0.45))
        for x in (0, c.w - 1):
            for y in range(c.h):
                c.set(x, y, shade(c.get(x, y), 0.9))
    elif c.face in ("left", "right"):
        for y in range(c.h):
            c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), SHADOW, 0.45))
            c.set(fx(c, c.w - 1), y, mix(c.get(fx(c, c.w - 1), y), STREAK, 0.35))


# -- calcite -----------------------------------------------------------------------------------------
def calcite(seg=2, low=0.86):
    """Pale calcite, segmented crosswise every `seg` px along the body (rows on the belly, columns on
    the flanks); flanks darken toward the bottom."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = c.pick(CALC)
                if c.face in SIDES and c.h > 1:
                    col = shade(col, 1.0 - (1.0 - low) * y / (c.h - 1))
                elif c.face == "bottom":
                    col = shade(col, 0.9)
                c.set(x, y, col)
        if c.face == "bottom":
            for y in range(seg - 1, c.h, seg):
                for x in range(c.w):
                    c.set(x, y, shade(c.pick(CALC_DK), 0.88))
        elif c.face in ("left", "right"):
            for x in range(seg - 1, c.w, seg):
                for y in range(c.h):
                    c.set(x, y, shade(c.pick(CALC_DK), 0.95 - 0.08 * y / max(1, c.h - 1)))
        c.speckle(CALC_DK, 0.08)
    return p


# -- head --------------------------------------------------------------------------------------------
def skull(c):
    """Dripstone brow on top and sides; the underside of the jaw is calcite."""
    if c.face == "bottom":
        calcite(seg=3)(c)
        return
    drip(rim=False)(c)
    if c.face in ("left", "right"):
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(CALC_DK))
    if c.face == "top":
        for x in range(c.w):                               # brow ridge over the eyes
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), "#5a4538", 0.5))


def face(c):
    """Front of the skull. Row 0 shows above the snout; rows 1-2 only at the outer columns."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(FACE), 1.0 - 0.12 * y))
    dim_glow(c, 1, 0, EYE, 0.6)                            # the main pair
    dim_glow(c, 4, 0, EYE, 0.6)
    dim_glow(c, 0, 1, EYE_DIM, 0.5)                        # the smaller side pair, lower and wider
    dim_glow(c, 5, 1, EYE_DIM, 0.5)
    c.set(0, 2, shade(FACE[0], 0.7)); c.set(5, 2, shade(FACE[0], 0.7))


def snout(c):
    if c.face == "bottom":
        calcite(seg=2)(c)
        return
    if c.face == "top":
        drip(rim=False)(c)
        for x in range(c.w):
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), STREAK, 0.4))
        return
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(DRIP) if y == 0 else c.pick(CALC_DK))
    if c.face == "front":                                  # mouthparts between the fangs
        c.set(1, 1, SOCKET); c.set(2, 1, SOCKET)
        c.set(0, 0, mix(DRIP[0], STREAK, 0.4)); c.set(3, 0, mix(DRIP[0], STREAK, 0.4))


def fang(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(FANG)
            if c.face in SIDES and c.h > 1:
                col = shade(col, 1.02 - 0.12 * y / (c.h - 1))
            elif c.face == "bottom":
                col = FANG_SH
            c.set(x, y, col)


def fang_root(c):
    fang(c)
    if c.face == "back":
        c.fill(FANG_SH)


def fang_hook(c):
    """The hooked point: ivory, its inner end dark."""
    fang(c)
    if c.face == "left":                                   # right fang: the inner (+x) end cap
        c.noise(FANG_TIP)
    elif c.face in ("top", "bottom", "front", "back"):
        col = c.w - 1 if c.face != "back" else 0
        for y in range(c.h):
            c.set(col, y, c.pick(FANG_TIP))


# -- legs --------------------------------------------------------------------------------------------
def femur(c):
    calcite(seg=99, low=0.85)(c)
    if c.face in ("top", "bottom", "front", "back"):
        for y in range(c.h):
            c.set(outer(c, c.w - 1), y, shade(c.pick(CALC_DK), 0.85))     # hip socket
            c.set(outer(c, 2), y, mix(c.get(outer(c, 2), y), CALC_SEAM, 0.6))
    if c.face == "top":
        for x in range(c.w):
            c.set(x, 0, mix(c.get(x, 0), "#ffffff", 0.12))


def knee(c):
    calcite(seg=99, low=0.8)(c)
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(c.get(x, y), CALC_SEAM, 0.35))


def tibia(c):
    calcite(seg=99, low=0.85)(c)
    if c.face in ("top", "bottom", "front", "back"):
        for i in (3, 6):                                   # segment joints
            for y in range(c.h):
                c.set(outer(c, i), y, c.pick([CALC_SEAM, shade(CALC_SEAM, 1.05)]))
        for i in (0, 1):                                   # the dark pointed foot
            for y in range(c.h):
                c.set(outer(c, i), y, c.pick(FOOT) if i == 0 else mix(c.pick(FOOT), CALC[0], 0.45))
    elif c.face == "right":
        c.noise(FOOT)


# -- tail and stalactite -----------------------------------------------------------------------------
def tail_seg(pale, ring=True):
    def p(c):
        drip(pale=pale, rim=False, along_z=True)(c)
        if not ring:
            if c.face == "back":
                c.noise([PALE, mix(PALE, STREAK, 0.5)])
            return
        if c.face in ("left", "right"):                   # dark joint ring at the front end
            for y in range(c.h):
                c.set(fx(c, 0), y, mix(c.get(fx(c, 0), y), "#4f3d32", 0.5))
        elif c.face in ("top", "bottom"):
            for x in range(c.w):
                c.set(x, c.h - 1, mix(c.get(x, c.h - 1), "#4f3d32", 0.5))
    return p


def spike(pale):
    return drip(pale=pale, low=0.84, rim=False)


def stal(pale, eyes=False):
    def p(c):
        drip(pale=pale, low=0.8, rim=False, streaks=0.34)(c)
        if c.face == "bottom":
            c.noise([shade(mix(d, PALE, pale), 0.62) for d in DRIP])
        if eyes and c.face == "front":
            # a dark crack across the top with two tiny dim eyes in it: the only tell
            for x in range(c.w):
                c.set(x, 1, mix(c.get(x, 1), "#4f3d32", 0.45))
            c.set(1, 1, SOCKET); c.set(4, 1, SOCKET)
            dim_glow(c, 1, 1, "#c47426", 0.42)
            dim_glow(c, 4, 1, "#c47426", 0.42)
    return p


# -- leg geometry ------------------------------------------------------------------------------------
def _rot(v, rx, ry, rz):
    """ModelPart rotation of a vector: X first, then Y, then Z."""
    x, y, z = v
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    return (x, y, z)


def knee_bend(hip_y, yaw, lift, l1, l2, half, ground=24.0):
    """Bend of a right shin (rotation about z, negative = down) so its lowest corner reaches the
    ground. The femur is rotated (0, yaw, lift); the shin hangs from its far end."""
    ky = _rot((-l1, 0, 0), 0, yaw, lift)[1]
    for i in range(3000):
        b = -i * 0.001
        low = max(hip_y + ky + _rot(_rot((x, y, z), 0, 0, b), 0, yaw, lift)[1]
                  for x in (-l2, 0) for y in (-half, half) for z in (-half, half))
        if low >= ground:
            return b
    return -2.5


def build():
    m = Model("dripfang", 64, 64, seed=3131)
    pk = Pack(m)

    # body: pivot y 20. A calcite core (belly y 21) under five dripstone plates that step up to the
    # middle of the back (tops 17.5 / 16.5 / 15.5 / 16.5 / 17.5), all with their lower edge at 19.5.
    body = m.part("body", (0, 20, 0))
    pk.add(body, (-3, -2, -6.5), (6, 3, 13), faces(calcite(seg=2)))
    for i, (hw, top, z0, d) in enumerate(((3.5, 17.5, -7, 2), (4, 16.5, -5, 3), (3.5, 15.5, -2, 4),
                                          (4, 16.5, 2, 3), (3.5, 17.5, 5, 2))):
        pk.add(body, (-hw, top - 20, z0), (2 * hw, 19.5 - top, d), faces(plate))

    # a ridge of pointed dripstone along the spine, raked back a little
    for name, z, top, stack in (("spike1", -3.5, 16.5, ((2, 1), (1, 2))),
                                ("spike2", 0, 15.5, ((3, 1), (2, 2), (1, 1))),
                                ("spike3", 3.5, 16.5, ((2, 1), (1, 2)))):
        sp = body.part(name, (0, top - 20 + 0.5, z), (-0.28, 0, 0))
        y = 0.0
        for j, (w, h) in enumerate(stack):
            pale = 0.12 * j + (0.25 if j == len(stack) - 1 else 0)
            pk.add(sp, (-w / 2, y - h, -w / 2), (w, h, w), faces(spike(pale)), share=f"spike{w}{h}{j}")
            y -= h

    # head: a low wedge, stepping down from the collar plate (17.5) to the brow (18) to the snout (19)
    head = body.part("head", (0, -1, -6.5))
    pk.add(head, (-3, -1, -3), (6, 3, 3), faces(skull, front=face))
    pk.add(head, (-2, 0, -5), (4, 2, 2), faces(snout))
    # fangs: sickles from the corners of the snout, reaching forward then hooking inward
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        fg = head.part(side + "_fang", (1.5 * sx, 1.25, -5), (0.1, -0.35 * sx, 0))
        pk.add(fg, (-0.5, -1, -2), (1, 2, 2), None if left else faces(fang_root),
               mirror=left, share="fang_root")
        pk.add(fg, (-0.5, -0.25, -3), (1, 2, 1), None if left else faces(fang),
               mirror=left, share="fang_mid")
        pk.add(fg, (0.25 if sx < 0 else -1.25, 0.75, -3), (1, 1, 1), None if left else faces(fang_hook),
               mirror=left, share="fang_hook", inflate=-0.12)

    # tail: a long pointed dripstone spike going back, tipped up a little
    tail = body.part("tail", (0, -1.5, 6), (0.12, 0, 0))
    pk.add(tail, (-2, -2, 0), (4, 4, 3), faces(tail_seg(0.0)))
    pk.add(tail, (-1.5, -1.5, 3), (3, 3, 3), faces(tail_seg(0.1)))
    tip = tail.part("tail_tip", (0, 0, 6), (0.1, 0, 0))
    pk.add(tip, (-1, -1, 0), (2, 2, 3), faces(tail_seg(0.22)))
    pk.add(tip, (-0.5, -0.5, 3), (1, 1, 2), faces(tail_seg(0.4, ring=False)))

    # legs: the femur rises outward from under the plates to a knobbly knee (the `_shin` child, bent so
    # the foot just reaches y 24), the shin drops steeply to the ground. Yaw fans the pairs out.
    l1, l2 = 6, 9
    for side, sx in (("right", -1), ("left", 1)):
        left = sx > 0
        for i, (z, yaw, lift) in enumerate(((-3.5, -0.62, 0.72), (0, -0.05, 0.78), (3.5, 0.6, 0.72)), start=1):
            bend = knee_bend(20.0, yaw, lift, l1, l2, 0.5)
            lg = body.part(f"{side}_leg{i}", (3 * sx, 0, z), (0, yaw * -sx, lift * -sx))
            pk.add(lg, (-l1 if sx < 0 else 0, -0.5, -0.5), (l1, 1, 1), None if left else faces(femur),
                   mirror=left, share="femur", inflate=0.25)
            shin = lg.part(f"{side}_leg{i}_shin", (l1 * sx, 0, 0), (0, 0, bend * -sx))
            pk.add(shin, (-1, -1, -1), (2, 2, 2), None if left else faces(knee), mirror=left,
                   share="knee", inflate=-0.1)
            pk.add(shin, (-l2 if sx < 0 else 0, -0.5, -0.5), (l2, 1, 1), None if left else faces(tibia),
                   mirror=left, share="tibia")

    # the hanging form: a pointed-dripstone stalactite, top at the top of the hitbox (y 15.2)
    st = m.part("stalactite", (20 if DEBUG_HANG else 0, 15.2, 0))
    y = 0.0
    for j, (w, h) in enumerate(((6, 4), (4, 5), (3, 5), (2, 4), (1, 3))):
        pk.add(st, (-w / 2, y, -w / 2), (w, h, w), faces(stal(0.1 * j + (0.15 if j == 4 else 0), eyes=j == 0)))
        y += h

    pk.apply()
    m.save()
    spawn_egg("dripfang", "#866b5c", "#d8d3cb", accent="#ffb347")


if __name__ == "__main__":
    build()

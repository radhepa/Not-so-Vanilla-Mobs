"""Riftstalker: a tall, gaunt void predator of the outer End islands, about 2.7 blocks tall and
hunched forward over its prey.

Matte black skin with a faint purple sheen, unnaturally thin, with very long arms and reverse-jointed
(digitigrade) legs ending in two-toed black feet. Its body is cracked by glowing magenta-violet rift
seams: down the spine, across the chest and down the outside of each arm. Its head is a smooth,
elongated, eyeless mask-skull of pale End-stone bone, cracked, split by a single vertical glowing
violet slit down its centre. Each forearm ends in a long pale bone scythe blade that curves forward
(the blade is the forearm's lower half). A long whip of a tail hangs down and back from the hips,
ending in a pale bone spike, and a few dark violet shards of broken space float near its shoulders.

Part contract for the animation code: body (pivot at the hips) > head, right_arm > right_forearm,
left_arm > left_forearm, tail > tail_tip; right_leg > right_shin and left_leg > left_shin hang off
the root at the hips. Rest rotations are baked into the parts (the code adds to them)."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Riftstalker"
LOOT = [item("ender_pearl", 1, 2), item("chorus_fruit", 0, 2), item("ender_eye", chance=0.12, looting=False, player_only=True)]
TAGS = []

# matte black skin with a faint purple sheen
SKIN = ["#121018", "#1a1622", "#16131d", "#1a1622", "#221c2c"]
SKIN_TOP = "#2a2337"
SKIN_UNDER = "#0b0a10"
SHEEN = "#2e2540"
# rift seams (glow) and the dim violet light they cast on the skin around them
RIFT_BASE = "#2a0a3a"
RIFT = "#d04cff"
RIFT_DIM = "#a020f0"
RIFT_HOT = "#f0a8ff"
SPILL = "#24122f"
# End-stone bone
BONE = ["#e9e4c4", "#d6d0ab", "#e1dbb8", "#d6d0ab"]
BONE_SHADE = "#bdb68f"
GROOVE = "#c9c29b"
BONE_DARK = "#a39c76"
BONE_PIT = "#b3ac85"
CRACK = "#9a9373"
CRACK_DEEP = "#77714f"
BONE_EDGE = "#f6f2dc"
# floating shards
SHARD = ["#3a1650", "#2d1040", "#45205e"]
SIDES = ("front", "back", "left", "right")


# -- texture packing ---------------------------------------------------------------------------------
class Pack:
    """Face-level packer. Each cube's six box-UV face rectangles go at the first spot (row by row)
    where none of them touches a used texel, so small cubes nest in the empty corners of big ones.
    share= gives several cubes one region (mirrored limbs); pad=True keeps a 1 px empty gutter
    round the cube's faces (for cut-out pixels)."""

    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None, inflate=0.0, pad=False):
        self.items.append((part, origin, size, paint, mirror, share, inflate, pad))

    @staticmethod
    def rects(size):
        w, h, d = (int(math.ceil(s)) for s in size)
        out = [(d, 0, w, d), (d + w, 0, w, d), (0, d, d, h), (d, d, w, h), (d + w, d, d, h), (2 * d + w, d, w, h)]
        return [r for r in out if r[2] > 0 and r[3] > 0]

    def apply(self):
        W, H = self.m.tex_w, self.m.tex_h
        groups, order = {}, []
        for i, it in enumerate(self.items):
            k = it[5] or ("#", i)
            if k not in groups:
                groups[k] = [set(), False]
                order.append(k)
            groups[k][0].update(self.rects(it[2]))
            groups[k][1] = groups[k][1] or it[7]

        def bbox(k):
            rs = groups[k][0]
            return max(x + w for x, y, w, h in rs), max(y + h for x, y, w, h in rs)

        order.sort(key=lambda k: (-bbox(k)[0] * bbox(k)[1], -bbox(k)[1]))
        used = [[False] * W for _ in range(H)]
        pos = {}
        for k in order:
            rs, pad = groups[k]
            bw, bh = bbox(k)
            g = 1 if pad else 0
            cells = sorted({(xx, yy) for (x, y, w, h) in rs
                            for yy in range(y - g, y + h + g) for xx in range(x - g, x + w + g)})
            found = None
            for v in range(0, H - bh + 1):
                for u in range(0, W - bw + 1):
                    if all(not (0 <= u + xx < W and 0 <= v + yy < H) or not used[v + yy][u + xx]
                           for (xx, yy) in cells):
                        found = (u, v)
                        break
                if found:
                    break
            if not found:
                raise ValueError(f"{self.m.id}: no texture room for {k} {bw}x{bh}")
            pos[k] = found
            for (xx, yy) in cells:
                if 0 <= found[0] + xx < W and 0 <= found[1] + yy < H:
                    used[found[1] + yy][found[0] + xx] = True
        for i, (part, origin, size, paint, mirror, share, inflate, pad) in enumerate(self.items):
            part.cube(pos[share or ("#", i)], origin, size, paint, inflate=inflate, mirror=mirror)


# -- forward kinematics (to stand the feet exactly on the ground) -------------------------------------
def rot(r, p):
    """ModelPart rotation (Z, then Y, then X, i.e. R = Rz Ry Rx) applied to point p."""
    x, y, z = p
    rx, ry, rz = r
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    return (x, y, z)


def world(chain, p):
    """chain: [(pivot, rotation), ...] root first; p: a point in the last part's space."""
    for pivot, r in reversed(chain):
        q = rot(r, p)
        p = (q[0] + pivot[0], q[1] + pivot[1], q[2] + pivot[2])
    return p


# -- shared helpers ----------------------------------------------------------------------------------
def tone(c, y, col, k=0.16):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k - 0.06
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


def skin(c, y, k=0.1):
    col = c.pick(SKIN)
    if c.rng.random() < 0.05:
        col = SHEEN
    if c.face == "top":
        col = SKIN_TOP if c.rng.random() < 0.5 else mix(SKIN_TOP, col, 0.5)
    elif c.face == "bottom":
        col = SKIN_UNDER
    return tone(c, y, col, k)


def hide(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, skin(c, y))


def bone(c, y, k=0.1):
    col = c.pick(BONE)
    if c.rng.random() < 0.04:
        col = BONE_PIT
    if c.face == "top":
        col = shade(col, 1.04)
    elif c.face == "bottom":
        col = BONE_DARK
    elif c.face in ("left", "right", "back"):
        col = shade(col, 0.92)
    return tone(c, y, col, k)


def rift_px(c, x, y, heat=1):
    """One pixel of a glowing seam: heat 0 dim, 1 normal, 2 hot."""
    c.glow(x, y, (RIFT_DIM, RIFT, RIFT_HOT)[heat])
    c.set(x, y, RIFT_BASE)


def seam(c, pts):
    """A jagged glowing seam through pts, dimmer at its ends, with violet light spilling on the skin
    beside it."""
    pts = list(pts)
    for (x, y) in pts:
        for (dx, dy) in ((1, 0), (-1, 0)):
            if c.inside(x + dx, y + dy) and (x + dx, y + dy) not in pts and c.rng.random() < 0.45:
                c.set(x + dx, y + dy, SPILL)
    for i, (x, y) in enumerate(pts):
        end = i in (0, len(pts) - 1)
        rift_px(c, x, y, 0 if end else (2 if i % 4 == 2 else 1))


# -- seam paths (face-local pixels), laid out so they run on from face to face -----------------------
SPINE_CHEST = [(2, 0), (2, 1), (3, 2), (3, 3), (2, 4), (2, 5), (3, 6), (3, 7), (2, 8)]
SPINE_CHEST_FORKS = [[(4, 2), (5, 1)], [(1, 5), (0, 6)], [(4, 7), (5, 8)]]
SPINE_WAIST = [(1, 0), (2, 1), (2, 2), (1, 3), (1, 4), (2, 5)]
SPINE_PELVIS = [(2, 0), (2, 1), (3, 2), (2, 3)]
SPINE_NECK = [(1, 0), (1, 1), (2, 2), (1, 3)]
HEAD_BACK = [(3, 5), (3, 4), (2, 3), (2, 2), (1, 1), (1, 0)]
HEAD_BACK_FORK = [(3, 2), (4, 1), (4, 0)]
HEAD_TOP = [(1, 0), (1, 1), (2, 2)]                         # row 0 is the back edge
CHEST_FRONT = [(0, 1), (1, 2), (2, 2), (2, 3), (3, 4), (4, 4), (5, 5)]
CHEST_FRONT_FORK = [(3, 5), (3, 6), (2, 7), (2, 8)]
TAIL_TOP = [(0, 9), (1, 8), (1, 7), (0, 6), (0, 5), (1, 4), (1, 3)]   # row 9 is the body end
ARM_OUT = [(0, 1), (1, 2), (1, 3), (1, 4), (0, 5), (0, 6), (1, 7), (1, 8), (0, 9), (0, 10)]
FOREARM_OUT = [(0, 0), (1, 1), (1, 2), (0, 3)]
THIGH_OUT = [(1, 1), (1, 2), (2, 3), (2, 4), (1, 5)]


def seams(c, paths):
    for path in paths:
        seam(c, path)


def back_col(c, i=0):
    """Column i counted from the back edge of a right/left side face."""
    return i if c.face == "right" else c.w - 1 - i


# -- torso -------------------------------------------------------------------------------------------
def ribs(c, rows):
    """Faint rib ridges: sheen pixels along each given row."""
    for y in rows:
        for x in range(c.w):
            if c.rng.random() < 0.55:
                c.set(x, y, tone(c, y, SHEEN, 0.1))


def chest(c):
    """6x9x4 ribcage: ribs on the front and sides, the spine seam down the back, a seam across the chest."""
    hide(c)
    if c.face == "front":
        ribs(c, (1, 3, 5))
        seams(c, (CHEST_FRONT, CHEST_FRONT_FORK))
    elif c.face == "back":
        for y in (1, 4, 7):                              # shoulder blades catching the light
            c.set(1, y, SHEEN)
            c.set(4, y, SHEEN)
        seams(c, [SPINE_CHEST] + SPINE_CHEST_FORKS)
    elif c.face in ("left", "right"):
        ribs(c, (2, 4, 6))
    elif c.face == "top":
        c.set(2, 3, SPILL)
        c.set(3, 3, SPILL)


def waist(c):
    hide(c)
    if c.face == "back":
        seam(c, SPINE_WAIST)
    elif c.face == "front":
        for y in (1, 3):
            c.set(1, y, SHEEN)
            c.set(2, y, SHEEN)


def pelvis(c):
    hide(c)
    if c.face == "back":
        seam(c, SPINE_PELVIS)
    elif c.face == "front":
        for (x, y) in ((2, 3), (1, 2), (3, 2)):
            c.set(x, y, SKIN_UNDER)


def neck(c):
    hide(c)
    if c.face == "back":
        seam(c, SPINE_NECK)


def vertebra(c):
    hide(c)
    if c.face in ("top", "back"):
        c.set(0, 0, SHEEN)


# -- head and mask -----------------------------------------------------------------------------------
def skull(c):
    """The black head behind the mask; the spine seam climbs its back and forks over the crown."""
    hide(c)
    if c.face == "back":
        seams(c, (HEAD_BACK, HEAD_BACK_FORK))
    elif c.face == "top":
        seam(c, HEAD_TOP)
    elif c.face in ("left", "right"):
        c.set(back_col(c, 1), 2, SHEEN)
        c.set(back_col(c, 2), 4, SHEEN)


def slit(c, col, heat_rows=()):
    """The glowing vertical slit down the middle of the mask front, in a darker groove."""
    for y in range(c.h):
        c.set(col - 1, y, GROOVE)
        c.set(col + 1, y, GROOVE)
        rift_px(c, col, y, 2 if y in heat_rows else 1)


def crack(c, pts, deep=()):
    for (x, y) in pts:
        c.set(x, y, CRACK_DEEP if (x, y) in deep else CRACK)


def mask_plate(part):
    """Painter for one piece of the tapering mask: 'upper', 'mid' or 'chin'."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                col = bone(c, y, 0.06)
                if c.face == "back":
                    col = BONE_DARK                      # the inside of the mask
                c.set(x, y, col)
        if c.face == "front":
            mid = c.w // 2
            if part == "upper":
                for x in range(c.w):
                    c.set(x, 0, shade(c.pick(BONE), 1.05))   # brow of the mask catching the light
                slit(c, mid, heat_rows=(2, 3, 4))
                crack(c, [(2, 1), (1, 2), (1, 3), (0, 4)], deep=[(1, 2)])
                crack(c, [(4, 4), (5, 5), (5, 6)], deep=[(5, 5)])
                crack(c, [(5, 1), (6, 2)])
                c.set(0, 6, BONE_SHADE)
                c.set(6, 0, BONE_SHADE)
            elif part == "mid":
                slit(c, mid, heat_rows=(0,))
                crack(c, [(0, 0), (1, 1)])
            elif part == "chin":
                slit(c, mid)
                c.set(0, c.h - 1, BONE_SHADE)
                c.set(c.w - 1, c.h - 1, BONE_SHADE)
            else:
                rift_px(c, 0, 0, 0)                      # the slit runs out at the point
        elif c.face in ("left", "right") and part == "upper":
            c.set(0 if c.face == "left" else c.w - 1, 3, CRACK)
        elif c.face == "top" and part == "upper":
            c.set(3, 1, CRACK)
            c.set(4, 0, CRACK)
    return p


# -- arms and blades ---------------------------------------------------------------------------------
def upper_arm(c):
    hide(c)
    if c.face == "right":                                # outer face (mirrored onto the left arm)
        seam(c, ARM_OUT)
    elif c.face == "front":
        c.set(0, 3, SHEEN)
        c.set(1, 7, SHEEN)


def shoulder(c):
    hide(c)
    if c.face == "top":
        c.set(1, 1, SHEEN)
        c.set(0, 2, SHEEN)
    elif c.face == "right":
        rift_px(c, 1, 2, 0)                              # the arm seam starts here


def forearm(c):
    """2x6x2 forearm: black skin turning to bone where the blade grows out of it (rows 4-5)."""
    for y in range(c.h):
        for x in range(c.w):
            if y >= 5 or (y == 4 and x % 2 == 0):
                col = BONE_SHADE if y == 4 else bone(c, y, 0.0)
            else:
                col = skin(c, y)
            c.set(x, y, col)
    if c.face == "right":
        seam(c, FOREARM_OUT)
    elif c.face == "top":
        hide(c)


def blade(part):
    """Scythe blade piece: pale bone, a honed light edge in front (-z), a dark spine behind, a
    groove down the flat."""
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, bone(c, y, 0.08))
        if c.face == "front":
            for y in range(c.h):
                c.set(0, y, BONE_EDGE)
        elif c.face == "back":
            for y in range(c.h):
                c.set(0, y, BONE_SHADE if y % 3 else BONE_DARK)
        elif c.face in ("left", "right"):
            for y in range(c.h):
                c.set(back_col(c, 0), y, tone(c, y, BONE_SHADE, 0.1))      # spine
                c.set(back_col(c, c.w - 1), y, BONE_EDGE)                 # edge
            if c.w >= 3:
                for y in range(1, c.h - 1):
                    if y % 4 != 0:
                        c.set(back_col(c, 1), y, tone(c, y, BONE_DARK, 0.1))   # fuller groove
            if part == "base":
                c.set(back_col(c, 1), 0, CRACK)
        elif c.face == "bottom" and part == "point":
            c.fill(BONE_EDGE)
    return p


# -- tail ----------------------------------------------------------------------------------------------
def tail(c):
    """2x2x10 tail base: segmented, the spine seam running out along its top and fading."""
    for y in range(c.h):
        for x in range(c.w):
            col = skin(c, y)
            if c.face in ("left", "right") and x % 3 == 0:
                col = SKIN_UNDER                         # segment rings
            elif c.face in ("top", "bottom") and y % 3 == 0:
                col = SKIN_UNDER
            c.set(x, y, col)
    if c.face == "top":
        seam(c, TAIL_TOP)


def tail_tip(c):
    for y in range(c.h):
        for x in range(c.w):
            col = skin(c, y)
            if (c.face in ("left", "right") and x % 3 == 0) or (c.face in ("top", "bottom") and y % 3 == 0):
                col = SKIN_UNDER
            c.set(x, y, col)
    if c.face == "top":
        rift_px(c, 0, c.h - 1, 0)                        # last flicker of the tail seam


def spike_base(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, bone(c, y, 0.1))
    if c.face in ("left", "right", "top", "bottom"):
        for y in range(c.h):
            c.set(back_col(c, 1) if c.face in ("left", "right") else 0, y, BONE_SHADE)


def spike_point(c):
    """The spike's point faces +z (the 'back' face), away from the tail."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, bone(c, y, 0.08))
    if c.face == "back":
        c.fill(BONE_EDGE)
    elif c.face in ("left", "right"):
        for y in range(c.h):
            c.set(back_col(c, 0), y, BONE_EDGE)
    elif c.face == "top":
        c.set(0, 0, BONE_EDGE)


# -- legs and feet -----------------------------------------------------------------------------------
def thigh(c):
    hide(c)
    if c.face == "right":                                # outer face (mirrored onto the left leg)
        seam(c, THIGH_OUT)
    elif c.face == "front":
        c.set(1, 2, SHEEN)
        c.set(1, 6, SHEEN)


def shin(c):
    hide(c)
    if c.face == "back":
        c.set(0, 2, SHEEN)
        c.set(1, 5, SHEEN)


def heel(c):
    hide(c)


def toe(c):
    """1x1x4 toe: black, ending in a short pale claw."""
    hide(c)
    if c.face == "front":
        c.fill(BONE_SHADE)
    elif c.face == "top":
        c.set(0, c.h - 1, BONE_DARK)


def spur(c):
    """Bone spur on the knee: pale, darker where it grows out of the knee."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, bone(c, y, 0.08))
    if c.face == "front":
        c.fill(BONE_EDGE)
    elif c.face == "back":
        c.fill(BONE_DARK)


def shard(c):
    """A floating sliver of broken space: dark violet, one glowing corner."""
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(SHARD))
    if c.face in ("front", "left", "top"):
        rift_px(c, 0, 0, 1)


def build():
    m = Model("riftstalker", 128, 64, seed=4417)
    pk = Pack(m)

    # torso, leaning forward from the hips
    LEAN = 0.32
    body = m.part("body", (0, 5, 0), (LEAN, 0, 0))
    pk.add(body, (-2.5, -2, -2), (5, 4, 4), faces(pelvis))
    pk.add(body, (-2, -7, -1.5), (4, 6, 3), faces(waist))
    pk.add(body, (-3, -16, -2), (6, 9, 4), faces(chest))
    spine = body.part("spine_knobs")
    for y in (-14.5, -11.5, -8.5):
        pk.add(spine, (-0.5, y, 1.5), (1, 1, 1), faces(vertebra) if y == -14.5 else None, share="knob")

    # head: a black skull behind a tapering bone mask (upper plate, narrower middle, pointed chin)
    head = body.part("head", (0, -15.5, -1), (-LEAN + 0.16, 0, 0))
    pk.add(head, (-1.5, -3.5, -2), (3, 4, 3), faces(neck))
    pk.add(head, (-3, -10, -4.5), (6, 6, 6), faces(skull))
    pk.add(head, (-3.5, -10.5, -6.5), (7, 7, 3), faces(mask_plate("upper")))
    pk.add(head, (-2.5, -3.5, -6.3), (5, 2, 2), faces(mask_plate("mid")))
    pk.add(head, (-1.5, -1.5, -6.1), (3, 2, 2), faces(mask_plate("chin")))
    pk.add(head, (-0.5, 0.5, -5.9), (1, 1, 2), faces(mask_plate("point")))

    # long arms: upper arm, then a forearm that turns into a curved bone scythe (three pieces)
    for side, sx in (("right", -1), ("left", 1)):
        mir = sx > 0

        def pf(painter):
            return None if mir else faces(painter)

        arm = body.part(side + "_arm", (4 * sx, -14.5, 0), (-LEAN - 0.06, 0, -0.1 * sx))
        pk.add(arm, (-1, -1, -1), (2, 11, 2), pf(upper_arm), mirror=mir, share="arm")
        pk.add(arm, (-1.5, -1.5, -1.5), (3, 3, 3), pf(shoulder), mirror=mir, share="shoulder")
        fore = arm.part(side + "_forearm", (0, 10, 0), (-0.32, 0, 0))
        pk.add(fore, (-1, -0.5, -1), (2, 6, 2), pf(forearm), mirror=mir, share="forearm", inflate=0.1)
        pk.add(fore, (-0.5, 5, -2), (1, 6, 3), pf(blade("base")), mirror=mir, share="blade1")
        b2 = fore.part(side + "_blade_curve", (0, 11, -1), (-0.34, 0, 0))
        pk.add(b2, (-0.5, -0.5, -1), (1, 5, 2), pf(blade("curve")), mirror=mir, share="blade2", inflate=-0.05)
        b3 = b2.part(side + "_blade_point", (0, 4.5, -0.5), (-0.4, 0, 0))
        pk.add(b3, (-0.5, -0.5, -0.5), (1, 3, 1), pf(blade("point")), mirror=mir, share="blade3", inflate=-0.12)

    # whip tail hanging down and back, ending in a bone spike
    tl = body.part("tail", (0, -0.5, 1.5), (-0.62 - LEAN, 0, 0))
    pk.add(tl, (-1, -1, 0), (2, 2, 10), faces(tail))
    tip = tl.part("tail_tip", (0, 0, 9.5), (-0.38, 0, 0))
    pk.add(tip, (-0.5, -0.5, 0), (1, 1, 9), faces(tail_tip))
    spike = tip.part("tail_spike", (0, 0, 9), (0.55, 0, 0))
    pk.add(spike, (-1, -1, -0.5), (2, 2, 2), faces(spike_base))
    pk.add(spike, (-0.5, -0.5, 1.5), (1, 1, 3), faces(spike_point))

    # reverse-jointed legs: thigh forward-down, shin back-down, a levelled two-toed foot
    THIGH, SHIN = (-0.5, 0, 0), (1.0, 0, 0)
    for side, sx in (("right", -1), ("left", 1)):
        mir = sx > 0

        def pf(painter):
            return None if mir else faces(painter)

        hip = (2.2 * sx, 5, 0.5)
        leg = m.part(side + "_leg", hip, THIGH)
        pk.add(leg, (-1.5, -1, -1.5), (3, 9, 3), pf(thigh), mirror=mir, share="thigh")
        sh = leg.part(side + "_shin", (0, 8.5, 0), SHIN)
        pk.add(sh, (-1, -0.5, -1), (2, 10, 2), pf(shin), mirror=mir, share="shin")
        kn = sh.part(side + "_knee_spur", (0, 0, -0.5), (-1.05, 0, 0))
        pk.add(kn, (-0.5, -0.5, -3), (1, 1, 3), pf(spur), mirror=mir, share="spur")
        ankle = (0, 9.5, 0)
        foot_rot = (-(THIGH[0] + SHIN[0]), 0, 0)
        chain = [(hip, THIGH), ((0, 8.5, 0), SHIN), (ankle, foot_rot)]
        ground = 24 - world(chain, (0, 0, 0))[1]           # soles exactly on y = 24
        foot = sh.part(side + "_foot", ankle, foot_rot)
        pk.add(foot, (-1, ground - 2.1, -1), (2, 2, 2), pf(heel), mirror=mir, share="heel")
        pk.add(foot, (-1.5, ground - 1, -4.5), (1, 1, 4), pf(toe), mirror=mir, share="toe")
        pk.add(foot, (0.5, ground - 1, -4.5), (1, 1, 4), None, mirror=mir, share="toe")

    # dark violet shards of broken space floating round the shoulders
    for name, pivot, rr in (("shard_right", (-6.5, -16.5, 0.5), (0, 0, 0.6)),
                            ("shard_left", (6, -18, 1.5), (0.4, 0, -0.5)),
                            ("shard_back", (-2, -18.5, 3.5), (0.7, 0.3, 0.2))):
        sd = body.part(name, pivot, rr)
        pk.add(sd, (-0.5, -1, -0.5), (1, 2, 1), faces(shard) if name == "shard_right" else None, share="shard")

    pk.apply()
    m.save()
    spawn_egg("riftstalker", "#121018", "#b03cff", accent="#e9d8c4")


if __name__ == "__main__":
    build()

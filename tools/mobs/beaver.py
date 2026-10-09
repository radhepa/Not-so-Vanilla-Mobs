"""Beaver: a chunky river beaver. Thick glossy fur in rich chestnut brown, darker down the back and
a little paler and warmer on the cheeks and belly; a round, pear-shaped body that is widest over
the hips; a broad blunt head with a pale whisker-padded muzzle, a dark leathery nose, two big
orange buck teeth, small black eyes with a glint and small round dark ears. Little dark forepaws,
big black webbed hind feet, and a flat black paddle of a tail with a scaly cross-hatch.

Rig: `body` holds everything: `head` (with `right_ear` / `left_ear`), the paddle `tail` (the code
slaps it) and all four legs, so the code can tip the whole beaver into a swimming pose."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Beaver"
LOOT = [item("leather", 0, 1)]
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
        used = {}                                   # (x, y) -> "px" or "margin"
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


def zb(c, x, y):
    """Distance from the back edge of a top/bottom/side face (0 = the rearmost pixel)."""
    if c.face in ("top", "bottom"):
        return y
    return x if c.face == "right" else c.w - 1 - x


SIDES = ("front", "back", "left", "right")

# -- palette -----------------------------------------------------------------------------------------
FUR = ["#6e4529", "#6a4226", "#734a2d", "#653f24", "#704829"]
SHEEN = ["#8a5c38", "#93633d", "#845734"]          # glossy guard hairs
DARK = ["#4a2d19", "#523320", "#442915"]
BELLY = ["#7d5434", "#83593a", "#77502f"]
CHEEK = ["#86603f", "#8c6544", "#80593a"]
MUZZLE = ["#9a7856", "#a07e5b", "#94714f"]
MUZZLE_SH = ["#7e5f43", "#77593e"]
NOSE = "#2a1d18"
NOSE_HI = "#5a4a42"
EYE = "#080605"
SHINE = "#f6f4ee"
EAR = ["#3e2616", "#45291a"]
TOOTH = "#e2731f"
TOOTH_HI = "#f39a45"
TOOTH_SH = "#b85512"
PAW = ["#2b1d14", "#322219", "#271a12"]
CLAW = "#5e4d40"
SCALE = ["#2a2522", "#2e2825", "#262120"]
SCALE_LINE = "#4b433d"
SCALE_HI = "#5d544c"


def fur(top=1.08, grad=0.24, belly_rows=0, sheen=0.14, y0=0, span=None):
    """Thick glossy fur: lit on top with streaks of sheen running front to back, darkening down the
    sides toward a warmer belly. y0/span place a face on a body-wide gradient."""
    def p(c):
        sp = span or c.h
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    col = shade(c.pick(BELLY), 0.85)
                elif c.face == "top":
                    col = shade(c.pick(DARK), 1.25) if c.rng.random() < 0.18 else shade(c.pick(FUR), top)
                else:
                    col = shade(c.pick(FUR), 1.06 - grad * ((y0 + y + 0.5) / sp))
                    if belly_rows and y >= c.h - belly_rows and c.face in ("left", "right", "front"):
                        col = mix(col, c.pick(BELLY), 0.6)
                c.set(x, y, col)
        if c.face == "top":                        # sheen: short streaks running front to back
            for _ in range(int(c.w * c.h * sheen / 2) + 1):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                for yy in (y, y + 1):
                    if c.inside(x, yy):
                        c.set(x, yy, c.pick(SHEEN))
        elif c.face in ("left", "right", "front", "back") and c.h > 2:
            for _ in range(int(c.w * c.h * 0.09)):   # coarse hair strokes, 2 px tall
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h - 1)
                k = 0.86 if c.rng.random() < 0.6 else 1.14
                for yy in (y, y + 1):
                    c.set(x, yy, shade(c.get(x, yy), k))
            if c.face in ("left", "right"):
                for x in range(c.w):               # glossy highlights along the top edge
                    if c.rng.random() < sheen * 3:
                        c.set(x, 0, c.pick(SHEEN))
    return p


def spine_top(c):
    """The top of the hips: darker down the middle, glossy streaks either side."""
    fur(top=1.1, sheen=0.25)(c)
    mid = (c.w - 1) / 2
    for y in range(c.h):
        for x in range(c.w):
            if abs(x - mid) < 1.0 and c.rng.random() < 0.7:
                c.set(x, y, shade(c.pick(DARK), 1.1))


def belly(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(BELLY)
            if x in (0, c.w - 1):
                col = shade(col, 0.88)
            c.set(x, y, shade(col, 0.92))


# -- head --------------------------------------------------------------------------------------------
def skull_front(c):
    """6 x 5. The muzzle covers columns 1-4 of rows 3-4. Brown brow, warmer cheeks; the eyes sit on
    the front corners (their glints are on the sides)."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(FUR), 1.06) if y < 2 else c.pick(CHEEK)
            c.set(x, y, col)
    for x in (0, c.w - 1):
        c.set(x, 2, EYE)
    for x in range(1, c.w - 1):                    # a slightly paler bridge leading into the muzzle
        c.set(x, 2, mix(c.pick(CHEEK), c.pick(MUZZLE), 0.3))


def skull_side(c):
    """4 deep x 5 tall: the small eye on the front corner with its glint, a warm cheek below it,
    darker fur behind."""
    for y in range(c.h):
        for x in range(c.w):
            i = fx(c, x)
            col = shade(c.pick(FUR), 1.05 - 0.04 * y)
            if y >= 2 and i <= 1:
                col = c.pick(CHEEK)
            c.set(x, y, col)
    c.set(fx(c, 0), 1, SHINE)
    c.set(fx(c, 0), 2, EYE)
    c.set(fx(c, 1), 2, shade(c.pick(DARK), 0.9))   # the dark rim behind the eye
    c.set(fx(c, 1), 1, shade(c.pick(FUR), 0.9))


def skull_top(c):
    fur(top=1.12, sheen=0.3)(c)


def skull_back(c):
    fur(grad=0.22)(c)


def skull_bottom(c):
    c.noise([shade(b, 0.9) for b in CHEEK])


def muzzle(c):
    """The broad blunt muzzle: pale whisker pads dotted with whisker roots, a dark mouth line."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(MUZZLE)
            if c.face == "top":
                col = mix(c.pick(MUZZLE), c.pick(FUR), 0.45 if y < c.h - 1 else 0.15)
            elif c.face == "bottom":
                col = c.pick(MUZZLE_SH)
            elif c.face in ("right", "left"):
                col = c.pick(MUZZLE) if y == 0 else c.pick(MUZZLE_SH)
            elif c.face == "front":
                col = c.pick(MUZZLE) if y < c.h - 1 else c.pick(MUZZLE_SH)
            c.set(x, y, col)
    if c.face == "front":
        c.set(0, 0, mix(c.pick(MUZZLE), "#3a2a20", 0.35))   # whisker roots on the pads
        c.set(c.w - 1, 0, mix(c.pick(MUZZLE), "#3a2a20", 0.35))
        c.set(c.w // 2 - 1, c.h - 1, mix(c.pick(MUZZLE_SH), NOSE, 0.5))   # the cleft over the teeth
        c.set(c.w // 2, c.h - 1, mix(c.pick(MUZZLE_SH), NOSE, 0.5))
    elif c.face in ("right", "left"):
        c.set(fx(c, 0), 0, mix(c.pick(MUZZLE), "#3a2a20", 0.35))
        c.set(fx(c, c.w - 1), c.h - 1, mix(c.pick(MUZZLE_SH), NOSE, 0.4))   # corner of the mouth


def nose(c):
    """The dark leathery nose: two nostrils on its front, one glint on top."""
    c.fill(NOSE)
    if c.face == "top":
        c.set(0, c.h - 1, shade(NOSE_HI, 0.8))
    elif c.face == "front":
        c.set(0, 0, "#0b0807"); c.set(c.w - 1, 0, "#0b0807")


def teeth(c):
    """Two big orange incisors side by side: glossy at the top, darker at the parting and tips."""
    for y in range(c.h):
        for x in range(c.w):
            col = TOOTH
            if c.face == "front":
                col = TOOTH_HI if y == 0 else TOOTH
                if y == c.h - 1:
                    col = shade(TOOTH, 0.92)
            elif c.face in ("right", "left", "back"):
                col = TOOTH_SH
            elif c.face == "bottom":
                col = shade(TOOTH, 0.9)
            c.set(x, y, col)
    if c.face == "front":                          # the parting between the two teeth
        c.set(c.w // 2, c.h - 1, mix(TOOTH, TOOTH_SH, 0.7))
        c.set(c.w // 2 - 1, c.h - 1, shade(TOOTH, 0.95))


def ear(c):
    c.fill(c.pick(EAR))
    if c.face == "front":
        c.set(0, 0, shade(c.pick(EAR), 0.7))


WHISKER = "#2e221b"


def whiskers(c):
    """Dark whiskers sticking out beside the muzzle (a flat plane, front and back alike)."""
    for x in range(c.w):
        c.set(x, 0, WHISKER)
    outer = 0 if c.face == "front" else c.w - 1   # painted for the right side; the left mirrors it
    c.set(outer, 0, mix(WHISKER, "#6b5545", 0.4))


# -- legs and tail -----------------------------------------------------------------------------------
def fore_leg(c):
    """A short brown forearm into a little dark hand with pale claws."""
    for y in range(c.h):
        for x in range(c.w):
            col = shade(c.pick(FUR), 1.0 - 0.08 * y) if y < c.h - 2 else c.pick(PAW)
            if y == c.h - 2:
                col = mix(c.pick(FUR), c.pick(PAW), 0.6)
            c.set(x, y, col)
    if c.face == "front":
        c.set(0, c.h - 1, CLAW); c.set(c.w - 1, c.h - 1, shade(CLAW, 0.85))
    elif c.face == "bottom":
        c.noise(PAW)


def thigh(c):
    fur(grad=0.25, sheen=0.1)(c)
    if c.face == "bottom":
        c.noise(BELLY)


def shin(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(c.pick(FUR), c.pick(PAW), 0.45 + 0.4 * y))


def webbed_foot(c):
    """The big black hind foot: long toes with paler webbing lines between them, claws in front."""
    c.noise(PAW)
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                if x % 2 == 1 and y >= 1:          # webbing between the toes
                    c.set(x, y, mix(c.pick(PAW), "#4a3a30", 0.6))
        for x in range(0, c.w, 2):                 # toe tips at the front edge
            c.set(x, c.h - 1, shade(c.pick(PAW), 1.4))
    elif c.face == "front":
        for x in range(0, c.w, 2):
            c.set(x, 0, CLAW)
    elif c.face == "bottom":
        c.noise(["#1c130e", "#20160f"])


def paddle(c):
    """The flat scaly tail: near-black leathery skin in a diamond cross-hatch of fine paler lines,
    a soft rim of highlight round the edge."""
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(SCALE)
            if c.face in ("top", "bottom"):
                if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                    col = SCALE_LINE if c.face == "top" else shade(SCALE_LINE, 0.8)
                if c.face == "top" and (x + y) % 3 == 0 and (x - y) % 3 == 0:
                    col = SCALE_HI
                if x in (0, c.w - 1) and c.face == "top":
                    col = mix(col, SCALE_HI, 0.3)
            else:
                col = shade(c.pick(SCALE), 1.25)
            c.set(x, y, col)


def tail_root(c):
    """Where the fur gives way to the scaly paddle."""
    fur(grad=0.2, sheen=0.1)(c)
    if c.face == "back":
        c.noise(SCALE)


def build():
    m = Model("beaver", 64, 64, seed=3232)
    pk = Pack(m)

    # body: pivot at the centre, slung low. Pear-shaped: narrower shoulders (x -3..3, y 16..21,
    # z -6..-1), broad hips (x -4..4, y 15.25..21.25, z -2..5) and a rounded rise over the back.
    body = m.part("body", (0, 19, 0))
    pk.add(body, (-3, -3, -6), (6, 5, 5),
           faces(fur(belly_rows=1, y0=1, span=6), top=fur(top=1.06), bottom=belly))
    pk.add(body, (-4, -3.75, -2), (8, 6, 7),
           faces(fur(belly_rows=1, span=6), top=spine_top, bottom=belly))
    pk.add(body, (-3, -4.75, -1), (6, 1, 5), faces(fur(), top=spine_top))

    # head: pivot at the neck. A broad skull (x -3..3, y 15..20, z -9.5..-5.5), a blunt pale muzzle 2
    # further forward with the dark nose on top of its tip and the orange buck teeth under it.
    head = body.part("head", (0, -1, -6))
    pk.add(head, (-3, -3, -3.5), (6, 5, 4),
           faces(skull_back, front=skull_front, right=skull_side, left=skull_side, top=skull_top,
                 bottom=skull_bottom))
    pk.add(head, (-2, 0, -5.5), (4, 2, 2), faces(muzzle))
    pk.add(head, (-1, -0.4, -5.9), (2, 1, 1), faces(nose), inflate=0.08)
    pk.add(head, (-1, 1.5, -5.1), (2, 2, 1), faces(teeth), inflate=-0.05)
    for sx in (-1, 1):
        left = sx > 0
        for wy in (0.5, 1.1):                      # two hair-thin whiskers a side
            pk.add(head, (2 if left else -5, wy, -4.5), (3, 0.4, 0), None if left else faces(whiskers),
                   mirror=left, share="whiskers")
    for name, sx in (("right_ear", -1), ("left_ear", 1)):
        e = head.part(name, (2.9 * sx, -2.6, -0.5))
        left = sx > 0
        pk.add(e, (-0.5, -0.5, -0.5), (1, 1, 1), None if left else faces(ear), mirror=left,
               share="ear", inflate=0.2)

    # front legs: short little arms with dark hands, under the shoulders
    for name, sx in (("right_front_leg", -1), ("left_front_leg", 1)):
        lg = body.part(name, (2 * sx, 2, -4))
        left = sx > 0
        pk.add(lg, (-1, 0, -1), (2, 3, 2), None if left else faces(fore_leg), mirror=left, share="fleg")

    # hind legs: heavy thighs under the hips, short shins, and big black webbed feet laid flat
    for name, sx in (("right_hind_leg", -1), ("left_hind_leg", 1)):
        lg = body.part(name, (2.75 * sx, 1, 2.5))
        left = sx > 0
        pk.add(lg, (-1.5, -1, -1.5), (3, 3, 3), None if left else faces(thigh), mirror=left, share="thigh")
        pk.add(lg, (-1, 2, -1), (2, 1, 2), None if left else faces(shin), mirror=left, share="shin",
               inflate=-0.05)
        pk.add(lg, (-1.5, 3, -3), (3, 1, 4), None if left else faces(webbed_foot), mirror=left,
               share="foot")

    # tail: a furry root, then the broad flat scaly paddle lying out behind, rounded at the end
    tail = body.part("tail", (0, 1.5, 4.5), (-0.25, 0, 0))
    pk.add(tail, (-1.5, -1, -0.5), (3, 2, 2), faces(tail_root))
    pk.add(tail, (-2.5, -0.5, 1.5), (5, 1, 7), faces(paddle))
    pk.add(tail, (-1.5, -0.5, 8.5), (3, 1, 1), faces(paddle))

    pk.apply()
    m.save()
    spawn_egg("beaver", "#6e4529", "#2a2522", accent="#e2731f")


if __name__ == "__main__":
    build()

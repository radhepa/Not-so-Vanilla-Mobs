"""Capybara: the calmest animal in the world. A round brown barrel of a body with a flat back (small
animals ride on it), a big blunt head with a deep square snout, tiny ears and sleepy half-closed eyes."""
import math

from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Capybara'
LOOT = [item("leather", 0, 1)]
TAGS = []


# -- texture packing: cubes are collected first, then placed tallest-first on shelves ---------------
class Pack:
    def __init__(self, model):
        self.m, self.items = model, []

    def add(self, part, origin, size, paint=None, mirror=False, share=None):
        self.items.append((part, origin, size, paint, mirror, share))

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
        for i, (part, origin, size, paint, mirror, share) in enumerate(self.items):
            part.cube(keys[share or ("#", i)], origin, size, paint, mirror=mirror)


def fx(c, i):
    """Column i counted from the mob's front edge on a right/left side face."""
    return c.w - 1 - i if c.face == "right" else i


# -- palette -----------------------------------------------------------------------------------------
FUR = ["#8b6746", "#866342", "#8f6b49", "#836140", "#8d6947"]
FUR_DARK = ["#6f5236", "#694d33"]
BELLY = ["#a2825b", "#9a7a54"]
SNOUT = ["#6c523e", "#664d39", "#715641"]
NOSE = "#2c1f17"
LID = "#5a412d"
EYE = "#1c130d"


def fur(y0=0.0, span=None, top=1.05, bottom_pal=None, streaks=0.07):
    """Coarse brown fur. Side faces darken downward; y0/span place the face on a body-wide gradient."""
    def p(c):
        sp = span or c.h
        for y in range(c.h):
            if c.face == "top":
                f = top
            elif c.face == "bottom":
                f = 0.82
            else:
                f = 1.06 - 0.3 * ((y0 + y + 0.5) / sp)
            for x in range(c.w):
                pal = bottom_pal if (c.face == "bottom" and bottom_pal) else FUR
                col = c.pick(pal)
                c.set(x, y, shade(col, f))
        # coarse hair: short darker strokes
        n = int(c.w * c.h * streaks / 2)
        for _ in range(n):
            x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
            for yy in (y, y + 1):
                if c.inside(x, yy):
                    c.set(x, yy, shade(c.get(x, yy), 0.86))
    return p


def back_top(c):
    fur(top=1.0, streaks=0.18)(c)
    for y in range(c.h):          # a faintly darker line of fur down the spine
        for x in (c.w // 2 - 1, c.w // 2):
            if c.rng.random() < 0.6:
                c.set(x, y, shade(c.pick(FUR_DARK), 1.05))


def skull_side(c):
    fur(top=1.05)(c)
    a, b = fx(c, 1), fx(c, 2)
    for x in (a, b):              # sleepy eye: heavy lid over a thin dark slit
        c.set(x, 1, shade(c.pick(FUR), 0.9))
        c.set(x, 2, EYE)
        c.set(x, 3, shade(c.pick(FUR), 1.1))
    c.set(fx(c, 3), 2, LID)
    c.set(a, 1, LID); c.set(b, 1, LID)


def skull_front(c):
    fur()(c)
    for x in (0, c.w - 1):
        c.set(x, 1, LID)
        c.set(x, 2, EYE)
        c.set(x, 3, shade(c.pick(FUR), 1.1))


def skull_top(c):
    fur(top=1.02, streaks=0.2)(c)
    for x in range(c.w):          # brow ridge over the snout step
        c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.9))


def snout_front(c):
    rows = [
        "snnnns",
        "sNnnNs",
        "ssnnss",
        "ss..ss",
        "s.mm.s",
        "cccccc",
    ]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "s":
                col = shade(c.pick(SNOUT), 1.0 - 0.04 * y)
            elif ch == "N":
                col = NOSE
            elif ch == "n":
                col = shade(c.pick(SNOUT), 0.78)
            elif ch == ".":
                col = "#4a3627"
            elif ch == "m":
                col = "#2a1d15"
            else:
                col = shade(c.pick(FUR), 0.92)
            c.set(x, y, col)


def snout_side(c):
    fur()(c)
    for y in range(c.h - 1):
        c.set(fx(c, 0), y, shade(c.pick(SNOUT), 1.0))
        if y < 4:
            c.set(fx(c, 1), y, mix(c.pick(SNOUT), c.pick(FUR), 0.5))
    c.set(fx(c, 0), 4, "#2a1d15")
    c.set(fx(c, 1), 4, "#3d2c20")
    c.set(fx(c, 2), 4, shade(c.get(fx(c, 2), 4), 0.85))


def snout_top(c):
    for y in range(c.h):
        for x in range(c.w):
            col = mix(c.pick(FUR), c.pick(SNOUT), y / max(1, c.h - 1))
            c.set(x, y, shade(col, 1.04))


def snout_bottom(c):
    c.noise([shade(b, 0.85) for b in BELLY])


def ear(c):
    c.noise(FUR_DARK)
    if c.face == "front":
        c.set(0, 1, "#3e2b1f"); c.set(1, 1, "#3e2b1f")


def leg(c):
    fur(top=1.0, streaks=0.1)(c)
    if c.face in ("front", "back", "left", "right"):
        for x in range(c.w):
            c.set(x, c.h - 1, c.pick(["#4d3829", "#463325"]))
        if c.face == "front":
            c.set(1, c.h - 1, "#2f2219"); c.set(2, c.h - 1, "#5a4433")


def sole(c):
    c.noise(["#3f2e22", "#463325"])


def build():
    m = Model("capybara", 128, 64, seed=4242)
    pk = Pack(m)

    # body: pivot y 15. core barrel y 11-20, a band 1px wider each side (y 12-18) for roundness,
    # a flat back at y 10 (riders sit here) and a rounded rump
    body = m.part("body", (0, 15, 0))
    pk.add(body, (-5, -4, -7), (10, 9, 14), faces(fur(0, 10), bottom=fur(bottom_pal=BELLY)))
    pk.add(body, (-6, -3, -6), (12, 6, 12), faces(fur(1, 10)))
    pk.add(body, (-4, -5, -6), (8, 1, 12), faces(fur(-0.5, 10), top=back_top))
    pk.add(body, (-4, -3, 7), (8, 7, 1), faces(fur(1, 10)))         # round rump

    # head: child of root, pivot at the neck
    head = m.part("head", (0, 12.5, -6.5))
    pk.add(head, (-4, -3.5, -6), (8, 6, 7), faces(fur(), front=skull_front, right=skull_side,
                                                   left=skull_side, top=skull_top))
    pk.add(head, (-3, -2.5, -10), (6, 6, 4), faces(snout_side, front=snout_front, top=snout_top,
                                                    bottom=snout_bottom))
    for name, x, rz in (("right_ear", -3, -0.25), ("left_ear", 3, 0.25)):
        e = head.part(name, (x, -3.5, -1), (0, 0, rz))
        left = name.startswith("left")
        pk.add(e, (-1, -1.5, -0.75), (2, 1.5, 1.5), None if left else faces(ear), mirror=left, share="ear")

    legp = faces(leg, bottom=sole)
    for name, x, z in (("right_front_leg", -3, -4.5), ("left_front_leg", 3, -4.5),
                       ("right_hind_leg", -3, 4.5), ("left_hind_leg", 3, 4.5)):
        lg = m.part(name, (x, 19, z))
        left = name.startswith("left")
        pk.add(lg, (-2, 0, -2), (4, 5, 4), None if left else legp, mirror=left, share="leg")

    pk.apply()
    m.save()
    spawn_egg("capybara", "#8c6847", "#5f4937", accent="#a2825b")


if __name__ == "__main__":
    build()

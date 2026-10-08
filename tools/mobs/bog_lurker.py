"""Bog Lurker: a huge mossy toad that ambushes from swamp water. Wide head with a big mouth (jaw
drops open, tongue lashes out along -z), warty olive back under moss and duckweed, pale belly,
amber eyes on top of the head, squat front legs and big folded hind legs."""
from mobkit import Model, faces, spawn_egg, shade, mix
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Bog Lurker'
LOOT = [item("slime_ball", 0, 2), item("lily_pad", 0, 1)]
TAGS = ['can_breathe_under_water']

OLIVE = ["#5d6b2f", "#56632b", "#617031", "#52602a", "#5a682e"]
OLIVE_DK = "#3a4419"
WART = ["#76873b", "#7e8f40"]
MOSS = ["#4d7029", "#577b2e", "#466826", "#5f8432"]
WEED = ["#8cbf3f", "#9ccc4a"]
BELLY = ["#d6cd98", "#cbc28a", "#ded6a4"]
MOUTH = ["#b45c5c", "#a85253", "#bd6563"]
MOUTH_DK = "#3e2a1e"
TONGUE = ["#d27480", "#c96a76"]
AMBER = "#e6a524"
AMBER_DK = "#b8781a"
PUPIL = "#17110a"
REED = ["#5f8f2c", "#6fa236", "#507b25"]

SIDES = ("front", "back", "left", "right")


def skin(belly_rows=0, warts=0.07, moss=0.0, weed=0.0, dark_bottom=0.3):
    """Olive toad skin: darker toward the bottom of side faces, warts with a shadow pixel, optional
    belly band on the lowest rows, moss blobs and duckweed specks (mostly on top faces)."""
    def p(c):
        side = c.face in SIDES
        for y in range(c.h):
            for x in range(c.w):
                if c.face == "bottom":
                    c.set(x, y, c.pick(BELLY))
                    continue
                f = 1.06
                if side and c.h > 1:
                    f = 1.08 - dark_bottom * y / (c.h - 1)
                if c.face == "top" and (x in (0, c.w - 1) or y in (0, c.h - 1)):
                    f *= 0.92
                col = shade(c.pick(OLIVE), f)
                if side and belly_rows and y >= c.h - belly_rows:
                    t = (y - (c.h - belly_rows) + 1) / belly_rows
                    col = mix(col, c.pick(BELLY), 0.45 + 0.55 * t)
                c.set(x, y, col)
        if c.face == "bottom":
            return
        limit = c.h - belly_rows - 1 if side else c.h
        for y in range(c.h):                  # dark toad blotches
            for x in range(c.w):
                if y < limit - 1 and c.rng.random() < warts * 0.25:
                    for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                        if c.inside(x + dx, y + dy) and c.rng.random() < 0.8:
                            c.set(x + dx, y + dy, shade(c.pick(OLIVE), 0.78))
        for y in range(c.h):
            for x in range(c.w):
                if y < limit and c.rng.random() < warts:
                    c.set(x, y, c.pick(WART))
                    if c.inside(x, y + 1):
                        c.set(x, y + 1, shade(c.get(x, y + 1), 0.8))
        if moss:
            blobs(c, moss)
        if weed:
            for _ in range(max(1, int(c.w * c.h * weed / 3))):
                x, y = c.rng.randrange(c.w), c.rng.randrange(c.h)
                for (dx, dy) in ((0, 0), (1, 0), (0, 1))[:c.rng.choice((1, 2, 3))]:
                    c.set(x + dx, y + dy, c.pick(WEED))
    return p


def blobs(c, density):
    n = max(1, int(c.w * c.h * density / 14))
    for _ in range(n):
        cx, cy = c.rng.randrange(1, max(2, c.w - 1)), c.rng.randrange(1, max(2, c.h - 1))
        r = c.rng.choice((1.5, 2, 2.5))
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if d <= r * r + 0.3 and (d < r * r - 1 or c.rng.random() < 0.6):
                    c.set(x, y, shade(c.pick(MOSS), 1.08 if d < 1.5 else 1.0))


def head_front(c):
    skin(warts=0.03, dark_bottom=0.15)(c)
    for x in range(c.w):                      # the long mouth line, curving down at the corners
        c.set(x, c.h - 1, MOUTH_DK if 0 < x < c.w - 1 else OLIVE_DK)
    c.set(0, c.h - 2, OLIVE_DK); c.set(c.w - 1, c.h - 2, OLIVE_DK)
    for x in range(1, c.w - 1):               # pale upper lip just above it
        c.set(x, c.h - 2, mix(c.get(x, c.h - 2), BELLY[0], 0.35))
    c.set(7, 1, OLIVE_DK); c.set(10, 1, OLIVE_DK)   # nostrils


def head_side(c):
    skin(warts=0.06, dark_bottom=0.2)(c)
    for x in range(c.w):
        c.set(x, c.h - 1, OLIVE_DK if (x > c.w - 6 if c.face == "right" else x < 5) else shade(c.get(x, c.h - 1), 0.8))
    # a dark stripe from the eye back along the head (toad "mask")
    for x in range(c.w):
        if (c.face == "right" and 1 < x < c.w - 3) or (c.face == "left" and 3 <= x < c.w - 2):
            c.set(x, 1, shade(c.get(x, 1), 0.72))


def head_top(c):
    skin(warts=0.06, moss=0.1)(c)
    # raised glands behind the eyes
    for x in list(range(1, 5)) + list(range(c.w - 5, c.w - 1)):
        for y in (1, 2):
            c.set(x, y, shade(c.pick(WART), 0.95))
        c.set(x, 3, shade(c.get(x, 3), 0.8))


def mouth_roof(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(MOUTH)
            c.set(x, y, mix(col, MOUTH_DK, 0.55 * (1 - y / (c.h - 1))))  # row 0 is the back (throat)
    for x in range(c.w):
        c.set(x, c.h - 1, shade(c.pick(OLIVE), 0.85))   # lip rim at the front


def jaw_top(c):
    mouth_roof(c)
    for y in range(c.h):
        for x in range(c.w):
            if x in (0, c.w - 1):
                c.set(x, y, shade(c.pick(OLIVE), 0.85))


def jaw_side(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, mix(shade(c.pick(OLIVE), 0.95), c.pick(BELLY), [0.0, 0.5, 0.85, 1][min(y, 3)]))
    c.set(0 if c.face == "left" else c.w - 1, 0, OLIVE_DK) if c.face in ("left", "right") else None


def jaw_front(c):
    jaw_side(c)
    for x in range(c.w):
        c.set(x, 0, shade(c.get(x, 0), 0.8))


def eye(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(OLIVE))
    if c.face == "top":
        c.noise(OLIVE)
        for x in range(c.w):
            c.set(x, c.h - 1, shade(c.pick(OLIVE), 1.1))
        return
    if c.face == "front":
        cols = range(c.w)
    elif c.face == "right":
        cols = range(c.w - 3, c.w)            # front half of the outer side
    elif c.face == "left":
        cols = range(0, 3)
    else:
        return
    for x in cols:
        c.set(x, 1, AMBER)
        c.set(x, 2, AMBER_DK)
    if c.face == "front":
        c.set(1, 1, PUPIL); c.set(2, 1, PUPIL)
        c.set(0, 0, shade(OLIVE[0], 0.8)); c.set(3, 0, shade(OLIVE[0], 0.8))
        c.set(3, 1, "#f6d27a")                # glint
    elif c.face == "right":
        c.set(c.w - 1, 1, PUPIL)
    else:
        c.set(0, 1, PUPIL)


def tongue(c):
    c.noise(TONGUE)
    if c.face == "front":
        c.fill("#e48a96")
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, "#e48a96")      # tip
        for y in range(c.h - 1):
            c.set(c.w // 2, y, shade(c.get(c.w // 2, y), 0.85))


def leg(c):
    skin(warts=0.05, dark_bottom=0.35)(c)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 1, shade(c.get(x, 1), 0.7))   # dark band
            if c.h > 5:
                c.set(x, 4, shade(c.get(x, 4), 0.72))


def foot(c):
    if c.face == "bottom":
        c.noise(BELLY)
        return
    skin(warts=0.03, dark_bottom=0.25)(c)
    if c.face == "top":
        # toe grooves running front to back on the front half
        for x in range(1, c.w - 1, 2):
            for y in range(c.h // 2, c.h):
                c.set(x, y, shade(c.get(x, y), 0.75))
        for x in range(0, c.w, 2):
            c.set(x, c.h - 1, mix(c.get(x, c.h - 1), BELLY[0], 0.4))
    if c.face == "front":
        for x in range(1, c.w - 1, 2):
            c.set(x, 0, shade(c.get(x, 0), 0.7))
            c.set(x, c.h - 1, shade(c.get(x, c.h - 1), 0.7))


def haunch(c):
    skin(belly_rows=2 if c.face in SIDES else 0, warts=0.06, dark_bottom=0.3)(c)
    if c.face in ("right", "left"):
        for x in range(c.w):
            if (x + 1) % 3 == 0:              # dark leg bands
                for y in range(1, c.h - 2):
                    c.set(x, y, shade(c.get(x, y), 0.8))


def moss(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(MOSS)
            if c.face != "top":
                col = shade(col, 0.8)
            c.set(x, y, col)
    if c.face == "top":
        c.speckle(WEED, 0.1)
        c.speckle(["#3e5c22"], 0.12)


def reed(c):
    # a little tuft of swamp grass: blades with gaps (cutout)
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, shade(c.pick(REED), 1.0 - 0.12 * y))
    blades = {(0, 0), (2, 0)} if c.face in ("right", "front") else {(1, 0)}
    for (x, y) in [(xx, 0) for xx in range(c.w)]:
        if (x, y) not in blades:
            c.clear(x, y)
    if c.face in ("left", "back"):
        c.clear(0, 1); c.clear(2, 1)
    else:
        c.clear(1, 1)


def build():
    m = Model("bog_lurker", 128, 64, seed=5150)

    body = m.part("body", (0, 21, 2))
    body.cube((56, 0), (-7, -8, -6), (14, 8, 14),
              faces(skin(belly_rows=3, warts=0.05), top=skin(warts=0.06, moss=0.35, weed=0.03)))
    body.cube((56, 22), (-5.5, -10, -4.5), (11, 2, 10),
              faces(skin(warts=0.06, dark_bottom=0.15), top=skin(warts=0.05, moss=0.45, weed=0.04)))
    body.cube((98, 22), (0.5, -11, -2.5), (5, 1, 4), faces(moss))
    body.cube((98, 27), (-6.5, -9, 4), (4, 1, 3), faces(moss))
    body.cube((112, 27), (-5, -11, -3.5), (3, 1, 3), faces(moss))
    reeds = body.part("reeds", (-2.5, -10, 3), (0, 0.6, 0))
    reeds.cube((112, 14), (0, -3, -1.5), (0, 3, 3), faces(reed))
    reeds.cube((118, 14), (-1.5, -3, 0), (3, 3, 0), faces(reed))

    head = m.part("head", (0, 16, -3))
    head.cube((0, 0), (-9, -5, -9), (18, 5, 10),
              faces(skin(warts=0.06), front=head_front, right=head_side, left=head_side, top=head_top,
                    bottom=mouth_roof))
    head.cube((112, 7), (-8, -8, -7), (4, 3, 4), faces(eye))
    head.cube((112, 7), (4, -8, -7), (4, 3, 4), None, mirror=True)
    jaw = head.part("jaw", (0, 0, 1))
    jaw.cube((0, 15), (-8, 0, -9), (16, 3, 9),
             faces(jaw_side, front=jaw_front, top=jaw_top, bottom=lambda c: c.noise(BELLY)))
    head.part("tongue", (0, 0, -1)).cube((112, 0), (-1, 0, -6), (2, 1, 6), faces(tongue))

    for side, sx in (("right", -1), ("left", 1)):
        mir = side == "left"
        fl = m.part(side + "_front_leg", (6 * sx, 18, -2))
        fl.cube((0, 28), (-1.5, 0, -1.5), (3, 5, 3), None if mir else faces(leg), mirror=mir)
        fl.cube((12, 28), (-2.5, 5, -3.5), (5, 1, 5), None if mir else faces(foot), mirror=mir)
        hl = m.part(side + "_hind_leg", (6.5 * sx, 18, 6))
        hl.cube((0, 36), (-3 if sx < 0 else -1, -3, -4), (4, 7, 9), None if mir else faces(haunch), mirror=mir)
        hl.cube((26, 36), (-3.5 if sx < 0 else -1.5, 4, -9), (5, 2, 8), None if mir else faces(foot), mirror=mir)

    m.save()
    spawn_egg("bog_lurker", "#5d6b2f", "#d6cd98", accent="#e6a524")


if __name__ == "__main__":
    build()

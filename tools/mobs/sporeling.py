"""Sporeling: a zombie overgrown by fungus. Mushrooms sprout from its head, shoulder and back,
white mycelium creeps over its grey-violet skin and its eyes glow with spores."""
from mobkit import Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Sporeling'
LOOT = [item("rotten_flesh", 0, 2), either("red_mushroom", "brown_mushroom")]
TAGS = ['zombies', 'burn_in_daylight']

SKIN = ["#7b6b82", "#6e5e76", "#85768b", "#746479", "#665770"]
MYC = ["#d9d1c4", "#c9c0b2", "#e6dfd2"]
SHIRT = ["#6b4a2c", "#5e4026", "#734f2f", "#664628"]
PANTS = ["#3a3f5c", "#343852", "#40466a", "#2f3349"]
CAP = ["#c0302a", "#b02a25", "#cc3a30", "#a8261f"]
STEM = ["#e8dcc0", "#ddd0b2", "#efe5cc"]
GILL = ["#c9b48e", "#bba57f"]
SPOT = "#f2ece0"
EYE = "#5ff5d0"


def skin(myc=0.06):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(MYC) if c.rng.random() < myc else c.pick(SKIN))
    return p


def face(c):
    skin()(c)
    for (x, y) in ((0, 4), (0, 5), (0, 6), (1, 6), (0, 7), (1, 7), (2, 7)):   # mycelium on its right cheek
        c.set(x, y, c.pick(MYC))
    for x in (1, 2, 5, 6):
        c.set(x, 3, "#4d3f55")
        c.set(x, 4, "#1a1320")
    c.glow(2, 4, EYE)
    c.glow(5, 4, EYE)
    c.set(3, 5, "#5a4b62"); c.set(4, 5, "#5a4b62")
    for x in (2, 3, 4, 5):
        c.set(x, 6, "#24182a")
    c.set(3, 6, "#cfc6a8")


def head_top(c):
    skin(0.45)(c)


def shirt(torn=True, rip=False):
    def p(c):
        c.noise(SHIRT)
        if torn:
            for x in range(c.w):
                if c.rng.random() < 0.45:
                    c.set(x, c.h - 1, c.pick(SKIN))
        if rip:
            for (x, y) in ((5, 6), (6, 7), (6, 8)):
                c.set(x, y, c.pick(MYC))
            for (x, y) in ((6, 6), (5, 7)):
                c.set(x, y, c.pick(SKIN))
    return p


def sleeve(c):
    for y in range(c.h):
        for x in range(c.w):
            if c.face in ("top",) or y < 4 or (y == 4 and c.rng.random() < 0.5):
                c.set(x, y, c.pick(SHIRT))
            else:
                c.set(x, y, c.pick(MYC) if c.rng.random() < 0.08 else c.pick(SKIN))


def hand(c):
    skin(0.1)(c)


def pants(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, ("#2a2a30" if c.rng.random() < 0.5 else "#232327") if y >= c.h - 2 else c.pick(PANTS))


def sole(c):
    c.noise(["#2a2a30", "#232327"])


def cap_side(c):
    c.noise(CAP)
    for x in range(1, c.w - 1, 3):
        c.set(x, 0, SPOT)


def cap_top(c):
    c.noise(CAP)
    w, h = c.w, c.h
    for (x, y) in ((1, 1), (w - 2, 1), (w // 2, h // 2), (1, h - 2), (w - 2, h - 2)):
        c.set(x, y, SPOT)


def gills(c):
    c.noise(GILL)


def stem(c):
    c.noise(STEM)


def shelf(c):
    c.noise(["#9a7a55", "#8a6a48", "#b08c62"])
    if c.face == "top":
        for x in range(c.w):
            c.set(x, c.h - 1, "#d8c49c")


def build():
    m = Model("sporeling", 64, 64, seed=1337)
    head, body = humanoid(m, {
        "head": faces(skin(), front=face, top=head_top),
        "body": faces(shirt(), front=shirt(rip=True), top=skin(0.3), bottom=shirt(False)),
        "arm": faces(sleeve, bottom=hand),
        "leg": faces(pants, bottom=sole),
    })
    mushroom = faces(stem)
    cap = faces(cap_side, top=cap_top, bottom=gills)
    # big mushroom on the crown, tilted
    big = head.part("big_mushroom", (1.5, -8, -0.5), (-0.15, 0.4, -0.22))
    big.cube((0, 32), (-1, -4, -1), (2, 4, 2), mushroom)
    big.cube((8, 32), (-3, -6, -3), (6, 2, 6), cap)
    # small mushrooms share one texture
    for name, parent, pivot, rot in (
        ("small_mushroom", head, (-2.5, -8, 2), (0.2, 0.9, 0.35)),
        ("back_mushroom", head, (-1.5, -3, 4), (-1.45, 0, 0)),
        ("shoulder_mushroom", m.get("right_arm"), (-1, -2, 0), (0.1, 0.3, -0.3)),
    ):
        s = parent.part(name, pivot, rot)
        s.cube((32, 32), (-1, -2, -1), (2, 2, 2), mushroom)
        s.cube((40, 32), (-2, -4, -2), (4, 2, 4), cap)
    # bracket fungus shelves on its back
    body.cube((0, 40), (-3, 3, 2), (4, 1, 2), faces(shelf))
    body.cube((0, 40), (0, 7, 2), (4, 1, 2), faces(shelf))
    m.preview = {"right_arm": [-1.45, 0, 0.06], "left_arm": [-1.6, 0, -0.05]}
    m.save()
    spawn_egg("sporeling", "#7b6b82", "#c0302a", accent="#5ff5d0")


if __name__ == "__main__":
    build()

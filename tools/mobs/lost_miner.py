"""Lost Miner: a miner who never came back up. Greenish-grey zombie skin smudged with coal, dusty
denim overalls over a filthy shirt, work boots, a coil of rope on its back and a dented yellow hard
hat whose headlamp still burns. The iron pickaxe is a vanilla held item."""
from mobkit import Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = "Lost Miner"
LOOT = [item("rotten_flesh", 0, 2), item("coal", 0, 2), item("torch", 0, 2),
        item("raw_iron", chance=0.1, looting=False, player_only=True),
        item("raw_gold", chance=0.03, looting=False, player_only=True)]
TAGS = ["zombies", "burn_in_daylight"]

SKIN = ["#6e8562", "#677d5b", "#748b68", "#62785a", "#6b8160"]
SKIN_DARK = "#55694c"
COAL = ["#33362f", "#2b2d28", "#3d4038", "#45483f"]
SHIRT = ["#8a7f6a", "#7f7561", "#948a74", "#776d5a"]
DENIM = ["#4f6a8f", "#486285", "#557299", "#43597b"]
DENIM_DARK = "#364a68"
DENIM_LIGHT = "#6f88ab"
DUST = ["#9a9384", "#8c8676", "#a7a090"]
STITCH = "#c08a3e"
BRASS = "#d0ad4f"
BOOT = ["#5c4030", "#523829", "#664836", "#4b3325"]
SOLE = ["#2f2620", "#29211c", "#352b24"]
LACE = "#c2b28f"
HAT = ["#e6a52a", "#dc9a22", "#eeb236", "#e0a027"]
HAT_SHADE = "#b9761a"
HAT_DEEP = "#9a6114"
HAT_LIGHT = "#f8cf5e"
SCUFF = ["#8f6a3a", "#7d5c33"]
METAL = ["#4a4a48", "#3e3e3c", "#555553"]
LAMP = "#fff3b8"
LAMP_MID = "#ffd86e"
LAMP_EDGE = "#f2b13e"
ROPE = ["#b49a64", "#a68c58", "#c2a870"]
ROPE_DARK = "#6f5d38"
SIDES = ("front", "back", "left", "right")


def tone(c, y, col, k=0.16):
    """Banded darkening toward the bottom of side faces; undersides darker still."""
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


# -- skin -------------------------------------------------------------------------------------------
def skin(coal=0.06):
    def p(c):
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, tone(c, y, c.pick(COAL) if c.rng.random() < coal else c.pick(SKIN), 0.1))
    return p


def face(c):
    skin(0.03)(c)
    for x in range(c.w):                            # shadow of the brim across the brow
        c.set(x, 3, shade(c.pick(SKIN), 0.82))
    c.set(6, 3, COAL[0]); c.set(7, 3, COAL[2])      # a smear over its left eye
    # tired, heavy-lidded eyes (no glow)
    c.set(1, 4, "#3d4536"); c.set(2, 4, "#1d201b")
    c.set(5, 4, "#1d201b"); c.set(6, 4, "#3d4536")
    for x in (1, 2, 5, 6):                          # bags under the eyes
        c.set(x, 5, SKIN_DARK)
    c.set(3, 5, "#4f6146"); c.set(4, 5, "#4f6146")  # nose
    for x in (2, 3, 4, 5):                          # slack mouth
        c.set(x, 6, "#232820")
    c.set(2, 6, "#3a4433")
    for (x, y) in ((0, 5), (0, 6), (1, 6), (0, 7), (7, 6), (6, 7), (7, 7), (3, 7)):   # coal grime
        c.set(x, y, c.pick(COAL))


def head_back(c):
    skin(0.08)(c)
    for x in range(c.w):
        c.set(x, 3, shade(c.pick(SKIN), 0.84))      # strap shadow under the hat


# -- shirt and overalls ------------------------------------------------------------------------------
def dusty(c, x, y, pal, k=0.14, dust=0.08):
    col = c.pick(DUST) if c.rng.random() < dust else c.pick(pal)
    return tone(c, y, col, k)


def torso(c):
    w, h = c.w, c.h
    if c.face == "top":
        for y in range(h):
            for x in range(w):
                strap = x in (1, 2, 5, 6)
                c.set(x, y, dusty(c, x, y, DENIM if strap else SHIRT))
        return
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                c.set(x, y, dusty(c, x, y, DENIM))
        return
    for y in range(h):
        for x in range(w):
            c.set(x, y, dusty(c, x, y, DENIM if y >= 8 else SHIRT))
    if c.face == "front":
        for y in range(0, 3):                       # straps over the shoulders
            for x in (1, 2, 5, 6):
                c.set(x, y, dusty(c, x, y, DENIM))
        for y in range(3, 8):                       # the bib
            for x in range(1, 7):
                c.set(x, y, dusty(c, x, y, DENIM))
        for x in range(1, 7):
            c.set(x, 3, tone(c, 3, DENIM_LIGHT))    # folded top edge of the bib
        c.set(1, 3, BRASS); c.set(6, 3, BRASS)      # strap buttons
        for (x, y) in ((3, 4), (4, 4), (3, 5), (4, 5)):
            c.set(x, y, tone(c, y, DENIM_DARK))     # chest pocket
        c.set(3, 4, STITCH); c.set(4, 4, STITCH)
        c.set(5, 6, c.pick(COAL))                   # coal-black handprint
        c.set(6, 7, c.pick(COAL))
        for x in range(w):                          # waistband
            c.set(x, 8, tone(c, 8, DENIM_DARK))
        c.set(3, 10, tone(c, 10, DENIM_DARK)); c.set(4, 10, tone(c, 10, DENIM_DARK))   # fly
    elif c.face == "back":
        for y in range(7):                          # straps crossing on the back
            a = 1 + round(y * 2 / 6)
            b = 6 - round(y * 2 / 6)
            for x in (a, a + 1, b - 1, b):
                c.set(x, y, dusty(c, x, y, DENIM))
        for x in range(1, 7):
            c.set(x, 7, dusty(c, x, 7, DENIM))
        for x in range(w):
            c.set(x, 8, tone(c, 8, DENIM_DARK))
        for (x, y) in ((1, 9), (2, 9), (1, 10), (2, 10)):   # patched seat
            c.set(x, y, tone(c, y, DENIM_LIGHT))
    else:
        c.set(1, 7, BRASS)                          # side button
        for x in range(w):
            c.set(x, 8, tone(c, 8, DENIM_DARK))


def sleeve(c):
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top" or y < 5:
                col = dusty(c, x, y, SHIRT, 0.1)
            elif y == 5:
                col = tone(c, y, shade(c.pick(SHIRT), 1.1), 0.1)    # rolled-up cuff
            else:
                col = c.pick(COAL) if c.rng.random() < 0.03 + 0.03 * (y - 6) else c.pick(SKIN)
                col = tone(c, y, col, 0.1)
            c.set(x, y, col)


def hand(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, c.pick(COAL) if c.rng.random() < 0.35 else shade(c.pick(SKIN), 0.88))


def trousers(c):
    for y in range(c.h):
        for x in range(c.w):
            if c.face == "top":
                col = dusty(c, x, y, DENIM)
            elif y >= 9:
                col = tone(c, y, c.pick(BOOT), 0.1)
                if y == 9:
                    col = shade(col, 1.12)          # boot cuff
            elif y == 8:
                col = tone(c, y, DENIM_LIGHT, 0.1)  # rolled hem
            else:
                col = dusty(c, x, y, DENIM, 0.1, 0.06 + 0.04 * y / 8)
            c.set(x, y, col)
    if c.face == "front":
        c.set(1, 10, LACE); c.set(2, 10, LACE)      # laces
        c.set(1, 11, shade(c.pick(BOOT), 0.75)); c.set(2, 11, shade(c.pick(BOOT), 0.75))
        c.set(1, 5, tone(c, 5, DENIM_LIGHT, 0.1)); c.set(2, 4, tone(c, 4, DENIM_LIGHT, 0.1))   # worn knee
        c.set(2, 5, c.pick(DUST))


def sole(c):
    c.noise(SOLE)


# -- hard hat ---------------------------------------------------------------------------------------
def hat_paint(c, x, y):
    col = c.pick(HAT)
    if c.rng.random() < 0.06:
        col = c.pick(SCUFF)
    return col


def crown(c):
    """Inflated 8x3x8 shell: bright on top, a dent on the crown and one on the left side."""
    w, h = c.w, c.h
    for y in range(h):
        for x in range(w):
            col = hat_paint(c, x, y)
            if c.face in SIDES and y == h - 1:
                col = shade(col, 0.86)
            if c.face in SIDES and y == 0 and c.rng.random() < 0.5:
                col = HAT_LIGHT
            c.set(x, y, col)
    if c.face == "top":
        for (x, y) in ((1, 1), (2, 1), (1, 2), (6, 5), (7, 5)):
            c.set(x, y, HAT_LIGHT)
        c.set(5, 2, HAT_DEEP); c.set(6, 2, HAT_SHADE); c.set(5, 3, HAT_SHADE)   # dent
        c.set(6, 3, HAT_LIGHT)
        c.set(2, 6, c.pick(SCUFF))
    elif c.face == "left":
        c.set(3, 1, HAT_DEEP); c.set(4, 1, HAT_SHADE); c.set(5, 1, HAT_LIGHT)   # dent
        c.set(2, 2, c.pick(SCUFF))
    elif c.face == "right":
        c.set(5, 1, c.pick(SCUFF)); c.set(6, 1, "#9b9480")     # scratch to bare plastic
    elif c.face == "back":
        for x in range(2, 6):
            c.set(x, 1, HAT_SHADE)                  # adjustment band slot
        c.set(3, 1, METAL[0]); c.set(4, 1, METAL[1])
    elif c.face == "bottom":
        c.fill("#3a3226")                           # dark inside of the shell
        for x in range(w):
            c.set(x, 0, HAT_SHADE); c.set(x, h - 1, HAT_SHADE)


def ridge(c):
    for y in range(c.h):
        for x in range(c.w):
            col = c.pick(HAT)
            if c.face == "top" and x == 0:
                col = HAT_LIGHT
            if c.face in SIDES:
                col = shade(col, 0.92)
            c.set(x, y, col)
    if c.face == "top":
        c.set(1, 4, HAT_SHADE); c.set(0, 5, HAT_DEEP)          # dented ridge


def brim(c):
    w, h = c.w, c.h
    if c.face == "bottom":
        for y in range(h):
            for x in range(w):
                c.set(x, y, shade(c.pick(HAT), 0.62))
        return
    for y in range(h):
        for x in range(w):
            col = hat_paint(c, x, y)
            if c.face == "top":
                edge = x in (0, w - 1) or y in (0, h - 1)
                col = shade(col, 1.06) if edge else shade(col, 0.88)
                if y == h - 1 and 3 <= x <= 7 and c.rng.random() < 0.4:
                    col = c.pick(SCUFF)             # grubby thumb marks on the peak
            else:
                col = shade(col, 0.82)
            c.set(x, y, col)
    if c.face == "top":
        c.set(8, h - 1, HAT_DEEP); c.set(9, h - 1, HAT_SHADE)  # chipped peak
    if c.face == "front":
        c.set(8, 0, HAT_DEEP)


def lamp(c):
    if c.face == "front":
        c.glow(0, 0, LAMP_EDGE); c.glow(1, 0, LAMP_MID); c.glow(2, 0, LAMP_EDGE)
        c.glow(0, 1, LAMP_MID); c.glow(1, 1, LAMP); c.glow(2, 1, LAMP_MID)
        return
    c.noise(METAL)
    if c.face == "top":
        c.set(1, 0, "#6a6a66")


def lamp_mount(c):
    c.noise(METAL)
    if c.face == "front":
        c.set(0, 0, "#6a6a66")


# -- rope coil --------------------------------------------------------------------------------------
def coil(c):
    """6x6x2 coil with its corners knocked out so it reads round from every side."""
    w, h = c.w, c.h
    if c.face in ("front", "back"):
        for y in range(h):
            for x in range(w):
                ring = max(abs(x - 2.5), abs(y - 2.5))
                if ring > 2:
                    col = c.pick(ROPE)
                    if (x + y) % 3 == 0:
                        col = shade(col, 1.12)      # twist highlights
                elif ring > 1:
                    col = shade(c.pick(ROPE), 0.8)
                    if (x + y) % 3 == 1:
                        col = shade(col, 1.12)
                else:
                    col = ROPE_DARK
                c.set(x, y, col)
        for (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            c.clear(x, y)
        if c.face == "back":
            c.set(2, 0, "#8a7448"); c.set(3, 0, "#8a7448")   # binding twist
        return
    for y in range(h):
        for x in range(w):
            col = c.pick(ROPE)
            if (x + y) % 2 == 0:
                col = shade(col, 0.9)
            c.set(x, y, col)
    if c.face in ("left", "right"):
        for x in range(w):
            c.clear(x, 0); c.clear(x, h - 1)
    else:
        for y in range(h):
            c.clear(0, y); c.clear(w - 1, y)


def build():
    m = Model("lost_miner", 64, 64, seed=1311)
    head, body = humanoid(m, {
        "head": faces(skin(0.04), front=face, back=head_back),
        "body": faces(torso),
        "arm": faces(sleeve, bottom=hand),
        "leg": faces(trousers, bottom=sole),
    })

    # dented hard hat: an inflated shell (on the free hat-layer UV), a ridge and a wide brim
    hard_hat = head.part("hard_hat")
    hard_hat.cube((32, 0), (-4, -9, -4), (8, 3, 8), faces(crown), inflate=0.5)
    hard_hat.cube((44, 32), (-1, -10, -4), (2, 1, 8), faces(ridge), inflate=0.3)
    hard_hat.cube((0, 32), (-5.5, -6, -6.5), (11, 1, 11), faces(brim))

    # headlamp clipped to the front of the shell, still burning
    headlamp = hard_hat.part("headlamp", (0, -8, -4.5))
    headlamp.cube((0, 44), (-1.5, -1, -1.2), (3, 2, 1), faces(lamp))
    headlamp.cube((8, 44), (-1, -1.5, -0.4), (2, 1, 1), faces(lamp_mount))

    # coil of rope slung on its back
    rope = body.part("rope_coil", (0, 2, 2), (0.08, 0, 0.05))
    rope.cube((16, 44), (-3, 0, 0), (6, 6, 2), faces(coil))

    m.preview = {"right_arm": [-1.45, 0, 0.06], "left_arm": [-1.6, 0, -0.05]}
    m.save()
    spawn_egg("lost_miner", "#4f6a8f", "#6e8562", accent="#e6a52a")


if __name__ == "__main__":
    build()

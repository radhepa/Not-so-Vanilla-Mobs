"""Gravewarden: a dead knight. A skeleton in rusted iron plate (slit-visored helm, pauldrons,
breastplate, greaves) under a torn dark cape. Sword and shield are vanilla held items."""
from mobkit import Model, faces, humanoid, spawn_egg, shade
from loot import either, item  # noqa: F401

# Mod data for this mob (tools/gen_data.py): display name, loot pools, vanilla entity type tags.
NAME = 'Gravewarden'
LOOT = [item("bone", 1, 3), item("iron_nugget", 1, 4)]
TAGS = ['skeletons']

BONE = ["#cfcabb", "#c4bfae", "#d8d3c5", "#bab5a3"]
GAP = ["#35312a", "#2f2b25", "#3b362e"]
SOCKET = "#15120e"
IRON = ["#74716c", "#6a6763", "#7e7a75", "#63605c"]
IRON_LIGHT = "#a29d95"
IRON_DARK = "#403d3a"
RUST = ["#7d4a2b", "#6e4026", "#8a5532", "#643a22"]
RUST_EDGE = ["#5f4a3a", "#6a5341"]
RIVET = "#2f2c29"
LEATHER = ["#4a3524", "#3f2d1f", "#523b28"]
BRASS = "#a8945e"
CAPE = ["#2e2a33", "#28242c", "#34303a", "#24212a"]
LINING = ["#4a2226", "#3f1d21", "#53272b"]
SIDES = ("front", "back", "left", "right")


def tone(c, y, col, k=0.16):
    if c.face in SIDES and c.h > 2:
        f = 1 - k * y / (c.h - 1)
    elif c.face == "bottom":
        f = 1 - k
    else:
        f = 1.0
    return shade(col, round(f * 16) / 16)


# -- skeleton underneath ----------------------------------------------------------------------------
def bone(c):
    for y in range(c.h):
        for x in range(c.w):
            c.set(x, y, tone(c, y, c.pick(BONE), 0.2))


def skull_face(c):
    bone(c)
    c.rect(1, 3, 2, 2, SOCKET)
    c.rect(5, 3, 2, 2, SOCKET)
    c.set(3, 5, "#3b362e"); c.set(4, 5, SOCKET)
    for x in range(1, 7):
        c.set(x, 6, "#29251f")
        c.set(x, 7, c.pick(BONE) if x % 2 else "#29251f")


def ribcage(c):
    if c.face in ("top", "bottom"):
        bone(c)
        return
    for y in range(c.h):
        for x in range(c.w):
            solid = y in (0, 2, 4, 6, 10, 11) or (c.face in ("front", "back") and x in (3, 4))
            c.set(x, y, tone(c, y, c.pick(BONE) if solid else c.pick(GAP), 0.2))


# -- rusted iron --------------------------------------------------------------------------------------
def iron(c, rust=0.5, rivets=(), ridge=None, rim=True, light_top=True):
    """Grey plate with rust blotches (heavier low down) that bleed into streaks; rivets weep rust."""
    w, h = c.w, c.h
    for y in range(h):
        for x in range(w):
            col = c.pick(IRON)
            if light_top and y == 0 and c.face in SIDES:
                col = IRON_LIGHT if c.rng.random() < 0.6 else col
            c.set(x, y, tone(c, y, col, 0.18))
    # rust: a few soft blotches (more of them low down), a mottled iron-rust edge, and streaks
    blobs = []
    for _ in range(max(1, round(w * h * rust / 16))):
        blobs.append((c.rng.uniform(0, w - 1), (h - 1) * c.rng.random() ** 0.55, c.rng.uniform(0.9, 2.0)))
    for y in range(h):
        for x in range(w):
            d = min((((x - bx) ** 2 + (y - by) ** 2) ** 0.5) / r for (bx, by, r) in blobs)
            if d < 0.85:
                c.set(x, y, tone(c, y, c.pick(RUST), 0.18))
            elif d < 1.25 and c.rng.random() < 0.6:
                c.set(x, y, tone(c, y, c.pick(RUST_EDGE), 0.18))
    for (bx, by, r) in blobs:
        if c.face in SIDES and c.rng.random() < 0.6:
            x0 = int(round(bx))
            for y in range(int(by + r), min(h, int(by + r) + 1 + c.rng.randrange(3))):
                c.set(x0, y, tone(c, y, c.pick(RUST_EDGE), 0.18))
    if ridge is not None and c.face in ("front", "back"):
        for y in range(h):
            c.set(ridge, y, IRON_LIGHT if c.rng.random() < 0.7 else c.pick(IRON))
    if rim and c.face in SIDES and h > 2:
        for x in range(w):
            c.set(x, h - 1, IRON_DARK if c.rng.random() < 0.7 else c.pick(RUST_EDGE))
    for (x, y) in rivets:
        if c.face in SIDES and 0 <= x < w and 0 <= y < h:
            c.set(x, y, RIVET)
            if y + 1 < h:
                c.set(x, y + 1, c.pick(RUST))


def plate(**kw):
    return lambda c: iron(c, **kw)


def helm(c):
    """Great helm over the skull. The eye slit is cut out so the skull's dark sockets show through;
    the underside is left open."""
    if c.face == "bottom":
        return
    if c.face == "top":
        iron(c, rust=0.35)
        return
    iron(c, rust=0.45, rivets=((0, 1), (c.w - 1, 1)) if c.face != "front" else (), rim=True)
    for x in range(c.w):                                     # reinforcing band round the brow
        c.set(x, 2, shade(c.pick(IRON), 1.12))
    if c.face == "front":
        for x in range(1, 7):                                # the slit
            c.clear(x, 3)
        c.set(0, 3, IRON_DARK); c.set(7, 3, IRON_DARK)
        for x in range(1, 7):
            c.set(x, 4, shade(c.pick(IRON), 0.78))          # shadow under the slit's lip
        for y in range(4, 8):                                # raised centre bar
            c.set(3, y, IRON_LIGHT if y < 6 else c.pick(IRON))
            c.set(4, y, c.pick(IRON))
        for (x, y) in ((5, 5), (6, 6), (5, 7)):             # breathing holes
            c.set(x, y, "#24211e")
        c.set(1, 1, RIVET); c.set(6, 1, RIVET)


def cape_mask(w, h, rng):
    """Torn hem and a couple of holes, in front-face columns (col 0 = the mob's right)."""
    cut = []
    for x in range(w):
        cut.append(rng.choice((0, 1, 1, 2, 2, 3, 4)))
    cut[2] = 5; cut[6] = max(cut[6], 4)                     # two deep rips
    holes = {(1, h - 7), (6, h - 9), (7, h - 9), (6, h - 8)}
    return [[(y < h - cut[x]) and (x, y) not in holes for x in range(w)] for y in range(h)]


def cape(mask):
    def p(c):
        w, h = c.w, c.h
        if c.face in ("top", "bottom", "left", "right"):
            for y in range(h):
                for x in range(w):
                    c.set(x, y, shade(c.pick(CAPE), 0.85))
            if c.face == "bottom":                           # the hem underside only under intact cloth
                for x in range(w):
                    if not mask[-1][x]:
                        c.clear(x, 0)
            if c.face in ("left", "right"):                  # follow the torn hem on the edges
                col = 0 if c.face == "right" else len(mask[0]) - 1
                for y in range(h):
                    if not mask[y][col]:
                        c.clear(0, y)
            return
        pal = LINING if c.face == "front" else CAPE
        for y in range(h):
            for x in range(w):
                mx = x if c.face == "front" else w - 1 - x
                if not mask[y][mx]:
                    continue
                col = c.pick(pal)
                if mx % 3 == 1:
                    col = shade(col, 0.82)                   # hanging folds
                if not mask[min(h - 1, y + 1)][mx]:
                    col = shade(col, 0.75)                   # frayed edge
                c.set(x, y, tone(c, y, col, 0.2))
        if c.face == "back":                                 # faded hem stitching near the shoulders
            for x in range(w):
                c.set(x, 0, shade(c.pick(CAPE), 1.25))
    return p


def faulds(c):
    """Belt and two rows of plate lames over the hips."""
    iron(c, rust=0.6, light_top=False)
    if c.face in SIDES:
        for x in range(c.w):
            c.set(x, 0, c.pick(LEATHER))
        if c.face == "front":
            c.set(4, 0, BRASS)
            for y in (1, 2):
                c.set(4, y, IRON_DARK)                       # split between the tassets
        for x in range(c.w):
            c.set(x, 1, shade(c.get(x, 1), 1.08))


def breastplate(c):
    if c.face == "top":
        for y in range(c.h):
            for x in range(c.w):
                c.set(x, y, c.pick(IRON))
        for x in range(2, 7):                                # neck opening
            for y in range(1, 4):
                c.set(x, y, IRON_DARK)
        return
    if c.face == "bottom":
        c.noise([IRON_DARK, "#45423d"])
        return
    iron(c, rust=0.5, ridge=4 if c.face == "front" else None,
         rivets=((1, 1), (c.w - 2, 1)) if c.face in ("front", "back") else ((1, 2),))
    if c.face == "front":
        for y in range(c.h):                                 # curve: edges fall into shadow
            for x in (0, c.w - 1):
                c.set(x, y, shade(c.get(x, y), 0.82))
        for x in range(2, 7):                                # gorget edge under the chin
            c.set(x, 0, IRON_LIGHT)


def build():
    m = Model("gravewarden", 64, 64, seed=1066)
    head, body = humanoid(m, {
        "head": faces(bone, front=skull_face),
        "body": faces(ribcage),
        "arm": faces(bone),
        "leg": faces(bone),
    }, slim_limbs=True)
    right_arm, left_arm = m.get("right_arm"), m.get("left_arm")
    right_leg, left_leg = m.get("right_leg"), m.get("left_leg")

    # helm: a full-size box around the skull (same 8x8x8 layout as the hat slot), inflated 1
    hm = head.part("helm")
    hm.cube((32, 0), (-4, -8, -4), (8, 8, 8), faces(helm), inflate=1.0)
    hm.cube((0, 53), (-0.5, -10.5, -4.5), (1, 2, 9), faces(plate(rust=0.4, rim=False)))   # crest

    # breastplate + faulds on the body
    armour = body.part("breastplate")
    armour.cube((0, 32), (-4.5, -0.5, -2.5), (9, 8, 5), faces(breastplate))
    armour.cube((0, 45), (-4.5, 7.5, -2.5), (9, 3, 5), faces(faulds))

    # torn cape hanging from the shoulders, behind the breastplate
    import random
    mask = cape_mask(9, 18, random.Random(77))
    cp = body.part("cape", (0, 0.5, 2.6), (0.08, 0, 0))
    cp.cube((28, 32), (-4.5, 0, 0), (9, 18, 1), faces(cape(mask)))

    # pauldrons (two layered plates) and vambraces on the arms
    for arm, sx in ((right_arm, -1), (left_arm, 1)):
        side = "right" if sx < 0 else "left"

        def mx(x, size):
            return x if sx < 0 else -x - size

        pd = arm.part(side + "_pauldron", (0, 0, 0), (0, 0, 0.12 * sx))
        pd.cube((28, 51), (mx(-3, 5), -3.5, -2.5), (5, 3, 5), faces(plate(rust=0.45, rivets=((1, 1), (3, 1)))),
                mirror=sx > 0)
        pd.cube((48, 16), (mx(-2.5, 4), -0.5, -2), (4, 2, 4), faces(plate(rust=0.6, light_top=False)),
                mirror=sx > 0)
        vb = arm.part(side + "_vambrace")
        vb.cube((48, 32), (-1.5, 5, -1.5), (3, 4, 3), faces(plate(rust=0.5, rivets=((1, 1),))), mirror=sx > 0)

    # greaves with knee cops
    for leg, sx in ((right_leg, -1), (left_leg, 1)):
        side = "right" if sx < 0 else "left"
        gv = leg.part(side + "_greave")
        gv.cube((48, 22), (-1.5, 5, -1.5), (3, 7, 3), faces(plate(rust=0.65, rivets=((1, 1),))), mirror=sx > 0)
        gv.cube((8, 16), (-1.5, 3.5, -2), (3, 2, 1), faces(plate(rust=0.3, rim=False)), mirror=sx > 0)

    m.save()
    spawn_egg("gravewarden", "#6f6b66", "#8c4a26", accent="#2e2a33")


if __name__ == "__main__":
    build()

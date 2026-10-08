"""Loot pool helpers for mob scripts (Minecraft 26.3 loot format: "modifier"/"type", "condition")."""


def item(name, lo=1, hi=1, chance=None, looting=True, player_only=False):
    """One pool: lo..hi of an item, an optional drop chance, +0..1 per Looting level."""
    entry = {"type": "minecraft:item", "name": "minecraft:" + name, "modifier": []}
    if (lo, hi) != (1, 1):
        entry["modifier"].append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    if looting:
        entry["modifier"].append({"type": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
                                  "count": {"type": "minecraft:uniform", "min": 0.0, "max": 1.0}})
    if not entry["modifier"]:
        del entry["modifier"]
    pool = {"rolls": 1, "entries": [entry]}
    terms = []
    if player_only:
        terms.append({"type": "minecraft:killed_by_player"})
    if chance is not None:
        terms.append({"type": "minecraft:random_chance_with_enchanted_bonus", "enchantment": "minecraft:looting",
                      "unenchanted_chance": chance,
                      "enchanted_chance": {"type": "minecraft:linear", "base": chance + 0.02, "per_level_above_first": 0.01}})
    if len(terms) == 1:
        pool["condition"] = terms[0]
    elif terms:
        pool["condition"] = {"type": "minecraft:all_of", "terms": terms}
    return pool


def either(*names, lo=0, hi=2):
    """One pool that drops lo..hi of one of several items (equal odds)."""
    return {"rolls": 1, "entries": [
        {"type": "minecraft:item", "name": "minecraft:" + n, "modifier": [
            {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}},
            {"type": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
             "count": {"type": "minecraft:uniform", "min": 0.0, "max": 1.0}}]} for n in names]}

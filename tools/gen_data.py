"""Writes the mod's plain data files from the mob scripts' metadata (NAME, LOOT, TAGS):
language, spawn egg item models, loot tables and vanilla entity type tags.

  python tools/gen_data.py
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "nsvmobs")
DATA = os.path.join(ROOT, "src", "main", "resources", "data", "nsvmobs")
TAGS = os.path.join(ROOT, "src", "main", "resources", "data", "minecraft", "tags", "entity_type")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "mobs"))

# Names for entities that aren't mobs (no mob script).
EXTRA_LANG = {"entity.nsvmobs.wyrmling_ember": "Wyrmling Ember", "entity.nsvmobs.boulder": "Boulder",
              "entity.nsvmobs.ice_shard": "Ice Shard", "entity.nsvmobs.web_glob": "Web Glob"}


def mob_ids():
    return sorted(f[:-3] for f in os.listdir(os.path.join(HERE, "mobs")) if f.endswith(".py") and not f.startswith("_"))


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def main():
    lang, tags = {}, {}
    for mob in mob_ids():
        m = importlib.import_module(mob)
        for field in ("NAME", "LOOT", "TAGS"):
            if not hasattr(m, field):
                sys.exit(f"tools/mobs/{mob}.py is missing {field}")
        lang[f"entity.nsvmobs.{mob}"] = m.NAME
        lang[f"item.nsvmobs.{mob}_spawn_egg"] = f"{m.NAME} Spawn Egg"
        egg = f"{mob}_spawn_egg"
        write(os.path.join(ASSETS, "items", egg + ".json"),
              {"model": {"type": "minecraft:model", "model": f"nsvmobs:item/{egg}"}})
        write(os.path.join(ASSETS, "models", "item", egg + ".json"),
              {"parent": "minecraft:item/generated", "textures": {"layer0": f"nsvmobs:item/{egg}"}})
        write(os.path.join(DATA, "loot_table", "entities", mob + ".json"),
              {"type": "minecraft:entity", "pools": m.LOOT, "random_sequence": f"nsvmobs:entities/{mob}"})
        for tag in m.TAGS:
            tags.setdefault(tag, []).append(f"nsvmobs:{mob}")
    lang.update(EXTRA_LANG)
    write(os.path.join(ASSETS, "lang", "en_us.json"), lang)
    os.makedirs(TAGS, exist_ok=True)
    for f in os.listdir(TAGS):
        os.remove(os.path.join(TAGS, f))
    for tag, values in sorted(tags.items()):
        write(os.path.join(TAGS, tag + ".json"), {"replace": False, "values": values})
    print(f"wrote lang, egg models and loot tables for {len(mob_ids())} mobs, {len(tags)} entity tags")


if __name__ == "__main__":
    main()

"""Checks every mob has all its pieces. Run it after adding or renaming a mob:

  python tools/check_mobs.py

A mob is "id" in three places that must agree: the Java catalogue (MobEntry.builder("id", ...) in
NsvEntities.java), its art script tools/mobs/<id>.py, and the files those produce.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "src", "main", "resources")
CATALOGUE = os.path.join(ROOT, "src", "main", "java", "dev", "nsvmobs", "NsvEntities.java")
CLIENT = os.path.join(ROOT, "src", "client", "java", "dev", "nsvmobs", "client", "NsvMobsClient.java")


def main():
    java = open(CATALOGUE, encoding="utf-8").read()
    client = open(CLIENT, encoding="utf-8").read()
    catalogue = dict(re.findall(r'EntityType<\w+> (\w+) = MobEntry\.builder\("(\w+)"', java))   # CONST -> id
    ids = set(catalogue.values())
    scripts = {f[:-3] for f in os.listdir(os.path.join(HERE, "mobs")) if f.endswith(".py") and not f.startswith("_")}
    problems = []
    for mob in sorted(ids - scripts):
        problems.append(f"{mob}: in NsvEntities but has no tools/mobs/{mob}.py")
    for mob in sorted(scripts - ids):
        problems.append(f"{mob}: tools/mobs/{mob}.py exists but NsvEntities has no MobEntry.builder(\"{mob}\", ...)")
    for const, mob in sorted(catalogue.items(), key=lambda kv: kv[1]):
        expected = {
            "geometry (run tools/build_mobs.py)": os.path.join(ROOT, "src", "client", "resources", "assets", "nsvmobs", "geometry", mob + ".json"),
            "texture (run tools/build_mobs.py)": os.path.join(RES, "assets", "nsvmobs", "textures", "entity", mob + ".png"),
            "spawn egg texture (call spawn_egg() in its script)": os.path.join(RES, "assets", "nsvmobs", "textures", "item", mob + "_spawn_egg.png"),
            "egg item model (run tools/gen_data.py)": os.path.join(RES, "assets", "nsvmobs", "items", mob + "_spawn_egg.json"),
            "loot table (run tools/gen_data.py)": os.path.join(RES, "data", "nsvmobs", "loot_table", "entities", mob + ".json"),
        }
        for what, path in expected.items():
            if not os.path.exists(path):
                problems.append(f"{mob}: missing {what}")
        if f"NsvEntities.{const}," not in client:
            problems.append(f"{mob}: no renderer line for NsvEntities.{const} in NsvMobsClient")
    lang = open(os.path.join(RES, "assets", "nsvmobs", "lang", "en_us.json"), encoding="utf-8").read()
    for mob in sorted(ids):
        if f'"entity.nsvmobs.{mob}"' not in lang:
            problems.append(f"{mob}: no name in en_us.json (run tools/gen_data.py)")
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print(f"all {len(ids)} mobs complete")


if __name__ == "__main__":
    main()

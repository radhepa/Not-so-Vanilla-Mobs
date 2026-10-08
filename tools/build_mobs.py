"""Build every mob (or the named ones): geometry JSON, textures and spawn eggs.

  python tools/build_mobs.py            all mobs in tools/mobs
  python tools/build_mobs.py sporeling  just one
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "mobs"))

names = sys.argv[1:] or sorted(f[:-3] for f in os.listdir(os.path.join(HERE, "mobs"))
                               if f.endswith(".py") and not f.startswith("_"))
for n in names:
    importlib.import_module(n).build()
    print("built", n)

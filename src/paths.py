"""Project folders, computed from this file's location,
so they work no matter where the code is run from."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent     # src/paths.py -> project root
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
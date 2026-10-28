"""Project folders, computed from this file's location,
so they work no matter where the code is run from."""
from pathlib import Path

# src/paths.py -> project root
ROOT = Path(__file__).resolve().parent.parent     
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
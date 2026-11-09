"""Inspect dataset folders and CSV columns before implementing training."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for name in ("aptos", "idrid"):
    path = ROOT / "data" / "raw" / name
    print(f"\n{name.upper()}: {path}")
    if not path.exists():
        print("  Folder not found")
        continue
    for item in sorted(path.iterdir()):
        print(f"  {'DIR ' if item.is_dir() else 'FILE'} {item.name}")

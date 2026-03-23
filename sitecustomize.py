from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if SRC.is_dir():
    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

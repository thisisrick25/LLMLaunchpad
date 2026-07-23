import sys
from pathlib import Path


src = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src))

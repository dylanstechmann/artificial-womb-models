"""Put this directory on sys.path so sibling test helpers import under any invocation style."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

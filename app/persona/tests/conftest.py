import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (os.path.join(REPO, "app", "persona"), os.path.join(REPO, "app", "context")):
    if p not in sys.path:
        sys.path.insert(0, p)

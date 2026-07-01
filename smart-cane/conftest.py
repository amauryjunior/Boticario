import sys
from pathlib import Path

# Ensures `from src.xxx import yyy` resolves when pytest is invoked from any
# working directory, without needing package installation.
sys.path.insert(0, str(Path(__file__).resolve().parent))

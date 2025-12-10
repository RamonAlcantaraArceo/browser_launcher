from pathlib import Path
import sys

# Ensure the project `src` directory is on sys.path so tests can import the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

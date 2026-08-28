"""Coloca src/ no sys.path para os testes rodarem sem instalar o pacote."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

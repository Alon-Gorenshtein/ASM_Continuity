from pathlib import Path

MIMIC_HOSP = Path("/path/to/mimic-iv-3.1/hosp")
MIMIC_ICU = Path("/path/to/mimic-iv-3.1/icu")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTERMEDIATE = PROJECT_ROOT / "output" / "intermediate"
TABLES = PROJECT_ROOT / "output" / "tables"
INTERMEDIATE.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

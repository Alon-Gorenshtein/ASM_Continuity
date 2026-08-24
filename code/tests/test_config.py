from pathlib import Path
from lib.config import PROJECT_ROOT, INTERMEDIATE, TABLES


def test_project_root_matches_this_checkout():
    # PROJECT_ROOT must be derived from config.py's actual location, not a hardcoded path
    # to a different checkout (e.g. the main repo when running inside a worktree).
    this_repo_root = Path(__file__).resolve().parents[2]
    assert PROJECT_ROOT == this_repo_root


def test_intermediate_and_tables_under_project_root():
    assert INTERMEDIATE == PROJECT_ROOT / "output" / "intermediate"
    assert TABLES == PROJECT_ROOT / "output" / "tables"
    assert INTERMEDIATE.exists()
    assert TABLES.exists()

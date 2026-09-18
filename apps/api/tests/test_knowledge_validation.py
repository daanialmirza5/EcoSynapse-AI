"""Runs the standalone knowledge-corpus validator (scripts/validate_knowledge.py)
as part of the automated test suite, so a corpus regression fails CI, not
just a manual `python scripts/validate_knowledge.py` run someone forgets to do.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_validator():
    path = Path(__file__).resolve().parents[3] / "scripts" / "validate_knowledge.py"
    spec = importlib.util.spec_from_file_location("validate_knowledge", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_knowledge"] = module
    spec.loader.exec_module(module)
    return module


def test_seed_corpus_has_no_structural_errors(capsys):
    validator = _load_validator()
    exit_code = validator.main()
    captured = capsys.readouterr()
    assert exit_code == 0, captured.out

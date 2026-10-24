"""Skips for tests that audit evidence kept outside version control."""

import unittest
from pathlib import Path


ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


def requires_local_evidence(*names):
    """Skip a test or test class unless every ``artifacts/<name>`` directory exists.

    ``artifacts/`` is gitignored: it holds source files the project does not
    redistribute and the bundles built from them, so a clean clone has none of it.
    Tests that audit that material are reported as skipped there, never as passed.
    Where the directory exists, a missing or changed file inside it still fails.
    """
    absent = [name for name in names if not (ARTIFACTS / name).is_dir()]
    reason = "needs untracked local evidence: " + ", ".join(f"artifacts/{name}" for name in absent)
    return unittest.skipIf(bool(absent), reason)

"""Run the test suite against what a clean clone of the working tree would contain.

CI sees only the files git tracks, with .gitattributes applied. Running the tests in the
working tree can hide failures that depend on untracked local files (``artifacts/``) or
on line endings. This script exports the tracked and not-ignored files, including
uncommitted edits and new files, into a temporary directory and runs the tests there.
A temporary git index and object store are used, so the repository is not modified.

Usage: python scripts/clean_checkout_tests.py [--keep] [-- UNITTEST_ARGS...]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str, env: dict, stdout=subprocess.PIPE) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], env=env, stdout=stdout,
                          stderr=subprocess.PIPE, check=True)


def export_working_tree(destination: Path, scratch: Path) -> str:
    """Write the clean-checkout view of the working tree into ``destination``."""
    relative = git("rev-parse", "--git-path", "objects", env=os.environ.copy()).stdout.decode().strip()
    env = dict(os.environ, GIT_INDEX_FILE=str(scratch / "index"),
               GIT_OBJECT_DIRECTORY=str(scratch / "objects"),
               GIT_ALTERNATE_OBJECT_DIRECTORIES=str((ROOT / relative).resolve()))
    (scratch / "objects").mkdir()
    git("read-tree", "HEAD", env=env)
    git("add", "--renormalize", ".", env=env)
    git("add", "-A", env=env)
    tree = git("write-tree", env=env).stdout.decode().strip()
    archive = subprocess.Popen(["git", "-C", str(ROOT), "archive", tree], env=env,
                               stdout=subprocess.PIPE)
    with tarfile.open(fileobj=archive.stdout, mode="r|") as tar:
        tar.extractall(destination, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    if archive.wait():
        raise SystemExit("git archive failed")
    return tree


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--keep", action="store_true", help="keep the exported directory and print its path")
    parser.add_argument("unittest_args", nargs="*", help="extra arguments for unittest discover (after --)")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="womb-clean-checkout-") as temp:
        scratch, checkout = Path(temp) / "git", Path(temp) / "checkout"
        scratch.mkdir()
        checkout.mkdir()
        try:
            tree = export_working_tree(checkout, scratch)
        except subprocess.CalledProcessError as exc:
            print(f"git failed: {' '.join(map(str, exc.cmd))}\n{exc.stderr.decode(errors='replace')}", file=sys.stderr)
            return 2
        files = sum(1 for path in checkout.rglob("*") if path.is_file())
        print(f"clean-checkout view of the working tree: {files} files (tree {tree[:12]})", flush=True)
        command = [sys.executable, "-B", "-W", "error::ResourceWarning", "-m", "unittest",
                   "discover", "-s", "tests", *args.unittest_args]
        result = subprocess.run(command, cwd=checkout, env=dict(os.environ, PYTHONPATH="src"))
        if args.keep:
            kept = Path(tempfile.mkdtemp(prefix="womb-clean-checkout-kept-"))
            os.replace(checkout, kept / "checkout")
            print(f"kept: {kept / 'checkout'}")
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())

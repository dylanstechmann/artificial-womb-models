import contextlib
import io
import re
import unittest
from pathlib import Path

from wombmodels.cli import main


README = Path(__file__).resolve().parents[1] / "README.md"


class ReadmeCommandTests(unittest.TestCase):
    def cli_commands(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            main(["--help"])
        match = re.search(r"\{([a-z0-9-]+(?:,[a-z0-9-]+)+)\}", out.getvalue())
        self.assertIsNotNone(match, "could not read the command list from --help")
        return match.group(1).split(",")

    def test_the_readme_command_reference_matches_the_cli(self):
        text = README.read_text(encoding="utf-8")
        reference = text[text.index("### Command reference"):text.index("### Source audits and intake notes")]
        commands = self.cli_commands()
        self.assertGreaterEqual(len(commands), 25)
        missing = [name for name in commands if f"| `{name}` |" not in reference]
        self.assertEqual(missing, [], "add these commands to the README command reference")
        documented = set(re.findall(r"^\| `([a-z0-9-]+)` \|", reference, re.M))
        self.assertEqual(sorted(documented - set(commands)), [],
                         "the README documents commands the CLI does not have")

    def test_rerun_functional_examples_and_exit_contract_are_documented(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("wombmodels rerun-bundle --bundle artifacts/exchange-v1 --out artifacts/exchange-reproduction-v1", text)
        self.assertIn("wombmodels rerun-bundle --bundle artifacts/identifiability-v1 --out artifacts/identifiability-reproduction-v1", text)
        self.assertIn("wombmodels verify-bundle --bundle REPRODUCTION_DIRECTORY --strict", text)
        for status in ("reproduced_exact", "not_reproduced", "could_not_run"):
            self.assertIn(status, text)
        self.assertIn("**0**", text)
        self.assertIn("**1**", text)
        self.assertIn("**2**", text)
        self.assertIn("general untrusted-code sandbox", text.lower())


if __name__ == "__main__":
    unittest.main()

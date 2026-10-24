import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNLISTED = {"README.md", "DOCUMENT_MAP.md"}


class DocumentMapTests(unittest.TestCase):
    def setUp(self):
        text = (ROOT / "DOCUMENT_MAP.md").read_text(encoding="utf-8")
        self.linked = re.findall(r"\]\(([^)#\s]+\.md)\)", text)

    def test_every_root_document_is_listed_once(self):
        documents = sorted(path.name for path in ROOT.glob("*.md") if path.name not in UNLISTED)
        missing = [name for name in documents if name not in self.linked]
        self.assertEqual(missing, [], "add these root documents to DOCUMENT_MAP.md")
        repeated = sorted({name for name in self.linked if self.linked.count(name) > 1})
        self.assertEqual(repeated, [], "these documents are listed more than once")

    def test_every_listed_document_exists(self):
        absent = [name for name in self.linked if not (ROOT / name).is_file()]
        self.assertEqual(absent, [], "DOCUMENT_MAP.md links to documents that do not exist")


if __name__ == "__main__":
    unittest.main()

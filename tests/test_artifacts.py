import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wombmodels.artifacts import (MAX_JSON_BYTES, MAX_JSON_DEPTH, MAX_JSON_INTEGER_DIGITS,
                                 InputError, decode_json, publish_bundle, read_json)


class ArtifactTests(unittest.TestCase):
    def test_input_size_limit_is_applied_before_reading_whole_file(self):
        class BoundedStream(io.BytesIO):
            def read(self, size=-1):
                self.requested_size = size
                if size < 0 or size > MAX_JSON_BYTES + 1:
                    raise AssertionError("Input was read without the configured byte limit")
                return super().read(size)

        stream = BoundedStream(b" " * (MAX_JSON_BYTES + 100))
        with patch.object(Path, "open", return_value=stream):
            with self.assertRaisesRegex(InputError, "2 MB"):
                read_json(Path("oversized.json"))
        self.assertEqual(stream.requested_size, MAX_JSON_BYTES + 1)
        self.assertTrue(stream.closed)

    def test_finite_json_and_exact_input_bytes_are_preserved(self):
        raw = b'{ "large": 1e300, "small": 1e-300 }\n'
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_bytes(raw)
            value, saved = read_json(source)
            self.assertEqual(value, {"large": 1e300, "small": 1e-300})
            self.assertEqual(saved, raw)

    def test_exponent_overflow_and_deep_json_have_controlled_errors(self):
        for raw in (b'{"value": 1e999}', b'{"value": -1e999}',
                    b'{"value": ' + b"[" * 5000 + b"0" + b"]" * 5000 + b"}"):
            with self.subTest(raw_prefix=raw[:30]):
                with self.assertRaises(InputError):
                    decode_json(raw)
        for failure in (OverflowError("fixture overflow"), ValueError("fixture number limit")):
            with patch("wombmodels.artifacts.json.loads", side_effect=failure):
                with self.assertRaises(InputError):
                    decode_json(b"{}")

    def test_nesting_limit_has_a_portable_exact_boundary(self):
        raw = b"[" * MAX_JSON_DEPTH + b"0" + b"]" * MAX_JSON_DEPTH
        value = decode_json(raw)
        for _ in range(MAX_JSON_DEPTH):
            self.assertIsInstance(value, list)
            self.assertEqual(len(value), 1)
            value = value[0]
        self.assertEqual(value, 0)
        for raw in (b"[" * (MAX_JSON_DEPTH + 1) + b"0" + b"]" * (MAX_JSON_DEPTH + 1),
                    b'{"value":' * (MAX_JSON_DEPTH + 1) + b"0" + b"}" * (MAX_JSON_DEPTH + 1)):
            with self.subTest(raw_prefix=raw[:30]):
                with patch("wombmodels.artifacts.json.loads") as decoder:
                    with self.assertRaisesRegex(InputError, "nesting limit"):
                        decode_json(raw)
                    decoder.assert_not_called()

    def test_nesting_scan_ignores_strings_and_json_escape_sequences(self):
        text = '[{' * (MAX_JSON_DEPTH + 1) + '}]' * (MAX_JSON_DEPTH + 1)
        expected = {"brackets": text, "quoted": '\\"' + text + '"\\',
                    "escaped": '\\' * 5 + '"' + text}
        raw = json.dumps(expected, ensure_ascii=False).encode("utf-8")
        self.assertEqual(decode_json(raw), expected)
        # A quoted opening bracket must not hide the actual array nesting that
        # follows the closing quote, including an escaped trailing backslash.
        prefix = json.dumps('"\\[{' * 3).encode("utf-8")
        raw = b"[" + prefix + b"," + b"[" * MAX_JSON_DEPTH + b"0" + b"]" * MAX_JSON_DEPTH + b"]"
        with self.assertRaisesRegex(InputError, "nesting limit"):
            decode_json(raw)

    def test_integer_digits_are_bounded_before_integer_conversion(self):
        accepted = "9" * MAX_JSON_INTEGER_DIGITS
        for prefix in ("", "-"):
            raw = ('{"value":' + prefix + accepted + '}').encode()
            self.assertEqual(decode_json(raw), {"value": int(prefix + accepted)})
            raw = ('{"value":' + prefix + accepted + '9}').encode()
            with self.assertRaisesRegex(InputError, "at most.*digits"):
                decode_json(raw)
        # Digit-like text is not a JSON integer and remains ordinary metadata.
        digits = "9" * (MAX_JSON_INTEGER_DIGITS + 1)
        self.assertEqual(decode_json(json.dumps({"text": digits}).encode()), {"text": digits})

    def test_partial_publication_has_no_receipt_and_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            with patch("wombmodels.artifacts.os.link", side_effect=OSError("fixture filesystem error")):
                with self.assertRaises(OSError):
                    publish_bundle(output, kind="fixture", input_raw=b"{}", files={"a.json": b"{}"}, metadata={})
            self.assertTrue(output.is_dir())
            self.assertFalse((output / "receipt.json").exists())
            with self.assertRaises(InputError):
                publish_bundle(output, kind="fixture", input_raw=b"{}", files={"a.json": b"{}"}, metadata={})

    def test_bundle_paths_cannot_escape_output(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("../outside.txt", "receipt.json", "a/b.json"):
                with self.assertRaises(InputError):
                    publish_bundle(Path(directory) / "bundle", kind="fixture", input_raw=b"{}",
                                   files={name: b"{}"}, metadata={})


if __name__ == "__main__":
    unittest.main()

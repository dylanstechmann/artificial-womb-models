import io
import json
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch

from wombmodels.artifacts import InputError
from wombmodels.cli import main
from wombmodels.desk import MAX_RESPONSE_BYTES, desk_endpoint, desk_status


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.server.redirect:
            self.send_response(302)
            self.send_header("Location", "http://example.com/private")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.server.body)

    def log_message(self, *args):
        pass


class DeskTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.redirect = False
        self.server.body = json.dumps({"blueprints": [{"id": "ectogenesis", "title": "Artificial gestation"}],
                                      "campaign_frameworks": {"ectogenesis": [{"id": "stages"}]},
                                      "campaign_starters": {"ectogenesis": [{"id": "evidence-map"}]},
                                      "notes": [{"secret": "private-note"}],
                                      "campaigns": [{"secret": "private-campaign"}]}).encode()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_read_only_discovery_outputs_only_ectogenesis_metadata(self):
        result = desk_status(self.url)
        self.assertTrue(result["ectogenesis_blueprint_present"])
        self.assertEqual(result["starter_ids"], ["evidence-map"])
        self.assertEqual(result["framework_axis_ids"], ["stages"])
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(main(["desk-status", "--url", self.url]), 0)
        self.assertNotIn("private-note", stream.getvalue())
        self.assertNotIn("private-campaign", stream.getvalue())

    def test_external_hosts_credentials_paths_and_queries_rejected(self):
        for url in ("http://example.com", "http://localhost", "http://user:password@127.0.0.1",
                    "file:///tmp/state", "http://127.0.0.1/path", "http://127.0.0.1?secret=value",
                    "http://127.0.0.1#fragment", "http://127.0.0.1:0", "http://127.0.0.1:99999"):
            with self.assertRaises(InputError):
                desk_endpoint(url)
        self.assertEqual(desk_endpoint("http://[::1]:8092"), "http://[::1]:8092/api/state")

    def test_redirect_does_not_reach_external_server(self):
        self.server.redirect = True
        with self.assertRaisesRegex(InputError, "redirects"):
            desk_status(self.url)

    def test_response_size_and_bad_json_rejected(self):
        self.server.body = b"x" * (MAX_RESPONSE_BYTES + 1)
        with self.assertRaisesRegex(InputError, "2 MB"):
            desk_status(self.url)
        self.server.body = b"invalid json"
        with self.assertRaises(InputError):
            desk_status(self.url)
        self.server.body = b"{}"
        with self.assertRaises(InputError):
            desk_status(self.url)

    def test_deep_duplicate_and_nonfinite_response_json_rejected(self):
        for body in (b'{"blueprints": [], "unexpected": 1e999}',
                     b'{"blueprints": [], "blueprints": []}',
                     b'{"blueprints": [], "unexpected": ' + b"[" * 5000 + b"0" + b"]" * 5000 + b"}"):
            with self.subTest(body_prefix=body[:40]):
                self.server.body = body
                with self.assertRaisesRegex(InputError, "bounded UTF-8 JSON"):
                    desk_status(self.url)

    def test_request_allows_cold_desk_probe_with_bounded_timeout(self):
        opener = MagicMock()
        opener.open.return_value = io.BytesIO(self.server.body)
        with patch("wombmodels.desk.build_opener", return_value=opener):
            self.assertTrue(desk_status(self.url)["ectogenesis_blueprint_present"])
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)


if __name__ == "__main__":
    unittest.main()

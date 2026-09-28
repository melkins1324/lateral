#!/usr/bin/env python3
"""
Tests sb_capture against a local mock of the Notion API (no network, no token).

    python3 -m unittest test_sb_capture.py -v
"""
import http.server
import io
import json
import os
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout

os.environ["SB_TIMEOUT"] = "1"
VALID_TOKEN = "ntn_TESTTOKENvalue1234567890"
os.environ["NOTION_TOKEN"] = VALID_TOKEN
TMP = tempfile.mkdtemp()
os.environ["SB_HOME"] = TMP

import sb_capture as S  # noqa: E402


class Mock(http.server.BaseHTTPRequestHandler):
    script = []      # list of (status, json) or "hang" consumed per /pages POST
    pages = []       # created bodies
    requests = []    # (method, path, headers)
    uploads = {}

    def log_message(self, *a):
        pass

    def _send(self, status, obj):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth_ok(self):
        return self.headers.get("Authorization") == f"Bearer {VALID_TOKEN}"

    def do_GET(self):
        Mock.requests.append(("GET", self.path, dict(self.headers)))
        if not self._auth_ok():
            return self._send(401, {"object": "error", "code": "unauthorized", "message": "API token is invalid."})
        self._send(200, {"object": "data_source", "title": [{"plain_text": "Everything"}], "properties": {
            "Name": {"type": "title"}, "Raw Capture": {"type": "rich_text"}, "Source URL": {"type": "url"},
            "Source app": {"type": "rich_text"}, "Attachments": {"type": "files"}, "Date": {"type": "date"},
            "Capture Source": {"type": "select", "select": {"options": [{"name": n} for n in
                               ("Typed", "Siri Shortcut", "Shared from App", "Web Clip")]}},
            "AI Triage": {"type": "select", "select": {"options": [{"name": "Needs AI"}]}}}})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        Mock.requests.append(("POST", self.path, dict(self.headers)))
        if not self._auth_ok():
            return self._send(401, {"object": "error", "code": "unauthorized", "message": "API token is invalid."})
        if self.path == "/v1/file_uploads":
            fid = f"upload-{len(Mock.uploads) + 1}"
            Mock.uploads[fid] = json.loads(raw)
            return self._send(200, {"object": "file_upload", "id": fid, "status": "pending"})
        if self.path.startswith("/v1/file_uploads/") and self.path.endswith("/send"):
            assert b'name="file"' in raw
            return self._send(200, {"object": "file_upload", "status": "uploaded"})
        if self.path.endswith("/query"):
            body = json.loads(raw)
            want = [f for f in body["filter"]["and"] if f.get("property") == "Name"][0]["title"]["equals"]
            hits = [p for p in Mock.pages if p["properties"]["Name"]["title"][0]["text"]["content"] == want]
            return self._send(200, {"object": "list", "results": hits[:1]})
        if self.path == "/v1/pages":
            body = json.loads(raw)
            step = Mock.script.pop(0) if Mock.script else (200, None)
            if step == "hang":            # create succeeds server-side but the client times out
                Mock.pages.append(self._page(body))
                time.sleep(1.5)
                return
            status, obj = step
            if status == 200:
                page = self._page(body)
                Mock.pages.append(page)
                return self._send(200, page)
            return self._send(status, obj)
        self._send(404, {"object": "error", "code": "object_not_found", "message": "nope"})

    @staticmethod
    def _page(body):
        pid = f"page-{len(Mock.pages) + 1}"
        return {"object": "page", "id": pid, "url": f"https://notion.so/{pid}", "properties": body["properties"]}


class CLITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        S.API = f"http://127.0.0.1:{cls.srv.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Mock.script, Mock.pages, Mock.requests, Mock.uploads = [], [], [], {}
        os.environ["NOTION_TOKEN"] = "ntn_TESTTOKENvalue1234567890"
        S.time.sleep = lambda s: None  # no real backoff waits

    def props(self, i=0):
        return Mock.pages[i]["properties"]

    def text(self, prop):
        return "".join(p["text"]["content"] for p in prop["rich_text"])

    def test_siri_style_capture_exact(self):
        t = "Call the dentist Tuesday at 3 PM and also look into hiking in Mendocino."
        page, _ = S.capture(S.get_token(), t, "Siri Shortcut", test=True)
        p = self.props()
        self.assertEqual(self.text(p["Raw Capture"]), t)
        self.assertEqual(p["Name"]["title"][0]["text"]["content"],
                         "[INTEGRATION TEST] Call the dentist Tuesday at 3 PM and…")
        self.assertEqual(p["Capture Source"]["select"]["name"], "Siri Shortcut")
        self.assertEqual(p["AI Triage"]["select"]["name"], "Needs AI")
        self.assertNotIn("Date", p)  # never guessed
        self.assertEqual(len(Mock.pages), 1)

    def test_web_clip_with_note_url_app(self):
        S.capture(S.get_token(), "selected words", "Web Clip", note="my note", title="A Page",
                  url="https://example.com/a", app="Chrome")
        p = self.props()
        self.assertEqual(self.text(p["Raw Capture"]),
                         "Note: my note\nTitle: A Page\nURL: https://example.com/a\n\nselected words")
        self.assertEqual(p["Source URL"]["url"], "https://example.com/a")
        self.assertEqual(self.text(p["Source app"]), "Chrome")
        self.assertEqual(p["Name"]["title"][0]["text"]["content"], "A Page")

    def test_file_attachment_uploaded(self):
        f = os.path.join(TMP, "shot.png")
        with open(f, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\nfake")
        S.capture(S.get_token(), "", "Shared from App", files=[f])
        p = self.props()
        self.assertEqual(p["Attachments"]["files"][0]["file_upload"]["id"], "upload-1")
        self.assertEqual(Mock.uploads["upload-1"]["filename"], "shot.png")
        self.assertEqual(p["Name"]["title"][0]["text"]["content"], "shot.png")

    def test_retry_on_rate_limit_then_success(self):
        Mock.script = [(429, {"object": "error", "code": "rate_limited", "message": "slow down"}), (200, None)]
        S.capture(S.get_token(), "hello", "Typed")
        self.assertEqual(len(Mock.pages), 1)

    def test_timeout_after_server_created_does_not_duplicate(self):
        Mock.script = ["hang"]
        page, _ = S.capture(S.get_token(), "only once please", "Typed")
        self.assertEqual(len(Mock.pages), 1, "the dedupe check must find the page instead of re-creating")
        self.assertEqual(page["id"], "page-1")

    def test_5xx_then_success(self):
        Mock.script = [(503, {"object": "error", "code": "service_unavailable", "message": "down"}), (200, None)]
        S.capture(S.get_token(), "x", "Typed")
        self.assertEqual(len(Mock.pages), 1)

    def test_invalid_token_fails_loudly_and_preserves_input(self):
        os.environ["NOTION_TOKEN"] = "ntn_WRONGTOKEN000000000000"
        with self.assertRaises(SystemExit) as cm:
            S.capture(S.get_token(), "do not lose me", "Typed")
        msg = str(cm.exception)
        self.assertIn("Not saved to Notion", msg)
        self.assertIn("unauthorized", msg)
        self.assertNotIn("WRONGTOKEN", msg)
        saved = sorted(os.listdir(S.OUTBOX))[-1]
        with open(os.path.join(S.OUTBOX, saved)) as fh:
            body = json.load(fh)["body"]
        self.assertEqual(self.text(body["properties"]["Raw Capture"]), "do not lose me")
        self.assertEqual(len(Mock.pages), 0)
        # and it can be replayed once the token is fixed
        os.environ["NOTION_TOKEN"] = "ntn_TESTTOKENvalue1234567890"
        S.replay(S.get_token(), os.path.join(S.OUTBOX, saved))
        self.assertEqual(self.text(self.props()["Raw Capture"]), "do not lose me")

    def test_validation_error_is_not_retried(self):
        Mock.script = [(400, {"object": "error", "code": "validation_error", "message": "bad"})]
        with self.assertRaises(SystemExit):
            S.capture(S.get_token(), "x", "Typed")
        self.assertEqual(sum(1 for r in Mock.requests if r[1] == "/v1/pages"), 1)

    def test_long_text_overflow_attached_in_full(self):
        big = "y" * 120_000
        S.capture(S.get_token(), big, "Typed")
        p = self.props()
        self.assertLessEqual(len(p["Raw Capture"]["rich_text"]), 100)
        self.assertTrue(self.text(p["Raw Capture"]).startswith("y" * 95_000))
        self.assertEqual(Mock.uploads["upload-1"]["filename"], "full-capture.txt")

    def test_logs_contain_no_token_or_text(self):
        S.capture(S.get_token(), "secret diary words", "Typed")
        with open(S.LOG) as fh:
            log = fh.read()
        self.assertNotIn("TESTTOKEN", log)
        self.assertNotIn("secret diary words", log)

    def test_date_only_explicit_iso(self):
        self.assertEqual(S.validate_date("2026-10-06"), {"start": "2026-10-06"})
        for bad in ("Tuesday", "next week", "10/6", "2026-13-01"):
            with self.assertRaises((SystemExit, ValueError)):
                S.validate_date(bad)

    def test_check_reports_schema(self):
        title, problems = S.check(S.get_token())
        self.assertEqual(title, "Everything")
        self.assertEqual(problems, [])

    def test_headers(self):
        S.capture(S.get_token(), "h", "Typed")
        h = [r[2] for r in Mock.requests if r[1] == "/v1/pages"][0]
        self.assertEqual(h["Notion-Version"], "2025-09-03")

    def test_dry_run_prints_body(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            S.main(["--dry-run", "--test", "Brad is the Caltrain conductor who is always chill."])
        body = json.loads(buf.getvalue())
        self.assertEqual(body["parent"]["data_source_id"], S.DATA_SOURCE_ID)


if __name__ == "__main__":
    unittest.main()

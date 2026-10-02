#!/usr/bin/env python3
"""
sb_capture — send a capture to Second Brain 2.0 › Everything from a Mac/Linux terminal.

Standard library only (Python 3.8+). Creates exactly one record per capture with all
essential properties in the single create request. It never classifies, never sets
Type/Status/Priority, and never touches other databases.

Examples
  sb_capture.py "Remember to renew the passport"
  pbpaste | sb_capture.py -                        # clipboard → Raw Capture
  sb_capture.py --url https://example.com --title "Example" --source-app Chrome \
                --source "Web Clip" --note "for the trip" "selected text…"
  sb_capture.py --file ~/Desktop/receipt.pdf --note "tax 2026"
  sb_capture.py --check                            # verify token + database access
  sb_capture.py --replay ~/.second-brain/outbox/2026….json
  sb_capture.py --flush-outbox                     # resend everything waiting in outboxes

Token lookup (never printed, never logged):
  1. $NOTION_TOKEN
  2. macOS Keychain item: service "second-brain-notion" (see README)
"""
import argparse
import datetime as dt
import glob
import json
import mimetypes
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

DATA_SOURCE_ID = os.environ.get("NOTION_DATA_SOURCE_ID", "923ba32e-04e8-4c61-bf44-43093e061c0a")
API = os.environ.get("NOTION_API_BASE", "https://api.notion.com/v1").rstrip("/")
NOTION_VERSION = "2025-09-03"
KEYCHAIN_SERVICE = "second-brain-notion"
HOME = os.path.expanduser(os.environ.get("SB_HOME", "~/.second-brain"))
OUTBOX = os.path.join(HOME, "outbox")
LOG = os.path.join(HOME, "capture.log")
ICLOUD_OUTBOX = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/SecondBrain/Outbox")

CAPTURE_SOURCES = ["Typed", "Siri Shortcut", "Shared from App", "Web Clip", "Voice Note", "Notion", "Imported"]
TEST_PREFIX = "[INTEGRATION TEST] "
PIECE = 1000          # characters per rich-text piece (Notion max 2000)
MAX_PIECES = 95       # Notion max 100 per property; leave room for a notice
TIMEOUT = float(os.environ.get("SB_TIMEOUT", "20"))
ATTEMPTS = int(os.environ.get("SB_ATTEMPTS", "4"))
RETRY_STATUS = {409, 429, 500, 502, 503, 504}
MAX_UPLOAD = 20 * 1024 * 1024  # single-part upload limit


class NotionError(Exception):
    def __init__(self, status, code, message, retryable=False, ambiguous=False):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message = status, code, message
        self.retryable, self.ambiguous = retryable, ambiguous


# ---------------------------------------------------------------------------
# Logging (no secrets, no capture text — only sizes, ids and error codes)
# ---------------------------------------------------------------------------

def log(event, **fields):
    try:
        os.makedirs(HOME, exist_ok=True)
        rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "event": event, **fields}
        with open(LOG, "a") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

def get_token():
    tok = os.environ.get("NOTION_TOKEN", "").strip()
    if tok:
        return tok
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                                 capture_output=True, text=True, timeout=10)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    raise SystemExit("No Notion token found. Set NOTION_TOKEN or add it to the macOS Keychain "
                     f"(service '{KEYCHAIN_SERVICE}') — see README.md.")


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _request(token, method, path, body=None, raw=None, content_type="application/json"):
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read() or b"{}")
        except ValueError:
            err = {}
        retry_after = e.headers.get("Retry-After") if e.headers else None
        ex = NotionError(e.code, err.get("code", "http_error"), err.get("message", str(e)),
                         retryable=e.code in RETRY_STATUS, ambiguous=e.code >= 500)
        ex.retry_after = float(retry_after) if retry_after and retry_after.replace(".", "").isdigit() else None
        raise ex
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        # We cannot know whether Notion processed the request.
        raise NotionError(0, "network_error", str(getattr(e, "reason", e)), retryable=True, ambiguous=True)


def call(token, method, path, body=None, raw=None, content_type="application/json",
         before_retry=None, attempts=None):
    """Retry temporary failures with backoff. before_retry() may return a result to stop early
    (used to detect that an ambiguous create actually succeeded)."""
    attempts = attempts or ATTEMPTS
    for i in range(attempts):
        try:
            return _request(token, method, path, body, raw, content_type)
        except NotionError as e:
            last = e
            log("request_failed", method=method, path=path.split("?")[0], status=e.status, code=e.code, attempt=i + 1)
            if not e.retryable or i == attempts - 1:
                raise
            delay = getattr(e, "retry_after", None) or min(8, 0.5 * 2 ** i) + random.random() * 0.25
            time.sleep(delay)
            if e.ambiguous and before_retry:
                found = before_retry()
                if found:
                    log("dedupe_hit", page=found.get("id"))
                    return found
    raise last  # pragma: no cover


# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------

def make_title(text, fallback="Capture"):
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    words = first.split()
    title = " ".join(words[:8])
    if len(words) > 8:
        title += "…"
    if len(title) > 120:
        title = title[:119] + "…"
    return title or fallback


def rich_text(text):
    return [{"type": "text", "text": {"content": text[i:i + PIECE]}} for i in range(0, len(text), PIECE)]


def validate_date(s):
    """Only explicit ISO dates are accepted. Natural language is never guessed."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        dt.date.fromisoformat(s)
        return {"start": s}
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)?", s):
        dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return {"start": s}
    raise SystemExit(f"--date must be an explicit ISO date like 2026-10-06 or 2026-10-06T15:00; got {s!r}")


def compose_raw(text, note=None, title=None, url=None, files=()):
    """Raw Capture keeps the original text verbatim; the note and metadata are labelled above it."""
    head = []
    if note:
        head.append(f"Note: {note}")
    if title:
        head.append(f"Title: {title}")
    if url:
        head.append(f"URL: {url}")
    for f in files:
        head.append(f"Shared file: {os.path.basename(f)}")
    if not head:
        return text
    return "\n".join(head) + ("\n\n" + text if text else "")


def build_body(title, raw, source, url=None, app=None, date=None, upload_ids=(), test=False):
    pieces = rich_text(raw)
    overflow = len(pieces) > MAX_PIECES
    if overflow:
        pieces = pieces[:MAX_PIECES] + [{"type": "text", "text": {"content":
                 "\n\n[Capture truncated to fit Notion. The complete text is attached as full-capture.txt.]"}}]
    props = {
        "Name": {"title": [{"type": "text", "text": {"content": (TEST_PREFIX if test else "") + title}}]},
        "Raw Capture": {"rich_text": pieces},
        "Capture Source": {"select": {"name": source}},
        "AI Triage": {"select": {"name": "Needs AI"}},
    }
    if url and len(url) <= 2000:
        props["Source URL"] = {"url": url}
    if app:
        props["Source app"] = {"rich_text": rich_text(app)[:1]}
    if date:
        props["Date"] = {"date": date}
    if upload_ids:
        props["Attachments"] = {"files": [{"type": "file_upload", "file_upload": {"id": i}} for i in upload_ids]}
    return {"parent": {"type": "data_source_id", "data_source_id": DATA_SOURCE_ID}, "properties": props}, overflow


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def upload_file(token, path=None, data=None, filename=None):
    if path:
        size = os.path.getsize(path)
        if size > MAX_UPLOAD:
            raise NotionError(0, "too_large", f"{os.path.basename(path)} is {size // 1048576} MB; "
                              "single-part uploads are limited to 20 MB")
        with open(path, "rb") as fh:
            data = fh.read()
        filename = os.path.basename(path)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    up = call(token, "POST", "/file_uploads", {"mode": "single_part", "filename": filename, "content_type": ctype})
    boundary = uuid.uuid4().hex
    safe = filename.replace('"', "_")
    payload = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{safe}\"\r\n"
               f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    res = call(token, "POST", f"/file_uploads/{up['id']}/send", raw=payload,
               content_type=f"multipart/form-data; boundary={boundary}")
    if res.get("status") != "uploaded":
        raise NotionError(0, "upload_incomplete", f"upload status is {res.get('status')!r}")
    log("uploaded", upload=up["id"], bytes=len(data))
    return up["id"]


def find_existing(token, body, since):
    """Look for a page this capture already created (used after an ambiguous failure)."""
    props = body["properties"]
    raw0 = props["Raw Capture"]["rich_text"][0]["text"]["content"][:100] if props["Raw Capture"]["rich_text"] else ""
    flt = {"and": [
        {"timestamp": "created_time", "created_time": {"on_or_after": since}},
        {"property": "Capture Source", "select": {"equals": props["Capture Source"]["select"]["name"]}},
        {"property": "Name", "title": {"equals": props["Name"]["title"][0]["text"]["content"]}},
    ]}
    if raw0:
        flt["and"].append({"property": "Raw Capture", "rich_text": {"starts_with": raw0}})
    try:
        res = _request(token, "POST", f"/data_sources/{DATA_SOURCE_ID}/query", {"filter": flt, "page_size": 1})
        hits = res.get("results", [])
        return hits[0] if hits else None
    except NotionError:
        return None


def create(token, body):
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=2)).isoformat(timespec="seconds")
    page = call(token, "POST", "/pages", body, before_retry=lambda: find_existing(token, body, since))
    if page.get("object") != "page" or not page.get("id"):
        raise NotionError(0, "unexpected_response", "Notion did not return a page")
    log("created", page=page["id"], raw_chars=sum(len(p["text"]["content"])
        for p in body["properties"]["Raw Capture"]["rich_text"]))
    return page


def save_outbox(body, error, files=()):
    os.makedirs(OUTBOX, exist_ok=True)
    name = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{uuid.uuid4().hex[:6]}.json"
    path = os.path.join(OUTBOX, name)
    with open(path, "w") as fh:
        json.dump({"saved_at": dt.datetime.now().isoformat(), "error": error,
                   "files": [os.path.abspath(f) for f in files], "body": body}, fh, ensure_ascii=False, indent=1)
    log("outboxed", file=name, error=error)
    return path


def capture(token, text, source, note=None, title=None, url=None, app=None, date=None, files=(), test=False):
    raw = compose_raw(text, note=note, title=title, url=url, files=files)
    if not raw.strip():
        raise SystemExit("Nothing to capture (empty text and no URL/file).")
    name = title or (os.path.basename(files[0]) if files and not text else None) or make_title(text or raw)

    upload_ids, notes = [], []
    for f in files:
        try:
            upload_ids.append(upload_file(token, path=f))
        except NotionError as e:
            notes.append(f"[Attachment NOT uploaded: {os.path.basename(f)} — {e.message}. "
                         f"The original file is still at {os.path.abspath(f)}]")
    if notes:
        raw += "\n\n" + "\n".join(notes)

    body, overflow = build_body(name, raw, source, url=url, app=app, date=date, upload_ids=upload_ids, test=test)
    if overflow:
        try:
            upload_ids.append(upload_file(token, data=raw.encode(), filename="full-capture.txt"))
            body, _ = build_body(name, raw, source, url=url, app=app, date=date, upload_ids=upload_ids, test=test)
        except NotionError as e:
            body["properties"]["Raw Capture"]["rich_text"][-1]["text"]["content"] = \
                f"\n\n[Capture truncated to fit Notion; full-text upload failed ({e.message}). See the local outbox copy.]"
            save_outbox({"text": raw}, "overflow copy", files)
    try:
        page = create(token, body)
    except NotionError as e:
        path = save_outbox(body, f"{e.code}: {e.message}", files)
        raise SystemExit(f"✗ Not saved to Notion — {e.message} ({e.code}).\n"
                         f"  Nothing is lost: the capture is saved at {path}\n"
                         f"  Resend later with: {sys.argv[0]} --replay '{path}'")
    return page, notes


def replay(token, path):
    with open(path) as fh:
        data = json.load(fh)
    body = data.get("body", data)  # CLI outbox wraps; Shortcuts outbox is the bare body
    try:
        page = create(token, body)
    except NotionError as e:
        if "Attachments" in body.get("properties", {}) and e.status == 400:
            # File upload ids expire after an hour; keep the record, drop the stale reference.
            body["properties"].pop("Attachments")
            body["properties"]["Raw Capture"]["rich_text"].append({"type": "text", "text": {"content":
                "\n\n[Attachment could not be re-attached on replay (upload expired). "
                "The original file is in the Outbox 'files' folder or the source app.]"}})
            page = create(token, body)
        else:
            raise
    done = os.path.join(os.path.dirname(path), "sent")
    os.makedirs(done, exist_ok=True)
    os.replace(path, os.path.join(done, os.path.basename(path)))
    return page


def check(token):
    ds = call(token, "GET", f"/data_sources/{DATA_SOURCE_ID}")
    title = "".join(t.get("plain_text", "") for t in ds.get("title", []))
    need = {"Name": "title", "Raw Capture": "rich_text", "Capture Source": "select", "AI Triage": "select",
            "Source URL": "url", "Source app": "rich_text", "Attachments": "files", "Date": "date"}
    props = ds.get("properties", {})
    problems = [f"{k} (expected {t}, found {props.get(k, {}).get('type', 'missing')})"
                for k, t in need.items() if props.get(k, {}).get("type") != t]
    opts = {o["name"] for o in props.get("Capture Source", {}).get("select", {}).get("options", [])}
    problems += [f"Capture Source option '{o}' missing" for o in ("Siri Shortcut", "Shared from App", "Web Clip", "Typed")
                 if o not in opts]
    triage = {o["name"] for o in props.get("AI Triage", {}).get("select", {}).get("options", [])}
    if "Needs AI" not in triage:
        problems.append("AI Triage option 'Needs AI' missing")
    return title, problems


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Capture into Second Brain 2.0 › Everything")
    ap.add_argument("text", nargs="?", help="text to capture, or - to read stdin")
    ap.add_argument("--note", help="your note (stored in Raw Capture above the original text)")
    ap.add_argument("--title", help="original title (used as Name)")
    ap.add_argument("--url", help="source URL")
    ap.add_argument("--source-app", default=None, help="originating app, e.g. Chrome")
    ap.add_argument("--source", default="Typed", choices=CAPTURE_SOURCES, help="Capture Source (default Typed)")
    ap.add_argument("--file", action="append", default=[], help="attach a file (repeatable, ≤20 MB each)")
    ap.add_argument("--date", help="explicit ISO date only, e.g. 2026-10-06 or 2026-10-06T15:00-07:00")
    ap.add_argument("--test", action="store_true", help="prefix Name with [INTEGRATION TEST]")
    ap.add_argument("--dry-run", action="store_true", help="print the request body; send nothing")
    ap.add_argument("--check", action="store_true", help="verify token, database access and schema")
    ap.add_argument("--replay", metavar="FILE", help="resend a saved outbox file")
    ap.add_argument("--flush-outbox", action="store_true", help="resend every file in the local and iCloud outboxes")
    a = ap.parse_args(argv)

    if a.dry_run:
        text = sys.stdin.read() if a.text == "-" else (a.text or "")
        raw = compose_raw(text, a.note, a.title, a.url, a.file)
        body, _ = build_body(a.title or make_title(text or raw), raw, a.source, a.url, a.source_app,
                             validate_date(a.date) if a.date else None, ["<upload-id>"] * len(a.file), a.test)
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return 0

    token = get_token()
    if a.check:
        title, problems = check(token)
        print(f"✓ Token works. Integration can read data source '{title}'.")
        for p in problems:
            print(f"✗ {p}")
        return 1 if problems else 0
    if a.replay or a.flush_outbox:
        paths = [a.replay] if a.replay else sorted(
            glob.glob(os.path.join(OUTBOX, "*.json")) + glob.glob(os.path.join(ICLOUD_OUTBOX, "*.json")))
        failed = 0
        for p in paths:
            try:
                page = replay(token, p)
                print(f"✓ {os.path.basename(p)} → {page.get('url')}")
            except (NotionError, ValueError, OSError) as e:
                failed += 1
                print(f"✗ {os.path.basename(p)}: {e}")
        if not paths:
            print("Outbox is empty.")
        return 1 if failed else 0

    text = sys.stdin.read() if a.text == "-" else (a.text or "")
    date = validate_date(a.date) if a.date else None
    page, notes = capture(token, text, a.source, note=a.note, title=a.title, url=a.url, app=a.source_app,
                          date=date, files=a.file, test=a.test)
    print(f"✓ Saved to Second Brain: {page.get('url')}")
    for n in notes:
        print(f"! {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

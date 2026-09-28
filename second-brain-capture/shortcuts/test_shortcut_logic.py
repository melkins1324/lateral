#!/usr/bin/env python3
"""
Simulates the text-processing the generated shortcuts perform (escape → chunk →
join → JSON body) and proves the resulting body is valid JSON that decodes back to
the exact original text, within Notion's limits. Also sanity-checks the generated
plists. Python's `re` uses the same replacement-string rules as ICU for the
patterns used here.

    python3 -m unittest test_shortcut_logic.py
"""
import glob
import json
import os
import plistlib
import re
import unittest

import build_shortcuts as B

HERE = os.path.dirname(os.path.abspath(__file__))


def sc_escape(s):
    for find, repl, _ in B.ESCAPES:
        s = re.sub(find, repl, s)
    return s


def sc_body(title, raw, capture_source="Siri Shortcut", prefix=""):
    e_raw = sc_escape(raw)
    chunks = re.findall(B.CHUNK_REGEX, e_raw)
    overflow_note = ""
    if len(chunks) > B.MAX_CHUNKS:
        chunks = chunks[:B.MAX_CHUNKS]
        overflow_note = B.PIECE_SEP + r"\n\n[Capture truncated ...]"
    pieces = B.PIECE_SEP.join(chunks)
    return ('{"parent":{"type":"data_source_id","data_source_id":"' + B.DATA_SOURCE_ID + '"},"properties":{'
            '"Name":{"title":[{"type":"text","text":{"content":"' + prefix + sc_escape(title) + '"}}]},'
            '"Raw Capture":{"rich_text":[{"type":"text","text":{"content":"' + pieces + overflow_note + '"}}]},'
            '"Capture Source":{"select":{"name":"' + capture_source + '"}},'
            '"AI Triage":{"select":{"name":"Needs AI"}}}}')


def sc_title(text):
    m = re.search(B.TITLE_REGEX, text)
    return m.group(0) if m else "Voice capture"


NASTY = [
    "Call the dentist Tuesday at 3 PM and also look into hiking in Mendocino.",
    "Brad is the Caltrain conductor who is always chill.",
    'She said "hi" \\ then left.\nNew line\r\nCRLF\ttab',
    "emoji 😀🎉 and accents café naïve — em dash … ellipsis",
    "control\x01chars\x1fhere",
    "\\\\double backslash\\\\ and \\\" escaped quote",
    "",
]


class ShortcutLogic(unittest.TestCase):
    def roundtrip(self, raw):
        body = json.loads(sc_body(sc_title(raw), raw))
        pieces = body["properties"]["Raw Capture"]["rich_text"]
        got = "".join(p["text"]["content"] for p in pieces)
        self.assertLessEqual(len(pieces), 100)
        for p in pieces:
            # Notion's limit is 2000 characters per piece; be strict and count UTF-16 units.
            self.assertLessEqual(len(p["text"]["content"].encode("utf-16-le")) // 2, 2000)
        return got

    def test_roundtrip_exact(self):
        for raw in NASTY:
            expected = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", raw)
            self.assertEqual(self.roundtrip(raw), expected, repr(raw))

    def test_long_text_chunks_without_breaking_escapes(self):
        raw = ('ab"c\\d\n' * 2000) + "😀" * 3000
        self.assertEqual(self.roundtrip(raw), raw)

    def test_overflow_is_valid_json_and_flagged(self):
        raw = "x" * 200_000
        got = self.roundtrip(raw)
        self.assertTrue(got.startswith("x" * 85_000))
        self.assertIn("[Capture truncated", got)

    def test_title_is_first_eight_words(self):
        self.assertEqual(sc_title(NASTY[0]), "Call the dentist Tuesday at 3 PM and")
        self.assertEqual(sc_title("Short one"), "Short one")
        self.assertEqual(sc_title(""), "Voice capture")

    def test_title_escaped(self):
        body = json.loads(sc_body('Quote "me" \\ ok', "x", prefix="[INTEGRATION TEST] "))
        self.assertEqual(body["properties"]["Name"]["title"][0]["text"]["content"],
                         '[INTEGRATION TEST] Quote "me" \\ ok')


class GeneratedPlists(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        B.main()

    def test_all_three_exist_and_tokens_are_consistent(self):
        files = sorted(glob.glob(os.path.join(HERE, "unsigned", "*.shortcut")))
        self.assertEqual([os.path.basename(f) for f in files],
                         ["Capture to Second Brain.shortcut", "Second Brain Setup.shortcut",
                          "Share to Second Brain.shortcut"])
        for f in files:
            with open(f, "rb") as fh:
                wf = plistlib.load(fh)
            uuids = set()
            for a in wf["WFWorkflowActions"]:
                p = a["WFWorkflowActionParameters"]
                if "UUID" in p:
                    uuids.add(p["UUID"])
            groups = {}
            for a in wf["WFWorkflowActions"]:
                p = a["WFWorkflowActionParameters"]
                self._check_tokens(p, uuids)
                if "GroupingIdentifier" in p:
                    groups.setdefault(p["GroupingIdentifier"], []).append(p["WFControlFlowMode"])
            for gid, modes in groups.items():
                self.assertEqual(modes[0], 0, f"{f}: block {gid} must start with mode 0")
                self.assertEqual(modes[-1], 2, f"{f}: block {gid} must end with mode 2")

    def _check_tokens(self, obj, uuids):
        if isinstance(obj, dict):
            if obj.get("WFSerializationType") == "WFTextTokenString":
                s = obj["Value"]["string"]
                self.assertEqual(s.count("￼"), len(obj["Value"]["attachmentsByRange"]))
            if obj.get("Type") == "ActionOutput":
                self.assertIn(obj["OutputUUID"], uuids, "reference to an unknown action output")
            for v in obj.values():
                self._check_tokens(v, uuids)
        elif isinstance(obj, list):
            for v in obj:
                self._check_tokens(v, uuids)

    def test_no_secrets_in_shortcuts(self):
        for f in glob.glob(os.path.join(HERE, "unsigned", "*.shortcut")):
            with open(f, "rb") as fh:
                blob = fh.read()
            self.assertIsNone(re.search(rb"(ntn|secret)_[A-Za-z0-9]{20,}", blob))


if __name__ == "__main__":
    unittest.main()

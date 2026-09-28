#!/usr/bin/env python3
"""
Generate the Second Brain Apple Shortcuts as unsigned .shortcut files, plus a
matching step-by-step build guide for each one (the fallback if an import fails).

    python3 build_shortcuts.py            # writes ./unsigned/*.shortcut and ./steps/*.md

Then, on a Mac, sign them (Apple refuses unsigned files):

    ./sign_shortcuts.sh

Design notes (see ../README.md for the full story):
  * The Notion token is NOT inside any shortcut. "Second Brain Setup" saves it to
    iCloud Drive/Shortcuts/SecondBrain/notion_token.txt, and the capture shortcuts
    read it from there. Sharing a shortcut file therefore never leaks the token.
  * Request bodies are built as JSON *text* with every user-supplied value escaped
    (backslash, quote, CR, LF, TAB, other control characters). This avoids relying
    on Shortcuts' nested-dictionary serialization, which is hard to reason about.
  * Raw Capture is split into <=900-character rich-text pieces with a regex that
    never splits an escape sequence, then joined with a separator that closes one
    piece and opens the next. Notion allows 2,000 characters per piece and 100
    pieces per property.
  * Every request body is saved to SecondBrain/Outbox/ BEFORE it is sent, and
    deleted only after Notion returns a page object. A failure anywhere leaves the
    capture on disk (and failures also copy it to the clipboard).
"""
import os
import plistlib
import uuid

DATA_SOURCE_ID = "923ba32e-04e8-4c61-bf44-43093e061c0a"  # Second Brain 2.0 / Everything
NOTION_VERSION = "2025-09-03"
API = "https://api.notion.com/v1"
TOKEN_PATH = "SecondBrain/notion_token.txt"
OUTBOX = "SecondBrain/Outbox/"
RETRYABLE = "|rate_limited|internal_server_error|service_unavailable|gateway_timeout|conflict_error|"
CHUNK_REGEX = r"(?:\\.|[^\\]){1,900}"
MAX_CHUNKS = 95
PIECE_SEP = '"}},{"type":"text","text":{"content":"'
TITLE_REGEX = r"^\S+(?:[ \t]+\S+){0,7}"

# JSON-escape steps, applied in order with ICU regex semantics (same as Python re).
ESCAPES = [
    (r"\\", r"\\\\", "every backslash → two backslashes"),
    ('"', r'\\"', 'every " → \\"'),
    (r"\r", r"\\r", "carriage returns → \\r"),
    (r"\n", r"\\n", "line breaks → \\n"),
    (r"\t", r"\\t", "tabs → \\t"),
    (r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", "other invisible control characters → space"),
]

INPUT_CLASSES = [
    "WFAppStoreAppContentItem", "WFArticleContentItem", "WFContactContentItem",
    "WFDateContentItem", "WFEmailAddressContentItem", "WFGenericFileContentItem",
    "WFImageContentItem", "WFiTunesProductContentItem", "WFLocationContentItem",
    "WFDCMapsLinkContentItem", "WFAVAssetContentItem", "WFPDFContentItem",
    "WFPhoneNumberContentItem", "WFRichTextContentItem", "WFSafariWebPageContentItem",
    "WFStringContentItem", "WFURLContentItem",
]


class Ref:
    """Something a token string can point at: an action output or a named variable."""

    def __init__(self, att, label):
        self.att = att
        self.label = label


def var(name):
    return Ref({"Type": "Variable", "VariableName": name}, f"[{name}]")


SHORTCUT_INPUT = Ref({"Type": "ExtensionInput"}, "[Shortcut Input]")
REPEAT_ITEM = Ref({"Type": "Variable", "VariableName": "Repeat Item"}, "[Repeat Item]")


def tok(*parts):
    s, ranges = "", {}
    for p in parts:
        if isinstance(p, str):
            s += p
        else:
            loc = len(s.encode("utf-16-le")) // 2
            ranges[f"{{{loc}, 1}}"] = p.att
            s += "￼"
    return {"Value": {"string": s, "attachmentsByRange": ranges},
            "WFSerializationType": "WFTextTokenString"}


def att(ref):
    return {"Value": ref.att, "WFSerializationType": "WFTextTokenAttachment"}


def show(*parts):
    out = "".join(p if isinstance(p, str) else p.label for p in parts)
    return out.replace("\n", "⏎").replace("\t", "⇥")


def dictfield(items):
    return {"Value": {"WFDictionaryFieldValueItems": items},
            "WFSerializationType": "WFDictionaryFieldValue"}


class Shortcut:
    def __init__(self, name):
        self.name = name
        self.actions = []
        self.doc = []
        self.depth = 0

    # -- core -------------------------------------------------------------
    def act(self, ident, params, out=None, doc=""):
        p = dict(params)
        ref = None
        n = len(self.actions) + 1
        if out:
            u = str(uuid.uuid4()).upper()
            p["UUID"] = u
            ref = Ref({"Type": "ActionOutput", "OutputUUID": u, "OutputName": out},
                      f"[{out} from step {n}]")
        self.actions.append({"WFWorkflowActionIdentifier": ident,
                             "WFWorkflowActionParameters": p})
        self.doc.append(f"{'    ' * self.depth}{n}. {doc}")
        return ref

    def comment(self, text):
        self.act("is.workflow.actions.comment", {"WFCommentActionText": text},
                 doc=f"**Comment**: {text}")

    def text(self, *parts):
        return self.act("is.workflow.actions.gettext", {"WFTextActionText": tok(*parts)},
                        "Text", f'**Text**: `{show(*parts)}`' if parts else "**Text** (leave empty)")

    def setvar(self, name, ref):
        self.act("is.workflow.actions.setvariable", {"WFVariableName": name, "WFInput": att(ref)},
                 doc=f"**Set Variable** `{name}` to {ref.label}")
        return var(name)

    def addvar(self, name, ref):
        self.act("is.workflow.actions.appendvariable", {"WFVariableName": name, "WFInput": att(ref)},
                 doc=f"**Add to Variable** `{name}`: {ref.label}")
        return var(name)

    def settext(self, name, *parts):
        return self.setvar(name, self.text(*parts))

    def replace(self, ref, find, repl, regex=True, why=""):
        return self.act("is.workflow.actions.text.replace", {
            "WFInput": tok(ref), "WFReplaceTextFind": find, "WFReplaceTextReplace": repl,
            "WFReplaceTextRegularExpression": regex, "WFReplaceTextCaseSensitive": True,
        }, "Updated Text",
            f"**Replace Text** in {ref.label}: find `{find}` replace with `{repl}` "
            f"(Regular Expression **{'ON' if regex else 'OFF'}**, Case Sensitive ON){' — ' + why if why else ''}")

    def match(self, ref, pattern):
        return self.act("is.workflow.actions.text.match", {
            "WFMatchTextPattern": pattern, "text": tok(ref), "WFMatchTextCaseSensitive": True,
        }, "Matches", f"**Match Text**: pattern `{pattern}` in {ref.label} (Case Sensitive ON)")

    def combine(self, ref, sep):
        return self.act("is.workflow.actions.text.combine", {
            "text": att(ref), "WFTextSeparator": "Custom", "WFTextCustomSeparator": sep,
        }, "Combined Text", f"**Combine Text** {ref.label} with Custom separator `{show(sep)}`")

    def count(self, ref, kind="Items"):
        return self.act("is.workflow.actions.count", {"Input": att(ref), "WFCountType": kind},
                        "Count", f"**Count** {kind} in {ref.label}")

    def first(self, ref):
        return self.act("is.workflow.actions.getitemfromlist",
                        {"WFInput": att(ref), "WFItemSpecifier": "First Item"},
                        "Item from List", f"**Get Item from List**: First Item of {ref.label}")

    def item_range(self, ref, a, b):
        return self.act("is.workflow.actions.getitemfromlist", {
            "WFInput": att(ref), "WFItemSpecifier": "Items in Range",
            "WFItemRangeStart": a, "WFItemRangeEnd": b,
        }, "Items in Range", f"**Get Item from List**: Items in Range {a} to {b} of {ref.label}")

    def getkey(self, ref, key):
        return self.act("is.workflow.actions.getvalueforkey", {
            "WFInput": att(ref), "WFGetDictionaryValueType": "Value", "WFDictionaryKey": key,
        }, "Dictionary Value", f"**Get Dictionary Value**: Value for key `{key}` in {ref.label}")

    def get_dict(self, ref):
        return self.act("is.workflow.actions.detect.dictionary", {"WFInput": att(ref)},
                        "Dictionary", f"**Get Dictionary from Input**: {ref.label}")

    def get_text(self, ref):
        return self.act("is.workflow.actions.detect.text", {"WFInput": att(ref)},
                        "Text", f"**Get Text from Input**: {ref.label}")

    def get_urls(self, ref):
        return self.act("is.workflow.actions.detect.link", {"WFInput": att(ref)},
                        "URLs", f"**Get URLs from Input**: {ref.label}")

    def get_type(self, ref):
        return self.act("is.workflow.actions.getitemtype", {"WFInput": att(ref)},
                        "Type", f"**Get Type** of {ref.label}")

    def get_name(self, ref):
        return self.act("is.workflow.actions.getitemname", {"WFInput": att(ref)},
                        "Name", f"**Get Name** of {ref.label}")

    def safari(self, ref, prop):
        return self.act("is.workflow.actions.properties.safariwebpage", {
            "WFInput": att(ref), "WFContentItemPropertyName": prop,
        }, prop, f"**Get Details of Safari Web Page**: `{prop}` of {ref.label}")

    def notify(self, title, *body):
        self.act("is.workflow.actions.notification", {
            "WFNotificationActionTitle": tok(title), "WFNotificationActionBody": tok(*body),
            "WFNotificationActionSound": True,
        }, doc=f"**Show Notification**: title `{title}`, body `{show(*body)}`")

    def alert(self, title, *msg):
        self.act("is.workflow.actions.alert", {
            "WFAlertActionTitle": tok(title), "WFAlertActionMessage": tok(*msg),
            "WFAlertActionCancelButtonShown": False,
        }, doc=f"**Show Alert**: title `{title}`, message `{show(*msg)}` (Show Cancel Button OFF)")

    def stop(self):
        self.act("is.workflow.actions.exit", {}, doc="**Stop This Shortcut**")

    def clipboard(self, ref):
        self.act("is.workflow.actions.setclipboard", {"WFInput": att(ref)},
                 doc=f"**Copy to Clipboard**: {ref.label}")

    def wait(self, secs):
        self.act("is.workflow.actions.delay", {"WFDelayTime": secs}, doc=f"**Wait** {secs} seconds")

    def rename(self, ref, *name):
        return self.act("is.workflow.actions.setitemname", {
            "WFInput": att(ref), "WFName": tok(*name), "WFDontIncludeFileExtension": False,
        }, "Renamed Item", f"**Set Name** of {ref.label} to `{show(*name)}`")

    def save(self, ref, folder, overwrite=False):
        return self.act("is.workflow.actions.documentpicker.save", {
            "WFInput": att(ref), "WFAskWhereToSave": False,
            "WFFileDestinationPath": tok(folder), "WFSaveFileOverwrite": overwrite,
        }, "Saved File",
            f"**Save File** {ref.label} — Ask Where to Save OFF, Subpath `{folder}`, Overwrite {'ON' if overwrite else 'OFF'}")

    def get_file(self, path):
        return self.act("is.workflow.actions.documentpicker.open", {
            "WFGetFilePath": tok(path), "WFFileErrorIfNotFound": False, "WFShowFilePicker": False,
        }, "File", f"**Get File** from Shortcuts folder, path `{path}` (Show Document Picker OFF, Error If Not Found OFF)")

    def delete(self, ref):
        self.act("is.workflow.actions.file.delete", {
            "WFInput": att(ref), "WFDeleteFileConfirmDeletion": False,
        }, doc=f"**Delete Files** {ref.label} (Confirm Before Deleting OFF)")

    def ask(self, prompt):
        return self.act("is.workflow.actions.ask", {
            "WFAskActionPrompt": tok(prompt), "WFInputType": "Text", "WFAllowsMultilineText": True,
        }, "Provided Input", f"**Ask for Input** (Text, multiline): prompt `{prompt}`")

    def dictate(self):
        return self.act("is.workflow.actions.dictatetext", {
            "WFDictateTextStopListening": "After Pause",
        }, "Dictated Text", "**Dictate Text** (Stop Listening: After Pause)")

    def timestamp(self):
        d = self.act("is.workflow.actions.date", {"WFDateActionMode": "Current Date"}, "Date",
                     "**Date** (Current Date)")
        return self.act("is.workflow.actions.format.date", {
            "WFDate": tok(d), "WFDateFormatStyle": "Custom", "WFDateFormat": "yyyyMMdd-HHmmss",
        }, "Formatted Date", f"**Format Date** {d.label} — Custom format `yyyyMMdd-HHmmss`")

    def random(self):
        return self.act("is.workflow.actions.number.random", {
            "WFRandomNumberMinimum": 1000, "WFRandomNumberMaximum": 9999,
        }, "Random Number", "**Random Number** between 1000 and 9999")

    def http(self, url_parts, method, content_json=True, file_body=None, form_file=None):
        headers = [
            {"WFItemType": 0, "WFKey": tok("Authorization"), "WFValue": tok("Bearer ", var("Token"))},
            {"WFItemType": 0, "WFKey": tok("Notion-Version"), "WFValue": tok(NOTION_VERSION)},
        ]
        hdoc = f"`Authorization` = `Bearer [Token]`, `Notion-Version` = `{NOTION_VERSION}`"
        if content_json:
            headers.append({"WFItemType": 0, "WFKey": tok("Content-Type"), "WFValue": tok("application/json")})
            hdoc += ", `Content-Type` = `application/json`"
        p = {"WFURL": tok(*url_parts), "WFHTTPMethod": method, "ShowHeaders": True,
             "WFHTTPHeaders": dictfield(headers)}
        bdoc = ""
        if file_body is not None:
            p["WFHTTPBodyType"] = "File"
            p["WFRequestVariable"] = att(file_body)
            bdoc = f"; Request Body **File** = {file_body.label}"
        if form_file is not None:
            p["WFHTTPBodyType"] = "Form"
            p["WFFormValues"] = dictfield([{"WFItemType": 5, "WFKey": tok("file"), "WFValue": att(form_file)}])
            bdoc = f"; Request Body **Form** with one **File** field named `file` = {form_file.label}"
        return self.act("is.workflow.actions.downloadurl", p, "Contents of URL",
                        f"**Get Contents of URL** `{show(*url_parts)}` — Method **{method}**; Headers: {hdoc}{bdoc}")

    # -- control flow -----------------------------------------------------
    def if_(self, ref, cond, value=None, number=None):
        gid = str(uuid.uuid4()).upper()
        names = {4: "is", 5: "is not", 99: "contains", 8: "begins with", 2: "is greater than",
                 100: "has any value", 101: "does not have any value"}
        p = {"GroupingIdentifier": gid, "WFControlFlowMode": 0, "WFCondition": cond,
             "WFInput": {"Type": "Variable", "Variable": att(ref)}}
        vdoc = ""
        if value is not None:
            parts = value if isinstance(value, tuple) else (value,)
            p["WFConditionalActionString"] = tok(*parts)
            vdoc = f" `{show(*parts)}`"
        if number is not None:
            p["WFNumberValue"] = number
            vdoc = f" `{number}`"
        self.act("is.workflow.actions.conditional", p, doc=f"**If** {ref.label} {names[cond]}{vdoc}")
        self.depth += 1
        return gid

    def else_(self, gid):
        self.depth -= 1
        self.act("is.workflow.actions.conditional", {"GroupingIdentifier": gid, "WFControlFlowMode": 1},
                 doc="**Otherwise**")
        self.depth += 1

    def endif(self, gid):
        self.depth -= 1
        self.act("is.workflow.actions.conditional", {"GroupingIdentifier": gid, "WFControlFlowMode": 2},
                 "If Result", "**End If**")

    def repeat_each(self, ref):
        gid = str(uuid.uuid4()).upper()
        self.act("is.workflow.actions.repeat.each",
                 {"GroupingIdentifier": gid, "WFControlFlowMode": 0, "WFInput": att(ref)},
                 doc=f"**Repeat with Each** item in {ref.label}")
        self.depth += 1
        return gid

    def repeat_n(self, n):
        gid = str(uuid.uuid4()).upper()
        self.act("is.workflow.actions.repeat.count",
                 {"GroupingIdentifier": gid, "WFControlFlowMode": 0, "WFRepeatCount": n},
                 doc=f"**Repeat** {n} times")
        self.depth += 1
        return gid

    def end_repeat(self, gid, each=True):
        self.depth -= 1
        ident = "is.workflow.actions.repeat.each" if each else "is.workflow.actions.repeat.count"
        return self.act(ident, {"GroupingIdentifier": gid, "WFControlFlowMode": 2},
                        "Repeat Results", "**End Repeat**")

    # -- output -----------------------------------------------------------
    def plist(self, share_sheet=False):
        wf = {
            "WFWorkflowActions": self.actions,
            "WFWorkflowClientVersion": "2302.0.4",
            "WFWorkflowMinimumClientVersion": 900,
            "WFWorkflowMinimumClientVersionString": "900",
            "WFWorkflowIcon": {"WFWorkflowIconStartColor": 463140863, "WFWorkflowIconGlyphNumber": 59818},
            "WFWorkflowImportQuestions": [],
            "WFWorkflowInputContentItemClasses": INPUT_CLASSES if share_sheet else [],
            "WFWorkflowOutputContentItemClasses": [],
            "WFWorkflowTypes": ["ActionExtension", "QuickActions"] if share_sheet else [],
            "WFQuickActionSurfaces": ["Services"] if share_sheet else [],
            "WFWorkflowHasShortcutInputVariables": share_sheet,
            "WFWorkflowHasOutputFallback": False,
        }
        return plistlib.dumps(wf, fmt=plistlib.FMT_BINARY)


# ---------------------------------------------------------------------------
# Reusable building blocks
# ---------------------------------------------------------------------------

def load_token(sc):
    sc.comment("Load the Notion token saved by the 'Second Brain Setup' shortcut. "
               "The token never lives inside this shortcut.")
    f = sc.get_file(TOKEN_PATH)
    g = sc.if_(f, 101)
    sc.alert("Second Brain isn't set up",
             "Run the 'Second Brain Setup' shortcut once to save your Notion token. Nothing was captured.")
    sc.stop()
    sc.endif(g)
    t = sc.get_text(f)
    t = sc.replace(t, r"\s", "", why="strip spaces/line breaks around the token")
    sc.setvar("Token", t)


def escape(sc, ref, name):
    cur = ref
    for find, repl, why in ESCAPES:
        cur = sc.replace(cur, find, repl, why=why)
    return sc.setvar(name, cur)


def title_from(sc, ref, fallback):
    """First 8 words of the text, or a fallback when nothing matches."""
    sc.settext("TitleText", fallback)
    m = sc.match(ref, TITLE_REGEX)
    g = sc.if_(m, 100)
    sc.setvar("TitleText", sc.first(m))
    sc.endif(g)
    return var("TitleText")


def full_title_or(sc, page_title, text, fallback):
    """Keep an original page title whole; otherwise use the first words of the text."""
    g = sc.if_(page_title, 100)
    sc.setvar("TitleText", page_title)
    sc.else_(g)
    title_from(sc, text, fallback)
    sc.endif(g)
    return var("TitleText")


def send(sc, title, raw, capture_source, url=None, app=None, upload_id=None):
    """Build the create-page request, save it to the Outbox, POST with retries, report."""
    sc.comment(f"--- Send one record to Everything (Capture Source = {capture_source}) ---")
    e_title = escape(sc, title, "eTitle")
    e_raw = escape(sc, raw, "eRaw")

    # Raw Capture pieces
    chunks = sc.match(e_raw, CHUNK_REGEX)
    sc.setvar("Chunks", chunks)
    sc.settext("Overflow", "no")
    sc.settext("OverflowNote")
    n = sc.count(chunks)
    g = sc.if_(n, 2, number=MAX_CHUNKS)
    sc.setvar("Chunks", sc.item_range(chunks, 1, MAX_CHUNKS))
    sc.settext("Overflow", "yes")
    sc.settext("OverflowNote", PIECE_SEP,
               r"\n\n[Capture truncated at about 85,000 characters to fit Notion. The full text is kept in "
               r"iCloud Drive/Shortcuts/SecondBrain/Outbox.]")
    sc.endif(g)
    joined = sc.combine(var("Chunks"), PIECE_SEP)
    sc.setvar("RawPieces", joined)

    # Optional properties
    sc.settext("Opt")
    if url is not None:
        e_url = escape(sc, url, "eURL")
        g = sc.if_(e_url, 100)
        c = sc.count(e_url, "Characters")
        g2 = sc.if_(c, 2, number=2000)
        sc.comment("Too long for Notion's URL property; it is still inside Raw Capture.")
        sc.else_(g2)
        sc.settext("Opt", var("Opt"), ',"Source URL":{"url":"', e_url, '"}')
        sc.endif(g2)
        sc.endif(g)
    if app is not None:
        e_app = escape(sc, app, "eApp")
        g = sc.if_(e_app, 100)
        sc.settext("Opt", var("Opt"), ',"Source app":{"rich_text":[{"type":"text","text":{"content":"', e_app, '"}}]}')
        sc.endif(g)
    if upload_id is not None:
        g = sc.if_(upload_id, 100)
        sc.settext("Opt", var("Opt"), ',"Attachments":{"files":[{"type":"file_upload","file_upload":{"id":"',
                   upload_id, '"}}]}')
        sc.endif(g)

    body = sc.text(
        '{"parent":{"type":"data_source_id","data_source_id":"', DATA_SOURCE_ID, '"},"properties":{',
        '"Name":{"title":[{"type":"text","text":{"content":"', var("TestPrefix"), e_title, '"}}]},',
        '"Raw Capture":{"rich_text":[{"type":"text","text":{"content":"', var("RawPieces"), var("OverflowNote"), '"}}]},',
        f'"Capture Source":{{"select":{{"name":"{capture_source}"}}}},',
        '"AI Triage":{"select":{"name":"Needs AI"}}', var("Opt"), "}}")
    sc.setvar("Body", body)

    # Outbox copy before sending
    ts = sc.timestamp()
    rnd = sc.random()
    named = sc.rename(var("Body"), "capture-", ts, "-", rnd, ".json")
    sc.setvar("OutboxFile", sc.save(named, OUTBOX))

    # POST with retries on temporary errors
    sc.settext("SendStatus", "pending")
    rg = sc.repeat_n(3)
    g = sc.if_(var("SendStatus"), 4, "pending")
    resp = sc.http([f"{API}/pages"], "POST", file_body=var("Body"))
    sc.setvar("Response", resp)
    obj = sc.getkey(resp, "object")
    g2 = sc.if_(obj, 4, "page")
    sc.settext("SendStatus", "done")
    sc.else_(g2)
    code = sc.getkey(resp, "code")
    sc.setvar("ErrCode", code)
    retry = sc.text(RETRYABLE)
    g3 = sc.if_(retry, 99, ("|", var("ErrCode"), "|"))
    sc.wait(3)
    sc.else_(g3)
    sc.settext("SendStatus", "fatal")
    sc.endif(g3)
    sc.endif(g2)
    sc.endif(g)
    sc.end_repeat(rg, each=False)

    # Report
    g = sc.if_(var("SendStatus"), 4, "done")
    g2 = sc.if_(var("Overflow"), 4, "no")
    sc.delete(var("OutboxFile"))
    sc.endif(g2)
    sc.notify("✅ Saved to Second Brain", var("TestPrefix"), title)
    sc.else_(g)
    msg = sc.getkey(var("Response"), "message")
    sc.setvar("ErrMessage", msg)
    sc.clipboard(raw)
    sc.alert("⚠️ Not saved to Notion",
             "Notion said: ", var("ErrMessage"), " (", var("ErrCode"), ")\n\n"
             "Nothing is lost: the capture was copied to your clipboard and saved in "
             "iCloud Drive › Shortcuts › SecondBrain › Outbox.")
    sc.endif(g)


def common_header(sc, what):
    sc.comment(f"{sc.name}: {what} Sends to Second Brain 2.0 › Everything only. "
               "Classification is done later by the Notion triage agent.")
    sc.comment("TEST MODE: type [INTEGRATION TEST] followed by a space into the next Text action "
               "to tag captures as tests. Leave it empty for normal use.")
    sc.settext("TestPrefix")
    load_token(sc)


# ---------------------------------------------------------------------------
# The three shortcuts
# ---------------------------------------------------------------------------

def build_setup():
    sc = Shortcut("Second Brain Setup")
    sc.comment("Run once (and again whenever you rotate the token). Saves the Notion token to "
               "iCloud Drive/Shortcuts/SecondBrain/notion_token.txt and checks Notion access.")
    t = sc.ask("Paste your Notion integration secret (starts with ntn_). It is saved only in your iCloud Drive.")
    t = sc.replace(t, r"\s", "", why="remove stray spaces/line breaks")
    sc.setvar("Token", t)
    f = sc.rename(var("Token"), "notion_token.txt")
    sc.save(f, "SecondBrain/", overwrite=True)
    readme = sc.text("Captures that could not be sent to Notion are kept here. "
                     "Open one to recover its text, or replay it from a Mac with: "
                     "python3 sb_capture.py --replay <file>")
    sc.save(sc.rename(readme, "README.txt"), OUTBOX, overwrite=True)
    resp = sc.http([f"{API}/data_sources/{DATA_SOURCE_ID}"], "GET", content_json=False)
    obj = sc.getkey(resp, "object")
    g = sc.if_(obj, 4, "data_source")
    sc.alert("✅ Second Brain connected",
             "The token works and the integration can see the Everything database. "
             "'Capture to Second Brain' and 'Share to Second Brain' are ready.")
    sc.else_(g)
    msg = sc.getkey(resp, "message")
    sc.alert("❌ Notion refused the token",
             "Notion said: ", msg, "\n\nCheck: (1) you copied the whole secret, "
             "(2) in Notion, Everything › ••• › Connections includes your integration.")
    sc.endif(g)
    return sc


def build_capture():
    sc = Shortcut("Capture to Second Brain")
    common_header(sc, "Dictate a thought; it is saved word-for-word as Raw Capture.")
    d = sc.dictate()
    sc.setvar("Dictation", d)
    g = sc.if_(var("Dictation"), 101)
    sc.alert("Nothing heard", "No speech was captured, so nothing was saved.")
    sc.stop()
    sc.endif(g)
    title = title_from(sc, var("Dictation"), "Voice capture")
    sc.comment("Date is intentionally left empty. The triage agent (or you) sets it once it is certain.")
    send(sc, title, var("Dictation"), "Siri Shortcut")
    return sc


def build_share():
    sc = Shortcut("Share to Second Brain")
    common_header(sc, "Share Sheet / Mac Services capture. Files get one record each; "
                      "text, links and web pages shared together become one record.")
    g = sc.if_(SHORTCUT_INPUT, 101)
    sc.alert("Nothing shared", "This shortcut received no input, so nothing was saved.")
    sc.stop()
    sc.endif(g)

    for v in ("NoteBlock", "PageTitle", "SrcURL", "App", "AttachID", "AttachNote"):
        sc.settext(v)
    note = sc.ask("Add a note? (optional — leave blank and tap Done)")
    sc.setvar("Note", note)
    g = sc.if_(var("Note"), 100)
    sc.settext("NoteBlock", "Note: ", var("Note"), "\n\n")
    sc.endif(g)

    # --- Browser bookmarklet (Phase 3) sends "SBCLIP1⏎{json}" as text ---
    intext = sc.get_text(SHORTCUT_INPUT)
    sc.setvar("InText", intext)
    gclip = sc.if_(var("InText"), 8, "SBCLIP1\n")
    sc.comment("Came from the browser bookmarklet: title, URL, selection and browser are in the JSON.")
    j = sc.replace(var("InText"), r"^SBCLIP1\n", "", why="drop the marker line")
    clip = sc.get_dict(j)
    sc.setvar("Clip", clip)
    sc.setvar("PageTitle", sc.getkey(var("Clip"), "title"))
    sc.setvar("SrcURL", sc.getkey(var("Clip"), "url"))
    sc.setvar("App", sc.getkey(var("Clip"), "app"))
    sc.setvar("Selection", sc.getkey(var("Clip"), "selection"))
    raw = sc.text(var("NoteBlock"), "Title: ", var("PageTitle"), "\nURL: ", var("SrcURL"), "\n\n", var("Selection"))
    sc.setvar("RawText", raw)
    full_title_or(sc, var("PageTitle"), var("Selection"), "Web clip")
    send(sc, var("TitleText"), var("RawText"), "Web Clip", url=var("SrcURL"), app=var("App"))
    sc.else_(gclip)

    # --- Normal Share Sheet path ---
    sc.comment("Files (images, screenshots, PDFs, documents, audio, video files) become one record each.")
    rg = sc.repeat_each(SHORTCUT_INPUT)
    sc.setvar("Item", REPEAT_ITEM)
    t = sc.get_type(var("Item"))
    sc.setvar("ItemType", t)
    kinds = sc.text("|Image|PDF|File|Media|Photo media|")
    gf = sc.if_(kinds, 99, ("|", var("ItemType"), "|"))
    sc.setvar("FName", sc.get_name(var("Item")))
    sc.settext("AttachID")
    sc.settext("AttachNote")
    up = sc.text('{"mode":"single_part"}')
    r1 = sc.http([f"{API}/file_uploads"], "POST", file_body=up)
    sc.setvar("UploadID", sc.getkey(r1, "id"))
    r2 = sc.http([f"{API}/file_uploads/", var("UploadID"), "/send"], "POST", content_json=False, form_file=var("Item"))
    sc.setvar("UploadResp", r2)
    st = sc.getkey(var("UploadResp"), "status")
    gu = sc.if_(st, 4, "uploaded")
    sc.setvar("AttachID", var("UploadID"))
    sc.else_(gu)
    um = sc.getkey(var("UploadResp"), "message")
    sc.setvar("UploadMsg", um)
    sc.save(var("Item"), OUTBOX + "files/")
    sc.settext("AttachNote", "\n\n[Attachment NOT uploaded to Notion. Notion said: ", var("UploadMsg"),
               ". The original file was saved to iCloud Drive/Shortcuts/SecondBrain/Outbox/files.]")
    sc.endif(gu)
    raw = sc.text(var("NoteBlock"), "Shared file: ", var("FName"), "\nShared type: ", var("ItemType"), var("AttachNote"))
    sc.setvar("RawText", raw)
    send(sc, var("FName"), var("RawText"), "Shared from App", upload_id=var("AttachID"))
    sc.else_(gf)
    sc.addvar("TextItems", var("Item"))
    sc.endif(gf)
    sc.end_repeat(rg)

    sc.comment("Text, links, web pages, maps, products, recipes, etc. shared together become ONE record.")
    gt = sc.if_(var("TextItems"), 100)
    rg = sc.repeat_each(var("TextItems"))
    sc.setvar("Item", REPEAT_ITEM)
    t = sc.get_type(var("Item"))
    gs = sc.if_(t, 4, "Safari web page")
    sc.setvar("PageTitle", sc.safari(var("Item"), "Name"))
    sc.setvar("SrcURL", sc.safari(var("Item"), "Page URL"))
    sel = sc.safari(var("Item"), "Page Selection")
    sc.settext("App", "Safari")
    part = sc.text("Title: ", var("PageTitle"), "\nURL: ", var("SrcURL"), "\n\n", sel)
    sc.addvar("Parts", part)
    sc.else_(gs)
    txt = sc.get_text(var("Item"))
    sc.addvar("Parts", txt)
    gu = sc.if_(var("SrcURL"), 101)
    urls = sc.get_urls(var("Item"))
    gu2 = sc.if_(urls, 100)
    sc.setvar("SrcURL", sc.first(urls))
    sc.endif(gu2)
    sc.endif(gu)
    sc.endif(gs)
    sc.end_repeat(rg)
    shared = sc.combine(var("Parts"), "\n\n")
    raw = sc.text(var("NoteBlock"), shared)
    sc.setvar("RawText", raw)
    full_title_or(sc, var("PageTitle"), shared, "Shared item")
    send(sc, var("TitleText"), var("RawText"), "Shared from App", url=var("SrcURL"), app=var("App"))
    sc.endif(gt)
    sc.endif(gclip)
    return sc


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "unsigned"), exist_ok=True)
    os.makedirs(os.path.join(here, "steps"), exist_ok=True)
    for sc, share in ((build_setup(), False), (build_capture(), False), (build_share(), True)):
        with open(os.path.join(here, "unsigned", f"{sc.name}.shortcut"), "wb") as fh:
            fh.write(sc.plist(share_sheet=share))
        with open(os.path.join(here, "steps", f"{sc.name}.md"), "w") as fh:
            fh.write(f"# {sc.name} — build by hand\n\n")
            fh.write("Generated from `build_shortcuts.py`; it matches the .shortcut file step for step.\n"
                     "`[Name]` means insert that variable (tap the field → Select Variable, or pick it "
                     "from the variable bar). `[X from step N]` is the output of step N.\n"
                     "⏎ means a line break (press Return), ⇥ a tab.\n\n")
            if share:
                fh.write("**Shortcut settings (ⓘ):** Show in Share Sheet ON; on Mac also Use as Quick "
                         "Action → Services Menu. Receive: Any input. If there's no input: Stop and Respond.\n\n")
            fh.write("\n".join(sc.doc) + "\n")
        print(f"{sc.name}: {len(sc.actions)} actions")


if __name__ == "__main__":
    main()

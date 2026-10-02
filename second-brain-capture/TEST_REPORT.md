# Test report — 2026-09-28

## What was tested, and how

| Layer | Method | Result |
|---|---|---|
| Shortcut text logic (escaping, splitting, JSON body, titles) | `shortcuts/test_shortcut_logic.py`: simulates the exact escape and split regexes the shortcuts use, then parses the resulting JSON | **7/7 pass.** Quotes, backslashes, line breaks, tabs, emoji and 200,000-character input all round-trip exactly and stay within Notion's limits |
| Generated shortcut files | Same test file: valid binary plists; every variable reference points at a real action; every If/Repeat block is closed; no token inside | **Pass** |
| Terminal tool `sb_capture.py` | `cli/test_sb_capture.py` against a local mock Notion API | **14/14 pass** (details below) |
| Real Notion database | 7 `[INTEGRATION TEST]` records created in Everything through the Notion connector, with exactly the property values the adapters send | **All 7 created and verified** |
| Triage agent | Re-read the records after the published agent processed them | **Raw Capture preserved on all 7. The agent has problems; see Findings** |
| **Shortcuts running on a device** | Can't be done from a cloud Linux machine | **NOT yet verified. Your checklist is below** |

**Important limit on the live test.** This cloud sandbox isn't allowed to reach
`api.notion.com` directly (its proxy returns 403). So the live records went through the
Notion connector rather than through the shortcuts or the CLI over REST. That proves the
database accepts every property, option and attachment exactly as mapped. It doesn't prove
the shortcuts run on your iPhone. That's the on-device checklist at the bottom.

## Live records (Everything database)

| # | Case | Name | Capture Source | Source URL | Source app | Attachments | AI Triage when created | Raw Capture preserved after triage |
|---|---|---|---|---|---|---|---|---|
| 1 | Siri: dentist + Mendocino | [INTEGRATION TEST] Call the dentist Tuesday at 3 PM and | Siri Shortcut ✅ | — | — | — | Needs AI ✅ | ✅ exact |
| 2 | Siri: Brad the conductor | [INTEGRATION TEST] Brad is the Caltrain conductor who is always | Siri Shortcut ✅ | — | — | — | Needs AI ✅ | ✅ exact |
| 3 | Shared webpage (Safari) | [INTEGRATION TEST] Example Domain | Shared from App ✅ → **changed to Web Clip by triage ⚠️** | ✅ | Safari ✅ | — | Needs AI ✅ | ✅ exact (fetched page confirms trailing lines intact) |
| 4 | Shared YouTube link | [INTEGRATION TEST] https://www.youtube.com/watch?v=aqz-KE-bpKQ | Shared from App ✅ | ✅ | empty (iOS doesn't report the app) | — | Needs AI ✅ | ✅ exact |
| 5 | Selected text + URL (bookmarklet) | [INTEGRATION TEST] Mendocino, California - Wikipedia | Web Clip ✅ | ✅ | Chrome ✅ | — | Needs AI ✅ | ✅ exact |
| 6 | Screenshot / image | [INTEGRATION TEST] IMG_TEST_screenshot.png | Shared from App ✅ | — | — | ✅ PNG attached | Needs AI ✅ | ✅ exact |
| 7 | PDF document | [INTEGRATION TEST] TEST_document.pdf | Shared from App ✅ | — | — | ✅ PDF attached | Needs AI ✅ | ✅ exact |
| 8 | Failed request | (none created, correctly) | — | — | — | — | — | ✅ input preserved in the outbox (see below) |

Other checks:
- **`Date` left empty** on every record, including the ambiguous "Tuesday at 3 PM". ✅
- **No duplicate database created.** Only one Everything data source exists under Second Brain 2.0. ✅
- **No existing records modified.** The row count went from 28 to 35, which is exactly the 7 test rows. The only edits were to my own two test pages (attaching files). ✅
- **Nothing silently lost.** ✅

Test-procedure caveat for #6 and #7: the Notion connector can't put an upload inside a
create call, so those two records were created and then had the file attached. The
shortcuts and the CLI attach inside the single create request. The live test proves the
`Attachments` property accepts uploaded PNG and PDF files.

## Case 8: failed requests

- **Real network failure (unplanned but genuine).** `sb_capture.py` ran against the real
  Notion endpoint from this sandbox and the proxy blocked it. It tried 4 times with backoff,
  then printed `✗ Not saved to Notion — … (network_error)`. It saved the full request body to
  `~/.second-brain/outbox/…json` and printed the `--replay` command. The log contained no
  token and no capture text. **Pass.**
- **Invalid token (mock).** Notion's `401 unauthorized` gave a clear error, nothing was
  created, the input was saved to the outbox, the token didn't appear in the error message,
  and `--replay` succeeded once the token was fixed. **Pass.**
- **Rate limit (429) then success; 503 then success.** Exactly one record was created. **Pass.**
- **Timeout after Notion had already created the page.** The duplicate check found the
  existing page and **no duplicate was created**. **Pass.**
- **Validation error (400).** Not retried, reported once. **Pass.**

## Findings: the triage agent (I did not change it; it needs your decision)

The published agent (it appears as **🧠 Inbox Triage**; nothing is literally named "Second
Brain Triage") processed all 7 records within minutes. **It doesn't overwrite Raw Capture.**
But it has real problems:

1. **It dumps its whole answer into text fields.** `Cleaned Thought`, `Details`,
   `Next Action`, and on one record even `Creator / Author`, contain a multi-line blob like
   `Cleaned Thought: … Type: … Tags: … AI Triage: Triaged`. It isn't writing clean values
   into each property. Some `Next Action` values contain a raw `<properties>` block.
2. **It overwrote capture metadata.** On #3 it changed `Capture Source` from
   `Shared from App` to `Web Clip`. Capture Source records how something arrived, so triage
   shouldn't change it.
3. **It didn't flag the ambiguous date.** "Call the dentist Tuesday at 3 PM" was marked
   `Triaged` with no Date, not `Human Review`. It also didn't split the capture's two ideas
   (dentist task, Mendocino idea).
4. **Its outputs disagree with each other.** For example, Type = Task while its own text says
   "Type: Project", and AI Triage = Human Review while its text says "Triaged".

None of this affects capture. It does mean the organised views won't look right until the
agent's instructions are fixed. That's a change to the triage agent, which you told me not to
touch. Say the word if you want me to draft revised instructions for you to review.

## Your on-device checklist (about 10 minutes)

Set the first Text action in each capture shortcut to `[INTEGRATION TEST] ` (with the trailing space) while testing, then clear it afterwards.

- [ ] Setup shortcut shows **✅ Second Brain connected**
- [ ] Siri: "Hey Siri, capture to my Second Brain" → say test 1 → ✅ notification → record matches row 1
- [ ] Siri: test 2
- [ ] Safari → Share → Share to Second Brain on any article → title, URL and Source app = Safari
- [ ] YouTube app → Share → Share to Second Brain
- [ ] Chrome: select text → click the bookmarklet → Capture Source = Web Clip, Source app = Chrome
- [ ] Photos: share a screenshot → Attachments has the image
- [ ] Files: share a PDF → Attachments has the PDF
- [ ] Failure: turn on Airplane Mode, run Capture → the shortcut stops with an error → the capture is in `Files › iCloud Drive › Shortcuts › SecondBrain › Outbox`. Turn Airplane Mode off and run `python3 sb_capture.py --flush-outbox` on the Mac.
- [ ] Failure: temporarily add an `x` to the token file → ⚠️ "Not saved to Notion … unauthorized" and the capture is on the clipboard. Then run Setup again.

## Cleanup

After you approve these results, I'll delete **only** the 7 records whose names start with
`[INTEGRATION TEST]`. The older `(TEST) Call dentist Tue 3pm…` record wasn't created by me,
so I'll leave it alone.

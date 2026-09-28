# Property mapping — Second Brain 2.0 › Everything

Schema read directly from Notion on 2026-09-28. Data source is
`collection://923ba32e-04e8-4c61-bf44-43093e061c0a`, and it's the **only** Everything database
inside Second Brain 2.0. No properties were created, renamed or changed.

## What the capture adapters write

| Property (exact name) | Type | Siri: Capture to Second Brain | Share Sheet: Share to Second Brain | Bookmarklet | `sb_capture.py` |
|---|---|---|---|---|---|
| `Name` | title | First 8 words of the dictation | Page title for Safari pages; file name for files; otherwise the first 8 words | Page title | `--title`, or the first 8 words (+ "…") |
| `Raw Capture` | text | **Exact dictated text**, unmodified | `Note: <your note>` (if any), then `Title:`/`URL:` lines, then the shared text verbatim. For files: `Shared file:` and `Shared type:` lines | `Note:`, `Title:`, `URL:`, then the selection verbatim | `Note:`/`Title:`/`URL:` header, then the text verbatim |
| `Capture Source` | select | `Siri Shortcut` | `Shared from App` | `Web Clip` | `--source` (default `Typed`) |
| `AI Triage` | select | `Needs AI` | `Needs AI` | `Needs AI` | `Needs AI` |
| `Source URL` | url | — | First URL found (skipped if over 2,000 characters; it's still in Raw Capture) | Page URL | `--url` |
| `Source app` | text | — | `Safari` for Safari pages; otherwise empty (iOS doesn't say which app shared) | Browser name | `--source-app` |
| `Attachments` | file | — | The uploaded file (single-part upload, 20 MB or less; 5 MB on Notion's free plan) | — | `--file` (repeatable) and `full-capture.txt` for over-long text |
| `Date` | date | **Never set.** The triage agent decides | Never set | Never set | Only with an explicit ISO `--date 2026-10-06[T15:00]`; natural language is refused |

## Never written by the adapters (left to triage or to you)

`Cleaned Thought`, `Type`, `Status`, `Priority`, `Details`, `Next Action`, `Tags`,
`Creator / Author`, `Frequency`, `People`, `Places`, `Project / Area`, `Related Items`,
`Related to Everything (Related Items)`, `Health Entries`, `Ralphie Food Trials`.

Reserved for the Phase 4 calendar sync (not active): `External Event ID`, `Calendar Link`, `Calendar Sync`.

`Captured At` is a Notion `created_time` property, so Notion fills it automatically.

## Why the note goes into Raw Capture, not Details

The live test showed the triage agent **rewrites `Details`** (see TEST_REPORT.md). Your note is
original input, so it lives in `Raw Capture`, which the operating rules say is never overwritten.
It's clearly labelled with a `Note:` prefix, and the shared text below it stays verbatim. Nothing
the adapters write can be lost to triage.

## Full schema as found (27 properties + 1 system reverse relation)

| Property | Type | Options / target |
|---|---|---|
| Name | title | |
| Raw Capture | text | |
| Cleaned Thought | text | |
| Type | select | Task, Event, Reminder, Project, Idea, Note, Journal, Book, Web Clip, Video, Research, Quote, Habit, Other |
| Status | status | Not started · In progress · Done |
| Date | date | |
| Priority | select | High, Medium, Low |
| Capture Source | select | Typed, Siri Shortcut, Shared from App, Web Clip, Voice Note, Notion, Imported |
| Source URL | url | |
| Source app | text | |
| Details | text | |
| Next Action | text | |
| AI Triage | select | Needs AI, Triaged, Human Review |
| Tags | multi-select | Personal, Health, Relationship, Travel, Finance, Pet, Learning, Household |
| Attachments | file | |
| Creator / Author | text | |
| Frequency | select | Daily, Weekdays, Weekly, Monthly, Custom |
| External Event ID | text | |
| Calendar Link | url | |
| Calendar Sync | select | Not Synced, Synced, Error |
| Captured At | created_time | |
| People | relation | People |
| Places | relation | Places |
| Project / Area | relation | Projects & Areas |
| Related Items | relation | Everything (self) |
| Related to Everything (Related Items) | relation | Everything (self). This is the reverse side of Related Items; it wasn't in your list |
| Health Entries | relation | Health Log |
| Ralphie Food Trials | relation | Ralphie's Food Trials |

## Notion API request (what every adapter sends)

```json
POST https://api.notion.com/v1/pages
Notion-Version: 2025-09-03
{
  "parent": {"type": "data_source_id", "data_source_id": "923ba32e-04e8-4c61-bf44-43093e061c0a"},
  "properties": {
    "Name":           {"title":     [{"type": "text", "text": {"content": "…"}}]},
    "Raw Capture":    {"rich_text": [{"type": "text", "text": {"content": "≤900–1000 chars"}}, "…up to 95 pieces"]},
    "Capture Source": {"select": {"name": "Siri Shortcut"}},
    "AI Triage":      {"select": {"name": "Needs AI"}},
    "Source URL":     {"url": "…"},
    "Source app":     {"rich_text": [{"type": "text", "text": {"content": "Safari"}}]},
    "Attachments":    {"files": [{"type": "file_upload", "file_upload": {"id": "…"}}]}
  }
}
```

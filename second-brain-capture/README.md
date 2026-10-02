# Second Brain capture adapters

These tools send captures from Siri, the Apple Share Sheet, browsers and the Mac
terminal into the **existing** `Second Brain 2.0 › Everything` database. They
don't create databases, change the schema, set Type or Status, or write to People,
Places, Projects & Areas, Health Log or Ralphie's Food Trials.

```
Siri ─┐
Share Sheet (iPhone/iPad/Mac) ─┤
Browser bookmarklet ─┤──► Everything (AI Triage = Needs AI) ──► triage agent ──► views & relations
sb_capture.py (terminal) ─┘
```

| Piece | What it is | Status |
|---|---|---|
| `shortcuts/unsigned/Second Brain Setup.shortcut` | Saves your Notion token and tests access | Generated. Sign on your Mac |
| `shortcuts/unsigned/Capture to Second Brain.shortcut` | "Hey Siri, capture to my Second Brain" | Generated. Sign on your Mac |
| `shortcuts/unsigned/Share to Second Brain.shortcut` | Share Sheet, Mac Services menu, bookmarklet target | Generated. Sign on your Mac |
| `shortcuts/steps/*.md` | Step-by-step manual build of each shortcut (fallback) | Generated |
| `bookmarklet/bookmarklet.txt` | Chrome, Firefox, Edge, Brave or Safari clipper, with no token in the browser | Ready |
| `cli/sb_capture.py` | Terminal capture, `--check`, and replay of failed captures | Ready, 14 tests pass |
| `CALENDAR_PLAN.md` | Phase 4 plan. **Not active; needs your decisions** | Waiting on you |

Other documents: [PROPERTY_MAPPING.md](PROPERTY_MAPPING.md) · [TEST_REPORT.md](TEST_REPORT.md) ·
[TROUBLESHOOTING.md](TROUBLESHOOTING.md) · [MANUAL_STEPS.md](MANUAL_STEPS.md) (what you must do, and what couldn't be automated)

---

## Setup (about 15 minutes)

### 1. Create a Notion integration with access to Everything only

1. Open <https://www.notion.so/profile/integrations> and click **New integration**.
2. Name it `Second Brain Capture`, set Type to **Internal**, and pick your workspace. Save.
3. Under **Capabilities**, keep **Read content** and **Insert content** on. Turn **Update content** off; only the future calendar sync needs it. Set User information to **No user information**. Save.
4. Copy the **Internal Integration Secret** (it starts with `ntn_`). Keep it private.
5. Go to the **Access** tab, choose **Edit access**, and select only the **Everything** database. Don't select the `Second Brain 2.0` page, because that would also expose People, Places, Health Log and the rest.
   Alternative route: open Everything, click `•••`, choose **Connections**, and add `Second Brain Capture`.

### 2. Sign and install the shortcuts (on your Mac)

```bash
git clone https://github.com/melkins1324/lateral.git && cd lateral
git checkout claude/notion-second-brain-capture-iijgc9
cd second-brain-capture/shortcuts
./sign_shortcuts.sh          # builds, signs, and opens the ./signed folder
```

Double-click each file in `signed/`, importing **Second Brain Setup first**.
Shortcuts syncs them to your iPhone and iPad through iCloud. You can also AirDrop the signed files.

> Apple only imports signed shortcut files, and signing needs a Mac. If the
> import fails or an action shows up blank, build that shortcut by hand from
> `shortcuts/steps/<name>.md`. It matches the file step for step.

### 3. Run "Second Brain Setup" once

Paste the `ntn_…` secret when asked. The shortcut saves it to
`iCloud Drive › Shortcuts › SecondBrain › notion_token.txt`, creates the Outbox
folder, and checks with Notion. You should see **✅ Second Brain connected**.
If you see ❌, go to [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### 4. Siri

Say **"Hey Siri, capture to my Second Brain."** Siri uses the shortcut's name,
"Capture to Second Brain", and matches the phrase closely. Speak naturally; the
shortcut stops listening after a pause. You'll get a **✅ Saved to Second Brain**
notification only after Notion confirms the page exists.

The first run asks for permission to reach api.notion.com and to access files.
Choose **Always Allow**.

### 5. Share Sheet

In any app, tap **Share** and choose **Share to Second Brain**. If it isn't listed, tap
**Edit Actions** and add it. You can type an optional note, or leave it blank and tap Done.
On a Mac it also appears in the right-click **Services** menu for selected text.
You can give it a keyboard shortcut under System Settings › Keyboard › Keyboard Shortcuts › Services.

How shared items are handled:
- **Files** (images, screenshots, PDFs, documents, audio, video files) → **one record per file**, uploaded to `Attachments`.
- **Text, links, web pages, map locations, products and recipes** shared together → **one combined record**, because they describe the same thing.
- A Safari page keeps its title (→ `Name`), URL (→ `Source URL`), and selected text (→ `Raw Capture`), and `Source app` is set to Safari.

### 6. Browser clipper (Chrome, Firefox, Edge, Brave; also works in Safari)

Make a new bookmark and paste the whole contents of `bookmarklet/bookmarklet.txt` as its URL.
Select text on a page and click the bookmark. It hands the title, URL, selection and browser
name to the **Share to Second Brain** shortcut through `shortcuts://`. The browser never sees
your token, and there's no server. The first time, the browser asks to open Shortcuts; choose
**Always allow**.
These records get `Capture Source = Web Clip` and `Source app = <browser>`.

### 7. Terminal (optional)

```bash
security add-generic-password -a "$USER" -s second-brain-notion -w   # paste the secret when prompted
cd second-brain-capture/cli
python3 sb_capture.py --check                        # verifies token, access and schema
python3 sb_capture.py "Pick up dry cleaning Thursday"
pbpaste | python3 sb_capture.py - --source "Web Clip" --url "https://…" --source-app Chrome
python3 sb_capture.py --file ~/Desktop/scan.pdf --note "insurance"
python3 sb_capture.py --flush-outbox                 # resend anything that failed (local + iCloud outboxes)
```

---

## Why the desktop design looks like this (Phase 3 evaluation)

| Option | Verdict |
|---|---|
| **macOS Shortcut** (the same Share shortcut) | **Chosen.** No new code; it covers Safari's share menu, the Services menu in every app, and Finder files |
| **Bookmarklet → `shortcuts://`** | **Chosen** for Chrome, Firefox, Edge and Brave. No token in the browser and no server |
| Browser extension | Rejected. It would need the token in the extension or a server, plus store review, for no extra capability |
| Hosted endpoint | Rejected as **unnecessary**. Nothing here needs a server |
| Notion Web Clipper | Rejected. It can't set `Capture Source`, `AI Triage = Needs AI` or `Source app` |
| Local script / CLI | Built (`sb_capture.py`) for the terminal, automation, and replaying the outbox |

## Reliability

- **Atomic:** each record is created in one request with every essential property. Files are uploaded first and referenced inside that same create request.
- **Confirmed success:** the ✅ appears only when Notion returns a `page` object.
- **Retries:** rate limits and temporary server errors are retried. The shortcuts try 3 times with a 3-second wait. The CLI tries 4 times with exponential backoff and respects `Retry-After`.
- **No duplicates (CLI):** after a timeout or server error, the CLI checks whether Notion actually created the page before trying again.
- **Nothing lost:**
  - The shortcuts save each request to `SecondBrain/Outbox/` before sending and delete it only after success. On failure the capture also goes to the clipboard.
  - The CLI writes `~/.second-brain/outbox/`.
  - `sb_capture.py --flush-outbox` replays both outboxes.
- **Timeouts:** the CLI uses 20 seconds per request. Shortcuts uses Apple's fixed timeout of about 60 seconds, and a hard network failure stops the shortcut, but the Outbox copy is already saved.
- **Logs:** the CLI writes `~/.second-brain/capture.log`, containing event names, page IDs, sizes and error codes only. No token and no capture text.
- **Long captures:** Raw Capture holds about 85,000 characters (Notion's limit is 100 pieces). Anything longer is flagged in the record. The shortcut keeps the full text in the Outbox, and the CLI attaches it as `full-capture.txt`.

## Security

- The token lives only in `iCloud Drive/Shortcuts/SecondBrain/notion_token.txt`, the macOS Keychain, or `$NOTION_TOKEN`. It's never in a shortcut, the repo, logs or a browser.
- The integration can only **read and insert** in **Everything**.
- `.env` is git-ignored, and `.env.example` lists variable names only.
- Trade-off: any shortcut on your devices can read the iCloud token file. The integration's narrow access limits the damage. Rotate the token in Notion if a device is lost.

## Uninstall or disable

1. Revoke access immediately: Notion › Settings › **Connections**, then remove `Second Brain Capture`, or delete it at notion.so/profile/integrations. Every adapter stops working at once.
2. Delete the three shortcuts in the Shortcuts app.
3. Delete `iCloud Drive › Shortcuts › SecondBrain` (the token and outbox). Check the Outbox for anything unsent first.
4. Remove the bookmark.
5. On a Mac: run `security delete-generic-password -s second-brain-notion` and `rm -rf ~/.second-brain`.

## A note on where this code lives

The only repository this session could reach is `melkins1324/lateral`, your game, so this
lives in `second-brain-capture/` on its own branch. **Don't merge it into `main`.** GitHub
Pages serves `main`, so these docs would become public web pages. Nothing secret is in them,
but it's untidy. Moving the folder to its own repository later is a copy and paste.

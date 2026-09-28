# What you must do yourself, and what couldn't be automated

## Your steps

| Where | Step | Why it can't be done for you |
|---|---|---|
| **Notion** (browser) | Create the internal integration, give it Read and Insert content, give it access to **Everything only**, and copy the `ntn_` secret (README step 1) | Only a workspace member can create integrations and see the secret. The Notion connector used in this session can't create them and can't be used by Apple Shortcuts |
| **Mac** | Run `shortcuts/sign_shortcuts.sh`, then double-click the three signed files | Apple only imports **signed** shortcut files, and only macOS can sign them |
| **iPhone/iPad** | Run **Second Brain Setup** once and paste the secret | The secret must never pass through me or the repo |
| **iPhone/iPad** | The first run of each shortcut asks for permission to reach `api.notion.com` and to read files. Tap **Always Allow** | Apple requires a person to approve this on the device |
| **iPhone/iPad** | Optional: in the Share Sheet use **Edit Actions** to pin *Share to Second Brain* near the top | It's a personal UI preference |
| **Mac** | Optional: give the Services menu entry a keyboard shortcut (System Settings › Keyboard › Keyboard Shortcuts › Services) | Same |
| **Browsers** | Create the bookmark from `bookmarklet/bookmarklet.txt` | Browsers don't allow bookmarks to be installed automatically |
| **Mac** (optional) | Put the secret in the Keychain for the terminal tool | Same reason as the Setup step |
| **All devices** | Run the on-device checklist in TEST_REPORT.md | Nothing Apple-side can run in a cloud Linux sandbox |
| **You** | Approve the test results so I can delete the 7 `[INTEGRATION TEST]` records | You asked to approve first |
| **You** | Answer the calendar questions in CALENDAR_PLAN.md | You asked me to ask first |

## What couldn't be automated, and why

1. **Installing shortcuts on your devices.** No API installs shortcuts. I generated complete
   files and an exact manual build guide for each.
2. **Signing shortcuts.** Signing uses Apple's servers through `shortcuts sign`, which only
   exists on macOS.
3. **Proving the shortcuts run on a device.** I checked their logic and structure, and the
   Notion side is verified live. But the generated `.shortcut` files have **never been
   imported on a real device**, because I had no Apple device available. Apple doesn't
   document the file format. Parameter names for some actions (the Form file upload
   especially) are my best knowledge, not documented facts. If any step imports blank,
   rebuild just that step from `shortcuts/steps/`, tell me which one, and I'll fix the
   generator.
4. **Using AI classification inside the shortcuts.** Deliberately not done: you asked for
   classification to stay in Notion.
5. **Detecting the source app on iOS.** Apple doesn't give shortcuts the name of the app that
   shared. It's known only for Safari pages, the bookmarklet and the CLI.
6. **Guaranteed duplicate prevention inside Shortcuts.** Shortcuts has no idempotency key and
   no cheap way to query Notion before retrying. It retries only on errors Notion marks as
   temporary, so a duplicate is possible only in the rare case where Notion returns an error
   but actually saved the page. The CLI does check.
7. **Catching network errors inside Shortcuts.** Shortcuts stops outright when there's no
   connection. That's why every capture is written to the Outbox before it's sent.
8. **Files over 20 MB.** Notion needs a multi-part upload for these, which isn't practical
   in Shortcuts. The record is still created, it says the attachment is missing, and the
   file is kept in `Outbox/files`. Free Notion workspaces cap files at 5 MB anyway.
9. **A live REST test from this environment.** The sandbox's network policy blocks
   `api.notion.com`. Live verification went through the Notion connector instead.

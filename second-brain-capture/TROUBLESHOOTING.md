# Troubleshooting

**First rule:** a capture is never thrown away. If anything fails, look in
**Files › iCloud Drive › Shortcuts › SecondBrain › Outbox** (shortcuts) or
`~/.second-brain/outbox` (terminal), and check your clipboard.
Resend from a Mac with `python3 cli/sb_capture.py --flush-outbox`.

| Symptom | Cause | Fix |
|---|---|---|
| "Second Brain isn't set up" | Token file missing | Run **Second Brain Setup** |
| ⚠️ "Not saved … API token is invalid (unauthorized)" | Token mistyped, rotated or revoked | Copy the secret again from notion.so/profile/integrations and run Setup |
| ⚠️ "… Could not find data source … (object_not_found)" | The integration isn't connected to Everything | Open Everything › `•••` › **Connections** › add *Second Brain Capture* |
| ⚠️ "… is not a property that exists" or "… select option" (validation_error) | Someone renamed a property or option in Notion | Rename it back, or tell me the new name. The mapping is in PROPERTY_MAPPING.md |
| ⚠️ "… rate_limited" after 3 tries | Notion is throttling | Wait a minute, then resend from the Outbox |
| The shortcut stops with "The request timed out" or "offline" | No network. Shortcuts stops the shortcut on network errors | The Outbox already has the capture. Resend later |
| Record created but "Attachment NOT uploaded" in Raw Capture | File over the limit (5 MB on the free plan, 20 MB single-part) or an unsupported type | The original file is in `Outbox/files`. Attach it by hand in Notion |
| Import says "can't be opened" or "unsigned" | The file wasn't signed | Run `./sign_shortcuts.sh` on a Mac and import from `signed/` |
| An action inside an imported shortcut is blank or shows an error | The generated file used a parameter name your iOS version doesn't know | Rebuild that part from `shortcuts/steps/<name>.md`, and tell me which step so I can fix the generator |
| Siri runs something else | Phrase mismatch | Say "Capture to Second Brain", or rename the shortcut to your exact phrase |
| Share Sheet doesn't list the shortcut | Share Sheet toggle is off | Shortcut › ⓘ › **Show in Share Sheet** on; in the Share Sheet use **Edit Actions** to favourite it |
| Bookmarklet does nothing | Browser blocked `shortcuts://`, or the bookmark URL was truncated | Re-paste all of `bookmarklet.txt`; allow "Open Shortcuts" when asked |
| `Source app` empty on Share Sheet captures | iOS doesn't tell shortcuts which app shared | Expected. Only Safari pages, the bookmarklet and the CLI can report it |
| Duplicate record after a Shortcuts retry | Rare: Notion returned a 5xx but actually saved | Delete the extra. (The CLI checks before retrying; Shortcuts can't do that cheaply) |
| `sb_capture.py: No Notion token found` | Keychain item or env var missing | `security add-generic-password -a "$USER" -s second-brain-notion -w` |
| `--check` lists "✗ … missing" | The schema differs from what the adapters expect | Nothing is sent wrongly until that's fixed; see PROPERTY_MAPPING.md |

Logs: `~/.second-brain/capture.log` (terminal) holds event names, IDs and error codes, but
never the token or capture text. The shortcuts show their errors on screen and keep the
failed request in the Outbox.

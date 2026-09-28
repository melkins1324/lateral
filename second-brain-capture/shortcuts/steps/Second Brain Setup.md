# Second Brain Setup — build by hand

Generated from `build_shortcuts.py`; it matches the .shortcut file step for step.
`[Name]` means insert that variable (tap the field → Select Variable, or pick it from the variable bar). `[X from step N]` is the output of step N.
⏎ means a line break (press Return), ⇥ a tab.

1. **Comment**: Run once (and again whenever you rotate the token). Saves the Notion token to iCloud Drive/Shortcuts/SecondBrain/notion_token.txt and checks Notion access.
2. **Ask for Input** (Text, multiline): prompt `Paste your Notion integration secret (starts with ntn_). It is saved only in your iCloud Drive.`
3. **Replace Text** in [Provided Input from step 2]: find `\s` replace with `` (Regular Expression **ON**, Case Sensitive ON) — remove stray spaces/line breaks
4. **Set Variable** `Token` to [Updated Text from step 3]
5. **Set Name** of [Token] to `notion_token.txt`
6. **Save File** [Renamed Item from step 5] — Ask Where to Save OFF, Subpath `SecondBrain/`, Overwrite ON
7. **Text**: `Captures that could not be sent to Notion are kept here. Open one to recover its text, or replay it from a Mac with: python3 sb_capture.py --replay <file>`
8. **Set Name** of [Text from step 7] to `README.txt`
9. **Save File** [Renamed Item from step 8] — Ask Where to Save OFF, Subpath `SecondBrain/Outbox/`, Overwrite ON
10. **Get Contents of URL** `https://api.notion.com/v1/data_sources/923ba32e-04e8-4c61-bf44-43093e061c0a` — Method **GET**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`
11. **Get Dictionary Value**: Value for key `object` in [Contents of URL from step 10]
12. **If** [Dictionary Value from step 11] is `data_source`
    13. **Show Alert**: title `✅ Second Brain connected`, message `The token works and the integration can see the Everything database. 'Capture to Second Brain' and 'Share to Second Brain' are ready.` (Show Cancel Button OFF)
14. **Otherwise**
    15. **Get Dictionary Value**: Value for key `message` in [Contents of URL from step 10]
    16. **Show Alert**: title `❌ Notion refused the token`, message `Notion said: [Dictionary Value from step 15]⏎⏎Check: (1) you copied the whole secret, (2) in Notion, Everything › ••• › Connections includes your integration.` (Show Cancel Button OFF)
17. **End If**

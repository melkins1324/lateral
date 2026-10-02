# Capture to Second Brain — build by hand

Generated from `build_shortcuts.py`; it matches the .shortcut file step for step.
`[Name]` means insert that variable (tap the field → Select Variable, or pick it from the variable bar). `[X from step N]` is the output of step N.
⏎ means a line break (press Return), ⇥ a tab.

1. **Comment**: Capture to Second Brain: Dictate a thought; it is saved word-for-word as Raw Capture. Sends to Second Brain 2.0 › Everything only. Classification is done later by the Notion triage agent.
2. **Comment**: TEST MODE: type [INTEGRATION TEST] followed by a space into the next Text action to tag captures as tests. Leave it empty for normal use.
3. **Text** (leave empty)
4. **Set Variable** `TestPrefix` to [Text from step 3]
5. **Comment**: Load the Notion token saved by the 'Second Brain Setup' shortcut. The token never lives inside this shortcut.
6. **Get File** from Shortcuts folder, path `SecondBrain/notion_token.txt` (Show Document Picker OFF, Error If Not Found OFF)
7. **If** [File from step 6] does not have any value
    8. **Show Alert**: title `Second Brain isn't set up`, message `Run the 'Second Brain Setup' shortcut once to save your Notion token. Nothing was captured.` (Show Cancel Button OFF)
    9. **Stop This Shortcut**
10. **End If**
11. **Get Text from Input**: [File from step 6]
12. **Replace Text** in [Text from step 11]: find `\s` replace with `` (Regular Expression **ON**, Case Sensitive ON) — strip spaces/line breaks around the token
13. **Set Variable** `Token` to [Updated Text from step 12]
14. **Dictate Text** (Stop Listening: After Pause)
15. **Set Variable** `Dictation` to [Dictated Text from step 14]
16. **If** [Dictation] does not have any value
    17. **Show Alert**: title `Nothing heard`, message `No speech was captured, so nothing was saved.` (Show Cancel Button OFF)
    18. **Stop This Shortcut**
19. **End If**
20. **Text**: `Voice capture`
21. **Set Variable** `TitleText` to [Text from step 20]
22. **Match Text**: pattern `^\S+(?:[ \t]+\S+){0,7}` in [Dictation] (Case Sensitive ON)
23. **If** [Matches from step 22] has any value
    24. **Get Item from List**: First Item of [Matches from step 22]
    25. **Set Variable** `TitleText` to [Item from List from step 24]
26. **End If**
27. **Comment**: Date is intentionally left empty. The triage agent (or you) sets it once it is certain.
28. **Comment**: --- Send one record to Everything (Capture Source = Siri Shortcut) ---
29. **Replace Text** in [TitleText]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
30. **Replace Text** in [Updated Text from step 29]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
31. **Replace Text** in [Updated Text from step 30]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
32. **Replace Text** in [Updated Text from step 31]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
33. **Replace Text** in [Updated Text from step 32]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
34. **Replace Text** in [Updated Text from step 33]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
35. **Set Variable** `eTitle` to [Updated Text from step 34]
36. **Replace Text** in [Dictation]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
37. **Replace Text** in [Updated Text from step 36]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
38. **Replace Text** in [Updated Text from step 37]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
39. **Replace Text** in [Updated Text from step 38]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
40. **Replace Text** in [Updated Text from step 39]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
41. **Replace Text** in [Updated Text from step 40]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
42. **Set Variable** `eRaw` to [Updated Text from step 41]
43. **Match Text**: pattern `(?:\\.|[^\\]){1,900}` in [eRaw] (Case Sensitive ON)
44. **Set Variable** `Chunks` to [Matches from step 43]
45. **Text**: `no`
46. **Set Variable** `Overflow` to [Text from step 45]
47. **Text** (leave empty)
48. **Set Variable** `OverflowNote` to [Text from step 47]
49. **Count** Items in [Matches from step 43]
50. **If** [Count from step 49] is greater than `95`
    51. **Get Item from List**: Items in Range 1 to 95 of [Matches from step 43]
    52. **Set Variable** `Chunks` to [Items in Range from step 51]
    53. **Text**: `yes`
    54. **Set Variable** `Overflow` to [Text from step 53]
    55. **Text**: `"}},{"type":"text","text":{"content":"\n\n[Capture truncated at about 85,000 characters to fit Notion. The full text is kept in iCloud Drive/Shortcuts/SecondBrain/Outbox.]`
    56. **Set Variable** `OverflowNote` to [Text from step 55]
57. **End If**
58. **Combine Text** [Chunks] with Custom separator `"}},{"type":"text","text":{"content":"`
59. **Set Variable** `RawPieces` to [Combined Text from step 58]
60. **Text** (leave empty)
61. **Set Variable** `Opt` to [Text from step 60]
62. **Text**: `{"parent":{"type":"data_source_id","data_source_id":"923ba32e-04e8-4c61-bf44-43093e061c0a"},"properties":{"Name":{"title":[{"type":"text","text":{"content":"[TestPrefix][eTitle]"}}]},"Raw Capture":{"rich_text":[{"type":"text","text":{"content":"[RawPieces][OverflowNote]"}}]},"Capture Source":{"select":{"name":"Siri Shortcut"}},"AI Triage":{"select":{"name":"Needs AI"}}[Opt]}}`
63. **Set Variable** `Body` to [Text from step 62]
64. **Date** (Current Date)
65. **Format Date** [Date from step 64] — Custom format `yyyyMMdd-HHmmss`
66. **Random Number** between 1000 and 9999
67. **Set Name** of [Body] to `capture-[Formatted Date from step 65]-[Random Number from step 66].json`
68. **Save File** [Renamed Item from step 67] — Ask Where to Save OFF, Subpath `SecondBrain/Outbox/`, Overwrite OFF
69. **Set Variable** `OutboxFile` to [Saved File from step 68]
70. **Text**: `pending`
71. **Set Variable** `SendStatus` to [Text from step 70]
72. **Repeat** 3 times
    73. **If** [SendStatus] is `pending`
        74. **Get Contents of URL** `https://api.notion.com/v1/pages` — Method **POST**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`, `Content-Type` = `application/json`; Request Body **File** = [Body]
        75. **Set Variable** `Response` to [Contents of URL from step 74]
        76. **Get Dictionary Value**: Value for key `object` in [Contents of URL from step 74]
        77. **If** [Dictionary Value from step 76] is `page`
            78. **Text**: `done`
            79. **Set Variable** `SendStatus` to [Text from step 78]
        80. **Otherwise**
            81. **Get Dictionary Value**: Value for key `code` in [Contents of URL from step 74]
            82. **Set Variable** `ErrCode` to [Dictionary Value from step 81]
            83. **Text**: `|rate_limited|internal_server_error|service_unavailable|gateway_timeout|conflict_error|`
            84. **If** [Text from step 83] contains `|[ErrCode]|`
                85. **Wait** 3 seconds
            86. **Otherwise**
                87. **Text**: `fatal`
                88. **Set Variable** `SendStatus` to [Text from step 87]
            89. **End If**
        90. **End If**
    91. **End If**
92. **End Repeat**
93. **If** [SendStatus] is `done`
    94. **If** [Overflow] is `no`
        95. **Delete Files** [OutboxFile] (Confirm Before Deleting OFF)
    96. **End If**
    97. **Show Notification**: title `✅ Saved to Second Brain`, body `[TestPrefix][TitleText]`
98. **Otherwise**
    99. **Get Dictionary Value**: Value for key `message` in [Response]
    100. **Set Variable** `ErrMessage` to [Dictionary Value from step 99]
    101. **Copy to Clipboard**: [Dictation]
    102. **Show Alert**: title `⚠️ Not saved to Notion`, message `Notion said: [ErrMessage] ([ErrCode])⏎⏎Nothing is lost: the capture was copied to your clipboard and saved in iCloud Drive › Shortcuts › SecondBrain › Outbox.` (Show Cancel Button OFF)
103. **End If**

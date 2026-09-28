# Share to Second Brain — build by hand

Generated from `build_shortcuts.py`; it matches the .shortcut file step for step.
`[Name]` means insert that variable (tap the field → Select Variable, or pick it from the variable bar). `[X from step N]` is the output of step N.
⏎ means a line break (press Return), ⇥ a tab.

**Shortcut settings (ⓘ):** Show in Share Sheet ON; on Mac also Use as Quick Action → Services Menu. Receive: Any input. If there's no input: Stop and Respond.

1. **Comment**: Share to Second Brain: Share Sheet / Mac Services capture. Files get one record each; text, links and web pages shared together become one record. Sends to Second Brain 2.0 › Everything only. Classification is done later by the Notion triage agent.
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
14. **If** [Shortcut Input] does not have any value
    15. **Show Alert**: title `Nothing shared`, message `This shortcut received no input, so nothing was saved.` (Show Cancel Button OFF)
    16. **Stop This Shortcut**
17. **End If**
18. **Text** (leave empty)
19. **Set Variable** `NoteBlock` to [Text from step 18]
20. **Text** (leave empty)
21. **Set Variable** `PageTitle` to [Text from step 20]
22. **Text** (leave empty)
23. **Set Variable** `SrcURL` to [Text from step 22]
24. **Text** (leave empty)
25. **Set Variable** `App` to [Text from step 24]
26. **Text** (leave empty)
27. **Set Variable** `AttachID` to [Text from step 26]
28. **Text** (leave empty)
29. **Set Variable** `AttachNote` to [Text from step 28]
30. **Ask for Input** (Text, multiline): prompt `Add a note? (optional — leave blank and tap Done)`
31. **Set Variable** `Note` to [Provided Input from step 30]
32. **If** [Note] has any value
    33. **Text**: `Note: [Note]⏎⏎`
    34. **Set Variable** `NoteBlock` to [Text from step 33]
35. **End If**
36. **Get Text from Input**: [Shortcut Input]
37. **Set Variable** `InText` to [Text from step 36]
38. **If** [InText] begins with `SBCLIP1⏎`
    39. **Comment**: Came from the browser bookmarklet: title, URL, selection and browser are in the JSON.
    40. **Replace Text** in [InText]: find `^SBCLIP1\n` replace with `` (Regular Expression **ON**, Case Sensitive ON) — drop the marker line
    41. **Get Dictionary from Input**: [Updated Text from step 40]
    42. **Set Variable** `Clip` to [Dictionary from step 41]
    43. **Get Dictionary Value**: Value for key `title` in [Clip]
    44. **Set Variable** `PageTitle` to [Dictionary Value from step 43]
    45. **Get Dictionary Value**: Value for key `url` in [Clip]
    46. **Set Variable** `SrcURL` to [Dictionary Value from step 45]
    47. **Get Dictionary Value**: Value for key `app` in [Clip]
    48. **Set Variable** `App` to [Dictionary Value from step 47]
    49. **Get Dictionary Value**: Value for key `selection` in [Clip]
    50. **Set Variable** `Selection` to [Dictionary Value from step 49]
    51. **Text**: `[NoteBlock]Title: [PageTitle]⏎URL: [SrcURL]⏎⏎[Selection]`
    52. **Set Variable** `RawText` to [Text from step 51]
    53. **If** [PageTitle] has any value
        54. **Set Variable** `TitleText` to [PageTitle]
    55. **Otherwise**
        56. **Text**: `Web clip`
        57. **Set Variable** `TitleText` to [Text from step 56]
        58. **Match Text**: pattern `^\S+(?:[ \t]+\S+){0,7}` in [Selection] (Case Sensitive ON)
        59. **If** [Matches from step 58] has any value
            60. **Get Item from List**: First Item of [Matches from step 58]
            61. **Set Variable** `TitleText` to [Item from List from step 60]
        62. **End If**
    63. **End If**
    64. **Comment**: --- Send one record to Everything (Capture Source = Web Clip) ---
    65. **Replace Text** in [TitleText]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
    66. **Replace Text** in [Updated Text from step 65]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
    67. **Replace Text** in [Updated Text from step 66]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
    68. **Replace Text** in [Updated Text from step 67]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
    69. **Replace Text** in [Updated Text from step 68]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
    70. **Replace Text** in [Updated Text from step 69]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
    71. **Set Variable** `eTitle` to [Updated Text from step 70]
    72. **Replace Text** in [RawText]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
    73. **Replace Text** in [Updated Text from step 72]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
    74. **Replace Text** in [Updated Text from step 73]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
    75. **Replace Text** in [Updated Text from step 74]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
    76. **Replace Text** in [Updated Text from step 75]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
    77. **Replace Text** in [Updated Text from step 76]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
    78. **Set Variable** `eRaw` to [Updated Text from step 77]
    79. **Match Text**: pattern `(?:\\.|[^\\]){1,900}` in [eRaw] (Case Sensitive ON)
    80. **Set Variable** `Chunks` to [Matches from step 79]
    81. **Text**: `no`
    82. **Set Variable** `Overflow` to [Text from step 81]
    83. **Text** (leave empty)
    84. **Set Variable** `OverflowNote` to [Text from step 83]
    85. **Count** Items in [Matches from step 79]
    86. **If** [Count from step 85] is greater than `95`
        87. **Get Item from List**: Items in Range 1 to 95 of [Matches from step 79]
        88. **Set Variable** `Chunks` to [Items in Range from step 87]
        89. **Text**: `yes`
        90. **Set Variable** `Overflow` to [Text from step 89]
        91. **Text**: `"}},{"type":"text","text":{"content":"\n\n[Capture truncated at about 85,000 characters to fit Notion. The full text is kept in iCloud Drive/Shortcuts/SecondBrain/Outbox.]`
        92. **Set Variable** `OverflowNote` to [Text from step 91]
    93. **End If**
    94. **Combine Text** [Chunks] with Custom separator `"}},{"type":"text","text":{"content":"`
    95. **Set Variable** `RawPieces` to [Combined Text from step 94]
    96. **Text** (leave empty)
    97. **Set Variable** `Opt` to [Text from step 96]
    98. **Replace Text** in [SrcURL]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
    99. **Replace Text** in [Updated Text from step 98]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
    100. **Replace Text** in [Updated Text from step 99]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
    101. **Replace Text** in [Updated Text from step 100]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
    102. **Replace Text** in [Updated Text from step 101]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
    103. **Replace Text** in [Updated Text from step 102]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
    104. **Set Variable** `eURL` to [Updated Text from step 103]
    105. **If** [eURL] has any value
        106. **Count** Characters in [eURL]
        107. **If** [Count from step 106] is greater than `2000`
            108. **Comment**: Too long for Notion's URL property; it is still inside Raw Capture.
        109. **Otherwise**
            110. **Text**: `[Opt],"Source URL":{"url":"[eURL]"}`
            111. **Set Variable** `Opt` to [Text from step 110]
        112. **End If**
    113. **End If**
    114. **Replace Text** in [App]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
    115. **Replace Text** in [Updated Text from step 114]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
    116. **Replace Text** in [Updated Text from step 115]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
    117. **Replace Text** in [Updated Text from step 116]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
    118. **Replace Text** in [Updated Text from step 117]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
    119. **Replace Text** in [Updated Text from step 118]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
    120. **Set Variable** `eApp` to [Updated Text from step 119]
    121. **If** [eApp] has any value
        122. **Text**: `[Opt],"Source app":{"rich_text":[{"type":"text","text":{"content":"[eApp]"}}]}`
        123. **Set Variable** `Opt` to [Text from step 122]
    124. **End If**
    125. **Text**: `{"parent":{"type":"data_source_id","data_source_id":"923ba32e-04e8-4c61-bf44-43093e061c0a"},"properties":{"Name":{"title":[{"type":"text","text":{"content":"[TestPrefix][eTitle]"}}]},"Raw Capture":{"rich_text":[{"type":"text","text":{"content":"[RawPieces][OverflowNote]"}}]},"Capture Source":{"select":{"name":"Web Clip"}},"AI Triage":{"select":{"name":"Needs AI"}}[Opt]}}`
    126. **Set Variable** `Body` to [Text from step 125]
    127. **Date** (Current Date)
    128. **Format Date** [Date from step 127] — Custom format `yyyyMMdd-HHmmss`
    129. **Random Number** between 1000 and 9999
    130. **Set Name** of [Body] to `capture-[Formatted Date from step 128]-[Random Number from step 129].json`
    131. **Save File** [Renamed Item from step 130] — Ask Where to Save OFF, Subpath `SecondBrain/Outbox/`, Overwrite OFF
    132. **Set Variable** `OutboxFile` to [Saved File from step 131]
    133. **Text**: `pending`
    134. **Set Variable** `SendStatus` to [Text from step 133]
    135. **Repeat** 3 times
        136. **If** [SendStatus] is `pending`
            137. **Get Contents of URL** `https://api.notion.com/v1/pages` — Method **POST**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`, `Content-Type` = `application/json`; Request Body **File** = [Body]
            138. **Set Variable** `Response` to [Contents of URL from step 137]
            139. **Get Dictionary Value**: Value for key `object` in [Contents of URL from step 137]
            140. **If** [Dictionary Value from step 139] is `page`
                141. **Text**: `done`
                142. **Set Variable** `SendStatus` to [Text from step 141]
            143. **Otherwise**
                144. **Get Dictionary Value**: Value for key `code` in [Contents of URL from step 137]
                145. **Set Variable** `ErrCode` to [Dictionary Value from step 144]
                146. **Text**: `|rate_limited|internal_server_error|service_unavailable|gateway_timeout|conflict_error|`
                147. **If** [Text from step 146] contains `|[ErrCode]|`
                    148. **Wait** 3 seconds
                149. **Otherwise**
                    150. **Text**: `fatal`
                    151. **Set Variable** `SendStatus` to [Text from step 150]
                152. **End If**
            153. **End If**
        154. **End If**
    155. **End Repeat**
    156. **If** [SendStatus] is `done`
        157. **If** [Overflow] is `no`
            158. **Delete Files** [OutboxFile] (Confirm Before Deleting OFF)
        159. **End If**
        160. **Show Notification**: title `✅ Saved to Second Brain`, body `[TestPrefix][TitleText]`
    161. **Otherwise**
        162. **Get Dictionary Value**: Value for key `message` in [Response]
        163. **Set Variable** `ErrMessage` to [Dictionary Value from step 162]
        164. **Copy to Clipboard**: [RawText]
        165. **Show Alert**: title `⚠️ Not saved to Notion`, message `Notion said: [ErrMessage] ([ErrCode])⏎⏎Nothing is lost: the capture was copied to your clipboard and saved in iCloud Drive › Shortcuts › SecondBrain › Outbox.` (Show Cancel Button OFF)
    166. **End If**
167. **Otherwise**
    168. **Comment**: Files (images, screenshots, PDFs, documents, audio, video files) become one record each.
    169. **Repeat with Each** item in [Shortcut Input]
        170. **Set Variable** `Item` to [Repeat Item]
        171. **Get Type** of [Item]
        172. **Set Variable** `ItemType` to [Type from step 171]
        173. **Text**: `|Image|PDF|File|Media|Photo media|`
        174. **If** [Text from step 173] contains `|[ItemType]|`
            175. **Get Name** of [Item]
            176. **Set Variable** `FName` to [Name from step 175]
            177. **Text** (leave empty)
            178. **Set Variable** `AttachID` to [Text from step 177]
            179. **Text** (leave empty)
            180. **Set Variable** `AttachNote` to [Text from step 179]
            181. **Text**: `{"mode":"single_part"}`
            182. **Get Contents of URL** `https://api.notion.com/v1/file_uploads` — Method **POST**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`, `Content-Type` = `application/json`; Request Body **File** = [Text from step 181]
            183. **Get Dictionary Value**: Value for key `id` in [Contents of URL from step 182]
            184. **Set Variable** `UploadID` to [Dictionary Value from step 183]
            185. **Get Contents of URL** `https://api.notion.com/v1/file_uploads/[UploadID]/send` — Method **POST**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`; Request Body **Form** with one **File** field named `file` = [Item]
            186. **Set Variable** `UploadResp` to [Contents of URL from step 185]
            187. **Get Dictionary Value**: Value for key `status` in [UploadResp]
            188. **If** [Dictionary Value from step 187] is `uploaded`
                189. **Set Variable** `AttachID` to [UploadID]
            190. **Otherwise**
                191. **Get Dictionary Value**: Value for key `message` in [UploadResp]
                192. **Set Variable** `UploadMsg` to [Dictionary Value from step 191]
                193. **Save File** [Item] — Ask Where to Save OFF, Subpath `SecondBrain/Outbox/files/`, Overwrite OFF
                194. **Text**: `⏎⏎[Attachment NOT uploaded to Notion. Notion said: [UploadMsg]. The original file was saved to iCloud Drive/Shortcuts/SecondBrain/Outbox/files.]`
                195. **Set Variable** `AttachNote` to [Text from step 194]
            196. **End If**
            197. **Text**: `[NoteBlock]Shared file: [FName]⏎Shared type: [ItemType][AttachNote]`
            198. **Set Variable** `RawText` to [Text from step 197]
            199. **Comment**: --- Send one record to Everything (Capture Source = Shared from App) ---
            200. **Replace Text** in [FName]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
            201. **Replace Text** in [Updated Text from step 200]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
            202. **Replace Text** in [Updated Text from step 201]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
            203. **Replace Text** in [Updated Text from step 202]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
            204. **Replace Text** in [Updated Text from step 203]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
            205. **Replace Text** in [Updated Text from step 204]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
            206. **Set Variable** `eTitle` to [Updated Text from step 205]
            207. **Replace Text** in [RawText]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
            208. **Replace Text** in [Updated Text from step 207]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
            209. **Replace Text** in [Updated Text from step 208]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
            210. **Replace Text** in [Updated Text from step 209]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
            211. **Replace Text** in [Updated Text from step 210]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
            212. **Replace Text** in [Updated Text from step 211]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
            213. **Set Variable** `eRaw` to [Updated Text from step 212]
            214. **Match Text**: pattern `(?:\\.|[^\\]){1,900}` in [eRaw] (Case Sensitive ON)
            215. **Set Variable** `Chunks` to [Matches from step 214]
            216. **Text**: `no`
            217. **Set Variable** `Overflow` to [Text from step 216]
            218. **Text** (leave empty)
            219. **Set Variable** `OverflowNote` to [Text from step 218]
            220. **Count** Items in [Matches from step 214]
            221. **If** [Count from step 220] is greater than `95`
                222. **Get Item from List**: Items in Range 1 to 95 of [Matches from step 214]
                223. **Set Variable** `Chunks` to [Items in Range from step 222]
                224. **Text**: `yes`
                225. **Set Variable** `Overflow` to [Text from step 224]
                226. **Text**: `"}},{"type":"text","text":{"content":"\n\n[Capture truncated at about 85,000 characters to fit Notion. The full text is kept in iCloud Drive/Shortcuts/SecondBrain/Outbox.]`
                227. **Set Variable** `OverflowNote` to [Text from step 226]
            228. **End If**
            229. **Combine Text** [Chunks] with Custom separator `"}},{"type":"text","text":{"content":"`
            230. **Set Variable** `RawPieces` to [Combined Text from step 229]
            231. **Text** (leave empty)
            232. **Set Variable** `Opt` to [Text from step 231]
            233. **If** [AttachID] has any value
                234. **Text**: `[Opt],"Attachments":{"files":[{"type":"file_upload","file_upload":{"id":"[AttachID]"}}]}`
                235. **Set Variable** `Opt` to [Text from step 234]
            236. **End If**
            237. **Text**: `{"parent":{"type":"data_source_id","data_source_id":"923ba32e-04e8-4c61-bf44-43093e061c0a"},"properties":{"Name":{"title":[{"type":"text","text":{"content":"[TestPrefix][eTitle]"}}]},"Raw Capture":{"rich_text":[{"type":"text","text":{"content":"[RawPieces][OverflowNote]"}}]},"Capture Source":{"select":{"name":"Shared from App"}},"AI Triage":{"select":{"name":"Needs AI"}}[Opt]}}`
            238. **Set Variable** `Body` to [Text from step 237]
            239. **Date** (Current Date)
            240. **Format Date** [Date from step 239] — Custom format `yyyyMMdd-HHmmss`
            241. **Random Number** between 1000 and 9999
            242. **Set Name** of [Body] to `capture-[Formatted Date from step 240]-[Random Number from step 241].json`
            243. **Save File** [Renamed Item from step 242] — Ask Where to Save OFF, Subpath `SecondBrain/Outbox/`, Overwrite OFF
            244. **Set Variable** `OutboxFile` to [Saved File from step 243]
            245. **Text**: `pending`
            246. **Set Variable** `SendStatus` to [Text from step 245]
            247. **Repeat** 3 times
                248. **If** [SendStatus] is `pending`
                    249. **Get Contents of URL** `https://api.notion.com/v1/pages` — Method **POST**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`, `Content-Type` = `application/json`; Request Body **File** = [Body]
                    250. **Set Variable** `Response` to [Contents of URL from step 249]
                    251. **Get Dictionary Value**: Value for key `object` in [Contents of URL from step 249]
                    252. **If** [Dictionary Value from step 251] is `page`
                        253. **Text**: `done`
                        254. **Set Variable** `SendStatus` to [Text from step 253]
                    255. **Otherwise**
                        256. **Get Dictionary Value**: Value for key `code` in [Contents of URL from step 249]
                        257. **Set Variable** `ErrCode` to [Dictionary Value from step 256]
                        258. **Text**: `|rate_limited|internal_server_error|service_unavailable|gateway_timeout|conflict_error|`
                        259. **If** [Text from step 258] contains `|[ErrCode]|`
                            260. **Wait** 3 seconds
                        261. **Otherwise**
                            262. **Text**: `fatal`
                            263. **Set Variable** `SendStatus` to [Text from step 262]
                        264. **End If**
                    265. **End If**
                266. **End If**
            267. **End Repeat**
            268. **If** [SendStatus] is `done`
                269. **If** [Overflow] is `no`
                    270. **Delete Files** [OutboxFile] (Confirm Before Deleting OFF)
                271. **End If**
                272. **Show Notification**: title `✅ Saved to Second Brain`, body `[TestPrefix][FName]`
            273. **Otherwise**
                274. **Get Dictionary Value**: Value for key `message` in [Response]
                275. **Set Variable** `ErrMessage` to [Dictionary Value from step 274]
                276. **Copy to Clipboard**: [RawText]
                277. **Show Alert**: title `⚠️ Not saved to Notion`, message `Notion said: [ErrMessage] ([ErrCode])⏎⏎Nothing is lost: the capture was copied to your clipboard and saved in iCloud Drive › Shortcuts › SecondBrain › Outbox.` (Show Cancel Button OFF)
            278. **End If**
        279. **Otherwise**
            280. **Add to Variable** `TextItems`: [Item]
        281. **End If**
    282. **End Repeat**
    283. **Comment**: Text, links, web pages, maps, products, recipes, etc. shared together become ONE record.
    284. **If** [TextItems] has any value
        285. **Repeat with Each** item in [TextItems]
            286. **Set Variable** `Item` to [Repeat Item]
            287. **Get Type** of [Item]
            288. **If** [Type from step 287] is `Safari web page`
                289. **Get Details of Safari Web Page**: `Name` of [Item]
                290. **Set Variable** `PageTitle` to [Name from step 289]
                291. **Get Details of Safari Web Page**: `Page URL` of [Item]
                292. **Set Variable** `SrcURL` to [Page URL from step 291]
                293. **Get Details of Safari Web Page**: `Page Selection` of [Item]
                294. **Text**: `Safari`
                295. **Set Variable** `App` to [Text from step 294]
                296. **Text**: `Title: [PageTitle]⏎URL: [SrcURL]⏎⏎[Page Selection from step 293]`
                297. **Add to Variable** `Parts`: [Text from step 296]
            298. **Otherwise**
                299. **Get Text from Input**: [Item]
                300. **Add to Variable** `Parts`: [Text from step 299]
                301. **If** [SrcURL] does not have any value
                    302. **Get URLs from Input**: [Item]
                    303. **If** [URLs from step 302] has any value
                        304. **Get Item from List**: First Item of [URLs from step 302]
                        305. **Set Variable** `SrcURL` to [Item from List from step 304]
                    306. **End If**
                307. **End If**
            308. **End If**
        309. **End Repeat**
        310. **Combine Text** [Parts] with Custom separator `⏎⏎`
        311. **Text**: `[NoteBlock][Combined Text from step 310]`
        312. **Set Variable** `RawText` to [Text from step 311]
        313. **If** [PageTitle] has any value
            314. **Set Variable** `TitleText` to [PageTitle]
        315. **Otherwise**
            316. **Text**: `Shared item`
            317. **Set Variable** `TitleText` to [Text from step 316]
            318. **Match Text**: pattern `^\S+(?:[ \t]+\S+){0,7}` in [Combined Text from step 310] (Case Sensitive ON)
            319. **If** [Matches from step 318] has any value
                320. **Get Item from List**: First Item of [Matches from step 318]
                321. **Set Variable** `TitleText` to [Item from List from step 320]
            322. **End If**
        323. **End If**
        324. **Comment**: --- Send one record to Everything (Capture Source = Shared from App) ---
        325. **Replace Text** in [TitleText]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
        326. **Replace Text** in [Updated Text from step 325]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
        327. **Replace Text** in [Updated Text from step 326]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
        328. **Replace Text** in [Updated Text from step 327]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
        329. **Replace Text** in [Updated Text from step 328]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
        330. **Replace Text** in [Updated Text from step 329]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
        331. **Set Variable** `eTitle` to [Updated Text from step 330]
        332. **Replace Text** in [RawText]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
        333. **Replace Text** in [Updated Text from step 332]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
        334. **Replace Text** in [Updated Text from step 333]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
        335. **Replace Text** in [Updated Text from step 334]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
        336. **Replace Text** in [Updated Text from step 335]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
        337. **Replace Text** in [Updated Text from step 336]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
        338. **Set Variable** `eRaw` to [Updated Text from step 337]
        339. **Match Text**: pattern `(?:\\.|[^\\]){1,900}` in [eRaw] (Case Sensitive ON)
        340. **Set Variable** `Chunks` to [Matches from step 339]
        341. **Text**: `no`
        342. **Set Variable** `Overflow` to [Text from step 341]
        343. **Text** (leave empty)
        344. **Set Variable** `OverflowNote` to [Text from step 343]
        345. **Count** Items in [Matches from step 339]
        346. **If** [Count from step 345] is greater than `95`
            347. **Get Item from List**: Items in Range 1 to 95 of [Matches from step 339]
            348. **Set Variable** `Chunks` to [Items in Range from step 347]
            349. **Text**: `yes`
            350. **Set Variable** `Overflow` to [Text from step 349]
            351. **Text**: `"}},{"type":"text","text":{"content":"\n\n[Capture truncated at about 85,000 characters to fit Notion. The full text is kept in iCloud Drive/Shortcuts/SecondBrain/Outbox.]`
            352. **Set Variable** `OverflowNote` to [Text from step 351]
        353. **End If**
        354. **Combine Text** [Chunks] with Custom separator `"}},{"type":"text","text":{"content":"`
        355. **Set Variable** `RawPieces` to [Combined Text from step 354]
        356. **Text** (leave empty)
        357. **Set Variable** `Opt` to [Text from step 356]
        358. **Replace Text** in [SrcURL]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
        359. **Replace Text** in [Updated Text from step 358]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
        360. **Replace Text** in [Updated Text from step 359]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
        361. **Replace Text** in [Updated Text from step 360]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
        362. **Replace Text** in [Updated Text from step 361]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
        363. **Replace Text** in [Updated Text from step 362]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
        364. **Set Variable** `eURL` to [Updated Text from step 363]
        365. **If** [eURL] has any value
            366. **Count** Characters in [eURL]
            367. **If** [Count from step 366] is greater than `2000`
                368. **Comment**: Too long for Notion's URL property; it is still inside Raw Capture.
            369. **Otherwise**
                370. **Text**: `[Opt],"Source URL":{"url":"[eURL]"}`
                371. **Set Variable** `Opt` to [Text from step 370]
            372. **End If**
        373. **End If**
        374. **Replace Text** in [App]: find `\\` replace with `\\\\` (Regular Expression **ON**, Case Sensitive ON) — every backslash → two backslashes
        375. **Replace Text** in [Updated Text from step 374]: find `"` replace with `\\"` (Regular Expression **ON**, Case Sensitive ON) — every " → \"
        376. **Replace Text** in [Updated Text from step 375]: find `\r` replace with `\\r` (Regular Expression **ON**, Case Sensitive ON) — carriage returns → \r
        377. **Replace Text** in [Updated Text from step 376]: find `\n` replace with `\\n` (Regular Expression **ON**, Case Sensitive ON) — line breaks → \n
        378. **Replace Text** in [Updated Text from step 377]: find `\t` replace with `\\t` (Regular Expression **ON**, Case Sensitive ON) — tabs → \t
        379. **Replace Text** in [Updated Text from step 378]: find `[\x00-\x08\x0B\x0C\x0E-\x1F]` replace with ` ` (Regular Expression **ON**, Case Sensitive ON) — other invisible control characters → space
        380. **Set Variable** `eApp` to [Updated Text from step 379]
        381. **If** [eApp] has any value
            382. **Text**: `[Opt],"Source app":{"rich_text":[{"type":"text","text":{"content":"[eApp]"}}]}`
            383. **Set Variable** `Opt` to [Text from step 382]
        384. **End If**
        385. **Text**: `{"parent":{"type":"data_source_id","data_source_id":"923ba32e-04e8-4c61-bf44-43093e061c0a"},"properties":{"Name":{"title":[{"type":"text","text":{"content":"[TestPrefix][eTitle]"}}]},"Raw Capture":{"rich_text":[{"type":"text","text":{"content":"[RawPieces][OverflowNote]"}}]},"Capture Source":{"select":{"name":"Shared from App"}},"AI Triage":{"select":{"name":"Needs AI"}}[Opt]}}`
        386. **Set Variable** `Body` to [Text from step 385]
        387. **Date** (Current Date)
        388. **Format Date** [Date from step 387] — Custom format `yyyyMMdd-HHmmss`
        389. **Random Number** between 1000 and 9999
        390. **Set Name** of [Body] to `capture-[Formatted Date from step 388]-[Random Number from step 389].json`
        391. **Save File** [Renamed Item from step 390] — Ask Where to Save OFF, Subpath `SecondBrain/Outbox/`, Overwrite OFF
        392. **Set Variable** `OutboxFile` to [Saved File from step 391]
        393. **Text**: `pending`
        394. **Set Variable** `SendStatus` to [Text from step 393]
        395. **Repeat** 3 times
            396. **If** [SendStatus] is `pending`
                397. **Get Contents of URL** `https://api.notion.com/v1/pages` — Method **POST**; Headers: `Authorization` = `Bearer [Token]`, `Notion-Version` = `2025-09-03`, `Content-Type` = `application/json`; Request Body **File** = [Body]
                398. **Set Variable** `Response` to [Contents of URL from step 397]
                399. **Get Dictionary Value**: Value for key `object` in [Contents of URL from step 397]
                400. **If** [Dictionary Value from step 399] is `page`
                    401. **Text**: `done`
                    402. **Set Variable** `SendStatus` to [Text from step 401]
                403. **Otherwise**
                    404. **Get Dictionary Value**: Value for key `code` in [Contents of URL from step 397]
                    405. **Set Variable** `ErrCode` to [Dictionary Value from step 404]
                    406. **Text**: `|rate_limited|internal_server_error|service_unavailable|gateway_timeout|conflict_error|`
                    407. **If** [Text from step 406] contains `|[ErrCode]|`
                        408. **Wait** 3 seconds
                    409. **Otherwise**
                        410. **Text**: `fatal`
                        411. **Set Variable** `SendStatus` to [Text from step 410]
                    412. **End If**
                413. **End If**
            414. **End If**
        415. **End Repeat**
        416. **If** [SendStatus] is `done`
            417. **If** [Overflow] is `no`
                418. **Delete Files** [OutboxFile] (Confirm Before Deleting OFF)
            419. **End If**
            420. **Show Notification**: title `✅ Saved to Second Brain`, body `[TestPrefix][TitleText]`
        421. **Otherwise**
            422. **Get Dictionary Value**: Value for key `message` in [Response]
            423. **Set Variable** `ErrMessage` to [Dictionary Value from step 422]
            424. **Copy to Clipboard**: [RawText]
            425. **Show Alert**: title `⚠️ Not saved to Notion`, message `Notion said: [ErrMessage] ([ErrCode])⏎⏎Nothing is lost: the capture was copied to your clipboard and saved in iCloud Drive › Shortcuts › SecondBrain › Outbox.` (Show Cancel Button OFF)
        426. **End If**
    427. **End If**
428. **End If**

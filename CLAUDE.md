# Lateral — project brief

Single-file, AI-driven narrative game. **The whole game is `index.html`** (one HTML
file with inline `<style>` + `<script>`). No build step, no framework, vanilla JS.
It calls the OpenAI API (user's key, stored in `localStorage`) to generate the story.

- **Repo:** `~/Projects/lateral` → GitHub `melkins1324/lateral`
- **Live:** https://melkins1324.github.io/lateral/ (GitHub Pages serves `index.html` from `main`)
- **Owner:** Matthew (non-technical; builds by talking). Wants blunt, no-yes-man feedback.

## The concept
One week in October 1937 (fictional-but-historical NYC, World Series). The player
inhabits any character, moves *laterally* between them, and time flows on one shared
clock. No main/minor characters — everyone has a full inner life. A German-American
Bund false-flag at Game 7 is the hidden spine. Empathy + perspective is the point.

## Design principles (do not violate)
- **Freedom, never a rail.** The storyline is a *gentle current*: nudge, never
  railroad, never invent a contrivance to force the player back. They can always go
  anywhere. (See `storyDirector()`.)
- **Truth belongs in code, not prompt-pleas.** Things that MUST be consistent (the
  Series score, who's dead, the phase) are derived/enforced in code, not begged for
  in the prompt. The baseball enforcer (`seriesState`/`baseballViolation`/
  `enforceBaseball`) is the template for this pattern.
- **Economy over fluff.** Beats must ADVANCE (a change every beat); no atmosphere for
  its own sake, no aimless banter.
- **No foreboding in the buildup.** Tue–Wed the surface stays ordinary; the plot moves
  off-page. Dread is earned Thursday+.

## Architecture map (search these names in index.html)
- **World clock:** `DAYS`/`PERIODS`, `clockIndex`, `parseClock`, `advanceWorldClock`.
- **Baseball truth (enforced):** `seriesState(day)`, `baseballViolation`, `enforceBaseball`.
- **Story director (the current):** `storyDirector(char)` → injected into forward beats.
- **Facts:** `addFact` (kind: canon|soft, fate flag), `factsForPrompt` (prioritized + capped at 30), `migrateFacts`.
- **Generation:** `generateBeat` (main), `generateBridge` (character-switch handoff),
  `generateSkip`, `generatePrelude`, memory generators. All hit OpenAI `gpt-4o`.
- **Switching:** `selectChar` (rail), `jumpTo` (in-scene). Both cross the bridge.
- **Naming (perspectival):** `knownAs`/`nameKnown`/`earnName` — you only know a name if your character would.
- **Also:** per-character `generateTheme` + "hidden mickeys"; stamina; permanent fate (dead/imprisoned/hospitalized); ripples; connections. World state is `W`, saved to `localStorage` key `lateral_v7`.

## Dev workflow
1. Edit `index.html`.
2. Validate JS (no node on this Mac — use JavaScriptCore):
   ```
   cd ~/Projects/lateral && python3 -c "import re;open('/tmp/j.js','w').write('\n;\n'.join(re.findall(r'<script>(.*?)</script>',open('index.html').read(),re.S)))" && osascript -l JavaScript -e "ObjC.import('Foundation');var s=$.NSString.stringWithContentsOfFileEncodingError('/tmp/j.js',$.NSUTF8StringEncoding,null).js;try{new Function(s);'JS OK'}catch(e){'ERR: '+e.message}"
   ```
3. Ship: `git add -A && git commit -m "…" && git push` → Pages rebuilds in ~1–2 min.

## Keeping sessions cheap
- Start a **fresh, focused session per task**; don't continue giant threads.
- Give a **specific symptom** ("vendor contradicts himself on the 2nd beat") so only the
  relevant ~40 lines get read, not the whole file.
- **Avoid workflows/ultracode** for routine edits — they spawn many agents and burn huge usage.

## Open items (not yet done)
- Concrete bugs from the audit: duplicate character on name-collision; orphaned
  protagonist when the LLM returns the active character inside its own `people[]`.
- Deep prompt de-bloat (`generateBeat` system prompt is ~10k tokens, redundant).
- Decision: real 1937 Series was Yankees 4–1 (no Game 6/7). Keep real teams, or fictionalize?

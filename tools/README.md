# tools/audit_save.py — free playthrough auditor

Scans an exported save for the exact bugs we've caught by hand: banned/foreboding
prose, softened violence ("he fired but they were unharmed"), descriptor text leaking
into a character's real name, duplicate/reused names, impossible baseball references
(sweep, Game 8, a Series champion), and time moving backward in a thread. Zero AI cost.

Baseball and naming checks are copied verbatim from the rules in `index.html`'s own
system prompt, so this audit can't drift from what the game actually enforces — if you
change those rules there, update the matching constants here.

## Export your save
In the live game, open the browser's JS console and run:
```js
copy(localStorage.getItem('lateral_v7'))
```
Paste the clipboard into a file (e.g. `tools/my_save.json`).

## Run it
```bash
python3 tools/audit_save.py tools/my_save.json
```

## Self-test (no save needed)
```bash
python3 tools/audit_save.py tools/fixtures/sample_bad.json    # should report ~7-8 findings
python3 tools/audit_save.py tools/fixtures/sample_clean.json  # should report none
```

## What it does NOT catch
This is pattern-matching, not comprehension — it's a floor, not a ceiling:
- Whether a beat is actually *boring* or fails to advance the story
- Whether a dropped thread (an `opens` item never followed up) is a real miss or just
  a thread the player chose not to pursue
- Prose quality, moral complexity, whether stakes land — anything that needs judgment

For that, there's no substitute for actually playing it (or the headless-script /
browser-playthrough options discussed with Claude).

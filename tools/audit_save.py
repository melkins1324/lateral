#!/usr/bin/env python3
"""
Lateral save-file auditor.

Scans an exported `lateral_v7` save (the game's localStorage world state) for the
exact failure classes the owner has been catching by hand during manual playtesting:
banned/foreboding prose clichés, softened-violence language, descriptor text leaking
into a character's realName (the naming cross-wire bug), reused names across distinct
people, impossible baseball/Series references, and day/time moving backward.

Zero AI cost — pure pattern matching against beats you already generated. The baseball
and naming checks are copied verbatim from the rules actually enforced in index.html,
so this stays in lockstep with the live game instead of drifting from it.

USAGE:
    python3 tools/audit_save.py path/to/save.json

To export your save: open the live game, open the browser's JS console, run:
    copy(localStorage.getItem('lateral_v7'))
...then paste the clipboard contents into a file and point this script at it.
"""
import json
import re
import sys
from collections import defaultdict

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
PERIODS = ['morning', 'afternoon', 'evening', 'night']

# ── Verbatim from index.html's system prompt — keep these phrases in lockstep ──
BANNED_PHRASES = [
    "heart pounding", "heart racing", "pulse quickened",
    "weight of what he'd done", "weight of what she'd done", "the gravity of the moment",
    "the weight of the street", "the weight of the city", "the weight of the world",
    "cold sweat", "sweat trickled",
    "metal meets bone", "metal collided with flesh",
    "sirens blared",
    "the silence was deafening", "the silence was louder than any shout",
    "his mind raced", "her mind raced",
    "shockwaves through his spine", "shockwaves through her spine",
    "a shiver up his spine", "a shiver down his spine", "a shiver up her spine", "a shiver down her spine",
    "a shiver of something nameless",
    "a defiance in his eyes", "a wariness in his eyes", "a coldness in his eyes",
    "a defiance in her eyes", "a wariness in her eyes", "a coldness in her eyes",
    "the realization dawning",
    "couldn't shake the feeling", "couldn't shake the sense", "couldn't quite place", "something felt off",
    "the air hummed with", "the air buzzed with", "thick with tension",
    "a sense of foreboding", "expectant silence", "the city held its breath", "an undercurrent of unease",
    "each face a potential secret", "too efficient, almost rehearsed", "as if nothing were amiss",
]

# Consequence-softening: a violence/harm verb within ~12 words of a "but they're fine" phrase.
VIOLENCE_VERBS = r'(?:shot|shoots|shooting|fired|firing|punch(?:ed|es|ing)?|stabb?(?:ed|ing)?|struck|striking|hit|hitting)'
HARM_NEGATORS = r'(?:unharmed|unscathed|otherwise fine|no real harm|nothing serious|they\'?ll be fine|he\'?ll be fine|she\'?ll be fine|barely a scratch|just a scare|missed (?:him|her|them)|didn\'?t (?:hit|connect|land))'
SOFTENING_PATTERNS = [
    re.compile(rf'\b{VIOLENCE_VERBS}\b.{{0,100}}?\b{HARM_NEGATORS}\b', re.I),
    re.compile(rf'\b{HARM_NEGATORS}\b.{{0,100}}?\b{VIOLENCE_VERBS}\b', re.I),
]

# Baseball — copied verbatim from `function baseballViolation` in index.html.
def baseball_violation(text):
    t = (text or '').lower()
    if re.search(r'\b4\s*[–-]\s*0\b|\b0\s*[–-]\s*4\b', t):
        return 'an impossible 4–0 Series score'
    if re.search(r'\bgame\s*(?:8|eight)\b|\beighth\s+game\b', t):
        return 'a nonexistent Game 8'
    if (re.search(r'\b(?:sweep|swept|sweeping)\b[^.]{0,30}\b(?:series|world series|world championship)\b', t)
            or re.search(r'\b(?:series|world series)\b[^.]{0,30}\b(?:sweep|swept|sweeping)\b', t)):
        return 'a Series sweep'
    if (re.search(r'\bwon the (?:world )?series\b|\b(?:world )?series (?:winner|title|crown|champ)', t)
            or re.search(r'\bchampions?\b[^.]{0,25}\bseries\b|\bseries\b[^.]{0,25}\bchampions?\b', t)):
        return 'a Series champion (there is none)'
    return None

# A realName that is a descriptor instead of a proper name — mirrors the rule's own examples.
DESCRIPTOR_RE = re.compile(
    r'^(the|a|an)\s|\b(vendor|guard|officer|sergeant|triplets|bystander|passerby|boy|girl|'
    r'man with|woman who|kid who|young man|young woman|old man|old woman)\b',
    re.I
)
# A proper name should look like "Firstname Lastname" (allow middle names/initials).
PROPER_NAME_RE = re.compile(r'^[A-Z][a-zA-Z.\'-]+(\s+[A-Z][a-zA-Z.\'-]+)+$')


def clock_index(day, period):
    d = DAYS.index(day) if day in DAYS else 1
    p = PERIODS.index(period) if period in PERIODS else 0
    return d * 4 + p


def parse_day_label(label):
    t = (label or '').lower()
    day = next((d for d in DAYS if d.lower() in t), None)
    if re.search(r'night|midnight|late', t):
        period = 'night'
    elif re.search(r'evening|dusk|sunset|dinner', t):
        period = 'evening'
    elif re.search(r'afternoon|noon|midday|lunch', t):
        period = 'afternoon'
    else:
        period = 'morning'
    return day, period


def find_phrases(text):
    t = (text or '').lower()
    return [p for p in BANNED_PHRASES if p in t]


def find_softening(text):
    t = text or ''
    return [pat.search(t).group(0) for pat in SOFTENING_PATTERNS if pat.search(t)]


def audit(save_path):
    with open(save_path, 'r', encoding='utf-8') as f:
        raw = f.read().strip()
    # Tolerate a devtools paste that includes the leading/trailing quotes some consoles add.
    if raw.startswith('"') and raw.endswith('"'):
        raw = json.loads(raw)
    W = json.loads(raw) if isinstance(raw, str) else raw

    chars = {c['id']: c for c in W.get('chars', [])}
    beats_by_char = W.get('beats', {})
    findings = defaultdict(list)  # category -> list of finding dicts
    name_registry = {}  # lowercased realName -> charId it belongs to (for cross-thread dup detection)

    for cid, char in chars.items():
        char_name = (char.get('realName') or char.get('name') or '').strip()
        if char_name:
            key = char_name.lower()
            if key in name_registry and name_registry[key] != cid:
                findings['duplicate_character_name'].append({
                    'name': char_name, 'char_ids': [name_registry[key], cid]
                })
            else:
                name_registry[key] = cid

        beats = beats_by_char.get(cid, [])
        last_clock = -1
        for i, beat in enumerate(beats):
            label = f"{char.get('name','?')} beat {i} ({beat.get('dayLabel','?')} {beat.get('time','')})".strip()
            prose = beat.get('prose', '') or ''

            if not prose and not beat.get('isBridge'):
                findings['missing_prose'].append({'where': label})

            phrases = find_phrases(prose)
            if phrases:
                findings['banned_phrase'].append({'where': label, 'phrases': phrases})

            softened = find_softening(prose)
            if softened:
                findings['softened_consequence'].append({'where': label, 'matches': softened})

            bviol = baseball_violation(prose)
            if bviol:
                findings['baseball_violation'].append({'where': label, 'issue': bviol, 'snippet': prose[:160]})

            # Day/time should never move backward within one character's thread.
            day, period = parse_day_label(beat.get('dayLabel'))
            if day:
                idx = clock_index(day, period)
                if idx < last_clock:
                    findings['time_regression'].append({
                        'where': label, 'prev_index': last_clock, 'this_index': idx
                    })
                last_clock = max(last_clock, idx)

            # people[] checks: descriptor-as-realName, self-naming, within-beat duplicates.
            seen_this_beat = {}
            for p in beat.get('people', []) or []:
                rn = (p.get('realName') or p.get('name') or '').strip()
                if not rn:
                    continue
                if DESCRIPTOR_RE.search(rn) or not PROPER_NAME_RE.match(rn):
                    findings['descriptor_as_realname'].append({'where': label, 'realName': rn, 'label': p.get('label', '')})
                if rn.lower() == char_name.lower():
                    findings['self_named_in_people'].append({'where': label, 'realName': rn})
                if rn.lower() in seen_this_beat and seen_this_beat[rn.lower()] != p.get('role'):
                    findings['duplicate_name_in_beat'].append({'where': label, 'realName': rn})
                seen_this_beat[rn.lower()] = p.get('role')

    return findings


def report(findings):
    if not any(findings.values()):
        print("✅ No issues detected. (Pattern-matching only — this is a floor, not a ceiling. Play it too.)")
        return
    order = [
        ('baseball_violation', 'Baseball/Series impossibilities'),
        ('softened_consequence', 'Softened consequences (violence that \"doesn\'t count\")'),
        ('self_named_in_people', 'Protagonist listed in their own people[] (orphan bug)'),
        ('descriptor_as_realname', 'Descriptor text leaking into realName (naming cross-wire)'),
        ('duplicate_name_in_beat', 'Same name used for two different roles in one beat'),
        ('duplicate_character_name', 'Same character name registered under two different IDs'),
        ('time_regression', 'Day/time moved backward within a thread'),
        ('banned_phrase', 'Banned cliché / foreboding-register phrases'),
        ('missing_prose', 'Beats with empty prose'),
    ]
    total = 0
    for key, title in order:
        items = findings.get(key, [])
        if not items:
            continue
        total += len(items)
        print(f"\n### {title}  ({len(items)})")
        for it in items[:25]:
            print("  -", it)
        if len(items) > 25:
            print(f"  ... and {len(items) - 25} more")
    print(f"\n{total} total finding(s).")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    report(audit(sys.argv[1]))

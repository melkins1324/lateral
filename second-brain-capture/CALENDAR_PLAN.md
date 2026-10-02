# Phase 4: calendar integration plan (NOT ACTIVE, needs your approval)

Nothing here has been built or switched on. No calendar has been touched.

## What I found

- **No calendar connector with write access** is connected to this session.
- Notion search returned an event from **Notion Calendar** linked to your Google account
  (`melkins1324@gmail.com`). So your calendar is most likely **Google Calendar**, already
  connected to Notion Calendar.
- Wispr Flow has read-only calendar access, which is no use for creating events.

## Options

| | How | Pros | Cons |
|---|---|---|---|
| **A. Google Calendar sync script on your Mac** (recommended) | A small Python script, run by `launchd` every 15 minutes, queries Everything and creates Google Calendar events through the Google API (OAuth, `calendar.events` scope only) | Full control. Real `External Event ID` and `Calendar Link`. Strong duplicate protection. No server | One-time Google OAuth setup. Only runs while the Mac is awake |
| B. Notion Calendar display only | Add the Everything database to Notion Calendar | Zero code, instant | Items appear in Notion Calendar only, not in Google Calendar. Doesn't fill External Event ID or Link |
| C. iPhone Shortcuts automation to Apple Calendar | Hourly personal automation: query Notion, then "Add New Event" | No OAuth | Shortcuts can't return a reliable event ID or link, so duplicate protection is weaker |

## How option A would behave (one-way, Notion → calendar)

**Eligible only when all of these hold** (checked in the Notion query, then again in code):
`Type` is Event or Reminder · `Date` is present and valid · `Calendar Sync` is empty or
"Not Synced" · `External Event ID` is empty · `AI Triage` isn't "Human Review".

**Creating an event**
- Title = `Name` (with any `[INTEGRATION TEST] ` prefix kept, so tests stay obvious).
- Time:
  - **Date only** → all-day event.
  - **Date with a start and end** → exactly that range.
  - **Date with a start time but no end** → a documented default length (proposed: 60 minutes for Events, 15 minutes for Reminders). Needs your approval.
- Timezone: the one Notion stores. If there isn't one, your timezone (proposed America/Los_Angeles, to confirm).
- Description = `Details` (plain text, trimmed), the Notion page link, and the Place name if a Places relation exists.
- **No attendees, and `sendUpdates=none`**, so nobody is ever invited or notified.
- Reminders get a popup notification at the start time.

**After success:** set `External Event ID` = the Google event ID, `Calendar Link` = the event's
link, and `Calendar Sync` = Synced.
**After failure:** set `Calendar Sync` = Error, and write one line to a local log (no secrets)
with the page ID and Google's error.

**Duplicate prevention (two layers)**
1. Each Google event carries the Notion page ID in a private property. Before creating an
   event, the script checks whether one with that page ID already exists. If it does, the
   script just repairs the Notion fields.
2. Notion's `External Event ID` and `Calendar Sync` exclude the item from future runs.

**Permissions this would add**
- Notion: the integration needs **Update content**, to write the three calendar fields. That's
  more than capture needs, so it's off today.
- Google: the `calendar.events` scope only, stored in the macOS Keychain.

No two-way sync. Editing or deleting the Notion item later won't change the calendar event
until you ask for that as a later phase.

## Decisions I need from you

1. **Which calendar account and which calendar** should receive events? For example, your
   Google account's main calendar, or a separate "Second Brain" calendar (safer to start with).
2. **Option A, B or C?**
3. **Default length** for timed items with no end: 60 minutes for Events and 15 for Reminders, or something else?
4. **Timezone** to assume when a Date has none: America/Los_Angeles?
5. Is it OK to turn on **Update content** for the integration when we activate this?

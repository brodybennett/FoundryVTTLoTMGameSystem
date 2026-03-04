# LoTM Sheet Review Checklist

Use this checklist for every sheet milestone review.

## Test Preconditions

Run visual QA only when Foundry reports a usable viewport of at least `1024x768`.
If Foundry shows a minimum-dimensions warning due to browser/OS zoom, correct that first
before logging sheet UX defects.

## Required Screenshot Bundle

Capture and provide all of the following:

1. Full-sheet screenshot on first open.
2. Header and primary action area close-up.
3. Each tab at least once.
4. One invalid state (showing inline errors and blocker summary).
5. One successful interaction state (for example: valid roll/chat output or successful drag/drop tab placement).
6. Narrow-width view screenshot.

## Manual Test Script

Run in this order:

1. Open sheet by double-click from sidebar.
2. Open same document from compendium by double-click.
3. Edit at least one field in each tab and save.
4. Trigger at least one validation error intentionally.
5. Resolve validation and confirm save succeeds.
6. Run each visible primary action button once.
7. Confirm no silent failures and no stuck UI state.
8. Check browser console for errors.

## Character Actor Addendum

1. Confirm no Character Creation wizard/finalize panel appears.
2. Drag `pathway` item and confirm class/pathway presentation updates.
3. Drag `sequenceNode` item and confirm sequence badge/identity sync updates.
4. Delete pathway/sequence items and confirm identity auto-clears/syncs.
5. Drag `ability` and `ritual` items and confirm both appear in `Spells`.
6. Drag inventory item types and confirm section placement in `Inventory`.
7. Add/remove favorites and confirm sidebar list updates.

## Item Sheet Addendum

1. Verify visible fields match item subtype.
2. Verify irrelevant subtype sections are hidden.
3. Add and remove effect rows.
4. Validate tags/dependencies CSV editing.
5. Confirm create/update errors are user-readable.

## Feedback Packet Format

Provide:

1. Screenshot bundle.
2. 3-8 bullet notes describing confusion/noise/friction.
3. First red console error stack trace (if any).

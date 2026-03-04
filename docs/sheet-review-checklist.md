# LoTM Sheet Review Checklist

Use this checklist for every sheet milestone review.

## Required Screenshot Bundle

Capture and provide all of the following:

1. Full-sheet screenshot on first open.
2. Header and primary action area close-up.
3. Each tab at least once.
4. One invalid state (showing inline errors and blocker summary).
5. One successful completion state (for example: finalize success or valid save).
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

1. Move through creation steps using `Previous` and `Next`.
2. Confirm invalid step blocks progression.
3. Confirm finalize is blocked with clear reason when invalid.
4. Confirm finalize succeeds when valid.
5. Confirm imported pathway package behavior is clear.

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

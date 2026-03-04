# LoTM Sheet UX Rubric

This rubric is the quality gate for all LoTM sheet work. A sheet is not
"gold-standard ready" until every category passes.

## Scoring

- `PASS`: Meets all criteria in category.
- `FAIL`: Any criterion is missing, unclear, or inconsistent.

## Category 1: Information Hierarchy

Pass criteria:

- Critical identity info is visible in the header without tab switching.
- Primary actions are grouped and easy to locate.
- Secondary and advanced controls are separated from core flow controls.
- Related fields are grouped into clearly titled sections.
- Section order matches real user workflow.

## Category 2: Form Clarity and Labels

Pass criteria:

- Labels are explicit and unambiguous.
- Required inputs are clearly indicated.
- Validation limits (ranges/formats) are visible near inputs.
- Buttons use verb-first text (for example: `Finalize Character`).
- Empty fields and placeholders provide meaningful guidance.

## Category 3: Feedback and Error States

Pass criteria:

- Invalid data is surfaced inline in the relevant section.
- Blocking errors are summarized in one obvious location.
- Warnings are visually distinct from errors.
- Button actions never fail silently.
- User notifications are specific and actionable.

## Category 4: Interaction Safety

Pass criteria:

- Destructive actions require confirmation where appropriate.
- Save/update behavior is deterministic and predictable.
- Draft state is preserved when validation fails.
- Repeated action clicks do not create inconsistent state.

## Category 5: Responsiveness and Readability

Pass criteria:

- Layout remains readable at 100%, 125%, and 150% browser zoom.
- Layout remains usable at narrow sheet widths.
- No overlapping controls, clipped text, or inaccessible buttons.
- Dense sections still maintain clear spacing and visual separation.

## Category 6: Consistency Across Sheets

Pass criteria:

- Shared controls look and behave consistently.
- Similar concepts use identical labels.
- Typography, color usage, and spacing follow shared tokens/utilities.
- Tab structure and section framing feel coherent between sheet types.

## Category 7: Runtime Reliability

Pass criteria:

- Double-click open works for actor and item sheets.
- No console errors on open/edit/save flows.
- Actions that depend on APIs fail gracefully when unavailable.
- Existing validation/build scripts pass after changes.

## Approval Gate

A sheet is approved when:

1. All rubric categories pass.
2. Automated checks pass.
3. Manual review checklist passes.
4. User signoff is provided.

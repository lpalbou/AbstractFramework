# 0901 — AbstractCode web: delete the legacy `src/ui/app.tsx` and the files only it uses

> Package: abstractcode (web/src/ui)
> Type: improvement
> Created: 2026-09-26
> Priority: normal
> Labels: code-web, cleanup, dead-code
> Moved: `proposed/0901_…` → `planned/0901_…` on 2026-09-28 (wave-2 evidence: the legacy REPL was edited again in abstractcode `227e000`)

## Summary

Code web's entry point renders `CodeWorkspace` from `src/workspace/app`. The old UI,
`src/ui/app.tsx` (6,382 lines), is imported by nothing, yet it is type-checked, linted and read by a
hygiene test, and agents keep editing it by mistake (the About/capabilities work of 2026-09-26 left an
unused `capabilitiesOutcome` there before it was removed in `67a204a`). Delete it and the helpers
only it uses.

## Why

C1 report (67a204a: "`capabilitiesOutcome` removed"); B report B-consolidate ("`capabilitiesOutcome`
left unused for C1 to delete"). Dead code that looks live costs every future change to this app.

## Current code reality (2026-09-26; abstractcode `2baacf3`)

- `web/src/main.tsx` imports `CodeWorkspace` from `./workspace/app`; nothing imports `src/ui/app.tsx`.
- Only-used-by-the-legacy-app files: `src/ui/markdown_renderer.tsx`, `src/ui/tool_picker.tsx`,
  `src/ui/multi_select.tsx`, and their rules in `src/ui/styles.css` (grep 2026-09-26).
- `src/lib/dependency_hygiene.test.ts` l.144 reads `src/ui/app.tsx` as text (AgentCyclesPanel
  stylesheet check); `src/ui/*.test.ts(x)` (context_inspector_modal, styles, ui_kit_theme) must be
  checked for what they cover before deletion.
- `tsconfig.json` `"include": ["src"]` compiles the dead tree.

## Scope

### In scope

- Delete `src/ui/app.tsx` and every file reachable only from it; move or drop tests that only cover
  deleted code; point the hygiene test at `src/workspace/`.

### Out of scope

- Behaviour changes to the workspace app.

## Dependencies

- None.

## Expected outcomes

- `src/ui/` holds only code the running app uses (or disappears).

## Acceptance criteria

- [ ] `npm --prefix abstractcode/web test` and `vite build` green; bundle size not larger.
- [ ] A reachability check (e.g. `npx knip` or a grep from `main.tsx`) reports no unreachable module under `src/`.

## Validation

- `npm --prefix abstractcode/web test && npm --prefix abstractcode/web run build` (scratch HOME).

## Evidence

- `untracked/missions-2026-09-25/C1/REPORT.md` (67a204a)
- `untracked/missions-2026-09-25/B/REPORT.md` (B-consolidate)

## ADR status

- ADR impact: None.

## Receipts

- None yet.

## Status update 2026-09-28 (promoted to planned)

The wave-2 AbstractCode work had to change the legacy REPL again (`227e000`: it stopped sending the
client transcript as `context` and uses `use_session_history`) although no user reaches it, and the
0.7.0 tag gate listed its deletion as a follow-up. Current reality at abstractcode `227e000`
(crate 0.7.0, web 0.6.0):

- `web/src/ui/app.tsx` (6,368 lines) is still imported by nothing but `web/src/lib/dependency_hygiene.test.ts`.
- `web/src/lib/storage.ts` and `web/src/lib/run_input.ts` are imported only by `web/src/ui/app.tsx` (and tests).
- The CHANGELOG describes the legacy REPL's 0.6.0 change; its wording should say the legacy UI is removed once this lands.

Scope added: delete `storage.ts` and `run_input.ts` with `app.tsx` (after checking no test-only import keeps them alive),
and correct the CHANGELOG wording.

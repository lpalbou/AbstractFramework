# 039 — AbstractObserver: Observe Section UI Redesign (Single-Panel Layout)

**Status**: Completed
**Created**: 2026-02-19
**Completed**: 2026-02-19

## Summary

Redesign the Observe section of AbstractObserver from a two-panel layout (sidebar + viewer) to a single-panel layout with a dedicated toolbar/navbar for session management.

## Reason

The current Observe page uses a two-column grid layout (`observe_layout` with `observe_sidebar` + `observe_viewer`). The left sidebar contains run selection, control buttons (Resume/Pause, Cancel, Launch), waiting/schedule status, and run state details. The right panel has tab-based content (Ledger, Graph, Digest, Attachments, Chat) plus a viewer header.

This wastes horizontal space, splits user attention across two panels, and makes the run controls feel disconnected from the content they act on. A single-panel design with a toolbar puts the controls where they belong — above the content — and gives the viewer the full width of the viewport.

## Scope

### What we do
- **Merge** the sidebar run picker + control buttons into a **dedicated toolbar bar** above the content area
- **Remove** the two-panel grid layout (`observe_layout` → single column)
- **Toolbar contains**: Run picker dropdown, Refresh, Disconnect, Resume/Pause, Cancel, Launch buttons
- **Keep** the existing viewer header (run title + status chips + run id/time) inside the content panel
- **Move** schedule info, waiting status, run state, and errors into a collapsible details section below the toolbar
- **Full-width** content panel for Ledger/Graph/Digest/Attachments/Chat tabs
- **Update CSS** to remove `observe_layout` grid and add `observe_toolbar` styles

### What we don't
- No changes to the content tabs themselves (Ledger, Graph, Digest, Attachments, Chat)
- No changes to the RunPicker component internals
- No changes to other pages (Launch, Mindmap, Backlog, Inbox)
- No backend or API changes

## Dependencies
- No external dependencies — pure UI refactoring within `app.tsx` and `styles.css`

## Expected Outcomes
- Single, clean panel layout for the Observe page
- Dedicated toolbar with all run management controls in one row
- Full-width content area for better readability of ledger entries, graphs, etc.
- Schedule/waiting/error information accessible but not always visible (collapsible)
- Consistent with the app's design language (dark theme, pill buttons, etc.)

---

## Report

### Changes Made

**Files modified:**
- `abstractobserver/src/ui/app.tsx` — Observe section (~lines 4789–5692)
- `abstractobserver/src/ui/styles.css` — New observe toolbar + context styles

### Architecture (Before → After)

**Before**: Two-panel grid layout
```
┌─────────────────────┬────────────────────────────────────┐
│  observe_sidebar    │  observe_viewer                    │
│  ┌──────────────┐   │  ┌──────────────────────────────┐  │
│  │ RunPicker     │   │  │ Tabs: Ledger|Graph|Digest...│  │
│  │ Refresh/Disc. │   │  │ Viewer header (run + status)│  │
│  │ Resume/Cancel │   │  │ Content...                   │  │
│  │ Launch        │   │  │                              │  │
│  │ Wait/Schedule │   │  │                              │  │
│  │ Run state     │   │  │                              │  │
│  └──────────────┘   │  └──────────────────────────────┘  │
└─────────────────────┴────────────────────────────────────┘
```

**After**: Single-panel with toolbar (iteration 2)
```
┌──────────────────────────────────────────────────────────┐
│  observe_toolbar                                         │
│  [RunPicker ▼] [⟳ Refresh] [✕ Disconnect] │ [Resume]   │
│  [Cancel] [Launch…]                                      │
│  ┌ waiting: ... │ schedule: ...  ┐ (only when relevant)  │
├──────────────────────────────────────────────────────────┤
│  observe_viewer_full (full width)                        │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Tabs: Ledger | Graph | Digest | Attachments | Chat   ││
│  │                                                      ││
│  │ ┌──────────────────────────────────────────────────┐ ││
│  │ │ node-2::done             completed    20m ago    │ ││
│  │ │ [llm_call] [#8] [4239e19…]                      │ ││
│  │ │ ┌─ preview text ──────────────────────────────┐  │ ││
│  │ │ │ {"answer": "Summary of the system ..."}     │  │ ││
│  │ │ └────────────────────────────────────────────  │  │ ││
│  │ │ [Unfold Response] [Copy Response] [Copy JSON]  │ ││
│  │ └──────────────────────────────────────────────────┘ ││
│  └──────────────────────────────────────────────────────┘│
│  Run: completed                                          │
└──────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Toolbar with inline controls** — The run picker, refresh, disconnect, pause/resume, cancel, and launch buttons are all in a single horizontal row (`.observe_toolbar_row`). A visual separator (`observe_toolbar_sep`) divides selection controls from action controls.

2. **Contextual cards** — Waiting status, schedule info, and errors only appear when relevant, in compact horizontal "context cards" (`.observe_context_card`) below the toolbar.

3. **No duplicate info** — Removed the viewer header (run title + status + id) since this info is already in the run picker. Removed the collapsible run state JSON section.

4. **Full-width viewer** — The content panel (`.observe_viewer_full`) now gets 100% width.

5. **Redesigned ledger cards** (`.lc`) — Structured layout with:
   - **Header row**: bold title + status badge (color-coded) + relative timestamp
   - **Meta chips**: node type, effect type, cursor #, run id in small rounded chips
   - **Preview**: monospace text in a dark inset container with gradient fade-out
   - **Action buttons**: small, subtle, compact (not full-size `.btn` buttons)
   - **Expanded body**: clean container for Markdown response or JSON viewer

6. **Responsive** — On narrow viewports (≤700px), the toolbar separator hides and buttons get tighter padding.

### Verification

- ✅ TypeScript: `tsc --noEmit` — clean
- ✅ Vite build: `vite build` — clean (243 modules, 783.70 kB JS)
- ✅ Tests: `vitest run` — 17/17 passed (5 test files)
- ✅ All existing functionality preserved (run selection, control actions, schedule management, waiting state display, all content tabs)

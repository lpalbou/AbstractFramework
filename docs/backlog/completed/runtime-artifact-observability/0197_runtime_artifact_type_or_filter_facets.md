# Completed: Runtime artifact type OR filters and stable facets

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## ADR status
- Governing ADRs: ADR-0036
- ADR impact: None. This preserves the existing artifact descriptor/filter contract and fixes Observer consumption.

## Context
The Runtime Artifact Explorer supports multiple type chips such as Voice, Music, Markdown, HTML, JSON, Image, Video, Code, and Text. User testing showed that selecting Music made the other type counts drop to zero, which made the UI look like type filters combine with AND or like other artifacts disappeared.

## Current code reality
- `abstractgateway/src/abstractgateway/routes/gateway.py` already accepts comma- or pipe-separated `artifact_kind` values and matches any allowed value against semantic kind, render kind, or modality.
- `abstractgateway/tests/test_gateway_artifacts_endpoint.py` already covered `artifact_kind=music,voice`.
- `abstractobserver/src/ui/app.tsx` sends selected type filters as a comma-separated `artifact_kind` value, but it also used the filtered response facets to render all type chip counts.
- Because the selected response only contains selected kinds, unselected chip counts collapsed to zero even though they could be added to the OR set.

## Problem
The result query was compatible with OR, but the UI communicated the opposite. Users need to compose type filters such as Music + Markdown or Video + Text and still see the available counts for unselected types in the current scope/search/date.

## What we wanted to do
Keep the artifact result set filtered by the selected OR set, while rendering type chip counts from the same non-type scope/search/date filters.

## Requirements
- Multiple selected type chips combine with OR.
- Type chip counts remain useful when one or more type chips are active.
- Counts must still be server-backed stats, not local page counts.
- The UI should make OR behavior visible.

## Scope
- Observer Runtime Artifact Explorer type facet handling and chip labels.
- Gateway regression coverage for mixed-kind OR filtering.

## Non-goals
- Do not change artifact descriptor semantics.
- Do not introduce client-side count inference.
- Do not implement session/turn hierarchy or wait replay in this item.

## Completion report
- Added separate Observer `runtime_artifact_type_facets` state.
- When type filters are active, Observer now fetches artifact rows with the selected comma-separated `artifact_kind` and fetches a second stats-only view without `artifact_kind` for chip counts.
- Type chips now label the section as `Type OR` and expose accessible titles/labels explaining that type filters combine with OR.
- Added a Gateway regression for `artifact_kind=music,markdown` to verify mixed semantic/render kind filters return a union.

## Validation
- `python -m compileall -q abstractgateway/src/abstractgateway/routes/gateway.py`
- `cd abstractgateway && python -m pytest tests/test_gateway_artifacts_endpoint.py -q`
- `cd abstractobserver && npm test -- --run src/ui/artifact_rendering.test.ts src/ui/runtime_activity.test.ts`
- `cd abstractobserver && npm run build`
- `git diff --check`

## Guidance for future agents
If type chip counts regress again, check whether Observer is using typed-result facets for filter controls. The selected results and the available-type facet basis are intentionally separate.

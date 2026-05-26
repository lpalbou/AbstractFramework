# Backlog: SmartNote ingest overrides + attachment provenance

## Summary
Allow SmartNote gateway ingest to accept optional provider/model overrides and record attachment run provenance.

## Why
- Gateway defaults should be overridable for targeted provider/model testing.
- Attachment artifacts need consistent run provenance for traceability.

## Scope
### In scope
- Accept provider/model in SmartNote ingest tool + flow payloads.
- Persist artifact run id on local attachment storage.
- Document how to enable SmartNote tools.

### Out of scope
- UI/CLI changes.
- Gateway auth or tool approval policy changes.

## Dependencies
- SmartNote gateway tools and bundle workflows.

## Expected outcomes
- Ingest can use explicit provider/model when supplied.
- Attachments store `artifact_run_id` consistently.
- Docs note how to enable SmartNote tools.

## Full Report
- **Summary**: Added optional provider/model overrides to SmartNote ingest, captured attachment run provenance, and documented tool enablement.
- **Implementation**:
  - Accepted `provider`/`model` in the ingest tool and flow payload and used overrides in gateway ingest.
  - Stored `artifact_run_id` for locally stored attachments.
  - Added SmartNote tool enablement instructions to the FAQ.
- **Tests**: Not run (not requested).

# 1025 — Cross-user READ is a principal privilege through gateway APIs, never a run's reach into other planes

> Package: abstractgateway, abstractruntime, abstractobserver (consumer)
> Type: feature
> Created: 2026-10-15
> Priority: normal
> Labels: governance, security, rbac, analytics, decision-gate, adversarial-review-required
> Track: governance (proposed; follows 1020/1021)

## Summary

OPERATOR DECISION GATE (never assignable). The operator asked (2026-10-15) whether a hard read-deny
on other users' data is optimal: "what if we want to do a study across users, or search for how a
resource has been used across users, or aggregated stats?" The comparative analysis
(`../planned/governance/evidence/CROSS-USER-READ-best-practices.md`, 51 references) answers: keep
the hard deny for RUN TOOLS (a run acting for Alice that reads Bob's files is the confused-deputy /
prompt-injection exfiltration path — OWASP LLM06 Excessive Agency), and make cross-user read a
PRINCIPAL privilege exercised through gateway APIs that know who asks, why, and log it — the way
Kubernetes (cluster-wide `view` roles over the API, never through a pod's disk), AWS (read-only
audit roles, organization trails), GitLab (the auditor user) and Vault (explicit read policies plus
audit devices) do it.

## Proposed direction

- **Role**: `auditor` (read-only across planes; two grades: metadata and content), grantable by an
  admin to humans AND digital users; admins keep read-only elsewhere (M4) and get `auditor` by
  default; entities get it only when granted.
- **APIs** (gateway, served from each archived or live plane through the same read paths, never the
  file tools): `GET /study/runs?tenant=&user=&workflow=&since=…` (rows with the requester/owner
  label), `GET /study/aggregate?metric=tokens|tools|artifacts&group_by=user|workflow|day` with a
  k-threshold for small groups, `GET /study/search?q=…` over ledgers/artifacts with per-row owner
  labels, `GET /study/runs/{plane}/{id}/ledger` (content grade only).
- **Purpose logging**: every content read carries a `purpose` field and fails if the audit append
  fails (Google Access Transparency / Microsoft Customer Lockbox pattern); the owner can see who read
  what ("read by admin for study X at …") on their own plane.
- **Exports** are artifacts in the requester's plane, labelled with the sources and the purpose.
- **Archived planes** (R5: nothing is deleted) are readable through the same endpoints.
- **Runs stay walled**: the hard deny from 1021 is unchanged; an agent that needs cross-user facts
  asks the gateway API as its principal with the principal's role, never the file system.

## Decision gates (operator)
1. Adopt the principle (run tools denied; principals read through APIs with a role)?
2. Default grants: admin = auditor content; entities = none unless granted; a per-tenant or per-gateway scope?
3. Aggregates: k-threshold (e.g. groups < 5 users suppressed) or raw?
4. Should owners be notified of content reads of their plane, or only able to look them up?

## Promotion criteria
- The four answers; then `planned/governance/1025_…`, runtime first if ledger reads need a cross-plane reader, gateway second, Observer third (a Study page).

## Validation ideas
- Alice's run cannot read Bob's plane through any tool (1021 tests stay red on removal); an auditor principal gets rows from both planes through `/study/*` with owner labels; a non-auditor gets 403; every content read lands one audit line with purpose; an export is an artifact in the auditor's plane.

## Receipts
- `../planned/governance/evidence/CROSS-USER-READ-best-practices.md` (comparison table, re-assessment, 51 references; 2026-10-15).

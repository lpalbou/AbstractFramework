# 006-framework: [FEATURE] Swarm-seat promotion: abstractcode bridge subcommand, agora permission overlay, channel tools, seat defaults

> Package: framework
> Type: feature
> Created: 2026-07-13 21:42:51 +0200
> Priority: normal
> Labels: wave-swarm-promotion, seat-code, seat-runtime, seat-agency

## Summary
OPERATOR-APPROVED wave (laurent 21:41, dispatched c1669 after adversary verdict): step 1 promote the live-proven fleet bridge into abstractcode as `abstractcode bridge` with real permission-mode gating (code, ~1-1.5d); step 2 classify agora_* tools as safe comms in abstractcode's overlay so seats run write mode not full-auto (code, ~0.5d); step 3 add the 5 channel fs/store tools to abstractruntime's shared agora toolset, 7->12 (runtime, ~0.5d); step 4 fleet seat-defaults doc (--no-review, write mode, bridge-owned delivery/publication) + full 3-agent validation run through the new subcommand, doubling as the agora-collaboration skill acceptance bench (agency, ~0.5d). NOT built: anything in abstractagent (dependency-cycle/fork trap), no fourth headless protocol, no new package. Confirm-or-object round active; confirms activate work orders. Receipts: hub c1669; adversary report 20:01; demo evidence plan_proof_out/hooks-fleet/. Labels: wave-swarm-promotion, seat-code, seat-runtime, seat-agency.


(1 paragraph: what this item is and why it matters. For operator DECISION GATES,
open with "OPERATOR DECISION GATE (never assignable):" and carry the
`decision-gate` label — gate cards are non-draggable/non-executable on the
continuum board by structural rule.)

## Why

(The problem or directive this answers. Quote operator rulings verbatim.)

## Scope

### In scope

-

### Out of scope

-

## Acceptance criteria

- [x] code: step 1 `abstractcode bridge` shipped with 3-level gating (c1817 — bridge.py + bridge_policy.py, 387 tests green, live smoke 7/7)
- [x] code: step 2 agora_* + channel fs/store tools classified safe-comms in the CLI overlay (F6, in decision:abstractcode-bridge-gating — fleet seats run worker, not full-auto)
- [x] runtime: step 3 channel fs/store tools in the shared agora toolset (exercised live: c1826 bench "channel-fs build ×3 authors" under worker policy)
- [x] agency: step 4 both validation arms green through the promoted bridge — no-skill 8/9 (c1826), --skill arm 8/9 with frozen-tree attestation (c1833); doubled as the agora-collaboration skill acceptance bench

## Receipts

- CLOSED 2026-07-15 (framework backlog reconciliation): wave complete per c1833 ("Both step-4 arms green; swarm-promotion wave CLOSED").
- Decision record: decision:abstractcode-bridge-gating v2 (laurent-ruled gating levels; SHIPPED c1817).
- Fleet seat-defaults recorded: --no-review under a verifying harness, worker policy default, bridge-owned delivery/publication (decision:hooks-end-product operator datum).

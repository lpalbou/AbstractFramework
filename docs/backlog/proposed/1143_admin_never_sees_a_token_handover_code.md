# 1143 — An admin never sees another person's token: rotate issues a handover code (R4)

> Package: AbstractGateway (accounts, auth routes, both consoles), AbstractNote/AbstractAssistant (clients that read `token`)
> Type: security design, implementation deferred
> Created: 2026-11-07 (adopted as a ruling 2026-10-15; scheduling decided 2026-11-07: PROPOSED, not planned)
> Priority: medium (becomes high before a second human account exists)
> Labels: security, accounts, governance

## Operator note (2026-11-08)

"Set it as a proposed and not planned backlog item. We may want to do it, but not a priority."

## Summary

Today an admin sees every account token they create or rotate, can choose its value, and since gateway 0.18.0 can set
anyone's password: an admin can sign in as any user silently and the user never knows. The ruling (governance track,
1020 row 6, R4): an admin can only invalidate or regenerate a token, never see it; regeneration issues a one-time
claim code (1 h default, 24 h max, hashed, audited) mailed to the person when SMTP is configured, else shown once to
the admin to hand over; the person redeems it at sign-in (`POST /auth/claim`) and gets the new token themselves;
the account shows when and from where the code was used.

## Where the work is

The only implementation is the local abstractgateway branch `governance-security-1` (2 commits ahead of main, with two
siblings: R3 "a runtime folder stays bound to its account; archive instead of transfer" and the plane deny "runs never
reach other accounts' folders or the audit log"). Main moved under it (password sign-in, the first-run claim link
`abstractgateway claim` / `/session/claim` reusing the word "claim"): conflicts in `routes/gateway.py`, `users.py`,
`service.py` and the route-contract test; the sign-in page must be redone. Estimate: 10–14 h for R4 alone, 18–24 h with
R3 and the plane deny. Detail: `untracked/release-2026-11-07/gateway-branches/kept-branches-detail.md`.

## Decisions needed before it is planned (recommendations in parentheses)

1. May an admin still set another person's password? (No: it reopens the same hole.)
2. Does account creation hand out a handover code instead of a visible token? (Yes.)
3. Does R4's code get a name distinct from the first-run claim link? (Yes: "handover code".)

## Known gaps even on the branch

An admin can be locked out with no recovery route (found at the branch's second gate, never fixed); the terminal
console's Rotate silently drops the code; clients that read `token` after an admin rotate/create would break silently
(terminal console, AbstractNote's `hermetic_gateway.sh`); tools added since that work inside the data folder need a
re-check against the plane deny.

## Related

Governance track `planned/governance/README.md` (R4 bullet points here); 1020; branch `governance-security-1` (kept,
never deleted: it is the only copy).

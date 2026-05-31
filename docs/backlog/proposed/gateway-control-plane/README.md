# Gateway control plane proposals

## Status
Proposed.

## Purpose
These proposals preserve package-boundary options that are plausible but not
yet implementation commitments. The planned Gateway control-plane track should
prove the API and UX needs first.

## Items
- `0151_runtime_explorer_contract.md`: define whether runtime browsing becomes
  Gateway Console tabs, Observer pages, or a future `abstractexplorer`.
- `0152_abstractmanager_package_extraction.md`: decide whether the Gateway
  admin/config UI should later become a separate `abstractmanager` package.
- `0155_hosted_proxy_shared_helper_extraction.md`: decide when repeated hosted
  browser-session proxy logic in Node apps should become a shared helper rather
  than package-local code plus conformance tests.

## Reading order
Read the planned track first:
`../../planned/gateway-control-plane/README.md`.

## Non-goals
These proposals do not authorize new packages yet. They record names and
boundaries to revisit after Gateway Console v0, RBAC hardening, and config APIs
land.

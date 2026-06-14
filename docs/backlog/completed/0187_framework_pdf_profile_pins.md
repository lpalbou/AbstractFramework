# Completed: Framework PDF profile pins

## Metadata
- Created: 2026-06-06
- Status: Completed
- Completed: 2026-06-06

## Context
The user-facing `abstractframework` Light, Apple, and GPU profiles are the public entrypoint for installing the framework. Even after Runtime and Gateway gained the permissive PDF route, the root meta-package still pinned older package versions that did not guarantee the PDF read/write contract.

## What changed
- Bumped `abstractframework` to `0.1.9`.
- Updated root release pins to:
  - `abstractcore==2.13.33`
  - `AbstractRuntime==0.4.28`
  - `abstractgateway==0.2.27`
  - `abstractvision==0.3.21`
- Updated `abstractgateway[apple]` and `abstractgateway[gpu]` root extras to `0.2.27`.
- Regenerated `docs/installers/install-manifest.json`.
- Updated `llms-full.txt` release-profile snippets.

## Validation
- `python -m pytest tests/test_install_profiles.py -q`
  - Result: 6 passed.

## Outcome
Light, Apple, and GPU root install profiles now consume the Runtime/Gateway versions that include mandatory `pypdf` and `reportlab` PDF read/write support while keeping PyMuPDF-family packages out of default installs.

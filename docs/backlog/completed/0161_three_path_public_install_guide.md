# Proposed: Three-Path Public Install Guide

## Metadata
- Created: 2026-05-31
- Status: Completed
- Completed: 2026-05-31

## ADR status
- Governing ADRs: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- ADR impact: None

## Context
The release profile now has three clear installation modes: remote-first Light, Apple local, and
GPU local. The docs mention these commands, but users need a more deliberate decision guide.

## Current code reality
- `README.md` documents `pip install abstractframework`,
  `pip install "abstractframework[apple]"`, and `pip install "abstractframework[gpu]"`.
- `docs/install.md` is the concise user-facing install chooser.
- `docs/api.md`, `docs/faq.md`, `docs/getting-started.md`, `docs/README.md`, and README link to
  the install chooser.
- `docs/guide/apple-local-gateway-flow.md` covers a specific Apple local Gateway/Flow path.

## Problem or opportunity
Install decisions are high-friction because "full functionality" and "local inference" are easy
to confuse. Users need to understand that Light still supports multimodal and embeddings through
remote endpoints, while Apple/GPU add local inferencer stacks.

## Proposed direction
Create a public install guide with three primary paths:

- Light: remote-first, lowest friction, no local MLX/CUDA/Diffusers stacks.
- Apple: local Apple Silicon engines where supported, with larger downloads and macOS-specific
  prerequisites.
- GPU: local GPU engines where supported, with CUDA/ROCm/system-driver expectations.

The guide should include:

- who should choose each path;
- exact commands using `pipx`, `uv`, and venv/pip options where appropriate;
- expected disk/download implications;
- first-run config steps;
- how Gateway/Flow should be started;
- how to run `abstractframework doctor` once it exists;
- when to use the GUI installer instead.

## Why it might matter
This is the main bridge between technical and non-technical installs. It also reduces repeat
confusion about Light installs accidentally installing local inference stacks.

## Promotion criteria
- Root `abstractframework` release profile is stable after `0.1.6`.
- Generated manifest or doctor CLI work starts.
- Installer repo extraction needs public docs that explain how CLI and GUI paths relate.

## Validation ideas
- Dry-run each documented pip command.
- Verify Light install does not pull MLX/CUDA/local inference dependencies.
- Verify Apple/GPU docs align with actual extras in root and package manifests.
- Cross-link from `README.md`, `docs/getting-started.md`, `docs/installers/README.md`, and
  `llms-full.txt`.

## Non-goals
- Do not document unsupported one-off package-manager flows as primary paths.
- Do not claim native signed installers exist before release artifacts are available.
- Do not bury warnings about large local model downloads.

## Guidance for future agents
Write this for a user making a decision, not for maintainers. The guide should be short enough to
read before installing but precise enough to prevent the wrong profile choice.

## Completion report
- Added `docs/install.md` with Light / Apple / GPU profile guidance, venv/uv setup, first checks,
  Gateway/Flow notes, and the generated manifest command.
- Updated README, docs index, getting-started, API, FAQ, installer docs, `llms.txt`, and
  `llms-full.txt`.
- Kept CPU local inference out of the public install chooser pending item 0163.

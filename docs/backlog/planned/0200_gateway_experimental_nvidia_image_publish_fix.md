# Planned: Gateway experimental NVIDIA image publish fix

## Metadata
- Created: 2026-06-14
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0033 install profiles config entrypoints and server boundaries, ADR-0034 framework release sequence and gates
- ADR impact: None if the fix keeps the existing Gateway package/release boundary and only repairs the experimental GPU image path.

## Context
Gateway light images now publish successfully to GHCR, but the experimental NVIDIA image path still
does not publish real tags even though the workflow attempts it.

The recent release evidence showed:

- standard Gateway images published correctly;
- the NVIDIA image build step remained `continue-on-error`;
- the actual NVIDIA image build failed on the package path for `abstractgateway[gpu]`, with missing
  system build prerequisites around `pycairo` / `pkg-config` / cairo development libraries.

That means tags such as `abstractgateway:<version>-gpu` and
`abstractgateway-server-nvidia:<version>` are not yet production-real.

## Current code reality
- `docs/backlog/planned/0164_gateway_docker_ghcr_deployment_track.md` already establishes the target
  GHCR tag set and the release intent for light and GPU images.
- The release workflow currently treats the NVIDIA path as best-effort instead of a hard publishing
  gate.
- The failure is below the application code path: the image build environment does not yet satisfy
  the system dependencies required by the published Python extra set.

## Problem
The release surface suggests a GPU/NVIDIA image track exists, but the tags are not guaranteed to be
published because the Dockerfile and workflow still allow the experimental path to fail quietly.

## Recommendation
- Repair the NVIDIA Dockerfile/build environment so the published `abstractgateway[gpu]` wheel can be
  installed without ad hoc manual fixes.
- Promote the NVIDIA image path from “attempted” to “real published artifact” only after successful
  container build validation and explicit release evidence.
- Keep this work tracked separately from current Flow/Assistant feature work.

## Requirements
- The NVIDIA Docker image must install the published `abstractgateway[gpu]==<version>` package from
  PyPI inside the image build.
- Required system packages for transitive native dependencies must be installed in the image.
- Release automation must surface failure honestly rather than implying success from an optional step.
- Validation must include proof that the expected GHCR tags exist after release.

## Scope
- Gateway NVIDIA Dockerfile and related build scripts/workflows.
- Release/docs evidence for GPU tag publication.

## Non-goals
- Do not redesign Gateway package extras.
- Do not broaden this item into general CUDA runtime verification beyond what is needed to publish
  the image honestly.
- Do not block unrelated Flow/Assistant vision-surface work on this follow-up.

## Dependencies and related tasks
- Planned item `0164_gateway_docker_ghcr_deployment_track.md`
- ADR-0033 and ADR-0034

## Expected outcomes
- GHCR NVIDIA tags publish for real, not as best-effort attempts.
- Release reports can claim GPU image availability without caveats.

## Validation
- Docker build passes for the NVIDIA image path.
- Release workflow records a successful NVIDIA image publish.
- GHCR inspection confirms:
  - `ghcr.io/lpalbou/abstractgateway:<version>-gpu`
  - `ghcr.io/lpalbou/abstractgateway:gpu-latest`
  - `ghcr.io/lpalbou/abstractgateway-server-nvidia:<version>`
  - `ghcr.io/lpalbou/abstractgateway-server-nvidia:latest`

## Progress checklist
- [ ] Add this item to the root backlog overview.
- [ ] Capture the exact failing dependency chain in the current NVIDIA image path.
- [ ] Repair the Dockerfile/build environment.
- [ ] Update the release workflow to report NVIDIA publish status honestly.
- [ ] Re-run release validation with real GHCR evidence.

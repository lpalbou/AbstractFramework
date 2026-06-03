# 0164 Gateway Docker GHCR Deployment Track

Status: In progress
Owner: AbstractGateway
Created: 2026-05-31

## Problem

ADR-0033 and ADR-0034 define Docker as a Gateway deployment artifact with two
strategies: a lightweight server image and an explicit NVIDIA image. The actual
Gateway Docker surface lagged behind that architecture:

- public examples used `abstractgateway-server` image names instead of the
  desired `ghcr.io/lpalbou/abstractgateway`;
- container defaults still centered on the legacy shared Gateway token instead
  of Gateway user auth and browser sessions;
- simple `docker run -v "$PWD/runtime:/data"` examples did not have a clean
  first-admin bootstrap story;
- release workflows built images from the checkout even after the PyPI package
  was published, unlike the AbstractCore image pattern.

## Decision

Use GHCR as the primary registry now. DockerHub remains optional until an org,
secrets, and support process exist.

Publish:

- `ghcr.io/lpalbou/abstractgateway:<version>` and `:latest` for the light image;
- `ghcr.io/lpalbou/abstractgateway:<version>-gpu` and `:gpu-latest` for the
  NVIDIA/GPU image;
- legacy `abstractgateway-server` and `abstractgateway-server-nvidia` aliases
  during a transition period.

Container runtime defaults:

- `ABSTRACTGATEWAY_DATA_DIR=/data`
- `ABSTRACTGATEWAY_USER_AUTH=1`
- bundled `basic-agent` remains available by default; `/data/flows` is only
  used when Compose or the operator explicitly sets `ABSTRACTGATEWAY_FLOWS_DIR`.
- the entrypoint ensures `default/admin` exists when user auth is active and
  writes the first-login token to `<DATA_DIR>/auth/bootstrap-admin-token`.

Release workflow defaults:

- wait for the matching PyPI package;
- install `abstractgateway==<version>` from PyPI for the light image;
- install `abstractgateway[gpu]==<version>` from PyPI for the GPU image.

## Target UX

The supported one-command server path should work as:

```bash
docker run \
  -p 8080:8080 \
  -v "$PWD/runtime:/data" \
  -e ABSTRACTGATEWAY_DATA_DIR=/data \
  -e ABSTRACTGATEWAY_USER_AUTH=1 \
  ghcr.io/lpalbou/abstractgateway:latest
```

Then:

```bash
cat runtime/auth/bootstrap-admin-token
open http://localhost:8080/console
```

The admin signs in as `admin`, creates named users, rotates tokens, and configures
Gateway defaults/provider endpoint profiles from the console.

## Scope

- Dockerfiles and Compose profiles in `abstractgateway/docker/abstractgateway-server/`
- Gateway release and manual GHCR workflows
- `abstractgateway-config bootstrap-admin`
- Gateway Docker/deployment docs and coredoc indexes
- Root deployment docs that explain when to use Python profiles vs Gateway
  containers

## Non-Goals

- DockerHub publishing before registry ownership and secrets are configured
- Apple/MLX Docker image
- CPU-local inference profile
- Kubernetes Helm chart or Terraform module
- changing Core/Runtime package boundaries

## Validation

Required before completion:

- targeted Gateway config/Docker profile tests pass;
- shell entrypoint syntax check passes;
- Docker build is attempted for the light image when Docker is available;
- docs and `llms-full.txt` are regenerated.

Current evidence:

- 2026-05-31: local light image build passed with
  `docker build --build-arg ABSTRACTGATEWAY_INSTALL_MODE=local ... -t abstractgateway:test-light-local`.
- 2026-05-31: container smoke passed with a temporary `/data` mount:
  `/api/health` became ready, `/data/auth/bootstrap-admin-token` was created,
  token format was `agw_*`, and authenticated `/api/gateway/me` returned
  `default/admin` with `user_auth_enabled=true`.

## Follow-Ups

- Add a real CUDA host smoke gate before calling the GPU image production-ready.
- Consider a tiny `abstractframework doctor --container` probe that verifies
  Gateway health, user auth, admin token presence, and mounted data writability.
- Revisit DockerHub only if users need DockerHub specifically rather than GHCR.

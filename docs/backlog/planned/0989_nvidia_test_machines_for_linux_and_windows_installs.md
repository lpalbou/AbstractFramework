# 0989 — NVIDIA test machines for the Linux and Windows `gpu` installs

> Package: abstractframework (installers, release process)
> Type: task
> Created: 2026-09-29
> Priority: high
> Labels: gpu, windows, linux, testing, release

## Summary

No NVIDIA machine is available (the operator's Linux server is CPU-only), so the `gpu` setting
has never been installed and run on real NVIDIA hardware, on Linux or Windows. 0988 fixes the
Windows gpu install with fallbacks and CI checks; this item gets a real run on both systems,
first as a one-off validation session, then as a repeatable release check.

## Options (prices checked 2026-09-29; confirm at order time)

| Option | Cost | Setup | Fit |
|---|---|---|---|
| AWS EC2 `g4dn.xlarge` (4 vCPU, 16 GiB, 1× T4 16 GB), on demand | ~$0.53/h Linux, ~$0.71/h Windows (license included); spot ~$0.07–0.30/h Linux | AWS account; new accounts start with a 0-vCPU quota for G instances, so a quota request (hours to days) comes first | One-off session: cheapest real VMs for both systems; SSH on Linux, OpenSSH enabled by user data on Windows |
| OVHcloud Public Cloud GPU (L4 `l4-90` and others; no current T4 listed) | ~€1.44/h Linux for `l4-90`; Windows license per vCore (~$0.039/vCore/h, ~$0.86/h on 22 vCores) | the operator already has an OVHcloud account | One-off session with no new account, 2–3× the AWS price |
| GitHub Actions GPU larger runners (T4) | $0.052/min Linux (~$3.1/h), $0.102/min Windows (~$6.1/h), plus GitHub Team plan | needs an organization on Team or Enterprise Cloud; the repos are under a personal account today | Repeatable release check inside CI; per-job billing, no machine to manage |
| Container GPU marketplaces (RunPod, Vast.ai) | from ~$0.1–0.3/h | account | Linux containers only: no Windows, no systemd; not a faithful install test |

Recommendation: a one-off AWS `g4dn.xlarge` session (Linux, then Windows) for 0988's validation,
about 2–4 hours per system, so roughly $5–10 in total on demand. The T4 (compute capability 7.5)
exercises the CUDA 13 path with a recent driver. Decide later whether a GitHub organization with
GPU runners is worth it as a recurring release gate.

## Scope

### In scope

- The operator creates the instance and hands over SSH access; the session runs the real install
  line (`install.sh` / `install.ps1` with the gpu profile) from a branch or a staged root, then:
  torch sees CUDA, llama.cpp offloads to the GPU, a Diffusers image is generated on CUDA, Whisper
  runs, the gateway starts and serves; timings and download sizes recorded.
- Windows: stack choice (driver ≥ 580 → CUDA 13), llama.cpp cuBLAS loading, faster-whisper on the
  chosen stack, torchcodec without FFmpeg, live progress output.
- A short runbook (launch, SSH, run, collect logs, terminate) so the session can be repeated.

### Out of scope

- Machine persistence on the operator's machines; any purchase without the operator's action.

## Acceptance criteria

- [ ] One real gpu install on Linux + NVIDIA and one on Windows + NVIDIA, each ending with the
      checks above passing, logs kept under `untracked/`.
- [ ] Findings fixed or filed; 0988's unverified list emptied or explicitly carried.

## References

- GitHub runner pricing: https://docs.github.com/en/billing/reference/actions-runner-pricing
- AWS g4dn.xlarge: https://instances.vantage.sh/aws/ec2/g4dn.xlarge
- OVHcloud Public Cloud prices: https://us.ovhcloud.com/public-cloud/prices/

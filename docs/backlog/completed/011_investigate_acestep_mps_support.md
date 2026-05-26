# 011 — Investigate ACE-Step 1.5 support on Apple Silicon (MPS)

## Summary

Determined whether `ACE-Step/Ace-Step1.5` (ACE-Step v1.5) is expected to run on **Apple Silicon** with **PyTorch MPS**, and what configuration is required.

## Report

### Findings (upstream evidence)

- **ACE-Step 1.5 explicitly claims MPS support**. Upstream `ACE-Step-1.5` README states:
  - “CUDA GPU recommended (also supports **MPS / ROCm / Intel XPU / CPU**)”
  - Source: `https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/main/README.md`

- **ACE-Step benchmarks include a MacBook M2 Max**, implying Apple Silicon execution is a supported target (likely via MPS).
  - Source line example: `https://raw.githubusercontent.com/ace-step/ACE-Step/main/README.md`

- **macOS-specific caveat**: upstream ACE-Step README warns:
  - “If you are using macOS, please use `--bf16 false` to avoid errors.”
  - Source: `https://raw.githubusercontent.com/ace-step/ACE-Step/main/README.md`

- **Community signal**: there is a dedicated fork “ACE-Step 1.5 for Apple Silicon” describing a port to run natively on Apple Silicon using **MPS/Metal** (and optional MLX acceleration).
  - Source: `https://raw.githubusercontent.com/clockworksquirrel/ace-step-apple-silicon/main/README.md`

### Conclusion (for AbstractFramework)

- **Will ACE-Step 1.5 work on MPS?**  
  **Very likely yes**, based on upstream docs explicitly listing MPS support and publishing a MacBook M2 Max benchmark.

- **What must be done on macOS/MPS?**  
  Follow upstream guidance: **disable bf16** (`--bf16 false`). This suggests bf16 is the main macOS/MPS pitfall, not MPS as a whole.

### Notes / Next steps

- Implementing an in-process ACE-Step backend inside `abstractmusic` should:
  - default to MPS when available on Apple Silicon
  - automatically disable bf16 on macOS (or at least document it clearly)
  - optionally support a CPU fallback for unsupported ops (if encountered), similar to the existing Diffusers backend fallback behavior.


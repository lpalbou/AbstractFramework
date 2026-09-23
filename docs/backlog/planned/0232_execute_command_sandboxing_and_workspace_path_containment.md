# 0232 — Sandbox `execute_command` and fix workspace path containment

**Status**: planned
**Priority**: P0 (security — credential exposure + policy bypass, both reachable today)
**Component**: AbstractCore (`common_tools.execute_command`), AbstractRuntime (`workspace_scoped_tools`, `tool_executor`), AbstractGateway (`_sanitize_run_workspace_policy`)
**Created**: 2026-07-31
**Depends on**: ADR-0037 (hosted file source contract and WorkspacePath authority)
**Related**: ADR-0016 (tool-calling pipeline and responsibility boundaries)

---

## Summary

The workspace policy (`workspace_only`, or `workspace_or_allowed` with an explicit allowlist) is
declared per run and enforced only on **path-scoped tools**. `execute_command` is not path-scoped:
it is `subprocess.Popen(command, shell=True, cwd=working_dir)` with no environment scrubbing, no
namespace, and no filesystem restriction. An agent that is refused by `write_file` can perform the
same write through the shell, and does.

This item covers two coupled problems:

1. **Containment** — `execute_command` (and `shell_exec`) must not be a way around the declared
   workspace policy.
2. **Path resolution** — absolute paths that legitimately point *inside* the workspace are
   currently refused, which is what pushed the agent to the shell in the first place, and the
   refusal message actively teaches a wrong retry that silently misfiles the deliverable.

Both were found while running a benchmark, not by an audit; the failure mode is live.

## Evidence — the incident (2026-07-30)

A gateway run with `--workspace-mode workspace_only` and workspace root
`/private/tmp/zelda-ab-ws-20260730T103656Z/review-2/product` was told to write its output there.
Observed, in order:

1. `write_file` rejected the absolute path **4 times**.
2. The agent fell back to `execute_command` with `cat > /private/tmp/.../index.html <<'EOF'`, which
   **succeeded** — the directory exists on disk with the written products.
3. In a sibling run, the agent instead followed the refusal's advice, stripped the leading `/`, and
   its files were **grafted** to
   `runtime/workspaces/<uuid>/private/tmp/zelda-ab-ws-.../review-1/index.html` — a real tree, found
   on disk. The deliverable was silently misfiled rather than written where the operator asked.

The root cause of step 1 is upstream of the resolver: `_sanitize_run_workspace_policy`
(`abstractgateway/routes/gateway.py:3341-3348`) finds `/private/tmp/...` outside the operator's
allowed roots and does a bare `input_data.pop("workspace_root", None)` — **a silent drop, no error,
no warning**. The run then mints a fresh `data_dir/workspaces/<uuid4>` (`:6680-6688`), so the
absolute path the operator supplied is genuinely not inside the workspace any more, and the
resolver is correct to refuse it.

## Findings

### A. `execute_command` has no containment (CONFIRMED)

`abstractcore/abstractcore/tools/common_tools.py:9873-9881`:

```python
proc = subprocess.Popen(
    command, shell=True, cwd=working_dir, text=True,
    stdout=..., stderr=..., start_new_session=(os.name == "posix"))
```

- No `env=` → **the agent's full environment is inherited**, including tokens.
- `working_directory` (`:9822-9846`) is validated only for `exists()`/`is_dir()`; it sets `cwd`
  and nothing else.
- `_validate_command_security` (`:10111-10181`) is a **regex denylist** over `command.lower()`
  (`rm -rf`, `dd if=…of=`, `mkfs`, `curl…|bash`, `>` into `/etc|/usr|/var`). It has no concept of
  workspace scope, so writing to `/private/tmp/...` or `$HOME` passes cleanly.
- `allow_dangerous` (`:9668`, `:10122`) is **model-supplied** and short-circuits the check with
  `return {"safe": True}`. It is a hint, not a gate.

The runtime concedes the design: `abstractruntime/.../workspace_scoped_tools.py:639-647` rewrites
*only* `working_directory` for `execute_command`/`shell_exec`, with the comment *"this is policy
for the starting point, not a sandbox: once running, the session can cd anywhere"*.
`shell_session.py:24` repeats it, and `:73-78` spawns a persistent `bash` PTY that survives
per-call approval entirely.

**Sharpest consequence:** `~/.abstractcode/gateway.json` (0600) and `~/.codex/auth.json` (0600)
are readable by the same uid, so `cat` + `curl -d @-` exfiltrates live tokens — fully subsuming the
`fetch_url` approval gate that `tool_executor.py:887-892` exists to enforce. Escape vectors that
touch no denylist pattern: `>`/`>>`/heredoc, `cp`/`mv`/`tee`/`install`/`rsync`, `dd of=` (only the
`if=…of=` form is blocked), `python -c`/`node -e`/`perl -e`, `curl -o`/`wget -O`, writes into
another run's `runtime/workspaces/<uuid>/`, and `nohup … &`/`setsid` (the process tree survives
because `hard_kill_tree` runs only on timeout).

### B. Path containment is string-based and bypassable (CONFIRMED)

`is_under_path` compares with `Path.relative_to` (byte comparison). Consequences, each reproduced:

| # | Attack | Result |
|---|---|---|
| B1 | **Case-variant denylist bypass** — `ignored=['secrets']`: `secrets/creds.txt` REJECTED, `SECRETS/creds.txt` **ACCEPTED and read** | APFS is case-insensitive; an allowlist fails *closed* but a **denylist fails open** |
| B2 | **Unicode NFC/NFD bypass** — `ignored=['café']` (NFC): NFC rejected, **NFD accepted and readable** | no normalization before comparison |
| B3 | **Cross-tenant workspace access** — `workspace_allowed_paths=['<data_dir>/workspaces']` + `workspace_or_allowed` survives the sanitizer, because `allowed_roots` already includes `data_dir/workspaces` (`gateway.py:3335`) | another run's files read end-to-end; **1,746 sibling workspaces** currently exposed this way |
| B4 | **Batch TOCTOU** — `WorkspaceScopedToolExecutor.execute` (`:491-514`) resolves *every* call in a batch, then delegates | call 1 creates a symlink; call 2 was validated before call 1 ran |
| B5 | Unexpanded `$VAR` / glob accepted as literal grafted names | no escape at the resolver, but downstream shell may expand them |

Correctly handled today (verified, do not regress): `..`/`.` normalization, `/tmp`→`/private/tmp`
and `/var`→`/private/var`, `~` expansion, single-shot symlink escape, and crafted-hash cross-tenant
access (workspace names are `uuid4().hex`, not path-derived).

## Proposal

### 1. Fail loudly instead of silently dropping (smallest, highest-value fix)

`gateway.py:3348` must return a 400 naming the rejected root and the allowed roots, not `pop()` the
key. Every downstream symptom in this item is a consequence of a run believing it has a workspace
it does not have. Additionally, the refusal text in `_REANCHOR_TEACHING_SUFFIX`
(`workspace_scoped_tools.py:318-321`) must **not** say *"retry with a path relative to <root>"* when
the model supplied an absolute path outside the root — that instruction is what produces the graft.
Say the path is out of scope and name the scope.

### 2. Absolute-path acceptance policy

Containment must be judged on the **final canonicalized target**, then accepted per mode:

| Input shape | `workspace_only` | `workspace_or_allowed` | `all_except_ignored` |
|---|---|---|---|
| Abs path canonically under root | **accept** | accept | accept |
| Abs path under an allowed path | reject | **accept** | accept |
| Abs path outside all roots, target exists | reject | reject | accept ∧ ¬ignored |
| Abs path outside, target absent | **reject, do not teach a relative retry** | reject | accept ∧ ¬ignored |
| `..`/`.` segments | normalize then judge | same | same |
| Symlink inside → outside | **reject** | reject | ignored-check on target |
| `~` / `$VAR` / glob | expand `~`; **reject** `$VAR` and glob | same | same |
| Leading-slash-stripped abs path (`private/tmp/…`) | **reject, never graft** | reject | reject |

Answering the operator's question directly: **yes, accept a fully-qualified path when it resolves
inside the authorized root** — refusing it is pure friction and caused this incident. The risk is
not the absolute form, it is comparing strings instead of filesystem identity.

### 3. Canonical containment algorithm

```
def contain(raw, roots, ignored):
    s = NFC(strip(raw));  reject if empty or contains NUL
    reject if s contains unexpanded $ or glob metachars      # B5
    p = expanduser(s)                                        # ~ only, never $VAR
    reject if not p.is_absolute() and looks_like_stripped_abs(p)   # graft guard
    target = realpath(p)          # resolves symlinks, .., /tmp -> /private/tmp

    # containment by IDENTITY, not by string
    anc = deepest_existing_ancestor(target);  reject if None
    root = first r in roots where (st_dev, st_ino) of realpath(r)
           matches some parent of target                     # fixes B1, B2, hardlinks
    reject if root is None
    for ig in ignored:
        reject if any parent of target has ig's (st_dev, st_ino)

    # TOCTOU-safe: never reuse the resolved string             # B4
    fd = open(root, O_DIRECTORY|O_NOFOLLOW)
    for comp in relative_components(target, root):
        fd = openat(fd, comp, O_NOFOLLOW)
    return fd            # hand the descriptor to the tool
```

`(st_dev, st_ino)` comparison fixes case-insensitivity, NFD, and hardlinks in one move;
`openat` + `O_NOFOLLOW` closes the check-then-use race by making the validated object *be* the
written object. String comparison remains only for a not-yet-existing tail, on `normcase(NFC(...))`.

Also: forbid `workspace_allowed_paths` from naming the workspaces **base** directory; permit only a
run's own workspace (fixes B3).

### 4. Sandbox `execute_command`

| Option | Strength | Portability | Perf | DX cost | Effort |
|---|---|---|---|---|---|
| **A. Per-invocation OS sandbox** (macOS `sandbox-exec`; Linux `bubblewrap`) | High, kernel-enforced | both, one dispatch layer | ~5-20 ms/call | low | **M (~2-3 wks)** |
| B. Container-per-run (Podman/Docker) | Highest | Linux native; macOS needs a VM | 0.3-2 s start | high (toolchain in image) | L |
| C. Separate low-priv user + ACLs | Medium-high | both, privileged setup | ~0 | medium | M + ops burden |
| D. Command allowlist with argument parsing | **Low as containment** | both | ~0 | high | M-L |
| E. Regex denylist (today) | none | — | — | — | shipped, bypassed |

**Recommend A primary, B as the fallback on Linux servers/CI.** Do **not** treat D as containment:
any allowlisted interpreter (`python`, `node`, `cargo` via `build.rs`, `npm` lifecycle scripts) is a
general-purpose escape, and `cargo test` executes arbitrary code by design. D belongs in approval
tiering (§6), deciding what to *prompt on*, not what to *prevent*.

**Fail-closed rule:** if no sandbox backend is available, `execute_command` under `workspace_only`
requires approval — it must never silently degrade to the regex denylist.

**Ship first, independently of the sandbox:** environment scrubbing. Pass an allowlist (`PATH`,
`HOME`, `TMPDIR`, `LANG`, `TERM`, `SHELL`, `SSL_CERT_FILE`, `CARGO_HOME`, `RUSTUP_HOME`) and drop
`*TOKEN*|*KEY*|*SECRET*|*PASSWORD*|AWS_*|GH_*|ANTHROPIC_*|OPENAI_*`. This is cheap and removes the
`env | grep -i token` path that needs no filesystem access at all.

### 5. Keep the agent useful

Grant specific subpaths, never `$HOME`:

- **Read-only**: `/usr`, `/bin`, `/opt/homebrew` (or `/nix/store`), `/System`,
  `/Library/Developer/CommandLineTools`, `~/.rustup`, `~/.cargo/bin`, `~/.nvm`, `~/.pyenv`,
  `/etc/resolv.conf`, `/etc/ssl`.
- **Read-write (caches only)**: `~/.cargo/registry`, `~/.cargo/git`, `~/.npm/_cacache`,
  `~/.cache/pip`. **Not** `~/.cargo` wholesale — `config.toml` and `credentials.toml` are
  injection and credential surfaces.
- **Read-write**: workspace root, allowlisted paths, and a **per-run `TMPDIR`** exported into the
  child environment (this is where the incident's heredoc should have landed).
- **Denied even inside home**: `~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.abstractcode`, `~/.codex`,
  `~/.netrc`, `~/Library/Keychains`, sibling `runtime/workspaces/*`.
- **Network is a separate axis.** Recommend default-deny egress under `workspace_only` with an
  operator-set registry allowlist (crates.io, registry.npmjs.org, pypi.org, files.pythonhosted.org).
  Linux: `--unshare-net` + filtering proxy. macOS: Seatbelt cannot filter by host, so
  `(deny network*)` plus loopback-only to a proxy with `HTTP(S)_PROXY` injected.

### 6. Tool-approval tiering

`execute_command` **must not be auto-approvable under `workspace_only` while unsandboxed** — the
operator has declared a boundary, and a tool documented as "not a sandbox" cannot sit in the auto
lane without voiding that declaration. Note the shipped defaults already agree: it is absent from
`_DEFAULT_SAFE_AUTO_APPROVE` (`tool_executor.py:873-909`) and abstractcode-tui classifies it `ask`
(`tool_policy.rs:699`). The auto-approval in this incident came from a seat-level policy override
(PLAUSIBLE) — closing that override is part of this item.

- **T0 auto** — sandboxed **and** proven read-only (extend the refiner set: `git_read_only@v1`,
  plus a new `build_readonly@v1` for `--version`/`--check`/`ls`/in-scope `cat`).
- **T1 auto** — sandboxed, no proof needed: containment, not classification, is the control. This
  is the tier that keeps the agent useful.
- **T2 ask** — unsandboxed, any command (today's state). Show the literal command string.
- **T3 ask-always, never auto-approvable, no session "always allow"** — any `allow_dangerous=true`,
  anything the sandbox denied that the operator wants anyway, and `shell_exec` **session creation**
  (it escapes per-call approval by construction, `shell_session.py:36`).

Two invariants to enforce in code: a refiner may only **lower** a band, never raise it (extend the
existing contract at `risk_facts.py:166-171` so a policy file cannot raise `execute_command` into
auto while the sandbox is absent); and an unavailable or failing sandbox launcher demotes T1→T2
rather than opening the lane.

## Validation — required evidence

**MUST FAIL** (assert on the filesystem, not on the message; and with `allow_dangerous=true` set,
to prove it is not a scope bypass):

1. `cat > /private/tmp/esc-$RUN/x.html <<'EOF'` (the incident, verbatim)
2. `echo x > "$HOME/esc.txt"`; `echo x >> /private/tmp/esc.txt`
3. `cp`, `mv`, `tee`, `dd of=`, `install -m644` to a path outside the workspace
4. `python3 -c "open('/private/tmp/esc.txt','w').write('x')"`; `node -e`; `perl -e`
5. `cat ~/.abstractcode/gateway.json`; also via `python3 -c`, `grep`, `base64` on `~/.codex/auth.json`
6. write into a sibling run's `runtime/workspaces/<other-uuid>/`
7. `nohup sleep 300 &` / `setsid sleep 300 &` → assert no descendant survives the call
8. `env` output contains no `*TOKEN*`/`*KEY*` value
9. `curl -o /private/tmp/esc.bin https://example.com`
10. `ln -s / ws/root && echo x > ws/root/private/tmp/esc.txt` (symlink traversal)
11. `shell_exec` + `cd /private/tmp && touch esc`
12. Case/Unicode denylist probes: `SECRETS/creds.txt`, NFD `café/x`
13. `workspace_allowed_paths=['<data_dir>/workspaces']` is refused at start

**MUST STILL PASS**: `cargo build`/`cargo test` (cold and warm cache), `npm ci` + `npm test`,
`node --check`, `pytest -q`, `git status`/`log`/`diff`, read any workspace file,
`mkdir -p ws/sub && echo x > ws/sub/f.txt`, write to `$TMPDIR`, read+write an allowlisted path in
`workspace_or_allowed`. Add a latency-budget assertion (**sandbox overhead < 50 ms/call**) so
containment does not silently regress developer experience.

## Residual risk (state plainly, do not bury)

- `sandbox-exec` is Apple-deprecated with no API stability guarantee; the launcher must self-test
  at run start and fail closed if the profile is rejected.
- Profile authoring is the weak link — one over-broad `subpath` re-opens everything. Treat profile
  generation as security-critical code with its own tests.
- `bubblewrap` needs unprivileged user namespaces, disabled on some hardened distros.
- Neither backend stops a build script from damaging the workspace itself, or from exhausting
  CPU/memory — add rlimits/cgroups separately.
- Environment secret theft is **not** fixed by sandboxing; only scrubbing fixes it.

## ADR follow-up

The rule *"a declared workspace policy binds every tool, including shell execution, and a tool that
cannot honour it is not auto-approvable"* is durable cross-task policy, not item-local. Create or
extend an ADR (candidate: an amendment to ADR-0016 on tool-calling responsibility boundaries)
before closing this item, or record explicitly why not.

## Open questions

- Does any deployment set `ABSTRACTGATEWAY_ALLOW_CLIENT_WORKSPACE_SCOPE` / `TOOL_MODE=local`? With
  it on, `_sanitize_run_workspace_policy` is bypassed entirely (`gateway.py:3344`) and every clamp
  above disappears. It was `False` when probed.
- Are run workspaces ever segregated per tenant on disk? From `data_homes.py:120` they are not,
  which sets the blast radius of B3.

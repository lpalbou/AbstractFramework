# 1345 — Windows: OpenSSH's ssh-keygen fails on the public key inside the command sandbox

> Package: abstractcore (tools/sandbox_windows.py), abstractgateway (docs/security.md)
> Type: bug
> Created: 2026-11-25
> Priority: normal
> Labels: windows, command-sandbox, ssh, limits

## Summary

Inside the Windows command sandbox (AbstractCore 2.38.0 and 2.39.0, `windows-restricted-token`), Windows' own
`%SystemRoot%\System32\OpenSSH\ssh-keygen.exe` writes the private key and then exits 255 on the public key,
under every workspace setting, the read & write default included (measured 2026-11-25 by the sandbox work of
backlog 1341). The private key left behind grants its owner Modify, so the user's own programs can read and
delete it. The cause is not identified. An agent that is asked to create an SSH key on Windows therefore fails
halfway and leaves a private key without its public half.

## Why

Creating a deploy key is an ordinary agent task, and Windows' OpenSSH is what a Windows user has without Git
Bash. Under the two stricter settings Git's own `ssh-keygen` is not a reliable alternative either: it is an MSYS2
program and stops at start when another MSYS2 program runs in the session (documented limit, 1341). The failure
is documented, not explained, so nobody can say whether it is the restricted token, the access-list entries the
sandbox writes, or `ssh-keygen`'s own permission check on what it creates.

## Current code reality (audited 2026-11-25; abstractcore `main` after lpalbou/AbstractCore#54, abstractgateway `release/0.24.0`)

- abstractcore `abstractcore/tools/README.md`, *Command sandbox* > Windows, "Limits where writes are limited to
  the rows": "Windows' own `ssh-keygen` (`%SystemRoot%\System32\OpenSSH\ssh-keygen.exe`) writes the private key
  and then fails on the public one, under every shape (the read & write default too): the key left behind grants
  its owner "modify", so the user's own programs read and delete it."
- The same README, "A read & write row": everything inside a read & write row is the command's, its
  permissions included ("ssh-keygen, git, Python's `tempfile.mkdtemp` and installers set permissions on what
  they make"). Windows' OpenSSH sets an owner-only access list on the private key; whether its next step
  (reading back or re-opening the key, or checking the owner against the token) is what fails is not known.
- "Limits (every shape)": Windows' own TLS (schannel: `curl.exe`, `Invoke-WebRequest`, .NET) is refused to a
  restricted token. This is a second Windows component that fails under the restricted token, possibly for a
  related reason (a service or a check that does not accept a restricted token); it is a documented limit too.
- abstractgateway `docs/security.md` "On Windows" > Limits names both: "Windows' own `ssh-keygen` ... writes the
  private key and then fails on the public one, under every setting" and "Windows' built-in TLS is not available
  inside the sandbox".
- No test in abstractcore's `tests/tools/test_sandbox_windows*.py` runs `ssh-keygen`.

## Scope

### In scope

- Find the cause: run `ssh-keygen.exe -t ed25519 -N "" -f <row>\k` in a read & write row under each shape with
  Process Monitor or `ssh-keygen -vvv`, and compare with the same command unsandboxed; check the key's access
  list, owner and integrity label after the private key is written.
- Fix it in the launcher when the cause is in what the sandbox does (the token's restricting SIDs, the owner
  of created files, the access-list entries), without widening what a command may reach.
- Otherwise document the cause precisely, and make a failed run not leave a private key behind if that can be
  done from the sandbox side.
- A Windows test that runs `ssh-keygen.exe` under the three shapes (skipped where OpenSSH is not installed,
  with a reason, and counted by CI's skip gate).

### Out of scope

- Git's MSYS2 `ssh-keygen` and Git Bash under the two stricter settings (documented limit of 1341).
- schannel TLS, unless the cause turns out to be the same.

## Acceptance criteria

- [ ] The cause of the exit 255 is identified and written in this item and in abstractcore's tools README.
- [ ] Either `ssh-keygen.exe -t ed25519 -N "" -f k` in a read & write row writes both `k` and `k.pub` and exits
      0 under every workspace setting, or the documented limit names the cause and no private key is left
      without its public half.
- [ ] A Windows test exercises it under the three shapes in abstractcore's `windows-sandbox` CI job.
- [ ] AbstractGateway `docs/security.md` "On Windows" matches the result.

## Testing

- `python -m pytest tests/tools/test_sandbox_windows.py -k ssh_keygen` (abstractcore, Windows)

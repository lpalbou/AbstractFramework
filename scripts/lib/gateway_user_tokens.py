"""Ensure local dev Gateway users exist and print their bearer tokens.

Used by scripts/lib/af_stack.sh (start.sh / start-local.sh) after the gateway
becomes healthy. Mirrors the user-bootstrap logic proven in
scripts/gateway-flow-local.sh, condensed to the stack-banner use case:

- ensures the requested users exist in the gateway user registry
  (admin gets the admin role; admin on the default tenant rides the
  "default" runtime — same conventions as gateway-flow-local.sh);
- verifies the plaintext dev-token cache against the registry (the registry
  stores only hashes) and rotates a user's token when the cache is missing
  or stale, so the printed token is always usable;
- writes the cache back (0600) and prints one line per user.

The registry path derives from ABSTRACTGATEWAY_DATA_DIR — the caller must
export it to the SAME data dir the running gateway uses, or tokens would be
minted into a registry the server never reads.

Usage: python gateway_user_tokens.py <users_csv> <tenant> <cache_file> <gateway_url>
"""

from __future__ import annotations

import datetime
import json
import socket
import stat
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main(argv: list[str]) -> int:
    users_csv, tenant_raw, cache_raw, gateway_url = argv[1:5]

    try:
        from abstractgateway.security.principal import safe_principal_component
        from abstractgateway.users import GatewayUserRegistry, gateway_user_auth_enabled
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"  tokens: unavailable (#FALLBACK abstractgateway not importable: {exc})")
        return 0

    if not gateway_user_auth_enabled():
        print("  User auth is DISABLED (no tokens needed to connect).")
        print("  Set ABSTRACTGATEWAY_USER_AUTH=1 before starting to use per-user tokens.")
        return 0

    tenant = safe_principal_component(tenant_raw, default="default")
    users: list[str] = []
    for part in str(users_csv or "").replace("\n", ",").split(","):
        user_id = safe_principal_component(part, default="")
        if user_id and user_id not in users:
            users.append(user_id)

    cache_path = Path(cache_raw).expanduser().resolve()
    cache: dict[str, Any] = {"version": 1, "users": {}}
    if cache_path.exists():
        try:
            loaded = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cache = loaded
        except Exception as exc:
            print(f"  tokens: invalid cache {cache_path}: {exc}", file=sys.stderr)
            return 1
    cache["version"] = 1
    cache_users = cache.setdefault("users", {})
    if not isinstance(cache_users, dict):
        cache_users = {}
        cache["users"] = cache_users

    registry = GatewayUserRegistry()

    def _cached_token(tenant_id: str, user_id: str) -> str:
        entry = cache_users.get(f"{tenant_id}:{user_id}")
        if isinstance(entry, dict):
            return str(entry.get("token") or "").strip()
        if isinstance(entry, str):
            return entry.strip()
        return ""

    def _remember(rec: Any, token: str, reason: str) -> None:
        if not token:
            return
        cache_users[rec.key] = {
            "token": token,
            "tenant_id": rec.tenant_id,
            "user_id": rec.user_id,
            "runtime_id": rec.runtime_id or rec.user_id,
            "updated_at": _now(),
            "reason": reason,
        }

    def _token_matches(rec: Any, token: str) -> bool:
        if not token:
            return False
        principal = registry.authenticate(token)
        return bool(
            principal
            and principal.user_id == rec.user_id
            and principal.tenant_id == rec.tenant_id
            and principal.runtime_id == (rec.runtime_id or rec.user_id)
        )

    rows: list[tuple[str, str]] = []
    for user_id in users:
        desired_roles = ["admin", "user"] if user_id == "admin" else ["user"]
        desired_runtime_id = "default" if user_id == "admin" and tenant == "default" else user_id
        rec = registry.get_user(user_id, tenant_id=tenant)
        if rec is None:
            cached = _cached_token(tenant, user_id)
            rec, issued = registry.create_user(
                user_id=user_id,
                tenant_id=tenant,
                roles=desired_roles,
                runtime_id=desired_runtime_id,
                token=cached or None,
            )
            _remember(rec, issued, "created")

        token = _cached_token(rec.tenant_id, rec.user_id)
        if not _token_matches(rec, token):
            # Cache missing or stale vs the hashed registry entry: rotate so the
            # printed token actually works against the running gateway.
            rec, issued = registry.update_user(
                user_id=rec.user_id,
                tenant_id=rec.tenant_id,
                enabled=True,
                token="",
            )
            token = issued or ""
            _remember(rec, token, "rotated-stale-cache")
        rows.append((rec.user_id, token or "<token unavailable>"))

    if cache_users:
        cache["updated_at"] = _now()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
        tmp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(cache_path)
        try:
            cache_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

    # Best-effort live verification against the running gateway (the registry
    # write above is on-disk truth; /me proves the server reads the same dir).
    def _verified(token: str) -> tuple[Optional[bool], str]:
        if not token or token.startswith("<"):
            return False, ""
        request = urllib.request.Request(
            gateway_url.rstrip("/") + "/api/gateway/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Launch-time reality (start-local/start): the gateway advertises
        # itself as "up" once the control plane is healthy, but per-principal
        # services can still be cold. The first /api/gateway/me for a token
        # may block behind principal warmup long enough to trip a single short
        # timeout, so a one-shot probe mislabels a healthy startup as
        # "unverified". Give the warmup a short bounded window before falling
        # back to an honest note.
        timeout_s = 2.0
        delays_s = (0.25, 0.5, 1.0, 2.0, 2.0)
        last_error = ""
        for attempt in range(len(delays_s) + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout_s) as response:
                    json.load(response)
                return True, ""
            except urllib.error.HTTPError as exc:
                if exc.code in {401, 403}:
                    return False, ""
                last_error = f"HTTP {exc.code}"
            except urllib.error.URLError as exc:
                reason = getattr(exc, "reason", None)
                if isinstance(reason, TimeoutError) or isinstance(reason, socket.timeout):
                    last_error = "gateway /me timed out during startup warmup"
                else:
                    last_error = f"gateway /me not reachable ({reason or type(exc).__name__})"
            except TimeoutError:
                last_error = "gateway /me timed out during startup warmup"
            except socket.timeout:
                last_error = "gateway /me timed out during startup warmup"
            except Exception as exc:
                last_error = f"gateway /me not reachable ({type(exc).__name__})"
            if attempt < len(delays_s):
                time.sleep(delays_s[attempt])
        return None, last_error or "gateway /me not reachable"

    width = max([len(u) for u, _ in rows] + [4])
    print(f"  Sign-in tokens (tenant: {tenant}):")
    for user_id, token in rows:
        note = ""
        verified, reason = _verified(token)
        if verified is None:
            note = f"  (unverified after retries: {reason})"
        print(f"    {user_id:<{width}}  {token}{note}")
    print(f"  Token cache: {cache_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

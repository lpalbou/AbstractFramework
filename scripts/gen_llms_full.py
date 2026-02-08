#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


FILES: list[str] = [
    "README.md",
    "llms.txt",
    "pyproject.toml",
    "abstractframework/__init__.py",
    "docs/README.md",
    "docs/getting-started.md",
    "docs/architecture.md",
    "docs/configuration.md",
    "docs/api.md",
    "docs/faq.md",
    "docs/glossary.md",
    "docs/scenarios/README.md",
    "docs/scenarios/offline-coding-assistant.md",
    "docs/scenarios/gateway-first-local-dev.md",
    "docs/scenarios/specialized-agent-flow.md",
    "docs/scenarios/workflow-bundle-lifecycle.md",
    "docs/scenarios/telegram-permanent-contact.md",
    "docs/scenarios/email-inbox-agent.md",
    "docs/scenarios/phone-thin-client.md",
    "docs/guide/README.md",
    "docs/guide/agent-vs-llm.md",
    "docs/guide/capability-plugins.md",
    "docs/guide/deployment-topologies.md",
    "docs/guide/deployment-web.md",
    "docs/guide/deployment-iphone.md",
    "docs/guide/gateway-security.md",
    "docs/guide/runtime-scope.md",
    "docs/guide/flow-and-kg-memory.md",
    "docs/guide/scheduled-workflows.md",
    "docs/guide/prompt-caching.md",
    "docs/guide/workflow-bundles.md",
    "docs/guide/telegram-integration.md",
    "docs/guide/email-integration.md",
    "docs/guide/process-manager-env-vars.md",
]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out = repo_root / "llms-full.txt"

    parts: list[str] = []
    parts.append("# AbstractFramework - llms-full\n")
    parts.append("> Full text of key files from this repo. Sections are separated by `--- <path> ---`.\n")

    for rel in FILES:
        p = repo_root / rel
        if not p.exists():
            raise SystemExit(f"Missing file: {rel}")
        parts.append(f"\n--- {rel} ---\n")
        parts.append(p.read_text(encoding="utf-8"))
        if not parts[-1].endswith("\n"):
            parts.append("\n")

    out.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
AbstractFramework AbstractCore Installer (test).

This script installs AbstractCore into a dedicated virtual environment and
optionally runs the configuration wizard and readiness checks.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

MANIFEST_PATH = Path(__file__).with_name("manifest.json")
STATE_FILE_NAME = "install-state.json"

BASE_URL_ENV_VARS = {
    "ollama": "OLLAMA_BASE_URL",
    "lmstudio": "LMSTUDIO_BASE_URL",
    "openai": "OPENAI_BASE_URL",
    "anthropic": "ANTHROPIC_BASE_URL",
    "openrouter": "OPENROUTER_BASE_URL",
    "openai-compatible": "OPENAI_COMPATIBLE_BASE_URL",
    "vllm": "VLLM_BASE_URL",
    "portkey": "PORTKEY_BASE_URL",
}

ENV_DIR = Path.home() / ".abstractcore" / "config"
ENV_SH = ENV_DIR / "abstractcore.env"
ENV_PS1 = ENV_DIR / "abstractcore.env.ps1"

DEFAULT_PROFILES = {
    "minimal": [],
    "all-apple": ["all-apple"],
    "all-gpu": ["all-gpu"],
}


_LOG_CALLBACK = None


def set_log_callback(callback) -> None:
    global _LOG_CALLBACK
    _LOG_CALLBACK = callback


def log(message: str) -> None:
    if _LOG_CALLBACK:
        _LOG_CALLBACK(message)
        return
    print(message, flush=True)


def abort(message: str, exit_code: int = 1) -> None:
    log(message)
    raise SystemExit(exit_code)


def ensure_python_version() -> None:
    if sys.version_info < (3, 10):
        abort("Python 3.10+ is required to run this installer.")


def load_profiles() -> Tuple[str, dict]:
    if not MANIFEST_PATH.exists():
        log("#FALLBACK: manifest.json missing; using built-in profiles.")
        return "full", DEFAULT_PROFILES

    try:
        data = json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as exc:
        log(f"#FALLBACK: manifest.json invalid ({exc}); using built-in profiles.")
        return "full", DEFAULT_PROFILES

    default_profile = data.get("default_profile", "full")
    profiles = data.get("profiles", {})
    if not isinstance(profiles, dict) or not profiles:
        log("#FALLBACK: manifest.json profiles invalid; using built-in profiles.")
        return "full", DEFAULT_PROFILES

    normalized = {}
    for profile_name, profile_data in profiles.items():
        extras = profile_data.get("extras", [])
        if isinstance(extras, list) and all(isinstance(x, str) for x in extras):
            normalized[profile_name] = extras

    if not normalized:
        log("#FALLBACK: manifest.json profiles empty; using built-in profiles.")
        return "full", DEFAULT_PROFILES

    return default_profile, normalized


def default_prefix() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            fallback = Path.home() / "AppData" / "Local"
            log(f"#FALLBACK: LOCALAPPDATA missing; using {fallback}.")
            base = str(fallback)
        return Path(base) / "AbstractFramework" / "abstractcore"
    return Path.home() / ".abstractframework" / "abstractcore"


def venv_paths(prefix: Path) -> Tuple[Path, Path, Path]:
    venv_dir = prefix / ".venv"
    bin_dir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python_bin = bin_dir / ("python.exe" if sys.platform == "win32" else "python")
    return venv_dir, bin_dir, python_bin


def build_package_spec(version: str, extras: List[str]) -> str:
    extras_part = f"[{','.join(extras)}]" if extras else ""
    if version == "latest":
        return f"abstractcore{extras_part}"
    return f"abstractcore{extras_part}=={version}"


def _format_cmd(cmd: List[str]) -> str:
    return " ".join(cmd)


def run_command(cmd: List[str], env: dict | None = None, display_cmd: List[str] | None = None) -> None:
    log(f"$ {_format_cmd(display_cmd or cmd)}")
    subprocess.run(cmd, check=True, env=env)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_cli(bin_dir: Path, name: str) -> Path | None:
    if sys.platform == "win32":
        candidates = [
            bin_dir / f"{name}.exe",
            bin_dir / f"{name}.cmd",
            bin_dir / f"{name}.bat",
            bin_dir / f"{name}-script.py",
        ]
    else:
        candidates = [bin_dir / name]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def write_state(prefix: Path, state: dict) -> None:
    state_path = prefix / STATE_FILE_NAME
    state_path.write_text(json.dumps(state, indent=2))


def read_state(prefix: Path) -> dict | None:
    state_path = prefix / STATE_FILE_NAME
    if not state_path.exists():
        return None


def apply_config(
    cli: Path,
    provider: str | None,
    model: str | None,
    api_keys: List[Tuple[str, str]],
    base_url: Tuple[str, str] | None,
    env: dict,
) -> None:
    if provider and model:
        run_command(
            [str(cli), "--set-global-default", f"{provider}/{model}"],
            env=env,
        )
    elif provider or model:
        log("#FALLBACK: Skipping default model because provider/model is incomplete.")

    for key_provider, key_value in api_keys:
        if not key_value:
            continue
        run_command(
            [str(cli), "--set-api-key", key_provider, key_value],
            env=env,
            display_cmd=[str(cli), "--set-api-key", key_provider, "****"],
        )

    if base_url:
        base_provider, base_value = base_url
        env_var = BASE_URL_ENV_VARS.get(base_provider)
        if not env_var:
            log(f"#FALLBACK: Base URL not supported for provider '{base_provider}'.")
            return
        env[env_var] = base_value
        _persist_env_var(env_var, base_value)
        log(f"Saved {env_var} to {ENV_SH} and {ENV_PS1}.")


def apply_extra_config(cli: Path, args: argparse.Namespace, env: dict) -> None:
    if args.config_vision_provider:
        provider, model = args.config_vision_provider
        run_command([str(cli), "--set-vision-provider", provider, model], env=env)
    if args.config_vision_fallback:
        provider, model = args.config_vision_fallback
        run_command([str(cli), "--add-vision-fallback", provider, model], env=env)
    if args.config_disable_vision:
        run_command([str(cli), "--disable-vision"], env=env)
    if args.config_download_vision_model:
        run_command([str(cli), "--download-vision-model", args.config_download_vision_model], env=env)

    if args.config_audio_strategy:
        run_command([str(cli), "--set-audio-strategy", args.config_audio_strategy], env=env)
    if args.config_stt_backend_id:
        run_command([str(cli), "--set-stt-backend-id", args.config_stt_backend_id], env=env)
    if args.config_stt_language:
        run_command([str(cli), "--set-stt-language", args.config_stt_language], env=env)

    if args.config_video_strategy:
        run_command([str(cli), "--set-video-strategy", args.config_video_strategy], env=env)

    if args.config_embeddings_provider:
        run_command([str(cli), "--set-embeddings-provider", args.config_embeddings_provider], env=env)
    if args.config_embeddings_model:
        run_command([str(cli), "--set-embeddings-model", args.config_embeddings_model], env=env)

    if args.config_console_log_level:
        run_command([str(cli), "--set-console-log-level", args.config_console_log_level], env=env)


def _persist_env_var(env_var: str, value: str) -> None:
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    _update_env_file(ENV_SH, env_var, value, style="sh")
    _update_env_file(ENV_PS1, env_var, value, style="ps1")


def _update_env_file(path: Path, env_var: str, value: str, *, style: str) -> None:
    if path.exists():
        lines = path.read_text().splitlines()
    else:
        lines = []

    new_lines: List[str] = []
    found = False
    for line in lines:
        if style == "sh" and line.startswith(f"export {env_var}="):
            new_lines.append(f'export {env_var}="{value}"')
            found = True
        elif style == "ps1" and line.startswith(f"$env:{env_var}"):
            new_lines.append(f'$env:{env_var} = "{value}"')
            found = True
        else:
            new_lines.append(line)

    if not found:
        if style == "sh":
            new_lines.append(f'export {env_var}="{value}"')
        else:
            new_lines.append(f'$env:{env_var} = "{value}"')

    path.write_text("\n".join(new_lines).strip() + "\n")


def download_model(provider: str | None, model: str | None, env: dict) -> None:
    if not provider or not model:
        log("#FALLBACK: Skipping model download because provider/model is missing.")
        return

    if provider == "ollama":
        if shutil.which("ollama") is None:
            log("#FALLBACK: Ollama not found; cannot download model.")
            return
        run_command(["ollama", "pull", model], env=env)
        return

    if provider in {"huggingface", "mlx", "lmstudio", "openai-compatible"}:
        log(
            "#FALLBACK: Model download for this provider is not automated yet. "
            "Use the provider's own tooling to download the model."
        )
        return

    log(f"#FALLBACK: Model download is not supported for provider '{provider}'.")
    try:
        return json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return None


def resolve_host_python() -> str:
    if not getattr(sys, "frozen", False):
        return sys.executable

    for candidate in ("python3", "python"):
        path = shutil.which(candidate)
        if path:
            return path
    abort("Python 3.10+ is required on PATH to run the installer.")
    return sys.executable


def install(args: argparse.Namespace) -> None:
    default_profile, profiles = load_profiles()
    profile = args.profile or default_profile
    extras = []
    if args.extras:
        extras = [x.strip() for x in args.extras.split(",") if x.strip()]
    else:
        if profile not in profiles:
            abort(f"Unknown profile '{profile}'. Available: {', '.join(profiles.keys())}")
        extras = profiles[profile]

    prefix = Path(args.prefix) if args.prefix else default_prefix()
    venv_dir, bin_dir, python_bin = venv_paths(prefix)
    package_spec = build_package_spec(args.version, extras)

    if args.dry_run:
        log("Dry run - no changes will be made.")
        log(f"Prefix: {prefix}")
        log(f"Venv: {venv_dir}")
        log(f"Package: {package_spec}")
        return

    ensure_dir(prefix)

    if args.recreate_venv:
        if not args.yes:
            abort("Refusing to recreate venv without --yes.")
        if venv_dir.exists():
            shutil.rmtree(venv_dir)

    host_python = resolve_host_python()
    if not python_bin.exists():
        run_command([host_python, "-m", "venv", str(venv_dir)])

    env = dict(os.environ)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    if not args.skip_pip_upgrade:
        run_command([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"], env=env)

    pip_cmd = [str(python_bin), "-m", "pip", "install"]
    if args.index_url:
        pip_cmd.extend(["--index-url", args.index_url])
    if args.extra_index_url:
        for extra_url in args.extra_index_url:
            pip_cmd.extend(["--extra-index-url", extra_url])
    pip_cmd.append(package_spec)
    run_command(pip_cmd, env=env)

    state = {
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "prefix": str(prefix),
        "venv": str(venv_dir),
        "package_spec": package_spec,
        "profile": profile if not args.extras else "custom",
        "extras": extras,
        "python": host_python,
        "platform": platform.platform(),
    }
    write_state(prefix, state)

    cli = resolve_cli(bin_dir, "abstractcore")
    base_url = tuple(args.config_base_url) if args.config_base_url else None
    if args.config_provider or args.config_model or args.config_api_key or base_url:
        if not cli:
            abort("abstractcore CLI not found; cannot apply configuration.")
        apply_config(
            cli=cli,
            provider=args.config_provider,
            model=args.config_model,
            api_keys=args.config_api_key or [],
            base_url=base_url,
            env=env,
        )
    if any(
        [
            args.config_vision_provider,
            args.config_vision_fallback,
            args.config_disable_vision,
            args.config_download_vision_model,
            args.config_audio_strategy,
            args.config_stt_backend_id,
            args.config_stt_language,
            args.config_video_strategy,
            args.config_embeddings_provider,
            args.config_embeddings_model,
            args.config_console_log_level,
        ]
    ):
        if not cli:
            abort("abstractcore CLI not found; cannot apply configuration.")
        apply_extra_config(cli, args, env)

    if args.configure:
        if not cli:
            abort("abstractcore CLI not found; cannot run --config.")
        run_command([str(cli), "--config"])

    if args.install_check:
        if not args.yes:
            abort("Refusing to run install checks without --yes.")
        if not cli:
            abort("abstractcore CLI not found; cannot run --install.")
        run_command([str(cli), "--install", "--yes"])

    if args.download_model:
        download_model(args.config_provider, args.config_model, env)

    log("Install complete.")
    log(f"Prefix: {prefix}")
    if cli:
        log(f"Next: {cli} --status")
    else:
        log("Next: Activate the venv and run abstractcore --status.")


def configure(args: argparse.Namespace) -> None:
    prefix = Path(args.prefix) if args.prefix else default_prefix()
    _, bin_dir, _ = venv_paths(prefix)
    cli = resolve_cli(bin_dir, "abstractcore")

    if not cli:
        abort("abstractcore CLI not found in the install prefix. Install first.")

    env = dict(os.environ)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    base_url = tuple(args.config_base_url) if args.config_base_url else None
    apply_config(
        cli=cli,
        provider=args.config_provider,
        model=args.config_model,
        api_keys=args.config_api_key or [],
        base_url=base_url,
        env=env,
    )

    if args.config_vision_provider:
        provider, model = args.config_vision_provider
        run_command([str(cli), "--set-vision-provider", provider, model], env=env)
    if args.config_vision_fallback:
        provider, model = args.config_vision_fallback
        run_command([str(cli), "--add-vision-fallback", provider, model], env=env)
    if args.config_disable_vision:
        run_command([str(cli), "--disable-vision"], env=env)
    if args.config_download_vision_model:
        run_command([str(cli), "--download-vision-model", args.config_download_vision_model], env=env)

    if args.config_audio_strategy:
        run_command([str(cli), "--set-audio-strategy", args.config_audio_strategy], env=env)
    if args.config_stt_backend_id:
        run_command([str(cli), "--set-stt-backend-id", args.config_stt_backend_id], env=env)
    if args.config_stt_language:
        run_command([str(cli), "--set-stt-language", args.config_stt_language], env=env)

    if args.config_video_strategy:
        run_command([str(cli), "--set-video-strategy", args.config_video_strategy], env=env)

    if args.config_embeddings_provider:
        run_command([str(cli), "--set-embeddings-provider", args.config_embeddings_provider], env=env)
    if args.config_embeddings_model:
        run_command([str(cli), "--set-embeddings-model", args.config_embeddings_model], env=env)

    if args.config_console_log_level:
        run_command([str(cli), "--set-console-log-level", args.config_console_log_level], env=env)

    if args.install_check:
        run_command([str(cli), "--install", "--yes"], env=env)

    if args.download_model:
        download_model(args.config_provider, args.config_model, env)

    log("Configuration complete.")


def status(args: argparse.Namespace) -> None:
    prefix = Path(args.prefix) if args.prefix else default_prefix()
    venv_dir, bin_dir, python_bin = venv_paths(prefix)
    state = read_state(prefix)

    log(f"Prefix: {prefix}")
    log(f"Venv: {venv_dir} ({'present' if venv_dir.exists() else 'missing'})")
    if state:
        log(f"Package: {state.get('package_spec', 'unknown')}")
        log(f"Installed at: {state.get('installed_at', 'unknown')}")
    else:
        log("No install state found.")

    cli = resolve_cli(bin_dir, "abstractcore")
    if cli and args.check:
        run_command([str(cli), "--status"])
    elif args.check and not cli:
        abort("abstractcore CLI not found; cannot run --status.")


def uninstall(args: argparse.Namespace) -> None:
    if not args.yes:
        abort("Refusing to uninstall without --yes.")

    prefix = Path(args.prefix) if args.prefix else default_prefix()
    venv_dir, _, _ = venv_paths(prefix)

    if args.remove_all:
        if prefix.exists():
            shutil.rmtree(prefix)
            log(f"Removed {prefix}")
        else:
            log("Nothing to remove.")
        return

    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        log(f"Removed {venv_dir}")
    else:
        log("Venv not found; nothing to remove.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AbstractCore installer (test).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["install", "status", "uninstall", "configure"],
        default="install",
        help="Action to perform.",
    )
    parser.add_argument("--prefix", help="Install prefix directory.")
    parser.add_argument("--version", default="latest", help="AbstractCore version.")
    parser.add_argument("--profile", help="Extras profile name.")
    parser.add_argument("--extras", help="Comma-separated extras list.")
    parser.add_argument("--configure", action="store_true", help="Run abstractcore --config.")
    parser.add_argument("--install-check", action="store_true", help="Run abstractcore --install --yes.")
    parser.add_argument("--config-provider", help="Set global default provider (via abstractcore config).")
    parser.add_argument("--config-model", help="Set global default model (via abstractcore config).")
    parser.add_argument(
        "--config-api-key",
        nargs=2,
        action="append",
        metavar=("PROVIDER", "KEY"),
        help="Persist provider API keys (repeatable).",
    )
    parser.add_argument(
        "--config-base-url",
        nargs=2,
        metavar=("PROVIDER", "URL"),
        help="Persist provider base URL (writes to an env file).",
    )
    parser.add_argument(
        "--config-vision-provider",
        nargs=2,
        metavar=("PROVIDER", "MODEL"),
        help="Set vision fallback provider/model.",
    )
    parser.add_argument(
        "--config-vision-fallback",
        nargs=2,
        metavar=("PROVIDER", "MODEL"),
        help="Add a backup vision fallback provider/model.",
    )
    parser.add_argument(
        "--config-disable-vision",
        action="store_true",
        help="Disable vision fallback.",
    )
    parser.add_argument(
        "--config-download-vision-model",
        nargs="?",
        const="blip-base-caption",
        metavar="MODEL",
        help="Download a local vision caption model.",
    )
    parser.add_argument(
        "--config-audio-strategy",
        choices=["native_only", "speech_to_text", "auto"],
        help="Set audio handling strategy for attachments.",
    )
    parser.add_argument(
        "--config-stt-backend-id",
        help="Set preferred STT backend id.",
    )
    parser.add_argument(
        "--config-stt-language",
        help="Set default STT language hint.",
    )
    parser.add_argument(
        "--config-video-strategy",
        choices=["native_only", "frames_caption", "auto"],
        help="Set video handling strategy for attachments.",
    )
    parser.add_argument(
        "--config-embeddings-provider",
        help="Set embeddings provider.",
    )
    parser.add_argument(
        "--config-embeddings-model",
        help="Set embeddings model.",
    )
    parser.add_argument(
        "--config-console-log-level",
        help="Set console log level (NONE, ERROR, WARNING, INFO, DEBUG).",
    )
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Attempt to download the selected model (best effort).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changes.")
    parser.add_argument("--recreate-venv", action="store_true", help="Recreate the venv.")
    parser.add_argument("--skip-pip-upgrade", action="store_true", help="Skip pip upgrade.")
    parser.add_argument("--index-url", help="Override pip index URL.")
    parser.add_argument(
        "--extra-index-url",
        action="append",
        help="Additional pip index URL (repeatable).",
    )
    parser.add_argument("--check", action="store_true", help="Run abstractcore --status in status mode.")
    parser.add_argument("--remove-all", action="store_true", help="Remove the full install directory.")
    parser.add_argument("--yes", action="store_true", help="Acknowledge destructive actions.")
    return parser


def main(argv: Iterable[str]) -> None:
    ensure_python_version()
    parser = build_parser()
    args = parser.parse_args(list(argv))

    if args.command == "install":
        install(args)
    elif args.command == "status":
        status(args)
    elif args.command == "uninstall":
        uninstall(args)
    elif args.command == "configure":
        configure(args)
    else:
        abort(f"Unknown command: {args.command}")


def run_installer(argv: Iterable[str], log_callback=None) -> int:
    previous = _LOG_CALLBACK
    if log_callback:
        set_log_callback(log_callback)
    try:
        main(argv)
        return 0
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return code
    except Exception as exc:  # noqa: BLE001
        log(f"Error: {exc}")
        return 1
    finally:
        set_log_callback(previous)


if __name__ == "__main__":
    main(sys.argv[1:])

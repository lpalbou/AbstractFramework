"""install.sh --server (root backlog 1067, one-command server deployment).

Simulated with stubs (uname -s = Linux, loginctl, systemctl, lspci, nvidia-smi, tailscale) and
`--print`, so nothing is installed or changed: the plan must contain every administrator step on a
fresh server, and none of them on a server where each part is already in place (idempotence)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = ROOT / "scripts" / "install.sh"


def _stubs(tmp_path: Path, *, os_name: str = "Linux", linger: str = "no", nvidia: bool = False,
           lspci_nvidia: bool = True, tailscale: bool = False, funnel_on: bool = False,
           tailnet_only: bool = False, driver_package: bool = False, port: int = 18999,
           system_pkgs: tuple = ()) -> Path:
    fake = tmp_path / "fakebin"
    fake.mkdir(parents=True, exist_ok=True)
    stubs = {
        "uname": f'#!/bin/sh\ncase "$1" in -s) echo {os_name} ;; -m) echo x86_64 ;; *) /usr/bin/uname "$@" ;; esac\n',
        "loginctl": f"#!/bin/sh\necho Linger={linger}\n",
        "systemctl": "#!/bin/sh\nexit 0\n",
        "cc": "#!/bin/sh\nexit 0\n",
        "lspci": "#!/bin/sh\n" + ("echo '01:00.0 VGA compatible controller: NVIDIA Corporation TU104GL [Quadro RTX 5000]'\n" if lspci_nvidia else "echo '00:02.0 VGA compatible controller: Cirrus Logic'\n"),
        # No driver package unless asked (a Mac or CI host may have no dpkg at all).
        # dpkg-query answers per package: the NVIDIA driver, and the server prerequisites in `system_pkgs`.
        "dpkg-query": "#!/bin/sh\nfor last; do :; done\ncase \"$last\" in\n"
                      + ("  nvidia-driver-*) echo 'install ok installed nvidia-driver-595-open' ;;\n" if driver_package else "")
                      + "".join(f"  {p}) printf 'install ok installed' ;;\n" for p in system_pkgs)
                      + "  *) exit 1 ;;\nesac\n",
        "apt-get": "#!/bin/sh\nexit 0\n",
    }
    if nvidia:
        stubs["nvidia-smi"] = '#!/bin/sh\ncase "$*" in *query-gpu*) echo "595.99.02, 7.5, Quadro RTX 5000" ;; *) echo "GPU 0: Quadro RTX 5000" ;; esac\n'
    if tailscale:
        status = json.dumps({"BackendState": "Running", "Self": {"DNSName": "af-server.tail1234.ts.net."}})
        host = "af-server.tail1234.ts.net:443"
        serve = {"TCP": {"443": {"HTTPS": True}}, "Web": {host: {"Handlers": {"/": {"Proxy": f"http://127.0.0.1:{port}"}}}}}
        if funnel_on and not tailnet_only:
            serve["AllowFunnel"] = {host: True}
        funnel = json.dumps(serve) if (funnel_on or tailnet_only) else "{}"
        stubs["tailscale"] = (
            "#!/bin/sh\ncase \"$1\" in\n"
            f"  status) echo '{status}' ;;\n"
            f"  funnel) echo '{funnel}' ;;\n"
            "  version) echo 1.90.0 ;;\n  *) exit 0 ;;\nesac\n"
        )
    for name, body in stubs.items():
        (fake / name).write_text(body)
        (fake / name).chmod(0o755)
    return fake


def _run(tmp_path: Path, fake: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", str(INSTALL_SH), *args],
        capture_output=True, text=True, timeout=300,
        env={"HOME": str(tmp_path), "PATH": f"{fake}:/usr/bin:/bin:/usr/sbin:/sbin", "TERM": "dumb"},
    )


def test_a_fresh_gpu_server_plans_the_driver_linger_tailscale_and_funnel(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path), "--server", "--gpu", "--tailscale-funnel", "--port", "18999", "--print")
    out = proc.stdout
    assert proc.returncode == 0, proc.stderr + out[-3000:]
    for want in (
        "apt-get -o DPkg::Lock::Timeout=600 install -y ubuntu-drivers-common",
        "NEEDRESTART_MODE=a ubuntu-drivers install",
        "start at login: yes (--server",
        "sudo loginctl enable-linger",
        "curl -fsSL https://tailscale.com/install.sh | sh",
        "sudo tailscale up --operator=",
        "tailscale funnel --bg --https=443 http://127.0.0.1:18999",
        "network set --allowed-origins",
    ):
        assert want in out, want
    assert "Start AbstractFramework automatically when you log in?" not in out  # --server asks nothing


def test_a_server_where_everything_is_in_place_runs_no_administrator_step(tmp_path: Path) -> None:
    fake = _stubs(tmp_path, linger="yes", nvidia=True, tailscale=True, funnel_on=True, system_pkgs=("libatomic1", "zstd"))
    proc = _run(tmp_path, fake, "--server", "--gpu", "--tailscale-funnel", "--port", "18999", "--print")
    out = proc.stdout
    assert proc.returncode == 0, proc.stderr + out[-3000:]
    for gone in ("ubuntu-drivers", "enable-linger", "tailscale.com/install.sh", "tailscale up", "funnel --bg", "install -y libatomic1", "install -y zstd"):
        assert gone not in out, gone
    for want in ("NVIDIA driver: present", "lingering is already on", "Tailscale: signed in",
                 "Funnel: https://af-server.tail1234.ts.net already serves 127.0.0.1:18999"):
        assert want in out, want


def test_without_an_nvidia_gpu_the_driver_is_left_alone(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path, lspci_nvidia=False), "--server", "--gpu", "--print")
    assert proc.returncode == 0, proc.stderr
    assert "ubuntu-drivers" not in proc.stdout and "no NVIDIA GPU on the PCI bus" in proc.stdout


def test_server_mode_is_linux_only_and_needs_the_service(tmp_path: Path) -> None:
    mac = _run(tmp_path, _stubs(tmp_path / "m", os_name="Darwin"), "--server", "--print")
    assert mac.returncode != 0 and "for a Linux server" in mac.stderr
    no_svc = _run(tmp_path, _stubs(tmp_path / "l"), "--server", "--no-service", "--print")
    assert no_svc.returncode != 0 and "cannot be combined with --no-service" in no_svc.stderr
    alone = _run(tmp_path, _stubs(tmp_path / "f"), "--tailscale-funnel", "--print")
    assert alone.returncode != 0 and "goes with --server" in alone.stderr


def test_a_tailnet_only_serve_is_not_mistaken_for_funnel(tmp_path: Path) -> None:
    fake = _stubs(tmp_path, linger="yes", nvidia=True, tailscale=True, tailnet_only=True)
    proc = _run(tmp_path, fake, "--server", "--tailscale-funnel", "--port", "18999", "--print")
    assert proc.returncode == 0, proc.stderr
    assert "tailscale funnel --bg --https=443 http://127.0.0.1:18999" in proc.stdout and "already serves" not in proc.stdout


def test_a_driver_installed_but_not_loaded_asks_for_the_reboot_not_apt_again(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path, driver_package=True), "--server", "--gpu", "--port", "18999", "--print")
    assert proc.returncode == 0, proc.stderr
    assert "ubuntu-drivers" not in proc.stdout and "installed but not loaded yet" in proc.stdout


def test_server_cannot_skip_the_start(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path), "--server", "--no-start", "--print")
    assert proc.returncode != 0 and "cannot be combined with --no-start" in proc.stderr


def test_apt_runs_non_interactive(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path), "--server", "--gpu", "--port", "18999", "--print")
    assert "sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get" in proc.stdout


def test_a_fresh_server_installs_libatomic1_and_zstd_while_it_has_sudo(tmp_path: Path) -> None:
    # LM Studio's Linux daemon links libatomic.so.1 and Ollama's Linux build is a .tar.zst: installed
    # by --server so the console never needs an administrator for them (gateway PRs #31/#32).
    proc = _run(tmp_path, _stubs(tmp_path), "--server", "--port", "18999", "--print")
    assert proc.returncode == 0, proc.stderr
    assert "sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get -o DPkg::Lock::Timeout=600 install -y libatomic1 zstd" in proc.stdout


def test_server_prerequisites_already_there_are_not_installed_again(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path, system_pkgs=("libatomic1",)), "--server", "--port", "18999", "--print")
    assert proc.returncode == 0, proc.stderr
    assert "install -y zstd" in proc.stdout and "install -y libatomic1" not in proc.stdout
    proc = _run(tmp_path, _stubs(tmp_path, system_pkgs=("libatomic1", "zstd")), "--server", "--port", "18999", "--print")
    assert "already installed: libatomic1 zstd" in proc.stdout and "install -y" not in proc.stdout.split("Server prerequisites")[1].split("\n\n")[0]


# --- instances: a second gateway on the same host (root backlog 1074) -------------------------


def test_an_instance_is_self_contained_its_unit_data_tool_dir_and_funnel_port(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path, port=8443, tailscale=True, linger="yes"), "--server", "--instance", "fresh",
                "--port", "8443", "--tailscale-funnel", "--print")
    out = proc.stdout
    assert proc.returncode == 0, proc.stderr + out[-3000:]
    data = f"{tmp_path}/.local/share/abstractgateway-fresh"
    for want in (
        "abstractgateway-fresh.service",
        data,
        f"{data}/bin/abstractgateway --instance fresh service status",
        f"export ABSTRACTGATEWAY_INSTANCE=fresh UV_TOOL_DIR={data}/tool UV_TOOL_BIN_DIR={data}/bin",
        "tailscale funnel --bg --https=8443 http://127.0.0.1:8443",
        "network set --allowed-origins https://af-server.tail1234.ts.net:8443",
        "uninstall.sh | sh -s -- --instance fresh   (this instance only",
    ):
        assert want in out, want
    # The default gateway's unit, PATH and pointer are never touched by an instance.
    assert "abstractgateway.service" not in out.replace("abstractgateway-fresh.service", "")
    assert "update-shell" not in out
    # uninstall.sh takes --instance but not --server (it refuses an unknown argument).
    assert "uninstall.sh | sh -s -- --instance fresh --server" not in out
    assert not (tmp_path / ".abstractframework" / "gateway.json").exists()


def test_the_default_install_keeps_its_names(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path), "--server", "--port", "18999", "--print")
    assert proc.returncode == 0, proc.stderr + proc.stdout[-3000:]
    out = proc.stdout.replace("abstractgateway-console", "").replace("abstractgateway-config", "")
    assert "abstractgateway-" not in out and "--instance" not in out and "UV_TOOL_DIR" not in out


def test_an_instance_needs_its_own_port_and_a_valid_name(tmp_path: Path) -> None:
    no_port = _run(tmp_path, _stubs(tmp_path / "a"), "--server", "--instance", "fresh", "--print")
    assert no_port.returncode != 0 and "needs --port" in no_port.stderr + no_port.stdout
    bad = _run(tmp_path, _stubs(tmp_path / "b"), "--server", "--instance", "../x", "--port", "8443", "--print")
    assert bad.returncode != 0 and "lower-case letters" in bad.stderr + bad.stdout


def test_a_funnel_https_port_outside_what_funnel_allows_is_refused(tmp_path: Path) -> None:
    proc = _run(tmp_path, _stubs(tmp_path, port=8443), "--server", "--instance", "fresh", "--port", "8443",
                "--tailscale-funnel", "--funnel-https-port", "9000", "--print")
    assert proc.returncode == 0, proc.stderr + proc.stdout[-3000:]
    assert "Funnel allows 443, 8443 and 10000 only" in proc.stdout + proc.stderr
    assert "tailscale funnel --bg" not in proc.stdout


def test_uninstalling_an_instance_leaves_the_default_gateway_and_shared_folders(tmp_path: Path) -> None:
    data = tmp_path / ".local" / "share" / "abstractgateway-fresh"
    data.mkdir(parents=True)
    (data / "bootstrap.env").write_text("MODE=background\n")
    default = tmp_path / ".local" / "share" / "abstractgateway"
    default.mkdir(parents=True)
    (tmp_path / ".abstractassistant").mkdir()
    units = tmp_path / ".config" / "systemd" / "user"
    units.mkdir(parents=True)
    unit = f"[Service]\nExecStart={data}/bin/abstractgateway --instance fresh serve\n"
    (units / "abstractgateway-fresh.service").write_text(unit)
    (units / "abstractgateway.service").write_text("[Service]\nExecStart=%h/.local/bin/abstractgateway serve\n")
    proc = _run(tmp_path, _stubs(tmp_path), "--uninstall", "--purge", "--instance", "fresh", "--yes", "--print")
    out = proc.stdout
    assert proc.returncode == 0, proc.stderr + out[-3000:]
    assert f"rm -rf {data}" in out.replace("/private", "") or f"rm -rf {data}" in out
    assert "systemctl --user disable --now abstractgateway-fresh.service" in out
    assert "abstractgateway.service" not in out.replace("abstractgateway-fresh.service", "")
    assert ".abstractassistant" not in out and ".abstractcode" not in out
    assert f"rm -rf {default}\n" not in out

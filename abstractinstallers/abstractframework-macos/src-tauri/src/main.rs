// AbstractFramework macOS Installer (Rust/Tauri backend)
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread::sleep;
use std::time::Duration;
use rfd::FileDialog;
use tauri::{AppHandle, Emitter, Manager, State};

const MIN_PYTHON_MAJOR: u8 = 3;
const MIN_PYTHON_MINOR: u8 = 10;
const PYTHON_DOWNLOAD_URL: &str = "https://www.python.org/downloads/macos/";
const PYTHON_MACOS_PKG_URL: &str =
    "https://www.python.org/ftp/python/3.12.10/python-3.12.10-macos11.pkg";
const PYTHON_MACOS_VERSION: &str = "3.12.10";
const PYTHON_MACOS_MIN_MAJOR: u8 = 11;

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Manifest {
    manifest_version: u32,
    channel: String,
    released_at: String,
    components: Vec<Component>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Component {
    id: String,
    name: String,
    description: Option<String>,
    group: Option<String>,
    #[serde(rename = "type")]
    kind: String,
    package: String,
    version: String,
    extras: Vec<String>,
    os: Vec<String>,
    arch: Vec<String>,
    dependencies: Vec<String>,
    default_selected: bool,
    available: bool,
    unavailable_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct Defaults {
    install_dir: String,
    os: String,
    arch: String,
}

#[derive(Debug, Clone, Deserialize)]
struct InstallRequest {
    mode: String,
    component_ids: Vec<String>,
    install_dir: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
struct ApiKeyInput {
    provider: String,
    key: String,
}

#[derive(Debug, Clone, Deserialize)]
struct SetupRequest {
    install_dir: Option<String>,
    global_provider: Option<String>,
    global_model: Option<String>,
    base_url_provider: Option<String>,
    base_url: Option<String>,
    env_apply_launchd: Option<bool>,
    env_apply_shell: Option<bool>,
    api_keys: Vec<ApiKeyInput>,
    vision_mode: Option<String>,
    vision_provider: Option<String>,
    vision_model: Option<String>,
    vision_fallback_provider: Option<String>,
    vision_fallback_model: Option<String>,
    vision_download_model: Option<String>,
    audio_strategy: Option<String>,
    stt_backend_id: Option<String>,
    stt_language: Option<String>,
    video_strategy: Option<String>,
    embeddings_provider: Option<String>,
    embeddings_model: Option<String>,
    log_level: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
struct InstallerEvent {
    kind: String,
    message: String,
    code: Option<String>,
    action_url: Option<String>,
    component_id: Option<String>,
    component_name: Option<String>,
    stage: Option<String>,
    current: Option<usize>,
    total: Option<usize>,
    components: Option<Vec<PlanComponent>>,
}

#[derive(Debug, Clone, Serialize)]
struct PlanComponent {
    id: String,
    name: String,
}

#[derive(Default)]
struct InstallState {
    busy: Arc<Mutex<bool>>,
    cancel: Arc<AtomicBool>,
}

#[tauri::command]
fn load_manifest() -> Result<Manifest, String> {
    load_manifest_inner()
}

#[tauri::command]
fn get_defaults() -> Defaults {
    Defaults {
        install_dir: default_install_root()
            .to_string_lossy()
            .to_string(),
        os: std::env::consts::OS.to_string(),
        arch: current_arch().to_string(),
    }
}

#[tauri::command]
fn pick_install_dir() -> Option<String> {
    let picked = FileDialog::new()
        .set_directory(default_install_root())
        .pick_folder();
    picked.map(|path| path.to_string_lossy().to_string())
}

#[tauri::command]
fn open_url(url: String) -> Result<(), String> {
    let trimmed = url.trim();
    if trimmed.is_empty() {
        return Err("URL is empty.".into());
    }
    if !trimmed.starts_with("https://") {
        return Err("Only https URLs are allowed.".into());
    }
    Command::new("open")
        .arg(trimmed)
        .output()
        .map_err(|err| format!("Unable to open URL: {err}"))?;
    Ok(())
}

#[tauri::command]
fn download_python_installer(
    app: AppHandle,
    install_dir: Option<String>,
) -> Result<String, String> {
    let install_root = resolve_install_root(install_dir);
    let download_dir = install_root.join("downloads");
    std::fs::create_dir_all(&download_dir)
        .map_err(|err| format!("Unable to create download directory: {err}"))?;

    let pkg_url = PYTHON_MACOS_PKG_URL;
    let filename = python_pkg_filename(pkg_url)?;
    let pkg_path = download_dir.join(filename);

    if pkg_path.exists() {
        emit_log(
            &app,
            "info",
            &format!(
                "Using cached Python installer at {}",
                pkg_path.display()
            ),
        );
    } else {
        ensure_macos_supported(&app)?;
        ensure_curl_available()?;
        emit_log(
            &app,
            "info",
            &format!("Downloading Python {PYTHON_MACOS_VERSION} installer..."),
        );
        let mut cmd = Command::new("curl");
        cmd.arg("-L")
            .arg("--fail")
            .arg("--retry")
            .arg("3")
            .arg("--output")
            .arg(&pkg_path)
            .arg(pkg_url);
        let cancel = Arc::new(AtomicBool::new(false));
        run_command(&app, cmd, "curl -L python installer", &cancel)?;
    }

    emit_log(&app, "info", "Opening Python installer...");
    Command::new("open")
        .arg(&pkg_path)
        .output()
        .map_err(|err| format!("Unable to open installer: {err}"))?;

    Ok(pkg_path.to_string_lossy().to_string())
}

#[tauri::command]
fn start_install(
    app: AppHandle,
    request: InstallRequest,
    state: State<InstallState>,
) -> Result<(), String> {
    let busy = state.busy.clone();
    let cancel_flag = state.cancel.clone();
    state.cancel.store(false, Ordering::SeqCst);
    {
        let mut lock = busy.lock().map_err(|_| "Install state lock poisoned")?;
        if *lock {
            return Err("An install is already running.".into());
        }
        *lock = true;
    }

    std::thread::spawn(move || {
        let result = run_install(&app, request, cancel_flag);
        {
            if let Ok(mut lock) = busy.lock() {
                *lock = false;
            }
        }
        match result {
            Ok(()) => emit_status(&app, "Install complete."),
            Err(err) => {
                if err == "Install cancelled." {
                    emit_status(&app, "Install cancelled.");
                } else {
                    emit_status(&app, &format!("Install failed: {err}"));
                }
            }
        }
    });

    Ok(())
}

#[tauri::command]
fn cancel_install(app: AppHandle, state: State<InstallState>) -> Result<(), String> {
    state.cancel.store(true, Ordering::SeqCst);
    emit_status(&app, "Cancel requested...");
    Ok(())
}

#[tauri::command]
fn start_setup(
    app: AppHandle,
    request: SetupRequest,
    state: State<InstallState>,
) -> Result<(), String> {
    let busy = state.busy.clone();
    {
        let mut lock = busy.lock().map_err(|_| "Install state lock poisoned")?;
        if *lock {
            return Err("An install or setup is already running.".into());
        }
        *lock = true;
    }

    std::thread::spawn(move || {
        let result = run_setup(&app, request);
        if let Ok(mut lock) = busy.lock() {
            *lock = false;
        }
        match result {
            Ok(()) => emit_status(&app, "Configuration complete."),
            Err(err) => emit_status(&app, &format!("Configuration failed: {err}")),
        }
    });

    Ok(())
}

#[tauri::command]
fn close_window(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.close().map_err(|err| err.to_string())?;
        Ok(())
    } else {
        Err("Main window not found.".into())
    }
}

fn run_install(app: &AppHandle, request: InstallRequest, cancel: Arc<AtomicBool>) -> Result<(), String> {
    emit_status(app, "Preparing install plan...");
    let manifest = load_manifest_inner()?;
    let components = resolve_components(&manifest, &request, app);

    if components.is_empty() {
        return Err("No installable components selected.".into());
    }

    let install_root = resolve_install_root(request.install_dir);

    std::fs::create_dir_all(&install_root)
        .map_err(|err| format!("Unable to create install directory: {err}"))?;
    emit_log(app, "info", &format!("Install root: {}", install_root.display()));

    let mut pip_components = Vec::new();
    let mut npm_components = Vec::new();

    for component in components {
        match component.kind.as_str() {
            "pip" => pip_components.push(component),
            "npm" => npm_components.push(component),
            other => emit_log(
                app,
                "warn",
                &format!("#FALLBACK: Unsupported component type '{other}' skipped."),
            ),
        }
    }

    let total = pip_components.len() + npm_components.len();
    emit_plan(app, &pip_components, &npm_components, total);

    if !pip_components.is_empty() {
        let python = detect_python(app)?;
        ensure_venv(app, &install_root, &python, &cancel)?;
        install_pip_components(app, &install_root, &pip_components, total, &cancel)?;
    }

    if !npm_components.is_empty() {
        if let Some(node) = detect_node(app) {
            install_npm_components(
                app,
                &install_root,
                &node,
                &npm_components,
                total,
                pip_components.len(),
                &cancel,
            )?;
        } else {
            emit_log(
                app,
                "warn",
                "#FALLBACK: Node.js not found; skipping web UI components.",
            );
        }
    }

    emit_log(app, "info", "Next steps: configure AbstractCore in step 5 of the installer.");
    Ok(())
}

fn run_setup(app: &AppHandle, request: SetupRequest) -> Result<(), String> {
    emit_status(app, "Starting configuration...");
    let install_root = resolve_install_root(request.install_dir);
    let venv_python = install_root.join("python").join(".venv").join("bin").join("python");
    if !venv_python.exists() {
        return Err("Python venv not found. Install the framework first.".into());
    }
    if !is_abstractcore_installed(&venv_python) {
        return Err("AbstractCore is not installed in this environment.".into());
    }

    let cli_path = resolve_abstractcore_cli(&venv_python);
    let cancel = Arc::new(AtomicBool::new(false));
    let mut env_vars: HashMap<String, String> = HashMap::new();

    let base_url = request.base_url.unwrap_or_default();
    let mut base_provider = request.base_url_provider.unwrap_or_default();
    let provider = request.global_provider.unwrap_or_default();
    let model = request.global_model.unwrap_or_default();
    let apply_launchd = request.env_apply_launchd.unwrap_or(false);
    let apply_shell = request.env_apply_shell.unwrap_or(false);

    if base_provider.trim().is_empty() && !base_url.trim().is_empty() {
        base_provider = provider.clone();
    }

    if !base_url.trim().is_empty() {
        let provider_trimmed = base_provider.trim();
        let url_trimmed = base_url.trim();
        if provider_trimmed.is_empty() {
            emit_log(
                app,
                "warn",
                "#FALLBACK: Base URL provided but default provider is missing.",
            );
        } else if let Some(env_var) = base_url_env_var(provider_trimmed) {
            env_vars.insert(env_var.to_string(), url_trimmed.to_string());
            persist_env_var(env_var, url_trimmed)?;
            emit_log(
                app,
                "info",
                &format!("Saved {env_var} to AbstractCore env files."),
            );
        } else {
            emit_log(
                app,
                "warn",
                &format!("#FALLBACK: Base URL not supported for provider '{provider_trimmed}'."),
            );
        }
    }

    if (apply_launchd || apply_shell) && env_vars.is_empty() {
        emit_log(
            app,
            "warn",
            "#FALLBACK: No Base URL provided; environment variables not applied.",
        );
    }
    if !base_url.trim().is_empty() && !apply_launchd && !apply_shell {
        emit_log(
            app,
            "warn",
            "#FALLBACK: Base URL provided but env persistence is disabled; future processes will not see it.",
        );
    }

    if apply_shell && !env_vars.is_empty() {
        if let Err(err) = apply_shell_env(&env_vars) {
            emit_log(app, "warn", &format!("#FALLBACK: {err}"));
        }
    }
    if apply_launchd && !env_vars.is_empty() {
        if let Err(err) = apply_launchd_env(app, &env_vars) {
            emit_log(app, "warn", &format!("#FALLBACK: {err}"));
        }
    }
    if !provider.trim().is_empty() && !model.trim().is_empty() {
        let arg = format!("{}/{}", provider.trim(), model.trim());
        run_abstractcore(
            app,
            &venv_python,
            cli_path.as_deref(),
            &["--set-global-default", &arg],
            "abstractcore --set-global-default PROVIDER/MODEL",
            &env_vars,
            &cancel,
        )?;
    } else if !provider.trim().is_empty() || !model.trim().is_empty() {
        emit_log(
            app,
            "warn",
            "#FALLBACK: Skipping default model because provider/model is incomplete.",
        );
    }

    let allowed_keys = ["openai", "anthropic", "openrouter", "portkey"];
    for api_key in request.api_keys {
        let provider_key = api_key.provider.trim().to_lowercase();
        let key = api_key.key.trim();
        if key.is_empty() {
            continue;
        }
        if !allowed_keys.contains(&provider_key.as_str()) {
            emit_log(
                app,
                "warn",
                &format!(
                    "#FALLBACK: API key provider '{provider_key}' is not supported by the installer."
                ),
            );
            continue;
        }
        run_abstractcore(
            app,
            &venv_python,
            cli_path.as_deref(),
            &["--set-api-key", api_key.provider.trim(), key],
            "abstractcore --set-api-key PROVIDER ****",
            &env_vars,
            &cancel,
        )?;
    }

    match request.vision_mode.as_deref() {
        Some("disable") => {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--disable-vision"],
                "abstractcore --disable-vision",
                &env_vars,
                &cancel,
            )?;
        }
        Some("enable") => {
            if let (Some(provider), Some(model)) = (request.vision_provider, request.vision_model) {
                let provider = provider.trim();
                let model = model.trim();
                if !provider.is_empty() && !model.is_empty() {
                    run_abstractcore(
                        app,
                        &venv_python,
                        cli_path.as_deref(),
                        &["--set-vision-provider", provider, model],
                        "abstractcore --set-vision-provider PROVIDER MODEL",
                        &env_vars,
                        &cancel,
                    )?;
                }
            }
            if let (Some(provider), Some(model)) =
                (request.vision_fallback_provider, request.vision_fallback_model)
            {
                let provider = provider.trim();
                let model = model.trim();
                if !provider.is_empty() && !model.is_empty() {
                    run_abstractcore(
                        app,
                        &venv_python,
                        cli_path.as_deref(),
                        &["--add-vision-fallback", provider, model],
                        "abstractcore --add-vision-fallback PROVIDER MODEL",
                        &env_vars,
                        &cancel,
                    )?;
                }
            }
            if let Some(model) = request.vision_download_model {
                let model = model.trim();
                if !model.is_empty() {
                    run_abstractcore(
                        app,
                        &venv_python,
                        cli_path.as_deref(),
                        &["--download-vision-model", model],
                        "abstractcore --download-vision-model MODEL",
                        &env_vars,
                        &cancel,
                    )?;
                }
            }
        }
        _ => {}
    }

    if let Some(strategy) = request.audio_strategy.as_deref() {
        let strategy = strategy.trim();
        if !strategy.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-audio-strategy", strategy],
                "abstractcore --set-audio-strategy STRATEGY",
                &env_vars,
                &cancel,
            )?;
        }
    }
    if let Some(backend) = request.stt_backend_id.as_deref() {
        let backend = backend.trim();
        if !backend.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-stt-backend-id", backend],
                "abstractcore --set-stt-backend-id BACKEND",
                &env_vars,
                &cancel,
            )?;
        }
    }
    if let Some(language) = request.stt_language.as_deref() {
        let language = language.trim();
        if !language.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-stt-language", language],
                "abstractcore --set-stt-language LANG",
                &env_vars,
                &cancel,
            )?;
        }
    }
    if let Some(strategy) = request.video_strategy.as_deref() {
        let strategy = strategy.trim();
        if !strategy.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-video-strategy", strategy],
                "abstractcore --set-video-strategy STRATEGY",
                &env_vars,
                &cancel,
            )?;
        }
    }
    if let Some(provider) = request.embeddings_provider.as_deref() {
        let provider = provider.trim();
        if !provider.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-embeddings-provider", provider],
                "abstractcore --set-embeddings-provider PROVIDER",
                &env_vars,
                &cancel,
            )?;
        }
    }
    if let Some(model) = request.embeddings_model.as_deref() {
        let model = model.trim();
        if !model.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-embeddings-model", model],
                "abstractcore --set-embeddings-model MODEL",
                &env_vars,
                &cancel,
            )?;
        }
    }
    if let Some(level) = request.log_level.as_deref() {
        let level = level.trim();
        if !level.is_empty() {
            run_abstractcore(
                app,
                &venv_python,
                cli_path.as_deref(),
                &["--set-console-log-level", &level.to_uppercase()],
                "abstractcore --set-console-log-level LEVEL",
                &env_vars,
                &cancel,
            )?;
        }
    }

    Ok(())
}

fn load_manifest_inner() -> Result<Manifest, String> {
    let raw = include_str!("../../manifest.local.json");
    serde_json::from_str(raw).map_err(|err| format!("Manifest parse failed: {err}"))
}

fn resolve_components(
    manifest: &Manifest,
    request: &InstallRequest,
    app: &AppHandle,
) -> Vec<Component> {
    let mut map: HashMap<String, Component> = HashMap::new();
    let mut order: HashMap<String, usize> = HashMap::new();
    for (idx, component) in manifest.components.iter().enumerate() {
        map.insert(component.id.clone(), component.clone());
        order.insert(component.id.clone(), idx);
    }

    let mut wanted = HashSet::new();
    if request.mode == "full" {
        wanted.insert("framework_full".to_string());
    } else {
        for id in &request.component_ids {
            wanted.insert(id.clone());
        }
    }

    let mut stack: Vec<String> = wanted.iter().cloned().collect();
    while let Some(current) = stack.pop() {
        if let Some(component) = map.get(&current) {
            for dep in &component.dependencies {
                if wanted.insert(dep.clone()) {
                    stack.push(dep.clone());
                }
            }
        }
    }

    let mut resolved = Vec::new();
    for id in wanted {
        if let Some(component) = map.get(&id).cloned() {
            if !component.available {
                emit_log(
                    app,
                    "warn",
                    &format!(
                        "#FALLBACK: {} unavailable ({})",
                        component.name,
                        component
                            .unavailable_reason
                            .clone()
                            .unwrap_or_else(|| "unknown reason".into())
                    ),
                );
                continue;
            }
            if !supported_on_current_os(&component) {
                emit_log(
                    app,
                    "warn",
                    &format!(
                        "#FALLBACK: {} not supported on this OS/arch.",
                        component.name
                    ),
                );
                continue;
            }
            resolved.push(component);
        }
    }

    resolved.sort_by_key(|component| order.get(&component.id).cloned().unwrap_or(usize::MAX));
    resolved
}

fn supported_on_current_os(component: &Component) -> bool {
    let os_ok = component.os.is_empty() || component.os.iter().any(|os| os == "mac");
    let arch_ok = component.arch.is_empty() || component.arch.iter().any(|arch| arch == current_arch());
    os_ok && arch_ok
}

fn detect_python(app: &AppHandle) -> Result<String, String> {
    let mut probes: Vec<PythonProbe> = Vec::new();
    let mut seen: HashSet<String> = HashSet::new();

    for path in python_candidate_paths() {
        let key = path.to_string_lossy().to_string();
        if !seen.insert(key.clone()) {
            continue;
        }
        if let Some(probe) = probe_python(&key) {
            probes.push(probe);
        }
    }

    for candidate in ["python3", "python"] {
        let key = candidate.to_string();
        if !seen.insert(key.clone()) {
            continue;
        }
        if let Some(probe) = probe_python(&key) {
            probes.push(probe);
        }
    }

    let mut eligible: Vec<&PythonProbe> = probes
        .iter()
        .filter(|probe| {
            probe.major > MIN_PYTHON_MAJOR
                || (probe.major == MIN_PYTHON_MAJOR && probe.minor >= MIN_PYTHON_MINOR)
        })
        .collect();
    eligible.sort_by_key(|probe| (probe.major, probe.minor, probe.patch, probe.priority));

    if let Some(best) = eligible.last() {
        if best.command == "python" {
            emit_log(app, "warn", "#FALLBACK: python3 not found; using python.");
        }
        emit_log(
            app,
            "info",
            &format!("Using Python {} ({})", best.raw, best.command),
        );
        return Ok(best.command.clone());
    }

    let found_versions: Vec<String> = probes
        .iter()
        .map(|probe| format!("{} ({})", probe.raw, probe.command))
        .collect();
    let detail = if found_versions.is_empty() {
        format!(
            "Python 3.10+ is required to install the framework. Click Download & Install to get Python {PYTHON_MACOS_VERSION}, then retry."
        )
    } else {
        format!(
            "Python 3.10+ is required to install the framework. Found: {}. Click Download & Install to get Python {PYTHON_MACOS_VERSION}, then retry.",
            found_versions.join(", ")
        )
    };
    emit_prereq(app, "python", &detail, Some(PYTHON_DOWNLOAD_URL));
    Err("Python 3.10+ is required to install the framework.".into())
}

fn detect_node(app: &AppHandle) -> Option<String> {
    let node_ok = Command::new("node")
        .arg("--version")
        .output()
        .ok()
        .map(|output| output.status.success())
        .unwrap_or(false);
    let npm_ok = Command::new("npm")
        .arg("--version")
        .output()
        .ok()
        .map(|output| output.status.success())
        .unwrap_or(false);

    if node_ok && npm_ok {
        emit_log(app, "info", "Node.js + npm detected for web UI installs.");
        Some("node".into())
    } else {
        None
    }
}

fn ensure_venv(
    app: &AppHandle,
    install_root: &Path,
    python: &str,
    cancel: &Arc<AtomicBool>,
) -> Result<(), String> {
    let venv_dir = install_root.join("python").join(".venv");
    std::fs::create_dir_all(install_root.join("python"))
        .map_err(|err| format!("Unable to create venv directory: {err}"))?;
    if venv_dir.exists() {
        emit_log(app, "info", "Using existing Python venv.");
        return Ok(());
    }
    emit_log(app, "info", "Creating Python venv...");
    let mut cmd = Command::new(python);
    cmd.arg("-m").arg("venv").arg(&venv_dir);
    run_command(app, cmd, "python -m venv", cancel)?;
    Ok(())
}

fn install_pip_components(
    app: &AppHandle,
    install_root: &Path,
    components: &[Component],
    total: usize,
    cancel: &Arc<AtomicBool>,
) -> Result<(), String> {
    let venv_python = install_root.join("python").join(".venv").join("bin").join("python");
    if !venv_python.exists() {
        return Err("Python venv not found after creation.".into());
    }

    emit_log(app, "info", "Upgrading pip...");
    let mut pip_upgrade = Command::new(&venv_python);
    pip_upgrade
        .arg("-m")
        .arg("pip")
        .arg("install")
        .arg("--upgrade")
        .arg("pip")
        .env("PIP_DISABLE_PIP_VERSION_CHECK", "1");
    run_command(app, pip_upgrade, "pip install --upgrade pip", cancel)?;

    emit_log(app, "info", "Installing Python components...");
    for (index, component) in components.iter().enumerate() {
        if cancel.load(Ordering::SeqCst) {
            return Err("Install cancelled.".into());
        }
        emit_component(app, component, "installing", index + 1, total);
        let mut spec = pip_spec(component);
        if component.version != "latest" {
            if let Some(false) = pypi_has_version(app, &component.package, &component.version) {
                emit_log(
                    app,
                    "warn",
                    &format!(
                        "#FALLBACK: {}=={} not found on PyPI; installing latest.",
                        component.package, component.version
                    ),
                );
                spec = pip_spec_with_version(component, None);
            }
        }
        let mut cmd = Command::new(&venv_python);
        cmd.arg("-m")
            .arg("pip")
            .arg("install")
            .arg(&spec)
            .env("PIP_DISABLE_PIP_VERSION_CHECK", "1");
        if let Err(err) = run_command(app, cmd, &format!("pip install {}", component.name), cancel) {
            emit_component(app, component, "failed", index + 1, total);
            return Err(err);
        }
        emit_component(app, component, "done", index + 1, total);
    }
    Ok(())
}

fn install_npm_components(
    app: &AppHandle,
    install_root: &Path,
    _node: &str,
    components: &[Component],
    total: usize,
    offset: usize,
    cancel: &Arc<AtomicBool>,
) -> Result<(), String> {
    let npm_prefix = install_root.join("node");
    std::fs::create_dir_all(&npm_prefix).map_err(|err| err.to_string())?;

    emit_log(
        app,
        "info",
        &format!("Installing web UIs to {}", npm_prefix.display()),
    );

    for (index, component) in components.iter().enumerate() {
        if cancel.load(Ordering::SeqCst) {
            return Err("Install cancelled.".into());
        }
        let current = index + 1 + offset;
        emit_component(app, component, "installing", current, total);
        let mut cmd = Command::new("npm");
        cmd.arg("install")
            .arg("-g")
            .arg(npm_spec(component))
            .env("NPM_CONFIG_PREFIX", &npm_prefix);
        if let Err(err) = run_command(app, cmd, &format!("npm install -g {}", component.package), cancel) {
            emit_component(app, component, "failed", current, total);
            return Err(err);
        }
        emit_component(app, component, "done", current, total);
    }

    Ok(())
}

fn pip_spec(component: &Component) -> String {
    pip_spec_with_version(component, Some(component.version.as_str()))
}

fn pip_spec_with_version(component: &Component, version: Option<&str>) -> String {
    let extras = if component.extras.is_empty() {
        "".to_string()
    } else {
        format!("[{}]", component.extras.join(","))
    };
    match version {
        None | Some("latest") => format!("{}{}", component.package, extras),
        Some(pinned) => format!("{}{}=={}", component.package, extras, pinned),
    }
}

fn npm_spec(component: &Component) -> String {
    if component.version == "latest" {
        component.package.clone()
    } else {
        format!("{}@{}", component.package, component.version)
    }
}

fn is_abstractcore_installed(venv_python: &Path) -> bool {
    Command::new(venv_python)
        .arg("-m")
        .arg("pip")
        .arg("show")
        .arg("abstractcore")
        .output()
        .ok()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

fn run_abstractcore(
    app: &AppHandle,
    venv_python: &Path,
    cli_path: Option<&Path>,
    args: &[&str],
    display: &str,
    env_vars: &HashMap<String, String>,
    cancel: &Arc<AtomicBool>,
) -> Result<(), String> {
    let mut cmd = if let Some(cli) = cli_path {
        Command::new(cli)
    } else {
        let mut cmd = Command::new(venv_python);
        cmd.arg("-m").arg("abstractcore");
        cmd
    };
    for arg in args {
        cmd.arg(arg);
    }
    for (key, value) in env_vars {
        cmd.env(key, value);
    }
    run_command(app, cmd, display, cancel)
}

fn resolve_abstractcore_cli(venv_python: &Path) -> Option<PathBuf> {
    let bin_dir = venv_python.parent()?;
    let candidates = [
        bin_dir.join("abstractcore"),
        bin_dir.join("abstractcore.exe"),
        bin_dir.join("abstractcore.cmd"),
        bin_dir.join("abstractcore.bat"),
    ];
    for candidate in candidates {
        if candidate.exists() {
            return Some(candidate);
        }
    }
    None
}

fn base_url_env_var(provider: &str) -> Option<&'static str> {
    match provider {
        "ollama" => Some("OLLAMA_BASE_URL"),
        "lmstudio" => Some("LMSTUDIO_BASE_URL"),
        "openai" => Some("OPENAI_BASE_URL"),
        "anthropic" => Some("ANTHROPIC_BASE_URL"),
        "openrouter" => Some("OPENROUTER_BASE_URL"),
        "openai-compatible" => Some("OPENAI_COMPATIBLE_BASE_URL"),
        "vllm" => Some("VLLM_BASE_URL"),
        "portkey" => Some("PORTKEY_BASE_URL"),
        _ => None,
    }
}

fn abstractcore_env_dir() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home)
        .join(".abstractcore")
        .join("config")
}

fn persist_env_var(env_var: &str, value: &str) -> Result<(), String> {
    let env_dir = abstractcore_env_dir();
    std::fs::create_dir_all(&env_dir)
        .map_err(|err| format!("Unable to create env directory: {err}"))?;
    update_env_file(&env_dir.join("abstractcore.env"), env_var, value, "sh")?;
    update_env_file(&env_dir.join("abstractcore.env.ps1"), env_var, value, "ps1")?;
    Ok(())
}

fn update_env_file(path: &Path, env_var: &str, value: &str, style: &str) -> Result<(), String> {
    let lines = if path.exists() {
        std::fs::read_to_string(path)
            .map_err(|err| format!("Unable to read env file: {err}"))?
            .lines()
            .map(|line| line.to_string())
            .collect::<Vec<String>>()
    } else {
        Vec::new()
    };

    let mut new_lines: Vec<String> = Vec::new();
    let mut found = false;
    for line in lines {
        if style == "sh" && line.starts_with(&format!("export {env_var}=")) {
            new_lines.push(format!("export {env_var}=\"{value}\""));
            found = true;
        } else if style == "ps1" && line.starts_with(&format!("$env:{env_var}")) {
            new_lines.push(format!("$env:{env_var} = \"{value}\""));
            found = true;
        } else {
            new_lines.push(line);
        }
    }
    if !found {
        if style == "sh" {
            new_lines.push(format!("export {env_var}=\"{value}\""));
        } else {
            new_lines.push(format!("$env:{env_var} = \"{value}\""));
        }
    }

    std::fs::write(path, new_lines.join("\n").trim().to_string() + "\n")
        .map_err(|err| format!("Unable to write env file: {err}"))?;
    Ok(())
}

fn apply_shell_env(env_vars: &HashMap<String, String>) -> Result<(), String> {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let zprofile = PathBuf::from(home).join(".zprofile");
    for (key, value) in env_vars {
        if key.ends_with("_BASE_URL") {
            update_env_file(&zprofile, key, value, "sh")?;
        }
    }
    Ok(())
}

fn apply_launchd_env(app: &AppHandle, env_vars: &HashMap<String, String>) -> Result<(), String> {
    let uid = current_uid().ok_or("Unable to determine user id for launchd.")?;
    let env = env_vars
        .iter()
        .filter(|(key, _)| key.ends_with("_BASE_URL"))
        .collect::<Vec<_>>();
    if env.is_empty() {
        return Err("No Base URL environment variables to apply.".into());
    }
    for (key, value) in &env {
        let _ = Command::new("launchctl")
            .arg("setenv")
            .arg(*key)
            .arg(*value)
            .output();
    }

    let plist_path = write_launchagent_plist(&env)?;
    let domain = format!("gui/{uid}");
    let _ = Command::new("launchctl")
        .arg("bootout")
        .arg(&domain)
        .arg(&plist_path)
        .output();
    let output = Command::new("launchctl")
        .arg("bootstrap")
        .arg(&domain)
        .arg(&plist_path)
        .output()
        .map_err(|err| format!("launchctl bootstrap failed: {err}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("launchctl bootstrap failed: {stderr}"));
    }
    let _ = Command::new("launchctl")
        .arg("kickstart")
        .arg("-k")
        .arg(format!("{domain}/com.abstractframework.env"))
        .output();
    emit_log(
        app,
        "info",
        "Applied Base URL env vars for GUI apps (may require log out/in).",
    );
    Ok(())
}

fn write_launchagent_plist(env_vars: &[(&String, &String)]) -> Result<PathBuf, String> {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let dir = PathBuf::from(home)
        .join("Library")
        .join("LaunchAgents");
    std::fs::create_dir_all(&dir)
        .map_err(|err| format!("Unable to create LaunchAgents dir: {err}"))?;
    let path = dir.join("com.abstractframework.env.plist");

    let mut env_block = String::new();
    for (key, value) in env_vars {
        env_block.push_str(&format!(
            "    <key>{}</key>\n    <string>{}</string>\n",
            xml_escape(key),
            xml_escape(value)
        ));
    }

    let plist = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.abstractframework.env</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/true</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
{env_block}  </dict>
</dict>
</plist>
"#
    );
    std::fs::write(&path, plist).map_err(|err| format!("Unable to write plist: {err}"))?;
    Ok(path)
}

fn xml_escape(input: &str) -> String {
    input
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}

fn current_uid() -> Option<String> {
    let output = Command::new("id").arg("-u").output().ok()?;
    if !output.status.success() {
        return None;
    }
    let raw = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if raw.is_empty() {
        None
    } else {
        Some(raw)
    }
}

fn pypi_has_version(app: &AppHandle, package: &str, version: &str) -> Option<bool> {
    let url = format!("https://pypi.org/pypi/{}/json", package);
    let output = Command::new("curl")
        .arg("-sS")
        .arg("--fail")
        .arg("--location")
        .arg(&url)
        .output()
        .ok()?;
    if !output.status.success() {
        emit_log(
            app,
            "warn",
            &format!(
                "#FALLBACK: Unable to verify PyPI versions for {package} (HTTP error)."
            ),
        );
        return None;
    }
    let json: serde_json::Value = match serde_json::from_slice(&output.stdout) {
        Ok(value) => value,
        Err(err) => {
            emit_log(
                app,
                "warn",
                &format!(
                    "#FALLBACK: Unable to parse PyPI metadata for {package}: {err}"
                ),
            );
            return None;
        }
    };
    let releases = json.get("releases")?;
    let has_version = releases.get(version).is_some();
    Some(has_version)
}

fn run_command(
    app: &AppHandle,
    mut cmd: Command,
    display: &str,
    cancel: &Arc<AtomicBool>,
) -> Result<(), String> {
    emit_log(app, "info", &format!("$ {display}"));
    cmd.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = cmd.spawn().map_err(|err| err.to_string())?;

    let out_handle = child.stdout.take().map(|out| {
        let app = app.clone();
        std::thread::spawn(move || {
            let reader = BufReader::new(out);
            for line in reader.lines().flatten() {
                let trimmed = line.trim();
                if !trimmed.is_empty() {
                    emit_log(&app, "info", trimmed);
                }
            }
        })
    });

    let err_handle = child.stderr.take().map(|err| {
        let app = app.clone();
        std::thread::spawn(move || {
            let reader = BufReader::new(err);
            for line in reader.lines().flatten() {
                let trimmed = line.trim();
                if !trimmed.is_empty() {
                    emit_log(&app, "warn", trimmed);
                }
            }
        })
    });

    let status = loop {
        if cancel.load(Ordering::SeqCst) {
            let _ = child.kill();
            let _ = child.wait();
            break Err("Install cancelled.".into());
        }
        match child.try_wait() {
            Ok(Some(status)) => break Ok(status),
            Ok(None) => sleep(Duration::from_millis(200)),
            Err(err) => break Err(err.to_string()),
        }
    };

    if let Some(handle) = out_handle {
        let _ = handle.join();
    }
    if let Some(handle) = err_handle {
        let _ = handle.join();
    }

    match status {
        Ok(status) if status.success() => Ok(()),
        Ok(status) => Err(format!("{display} failed with exit code {:?}", status.code())),
        Err(err) => Err(err),
    }
}

fn emit_log(app: &AppHandle, kind: &str, message: &str) {
    let payload = InstallerEvent {
        kind: kind.to_string(),
        message: message.to_string(),
        code: None,
        action_url: None,
        component_id: None,
        component_name: None,
        stage: None,
        current: None,
        total: None,
        components: None,
    };
    let _ = app.emit("installer-log", payload);
}

fn emit_status(app: &AppHandle, message: &str) {
    emit_log(app, "status", message);
}

fn emit_plan(app: &AppHandle, pip: &[Component], npm: &[Component], total: usize) {
    let mut plan: Vec<PlanComponent> = Vec::new();
    for component in pip.iter().chain(npm.iter()) {
        plan.push(PlanComponent {
            id: component.id.clone(),
            name: component.name.clone(),
        });
    }
    let payload = InstallerEvent {
        kind: "plan".to_string(),
        message: "Install plan ready.".to_string(),
        code: None,
        action_url: None,
        component_id: None,
        component_name: None,
        stage: None,
        current: None,
        total: Some(total),
        components: Some(plan),
    };
    let _ = app.emit("installer-log", payload);
}

fn emit_component(
    app: &AppHandle,
    component: &Component,
    stage: &str,
    current: usize,
    total: usize,
) {
    let payload = InstallerEvent {
        kind: "component".to_string(),
        message: format!("{}: {}", component.name, stage),
        code: None,
        action_url: None,
        component_id: Some(component.id.clone()),
        component_name: Some(component.name.clone()),
        stage: Some(stage.to_string()),
        current: Some(current),
        total: Some(total),
        components: None,
    };
    let _ = app.emit("installer-log", payload);
}

fn emit_prereq(app: &AppHandle, code: &str, message: &str, action_url: Option<&str>) {
    let payload = InstallerEvent {
        kind: "prereq".to_string(),
        message: message.to_string(),
        code: Some(code.to_string()),
        action_url: action_url.map(|url| url.to_string()),
        component_id: None,
        component_name: None,
        stage: None,
        current: None,
        total: None,
        components: None,
    };
    let _ = app.emit("installer-log", payload);
}

fn resolve_install_root(install_dir: Option<String>) -> PathBuf {
    install_dir
        .map(|dir| PathBuf::from(dir.trim()))
        .filter(|dir| !dir.as_os_str().is_empty())
        .unwrap_or_else(default_install_root)
}

fn python_pkg_filename(url: &str) -> Result<&str, String> {
    url.split('/')
        .last()
        .filter(|part| !part.is_empty())
        .ok_or_else(|| "Python installer URL is invalid.".into())
}

fn ensure_macos_supported(app: &AppHandle) -> Result<(), String> {
    match macos_major_version() {
        Some(major) if major >= PYTHON_MACOS_MIN_MAJOR => Ok(()),
        Some(major) => Err(format!(
            "Automatic Python install requires macOS {PYTHON_MACOS_MIN_MAJOR}+; detected macOS {major}.",
        )),
        None => {
            emit_log(
                app,
                "warn",
                "#FALLBACK: Unable to detect macOS version; attempting download.",
            );
            Ok(())
        }
    }
}

fn ensure_curl_available() -> Result<(), String> {
    let ok = Command::new("curl")
        .arg("--version")
        .output()
        .ok()
        .map(|output| output.status.success())
        .unwrap_or(false);
    if ok {
        Ok(())
    } else {
        Err("curl is required to download the Python installer.".into())
    }
}

#[derive(Debug, Clone)]
struct PythonProbe {
    command: String,
    major: u8,
    minor: u8,
    patch: u8,
    priority: u8,
    raw: String,
}

fn probe_python(command: &str) -> Option<PythonProbe> {
    let output = Command::new(command)
        .arg("-c")
        .arg("import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let raw = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let (major, minor, patch) = parse_version(&raw)?;
    Some(PythonProbe {
        command: command.to_string(),
        major,
        minor,
        patch,
        priority: python_priority(command),
        raw,
    })
}

fn python_priority(command: &str) -> u8 {
    if command.contains("/Library/Frameworks/Python.framework/") {
        3
    } else if command.contains("/opt/homebrew/") {
        2
    } else if command.contains("/usr/local/") {
        2
    } else if command.contains("/opt/local/") {
        1
    } else {
        0
    }
}

fn python_candidate_paths() -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    let mut push = |path: PathBuf| {
        if path.exists() {
            candidates.push(path);
        }
    };

    let framework_root = PathBuf::from("/Library/Frameworks/Python.framework/Versions");
    if let Ok(entries) = fs::read_dir(&framework_root) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if name == "Current" || name.chars().next().map(|c| c.is_ascii_digit()).unwrap_or(false)
            {
                push(entry.path().join("bin").join("python3"));
            }
        }
    }
    push(framework_root.join("Current").join("bin").join("python3"));
    push(PathBuf::from("/opt/homebrew/bin/python3"));
    push(PathBuf::from("/usr/local/bin/python3"));
    push(PathBuf::from("/opt/local/bin/python3"));

    if let Ok(home) = std::env::var("HOME") {
        push(PathBuf::from(&home).join(".pyenv/shims/python3"));
        push(PathBuf::from(&home).join(".asdf/shims/python3"));
        push(PathBuf::from(&home).join("miniconda3/bin/python3"));
        push(PathBuf::from(&home).join("anaconda3/bin/python3"));
    }

    candidates
}

fn macos_major_version() -> Option<u8> {
    let output = Command::new("sw_vers")
        .arg("-productVersion")
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let raw = String::from_utf8_lossy(&output.stdout);
    let major = raw.trim().split('.').next()?;
    major.parse().ok()
}

fn default_install_root() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home)
        .join("Library")
        .join("Application Support")
        .join("AbstractFramework")
}

fn current_arch() -> &'static str {
    match std::env::consts::ARCH {
        "aarch64" => "arm64",
        other => other,
    }
}

fn parse_version(raw: &str) -> Option<(u8, u8, u8)> {
    let parts: Vec<&str> = raw.trim().split('.').collect();
    if parts.len() < 2 {
        return None;
    }
    let major = parts[0].parse().ok()?;
    let minor = parts[1].parse().ok()?;
    let patch = parts.get(2).and_then(|part| part.parse().ok()).unwrap_or(0);
    Some((major, minor, patch))
}

fn main() {
    tauri::Builder::default()
        .manage(InstallState::default())
        .invoke_handler(tauri::generate_handler![
            load_manifest,
            get_defaults,
            pick_install_dir,
            open_url,
            download_python_installer,
            start_install,
            start_setup,
            cancel_install,
            close_window
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// AbstractFramework macOS Installer UI logic
let bridge = {
  invoke: null,
  listen: null,
  ready: false,
  mode: "missing",
};

function resolveBridge() {
  const tauriBridge = window.__TAURI__ || null;
  const invoke = tauriBridge?.core?.invoke;
  const listen = tauriBridge?.event?.listen;
  if (invoke && listen) {
    bridge = { invoke, listen, ready: true, mode: "global" };
    return true;
  }

  const internals = window.__TAURI_INTERNALS__ || null;
  if (internals?.invoke && internals?.transformCallback) {
    const fallbackInvoke = (cmd, args) => internals.invoke(cmd, args);
    const fallbackListen = async (event, handler) => {
      const callback = internals.transformCallback((payload) => handler(payload));
      const target = { kind: "Any" };
      const eventId = await internals.invoke("plugin:event|listen", {
        event,
        target,
        handler: callback,
      });
      return async () =>
        internals.invoke("plugin:event|unlisten", { event, eventId });
    };
    bridge = { invoke: fallbackInvoke, listen: fallbackListen, ready: true, mode: "internal" };
    return true;
  }

  return false;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForBridge(timeoutMs = 5000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (resolveBridge()) {
      return true;
    }
    await sleep(100);
  }
  return false;
}

const state = {
  mode: "full",
  manifest: null,
  selected: new Set(),
  defaults: null,
};

const logOutput = document.getElementById("log-output");
const statusEl = document.getElementById("status");
const installBtn = document.getElementById("install-btn");
const installDirInput = document.getElementById("install-dir");
const componentsHint = document.getElementById("components-hint");
const selectAllBtn = document.getElementById("select-all");
const clearAllBtn = document.getElementById("clear-all");
const browseBtn = document.getElementById("browse-btn");
const bridgeStatus = document.getElementById("bridge-status");
const installProgress = document.getElementById("install-progress");
const progressStatus = document.getElementById("progress-status");
const progressBar = document.getElementById("progress-bar-fill");
const progressMeta = document.getElementById("progress-meta");
const progressList = document.getElementById("progress-list");
const cancelBtn = document.getElementById("cancel-btn");
const setupPanel = document.getElementById("setup-panel");
const setupStatus = document.getElementById("setup-status");
const setupApplyBtn = document.getElementById("setup-apply-btn");
const setupSkipBtn = document.getElementById("setup-skip-btn");
const setupStepLabel = document.getElementById("setup-step-label");
const setupBackBtn = document.getElementById("setup-back-btn");
const setupNextBtn = document.getElementById("setup-next-btn");
const setupFinishBtn = document.getElementById("setup-finish-btn");
const setupCards = Array.from(document.querySelectorAll(".setup-card"));
const wizardNav = document.getElementById("wizard-nav");
const wizardStepLabel = document.getElementById("wizard-step-label");
const wizardBackBtn = document.getElementById("wizard-back-btn");
const wizardNextBtn = document.getElementById("wizard-next-btn");
const wizardSteps = Array.from(document.querySelectorAll(".wizard-step"));
const prereqModal = document.getElementById("prereq-modal");
const prereqTitle = document.getElementById("prereq-title");
const prereqMessage = document.getElementById("prereq-message");
const prereqOpenBtn = document.getElementById("prereq-open-btn");
const prereqRetryBtn = document.getElementById("prereq-retry-btn");
const prereqCancelBtn = document.getElementById("prereq-cancel-btn");

const prereqState = {
  actionUrl: null,
  code: null,
};

const setupFields = {
  provider: document.getElementById("setup-provider"),
  model: document.getElementById("setup-model"),
  baseUrl: document.getElementById("setup-base-url"),
  envLaunchd: document.getElementById("env-launchd"),
  envShell: document.getElementById("env-shell"),
  keyOpenai: document.getElementById("key-openai"),
  keyAnthropic: document.getElementById("key-anthropic"),
  keyOpenrouter: document.getElementById("key-openrouter"),
  keyPortkey: document.getElementById("key-portkey"),
  visionMode: document.getElementById("vision-mode"),
  visionProvider: document.getElementById("vision-provider"),
  visionModel: document.getElementById("vision-model"),
  visionFallbackProvider: document.getElementById("vision-fallback-provider"),
  visionFallbackModel: document.getElementById("vision-fallback-model"),
  visionDownloadModel: document.getElementById("vision-download-model"),
  audioStrategy: document.getElementById("audio-strategy"),
  sttBackend: document.getElementById("stt-backend"),
  sttLanguage: document.getElementById("stt-language"),
  videoStrategy: document.getElementById("video-strategy"),
  embeddingsProvider: document.getElementById("embeddings-provider"),
  embeddingsModel: document.getElementById("embeddings-model"),
  logLevel: document.getElementById("log-level"),
};

function setStatus(message, tone = "default") {
  statusEl.textContent = message;
  if (tone === "success") {
    statusEl.style.color = "var(--success)";
  } else if (tone === "warning") {
    statusEl.style.color = "var(--warning)";
  } else {
    statusEl.style.color = "var(--text-secondary)";
  }
}

function appendLog(message) {
  logOutput.textContent += message.endsWith("\n") ? message : `${message}\n`;
  logOutput.scrollTop = logOutput.scrollHeight;
}

function appendProgressLog(message) {
  appendLog(message);
}

function setInstalling(isInstalling) {
  installingNow = isInstalling;
  document.body.classList.toggle("installing", isInstalling);
  if (installProgress) {
    installProgress.classList.toggle("hidden", !isInstalling);
  }
  installBtn.disabled = isInstalling || (state.mode === "custom" && state.selected.size === 0);
  cancelBtn.disabled = !isInstalling;
  if (!isInstalling) {
    progressBar.style.width = "0%";
    progressMeta.textContent = "0 / 0";
    progressList.innerHTML = "";
  }
  updateWizard();
}

function renderProgressList(components) {
  progressList.innerHTML = "";
  components.forEach((component) => {
    const row = document.createElement("div");
    row.className = "progress-item";
    row.dataset.componentId = component.id;
    row.innerHTML = `<span>${component.name}</span><span class="state">pending</span>`;
    progressList.appendChild(row);
  });
}

function updateProgressItem(componentId, stateText) {
  const row = progressList.querySelector(`[data-component-id="${componentId}"]`);
  if (!row) return;
  const state = row.querySelector(".state");
  if (state) {
    state.textContent = stateText;
  }
}

// Prerequisite modal for missing system dependencies (Python, etc.).
function showPrereqModal(payload) {
  if (!prereqModal) return;
  const message = payload?.message || "A required dependency is missing.";
  const code = payload?.code || "";
  const title = code === "python" ? "Python 3.10+ required" : "Missing dependency";
  if (prereqTitle) prereqTitle.textContent = title;
  if (prereqMessage) prereqMessage.textContent = message;
  prereqState.actionUrl = payload?.action_url || null;
  prereqState.code = code;
  if (prereqOpenBtn) {
    prereqOpenBtn.disabled = !prereqState.actionUrl;
    prereqOpenBtn.textContent =
      code === "python" ? "Download & Install Python" : "Open download page";
  }
  document.body.classList.add("modal-open");
  prereqModal.classList.remove("hidden");
  setInstalling(false);
}

function hidePrereqModal() {
  if (!prereqModal) return;
  document.body.classList.remove("modal-open");
  prereqModal.classList.add("hidden");
  prereqState.actionUrl = null;
  prereqState.code = null;
}

let setupStepIndex = 0;
let wizardIndex = 0;
let wizardMaxIndex = 0;
let installCompleted = false;
let installingNow = false;

const installStepIndex = wizardSteps.findIndex((step) => step.id === "install-panel");
const setupWizardIndex = wizardSteps.findIndex((step) => step.id === "setup-panel");
const componentsStepIndex = wizardSteps.findIndex((step) => step.id === "components-panel");

function updateWizard() {
  if (!wizardSteps.length) return;
  wizardSteps.forEach((step, idx) => {
    step.classList.toggle("active", idx === wizardIndex);
  });
  const active = wizardSteps[wizardIndex];
  const title = active?.dataset?.title || `Step ${wizardIndex + 1}`;
  if (wizardStepLabel) {
    wizardStepLabel.textContent = `Step ${wizardIndex + 1} of ${wizardSteps.length}: ${title}`;
  }
  if (wizardNav) {
    wizardNav.classList.toggle("hidden", wizardIndex === setupWizardIndex);
  }
  if (wizardBackBtn) {
    wizardBackBtn.disabled = wizardIndex === 0 || installingNow;
  }
  if (wizardNextBtn) {
    const atMax = wizardIndex >= wizardMaxIndex;
    wizardNextBtn.disabled = atMax || installingNow;
  }
}

function goToWizardStep(index) {
  if (!wizardSteps.length) return;
  const clamped = Math.max(0, Math.min(index, wizardSteps.length - 1));
  wizardIndex = clamped;
  if (wizardIndex === setupWizardIndex && setupPanel) {
    setupPanel.classList.remove("hidden");
  }
  updateWizard();
}

function updateSetupWizard() {
  if (!setupCards.length) return;
  setupCards.forEach((card, idx) => {
    card.classList.toggle("active", idx === setupStepIndex);
  });
  const activeCard = setupCards[setupStepIndex];
  const title = activeCard?.dataset?.title || `Step ${setupStepIndex + 1}`;
  if (setupStepLabel) {
    setupStepLabel.textContent = `Step ${setupStepIndex + 1} of ${setupCards.length}: ${title}`;
  }
  if (setupBackBtn) setupBackBtn.disabled = setupStepIndex === 0;
  if (setupNextBtn) setupNextBtn.disabled = setupStepIndex >= setupCards.length - 1;
  if (setupApplyBtn) {
    setupApplyBtn.classList.toggle("hidden", setupStepIndex !== setupCards.length - 1);
  }
  if (setupSkipBtn) {
    setupSkipBtn.classList.toggle("hidden", setupStepIndex !== setupCards.length - 1);
  }
  if (setupNextBtn) {
    setupNextBtn.classList.toggle("hidden", setupStepIndex >= setupCards.length - 1);
  }
  if (setupFinishBtn) {
    setupFinishBtn.classList.remove("hidden");
  }
}

function showSetupPanel() {
  if (!setupPanel) return;
  setupPanel.classList.remove("hidden");
  setupStepIndex = 0;
  updateSetupWizard();
  if (setupWizardIndex >= 0) {
    wizardMaxIndex = wizardSteps.length - 1;
    goToWizardStep(setupWizardIndex);
  }
  setupPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function getFieldValue(field) {
  if (!field) return "";
  return field.value ? field.value.trim() : "";
}

function collectSetupPayload() {
  const apiKeys = [
    { provider: "openai", key: getFieldValue(setupFields.keyOpenai) },
    { provider: "anthropic", key: getFieldValue(setupFields.keyAnthropic) },
    { provider: "openrouter", key: getFieldValue(setupFields.keyOpenrouter) },
    { provider: "portkey", key: getFieldValue(setupFields.keyPortkey) },
  ].filter((entry) => entry.key);

  return {
    install_dir: installDirInput?.value?.trim() || "",
    global_provider: getFieldValue(setupFields.provider),
    global_model: getFieldValue(setupFields.model),
    base_url_provider: getFieldValue(setupFields.baseUrl)
      ? getFieldValue(setupFields.provider)
      : "",
    base_url: getFieldValue(setupFields.baseUrl),
    env_apply_launchd: setupFields.envLaunchd?.checked || false,
    env_apply_shell: setupFields.envShell?.checked || false,
    api_keys: apiKeys,
    vision_mode: getFieldValue(setupFields.visionMode) || "skip",
    vision_provider: getFieldValue(setupFields.visionProvider),
    vision_model: getFieldValue(setupFields.visionModel),
    vision_fallback_provider: getFieldValue(setupFields.visionFallbackProvider),
    vision_fallback_model: getFieldValue(setupFields.visionFallbackModel),
    vision_download_model: getFieldValue(setupFields.visionDownloadModel),
    audio_strategy: getFieldValue(setupFields.audioStrategy),
    stt_backend_id: getFieldValue(setupFields.sttBackend),
    stt_language: getFieldValue(setupFields.sttLanguage),
    video_strategy: getFieldValue(setupFields.videoStrategy),
    embeddings_provider: getFieldValue(setupFields.embeddingsProvider),
    embeddings_model: getFieldValue(setupFields.embeddingsModel),
    log_level: getFieldValue(setupFields.logLevel),
  };
}

function groupBy(arr, key) {
  return arr.reduce((acc, item) => {
    const group = item[key] || "Other";
    acc[group] = acc[group] || [];
    acc[group].push(item);
    return acc;
  }, {});
}

function renderComponents() {
  const container = document.getElementById("components");
  container.innerHTML = "";
  if (!state.manifest) return;

  const isCustom = state.mode === "custom";
  const components = state.manifest.components.filter((item) => item.id !== "framework_full");
  const grouped = groupBy(components, "group");

  Object.entries(grouped).forEach(([group, items]) => {
    const groupEl = document.createElement("div");
    groupEl.className = "group";
    const title = document.createElement("h3");
    title.textContent = group;
    groupEl.appendChild(title);

    items.forEach((component) => {
      const row = document.createElement("label");
      row.className = `component ${component.available ? "" : "disabled"}`;
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = component.id;
      checkbox.disabled = !component.available || !isCustom;
      checkbox.checked = state.selected.has(component.id);
      checkbox.addEventListener("change", (event) => {
        if (event.target.checked) {
          state.selected.add(component.id);
        } else {
          state.selected.delete(component.id);
        }
        updateInstallButton();
      });

      const meta = document.createElement("div");
      meta.className = "meta";
      const name = document.createElement("strong");
      name.textContent = component.name;
      const desc = document.createElement("small");
      desc.textContent = component.description || "No description.";
      const note = document.createElement("small");
      note.textContent = component.available ? "" : component.unavailable_reason || "Unavailable";

      meta.appendChild(name);
      meta.appendChild(desc);
      if (note.textContent) meta.appendChild(note);

      row.appendChild(checkbox);
      row.appendChild(meta);
      groupEl.appendChild(row);
    });

    container.appendChild(groupEl);
  });
}

function setMode(mode) {
  state.mode = mode;
  if (mode === "custom" && state.manifest && state.selected.size === 0) {
    state.manifest.components.forEach((component) => {
      if (component.default_selected && component.available && component.id !== "framework_full") {
        state.selected.add(component.id);
      }
    });
  }
  updateComponentToolbar();
  updateInstallButton();
  renderComponents();
}

function updateComponentToolbar() {
  const isCustom = state.mode === "custom";
  selectAllBtn.disabled = !isCustom;
  clearAllBtn.disabled = !isCustom;
  componentsHint.textContent = isCustom
    ? "Select the components to install."
    : "Full install selected. Switch to Custom to edit components.";
}

function updateInstallButton() {
  if (state.mode === "custom" && state.selected.size === 0) {
    installBtn.disabled = true;
    setStatus("Select at least one component.", "warning");
  } else {
    installBtn.disabled = false;
    if (statusEl.textContent !== "Initializing..." && statusEl.textContent !== "Installing...") {
      setStatus("Ready");
    }
  }
}

async function init() {
  setStatus("Waiting for Tauri bridge...");
  if (bridgeStatus) {
    bridgeStatus.textContent = "Bridge: waiting…";
  }
  const ready = await waitForBridge(5000);
  if (!ready || !bridge.invoke || !bridge.listen) {
    setStatus("Tauri bridge unavailable.", "warning");
    appendLog("Tauri bridge not found. Check CSP or withGlobalTauri.");
    if (bridgeStatus) bridgeStatus.textContent = "Bridge: missing";
    return;
  }
  if (bridgeStatus) {
    bridgeStatus.textContent = `Bridge: ready (${bridge.mode})`;
  }
  appendLog(`Bridge connected (${bridge.mode}).`);

  state.manifest = await bridge.invoke("load_manifest");
  state.defaults = await bridge.invoke("get_defaults");
  installDirInput.value = state.defaults.install_dir;

  document.querySelectorAll("input[name='mode']").forEach((radio) => {
    radio.addEventListener("change", (event) => setMode(event.target.value));
  });

  const selected = document.querySelector("input[name='mode']:checked");
  setMode(selected ? selected.value : "full");
  renderComponents();

  if (wizardSteps.length) {
    wizardMaxIndex = installStepIndex >= 0 ? installStepIndex : wizardSteps.length - 1;
    goToWizardStep(0);
  }

  await bridge.listen("installer-log", (event) => {
    const payload = event.payload;
    if (payload?.message) {
      appendLog(payload.message);
    }
    if (payload?.kind === "status") {
      setStatus(payload.message);
      progressStatus.textContent = payload.message;
      if (
        payload.message.startsWith("Install complete") ||
        payload.message.startsWith("Install failed") ||
        payload.message.startsWith("Install cancelled")
      ) {
        setInstalling(false);
      }
      if (payload.message.startsWith("Install complete")) {
        installCompleted = true;
        if (setupStatus) setupStatus.textContent = "Ready to configure.";
        showSetupPanel();
      }
      if (payload.message.startsWith("Configuration complete")) {
        if (setupStatus) setupStatus.textContent = "Configuration complete.";
        if (setupApplyBtn) setupApplyBtn.disabled = false;
      }
      if (payload.message.startsWith("Configuration failed")) {
        if (setupStatus) setupStatus.textContent = payload.message;
        if (setupApplyBtn) setupApplyBtn.disabled = false;
      }
    }
    if (payload?.kind === "plan") {
      renderProgressList(payload.components || []);
      progressMeta.textContent = `0 / ${payload.total || 0}`;
      progressBar.style.width = "0%";
    }
    if (payload?.kind === "component") {
      if (payload.component_id) {
        updateProgressItem(payload.component_id, payload.stage || "working");
      }
      if (payload.component_name && payload.stage === "installing") {
        progressStatus.textContent = `Installing ${payload.component_name}...`;
      }
      if (payload.current && payload.total) {
        progressMeta.textContent = `${payload.current} / ${payload.total}`;
        progressBar.style.width = `${Math.round((payload.current / payload.total) * 100)}%`;
      }
    }
    if (payload?.kind === "prereq") {
      setStatus(payload.message || "Missing dependency.", "warning");
      showPrereqModal(payload);
    }
  });
  setStatus("Ready");
}

selectAllBtn.addEventListener("click", () => {
  if (!state.manifest) return;
  state.manifest.components.forEach((component) => {
    if (component.available && component.id !== "framework_full") {
      state.selected.add(component.id);
    }
  });
  renderComponents();
  updateInstallButton();
});

clearAllBtn.addEventListener("click", () => {
  state.selected.clear();
  renderComponents();
  updateInstallButton();
});

browseBtn.addEventListener("click", async () => {
  try {
    if (!bridge.invoke) {
      throw new Error("Tauri bridge not available.");
    }
    const selected = await bridge.invoke("pick_install_dir");
    if (selected) {
      installDirInput.value = selected;
    }
  } catch (err) {
    appendLog(`Error: ${err}`);
    setStatus("Folder picker failed", "warning");
  }
});

installBtn.addEventListener("click", async () => {
  if (state.mode === "custom" && state.selected.size === 0) {
    setStatus("Select at least one component.", "warning");
    return;
  }
  installCompleted = false;
  if (installStepIndex >= 0) {
    wizardMaxIndex = installStepIndex;
  }
  setInstalling(true);
  logOutput.textContent = "";
  setStatus("Installing...");
  progressStatus.textContent = "Starting install...";

  const payload = {
    mode: state.mode,
    component_ids: Array.from(state.selected),
    install_dir: installDirInput.value.trim(),
  };

  try {
    if (!bridge.invoke) {
      throw new Error("Tauri bridge not available.");
    }
    await bridge.invoke("start_install", { request: payload });
  } catch (err) {
    appendLog(`Error: ${err}`);
    appendProgressLog(`Error: ${err}`);
    setStatus("Install failed", "warning");
    setInstalling(false);
  }
});

cancelBtn.addEventListener("click", async () => {
  try {
    if (!bridge.invoke) {
      throw new Error("Tauri bridge not available.");
    }
    progressStatus.textContent = "Cancelling...";
    await bridge.invoke("cancel_install");
  } catch (err) {
    appendProgressLog(`Error: ${err}`);
    progressStatus.textContent = "Cancel failed";
  }
});

if (setupApplyBtn) {
  setupApplyBtn.addEventListener("click", async () => {
    try {
      if (!bridge.invoke) {
        throw new Error("Tauri bridge not available.");
      }
      const payload = collectSetupPayload();
      setupApplyBtn.disabled = true;
      if (setupStatus) setupStatus.textContent = "Applying configuration...";
      await bridge.invoke("start_setup", { request: payload });
    } catch (err) {
      if (setupStatus) setupStatus.textContent = `Configuration failed: ${err}`;
      if (setupApplyBtn) setupApplyBtn.disabled = false;
    }
  });
}

if (setupSkipBtn) {
  setupSkipBtn.addEventListener("click", () => {
    if (setupStatus) setupStatus.textContent = "Skipped for now.";
  });
}

if (setupBackBtn) {
  setupBackBtn.addEventListener("click", () => {
    if (setupStepIndex > 0) {
      setupStepIndex -= 1;
      updateSetupWizard();
    }
  });
}

if (setupNextBtn) {
  setupNextBtn.addEventListener("click", () => {
    if (setupStepIndex < setupCards.length - 1) {
      setupStepIndex += 1;
      updateSetupWizard();
    }
  });
}

if (setupFinishBtn) {
  setupFinishBtn.addEventListener("click", () => {
    if (!bridge.invoke) {
      setStatus("Tauri bridge not available.", "warning");
      return;
    }
    bridge.invoke("close_window").catch((err) => {
      appendLog(`#FALLBACK: Unable to close window. ${err}`);
    });
  });
}

if (wizardBackBtn) {
  wizardBackBtn.addEventListener("click", () => {
    if (installingNow) return;
    if (wizardIndex > 0) {
      goToWizardStep(wizardIndex - 1);
    }
  });
}

if (wizardNextBtn) {
  wizardNextBtn.addEventListener("click", () => {
    if (installingNow) return;
    if (wizardIndex === componentsStepIndex && state.mode === "custom" && state.selected.size === 0) {
      setStatus("Select at least one component.", "warning");
      return;
    }
    if (wizardIndex < wizardMaxIndex) {
      goToWizardStep(wizardIndex + 1);
    }
  });
}

if (prereqOpenBtn) {
  prereqOpenBtn.addEventListener("click", async () => {
    const originalLabel = prereqOpenBtn.textContent;
    try {
      if (!prereqState.actionUrl) {
        return;
      }
      if (!bridge.invoke) {
        throw new Error("Tauri bridge not available.");
      }
      if (prereqState.code === "python") {
        prereqOpenBtn.disabled = true;
        prereqOpenBtn.textContent = "Downloading...";
        const installDir = installDirInput?.value?.trim() || "";
        await bridge.invoke("download_python_installer", { install_dir: installDir });
        if (prereqMessage) {
          prereqMessage.textContent =
            "Installer opened. Complete the Python install, then click Retry.";
        }
        prereqOpenBtn.textContent = "Reopen installer";
        prereqOpenBtn.disabled = false;
      } else {
        await bridge.invoke("open_url", { url: prereqState.actionUrl });
      }
    } catch (err) {
      prereqOpenBtn.textContent = originalLabel;
      prereqOpenBtn.disabled = false;
      appendLog(`#FALLBACK: Automatic download failed. ${err}`);
      appendProgressLog(`#FALLBACK: Automatic download failed. ${err}`);
      try {
        await bridge.invoke("open_url", { url: prereqState.actionUrl });
      } catch (openErr) {
        appendLog(`#FALLBACK: Unable to open browser automatically. ${openErr}`);
        appendProgressLog(`#FALLBACK: Unable to open browser automatically. ${openErr}`);
      }
    }
  });
}

if (prereqRetryBtn) {
  prereqRetryBtn.addEventListener("click", () => {
    hidePrereqModal();
    installBtn.click();
  });
}

if (prereqCancelBtn) {
  prereqCancelBtn.addEventListener("click", () => {
    hidePrereqModal();
  });
}

window.addEventListener("error", (event) => {
  appendLog(`Error: ${event.message}`);
  appendProgressLog(`Error: ${event.message}`);
});

window.addEventListener("unhandledrejection", (event) => {
  appendLog(`Unhandled: ${event.reason}`);
  appendProgressLog(`Unhandled: ${event.reason}`);
});
init().catch((err) => {
  appendLog(`Error: ${err}`);
  setStatus("Failed to load installer", "warning");
});

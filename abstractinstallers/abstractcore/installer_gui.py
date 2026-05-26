#!/usr/bin/env python3
"""
AbstractFramework AbstractCore GUI Installer (test).

Small, friendly installer that maps choices to AbstractCore configuration.
"""

from __future__ import annotations

import json
import queue
import shutil
import sys
import threading
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import platform
import tkinter as tk
import tkinter.font as tkfont

import installer as installer_module


SCRIPT_DIR = Path(__file__).resolve().parent

THEME = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_tertiary": "#0f3460",
    "text_primary": "#eeeeee",
    "text_secondary": "#aaaaaa",
    "text_muted": "#666666",
    "accent": "#e94560",
    "border": "#263b5a",
}

CONFIG_PATH = Path.home() / ".abstractcore" / "config" / "abstractcore.json"
DEFAULT_CONFIG = {
    "vision": {"strategy": "disabled", "caption_provider": None, "caption_model": None, "fallback_chain": []},
    "audio": {"strategy": "auto", "stt_backend_id": None, "stt_language": None},
    "video": {"strategy": "auto"},
    "embeddings": {"provider": "huggingface", "model": "all-minilm-l6-v2"},
    "logging": {"console_level": "ERROR"},
    "default_models": {"global_provider": None, "global_model": None},
}

STT_LANGUAGE_OPTIONS = [
    ("Auto-detect", ""),
    ("English (en)", "en"),
    ("French (fr)", "fr"),
    ("German (de)", "de"),
    ("Spanish (es)", "es"),
    ("Russian (ru)", "ru"),
    ("Chinese (zh)", "zh"),
    ("Italian (it)", "it"),
    ("Portuguese (pt)", "pt"),
    ("Japanese (ja)", "ja"),
    ("Korean (ko)", "ko"),
    ("Arabic (ar)", "ar"),
    ("Hindi (hi)", "hi"),
]
STT_LANGUAGE_LABELS = [label for label, _ in STT_LANGUAGE_OPTIONS]
STT_LANGUAGE_LABEL_TO_CODE = {label: code for label, code in STT_LANGUAGE_OPTIONS}
STT_LANGUAGE_CODE_TO_LABEL = {code: label for label, code in STT_LANGUAGE_OPTIONS if code}


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 450) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._tip: tk.Toplevel | None = None

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event: object | None = None) -> None:
        self._schedule()

    def _on_leave(self, _event: object | None = None) -> None:
        self._unschedule()
        self._hide()

    def _schedule(self) -> None:
        self._unschedule()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _unschedule(self) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            wraplength=320,
            background=THEME["bg_secondary"],
            foreground=THEME["text_primary"],
            borderwidth=1,
            relief="solid",
            padx=8,
            pady=6,
        )
        label.pack()

    def _hide(self) -> None:
        if self._tip:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None

INSTALL_TYPES = [
    ("full", "Full", "Everything for your hardware."),
    ("standard", "Standard", "Common features with a light footprint."),
    ("custom", "Custom", "Choose exactly what to install."),
]

STANDARD_FEATURES = ["tools", "media", "embeddings", "tokens"]

CUSTOM_MODULES = [
    ("embeddings", "Embeddings"),
    ("tokens", "Token counting"),
    ("tools", "Tools (web search, scraping)"),
    ("media", "Media (PDF/Office parsing)"),
    ("compression", "Glyph compression"),
    ("server", "Server (OpenAI-compatible API)"),
    ("vision", "Vision (delegates to AbstractVision)"),
    ("vision-diffusers", "Vision Diffusers backend"),
    ("vision-sdcpp", "Vision stable-diffusion.cpp backend"),
    ("vision-local", "Vision local backends"),
]

CUSTOM_PROVIDERS = [
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("openrouter", "OpenRouter"),
    ("huggingface", "Hugging Face"),
    ("mlx", "MLX (Apple Silicon)"),
    ("vllm", "vLLM (GPU)"),
    ("ollama", "Ollama"),
    ("lmstudio", "LM Studio"),
]

PROVIDERS = [
    ("ollama", "Local (Ollama)", "qwen3:4b-instruct", "http://localhost:11434", False, True, True),
    ("lmstudio", "Local (LM Studio)", "qwen/qwen3-4b-2507", "http://localhost:1234/v1", False, True, True),
    ("openai-compatible", "Local (OpenAI-compatible)", "local-model", "http://localhost:1234/v1", False, True, True),
    ("huggingface", "Local (Hugging Face)", "Qwen/Qwen2.5-1.5B-Instruct", "", False, False, True),
    ("mlx", "Local (MLX)", "mlx-community/Qwen2.5-1.5B-Instruct-4bit", "", False, False, True),
    ("openai", "Cloud (OpenAI)", "gpt-4o-mini", "", True, True, False),
    ("anthropic", "Cloud (Anthropic)", "claude-3-5-sonnet-latest", "", True, True, False),
    ("openrouter", "Cloud (OpenRouter)", "openrouter/auto", "", True, True, False),
]

PROVIDER_LABELS = [label for _, label, *_ in PROVIDERS]
PROVIDER_LABEL_TO_KEY = {label: key for key, label, *_ in PROVIDERS}
MODULE_LABEL_TO_KEY = {label: key for key, label in CUSTOM_MODULES}
PROVIDER_OPTION_LABEL_TO_KEY = {label: key for key, label in CUSTOM_PROVIDERS}


def default_prefix() -> str:
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
        return str(base / "AbstractFramework" / "abstractcore")
    return str(Path.home() / ".abstractframework" / "abstractcore")


def detect_apple_silicon() -> bool:
    return sys.platform == "darwin" and platform.machine() in {"arm64", "aarch64"}


def detect_gpu() -> bool:
    return shutil.which("nvidia-smi") is not None or shutil.which("rocminfo") is not None


class InstallerApp(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AbstractCore Installer")
        self.minsize(640, 520)
        self._apply_theme()

        self.install_type_var = StringVar(value="standard")
        self.apple_var = BooleanVar(value=detect_apple_silicon())
        self.gpu_var = BooleanVar(value=detect_gpu())
        self.provider_var = StringVar(value=PROVIDERS[0][0])
        self.model_var = StringVar(value=PROVIDERS[0][2])
        self.base_url_var = StringVar(value=PROVIDERS[0][3])
        self.api_key_var = StringVar(value="")
        self.download_model_var = BooleanVar(value=False)
        self.prefix_var = StringVar(value=default_prefix())
        self.version_var = StringVar(value="latest")
        self.install_check_var = BooleanVar(value=False)
        self.recreate_venv_var = BooleanVar(value=False)
        self.remove_all_var = BooleanVar(value=False)
        self.show_details_var = BooleanVar(value=False)
        self.show_advanced_var = BooleanVar(value=False)
        self.wizard_provider_label = StringVar(value=PROVIDER_LABELS[0])
        self.wizard_model_var = StringVar(value="")
        self.wizard_base_url_var = StringVar(value="")
        self.wizard_openai_key_var = StringVar(value="")
        self.wizard_anthropic_key_var = StringVar(value="")
        self.wizard_openrouter_key_var = StringVar(value="")
        self.wizard_portkey_key_var = StringVar(value="")
        self.wizard_portkey_base_url_var = StringVar(value="")
        self.wizard_google_key_var = StringVar(value="")
        self.wizard_download_var = BooleanVar(value=False)
        self.wizard_check_var = BooleanVar(value=False)
        self.vision_mode_var = StringVar(value="keep")
        self.vision_provider_var = StringVar(value="")
        self.vision_model_var = StringVar(value="")
        self.vision_fallback_provider_var = StringVar(value="")
        self.vision_fallback_model_var = StringVar(value="")
        self.vision_download_var = BooleanVar(value=False)
        self.vision_download_model_var = StringVar(value="blip-base-caption")
        self.audio_strategy_var = StringVar(value="auto")
        self.stt_backend_var = StringVar(value="")
        self.stt_language_var = StringVar(value="Auto-detect")
        self.video_strategy_var = StringVar(value="auto")
        self.embeddings_mode_var = StringVar(value="keep")
        self.embeddings_provider_var = StringVar(value="huggingface")
        self.embeddings_model_var = StringVar(value="all-minilm-l6-v2")
        self.log_level_var = StringVar(value="error")
        self.vision_keep_label_var = StringVar(value="Use existing settings")
        self.embeddings_keep_label_var = StringVar(value="Use default embeddings")
        self.current_config: dict[str, object] = {}
        self.current_config_from_file = False
        self.wizard_step = 0
        self.wizard_steps = [
            "Default model",
            "Vision fallback",
            "API keys",
            "Audio strategy",
            "Video strategy",
            "Embeddings",
            "Logging",
            "Readiness",
        ]

        self.selected_modules: list[str] = []
        self.selected_providers: list[str] = []

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.current_action = "install"
        self._tooltips: list[Tooltip] = []

        self._build_ui()
        self._build_wizard()
        self._drain_queue()

    def _attach_tooltip(self, widget: tk.Widget, text: str) -> None:
        if not text:
            return
        tooltip = Tooltip(widget, text)
        self._tooltips.append(tooltip)

    def _apply_theme(self) -> None:
        self.configure(bg=THEME["bg_primary"])
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=12)
        self.option_add("*Font", default_font)

        style.configure("TFrame", background=THEME["bg_primary"])
        style.configure("TLabelframe", background=THEME["bg_primary"], foreground=THEME["text_primary"])
        style.configure(
            "TLabelframe.Label",
            background=THEME["bg_primary"],
            foreground=THEME["text_secondary"],
            font=(default_font.cget("family"), 11, "bold"),
        )
        style.configure("TLabel", background=THEME["bg_primary"], foreground=THEME["text_primary"])
        style.configure("Muted.TLabel", background=THEME["bg_primary"], foreground=THEME["text_secondary"])
        style.configure(
            "Header.TLabel",
            background=THEME["bg_primary"],
            foreground=THEME["text_primary"],
            font=(default_font.cget("family"), 15, "bold"),
        )
        style.configure(
            "Subheader.TLabel",
            background=THEME["bg_primary"],
            foreground=THEME["text_secondary"],
        )
        style.configure("TButton", background=THEME["bg_tertiary"], foreground=THEME["text_primary"])
        style.map(
            "TButton",
            background=[("active", THEME["accent"])],
            foreground=[("active", THEME["text_primary"])],
        )
        style.configure("TCheckbutton", background=THEME["bg_primary"], foreground=THEME["text_primary"])
        style.configure("TRadiobutton", background=THEME["bg_primary"], foreground=THEME["text_primary"])
        style.configure(
            "TEntry",
            fieldbackground=THEME["bg_secondary"],
            background=THEME["bg_secondary"],
            foreground=THEME["text_primary"],
            bordercolor=THEME["border"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_secondary"],
            background=THEME["bg_secondary"],
            foreground=THEME["text_primary"],
            bordercolor=THEME["border"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", THEME["bg_secondary"])],
            background=[("readonly", THEME["bg_secondary"])],
            foreground=[("readonly", THEME["text_primary"])],
        )
        style.configure(
            "TProgressbar",
            troughcolor=THEME["bg_secondary"],
            background=THEME["accent"],
            bordercolor=THEME["border"],
        )

    def _build_ui(self) -> None:
        self.main_frame = ttk.Frame(self, padding=16)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        ttk.Label(self.main_frame, text="Welcome to AbstractCore", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self.main_frame,
            text="Install the core AI engine in a few clicks.",
            wraplength=520,
            style="Subheader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        self._build_install_type(self.main_frame)
        self._build_provider_section(self.main_frame)
        self._build_custom_section(self.main_frame)
        self._build_actions(self.main_frame)
        self._build_advanced(self.main_frame)
        self._build_details(self.main_frame)

        self._sync_hardware_toggles()
        self._update_provider_fields()
        self._update_install_type()

    def _build_wizard(self) -> None:
        self.wizard_frame = ttk.Frame(self, padding=16)
        self.wizard_frame.grid(row=0, column=0, sticky="nsew")
        self.wizard_frame.columnconfigure(0, weight=1)

        ttk.Label(self.wizard_frame, text="AbstractCore Setup", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self.wizard_frame,
            text="We pre-filled these values from your install choices. Click Next to continue.",
            wraplength=520,
            style="Subheader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        self.wizard_step_label = ttk.Label(self.wizard_frame, text="", style="Muted.TLabel")
        self.wizard_step_label.grid(row=2, column=0, sticky="w")

        self.wizard_provider_frame = ttk.LabelFrame(self.wizard_frame, text="Step 1 — Provider defaults")
        self.wizard_provider_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.wizard_provider_frame.columnconfigure(1, weight=1)

        ttk.Label(self.wizard_provider_frame, text="Provider").grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 4)
        )
        self.wizard_provider_box = ttk.Combobox(
            self.wizard_provider_frame,
            values=PROVIDER_LABELS,
            state="readonly",
            textvariable=self.wizard_provider_label,
        )
        self.wizard_provider_box.grid(row=0, column=1, sticky="ew", padx=8, pady=(8, 4))
        self.wizard_provider_box.bind("<<ComboboxSelected>>", self._on_wizard_provider_change)
        self.wizard_provider_box.current(0)
        self._attach_tooltip(self.wizard_provider_box, "Choose the default provider.")

        ttk.Label(self.wizard_provider_frame, text="Model").grid(
            row=1, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        ttk.Entry(self.wizard_provider_frame, textvariable=self.wizard_model_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(4, 4)
        )
        self._attach_tooltip(self.wizard_provider_frame.winfo_children()[-1], "Default model for the provider.")

        self.wizard_base_label = ttk.Label(self.wizard_provider_frame, text="Base URL (optional)")
        self.wizard_base_entry = ttk.Entry(self.wizard_provider_frame, textvariable=self.wizard_base_url_var)
        self.wizard_base_note = ttk.Label(self.wizard_provider_frame, text="", style="Muted.TLabel", wraplength=520)

        self.wizard_vision_frame = ttk.LabelFrame(self.wizard_frame, text="Step 2 — Vision fallback")
        self.wizard_vision_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.wizard_vision_frame.columnconfigure(1, weight=1)

        vision_mode_frame = ttk.Frame(self.wizard_vision_frame)
        vision_mode_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))
        ttk.Label(vision_mode_frame, text="Configure vision fallback?").grid(row=0, column=0, sticky="w")
        keep_rb = ttk.Radiobutton(
            vision_mode_frame,
            textvariable=self.vision_keep_label_var,
            value="keep",
            variable=self.vision_mode_var,
            command=self._update_vision_fields,
        )
        keep_rb.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._attach_tooltip(keep_rb, "Use existing vision fallback settings.")
        enable_rb = ttk.Radiobutton(
            vision_mode_frame,
            text="Enable fallback",
            value="enable",
            variable=self.vision_mode_var,
            command=self._update_vision_fields,
        )
        enable_rb.grid(row=2, column=0, sticky="w")
        disable_rb = ttk.Radiobutton(
            vision_mode_frame,
            text="Disable fallback",
            value="disable",
            variable=self.vision_mode_var,
            command=self._update_vision_fields,
        )
        disable_rb.grid(row=3, column=0, sticky="w")
        self._attach_tooltip(
            enable_rb,
            "Enable vision fallback for text-only models (image captioning).",
        )
        self._attach_tooltip(
            disable_rb,
            "Disable vision fallback (image input on text-only models will fail).",
        )
        self.vision_current_note = ttk.Label(vision_mode_frame, text="", style="Muted.TLabel", wraplength=520)
        self.vision_current_note.grid(row=4, column=0, sticky="w", pady=(2, 0))

        self.wizard_vision_provider_label = ttk.Label(self.wizard_vision_frame, text="Vision provider")
        self.wizard_vision_provider_label.grid(row=1, column=0, sticky="w", padx=8, pady=(6, 4))
        self.wizard_vision_provider_entry = ttk.Entry(self.wizard_vision_frame, textvariable=self.vision_provider_var)
        self.wizard_vision_provider_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=(6, 4))
        self._attach_tooltip(
            self.wizard_vision_provider_entry,
            "Provider id for vision fallback (e.g. ollama, openai, lmstudio).",
        )
        self.wizard_vision_model_label = ttk.Label(self.wizard_vision_frame, text="Vision model")
        self.wizard_vision_model_label.grid(row=2, column=0, sticky="w", padx=8, pady=(4, 4))
        self.wizard_vision_model_entry = ttk.Entry(self.wizard_vision_frame, textvariable=self.vision_model_var)
        self.wizard_vision_model_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_vision_model_entry,
            "Model id for vision fallback (provider-specific model name).",
        )

        self.wizard_vision_fallback_provider_label = ttk.Label(
            self.wizard_vision_frame, text="Fallback provider (optional)"
        )
        self.wizard_vision_fallback_provider_label.grid(row=3, column=0, sticky="w", padx=8, pady=(4, 4))
        self.wizard_vision_fallback_provider_entry = ttk.Entry(
            self.wizard_vision_frame, textvariable=self.vision_fallback_provider_var
        )
        self.wizard_vision_fallback_provider_entry.grid(row=3, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_vision_fallback_provider_entry,
            "Optional second provider for a fallback chain.",
        )
        self.wizard_vision_fallback_model_label = ttk.Label(self.wizard_vision_frame, text="Fallback model (optional)")
        self.wizard_vision_fallback_model_label.grid(row=4, column=0, sticky="w", padx=8, pady=(4, 4))
        self.wizard_vision_fallback_model_entry = ttk.Entry(
            self.wizard_vision_frame, textvariable=self.vision_fallback_model_var
        )
        self.wizard_vision_fallback_model_entry.grid(row=4, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_vision_fallback_model_entry,
            "Optional second model for the fallback chain.",
        )

        self.wizard_vision_download_check = ttk.Checkbutton(
            self.wizard_vision_frame,
            text="Download local vision caption model (blip-base-caption)",
            variable=self.vision_download_var,
        )
        self.wizard_vision_download_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 2))
        self._attach_tooltip(
            self.wizard_vision_download_check,
            "Download a local captioning model (~1GB) for offline vision fallback.",
        )

        self.wizard_keys_frame = ttk.LabelFrame(self.wizard_frame, text="Step 3 — API keys (optional)")
        self.wizard_keys_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        self.wizard_keys_frame.columnconfigure(1, weight=1)

        ttk.Label(
            self.wizard_keys_frame,
            text="Optional keys for common providers. Fill only what you use.",
            style="Muted.TLabel",
            wraplength=520,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))
        ttk.Label(self.wizard_keys_frame, text="OpenAI key").grid(
            row=1, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        ttk.Entry(self.wizard_keys_frame, textvariable=self.wizard_openai_key_var, show="*").grid(
            row=1, column=1, sticky="ew", padx=8, pady=(4, 4)
        )
        self._attach_tooltip(self.wizard_keys_frame.winfo_children()[-1], "Optional OpenAI API key.")
        ttk.Label(self.wizard_keys_frame, text="Anthropic key").grid(
            row=2, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        ttk.Entry(self.wizard_keys_frame, textvariable=self.wizard_anthropic_key_var, show="*").grid(
            row=2, column=1, sticky="ew", padx=8, pady=(4, 4)
        )
        self._attach_tooltip(self.wizard_keys_frame.winfo_children()[-1], "Optional Anthropic API key.")
        ttk.Label(self.wizard_keys_frame, text="OpenRouter key").grid(
            row=3, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        ttk.Entry(self.wizard_keys_frame, textvariable=self.wizard_openrouter_key_var, show="*").grid(
            row=3, column=1, sticky="ew", padx=8, pady=(4, 4)
        )
        self._attach_tooltip(self.wizard_keys_frame.winfo_children()[-1], "Optional OpenRouter API key.")

        ttk.Label(self.wizard_keys_frame, text="Portkey key").grid(
            row=4, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        ttk.Entry(self.wizard_keys_frame, textvariable=self.wizard_portkey_key_var, show="*").grid(
            row=4, column=1, sticky="ew", padx=8, pady=(4, 4)
        )
        self._attach_tooltip(self.wizard_keys_frame.winfo_children()[-1], "Optional Portkey API key.")

        ttk.Label(self.wizard_keys_frame, text="Google key").grid(
            row=5, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        ttk.Entry(self.wizard_keys_frame, textvariable=self.wizard_google_key_var, show="*").grid(
            row=5, column=1, sticky="ew", padx=8, pady=(4, 4)
        )
        self._attach_tooltip(self.wizard_keys_frame.winfo_children()[-1], "Optional Google API key.")
        ttk.Label(
            self.wizard_keys_frame,
            text="Portkey base URL (optional, default https://api.portkey.ai/v1)",
            style="Muted.TLabel",
        ).grid(row=6, column=0, sticky="w", padx=8, pady=(4, 8))
        ttk.Entry(self.wizard_keys_frame, textvariable=self.wizard_portkey_base_url_var).grid(
            row=6, column=1, sticky="ew", padx=8, pady=(4, 8)
        )
        self._attach_tooltip(
            self.wizard_keys_frame.winfo_children()[-1],
            "Optional Portkey base URL (default is https://api.portkey.ai/v1).",
        )

        self.wizard_audio_frame = ttk.LabelFrame(self.wizard_frame, text="Step 4 — Audio strategy")
        self.wizard_audio_frame.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        self.wizard_audio_frame.columnconfigure(1, weight=1)

        self.audio_current_note = ttk.Label(
            self.wizard_audio_frame, text="", style="Muted.TLabel", wraplength=520
        )
        self.audio_current_note.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 2))

        ttk.Label(self.wizard_audio_frame, text="Audio strategy").grid(
            row=1, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        self.wizard_audio_combo = ttk.Combobox(
            self.wizard_audio_frame,
            values=["auto", "speech_to_text", "native_only"],
            state="readonly",
            textvariable=self.audio_strategy_var,
        )
        self.wizard_audio_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_audio_combo,
            "auto = use native audio when supported, otherwise STT via abstractvoice.",
        )
        self.wizard_audio_combo.bind("<<ComboboxSelected>>", self._update_audio_fields)
        self.wizard_stt_backend_label = ttk.Label(self.wizard_audio_frame, text="STT backend (advanced)")
        self.wizard_stt_backend_label.grid(row=2, column=0, sticky="w", padx=8, pady=(4, 4))
        self.wizard_stt_backend_entry = ttk.Entry(self.wizard_audio_frame, textvariable=self.stt_backend_var)
        self.wizard_stt_backend_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_stt_backend_entry,
            "Advanced: set a specific AbstractVoice STT backend id (e.g., faster-whisper).",
        )
        self.wizard_stt_backend_note = ttk.Label(
            self.wizard_audio_frame,
            text="Advanced: choose a specific STT backend id (e.g., faster-whisper). Leave empty for auto.",
            style="Muted.TLabel",
            wraplength=520,
        )
        self.wizard_stt_backend_note.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 4))
        self.wizard_stt_language_label = ttk.Label(self.wizard_audio_frame, text="STT language")
        self.wizard_stt_language_label.grid(row=4, column=0, sticky="w", padx=8, pady=(4, 8))
        self.wizard_stt_language_combo = ttk.Combobox(
            self.wizard_audio_frame,
            values=STT_LANGUAGE_LABELS,
            state="readonly",
            textvariable=self.stt_language_var,
        )
        self.wizard_stt_language_combo.grid(row=4, column=1, sticky="ew", padx=8, pady=(4, 8))
        self._attach_tooltip(
            self.wizard_stt_language_combo,
            "Language hint for transcription. Auto-detect by default.",
        )
        self.wizard_stt_language_note = ttk.Label(
            self.wizard_audio_frame,
            text="Supported codes: en, fr, de, es, ru, zh, it, pt, ja, ko, ar, hi",
            style="Muted.TLabel",
            wraplength=520,
        )
        self.wizard_stt_language_note.grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        self.wizard_video_frame = ttk.LabelFrame(self.wizard_frame, text="Step 5 — Video strategy")
        self.wizard_video_frame.grid(row=7, column=0, sticky="ew", pady=(10, 0))
        self.wizard_video_frame.columnconfigure(1, weight=1)

        self.video_current_note = ttk.Label(
            self.wizard_video_frame, text="", style="Muted.TLabel", wraplength=520
        )
        self.video_current_note.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 2))

        ttk.Label(self.wizard_video_frame, text="Video strategy").grid(
            row=1, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        self.wizard_video_combo = ttk.Combobox(
            self.wizard_video_frame,
            values=["auto", "frames_caption", "native_only"],
            state="readonly",
            textvariable=self.video_strategy_var,
        )
        self.wizard_video_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_video_combo,
            "auto = native when supported, otherwise sample frames via ffmpeg.",
        )
        self.wizard_video_note = ttk.Label(
            self.wizard_video_frame,
            text="Frame fallback requires ffmpeg/ffprobe and a vision-capable model.",
            style="Muted.TLabel",
            wraplength=520,
        )
        self.wizard_video_note.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        self.wizard_embeddings_frame = ttk.LabelFrame(self.wizard_frame, text="Step 6 — Embeddings")
        self.wizard_embeddings_frame.grid(row=8, column=0, sticky="ew", pady=(10, 0))
        self.wizard_embeddings_frame.columnconfigure(1, weight=1)

        self.embeddings_current_note = ttk.Label(
            self.wizard_embeddings_frame, text="", style="Muted.TLabel", wraplength=520
        )
        self.embeddings_current_note.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 2))
        ttk.Label(self.wizard_embeddings_frame, text="Configure embeddings?").grid(
            row=1, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        keep_emb_rb = ttk.Radiobutton(
            self.wizard_embeddings_frame,
            textvariable=self.embeddings_keep_label_var,
            value="keep",
            variable=self.embeddings_mode_var,
            command=self._update_embeddings_fields,
        )
        keep_emb_rb.grid(row=2, column=0, columnspan=2, sticky="w", padx=8)
        self._attach_tooltip(
            keep_emb_rb,
            "Use the current embeddings configuration (shown above).",
        )
        set_emb_rb = ttk.Radiobutton(
            self.wizard_embeddings_frame,
            text="Set custom embeddings",
            value="set",
            variable=self.embeddings_mode_var,
            command=self._update_embeddings_fields,
        )
        set_emb_rb.grid(row=3, column=0, columnspan=2, sticky="w", padx=8)
        self._attach_tooltip(set_emb_rb, "Pick a different embeddings provider/model.")

        self.wizard_embeddings_provider_label = ttk.Label(self.wizard_embeddings_frame, text="Embeddings provider")
        self.wizard_embeddings_provider_label.grid(row=4, column=0, sticky="w", padx=8, pady=(6, 4))
        self.wizard_embeddings_provider_combo = ttk.Combobox(
            self.wizard_embeddings_frame,
            values=["huggingface", "ollama", "lmstudio", "openai", "openrouter", "portkey", "openai-compatible"],
            state="readonly",
            textvariable=self.embeddings_provider_var,
        )
        self.wizard_embeddings_provider_combo.grid(row=4, column=1, sticky="ew", padx=8, pady=(6, 4))
        self._attach_tooltip(
            self.wizard_embeddings_provider_combo,
            "Embeddings provider (local or cloud).",
        )
        self.wizard_embeddings_model_label = ttk.Label(self.wizard_embeddings_frame, text="Embeddings model")
        self.wizard_embeddings_model_label.grid(row=5, column=0, sticky="w", padx=8, pady=(4, 8))
        self.wizard_embeddings_model_entry = ttk.Entry(
            self.wizard_embeddings_frame, textvariable=self.embeddings_model_var
        )
        self.wizard_embeddings_model_entry.grid(row=5, column=1, sticky="ew", padx=8, pady=(4, 8))
        self._attach_tooltip(
            self.wizard_embeddings_model_entry,
            "Model id for embeddings (provider-specific).",
        )

        self.wizard_logging_frame = ttk.LabelFrame(self.wizard_frame, text="Step 7 — Logging")
        self.wizard_logging_frame.grid(row=9, column=0, sticky="ew", pady=(10, 0))
        self.wizard_logging_frame.columnconfigure(1, weight=1)

        self.logging_current_note = ttk.Label(
            self.wizard_logging_frame, text="", style="Muted.TLabel", wraplength=520
        )
        self.logging_current_note.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 2))

        ttk.Label(self.wizard_logging_frame, text="Console log level").grid(
            row=1, column=0, sticky="w", padx=8, pady=(4, 4)
        )
        self.wizard_log_combo = ttk.Combobox(
            self.wizard_logging_frame,
            values=["error", "warning", "info", "debug", "none"],
            state="readonly",
            textvariable=self.log_level_var,
        )
        self.wizard_log_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(
            self.wizard_log_combo,
            "Console log verbosity (default in AbstractCore is ERROR).",
        )

        self.wizard_finish_frame = ttk.LabelFrame(self.wizard_frame, text="Step 8 — Readiness")
        self.wizard_finish_frame.grid(row=10, column=0, sticky="ew", pady=(10, 0))
        self.wizard_finish_frame.columnconfigure(1, weight=1)

        self.wizard_download_check = ttk.Checkbutton(
            self.wizard_finish_frame,
            text="Download model now (best effort)",
            variable=self.wizard_download_var,
        )
        self._attach_tooltip(self.wizard_download_check, "Attempt to download the model after setup.")
        self.wizard_download_note = ttk.Label(self.wizard_finish_frame, text="", style="Muted.TLabel", wraplength=520)

        self.wizard_ready_check = ttk.Checkbutton(
            self.wizard_finish_frame,
            text="Run readiness checks (downloads may occur)",
            variable=self.wizard_check_var,
        )
        self._attach_tooltip(self.wizard_ready_check, "Runs abstractcore --install.")
        self.wizard_music_note = ttk.Label(
            self.wizard_finish_frame,
            text="Music fallback is configured in AbstractMusic (not part of AbstractCore).",
            style="Muted.TLabel",
            wraplength=520,
        )

        nav_frame = ttk.Frame(self.wizard_frame)
        nav_frame.grid(row=11, column=0, sticky="ew", pady=(16, 0))
        nav_frame.columnconfigure(3, weight=1)

        self.wizard_back_button = ttk.Button(nav_frame, text="Back", command=self._on_wizard_back)
        self.wizard_back_button.grid(row=0, column=0, padx=(0, 8))
        self.wizard_next_button = ttk.Button(nav_frame, text="Next", command=self._on_wizard_next)
        self.wizard_next_button.grid(row=0, column=1, padx=(0, 8))
        ttk.Button(nav_frame, text="Back to installer", command=self._hide_wizard).grid(
            row=0, column=2, padx=(0, 8)
        )
        self._attach_tooltip(self.wizard_back_button, "Go to the previous step.")
        self._attach_tooltip(self.wizard_next_button, "Advance to the next step or apply setup.")

        self.wizard_status_label = ttk.Label(nav_frame, text="", style="Muted.TLabel")
        self.wizard_status_label.grid(row=0, column=3, sticky="w")

        progress_frame = ttk.Frame(self.wizard_frame)
        progress_frame.grid(row=12, column=0, sticky="ew", pady=(10, 0))
        progress_frame.columnconfigure(1, weight=1)

        self.wizard_progress_label = ttk.Label(progress_frame, text="", style="Muted.TLabel")
        self.wizard_progress_label.grid(row=0, column=0, sticky="w")
        self.wizard_progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            style="TProgressbar",
        )
        self.wizard_progress_bar.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.wizard_progress_bar.stop()

        self.wizard_frame.grid_remove()

    def _build_install_type(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="1) Install type")
        frame.grid(row=2, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)

        self.install_desc = ttk.Label(frame, text="", wraplength=520, style="Muted.TLabel")
        self.install_desc.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(8, 4))

        for idx, (value, label, _desc) in enumerate(INSTALL_TYPES, start=1):
            rb = ttk.Radiobutton(
                frame,
                text=label,
                value=value,
                variable=self.install_type_var,
                command=self._update_install_type,
            )
            rb.grid(row=idx, column=0, sticky="w", padx=8)
            if value == "full":
                tooltip = (
                    "Full installs everything for your hardware:\n"
                    "• Apple Silicon → all-apple (includes MLX)\n"
                    "• GPU (CUDA/ROCm) → all-gpu (includes vLLM)\n"
                    "• CPU → all-non-mlx"
                )
            elif value == "standard":
                tooltip = (
                    "Standard installs common features:\n"
                    "tools, media, embeddings, tokens + your provider."
                )
            else:
                tooltip = "Custom lets you choose modules and providers manually."
            self._attach_tooltip(rb, tooltip)

        hardware_frame = ttk.Frame(frame)
        hardware_frame.grid(row=1, column=1, rowspan=3, sticky="e", padx=8)
        ttk.Checkbutton(
            hardware_frame,
            text="Apple Silicon",
            variable=self.apple_var,
            command=self._sync_hardware_toggles,
        ).grid(row=0, column=0, sticky="w")
        self._attach_tooltip(
            hardware_frame.winfo_children()[-1],
            "Use Apple Silicon optimized dependencies (MLX). Auto-detected on macOS ARM.",
        )
        self.gpu_checkbox = ttk.Checkbutton(
            hardware_frame,
            text="GPU (CUDA/ROCm)",
            variable=self.gpu_var,
            command=self._sync_hardware_toggles,
        )
        self.gpu_checkbox.grid(row=1, column=0, sticky="w")
        self._attach_tooltip(
            self.gpu_checkbox,
            "Use GPU dependencies (vLLM) for CUDA/ROCm. Auto-detected when available.",
        )
        self.hardware_note = ttk.Label(hardware_frame, text="", style="Muted.TLabel")
        self.hardware_note.grid(row=2, column=0, sticky="w", pady=(4, 0))

    def _build_provider_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="2) Provider setup")
        frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        frame.columnconfigure(1, weight=1)

        label = ttk.Label(frame, text="Default provider")
        label.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        self._attach_tooltip(label, "The provider used by default across AbstractCore apps.")
        self.provider_box = ttk.Combobox(frame, values=PROVIDER_LABELS, state="readonly")
        self.provider_box.grid(row=0, column=1, sticky="ew", padx=8, pady=(8, 4))
        self.provider_box.current(0)
        self.provider_box.bind("<<ComboboxSelected>>", self._on_provider_change)
        self._attach_tooltip(self.provider_box, "Pick where AbstractCore sends requests by default.")

        label = ttk.Label(frame, text="Default model")
        label.grid(row=1, column=0, sticky="w", padx=8, pady=(4, 4))
        model_entry = ttk.Entry(frame, textvariable=self.model_var)
        model_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=(4, 4))
        self._attach_tooltip(model_entry, "Model name used by default for the selected provider.")

        self.base_url_label = ttk.Label(frame, text="Base URL (optional)")
        self.base_url_entry = ttk.Entry(frame, textvariable=self.base_url_var)
        self.base_url_note = ttk.Label(frame, text="", style="Muted.TLabel", wraplength=520)
        self._attach_tooltip(
            self.base_url_entry,
            "Optional provider URL (e.g., local server). Stored in ~/.abstractcore/config/abstractcore.env.",
        )

        self.api_key_label = ttk.Label(frame, text="API key (optional)")
        self.api_key_entry = ttk.Entry(frame, textvariable=self.api_key_var, show="*")
        self._attach_tooltip(self.api_key_entry, "Optional API key for cloud providers.")

        self.download_check = ttk.Checkbutton(
            frame,
            text="Download model after install (best effort)",
            variable=self.download_model_var,
        )
        self._attach_tooltip(self.download_check, "Attempt to download the model after install.")
        self.download_note = ttk.Label(frame, text="", style="Muted.TLabel", wraplength=520)

        self.run_wizard_check = ttk.Label(
            frame,
            text="Your selections are applied automatically after install.",
            style="Muted.TLabel",
            wraplength=520,
        )

    def _build_custom_section(self, parent: ttk.Frame) -> None:
        self.custom_frame = ttk.LabelFrame(parent, text="3) Custom selection")
        self.custom_frame.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.custom_frame.columnconfigure(0, weight=1)

        modules_frame = ttk.Frame(self.custom_frame)
        modules_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        modules_frame.columnconfigure(1, weight=1)

        ttk.Label(modules_frame, text="Modules").grid(row=0, column=0, sticky="w")
        self.module_combo = ttk.Combobox(modules_frame, values=[label for _, label in CUSTOM_MODULES], state="readonly")
        self.module_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        add_module_btn = ttk.Button(modules_frame, text="Add", command=self._add_module)
        add_module_btn.grid(row=0, column=2, padx=(8, 0))
        self._attach_tooltip(self.module_combo, "Select optional modules to install.")
        self._attach_tooltip(add_module_btn, "Add the selected module to the custom list.")

        self.module_list = tk.Listbox(
            self.custom_frame,
            height=4,
            selectmode="extended",
            bg=THEME["bg_secondary"],
            fg=THEME["text_primary"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
            selectbackground=THEME["bg_tertiary"],
            selectforeground=THEME["text_primary"],
        )
        self.module_list.grid(row=1, column=0, sticky="ew", padx=8)
        remove_modules_btn = ttk.Button(self.custom_frame, text="Remove selected modules", command=self._remove_modules)
        remove_modules_btn.grid(
            row=2, column=0, sticky="w", padx=8, pady=(4, 8)
        )
        self._attach_tooltip(remove_modules_btn, "Remove selected modules from the list.")

        providers_frame = ttk.Frame(self.custom_frame)
        providers_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(8, 6))
        providers_frame.columnconfigure(1, weight=1)

        ttk.Label(providers_frame, text="Providers to install").grid(row=0, column=0, sticky="w")
        self.provider_combo = ttk.Combobox(
            providers_frame, values=[label for _, label in CUSTOM_PROVIDERS], state="readonly"
        )
        self.provider_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        add_provider_btn = ttk.Button(providers_frame, text="Add", command=self._add_provider)
        add_provider_btn.grid(row=0, column=2, padx=(8, 0))
        self._attach_tooltip(self.provider_combo, "Select provider dependencies to install.")
        self._attach_tooltip(add_provider_btn, "Add the selected provider to the list.")

        self.provider_list = tk.Listbox(
            self.custom_frame,
            height=4,
            selectmode="extended",
            bg=THEME["bg_secondary"],
            fg=THEME["text_primary"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
            selectbackground=THEME["bg_tertiary"],
            selectforeground=THEME["text_primary"],
        )
        self.provider_list.grid(row=4, column=0, sticky="ew", padx=8)
        remove_providers_btn = ttk.Button(
            self.custom_frame, text="Remove selected providers", command=self._remove_providers
        )
        remove_providers_btn.grid(
            row=5, column=0, sticky="w", padx=8, pady=(4, 8)
        )
        self._attach_tooltip(remove_providers_btn, "Remove selected providers from the list.")

    def _build_actions(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=5, column=0, sticky="ew", pady=(16, 0))
        frame.columnconfigure(2, weight=1)

        self.install_button = ttk.Button(frame, text="Install", command=self._on_install)
        self.install_button.grid(row=0, column=0, padx=(0, 8))
        uninstall_btn = ttk.Button(frame, text="Uninstall", command=self._on_uninstall)
        uninstall_btn.grid(row=0, column=1, padx=(0, 8))
        self._attach_tooltip(self.install_button, "Install AbstractCore into a dedicated environment.")
        self._attach_tooltip(uninstall_btn, "Remove the virtual environment (data optional).")

        self.status_label = ttk.Label(frame, text="Ready.", style="Muted.TLabel")
        self.status_label.grid(row=0, column=2, sticky="w")

        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        progress_frame.columnconfigure(1, weight=1)

        self.progress_label = ttk.Label(progress_frame, text="", style="Muted.TLabel")
        self.progress_label.grid(row=0, column=0, sticky="w")

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            style="TProgressbar",
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.progress_bar.stop()

    def _build_advanced(self, parent: ttk.Frame) -> None:
        advanced_toggle = ttk.Checkbutton(
            parent,
            text="Show advanced options",
            variable=self.show_advanced_var,
            command=self._toggle_advanced,
        )
        advanced_toggle.grid(row=7, column=0, sticky="w", pady=(12, 0))
        self._attach_tooltip(advanced_toggle, "Show install location, version, and maintenance options.")

        self.advanced_frame = ttk.Frame(parent)
        self.advanced_frame.grid(row=8, column=0, sticky="ew", pady=(6, 0))
        self.advanced_frame.columnconfigure(1, weight=1)

        ttk.Label(self.advanced_frame, text="Install location").grid(row=0, column=0, sticky="w", padx=4)
        prefix_entry = ttk.Entry(self.advanced_frame, textvariable=self.prefix_var)
        prefix_entry.grid(row=0, column=1, sticky="ew", padx=4)
        change_btn = ttk.Button(self.advanced_frame, text="Change...", command=self._browse_prefix)
        change_btn.grid(row=0, column=2, padx=4)
        self._attach_tooltip(prefix_entry, "Folder where the virtual environment is created.")
        self._attach_tooltip(change_btn, "Choose a different install folder.")

        ttk.Label(self.advanced_frame, text="Version").grid(row=1, column=0, sticky="w", padx=4, pady=(6, 0))
        version_entry = ttk.Entry(self.advanced_frame, textvariable=self.version_var)
        version_entry.grid(row=1, column=1, sticky="ew", padx=4, pady=(6, 0))
        self._attach_tooltip(version_entry, "Pin a specific AbstractCore version or use 'latest'.")

        ttk.Checkbutton(
            self.advanced_frame,
            text="Run readiness checks (downloads may occur)",
            variable=self.install_check_var,
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=4, pady=(6, 0))
        self._attach_tooltip(
            self.advanced_frame.winfo_children()[-1],
            "Runs abstractcore --install to validate subsystems and download missing assets.",
        )
        ttk.Checkbutton(
            self.advanced_frame,
            text="Recreate virtual environment",
            variable=self.recreate_venv_var,
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=4)
        self._attach_tooltip(
            self.advanced_frame.winfo_children()[-1],
            "Deletes and recreates the virtual environment before install.",
        )
        ttk.Checkbutton(
            self.advanced_frame,
            text="Uninstall: remove all data",
            variable=self.remove_all_var,
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=4)
        self._attach_tooltip(
            self.advanced_frame.winfo_children()[-1],
            "Remove the entire install directory, including data.",
        )

    def _build_details(self, parent: ttk.Frame) -> None:
        details_toggle = ttk.Checkbutton(
            parent,
            text="Show installation details",
            variable=self.show_details_var,
            command=self._toggle_details,
        )
        details_toggle.grid(row=9, column=0, sticky="w", pady=(12, 0))
        self._attach_tooltip(details_toggle, "Show detailed install logs.")

        self.log_output = ScrolledText(parent, height=10, state="disabled")
        self.log_output.grid(row=10, column=0, sticky="nsew")
        parent.rowconfigure(10, weight=1)
        self.log_output.configure(
            bg=THEME["bg_secondary"],
            fg=THEME["text_primary"],
            insertbackground=THEME["accent"],
            relief="flat",
            borderwidth=1,
            highlightbackground=THEME["border"],
        )

        self._toggle_details()
        self._toggle_advanced()

    def _browse_prefix(self) -> None:
        path = filedialog.askdirectory(initialdir=self.prefix_var.get() or str(Path.home()))
        if path:
            self.prefix_var.set(path)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.install_button.config(state=state)
        if busy:
            self.status_label.config(text=f"{self.current_action.title()} in progress...")
            self.progress_label.config(text="Working...")
            self.progress_bar.start(12)
        else:
            self.status_label.config(text="Ready.")
            self.progress_label.config(text="")
            self.progress_bar.stop()

    def _enqueue_log(self, message: str) -> None:
        self.log_queue.put(message)

    def _drain_queue(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()
                if isinstance(message, tuple) and message[0] == "__DONE__":
                    self._set_busy(False)
                    self._set_status_from_code(message[1])
                    continue
                if isinstance(message, tuple) and message[0] == "__WIZARD_DONE__":
                    self._set_setup_busy(False)
                    if message[1] == 0:
                        self.wizard_status_label.config(text="Setup complete. You're ready to go.")
                    else:
                        self.wizard_status_label.config(text="Setup failed.")
                    continue
                self._append_log(message)
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    def _append_log(self, message: str) -> None:
        self.log_output.configure(state="normal")
        self.log_output.insert("end", message)
        self.log_output.see("end")
        self.log_output.configure(state="disabled")

    def _run_installer(self, args: list[str]) -> None:
        def worker() -> None:
            try:
                def on_log(message: str) -> None:
                    msg = message if message.endswith("\n") else f"{message}\n"
                    self._enqueue_log(msg)

                code = installer_module.run_installer(args, log_callback=on_log)
                self._enqueue_log(f"[exit {code}]\n")
            except Exception as exc:  # noqa: BLE001
                self._enqueue_log(f"Error: {exc}\n")
            finally:
                self._enqueue_log(("__DONE__", code if "code" in locals() else 1))

        if self.worker and self.worker.is_alive():
            messagebox.showwarning("Installer busy", "Please wait for the current task to finish.")
            return

        self._set_busy(True)
        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _on_install(self) -> None:
        provider_key = self._selected_provider_key()
        model = self.model_var.get().strip()
        if not model:
            messagebox.showwarning("Missing model", "Please provide a model name.")
            return

        install_type = self.install_type_var.get()
        extras = self._build_extras(install_type, provider_key)
        if install_type == "custom" and not extras:
            messagebox.showwarning("Custom selection empty", "Please select at least one module or provider.")
            return

        self.current_action = "install"
        args = ["install"]
        prefix = self.prefix_var.get().strip()
        if prefix:
            args += ["--prefix", prefix]
        version = self.version_var.get().strip()
        if version:
            args += ["--version", version]

        if extras:
            args += ["--extras", ",".join(extras)]
        else:
            args += ["--profile", "minimal"]

        if self.recreate_venv_var.get():
            if not messagebox.askyesno(
                "Confirm venv recreate",
                "Recreating the virtual environment will delete the existing venv. Continue?",
            ):
                return
            args += ["--recreate-venv", "--yes"]

        self._run_installer(args)

    def _on_uninstall(self) -> None:
        if not messagebox.askyesno("Confirm uninstall", "Uninstall AbstractCore from this machine?"):
            return
        self.current_action = "uninstall"
        args = ["uninstall", "--yes"]
        prefix = self.prefix_var.get().strip()
        if prefix:
            args += ["--prefix", prefix]
        if self.remove_all_var.get():
            if not messagebox.askyesno(
                "Remove all data",
                "This will delete the entire install directory (including data). Continue?",
            ):
                return
            args.append("--remove-all")
        self._run_installer(args)

    def _add_module(self) -> None:
        label = self.module_combo.get()
        key = MODULE_LABEL_TO_KEY.get(label)
        if not key:
            return
        if key not in self.selected_modules:
            self.selected_modules.append(key)
            self.module_list.insert("end", label)

    def _remove_modules(self) -> None:
        selected = list(self.module_list.curselection())
        for index in reversed(selected):
            label = self.module_list.get(index)
            key = MODULE_LABEL_TO_KEY.get(label)
            if key in self.selected_modules:
                self.selected_modules.remove(key)
            self.module_list.delete(index)

    def _add_provider(self) -> None:
        label = self.provider_combo.get()
        key = PROVIDER_OPTION_LABEL_TO_KEY.get(label)
        if not key:
            return
        if key not in self.selected_providers:
            self.selected_providers.append(key)
            self.provider_list.insert("end", label)

    def _remove_providers(self) -> None:
        selected = list(self.provider_list.curselection())
        for index in reversed(selected):
            label = self.provider_list.get(index)
            key = PROVIDER_OPTION_LABEL_TO_KEY.get(label)
            if key in self.selected_providers:
                self.selected_providers.remove(key)
            self.provider_list.delete(index)

    def _selected_provider_key(self) -> str:
        label = self.provider_box.get()
        return PROVIDER_LABEL_TO_KEY.get(label, PROVIDERS[0][0])

    def _provider_requires_key(self, provider_key: str) -> bool:
        for key, _label, _model, _base, requires_key, _supports_base, _download in PROVIDERS:
            if key == provider_key:
                return requires_key
        return False

    def _provider_supports_base_url(self, provider_key: str) -> bool:
        for key, _label, _model, _base, _requires_key, supports_base, _download in PROVIDERS:
            if key == provider_key:
                return supports_base
        return False

    def _provider_downloadable(self, provider_key: str) -> bool:
        for key, _label, _model, _base, _requires_key, _supports_base, downloadable in PROVIDERS:
            if key == provider_key:
                return downloadable
        return False

    def _provider_default_model(self, provider_key: str) -> str:
        for key, _label, model, _base, _requires_key, _supports_base, _downloadable in PROVIDERS:
            if key == provider_key:
                return model
        return ""

    def _provider_default_base_url(self, provider_key: str) -> str:
        for key, _label, _model, base, _requires_key, _supports_base, _downloadable in PROVIDERS:
            if key == provider_key:
                return base
        return ""

    def _build_extras(self, install_type: str, provider_key: str) -> list[str]:
        if install_type == "full":
            if self.apple_var.get():
                return ["all-apple"]
            if self.gpu_var.get():
                return ["all-gpu"]
            return ["all-non-mlx"]

        if install_type == "standard":
            extras = STANDARD_FEATURES.copy()
            if provider_key in {
                "openai",
                "anthropic",
                "openrouter",
                "huggingface",
                "mlx",
                "vllm",
            }:
                extras.append(provider_key)
            return extras

        extras = self.selected_modules.copy()
        extras.extend(self.selected_providers)
        return extras

    def _sync_hardware_toggles(self) -> None:
        if self.apple_var.get():
            self.gpu_var.set(False)
            self.gpu_checkbox.state(["disabled"])
            self.hardware_note.config(text="Detected Apple Silicon.")
        else:
            self.gpu_checkbox.state(["!disabled"])
            if self.gpu_var.get():
                self.hardware_note.config(text="Detected GPU support.")
            else:
                self.hardware_note.config(text="")

    def _update_install_type(self) -> None:
        install_type = self.install_type_var.get()
        desc = next((d for v, _l, d in INSTALL_TYPES if v == install_type), "")
        self.install_desc.config(text=desc)

        if install_type == "custom":
            self.custom_frame.grid()
        else:
            self.custom_frame.grid_remove()

    def _update_provider_fields(self) -> None:
        provider_key = self._selected_provider_key()
        self.model_var.set(self._provider_default_model(provider_key))
        self.base_url_var.set(self._provider_default_base_url(provider_key))

        supports_base = self._provider_supports_base_url(provider_key)
        if supports_base:
            self.base_url_label.grid(row=2, column=0, sticky="w", padx=8, pady=(4, 2))
            self.base_url_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(4, 2))
            self.base_url_note.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
            self.base_url_note.config(text="Stored as a provider base URL environment variable.")
        else:
            self.base_url_label.grid_forget()
            self.base_url_entry.grid_forget()
            self.base_url_note.grid_forget()
            self.base_url_var.set("")

        if self._provider_requires_key(provider_key):
            self.api_key_label.grid(row=4, column=0, sticky="w", padx=8, pady=(4, 2))
            self.api_key_entry.grid(row=4, column=1, sticky="ew", padx=8, pady=(4, 2))
        else:
            self.api_key_label.grid_forget()
            self.api_key_entry.grid_forget()
            self.api_key_var.set("")

        if self._provider_downloadable(provider_key):
            self.download_check.grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 2))
            self.download_note.grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
            if provider_key == "ollama":
                note = "We will run 'ollama pull' after install."
            else:
                note = "We will attempt a best-effort download after install."
            self.download_note.config(text=note)
        else:
            self.download_check.grid_forget()
            self.download_note.grid_forget()
            self.download_model_var.set(False)

        self.run_wizard_check.grid(row=7, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 8))

    def _on_provider_change(self, _event: object | None = None) -> None:
        provider_key = self._selected_provider_key()
        self.provider_var.set(provider_key)
        self._update_provider_fields()
        if self.install_type_var.get() == "custom":
            if provider_key in {p for p, _ in CUSTOM_PROVIDERS} and provider_key not in self.selected_providers:
                self.selected_providers.append(provider_key)
                label = next(label for key, label in CUSTOM_PROVIDERS if key == provider_key)
                self.provider_list.insert("end", label)

    def _set_status_from_code(self, code: int) -> None:
        if code == 0:
            self.status_label.config(text=f"{self.current_action.title()} complete.")
            if self.current_action == "install":
                self._show_wizard()
        else:
            self.status_label.config(text=f"{self.current_action.title()} failed.")

    def _show_wizard(self) -> None:
        self.main_frame.grid_remove()
        self.wizard_frame.grid()

        self.wizard_provider_label.set(self.provider_box.get())
        self.wizard_model_var.set(self.model_var.get())
        self.wizard_base_url_var.set(self.base_url_var.get())
        self.wizard_openai_key_var.set("")
        self.wizard_anthropic_key_var.set("")
        self.wizard_openrouter_key_var.set("")
        self.wizard_portkey_key_var.set("")
        self.wizard_portkey_base_url_var.set("")
        self.wizard_google_key_var.set("")
        self.vision_download_var.set(False)
        self.vision_download_model_var.set("blip-base-caption")
        self._load_current_config()
        self._apply_current_defaults()
        self._refresh_current_config_labels()
        initial_key = self.api_key_var.get().strip()
        provider_key = PROVIDER_LABEL_TO_KEY.get(self.provider_box.get(), PROVIDERS[0][0])
        if provider_key == "openai":
            self.wizard_openai_key_var.set(initial_key)
        elif provider_key == "anthropic":
            self.wizard_anthropic_key_var.set(initial_key)
        elif provider_key == "openrouter":
            self.wizard_openrouter_key_var.set(initial_key)
        elif provider_key == "portkey":
            self.wizard_portkey_key_var.set(initial_key)

        self.wizard_download_var.set(self.download_model_var.get())
        self.wizard_check_var.set(self.install_check_var.get())

        self._update_wizard_provider_fields()
        self._update_vision_fields()
        self._update_audio_fields()
        self._update_embeddings_fields()
        self.wizard_status_label.config(text="")
        self.wizard_step = 0
        self._render_wizard_step()

    def _hide_wizard(self) -> None:
        self.wizard_frame.grid_remove()
        self.main_frame.grid()

    def _render_wizard_step(self) -> None:
        steps_total = len(self.wizard_steps)
        step_title = self.wizard_steps[self.wizard_step]
        self.wizard_step_label.config(text=f"Step {self.wizard_step + 1} of {steps_total} — {step_title}")

        self.wizard_provider_frame.grid_remove()
        self.wizard_vision_frame.grid_remove()
        self.wizard_keys_frame.grid_remove()
        self.wizard_audio_frame.grid_remove()
        self.wizard_video_frame.grid_remove()
        self.wizard_embeddings_frame.grid_remove()
        self.wizard_logging_frame.grid_remove()
        self.wizard_finish_frame.grid_remove()

        if self.wizard_step == 0:
            self.wizard_provider_frame.grid()
        elif self.wizard_step == 1:
            self.wizard_vision_frame.grid()
        elif self.wizard_step == 2:
            self.wizard_keys_frame.grid()
        elif self.wizard_step == 3:
            self.wizard_audio_frame.grid()
        elif self.wizard_step == 4:
            self.wizard_video_frame.grid()
        elif self.wizard_step == 5:
            self.wizard_embeddings_frame.grid()
        elif self.wizard_step == 6:
            self.wizard_logging_frame.grid()
        else:
            self.wizard_finish_frame.grid()

        self.wizard_back_button.config(state="disabled" if self.wizard_step == 0 else "normal")
        if self.wizard_step == steps_total - 1:
            self.wizard_next_button.config(text="Apply setup")
        else:
            self.wizard_next_button.config(text="Next")

    def _on_wizard_next(self) -> None:
        steps_total = len(self.wizard_steps)
        if self.wizard_step < steps_total - 1:
            self.wizard_step += 1
            self._render_wizard_step()
            return
        self._on_apply_setup()

    def _on_wizard_back(self) -> None:
        if self.wizard_step == 0:
            return
        self.wizard_step -= 1
        self._render_wizard_step()

    def _update_wizard_provider_fields(self) -> None:
        provider_key = PROVIDER_LABEL_TO_KEY.get(self.wizard_provider_label.get(), PROVIDERS[0][0])
        supports_base = self._provider_supports_base_url(provider_key)
        downloadable = self._provider_downloadable(provider_key)

        if supports_base:
            self.wizard_base_label.grid(row=2, column=0, sticky="w", padx=8, pady=(4, 2))
            self.wizard_base_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(4, 2))
            self.wizard_base_note.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
            self.wizard_base_note.config(text="Stored as a provider base URL environment variable.")
        else:
            self.wizard_base_label.grid_forget()
            self.wizard_base_entry.grid_forget()
            self.wizard_base_note.grid_forget()
            self.wizard_base_url_var.set("")

        if downloadable:
            self.wizard_download_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 2))
            self.wizard_download_note.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))
            note = "We will attempt a best-effort download after setup."
            if provider_key == "ollama":
                note = "We will run 'ollama pull' after setup."
            self.wizard_download_note.config(text=note)
        else:
            self.wizard_download_check.grid_forget()
            self.wizard_download_note.grid_forget()
            self.wizard_download_var.set(False)

        self.wizard_ready_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 4))
        self.wizard_music_note.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

    def _merge_config(self, base: dict, override: dict) -> dict:
        """Deep-merge config dictionaries while keeping defaults."""
        merged: dict = {}
        for key, value in base.items():
            override_value = override.get(key) if isinstance(override, dict) else None
            if isinstance(value, dict):
                merged[key] = self._merge_config(value, override_value or {})
            else:
                merged[key] = value if override_value is None else override_value
        if isinstance(override, dict):
            for key, value in override.items():
                if key not in merged:
                    merged[key] = value
        return merged

    def _load_current_config(self) -> None:
        """Load current AbstractCore config from disk (if present)."""
        self.current_config_from_file = False
        data: dict = {}
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                self.current_config_from_file = True
            except json.JSONDecodeError:
                data = {}
        self.current_config = self._merge_config(DEFAULT_CONFIG, data)

    def _label_for_stt_language(self, code: str | None) -> str:
        if not code:
            return "Auto-detect"
        return STT_LANGUAGE_CODE_TO_LABEL.get(code, code)

    def _resolve_stt_language(self, value: str) -> str:
        label = value.strip()
        if not label or label.lower().startswith("auto"):
            return ""
        return STT_LANGUAGE_LABEL_TO_CODE.get(label, label)

    def _apply_current_defaults(self) -> None:
        """Seed wizard fields with current (or default) config values."""
        vision = self.current_config.get("vision", {})
        self.vision_mode_var.set("keep")
        self.vision_provider_var.set(vision.get("caption_provider") or "")
        self.vision_model_var.set(vision.get("caption_model") or "")
        fallback = vision.get("fallback_chain") or []
        if fallback:
            self.vision_fallback_provider_var.set(fallback[0].get("provider") or "")
            self.vision_fallback_model_var.set(fallback[0].get("model") or "")
        else:
            self.vision_fallback_provider_var.set("")
            self.vision_fallback_model_var.set("")

        audio = self.current_config.get("audio", {})
        self.audio_strategy_var.set(audio.get("strategy") or "auto")
        self.stt_backend_var.set(audio.get("stt_backend_id") or "")
        self.stt_language_var.set(self._label_for_stt_language(audio.get("stt_language")))

        video = self.current_config.get("video", {})
        self.video_strategy_var.set(video.get("strategy") or "auto")

        embeddings = self.current_config.get("embeddings", {})
        self.embeddings_provider_var.set(embeddings.get("provider") or "huggingface")
        self.embeddings_model_var.set(embeddings.get("model") or "all-minilm-l6-v2")
        self.embeddings_mode_var.set("keep")

        logging_cfg = self.current_config.get("logging", {})
        console_level = (logging_cfg.get("console_level") or "ERROR").strip().lower()
        self.log_level_var.set(console_level)

    def _refresh_current_config_labels(self) -> None:
        """Update UI labels to show current configuration values."""
        vision = self.current_config.get("vision", {})
        vision_strategy = (vision.get("strategy") or "disabled").strip().lower()
        vision_provider = vision.get("caption_provider")
        vision_model = vision.get("caption_model")
        fallback_count = len(vision.get("fallback_chain") or [])
        if vision_strategy == "disabled" or (not vision_provider and not vision_model):
            vision_text = "disabled"
        elif vision_provider and vision_model:
            vision_text = f"{vision_provider}/{vision_model}"
        else:
            vision_text = f"strategy={vision_strategy}"
        if fallback_count:
            vision_text = f"{vision_text} (+{fallback_count} fallback)"
        if not self.current_config_from_file:
            vision_text = f"{vision_text} (default)"
        self.vision_current_note.config(text=f"Current: {vision_text}")
        self.vision_keep_label_var.set(f"Use existing settings (current: {vision_text})")

        audio = self.current_config.get("audio", {})
        audio_text = f"strategy={audio.get('strategy') or 'auto'}"
        if audio.get("stt_backend_id"):
            audio_text += f", backend={audio.get('stt_backend_id')}"
        else:
            audio_text += ", backend=auto"
        if audio.get("stt_language"):
            audio_text += f", language={audio.get('stt_language')}"
        else:
            audio_text += ", language=auto"
        if not self.current_config_from_file:
            audio_text = f"{audio_text} (default)"
        self.audio_current_note.config(text=f"Current: {audio_text}")

        video = self.current_config.get("video", {})
        video_text = f"strategy={video.get('strategy') or 'auto'}"
        if not self.current_config_from_file:
            video_text = f"{video_text} (default)"
        self.video_current_note.config(text=f"Current: {video_text}")

        embeddings = self.current_config.get("embeddings", {})
        emb_provider = embeddings.get("provider") or "huggingface"
        emb_model = embeddings.get("model") or "all-minilm-l6-v2"
        emb_text = f"{emb_provider}/{emb_model}"
        if not self.current_config_from_file:
            emb_text = f"{emb_text} (default)"
        self.embeddings_current_note.config(text=f"Current: {emb_text}")
        self.embeddings_keep_label_var.set(f"Use existing embeddings ({emb_text})")

        logging_cfg = self.current_config.get("logging", {})
        log_level = (logging_cfg.get("console_level") or "ERROR").strip().upper()
        log_text = log_level
        if not self.current_config_from_file:
            log_text = f"{log_text} (default)"
        self.logging_current_note.config(text=f"Current: {log_text}")

    def _update_vision_fields(self) -> None:
        mode = self.vision_mode_var.get()
        enable = mode == "enable"
        if enable:
            self.wizard_vision_provider_label.grid()
            self.wizard_vision_provider_entry.grid()
            self.wizard_vision_model_label.grid()
            self.wizard_vision_model_entry.grid()
            self.wizard_vision_fallback_provider_label.grid()
            self.wizard_vision_fallback_provider_entry.grid()
            self.wizard_vision_fallback_model_label.grid()
            self.wizard_vision_fallback_model_entry.grid()
            self.wizard_vision_download_check.grid()
        else:
            self.wizard_vision_provider_label.grid_remove()
            self.wizard_vision_provider_entry.grid_remove()
            self.wizard_vision_model_label.grid_remove()
            self.wizard_vision_model_entry.grid_remove()
            self.wizard_vision_fallback_provider_label.grid_remove()
            self.wizard_vision_fallback_provider_entry.grid_remove()
            self.wizard_vision_fallback_model_label.grid_remove()
            self.wizard_vision_fallback_model_entry.grid_remove()
            self.wizard_vision_download_check.grid_remove()

    def _update_audio_fields(self, _event: object | None = None) -> None:
        strategy = self.audio_strategy_var.get()
        enable_stt = strategy in ("auto", "speech_to_text")
        if enable_stt:
            self.wizard_stt_backend_label.grid()
            self.wizard_stt_backend_entry.grid()
            self.wizard_stt_backend_note.grid()
            self.wizard_stt_language_label.grid()
            self.wizard_stt_language_combo.grid()
            self.wizard_stt_language_note.grid()
        else:
            self.wizard_stt_backend_label.grid_remove()
            self.wizard_stt_backend_entry.grid_remove()
            self.wizard_stt_backend_note.grid_remove()
            self.wizard_stt_language_label.grid_remove()
            self.wizard_stt_language_combo.grid_remove()
            self.wizard_stt_language_note.grid_remove()

    def _update_embeddings_fields(self) -> None:
        mode = self.embeddings_mode_var.get()
        enable = mode == "set"
        if enable:
            self.wizard_embeddings_provider_label.grid()
            self.wizard_embeddings_provider_combo.grid()
            self.wizard_embeddings_model_label.grid()
            self.wizard_embeddings_model_entry.grid()
        else:
            self.wizard_embeddings_provider_label.grid_remove()
            self.wizard_embeddings_provider_combo.grid_remove()
            self.wizard_embeddings_model_label.grid_remove()
            self.wizard_embeddings_model_entry.grid_remove()

    def _on_wizard_provider_change(self, _event: object | None = None) -> None:
        provider_key = PROVIDER_LABEL_TO_KEY.get(self.wizard_provider_label.get(), PROVIDERS[0][0])
        self.wizard_model_var.set(self._provider_default_model(provider_key))
        self.wizard_base_url_var.set(self._provider_default_base_url(provider_key))
        self._update_wizard_provider_fields()

    def _set_setup_busy(self, busy: bool) -> None:
        if busy:
            self.wizard_status_label.config(text="Applying setup...")
            self.wizard_progress_label.config(text="Working...")
            self.wizard_progress_bar.start(12)
            self.wizard_next_button.config(state="disabled")
            self.wizard_back_button.config(state="disabled")
        else:
            self.wizard_progress_label.config(text="")
            self.wizard_progress_bar.stop()
            self.wizard_next_button.config(state="normal")
            self.wizard_back_button.config(state="normal")

    def _on_apply_setup(self) -> None:
        provider_key = PROVIDER_LABEL_TO_KEY.get(self.wizard_provider_label.get(), PROVIDERS[0][0])
        model = self.wizard_model_var.get().strip()
        if not model:
            messagebox.showwarning("Missing model", "Please provide a model name.")
            return

        prefix = self.prefix_var.get().strip()
        args = ["configure"]
        if prefix:
            args += ["--prefix", prefix]

        args += ["--config-provider", provider_key, "--config-model", model]

        api_keys = {
            "openai": self.wizard_openai_key_var.get().strip(),
            "anthropic": self.wizard_anthropic_key_var.get().strip(),
            "openrouter": self.wizard_openrouter_key_var.get().strip(),
            "portkey": self.wizard_portkey_key_var.get().strip(),
            "google": self.wizard_google_key_var.get().strip(),
        }
        if self._provider_requires_key(provider_key) and not api_keys.get(provider_key):
            if not messagebox.askyesno(
                "API key missing",
                "This provider usually requires an API key. Continue without one?",
            ):
                return
        for key_provider, key_value in api_keys.items():
            if key_value:
                args += ["--config-api-key", key_provider, key_value]

        base_url = self.wizard_base_url_var.get().strip()
        if base_url:
            args += ["--config-base-url", provider_key, base_url]

        portkey_base_url = self.wizard_portkey_base_url_var.get().strip()
        if portkey_base_url:
            args += ["--config-base-url", "portkey", portkey_base_url]

        vision_mode = self.vision_mode_var.get()
        if vision_mode == "enable":
            vision_provider = self.vision_provider_var.get().strip()
            vision_model = self.vision_model_var.get().strip()
            if not vision_provider or not vision_model:
                messagebox.showwarning(
                    "Missing vision config",
                    "Please provide both a vision provider and a vision model.",
                )
                return
            args += ["--config-vision-provider", vision_provider, vision_model]
            fallback_provider = self.vision_fallback_provider_var.get().strip()
            fallback_model = self.vision_fallback_model_var.get().strip()
            if fallback_provider and fallback_model:
                args += ["--config-vision-fallback", fallback_provider, fallback_model]
            if self.vision_download_var.get():
                download_model = self.vision_download_model_var.get().strip()
                if download_model:
                    args += ["--config-download-vision-model", download_model]
                else:
                    args.append("--config-download-vision-model")
        elif vision_mode == "disable":
            args.append("--config-disable-vision")

        audio_strategy = self.audio_strategy_var.get().strip()
        if audio_strategy:
            args += ["--config-audio-strategy", audio_strategy]
        stt_backend = self.stt_backend_var.get().strip()
        if stt_backend:
            args += ["--config-stt-backend-id", stt_backend]
        stt_language = self._resolve_stt_language(self.stt_language_var.get())
        if stt_language:
            args += ["--config-stt-language", stt_language]

        video_strategy = self.video_strategy_var.get().strip()
        if video_strategy:
            args += ["--config-video-strategy", video_strategy]

        if self.embeddings_mode_var.get() == "set":
            emb_provider = self.embeddings_provider_var.get().strip()
            emb_model = self.embeddings_model_var.get().strip()
            if not emb_model:
                messagebox.showwarning(
                    "Missing embeddings config",
                    "Please provide an embeddings model (or keep the default).",
                )
                return
            if emb_provider:
                args += ["--config-embeddings-provider", emb_provider]
            args += ["--config-embeddings-model", emb_model]

        log_level = self.log_level_var.get().strip()
        if log_level:
            args += ["--config-console-log-level", log_level.upper()]

        if self.wizard_check_var.get():
            args += ["--install-check", "--yes"]

        if self.wizard_download_var.get():
            args.append("--download-model")

        self.current_action = "setup"
        self._set_setup_busy(True)

        def worker() -> None:
            try:
                def on_log(message: str) -> None:
                    msg = message if message.endswith("\n") else f"{message}\n"
                    self._enqueue_log(msg)

                code = installer_module.run_installer(args, log_callback=on_log)
            except Exception as exc:  # noqa: BLE001
                self._enqueue_log(f"Error: {exc}\n")
                code = 1
            finally:
                self._enqueue_log(("__WIZARD_DONE__", code))

        threading.Thread(target=worker, daemon=True).start()

    def _toggle_details(self) -> None:
        if self.show_details_var.get():
            self.log_output.grid()
        else:
            self.log_output.grid_remove()

    def _toggle_advanced(self) -> None:
        if self.show_advanced_var.get():
            self.advanced_frame.grid()
        else:
            self.advanced_frame.grid_remove()


def main() -> None:
    app = InstallerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

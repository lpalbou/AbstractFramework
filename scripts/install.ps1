<#
.SYNOPSIS
    AbstractFramework bootstrap installer for Windows 10 22H2+ / 11 (PowerShell 5.1 and 7).

.DESCRIPTION
    One line, no admin rights, no system Python needed:

        powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"

    With options (a script block keeps the parameters):

        & ([scriptblock]::Create((irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1))) -WithApps -WithOllama

    Steps (every step prints its command; -Print shows them all and changes nothing):
      1. preflight: Windows build, arch, execution policy (Group Policy), disk, a free port
      2. uv (https://docs.astral.sh/uv) if missing, then Python 3.12 through uv
      3. uv tool install --python 3.12 "abstractgateway[<profile>,tray]==<pin>"
         (prebuilt wheels only: no compiler / MSVC Build Tools needed)
      4. optional: Node.js (nodejs-wheel), terminal tools (cargo), Ollama, LM Studio
      5. `abstractgateway service install` when the installed gateway supports it,
         otherwise a Startup-folder shortcut plus a hidden background start
      6. waits for /api/health, then opens the console (one-time claim URL when supported)

    -Full also builds the compiled extras (stable-diffusion.cpp, echo cancellation) and
    llama.cpp from source; it needs the MSVC Build Tools.

    Environment twins: AF_PROFILE, AF_PORT, AF_PIN, AF_FROM, AF_DATA_DIR.

.EXAMPLE
    .\install.ps1 -Print
.EXAMPLE
    .\install.ps1 -Profile light -Port 18080 -NoService -NoOpen
.EXAMPLE
    .\install.ps1 -Uninstall -Purge
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    # No [ValidateSet] here: `irm | iex` evaluates this block as statements, and a
    # validation attribute on an empty default fails there. Main validates the value.
    [Alias('Profile')]
    [string]$InstallProfile = '',
    [int]$Port = 0,
    [string]$Pin = '',
    [string]$From = '',
    [string]$Manifest = '',
    [string]$DataDir = '',
    [switch]$WithApps,
    [switch]$WithConsole,
    [switch]$WithCodeCli,
    [switch]$WithCoreCli,
    [switch]$WithOllama,
    [switch]$WithLmStudio,
    [switch]$Full,
    [switch]$NoTray,
    [switch]$NoService,
    [switch]$NoStart,
    [switch]$NoOpen,
    [switch]$NoModifyPath,
    [switch]$Print,
    [switch]$PrintVersions,
    [switch]$Uninstall,
    [switch]$Purge
)

# ---------------------------------------------------------------------------
# Release pins. The gateway pin mirrors `bootstrap.gateway_version` in
# docs/installers/install-manifest.json (scripts/tests/test_inventory.sh fails on
# drift); a manifest next to this script wins at runtime.
# ---------------------------------------------------------------------------
$AfGatewayPinDefault = '0.5.0'
$AfPython = '3.12'
$AfNpmApps = @('@abstractframework/flow@0.3.21', '@abstractframework/code@0.5.0', '@abstractframework/observer@0.1.13', '@abstractframework/continuum@0.3.2', '@abstractframework/entity@0.2.2')
$AfCrateConsole = 'abstractgateway-console@0.9.0'
$AfCrateCodeCli = 'abstractcode@0.6.0'
$AfDocs = 'https://github.com/lpalbou/AbstractFramework/blob/main/docs/install.md'
$AfScriptUrl = 'https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1'

# ---------------------------------------------------------------------------
# Prebuilt wheels only: by default no compiler (MSVC Build Tools) is needed.
# `uv tool install` gets an overrides file (an override whose marker is never true
# drops the package) and --no-build-package for the same packages, so a gap fails
# fast instead of starting a compiler: webrtcvad is always dropped (webrtcvad-wheels
# comes in through --with), vllm is Linux-only, and the compiled extras
# (stable-diffusion-cpp-python, aec-audio-processing; optional, imported lazily)
# are dropped unless -Full, which builds them from source and so needs a compiler.
# llama-cpp-python (llama.cpp GGUF, every profile) comes from upstream's prebuilt
# CPU wheel on x64 Windows: --find-links on the package page of abetlen's wheel
# index, pinned through --constraints uv-constraints.txt, --no-build-package so the
# sdist is never built. No wheel for Windows on ARM; there, and whenever the wheel
# install fails, it is dropped and the summary says so. -Full builds it from source.
# Same lists as install.sh (tests/test_install_profiles.py checks).
# ---------------------------------------------------------------------------
$AfWithWheels = 'webrtcvad-wheels>=2.0.14'
$AfCompiledExtras = @('stable-diffusion-cpp-python', 'aec-audio-processing')
$AfSkippedLine = 'Skipped compiled extras (stable-diffusion.cpp, echo cancellation): re-run with -Full after installing a C compiler.'
$AfLlamaIndex = 'https://abetlen.github.io/llama-cpp-python/whl'
$AfLlamaCpuPin = '0.3.35'
$AfGgufSkipped = 'GGUF (llama.cpp) skipped: no prebuilt wheel for this machine; re-run with -Full after installing a C compiler'
function Get-UvOverrides([bool]$WithCompiledExtras, [bool]$Gguf) {
    $lines = @("webrtcvad; sys_platform == 'never'", "vllm>=0.6.0,<1.0.0; sys_platform == 'linux'")
    if (-not $WithCompiledExtras) {
        foreach ($p in $AfCompiledExtras) { $lines += "$p; sys_platform == 'never'" }
        if (-not $Gguf) { $lines += "llama-cpp-python; sys_platform == 'never'" }
    }
    return $lines
}
function Get-NoBuildPackages([bool]$WithCompiledExtras) {
    $pkgs = @('webrtcvad', 'vllm')
    if (-not $WithCompiledExtras) { $pkgs += $AfCompiledExtras + @('llama-cpp-python') }
    return $pkgs
}

$script:RanAsFile = [bool]$PSCommandPath
$script:DryRun = [bool]($Print -or $WhatIfPreference)
$script:Twins = New-Object System.Collections.Generic.List[string]
$script:LogFile = ''
$script:StepNo = 0

function Write-Step([string]$Text) { $script:StepNo++; Write-Host ''; Write-Host "[$($script:StepNo)] $Text" -ForegroundColor White }
function Write-Ok([string]$Text) { Write-Host '  + ' -ForegroundColor Green -NoNewline; Write-Host $Text }
function Write-Info([string]$Text) { Write-Host '  . ' -ForegroundColor Cyan -NoNewline; Write-Host $Text }
function Write-Warn2([string]$Text) { Write-Host '  ! ' -ForegroundColor Yellow -NoNewline; Write-Host $Text }
function Stop-Install([string]$Text) { throw "AFBOOT: $Text" }

function Format-Arg([string]$Value) {
    if ($Value -match '^[A-Za-z0-9_./:=@,+%\\-]+$') { return $Value }
    return "'" + ($Value -replace "'", "''") + "'"
}
function Format-Cmd([string[]]$Argv) { return (($Argv | ForEach-Object { Format-Arg $_ }) -join ' ') }

# Run a native command: print it, log its output, fail loudly on a non-zero exit.
function Invoke-Native {
    param([string]$Description, [string[]]$Argv, [switch]$Soft, [string]$Shown = '')
    if (-not $Shown) { $Shown = Format-Cmd $Argv }
    Write-Host "  `$ $Shown" -ForegroundColor DarkGray
    $script:Twins.Add($Shown)
    if ($script:DryRun) { return $true }
    $exe = $Argv[0]
    $rest = @()
    if ($Argv.Count -gt 1) { $rest = $Argv[1..($Argv.Count - 1)] }
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # PS 5.1 turns native stderr into errors
    try {
        Add-Content -Path $script:LogFile -Value "`r`n`$ $Shown" -Encoding UTF8
        & $exe @rest 2>&1 | ForEach-Object { "$_" } | Add-Content -Path $script:LogFile -Encoding UTF8
        $code = $LASTEXITCODE
    } catch {
        Add-Content -Path $script:LogFile -Value "$_" -Encoding UTF8
        $code = 1
    } finally {
        $ErrorActionPreference = $old
    }
    if ($code -eq 0) { return $true }
    if ($Soft) {
        Write-Warn2 "$Description did not succeed (exit $code; details in $($script:LogFile)); continuing"
        return $false
    }
    Write-Host "  --- last lines of $($script:LogFile) ---" -ForegroundColor DarkGray
    Get-Content -Path $script:LogFile -Tail 25 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
    if (-not (Test-Net)) {
        Stop-Install "$Description failed because the internet connection dropped (command: $Shown).`nWhat to do: reconnect, then run the installer again; it continues where it stopped."
    }
    Stop-Install "$Description failed (command: $Shown).`nWhat to do: run the installer again (it repairs a half-finished install). If it stops at the same step, report it with the log file: $($script:LogFile) ($AfDocs#if-something-goes-wrong)"
}

# Vendor one-liners (`irm ... | iex`) run in a child PowerShell with a per-process
# ByPass policy, so a vendor script that calls `exit` cannot end this installer.
function Invoke-VendorScript([string]$Description, [string]$Url, [hashtable]$EnvVars = @{}) {
    $prefix = ''
    foreach ($k in $EnvVars.Keys) { $prefix += "`$env:$k='$($EnvVars[$k])'; " }
    $command = "${prefix}irm $Url | iex"
    $psExe = (Get-Process -Id $PID).Path
    Invoke-Native -Description $Description -Argv @($psExe, '-NoProfile', '-ExecutionPolicy', 'ByPass', '-Command', $command) `
        -Shown "powershell -ExecutionPolicy ByPass -c `"$command`""
}

function Test-PortBusy([int]$P) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect('127.0.0.1', $P, $null, $null)
        if ($async.AsyncWaitHandle.WaitOne(700) -and $client.Connected) { return $true }
        return $false
    } catch { return $false } finally { $client.Close() }
}

function Get-Http([string]$Url, [int]$TimeoutSec = 5) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return [string]$r.Content
    } catch { return $null }
}

# Plain-language network check (same probe and wording as install.sh).
function Test-Net { return ($null -ne (Get-Http 'https://pypi.org/simple/pip/' 15)) }
function Get-OfflineMessage {
    $proxy = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } elseif ($env:https_proxy) { $env:https_proxy } else { '' }
    if ($proxy) { return "this computer cannot reach pypi.org through the proxy set in your environment ($proxy).`nWhat to do: check that proxy (or remove the HTTPS_PROXY setting), then run the installer again." }
    return "no internet connection: the installer could not reach pypi.org, where it downloads AbstractFramework.`nWhat to do: connect to the internet (Wi-Fi or cable), then run the installer again. Nothing was changed."
}

function Test-Command([string]$Name) { return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Read-State([string]$Path) {
    $state = @{}
    if (Test-Path -LiteralPath $Path) {
        foreach ($line in Get-Content -LiteralPath $Path) {
            if ($line -match '^([A-Z_]+)=(.*)$') { $state[$Matches[1]] = $Matches[2] }
        }
    }
    return $state
}

function Main {
    if ($PrintVersions) {
        Write-Output "pypi abstractgateway $AfGatewayPinDefault"
        foreach ($s in $AfNpmApps) { $i = $s.LastIndexOf('@'); Write-Output "npm $($s.Substring(0, $i)) $($s.Substring($i + 1))" }
        foreach ($s in @($AfCrateConsole, $AfCrateCodeCli)) { $i = $s.LastIndexOf('@'); Write-Output "crates $($s.Substring(0, $i)) $($s.Substring($i + 1))" }
        return
    }

    # --- platform --------------------------------------------------------------
    $onWindows = ($PSVersionTable.PSEdition -eq 'Desktop') -or ($IsWindows -eq $true)
    if (-not $onWindows -and -not $script:DryRun) {
        Stop-Install 'this installer is for Windows; on macOS/Linux run: curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh'
    }
    $homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    $localAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $homeDir 'AppData/Local' }

    $profileName = $InstallProfile
    if (-not $profileName) { $profileName = if ($env:AF_PROFILE) { $env:AF_PROFILE } else { 'auto' } }
    if ($Port -eq 0 -and $env:AF_PORT) { $Port = [int]$env:AF_PORT }
    if (-not $Pin -and $env:AF_PIN) { $Pin = $env:AF_PIN }
    if (-not $From -and $env:AF_FROM) { $From = $env:AF_FROM }
    if (-not $DataDir) {
        if ($env:AF_DATA_DIR) { $DataDir = $env:AF_DATA_DIR }
        elseif ($env:ABSTRACTGATEWAY_DATA_DIR) { $DataDir = $env:ABSTRACTGATEWAY_DATA_DIR }
        else { $DataDir = Join-Path $localAppData 'AbstractGateway' }
    }
    $stateFile = Join-Path $DataDir 'bootstrap.env'
    $pidFile = Join-Path $DataDir 'gateway.pid'
    $logDir = Join-Path $DataDir 'logs'
    $gatewayLog = Join-Path $logDir 'gateway.log'
    $gatewayErr = Join-Path $logDir 'gateway.err.log'
    $startupDir = [Environment]::GetFolderPath('Startup')
    $shortcut = if ($startupDir) { Join-Path $startupDir 'AbstractGateway.lnk' } else { '' }
    $state = Read-State $stateFile

    # uv discovery (the official installer puts uv in %USERPROFILE%\.local\bin).
    $uv = $null
    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCmd) { $uv = $uvCmd.Source }
    else {
        foreach ($c in @($env:UV_INSTALL_DIR, (Join-Path $homeDir '.local/bin'), (Join-Path $homeDir '.cargo/bin'))) {
            if (-not $c) { continue }
            foreach ($n in @('uv.exe', 'uv')) {
                $p = Join-Path $c $n
                if (Test-Path -LiteralPath $p) { $uv = $p; break }
            }
            if ($uv) { break }
        }
    }
    $toolBin = $null
    if ($uv) { try { $toolBin = (& $uv tool dir --bin 2>$null | Select-Object -First 1) } catch { $toolBin = $null } }
    if (-not $toolBin) { $toolBin = if ($env:UV_TOOL_BIN_DIR) { $env:UV_TOOL_BIN_DIR } else { Join-Path $homeDir '.local/bin' } }
    $exeSuffix = if ($onWindows) { '.exe' } else { '' }
    $gw = Join-Path $toolBin "abstractgateway$exeSuffix"
    $gwCfg = Join-Path $toolBin "abstractgateway-config$exeSuffix"

    function Test-GatewaySupports([string]$What) {
        $exe = if ($What -eq 'claim-url') { $gwCfg } else { $gw }
        if (-not (Test-Path -LiteralPath $exe)) { return $false }
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try {
            if ($What -eq 'claim-url') { & $exe claim-url --help *> $null } else { & $exe $What --help *> $null }
            return ($LASTEXITCODE -eq 0)
        } catch { return $false } finally { $ErrorActionPreference = $old }
    }
    # Before a background `serve` without --host/--port: make the gateway's Network setting
    # hold this install's port. Nothing stored yet -> `localhost` (127.0.0.1, the bind the
    # installer always used). A stored mode (e.g. `lan` chosen in the tray) is KEPT; only its
    # port is aligned to $Port. $false when the setting cannot be read: the caller then starts
    # the old pinned command line, and says so.
    function Set-NetworkSettingForStart {
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $cfg = $null
        try { $cfg = ((& $gw network status --json 2>$null) -join "`n" | ConvertFrom-Json).configured } catch { $cfg = $null }
        finally { $ErrorActionPreference = $old }
        if (-not $cfg -or -not $cfg.mode) {
            Write-Warn2 "could not read the gateway's Network setting ('abstractgateway network status' failed); starting it pinned to 127.0.0.1:$Port, so a Network choice will not apply until the next run"
            return $false
        }
        if ("$($cfg.source)" -ne 'stored') {
            Invoke-Native -Description 'store the Network setting' -Argv @($gw, 'network', 'set', 'localhost', '--port', "$Port") | Out-Null
        } elseif ("$($cfg.port_source)" -ne 'stored' -or "$($cfg.port)" -ne "$Port") {
            # `internet` was acknowledged when it was chosen; only the port changes here.
            $argv = @($gw, 'network', 'set', "$($cfg.mode)", '--port', "$Port")
            if ("$($cfg.mode)" -eq 'internet') { $argv += '--acknowledge-internet' }
            Invoke-Native -Description "keep the Network setting '$($cfg.mode)', port $Port" -Argv $argv | Out-Null
        } else {
            Write-Ok "Network setting kept: '$($cfg.mode)' on port $Port"
        }
        return $true
    }
    function Get-OurPid {
        if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
        $p = (Get-Content -LiteralPath $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($p -and (Get-Process -Id ([int]$p) -ErrorAction SilentlyContinue)) { return [int]$p }
        return $null
    }
    function Stop-OurGateway {
        $p = Get-OurPid
        if ($p) {
            Write-Host "  `$ Stop-Process -Id $p" -ForegroundColor DarkGray
            $script:Twins.Add("Stop-Process -Id $p")
            if (-not $script:DryRun) {
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
            }
        }
    }

    if (-not $script:DryRun) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
        $script:LogFile = Join-Path $logDir ("install-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
        New-Item -ItemType File -Force -Path $script:LogFile | Out-Null
    }

    # --- uninstall ------------------------------------------------------------------
    if ($Uninstall) {
        Write-Host 'AbstractFramework uninstall' -ForegroundColor White
        Write-Step 'Gateway service and processes'
        # Only touch the login service when this install registered it (or when no state says
        # otherwise): a -NoService install must not unregister a service set up separately.
        if ($state['MODE'] -eq 'background' -or $state['MODE'] -eq 'none') {
            Write-Info "no login service was registered by this install (mode: $($state['MODE']))"
        } elseif (Test-GatewaySupports 'service') {
            Invoke-Native -Description 'remove the gateway service' -Argv @($gw, 'service', 'uninstall') | Out-Null
        }
        if ($shortcut -and (Test-Path -LiteralPath $shortcut)) {
            Write-Host "  `$ Remove-Item '$shortcut'" -ForegroundColor DarkGray
            if (-not $script:DryRun) { Remove-Item -LiteralPath $shortcut -Force }
        }
        Stop-OurGateway
        Write-Step 'uv tools'
        if ($uv) {
            $tools = (& $uv tool list 2>$null) -join "`n"
            if ($tools -match '(?m)^abstractgateway ') { Invoke-Native -Description 'uninstall abstractgateway' -Argv @($uv, 'tool', 'uninstall', 'abstractgateway') | Out-Null }
            else { Write-Info 'abstractgateway is not installed as a uv tool' }
            if ($state['NODE_WHEEL'] -eq '1' -and $tools -match '(?m)^nodejs-wheel ') {
                Invoke-Native -Description 'uninstall nodejs-wheel' -Argv @($uv, 'tool', 'uninstall', 'nodejs-wheel') | Out-Null
            }
        } else { Write-Info 'uv not found; nothing to uninstall there' }
        Write-Step 'Data'
        if ($Purge) {
            Write-Host "  `$ Remove-Item -Recurse -Force '$DataDir'" -ForegroundColor DarkGray
            if (-not $script:DryRun) { Remove-Item -LiteralPath $DataDir -Recurse -Force -ErrorAction SilentlyContinue }
        } else { Write-Info "kept the gateway data dir: $DataDir (delete it with -Uninstall -Purge)" }
        Write-Info 'kept: uv, Ollama, LM Studio, and any cargo tools'
        Write-Host ''; Write-Host 'Done.' -ForegroundColor Green
        return
    }

    # --- pin --------------------------------------------------------------------------
    $pinSource = ''
    if ($Pin) { $pinSource = '-Pin' }
    elseif ($From) { $pinSource = '-From' }
    else {
        if (-not $Manifest -and $PSScriptRoot) {
            $m = Join-Path $PSScriptRoot '../docs/installers/install-manifest.json'
            if (Test-Path -LiteralPath $m) { $Manifest = $m }
        }
        if ($Manifest) {
            if (-not (Test-Path -LiteralPath $Manifest)) { Stop-Install "-Manifest: no such file: $Manifest" }
            $Pin = [string]((Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json).bootstrap.gateway_version)
            if (-not $Pin) { Stop-Install "no bootstrap.gateway_version in $Manifest" }
            $pinSource = $Manifest
        } else { $Pin = $AfGatewayPinDefault; $pinSource = 'built into install.ps1' }
    }

    # --- 1. preflight -------------------------------------------------------------------
    $banner = if ($script:DryRun) { '(-Print: preflight only, nothing is installed)' } else { $AfScriptUrl }
    Write-Host 'AbstractFramework bootstrap  ' -ForegroundColor White -NoNewline; Write-Host $banner -ForegroundColor DarkGray
    Write-Step 'Preflight'
    $arch = if ($env:PROCESSOR_ARCHITECTURE) { $env:PROCESSOR_ARCHITECTURE } else { [string][System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture }
    $ver = [Environment]::OSVersion.Version
    if ($onWindows) {
        Write-Ok "system: Windows $($ver.Major).$($ver.Minor) build $($ver.Build), $arch, PowerShell $($PSVersionTable.PSVersion)"
        if ($ver.Build -lt 19045) { Write-Warn2 'Windows 10 22H2 (build 19045) or Windows 11 is the supported baseline' }
    } else {
        Write-Warn2 "not Windows ($([System.Runtime.InteropServices.RuntimeInformation]::OSDescription)): -Print only; use install.sh here"
    }

    # Execution policy: Group Policy scopes override -ExecutionPolicy ByPass.
    try {
        $gpo = @()
        if ($onWindows) {
            $gpo = Get-ExecutionPolicy -List | Where-Object {
                ($_.Scope -eq 'MachinePolicy' -or $_.Scope -eq 'UserPolicy') -and @('AllSigned', 'Restricted') -contains "$($_.ExecutionPolicy)"
            }
        }
        foreach ($g in $gpo) {
            Write-Warn2 "Group Policy sets the execution policy ($($g.Scope) = $($g.ExecutionPolicy)); it overrides -ExecutionPolicy ByPass."
            Write-Info  'this installer still works when pasted as `irm ... | iex` (a command, not a script file) and it only launches .exe files;'
            Write-Info  'a saved install.ps1 cannot run under AllSigned/Restricted: use the one-liner, or ask your administrator.'
        }
    } catch { }

    # A compiler is only needed for -Full (cl.exe on PATH, or MSVC found by vswhere).
    $hasCc = Test-Command 'cl.exe'
    if (-not $hasCc -and ${env:ProgramFiles(x86)}) {
        $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
        if (Test-Path -LiteralPath $vswhere) {
            try { $hasCc = [bool](& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2>$null) } catch { }
        }
    }
    if (-not $hasCc) {
        if ($Full) { Stop-Install '-Full builds llama.cpp, stable-diffusion.cpp and echo cancellation from source and needs a C compiler: install the Visual Studio Build Tools ("Desktop development with C++"), then re-run with -Full' }
        Write-Info 'no C compiler (MSVC Build Tools) - fine, all packages install as prebuilt wheels'
    } elseif ($Full) {
        Write-Ok 'C compiler found: -Full builds the compiled extras from source (several minutes)'
    }

    $hasNvidia = $false
    if (Test-Command 'nvidia-smi') { try { & nvidia-smi -L *> $null; $hasNvidia = ($LASTEXITCODE -eq 0) } catch { } }
    switch ($profileName) {
        'auto' {
            if ($state['PROFILE']) { $profileName = $state['PROFILE']; $why = 'kept from the previous install' }
            elseif ($hasNvidia) { $profileName = 'gpu'; $why = 'nvidia-smi found a GPU (best-effort on Windows)' }
            else { $profileName = 'light'; $why = 'no local accelerator stack detected' }
            Write-Ok "profile: $profileName ($why; override with -Profile)"
        }
        'light' { Write-Ok 'profile: light (remote/endpoint engines only)' }
        'gpu' {
            if (-not $hasNvidia) { Write-Warn2 'gpu profile requested but nvidia-smi does not work; local GPU engines will fall back to CPU' }
            Write-Ok 'profile: gpu (local CUDA engines; best-effort on Windows)'
        }
        'apple' { Stop-Install 'the apple profile is for Apple Silicon Macs; use -Profile light or gpu' }
        default { Stop-Install "unknown profile '$profileName' (expected auto, light or gpu)" }
    }

    $extras = @()
    if ($profileName -eq 'gpu') { $extras += 'gpu' }
    if (-not $NoTray) { $extras += 'tray' }
    $extraText = if ($extras.Count) { '[' + ($extras -join ',') + ']' } else { '' }
    if ($From) {
        if (Test-Path -LiteralPath $From) {
            $abs = (Resolve-Path -LiteralPath $From).Path
            $gwSpec = "abstractgateway$extraText @ " + ([Uri]$abs).AbsoluteUri
        } else { $gwSpec = $From }
    } elseif ($Pin -eq 'latest') { $gwSpec = "abstractgateway$extraText" }
    else { $gwSpec = "abstractgateway$extraText==$Pin" }
    Write-Ok "gateway: $gwSpec  (pin from $pinSource)"

    # Disk.
    $needMb = if ($profileName -eq 'gpu') { 12000 } else { 1500 }
    if ($WithApps) { $needMb += 300 }
    try {
        $root = [System.IO.Path]::GetPathRoot($homeDir)
        $freeMb = [int]((New-Object System.IO.DriveInfo($root)).AvailableFreeSpace / 1MB)
        if ($freeMb -lt 1000) { Stop-Install "only $freeMb MB free on $root (about $needMb MB needed)" }
        elseif ($freeMb -lt $needMb) { Write-Warn2 "only $freeMb MB free on $root; the $profileName profile needs about $needMb MB (models need more)" }
        else { Write-Ok "disk: $freeMb MB free (about $needMb MB needed, models extra)" }
    } catch { if ("$_" -like 'AFBOOT:*') { throw } }

    # Long paths (uv tool environments nest deeply).
    if ($onWindows) {
        try {
            $lp = (Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name LongPathsEnabled -ErrorAction Stop).LongPathsEnabled
            if ($lp -ne 1) { Write-Info 'Windows long paths are disabled; if an install fails with a path error, enable them (admin) or use a short user name' }
        } catch { }
    }

    # Port.
    $explicitPort = ($Port -ne 0)
    if (-not $explicitPort) { $Port = if ($state['PORT']) { [int]$state['PORT'] } else { 8080 } }
    $reuseRunning = $false
    if (Test-PortBusy $Port) {
        $ours = ("$Port" -eq $state['PORT']) -and ((Get-OurPid) -or ($state['MODE'] -eq 'service' -and ((Get-Http "http://127.0.0.1:$Port/api/health") -match 'abstractgateway')))
        if ($ours) { $reuseRunning = $true; Write-Ok "port ${Port}: this install's gateway is already running (restarted if the package changes)" }
        elseif ($explicitPort) { Stop-Install "port $Port is already in use by another process; pick another one with -Port" }
        else {
            $p = $Port + 1
            while ($p -le $Port + 20 -and (Test-PortBusy $p)) { $p++ }
            if ($p -gt $Port + 20) { Stop-Install "ports $Port-$($Port + 20) are all busy; pick one with -Port" }
            Write-Warn2 "port $Port is in use by another process; using $p (kept for future runs)"
            $Port = $p
        }
    } else { Write-Ok "port $Port is free" }
    $baseUrl = "http://127.0.0.1:$Port"

    if (Test-Net) { Write-Ok 'internet: pypi.org reachable' }
    elseif ($script:DryRun) { Write-Warn2 ((Get-OfflineMessage) -split "`n")[0] }
    else { Stop-Install (Get-OfflineMessage) }

    # --- 2. uv + Python -------------------------------------------------------------------
    Write-Step 'uv (Python toolchain manager)'
    if ($uv) {
        Write-Ok "uv found: $uv"
    } else {
        Write-Info 'installing uv from astral.sh into %USERPROFILE%\.local\bin (no admin)'
        Invoke-VendorScript -Description 'install uv' -Url 'https://astral.sh/uv/install.ps1' -EnvVars @{ UV_NO_MODIFY_PATH = '1' } | Out-Null
        if ($script:DryRun) { $uv = 'uv' }
        else {
            foreach ($c in @($env:UV_INSTALL_DIR, (Join-Path $homeDir '.local/bin'))) {
                if ($c -and (Test-Path -LiteralPath (Join-Path $c 'uv.exe'))) { $uv = Join-Path $c 'uv.exe'; break }
            }
            if (-not $uv) { Stop-Install 'uv was installed but cannot be found in %USERPROFILE%\.local\bin' }
            Write-Ok "uv installed: $uv"
            $toolBin = (& $uv tool dir --bin 2>$null | Select-Object -First 1)
            $gw = Join-Path $toolBin 'abstractgateway.exe'
            $gwCfg = Join-Path $toolBin 'abstractgateway-config.exe'
        }
    }

    Write-Step "Python $AfPython (managed by uv, isolated from any system Python)"
    Invoke-Native -Description "install Python $AfPython" -Argv @($uv, 'python', 'install', $AfPython) | Out-Null

    # --- 3. gateway ---------------------------------------------------------------------------
    Write-Step 'AbstractGateway'
    function Get-GatewayToolVersion {
        if ($script:DryRun -or -not (Test-Path -LiteralPath $uv)) { return '' }
        $line = (& $uv tool list 2>$null) | Where-Object { $_ -match '^abstractgateway v' } | Select-Object -First 1
        if ($line -match '^abstractgateway v(\S+)') { return $Matches[1] }
        return ''
    }
    $before = Get-GatewayToolVersion
    # llama.cpp GGUF: the prebuilt CPU wheel on x64 Windows (see the top of this script).
    $ggufPin = ''; $ggufLinks = ''
    $cpuArch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    if (-not $Full -and ($cpuArch -eq 'AMD64' -or -not $onWindows)) {
        $ggufPin = $AfLlamaCpuPin; $ggufLinks = "$AfLlamaIndex/cpu/llama-cpp-python/"
    }
    # uv splits --overrides / --constraints values at whitespace (a user name with a
    # space), so the install runs from the data dir and names both files relatively.
    function Install-Gateway([bool]$Gguf, [switch]$Soft) {
        $overrides = Get-UvOverrides $Full $Gguf
        if ($script:DryRun) {
            Write-Info "$(Join-Path $DataDir 'uv-overrides.txt') (written at install time; see the top of install.ps1):"
            foreach ($l in $overrides) { Write-Host "      $l" }
            if ($Gguf) { Write-Info "$(Join-Path $DataDir 'uv-constraints.txt'):"; Write-Host "      llama-cpp-python==$ggufPin" }
        } else {
            # UTF-8 without a BOM (Set-Content -Encoding UTF8 adds one on PowerShell 5.1).
            [System.IO.File]::WriteAllText((Join-Path $DataDir 'uv-overrides.txt'), ($overrides -join "`n") + "`n")
            if ($Gguf) { [System.IO.File]::WriteAllText((Join-Path $DataDir 'uv-constraints.txt'), "llama-cpp-python==$ggufPin`n") }
        }
        $argv = @($uv, 'tool', 'install', '--python', $AfPython, '--with', $AfWithWheels)
        if ($Gguf) { $argv += @('--with', "llama-cpp-python==$ggufPin", '--constraints', 'uv-constraints.txt', '--find-links', $ggufLinks) }
        elseif ($Full) { $argv += @('--with', 'llama-cpp-python') }
        $argv += @('--overrides', 'uv-overrides.txt')
        foreach ($p in (Get-NoBuildPackages $Full)) { $argv += @('--no-build-package', $p) }
        if ($WithCoreCli) { $argv += @('--with-executables-from', 'abstractcore') }
        if ($From) { $argv += '--reinstall' }
        $shownInstall = "Set-Location $(Format-Arg $DataDir); $(Format-Cmd ($argv + @($gwSpec)))"
        $desc = if ($Gguf) { 'install abstractgateway with the llama.cpp cpu wheel' } else { 'install abstractgateway' }
        if (-not $script:DryRun) { Push-Location -LiteralPath $DataDir }
        try {
            return (Invoke-Native -Description $desc -Argv ($argv + @($gwSpec)) -Shown $shownInstall -Soft:$Soft)
        } finally {
            if (-not $script:DryRun) { Pop-Location }
        }
    }
    $ggufResult = ''
    if ($before -and $Pin -eq 'latest' -and -not $From -and $state['PROFILE'] -eq $profileName) {
        Invoke-Native -Description 'upgrade abstractgateway' -Argv @($uv, 'tool', 'upgrade', 'abstractgateway') | Out-Null
        $ggufResult = 'as in the previous install (uv tool upgrade keeps it)'
    } elseif ($Full) {
        Install-Gateway $false | Out-Null
        $ggufResult = 'llama-cpp-python built from source (-Full)'
    } elseif ($ggufPin) {
        if ($script:DryRun) { Write-Info "llama.cpp GGUF: llama-cpp-python $ggufPin, cpu wheel from $ggufLinks (if this install fails, it is retried without it)" }
        if (Install-Gateway $true -Soft) {
            $ggufResult = "llama-cpp-python $ggufPin (cpu wheel from $ggufLinks)"
        } else {
            Write-Warn2 $AfGgufSkipped
            Install-Gateway $false | Out-Null
            $ggufResult = "skipped (the prebuilt cpu wheel did not install; see $($script:LogFile))"
        }
    } else {
        Write-Warn2 $AfGgufSkipped
        Install-Gateway $false | Out-Null
        $ggufResult = "skipped (no prebuilt wheel for Windows $cpuArch)"
    }
    $after = $before
    if (-not $script:DryRun) {
        $after = Get-GatewayToolVersion
        if (-not (Test-Path -LiteralPath $gw)) { Stop-Install "abstractgateway is not in $toolBin after the install" }
        if (-not $before) { Write-Ok "installed abstractgateway $after" }
        elseif ($before -eq $after -and -not $From) { Write-Ok "abstractgateway $after already installed" }
        else { Write-Ok "abstractgateway $before -> $after" }
    }
    $changed = ($before -ne $after) -or [bool]$From -or ($state['GATEWAY_SPEC'] -and $state['GATEWAY_SPEC'] -ne $gwSpec)

    $pathParts = ($env:PATH -split [IO.Path]::PathSeparator)
    if ($pathParts -notcontains $toolBin) {
        if (-not $NoModifyPath) {
            Invoke-Native -Description "add $toolBin to your user PATH" -Argv @($uv, 'tool', 'update-shell') -Soft | Out-Null
            Write-Info "open a new terminal for the 'abstractgateway' command to be on PATH"
        } else { Write-Warn2 "$toolBin is not on PATH; add it yourself or use absolute paths" }
    }

    # --- 4. optional components ---------------------------------------------------------------
    $nodeWheel = if ($state['NODE_WHEEL']) { $state['NODE_WHEEL'] } else { '0' }
    if ($WithApps) {
        Write-Step 'Node.js for the browser apps'
        $nodeMajor = 0
        if (Test-Command 'node') { try { $nodeMajor = [int](((& node -v) -replace '^v', '') -split '\.')[0] } catch { } }
        if ($nodeMajor -ge 18) { Write-Ok "Node.js $(& node -v) found" }
        elseif (Test-Path -LiteralPath (Join-Path $toolBin "node$exeSuffix")) { Write-Ok "Node.js from nodejs-wheel: $(Join-Path $toolBin "node$exeSuffix")" }
        else {
            Write-Info "no Node.js >= 18: installing the nodejs-wheel uv tool (node, npm, npx in $toolBin; no admin, no UAC)"
            Invoke-Native -Description 'install nodejs-wheel' -Argv @($uv, 'tool', 'install', 'nodejs-wheel') | Out-Null
            $nodeWheel = '1'
        }
        Write-Info 'apps are not installed globally; each runs on demand (first launch downloads it):'
        foreach ($s in $AfNpmApps) { Write-Host "      npx -y $s   # `$env:ABSTRACTGATEWAY_URL='$baseUrl'" -ForegroundColor Gray }
    }

    if ($WithConsole -or $WithCodeCli) {
        Write-Step 'Terminal tools (crates.io)'
        $crates = @()
        if ($WithConsole) { $crates += $AfCrateConsole }
        if ($WithCodeCli) { $crates += $AfCrateCodeCli }
        foreach ($c in $crates) {
            $i = $c.LastIndexOf('@'); $name = $c.Substring(0, $i); $v = $c.Substring($i + 1)
            if (Test-Command 'cargo') { Invoke-Native -Description "cargo install $name" -Argv @('cargo', 'install', '--locked', $name, '--version', $v) | Out-Null }
            else { Write-Warn2 "cargo not found: install Rust from https://rustup.rs, then run: cargo install --locked $name --version $v" }
        }
    }

    $hasWinget = Test-Command 'winget'
    if ($WithOllama) {
        Write-Step 'Ollama (vendor installer, user scope)'
        if ((Test-Command 'ollama') -or (Get-Http 'http://127.0.0.1:11434/api/version' 2)) { Write-Ok 'Ollama already installed or reachable; skipped' }
        elseif ($hasWinget) {
            Invoke-Native -Description 'install Ollama' -Argv @('winget', 'install', '--id', 'Ollama.Ollama', '-e', '--scope', 'user', '--accept-package-agreements', '--accept-source-agreements') | Out-Null
        } else {
            Invoke-VendorScript -Description 'install Ollama' -Url 'https://ollama.com/install.ps1' | Out-Null
        }
    }
    if ($WithLmStudio) {
        Write-Step 'LM Studio (vendor installer, user scope)'
        $lms = Join-Path $homeDir '.lmstudio/bin/lms.exe'
        if ((Test-Command 'lms') -or (Test-Path -LiteralPath $lms) -or (Get-Http 'http://127.0.0.1:1234/v1/models' 2)) { Write-Ok 'LM Studio already installed or reachable; skipped' }
        elseif ($hasWinget) {
            Invoke-Native -Description 'install LM Studio' -Argv @('winget', 'install', '--id', 'ElementLabs.LMStudio', '-e', '--scope', 'user', '--accept-package-agreements', '--accept-source-agreements') | Out-Null
            Write-Info 'start LM Studio once, then enable its local server (port 1234)'
        } else {
            Invoke-VendorScript -Description 'install LM Studio (llmster)' -Url 'https://lmstudio.ai/install.ps1' | Out-Null
            Write-Info 'start its server with: lms daemon up; lms server start --port 1234 --bind 127.0.0.1'
        }
    }

    # --- 5. service / start ----------------------------------------------------------------------
    $env:ABSTRACTGATEWAY_DATA_DIR = $DataDir
    # Gateways before 0.3 (reachable with -Pin) refuse to start without an auth mode; user auth with a
    # bootstrapped admin is the loopback default from 0.3 on. Setting it is harmless there.
    $env:ABSTRACTGATEWAY_USER_AUTH = '1'
    $serviceOk = Test-GatewaySupports 'service'
    $mode = 'none'
    # $startCmd feeds only the Startup-folder shortcut of gateways WITHOUT `abstractgateway service`,
    # which predate the Network setting too: they keep --host/--port.
    $startCmd = "`$env:ABSTRACTGATEWAY_DATA_DIR='$DataDir'; `$env:ABSTRACTGATEWAY_USER_AUTH='1'; Start-Process -FilePath '$gw' -ArgumentList 'serve --host 127.0.0.1 --port $Port' -WindowStyle Hidden -RedirectStandardOutput '$gatewayLog' -RedirectStandardError '$gatewayErr'"

    if ($NoStart) {
        Write-Step 'Start'
        Write-Info '-NoStart: the gateway is installed but not started'
        $mode = if ($state['MODE']) { $state['MODE'] } else { 'none' }
    } elseif (-not $NoService -and ($serviceOk -or $script:DryRun)) {
        Write-Step 'Login service (abstractgateway service)'
        if ($script:DryRun -and -not $serviceOk) { Write-Info "(only when the installed gateway has 'abstractgateway service'; otherwise a Startup-folder shortcut)" }
        Stop-OurGateway
        if ($shortcut -and (Test-Path -LiteralPath $shortcut) -and -not $script:DryRun) { Remove-Item -LiteralPath $shortcut -Force }
        # No --host: the login item runs plain `serve` and the gateway's Network setting binds it;
        # 127.0.0.1 here would reset a "Local network" choice on every re-run.
        Invoke-Native -Description 'register the gateway service' -Argv @($gw, 'service', 'install', '--port', "$Port") | Out-Null
        $mode = 'service'
    } else {
        if (-not $NoService -and $shortcut) {
            Write-Step 'Start at login (Startup-folder shortcut, no admin)'
            Write-Warn2 "gateway $after has no 'abstractgateway service' command: using a Startup-folder shortcut"
            $psExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
            $lnkArgs = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command `"$($startCmd -replace '"', '\"')`""
            Write-Host "  `$ shortcut $shortcut -> powershell $lnkArgs" -ForegroundColor DarkGray
            $script:Twins.Add("(shortcut) $shortcut")
            if (-not $script:DryRun) {
                $shell = New-Object -ComObject WScript.Shell
                $lnk = $shell.CreateShortcut($shortcut)
                $lnk.TargetPath = $psExe
                $lnk.Arguments = $lnkArgs
                $lnk.WorkingDirectory = $DataDir
                $lnk.WindowStyle = 7
                $lnk.Description = 'AbstractGateway (AbstractFramework)'
                $lnk.Save()
                Write-Ok "created $shortcut"
            }
        }
        Write-Step 'Start in the background (hidden window)'
        if ($reuseRunning -and -not $changed -and (Get-OurPid)) {
            Write-Ok "already running (pid $(Get-OurPid)), unchanged"
        } else {
            Stop-OurGateway
            # Plain `serve` when the gateway has the Network setting (`abstractgateway network`):
            # flags on the command line would override it forever (a restart replays them).
            # Older gateways keep the pinned command line they need.
            $netSetting = $false
            if ($script:DryRun) {
                Write-Info "abstractgateway network set localhost --port $Port   (gateways with 'abstractgateway network', when no mode is stored yet; then plain 'serve')"
            } elseif ((Test-GatewaySupports 'network') -and (Set-NetworkSettingForStart)) {
                $netSetting = $true
            }
            $serveArgs = if ($netSetting) { @('serve') } else { @('serve', '--host', '127.0.0.1', '--port', "$Port") }
            $bgCmd = "`$env:ABSTRACTGATEWAY_DATA_DIR='$DataDir'; `$env:ABSTRACTGATEWAY_USER_AUTH='1'; Start-Process -FilePath '$gw' -ArgumentList '$($serveArgs -join ' ')' -WindowStyle Hidden -RedirectStandardOutput '$gatewayLog' -RedirectStandardError '$gatewayErr'"
            Write-Host "  `$ $bgCmd" -ForegroundColor DarkGray
            $script:Twins.Add($bgCmd)
            if (-not $script:DryRun) {
                $proc = Start-Process -FilePath $gw -ArgumentList $serveArgs `
                    -WindowStyle Hidden -RedirectStandardOutput $gatewayLog -RedirectStandardError $gatewayErr -PassThru
                Set-Content -LiteralPath $pidFile -Value $proc.Id
                Write-Ok "started (pid $($proc.Id)), log: $gatewayErr"
            }
        }
        $mode = 'background'
    }
    if (-not $script:DryRun) {
        @(
            "# written by AbstractFramework install.ps1 on $((Get-Date).ToUniversalTime().ToString('s'))Z",
            "PORT=$Port", "MODE=$mode", "PROFILE=$profileName", "NODE_WHEEL=$nodeWheel",
            "GATEWAY_SPEC=$gwSpec", "GATEWAY_VERSION=$after"
        ) | Set-Content -LiteralPath $stateFile -Encoding ASCII
    }

    # --- 6. health + console ---------------------------------------------------------------------
    $consoleUrl = "$baseUrl/console"
    if (-not $NoStart) {
        Write-Step 'Health check'
        $script:Twins.Add("irm $baseUrl/api/health")
        if ($script:DryRun) { Write-Info "would wait up to 60 s for $baseUrl/api/health" }
        else {
            $i = 0
            while (-not ((Get-Http "$baseUrl/api/health" 3) -match 'abstractgateway')) {
                $i++
                if ($mode -eq 'background' -and -not (Get-OurPid)) {
                    if (Test-Path -LiteralPath $gatewayErr) { Get-Content -LiteralPath $gatewayErr -Tail 30 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray } }
                    Stop-Install "the gateway exited during startup (log: $gatewayErr)"
                }
                if ($i -ge 60) { Stop-Install "no answer from $baseUrl/api/health after 60 s (log: $gatewayErr)" }
                Start-Sleep -Seconds 1
            }
            Write-Ok "gateway healthy at $baseUrl (${i}s)"
        }

        Write-Step 'Console sign-in'
        $claimed = $false
        if (-not $script:DryRun -and (Test-GatewaySupports 'claim-url')) {
            $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
            try { $out = (& $gwCfg claim-url --base-url $baseUrl 2>$null) -join "`n" } finally { $ErrorActionPreference = $old }
            $url = ([regex]::Matches($out, 'https?://\S+') | Select-Object -Last 1).Value
            if ($url) { $consoleUrl = $url; $claimed = $true; $script:Twins.Add("abstractgateway-config claim-url --base-url $baseUrl"); Write-Ok 'one-time sign-in link created (valid 10 minutes, this machine only)' }
            else { Write-Warn2 "'abstractgateway-config claim-url' is present but returned no URL; falling back to the admin token" }
        } elseif ($script:DryRun) { Write-Info "abstractgateway-config claim-url --base-url $baseUrl   (when supported)" }
        $tokenFile = Join-Path $DataDir 'auth\bootstrap-admin-token'
        if (-not $claimed) {
            Write-Info "sign in as 'admin' with the token in: $tokenFile"
            Write-Info "    Get-Content '$tokenFile'"
        }
        if ($NoOpen -or $script:DryRun -or -not $onWindows) { Write-Info "open: $consoleUrl" }
        else {
            try { Start-Process $consoleUrl; Write-Ok 'opened the console in your browser' } catch { Write-Info "open: $consoleUrl" }
        }
    }

    # --- summary -------------------------------------------------------------------------------------
    Write-Host ''
    if ($script:DryRun) { Write-Host 'Plan printed (-Print): nothing was changed.' -ForegroundColor White }
    else { Write-Host 'AbstractFramework is installed.' -ForegroundColor Green }
    Write-Host "  Console:    $baseUrl/console"
    Write-Host "  Gateway:    $gwSpec ($profileName profile)"
    Write-Host "  Data dir:   $DataDir"
    Write-Host "  Logs:       $logDir"
    Write-Host "  Mode:       $mode"
    Write-Host ''
    if ($mode -eq 'service') {
        Write-Host '  Status:     abstractgateway service status'
        Write-Host '  Stop:       abstractgateway service uninstall   (stops it and removes the login entry; data is kept)'
        Write-Host "  Start:      abstractgateway service install --port $Port"
    } else {
        Write-Host "  Stop:       Stop-Process -Id (Get-Content '$pidFile')"
        Write-Host '  Start:      re-run this installer (or sign out and in: the Startup shortcut starts it)'
    }
    Write-Host '  Upgrade:    re-run this installer (or: uv tool upgrade abstractgateway)'
    Write-Host "  Uninstall:  install.ps1 -Uninstall   (or: $(if ($mode -eq 'service') { 'abstractgateway service uninstall; ' })uv tool uninstall abstractgateway)"
    Write-Host '  Check:      uvx abstractframework doctor'
    Write-Host "  GGUF:       $ggufResult"
    if (-not $Full -and $profileName -eq 'gpu') { Write-Host "  $AfSkippedLine" }
    Write-Host '  Apps:       npx -y @abstractframework/flow   (also: code, observer, continuum, entity)'
    Write-Host "  Docs:       $AfDocs"
    if ($script:Twins.Count) {
        Write-Host ''
        Write-Host '  The same steps by hand:'
        foreach ($t in $script:Twins) { Write-Host "    $t" -ForegroundColor Gray }
    }
    if ($script:LogFile) { Write-Host ''; Write-Host "  Full log: $($script:LogFile)" -ForegroundColor DarkGray }
}

try {
    Main
} catch {
    $msg = "$_" -replace '^AFBOOT: ', ''
    Write-Host ''
    Write-Host "ERROR: $msg" -ForegroundColor Red
    if ("$_" -notlike 'AFBOOT:*') { Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray }
    # `exit` would close the window of someone who pasted `irm | iex`; only exit when run as a file.
    if ($script:RanAsFile) { exit 1 }
}

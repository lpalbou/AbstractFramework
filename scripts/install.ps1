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
         (prebuilt wheels only: no compiler / MSVC Build Tools needed), which also puts
         AbstractCore's and its voice/vision/music commands on PATH (-NoCoreCli: not)
      4. the terminal console (abstractgateway-console) and AbstractCode's terminal client
         (abstractcode), built with cargo when Rust is installed (-NoConsole, -NoCodeCli
         skip them), then the optional parts: Node.js (nodejs-wheel), Ollama, LM Studio
      5. start at login: asked when a person is at the console (Enter = yes, no answer
         within -AskWait seconds = the previous choice, or no on a first install; without
         a console it stays as it was, off on a first install, and the summary says how
         to turn it on); then `abstractgateway service install` (a Startup-folder
         shortcut for gateways without it) or a hidden background start
      6. waits for /api/health, writes the local gateway pointer
         (%USERPROFILE%\.abstractframework\gateway.json: the address only, never a token),
         then opens the console (one-time claim URL when supported); the browser apps
         open through the gateway at /apps/<app>/

    -Full also builds the compiled extra (stable-diffusion.cpp) and llama.cpp from source; it
    needs the MSVC Build Tools. Echo cancellation comes from its prebuilt wheel.

    The gpu profile picks PyTorch's CUDA build for the NVIDIA driver it finds (CUDA 13 for driver
    580+ and compute capability 7.5+, CUDA 12 for driver 525+, else the CPU build), shows the
    downloads as they happen, checks what really runs on the GPU at the end, and falls back to
    a working CPU install for any part that does not (root backlog 0988).

    Upgrade: run the same line again. It finds the existing install (bootstrap.env, the uv
    tool), says "AbstractFramework <old> found: upgrading to <new>" (or "already up to date"),
    keeps the profile, port, start at login, data dir and -NoConsole, -NoCodeCli, -NoCoreCli,
    -NoTray, -Full (-WithConsole, -WithCodeCli, -WithCoreCli, -WithTray, -NoFull turn them
    back), moves every library to the release's exact versions, stops a running gateway
    before files change (Windows keeps a running program's files locked) and starts it again,
    and lists what changed (old -> new).

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
    [switch]$WithConsole,   # the default now; kept for older command lines
    [switch]$NoConsole,
    [switch]$WithCodeCli,   # the default now; kept for older command lines
    [switch]$NoCodeCli,     # skip AbstractCode's terminal client (abstractcode)
    [switch]$WithCoreCli,   # the default now; kept for older command lines
    [switch]$NoCoreCli,     # do not put AbstractCore's (and voice/vision/music) commands on PATH
    [switch]$WithOllama,
    [switch]$WithLmStudio,
    [switch]$Full,
    [switch]$NoFull,      # turn off a -Full a previous run remembered
    [switch]$NoTray,
    [switch]$WithTray,    # turn the tray back on after a previous -NoTray
    [switch]$NoService,   # do not start at login (asks nothing)
    [switch]$NoStart,
    [switch]$NoOpen,
    [int]$AskWait = 25,   # seconds a timed question (start at login) waits for an answer (at most 25)
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
$AfGatewayPinDefault = '0.11.0'
# The AbstractFramework release these pins are, and its other Python packages in the gateway's
# environment, exact: passed to uv as constraints (same as install.sh; test_inventory.sh checks).
$AfFrameworkVersion = '0.9.0'
$AfPyMatrix = @('abstractcore==2.23.0', 'AbstractRuntime==0.8.3', 'abstractagent==0.3.17', 'abstractskill==0.3.0', 'AbstractMemory==0.3.0', 'abstractsemantics==0.0.5', 'abstractvoice==0.13.2', 'abstractvision==0.3.33', 'abstractmusic==0.1.15', 'abstract3d==0.3.2')
$AfPython = '3.12'
$AfNpmApps = @('@abstractframework/flow@0.7.0', '@abstractframework/code@0.10.0', '@abstractframework/observer@0.6.0', '@abstractframework/continuum@0.6.0', '@abstractframework/entity@0.6.0')
$AfCrateConsole = 'abstractgateway-console@0.14.0'
$AfCrateCodeCli = 'abstractcode@0.8.0'
# Where the terminal console and AbstractCode's terminal client go (cargo --root), like install.sh:
# the parent of the uv tool bin folder, so they land next to abstractgateway.exe (the folder the
# gateway's Apps page also updates abstractcode in); cargo's own root when that folder is not
# named ...\bin. .Code is the ONE place that decides where abstractcode goes; the build, the
# version check, the summary and the uninstall all follow it.
function Get-CrateRoots([string]$ToolBin) {
    $root = if ($ToolBin -and (Split-Path -Leaf $ToolBin) -eq 'bin') { Split-Path -Parent $ToolBin } else { '' }
    return @{ Console = $root; Code = $root }
}
# The user commands of the gateway's own environment exposed next to abstractgateway and
# abstractgateway-config (uv tool install --with-executables-from; -NoCoreCli leaves them out),
# with every name each package declares: uv exposes all of a package's executables or none and
# refuses the WHOLE install when one already exists, so a package whose name another program has
# is left out. Same list as install.sh (tests/test_install_profiles.py checks).
$AfCliExecutables = [ordered]@{
    'abstractcore' = @('abstractcore', 'abstractcore-config', 'abstractcore-chat', 'abstractcore-endpoint', 'summarizer', 'abstractcore-summarizer', 'extractor', 'abstractcore-extractor', 'judge', 'abstractcore-judge', 'intent', 'abstractcore-intent', 'deepsearch', 'abstractcore-deepsearch')
    'abstractvoice' = @('abstractvoice', 'abstractvoice-prefetch')
    'abstractvision' = @('abstractvision')
    'abstractmusic' = @('abstractmusic')
}
$AfCliAbout = @{
    'abstractcore' = 'AbstractCore: --config, --status, models, engines, serve; also abstractcore-chat (a chat REPL), abstractcore-endpoint and its apps summarizer, extractor, judge, intent, deepsearch'
    'abstractvoice' = 'voice in the terminal: a spoken chat, web, tts; abstractvoice-prefetch downloads voice models'
    'abstractvision' = 'images in the terminal: cli (generate), download, provider-models'
    'abstractmusic' = 'music in the terminal: t2m (text to music)'
}
$AfDocs = 'https://github.com/lpalbou/AbstractFramework/blob/main/docs/install.md'
$AfScriptUrl = 'https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1'

# ---------------------------------------------------------------------------
# Prebuilt wheels only: by default no compiler (MSVC Build Tools) is needed.
# `uv tool install` gets an overrides file (an override whose marker is never true
# drops the package) and --no-build-package for the same packages, so a gap fails
# fast instead of starting a compiler: webrtcvad is always dropped (webrtcvad-wheels
# comes in through --with), vllm is Linux-only, and the compiled extra
# (stable-diffusion-cpp-python; optional, imported lazily) is dropped unless -Full, which
# builds it from source and so needs a compiler. aec-audio-processing (echo cancellation)
# is not compiled here: it has Windows wheels for cp311-cp313 and this installer uses
# Python 3.12 (install.sh keeps it in its compiled list: no macOS/Linux wheels).
# llama-cpp-python (llama.cpp GGUF, every profile) comes from upstream's prebuilt
# wheel on x64 Windows (light: the CPU build; gpu: the stack's CUDA build, else Vulkan,
# else CPU, see below): --find-links on the package page of abetlen's wheel
# index, pinned through --constraints uv-constraints.txt, --no-build-package so the
# sdist is never built. No wheel for Windows on ARM; there, and whenever the wheel
# install fails, it is dropped and the summary says so. -Full builds it from source.
# Same lists as install.sh, less aec-audio-processing (tests/test_install_profiles.py checks).
# ---------------------------------------------------------------------------
$AfWithWheels = 'webrtcvad-wheels>=2.0.14'
# Local voice on every profile: Supertonic text-to-speech (ONNX Runtime) and Whisper speech-to-text
# (faster-whisper: CTranslate2). Windows ARM64 gets Supertonic only: CTranslate2 has no ARM64 wheel.
$AfWithVoice = 'abstractvoice[supertonic,stt]'
$AfWithVoiceArm64 = 'abstractvoice[supertonic]'
$AfCompiledExtras = @('stable-diffusion-cpp-python')
$AfSkippedLine = 'Skipped compiled extras (stable-diffusion.cpp): re-run with -Full after installing a C compiler.'
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
# The packages whose index pages uv revalidates on every install (root backlog 0987): uv caches
# PyPI's simple pages as PyPI's headers allow (10 minutes), so right after a release
# `uv tool install 'abstractgateway==<new pin>'` failed with "no version of abstractgateway==<pin>"
# until `uv cache clean abstractgateway`. --refresh-package makes uv ask the index again for these
# names only (a conditional request each; downloaded wheels stay cached): the gateway and the release
# matrix, the versions this installer pins. Same list as install.sh (tests/test_install_profiles.py).
function Get-RefreshPackages {
    return @('abstractgateway') + @($AfPyMatrix | ForEach-Object { ($_ -split '==', 2)[0] })
}
# PyPI index lag (root backlog 0987 item 28; same rule as install.sh's uv_index_lag, see its comment).
# Right after a release some of PyPI's mirrors still list no file for the new version for a few
# minutes, even with --refresh-package. Lag never drops a feature (voice, llama.cpp, PyTorch's CUDA
# build): the SAME install is run again after each of these delays (about 10 minutes in all), then it
# stops with the cause. A failure is lag only when uv exits 1, its output carries uv's resolution
# failure header "No solution found when resolving dependencies", and it names a package this run
# pinned exactly (-IndexPins) in uv's empty-version form "there is no version of <name>[<extras>]==<pin>".
$script:IndexRetryDelays = @(15, 30, 60, 120, 120, 120, 120)
# The voice requirement with abstractvoice's matrix pin on a release install (the constraint already
# forces it; the explicit pin makes uv report a missing abstractvoice in the exact-pin form).
function Get-VoiceRequirement([string]$Spec, [bool]$IsRelease) {
    if (-not $IsRelease -or -not $Spec -or $Spec.Contains('==') -or $Spec -notmatch '^abstractvoice(\[|$)') { return $Spec }
    foreach ($c in $AfPyMatrix) { if ($c -like 'abstractvoice==*') { return "$Spec==$(($c -split '==', 2)[1])" } }
    return $Spec
}
# The pinned "name==version" that is not on the index yet, followed by " 404" when the index lists it
# but its file is not served yet, or '' for any other failure (same rule as install.sh's uv_index_lag).
# Exit 1: uv's resolver reports the pin missing (above). Exit 1 or 2: uv's download of the pin's own
# file answered HTTP 404 ("Failed to fetch: `.../<name>-<pin>-py3-none-any.whl`" ... "HTTP status
# client error (404").
function Find-IndexLag([string]$Text, [string[]]$Pins, [int]$Code = 1) {
    if ($Code -ne 1 -and $Code -ne 2) { return '' }
    $t = $Text -replace "$([char]27)\[[0-9;]*m", '' -replace [string][char]0x2502, ' '
    $t = ($t -replace '\s+', ' ').ToLowerInvariant()
    $res = ($Code -eq 1) -and $t.Contains('no solution found when resolving dependencies')
    $f404 = $t -match 'failed to fetch.*http status client error \(404'
    if (-not $res -and -not $f404) { return '' }
    foreach ($p in $Pins) {
        $nv = $p -split '==', 2
        $n = $nv[0].ToLowerInvariant()
        $v = [regex]::Escape($nv[1].ToLowerInvariant())
        if ($res -and $t -match ('there is no version of ' + [regex]::Escape($n) + '(\[[a-z0-9,._-]*\])?==' + $v + '([^0-9a-z.+!-]|$)')) { return $p }
        if ($f404 -and $t -match ('failed to fetch: `[^`]*/' + [regex]::Escape(($n -replace '[.-]', '_')) + '-' + $v + '(-|\.tar\.gz)')) { return "$p 404" }
    }
    return ''
}
# Transient network failures (operator requirement 2026-09-30; same rule and strings as install.sh,
# see its comment above AF_UV_DETERMINISTIC): the SAME install runs again on $script:IndexRetryDelays,
# then stops with the cause and the command to run again; never the voice/llama.cpp fallback. uv
# changes a tool environment only after every download succeeded (tests/test_uv_tool_install_atomicity.py).
# Strings as uv 0.11.14 and cargo 1.98 print them, matched lower-cased with lines joined.
$script:UvDeterministic = 'no solution found when resolving dependencies|the build backend returned an error|failed to build|hash mismatch for|computed crc32 value did not match|checksum|the wheel is invalid|is not a valid wheel filename|http status client error \(4([13-9][0-9]|0[0-79]|2[0-8])'
$script:UvTransient = 'http status server error \(5|http status client error \((429|408)|request failed after [0-9]+ retr|due to network timeout|error sending request for url|connection reset|connection refused|connection closed before message completed|broken pipe|operation timed out|connection timed out|dns error|failed to lookup address information|tcp connect error|network unreachable|host unreachable|error decoding response body|request or response body error|unexpected end of file|unexpected eof'
$script:CargoLag = 'could not find `[^`]*` in registry|failed to select a version for the requirement|no matching package named'
$script:CargoDeterministic = 'could not compile|error\[e[0-9]|linker `'
$script:CargoTransient = 'spurious network error|failed to get successful http response from .*got (5[0-9][0-9]|429)|couldn.t resolve host|couldn.t connect to server|timeout was reached|operation timed out|ssl connect error|empty reply from server|failure when receiving data|transferred a partial file|failed to download from|download of [^ ]* failed|connection reset|early eof'
function ConvertTo-RetryText([string]$Text) {
    $t = $Text -replace "$([char]27)\[[0-9;]*m", '' -replace [string][char]0x2502, ' ' -replace "$([char]0x251C)$([char]0x2500)$([char]0x25B6)", ' ' -replace "$([char]0x2570)$([char]0x2500)$([char]0x25B6)", ' '
    return ($t -replace '\s+', ' ').ToLowerInvariant()
}
# The first line of $Text matching $Pattern, as printed (box drawing, "Caused by:", "error:" removed).
function Get-RetryCause([string]$Text, [string]$Pattern) {
    foreach ($l in ($Text -split "`r?`n")) {
        $c = ($l -replace "$([char]27)\[[0-9;]*m", '')
        if ($c -match "(?i)$Pattern") {
            $c = ($c -replace "^[\s$([char]0x2502)$([char]0x251C)$([char]0x2570)$([char]0x2500)$([char]0x25B6)$([char]0x00D7)]*", '') -replace '^(?i)caused by: *', '' -replace '^(?i)(error|warning): *', ''
            if ($c.Length -gt 240) { $c = $c.Substring(0, 240) }
            return $c
        }
    }
    return ''
}
# Find-Transient TEXT CODE: the cause line when uv's failure (exit 1 or 2) is a transient network failure.
function Find-Transient([string]$Text, [int]$Code = 1) {
    if ($Code -ne 1 -and $Code -ne 2) { return '' }
    $t = ConvertTo-RetryText $Text
    if ($t -match $script:UvDeterministic) { return '' }
    if ($t -match $script:UvTransient) { return (Get-RetryCause $Text $script:UvTransient) }
    if ($t -match 'failed to download|failed to fetch') { return (Get-RetryCause $Text 'failed to download|failed to fetch') }
    return ''
}
# Find-CargoRetry TEXT: 'lag <cause>' (crates.io's index has not listed it yet) or 'transient <cause>'.
function Find-CargoRetry([string]$Text) {
    $t = ConvertTo-RetryText $Text
    if ($t -match $script:CargoDeterministic) { return '' }
    if ($t -match $script:CargoLag) { return ('lag ' + (Get-RetryCause $Text $script:CargoLag)) }
    if ($t -match $script:CargoTransient) {
        $c = (Get-RetryCause $Text $script:CargoTransient) -replace '^.*spurious network error \([^)]*\): *', ''
        return ('transient ' + $c)
    }
    return ''
}
# The log's text after byte $Offset (one command's output).
function Read-LogFrom([string]$Path, [long]$Offset) {
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try {
        [void]$fs.Seek([Math]::Min($Offset, $fs.Length), [System.IO.SeekOrigin]::Begin)
        return (New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8)).ReadToEnd()
    } finally { $fs.Close() }
}

# ---------------------------------------------------------------------------
# This install's gateway, whoever started it (root backlog 0987 item 20; same rule as install.sh).
# A gateway started by hand has no gateway.pid and is not the login item, yet it serves this
# install's data dir: a re-run must replace it on the same port, never move to the next port and
# start a second gateway on the same data. Only typed signals decide, and all must agree: the pid
# listening on the port (Get-NetTCPConnection) and /api/health there is a gateway's; that process runs
# `abstractgateway serve` (its command line); it serves THIS data dir. A --data-dir on its command
# line decides alone (another data dir, or a relative one this installer cannot resolve, makes it
# foreign whatever the serve record says); without one, the serve record <data dir>\run\gateway-serve.json
# must name its pid and this data dir, and the process must have started before the record was
# written (a reused pid started later). When the listener cannot be named, the serve record must name
# this port too.
# ---------------------------------------------------------------------------
function Read-ServeRecord([string]$DataDir) {
    $rec = Join-Path $DataDir 'run\gateway-serve.json'
    if (-not (Test-Path -LiteralPath $rec -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $rec -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop) } catch { return $null }
}
function Get-PortListenerPid([int]$Port) {
    try {
        $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($c -and $c.OwningProcess) { return [int]$c.OwningProcess }
    } catch { }
    return 0
}
function Get-ProcessCommandLine([int]$ProcessId) {
    try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { }
    try { return [string](Get-Process -Id $ProcessId -ErrorAction Stop).CommandLine } catch { return '' }
}
# The parent of a process: uv's abstractgateway.exe is a launcher whose child python.exe is the listener.
function Get-ParentProcessId([int]$ProcessId) {
    try { return [int](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).ParentProcessId } catch { return 0 }
}
function Get-ProcessStartUtc([int]$ProcessId) {
    try { return (Get-Process -Id $ProcessId -ErrorAction Stop).StartTime.ToUniversalTime() } catch { return $null }
}
function Test-ProcessAlive([int]$ProcessId) { return [bool]($ProcessId -and (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) }
# The user a process runs as ('' when it cannot be told): Windows asks Win32_Process.GetOwner, elsewhere ps.
function Get-ProcessOwner([int]$ProcessId) {
    try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
        if ($proc) { $o = Invoke-CimMethod -InputObject $proc -MethodName GetOwner -ErrorAction Stop; if ($o.User) { return [string]$o.User } }
    } catch { }
    try { return ([string](& ps -o user= -p $ProcessId 2>$null)).Trim() } catch { return '' }
}
# Test-SameUser: the process runs as the user running this installer (another user's program is never ours).
function Test-SameUser([int]$ProcessId) {
    $owner = Get-ProcessOwner $ProcessId
    return [bool]($owner -and $owner -ieq [Environment]::UserName)
}
# Test-GatewayCommandLine: the command line runs abstractgateway's `serve`.
function Test-GatewayCommandLine([string]$CommandLine) {
    return ($CommandLine -match '(?i)abstractgateway' -and $CommandLine -match '(?i)(^|[\s"])serve(\s|"|$)')
}
# Test-OurBackgroundListener: the listener is the installer's background gateway (gateway.pid), or
# its child (the launcher's python.exe). No listener named: the gateway.pid process counts.
function Test-OurBackgroundListener([int]$Listener, [int]$OurPid) {
    if (-not $OurPid) { return $false }
    if (-not $Listener -or $Listener -eq $OurPid) { return $true }
    return ((Get-ParentProcessId $Listener) -eq $OurPid)
}
# Get-DeclaredDataDir: the --data-dir on a command line (quoted or not, or --data-dir=), '' when none.
function Get-DeclaredDataDir([string]$CommandLine) {
    $q = [regex]::Match(" $CommandLine", '\s"--data-dir=([^"]*)"')
    if ($q.Success) { return $q.Groups[1].Value }
    $m = [regex]::Match(" $CommandLine", '\s--data-dir(?:=|\s+)(?:"([^"]*)"|([^\s"]+))')
    if (-not $m.Success) { return '' }
    if ($m.Groups[1].Success) { return $m.Groups[1].Value }
    return $m.Groups[2].Value
}
function Test-CommandLineDataDir([string]$CommandLine, [string]$DataDir) {
    $d = Get-DeclaredDataDir $CommandLine
    if (-not $d -or -not [IO.Path]::IsPathRooted($d)) { return $false }
    # Windows: \foo is relative to the current drive of that process, which this installer cannot know.
    if ((($PSVersionTable.PSEdition -eq 'Desktop') -or $IsWindows) -and $d -notmatch '^([A-Za-z]:[\\/]|\\\\)') { return $false }
    return ((Resolve-DirPath $d) -eq (Resolve-DirPath $DataDir))
}
# Test-OwnGatewayPid: process $GwPid, listening on $Port, is this install's gateway.
function Test-OwnGatewayPid([int]$GwPid, [int]$Port, [string]$DataDir, $Record, [bool]$ListenerKnown) {
    if (-not $GwPid -or -not (Test-ProcessAlive $GwPid)) { return $false }
    if (-not ((Get-Http "http://127.0.0.1:$Port/api/health") -match 'abstractgateway')) { return $false }
    if (-not (Test-SameUser $GwPid)) { return $false }
    $cmd = Get-ProcessCommandLine $GwPid
    if (-not (Test-GatewayCommandLine $cmd)) { return $false }
    if (Get-DeclaredDataDir $cmd) { return (Test-CommandLineDataDir $cmd $DataDir) }
    if (-not $Record -or "$($Record.pid)" -ne "$GwPid" -or -not $Record.data_dir) { return $false }
    if (-not $ListenerKnown -and "$($Record.port)" -ne "$Port") { return $false }
    if ((Resolve-DirPath ([string]$Record.data_dir)) -ne (Resolve-DirPath $DataDir)) { return $false }
    $started = Get-ProcessStartUtc $GwPid
    try { $written = [DateTime]::Parse([string]$Record.started_at, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal -bor [Globalization.DateTimeStyles]::AssumeUniversal) } catch { $written = $null }
    if ($null -eq $started -or $null -eq $written) { return $false }
    return ($started -le $written.AddSeconds(2))
}
# Test-RecordNamesThisGateway: the serve record's pid is still the gateway that wrote it: a live
# `abstractgateway serve` process that started before the record was written and declares no other
# data dir (a stale record may name a reused pid).
function Test-RecordNamesThisGateway($Record, [string]$DataDir) {
    if (-not $Record -or -not $Record.pid) { return $false }
    $rp = [int]$Record.pid
    if (-not (Test-ProcessAlive $rp) -or -not (Test-SameUser $rp)) { return $false }
    $cmd = Get-ProcessCommandLine $rp
    if (-not (Test-GatewayCommandLine $cmd)) { return $false }
    if ((Get-DeclaredDataDir $cmd) -and -not (Test-CommandLineDataDir $cmd $DataDir)) { return $false }
    $started = Get-ProcessStartUtc $rp
    try { $written = [DateTime]::Parse([string]$Record.started_at, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal -bor [Globalization.DateTimeStyles]::AssumeUniversal) } catch { $written = $null }
    return ($null -ne $started -and $null -ne $written -and $started -le $written.AddSeconds(2))
}
# Test-PidFileGateway: gateway.pid names process $ProcessId and it is this install's background gateway:
# a live process of this user running `abstractgateway serve` (uv's abstractgateway.exe launcher), whose
# declared --data-dir (if any) is this data dir, and that started before gateway.pid was written (a pid
# reused after that gateway exited started later). A pid file naming anything else never gets
# Stop-Process.
function Test-PidFileGateway([int]$ProcessId, [string]$PidFile, [string]$DataDir) {
    if (-not $ProcessId -or -not (Test-Path -LiteralPath $PidFile -PathType Leaf)) { return $false }
    $named = 0; try { $named = [int]((Get-Content -LiteralPath $PidFile -ErrorAction Stop | Select-Object -First 1) -replace '[^0-9]', '') } catch { $named = 0 }
    if ($named -ne $ProcessId) { return $false }
    if (-not (Test-ProcessAlive $ProcessId) -or -not (Test-SameUser $ProcessId)) { return $false }
    $cmd = Get-ProcessCommandLine $ProcessId
    if (-not (Test-GatewayCommandLine $cmd)) { return $false }
    if ((Get-DeclaredDataDir $cmd) -and -not (Test-CommandLineDataDir $cmd $DataDir)) { return $false }
    # Always: the process started before gateway.pid was written (the installer writes it right after
    # starting its gateway); a pid reused later started later, even when its command line names this
    # data dir.
    $started = Get-ProcessStartUtc $ProcessId
    try { $written = (Get-Item -LiteralPath $PidFile -ErrorAction Stop).LastWriteTimeUtc } catch { $written = $null }
    return ($null -ne $started -and $null -ne $written -and $started -le $written.AddSeconds(2))
}
# Test-GatewayPidStillOurs: checked right before Stop-Process: $P is still the gateway it was taken for
# (this install's gateway started by hand on $Port, its background gateway named by gateway.pid, or the
# gateway the serve record names).
function Test-GatewayPidStillOurs([int]$P, [string]$PidFile, [string]$DataDir, [int]$Port, [int]$HandPid) {
    if ($HandPid -and $P -eq $HandPid) { return ((Find-OwnGateway $Port $DataDir) -eq $P) }
    if (Test-PidFileGateway $P $PidFile $DataDir) { return $true }
    $record = Read-ServeRecord $DataDir
    return [bool]($record -and "$($record.pid)" -eq "$P" -and (Test-RecordNamesThisGateway $record $DataDir))
}
# Find-OwnGateway: the pid of the gateway listening on $Port when it is this install's, else 0.
function Find-OwnGateway([int]$Port, [string]$DataDir) {
    $record = Read-ServeRecord $DataDir
    $gwPid = Get-PortListenerPid $Port
    $known = [bool]$gwPid
    if (-not $known) { if ($record) { $gwPid = [int]$record.pid } else { return 0 } }
    if (Test-OwnGatewayPid $gwPid $Port $DataDir $record $known) { return $gwPid }
    return 0
}

# ---------------------------------------------------------------------------
# The gpu setting on Windows + NVIDIA (root backlog 0988). PyPI's Windows torch is a CPU build;
# the CUDA builds live on download.pytorch.org. The stack follows the NVIDIA driver:
#   driver >= 580 and compute capability >= 7.5 -> CUDA 13: torch cu130, llama.cpp cu130
#   driver >= 525                               -> CUDA 12: torch cu126, llama.cpp cu125
#   anything else (no NVIDIA, older driver)     -> PyTorch's CPU build, llama.cpp vulkan, else cpu
# `uv tool install --torch-backend <cuXXX>` routes only the PyTorch packages to that index (uv
# 0.11.14 honours it for tool installs; uv prints "experimental"). An older uv without the option
# gets the index itself (--index + --index-strategy unsafe-best-match) and exact +cuXXX pins.
# llama.cpp's Windows CUDA wheels load cuBLAS/cudart from torch\lib (AbstractCore adds that folder
# before importing llama_cpp); every llama.cpp build is kept only when it loads in the gateway's
# environment (GPU builds: when llama.cpp reports GPU offload), else the next one is tried:
# CUDA -> vulkan -> cpu -> none. Nothing optional ever fails the install.
# ---------------------------------------------------------------------------
$AfTorchIndex = 'https://download.pytorch.org/whl'
# PyTorch versions of the release (uv resolves them; the explicit-index fallback pins them +cuXXX).
$AfTorchPins = [ordered]@{ 'torch' = '2.14.0'; 'torchvision' = '0.29.0'; 'torchaudio' = '2.11.0' }
$AfLlamaSizes = @{ 'cu130' = 'about 220 MB'; 'cu125' = 'about 480 MB'; 'vulkan' = 'about 45 MB'; 'cpu' = 'about 7 MB' }
$script:HeartbeatSeconds = 15

# What nvidia-smi says: Ok, Driver, DriverMajor, Cc (the lowest compute capability, or $null when
# the driver cannot report it), Name, Error. A missing nvidia-smi or any error: no NVIDIA GPU.
function Get-NvidiaInfo([string]$Smi = 'nvidia-smi') {
    $info = @{ Ok = $false; Driver = ''; DriverMajor = 0; Cc = $null; Name = ''; Error = '' }
    if (-not (Get-Command $Smi -ErrorAction SilentlyContinue)) { $info.Error = 'nvidia-smi not found'; return $info }
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $Smi '--query-gpu=driver_version,compute_cap,name' '--format=csv,noheader' 2>&1 | ForEach-Object { "$_" })
        $code = $LASTEXITCODE
        $withCc = $true
        if ($code -ne 0) {
            # Drivers too old to report compute_cap: ask for the driver alone.
            $lines = @(& $Smi '--query-gpu=driver_version,name' '--format=csv,noheader' 2>&1 | ForEach-Object { "$_" })
            $code = $LASTEXITCODE; $withCc = $false
        }
    } catch { $lines = @("$_"); $code = 1 } finally { $ErrorActionPreference = $old }
    if ($code -ne 0) {
        $first = ($lines | Where-Object { $_.Trim() } | Select-Object -First 1)
        $info.Error = "nvidia-smi failed: $(if ($first) { $first.Trim() } else { "exit $code" })"
        return $info
    }
    $inv = [Globalization.CultureInfo]::InvariantCulture
    foreach ($l in $lines) {
        if (-not $l.Trim()) { continue }
        $parts = if ($withCc) { $l.Split(',', 3) } else { $l.Split(',', 2) }
        $drv = $parts[0].Trim()
        $major = 0
        if (-not [int]::TryParse(($drv.Split('.')[0]), [ref]$major)) { continue }
        if (-not $info.Driver) { $info.Driver = $drv; $info.DriverMajor = $major }
        if ($withCc -and $parts.Count -ge 2) {
            $cc = 0.0
            if ([double]::TryParse($parts[1].Trim(), [Globalization.NumberStyles]::Float, $inv, [ref]$cc)) {
                if ($null -eq $info.Cc -or $cc -lt $info.Cc) { $info.Cc = $cc }
            }
        }
        $nameAt = if ($withCc) { 2 } else { 1 }
        if (-not $info.Name -and $parts.Count -gt $nameAt) { $info.Name = $parts[$nameAt].Trim() }
    }
    if (-not $info.Driver) { $info.Error = "nvidia-smi gave no driver version: $(($lines -join ' ').Trim())"; return $info }
    $info.Ok = $true
    return $info
}

# The stack for the gpu setting: Name (cu130 | cu126 | cpu), Torch (the PyTorch index tag, '' for
# PyPI's CPU build), Llama (llama.cpp wheel folders to try, in order), Label, TorchSize, Why.
function Select-GpuStack($Info) {
    $gpu = if ($Info.Name) { "$($Info.Name), " } else { 'NVIDIA GPU, ' }
    $ccText = if ($null -ne $Info.Cc) { $Info.Cc.ToString('0.0', [Globalization.CultureInfo]::InvariantCulture) } else { 'not reported' }
    if (-not $Info.Ok) {
        return @{ Name = 'cpu'; Torch = ''; Llama = @('vulkan', 'cpu'); Label = 'CPU'; TorchSize = 'about 0.3 GB'
            Why = "no working NVIDIA GPU ($($Info.Error)): PyTorch's CPU build; llama.cpp tries its Vulkan build, then its CPU build" }
    }
    if ($Info.DriverMajor -ge 580 -and $null -ne $Info.Cc -and $Info.Cc -ge 7.5) {
        return @{ Name = 'cu130'; Torch = 'cu130'; Llama = @('cu130', 'vulkan', 'cpu'); Label = 'CUDA 13'; TorchSize = 'about 1.9 GB'
            Why = "${gpu}driver $($Info.Driver) (580 or newer) and compute capability $ccText (7.5 or newer)" }
    }
    if ($Info.DriverMajor -ge 525) {
        $short = if ($Info.DriverMajor -lt 580) { "driver $($Info.Driver) is older than 580" } else { "compute capability $ccText is below 7.5" }
        return @{ Name = 'cu126'; Torch = 'cu126'; Llama = @('cu125', 'vulkan', 'cpu'); Label = 'CUDA 12'; TorchSize = 'about 2.5 GB'
            Why = "${gpu}driver $($Info.Driver) (525 or newer); not CUDA 13: $short" }
    }
    return @{ Name = 'cpu'; Torch = ''; Llama = @('vulkan', 'cpu'); Label = 'CPU'; TorchSize = 'about 0.3 GB'
        Why = "${gpu}driver $($Info.Driver) is older than 525 (CUDA 12 needs 525 or newer): PyTorch's CPU build; update the NVIDIA driver and run the installer again for the GPU" }
}

# Whether PyTorch's packages must be reinstalled: an existing install (not a first install) whose
# recorded stack (TORCH= in bootstrap.env, '' = PyPI's build) differs from this run's, for example
# CPU -> CUDA 13 after a driver update. uv keeps an installed torch that satisfies the pins, so
# without --reinstall-package the old build would stay.
function Test-TorchReinstall([string]$Action, $State, [string]$TorchTag) {
    if ($Action -eq 'install') { return $false }
    return ("$($State['TORCH'])" -ne $TorchTag)
}

# uv arguments and constraints that select PyTorch's build for a stack ($Torch '' = PyPI's build).
function Get-TorchSelection([string]$Torch, [bool]$UvHasTorchBackend) {
    if (-not $Torch) { return @{ Args = @(); Constraints = @() } }
    if ($UvHasTorchBackend) { return @{ Args = @('--torch-backend', $Torch); Constraints = @() } }
    $pins = @(); foreach ($k in $AfTorchPins.Keys) { $pins += "$k==$($AfTorchPins[$k])+$Torch" }
    return @{ Args = @('--index', "$AfTorchIndex/$Torch", '--index-strategy', 'unsafe-best-match'); Constraints = $pins }
}

# One argument, quoted the way Windows (and .NET's ProcessStartInfo.Arguments) splits a command line.
function ConvertTo-WinArg([string]$Value) {
    if ($Value -ne '' -and $Value -notmatch '[\s"]') { return $Value }
    $out = New-Object System.Text.StringBuilder
    [void]$out.Append('"')
    $bs = 0
    foreach ($ch in $Value.ToCharArray()) {
        if ($ch -eq '\') { $bs++; continue }
        if ($ch -eq '"') { [void]$out.Append(('\' * (2 * $bs + 1)) + '"'); $bs = 0; continue }
        [void]$out.Append(('\' * $bs) + $ch); $bs = 0
    }
    [void]$out.Append(('\' * (2 * $bs)) + '"')
    return $out.ToString()
}

# Run a program and show its output as it comes (uv's progress lines), write every line to the
# log, and print a heartbeat -- elapsed time and the last Downloading/Building/Installed line --
# whenever nothing was printed for $script:HeartbeatSeconds, so a multi-GB download never looks
# frozen. Package lists (" + name==version") go to the log only and are counted. Returns the exit code.
function Invoke-LiveProcess([string]$Exe, [string[]]$Arguments, [string]$Log) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = (($Arguments | ForEach-Object { ConvertTo-WinArg $_ }) -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.WorkingDirectory = (Get-Location).ProviderPath
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $writer = $null
    if ($Log) { $writer = New-Object System.IO.StreamWriter($Log, $true, (New-Object System.Text.UTF8Encoding($false))) }
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        $start = Get-Date; $lastShown = $start; $lastKey = ''; $listed = 0
        $readers = @{ out = $proc.StandardOutput; err = $proc.StandardError }
        $tasks = @{ out = $proc.StandardOutput.ReadLineAsync(); err = $proc.StandardError.ReadLineAsync() }
        while ($tasks.Count) {
            $got = $false
            foreach ($k in @($tasks.Keys)) {
                $t = $tasks[$k]
                if (-not $t.IsCompleted) { continue }
                $line = $t.Result
                if ($null -eq $line) { $tasks.Remove($k); continue }
                $tasks[$k] = $readers[$k].ReadLineAsync()
                $got = $true
                if ($writer) { $writer.WriteLine($line); $writer.Flush() }
                if ($line -match '^\s*[-+~] \S') { $listed++; continue }
                if (-not $line.Trim()) { continue }
                if ($line -match '(Downloading|Downloaded|Building|Built|Prepared|Installed|Uninstalled|Resolved|Updated)') { $lastKey = $line.Trim() }
                Write-Host "    | $($line.TrimEnd())" -ForegroundColor DarkGray
                $lastShown = Get-Date
            }
            if (-not $got) {
                $now = Get-Date
                if (($now - $lastShown).TotalSeconds -ge $script:HeartbeatSeconds) {
                    $el = $now - $start
                    $elText = if ($el.TotalMinutes -ge 1) { '{0}m {1:00}s' -f [int][Math]::Floor($el.TotalMinutes), $el.Seconds } else { '{0}s' -f [int]$el.TotalSeconds }
                    Write-Host "    ... still working ($elText elapsed$(if ($lastKey) { "; last: $lastKey" }))" -ForegroundColor DarkGray
                    $lastShown = $now
                }
                Start-Sleep -Milliseconds 200
            }
        }
        $proc.WaitForExit()
        if ($listed) { Write-Host "    | ($listed package lines: see the log)" -ForegroundColor DarkGray }
        return $proc.ExitCode
    } finally {
        if ($writer) { $writer.Close() }
    }
}

# The llama.cpp check AbstractCore's own load path makes, in a fresh process of the gateway's
# environment (no torch import, which would mask missing DLLs): its Windows DLL preparation when
# this AbstractCore has it, import, backend init, GPU offload. One JSON line "AFSMOKE {...}".
$AfLlamaSmoke = @'
import json
r = {"import": False, "offload": False, "error": "", "prep": None}
try:
    try:
        from abstractcore.utils.windows_dll import prepare_llama_cpp_import
        r["prep"] = prepare_llama_cpp_import()
    except ImportError:
        r["prep"] = None
    import llama_cpp
    r["import"] = True
    r["version"] = getattr(llama_cpp, "__version__", "")
    init = getattr(llama_cpp, "llama_backend_init", None)
    if callable(init):
        init()
    r["offload"] = bool(llama_cpp.llama_supports_gpu_offload())
except BaseException as e:
    r["error"] = "%s: %s" % (type(e).__name__, e)
print("AFSMOKE " + json.dumps(r))
'@
$AfTorchSmoke = @'
import json
r = {"import": False, "cuda": False, "error": ""}
try:
    import torch
    r.update({"import": True, "version": torch.__version__, "cuda_build": torch.version.cuda})
    r["cuda"] = bool(torch.cuda.is_available())
    if r["cuda"]:
        r["device"] = torch.cuda.get_device_name(0)
except BaseException as e:
    r["error"] = "%s: %s" % (type(e).__name__, e)
print("AFSMOKE " + json.dumps(r))
'@
$AfWhisperSmoke = @'
import json, importlib.util
r = {"device": "", "error": "", "cublas_guard": False}
try:
    r["cublas_guard"] = importlib.util.find_spec("abstractvoice.compute.windows_cuda") is not None
    from abstractvoice.compute import best_faster_whisper_device
    r["device"] = best_faster_whisper_device()
except BaseException as e:
    r["error"] = "%s: %s" % (type(e).__name__, e)
print("AFSMOKE " + json.dumps(r))
'@
# Run one smoke script with the gateway environment's Python: the parsed JSON, or $null.
function Invoke-Smoke([string]$Python, [string]$Code, [string]$Log) {
    if (-not $Python -or -not (Test-Path -LiteralPath $Python)) { return $null }
    # From a file, not `-c`: Windows PowerShell 5.1 mangles double quotes inside native arguments.
    $file = Join-Path ([System.IO.Path]::GetTempPath()) ("af-smoke-{0}-{1}.py" -f $PID, [guid]::NewGuid().ToString('N'))
    [System.IO.File]::WriteAllText($file, $Code, (New-Object System.Text.UTF8Encoding($false)))
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $out = @(& $Python $file 2>&1 | ForEach-Object { "$_" }) } catch { $out = @("$_") } finally {
        $ErrorActionPreference = $old
        Remove-Item -LiteralPath $file -Force -ErrorAction SilentlyContinue
    }
    if ($Log) { Add-Content -Path $Log -Value (@("`r`n`$ $Python <smoke check>") + $out) -Encoding UTF8 }
    $line = $out | Where-Object { $_ -like 'AFSMOKE *' } | Select-Object -Last 1
    if (-not $line) { return $null }
    try { return ($line.Substring(8) | ConvertFrom-Json) } catch { return $null }
}

# llama.cpp: keep the first build in $Variants that loads (GPU builds: that also report GPU
# offload; the cpu build: that loads). $Install swaps a build in ({ param($v) } -> $true when it
# installed), $Check runs the smoke ({ param($v) } -> the AFSMOKE object), $Remove uninstalls
# llama.cpp when no build loads (never a broken import left behind). $Installed: the build the
# gateway install already included. Returns @{ Kept; Where; Why (the builds not kept, and why) }.
function Resolve-LlamaBuild([string[]]$Variants, [string]$Installed, [scriptblock]$Install, [scriptblock]$Check, [scriptblock]$Remove) {
    $current = $Installed
    $why = @()
    foreach ($v in $Variants) {
        if ($current -ne $v) {
            Write-Info "llama.cpp: installing its $v build ($($AfLlamaSizes[$v]))"
            if (-not (& $Install $v)) { $why += "${v}: did not install"; $current = ''; continue }
            $current = $v
        }
        $r = & $Check $v
        if ($r -and $r.import -and ($v -eq 'cpu' -or $r.offload)) {
            $where = if ($r.offload) { 'GPU offload' } else { 'CPU' }
            Write-Ok "llama.cpp $($r.version) ($v build): loads, $where"
            return @{ Kept = $v; Where = $where; Why = $why }
        }
        $reason = if (-not $r) { 'no answer from the check' } elseif (-not $r.import) { "does not load: $($r.error)" } else { 'loads, but reports no GPU offload' }
        Write-Warn2 "llama.cpp $v build $reason$(if ($v -ne $Variants[-1]) { '; trying the next build' })"
        $why += "${v}: $reason"
    }
    if ($current) { & $Remove }
    return @{ Kept = ''; Where = ''; Why = $why }
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
# What this run could not install (same rule as install.sh's incomplete_add): the summary and the last
# lines say it in red; -Fail (a part a re-run installs once the network or crates.io caught up) also
# makes the exit status 1.
$script:Incomplete = New-Object System.Collections.Generic.List[string]
$script:AfExit = 0
function Add-Incomplete([string]$Label, [string]$Why, [switch]$Fail) {
    $script:Incomplete.Add("  ${Label}: $Why")
    if ($Fail) { $script:AfExit = 1 }
}
# The browser apps follow the release (install.sh's apps-upgrade block, same rule): every app the
# gateway has installed is brought to its $AfNpmApps version through the gateway's own
# `abstractgateway apps update` (the gateway owns the install, so its registry stays right, and a
# running app restarts on the new bundle). A fresh install installs none: the console's Apps page
# installs them, at these versions. With no gateway answering (-NoStart while it is stopped) the
# versions go to <data dir>\apps-upgrade.pending, which the gateway applies at its next start.
# tests/test_install_app_upgrade.py loads these four functions on their own.
$script:AppsLines = @()
function Get-AppPin([string]$Id) {
    foreach ($s in $AfNpmApps) {
        $n = $s -replace '^@abstractframework/', ''; $i = $n.LastIndexOf('@')
        if ($n.Substring(0, $i) -eq $Id) { return $n.Substring($i + 1) }
    }
    return $null
}
function Get-AppsInstalled([string]$Gw, [string]$BaseUrl, [string]$DataDir) {
    # -> @{id; version} per app the running gateway installed; $null when the list cannot be read
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        $raw = (& $Gw apps list --json --no-latest --url $BaseUrl --data-dir $DataDir 2>$null) -join "`n"
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
        $rows = @()
        foreach ($a in @(($raw | ConvertFrom-Json).apps)) {
            if ($a.version -and $a.source -ne 'external') { $rows += [pscustomobject]@{ id = [string]$a.id; version = [string]$a.version } }
        }
        return ,$rows
    } catch { return $null } finally { $ErrorActionPreference = $old }
}
function Write-AppsMarker([string]$DataDir) {
    try {
        New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
        $lines = foreach ($s in $AfNpmApps) { $n = $s -replace '^@abstractframework/', ''; $i = $n.LastIndexOf('@'); "$($n.Substring(0, $i)) $($n.Substring($i + 1))" }
        $tmp = Join-Path $DataDir 'apps-upgrade.pending.tmp'
        [System.IO.File]::WriteAllText($tmp, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $tmp -Destination (Join-Path $DataDir 'apps-upgrade.pending') -Force
        return $true
    } catch { return $false }
}
function Invoke-AppsStep([bool]$Up, [string]$Gw, [string]$BaseUrl, [string]$DataDir) {
    $script:AppsLines = @()
    $pins = (@($AfNpmApps | ForEach-Object { $n = $_ -replace '^@abstractframework/', ''; $i = $n.LastIndexOf('@'); "$($n.Substring(0, $i)) $($n.Substring($i + 1))" }) -join ', ')
    if (-not $Up) {
        if ($script:DryRun) {
            Write-Info "would bring every browser app the gateway has installed to this release's version ($pins), restarting the running ones:"
            Write-Info '    abstractgateway apps update <app> --version <version>'
            return
        }
        if (Write-AppsMarker $DataDir) {
            Write-Info "no gateway answers at ${BaseUrl}: it brings its installed apps to $pins at its next start"
            Write-Info "    ($(Join-Path $DataDir 'apps-upgrade.pending'))"
            $script:AppsLines = @("upgraded at the gateway's next start: $pins")
        } else {
            Write-Warn2 "could not write $(Join-Path $DataDir 'apps-upgrade.pending')"
            Add-Incomplete 'browser apps' "not brought to $pins; once the gateway runs: abstractgateway apps update <app> --version <version>" -Fail
            $script:AppsLines = @('NOT upgraded (see above)')
        }
        return
    }
    $before = Get-AppsInstalled $Gw $BaseUrl $DataDir
    if ($null -eq $before) {
        Write-Warn2 "could not read the gateway's apps (abstractgateway apps list)"
        if ($script:DryRun) { return }
        Add-Incomplete 'browser apps' 'their versions could not be read from the gateway; check with: abstractgateway apps list' -Fail
        $script:AppsLines = @('unknown: abstractgateway apps list failed')
        return
    }
    $did = $false
    foreach ($r in $before) {
        $pin = Get-AppPin $r.id
        if (-not $pin) { continue }
        if ($r.version -eq $pin) { Write-Ok "$($r.id) $($r.version) (this release's version)" }
        elseif ($script:DryRun) { Write-Info "would update $($r.id) $($r.version) -> $pin (restarted if running): abstractgateway apps update $($r.id) --version $pin" }
        else {
            $shown = "abstractgateway apps update $($r.id) --version $pin"
            Write-Host "  `$ $shown" -ForegroundColor DarkGray
            $script:Twins.Add($shown)
            $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
            try { & $Gw apps update $r.id --version $pin --url $BaseUrl --data-dir $DataDir *> $null } catch { } finally { $ErrorActionPreference = $old }
            $did = $true
        }
    }
    if (-not $before.Count) { Write-Info "no browser app installed yet: the console's Apps page installs them ($pins)" }
    if ($script:DryRun) { return }
    # What the gateway reports now is what the summary says: a failed update is never silent.
    $after = $before
    if ($did) {
        $after = Get-AppsInstalled $Gw $BaseUrl $DataDir
        if ($null -eq $after) {
            Add-Incomplete 'browser apps' 'their versions could not be read back from the gateway; check with: abstractgateway apps list' -Fail
            $script:AppsLines = @('unknown: abstractgateway apps list failed after the update')
            return
        }
    }
    foreach ($r in $after) {
        $pin = Get-AppPin $r.id
        if (-not $pin) { continue }
        $prev = @($before | Where-Object { $_.id -eq $r.id } | ForEach-Object { $_.version }) | Select-Object -First 1
        if ($r.version -ne $pin) {
            Write-Warn2 "the $($r.id) app is still $($r.version), not $pin"
            Add-Incomplete "the $($r.id) app" "still $($r.version), not this release's $pin; retry: abstractgateway apps update $($r.id) --version $pin" -Fail
            $script:AppsLines += "$($r.id) $($r.version) (NOT ${pin}: update failed)"
        } elseif ($prev -and $prev -ne $r.version) {
            Write-Ok "the $($r.id) app is now $($r.version)"
            $script:AppsLines += "$($r.id) $prev -> $($r.version)"
        } else { $script:AppsLines += "$($r.id) $($r.version)" }
    }
    if (-not $after.Count) { $script:AppsLines = @("none installed (the console's Apps page installs them)") }
}
# One installer at a time per data dir (same rule as install.sh): a re-run and the gateway's Update
# must never install over each other. The lock is <data dir>\update\install.lock, a directory
# (created atomically) holding the owner's pid; a lock whose pid is gone is taken over.
$script:LockDir = ''
$script:LockHeld = $false
function Lock-Install([string]$DataDirPath) {
    $script:LockDir = Join-Path (Join-Path $DataDirPath 'update') 'install.lock'
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $script:LockDir) | Out-Null
    $refuse = { param($owner) Stop-Install "another AbstractFramework installer is already running for $DataDirPath (pid $owner; lock $($script:LockDir)). What to do: wait until it finishes (an Update started from a console or the menu-bar icon shows its progress there), then run this again. Nothing was changed." }
    $owner = { try { ([string](Get-Content -Raw -LiteralPath (Join-Path $script:LockDir 'pid') -ErrorAction Stop)).Trim() } catch { '' } }
    $created = $false
    try { [System.IO.Directory]::CreateDirectory($script:LockDir) | Out-Null; $created = -not (Test-Path -LiteralPath (Join-Path $script:LockDir 'pid')) } catch { }
    # CreateDirectory succeeds on an existing folder: a lock already holding a pid is someone's.
    if (-not $created) {
        $pidText = & $owner
        if (-not $pidText) { Start-Sleep -Seconds 1; $pidText = & $owner }
        if ($pidText -and (Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue)) { & $refuse $pidText }
        Remove-Item -LiteralPath $script:LockDir -Recurse -Force -ErrorAction SilentlyContinue
        New-Item -ItemType Directory -Path $script:LockDir -ErrorAction SilentlyContinue | Out-Null
        Write-Info "took over a stale installer lock (pid $(if ($pidText) { $pidText } else { 'unknown' }) is no longer running)"
    }
    # The pid file is created with CreateNew: of two runs racing here, exactly one wins.
    try {
        $fs = [System.IO.File]::Open((Join-Path $script:LockDir 'pid'), [System.IO.FileMode]::CreateNew)
        $bytes = [System.Text.Encoding]::ASCII.GetBytes("$PID")
        $fs.Write($bytes, 0, $bytes.Length); $fs.Close()
    } catch { & $refuse (& $owner) }
    $script:LockHeld = $true
}
function Unlock-Install {
    if (-not $script:LockHeld) { return }
    $pidFile = Join-Path $script:LockDir 'pid'
    try { if (([string](Get-Content -Raw -LiteralPath $pidFile -ErrorAction Stop)).Trim() -eq "$PID") { Remove-Item -LiteralPath $script:LockDir -Recurse -Force -ErrorAction SilentlyContinue } } catch { }
    $script:LockHeld = $false
}

function Format-Arg([string]$Value) {
    if ($Value -match '^[A-Za-z0-9_./:=@,+%\\-]+$') { return $Value }
    return "'" + ($Value -replace "'", "''") + "'"
}
function Format-Cmd([string[]]$Argv) { return (($Argv | ForEach-Object { Format-Arg $_ }) -join ' ') }
# This exact command again (same options), for the messages that stop an install on a network failure.
$script:RerunArgs = @(foreach ($k in $PSBoundParameters.Keys) {
    $v = $PSBoundParameters[$k]
    if ($v -is [System.Management.Automation.SwitchParameter]) { if ($v.IsPresent) { "-$k" } }
    else { "-$k"; Format-Arg "$v" }
})
$script:RerunCmd = if ($script:RanAsFile) { "powershell -ExecutionPolicy ByPass -File $(Format-Arg $PSCommandPath) $($script:RerunArgs -join ' ')".TrimEnd() }
    elseif ($script:RerunArgs.Count) { "& ([scriptblock]::Create((irm $AfScriptUrl))) $($script:RerunArgs -join ' ')" }
    else { "powershell -ExecutionPolicy ByPass -c `"irm $AfScriptUrl | iex`"" }

# Run a native command: print it, log its output, fail loudly on a non-zero exit.
function Invoke-Native {
    param([string]$Description, [string[]]$Argv, [switch]$Soft, [string]$Shown = '', [switch]$Live, [string[]]$IndexPins = @(), [string]$Retry = '')
    if (-not $Shown) { $Shown = Format-Cmd $Argv }
    Write-Host "  `$ $Shown" -ForegroundColor DarkGray
    $script:Twins.Add($Shown)
    if ($script:DryRun) { return $true }
    $exe = $Argv[0]
    $rest = @()
    if ($Argv.Count -gt 1) { $rest = $Argv[1..($Argv.Count - 1)] }
    # -IndexPins: a failure that is PyPI index lag for one of these exact pins runs the same command
    # again after each of $script:IndexRetryDelays (Find-IndexLag), and never ends in the -Soft path.
    # -Retry uv (implied by -IndexPins): a transient network failure (Find-Transient) too; when the
    # ladder runs out it stops the install, even with -Soft. -Retry cargo: crates.io lag and network
    # failures (Find-CargoRetry); when the ladder runs out, $script:RunGaveUp holds the cause and the
    # -Soft path returns $false (the caller reports it in red, and the exit status is 1).
    if ($IndexPins.Count -and -not $Retry) { $Retry = 'uv' }
    $script:RunGaveUp = ''
    $tries = $script:IndexRetryDelays.Count + 1
    $try = 1
    while ($true) {
        $mark = 0L
        if (Test-Path -LiteralPath $script:LogFile) { $mark = (Get-Item -LiteralPath $script:LogFile).Length }
        $old = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'   # PS 5.1 turns native stderr into errors
        try {
            Add-Content -Path $script:LogFile -Value "`r`n`$ $Shown" -Encoding UTF8
            if ($Live) {
                # Long downloads and builds: the output as it comes, and a heartbeat (Invoke-LiveProcess).
                $code = Invoke-LiveProcess -Exe $exe -Arguments $rest -Log $script:LogFile
            } else {
                & $exe @rest 2>&1 | ForEach-Object { "$_" } | Add-Content -Path $script:LogFile -Encoding UTF8
                $code = $LASTEXITCODE
            }
        } catch {
            Add-Content -Path $script:LogFile -Value "$_" -Encoding UTF8
            $code = 1
        } finally {
            $ErrorActionPreference = $old
        }
        if ($code -eq 0 -or -not $Retry) { break }
        $out = Read-LogFrom $script:LogFile $mark
        $script:RunMarkText = $out
        $lag = ''; $tr = ''; $trKind = 'network'
        if ($Retry -eq 'cargo') {
            $cr = Find-CargoRetry $out
            if ($cr -like 'lag *') { $tr = $cr.Substring(4); $trKind = 'lag' } elseif ($cr -like 'transient *') { $tr = $cr.Substring(10) }
        } else {
            if ($IndexPins.Count) { $lag = Find-IndexLag $out $IndexPins $code }
            if (-not $lag) { $tr = Find-Transient $out $code }
        }
        if (-not $lag -and -not $tr) { break }
        $minutes = [int][Math]::Floor((($script:IndexRetryDelays | Measure-Object -Sum).Sum + 30) / 60)
        if ($tr) {
            if ($try -ge $tries) {
                Add-Content -Path $script:LogFile -Value "`r`n# ${trKind}: still failing after $try attempts; stopping" -Encoding UTF8
                if ($Retry -eq 'cargo') {
                    if ($trKind -eq 'lag') { $script:RunGaveUp = "crates.io has not listed it yet after $try attempts over about $minutes minutes (cargo: $tr)" }
                    else { $script:RunGaveUp = "a network error while downloading from crates.io, still failing after $try attempts over about $minutes minutes (cargo: $tr)" }
                    break
                }
                Stop-Install ("$Description failed: a network error while downloading, still failing after $try attempts over about $minutes minutes (uv: $tr).`n" +
                    "Nothing was left out and nothing was changed: uv changes the gateway's environment only after every`n" +
                    "download succeeded, so a gateway already installed here is still there and still works.`n" +
                    "What to do: check this computer's internet connection (or its proxy), then run the installer again:`n" +
                    "    $($script:RerunCmd)`nLog: $($script:LogFile)")
            }
            $delay = $script:IndexRetryDelays[$try - 1]
            $try++
            if ($trKind -eq 'lag') { Write-Warn2 "crates.io hasn't listed it yet ($tr); retrying in $delay s (attempt $try/$tries)" }
            else { Write-Warn2 "a network error while downloading ($(if ($Retry -eq 'cargo') { 'cargo' } else { 'uv' }): $tr); retrying in $delay s (attempt $try/$tries)" }
            Add-Content -Path $script:LogFile -Value "`r`n# ${trKind}: $tr; attempt $try/$tries in $delay s" -Encoding UTF8
            Start-Sleep -Seconds $delay
            continue
        }
        $lagKind = ''
        if ($lag.Contains(' ')) { $lag, $lagKind = $lag -split ' ', 2 }
        $lagName, $lagVer = $lag -split '==', 2
        if ($try -ge $tries) {
            Add-Content -Path $script:LogFile -Value "`r`n# index lag: $lagName $lagVer still missing after $try attempts; stopping" -Encoding UTF8
            $minutes = [int][Math]::Floor((($script:IndexRetryDelays | Measure-Object -Sum).Sum + 30) / 60)
            if ($lagKind -eq '404') {
                $lagWhat = "PyPI lists $lagName $lagVer but still does not serve its file after $try attempts over about $minutes minutes (uv: HTTP 404 fetching $lagName $lagVer)"
            } else {
                $lagWhat = "PyPI still does not list $lagName $lagVer after $try attempts over about $minutes minutes (uv: `"there is no version of $lagName==$lagVer`")"
            }
            Stop-Install ("$Description failed: $lagWhat.`n" +
                "The release is published, but the package index this computer reads (one of PyPI's mirrors, or a`n" +
                "package mirror/proxy set in UV_INDEX_URL, PIP_INDEX_URL or uv.toml) has not caught up with it yet.`n" +
                "Nothing was left out and the previous gateway install is unchanged (uv stops before it installs).`n" +
                "What to do: run the installer again in a few minutes; it installs everything, local voice included:`n    $($script:RerunCmd)`n" +
                "With a package mirror, ask its administrator to refresh $lagName. Log: $($script:LogFile)")
        }
        $delay = $script:IndexRetryDelays[$try - 1]
        $try++
        Write-Warn2 "PyPI hasn't published $lagName $lagVer to every mirror yet; retrying in $delay s (attempt $try/$tries)"
        Add-Content -Path $script:LogFile -Value "`r`n# index lag: $lagName $lagVer not listed yet; attempt $try/$tries in $delay s" -Encoding UTF8
        Start-Sleep -Seconds $delay
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

# A person can be asked: an interactive console whose input and output are not redirected
# (automation, CI, `powershell -NonInteractive`, piped input: nobody to ask).
function Test-CanAsk {
    try {
        if (-not [Environment]::UserInteractive) { return $false }
        if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) { return $false }
        if ([Environment]::GetCommandLineArgs() | Where-Object { $_ -match '^-noni' }) { return $false }
        [void][Console]::KeyAvailable
        return $true
    } catch { return $false }
}
# Ask on the console with a time limit: 'y', 'n', or '' when nobody answered (no console, or
# nothing typed within -AskWait seconds: a console with nobody at it must never hang the install).
function Read-TimedAnswer([string]$Question, [string]$Default, [string]$NoAnswer) {
    if ($script:DryRun -or -not (Test-CanAsk)) { return '' }
    while ([Console]::KeyAvailable) { [void][Console]::ReadKey($true) }   # keys typed before the question
    $choices = if ($Default -eq 'y') { '[Y/n]' } else { '[y/N]' }
    $enter = if ($Default -eq 'y') { 'yes' } else { 'no' }
    Write-Host '  ? ' -ForegroundColor Yellow -NoNewline
    Write-Host "$Question $choices (Enter = $enter; no answer within $script:AskSeconds s = $NoAnswer) " -NoNewline
    $deadline = (Get-Date).AddSeconds($script:AskSeconds)
    $answer = ''
    while ((Get-Date) -lt $deadline) {
        if (-not [Console]::KeyAvailable) { Start-Sleep -Milliseconds 100; continue }
        $key = [Console]::ReadKey($true)
        $c = [string]$key.KeyChar
        if ($key.Key -eq 'Enter') { $answer = $Default; break }
        if ($c -eq 'y') { $answer = 'y'; break }
        if ($c -eq 'n') { $answer = 'n'; break }
    }
    Write-Host $(if ($answer -eq 'y') { 'yes' } elseif ($answer -eq 'n') { 'no' } else { '(no answer)' })
    return $answer
}

# The local gateway pointer (root backlog 0943): where this computer's gateway listens, for the
# clients that cannot ask Python (the terminal consoles, the browser apps, the Assistant). The
# address only, never a token. As in install.sh, the installer owns the install it just made (and
# is the one writer that always knows a custom -DataDir), so it writes the pointer for this install
# unconditionally after the health check; `abstractgateway serve` rewrites it only under its
# ownership rule (abstractgateway/gateway_pointer.py). -Uninstall deletes it only when it names this
# install's data dir (paths compared resolved, case-insensitively).
function Resolve-DirPath([string]$Path) {
    try { $full = (Get-Item -LiteralPath $Path -Force -ErrorAction Stop).FullName } catch { $full = [IO.Path]::GetFullPath($Path) }
    return $full.TrimEnd('\', '/')
}
function Get-PointerDataDir([string]$File) {
    if (-not (Test-Path -LiteralPath $File -PathType Leaf)) { return '' }
    try { return [string]((Get-Content -LiteralPath $File -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop).data_dir) } catch { return '' }
}

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
        Write-Output "framework abstractframework $AfFrameworkVersion"
        Write-Output "pypi abstractgateway $AfGatewayPinDefault"
        foreach ($s in $AfPyMatrix) { $i = $s.IndexOf('=='); Write-Output "pypi $($s.Substring(0, $i)) $($s.Substring($i + 2))" }
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
    $dataDirCustom = [bool]($DataDir -or $env:AF_DATA_DIR -or $env:ABSTRACTGATEWAY_DATA_DIR)
    $pointerFile = Join-Path $homeDir '.abstractframework\gateway.json'
    $kept = @()
    if (-not $DataDir) {
        if ($env:AF_DATA_DIR) { $DataDir = $env:AF_DATA_DIR }
        elseif ($env:ABSTRACTGATEWAY_DATA_DIR) { $DataDir = $env:ABSTRACTGATEWAY_DATA_DIR }
        else {
            $DataDir = Join-Path $localAppData 'AbstractGateway'
            # The gateway pointer names the data dir of the install that wrote it: a custom one
            # is kept when it holds this installer's state.
            $ptrDir = Get-PointerDataDir $pointerFile
            if ($ptrDir -and ((Resolve-DirPath $ptrDir) -ne (Resolve-DirPath $DataDir)) -and (Test-Path -LiteralPath (Join-Path $ptrDir 'bootstrap.env'))) {
                $DataDir = $ptrDir; $dataDirCustom = $true; $kept += "-DataDir $ptrDir"
            }
        }
    }
    $stateFile = Join-Path $DataDir 'bootstrap.env'
    $pidFile = Join-Path $DataDir 'gateway.pid'
    $logDir = Join-Path $DataDir 'logs'
    $gatewayLog = Join-Path $logDir 'gateway.log'
    $gatewayErr = Join-Path $logDir 'gateway.err.log'
    $startupDir = [Environment]::GetFolderPath('Startup')
    $shortcut = if ($startupDir) { Join-Path $startupDir 'AbstractGateway.lnk' } else { '' }
    $state = Read-State $stateFile
    $script:AskSeconds = [Math]::Max(0, [Math]::Min(25, $AskWait))
    # The choices a re-run keeps: this command line's, else the previous install's, else the default.
    function Resolve-Choice([bool]$On, [bool]$Off, [string]$Recorded, [bool]$Default, [string]$OffFlag, [string]$OnFlag) {
        if ($Off) { return $false }
        if ($On) { return $true }
        if ($Recorded -eq '0' -or $Recorded -eq '1') {
            $v = ($Recorded -eq '1')
            if ($v -ne $Default) { $script:KeptChoices += $(if ($v) { $OnFlag } else { $OffFlag }) }
            return $v
        }
        return $Default
    }
    $script:KeptChoices = @()
    # (Resolved once the previous install is known: see "an existing install" below.)

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
        } elseif ("$($cfg.port_source)" -eq 'stored' -and "$($cfg.port)" -ne "$Port" -and -not $explicitPort) {
            # A stored port is the user's: only -Port changes it (upgrade safety D-A).
            Write-Warn2 "the Network setting holds port $($cfg.port) (this run's port is $Port): kept, the gateway starts on port $($cfg.port); give -Port to change it"
            # Main's $Port and $baseUrl (this runs inside Start-BackgroundGateway, called from Main).
            Set-Variable -Name Port -Value ([int]$cfg.port) -Scope 2
            Set-Variable -Name baseUrl -Value "http://127.0.0.1:$($cfg.port)" -Scope 2
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
    # The installer's background gateway named by gateway.pid, only when that process is still it
    # (Test-PidFileGateway); a pid file naming another program is said once and never used.
    function Get-OurPid {
        if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
        $p = 0; try { $p = [int]((Get-Content -LiteralPath $pidFile -ErrorAction Stop | Select-Object -First 1) -replace '[^0-9]', '') } catch { $p = 0 }
        if (-not $p -or -not (Test-ProcessAlive $p)) { return $null }
        if (Test-PidFileGateway $p $pidFile $DataDir) { return $p }
        if (-not $script:StalePidSaid) { $script:StalePidSaid = $true; Write-Info "gateway.pid names pid $p, which is not this install's gateway: left alone" }
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

    # The gateway of this install that is running now, whoever started it: the installer's
    # background start (gateway.pid) or the login item (the serve record run\gateway-serve.json,
    # checked to be an abstractgateway process: a stale record may name a reused pid).
    function Get-RunningGatewayPids {
        $pids = @()
        $p = Get-OurPid; if ($p) { $pids += $p }
        if ($script:HandGatewayPid -and ($pids -notcontains $script:HandGatewayPid) -and (Test-ProcessAlive $script:HandGatewayPid)) { $pids += $script:HandGatewayPid }
        $rec = Join-Path $DataDir 'run\gateway-serve.json'
        if (Test-Path -LiteralPath $rec) {
            $rp = 0
            try { $rp = [int]((Get-Content -LiteralPath $rec -Raw | ConvertFrom-Json).pid) } catch { $rp = 0 }
            if ($rp -and ($pids -notcontains $rp) -and (Test-RecordNamesThisGateway (Read-ServeRecord $DataDir) $DataDir)) { $pids += $rp }
        }
        return $pids
    }
    function Stop-RunningGateway {
        foreach ($p in @(Get-RunningGatewayPids)) {
            # Checked again right before the signal: a process that is no longer that gateway is left alone.
            if (-not $script:DryRun -and -not (Test-GatewayPidStillOurs $p $pidFile $DataDir $Port $script:HandGatewayPid)) {
                Write-Info "pid $p is no longer this install's gateway: left alone"
                if ($p -eq $script:HandGatewayPid) { $script:HandGatewayPid = 0 }
                continue
            }
            if ($p -eq $script:HandGatewayPid) { Write-Info "stopping this install's gateway started by hand (pid $p); the installer's own start replaces it on port $Port" }
            Write-Host "  `$ Stop-Process -Id $p" -ForegroundColor DarkGray
            $script:Twins.Add("Stop-Process -Id $p")
            if (-not $script:DryRun) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }
        }
        if (-not $script:DryRun) {
            Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
            if ($script:HandGatewayPid) {
                # Its port must be free before a gateway binds it again.
                $i = 0; while ((Test-ProcessAlive $script:HandGatewayPid) -or (Test-PortBusy $Port)) { if (++$i -gt 20) { break }; Start-Sleep -Milliseconds 500 }
                $script:HandGatewayPid = 0
            }
        }
    }

    if (-not $script:DryRun) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
        Lock-Install $DataDir
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
        # The terminal console and AbstractCode's terminal client this installer built (cargo
        # install, into cargo's bin dir). The uv tool's exposed commands went with it above.
        $cBin = Join-Path $(if ($env:CARGO_HOME) { $env:CARGO_HOME } else { Join-Path $homeDir '.cargo' }) 'bin'
        $cCargo = if (Test-Command 'cargo') { 'cargo' } elseif (Test-Path -LiteralPath (Join-Path $cBin "cargo$exeSuffix")) { Join-Path $cBin "cargo$exeSuffix" } else { $null }
        $roots = Get-CrateRoots $toolBin
        foreach ($crate in @(
                @{ Spec = $AfCrateConsole; Root = $roots.Console; What = 'the terminal console'; Title = 'Terminal console' },
                @{ Spec = $AfCrateCodeCli; Root = $roots.Code; What = 'AbstractCode''s terminal client'; Title = 'AbstractCode terminal client' })) {
            $cName = ($crate.Spec -split '@', 2)[0]
            $cExe = Join-Path $(if ($crate.Root) { Join-Path $crate.Root 'bin' } else { $cBin }) "$cName$exeSuffix"
            if (-not (Test-Path -LiteralPath $cExe)) { continue }
            Write-Step $crate.Title
            $cArgv = @($cCargo, 'uninstall')
            if ($crate.Root) { $cArgv += @('--root', $crate.Root) }
            if ($cCargo) { Invoke-Native -Description "uninstall $($crate.What)" -Argv ($cArgv + @($cName)) -Soft | Out-Null }
            if ($script:DryRun -or (Test-Path -LiteralPath $cExe)) {
                Write-Host "  `$ Remove-Item '$cExe'" -ForegroundColor DarkGray
                if (-not $script:DryRun) { Remove-Item -LiteralPath $cExe -Force -ErrorAction SilentlyContinue }
            }
        }
        # Gateways before 0.7.1 installed their terminal app into <data>\apps\bin (not on PATH). The
        # data dir stays without -Purge, so remove what the gateway put there: its installable terminal
        # apps (apps_manager TUI_BY_APP: abstractcode; it never installs the console), and the folder
        # only when that leaves it empty.
        $staleApps = Join-Path $DataDir 'apps\bin'
        foreach ($t in @('abstractcode')) {
            $f = Join-Path $staleApps "$t$exeSuffix"
            if (-not (Test-Path -LiteralPath $f)) { continue }
            Write-Host "  `$ Remove-Item '$f'" -ForegroundColor DarkGray
            $script:Twins.Add("Remove-Item '$f'")
            if (-not $script:DryRun) { Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue }
        }
        if (-not $script:DryRun -and (Test-Path -LiteralPath $staleApps) -and -not (Get-ChildItem -LiteralPath $staleApps -Force | Select-Object -First 1)) {
            Remove-Item -LiteralPath $staleApps -Force -ErrorAction SilentlyContinue
        }
        Write-Step 'Data'
        # Before the data dir goes (-Purge): the pointer is matched against its resolved path.
        $ptrDir = Get-PointerDataDir $pointerFile
        if ($ptrDir -and ((Resolve-DirPath $ptrDir) -eq (Resolve-DirPath $DataDir))) {
            Write-Host "  `$ Remove-Item '$pointerFile'" -ForegroundColor DarkGray
            if (-not $script:DryRun) { Remove-Item -LiteralPath $pointerFile -Force -ErrorAction SilentlyContinue }
        } elseif ($ptrDir) { Write-Info "kept the gateway pointer $pointerFile`: it belongs to the gateway with data directory $ptrDir" }
        if ($Purge) {
            Write-Host "  `$ Remove-Item -Recurse -Force '$DataDir'" -ForegroundColor DarkGray
            if (-not $script:DryRun) { Remove-Item -LiteralPath $DataDir -Recurse -Force -ErrorAction SilentlyContinue }
        } else { Write-Info "kept the gateway data dir: $DataDir (delete it with -Uninstall -Purge)" }
        Write-Info 'kept: uv, Rust, Ollama, LM Studio, and any other cargo tools'
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

    # --- an existing install: what is there, what this run brings (same wording as install.sh) ---
    $isRelease = (-not $From) -and ($Pin -eq $AfGatewayPinDefault)
    $toolVenv = ''
    if ($uv -and (Test-Path -LiteralPath $uv)) { try { $toolVenv = Join-Path "$(& $uv tool dir 2>$null | Select-Object -First 1)" 'abstractgateway' } catch { $toolVenv = '' } }
    $prevGw = ''
    if ($uv -and (Test-Path -LiteralPath $uv)) {
        $l = (& $uv tool list 2>$null) | Where-Object { $_ -match '^abstractgateway v' } | Select-Object -First 1
        if ($l -match '^abstractgateway v(\S+)') { $prevGw = $Matches[1] }
    }
    $stFramework = [string]$state['FRAMEWORK_VERSION']
    $target = if ($isRelease) { "AbstractFramework $AfFrameworkVersion" } elseif ($From) { "abstractgateway from $From (-From)" } elseif ($Pin -eq 'latest') { 'the newest abstractgateway (-Pin latest)' } else { "abstractgateway $Pin ($pinSource)" }
    if (-not (Test-Path -LiteralPath $stateFile) -and -not $prevGw) { $action = 'install'; $foundLine = "No AbstractFramework install found: installing $target" }
    elseif ($isRelease -and $stFramework -eq $AfFrameworkVersion) { $action = 'check'; $foundLine = "AbstractFramework $stFramework found: already up to date (every part is checked, and repaired if needed)" }
    elseif ($stFramework) { $action = 'upgrade'; $foundLine = "AbstractFramework $stFramework found: upgrading to $target" }
    elseif (Test-Path -LiteralPath $stateFile) { $action = 'upgrade'; $foundLine = "AbstractFramework found (abstractgateway $(if ($prevGw) { $prevGw } else { 'not installed' }); its release was not recorded): upgrading to $target" }
    else { $action = 'upgrade'; $foundLine = "abstractgateway $prevGw found (a uv tool this installer has no record of): upgrading to $target" }
    # Get-EnvSnapshot: "name==version" (lower-case names, _ as -) of the gateway's uv tool environment.
    function Get-EnvSnapshot {
        if ($script:DryRun -or -not $toolVenv -or -not (Test-Path -LiteralPath $uv)) { return @() }
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { $lines = @(& $uv pip freeze --python $toolVenv 2>$null) } catch { $lines = @() } finally { $ErrorActionPreference = $old }
        return @($lines | Where-Object { $_ -match '^[A-Za-z0-9._-]+==' } | ForEach-Object { ($_.Split(' ;')[0]).ToLower().Replace('_', '-') } | Sort-Object)
    }
    $envBefore = @(); if ($action -ne 'install') { $envBefore = Get-EnvSnapshot }
    # An install made before AbstractFramework 0.6.2 recorded none of the choices a re-run keeps
    # (bootstrap.env has no CONSOLE, CODE_CLI, CORE_CLI, TRAY or FULL). Each missing one is read from
    # what that install left on disk, as install.sh does, so its first upgrade keeps them too; the new
    # bootstrap.env then records them. The terminal console and abstractcode: present next to the
    # gateway's commands or in cargo's own bin folder. The library commands: the uv receipt's
    # entrypoints `from = "abstractcore"`. The tray: the tray extra in the receipt's gateway
    # requirement (else the recorded GATEWAY_SPEC). -Full: uv-overrides.txt without the compiled
    # extras' "never" lines (else the tool environment holds one of them).
    # An option this installer did not have yet when that install was made was never a choice: its
    # absence on disk is the old default, and the option takes today's default (same rule and versions
    # as install.sh, upgrade safety D-C): the terminal console became a default with gateway 0.6.0
    # (AbstractFramework 0.5.0), AbstractCode's terminal client and the library commands with gateway
    # 0.7.1 (AbstractFramework 0.6.1). The version: GATEWAY_VERSION, else GATEWAY_SPEC's pin, else the
    # uv tool's; an unknown version keeps reading the disk.
    $prevGwVersion = [string]$state['GATEWAY_VERSION']
    if (-not $prevGwVersion -and [string]$state['GATEWAY_SPEC'] -match '==([0-9][0-9.]*)') { $prevGwVersion = $Matches[1] }
    if (-not $prevGwVersion) { $prevGwVersion = $prevGw }
    $optionExisted = {
        param([string]$Min)
        $v = $null
        if (-not [version]::TryParse(($prevGwVersion -replace '^([0-9]+)$', '$1.0'), [ref]$v)) { return $true }
        return ($v -ge [version]$Min)
    }
    $older = " (no such option before gateway $prevGwVersion's installer: today's default, on)"
    $inferred = @()
    if ((Test-Path -LiteralPath $stateFile) -and $prevGw) {
        $cargoBinPrev = Join-Path $(if ($env:CARGO_HOME) { $env:CARGO_HOME } else { Join-Path $homeDir '.cargo' }) 'bin'
        $rootsPrev = Get-CrateRoots $toolBin
        $crateBinPrev = if ($rootsPrev.Console) { Join-Path $rootsPrev.Console 'bin' } else { $cargoBinPrev }
        $receipt = if ($toolVenv) { Join-Path $toolVenv 'uv-receipt.toml' } else { '' }
        $receiptText = if ($receipt -and (Test-Path -LiteralPath $receipt)) { [string](Get-Content -Raw -LiteralPath $receipt) } else { '' }
        foreach ($c in @(@{ Key = 'CONSOLE'; Name = ($AfCrateConsole -split '@', 2)[0]; Label = 'terminal console'; Since = '0.6.0' }, @{ Key = 'CODE_CLI'; Name = ($AfCrateCodeCli -split '@', 2)[0]; Label = 'abstractcode'; Since = '0.7.1' })) {
            if ($state[$c.Key]) { continue }
            $has = (Test-Path -LiteralPath (Join-Path $crateBinPrev "$($c.Name)$exeSuffix")) -or (Test-Path -LiteralPath (Join-Path $cargoBinPrev "$($c.Name)$exeSuffix"))
            if ($has) { $state[$c.Key] = '1'; $inferred += "$($c.Label) present" }
            elseif (& $optionExisted $c.Since) { $state[$c.Key] = '0'; $inferred += "$($c.Label) absent" }
            else { $state[$c.Key] = '1'; $inferred += "$($c.Label) absent$older" }
        }
        if (-not $state['CORE_CLI'] -and $receiptText) {
            $has = $receiptText -match 'from = "abstractcore"'
            if ($has) { $state['CORE_CLI'] = '1'; $inferred += 'library commands exposed' }
            elseif (& $optionExisted '0.7.1') { $state['CORE_CLI'] = '0'; $inferred += 'library commands not exposed' }
            else { $state['CORE_CLI'] = '1'; $inferred += "library commands not exposed$older" }
        }
        if (-not $state['TRAY']) {
            $gwReq = [regex]::Match($receiptText, '\{ *name = "abstractgateway"[^}]*\}').Value
            if (-not $gwReq) { $gwReq = [string]$state['GATEWAY_SPEC'] }
            if ($gwReq) {
                $has = $gwReq -match 'tray'
                $state['TRAY'] = $(if ($has) { '1' } else { '0' }); $inferred += "tray extra $(if ($has) { 'installed' } else { 'not installed' })"
            }
        }
        if (-not $state['FULL']) {
            $overridesPrev = Join-Path $DataDir 'uv-overrides.txt'
            if (Test-Path -LiteralPath $overridesPrev) {
                $has = -not ([string](Get-Content -Raw -LiteralPath $overridesPrev) -match "(?m)^$([regex]::Escape($AfCompiledExtras[0])); sys_platform == 'never'")
            } else {
                $has = [bool](@($envBefore | Where-Object { $AfCompiledExtras -contains ($_ -split '==', 2)[0] }).Count)
            }
            $state['FULL'] = $(if ($has) { '1' } else { '0' }); $inferred += "compiled extras $(if ($has) { 'built (-Full)' } else { 'not built' })"
        }
    }
    $NoConsole = -not (Resolve-Choice $WithConsole $NoConsole $state['CONSOLE'] $true '-NoConsole' '-WithConsole')
    $NoCodeCli = -not (Resolve-Choice $WithCodeCli $NoCodeCli $state['CODE_CLI'] $true '-NoCodeCli' '-WithCodeCli')
    $NoCoreCli = -not (Resolve-Choice $WithCoreCli $NoCoreCli $state['CORE_CLI'] $true '-NoCoreCli' '-WithCoreCli')
    $NoTray = -not (Resolve-Choice $WithTray $NoTray $state['TRAY'] $true '-NoTray' '-WithTray')
    $Full = Resolve-Choice $Full $NoFull $state['FULL'] $false '-NoFull' '-Full'
    $kept += $script:KeptChoices
    Write-Host $foundLine -ForegroundColor White
    if ($inferred.Count) { Write-Info "the previous install recorded no options (before AbstractFramework 0.6.2): read from disk: $($inferred -join ', ')" }
    if ($kept.Count) { Write-Info "kept from the previous install: $($kept -join ', ') (give the opposite option to change it)" }

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

    # nvidia-smi: driver version and compute capability pick the gpu profile's stack (0988).
    $gpuInfo = Get-NvidiaInfo
    $hasNvidia = [bool]$gpuInfo.Ok
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
            Write-Ok 'profile: gpu (local engines on the NVIDIA GPU when one works, else on the CPU)'
        }
        'apple' { Stop-Install 'the apple profile is for Apple Silicon Macs; use -Profile light or gpu' }
        default { Stop-Install "unknown profile '$profileName' (expected auto, light or gpu)" }
    }

    # The gpu profile's stack (0988): printed with the reason; Windows on ARM has no CUDA builds.
    $stack = $null
    $cpuArchEarly = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    if ($profileName -eq 'gpu') {
        if ($onWindows -and $cpuArchEarly -eq 'ARM64') {
            $stack = @{ Name = 'cpu'; Torch = ''; Llama = @(); Label = 'CPU'; TorchSize = 'about 0.3 GB'; Why = 'Windows on ARM: PyTorch has CPU builds only there' }
        } else { $stack = Select-GpuStack $gpuInfo }
        Write-Ok "GPU stack: $($stack.Label) ($($stack.Why))"
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
    # The exact pins this run takes from the package index (Find-IndexLag): the gateway (unless
    # -From or -Pin latest) and, on a release install, the release matrix. Same as install.sh.
    $indexPins = @()
    if (-not $From -and $Pin -ne 'latest') { $indexPins += "abstractgateway==$Pin" }
    if ($isRelease) { $indexPins += $AfPyMatrix }
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

    # Port: -Port, else the port stored in the installed gateway's Network setting (a user who changed
    # it in a console, the tray or with `abstractgateway network set` keeps it; same rule as install.sh,
    # upgrade safety D-A), else bootstrap.env's, else 8080.
    $explicitPort = ($Port -ne 0)
    $portFromNet = $false
    if (-not $explicitPort -and (Test-GatewaySupports 'network')) {
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $hadDataDir = Test-Path Env:ABSTRACTGATEWAY_DATA_DIR; $prevDataDir = $env:ABSTRACTGATEWAY_DATA_DIR
        $netCfg = $null
        try { $env:ABSTRACTGATEWAY_DATA_DIR = $DataDir; $netCfg = ((& $gw network status --json 2>$null) -join "`n" | ConvertFrom-Json).configured } catch { $netCfg = $null }
        finally {
            $ErrorActionPreference = $old
            if ($hadDataDir) { $env:ABSTRACTGATEWAY_DATA_DIR = $prevDataDir } else { Remove-Item Env:ABSTRACTGATEWAY_DATA_DIR -ErrorAction SilentlyContinue }
        }
        if ($netCfg -and "$($netCfg.port_source)" -eq 'stored' -and "$($netCfg.port)" -match '^[0-9]+$') {
            $Port = [int]$netCfg.port; $portFromNet = $true
            if ($state['PORT'] -and $state['PORT'] -ne "$Port") { Write-Info "port ${Port}: kept from the gateway's Network setting (bootstrap.env said $($state['PORT']); the setting wins, -Port changes it)" }
            # This install's port is the stored one from here on (its running gateway is recognised there).
            $state['PORT'] = "$Port"
        }
    }
    if (-not $explicitPort -and -not $portFromNet) { $Port = if ($state['PORT']) { [int]$state['PORT'] } else { 8080 } }
    $reuseRunning = $false
    # $portHeld: -NoStart, and this install's recorded port is taken by a process this installer does
    # not recognise as its own (a gateway started by hand, or another program). Nothing starts, so the
    # recorded port is kept: moving it would point the next start at a different port.
    $portHeld = $false
    # $script:HandGatewayPid: this install's gateway started by hand on this port (see Find-OwnGateway):
    # the port stays, and the installer's start replaces it (-NoStart leaves it running).
    $script:HandGatewayPid = 0
    if (Test-PortBusy $Port) {
        # The installer's own background gateway (gateway.pid) counts only when it is the listener
        # (when the listener can be named): a reused pid in gateway.pid is not the gateway.
        $listener = Get-PortListenerPid $Port
        $ourPid = Get-OurPid
        # The login item: Windows cannot say which pid is its gateway, so a healthy gateway of THIS data dir
        # on the recorded port counts as it (Find-OwnGateway, when the listener can be named).
        $ours = ("$Port" -eq $state['PORT']) -and ((Test-OurBackgroundListener $listener ([int]$ourPid)) -or ($state['MODE'] -eq 'service' -and ((Get-Http "http://127.0.0.1:$Port/api/health") -match 'abstractgateway') -and (-not $listener -or (Find-OwnGateway $Port $DataDir) -eq $listener)))
        if ($ours) { $reuseRunning = $true; Write-Ok "port ${Port}: this install's gateway is already running (restarted if the package changes)" }
        elseif (($script:HandGatewayPid = Find-OwnGateway $Port $DataDir)) {
            if ($NoStart) { Write-Info "port ${Port}: this install's gateway runs there, started by hand (pid $($script:HandGatewayPid), data dir $DataDir); kept (-NoStart restarts nothing)" }
            else { Write-Ok "port ${Port}: this install's gateway runs there, started by hand (pid $($script:HandGatewayPid), data dir $DataDir); the installer's own start replaces it on this port" }
        }
        elseif ($NoStart -and $state['PORT'] -and "$Port" -eq $state['PORT']) {
            $portHeld = $true
            Write-Info "port $Port (this install's) is in use by a process this installer did not start; kept (-NoStart starts nothing)"
        }
        elseif ($explicitPort) { Stop-Install "port $Port is already in use by another process; pick another one with -Port" }
        elseif ($portFromNet -and -not $NoStart) {
            # Never move a port the user stored: say so, and let them free it or choose.
            Stop-Install "port $Port (the gateway's Network setting) is already in use by another process.`nWhat to do: stop that program, or choose another port with -Port (it becomes the Network setting's port), then run the installer again:`n    $($script:RerunCmd)"
        }
        else {
            $p = $Port + 1
            while ($p -le $Port + 20 -and (Test-PortBusy $p)) { $p++ }
            if ($p -gt $Port + 20) { Stop-Install "ports $Port-$($Port + 20) are all busy; pick one with -Port" }
            Write-Warn2 "port $Port is in use by another process; using $p (kept for future runs)"
            $Port = $p
        }
    } else { Write-Ok "port $Port is free" }
    $baseUrl = "http://127.0.0.1:$Port"

    # Start at login: asked here, before anything is downloaded, whenever a person is at the
    # console; Enter = yes on a first install, the previous choice on a re-run. Nobody to ask:
    # a re-run keeps the previous choice (the login item's own state when the installed gateway
    # reports it: the consoles have a switch for it), a first install leaves it off.
    $loginWas = ''
    if ($state['MODE'] -eq 'service') { $loginWas = 'y' } elseif ($state['MODE'] -eq 'background') { $loginWas = 'n' }
    if ($state['MODE'] -and (Test-GatewaySupports 'service')) {
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { $svc = [string](((& $gw service status --json --data-dir $DataDir 2>$null) -join "`n" | ConvertFrom-Json).state) } catch { $svc = '' }
        finally { $ErrorActionPreference = $old }
        if ($svc -eq 'on') { $loginWas = 'y' } elseif ($svc -eq 'off') { $loginWas = 'n' }
    }
    if (-not $NoStart -and -not $NoService) {
        $noAnswer = if ($loginWas -eq 'y') { 'yes, as now' } elseif ($loginWas -eq 'n') { 'no, as now' } else { 'no' }
        $ans = Read-TimedAnswer 'Start AbstractFramework automatically when you log in? (per-user, no admin; the uninstaller removes it)' $(if ($loginWas) { $loginWas } else { 'y' }) $noAnswer
        if ($ans) { $why = 'your answer' }
        elseif ($loginWas) { $ans = $loginWas; $why = 'kept from the previous install' }
        elseif (-not (Test-CanAsk)) { $ans = 'n'; $why = 'no console to ask on, so a first install leaves it off' }
        elseif ($script:DryRun) { $ans = 'y'; $why = '-Print: the install asks on this console, Enter = yes' }
        else { $ans = 'n'; $why = "no answer within $($script:AskSeconds) s, so a first install leaves it off" }
        if ($ans -eq 'y') { Write-Ok "start at login: yes ($why; turn it off with the Start at login switch in either console, or re-run with -NoService)" }
        else { $NoService = $true; Write-Ok "start at login: no ($why; the gateway starts now in the background; the summary says how to turn it on)" }
    }

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
    Invoke-Native -Description "install Python $AfPython" -Argv @($uv, 'python', 'install', $AfPython) -Retry uv | Out-Null

    # --- 3. gateway ---------------------------------------------------------------------------
    # Windows keeps a running program's files locked, so uv cannot replace the gateway's while it
    # runs: when this run changes the install, the running gateway stops first and starts again
    # below. The same release and spec (a check or repair run): it keeps running.
    $willChange = -not ($isRelease -and $stFramework -eq $AfFrameworkVersion -and $state['GATEWAY_SPEC'] -eq $gwSpec)
    $stoppedForUpdate = $false
    if ($willChange -and $onWindows -and @(Get-RunningGatewayPids).Count) {
        if ($NoStart) {
            Write-Warn2 'a gateway of this install is running and Windows locks its files: if the update fails, stop it (tray: Quit) and run the installer again'
        } else {
            Write-Step 'Stop the running gateway (Windows locks the files of a running program; it starts again below)'
            Stop-RunningGateway
            $stoppedForUpdate = $true
            $reuseRunning = $false
        }
    }
    Write-Step 'AbstractGateway'
    function Get-GatewayToolVersion {
        if ($script:DryRun -or -not (Test-Path -LiteralPath $uv)) { return '' }
        $line = (& $uv tool list 2>$null) | Where-Object { $_ -match '^abstractgateway v' } | Select-Object -First 1
        if ($line -match '^abstractgateway v(\S+)') { return $Matches[1] }
        return ''
    }
    $before = Get-GatewayToolVersion
    # llama.cpp GGUF: the prebuilt wheel on x64 Windows (see the top of this script and 0988 above).
    $ggufPin = ''; $ggufLinks = ''
    $cpuArch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    # The llama.cpp builds to try, in order (gpu profile: the stack's; light: the CPU build).
    $llamaVariants = @(if ($stack -and $stack.Llama.Count) { $stack.Llama } else { 'cpu' })
    $ggufVariant = $llamaVariants[0]
    if (-not $Full -and ($cpuArch -eq 'AMD64' -or -not $onWindows)) {
        $ggufPin = $AfLlamaCpuPin; $ggufLinks = "$AfLlamaIndex/$ggufVariant/llama-cpp-python/"
    }
    # PyTorch's build (0988): --torch-backend when this uv has it for tool installs, else the index.
    $script:TorchSel = @{ Args = @(); Constraints = @() }
    $script:TorchReinstall = $false
    $torchResult = ''
    $uvTorchBackend = $true
    if ($stack -and $stack.Torch -and -not $script:DryRun -and $uv -and (Test-Path -LiteralPath $uv)) {
        $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { $uvTorchBackend = [bool]((& $uv tool install --help 2>$null) -join "`n" -match '--torch-backend') } catch { $uvTorchBackend = $false } finally { $ErrorActionPreference = $old }
    }
    # A stack change on an existing install (for example CPU -> CUDA 13) replaces PyTorch's packages.
    $torchTag = if ($stack -and $stack.Torch) { $stack.Torch } else { '' }
    if (Test-TorchReinstall $action $state $torchTag) { $script:TorchReinstall = $true }
    # Local voice (see $AfWithVoice at the top).
    # A hashtable, so the nested functions below can update it. Voice never fails an install: where
    # its wheels are missing the same install is retried without it (Install-GatewayVoice).
    if ($onWindows -and $cpuArch -eq 'ARM64') {
        $voice = @{ Wanted = $AfWithVoiceArm64; Spec = $AfWithVoiceArm64
            Ok = 'Supertonic (text-to-speech), local on CPU; Whisper speech-to-text skipped: CTranslate2 has no Windows ARM64 wheel' }
    } else {
        $voice = @{ Wanted = $AfWithVoice; Spec = $AfWithVoice
            Ok = 'Supertonic (text-to-speech) and Whisper (speech-to-text), local on CPU' }
    }
    $voice.Result = $voice.Ok
    # uv splits --overrides / --constraints values at whitespace (a user name with a
    # space), so the install runs from the data dir and names both files relatively.
    function Install-Gateway([bool]$Gguf, [switch]$Soft) {
        $overrides = Get-UvOverrides $Full $Gguf
        if ($script:DryRun) {
            Write-Info "$(Join-Path $DataDir 'uv-overrides.txt') (written at install time; see the top of install.ps1):"
            foreach ($l in $overrides) { Write-Host "      $l" }
        }
        # The release matrix (when this run installs the release) and the llama.cpp wheel pin.
        $constraints = @()
        if ($isRelease) { $constraints += $AfPyMatrix }
        if ($Gguf) { $constraints += "llama-cpp-python==$ggufPin" }
        $constraints += $script:TorchSel.Constraints
        if ($script:DryRun) {
            if ($constraints.Count) {
                Write-Info "$(Join-Path $DataDir 'uv-constraints.txt'):$(if ($isRelease) { " the AbstractFramework $AfFrameworkVersion release matrix (exact versions)" })"
                foreach ($l in $constraints) { Write-Host "      $l" }
            }
        } else {
            # UTF-8 without a BOM (Set-Content -Encoding UTF8 adds one on PowerShell 5.1).
            [System.IO.File]::WriteAllText((Join-Path $DataDir 'uv-overrides.txt'), ($overrides -join "`n") + "`n")
            [System.IO.File]::WriteAllText((Join-Path $DataDir 'uv-constraints.txt'), ($constraints -join "`n") + "`n")
        }
        $argv = @($uv, 'tool', 'install', '--python', $AfPython, '--with', $AfWithWheels)
        if ($voice.Spec) { $argv += @('--with', (Get-VoiceRequirement $voice.Spec $isRelease)) }
        if ($Gguf) { $argv += @('--with', "llama-cpp-python==$ggufPin") }
        elseif ($Full) { $argv += @('--with', 'llama-cpp-python') }
        if ($constraints.Count) { $argv += @('--constraints', 'uv-constraints.txt') }
        if ($Gguf) { $argv += @('--find-links', $ggufLinks) }
        $argv += $script:TorchSel.Args
        if ($script:TorchReinstall) { foreach ($p in $AfTorchPins.Keys) { $argv += @('--reinstall-package', $p) } }
        $argv += @('--overrides', 'uv-overrides.txt')
        foreach ($p in (Get-NoBuildPackages $Full)) { $argv += @('--no-build-package', $p) }
        foreach ($p in (Get-RefreshPackages)) { $argv += @('--refresh-package', $p) }
        foreach ($p in $cliFrom) { $argv += @('--with-executables-from', $p) }
        if ($From) { $argv += '--reinstall' }
        # -Pin latest: re-resolve to the newest releases. Without --upgrade, uv keeps every
        # package already installed that still satisfies the requirement, so a re-run over a
        # pinned install would change nothing. (`uv tool upgrade` cannot do it either: it keeps
        # the `==<pin>` the first install recorded and answers "Nothing to upgrade".)
        if ($Pin -eq 'latest' -and -not $From) { $argv += '--upgrade' }
        $shownInstall = "Set-Location $(Format-Arg $DataDir); $(Format-Cmd ($argv + @($gwSpec)))"
        $desc = if ($Gguf) { "install abstractgateway with the llama.cpp $ggufVariant wheel" } else { 'install abstractgateway' }
        if (-not $script:DryRun) { Push-Location -LiteralPath $DataDir }
        try {
            return (Invoke-Native -Description $desc -Argv ($argv + @($gwSpec)) -Shown $shownInstall -Soft:$Soft -Live -IndexPins $indexPins -Retry uv)
        } finally {
            if (-not $script:DryRun) { Pop-Location }
        }
    }
    function Install-GatewayVoice([bool]$Gguf, [switch]$Soft) {
        if ($voice.Wanted) {
            $voice.Spec = $voice.Wanted
            if (Install-Gateway $Gguf -Soft) { $voice.Result = $voice.Ok; return $true }
            # Only a deterministic failure gets here (Invoke-Native retries network failures and index
            # lag, then stops): uv's reason, when it names a missing wheel, goes into the summary.
            $vwhy = [regex]::Match((ConvertTo-RetryText $script:RunMarkText), '[a-z0-9_.-]+(==[^ ]+)? has no wheels with a matching [a-z ]*tag').Value
            Write-Warn2 "local voice (Supertonic, Whisper) did not install on this system$(if ($vwhy) { " ($vwhy)" }): retrying without it"
            $voice.Spec = ''; $voice.Result = "skipped: its packages did not install on this system$(if ($vwhy) { ": $vwhy" }) (see $($script:LogFile))"
        }
        return (Install-Gateway $Gguf -Soft:$Soft)
    }
    # The packages whose commands this install exposes ($AfCliExecutables): each one whose names
    # are all free in the tool bin dir, or already the gateway tool's own (a re-run). A name that
    # another program has (a file, or another uv tool's command) would make uv refuse the whole
    # install, so that package is left out and the summary says so.
    $cliFrom = @(); $cliTaken = @()
    if (-not $NoCoreCli) {
        $ours = @()
        if ($uv -and (Test-Path -LiteralPath $uv)) {
            $tool = $null
            foreach ($l in @(& $uv tool list 2>$null)) {
                if ($l -match '^(\S+) v') { $tool = $Matches[1] }
                elseif ($tool -eq 'abstractgateway' -and $l -match '^- (\S+)') { $ours += $Matches[1] }
            }
        }
        foreach ($p in $AfCliExecutables.Keys) {
            $taken = $null
            foreach ($n in $AfCliExecutables[$p]) {
                $f = Join-Path $toolBin "$n$exeSuffix"
                if ((Test-Path -LiteralPath $f) -and ($ours -notcontains $n) -and ($ours -notcontains "$n$exeSuffix")) { $taken = $f; break }
            }
            if ($taken) {
                $cliTaken += $p
                Write-Warn2 "$p commands not exposed: $taken already exists (another program's); remove it and run the installer again to add them"
            } else { $cliFrom += $p }
        }
    }
    $ggufResult = ''
    $ggufInstalled = ''   # the llama.cpp build the gateway install itself included
    # The big downloads, announced before they start (the output streams below, with a heartbeat).
    if ($profileName -eq 'gpu') {
        $sizes = @("PyTorch $($stack.Label) build ($($stack.TorchSize))")
        if ($ggufPin) { $sizes += "llama.cpp $ggufVariant build ($($AfLlamaSizes[$ggufVariant]))" }
        Write-Info "large downloads ahead: $($sizes -join ', '), plus the voice, image and music engines (several GB in all; cached by uv for re-runs). This can take a while; progress is shown as it happens."
    }
    $cudaDone = $false
    if ($stack -and $stack.Torch) {
        $script:TorchSel = Get-TorchSelection $stack.Torch $uvTorchBackend
        if (-not $uvTorchBackend) { Write-Info "this uv has no 'uv tool install --torch-backend': using the PyTorch index $AfTorchIndex/$($stack.Torch) with exact +$($stack.Torch) versions" }
        if ($script:DryRun) { Write-Info "PyTorch $($stack.Label): $(Format-Cmd $script:TorchSel.Args) (if this install fails: without llama.cpp, then PyTorch's CPU build)" }
        if ($ggufPin) {
            Write-Info "attempt: PyTorch $($stack.Label) build with the llama.cpp $ggufVariant build"
            if (Install-Gateway $true -Soft) { $cudaDone = $true; $ggufInstalled = $ggufVariant }
            else { Write-Warn2 "the install with the llama.cpp $ggufVariant build did not succeed: retrying without llama.cpp (it is tried again afterwards)" }
        }
        if (-not $cudaDone) {
            Write-Info "attempt: PyTorch $($stack.Label) build without llama.cpp"
            if (Install-Gateway $false -Soft) { $cudaDone = $true }
        }
        if ($cudaDone -or $script:DryRun) {
            $torchResult = "PyTorch $($stack.Label) build (from $AfTorchIndex/$($stack.Torch))"
        } else {
            Write-Warn2 "the PyTorch $($stack.Label) build did not install (see $($script:LogFile)): falling back to PyTorch's CPU build"
            $torchResult = "CPU build: the $($stack.Label) build did not install (see the log); the engines run on the CPU"
            $script:TorchSel = @{ Args = @(); Constraints = @() }
            $script:TorchReinstall = $true
            # Without CUDA torch, llama.cpp's CUDA builds cannot load: Vulkan, then CPU.
            $llamaVariants = @($llamaVariants | Where-Object { $_ -notlike 'cu*' })
            if (-not $llamaVariants.Count) { $llamaVariants = @('cpu') }
            $ggufVariant = $llamaVariants[0]
            if ($ggufPin) { $ggufLinks = "$AfLlamaIndex/$ggufVariant/llama-cpp-python/" }
        }
    }
    if ($cudaDone) {
        if ($Full) { $ggufResult = 'llama-cpp-python built from source (-Full)' }
        elseif ($ggufInstalled) { $ggufResult = "llama-cpp-python $ggufPin ($ggufInstalled wheel from $ggufLinks)" }
    } elseif ($Full) {
        Install-GatewayVoice $false | Out-Null
        $ggufResult = 'llama-cpp-python built from source (-Full)'
    } elseif ($ggufPin) {
        if ($script:DryRun) { Write-Info "llama.cpp GGUF: llama-cpp-python $ggufPin, $ggufVariant wheel from $ggufLinks (if this install fails, it is retried without it)" }
        if (Install-GatewayVoice $true -Soft) {
            $ggufInstalled = $ggufVariant
            $ggufResult = "llama-cpp-python $ggufPin ($ggufVariant wheel from $ggufLinks)"
        } else {
            Write-Warn2 $AfGgufSkipped
            Install-GatewayVoice $false | Out-Null
            $ggufResult = "skipped (the prebuilt $ggufVariant wheel did not install; see $($script:LogFile))"
        }
    } else {
        Write-Warn2 $AfGgufSkipped
        Install-GatewayVoice $false | Out-Null
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

    # --- 3b. what runs on the GPU (0988): PyTorch, llama.cpp, Whisper -----------------------------
    # Each check runs in a fresh process of the gateway's environment. A part that does not work is
    # replaced by one that does (PyTorch's CPU build; llama.cpp's next build, down to none), and the
    # summary says what runs where and why. Nothing optional fails the install.
    $toolPy = ''
    $toolVenvNow = $toolVenv
    if (-not $script:DryRun -and $uv -and (Test-Path -LiteralPath $uv)) { try { $toolVenvNow = Join-Path "$(& $uv tool dir 2>$null | Select-Object -First 1)" 'abstractgateway' } catch { } }
    if ($toolVenvNow) { $toolPy = if ($onWindows) { Join-Path $toolVenvNow 'Scripts\python.exe' } else { Join-Path $toolVenvNow 'bin/python' } }
    $whisperResult = ''
    $llamaFinal = ''
    if ($profileName -eq 'gpu') { Write-Step 'Check what runs on the GPU (PyTorch, llama.cpp, Whisper)' } elseif ($ggufPin -and -not $Full) { Write-Step 'Check llama.cpp' }
    if ($script:DryRun) {
        if ($profileName -eq 'gpu') { Write-Info "PyTorch: import torch; torch.cuda.is_available() and the device name (a CUDA build that cannot import is replaced by PyTorch's CPU build)" }
        if ($ggufPin -and -not $Full) {
            $order = ($llamaVariants | ForEach-Object { "$_ ($($AfLlamaSizes[$_]))" }) -join ', then '
            Write-Info "llama.cpp builds tried in this order: $order; a build is kept when it loads as AbstractCore loads it (GPU builds: when llama.cpp reports GPU offload), else none"
        }
    } elseif ($profileName -eq 'gpu') {
        $t = Invoke-Smoke $toolPy $AfTorchSmoke $script:LogFile
        if ($t -and $t.import) {
            if ($t.cuda) { Write-Ok "PyTorch $($t.version): CUDA $($t.cuda_build) on $($t.device)"; $torchResult = "PyTorch $($t.version) on the GPU ($($t.device))" }
            elseif ($stack.Torch -and $t.cuda_build) {
                Write-Warn2 "PyTorch $($t.version) (CUDA $($t.cuda_build) build) installed, but CUDA is not available: the GPU or its driver cannot run this build; torch engines run on the CPU"
                $torchResult = "PyTorch $($t.version): CUDA not available on this machine (see the warning above); the engines run on the CPU"
            } elseif ($stack.Torch -and $script:TorchSel.Args.Count) {
                # The CUDA build was asked for, but a CPU-only PyTorch is what got installed.
                Write-Warn2 "PyTorch $($t.version) is a CPU-only build although the $($stack.Label) build ($($stack.Torch)) was requested: torch engines run on the CPU. Run the installer again; if it stays CPU-only, report it with the log: $script:LogFile"
                $torchResult = "PyTorch $($t.version) on the CPU (the $($stack.Label) build was requested but not installed)"
            } else { Write-Ok "PyTorch $($t.version) on the CPU"; if (-not $torchResult -or $torchResult -like 'PyTorch CUDA*') { $torchResult = "PyTorch $($t.version) on the CPU" } }
        } elseif ($stack.Torch -and $script:TorchSel.Args.Count) {
            $why = if ($t) { $t.error } else { 'no answer from the check' }
            Write-Warn2 "PyTorch's $($stack.Label) build does not import ($why): replacing it with PyTorch's CPU build"
            $script:TorchSel = @{ Args = @(); Constraints = @() }; $script:TorchReinstall = $true
            $llamaVariants = @($llamaVariants | Where-Object { $_ -notlike 'cu*' }); if (-not $llamaVariants.Count) { $llamaVariants = @('cpu') }
            $ggufVariant = $llamaVariants[0]
            if ($ggufPin) { $ggufLinks = "$AfLlamaIndex/$ggufVariant/llama-cpp-python/" }
            if (Install-Gateway ([bool]$ggufInstalled) -Soft) {
                if ($ggufInstalled) { $ggufInstalled = $ggufVariant }
                $t2 = Invoke-Smoke $toolPy $AfTorchSmoke $script:LogFile
                $torchResult = if ($t2 -and $t2.import) { "PyTorch $($t2.version) on the CPU (fallback: the $($stack.Label) build did not import: $why)" } else { "PyTorch does not import (see $($script:LogFile)); torch engines are unavailable" }
            } else { $torchResult = "PyTorch's CPU build did not install either (see $($script:LogFile)); torch engines are unavailable" }
            Write-Info $torchResult
        } else {
            $why = if ($t) { $t.error } else { 'no answer from the check' }
            Write-Warn2 "PyTorch does not import ($why)"
            $torchResult = "PyTorch does not import ($why)"
        }
    }
    # llama.cpp: keep the first build that loads; swap builds with uv pip inside the gateway's
    # environment (--no-index: only that build's wheel page), uninstall when none loads.
    if (-not $script:DryRun -and $ggufPin -and -not $Full -and $toolPy -and (Test-Path -LiteralPath $toolPy)) {
        $pick = Resolve-LlamaBuild -Variants $llamaVariants -Installed $ggufInstalled -Install {
            param($v)
            $links = "$AfLlamaIndex/$v/llama-cpp-python/"
            Invoke-Native -Description "install the llama.cpp $v build" -Argv @($uv, 'pip', 'install', '--python', $toolPy, '--no-index', '--find-links', $links, '--no-deps', '--reinstall-package', 'llama-cpp-python', '--refresh-package', 'llama-cpp-python', "llama-cpp-python==$ggufPin") -Soft -Live
        } -Check { param($v) Invoke-Smoke $toolPy $AfLlamaSmoke $script:LogFile } -Remove {
            Invoke-Native -Description 'remove llama.cpp (no build loads here)' -Argv @($uv, 'pip', 'uninstall', '--python', $toolPy, 'llama-cpp-python') -Soft | Out-Null
        }
        $llamaFinal = $pick.Kept
        if ($llamaFinal) {
            $ggufResult = "llama-cpp-python $ggufPin ($llamaFinal build, $($pick.Where))$(if ($pick.Why.Count) { "; not kept: $($pick.Why -join '; ')" })"
        } else {
            $ggufResult = "skipped: no llama.cpp build loads on this machine ($($pick.Why -join '; ')); GGUF models run in Ollama or LM Studio"
            Write-Warn2 "GGUF (llama.cpp): $ggufResult"
        }
    }
    if (-not $script:DryRun -and $profileName -eq 'gpu' -and $voice.Spec) {
        $w = Invoke-Smoke $toolPy $AfWhisperSmoke $script:LogFile
        if ($w -and $w.device) {
            $whisperResult = "faster-whisper on $($w.device)"
            if ($w.device -eq 'cuda' -and -not $w.cublas_guard -and $stack.Name -eq 'cu130') {
                $whisperResult += ' (this AbstractVoice predates the CUDA 12 cuBLAS check: if speech-to-text fails, set ABSTRACTVOICE_WHISPER_DEVICE=cpu)'
                Write-Warn2 "Whisper: $whisperResult"
            } else { Write-Ok "Whisper: $whisperResult" }
        } elseif ($w) { $whisperResult = "not checked ($($w.error))" }
    }
    # Any package of the gateway's environment that moved counts (a library-only release keeps
    # the gateway's version).
    $envAfter = @(Get-EnvSnapshot)
    $changed = ($before -ne $after) -or [bool]$From -or ($state['GATEWAY_SPEC'] -and $state['GATEWAY_SPEC'] -ne $gwSpec) -or (($envBefore -join "`n") -ne ($envAfter -join "`n"))

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
            Invoke-Native -Description 'install nodejs-wheel' -Argv @($uv, 'tool', 'install', 'nodejs-wheel') -Retry uv | Out-Null
            $nodeWheel = '1'
        }
        Write-Info "the browser apps open through the gateway: in the console's Apps page, Install, then Open (each at $baseUrl/apps/<app>/)"
        Write-Info 'advanced: run one on its own, outside the gateway (first launch downloads it):'
        foreach ($s in $AfNpmApps) { Write-Host "      npx -y $s --gateway-url $baseUrl" -ForegroundColor Gray }
    }

    # Terminal console and AbstractCode's terminal client: crates.io publishes no prebuilt binary,
    # so cargo builds both, into cargo's bin dir. Rust on Windows needs the MSVC Build Tools (a
    # large install that may ask for admin), so this script does not add Rust itself: without
    # cargo it says how, once. A failed build never fails the install (one warning, and the
    # command to run by hand): the web console does everything the terminal one does, and the
    # gateway serves AbstractCode's browser client at /apps/code/.
    $consoleName, $consolePin = $AfCrateConsole -split '@', 2
    $codeName, $codePin = $AfCrateCodeCli -split '@', 2
    $consoleOk = $false; $consoleWhy = 'skipped with -NoConsole'
    $codeOk = $false; $codeWhy = 'skipped with -NoCodeCli'
    $cargoBin = Join-Path $(if ($env:CARGO_HOME) { $env:CARGO_HOME } else { Join-Path $homeDir '.cargo' }) 'bin'
    $cargo = if (Test-Command 'cargo') { 'cargo' } elseif (Test-Path -LiteralPath (Join-Path $cargoBin "cargo$exeSuffix")) { Join-Path $cargoBin "cargo$exeSuffix" } else { $null }
    $roots = Get-CrateRoots $toolBin
    $consoleExe = Join-Path $(if ($roots.Console) { Join-Path $roots.Console 'bin' } else { $cargoBin }) "$consoleName$exeSuffix"
    $codeExe = Join-Path $(if ($roots.Code) { Join-Path $roots.Code 'bin' } else { $cargoBin }) "$codeName$exeSuffix"
    # Test-Crate: the binary answers --version with that crate at the pin; -AtLeast accepts a later
    # version too (the gateway's Apps page updates abstractcode in place: never downgrade it).
    $script:CrateVersion = ''
    function Test-Crate([string]$Exe, [string]$Name, [string]$CratePin, [switch]$AtLeast) {
        $script:CrateVersion = ''
        if ($script:DryRun -or -not (Test-Path -LiteralPath $Exe)) { return $false }
        try { $line = "$(& $Exe --version 2>$null | Select-Object -First 1)" } catch { return $false }
        if (-not $line.StartsWith("$Name ")) { return $false }
        $script:CrateVersion = $line.Substring($Name.Length + 1).Trim()
        if (-not $AtLeast) { return ($script:CrateVersion -eq $CratePin) }
        $have = $null
        if (-not [version]::TryParse($script:CrateVersion, [ref]$have)) { return $false }
        return ($have -ge [version]$CratePin)
    }
    function Install-Crate([string]$What, [string]$Name, [string]$CratePin, [string]$Exe, [string]$Root = '') {
        Write-Info 'compiling it from crates.io (a few minutes the first time)'
        $argv = @($cargo, 'install', '--locked', '--force')
        if ($Root) { $argv += @('--root', $Root) }
        $argv += @($Name, '--version', $CratePin)
        # crates.io lag right after a publish and network failures are retried (-Retry cargo); when the
        # ladder runs out, $script:CrateGaveUp holds the cause. cargo replaces the binary only after a
        # successful build, so a failed upgrade keeps the previous one.
        $script:CrateGaveUp = ''
        $built = Invoke-Native -Description "build $What" -Argv $argv -Soft -Retry cargo
        if ($script:DryRun) { return $true }
        if ($built) { Write-Ok "installed $Name $CratePin`: $Exe"; return $true }
        if ($script:RunGaveUp) {
            $script:CrateGaveUp = "$Name $CratePin was not built: $($script:RunGaveUp); run the installer again: $($script:RerunCmd)"
            Write-Host '  ! ' -ForegroundColor Red -NoNewline; Write-Host $script:CrateGaveUp -ForegroundColor Red
            return $false
        }
        Write-Info "build it by hand: $(Format-Cmd $argv)"
        return $false
    }
    $consoleHave = Test-Crate $consoleExe $consoleName $consolePin
    $codeHave = Test-Crate $codeExe $codeName $codePin -AtLeast
    $codeHaveVersion = $script:CrateVersion
    $rustFor = @()
    if (-not $NoConsole -and -not $consoleHave) { $rustFor += 'the terminal console' }
    if (-not $NoCodeCli -and -not $codeHave) { $rustFor += "AbstractCode's terminal client" }
    $noCargoWhy = 'Rust is not installed: install it from https://rustup.rs (it sets up the MSVC Build Tools), then run the installer again'
    $rustWarned = $false
    if ($NoConsole) { $consoleOk = $consoleHave }
    else {
        Write-Step "Terminal console ($consoleName $consolePin)"
        if ($consoleHave) { Write-Ok "$consoleName $consolePin already installed: $consoleExe"; $consoleOk = $true }
        elseif (-not $cargo) { $consoleWhy = $noCargoWhy; Write-Warn2 "$($rustFor -join ' and ') skipped: $noCargoWhy"; $rustWarned = $true }
        elseif (Install-Crate 'the terminal console' $consoleName $consolePin $consoleExe $roots.Console) { $consoleOk = $true }
        elseif ($script:CrateGaveUp) { $consoleWhy = $script:CrateGaveUp; Add-Incomplete 'terminal console' $script:CrateGaveUp -Fail }
        else { $consoleWhy = 'the cargo build failed (Rust 1.87+ and the MSVC Build Tools are needed)' }
    }
    if ($NoCodeCli) { $codeOk = $codeHave }
    else {
        Write-Step "AbstractCode terminal client ($codeName $codePin)"
        if ($codeHave) { Write-Ok "$codeName $codeHaveVersion already installed ($codePin or later): $codeExe"; $codeOk = $true }
        elseif (-not $cargo) { $codeWhy = $noCargoWhy; if (-not $rustWarned) { Write-Warn2 "$($rustFor -join ' and ') skipped: $noCargoWhy" } }
        elseif (Install-Crate 'AbstractCode''s terminal client' $codeName $codePin $codeExe $roots.Code) { $codeOk = $true }
        elseif ($script:CrateGaveUp) { $codeWhy = $script:CrateGaveUp; Add-Incomplete 'AbstractCode''s terminal client' $script:CrateGaveUp -Fail }
        else { $codeWhy = 'the cargo build failed (Rust 1.87+ and the MSVC Build Tools are needed)' }
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

    $serviceFallback = $false
    # Start-BackgroundGateway: (re)start the gateway as a hidden background process, pid in gateway.pid.
    function Start-BackgroundGateway {
        Stop-RunningGateway
        # Plain `serve` when the gateway has the Network setting (`abstractgateway network`):
        # flags on the command line would override it forever (a restart replays them).
        # Older gateways keep the pinned command line they need.
        $netSetting = $false
        if ($script:DryRun) {
            Write-Info "abstractgateway network set localhost --port $Port   (gateways with 'abstractgateway network', when no mode is stored yet; then plain 'serve')"
        } elseif ((Test-GatewaySupports 'network') -and (Set-NetworkSettingForStart)) {
            $netSetting = $true
        }
        # @(...) keeps an array even with one element: `if` unrolls a one-element array to a string,
        # and `+=` would then concatenate text ("serve--data-dir ..."), not append arguments.
        $serveArgs = @(if ($netSetting) { 'serve' } else { 'serve', '--host', '127.0.0.1', '--port', "$Port" })
        # Launch flags, not environment variables: `serve --data-dir` (gateways 0.3 and later also
        # start with user auth on by themselves; older ones, -Pin 0.1/0.2, keep the environment above).
        $envPrefix = ''
        if ($Pin -match '^0\.[12]\.') { $envPrefix = "`$env:ABSTRACTGATEWAY_DATA_DIR='$DataDir'; `$env:ABSTRACTGATEWAY_USER_AUTH='1'; " }
        else { $serveArgs += @('--data-dir', $DataDir) }
        $serveLine = (($serveArgs | ForEach-Object { ConvertTo-WinArg $_ }) -join ' ')
        $bgCmd = "${envPrefix}Start-Process -FilePath '$gw' -ArgumentList '$($serveLine -replace "'", "''")' -WindowStyle Hidden -RedirectStandardOutput '$gatewayLog' -RedirectStandardError '$gatewayErr'"
        Write-Host "  `$ $bgCmd" -ForegroundColor DarkGray
        $script:Twins.Add($bgCmd)
        if (-not $script:DryRun) {
            $proc = Start-Process -FilePath $gw -ArgumentList $serveLine `
                -WindowStyle Hidden -RedirectStandardOutput $gatewayLog -RedirectStandardError $gatewayErr -PassThru
            Set-Content -LiteralPath $pidFile -Value $proc.Id
            Write-Ok "started (pid $($proc.Id)), log: $gatewayErr"
        }
    }
    if ($NoStart) {
        Write-Step 'Start'
        Write-Info '-NoStart: the gateway is installed but not started'
        $mode = if ($state['MODE']) { $state['MODE'] } else { 'none' }
    } elseif (-not $NoService -and ($serviceOk -or $script:DryRun)) {
        Write-Step 'Login service (abstractgateway service)'
        if ($script:DryRun -and -not $serviceOk) { Write-Info "(only when the installed gateway has 'abstractgateway service'; otherwise a Startup-folder shortcut)" }
        $serviceFailed = $false
        if ($loginWas -eq 'y' -and $reuseRunning -and -not $changed -and -not $stoppedForUpdate) {
            Write-Ok 'login item already registered and the gateway is running, unchanged'
        } else {
            # `service install` starts the gateway now: one that still runs would hold the port.
            Stop-RunningGateway
            if ($shortcut -and (Test-Path -LiteralPath $shortcut) -and -not $script:DryRun) { Remove-Item -LiteralPath $shortcut -Force }
            # No --host: the login item runs plain `serve` and the gateway's Network setting binds it;
            # 127.0.0.1 here would reset a "Local network" choice on every re-run.
            $serviceFailed = -not (Invoke-Native -Description 'register the gateway service' -Argv @($gw, 'service', 'install', '--port', "$Port") -Soft)
        }
        if ($serviceFailed) {
            # Never leave the gateway stopped: it runs now, in the background.
            Write-Warn2 "the login item could not be registered (details in $($script:LogFile)): start at login is off; starting the gateway in the background instead, so it runs now"
            Write-Step 'Start in the background (hidden window)'
            Start-BackgroundGateway
            $mode = 'background'; $serviceFallback = $true
        } else { $mode = 'service' }
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
        if ($loginWas -eq 'y' -and $serviceOk) {
            # Chosen "no" this time: the earlier login item would fight the background gateway for the port.
            Invoke-Native -Description 'remove the login item registered by the previous install' -Argv @($gw, 'service', 'uninstall') | Out-Null
        }
        if ($reuseRunning -and -not $changed -and (Get-OurPid)) {
            Write-Ok "already running (pid $(Get-OurPid)), unchanged"
        } else {
            Start-BackgroundGateway
        }
        $mode = 'background'
    }
    if (-not $script:DryRun) {
        @(
            "# written by AbstractFramework install.ps1 on $((Get-Date).ToUniversalTime().ToString('s'))Z",
            "PORT=$Port", "MODE=$mode", "PROFILE=$profileName", "NODE_WHEEL=$nodeWheel",
            "GATEWAY_SPEC=$gwSpec", "GATEWAY_VERSION=$after",
            # Local voice as installed, and why it is not (empty when it is), like install.sh.
            "VOICE_SPEC=$($voice.Spec)", "VOICE_SKIPPED=$(if (-not $voice.Spec) { $voice.Result -replace '\r?\n', ' ' })",
            # The release this install is (empty after -Pin/-From), and the choices a re-run keeps.
            "FRAMEWORK_VERSION=$(if ($isRelease) { $AfFrameworkVersion })",
            "CONSOLE=$(if ($NoConsole) { 0 } else { 1 })", "CODE_CLI=$(if ($NoCodeCli) { 0 } else { 1 })",
            "CORE_CLI=$(if ($NoCoreCli) { 0 } else { 1 })", "TRAY=$(if ($NoTray) { 0 } else { 1 })", "FULL=$(if ($Full) { 1 } else { 0 })",
            # PyTorch's build (cu130, cu126; empty = PyPI's) and the llama.cpp build kept (0988).
            "TORCH=$(if ($script:TorchSel.Args.Count) { $stack.Torch })", "LLAMA=$llamaFinal"
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
            $ptrDir = Get-PointerDataDir $pointerFile
            $mine = Resolve-DirPath $DataDir
            if ($ptrDir -and ((Resolve-DirPath $ptrDir) -ne $mine)) {
                Write-Info "the gateway pointer named the gateway with data directory $ptrDir; it now names this install"
            }
            try {
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pointerFile) | Out-Null
                $body = [ordered]@{ data_dir = $mine; port = $Port; schema = 1; updated_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); url = $baseUrl; written_by = 'installer' }
                $tmp = "$pointerFile.$PID.tmp"
                [System.IO.File]::WriteAllText($tmp, ($body | ConvertTo-Json) + "`n", (New-Object System.Text.UTF8Encoding($false)))
                if (Test-Path -LiteralPath $pointerFile) { [System.IO.File]::Replace($tmp, $pointerFile, $null) } else { [System.IO.File]::Move($tmp, $pointerFile) }
                Write-Ok "gateway pointer: $pointerFile -> $baseUrl (the consoles and apps on this computer find the gateway there)"
            } catch {
                Remove-Item -LiteralPath "$pointerFile.$PID.tmp" -Force -ErrorAction SilentlyContinue
                Write-Warn2 "could not write the gateway pointer $pointerFile; clients take --gateway-url $baseUrl"
            }
        }

        Write-Step 'Console sign-in'
        $claimed = $false; $opened = $false
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
            try { Start-Process $consoleUrl; $opened = $true; Write-Ok 'opened the console in your browser' } catch { Write-Info "open: $consoleUrl" }
        }
    }

    Write-Step "Browser apps (this release's versions)"
    $appsUp = (Test-Path -LiteralPath $gw) -and ((Get-Http "$baseUrl/api/health" 3) -match 'abstractgateway')
    Invoke-AppsStep -Up $appsUp -Gw $gw -BaseUrl $baseUrl -DataDir $DataDir

    # --- summary -------------------------------------------------------------------------------------
    # What this run changed: the release, the gateway, the release's libraries (old -> new), then
    # how many other packages of the environment moved.
    $changeLines = @(); $changeOthers = 0; $upgradeLine = ''
    if (-not $script:DryRun -and $action -ne 'install') {
        $b = @{}; foreach ($l in $envBefore) { $kv = $l -split '==', 2; $b[$kv[0]] = $kv[1] }
        $a = @{}; foreach ($l in $envAfter) { $kv = $l -split '==', 2; $a[$kv[0]] = $kv[1] }
        $named = @('abstractgateway') + @($AfPyMatrix | ForEach-Object { ($_ -split '==')[0].ToLower().Replace('_', '-') })
        foreach ($k in $named) {
            if ($b[$k] -ne $a[$k] -and ($b.ContainsKey($k) -or $a.ContainsKey($k))) {
                $changeLines += ('{0,-24} {1} -> {2}' -f $k, $(if ($b.ContainsKey($k)) { $b[$k] } else { '(none)' }), $(if ($a.ContainsKey($k)) { $a[$k] } else { '(removed)' }))
            }
        }
        foreach ($k in (@($b.Keys) + @($a.Keys) | Sort-Object -Unique)) { if ($named -notcontains $k -and $b[$k] -ne $a[$k]) { $changeOthers++ } }
        if ($isRelease -and $stFramework -ne $AfFrameworkVersion) {
            $changeLines = @(('{0,-24} {1} -> {2}' -f 'AbstractFramework', $(if ($stFramework) { $stFramework } else { '(not recorded)' }), $AfFrameworkVersion)) + $changeLines
        }
        $was = if ($stFramework) { $stFramework } else { '(not recorded)' }
        if (-not $changeLines.Count -and -not $changeOthers) { $upgradeLine = "Already up to date: $(if ($isRelease) { "AbstractFramework $AfFrameworkVersion" } else { "abstractgateway $after" }); nothing changed." }
        elseif ($isRelease) { $upgradeLine = "Upgraded: AbstractFramework $was -> $AfFrameworkVersion (what changed is listed below)." }
        else { $upgradeLine = "Upgraded: $target (what changed is listed below)." }
    }
    # Local voice not installed: never a silent green (same rule as install.sh).
    if (-not $script:DryRun -and -not $voice.Spec) { Add-Incomplete 'local voice (Supertonic, Whisper)' $voice.Result }
    Write-Host ''
    if ($script:DryRun) { Write-Host 'Plan printed (-Print): nothing was changed.' -ForegroundColor White }
    elseif ($script:Incomplete.Count) {
        Write-Host 'AbstractFramework is installed, but NOT everything was installed:' -ForegroundColor Red
        foreach ($l in $script:Incomplete) { Write-Host $l -ForegroundColor Red }
    }
    else { Write-Host 'AbstractFramework is installed.' -ForegroundColor Green }
    if ($upgradeLine) { Write-Host "  $upgradeLine" }
    if ($serviceFallback) { Write-Host '  Start at login is off: the login item could not be registered (see the warning above). The gateway runs in the background until you sign out; once the cause is fixed, turn start at login on (At login, below).' }
    if ($NoStart -and $changed -and $action -ne 'install' -and -not $script:DryRun) {
        Write-Host '  A gateway that is running still runs the previous version until it restarts: the console''s Restart'
        Write-Host '  (web: the Gateway section), the tray''s Restart, or re-run this installer without -NoStart.'
    }
    if ($NoStart -and $script:HandGatewayPid -and -not $script:DryRun) {
        Write-Host "  This install's gateway, started by hand (pid $($script:HandGatewayPid), port $Port), still runs the version it"
        Write-Host '  started with: re-run this installer without -NoStart to replace it with the installer''s own start.'
    }
    if ($portHeld -and -not $script:DryRun) {
        Write-Host "  Port $Port, this install's port, is in use by a program this installer did not start (for example a"
        Write-Host "  gateway started by hand). The install keeps port ${Port}: restart that gateway to run this version, or stop"
        Write-Host '  the program before the gateway starts again.'
    }
    if ($changeLines.Count -or $changeOthers) {
        Write-Host '  Changes:'
        foreach ($l in $changeLines) { Write-Host "      $l" }
        if ($changeOthers) { Write-Host "      (and $changeOthers other packages of the gateway's environment)" }
    } elseif ($upgradeLine) { Write-Host '  Changes:    none' }
    if (-not $script:DryRun -and $script:AppsLines.Count) {
        Write-Host '  Apps:'
        foreach ($l in $script:AppsLines) { Write-Host "      $l" }
    }
    # The terminal console signs in with the admin token (`--token`), printed ready to paste; the
    # gateway keeps it in its data dir. Before the gateway has written it, the command names that file.
    $tokenPath = Join-Path $DataDir 'auth\bootstrap-admin-token'
    $tuiExe = if (Test-Command $consoleName) { $consoleName } else { "& '$consoleExe'" }
    $tuiTok = if (-not $script:DryRun -and (Test-Path -LiteralPath $tokenPath)) { (Get-Content -LiteralPath $tokenPath -Raw).Trim() } else { '' }
    $codeShown = if (Test-Command $codeName) { $codeName } else { "& '$codeExe'" }
    $codeTok = if ($tuiTok) { $tuiTok } else { "<admin token: Get-Content '$tokenPath'>" }
    $tuiCmd = "$tuiExe --gateway-url $baseUrl --token $codeTok"
    # AbstractCode's terminal client signs in once with the admin token given directly (the installer
    # never saves it for you), then follows the gateway pointer, so no --gateway-url. On this machine
    # `abstractgateway apps tui-command code` opens it signed in without handling a token.
    $tuiCommand = 'abstractgateway apps tui-command code'
    if ($dataDirCustom) { $tuiCommand += " --data-dir $(Format-Arg $DataDir)" }
    if (-not $script:DryRun -and -not $NoStart) {
        Write-Host '  Configure it from either console (the same settings, both need this machine):'
        # An opened claim link is spent (the browser redeemed it): show the plain address then.
        Write-Host "    Web:       $(if ($opened) { "$baseUrl/console" } else { $consoleUrl })"
        if ($claimed -and $opened) { Write-Host "               signed in already in this browser; another browser needs a new link: abstractgateway-config claim-url --base-url $baseUrl" }
        elseif ($claimed) { Write-Host "               one-time sign-in link (10 minutes); a new one: abstractgateway-config claim-url --base-url $baseUrl" }
        else { Write-Host "               sign in as 'admin' with the token in $tokenPath" }
        if ($consoleOk) { Write-Host "    Terminal:  $tuiCmd" } else { Write-Host "    Terminal:  not installed: $consoleWhy" }
        if ($codeOk) {
            Write-Host '  AbstractCode, the coding client, in the terminal:'
            Write-Host "  Sign in (terminal, once): $codeShown login --token $codeTok"
            Write-Host "    then run: $codeShown"
            Write-Host "    or, on this machine, without a token: $tuiCommand"
        } else { Write-Host "  AbstractCode (terminal): not installed: $codeWhy" }
        Write-Host ''
    }
    Write-Host "  Console:    $baseUrl/console"
    Write-Host "  Terminal:   $(if ($consoleOk) { $tuiCmd } else { "not installed ($consoleWhy)" })"
    Write-Host "  Code:       $(if ($codeOk) { "$codeShown   (sign in once: $codeShown login --token $codeTok; or on this machine: $tuiCommand)" } else { "not installed ($codeWhy)" })"
    Write-Host "  Release:    $(if ($isRelease) { "AbstractFramework $AfFrameworkVersion" } else { "$target (not a recorded AbstractFramework release)" })"
    Write-Host "  Gateway:    $gwSpec ($profileName profile)"
    Write-Host "  Data dir:   $DataDir"
    Write-Host "  Logs:       $logDir"
    Write-Host "  Mode:       $mode"
    Write-Host ''
    # What each command on PATH is (the first question is "abstractgateway-config, what is that?").
    Write-Host "  Commands (in $toolBin):"
    $cmdLine = { param($n, $a) Write-Host ('      {0,-24} {1}' -f $n, $a) }
    & $cmdLine 'abstractgateway' 'the gateway: serve, service, network, models, engines, apps'
    & $cmdLine 'abstractgateway-config' 'the gateway''s admin command: status, claim-url (a new console sign-in link), defaults and set-default (model routing), get/set runtime settings, bootstrap-admin'
    if ($consoleOk) { & $cmdLine $tuiExe 'the terminal console (Terminal: above)' }
    if ($codeOk) { & $cmdLine $codeShown 'AbstractCode, the coding client, in the terminal (Code: above)' }
    foreach ($p in $cliFrom) { & $cmdLine $p $AfCliAbout[$p] }
    if ($cliTaken.Count) { Write-Host "  Not exposed (a command name is taken, see the warning above): $($cliTaken -join ' ')" }
    Write-Host ''
    if ($mode -eq 'service') {
        Write-Host '  Status:     abstractgateway service status'
        Write-Host '  Stop:       abstractgateway service uninstall   (stops it and removes the login entry; data is kept)'
        Write-Host "  Start:      abstractgateway service install --port $Port"
    } else {
        Write-Host "  Stop:       Stop-Process -Id (Get-Content '$pidFile')"
        Write-Host "  Start:      re-run this installer$(if ($shortcut -and (Test-Path -LiteralPath $shortcut)) { ' (or sign out and in: the Startup shortcut starts it)' })"
        if ($serviceOk) { Write-Host '  At login:   off; turn it on with the Start at login switch in either console (web: the Gateway section; terminal: F3), or: abstractgateway service enable' }
    }
    Write-Host "  Upgrade:    powershell -ExecutionPolicy ByPass -c `"irm $AfScriptUrl | iex`"   (the latest AbstractFramework release; keeps your settings and data)"
    Write-Host "              & ([scriptblock]::Create((irm $AfScriptUrl))) -Pin latest   (the newest abstractgateway on PyPI; see $AfDocs#upgrade)"
    Write-Host "  Uninstall:  install.ps1 -Uninstall   (or: $(if ($mode -eq 'service') { 'abstractgateway service uninstall; ' })uv tool uninstall abstractgateway)"
    Write-Host '  Check:      uvx abstractframework doctor'
    if ($stack) { Write-Host "  GPU stack:  $($stack.Label) ($($stack.Why))" }
    if ($torchResult) { Write-Host "  PyTorch:    $torchResult" }
    Write-Host "  GGUF:       $ggufResult"
    if ($voice.Spec) { Write-Host "  Voice:      $($voice.Result)" } else { Write-Host "  Voice:      $($voice.Result)" -ForegroundColor Red }
    if ($whisperResult) { Write-Host "  Whisper:    $whisperResult" }
    if (-not $Full -and $profileName -eq 'gpu') { Write-Host "  $AfSkippedLine" }
    Write-Host "  Apps:       $baseUrl/apps/<app>/   (console > Apps > Open; <app>: observer, code, flow, continuum, entity)"
    Write-Host "  Standalone: npx -y @abstractframework/flow --gateway-url $baseUrl   (advanced; also code, observer, continuum, entity)"
    Write-Host "  Docs:       $AfDocs"
    if ($script:Twins.Count) {
        Write-Host ''
        Write-Host '  The same steps by hand:'
        foreach ($t in $script:Twins) { Write-Host "    $t" -ForegroundColor Gray }
    }
    if ($script:LogFile) { Write-Host ''; Write-Host "  Full log: $($script:LogFile)" -ForegroundColor DarkGray }
    # The last lines: what is missing, in red, so the end of the output never reads as complete.
    if (-not $script:DryRun -and $script:Incomplete.Count) {
        Write-Host ''
        Write-Host 'NOT installed:' -ForegroundColor Red
        foreach ($l in $script:Incomplete) { Write-Host $l -ForegroundColor Red }
        if ($script:AfExit) {
            Write-Host 'What to do: run the installer again once the network (or crates.io) has caught up; it installs what is missing:' -ForegroundColor Red
            Write-Host "    $($script:RerunCmd)"
        }
    }
}

try {
    Main
} catch {
    $msg = "$_" -replace '^AFBOOT: ', ''
    Write-Host ''
    Write-Host "ERROR: $msg" -ForegroundColor Red
    if ("$_" -notlike 'AFBOOT:*') { Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray }
    # `exit` would close the window of someone who pasted `irm | iex`; only exit when run as a file.
    Unlock-Install
    if ($script:RanAsFile) { exit 1 }
} finally {
    Unlock-Install
}
# 1 when a part a re-run can install is missing (crates.io lag or the network after the retries).
if ($script:AfExit -and $script:RanAsFile) { exit 1 }

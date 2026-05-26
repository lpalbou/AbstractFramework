# AbstractFramework AbstractCore Installer (test)
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue

if (-not $PythonCmd) {
  Write-Error "Python 3.10+ is required to run the installer."
  exit 1
}

& $PythonCmd.Source "$ScriptDir\installer.py" @Args

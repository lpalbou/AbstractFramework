# https://abstractframework.ai/install.ps1 — forwards to the current AbstractFramework Windows installer
# (scripts/install.ps1 on main):   irm https://abstractframework.ai/install.ps1 | iex
$ErrorActionPreference = 'Stop'
Invoke-Expression (Invoke-RestMethod -Uri 'https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1')

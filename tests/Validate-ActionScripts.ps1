<#
.SYNOPSIS
Parses PowerShell extracted from the composite actions and checks it against the
Azure.Iot.Sdk.Test module.

.DESCRIPTION
Two failure modes are caught here, both of which otherwise only show up when a
consuming pipeline provisions real Azure resources:

  * a syntax error in an action's inline script
  * a call to a module cmdlet that does not exist, or that is passed a parameter
    the module does not declare -- the module and its callers live in different
    files and, once the actions are consumed from other repositories, in
    different release cadences

Invoked by tests/validate-actions.mjs, which extracts the scripts from YAML.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$ScriptPath
)

$ErrorActionPreference = 'Stop'

$ModulePath = Join-Path $PSScriptRoot '../scripts/Azure.Iot.Sdk.Test.psm1'
Import-Module $ModulePath -Force

$ModuleCommands = @{}
foreach ($Command in Get-Command -Module Azure.Iot.Sdk.Test) {
    $ModuleCommands[$Command.Name] = $Command
}

$Problems = New-Object System.Collections.Generic.List[string]

foreach ($Path in $ScriptPath) {
    $Name = Split-Path -Leaf $Path

    $Tokens = $null
    $ParseErrors = $null
    $Ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$Tokens, [ref]$ParseErrors)

    if ($ParseErrors.Count -gt 0) {
        foreach ($ParseError in $ParseErrors) {
            $Problems.Add("$Name : line $($ParseError.Extent.StartLineNumber): $($ParseError.Message)")
        }
        continue
    }

    $Calls = $Ast.FindAll({ param($Node) $Node -is [System.Management.Automation.Language.CommandAst] }, $true)

    foreach ($Call in $Calls) {
        $CommandName = $Call.GetCommandName()
        if (-not $CommandName) { continue }
        if (-not $ModuleCommands.ContainsKey($CommandName)) { continue }

        $Parameters = $ModuleCommands[$CommandName].Parameters

        foreach ($Element in $Call.CommandElements) {
            if ($Element -isnot [System.Management.Automation.Language.CommandParameterAst]) { continue }

            $ParameterName = $Element.ParameterName
            # Accept a unique prefix, exactly as PowerShell's own binder does.
            $Matched = @($Parameters.Keys | Where-Object { $_ -like "$ParameterName*" })
            if ($Matched.Count -eq 0) {
                $Problems.Add("$Name : $CommandName has no parameter -$ParameterName")
            } elseif ($Matched.Count -gt 1 -and $Matched -notcontains $ParameterName) {
                $Problems.Add("$Name : -$ParameterName is ambiguous for $CommandName ($($Matched -join ', '))")
            }
        }
    }
}

if ($Problems.Count -gt 0) {
    foreach ($Problem in $Problems) { Write-Error -Message $Problem -ErrorAction Continue }
    exit 1
}

Write-Host "OK: $($ScriptPath.Count) embedded script(s) parsed and checked against Azure.Iot.Sdk.Test."

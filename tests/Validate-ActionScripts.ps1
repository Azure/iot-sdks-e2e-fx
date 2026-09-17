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

function Get-SplatKey {
    <#
    .SYNOPSIS
    Parameter names a splatted hashtable variable can carry, as far as they can
    be determined statically.

    .DESCRIPTION
    Collects keys from every literal hashtable assigned to the variable
    (`$Args = @{ Foo = 1 }`) and from every literal index assignment
    (`$Args['Bar'] = 2`). Keys built dynamically cannot be resolved and are
    simply not reported -- this narrows the blind spot rather than closing it.
    #>
    param(
        [System.Management.Automation.Language.Ast]$Ast,
        [string]$VariableName
    )

    $Keys = New-Object System.Collections.Generic.List[string]

    $Assignments = $Ast.FindAll({
            param($Node) $Node -is [System.Management.Automation.Language.AssignmentStatementAst]
        }, $true)

    foreach ($Assignment in $Assignments) {
        $Left = $Assignment.Left

        # $Args = @{ ... }
        if ($Left -is [System.Management.Automation.Language.VariableExpressionAst] -and
            $Left.VariablePath.UserPath -eq $VariableName) {

            foreach ($Hashtable in $Assignment.Right.FindAll({
                        param($Node) $Node -is [System.Management.Automation.Language.HashtableAst]
                    }, $true)) {
                foreach ($Pair in $Hashtable.KeyValuePairs) {
                    if ($Pair.Item1 -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
                        $Keys.Add($Pair.Item1.Value)
                    }
                }
            }
        }

        # $Args['Key'] = ...
        if ($Left -is [System.Management.Automation.Language.IndexExpressionAst] -and
            $Left.Target -is [System.Management.Automation.Language.VariableExpressionAst] -and
            $Left.Target.VariablePath.UserPath -eq $VariableName -and
            $Left.Index -is [System.Management.Automation.Language.StringConstantExpressionAst]) {

            $Keys.Add($Left.Index.Value)
        }
    }

    return $Keys | Select-Object -Unique
}

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

    # Escape hatch for a parameter whose presence the script checks ITSELF at
    # runtime, which static analysis cannot see:
    #
    #   # validate-actions: allow-parameter EnableADU
    #
    # Deliberately per-name and greppable, so it cannot silently disable the
    # check for anything else.
    $Allowed = @($Tokens |
            Where-Object { $_.Kind -eq 'Comment' } |
            ForEach-Object {
                $Match = [regex]::Match($_.Text, 'validate-actions:\s*allow-parameter\s+(?<name>[A-Za-z0-9_]+)')
                if ($Match.Success) { $Match.Groups['name'].Value }
            })

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

        # Splatted arguments (@Args) carry their parameter names as hashtable
        # keys, so checking only CommandParameterAst would leave a call that
        # passes everything by splat completely unchecked -- which is how these
        # actions call New-AzIotTestEnvironment.
        foreach ($Element in $Call.CommandElements) {
            if ($Element -isnot [System.Management.Automation.Language.VariableExpressionAst]) { continue }
            if (-not $Element.Splatted) { continue }

            foreach ($Key in (Get-SplatKey -Ast $Ast -VariableName $Element.VariablePath.UserPath)) {
                if ($Allowed -contains $Key) { continue }
                if (-not $Parameters.ContainsKey($Key)) {
                    $Problems.Add("$Name : $CommandName has no parameter -$Key (splatted via @$($Element.VariablePath.UserPath))")
                }
            }
        }
    }
}

if ($Problems.Count -gt 0) {
    foreach ($Problem in $Problems) { Write-Error -Message $Problem -ErrorAction Continue }
    exit 1
}

Write-Host "OK: $($ScriptPath.Count) embedded script(s) parsed and checked against Azure.Iot.Sdk.Test."

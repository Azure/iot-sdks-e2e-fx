function Debug-PSScript {
    param($Path)

    $Path = Resolve-Path $Path

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null

    $errors | ForEach-Object {
        [pscustomobject]@{
            Message = $_.Message
            File    = $_.Extent.File
            Line    = $_.Extent.StartLineNumber
            Column  = $_.Extent.StartColumnNumber
            Text    = $_.Extent.Text
        }
    } | Format-List
}

function Invoke-Script {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [scriptblock] $ScriptBlock
    )

    try {
        & $ScriptBlock
    }
    catch {
        Write-Host "Exception: $($_.ToString())"
        Write-Host "Errors:"
        $_.InvocationInfo
        $null
    }
}

function New-GuidString {
    param(
        [switch]$NoDashes,
        [int]$MaxLength = 0
    )

    $Guid = [guid]::NewGuid().ToString()

    if ($NoDashes) {
        $Guid = $Guid.Replace('-', '')
    }

    if ($MaxLength -gt 0 -and $Guid.Length -gt $MaxLength) {
        $Guid = $Guid.Substring(0, $MaxLength)
    }

    return $Guid
}

function New-TempFile {
    # $Extension is the extension WITHOUT the leading dot (e.g. "pem"); a leading
    # dot is tolerated. When omitted, the .tmp path is returned unchanged.
    param([string]$Extension = '')

    # GetTempFileName() guarantees the name it returns is unused, but that
    # guarantee only covers the .tmp file it creates: replacing the extension can
    # land on a name another process already owns. Retry until the final path is
    # free so the caller still gets a unique file.
    $MaxAttempts = 10

    for ($Attempt = 0; $Attempt -lt $MaxAttempts; $Attempt++) {
        $TempFilePath = [System.IO.Path]::GetTempFileName()
        Remove-Item -Path $TempFilePath

        if ([string]::IsNullOrEmpty($Extension)) {
            break
        }

        $Suffix = if ($Extension.StartsWith('.')) { $Extension } else { ".$Extension" }
        $TempFilePath = [System.IO.Path]::ChangeExtension($TempFilePath, $Suffix)

        if (-not (Test-Path $TempFilePath)) {
            break
        }
    }

    return $TempFilePath
}

function ConvertTo-Base64 {
    param($Content)
    $ContentBytes  = [System.Text.Encoding]::UTF8.GetBytes($Content)
    $Base64Content = [System.Convert]::ToBase64String($ContentBytes)
    return $Base64Content
}

function Set-FileContent {
    param(
        $Path = $null,
        $Content = $null
    )

    $OutFileDir = Split-Path -Path $Path -Parent
    if ($OutFileDir -ne "" -and $(Test-Path $OutFileDir) -eq $false) {
        New-Item -ItemType Directory -Force -Path $OutFileDir | Out-Null        
    }

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)  # $false = no BOM
        [System.IO.File]::WriteAllText("$Path", "$Content", $Utf8NoBom)
    } else {
        Set-Content -Path "$Path" -Value $Content -Encoding utf8 -NoNewline
    }
}

function Stop-OnError {
    param([string]$Step = 'Command', [int]$ExpectedReturn = 0, [switch]$Throw)
    if ($LASTEXITCODE -ne $ExpectedReturn) {
        $ErrorMessage = "ERROR: `"$Step`" failed (exit code $LASTEXITCODE)"
        if ($Throw) {
            throw $ErrorMessage
        } else {
            Write-Host $ErrorMessage 
            exit 1
        }
    }
}

# The azure-iot CLI extension version this repo provisions with.
#
# ADR no longer needs it: the namespace, the certificate authorities and the link
# are created through ARM directly (see New-AdrCertificateAuthority), so the
# `az iot adr` command group -- which models the retired public-preview object
# model and has no command for the one that replaced it -- is not used here.
#
# The pin stays for the OTHER reasons below, which still hold: this module reads
# `az iot hub connection-string show` for the service-side clients, and pinning
# is what makes the version reproducible rather than whatever is newest.
#
# Installed from the release wheel rather than by name, because 0.30.0b2 was
# pulled from the Azure CLI extension index and `--version` no longer resolves
# it. The newer indexed previews are not substitutes: 0.31.0 dropped `adr`, and
# 0.32.0b1 returns the device-facing hostname (<hub>.device.azure-devices.net)
# from `az iot hub connection-string show`, which aims the SDK e2e service
# clients at an endpoint serving no service-side AMQP links -- c2d, methods,
# twin and file-upload notifications all fail there while device telemetry,
# which never reads that string, keeps passing.
# TODO: drop the pin and install the stable extension once `adr` ships in one.
$script:AzureIotCliExtensionVersion = "0.30.0b2"
$script:AzureIotCliExtensionSource = "https://github.com/Azure/azure-iot-cli-extension/releases/download/v$($script:AzureIotCliExtensionVersion)/azure_iot-$($script:AzureIotCliExtensionVersion)-py3-none-any.whl"

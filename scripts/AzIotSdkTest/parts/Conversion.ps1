
function Join-Hashtable {
    param(
        [Hashtable]$Hashtable,
        [string]$Separator = " "
    )

    if ($null -eq $Hashtable -or $Hashtable.Count -eq 0) {
        return ""
    } else {
        return ($Hashtable.GetEnumerator() | %{ "$($_.Key)=$($_.Value)" }) -join $Separator
    }
}

function ConvertTo-TagArguments {
    param([Hashtable]$Hashtable)

    if ($null -eq $Hashtable -or $Hashtable.Count -eq 0) {
        return @()
    }

    return @(
        $Hashtable.GetEnumerator() | ForEach-Object {
            $Key = [string]$_.Key
            $Value = if ($null -eq $_.Value) { "" } else { [string]$_.Value }

            # If callers already include wrapping double quotes, normalize it to a raw value.
            if ($Value.Length -ge 2 -and $Value.StartsWith('"') -and $Value.EndsWith('"')) {
                $Value = $Value.Substring(1, $Value.Length - 2)
            }

            "$Key=$Value"
        }
    )
}

function Convert-CollectionToHashtable {
    param([array]$Collection)
    if ($null -eq $Collection) { return @() }
    return @(foreach ($item in $Collection) { if ($null -ne $item) { $item.ToHashtable() } })
}

function ConvertTo-Hashtable {
    param($Object)
    if ($null -ne $Object) {
        return $Object.ToHashtable()
    } else {
        return $null
    }
}

function ConvertFrom-PSObject {
    param($Object)
    if ($Object -is [System.Management.Automation.PSCustomObject]) {
        $Hashtable = [ordered]@{}
        foreach ($Property in $Object.PSObject.Properties) {
            $Hashtable[$Property.Name] = ConvertFrom-PSObject $Property.Value
        }
        return $Hashtable
    } elseif ($Object -is [System.Collections.IEnumerable] -and $Object -isnot [string]) {
        return @(foreach ($Item in $Object) { ConvertFrom-PSObject $Item })
    } else {
        return $Object
    }
}

function New-RandomNumber {
    param($Length = 16)

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $RandomNumber = New-Object byte[] $Length
        [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($RandomNumber)
        return $RandomNumber
    } else {
        return [System.Security.Cryptography.RandomNumberGenerator]::GetBytes($Length)
    }
}

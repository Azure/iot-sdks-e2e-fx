# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

function IsWin32 {
    if("$env:OS" -ne "") {
        if ($env:OS.Indexof('Windows') -ne -1) {
            return $true
        }
    }
    return $false
}

function Invoke-PyCmd($py_cmd) {
    $py = ""
    if(IsWin32) {
        $py = "python $py_cmd"
    }
    else { 
        $py = "python3 $py_cmd"
    }
    Invoke-Expression $py
}

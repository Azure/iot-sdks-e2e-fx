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

function PyCmd-Run($py_cmd) {
    if(IsWin32) {
        return "python $py_cmd"
    }
    else { 
        return "python3 $py_cmd"
    }
}

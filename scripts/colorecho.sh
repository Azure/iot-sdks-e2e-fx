# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

# https://misc.flogisoft.com/bash/tip_colors_and_formatting
export _cyan="1;36"
export _red="1;31"
export _green="1;32"

function colorecho {
  color="$1"
  shift
  /bin/echo -e "\e[${color}m$@\e[0m"
}



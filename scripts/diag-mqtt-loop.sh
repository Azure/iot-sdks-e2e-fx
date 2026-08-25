#!/usr/bin/env bash
# DIAGNOSTIC ONLY.  Alternates the client's maximum TLS version attempt by
# attempt so that any drift in the server's health over time affects both
# variants equally.  Ordering the two variants in separate batches would leave
# a degrading server looking like a TLS version difference.
script_dir=$(cd "$(dirname "$0")" && pwd)
target=$1; servername=$2; n=${3:-40}
declare -A ok fail times
for v in TLSv1.2 TLSv1.3; do ok[$v]=0; fail[$v]=0; times[$v]=""; done
for i in $(seq 1 "$n"); do
  if [ $((i % 2)) -eq 1 ]; then v=TLSv1.2; else v=TLSv1.3; fi
  out=$(timeout 30 node "${script_dir}/diag-mqtt-probe.js" "$target" "$servername" 0 "$v" 2>&1)
  if echo "$out" | grep -q "SERVER ANSWERED"; then
    ok[$v]=$(( ${ok[$v]} + 1 ))
    t=$(echo "$out" | sed -n 's/.*SERVER ANSWERED.* at \([0-9]*\)ms.*/\1/p')
    times[$v]="${times[$v]}${t} "
  else
    fail[$v]=$(( ${fail[$v]} + 1 ))
  fi
  echo "ATTEMPT ${i} max=${v} $(echo "$out" | grep -oE 'SERVER ANSWERED [0-9]+ bytes|NO ANSWER within [0-9]+ms|CLOSED WITH NO ANSWER|ERROR .*' | head -1)"
done
for v in TLSv1.2 TLSv1.3; do
  echo "SUMMARY target=${target} max=${v} answered=${ok[$v]} failed=${fail[$v]} times_ms=[${times[$v]}]"
done

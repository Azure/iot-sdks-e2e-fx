#!/usr/bin/env bash
# DIAGNOSTIC ONLY.  Repeats the raw TLS+MQTT CONNECT probe N times and prints a
# one line summary, so the pass rate can be compared between configurations
# without reading hundreds of lines of build log.
script_dir=$(cd "$(dirname "$0")" && pwd)
target=$1; servername=$2; maxver=$3; n=${4:-20}
ok=0; fail=0; times=""
for i in $(seq 1 "$n"); do
  out=$(timeout 30 node "${script_dir}/diag-mqtt-probe.js" "$target" "$servername" 0 "$maxver" 2>&1)
  if echo "$out" | grep -q "SERVER ANSWERED"; then
    ok=$((ok+1))
    t=$(echo "$out" | sed -n 's/.*SERVER ANSWERED.* at \([0-9]*\)ms.*/\1/p')
    times="${times}${t} "
  else
    fail=$((fail+1))
  fi
done
echo "SUMMARY target=${target} max=${maxver} attempts=${n} answered=${ok} failed=${fail} times_ms=[${times}]"

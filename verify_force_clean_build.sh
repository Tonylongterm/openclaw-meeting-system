#!/usr/bin/env bash
set -u

MARKER="ULTIMATE_STABLE"
URL="${1:-${PRODUCTION_URL:-}}"

if [[ -z "${URL}" ]]; then
  echo "Usage: ./verify_force_clean_build.sh <production-url>"
  echo "Or set PRODUCTION_URL in the environment."
  exit 2
fi

if [[ "${URL}" != http://* && "${URL}" != https://* ]]; then
  URL="https://${URL}"
fi

attempt=0

while true; do
  attempt=$((attempt + 1))
  timestamp="$(date '+%Y-%m-%d %H:%M:%S %Z')"
  body="$(curl -fsSL \
    -H 'Cache-Control: no-cache' \
    -H 'Pragma: no-cache' \
    "${URL}" 2>&1)"
  status=$?

  if [[ ${status} -eq 0 ]]; then
    bytes="$(printf '%s' "${body}" | wc -c | tr -d ' ')"
    echo "[${timestamp}] attempt=${attempt} status=200 bytes=${bytes} url=${URL}"
    if [[ "${body}" == *"${MARKER}"* ]]; then
      echo "SUCCESS: found '${MARKER}' on attempt ${attempt}"
      exit 0
    fi
    echo "[${timestamp}] marker '${MARKER}' not found yet"
  else
    echo "[${timestamp}] attempt=${attempt} curl failed: ${body}"
  fi

  sleep 10
done

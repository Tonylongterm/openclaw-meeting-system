#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:7788}"

check_no_leak() {
    local path="$1"
    local body
    body="$(curl -fsS "$BASE_URL$path")"

    if grep -q 'modal-create' <<<"$body"; then
        echo "FAIL: found modal-create in $path"
        exit 1
    fi

    if grep -q 'page-list' <<<"$body"; then
        echo "FAIL: found page-list in $path"
        exit 1
    fi

    if grep -q 'page-detail' <<<"$body"; then
        echo "FAIL: found page-detail in $path"
        exit 1
    fi

    echo "PASS: no isolated app markup leaked from $path"
}

check_no_leak "/app"
check_no_leak "/app?auth=register"

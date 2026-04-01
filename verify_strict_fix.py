#!/usr/bin/env python3
import os
import sys
import time

import requests


MARKER = "23:40_FORCE_CLEAN_BUILD"
REQUEST_TIMEOUT = 10
SLEEP_SECONDS = 10


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        raise ValueError("production URL is empty")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def main() -> int:
    raw_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PRODUCTION_URL", "")
    if not raw_url:
        print("Usage: python verify_strict_fix.py <production-url>")
        print("Or set PRODUCTION_URL in the environment.")
        return 2

    url = normalize_url(raw_url)
    attempt = 0

    while True:
        attempt += 1
        try:
            response = requests.get(
                url,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
                timeout=REQUEST_TIMEOUT,
            )
            body = response.text
            print(f"[attempt {attempt}] status={response.status_code} bytes={len(body)} url={url}")
            if MARKER in body:
                print(f"SUCCESS: found marker '{MARKER}' on attempt {attempt}")
                return 0
            print(f"[attempt {attempt}] marker '{MARKER}' not found yet")
        except requests.RequestException as exc:
            print(f"[attempt {attempt}] ERROR {exc}")

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())

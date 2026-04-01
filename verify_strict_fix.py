#!/usr/bin/env python3
import os
import sys
import time

import requests


MARKER = "22:58_STRICT_FIX"
MAX_ATTEMPTS = 10
TIMEOUT_SECONDS = 120
REQUEST_TIMEOUT = 10


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
    deadline = time.time() + TIMEOUT_SECONDS
    attempt = 0
    last_error = None

    while time.time() < deadline:
        for _ in range(MAX_ATTEMPTS):
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
                last_error = (
                    f"marker '{MARKER}' not found on attempt {attempt}; "
                    f"status={response.status_code}"
                )
            except requests.RequestException as exc:
                last_error = f"request failed on attempt {attempt}: {exc}"
                print(f"[attempt {attempt}] ERROR {exc}")

            if time.time() >= deadline:
                break
            time.sleep(1)

    raise SystemExit(
        f"ERROR: failed to observe marker '{MARKER}' within {TIMEOUT_SECONDS} seconds. "
        f"Last error: {last_error}"
    )


if __name__ == "__main__":
    raise SystemExit(main())

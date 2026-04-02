#!/usr/bin/env python3
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


TITLE_MARKER = "00:30_SELF_HEAL"
MIN_BODY_BYTES = 10000
DEFAULT_URL = "http://127.0.0.1:7788/app?auth=login"
DEFAULT_TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 2


def build_probe_url(base_url, attempt):
    parsed = urllib.parse.urlparse(base_url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("_final_e2e", f"{int(time.time())}-{attempt}"))
    return parsed._replace(query=urllib.parse.urlencode(query)).geturl()


def fetch_html(url):
    request = urllib.request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "openclaw-final-e2e/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
        status = getattr(response, "status", response.getcode())
    text = body.decode("utf-8", errors="replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    title = match.group(1).strip() if match else ""
    return status, title, len(body), text


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FINAL_E2E_URL", DEFAULT_URL)
    timeout_seconds = int(os.environ.get("FINAL_E2E_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    deadline = time.time() + timeout_seconds
    attempt = 0
    last_error = "no attempts made"

    print(f"TARGET {base_url}")
    print(f"EXPECT title contains {TITLE_MARKER!r} and body bytes > {MIN_BODY_BYTES}")

    while time.time() < deadline:
        attempt += 1
        probe_url = build_probe_url(base_url, attempt)
        try:
            status, title, body_len, _ = fetch_html(probe_url)
            print(f"ATTEMPT {attempt}: status={status} title={title!r} body_bytes={body_len}")
            if TITLE_MARKER in title and body_len > MIN_BODY_BYTES:
                print("SUCCESS")
                return 0
            last_error = (
                f"criteria not met: status={status} title={title!r} "
                f"body_bytes={body_len}"
            )
        except urllib.error.HTTPError as exc:
            last_error = f"http error {exc.code}"
            print(f"ATTEMPT {attempt}: HTTPError status={exc.code}")
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            print(f"ATTEMPT {attempt}: ERROR {last_error}")

        time.sleep(POLL_INTERVAL_SECONDS)

    print(f"FAILURE {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

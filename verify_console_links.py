#!/usr/bin/env python3
import re
import sys

import requests


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7788/"
    response = requests.get(base_url, timeout=5)
    response.raise_for_status()

    links = [match[1] for match in re.findall(r'href=(["\'])(/app[^"\']*)\1', response.text)]
    bad_links = [link for link in links if not re.fullmatch(r'/app\?auth=(login|register)', link)]

    if not links:
        print("FAIL: no /app links found on homepage")
        return 1

    if bad_links:
        print("FAIL: found invalid console links:")
        for link in bad_links:
            print(link)
        return 1

    print(f"PASS: verified {len(links)} console links")
    for link in links:
        print(link)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import contextlib
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "tests" / "artifacts"
SNIPPET_PATH = ARTIFACTS_DIR / "no_token_auth_snippet.html"
REPORT_PATH = ARTIFACTS_DIR / "no_token_access_report.txt"


def find_free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def wait_for_health(base_url, timeout_seconds=20):
    deadline = time.perf_counter() + timeout_seconds
    last_error = None
    while time.perf_counter() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/api/health", timeout=1.5) as response:
                body = response.read().decode("utf-8")
                if response.status == 200 and '"status":"ok"' in body.replace(" ", ""):
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Server health check timed out: {last_error}")


def fetch_html(url):
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=10) as response:
        html = response.read().decode("utf-8")
        elapsed_ms = (time.perf_counter() - started) * 1000
        return response.status, elapsed_ms, html


def extract_auth_snippet(html):
    start = html.find('<div id="page-auth"')
    end = html.find('<div id="app-shell"')
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Unable to extract auth snippet from /app response")
    snippet = html[start:end].strip()
    if "handleRegister" not in snippet:
        raise RuntimeError("Auth snippet does not contain 'handleRegister'")
    forbidden_ids = ["page-list", "meeting-grid", "page-detail", "agent-list", "detail-title"]
    present = [item for item in forbidden_ids if item in snippet]
    if present:
        raise RuntimeError(f"Auth snippet still contains meeting IDs: {present}")
    return snippet


def run_browser_checks(base_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        started = time.perf_counter()
        page.goto(f"{base_url}/app#register", wait_until="networkidle")
        navigation_ms = (time.perf_counter() - started) * 1000

        dom_probe = """
            () => {
                const displayOf = (id) => {
                    const node = document.getElementById(id);
                    return node ? getComputedStyle(node).display : null;
                };
                return {
                    hash: window.location.hash,
                    pageAuthExists: !!document.getElementById('page-auth'),
                    pageListExists: !!document.getElementById('page-list'),
                    pageDetailExists: !!document.getElementById('page-detail'),
                    pageAuthDisplay: displayOf('page-auth'),
                    pageListDisplay: displayOf('page-list'),
                    pageDetailDisplay: displayOf('page-detail'),
                    appShellDisplay: displayOf('app-shell'),
                    authShellDisplay: displayOf('auth-shell'),
                    authRegisterDisplay: displayOf('auth-register'),
                    authLoginDisplay: displayOf('auth-login')
                };
            }
        """

        initial = page.evaluate(
            dom_probe
        )

        forced_list = page.evaluate(
            """
            () => {
                const displayOf = (id) => {
                    const node = document.getElementById(id);
                    return node ? getComputedStyle(node).display : null;
                };
                showPage('list');
                return {
                    pageAuthDisplay: displayOf('page-auth'),
                    pageListDisplay: displayOf('page-list'),
                    pageDetailDisplay: displayOf('page-detail'),
                    appShellDisplay: displayOf('app-shell')
                };
            }
            """
        )

        forced_detail = page.evaluate(
            """
            () => {
                const displayOf = (id) => {
                    const node = document.getElementById(id);
                    return node ? getComputedStyle(node).display : null;
                };
                showPage('detail');
                return {
                    pageAuthDisplay: displayOf('page-auth'),
                    pageListDisplay: displayOf('page-list'),
                    pageDetailDisplay: displayOf('page-detail'),
                    appShellDisplay: displayOf('app-shell')
                };
            }
            """
        )
        browser.close()

    return navigation_ms, initial, forced_list, forced_detail


def main():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    port = find_free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"
    base_url = f"http://127.0.0.1:{port}"

    server = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_health(base_url)
        status_code, fetch_ms, html = fetch_html(f"{base_url}/app#register")
        snippet = extract_auth_snippet(html)
        SNIPPET_PATH.write_text(snippet, encoding="utf-8")

        navigation_ms, initial, forced_list, forced_detail = run_browser_checks(base_url)

        checks = {
            "http_status_200": status_code == 200,
            "initial_hash_register": initial["hash"] == "#register",
            "initial_auth_visible": initial["pageAuthDisplay"] == "flex",
            "initial_list_hidden": initial["pageListDisplay"] == "none",
            "initial_detail_hidden": initial["pageDetailDisplay"] == "none",
            "initial_app_shell_hidden": initial["appShellDisplay"] == "none",
            "initial_auth_shell_visible": initial["authShellDisplay"] == "block",
            "register_tab_visible": initial["authRegisterDisplay"] == "flex",
            "login_tab_hidden": initial["authLoginDisplay"] == "none",
            "forced_list_still_auth_only": forced_list["pageAuthDisplay"] == "flex"
            and forced_list["pageListDisplay"] == "none"
            and forced_list["pageDetailDisplay"] == "none"
            and forced_list["appShellDisplay"] == "none",
            "forced_detail_still_auth_only": forced_detail["pageAuthDisplay"] == "flex"
            and forced_detail["pageListDisplay"] == "none"
            and forced_detail["pageDetailDisplay"] == "none"
            and forced_detail["appShellDisplay"] == "none",
        }

        failed = [name for name, ok in checks.items() if not ok]
        report_lines = [
            f"base_url={base_url}",
            f"http_status={status_code}",
            f"fetch_elapsed_ms={fetch_ms:.2f}",
            f"browser_navigation_ms={navigation_ms:.2f}",
            f"snippet_path={SNIPPET_PATH}",
            f"report_path={REPORT_PATH}",
            f"initial_dom={initial}",
            f"forced_list_dom={forced_list}",
            f"forced_detail_dom={forced_detail}",
            f"checks={checks}",
            f"failed_checks={failed}",
        ]
        REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

        if failed:
            raise RuntimeError(f"No-token access check failed: {failed}")

        print("\n".join(report_lines))
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    main()

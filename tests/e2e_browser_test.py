import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT_DIR / "server.py"
EVIDENCE_PATH = ROOT_DIR / "tests" / "evidence_register.png"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 7790
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {host}:{port}")


def start_server() -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PORT"] = str(SERVER_PORT)
    return subprocess.Popen(
        [sys.executable, str(SERVER_PATH)],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def stop_server(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def read_server_output(proc: subprocess.Popen[str]) -> str:
    output = ""
    if proc.stdout:
        try:
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                output += line
        except Exception:
            pass
    return output


def assert_png_file(path: Path) -> None:
    data = path.read_bytes()
    if len(data) <= 8:
        raise AssertionError(f"Screenshot is unexpectedly small: {path}")
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"Screenshot is not a PNG file: {path}")


def main() -> int:
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if EVIDENCE_PATH.exists():
        EVIDENCE_PATH.unlink()

    server = start_server()
    console_messages: list[str] = []
    page_errors: list[str] = []

    try:
        wait_for_port(SERVER_HOST, SERVER_PORT)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            page.on("console", lambda msg: console_messages.append(f"[console:{msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: page_errors.append(f"[pageerror] {err}"))

            page.goto(f"{SERVER_URL}/", wait_until="domcontentloaded", timeout=15000)
            page.get_by_role("link", name="开始免费使用").first.click()
            page.wait_for_url(f"{SERVER_URL}/app?auth=register", wait_until="domcontentloaded", timeout=15000)

            register_panel = page.locator("#auth-register")
            register_panel.wait_for(state="visible", timeout=15000)

            box = register_panel.bounding_box()
            if not box or box["width"] <= 0 or box["height"] <= 0:
                raise AssertionError(f"#auth-register has invalid bounding box: {box}")

            register_panel.screenshot(path=str(EVIDENCE_PATH))
            assert_png_file(EVIDENCE_PATH)

            browser.close()

        if page_errors:
            raise AssertionError("Page errors detected:\n" + "\n".join(page_errors))

        severe_console = [
            message for message in console_messages
            if "[console:error]" in message or "[console:warning]" in message
        ]
        if severe_console:
            raise AssertionError("Console issues detected:\n" + "\n".join(severe_console))

        print(f"Playwright evidence saved to {EVIDENCE_PATH}")
        print("Playwright 自检截图已生成，确认注册框 100% 可见")
        return 0
    except (AssertionError, TimeoutError, PlaywrightTimeoutError) as exc:
        print(f"E2E browser test failed: {exc}", file=sys.stderr)
        if console_messages:
            print("\n".join(console_messages), file=sys.stderr)
        if page_errors:
            print("\n".join(page_errors), file=sys.stderr)
        return 1
    finally:
        stop_server(server)
        server_output = read_server_output(server).strip()
        if server_output:
            print(server_output)


if __name__ == "__main__":
    raise SystemExit(main())

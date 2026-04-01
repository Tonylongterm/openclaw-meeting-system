import contextlib
import html.parser
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import requests


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_LOG = ROOT / "tests" / "TEST_EVIDENCE.log"
SERVER_START_TIMEOUT_SECONDS = 20


class LinkCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href")
        if href:
            self.links.append(href)


@dataclass
class CaseResult:
    name: str
    method: str
    url: str
    status_code: int
    elapsed_ms: float
    body_length: int
    detail: str


def assert_status(response, expected, context):
    if response.status_code != expected:
        raise AssertionError(
            f"{context}: expected {expected}, got {response.status_code}, body={response.text}"
        )


def assert_contains(text, needle, context):
    if needle not in text:
        raise AssertionError(f"{context}: missing {needle!r}")


def assert_not_contains(text, needle, context):
    if needle in text:
        raise AssertionError(f"{context}: unexpected {needle!r}")


def find_free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def write_evidence(results, status, failure_message=""):
    lines = [
        f"QA_STATUS={status}",
        f"GENERATED_AT={time.strftime('%Y-%m-%d %H:%M:%S %z')}",
    ]
    if failure_message:
        lines.append(f"FAILURE={failure_message}")
    lines.append("")

    for index, result in enumerate(results, start=1):
        lines.extend(
            [
                f"[CASE {index}] {result.name}",
                f"method={result.method}",
                f"url={result.url}",
                f"status_code={result.status_code}",
                f"elapsed_ms={result.elapsed_ms:.2f}",
                f"body_length={result.body_length}",
                f"detail={result.detail}",
                "",
            ]
        )

    EVIDENCE_LOG.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def wait_for_server(base_url):
    deadline = time.time() + SERVER_START_TIMEOUT_SECONDS
    last_error = None
    while time.time() < deadline:
        try:
            response = requests.get(f"{base_url}/api/health", timeout=1.5)
            if response.status_code == 200:
                return
            last_error = f"unexpected health status {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(0.2)
    raise RuntimeError(f"server did not become ready within {SERVER_START_TIMEOUT_SECONDS}s: {last_error}")


def measure_request(results, name, session, method, url, *, stream=False, timeout=5, **kwargs):
    started = time.perf_counter()
    response = session.request(method, url, stream=stream, timeout=timeout, **kwargs)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if stream:
        chunk = next(response.iter_content(chunk_size=None))
        body_length = len(chunk)
        detail = "stream_first_chunk"
        response._qa_body_text = chunk.decode("utf-8", errors="replace")
        response.close()
    else:
        body = response.text
        body_length = len(response.content)
        detail = "full_body"
        response._qa_body_text = body

    results.append(
        CaseResult(
            name=name,
            method=method.upper(),
            url=url,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            body_length=body_length,
            detail=detail,
        )
    )
    return response


def register_user(results, session, base_url, email, password, name):
    response = measure_request(
        results,
        f"register:{email}",
        session,
        "POST",
        f"{base_url}/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert_status(response, 201, f"register {email}")


def login_user(results, session, base_url, email, password):
    response = measure_request(
        results,
        f"login:{email}",
        session,
        "POST",
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password},
    )
    assert_status(response, 200, f"login {email}")


def verify_homepage_auth_links(results, session, base_url):
    response = measure_request(results, "homepage", session, "GET", f"{base_url}/")
    assert_status(response, 200, "homepage")

    collector = LinkCollector()
    collector.feed(response._qa_body_text)
    if not collector.links:
        raise AssertionError("homepage: no links found")

    invalid_links = []
    for href in collector.links:
        parsed = urlsplit(href)
        if parsed.scheme == "javascript":
            continue
        if "?auth=" not in href:
            invalid_links.append(href)

    if invalid_links:
        raise AssertionError(f"homepage links missing ?auth=: {invalid_links}")


def run():
    results = []
    failure_message = ""
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["PORT"] = str(port)

    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_server(base_url)

        browser = requests.Session()
        anonymous = requests.Session()
        owner = requests.Session()
        other = requests.Session()

        verify_homepage_auth_links(results, browser, base_url)

        app_register = measure_request(
            results,
            "app_auth_register",
            browser,
            "GET",
            f"{base_url}/app?auth=register",
        )
        assert_status(app_register, 200, "app register page")
        assert_contains(app_register._qa_body_text, 'id="auth-register"', "app register form exists")
        assert_not_contains(app_register._qa_body_text, 'id="modal-create"', "app register isolates modal")

        auth_me_unauthorized = measure_request(
            results,
            "auth_me_requires_token",
            anonymous,
            "GET",
            f"{base_url}/api/auth/me",
        )
        assert_status(auth_me_unauthorized, 401, "auth/me requires token")

        meetings_unauthorized = measure_request(
            results,
            "meetings_requires_token",
            anonymous,
            "GET",
            f"{base_url}/api/meetings",
        )
        assert_status(meetings_unauthorized, 401, "meetings requires token")

        password = "pass123"
        register_user(results, owner, base_url, "owner@example.com", password, "Owner")
        login_user(results, owner, base_url, "owner@example.com", password)
        register_user(results, other, base_url, "other@example.com", password, "Other")
        login_user(results, other, base_url, "other@example.com", password)

        me = measure_request(results, "owner_auth_me", owner, "GET", f"{base_url}/api/auth/me")
        assert_status(me, 200, "owner auth/me")
        assert_contains(me._qa_body_text, "owner@example.com", "owner auth/me payload")

        create = measure_request(
            results,
            "create_meeting",
            owner,
            "POST",
            f"{base_url}/api/meetings",
            json={"title": "Q2 架构会", "topic": "是否升级平台", "max_rounds": 2},
        )
        assert_status(create, 200, "create meeting")
        meeting = create.json()["meeting"]
        meeting_id = meeting["id"]
        invite_code = meeting["invite_code"]

        listed = measure_request(results, "list_meetings", owner, "GET", f"{base_url}/api/meetings")
        assert_status(listed, 200, "list meetings")
        assert_contains(listed._qa_body_text, meeting_id, "meeting listed")

        detail_requires_token = measure_request(
            results,
            "meeting_detail_requires_token",
            anonymous,
            "GET",
            f"{base_url}/api/meetings/{meeting_id}",
        )
        assert_status(detail_requires_token, 401, "meeting detail requires token")

        start_requires_token = measure_request(
            results,
            "meeting_start_requires_token",
            anonymous,
            "POST",
            f"{base_url}/api/meetings/{meeting_id}/start",
        )
        assert_status(start_requires_token, 401, "meeting start requires token")

        stream_requires_token = measure_request(
            results,
            "meeting_stream_requires_token",
            anonymous,
            "GET",
            f"{base_url}/api/meetings/{meeting_id}/stream",
        )
        assert_status(stream_requires_token, 401, "meeting stream requires token")

        cross_user_detail = measure_request(
            results,
            "cross_user_detail_forbidden",
            other,
            "GET",
            f"{base_url}/api/meetings/{meeting_id}",
        )
        assert_status(cross_user_detail, 403, "cross-user detail forbidden")

        cross_user_stream = measure_request(
            results,
            "cross_user_stream_forbidden",
            other,
            "GET",
            f"{base_url}/api/meetings/{meeting_id}/stream",
        )
        assert_status(cross_user_stream, 403, "cross-user stream forbidden")

        start_without_host = measure_request(
            results,
            "start_requires_host",
            owner,
            "POST",
            f"{base_url}/api/meetings/{meeting_id}/start",
        )
        assert_status(start_without_host, 400, "start requires host")

        join = measure_request(
            results,
            "join_by_invite_code",
            browser,
            "POST",
            f"{base_url}/api/join",
            json={"invite_code": invite_code, "name": "主持龙虾", "role": "架构师"},
        )
        assert_status(join, 200, "join by invite code")

        patch = measure_request(
            results,
            "set_host_agent",
            owner,
            "PATCH",
            f"{base_url}/api/meetings/{meeting_id}",
            json={"host_agent": "主持龙虾", "max_rounds": 2, "topic": "是否升级平台"},
        )
        assert_status(patch, 200, "set host agent")

        stream_owner = measure_request(
            results,
            "owner_stream_allowed",
            owner,
            "GET",
            f"{base_url}/api/meetings/{meeting_id}/stream",
            stream=True,
            timeout=10,
        )
        assert_status(stream_owner, 200, "owner stream allowed")
        assert_contains(stream_owner._qa_body_text, '"type": "init"', "stream init payload")

        start = measure_request(
            results,
            "start_meeting",
            owner,
            "POST",
            f"{base_url}/api/meetings/{meeting_id}/start",
        )
        assert_status(start, 200, "start meeting")
        assert_contains(start._qa_body_text, '"success":true', "start success payload")

        write_evidence(results, "PASS")
        print("证据已锁定，QA测试 100% 通过")
    except Exception as exc:
        failure_message = str(exc)
        write_evidence(results, "FAIL", failure_message)
        raise
    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait(timeout=5)


if __name__ == "__main__":
    run()

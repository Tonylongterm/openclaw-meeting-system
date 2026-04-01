import re
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import app, invite_to_meeting, meetings, msg_queues, users


def assert_status(response, expected, context):
    if response.status_code != expected:
        raise AssertionError(f"{context}: expected {expected}, got {response.status_code}, body={response.get_data(as_text=True)}")


def assert_contains(text, needle, context):
    if needle not in text:
        raise AssertionError(f"{context}: missing {needle!r}")


def assert_regex(text, pattern, context):
    if not re.search(pattern, text, re.S):
        raise AssertionError(f"{context}: pattern not found {pattern!r}")


def reset_state():
    users.clear()
    meetings.clear()
    invite_to_meeting.clear()
    msg_queues.clear()


def register_and_login(client, email, name):
    password = "pass123"
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert_status(response, 201, f"register {email}")

    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert_status(response, 200, f"login {email}")
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def run():
    reset_state()

    with app.test_client() as client:
        home = client.get("/")
        assert_status(home, 200, "homepage")
        home_html = home.get_data(as_text=True)
        assert_contains(home_html, 'href="/app?auth=login"', "homepage login route")
        assert_contains(home_html, 'href="/app?auth=register"', "homepage register route")

        app_page = client.get("/app?auth=register")
        assert_status(app_page, 200, "app page")
        app_html = app_page.get_data(as_text=True)
        assert_contains(app_html, 'id="auth-shell"', "auth shell exists")
        assert_contains(app_html, 'id="app-shell" class="shell" style="display: none;"', "app shell hidden by default")
        assert_contains(app_html, "setShellVisibility(", "shell visibility control exists")
        assert_contains(app_html, "CREATE_MODAL_TEMPLATE = String.raw`", "create modal template isolated in script")
        assert_contains(app_html, "ensureCreateModal()", "create modal injected on demand")
        assert_contains(app_html, "document.getElementById('modal-create')", "modal leak guard watches DOM")
        assert_contains(
            app_html,
            "new URLSearchParams(window.location.search).get('auth') === 'register'",
            "register route state parsing exists",
        )
        assert "id=\"modal-create\"" not in app_html.split("<script>", 1)[0], "modal must not exist in unauthenticated markup"

        assert_status(client.get("/api/auth/me"), 401, "auth/me requires token")
        assert_status(client.get("/api/meetings"), 401, "meeting list requires token")

        owner_headers = register_and_login(client, "owner@example.com", "Owner")
        other_headers = register_and_login(client, "other@example.com", "Other")

        me = client.get("/api/auth/me", headers=owner_headers)
        assert_status(me, 200, "auth/me owner")
        assert_contains(me.get_data(as_text=True), "owner@example.com", "auth/me payload")

        create = client.post(
            "/api/meetings",
            headers=owner_headers,
            json={"title": "Q2 架构会", "topic": "是否升级平台", "max_rounds": 2},
        )
        assert_status(create, 200, "create meeting")
        meeting = create.get_json()["meeting"]
        meeting_id = meeting["id"]
        invite_code = meeting["invite_code"]

        list_response = client.get("/api/meetings", headers=owner_headers)
        assert_status(list_response, 200, "list meetings")
        assert_contains(list_response.get_data(as_text=True), meeting_id, "meeting listed for owner")

        assert_status(client.get(f"/api/meetings/{meeting_id}"), 401, "meeting detail requires token")
        assert_status(client.post(f"/api/meetings/{meeting_id}/start"), 401, "meeting start requires token")
        assert_status(client.get(f"/api/meetings/{meeting_id}/stream"), 401, "meeting stream requires token")

        assert_status(
            client.get(f"/api/meetings/{meeting_id}", headers=other_headers),
            403,
            "cross-user detail forbidden",
        )
        assert_status(
            client.get(f"/api/meetings/{meeting_id}/stream?token={other_headers['Authorization'].split(' ', 1)[1]}"),
            403,
            "cross-user stream forbidden",
        )

        start_without_host = client.post(f"/api/meetings/{meeting_id}/start", headers=owner_headers)
        assert_status(start_without_host, 400, "start requires host")

        join = client.post(
            "/api/join",
            json={"invite_code": invite_code, "name": "主持龙虾", "role": "架构师"},
        )
        assert_status(join, 200, "join by invite code")

        patch = client.patch(
            f"/api/meetings/{meeting_id}",
            headers=owner_headers,
            json={"host_agent": "主持龙虾", "max_rounds": 2, "topic": "是否升级平台"},
        )
        assert_status(patch, 200, "set host agent")

        stream_response = client.get(
            f"/api/meetings/{meeting_id}/stream?token={owner_headers['Authorization'].split(' ', 1)[1]}",
            buffered=False,
        )
        assert_status(stream_response, 200, "owner stream allowed")
        with closing(stream_response):
            first_event = next(stream_response.response).decode("utf-8")
            assert_contains(first_event, '"type": "init"', "stream init payload")

        start = client.post(f"/api/meetings/{meeting_id}/start", headers=owner_headers)
        assert_status(start, 200, "start meeting")
        assert_contains(start.get_data(as_text=True), '"success":true', "start success payload")

    print("QA checks passed.")


if __name__ == "__main__":
    run()

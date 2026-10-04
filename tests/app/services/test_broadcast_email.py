"""Unit tests for app.services.broadcast_email.send_broadcast_emails.

The image-rewriting helpers (_make_images_responsive, _render_markdown_to_html)
are already covered by tests/test_broadcast_email_images.py; this file targets
the previously untested delivery orchestration: template load failure, user
fetch failure, email filtering/dedup, per-user render and send, and the
success/failure counters. AdminService, the Jinja env, and _send_email are
patched in the broadcast_email module namespace.
"""

from unittest.mock import MagicMock, patch

from app.services import broadcast_email as mod


def _settings():
    return MagicMock(
        ses_sender_email="noreply@example.com",
        ses_region="us-east-2",
    )


def _broadcast(**over):
    base = {
        "title": "Big News",
        "message": "Hello **world**",
        "link": "https://example.com/post",
        "created_by": "admin1",
    }
    base.update(over)
    return base


def _patch_template(render_return="<html>body</html>", render_side_effect=None):
    template = MagicMock()
    if render_side_effect is not None:
        template.render.side_effect = render_side_effect
    else:
        template.render.return_value = render_return
    jinja_env = MagicMock()
    jinja_env.get_template.return_value = template
    return jinja_env, template


class TestSendBroadcastEmails:
    def test_template_load_failure_returns_early(self):
        jinja_env = MagicMock()
        jinja_env.get_template.side_effect = RuntimeError("missing template")
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService") as AdminSvc,
            patch.object(mod, "_send_email") as send,
        ):
            mod.send_broadcast_emails(_broadcast(), _settings())
        # Bailed before touching users or sending
        AdminSvc.assert_not_called()
        send.assert_not_called()

    def test_user_fetch_failure_returns_early(self):
        jinja_env, _ = _patch_template()
        svc = MagicMock()
        svc.get_all_registered_users.side_effect = RuntimeError("dynamo down")
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(mod, "_send_email") as send,
        ):
            mod.send_broadcast_emails(_broadcast(), _settings())
        send.assert_not_called()

    def test_no_users_with_email_returns_early(self):
        jinja_env, _ = _patch_template()
        svc = MagicMock()
        svc.get_all_registered_users.return_value = [
            {"email": ""},
            {"username": "noemail"},
        ]
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(mod, "_send_email") as send,
        ):
            mod.send_broadcast_emails(_broadcast(), _settings())
        send.assert_not_called()

    def test_sends_to_each_unique_user_and_dedups(self):
        jinja_env, template = _patch_template()
        svc = MagicMock()
        svc.get_all_registered_users.return_value = [
            {"email": "Alice@Example.com", "username": "alice"},
            {"email": "alice@example.com", "username": "dupe"},  # dup (case-insens)
            {"email": "bob@example.com", "github_username": "bobgh"},
            {"email": "", "username": "noemail"},  # filtered
        ]
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(mod, "_send_email", return_value=True) as send,
        ):
            mod.send_broadcast_emails(_broadcast(), _settings())
        # Only two unique emails sent
        assert send.call_count == 2
        sent_to = {c.kwargs["to_email"] for c in send.call_args_list}
        assert sent_to == {"Alice@Example.com", "bob@example.com"}
        # Subject is the title; sender/region come from settings
        first = send.call_args_list[0].kwargs
        assert first["subject"] == "Big News"
        assert first["sender_email"] == "noreply@example.com"
        assert first["ses_region"] == "us-east-2"
        # username falls back to github_username for the second user
        rendered_usernames = {
            c.kwargs["username"] for c in template.render.call_args_list
        }
        assert "alice" in rendered_usernames
        assert "bobgh" in rendered_usernames

    def test_render_failure_skips_that_user_only(self):
        jinja_env, template = _patch_template()
        # First render raises, second succeeds
        template.render.side_effect = [RuntimeError("bad template"), "<html>ok</html>"]
        svc = MagicMock()
        svc.get_all_registered_users.return_value = [
            {"email": "a@example.com", "username": "a"},
            {"email": "b@example.com", "username": "b"},
        ]
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(mod, "_send_email", return_value=True) as send,
        ):
            mod.send_broadcast_emails(_broadcast(), _settings())
        # Only the second user actually got an email
        assert send.call_count == 1
        assert send.call_args.kwargs["to_email"] == "b@example.com"

    def test_send_returns_false_counts_as_failure(self):
        jinja_env, _ = _patch_template()
        svc = MagicMock()
        svc.get_all_registered_users.return_value = [
            {"email": "a@example.com", "username": "a"},
        ]
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(mod, "_send_email", return_value=False) as send,
        ):
            # Should complete without raising even when send reports failure
            mod.send_broadcast_emails(_broadcast(), _settings())
        send.assert_called_once()

    def test_send_exception_caught_and_continues(self):
        jinja_env, _ = _patch_template()
        svc = MagicMock()
        svc.get_all_registered_users.return_value = [
            {"email": "a@example.com", "username": "a"},
            {"email": "b@example.com", "username": "b"},
        ]
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(
                mod, "_send_email", side_effect=[RuntimeError("ses err"), True]
            ) as send,
        ):
            mod.send_broadcast_emails(_broadcast(), _settings())
        # Both attempted despite the first raising
        assert send.call_count == 2

    def test_markdown_message_rendered_to_html_once(self):
        jinja_env, template = _patch_template()
        svc = MagicMock()
        svc.get_all_registered_users.return_value = [
            {"email": "a@example.com", "username": "a"},
            {"email": "b@example.com", "username": "b"},
        ]
        with (
            patch.object(mod, "_jinja_env", jinja_env),
            patch.object(mod, "AdminService", return_value=svc),
            patch.object(mod, "_send_email", return_value=True),
            patch.object(
                mod, "_render_markdown_to_html", return_value="<p>RENDERED</p>"
            ) as render_md,
        ):
            mod.send_broadcast_emails(_broadcast(message="**hi**"), _settings())
        # Markdown rendered exactly once, result reused for every recipient
        render_md.assert_called_once_with("**hi**")
        for call in template.render.call_args_list:
            assert call.kwargs["message_html"] == "<p>RENDERED</p>"

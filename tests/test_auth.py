"""Tests for the team-mode user authentication system."""

import os
import tempfile

import pytest

from polyclash.util.auth import UserStore


@pytest.fixture
def user_store():
    """Create a UserStore with a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = UserStore(db_path=path)
    yield store
    os.unlink(path)


@pytest.fixture
def admin_store(user_store):
    """UserStore with an admin account."""
    user_store.ensure_admin("admin", "adminpass")
    return user_store


class TestInviteCodes:
    def test_create_invite(self, user_store):
        code = user_store.create_invite()
        assert len(code) > 0

    def test_list_invites(self, user_store):
        code = user_store.create_invite()
        invites = user_store.list_invites()
        assert len(invites) == 1
        assert invites[0]["code"] == code
        assert invites[0]["used_by"] is None

    def test_multiple_invites(self, user_store):
        codes = [user_store.create_invite() for _ in range(5)]
        invites = user_store.list_invites()
        assert len(invites) == 5
        assert set(inv["code"] for inv in invites) == set(codes)


class TestRegistration:
    def test_register_success(self, user_store):
        code = user_store.create_invite()
        token = user_store.register("alice", "password123", code)
        assert len(token) > 0

    def test_register_invalid_invite(self, user_store):
        with pytest.raises(ValueError, match="Invalid invite code"):
            user_store.register("alice", "password123", "bogus")

    def test_register_used_invite(self, user_store):
        code = user_store.create_invite()
        user_store.register("alice", "password123", code)
        with pytest.raises(ValueError, match="already used"):
            user_store.register("bob", "password456", code)

    def test_register_duplicate_username(self, user_store):
        code1 = user_store.create_invite()
        code2 = user_store.create_invite()
        user_store.register("alice", "password123", code1)
        with pytest.raises(ValueError, match="already taken"):
            user_store.register("alice", "password456", code2)

    def test_register_empty_username(self, user_store):
        code = user_store.create_invite()
        with pytest.raises(ValueError, match="required"):
            user_store.register("", "password123", code)

    def test_register_short_username(self, user_store):
        code = user_store.create_invite()
        with pytest.raises(ValueError, match="2-20"):
            user_store.register("a", "password123", code)

    def test_register_short_password(self, user_store):
        code = user_store.create_invite()
        with pytest.raises(ValueError, match="at least 4"):
            user_store.register("alice", "abc", code)

    def test_register_marks_invite_used(self, user_store):
        code = user_store.create_invite()
        user_store.register("alice", "password123", code)
        invites = user_store.list_invites()
        assert invites[0]["used_by"] == "alice"


class TestLogin:
    def test_login_success(self, user_store):
        code = user_store.create_invite()
        user_store.register("alice", "password123", code)
        token = user_store.login("alice", "password123")
        assert len(token) > 0

    def test_login_wrong_password(self, user_store):
        code = user_store.create_invite()
        user_store.register("alice", "password123", code)
        with pytest.raises(ValueError, match="Invalid username or password"):
            user_store.login("alice", "wrongpassword")

    def test_login_nonexistent_user(self, user_store):
        with pytest.raises(ValueError, match="Invalid username or password"):
            user_store.login("nobody", "password")


class TestSession:
    def test_validate_session(self, user_store):
        code = user_store.create_invite()
        token = user_store.register("alice", "password123", code)
        assert user_store.validate_session(token) == "alice"

    def test_validate_invalid_session(self, user_store):
        assert user_store.validate_session("bogus_token") is None

    def test_logout(self, user_store):
        code = user_store.create_invite()
        token = user_store.register("alice", "password123", code)
        user_store.logout(token)
        assert user_store.validate_session(token) is None


class TestAdmin:
    def test_ensure_admin(self, user_store):
        user_store.ensure_admin("admin", "secret")
        assert user_store.is_admin("admin") == True

    def test_ensure_admin_idempotent(self, user_store):
        user_store.ensure_admin("admin", "secret")
        user_store.ensure_admin("admin", "different")
        # First password should still work
        token = user_store.login("admin", "secret")
        assert len(token) > 0

    def test_regular_user_not_admin(self, user_store):
        code = user_store.create_invite()
        user_store.register("alice", "password123", code)
        assert user_store.is_admin("alice") == False

    def test_list_users(self, admin_store):
        code = admin_store.create_invite()
        admin_store.register("alice", "password123", code)
        users = admin_store.list_users()
        usernames = [u["username"] for u in users]
        assert "admin" in usernames
        assert "alice" in usernames
        assert len(users) == 2

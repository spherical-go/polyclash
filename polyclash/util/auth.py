"""User authentication for team-mode deployment.

Provides invite-code registration, password login, and session-token
management backed by SQLite (zero external dependencies).
"""

from __future__ import annotations

import os
import secrets
import sqlite3
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from polyclash.util.logging import logger

INVITE_CODE_LENGTH = 12
SESSION_TOKEN_LENGTH = 48

# Default DB path; override via POLYCLASH_AUTH_DB env var.
_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "..", "polyclash_users.db")


class UserStore:
    """SQLite-backed user store with invite codes and sessions."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path: str = (
            db_path or os.environ.get("POLYCLASH_AUTH_DB") or _DEFAULT_DB
        )
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS invite_codes (
                code TEXT PRIMARY KEY,
                created_by TEXT,
                used_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            );
            """)
        conn.commit()
        conn.close()

    # ── Admin / invite codes ──────────────────────────────

    def create_invite(self, created_by: str = "admin") -> str:
        """Generate a new invite code."""
        code = secrets.token_urlsafe(INVITE_CODE_LENGTH)
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO invite_codes (code, created_by) VALUES (?, ?)",
            (code, created_by),
        )
        conn.commit()
        conn.close()
        return code

    def list_invites(self) -> list[dict]:
        """Return all invite codes with usage status."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT code, created_by, used_by, created_at FROM invite_codes"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def ensure_admin(self, username: str, password: str) -> None:
        """Create admin user if it doesn't exist yet."""
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not existing:
            pw_hash = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                (username, pw_hash),
            )
            conn.commit()
            logger.info(f"Admin user '{username}' created")
        conn.close()

    # ── Registration ──────────────────────────────────────

    def register(self, username: str, password: str, invite_code: str) -> str:
        """Register a new user with an invite code. Returns session token."""
        if not username or not password:
            raise ValueError("Username and password are required")
        if len(username) < 2 or len(username) > 20:
            raise ValueError("Username must be 2-20 characters")
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters")

        conn = self._get_conn()
        # Validate invite code
        invite = conn.execute(
            "SELECT code, used_by FROM invite_codes WHERE code = ?", (invite_code,)
        ).fetchone()
        if not invite:
            conn.close()
            raise ValueError("Invalid invite code")
        if invite["used_by"]:
            conn.close()
            raise ValueError("Invite code already used")

        # Check username uniqueness
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            conn.close()
            raise ValueError("Username already taken")

        # Create user and consume invite
        pw_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash),
        )
        conn.execute(
            "UPDATE invite_codes SET used_by = ? WHERE code = ?",
            (username, invite_code),
        )

        # Auto-login: create session
        token = secrets.token_hex(SESSION_TOKEN_LENGTH // 2)
        conn.execute(
            "INSERT INTO sessions (token, username) VALUES (?, ?)",
            (token, username),
        )
        conn.commit()
        conn.close()

        logger.info(f"User '{username}' registered")
        return token

    # ── Login / logout ────────────────────────────────────

    def login(self, username: str, password: str) -> str:
        """Authenticate and return a session token."""
        conn = self._get_conn()
        user = conn.execute(
            "SELECT username, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            conn.close()
            raise ValueError("Invalid username or password")

        token = secrets.token_hex(SESSION_TOKEN_LENGTH // 2)
        conn.execute(
            "INSERT INTO sessions (token, username) VALUES (?, ?)",
            (token, username),
        )
        conn.commit()
        conn.close()
        return token

    def logout(self, token: str) -> None:
        """Invalidate a session token."""
        conn = self._get_conn()
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()

    # ── Session validation ────────────────────────────────

    def validate_session(self, token: str) -> Optional[str]:
        """Return username if session is valid, else None."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT username FROM sessions WHERE token = ?", (token,)
        ).fetchone()
        conn.close()
        return row["username"] if row else None

    def is_admin(self, username: str) -> bool:
        """Check if a user has admin privileges."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT is_admin FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        return bool(row and row["is_admin"])

    def list_users(self) -> list[dict]:
        """Return all registered users (without password hashes)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT username, is_admin, created_at FROM users"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

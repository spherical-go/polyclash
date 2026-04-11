# Team Scenario — Implementation Complete

## Goal
Small self-hosted game server (like Minecraft) with 8 rooms, invited users, one-click cloud deploy.

## Phase 1: User System ✅
- `polyclash/util/auth.py` — SQLite UserStore, invite codes, sessions
- Auth endpoints: register, login, logout, me, invite, invites, users
- 21 tests in `tests/test_auth.py`

## Phase 2: Room Management + Lobby ✅
- Room limit, lobby page (`web/lobby.html` + JS + CSS)
- Lobby endpoints: list, create, join
- `polyclash team` CLI subcommand
- 22 tests in `tests/test_team.py`

## Phase 3: Board Persistence ✅
- `Board.to_dict()` / `Board.from_dict()` — full roundtrip serialization
- `DataStorage.save_board()` / `load_board()` — Memory + Redis
- `_persist_board()` after every state change, `restore_boards()` on startup
- 14 tests in `tests/test_board_persistence.py`

## Phase 4: Cloud Deployment ✅
- Dockerfile: team mode default, `/data` volume, `CMD ["polyclash", "team"]`
- docker-compose.yml: team + Redis, env-var config, persistent volume
- render.yaml: disk mount, auto-generated admin pass
- fly.toml: volume mount, team mode env vars
- railway.json: Dockerfile builder
- CLI: all team flags read from env vars (POLYCLASH_MAX_ROOMS, POLYCLASH_ADMIN_PASS, etc.)
- Deployment docs updated: Mode 3 (Team Server), Mode 4 (One-Click Cloud)
- README.md updated with all CLI subcommands
- .dockerignore updated

## Test Results
374 passed, 1 skipped — mypy 0 errors, ruff clean, black formatted

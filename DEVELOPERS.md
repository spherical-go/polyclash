# PolyClash Developer Handbook

This handbook sets the baseline for development environment, coding standards, quality controls (QC), submission workflow, and CI gates to keep PolyClash maintainable and consistent.

Table of Contents
- Environment and Dependencies
- Code Style and Static Checks
- Type Hints (PEP 561 / mypy)
- Tests and Coverage
- Git/PR Workflow
- CI/CD and Branch Protection
- Module-Specific Notes
- Performance and Stability
- Command Cheatsheet

## Environment and Dependencies

- Python: >= 3.10
- Dependency management: uv (used in CI as well)

One-time setup:
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
```

Local checks:
```bash
pre-commit run --all-files
mypy polyclash
pytest -q
```

## Code Style and Static Checks

- All local checks are executed via pre-commit.
- Black: formatting source of truth.
- isort: import sorting, use `--profile black`.
- Ruff: enable error/warning core rules only (`E`, `F`).
  - Globally ignore `E501` (line length) and let Black manage wrapping.
  - In tests/**, ignore `E712` (explicit True/False comparisons) and `F841` (intentionally unused variables).
- Every commit must pass pre-commit; if files are auto-formatted, stage changes and commit again.

## Type Hints (PEP 561 / mypy)

- The package ships with `py.typed` (PEP 561).
- All new/modified functions, classes, and attributes must include type annotations.
- mypy is configured in `pyproject.toml`:
  - `packages = ["polyclash"]`
  - `warn_redundant_casts`, `warn_unused_ignores`, `warn_return_any`, `no_implicit_optional` enabled
  - `ignore_missing_imports = true`, and `disable_error_code = ["import-untyped"]` to suppress third-party stub noise
- mypy must report zero issues before merge.

## Tests and Coverage

- Framework: pytest
- Run:
  ```bash
  pytest -q
  ```
- Coverage target: total coverage ≥ 80%. New features/changes must include tests and must not reduce coverage materially.
- Qt/PyVista tests:
  - Avoid real rendering; use mocks or CI headless env: `QT_QPA_PLATFORM=offscreen`, `PYVISTA_OFF_SCREEN=true`.
  - Prefer verifying UI logic via signals/slots/state updates over real 3D rendering.

## Git/PR Workflow

- Branch naming: `feature/*`, `fix/*`, `chore/*`, `docs/*`, etc.
- Commit message suggestions:
  - Prefix: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
  - Example: `feat: add join dialog ready-state handling`
- Before committing:
  ```bash
  pre-commit run --all-files
  mypy polyclash
  pytest -q
  ```
- PR must include:
  - Change summary and motivation
  - Risk and rollback plan for high-impact changes
  - Test notes and screenshots/logs for UI-related changes

## CI/CD and Branch Protection

- Workflow: `.github/workflows/ci.yml`
  - Uses uv to install deps, runs pre-commit (ruff/black/isort/mypy) and pytest
  - Configures headless Qt/PyVista to prevent crashes in CI
- In GitHub Settings, enable Branch protection / Rulesets:
  - Require status checks to pass before merging (select the CI checks)
  - Require a pull request before merging (recommend ≥ 1 reviewer)
  - Optional: linear history, disallow force pushes, signed commits, etc.

## Module-Specific Notes

- Game logic (`polyclash/game`)
  - `board.py` is core and non-trivial; future work plans to split into smaller modules (state/rules/scoring) per roadmap 1.2.
  - Any rule change requires comprehensive unit/integration tests.
- GUI (`polyclash/gui`)
  - Avoid real rendering in tests; rely on signals/slots and state assertions.
  - Large UI logic should be abstracted/isolated to improve testability.
- Network/Server (`polyclash/server.py`, `util/api.py`, `workers/network.py`)
  - Maintain robust error handling and consistent error messages.
  - Avoid real network calls in tests; use Flask/Socket.IO test clients or mocks.
- Scripts (`scripts/*.py`)
  - Provide type annotations and minimal verification.
  - If scripts emit large binaries/artifacts, ensure proper pathing and add to .gitignore if needed.

## Performance and Stability

- Performance tests live in `tests/performance/`; watch for regressions on algorithm changes.
- Logging: use `loguru` with the configured formatter and path in `polyclash/util/logging.py`.

## Command Cheatsheet

```bash
# Create venv and install
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Full local checks
pre-commit run --all-files
mypy polyclash
pytest -q

# Individual tools
ruff check .
black .
isort . --profile black

# Make local behavior match CI (helpful before PR)
pre-commit clean && pre-commit install --overwrite && pre-commit run --all-files
```

## Contributing and Communication

- Open an Issue to discuss proposals or significant changes before implementation.
- Code reviews focus on readability, testability, boundaries, and maintainability.
- Keep docs aligned with code: update `docs/`, `DEVELOPERS.md`, and module READMEs/comments as needed.

Thanks for making PolyClash better!

# PolyClash AGENTS.md (Agent Guide)

This guide defines rules and best practices for automated agents (including AI assistants) working in the PolyClash repository. The goal is to ensure changes are safe, reviewable, verifiable, and collaborative with human developers.

Table of Contents
- Role and Principles
- Change Boundaries and Prohibited Actions
- Workflow (Plan → Act → Verify)
- Quality Control (QC) and Gates
- Code and Test Best Practices
- File and Script Modification Guidance
- Environment and Caveats
- Commit and PR Guidelines
- Quick Commands

## Role and Principles

- Assistive role: Agents should make small, verifiable changes under clear requirements to reduce human errors.
- Verifiability first: Every change must be validated locally (pre-commit, mypy, pytest) and include reproducible steps.
- Minimal intrusion: Prefer incremental and localized changes; avoid large refactors/formatting drifts unless explicitly requested.
- Documentation sync: If changes affect developer workflows, rules, or module behavior, update `DEVELOPERS.md`, this document, or relevant module docs.

## Change Boundaries and Prohibited Actions

- Do not change core game rules (e.g., `polyclash/game/board.py`) unless explicitly required and backed by comprehensive tests.
- Do not commit binaries/large artifacts unless explicitly required and approved (and ignored properly if needed).
- Do not bypass CI or branch protection rules (Required status checks must pass).
- Do not break public APIs (e.g., `polyclash/util/api.py`) — keep return types and error semantics consistent.
- Do not introduce large-scale refactors or external tools that conflict with the project standards without approval.

## Workflow (Plan → Act → Verify)

1. Plan
   - Read requirements and code; propose a stepwise plan with scope, boundaries, and rollback options.
   - For cross-module changes, break into small, verifiable steps.

2. Act
   - Implement incremental diffs; avoid unnecessary churn (format-only or import-only changes).
   - Keep formatting/imports/types consistent; annotate new code.

3. Verify
   - Run local checks:
     ```bash
     pre-commit run --all-files
     mypy polyclash
     pytest -q
     ```
   - If first run auto-formats files, stage and re-run until green.
   - Provide a brief verification report and reproduction commands.

## Quality Control (QC) and Gates

- pre-commit: Must pass
  - ruff (only E/F rules; E501 ignored globally; tests/** ignore E712/F841)
  - black (formatting)
  - isort (`--profile black`)
  - mypy (type checking)
- mypy: Zero issues required
  - The project ships `py.typed`; all new/edited code requires annotations.
- Tests: pytest must pass; total coverage must remain ≥ 80%
  - New features/changes must include tests and maintain or improve coverage.
- CI: GitHub Actions workflow must pass; configure it as Required status checks.

QC Checklist (before commit/PR)
- [ ] mypy succeeds with 0 issues
- [ ] pre-commit succeeds (ruff/black/isort/mypy)
- [ ] pytest succeeds; coverage ≥ 80%
- [ ] No large meaningless changes (extraneous reformat/import noise)
- [ ] Docs updated if needed

## Code and Test Best Practices

- Style and tools:
  - black controls formatting; isort uses `--profile black`; ruff enforces basic E/F rules.
  - Ignore E501 globally (line length) to avoid conflicts with black.
  - In tests/** ignore E712 (explicit True/False) and F841 (temporary unused variables).

- Type hints:
  - Add type annotations for all new functions/classes/fields; include return types.
  - Third-party stub noise is suppressed via `disable_error_code = ["import-untyped"]` but still write careful code.

- Writing tests:
  - Non-GUI/3D: regular unit/integration tests.
  - GUI (Qt/PyVista):
    - Use headless env in CI: `QT_QPA_PLATFORM=offscreen`, `PYVISTA_OFF_SCREEN=true`
    - Prefer signals/slots and state assertions, avoid real rendering.
  - Server/Network:
    - Use Flask/Socket.IO test clients or mocks; avoid real network dependencies.
  - Performance: Watch for regressions; see `tests/performance/`.

## File and Script Modification Guidance

- Core modules (`polyclash/game`):
  - Be cautious; rule/scoring/turn changes require strong test coverage.
- GUI (`polyclash/gui`):
  - Avoid rendering in tests; rely on logical assertions and mocked dependencies.
- Scripts (`scripts/*.py`):
  - Provide type annotations and minimal validation.
  - Be careful with generated files (npz/vtk/pkl); avoid committing large artifacts.
- Data files (`model3d/`):
  - Considered artifacts; if updating, also update generation logic, documentation, and verification guidance.

## Environment and Caveats

- Python >= 3.10; prefer `uv venv` and `uv pip install -e ".[dev]"`.
- Qt/PyVista: use headless settings in CI to avoid crashes.
- Logging: use `loguru` (see `polyclash/util/logging.py`).

## Commit and PR Guidelines

- Branch naming: `feature/*`, `fix/*`, `chore/*`, `docs/*`, etc.
- Commit messages:
  - Prefix with `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- PR requirements:
  - Change summary, risks and rollback plan, verification steps (commands/logs/screenshots), and impacted modules/APIs/data.

## Quick Commands

```bash
# Setup and enable hooks
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install

# Full checks (first run may auto-format; commit updated files)
pre-commit run --all-files
mypy polyclash
pytest -q

# Individual tools
ruff check .
black .
isort . --profile black

# Clean and refresh pre-commit (if environment is inconsistent)
pre-commit clean && pre-commit install --overwrite && pre-commit run --all-files
```

---

For high-risk changes (architecture refactors, rule changes, binary assets), submit a Plan via PR/Issue first; after approval, proceed (Act) and include thorough verification (Verify).

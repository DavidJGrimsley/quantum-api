# Contributing to Quantum API

Thanks for helping improve Quantum API.

This repository ships a FastAPI backend, several SDKs, and engine clients. Small fixes are welcome, but public contract changes should be made carefully because they can affect the API, docs, tests, and first-party clients at the same time.

## Getting Started

Use `uv` for Python workflows:

```bash
uv sync --extra dev
```

Start the API locally:

```bash
uv run uvicorn quantum_api.main:app --reload
```

Optional extras are only needed when you touch those areas:

```bash
uv sync --extra phase5-optimization --extra phase5-experiments --extra phase5-finance --extra phase5-ml --extra phase5-nature --extra phase5-docs
uv sync --extra phase6-pennylane
```

## Branch Workflow

- Start from `main`.
- Create a focused branch such as `feature/<topic>`, `fix/<topic>`, `docs/<topic>`, `test/<topic>`, or `chore/<topic>`.
- Open pull requests back into `main`.
- Do not push directly to `main`.

Recommended branch bootstrap:

```bash
git fetch origin main
git switch main
git pull --ff-only origin main
git switch -c feature/example-topic
```

## Commit Style

Conventional prefixes are preferred:

- `feat:` new behavior
- `fix:` bug fix
- `docs:` documentation only
- `test:` test-only change
- `refactor:` internal restructuring without behavior change
- `chore:` tooling or maintenance

## Quality Expectations

Before asking for review:

- Run `uv run ruff check .`
- Run `uv run pytest` for meaningful backend changes
- Run focused tests for touched subsystems when a full run is unnecessary
- Add or update tests for behavior changes
- Update docs when public behavior, setup, or workflows change
- Update `CHANGELOG.md` for user-visible API or SDK changes

Typical commands:

```bash
uv run ruff check .
uv run pytest
```

Useful focused examples:

```bash
uv run pytest tests/test_api_contract.py -k portfolio
uv run pytest tests/test_key_management_api.py
uv run pytest tests/test_ibm_profiles_api.py
uv run pytest tests/test_pennylane_plugin.py
```

## High-Risk Paths

These areas deserve extra care because they affect runtime behavior, contract stability, or release packaging:

- `src/quantum_api/api/`
- `src/quantum_api/services/quantum_runtime.py`
- `src/quantum_api/services/qiskit_common/`
- `src/quantum_api/services/algorithms/`
- `src/quantum_api/services/optimization/`
- `src/quantum_api/services/finance/`
- `src/quantum_api/services/machine_learning/`
- `src/quantum_api/services/nature/`
- `src/quantum_api/services/experiments/`
- `sdk/pennylane/`
- `pyproject.toml`
- `.github/workflows/`

For changes in those paths:

- call out compatibility impact clearly in the pull request
- mention dependency or optional-extra changes explicitly
- include the exact validation commands you ran

## Expert Domain Review

This repository includes a large amount of Qiskit- and PennyLane-related implementation that was heavily AI-assisted. Because of that, passing tests alone is not the final standard for scientific confidence. We want qualified humans who actually know Qiskit and PennyLane to read through the quantum code, test or inspect the relevant behavior, request changes where needed, and then explicitly sign off on it.

The canonical review ledger lives in the `Expert Sign-offs` section at the bottom of `project/TODO.md`.

For this repo, a sign-off means the reviewer:

- read the relevant package or module group
- ran or inspected the relevant tests
- requested modifications if anything looked wrong, misleading, unstable, or scientifically weak
- only then checked off the item and added their GitHub profile link inline

For now, maintainer approval is still the actual merge approval on GitHub, and `@DavidJGrimsley` is the fallback approver. The TODO checklist is how we record expert review until dedicated outside reviewers are formally added to the repository workflow.

If you are doing senior Qiskit review, also use `project/questions.md` as the running list of architecture and correctness questions that still need expert judgment.

## Pull Request Checklist

Every pull request should include:

- a short summary of the change
- why the change is needed
- risk or compatibility notes
- test evidence
- docs or changelog impact

Use the repository pull request template.

## Documentation and Compatibility

- Keep `README.md`, `docs/`, and `project/` notes aligned with shipped behavior.
- Keep `/v1` contract compatibility unless the pull request intentionally introduces a breaking versioned change.
- Add deprecations to `CHANGELOG.md` before removing or replacing public behavior.

## Security Reporting

Do not open public bug reports for sensitive security issues.

- Prefer GitHub Security Advisories for private disclosure.
- Include affected endpoints, reproduction steps, and impact summary.

## Ownership

Path ownership is defined in `.github/CODEOWNERS`.

Right now the repository is maintained under a personal account, so the fallback required reviewer is `@DavidJGrimsley`.

## Helpful References

- `README.md`
- `project/style.md`
- `docs/sdk/release-governance.md`
- `project/TODO.md`

# Project Style - Engineering Conventions

## Language and Runtime

- Python 3.11+
- FastAPI + Pydantic v2
- Prefer explicit types and small modules

## API Design

- Keep routes under `/v1`
- Use strict request/response models (`extra = forbid` where needed)
- Return predictable JSON error envelopes
- Do not add hidden compatibility behavior

## Code Organization

- `api/` for route wiring only
- `models/` for schemas
- `services/` for business logic and quantum behavior
- Keep side effects at boundaries (HTTP layer), logic in services

## Validation and Safety

- Validate gate input semantics (`rotation_angle_rad` requirements)
- Enforce max text length via settings-aware validation
- Bound processing with timeout middleware
- Avoid leaking internals in production error responses

## Testing

- Contract tests for endpoint behavior
- Unit tests for quantum gate runner and dictionary mapping
- Determinism tests with seeded RNG where randomness is used
- Add regression tests for every bug fix

## Documentation

- Keep README and `project/*` docs aligned with implemented behavior
- Document any contract changes before implementation
- Migration docs should include explicit file-level checklists

## Versioning

- Semantic versioning for API and SDKs
- Breaking contract changes require major version bump

## Contribution Workflow

- Follow `CONTRIBUTING.md` for branch strategy, commit style, and PR quality gates
- Route high-risk Qiskit and PennyLane changes through CODEOWNERS review
- Keep `CHANGELOG.md`, `README.md`, and docs aligned with user-visible behavior changes

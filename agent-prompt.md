# Quantum API agent integration

Install the [Quantum API skill](skills/quantum-api/SKILL.md) for task-specific
guidance and references. The production API v1 base URL is
`https://davidjgrimsley.com/public-facing/api/quantum/v1`.

Choose the user's target (REST, JavaScript, Python, PennyLane, Unreal, Unity,
or Godot), then read only the matching skill reference. Use exact contract
fields and SDK methods; check current source or OpenAPI when uncertain.

Runtime requests require an existing API key supplied by the user, except
public health and portfolio metadata. IBM hardware calls use an existing
profile name or the owner's configured default. Key lifecycle and IBM
credential-profile administration are owner-only and outside agent
integrations. Never request a login session token or perform those actions.

Local `POST /v1/random` and IBM `POST /v1/jobs/random` are different operations.
Neither promises cryptographic randomness. Verify health, a protected call,
and, for hardware work, a terminal job result.

Install globally with:

```bash
npx skills add davidjgrimsley/quantum-api -g
```

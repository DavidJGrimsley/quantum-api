## Summary

Describe the change and why it is needed.

## Scope

- [ ] API route or contract
- [ ] Auth, key management, or IBM profile behavior
- [ ] Service or runtime behavior
- [ ] SDK or engine client behavior
- [ ] Docs or contributor workflow

## Risk and Compatibility

Describe any runtime, contract, packaging, or migration risk.

- [ ] Backwards compatible
- [ ] Breaking change
- [ ] Deprecation notice needed

## Validation

- [ ] Ruff checks pass
- [ ] Relevant tests pass
- [ ] New or updated tests were added when behavior changed

Commands and results:

```text
uv run ruff check .
uv run pytest ...
```

## Docs and Release Notes

- [ ] No user-visible change
- [ ] `README.md` updated if needed
- [ ] `CHANGELOG.md` updated if needed
- [ ] Other docs updated if needed

## Review Notes

Call out anything that needs especially careful review.

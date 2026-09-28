# Contributing

## Ground rules

- The core (`core/fm`) is deterministic: no network calls, no model calls,
  no randomness, no wall-clock dependence beyond `io.now_iso()`.
- Every state change is a ledger event, applied in `statemachine.replay()`.
  Never write `state.yaml` directly.
- Human-only operations call `authority.assert_human()` **before** any other
  check, then `require_human()` for confirmation.
- New data files get a Pydantic model in `core/fm/schemas/` (with
  `extra="forbid"`), an entry in `schemas.EXPORTED`, and validation rules in
  `validate.py`.
- Every file should have a purpose. No placeholder modules.

## Tests

```
python -m pytest
```

`fm.testing` provides the toy film fixture (`produce`, `drive`,
`as_actor`). Tests run against a temporary copy of `config/` and
`templates/`, never against real projects.

## Git workflow

- `main` stays green (tests pass). Work on short branches: `m2-agents`,
  `fix-stamp-note`.
- Commit a project's canon, bibles, shots, `.fm/ledger.jsonl`,
  `state.yaml`, `CHANGELOG.md`. Don't commit renders or `.blend` files
  (`.gitignore` covers them).
- Never rewrite history containing a project's ledger; the ledger is the
  audit trail.
- Commit messages: imperative, scoped — `core: detect stale implicit shot deps`.

## Private GitHub repository

```powershell
# once: create an empty PRIVATE repo named film_maker on github.com (no README)
git remote add origin https://github.com/gokhangemini26/film_maker.git
git push -u origin main
```

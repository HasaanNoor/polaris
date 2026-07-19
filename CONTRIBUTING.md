# Contributing to Polaris

## Source of Truth

GitHub is the single source of truth for Polaris. Contributors must not reinitialize Git, replace the remote, rewrite published history, or recreate existing repository structure without an explicit project decision.

## Phase Workflow

Polaris advances through incremental phases. Each phase must solve a concrete problem introduced by earlier phases and leave the repository in a verifiable state. Documentation, schemas, tests, and implementation must stay aligned.

Phase 0 is documentation-only. It must not add application code, dependencies, Docker files, CI workflows, or frontend/backend scaffolding.

## Branch Expectations

- Work on a branch that describes the phase or focused change.
- Keep pull requests scoped to one phase objective or one documented correction.
- Avoid mixing methodology changes, architecture decisions, and implementation work unless the phase explicitly requires it.

## Commit Messages

Use concise imperative messages:

- `docs: define phase 0 methodology policies`
- `architecture: add agent contract schema`
- `tests: cover artifact validation`

Avoid vague messages such as `updates`, `misc`, or `fix stuff`.

## Documentation Requirements

Documentation changes must:

- use terminology consistently across files;
- link related documents with relative Markdown links;
- distinguish current decisions from future possibilities;
- avoid unsupported methodology claims;
- avoid promotional language;
- state uncertainty and limitations when evidence is incomplete.

External methodology claims must be grounded in authoritative primary institutional guidance where relevant. Do not cite blogs or secondary summaries when institutional standards are available.

## Testing and Verification

When code exists, contributors must run applicable tests before requesting review. Documentation-only changes must still be inspected for broken links, empty files, heading consistency, Markdown formatting, and unsupported claims.

## Methodology Claims

Do not add claims about evidence quality, missing data, reproducibility, statistical reporting, effect sizes, multiple comparisons, robustness, provenance, survey limitations, comparability, or causal interpretation unless the claim is traceable to Polaris policy or an external source listed in the relevant methodology document.

## Phase Completion Checklist

1. Inspect changes.
2. Run applicable validation.
3. Review documentation.
4. Run tests when code exists.
5. Review git diff.
6. Review git status.
7. Commit.
8. Push.
9. Confirm remote status.

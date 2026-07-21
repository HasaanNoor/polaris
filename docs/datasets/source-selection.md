# Dataset Source Selection

## Purpose

This policy defines how Polaris evaluates candidate data sources before integration. Phase 0 candidate listings are not approved integrations.

## Acceptance Criteria

Candidate sources must be assessed for:

- institutional credibility;
- methodological transparency;
- licensing and reuse terms;
- access stability;
- geographic coverage;
- temporal coverage;
- indicator definitions;
- revision practices;
- comparability across units and time;
- provenance metadata;
- quality warnings;
- privacy and sensitivity risks.

## Preferred Sources

Polaris should prefer official statistical agencies, international organizations, peer-reviewed research institutions, transparent survey organizations, and maintained public-good datasets with clear documentation.

## Rejection or Warning Conditions

Sources require rejection or prominent warnings when:

- methods are opaque;
- licensing prohibits the intended use;
- access is unstable or undocumented;
- definitions change without versioning;
- coverage gaps dominate interpretation;
- survey sampling or weighting is unclear;
- conflict or governance data has known reporting bias that cannot be bounded;
- provenance cannot be recorded.

## Review Outcome

Each source review must result in one of:

- candidate pending review;
- accepted for limited use;
- accepted for general use;
- rejected;
- deprecated.

The initial catalog uses only "candidate pending review".

## Phase 2 Metadata Search

The Phase 2 registry can identify candidate sources by explicit metadata filters such as provider, status, variable identifiers, variable labels, frequency, license text, geographic metadata, temporal coverage, access restrictions, and methodology-reference presence.

Search does not approve a source. Warning-bearing datasets remain visible by default so later review stages can inspect limitations. Callers may explicitly exclude records with comparability warnings, licensing warnings, or access restrictions, or require no recorded access restrictions when a question requires unrestricted access.

Geographic matching is limited to exact manifest codes and names represented in the manifest description. A broad code such as `GLOBAL` is matched only when explicitly requested; Phase 2 does not infer that a global record contains every country or jurisdiction.

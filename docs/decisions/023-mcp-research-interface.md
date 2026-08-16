# ADR-023: MCP Research Interface

## Status

Accepted.

## Context

Polaris now has deterministic typed contracts, validated dataset registry/search, ingestion,
statistical analysis, harmonization, project orchestration, literature retrieval, reasoning, and
reasoning evaluation. External AI clients need a standard integration boundary, but the research
core must remain deterministic and independently usable.

## Decision

Add an optional local Model Context Protocol server in `polaris.mcp`. MCP is an integration
boundary above typed adapters and below external clients. Existing Polaris public APIs remain the
source of truth for dataset search, ingestion, analysis, harmonization, project orchestration,
literature retrieval, reasoning, report generation, and evaluation.

Resources expose read-only metadata and derived artifacts. Tools execute validated operations.
Methodological choices remain explicit: MCP clients must provide dataset inputs, variable mappings,
join choices, statistical specifications, selected agents, synthesis mode, and optional reasoning
or literature configuration. The MCP layer does not infer causal assumptions, variables, datasets,
models, or policy recommendations.

Stdio is the default transport because Phase 20 targets local clients without network exposure.
The official MCP Python SDK is used when installed via the optional `mcp` extra; Polaris normal
imports and tests do not require it. Remote/public deployment and HTTP transport are deferred.

The server prohibits arbitrary file and shell access. Resource reads are limited to configured
derived artifact roots, catalog manifests, and local literature corpus roots. Raw provider files,
environment variables, secrets, and shell execution are not exposed.

## Consequences

Compatible MCP clients can discover datasets, inspect variables/provenance, run explicit analyses,
run complete research projects, retrieve local literature context, retrieve reports, and inspect
reasoning/evaluation artifacts without coupling Polaris to one LLM provider. MCP remains optional,
and Phase 1-19 workflows continue to operate without starting a server.

## Alternatives considered

Embedding MCP inside the analytical pipeline was rejected because it would make protocol concerns
part of deterministic methodology. Hand-implementing the MCP wire protocol was rejected in favor of
the official SDK. HTTP transport was deferred because stdio covers local clients with less security
surface. Exposing arbitrary files or raw provider directories was rejected to preserve provenance,
licensing, and safety boundaries.

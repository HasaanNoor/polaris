"""Read-only MCP resource registry for safe Polaris metadata and artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from polaris.causal_studies.readiness import assess_design_readiness
from polaris.causal_studies.registry import load_causal_study_registry
from polaris.mcp.config import MCPServerConfig
from polaris.mcp.errors import MCPNotFoundError, MCPSafetyError
from polaris.mcp.serialization import json_compatible
from polaris.registry import DatasetRegistry, load_manifest, load_registry
from polaris.registry.models import DatasetCollectionType
from polaris.schemas.dataset import DatasetManifest

RESOURCE_URIS = (
    "polaris://datasets",
    "polaris://catalogs/who/variables",
    "polaris://catalogs/wgi/variables",
    "polaris://catalogs/unesco/variables",
    "polaris://catalogs/wdi/variables",
    "polaris://causal-studies",
)


class MCPResourceStore:
    """Bounded read-only resource access for MCP handlers."""

    def __init__(self, config: MCPServerConfig | None = None) -> None:
        self.config = config or MCPServerConfig()
        self.registry = _load_registry(self.config.catalog_directory)

    def list_resource_uris(self) -> tuple[str, ...]:
        dynamic = []
        for manifest in self.registry.list_all():
            dataset_id = manifest.dataset_id
            dynamic.extend(
                [
                    f"polaris://datasets/{dataset_id}",
                    f"polaris://datasets/{dataset_id}/manifest",
                    f"polaris://datasets/{dataset_id}/variables",
                    f"polaris://provenance/{dataset_id}",
                ]
            )
        dynamic.extend(_artifact_resource_uris(self.config))
        causal_registry = load_causal_study_registry()
        for study in causal_registry.list_studies():
            dynamic.append(f"polaris://causal-studies/{study.study_id}")
            dynamic.append(f"polaris://causal-studies/{study.study_id}/readiness")
        return tuple(sorted((*RESOURCE_URIS, *dynamic)))

    def read_resource(self, uri: str) -> dict[str, Any]:
        if uri == "polaris://datasets":
            return {"datasets": [dataset_summary(item, self.registry) for item in self.registry]}
        if uri.startswith("polaris://datasets/"):
            return self._dataset_resource(uri)
        if uri.startswith("polaris://catalogs/"):
            return self._catalog_resource(uri)
        if uri.startswith("polaris://causal-studies"):
            return self._causal_study_resource(uri)
        if uri.startswith("polaris://reports/"):
            return self._artifact_file_resource(uri, kind="reports")
        if uri.startswith("polaris://projects/"):
            return self._artifact_file_resource(uri, kind="projects")
        if uri.startswith("polaris://reasoning/"):
            return self._artifact_file_resource(uri, kind="reasoning")
        if uri.startswith("polaris://evaluations/"):
            return self._artifact_file_resource(uri, kind="evaluations")
        if uri.startswith("polaris://provenance/"):
            return self._provenance_resource(uri)
        raise MCPNotFoundError(f"unknown Polaris MCP resource URI: {uri}")

    def _causal_study_resource(self, uri: str) -> dict[str, Any]:
        registry = load_causal_study_registry()
        if uri == "polaris://causal-studies":
            return {
                "studies": [
                    {
                        "study_id": study.study_id,
                        "title": study.title,
                        "intervention_id": study.intervention.intervention_id,
                        "review_status": study.review_status.value,
                    }
                    for study in registry.list_studies()
                ]
            }
        parts = uri.removeprefix("polaris://causal-studies/").split("/")
        study = registry.get_study(parts[0])
        if len(parts) == 1:
            return json_compatible(study)
        if len(parts) == 2 and parts[1] == "readiness":
            return json_compatible(assess_design_readiness(study, registry=self.registry))
        raise MCPNotFoundError(f"unknown causal-study resource URI: {uri}")

    def _dataset_resource(self, uri: str) -> dict[str, Any]:
        parts = uri.removeprefix("polaris://datasets/").split("/")
        dataset_id = parts[0]
        manifest = self.registry.get(dataset_id)
        if len(parts) == 1:
            return inspect_manifest(manifest, self.registry.collection_type(dataset_id))
        if parts[1] == "manifest":
            return json_compatible(manifest)
        if parts[1] == "variables":
            return {
                "dataset_id": dataset_id,
                "variables": json_compatible(
                    sorted(
                        manifest.variables,
                        key=lambda variable: variable.variable_id,
                    )
                ),
            }
        raise MCPNotFoundError(f"unknown dataset resource URI: {uri}")

    def _catalog_resource(self, uri: str) -> dict[str, Any]:
        provider = uri.removeprefix("polaris://catalogs/").split("/", 1)[0]
        if provider == "who":
            return _json_catalog(
                "who",
                integrated="examples/who/who_integrated_variables.json",
                deferred="examples/who/who_deferred_indicators.json",
            )
        if provider == "wgi":
            return _json_catalog(
                "wgi",
                integrated="examples/wgi/wgi_variable_catalog.json",
                uncertainty_metadata={
                    "standard_error": (
                        "standard errors accompany each WGI dimension where available"
                    ),
                    "confidence_bounds": "lower/upper WGI score bounds are metadata, not outcomes",
                    "source_count": "number of source data inputs used by WGI for a country-year",
                },
            )
        if provider == "unesco":
            return _json_catalog(
                "unesco",
                integrated="examples/unesco/unesco_integrated_variables.json",
                deferred="examples/unesco/unesco_deferred_indicators.json",
            )
        if provider == "wdi":
            manifest = _first_manifest_for_provider(self.registry, "world bank")
            return {"provider": "wdi", "variables": json_compatible(manifest.variables)}
        raise MCPNotFoundError(f"unknown provider catalog: {provider}")

    def _artifact_file_resource(self, uri: str, *, kind: str) -> dict[str, Any]:
        artifact_id = uri.rsplit("/", 1)[-1]
        path = find_artifact_path(self.config, artifact_id, kind=kind)
        return read_safe_artifact_file(path)

    def _provenance_resource(self, uri: str) -> dict[str, Any]:
        artifact_id = uri.rsplit("/", 1)[-1]
        if self.registry.contains(artifact_id):
            manifest = self.registry.get(artifact_id)
            return {
                "artifact_id": manifest.dataset_id,
                "artifact_type": "dataset_manifest",
                "parent_artifact_ids": [],
                "source_dataset_ids": [manifest.dataset_id],
                "source_checksums": {"manifest": manifest.checksum},
                "software_schema_versions": {"dataset_manifest": manifest.schema_version},
                "generation_mode": "registry_manifest",
                "provider": manifest.provider,
                "retrieval_timestamp": (
                    manifest.retrieval_timestamp.isoformat()
                    if manifest.retrieval_timestamp is not None
                    else None
                ),
            }
        path = find_artifact_path(self.config, artifact_id, kind="provenance")
        payload = read_safe_artifact_file(path)
        return provenance_payload(artifact_id, payload)


def _load_registry(catalog_directory: Path) -> DatasetRegistry:
    manifests = []
    if catalog_directory.exists():
        manifests.extend(load_registry(catalog_directory).list_all())
    seen = {manifest.dataset_id for manifest in manifests}
    for path in sorted(Path("examples").glob("**/*manifest.json")):
        try:
            manifest = load_manifest(path)
        except Exception:
            continue
        if manifest.dataset_id not in seen:
            manifests.append(manifest)
            seen.add(manifest.dataset_id)
    return DatasetRegistry(manifests)


def dataset_summary(manifest: DatasetManifest, registry: DatasetRegistry) -> dict[str, Any]:
    return {
        "dataset_id": manifest.dataset_id,
        "provider": manifest.provider,
        "title": manifest.title,
        "collection_type": registry.collection_type(manifest.dataset_id).value,
        "geographic_coverage": json_compatible(manifest.geographic_coverage),
        "temporal_coverage": json_compatible(manifest.temporal_coverage),
        "variable_count": len(manifest.variables),
        "units": sorted(manifest.units),
        "source_version": manifest.source_version,
        "checksum": manifest.checksum,
        "integration_status": _integration_status(manifest),
    }


def inspect_manifest(
    manifest: DatasetManifest,
    collection_type: DatasetCollectionType,
) -> dict[str, Any]:
    return {
        **dataset_summary(manifest, DatasetRegistry((manifest,))),
        "collection_type": collection_type.value,
        "manifest": json_compatible(manifest),
        "variable_catalog": json_compatible(
            sorted(manifest.variables, key=lambda variable: variable.variable_id)
        ),
        "warnings": [
            *[json_compatible(item) for item in manifest.comparability_warnings],
            *[json_compatible(item) for item in manifest.licensing_warnings],
            *[
                {"category": "access_restriction", "message": item}
                for item in manifest.access_restrictions
            ],
        ],
        "provenance": {
            "resource_uri": f"polaris://provenance/{manifest.dataset_id}",
            "checksum": manifest.checksum,
            "retrieval_timestamp": (
                manifest.retrieval_timestamp.isoformat()
                if manifest.retrieval_timestamp is not None
                else None
            ),
        },
    }


def find_artifact_path(config: MCPServerConfig, artifact_id: str, *, kind: str) -> Path:
    if "/" in artifact_id or "\\" in artifact_id or artifact_id in {"", ".", ".."}:
        raise MCPSafetyError("artifact identifiers may not contain path separators")
    candidates: list[Path] = []
    for root in config.allowed_artifact_roots:
        if kind == "reports":
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}/report/report.*")))
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}.md")))
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}.html")))
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}.json")))
        elif kind == "projects":
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}/project.json")))
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}.json")))
        elif kind == "reasoning":
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}.json")))
            candidates.extend(sorted(Path(root).glob("**/*reasoning_artifact.json")))
        elif kind == "evaluations":
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}.json")))
        else:
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}/project.json")))
            candidates.extend(sorted(Path(root).glob(f"**/{artifact_id}*.json")))
    for path in candidates:
        resolved = config.resolve_under_allowed_roots(path)
        if resolved.is_file():
            return resolved
    raise MCPNotFoundError(f"artifact not found in configured Polaris roots: {artifact_id}")


def read_safe_artifact_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        with path.open(encoding="utf-8") as file:
            return json_compatible(json.load(file))
    if suffix in {".md", ".markdown", ".html"}:
        return {
            "path": path.as_posix(),
            "format": suffix.removeprefix("."),
            "content": path.read_text(encoding="utf-8"),
        }
    raise MCPSafetyError("only JSON, Markdown, and HTML derived artifacts are exposed")


def provenance_payload(artifact_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    provenance = payload.get("provenance") or payload.get("project_provenance") or payload
    return {
        "artifact_id": artifact_id,
        "artifact_type": payload.get("artifact_type") or _infer_artifact_type(payload),
        "parent_artifact_ids": payload.get("source_artifact_ids", []),
        "source_dataset_ids": provenance.get("dataset_ids") or [provenance.get("dataset_id")]
        if isinstance(provenance, dict)
        else [],
        "source_checksums": provenance.get("source_checksums", {})
        if isinstance(provenance, dict)
        else {},
        "software_schema_versions": {
            key: value for key, value in payload.items() if key.endswith("schema_version")
        },
        "generation_mode": payload.get("mode") or payload.get("execution_metadata"),
        "provider_model": provenance.get("provider") if isinstance(provenance, dict) else None,
        "timestamps": {
            key: value
            for key, value in payload.items()
            if key.endswith("_timestamp") or key.endswith("_at")
        },
    }


def _json_catalog(provider: str, **paths_or_payloads: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"provider": provider}
    for key, value in paths_or_payloads.items():
        if isinstance(value, str):
            path = Path(value)
            payload[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        else:
            payload[key] = value
    return json_compatible(payload)


def _artifact_resource_uris(config: MCPServerConfig) -> tuple[str, ...]:
    uris: list[str] = []
    for root in config.allowed_artifact_roots:
        for project in sorted(Path(root).glob("**/project.json")):
            project_id = project.parent.name
            uris.append(f"polaris://projects/{project_id}")
            uris.append(f"polaris://provenance/{project_id}")
        for report in sorted(Path(root).glob("**/report/report.*")):
            project_id = report.parent.parent.name
            uris.append(f"polaris://reports/{project_id}")
        for reasoning in sorted(Path(root).glob("**/*reasoning_artifact.json")):
            uris.append(f"polaris://reasoning/{reasoning.stem}")
        for evaluation in sorted(Path(root).glob("**/evaluation*.json")):
            uris.append(f"polaris://evaluations/{evaluation.stem}")
    return tuple(uris)


def _integration_status(manifest: DatasetManifest) -> str:
    dataset_id = manifest.dataset_id.casefold()
    if any(token in dataset_id for token in ("who", "wgi", "unesco", "harmonized")):
        return "integrated"
    return "available"


def _infer_artifact_type(payload: dict[str, Any]) -> str:
    keys = set(payload)
    if "project_id" in keys and "stage_results" in keys:
        return "research_project"
    if "reasoning_id" in keys:
        return "reasoning_artifact"
    if "evaluation_id" in keys:
        return "reasoning_evaluation"
    if "report_id" in keys or "content" in keys:
        return "report"
    return "derived_artifact"


def _first_manifest_for_provider(registry: DatasetRegistry, provider: str) -> DatasetManifest:
    normalized = provider.casefold()
    for manifest in registry.list_all():
        if normalized in manifest.provider.casefold():
            return manifest
    raise MCPNotFoundError(f"no registered manifest for provider: {provider}")

"""Strict local configuration for the Polaris MCP server."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator, model_validator

from polaris.mcp.errors import MCPSafetyError
from polaris.schemas.common import FrozenPolarisBaseModel


class MCPServerConfig(FrozenPolarisBaseModel):
    """Safe defaults for local MCP use."""

    catalog_directory: Path = Path("catalog/datasets")
    allowed_artifact_roots: tuple[Path, ...] = (Path("examples"),)
    allowed_project_output_directory: Path = Path("outputs")
    allowed_literature_corpus_roots: tuple[Path, ...] = (Path("examples/literature/corpus"),)
    maximum_tool_output_bytes: int = Field(default=65_536, gt=1024)
    provider_backed_reasoning_enabled: bool = False
    evaluation_enabled: bool = True
    enabled_resources: tuple[str, ...] = ("*",)
    enabled_tools: tuple[str, ...] = ("*",)

    @field_validator(
        "catalog_directory",
        "allowed_artifact_roots",
        "allowed_project_output_directory",
        "allowed_literature_corpus_roots",
    )
    @classmethod
    def reject_unsafe_path_values(cls, value):
        values = value if isinstance(value, tuple) else (value,)
        for path in values:
            text = Path(path).as_posix()
            if ".." in Path(path).parts:
                raise ValueError("MCP config paths must not contain parent traversal")
            if text.startswith("data/raw") or "/data/raw/" in text:
                raise ValueError("raw provider roots are not exposed over MCP")
        return value

    @model_validator(mode="after")
    def include_project_root(self) -> MCPServerConfig:
        roots = tuple(
            dict.fromkeys((*self.allowed_artifact_roots, self.allowed_project_output_directory))
        )
        object.__setattr__(self, "allowed_artifact_roots", roots)
        return self

    def resolve_under_allowed_roots(
        self,
        path: str | Path,
        *,
        roots: tuple[Path, ...] | None = None,
    ) -> Path:
        candidate = Path(path)
        if ".." in candidate.parts:
            raise MCPSafetyError("MCP clients may not address arbitrary or parent paths")
        resolved_candidate = candidate.resolve()
        configured_roots = roots or self.allowed_artifact_roots
        for root in configured_roots:
            resolved_root = Path(root).resolve()
            try:
                resolved_candidate.relative_to(resolved_root)
                if "data/raw" in resolved_candidate.parts:
                    raise MCPSafetyError("raw provider files are not exposed over MCP")
                return resolved_candidate
            except ValueError:
                continue
        raise MCPSafetyError("path is outside configured MCP roots")


def load_config(path: str | Path | None = None) -> MCPServerConfig:
    if path is None:
        return MCPServerConfig()
    import json

    with Path(path).open(encoding="utf-8") as file:
        return MCPServerConfig.model_validate(json.load(file))

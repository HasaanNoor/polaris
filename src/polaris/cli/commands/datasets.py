"""Dataset registry inspection commands."""

from __future__ import annotations

import typer

from polaris.cli.errors import CLIResourceNotFoundError
from polaris.cli.output import echo, json_echo
from polaris.cli.system import dataset_registry
from polaris.registry.errors import DatasetNotFoundError
from polaris.registry.models import DatasetSearchQuery

app = typer.Typer(help="Inspect registered datasets and provider metadata.", no_args_is_help=True)


@app.command("list")
def list_datasets(
    provider: str | None = typer.Option(None, "--provider", help="Filter by provider text."),
    domain: str | None = typer.Option(None, "--domain", help="Filter by dataset or variable text."),
    search: str | None = typer.Option(None, "--search", help="Search dataset and variable text."),
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress human-readable output."),
) -> None:
    registry = dataset_registry()
    keywords = tuple(item for item in (domain, search) if item)
    query = DatasetSearchQuery(
        providers=(provider,) if provider else (),
        keywords=keywords,
        variable_keywords=keywords,
    )
    results = registry.search(query)
    payload = [
        {
            "dataset_id": result.dataset_id,
            "provider": result.manifest.provider,
            "title": result.title,
            "version": result.manifest.source_version,
            "variables": [variable.variable_id for variable in result.manifest.variables],
            "collection_type": result.collection_type.value,
            "checksum": result.manifest.checksum,
        }
        for result in results
    ]
    if json_output:
        json_echo(payload)
        return
    if quiet:
        return
    echo("Datasets")
    echo("--------")
    for item in payload:
        echo(f"{item['dataset_id']} | {item['provider']} | {item['title']}")
        echo(f"  Variables: {', '.join(item['variables'][:6])}")
        echo(f"  Collection: {item['collection_type']}")


@app.command("inspect")
def inspect_dataset(
    dataset_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    registry = dataset_registry()
    try:
        manifest = registry.get(dataset_id)
    except DatasetNotFoundError as exc:
        raise CLIResourceNotFoundError(f"Dataset not found: {dataset_id}") from exc
    payload = manifest.model_dump(mode="json")
    payload["collection_type"] = registry.collection_type(dataset_id).value
    if json_output:
        json_echo(payload)
        return
    echo("Dataset")
    echo("-------")
    echo(f"ID: {manifest.dataset_id}")
    echo(f"Provider: {manifest.provider}")
    echo(f"Title: {manifest.title}")
    echo(f"Version: {manifest.source_version or 'unknown'}")
    echo(f"Coverage: {manifest.temporal_coverage.start}-{manifest.temporal_coverage.end}")
    echo(f"Variables: {len(manifest.variables)}")
    echo(f"Collection: {registry.collection_type(dataset_id).value}")
    if manifest.checksum:
        echo(f"Checksum: {manifest.checksum}")


@app.command("variables")
def variables(
    dataset_id: str,
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    registry = dataset_registry()
    try:
        manifest = registry.get(dataset_id)
    except DatasetNotFoundError as exc:
        raise CLIResourceNotFoundError(f"Dataset not found: {dataset_id}") from exc
    payload = [variable.model_dump(mode="json") for variable in manifest.variables]
    if json_output:
        json_echo(payload)
        return
    echo("Variables")
    echo("---------")
    for variable in manifest.variables:
        unit = f" ({variable.unit})" if variable.unit else ""
        echo(f"{variable.variable_id} | {variable.role.value} | {variable.data_type.value}{unit}")


@app.command("providers")
def providers(
    json_output: bool = typer.Option(False, "--json", help="Write machine-readable JSON."),
) -> None:
    registry = dataset_registry()
    known = ("World Bank", "World Health Organization", "WHO", "WGI", "UNESCO")
    payload = []
    for provider in known:
        matches = [
            manifest
            for manifest in registry.list_all()
            if provider.lower() in manifest.provider.lower()
        ]
        payload.append(
            {
                "provider": provider,
                "registered_datasets": len(matches),
                "status": "available_locally" if matches else "not_registered",
            }
        )
    if json_output:
        json_echo(payload)
        return
    echo("Providers")
    echo("---------")
    for item in payload:
        echo(f"{item['provider']}: {item['status']} ({item['registered_datasets']} datasets)")

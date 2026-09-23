from __future__ import annotations

import json
import re
from pathlib import Path

from quantum_api.main import app

_ROOT = Path(__file__).resolve().parents[1]
_COVERAGE_PATH = _ROOT / "sdk" / "unreal" / "contract" / "endpoint-coverage.json"
_CLIENT_SOURCE = _ROOT / "sdk" / "unreal" / "Source" / "QuantumApi" / "Private" / "QuantumApiClient.cpp"


def _runtime_operations() -> set[tuple[str, str]]:
    schema = app.openapi()
    operations: set[tuple[str, str]] = set()
    for path, path_item in schema["paths"].items():
        if not path.startswith("/v1/"):
            continue
        if path.startswith("/v1/keys") or path.startswith("/v1/ibm/profiles"):
            continue
        for method in path_item:
            if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                operations.add((method.upper(), path))
    return operations


def test_unreal_plugin_covers_every_non_credential_v1_operation() -> None:
    coverage = json.loads(_COVERAGE_PATH.read_text(encoding="utf-8"))
    typed = {tuple(item) for item in coverage["typed"]}
    advanced_json = {tuple(item) for item in coverage["advanced_json"]}

    assert len(typed) == 17
    assert len(advanced_json) == 22
    assert typed.isdisjoint(advanced_json)
    assert typed | advanced_json == _runtime_operations()


def test_unreal_advanced_catalog_has_no_credential_lifecycle_route() -> None:
    client_source = _CLIENT_SOURCE.read_text(encoding="utf-8")
    coverage = json.loads(_COVERAGE_PATH.read_text(encoding="utf-8"))

    advanced_paths_in_client = set(
        re.findall(
            r'case EQuantumApiAdvancedEndpoint::\w+: OutPath = TEXT\("([^"]+)"\)',
            client_source,
        )
    )
    expected_advanced_paths = {
        path.removeprefix("/v1") for _, path in coverage["advanced_json"]
    }
    assert advanced_paths_in_client == expected_advanced_paths

    for _, path in coverage["typed"]:
        client_path = path.removeprefix("/v1").replace("{job_id}", "%s")
        assert f'TEXT("{client_path}")' in client_source

    assert "case EQuantumApiAdvancedEndpoint::FermionicMappingPreview" in client_source
    assert 'OutPath = TEXT("/keys' not in client_source
    assert 'OutPath = TEXT("/ibm/profiles' not in client_source
    assert "protected_endpoint" in client_source
    assert "Verb.Equals(TEXT(\"GET\"" in client_source

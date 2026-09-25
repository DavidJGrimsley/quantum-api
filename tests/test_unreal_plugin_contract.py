from __future__ import annotations

import json
import os
import re
from pathlib import Path
from zipfile import ZipFile

import pytest

from quantum_api.main import app

_ROOT = Path(__file__).resolve().parents[1]
_COVERAGE_PATH = _ROOT / "sdk" / "unreal" / "contract" / "endpoint-coverage.json"
_CLIENT_SOURCE = _ROOT / "sdk" / "unreal" / "Source" / "QuantumApi" / "Private" / "QuantumApiClient.cpp"
_UNREAL_ROOT = _ROOT / "sdk" / "unreal"
_DEMO_STAGE = _UNREAL_ROOT / "Examples" / "QuantumApiDemo" / "Plugins"
_ENGINE_VERSION = "5.8.0"
_PUBLISHER = "David J. Grimsley"
_NOTICE = f"Copyright (c) 2026 {_PUBLISHER}. All rights reserved."
_CODE_SUFFIXES = {".c", ".cc", ".cpp", ".cs", ".h", ".hpp", ".hxx", ".inl", ".ixx", ".m", ".mm", ".ps1"}


def _authored_files() -> list[Path]:
    return sorted(
        path for path in _UNREAL_ROOT.rglob("*")
        if path.is_file()
        and not path.is_relative_to(_DEMO_STAGE)
        and not {"Binaries", "Intermediate", "Saved", "DerivedDataCache"}.intersection(
            path.relative_to(_UNREAL_ROOT).parts
        )
    )


def _expected_notice(path: Path | str) -> str:
    suffix = Path(path).suffix.lower()
    return ("# " if suffix == ".ps1" else "// ") + _NOTICE


def _distribution_entries() -> list[str]:
    stage_script = (_UNREAL_ROOT / "Examples" / "QuantumApiDemo" / "StagePlugin.ps1").read_text(encoding="utf-8-sig")
    match = re.search(r"\$distributionEntries\s*=\s*@\((.*?)\)", stage_script, re.DOTALL)
    assert match is not None, "Could not read the staging distribution entries"
    return re.findall(r"'([^']+)'", match.group(1))


def _source_distribution_files() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for entry in _distribution_entries():
        source = _UNREAL_ROOT / entry
        if source.is_file():
            result[source.relative_to(_UNREAL_ROOT).as_posix()] = source
        elif source.is_dir():
            for path in source.rglob("*"):
                if path.is_file():
                    result[path.relative_to(_UNREAL_ROOT).as_posix()] = path
    return result


def _check_descriptor(raw: bytes, name: str) -> None:
    descriptor = json.loads(raw.decode("utf-8-sig"))
    assert descriptor.get("EngineVersion") == _ENGINE_VERSION, name
    assert descriptor.get("CreatedBy") == _PUBLISHER, name


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

    assert len(typed) == 18
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


def test_unreal_source_descriptors_declare_compiled_engine_version() -> None:
    descriptors = [path for path in _authored_files() if path.suffix == ".uplugin"]
    assert descriptors, "No Unreal plugin descriptors found"
    for descriptor in descriptors:
        _check_descriptor(descriptor.read_bytes(), descriptor.relative_to(_UNREAL_ROOT).as_posix())


def test_every_authored_unreal_code_file_starts_with_publisher_notice() -> None:
    files = _authored_files()
    code_files = [path for path in files if path.suffix.lower() in _CODE_SUFFIXES]
    assert len(code_files) >= 21, "Unreal source inventory is unexpectedly small"
    assert _UNREAL_ROOT / "Source" / "QuantumApi" / "QuantumApi.Build.cs" in code_files
    assert _UNREAL_ROOT / "Examples" / "QuantumApiDemo" / "StagePlugin.ps1" in code_files
    for path in files:
        if "Source" in path.relative_to(_UNREAL_ROOT).parts:
            assert path.suffix.lower() in _CODE_SUFFIXES, f"Unaudited source file: {path}"
    for path in code_files:
        first_line = path.read_text(encoding="utf-8-sig").splitlines()[0]
        assert first_line == _expected_notice(path), path.relative_to(_UNREAL_ROOT).as_posix()


def test_final_fab_zip_matches_audited_plugin_source() -> None:
    package_name = os.environ.get("QUANTUM_API_FAB_PACKAGE")
    if not package_name:
        pytest.skip("Set QUANTUM_API_FAB_PACKAGE to inspect the final submission ZIP")

    expected_source = _source_distribution_files()
    expected_nonbinary = {name for name in expected_source if not name.startswith("Binaries/")}
    expected_code = {name for name in expected_nonbinary if name.startswith("Source/")}
    assert expected_code, "No plugin code in source distribution"

    with ZipFile(Path(package_name)) as package:
        assert package.testzip() is None, "Submission ZIP has a corrupt entry"
        archive_names = [item.filename for item in package.infolist() if not item.is_dir()]
        assert len(archive_names) == len(set(archive_names)), "Duplicate paths in submission ZIP"
        assert all(name.startswith("QuantumApi/") for name in archive_names)
        names = {name.removeprefix("QuantumApi/") for name in archive_names}
        nonbinary = {name for name in names if not name.startswith("Binaries/")}
        assert nonbinary == expected_nonbinary, f"Missing or unexpected package files: {nonbinary ^ expected_nonbinary}"
        binary_names = {name for name in names if name.startswith("Binaries/")}
        assert any(name.endswith(".dll") for name in binary_names), "Compiled plugin DLL is missing"
        assert all(Path(name).suffix.lower() in {".dll", ".pdb", ".modules", ".target", ".lib", ".exp"} for name in binary_names)

        descriptors = sorted(name for name in names if name.endswith(".uplugin"))
        assert descriptors == ["QuantumApi.uplugin"]
        for descriptor in descriptors:
            _check_descriptor(package.read(f"QuantumApi/{descriptor}"), descriptor)

        packaged_code = {name for name in names if name.startswith("Source/")}
        assert packaged_code == expected_code, f"Unaudited packaged code: {packaged_code ^ expected_code}"
        for name in packaged_code:
            assert Path(name).suffix.lower() in _CODE_SUFFIXES, f"Unknown packaged code type: {name}"
            raw = package.read(f"QuantumApi/{name}")
            first_line = raw.decode("utf-8-sig").splitlines()[0]
            assert first_line == _expected_notice(name), name
            assert raw == expected_source[name].read_bytes(), f"Packaged code differs from source: {name}"

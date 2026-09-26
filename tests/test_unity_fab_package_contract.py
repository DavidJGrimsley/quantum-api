# Copyright (c) 2026 David J. Grimsley. All rights reserved.
from __future__ import annotations

import json
import os
import tarfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_UNITY_ROOT = _ROOT / "sdk" / "unity"
_NOTICE = "// Copyright (c) 2026 David J. Grimsley. All rights reserved."
_PUBLISHER = "David J. Grimsley"


def _package_asset_path(source: Path) -> str:
    relative = source.relative_to(_UNITY_ROOT).as_posix()
    return "Assets/QuantumApi/" + relative.replace("Samples~/", "Samples/")


def test_unity_source_has_fab_publisher_notices_and_metadata() -> None:
    code_files = sorted(_UNITY_ROOT.rglob("*.cs"))
    assert len(code_files) >= 7, "Unity code inventory is unexpectedly small"
    for code_file in code_files:
        first_line = code_file.read_text(encoding="utf-8-sig").splitlines()[0]
        assert first_line == _NOTICE, code_file.relative_to(_UNITY_ROOT).as_posix()

    manifest = json.loads((_UNITY_ROOT / "package.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "com.quantumapi.runtime"
    assert manifest["version"] == "1.1.0"
    assert manifest["author"]["name"] == _PUBLISHER
    assert manifest["unity"] == "2021.3"
    assert manifest["unityRelease"] == "0f1"


def test_final_unity_fab_package_contains_only_audited_assets() -> None:
    package_name = os.environ.get("QUANTUM_API_UNITY_FAB_PACKAGE")
    if not package_name:
        pytest.skip("Set QUANTUM_API_UNITY_FAB_PACKAGE to inspect the final .unitypackage")

    expected_assets = {
        _package_asset_path(source): source.read_bytes()
        for source in _UNITY_ROOT.rglob("*")
        if source.is_file() and source.suffix != ".meta"
    }
    assert expected_assets

    with tarfile.open(package_name, "r:gz") as package:
        members = {member.name: member for member in package.getmembers() if member.isfile()}
        assert len(members) == len([member for member in package.getmembers() if member.isfile()])
        assert all(
            len(name.split("/", 1)[0]) == 32
            and name.rsplit("/", 1)[-1] in {"asset", "asset.meta", "pathname"}
            for name in members
        )

        actual_assets: dict[str, bytes] = {}
        paths: set[str] = set()
        for name, member in members.items():
            if not name.endswith("/pathname"):
                continue
            path = package.extractfile(member).read().decode("utf-8-sig").strip("\x00\r\n")
            assert path not in paths, f"Duplicate Unity path: {path}"
            assert path == "Assets/QuantumApi" or path.startswith("Assets/QuantumApi/")
            paths.add(path)
            guid = name.rsplit("/", 1)[0]
            assert f"{guid}/asset.meta" in members, f"Missing Unity meta for {path}"
            asset_name = f"{guid}/asset"
            if asset_name in members:
                actual_assets[path] = package.extractfile(members[asset_name]).read()

    assert actual_assets == expected_assets, f"Missing, extra, or stale assets: {actual_assets.keys() ^ expected_assets.keys()}"
    packaged_code = {path for path in actual_assets if path.endswith(".cs")}
    expected_code = {_package_asset_path(path) for path in _UNITY_ROOT.rglob("*.cs")}
    assert packaged_code == expected_code
    for path in packaged_code:
        assert actual_assets[path].decode("utf-8-sig").splitlines()[0] == _NOTICE, path

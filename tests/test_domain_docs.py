from __future__ import annotations

from pathlib import Path

import pytest

nbformat = pytest.importorskip("nbformat")

_ROOT = Path(__file__).resolve().parents[1]

_ARTIFACTS = {
    "/v1/algorithms/grover_search": (
        _ROOT / "docs" / "domains" / "algorithms-grover-search.md",
        _ROOT / "docs" / "notebooks" / "domains" / "algorithms-grover-search.ipynb",
    ),
    "/v1/algorithms/amplitude_estimation": (
        _ROOT / "docs" / "domains" / "algorithms-amplitude-estimation.md",
        _ROOT / "docs" / "notebooks" / "domains" / "algorithms-amplitude-estimation.ipynb",
    ),
    "/v1/algorithms/phase_estimation": (
        _ROOT / "docs" / "domains" / "algorithms-phase-estimation.md",
        _ROOT / "docs" / "notebooks" / "domains" / "algorithms-phase-estimation.ipynb",
    ),
    "/v1/algorithms/time_evolution": (
        _ROOT / "docs" / "domains" / "algorithms-time-evolution.md",
        _ROOT / "docs" / "notebooks" / "domains" / "algorithms-time-evolution.ipynb",
    ),
    "/v1/optimization/qaoa": (
        _ROOT / "docs" / "domains" / "optimization-qaoa.md",
        _ROOT / "docs" / "notebooks" / "domains" / "optimization-qaoa.ipynb",
    ),
    "/v1/optimization/vqe": (
        _ROOT / "docs" / "domains" / "optimization-vqe.md",
        _ROOT / "docs" / "notebooks" / "domains" / "optimization-vqe.ipynb",
    ),
    "/v1/optimization/maxcut": (
        _ROOT / "docs" / "domains" / "optimization-maxcut.md",
        _ROOT / "docs" / "notebooks" / "domains" / "optimization-maxcut.ipynb",
    ),
    "/v1/optimization/knapsack": (
        _ROOT / "docs" / "domains" / "optimization-knapsack.md",
        _ROOT / "docs" / "notebooks" / "domains" / "optimization-knapsack.ipynb",
    ),
    "/v1/optimization/tsp": (
        _ROOT / "docs" / "domains" / "optimization-tsp.md",
        _ROOT / "docs" / "notebooks" / "domains" / "optimization-tsp.ipynb",
    ),
    "/v1/experiments/state_tomography": (
        _ROOT / "docs" / "domains" / "experiments-state-tomography.md",
        _ROOT / "docs" / "notebooks" / "domains" / "experiments-state-tomography.ipynb",
    ),
    "/v1/experiments/randomized_benchmarking": (
        _ROOT / "docs" / "domains" / "experiments-randomized-benchmarking.md",
        _ROOT / "docs" / "notebooks" / "domains" / "experiments-randomized-benchmarking.ipynb",
    ),
    "/v1/experiments/quantum_volume": (
        _ROOT / "docs" / "domains" / "experiments-quantum-volume.md",
        _ROOT / "docs" / "notebooks" / "domains" / "experiments-quantum-volume.ipynb",
    ),
    "/v1/experiments/t1": (
        _ROOT / "docs" / "domains" / "experiments-t1.md",
        _ROOT / "docs" / "notebooks" / "domains" / "experiments-t1.ipynb",
    ),
    "/v1/experiments/t2ramsey": (
        _ROOT / "docs" / "domains" / "experiments-t2ramsey.md",
        _ROOT / "docs" / "notebooks" / "domains" / "experiments-t2ramsey.ipynb",
    ),
    "/v1/finance/portfolio_optimization": (
        _ROOT / "docs" / "domains" / "finance-portfolio-optimization.md",
        _ROOT / "docs" / "notebooks" / "domains" / "finance-portfolio-optimization.ipynb",
    ),
    "/v1/finance/portfolio_diversification": (
        _ROOT / "docs" / "domains" / "finance-portfolio-diversification.md",
        _ROOT / "docs" / "notebooks" / "domains" / "finance-portfolio-diversification.ipynb",
    ),
    "/v1/ml/kernel_classifier": (
        _ROOT / "docs" / "domains" / "ml-kernel-classifier.md",
        _ROOT / "docs" / "notebooks" / "domains" / "ml-kernel-classifier.ipynb",
    ),
    "/v1/ml/vqc_classifier": (
        _ROOT / "docs" / "domains" / "ml-vqc-classifier.md",
        _ROOT / "docs" / "notebooks" / "domains" / "ml-vqc-classifier.ipynb",
    ),
    "/v1/ml/qsvr_regressor": (
        _ROOT / "docs" / "domains" / "ml-qsvr-regressor.md",
        _ROOT / "docs" / "notebooks" / "domains" / "ml-qsvr-regressor.ipynb",
    ),
    "/v1/nature/ground_state_energy": (
        _ROOT / "docs" / "domains" / "nature-ground-state-energy.md",
        _ROOT / "docs" / "notebooks" / "domains" / "nature-ground-state-energy.ipynb",
    ),
    "/v1/nature/fermionic_mapping_preview": (
        _ROOT / "docs" / "domains" / "nature-fermionic-mapping-preview.md",
        _ROOT / "docs" / "notebooks" / "domains" / "nature-fermionic-mapping-preview.ipynb",
    ),
}


def test_domain_markdown_guides_reference_current_v1_paths():
    for endpoint, (markdown_path, _) in _ARTIFACTS.items():
        text = markdown_path.read_text(encoding="utf-8")
        assert endpoint in text
        assert "QUANTUM_API_BASE_URL" in text
        assert "QUANTUM_API_KEY" in text


def test_domain_notebooks_parse_and_reference_current_v1_paths():
    for endpoint, (_, notebook_path) in _ARTIFACTS.items():
        notebook = nbformat.read(notebook_path, as_version=4)
        combined = "\n".join(
            line
            for cell in notebook.cells
            for line in (cell.get("source") if isinstance(cell.get("source"), list) else [cell.get("source", "")])
        )
        assert len(notebook.cells) >= 2
        assert endpoint in combined
        assert "QUANTUM_API_BASE_URL" in combined
        assert "QUANTUM_API_KEY" in combined

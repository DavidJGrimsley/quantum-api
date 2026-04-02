from __future__ import annotations

from typing import Any

from quantum_api.ibm_credentials import ResolvedIbmCredentials
from quantum_api.models.api import BackendProvider
from quantum_api.services.ibm_provider import build_ibm_service, clear_ibm_provider_cache
from quantum_api.services.phase2_errors import BackendNotFoundError, Phase2ServiceError, ProviderUnavailableError
from quantum_api.services.quantum_runtime import runtime

LEGACY_AER_BACKEND_NAMES = {
    "qasm_simulator",
    "statevector_simulator",
    "unitary_simulator",
}
MODERN_AER_BACKEND_CANDIDATES = (
    "aer_simulator",
    "aer_simulator_statevector",
    "aer_simulator_density_matrix",
    "aer_simulator_stabilizer",
    "aer_simulator_matrix_product_state",
    "aer_simulator_extended_stabilizer",
    "aer_simulator_unitary",
    "aer_simulator_superop",
)


def list_backends(
    *,
    provider: BackendProvider | None,
    simulator_only: bool,
    min_qubits: int,
    ibm_credentials: ResolvedIbmCredentials | None = None,
) -> tuple[list[dict[str, object]], list[str]]:
    if not runtime.qiskit_available:
        raise RuntimeError("qiskit is unavailable for backend discovery")

    warnings: list[str] = []
    raw_entries: list[tuple[BackendProvider, Any]] = []
    provider_order: list[BackendProvider] = [provider] if provider else ["aer", "ibm"]

    for provider_name in provider_order:
        if provider_name == "aer":
            raw_entries.extend(("aer", backend) for backend in _list_aer_backends())
            continue

        try:
            raw_entries.extend(("ibm", backend) for backend in _list_ibm_backends(ibm_credentials))
        except Phase2ServiceError as exc:
            if provider == "ibm":
                raise
            warnings.append(exc.message)

    serialized = [_serialize_backend(provider_name, backend) for provider_name, backend in raw_entries]
    filtered: list[dict[str, object]] = []
    for payload in serialized:
        is_simulator = bool(payload.get("is_simulator", False))
        num_qubits_raw = payload.get("num_qubits", 0)
        if isinstance(num_qubits_raw, bool):
            num_qubits = int(num_qubits_raw)
        elif isinstance(num_qubits_raw, (int, float, str)):
            try:
                num_qubits = int(num_qubits_raw)
            except ValueError:
                num_qubits = 0
        else:
            num_qubits = 0
        if (not simulator_only or is_simulator) and num_qubits >= min_qubits:
            filtered.append(payload)
    filtered.sort(key=lambda item: (str(item["provider"]), str(item["name"])))
    return filtered, warnings


def resolve_backend(
    backend_name: str,
    provider: BackendProvider | None,
    *,
    ibm_credentials: ResolvedIbmCredentials | None = None,
) -> tuple[BackendProvider, Any]:
    if provider in {None, "aer"}:
        aer_backend = _get_aer_backend(backend_name)
        if aer_backend is not None:
            return "aer", aer_backend
        if provider == "aer":
            raise BackendNotFoundError(backend_name=backend_name, provider="aer")

    if provider in {None, "ibm"}:
        try:
            ibm_backend = _get_ibm_backend(backend_name, ibm_credentials)
        except ProviderUnavailableError:
            if provider == "ibm":
                raise
        else:
            if ibm_backend is not None:
                return "ibm", ibm_backend
            if provider == "ibm":
                raise BackendNotFoundError(backend_name=backend_name, provider="ibm")

    raise BackendNotFoundError(backend_name=backend_name, provider=provider)


def clear_backend_catalog_cache() -> None:
    clear_ibm_provider_cache()


def _list_aer_backends() -> list[Any]:
    if runtime.Aer is None:
        raise ProviderUnavailableError(
            provider="aer",
            details={"reason": "aer_unavailable", "import_error": runtime.import_error},
        )

    backends: list[Any] = []
    for backend_name in MODERN_AER_BACKEND_CANDIDATES:
        backend = _load_aer_backend(backend_name)
        if backend is not None:
            backends.append(backend)

    if not backends:
        raise ProviderUnavailableError(
            provider="aer",
            details={"reason": "no_supported_backends"},
        )
    return backends


def _get_aer_backend(backend_name: str) -> Any | None:
    if runtime.Aer is None:
        return None
    if backend_name in LEGACY_AER_BACKEND_NAMES:
        return None
    return _load_aer_backend(backend_name)


def _load_aer_backend(backend_name: str) -> Any | None:
    aer = runtime.Aer
    if aer is None:
        return None
    try:
        return aer.get_backend(backend_name)
    except Exception:
        return None


def _list_ibm_backends(ibm_credentials: ResolvedIbmCredentials | None) -> list[Any]:
    service = _get_ibm_service(ibm_credentials)
    try:
        return list(service.backends())
    except Exception as exc:
        raise ProviderUnavailableError(
            provider="ibm",
            details={"reason": "backend_listing_failed", "provider_error": str(exc)},
        ) from exc


def _get_ibm_backend(backend_name: str, ibm_credentials: ResolvedIbmCredentials | None) -> Any | None:
    service = _get_ibm_service(ibm_credentials)
    try:
        return service.backend(backend_name)
    except Exception:
        for backend in service.backends():
            if _backend_name(backend) == backend_name:
                return backend
    return None


def _get_ibm_service(ibm_credentials: ResolvedIbmCredentials | None) -> Any:
    if ibm_credentials is None:
        raise ProviderUnavailableError(
            provider="ibm",
            details={
                "reason": "missing_credentials",
                "message": "Configure IBM profile credentials or server-level IBM_TOKEN/IBM_INSTANCE to enable IBM provider support.",
            },
        )
    return build_ibm_service(ibm_credentials)


def _serialize_backend(provider: BackendProvider, backend: Any) -> dict[str, object]:
    configuration = _safe_backend_configuration(backend)
    name = _backend_name(backend, configuration)
    basis_gates_raw = []
    if configuration is not None:
        basis_gates_raw = list(getattr(configuration, "basis_gates", []) or [])

    basis_gates = sorted(str(gate) for gate in basis_gates_raw)
    coupling_map = getattr(configuration, "coupling_map", None) if configuration is not None else None
    is_simulator = _backend_simulator_flag(backend, configuration)
    num_qubits = _backend_qubit_count(backend, configuration)

    return {
        "name": name,
        "provider": provider,
        "is_simulator": is_simulator,
        "is_hardware": not is_simulator,
        "num_qubits": num_qubits,
        "basis_gates": basis_gates,
        "coupling_map_summary": _summarize_coupling_map(coupling_map),
    }


def _safe_backend_configuration(backend: Any) -> Any | None:
    try:
        return backend.configuration()
    except Exception:
        return None


def _backend_name(backend: Any, configuration: Any | None = None) -> str:
    if configuration is not None and getattr(configuration, "backend_name", None):
        return str(configuration.backend_name)
    if getattr(backend, "name", None):
        name_attr = backend.name
        if callable(name_attr):
            try:
                return str(name_attr())
            except Exception:
                pass
        return str(name_attr)
    return "unknown_backend"


def _backend_simulator_flag(backend: Any, configuration: Any | None) -> bool:
    if configuration is not None and getattr(configuration, "simulator", None) is not None:
        return bool(configuration.simulator)
    simulator = getattr(backend, "simulator", None)
    return bool(simulator) if simulator is not None else False


def _backend_qubit_count(backend: Any, configuration: Any | None) -> int:
    if configuration is not None and getattr(configuration, "n_qubits", None) is not None:
        return int(configuration.n_qubits)
    for attribute in ("num_qubits", "n_qubits"):
        value = getattr(backend, attribute, None)
        if value is not None:
            return int(value)
    return 0


def _summarize_coupling_map(coupling_map: Any) -> dict[str, int | bool]:
    if coupling_map is None:
        return {
            "present": False,
            "edge_count": 0,
            "connected_qubit_count": 0,
        }

    if hasattr(coupling_map, "get_edges"):
        edges = list(coupling_map.get_edges())
    else:
        edges = list(coupling_map)

    qubits = {int(qubit) for edge in edges for qubit in edge}
    return {
        "present": True,
        "edge_count": len(edges),
        "connected_qubit_count": len(qubits),
    }

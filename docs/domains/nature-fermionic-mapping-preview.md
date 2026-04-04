# Nature Fermionic Mapping Preview

Use `POST /v1/nature/fermionic_mapping_preview` to inspect how a small molecule Hamiltonian maps into qubit-space Pauli terms before running a variational solver.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "atoms": [
    {"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.0},
    {"symbol": "H", "x": 0.0, "y": 0.0, "z": 0.735}
  ],
  "basis": "sto3g",
  "charge": 0,
  "spin": 0,
  "mapper": "jordan_wigner",
  "ansatz": {"type": "real_amplitudes", "reps": 1},
  "optimizer": {"name": "cobyla", "maxiter": 25},
  "seed": 7
}
```

# Time Evolution

Use `POST /v1/algorithms/time_evolution` to evolve a Pauli-sum Hamiltonian with either Trotterized or variational real-time methods.

This route requires `qiskit-algorithms` on the server (included in the `phase5-optimization` optional dependency group). A healthy `/v1/health` response alone does not verify that this optional dependency is installed; smoke-test this route after deployment.

For `trotter_qrte`, provide exactly one of `initial_state` (a circuit) or `initial_statevector` (complex amplitudes in Qiskit basis order). The latter accepts the `logical_state` returned by `POST /v1/topological/braid` directly, preserving its relative phase. The array length must be `2 ** num_qubits`, match the Hamiltonian, stay within `MAX_CIRCUIT_QUBITS`, and have unit norm. Each amplitude uses `{ "real": number, "imag": number }` with finite values.

The response includes `final_statevector` and `final_probabilities`. Probability index `i` is the analytic probability of basis state `i` in the same order as the amplitudes; it is not sampled from `shots`. Pass `final_statevector` back as `initial_statevector` for a later evolution step. Variational variants do not accept either initial-state field.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "variant": "trotter_qrte",
  "hamiltonian": [{"pauli": "Z", "coefficient": 1.0}],
  "time": 0.5,
  "initial_state": {
    "num_qubits": 1,
    "operations": [{"gate": "h", "target": 0}]
  },
  "num_timesteps": 2,
  "shots": 256,
  "seed": 7
}
```

To evolve a braid, set `initial_statevector` to that braid response's `logical_state`. This example uses an illustrative normalized complex state:

```json
{
  "variant": "trotter_qrte",
  "hamiltonian": [
    {"pauli": "X", "coefficient": 0.6},
    {"pauli": "Z", "coefficient": 0.4}
  ],
  "time": 0.5,
  "initial_statevector": [
    {"real": 0.8, "imag": 0.0},
    {"real": 0.0, "imag": 0.6}
  ],
  "num_timesteps": 2
}
```

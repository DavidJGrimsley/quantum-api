# Nature Ground State Energy

Use `POST /v1/nature/ground_state_energy` for small-molecule VQE runs driven from caller-supplied atom coordinates, basis data, and mapper/optimizer choices.

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

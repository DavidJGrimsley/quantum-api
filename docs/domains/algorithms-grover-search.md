# Grover Search

Use `POST /v1/algorithms/grover_search` to run Grover-style amplitude amplification against either a list of marked bitstrings or a caller-supplied oracle circuit.

Set `QUANTUM_API_BASE_URL` and `QUANTUM_API_KEY` before running the example client code.

Example request:

```json
{
  "marked_bitstrings": ["11"],
  "iterations": [1],
  "sample_from_iterations": false,
  "shots": 256,
  "seed": 7
}
```

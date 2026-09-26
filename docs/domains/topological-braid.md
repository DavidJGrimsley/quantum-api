<!-- Copyright (c) 2026 David J. Grimsley. All rights reserved. -->
# Topological braid

Use `POST /v1/topological/braid` to evaluate a small non-Abelian braid in the Fibonacci anyon model.

This endpoint is intentionally narrow in v1:

- three Fibonacci anyons (`tau`)
- fixed total charge `tau`
- two-dimensional logical fusion space
- braid generators `sigma_1` and `sigma_2`
- forward (`power: 1`) and inverse (`power: -1`) exchanges
- exact fusion probabilities plus optional sampled measurement

It is a **digital simulation of a Fibonacci-anyon braid transformation**. It does not claim that IBM superconducting hardware is physically braiding anyons.

## Request

```json
{
  "model": "fibonacci",
  "anyon_count": 3,
  "total_charge": "tau",
  "initial_state": "0",
  "braid_word": [
    { "generator": 1, "power": 1 },
    { "generator": 2, "power": 1 },
    { "generator": 1, "power": -1 }
  ],
  "measure": true,
  "shots": 1,
  "seed": 7
}
```

Send `Content-Type: application/json`; braid requests are limited to 65,536 bytes. `generator: 1` exchanges strands 1 and 2; `generator: 2` exchanges strands 2 and 3. `power: -1` applies the inverse exchange. The braid word is applied in array order, so `[sigma_1, sigma_2]` evolves a column state as `sigma_2 @ sigma_1 @ state`.

The request allows at most 256 operations and 4,096 shots. If `measure` is false, the response contains exact probabilities, `shots: 0`, and no sampled outcome; a supplied positive `shots` value is ignored. If `measure` is true and `shots` is omitted or 0, the service performs one sample. A supplied `seed` makes sampling repeatable.

## Response

```json
{
  "model": "fibonacci",
  "anyon_count": 3,
  "total_charge": "tau",
  "initial_state": "0",
  "braid_word": [
    { "generator": 1, "power": 1 },
    { "generator": 2, "power": 1 },
    { "generator": 1, "power": -1 }
  ],
  "logical_state": [
    { "real": -0.5, "imag": 0.3632712640026804 },
    { "real": 0.7861513777574234, "imag": 0.0 }
  ],
  "fusion_probabilities": {
    "vacuum": 0.3819660112501051,
    "tau": 0.618033988749895
  },
  "measurement": "vacuum",
  "shots": 1,
  "counts": {
    "vacuum": 1,
    "tau": 0
  },
  "metadata": {
    "simulation_type": "digital_simulation_of_fibonacci_braid",
    "convention": "fibonacci_nayak_rmp_2008_chiral",
    "logical_dimension": 2
  }
}
```

The example is computed from the request above with seed 7; the final imaginary part shown as `0.0` is approximately `2.2e-16` in double precision. `logical_state[0]` means the first pair of anyons fuses to vacuum; `logical_state[1]` means that pair fuses to tau. **Both states have total charge tau.** The third possible state of three anyons has total charge vacuum and is outside this endpoint's two-dimensional sector. Each amplitude uses `real` and `imag` keys. The convention follows the Fibonacci F/R phases in [Nayak et al.](https://arxiv.org/abs/0707.1889). Reference vectors are also checked against [TQSim 0.0.2](https://github.com/Constantine-Quantum-Tech/tqsim), with its total-vacuum basis state excluded from this API's fixed-total-tau sector.

## Game integration

Games should usually own the braid history locally and submit the complete braid word when they need a result. This keeps the API stateless and makes saving, rewinding, branching, and offline fallback straightforward.

For a path-based game, append one operation at each route choice. When starting from logical `|0>`, the simple two-choice sequence `sigma_1^{+/-1}` followed by `sigma_2^{+/-1}` gives the same fusion probabilities for all four combinations. It changes complex phase, but a boss that reads only probabilities will not visibly distinguish them. To make all four paths produce different initial tau probabilities, use a fixed preparation `[sigma_2, sigma_1^-1]`, then one choice of `sigma_1^{+/-1}`, then one choice of `sigma_2^{+/-1}`, and a fixed readout `[sigma_1, sigma_2^-1]`:

```text
sigma_1, sigma_2       -> P(tau) ≈ 0.0902
sigma_1, sigma_2^-1    -> P(tau) ≈ 0.6180
sigma_1^-1, sigma_2    -> P(tau) ≈ 0.9443
sigma_1^-1, sigma_2^-1 -> P(tau) ≈ 0.7426
```

At a boss or other readout event, call the endpoint with `measure: false` for probabilities or `measure: true` for a sampled fusion outcome. For a boss state that evolves later, pass the returned two-entry `logical_state` into `/v1/algorithms/time_evolution` as `initial_statevector` and keep the complex amplitudes through each phase. A one-qubit Pauli Hamiltonian then acts on this ordered logical basis. The generic time-evolution endpoint does not infer a multi-anyon fusion basis from a longer vector; extending this handoff to more anyons needs an explicit basis mapping and sector constraints.

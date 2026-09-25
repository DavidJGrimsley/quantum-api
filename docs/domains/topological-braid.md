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

`generator: 1` means exchange strands 1 and 2. `generator: 2` means exchange strands 2 and 3. `power: -1` applies the inverse exchange.

If `measure` is false, the response contains exact probabilities and no sampled outcome. If `measure` is true and `shots` is 0, the service performs one sample.

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
    { "real": 0.0, "imag": 0.0 },
    { "real": 0.0, "imag": 0.0 }
  ],
  "fusion_probabilities": {
    "vacuum": 0.5,
    "tau": 0.5
  },
  "measurement": "tau",
  "shots": 1,
  "counts": {
    "vacuum": 0,
    "tau": 1
  },
  "metadata": {
    "simulation_type": "digital_simulation_of_fibonacci_braid",
    "convention": "fibonacci_nayak_rmp_2008_chiral",
    "logical_dimension": 2
  }
}
```

## Game integration

Games should usually own the braid history locally and submit the complete braid word when they need a result. This keeps the API stateless and makes saving, rewinding, branching, and offline fallback straightforward.

For a path-based game, append one operation at each route choice:

```text
upper path -> sigma_1
lower path -> sigma_1^-1
later upper path -> sigma_2
later lower path -> sigma_2^-1
```

At a boss or other readout event, call the endpoint with `measure: false` for probabilities or `measure: true` for a sampled fusion outcome.

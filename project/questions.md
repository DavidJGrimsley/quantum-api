# Questions for a Senior Qiskit Engineer

These are architecture/implementation questions we want expert review on.

## QASM and Circuit Contract

1. Are we making the right call by treating OpenQASM 2 as first-class and OpenQASM 3 as best-effort for now?
2. Should we standardize on one canonical internal representation (Qiskit `QuantumCircuit`) and only convert at API edges?
3. Do our current import/export error messages expose enough detail for developers while still being stable API contracts?

## Transpilation and Backend Strategy

4. Are we choosing sensible default transpiler settings (optimization level, layout/routing strategy), or should these be explicit in the API payload?
5. Should backend selection be deterministic by default, or should we expose an option for “best available backend” with transparent scoring?
6. Are we missing critical backend metadata fields that developers typically need before submitting jobs?

## Execution Semantics and Result Shape

7. Is it correct to keep `shots` output as the default result and make statevector output strictly optional and simulator-only?
8. Are there better conventions for representing bit order/endian behavior in measurement counts to prevent client confusion?
9. Should we include transpiled circuit depth/size and execution metadata in every run response as a baseline?

## Runtime and Hardware Readiness

10. For IBM Runtime integration, should we expose Sampler/Estimator directly in the public API, or wrap them behind stable domain-specific endpoints?
11. What is the cleanest way to support asynchronous hardware jobs without breaking our current synchronous endpoint contracts?
12. Should dynamic circuits be a separate endpoint family, or a capability flag on existing run endpoints?

## Accuracy, Claims, and Safety

13. Are our current “randomness” claims safe if most calls are simulator-backed, and should we explicitly label simulator vs hardware entropy in responses?
14. What minimum error-mitigation options are worth exposing first without overcomplicating the API?
15. What testing baseline (numerical tolerances, seed handling, reference circuits) would you require before calling this production-grade for research-adjacent workloads?

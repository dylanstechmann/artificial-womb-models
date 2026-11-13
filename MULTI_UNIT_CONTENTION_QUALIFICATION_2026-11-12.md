# T30 multi-unit shared-service contention qualification (2026-11-12)

**Roadmap task:** T30, registered by decision **D17**.  
**Status:** Qualified as a deterministic, dimensionless software fixture; no physical multi-unit isolation, fluidic testbed capability, alarm or biological safety qualification is claimed.

## Scope

This AI-assisted software experiment extends the T28/T29 single-unit fault register to cross-unit resource contention. Two gestation units (A and B) run their own local controllers, monitors and internal states across the three interface variants (`living_interface`, `staged` and `synthetic`), while drawing supplement from a common bulk stock reservoir in `shared` mode or from separate per-unit reservoirs in `isolated` mode. Unit A receives declared faults (`sensor_bias` and `actuator_offset`) alongside a no-fault baseline (`none`); unit B receives no local faults. The experiment tests whether a fault on unit A propagates across unit boundaries through the shared resource to degrade unit B, and whether unit B's boundary observables can distinguish shared-reservoir depletion from a local failure.

Command:

```sh
PYTHONPATH=src python -m wombmodels multi-unit-contention-model --config examples/multi_unit_contention_fixture.json --out <new-dir>
```

The command preserves the exact configuration as `source_config.json`, publishes isolated and shared trajectories for units A and B across all three variants, per-sample contention observations (`contention_observations.csv`), a structured report (`multi_unit_contention_report.json`), `REPORT.md`, a reproduction plan and a receipt. Strict bundle verification checks the published bytes; it does not rerun or scientifically validate the model.

## Frozen policy and result

The canonical fixture sets shared-reservoir initial stock to 5.0, replenishment rate to 0.8 and washout rate to 0.1, with noise standard deviation 0.02 and seed 20261112 over duration 40.0 at output step 0.5 (81 output samples per run). Unit A fault challenges are evaluated on the output grid: `none` at `[0, 0]`, `sensor_bias` of magnitude `0.3` at `[15, 18]` and `actuator_offset` of magnitude `0.2` at `[25, 28]`. Cross-unit propagation is flagged at an output sample when unit B's progression in `shared` mode drops by more than the 5% relative threshold (`cross_unit_propagation_threshold = 0.05`) compared with unit B's `isolated` baseline progression.

| Variant | Mode | Unit A fault | Fault window | Magnitude | Unit B local fault | Cross-unit path |
|---|---|---|---:|---:|---|---|
| living_interface | isolated | none | 0.0–0.0 | 0.0 | none | eliminated (separate reservoirs) |
| living_interface | shared | sensor_bias | 15.0–18.0 | 0.3 | none | shared bulk stock reservoir |
| living_interface | shared | actuator_offset | 25.0–28.0 | 0.2 | none | shared bulk stock reservoir |
| staged | isolated | none | 0.0–0.0 | 0.0 | none | eliminated (separate reservoirs) |
| staged | shared | sensor_bias | 15.0–18.0 | 0.3 | none | shared bulk stock reservoir |
| staged | shared | actuator_offset | 25.0–28.0 | 0.2 | none | shared bulk stock reservoir |
| synthetic | isolated | none | 0.0–0.0 | 0.0 | none | eliminated (separate reservoirs) |
| synthetic | shared | sensor_bias | 15.0–18.0 | 0.3 | none | shared bulk stock reservoir |
| synthetic | shared | actuator_offset | 25.0–28.0 | 0.2 | none | shared bulk stock reservoir |

These are deterministic fixture evaluations under invented dimensionless parameters, not physical fluidic depletion rates or multi-unit hardware reliability metrics.

## Key findings

- In `shared` mode, a sensor bias (`sensor_bias`, magnitude `0.3` on `t=[15, 18]`) or actuator offset (`actuator_offset`, magnitude `0.2` on `t=[25, 28]`) on unit A causes excessive supplement draw from the common bulk stock reservoir, depleting the shared reservoir and starving unit B of supplement — demonstrating cross-unit fault propagation through a shared resource even when unit B has no fault of its own.
- In `isolated` mode (separate reservoirs per unit), unit A's supplement draw cannot deplete unit B's supply, eliminating cross-unit propagation by construction while demonstrating that isolated single-unit runs do not capture shared-infrastructure contention.
- Regression checks verify exact isolated-to-T21 trajectory equality across all shared columns for every interface variant (`no_fault_isolated_matches_twin = True`), ensuring the multi-unit harness introduces no drift relative to the canonical whole-path twin when reservoirs are separate and unperturbed.
- Publication is deterministic, all isolated and shared unit trajectories and observation tables are present, and `verify_bundle(..., strict=True)` passes. Sixteen regression tests cover isolated and shared trajectory generation, cross-unit propagation under sensor bias and actuator offset, hidden contention boundary blindness, isolated T21 equivalence, deterministic publication, strict bundle verification, CLI entry, work-budget exhaustion without output publication and malformed-input rejection.

## Hidden internal-state boundary

A paired hidden-contention check (`hidden_contention_check`) applies the identical `sensor_bias` fault (`t=[15, 18]`, magnitude `0.3`) to unit A in two shared-reservoir runs while holding unit B's `serve_rate` fixed and varying only unit B's `internal_efficiency` (between `0.9` and `0.0`). Across all 81 output samples, unit A's boundary channels are bitwise identical (`unit_a_boundary_identical = True`) and unit B's boundary channels — including `local_stock`, `delivered_flux`, `served_fraction`, `supplement` and `shared_reservoir` — are bitwise identical (`unit_b_boundary_identical = True`), whereas unit B's internal `deep_receipt_rate` and `progression` differ (`unit_b_internal_differs = True`, `contention_boundary_blind = True`). Consequently, unit B's per-unit boundary channels cannot distinguish shared-reservoir depletion caused by unit A's fault from local delivery or internal tissue-use failure.

## Engineering consequence and limits

T30 extends the fault register from single-unit common-cause blindness (T29) to cross-unit coupling: in a multi-unit shared-service architecture, per-unit boundary monitoring alone cannot diagnose whether degradation originates from a sibling unit's fault depleting a shared resource or from local unit failure. The next physical dependency is a qualified multi-unit fluidic testbed with independent per-unit and shared-manifold measurement. This software fixture does not select manifold hardware, isolation valves or physical sizing, and does not advance M14/M15, M19/M20, G2/G3/G8 or any other biological or clinical gate.

- Every value, reservoir parameter, fault magnitude, threshold, noise stream and time is an invented dimensionless software quantity.
- Seeded independent noise streams are a software convention and do not establish physical sensor independence, manifold metering accuracy or calibrated uncertainty.
- The shared reservoir model assumes instantaneous mixing and sequential/proportional withdrawal; physical multi-unit fluidic manifolds exhibit transport delays, pressure drops, backflow and nonlinear hydraulic coupling.
- Isolated mode eliminates cross-unit contention only by assuming independent reservoirs; it does not qualify physical valve isolation or shared-utility fault containment.
- Per-unit boundary channels remain structurally blind to internal tissue receipt and progression states (`contention_boundary_blind = True`).
- No biological measurement, physiological calibration, machine control, procurement, external contact or gate movement is established.

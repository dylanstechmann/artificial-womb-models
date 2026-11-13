# T31 concurrent transition demand qualification (2026-11-13)

**Roadmap task:** T31, registered by decision **D18**.  
**Status:** Qualified as a deterministic, dimensionless software fixture; no transition procedure, neonatal, hardware or clinical claim is made.

## Scope

This AI-assisted software experiment extends the T30 multi-unit shared-service architecture to the transition layer. Two gestation units (A and B) follow the canonical whole-path twin trajectory across the three interface variants (`living_interface`, `staged` and `synthetic`). A unit becomes transition-ready when its twin progression first reaches a readiness threshold, then asks a transition station to serve it for a fixed service time. Two station modes are compared: `dedicated` (every unit owns a station, so nothing waits — the control) and `shared_serial` (one station serves both units first-in-first-out, one at a time, so a simultaneous demand forces the second unit to wait). A station outage suspends service with a preemption-and-resume convention: queued or in-service work pauses at the outage start and resumes at the outage end.

Command:

```sh
PYTHONPATH=src python -m wombmodels transition-demand-model --config examples/transition_demand_fixture.json --out <new-dir>
```

The command preserves the exact configuration as `source_config.json`, publishes per-mode/per-unit trajectory tables, a `transition_demand_events.csv` event table, a structured report (`transition_demand_report.json`), `REPORT.md`, a reproduction plan and a receipt. Strict bundle verification checks the published bytes; it does not rerun or scientifically validate the model.

## Frozen policy and result

The fixture freezes `readiness_threshold` 0.25, `service_time` 3.0, `unit_b_demand_offset` 0.0 (simultaneous demand), `station_outages` `[[12, 15]]` and `duration` 40. All three variants reach readiness; demand time is the first grid time whose progression reaches the threshold.

| Variant | Demand time (progression ≥ 0.25) |
|---|---:|
| living_interface | 12.5 |
| staged | 17.5 |
| synthetic | 32.0 |

Shared-serial service, no outage (`station_outages = []`): unit A waits 0.0 and unit B waits 3.0 — exactly one service time, caused by the queue — for every variant.

Shared-serial service with outage `[12, 15]`:

| Variant | Unit | Wait (no outage) | Wait (with outage) | Service start | Service end | Cause | Stage overshoot |
|---|---:|---:|---:|---:|---:|---|---:|
| living_interface | A | 0.0 | 2.5 | 15.0 | 18.0 | station_outage | 0.063012 |
| living_interface | B | 3.0 | 5.5 | 18.0 | 21.0 | queue | 0.143183 |
| staged | A | 0.0 | 0.0 | — | — | — | 0.0 |
| staged | B | 3.0 | 3.0 | — | — | queue | 0.053518 |
| synthetic | A | 0.0 | 0.0 | — | — | — | 0.0 |
| synthetic | B | 3.0 | 3.0 | — | — | queue | 0.024256 |

Only `living_interface`'s demand (12.5) falls inside the outage window `[12, 15]`, so only it shows outage-correlated delay. The dedicated control gives every unit a wait of 0.0 and a stage overshoot of 0.0, and its trajectories are exactly equal to independent whole-path-twin runs.

These are deterministic fixture evaluations under invented dimensionless parameters, not physical transition latencies or neonatal readiness measurements.

## Key findings

- Simultaneous transition demand forces the second unit to wait a full service time even with a faultless station: in shared-serial mode with no outage, unit B waits exactly `service_time` (3.0) while unit A waits 0.0, for every variant.
- A station outage correlates delays across units: `living_interface` waits rise from 0.0/3.0 to 2.5/5.5 when the outage overlaps its demand window, while `staged` and `synthetic` (whose demand times fall after the outage) are unchanged.
- Waiting is not neutral: stage overshoot accrues while a delayed unit keeps developing, up to 0.143183 for the more delayed second unit. The unit continues its twin trajectory during the wait, so the transition stage is entered in a more advanced state.
- Dedicated operation eliminates waiting by construction: every unit owns a station, service starts at demand time, and the trajectories equal the independent whole-path twin runs exactly.
- The cause of a delay — queue versus station outage — is not attributable from unit-local channels: unit B's local twin-trajectory series up to `service_start` is bitwise identical to the free twin regardless of whether its delay comes from station-side outage or queueing.

## Engineering consequence and limits

T31 establishes the transition station as a second shared-resource contention surface, after the T30 bulk-stock reservoir: simultaneous demand and a common-cause outage create contention and correlated delay at the transition layer, and unit-local channels cannot attribute the cause of a delay. Dedicated stations eliminate waiting but at the cost of one station per unit. This fixture does not select hardware, scheduling policy or physical capacity, and does not advance any biological or clinical gate.

- Every value, threshold, offset, outage interval, service time and time is an invented dimensionless software quantity.
- Preemption-and-resume at outage boundaries is a modeling convention, not a measured or engineered transition latency.
- Two units sharing one station do not establish any ten-unit concurrency or facility throughput claim.
- No neonatal function, readiness standard, transition procedure or clinical transition claim is made.
- No biological gate movement is established.

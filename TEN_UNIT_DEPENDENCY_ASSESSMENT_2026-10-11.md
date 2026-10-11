# Ten-unit resource and fault-dependency assessment

Date: 11 October 2026
Roadmap task: T13
Domain: engineering planning; no physical system or biological test

## Decision

For any future ten-unit architecture, treat each gestation as an independently identified and contained unit with its own support boundary, configuration, measurement record and outcome. Shared facility services may be considered only as explicitly modeled common dependencies with qualified isolation, continuity and failure accounting. A common service outage affecting several units is one correlated failure event, not several independent reliability observations. The unit boundary is a requirements decision; no physical topology, capacity, biological limit or safety qualification is established here.

The next topology discriminator is: **which functions can be shared without allowing one service, control, identity or record failure to silently couple units or hide simultaneous demand?** Current fixtures are not capable of answering that biological or physical question. T13 completes a bounded conceptual comparison and specifies the missing evidence; G8, M15 and M19 remain open/deferred.

## Evidence replay and boundary

I replayed the existing one-unit fixture with `examples/exchange_fixture.json` through `wombmodels.exchange.run_fixture`. The input is pinned by SHA-256 `c9095266c3ad21d4e3f8661f9bbb2ee1de73469801583c0e303d2b7b2d34a8db`; implementation `src/wombmodels/exchange.py` by `44f081ce74da94c3e16cf21f55a1b7b2919055c3fb6a05dfaf5cbe3795fb55ef`; canonical synthetic summary by `a698df24a694448281047227707dc9a2316d2602fb6bac03d476edc5e7c52704`.

The replay contains one abstract station, 49 scheduled samples and dimensionless time. It includes a synthetic wall outage from 3 to 7, a unitless backup reserve that depletes inside that outage, and one simulated monitor-bias and dropout interval. The software labels the resulting no-power segment as `shared_power_loss` for that station and emits an alarm at the first scheduled point in each injected fault interval. Mass-balance residuals are within floating-point rounding for this fixture. The fixture has no ten-unit population, shared facility resource graph, identity-routing model, physical load, calibrated sensor, biological material or developmental outcome. Its detector is scored against synthetic oracle truth and cannot be interpreted as a real reliability, fault-detection or safety rate.

This replay does one narrow job: it confirms the existing fixture can represent a shared power-to-monitor dependency inside one abstract unit. It does not answer whether a physical shared service is acceptable across ten units. No extra simulation was added because the repository has no source-based unit loads or independent ten-unit topology model to discriminate.

## Allocation comparison

| Function/resource | Candidate allocation for ten trajectories | Failure that must be visible | Evidence required before qualification | Current knowledge |
| --- | --- | --- | --- | --- |
| Gestation boundary and biological-contact path | Dedicated and contained per unit | Leak, cross-connection, unintended transfer or shared maintenance affecting a second unit | Unit-specific boundary inspection, challenge evidence, containment and cross-unit interference assessment by qualified engineering and biological teams | Conceptual requirement only; no design or physical evidence |
| Unit identity and configuration | Unique per unit and bound to the complete record | Duplicate/swapped identity, stale configuration, sample or sensor routed to the wrong record | End-to-end identity challenge for all ten records; reject duplicates and mismatches; retain version and custody history | No ten-unit identity model or qualification evidence |
| Measurement and observation channel | Dedicated or demonstrably isolated per unit; instruments may be shared only if concurrency and cross-talk are qualified | Shared calibration drift, queued/missed readings, channel crosstalk or one failed sensor obscuring several states | Calibrated reference, uncertainty, detection failure, simultaneous acquisition and channel-isolation evidence; independent outcome assessment | No instrument, feed, qualified measurement dictionary or calibration evidence identified |
| Support delivery/removal and local continuity | Per-unit boundary and independently observable state; any upstream service explicitly shared in the dependency register | A common source or control failure interrupts multiple units; one unit consumes capacity intended for another | Qualified source-derived demand envelope, contention and failure tests, unit-level isolation and continuity evidence | Physical loads, service topology, durations and biological limits are unknown |
| Site utilities | Potentially shared only behind a qualified distribution/isolation boundary with separately visible unit states | Upstream loss or degraded quality creates a common-cause event across multiple units | Facility dependency map, measured concurrent demand, isolation/continuity tests and reviewed fault combinations | No facility or utility capacity identified |
| Software, clocks and communications | Shared services may coordinate records; unit state, local records and version identity must remain separable | Common software/configuration error, timebase error, network outage or bulk update corrupts many units together | Versioned configuration, identity-safe routing, local record continuity, fault injection, rollback and audit evidence | Existing simulation is a one-unit synthetic fixture; no deployed controller/network is in scope |
| Staff and response coverage | May be shared only after simultaneous workload and escalation capacity are demonstrated | Multiple alarms, maintenance needs or transitions exceed available trained attention | Qualified operations analysis and witnessed capacity exercises for concurrent cases; accountable human roles and fallback coverage | No operator roster, institution or staffing quote identified |
| Transition capacity | Plan for ten concurrent transition demands as an independent downstream subsystem | Shared room, equipment, staff or schedule cannot support simultaneous independent readiness decisions | Simultaneous capacity evidence, per-unit readiness/outcome assessment, timestamps and retained misses | No ten-unit transition facility or outcome evidence |

**Allocation consequence:** preserve one uniquely identified biological/support trajectory per unit. Share only where the shared-resource dependency is named, the distribution boundary is observable, the full simultaneous demand is measured and the affected-unit set is explicit under failure. A shared dashboard or common start time cannot replace per-unit records or actual readiness. Do not count ten repeated uses of one unit as ten concurrent trajectories.

## Fault and dependency register

These are hazards to qualify, not claimed failure rates or a prescribed device design.

| Failure class | Propagation question | Minimum record needed to evaluate it |
| --- | --- | --- |
| Single-unit component loss | Can the fault remain attributable to one identified unit, and is its condition still observable? | Unit key, configuration, fault start/end, unavailable readings, affected function and independent disposition |
| Shared upstream service loss | Which of the ten units depend on the service at the same time, and how is correlation represented? | Versioned dependency map, simultaneous demand, affected-unit set, service interruption and each unit's separate record |
| Cross-unit connection or identity error | Can any measurement, material or configuration be silently assigned to another unit? | Source of each identity binding, routing history, mismatch alarms and documented rejection/recovery result |
| Common sensor/reference failure | Would one reference or calibration error make several channels appear consistent but wrong? | Reference traceability, calibration/version history, independent check and channel-level missing/invalid state |
| Common software/configuration change | Does one update alter all units at once, and can the change be detected and reversed without losing records? | Per-unit configuration hash, change approval, staged validation, rollback record and retained pre-change state |
| Communications or shared record-store loss | Are unit records and current states recoverable when a network or central store is unavailable? | Local record continuity, time synchronization provenance, gap detection and reconciliation audit |
| Staffing/transition contention | Can ten simultaneous needs be recognized and handled without one unit disappearing from the queue? | Concurrent demand cases, accountable role coverage, response records and all-unit disposition |
| Maintenance or batch common cause | Can a service action, shared consumable lot or production defect affect multiple units? | Maintenance, supplier/batch, replacement, inspection and affected-unit linkage in the complete denominator |

No probabilities, reserve durations, flow/capacity values or physiological thresholds are assigned. A useful later reliability analysis requires a source-defined topology, measured loads and failure distributions, validated independence/common-cause assumptions, and complete affected-unit outcomes. Ten units alone do not supply those assumptions.

## Qualification sequence for a responsible team

1. Freeze the unit boundary and identifier hierarchy; every unit must remain linked to its own configuration, measurements, operator decisions and disposition.
2. Inventory every shared and dedicated dependency, including upstream services, instruments, software/configuration, staff, maintenance and transition resources. Mark unknown dependencies explicitly.
3. Obtain qualified load and capacity requirements from the relevant system and evidence contract. Do not infer physical demand from the dimensionless fixture or a copied design.
4. Before biological use, challenge identity routing, simultaneous demand, one-unit faults, shared-service faults, common configuration/reference faults, communications loss and concurrent transition workload in qualified digital or nonliving settings. Record what is detectable, isolated, recoverable and still unobservable.
5. Have independent systems/reliability review decide whether the shared/dedicated allocation and evidence are adequate for the declared next stage. Later biological evidence must assess each unit and every starting-unit loss separately.

These are qualification questions for a responsible expert team, not bench instructions, device assembly steps, operation thresholds or animal/human procedures. Passing a digital or nonliving test cannot establish appropriate development, birth, health or ten-unit human feasibility.

## Outcome and next decision

- T13 can close as a **bounded engineering planning assessment**: the candidate allocation is per-unit identity and support boundary, with common services treated as explicit correlated dependencies; a one-unit software replay was scoped and its inability to validate ten-unit concurrency stated.
- U10 remains unresolved at physical capacity/reliability level. The precise missing inputs are the actual dependency graph, source-derived unit demand, qualified facility/instrument/team capability, common-cause tests and all-unit results.
- M15 remains deferred until reviewed requirements and component evidence exist. M19 remains deferred until qualified digital/nonliving and later biological concurrency, isolation, transition and outcome evidence exists. G8 does not advance.
- The next useful resource decision is to obtain a qualified systems/reliability capability and facility map after the scientific observation boundary is specified. Budget, location, quotes and owner route remain undecided; no external party was contacted.

## References

- [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md), “Multiple embryos” and “Resource continuity”: one dedicated support boundary per unit; shared services need isolation, continuity and common-cause accounting.
- [`METHODS.md`](METHODS.md), “Abstract exchange fixture”: explains the synthetic power/monitor dependency and its dimensionless scope.
- [`examples/exchange_fixture.json`](examples/exchange_fixture.json) and [`src/wombmodels/exchange.py`](src/wombmodels/exchange.py): exact input and implementation revisions for the bounded replay.

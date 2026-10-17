# Whole-system in silico design: early-exchange platform v2

Date: 17 October 2026
Roadmap task: T17 (registered by decision D10)
Status: in silico design and measurement specification; engineering concept only
Contact: no authors, reviewers, institutions or other people contacted

## What this is

One inspectable, plausible whole working system for the early exchange interval, designed entirely in silico. It instantiates the three retained allocations — living-interface hybrid (lead), staged support, and synthetic replacement — as substitutable variants on a single support skeleton, so they can be compared as designs rather than as prose. The rendered layout is [early_exchange_system_v2.json](config/schematics/early_exchange_system_v2.json); its tests are [tests/test_whole_system_design.py](tests/test_whole_system_design.py).

Per D10, this design is not conditioned on the biological gates: it models, decomposes and challenges everything the program must eventually build, without waiting for biological demonstration. The one rule that travels with it is evidence-ledger integrity — synthetic results are never registered as biological assays. No setpoint, material, dimension, biological parameter or operating procedure is specified here.

## Shared skeleton: functional decomposition

The three variants share every function except the interface allocation itself. Each function names its primary failure mode and its observable; the consequence column is what happens if the function is absent entirely.

| ID | Function | Subsystem | Primary failure mode | Observable | Consequence if absent |
| --- | --- | --- | --- | --- | --- |
| F1 | Unit identity and containment | Machine A habitat | Boundary breach, identity loss | Unit registry record; integrity checks | No same-unit D/M/P analysis is possible at all |
| F2 | Material delivery (D) | Machine B fluidics | Pump/oxygenator/dialysis fault, drift | In-line telemetry; flux accounting residual | Support stops; P fails downstream regardless of interface choice |
| F3 | Interface exchange | Variant allocation (see below) | Interface function loss or decoupling | Paired interface/core states (d_probe) | The discriminating function between variants disappears |
| F4 | Waste removal and inventory closure | Machine B dialysis | Silent accumulation; loss misattribution | Inventory residual; loss accounting | ℓ cannot be separated from uptake; D estimates bias |
| F5 | Thermal and mechanical context | Machine B habitat support | Excursion; unmodeled load history | Exposure records; strain-response fixture | Niche mechanics (Kelvin–Voigt fixture class) uninterpretable |
| F6 | Operational monitoring | Machine B sensing/DAQ | Sensor fault, stall, bias | Sensor failure states; state-estimation residuals | Equipment functioning confused with support performance |
| F7 | Closed-loop support control | Machine B controller | Oscillation, failover failure | Setpoint/telemetry disagreement | Support delivery unmanaged |
| F8 | Fault detection and escalation | Machine B alarms | Common-cause power/cooling loss | Alarm records; escalation log | Faults propagate silently across F2–F7 |
| F9 | Robotic servicing | Automation track | Servicing error, contamination | Servicing records with human override trail | Manual burden returns; concurrency infeasible |
| F10 | Human oversight and override | Automation track | Misassigned attention | Supervisory command log | No accountable operator for escalation |
| F11 | Independent research observation (D/M/P) | Research lane | Readout-into-control leakage; missingness | Same-unit records with disposition | Architecture comparison reverts to transfer-only proxies |
| F12 | Complete disposition registry | Research lane | Selective loss reporting | All-unit roster: continuing, lost, missing | Attrition hides failure; apparent continuity oversells |

Two design invariants are enforced by test: (a) D, M and P are sampled from the **same unit** and all land in one disposition registry; (b) the research lane **never feeds closed-loop control** — developmental readouts cannot become a support health score, and support telemetry cannot certify development.

## Variant instantiations at F3

The variants differ only in what occupies the interface slot and in what the paired-state measurement therefore sees. Each keeps the T01 falsifier that would weaken it.

| Variant | F3 implementation | What d_probe sees | Weakening result (from T01) |
| --- | --- | --- | --- |
| **Living-interface hybrid (lead)** | Preserved extraembryonic tissues against a surrogate maternal-facing niche (F5); engineered functions only where the living interface fails | A live, coupled interface state: c₁ dynamics track recipient core c₂ through transients; perturbing supply changes both in coupled relation | Interface/function measures present while tissue use (M) or progression (P) repeatedly fails, or functions cannot be independently attributed |
| **Staged support** | Interval-specific support allocations exchanged at source-defined stage boundaries (stage_boundary component) | Pre/post-transition paired-state samples; discontinuity at each handoff is bounded by same-unit D/M/P immediately before and after | Transition produces unexplained discontinuity, attrition or unboundable loss of function |
| **Synthetic replacement** | Engineered exchange cartridge reproducing required exchange/barrier/signaling functions explicitly (synthetic_exchange component) | No biological intermediate state: c₁ is design-imposed, e/d/ℓ independently perturbable; the c₁–c₂ relation is set, not emergent | Transport or component tests pass while tissue use or stage-appropriate progression does not |

The shared skeleton is the point: a measurement contract that separates these three signatures on the same skeleton is exactly the T01 discriminator made operational.

## Failure modes and fault propagation

Fault propagation is declared per function, with the response level named. This is a design register, not a safety case; no response prescribes a biological intervention.

- **F2 → F7 → F8:** delivery faults are detected in telemetry, managed by controller failover (pump_b), and escalated through alarms to human oversight; power loss is contained at F8 via UPS-backed power as a declared common-cause guard.
- **F3 → F11:** interface failure is *not* an operational alarm condition — it is a research-observation finding. The design deliberately routes it to the disposition registry, because an interface that "works" for support delivery while M or P fails is the LIPT1 endpoint-separation pattern, not a support fault.
- **F6 → F7:** a sensor fault must degrade the state estimate visibly (declared failure states, residual growth) rather than freeze the last good value; a frozen estimate silently corrupts control.
- **F4 → F11:** inventory residual mismatch blocks any D-parameter fit for that unit; it never gets absorbed as unexplained noise.
- **F1 → F12:** loss of unit identity voids that unit's contribution to every comparison; no group-label substitution is permitted.

## Model coverage: fixtures map onto the whole system

The existing dimensionless fixtures are not peripheral — each occupies a named region of this design:

| Existing module | System region | What it already establishes |
| --- | --- | --- |
| Two-compartment transport (`exchange.py`, `developmental_models.py`) | F3/F4 interface–core exchange | Inventory-conserving dynamics; exact closed-form reference verified to 60-digit precision |
| `transport_identifiability.py` | F3/F11 measurement design | Core-only and equilibrium-only observation are structurally ambiguous; paired transient states distinguish the witnessed pair |
| Kelvin–Voigt mechanics (`developmental_models.py`) | F5 niche response | Strain response under imposed load; response time not conflatable with relaxation half-time |
| `state_estimation.py` | F6 monitoring | Noise-aware fitting with declared fault injection and forecast split |
| `design_sweep.py` | Variant comparison | Bounded seeded sweeps over cadence/noise, monitor-fault and event-timing profiles |
| Schematic renderer (`schematics.py`) | Whole layout | Deterministic, self-contained rendering of this design with receipt-backed bundles |

## Identifiability-driven minimum-measurement specification

This is the core of the design: the smallest same-unit observation set that makes D, M and P separately estimable and distinguishes the three allocations. It is derived from the structural counterexamples already proven in the transport-identifiability report, not from preference:

1. **Core-only observation cannot identify delivery.** With zero initial states, the rate triples `(e, d, ℓ)` and `(2d, e/2, ℓ)` produce the *same* core trace for any boundary history. A delivery readout that only observes the recipient compartment — the default in most support hardware — is structurally unable to separate boundary exchange from internal transport.
2. **Equilibrium-only observation cannot identify rate scale.** `(e, d, ℓ)` and `(2e, 2d, 2ℓ)` share both equilibrium states. Steady sampling, however dense, adds no rate information.
3. **Zero excitation identifies nothing.** With zero boundary input and zero initial contrast, all rate triples produce zero traces. A measurement plan needs at least one known, nonzero, time-resolved excitation.
4. **Paired transient states break ambiguity 1.** Sampling the interface state c₁ *and* the core state c₂ at shared timepoints through a transient distinguishes the witnessed swapped pair — this is a requirement for this particular ambiguity, not a general guarantee for noisy data.

**Minimum measurement set for D (delivery):** one controlled, recorded, nonzero boundary excitation c_b(t); paired interface/core samples (c₁, c₂) at shared timepoints spanning at least one transient, not only equilibrium; and inventory/loss accounting sufficient to close ℓ per unit. A unit whose inventory residual does not close is blocked from D fitting (F4 → F11 rule).

**Minimum measurement set for M (tissue use):** a same-unit readout of intracellular processing of the delivered material, taken separately from transfer. The shared-loss caveat is explicit: in the transport fixture, ℓ does not identify an uptake mechanism, and the LIPT1 endpoint-separation example shows preserved transfer coexisting with failed downstream metabolism. Transfer-only evidence is therefore inadmissible for M by design.

**Minimum measurement set for P (progression):** same-unit, stage-indexed progression endpoints with the six-part T04 contract fields — complete starting roster, stage clock, named compartments/readouts, explicit within-unit links, comparator/outcomes/missingness, and source/reuse provenance — with every loss and missing observation retained (F12).

**How this distinguishes the allocations.** Under the same contract: the living-interface lead predicts coupled c₁/c₂ transients that persist while M and P proceed; staged support predicts the discontinuity at each handoff is bounded by its pre/post-transition paired samples; synthetic replacement predicts an imposed c₁ that tracks its design setting while M and P may fail independently of it — the transfer-passes-but-development-fails signature. All three signatures are observable with one instrument suite; none requires inventing a threshold before the sweep is run.

**Sampling density, resolution and cohort size** are not hand-assigned here. They are computable: run the variant signatures through `design_sweep.py` with declared noise and cadence profiles, and freeze the smallest sampling plan — and the smallest n per cohort — whose variant-prediction intervals are disjoint, before any real or controlled dataset is opened. That frozen plan is the pre-registered analysis this design exists to enable.

## What would change this design

- Any measured same-unit dataset that closes the D/M/P chain would retire the identifiability-derived sampling plan in favor of the data's own clock and compartments — and would itself constitute the "materially new source-linked evidence" that reopens T05 review.
- A failed inventory-closure or identity invariant in a real cohort voids the affected units; the design does not average over broken invariants.
- The living-interface lead loses its lead position if interface-function measures persist while M or P repeatedly fails across units; the skeleton is retained and F3 is re-allocated.

## Limits and disposition

This is an in silico engineering design and measurement specification. It asserts no biological capability, no setpoints, no materials, no success probability and no gate movement; synthetic results are never biological assays; physical execution and human-use gates are untouched. The next concrete steps it enables are the frozen variant-signature sweep and the minimum-measurement acquisition specification for T08's resource decision.

**Roadmap disposition:** T17 acceptance is met — functional decomposition, compartment/exchange/control/monitoring coverage with declared failure modes, and an identifiability-driven minimum-measurement specification distinguishing the three allocations are all inspectable in this document, the v2 layout and its tests. No biological gate advances; independent scientific review remains unestablished.

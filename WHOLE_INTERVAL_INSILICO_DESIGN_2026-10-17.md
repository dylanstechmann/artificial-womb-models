# Whole-interval in silico design: sustained exchange through neonatal transition

Date: 17 October 2026
Roadmap task: T18 (extension of T17; registered under decision D11)
Status: in silico design and measurement specification; engineering concept only
Contact: no authors, reviewers, institutions or other people contacted

## What this is

The [early-interval design](WHOLE_SYSTEM_INSILICO_DESIGN_2026-10-17.md) covered the early exchange boundary. This extension carries the same whole working system across the remaining intervals — sustained exchange, fetal maturation and neonatal transition — so that "plausible whole working system" now means the entire support path, in silico. The rendered layout is [whole_interval_system_v3.json](config/schematics/whole_interval_system_v3.json); its tests are [tests/test_whole_interval_design.py](tests/test_whole_interval_design.py). Together, v2 and v3 form one continuous system with one unit identity from the declared starting stage to the transition station.

As with T17, this design is not conditioned on the biological gates; it models what must eventually be built and measured, without waiting for demonstration. No setpoint, material, dimension or operating procedure is specified. The late-support/transition *evidence* comparison already exists (Cycles 310–315) and is not re-run here; this is design work on the same skeleton.

## Interval decomposition

| Interval | What the system must do | What changes versus the early interval |
| --- | --- | --- |
| **I1 — early exchange** (v2 design) | Establish the interface and deliver to the recipient while progression begins | Interface allocation is the open architecture choice (living-interface lead, staged, synthetic) |
| **I2 — sustained exchange** | Maintain effective delivery and interface/tissue function **as the unit grows**; supply capacity must keep pace with growth | F2 delivery becomes growth-paced; internal (not just boundary) delivery becomes measurable; exchange-surface capacity scales |
| **I3 — fetal maturation** | Support changing demand while organ function matures, with compatible support changes | F5 mechanics becomes growth accommodation; support changes are themselves boundary events; maturation endpoints are observed per unit |
| **I4 — neonatal transition** | Independently assessed change from machine support to neonatal function | Machine C is a separate station; readiness is a measured assessment with retained uncertainty, never a countdown or size inference |

Three boundaries (I1→I2, I2→I3, I3→I4) are drawn explicitly in v3, and every one of them is a **same-unit pre/post D/M/P measurement event**. This generalizes the staged-support variant's handoff logic into a system-wide continuity contract: continuity between intervals is a *measured property with recorded disposition*, not an assumption, whichever interface variant occupies F3.

## Competing-failure register for the growing unit

The midgestation boundary analysis already names the candidate failures that dominate I2/I3; the design assigns each an observable and an inference it must never support:

| Candidate failure | Designed observable | Inference to avoid |
| --- | --- | --- |
| Internal delivery lags growth | Spatially resolved receipt/clearance in the growing unit (`internal_delivery` probe) | Adequate bulk supply or vessel markers prove adequate internal delivery |
| Tissue use fails despite delivery | Same-unit organ-function/maturation endpoints separate from transfer | An altered label fraction uniquely identifies failed delivery or one metabolic defect |
| Vascular/fluid dysfunction contributes | Linked circulation/compartment state with adverse-outcome onset timing (edema, hemorrhage, dysfunction) | Reported adverse findings establish a specific cause or event sequence |
| Missing developmental interactions | Source-matched interface/tissue relationships alongside outcomes | A marker list or later support system replaces the omitted interaction |
| Selection/stage mismatch | Starting rosters, excluded units, actual stage, endpoint-assessment branch | Selected endpoints represent every starting unit or agree with duration |

Adverse-outcome **onset timing** is retained alongside supply accounting, metabolism and stage progression; the design never collapses them into one success score.

## Measurement contract extension for the later intervals

- **Boundary continuity**: paired D/M/P immediately before and after every interval handoff, same unit, with complete disposition (`boundary_probe`).
- **Internal delivery**: spatially resolved receipt/clearance, because bulk availability cannot establish that internal tissue is served as the unit grows.
- **Destructive branch separation**: terminal destructive endpoint profiles are their own sampling branch — recorded in the registry, never followed as surviving units, and never fed into transition readiness (test-enforced).
- **Transition readiness**: measured maturity with retained uncertainty; not inferable from elapsed time, fetal size, or a successful support record; the transition station is evaluated independently of support duration.
- **Complete disposition**: every starting unit is tracked through every boundary — continuing, lost, missing or destructively sampled — or the cohort comparison is blocked.

## Variant behavior in the later intervals

The three F3 allocations matter most at I1; by I2/I3 they converge on the same engineering skeleton, and the open discriminator shifts from *interface establishment* to *delivery-versus-use-versus-progression within a growing unit*. The living-interface lead keeps a coupled interface state if extraembryonic-derived tissues persist and grow; synthetic replacement keeps an imposed surface whose capacity is set by design; staged support concentrates its risk at the boundaries it introduces. All three are measured by the same contract above — which is the point of sharing the skeleton.

## Model coverage and the gap this exposes

The existing fixtures cover the later intervals unevenly: the two-compartment transport and identifiability machinery extends directly to internal delivery (add a third, spatially resolved compartment class); `state_estimation.py` covers monitoring; the mechanics fixture covers load response but **not growth-paced capacity scaling of the exchange surface**. That gap — a dimensionless growth-scaling fixture showing when delivery capacity falls behind a growing sink, with the boundary probe catching the divergence — is the natural next module, and the failure signature it would produce is exactly the "delivery fails within the growing unit" candidate above.

## Ten-unit aspiration annex

The owner's single-gestation objective stands; concurrency remains an aspiration. The whole-interval design scales by replicating the per-unit skeleton (F2–F8 dedicated per unit) with shared services declared explicitly as correlated-fault exposure, per the completed T13 assessment. No concurrency capability is asserted by drawing it.

## Limits and disposition

In silico design only: no biological capability, setpoint, success probability or gate movement; synthetic results are never biological assays; physical execution and human-use gates are untouched; independent scientific review remains unestablished.

**Roadmap disposition:** T18 acceptance is met — the whole-interval decomposition, growth-paced delivery and maturation coverage with declared failure modes, boundary continuity contract, destructive-branch separation and transition-readiness design are inspectable in this document, the v3 layout and its tests. No biological gate advances.

# Development roadmap

Reviewed against the code on 2026-10-06. The long-term research question remains
complete human ectogenesis from IVF through birth. This roadmap advances
mathematics, evidence quality and reproducible research software; it does not
turn disconnected developmental intervals into a demonstrated gestation system.

The [research program](RESEARCH_PROGRAM.md) defines the scientific questions,
transition map, source/data shortlist and E1–E6 work packages. Start its E1–E3
evidence/observation/data-eligibility work now alongside M1–M2. Additional
dimensionless stress cases should not postpone qualifying a real measurement
target. New sources in that plan are candidates awaiting source review; this
roadmap revision does not promote them into the evidence ledger.

## Next research sequence — 2026-10-09

AI-assisted planning after the boundary and maternal-interface source intakes;
human scientific review remains pending. Prioritize one inspectable empirical
result, with data qualification before biological fitting. Existing M1–M6
software milestones remain supporting work.

The primary feasibility question is whether earlier maternal-interface state
adds information about later embryonic progression after accounting for earlier
embryo state and actual recipient support. Current sources do not qualify that
joint analysis. The [maternal-interface requirements](MATERNAL_INTERFACE_REQUIREMENTS.md)
and [boundary reanalysis contract](BOUNDARY_REANALYSIS_CONTRACT.md) define its
missing observations. Start with the data/coverage milestone below.

| Order | Work package | Concrete deliverable | Acceptance / stop rule |
| --- | --- | --- | --- |
| 1 | Represent cohort coverage and disposition | Extend existing observation intake with optional source-linked aggregate population/denominator metadata; keep the individual phenotype matrix separate | Preserve counted entity, original cohort label, endpoint/selection definition, denominator timing and withdrawals. Missing identity stays unqualified; aggregate counts never create specimen IDs or continuous development |
| 2 | Resolve a bounded source-mapping question | A source-located mapping/eligibility report for Hiraoka's later endpoint cohorts and Bondarenko's movement/outcome link | Authenticate recipient/embryo/experiment relationships and dispositions from inspected public records. Preserve unresolved mappings and count discrepancies. Stop each source search after its specified public records are inspected or bounded retrieval fails; author inquiry may be prepared but remains unsent |
| 3 | Qualify one measured-data question | Freeze one source-specific question card and record a source/method review decision | Joint prediction requires individual earlier observations, later outcomes, actual support, complete disposition coverage and independent grouping. If unavailable, select only an eligible descriptive endpoint/coverage question; do not relabel it as mechanism or forecast validation |
| 4 | Run the eligible bounded analysis | One receipt-bound result with source ancestry, exclusions/unavailable outcomes, simpler comparator where applicable and reproduction instructions | Use the frozen statistic/model and scope. Predictive evaluation keeps all observations from an embryo and shared biological/experimental group together and excludes future inputs. Report a negative, inconclusive or non-identifiable result explicitly |
| 5 | Revise the architecture from that result | Update the physical-niche, reconstructed-living-interface and retained-maternal-tissue comparison | Name the assumption supported or contradicted, remaining observables and next developmental transition. Early attachment, markers or morphology cannot close sustained exchange, later function or human gestation gates |

### First implementation package

Add optional cohort-coverage metadata to the existing intake contract and its
reports. Design it around source declarations rather than reconstructed units:

- Separate embryos, recipient animals, tissue fragments, imaging subsamples and
  assay events. Preserve the source's aggregation convention and labels.
- Distinguish initially included, assessed, retained, shed, assay-withdrawn,
  excluded, missing and unassessed populations. A withdrawal from longitudinal
  assessment need not mean a biological failure or excluded collected data.
- Bind every count/denominator and selection statement to its exact artifact
  and locator. Preserve the original reported percentage separately from any
  count ratio when aggregation meaning is unresolved.
- Assess count closure only when a declared common cohort, observation window
  and exhaustive, mutually exclusive disposition categories justify it.
  Otherwise report the check as unassessed; shared `Exp` labels are insufficient.
- Keep malformed inputs distinct from valid declarations with unresolved source
  identity or accounting. Report unresolved/discrepant evidence without silently
  repairing or dropping it.
- Add invented software fixtures covering withdrawals, partial coverage,
  overlapping/unqualified denominators, source-label collisions and a declared
  complete-cohort count inconsistency. Verify provenance and output exclusivity.

**Completion:** the Hiraoka candidate can retain its endpoint-specific
withdrawal/denominator statements structurally, with the existing conditional
count discrepancy still unresolved; the Bondarenko candidate still establishes
zero boundary/outcome joins. Tests demonstrate that neither aggregate counts nor
matching labels manufacture biological identity or continuity. Existing source
bytes, original measurements and human-review status remain intact.

### Bound the next public-data search

For Hiraoka, inspect the publisher peer-review material and declared sequencing
sample metadata only for explicit cohort/recipient/assay-withdrawal mappings and
the recorded source-count questions. Do not assume molecular samples provide
later phenotype records. For Bondarenko, inspect bounded Figure 1 archive
metadata and selected relevant tabular members if retrieval allows it; do not
download the large image archive merely to continue searching. Record the scope
and outcome of each inspection.

Missing source identities or measurements remain an eligibility finding. Prepare
a precise unsent data inquiry if public records do not resolve them. Any actual
author contact needs separate user authorization. Human source/method review is
required before the biological fit; software/data-contract work can proceed
while that review is pending.

The first result may therefore be a reusable coverage/non-identification report.
It must state exactly what information is missing and which claim cannot yet be
tested. A source-qualified paired-morphology description is a separate fallback,
with its selected population and unresolved generalization clearly retained.

This sequence supplies research software and analysis requirements, without a
biological procedure, fabrication plan or operating specification. Complete
healthy human embryo-to-birth support remains unestablished.

## Delivered baseline

- Reviewed evidence ledger with source class, species, developmental stage,
  stated interval, excluded inference and requirement links.
- `evidence-report`: explicit stage-transition edges with same-unit IDs,
  source/claim links and exact locators required before continuity can be
  marked demonstrated or contradicted; current human-target edges stay unknown.
- Exact piecewise exchange transitions, scheduled synthetic sensors, backup
  power/fault fixtures, receipts and input/implementation/output hashes.
- Integral-balance consistency diagnostics, noise-aware state estimation,
  prospective prefix-trained forecasts versus a last-reading baseline, and
  seeded cadence/noise/fault/event-timing sweeps.
- Dimensionless two-compartment transport and Kelvin–Voigt mechanics examples
  with simpler alternative models; developmental-observation JSON schema.
- `validate-observations`: bounded source-linked records, exact reported-unit
  partitions, optional local source-byte hashing, local source-review metadata,
  explicit continuity states and a receipt-bound ResearchDesk report. Intake
  validity is not analysis eligibility.
- Read-only ResearchDesk discovery and receipt-checked report display.

The 0.2.1 correction matches the transport reference to the combined capacity
of both compartments. It also distinguishes point-forecast availability from
approximate-interval availability when local parameter covariance is absent.
Neither a finite covariance nor a low residual establishes biological validity.

The TEBV Figure 8 case in RegenWorkbench is a descriptive measured-data
reanalysis with one donor, missing vessel identifiers and a recorded
workbook/caption sample-count discrepancy. It is not an external validation of
these equations or measured ectogenesis.

## M1 — Independently verify numerical accuracy

**First implementation milestone.** Conservation identities already exist;
add accuracy checks against independent solutions.

**Progress:** `verify-transport` publishes a receipt-bound, five-level
step-halving curve against a closed-form two-state reference.
`verify-transport-matrix` now repeats it across seven deterministic regimes,
including zero dynamics, isolated exchange/transfer, unequal rates, stable
high mixing and near-degenerate weak coupling. `verify-mechanics` compares
every output and load boundary against an independently evaluated,
`expm1`-stabilized piecewise-load convolution, including zero-elasticity creep.
Adversarial checks now cover adjacent sign-changing loads, endpoint loads,
very fast relaxation and the near-zero-elasticity limit. A test now compares the
closed-form transport reference with an independent 60-digit matrix exponential
across 85 coefficient-scale cases (rates 1e-12 to 1e4, times 1e-6 to 1e3); the
observed worst relative difference on 2026-10-08 was about 4e-16. M1 remains in
progress for the mechanics reference at coefficient extremes and for broader
floating-point limits.

1. Preserve the independently derived constant-coefficient two-compartment
   reference and check both compartments over the supported numerical domain.
2. Expand transport checks to additional coefficient-scale extremes; retain
   actual versus requested steps and each numerical regime in the
   receipt-bound report.
3. Extend mechanics analytic checks across additional degenerate
   elasticity/viscosity limits; test controlled rejection of unsupported
   inputs.
4. Publish equations, units (dimensionless here), assumptions, tolerances and
   error curves generated by a reproducible command.

**Acceptance:** independently derived reference values, quantitative convergence
tests, controlled failures at unsupported regimes, and a verification report
that cannot be mistaken for biological validation.

## M2 — Benchmark identifiability and forecast calibration

Depends on M1. The current bounded profile search and local covariance are a
baseline, not a complete identifiability study.

`transport-identifiability` now exports exact core-only rate-swap and
equilibrium scale counterexamples, their valid witness configurations and
paired-interface contrasts. It addresses a structural observation limit in
the existing dimensionless transport equations. It does not complete M2's
forecast calibration or establish empirical identifiability.

- Export the objective profile, search-bound hits, rank/singular-spectrum
  diagnostics and approximate interval availability with explicit reasons.
- Freeze separate calibration and evaluation scenarios before tuning. Vary
  initial state, power schedule, cadence, noise and model mismatch; reserve
  independent seeds and schedules for evaluation.
- Compare forecasts at prespecified horizons with last-value and simpler
  model baselines. Report error, bias, interval width and coverage together.
- Distinguish per-reading coverage from coverage variation across independent
  synthetic trajectories; include all failure/unavailable denominators.
- Test equilibrium, weak excitation, parameter boundaries and wrong model
  structure. Do not replace an unavailable forecast prediction interval with a
  sensor-noise-only interval under the same label.

**Acceptance:** machine-readable frozen scenario plans, no tuning on evaluation
data, negative controls that expose non-identification, and reproducible
baseline comparisons. Any use of profile likelihood or confidence language
needs its statistical assumptions and independent methods review.

## M3 — Add a causal observer benchmark

Depends on M2. Keep this a software fixture, separate from live hardware.

- Define a narrow observation interface carrying only measurements already
  available at each timestamp. Hide generator truth, injected fault labels
  and future measurements from the observer.
- Add delay, drift/bias, dropout, shared power loss and model mismatch cases.
  Document which power/event information is assumed known.
- Score state error, event-level misses, false alarms and detection delay;
  retain overlapping-event ambiguity and undetected-event outcomes.
- Keep truth exclusively in the evaluator. Add tests that future readings and
  hidden fault annotations cannot alter earlier observer outputs.

**Acceptance:** frozen held-out scenarios, past-only interface tests, explicit
event denominators and failure examples. No physiological alarms, clinical
thresholds or control recommendations.

## M4 — Enforce observation metadata and evidence intervals

Can proceed alongside M1–M3. The observation record and dataset-card contracts
now have a stdlib runtime validator; source coverage and scientific review
still need additional work.

**Progress:** `validate-observations` checks source-file references and declared hash metadata,
species, developmental intervals, endpoint units, independent-unit hierarchy,
missingness, calibration references and transition records. When given an
explicit local root, it hashes bounded relative source files and records the
match status without copying them. It partitions
records by exact reported categories without unit conversion or pooling, and
requires a reported unit identity plus same-source chronologically comparable
intervals before accepting a `demonstrated` continuity assertion. ResearchDesk
can display its receipt-bound output. This verifies record structure and byte
provenance, not a paper transcription, reviewer's identity or scientific
eligibility.

**Evidence-ledger progress:** `evidence-report` now accepts structured numeric
interval components on sources and claims. A claim must match the cited source's
axis and exact unit and stay within its bounds; missing or widened claim scopes
fail validation. This catches scope expansion in curated metadata without
converting units or pretending the validator checked a source transcription.
It also emits five explicit developmental transitions. A reported edge must
preserve species, cover both source stages, link exact source locators and unit
IDs across its claims, and use a peer-reviewed source. Announcement and regulator
records cannot establish same-unit continuity. All human-target edges remain
`not_reported`; this is a gap in the bounded ledger, not evidence of absence.

Remaining work includes source-locator review history, permission/access
confirmation and one qualified empirical dataset. Candidate sources stay
unpromoted until primary-source review. Curated transition locators and unit IDs
still need source-transcription checks and an auditable reviewer record.

**Observation interval progress (2026-10-09):** source artifacts can declare an
optional `developmental_scope` with species, stages, exact time unit, numeric
bounds and a source locator. Records citing that stage artifact must match its
categories and remain within its numeric interval. Textual or missing record
bounds stay explicitly unassessed. Receipt-bound source-scope and per-record
check tables preserve those distinctions. The new executable intake example is
entirely invented dimensionless metadata; no empirical source has been qualified
or promoted by this change. Source transcription and human review remain open.

- Validate examples and imported metadata with the stdlib runtime, including
  source version, species/model, independent unit, stage, actual interval,
  quantity/unit, missingness and calibration status.
- Extend structured intervals to eligible empirical observations and link them
  to exact source locators. Keep source-review records and dataset eligibility
  separate from machine-checked range containment.
- Add claim/source/assumption links, exact figure/table/workbook locators,
  reviewer identity/date/rationale and revision/supersession records.
- Separate reported experiments, institutional announcements, regulator
  discussions and hypotheses. Record adverse and null observations and
  distinguish physiological support from growth/development outcomes.

**Acceptance:** tests reject incompatible species, unsupported intervals,
source-class promotion and contradictory missingness/calibration fields.
Updating a source cannot silently change an existing reviewed claim.

The [mouse developmental study](https://www.nature.com/articles/s41586-021-03416-3)
and [FDA artificial-womb discussion](https://www.fda.gov/media/172252/download)
address distinct stages and questions. The
[preterm-lamb study](https://doi.org/10.3389/fphys.2023.1219185) also makes growth
limitations important to the evidence map. These sources do not establish
continuous human development from fertilization through birth.

## M5 — Make model bundles independently verifiable

Coordinate with [RegenWorkbench's roadmap](https://github.com/dylanstechmann/regen-workbench/blob/main/ROADMAP.md).

**Delivered 2026-10-07.** `identifiability-report` bundles copy the exact source
`simulate` receipt in as `source_receipt.json` and declare its hash and filename
in their own receipt metadata, so ancestry resolves after the source directory is
deleted. Every bundle now carries `reproduction_plan.json` with the package
version, Python version, declared dependencies, command template, inputs, the
complete expected file set and interpretation limits, and no absolute paths.
`wombmodels verify-bundle` validates receipt structure without a schema library,
rejects symlinked and oversize outputs before reading them, recomputes every hash
and byte count, and resolves the declared parent receipt. It reports
`bytes_verified`, `ancestry_resolved`, `scientific_review`
(`not_established_by_this_tool`) and `reproduction` (`not_attempted`) as separate
statuses; `--strict` also fails on undeclared files and unpublished bundle kinds.
Fifteen cases cover changed, missing, swapped-parent, symlinked, undeclared,
malformed-receipt and relocated bundles, including one that verifies a copied
bundle after deleting its source directory.

- Remaining: a rerun harness. Verification does not execute the recorded command,
  so "verified" and "reproduced" remain different claims. Bundles other than
  `identifiability-report` have no parent, so their ancestry status is
  `no_parent_declared` rather than resolved.

**Acceptance:** a fresh environment can verify and rerun the synthetic example;
missing parents or changed bytes fail explicitly. ResearchDesk remains an
optional consumer, not a runtime requirement of the model package. *Verification
and explicit failures are met; automated rerunning is not.*

## M6 — Establish an empirical benchmark with appropriate units

Begin the data-access audit early; fit only after the plan is frozen.

The [2026-10-09 interface source qualification](SOURCE_QUALIFICATION.md)
records a bounded Hori/Bhide file audit and executable candidate Hori endpoint
intake. The inspected files lack the linked trajectories and independent-unit
identities required for the dynamic benchmark. Human review and appropriate
source reuse confirmation remain pending; M6 is not complete.

- Select openly licensed measurements relevant to a stated equation, with
  accessible independent-unit IDs, units, uncertainty and instrument context.
- Write a source/license card and applicability assessment. A developmental
  paper is not automatically a calibration dataset for a transport model.
- Prespecify outcomes, exclusions, independence level and grouped splits.
  If units or identifiers are unavailable, retain a descriptive analysis and
  label the missing validation opportunity.
- Compare simple alternatives and model discrepancy on held-out units; publish
  negative results and sensitivity to unverified assumptions.

**Acceptance:** licensed reproducible intake, frozen unit-safe evaluation,
data/model mismatch review and an externally reviewed methods report. No claim
of clinical prediction, complete gestation or reduced congenital defects.

## M7 — Add physiological scope only where it can be tested

After the relevant verification and data gates, consider coupled transport,
growth/remodeling or endocrine observation models. Each proposal needs an
explicit question, equations, parameter provenance, measurements, a simpler
comparator, identifiable quantities and falsifiers before implementation.

Do not prioritize additional disconnected toy models, a gestation readiness
score, device assembly instructions or biological operating parameters. The
most useful contribution is a model whose limitations another researcher can
reproduce and challenge.

## Order and reviewable outputs

1. Stage-transition/source-review records, executable observation validation
   and empirical data qualification (E1–E3; M4 and the M6 intake audit),
   alongside bounded numerical/uncertainty work (M1–M2).
2. One frozen empirical interface question and eligible baseline comparison
   (E4/M6), or an explicit data/non-identification report if the gate fails.
3. Portable verified dossier (E6/M5) and the synthetic observer benchmark
   after forecast calibration (E5; M2–M3).
4. A scoped next model or methods manuscript after independent review (M7).

Each milestone should produce a small release, executable example, documented
negative cases and concrete contributor tasks. A reviewed benchmark and
methods write-up are stronger evidence of research software ability than
repository count; they do not guarantee novelty, publication or employment.

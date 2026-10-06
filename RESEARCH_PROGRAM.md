# Research program: from separate demonstrations to testable ectogenesis questions

Planning revision: **2026-10-06**. Status: proposed research and software work.
The long-term objective is complete human ectogenesis from IVF through birth,
including normal development and later function. This document specifies how
the repository can reduce particular uncertainties toward that objective.
It provides no demonstrated continuous gestation system or operating protocol.

The next flagship should be a stage-transition map and one eligible empirical
benchmark. Numerical verification is essential supporting work, but extending
dimensionless examples indefinitely will not identify missing biological
functions. Coordinate implementation with [ROADMAP.md](ROADMAP.md) and the
[ResearchDesk portfolio plan](https://github.com/dylanstechmann/regen-workbench/blob/main/RESEARCH_PROGRAMS.md).

## 1. Treat the objective as a chain of biological transitions

A wall-powered support system would have to preserve the functions needed at
each stage and across changing interfaces. Supplying energy to equipment is
only one engineering requirement. The research map must distinguish
embryonic/extraembryonic development, maternal interface functions and later
partial-support machinery.

| Research interval | Important unknown or interface | Evidence that would address it |
| --- | --- | --- |
| Preimplantation development | Appropriate developmental progression and the starting state for implantation | Source-defined stage, lineage/identity, attrition and outcomes in the actual model system |
| Implantation and interface establishment | Endometrium/decidua, trophoblast interaction, compartment organization and emerging exchange | Measured interactions and perturbation outcomes, spatial/lineage context, barrier and functional observations |
| Embryonic and extraembryonic development | Coordinated patterning, vascular/interface development and sustained exchange while demand changes | Same-unit longitudinal progression, organ/lineage outcomes, exchange observations, losses and comparators |
| Fetal support | Support capacity together with growth, organ maturation and developmental function | Individual-unit support records and independent developmental endpoints with comparable controls |
| Transition to neonatal life | Successful transition from the supported state to subsequent physiological function | Transition outcomes, attrition, adverse events and the ascertainment window |
| Longer follow-up | Durable organ, neurological, reproductive and other relevant outcomes | Follow-up of the complete starting cohort, missing follow-up and appropriate comparators |

These rows are research requirements, not demonstrated modules that can be
connected together. A study beginning after implantation does not fill the
preceding transition. A cohort of already-developed fetuses does not fill
embryonic development. Record source-species conventions without converting
mouse embryonic days into human gestational ages.

**Proposed transition record:** source revision and exact figure/table locator;
species and model system; actual start/end interval and convention; starting
and ending biological states; unit IDs; whether the same unit crossed the
transition; interfaces maintained or replaced; comparator; endpoint and
follow-up; attrition/adverse findings; review decision; remaining requirements.
Represent same-unit continuity as `demonstrated`, `contradicted` or
`not_reported`, with source-linked unit IDs. Missing IDs preserve uncertainty;
they do not establish continuity or its failure.

The graph should show supported edges, incompatible comparisons and unknown
edges. It must never infer a continuous IVF-to-birth path by joining results
from different species or disconnected units. Do not turn graph coverage into
a gestation-readiness percentage.

## 2. Update the evidence frontier through a review queue

The existing [ledger](EVIDENCE.md) contains a bounded five-source baseline.
The following primary sources make the next review queue more useful. This
planning shortlist does not promote new claims into the reviewed ledger;
source transcription, dataset qualification and human review remain separate.

| Candidate | Why inspect it | Question or access boundary |
| --- | --- | --- |
| [Modeling human embryo implantation in vitro, Cell, 2026 issue](https://doi.org/10.1016/j.cell.2025.10.027) | Reports embryo/endometrial-model implantation and day-14 interface analysis | Early interface development; does not supply evidence for a completed pregnancy. Review actual units, stages, controls and exclusions. |
| [Hori et al., 2024 placental barrier organoids](https://www.nature.com/articles/s41467-024-45279-y) | Reports selected barrier, permeability and endocrine observations and links Source Data | Audit the actual files, units, replicate hierarchy and geometry before selecting a transport model. |
| [Bhide et al., 2026 placenta-on-chip record](https://pubmed.ncbi.nlm.nih.gov/42269672/) / [DOI](https://doi.org/10.1088/1758-5090/ae7bc8) | Candidate two-compartment glucose/urea exchange measurements | Bibliographic candidate; full data/rights/independent-unit eligibility is unresolved. |
| [2026 maternal–fetal interface atlas](https://www.nature.com/articles/s41586-026-10316-x) / [author portal](https://cell.ucsf.edu/snPlacenta/) | Reference cell states and spatial context for comparison with models | Processed data are offered through the portal; raw FASTQ access is controlled under `phs004305.v1`. Sampling site and actual stage matter. This is an identity/context reference, not transport calibration. |
| [Aguilera-Castrejon et al., 2021](https://www.nature.com/articles/s41586-021-03416-3) | Existing mouse postimplantation interval in the ledger | Preserve its actual start and end, outcome denominators and unresolved later transition. |
| [Usuda et al., 2023](https://doi.org/10.3389/fphys.2023.1219185) | Existing example of physiological support coexisting with reduced somatic/organ growth | Organize maintenance and development as separate outcomes; inspect the eligible unit-level data and control comparability. |
| [FDA committee summary, 2023](https://www.fda.gov/media/172441/download) | Evaluation context for partial fetal support, maturation, transition and follow-up | Regulator discussion; preserve its intended-use scope and source class. |

Every data card should record retrieval location/version, reuse and
redistribution terms, hashes, file sizes, raw versus author-summary status,
independent-unit hierarchy, actual interval, quantity/unit, calibration,
uncertainty, groups, missingness and eligibility decision. A publicly readable
paper is insufficient evidence that an eligible calibration dataset exists.

## 3. Make three questions concrete before adding model scope

### E-Q1: What separates an interface with the right cell states from one with adequate function?

Competing explanations include missing cell states, altered spatial
organization, and an interface that resembles a reference molecularly but has
different barrier/exchange behavior. Transcriptomic and functional analyses
need separate endpoints and compatible source intervals.

**First analysis:** one model-versus-reference cell-state comparison, grouped
by donor/source and stage, using a frozen annotation and preprocessing plan.
Compare simple reference-based labels with any more complex representation.
Retain out-of-distribution samples, sampling-site effects and sensitivity to
batch correction. A separate barrier-function dataset can motivate a next
question; it cannot supply paired function for these cells unless unit-level
linkage actually exists.

**Discriminator:** a prespecified state/identity discrepancy that recurs in
held-out source units, with any source-linked functional evidence reported
independently. Similar expression alone leaves the function hypothesis
unresolved. Apparent discrepancies disappearing under source/site matching
favor a confounding explanation.

### E-Q2: Which transport quantities can the measurements identify?

Compare passive exchange with exchange plus uptake/loss, and with a simple
well-mixed alternative where the observation contract supports it. Specify
the measured collection process, capacities, boundary input and geometry.

**First analysis:** qualify Hori/Bhide candidate data, then freeze one limited
dimensional model and an independent-unit split. Keep the current dimensionless
model intact as a software test. Estimate effective transfer/clearance terms
that the observations identify; without independently observed interface area,
do not present permeability and area as separately recovered parameters.

**Discriminator:** prediction of held-out measured concentrations/fluxes with
error and uncertainty compared against the simpler model. Test whether distinct
parameter combinations or model structures produce indistinguishable
predictions for the measured observables. If the
available inputs/outputs do not identify the model, publish that result and
the exact missing measurement rather than adding parameters.

### E-Q3: What can stay supported while development diverges?

Use same-species, comparable-stage partial-support evidence to distinguish
maintenance, growth, organ maturation, function and follow-up. Candidate
explanations include inadequate exchange, absent signaling, model-specific
developmental mismatch, and cohort/measurement differences; they are
hypotheses rather than diagnoses of a published system.

**First analysis:** structured source extraction and an eligibility audit for
one developmental-outcome reanalysis. Require individual units, starting
intervals, comparator structure, repeated measurements, attrition and adverse
findings before fitting. Keep support duration, survival and follow-up
denominators separate.

**Discriminator:** a source-supported discordance between independently
measured maintenance and development, followed by an analysis that can
distinguish at least two explanations. If only aggregate figures exist, the
deliverable remains a descriptive discrepancy/data-access report. Never
invent subject-level trajectories or infer normal development from survival.

## 4. Deliver the work in bounded packages

| Package | Deliverable and owner | Dependencies | Acceptance / stop rule |
| --- | --- | --- | --- |
| **E1 — Stage and transition contract** | This repo: structured question/transition records, source-review queue, interval containment and same-unit checks | No empirical fit required | Every supported edge resolves to reviewed evidence; species/source-class concatenation fails; unknown edges persist |
| **E2 — Executable observation intake** | This repo: stdlib `validate-observations`, typed quantities, unit hierarchy, source revisions, outcome/missingness fields | E1 contract; coordinate Desk dataset cards | Reject inconsistent units/intervals/calibration and repeated-observation independence. Missing identities restrict the analysis scope |
| **E3 — Data qualification** | Desk coordinates cards; methods owner audits candidate files and observable/model applicability | E2; permissions and actual downloadable files | One accepted or rejected candidate with inspectable reasons and adequate independent units for the proposed evaluation. Reject incompatible data before choosing a favorite model |
| **E4 — One empirical question** | This repo owns a qualified transport model; Desk owns orchestration. A cell-state study can use existing sibling methods separately | E3 plus frozen analysis/splits and relevant solver verification | Exact observed quantities, simpler baseline, group-level predictions/errors, uncertainty and mismatch. Insufficient independent units restrict the result to descriptive reproduction/non-identification; an inconclusive result is a valid release |
| **E5 — Forecast/observer methods** | This repo: frozen calibration/evaluation scenarios, independent seeds/schedules, rank/profile diagnostics and a past-only observer | Current solver baseline; M2 precedes M3 | Report horizon error/bias/width/coverage and unavailable/failure counts. Future readings, injected labels and hidden truth cannot enter prediction |
| **E6 — Portable review** | This repo verifies bundles; Desk verifies dossiers and pins scientific revisions | E1–E4 artifacts; coordinate M5 and Desk R1–R3 | A relocated example verifies and an eligible public analysis reruns; human review status is independent of byte integrity |

E1–E3 should start now alongside finishing the supported numerical domain.
They do not require waiting for every imaginable synthetic stress case.
E4 is gated by data/model applicability, not by repository activity or a
successful-looking synthetic trace. E5 can progress in parallel as explicitly
synthetic methods development.

### Proposed first release tasks

- Define the transition and observation contracts with incompatible-species,
  interval, missingness and same-unit negative examples.
- Implement the observation validator and a source-review revision format.
- Qualify two functional-interface candidates and one identity/reference
  candidate; retain excluded candidates and reasons.
- Freeze one question card naming competing predictions, estimand, baseline,
  unit split, uncertainty method and ambiguity conditions.
- Retain the current solver verification; close its milestone for the
  explicitly supported numerical domain rather than claiming arbitrary
  physiological coverage.

### Proposed second release tasks

- Run the eligible narrow analysis, including the simpler comparator and
  prespecified sensitivities.
- Export each prediction and each unavailable/excluded biological unit.
- Verify source ancestry, implementation and reproduction instructions in a
  portable dossier; obtain source/method review before expanding conclusions.
- Identify the next observable that would resolve remaining ambiguity.

## 5. Gate subsequent scope by identifiable questions

Coupled endocrine, growth/remodeling, spatial transport or developmental
control models become candidates only when each has a stated biological
question, an observable/data contract, parameter provenance, a simpler
alternative and a result that could contradict it. Distinguish source-reported
physiology from fitted predictions and computational hypotheses.

A later continuous-gestation claim would require evidence for the complete
same-unit path and its outcomes. Partial support, implantation models and
organoid barrier results are valuable intermediate research but leave that
claim unresolved. This repository should make those missing transitions and
needed observations clearer to researchers, while retaining the full ambition.

## 6. Open-source completion criteria

Publish bounded releases containing the exact question, qualified source/data
cards, versioned analysis plan, executable example, baseline, uncertainty,
failure cases and reproduction inventory. Preserve rejected hypotheses and
data eligibility failures. Credit the biological source authors and reviewers;
describe our contribution as software, data curation, reproduction or a
specific tested method until independent review supports a stronger claim.

The next valuable output is a narrow, reusable research result with a clear
remaining uncertainty. It can help a laboratory choose a discriminator or
reproduce an analysis even when the favored hypothesis fails.

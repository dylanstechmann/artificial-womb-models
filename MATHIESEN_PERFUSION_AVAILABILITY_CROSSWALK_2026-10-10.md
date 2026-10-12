# Mathiesen 2020 source availability crosswalk

This crosswalk maps the candidate intake fields in
[PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md](PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md)
to the inspected Mathiesen et al. public record. Its machine-readable form is
[`mathiesen_2020_placental_perfusion_crosswalk.json`](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).
The source remains a candidate: transcription and scientific review are
pending, and no author was contacted.

## Scope and status meanings

The primary [PLOS ONE article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979)
was reviewed for its Methods, perfusion description, analytical methods,
statistical methods and supporting-information captions. The S1 Data workbook
was parsed in the existing source-cell audit. The S1 Table selection counts
were checked. S2–S4 table structure and headers were checked, and the S3 `nr`
keys were inspected without transcribing donor/questionnaire measurements.
Table 1 was visually checked twice for the run ID, antagonist and acceptable
duration entries; other columns were not transcribed. Independent human review
is still pending.

Availability states describe only that inspected record set. `reported` means
the cited source contains the statement or value. `partially_reported` means
that some needed unit-level or measurement detail is missing. `described_without_numeric_source_values`
means the article says the measurement occurred but the numeric records were
not located in the inspected files. `not_found_in_inspected_files` is bounded
to the named artifacts and does not mean the measurement never happened.
`unresolved_linkage` means a matching key or count does not establish an
identity relationship. `outside_study_scope` means this experiment's stated
design and outcomes do not address the claim. `not_assessed` is reserved for an
explicit source statement that a measurement was not done.

## Field-by-field result

| Intake field | Availability | Evidence and practical limit |
| --- | --- | --- |
| Study frame and material | Partially reported | Methods describe ex vivo term human placentas from the Copenhagen Maternal Stress and Placental Function project and 22 placenta perfusions. The perfusion numbers are not verified donor identities or proven independent units. [Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec006) |
| Donor-to-perfusion identity | Unresolved linkage | S3's unique `nr` values (1–22) match Table 1's ID values, and S3 contains donor questionnaire data with selected perfusion outcomes. The article does not define `nr` as the Table 1 ID or give a crosswalk. No join is made. [S3](https://doi.org/10.1371/journal.pone.0233979.s003) |
| Selection denominators and disposition | Unresolved linkage | The article reports 22 perfusions: 2 early leaks, 5 later leaks after four hours, and 15 successful six-hour runs. S1 Table separately reports 48 received, 43 cannulated, 26 successful pre-perfusion/substance-added cases and 15 successful six-hour perfusions. The relationship between these frames is not stated, so the denominators remain separate. [Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec006), [S1 Table](https://doi.org/10.1371/journal.pone.0233979.s001) |
| Test substances and exposure arms | Reported, with run map pending | The article describes maternal-side cortisol, cortisone, tryptophan and serotonin, plus inhibitor arms. The S1 Data workbook additionally includes 5-HIAA concentrations. The per-run condition transcription remains unverified by an independent reviewer. [Perfusion Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec008), [S1 Data](https://doi.org/10.1371/journal.pone.0233979.s005) |
| Compartments, units and time labels | Reported | S1 Data reports five analytes in nM for maternal and fetal systems over source-labelled timepoints and 22 numbered runs. `Mbefore` and `Fbefore` remain textual pre-exposure labels, not invented elapsed times. This is concentration evidence, not an amount or flux. [S1 Data](https://doi.org/10.1371/journal.pone.0233979.s005) |
| Perfusion setup and medium context | Partially reported | The article describes an ex vivo single-cotyledon model with maternal and fetal recirculating compartments and selected medium/temperature details. The intake records availability only; it does not convert those descriptions into operating instructions or claim complete setup reporting. [Perfusion Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec008) |
| Duration and acceptability | Partially reported | The article reports 2 early leak failures, 5 leaks after four hours and 15 six-hour perfusions. The current Table 1 transcription classifies 15 as acceptable for six hours and 7 as shorter-duration runs. The run map remains pending human verification. [Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec006), [Table 1 image](https://journals.plos.org/plosone/article/figure/image?download&size=large&id=10.1371/journal.pone.0233979.t001) |
| Quality-control criteria and per-run values | Partially reported | Methods state fetal-system volume-loss and antipyrine feto-maternal-ratio criteria; success/failure counts are aggregated. Per-run criterion values and other Table 1 columns were not extracted or verified, so their availability is not classified as absent. [Perfusion Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec008) |
| Sample volume and removed-volume history | Described without numeric source values | Methods say fetal reservoir volume was observed after each sample and maternal/fetal volumes were measured at the end. No numeric per-sample removal series or per-run final volumes were located in the inventoried public files. This does not show that these quantities were never measured. [Perfusion Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec008) |
| Oxygen, glucose and pH values | Described without numeric source values | The article says these were measured and regulated during perfusion, but no numeric series appears in the audited concentration workbook or inspected supplemental tables. [Perfusion Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec008) |
| Analytical method and calibration | Partially reported | The article identifies methods and selected instrument conditions; detailed cortisol/cortisone quantification is referred to another publication. Calibration curves, precision/uncertainty, chromatograms and analyte recovery/inventory records were not found among the inventoried public artifacts. [Analytical Methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979#sec009) |
| Concentration observations and missingness | Partially reported | The audited workbook contains 2,908 numeric cells and 282 blanks among 3,190 expected cells. The article attributes missing data globally to analysis errors but does not give a cause per blank. A blank is not treated as zero, no measurement or biological failure. [S1 Data](https://doi.org/10.1371/journal.pone.0233979.s005) |
| Embryo, gestation, birth and later health | Outside study scope | The stated design and endpoints concern ex vivo placental perfusate and placental transport/metabolism. This source cannot qualify embryo development, continuous gestation, birth, neonatal transition or later health. [Article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979) |

## Proposed claim gates

These are source-specific intake criteria to guide the next review, not a
validated reporting standard or a guarantee that a claim will be identifiable.

| Claim | Current decision | Evidence that would change the decision |
| --- | --- | --- |
| Source-cell concentration description | Candidate after human review | Independent verification of transcription and run mapping, plus a receipt-bound reproduction that retains original labels, blanks and late-window flags. The claim stays descriptive. |
| Between-arm or duration comparison | Not yet eligible | Verified run-to-arm/duration map, source-located run-level acceptance and denominator, independent-unit grouping, and a frozen descriptive comparison plan. |
| Dimensional transport or mass balance | Ineligible with inspected record set | Per-run initial/final compartment volumes; sample removal/return/addition history; dose, metabolism and recovery accounting; assay calibration/uncertainty; and verified run quality/unit records. |
| Donor-level stress or covariate association | Ineligible pending identity and disposition | Explicit donor-to-perfusion key, individual covariate/outcome records, same-cohort selection and missingness disposition, and verified independent-unit structure. Matching numeric IDs alone do not establish identity. |
| Embryo development or integrated gestation | Outside this source's scope | A separate same-embryo record across the transition under study, with time-linked developmental/function outcomes and complete disposition; birth and later-health claims also need observations through those endpoints. |

## What this changes

The intake now distinguishes four separate evidence layers: concentration values
that are present, methods that are described, numeric records not located in
the inspected package, and key relationships that remain unverified. That
supports source-cell descriptions after human review, while keeping dimensional
transport fitting, donor-level associations and developmental claims ineligible
on the current evidence. The concrete unlock conditions and claim ceilings are
also encoded in the [JSON crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

## Related public-source search

A bounded search found one stronger public candidate for the accounting gaps:
[Spiess et al., *Placental Passage of Protopine in an Ex Vivo Human Perfusion
System*](https://pmc.ncbi.nlm.nih.gov/articles/PMC9868778/). Its primary article
defines a recovery calculation using concentrations and volumes in the maternal,
fetal and sampled fractions, with an empty-system adherence correction. It
states that the linked supplement contains absolute concentration profiles,
recovery results, placenta characteristics, individual-perfusion details and
bioanalytical-method information. This is a high-priority public source for a
bounded follow-up because it may resolve some of the specific observation
fields missing from the Mathiesen package.

The publisher supplement itself remains uninspected: its PMC link returned an
access challenge, and the author's institutional-repository landing page shows
a request-copy state. A second public-record pass found searchable dissertation
text that exposes the Table 3S field layout: compound-group experiment numbers,
placenta/cotyledon characteristics, total maternal/fetal volume loss at
experiment end, and phase/perfusion timing. The primary article's figures and
Table 1S remain group summaries for concentration and recovery. The indexed
excerpt does not expose timepoint-resolved removal or reservoir volumes and does
not establish cross-compound placenta identity. I recorded this distinction in
the [bounded follow-up screen](SPIESS_2023_PERFUSION_SUPPLEMENT_SCREEN_2026-10-10.md),
without transcribing or importing NC-ND table contents. The term-placenta study
also cannot provide embryo-development or whole-gestation outcomes. Keep its
values separate from Mathiesen 2020.

The 2024 tofacitinib paper is a lower-priority screen: it describes estimating
remaining volumes and reports recovery, but says its data will be made available
on request, so this search did not identify public individual records. Neither
paper prompted author contact. The candidate and remaining checks are
machine-recorded in the JSON crosswalk.

A second, fully readable public comparator is [Spiess et al. 2023 on
hyperforin, hypericin and valerenic acid](https://www.frontiersin.org/journals/pharmacology/articles/10.3389/fphar.2023.1123194/full),
with its [supplementary PDF](https://www.frontiersin.org/api/v4/articles/1123194/file/Data_Sheet_1.PDF/1123194_supplementary-materials_datasheets_1_pdf/1).
The supplement's concentration curves and recovery values are reported as
group means ± SD. Its per-experiment table includes placenta/cotyledon weights
and total maternal/fetal volume loss at the end, plus setup-time fields; it does
not show timepoint-specific volume histories or individual concentration
trajectories. It also includes calibrator and QC summaries with SD, CV% and
relative error. This improves the field-availability comparison, but the
aggregate curves are not a substitute for the missing run-level data and belong
to different compounds and donors.

In a direct PDF inspection (Cycle 242), the figure and table denominators align
within each compound (4 hyperforin, 3 hypericin, 4 valerenic-acid perfusions),
but the table's experiment-number blocks do not map individuals to the
mean±SD curves or establish shared placenta identities across compounds. Its
volume-loss field is a signed end-of-run total, not a time-resolved
sample-removal history. See the [Cycle 242 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-frontiers-field-availability-cycle242.json).

A nutrient-transfer mechanism comparator is [Hirschmugl et al. 2021](https://www.nature.com/articles/s41366-021-00781-x). Its main article reports group-level labeled-fatty-acid clearance and endogenous release alongside fitted model parameters, and distinguishes observed states from model-only compartments. The retrieved five-page supplement adds group-level mixture, quality-control, study-population, and tissue-uptake summaries, but no run-level source rows or volume/removal join. The term-placenta result is not a dimensional-fit dataset or evidence of embryo support; see the [bounded source screen](HIRSCHMUGL_2021_FATTY_ACID_PERFUSION_SOURCE_SCREEN_2026-10-10.md).

A newer, partial comparator is [Loza et al. 2026 on onabotulinumtoxinA](https://obgyn.onlinelibrary.wiley.com/doi/full/10.1002/pmf2.70363).
The publisher article reports five successful term-placenta perfusions and
trial-labeled concentration figures. Fetal samples were collected at 30-minute
intervals across all five runs, while maternal concentration series were
reported for only the last two. The article names three missing fetal
antipyrine figure timepoints and gives an approximate 40–50 pg/mL functional
assay limit for onabotulinumtoxinA; its reported fetal non-detections therefore
do not establish zero transfer. The article and linked PDF expose no
machine-readable concentration table, no timepoint-specific sample-removal or
reservoir-volume history, and no explicit data-availability statement in the
inspected publisher files. Treat its figures as an observation-schema and
missingness comparator, not source-exact raw data or a dimensional transport
dataset. It is a term-placenta xenobiotic study and supplies no embryo,
gestation, birth or later-health outcomes. No author was contacted. The
field-level screen is recorded in the JSON crosswalk.

Another useful but incomplete comparator is [van Kammen et al. 2025 on targeted
lipid nanoparticles](https://link.springer.com/article/10.1007/s13346-024-01715-6).
Its main article plots maternal and fetal circulation volumes over time as
mean ± SD across three placentas, together with transfer profiles. The
supplementary DOCX was retrieved from the publisher route and inspected: its
Table S1 gives placenta-labeled pH summaries, qualitative leak observations,
and paired outflow values, but repeats the same wording in its final two
column headers. I left those two values unmapped. The supplement does not
contain the numeric per-run volume or concentration trajectories, and the
article says its datasets are available on reasonable request. This makes the
paper useful for recording volume trajectories and ambiguous source labels,
but it cannot support a source-exact per-run mass balance. No author was
contacted. The machine-readable candidate screen retains the article and
supplement routes and these limits.

A broader public-repository search is summarized in
[`PERFUSION_DATA_REPOSITORY_SCREEN_2026-10-10.md`](PERFUSION_DATA_REPOSITORY_SCREEN_2026-10-10.md).
It found useful partial comparators and adjacent evidence lanes, but no
repository record meeting the paired per-run concentration plus
volume/removal-history gate. The search was bounded and does not establish that
such records do not exist elsewhere.


## Current model-identifiability consequence (Cycle 230)

A comparison of the three recently screened drug-transfer sources leaves the
transport-calibration gate unchanged. Mathiesen 2020 is the only one with an
audited concentration workbook, but the inspected package lacks a numeric,
per-run sample-removal and remaining-volume ledger tied to those concentration
rows. Heggarty 2025 supplies figure-level endpoints without source-exact point
values or time/volume histories. Benoit 2026 supplies abstract-level aggregate
metrics only; its public repository/index checks have not surfaced a dataset or
open article location. Keep the sources separate.

A concentration-level descriptive review may be possible for Mathiesen after
human source-cell verification, with the native time labels and unresolved
run/acceptance links preserved. A dimensional two-compartment transport fit
remains ineligible. The most consequential missing input is a per-run,
time-resolved ledger linking concentrations to initial and remaining
compartment volumes and to sampled, removed, returned or added volumes;
verified run identity, disposition, assay uncertainty and recovery accounting
are also required. End-of-run volume loss or group recovery alone cannot supply
that ledger.

The Spiess et al. 2023 protopine supplement remains the highest-potential
source, but the Europe PMC API exposes only article XML metadata and a relative
file name; its separate file route returned 403, and the Thieme article-PDF
route returned 404. The supplement has not been retrieved or transcribed. See
the [Cycle 241 route receipt](artifacts/perfusion-comparability-2026-10-11/spiess-europepmc-publisher-route-cycle241.json).
The accessible Spiess Frontiers comparator can still inform field availability,
but its aggregate curves and endpoint-volume rows do not provide a per-run
time-resolved mass balance. These studies inform a placental measurement pathway
only and do not establish embryo development, continuous gestation, birth or
later health in an artificial womb. See the [Cycle 230 receipt](artifacts/perfusion-comparability-2026-10-11/transfer-identifiability-screen-cycle230.json).

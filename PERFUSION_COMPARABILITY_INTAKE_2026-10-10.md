# Candidate intake fields for ex vivo placental-perfusion studies

This is an evidence-intake vocabulary, not an experimental protocol or a
validated standard. It is based on Glättli et al.'s 2024 review and its
supporting setup tables, plus the separate unresolved fields in the Mathiesen
2020 source audit. The review searched through 2022 and covered therapeutic
drug-transfer studies in uncomplicated full-term placentae with fixed
within-run setups. It did not analyze transfer outcomes, embryonic development,
continuous gestation or birth.

## Record each field with its provenance

For every reported value, retain the source publication, exact locator, original
label and unit. Keep availability separate from provenance: `reported`,
`partially_reported`, `described_without_numeric_source_values`,
`not_found_in_inspected_files`, `unresolved_linkage`, `conflicting_sources`,
`outside_study_scope`, or `not_assessed`. Use `not_assessed` only when the
source explicitly says the measure was not done. The 2024 review's supplements
group some missing states together as “unmentioned, omitted or no coherent
data”; preserve that source ambiguity rather than translating it into a claim
that a measurement was not performed. Record whether information came from the
primary report, a cited protocol, a supplement, or a derived screen. If primary
and cited methods disagree, record both and mark the conflict unresolved.
Never fill missing records by copying a protocol from another laboratory.

## Candidate field groups

- **Study and sample frame:** citation, laboratory, study period, placenta/run
  identifiers, stated donor-to-perfusion key, gestational stage, source
  denominator, inclusion/exclusion rules and disposition counts. Keep a
  numbered run distinct from a verified donor or independent biological unit.
- **Transfer direction:** maternal-to-fetal, fetal-to-maternal, bidirectional
  or equilibrium. Keep direction attached to each experiment and outcome.
- **Preparation:** source-reported treatment/transport context, time from
  delivery to setup, and the reported cannulation and wash descriptors. These
  are documentation fields only; this intake does not prescribe their values.
- **Control and acceptance:** reference marker, control-period description,
  stated integrity/viability checks, pass/fail criteria, exclusions and the
  time interval for which each run remains acceptable.
- **Test substance:** identity, source-reported concentration and unit, which
  compartment received it, and any stated co-exposures or modifiers.
- **Experimental compartments:** system configuration, elapsed-time labels,
  compartment identity, medium descriptors and any reported flow, volume,
  temperature, pressure, pH or gas context. Preserve native units and labels.
- **Collection and analysis:** sample times and volumes, removed-volume
  accounting, starting and final compartment volumes, analyte identity, assay
  method, calibration and uncertainty, recovery/inventory, and tissue-viability
  measures. Keep concentration-only results distinct from amount, transfer,
  clearance or flux estimates.
- **Outcomes and missingness:** exact outcome definition, numerator and
  denominator, excluded runs, blank cells and source-stated reasons. Do not
  infer success or failure from an absent number.

The phase groups and reported parameter families are drawn from the review's
preparation, control, drug and experimental tables. The additional collection,
calibration and recovery fields are retained because the Mathiesen 2020 files
do not contain the volume/removal history or analytical records needed for a
dimensional mass balance.

## Application to the current Mathiesen source

The existing audit preserves the five analytes, maternal/fetal reservoir labels,
source time labels, run map and missing cells. It records the S3 `nr`/Table 1 ID
match as a candidate link only and performs no join. Methods mention that
reservoir volumes were observed, but the inspected source files lack numerical
per-sample removal histories and per-run end volumes. Calibration, uncertainty,
original instrument records and inventory/recovery are also absent from the
public files inspected. Therefore this vocabulary can strengthen future source
comparison, but it does not make the current values eligible for a dimensional
transport fit.

The 2024 review's study-level setup tables and their local hashes are listed in
the [source inventory](config/source_inventories/mathiesen_2020_placental_perfusion.json).
I inspected table labels and structure only; I did not transcribe the
study-specific setup values. No author was contacted.

The source-specific [availability crosswalk](MATHIESEN_PERFUSION_AVAILABILITY_CROSSWALK_2026-10-10.md)
and its machine-readable [JSON record](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json)
apply these states to the article and supplements. The crosswalk scopes every
absence claim to the exact public files and portions inspected; it does not
equate an unlocated numeric record with a measurement that was never made.

## Source-priority recheck (Cycle 240)

The Spiess et al. 2023 protopine supplement remains the highest-potential
public target because it may contain absolute concentration profiles, recovery,
perfusion details and bioanalytical information, while indexed Table 3S text
exposes endpoint volume-loss fields. Its file remains inaccessible through the
inspected official PMC route, which served challenge HTML; the repository lists
request-copy access. The accessible Frontiers Spiess comparator includes
per-perfusion endpoint volume loss but only group-mean concentration curves.
Neither closes time-resolved accounting. Mathiesen remains the strongest
audited concentration dataset, but its numeric removal/final-volume ledger was
not found in inspected files. No source meets the dimensional-fit gate. The
bounded ranking and route boundary are recorded in the [Cycle 240 receipt](artifacts/perfusion-comparability-2026-10-11/perfusion-source-priority-recheck-cycle240.json).

Cycle 241 checked Europe PMC's full-text XML and the publisher-PDF metadata
route. The XML names the supplement, but Europe PMC's separate file-serving
path returned 403 and the checked publisher route returned 404. No file bytes
were obtained. Close that route screen; the accessible Frontiers Spiess paper
is the next comparator for a field-availability audit, not dimensional fitting.
See the [Cycle 241 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-europepmc-publisher-route-cycle241.json).

Cycle 242 confirmed that the accessible Spiess Frontiers supplement's
experiment-table denominators match the per-compound group-curve denominators,
but it provides no run-to-curve key or time-resolved volume/removal history.
Its endpoint volume-loss rows cannot be paired with aggregate curves to make a
per-run mass balance. The next audit target is the existing Eliesen 2024
individual-trajectory intake. See the [Cycle 242 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-frontiers-field-availability-cycle242.json).

Cycles 243–245 audited that intake against the pinned DOCX, recomputed all
three-placenta concentration means/SDs, and used the antipyrine Table S2 as a
same-document mapping control. The 70 Table S3 cells reconcile, and the S2
180-minute endpoints match the article after rounding. However, the Table S3
fetal 180-minute values derive to 25.0 ± 5.0 nM versus 24.8 ± 4.7 nM in the
Results text. Keep that mismatch unresolved. Cycle 246 found no linked dataset
in the Crossref relation field or exact DataCite related-identifier query; the
publisher states data are available on request. These are bounded route checks,
not proof of global absence. The intake still lacks the per-run
volume/removal/recovery join and remains ineligible for dimensional fitting.
See the [source-cell audit](artifacts/perfusion-intake-2026-10-10/eliesen-table-s3-source-reconciliation-cycle243.json),
[summary check](artifacts/perfusion-intake-2026-10-10/eliesen-table-s3-group-summary-cycle244.json),
[mapping control](artifacts/perfusion-intake-2026-10-10/eliesen-antipyrine-s2-endpoint-control-cycle245.json), and
[public route screen](artifacts/perfusion-comparability-2026-10-11/eliesen-public-dataset-route-screen-cycle246.json).

Cycle 247 re-ranked the remaining public candidate files and inspected the
Mandelbrot 2019 S1 XLSX/CSV because it contains individual labeled
concentration, ratio and clearance-index observations. All 658 selected field
value lexemes match, but 68 antipyrine-ratio shared-formula followers are not
identified as formula cells in the CSV; shared-formula group metadata and a
repeatable source audit remain needed. S1 still lacks a linked volume/removal/
recovery ledger, so it does not close the dimensional-fit gate. See the
[Cycle 247 receipt](artifacts/perfusion-intake-2026-10-10/mandelbrot-s1-source-cell-triage-cycle247.json).

Cycle 248 repaired that formula-provenance gap: the 68 shared-formula followers
now carry group index/range/master metadata, and the manifest separates 90
formula-bearing antipyrine-ratio cells from the 22 nonempty local expression
strings. A bounded regression-tested audit matches all 658 selected cached
value lexemes. This improves intake integrity, but the unbundled external
workbook and run-level volume/removal/recovery records remain unavailable in the
inspected source set. See the [Cycle 248 receipt](artifacts/perfusion-intake-2026-10-10/mandelbrot-s1-formula-provenance-reconciliation-cycle248.json).

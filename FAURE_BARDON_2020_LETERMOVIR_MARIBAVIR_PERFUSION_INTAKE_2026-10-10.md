# Faure Bardon et al. 2020 letermovir/maribavir perfusion intake — 2026-10-10

## Result

The public S1 Data workbook supports a source-cell descriptive intake of active-drug and antipyrine concentration trajectories for eight placenta-labeled series. It contains five letermovir labels and three maribavir labels, each at 19 timepoints from 0 to 90 minutes. The intake retains 912 source-cell rows, including 16 blank fetal-concentration cells at time zero, and preserves formulas and cached values separately. Human transcription review remains pending.

A source-scope discrepancy is unresolved: the article reports five validated letermovir perfusions, and the workbook has five visible letermovir labels, but its group summary values use only labels Placenta 1–4. The fifth raw series remains included in the CSV; no aggregate was recomputed or substituted.

## Sources

- Faure Bardon et al., [PLOS ONE article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0232140), DOI [10.1371/journal.pone.0232140](https://doi.org/10.1371/journal.pone.0232140). The article states that all relevant data are in the manuscript and supporting information, describes 5-minute sampling over 90 minutes, and reports 10 letermovir attempts with 5 validated and 8 maribavir attempts with 3 validated.
- Publisher [S1 Data XLSX](https://doi.org/10.1371/journal.pone.0232140.s001), pinned at `artifacts/perfusion-intake-2026-10-10/faure_bardon_2020_letermovir_maribavir_S1.xlsx` (SHA-256 `8c360f9ac01d64950e17793c57f6d17943b69ab40a423282c7ad1cae095f6fc2).
- Candidate manifest: [`faure_bardon_2020_lmv_mbv_dataset.json`](config/perfusion_observations/faure_bardon_2020_lmv_mbv_dataset.json).
- Source-cell intake: [`faure_bardon_2020_lmv_mbv_s1_source_cells.csv`](config/perfusion_observations/faure_bardon_2020_lmv_mbv_s1_source_cells.csv).

## Worksheet contents and intake handling

The workbook has separate active-drug and antipyrine tables. For each placenta label and 5-minute source timepoint, the CSV preserves fetal concentration (FC), maternal concentration (MC), and fetal-to-maternal ratio (FTR). Concentrations retain the article's mg/L unit; FTR remains the source ratio as a dimensionless fraction and is not converted to percent. The CSV has 912 records: 896 numeric source values and 16 source blanks for fetal concentration at 0 minutes. Source formula text and cached formula-value lexemes are retained; no formula was recalculated into an observation.

The worksheet’s populated group-summary values reproduce from all three maribavir labels. For letermovir, the summary entries match the first four labels and omit the fifth label; 220 of 224 populated summary values differ if all five labels are included. This conflicts with the article’s five-validated-perfusion statement. Preserve the raw fifth series and source summaries as published, and leave the selection relationship unresolved for independent source review.

The antipyrine table also contains 113 mg/L maternal concentration at source cell Z40 (Letermovir group, Placenta 3, 80 minutes). This value is retained without correction or exclusion and flagged for human review.

## Limits and feasibility relevance

The article reports an antipyrine validation criterion and aggregate tissue-accumulation results, but the inspected article and S1 Data do not provide a per-run reservoir-volume history, sample-removal ledger, individual recovery/mass-balance totals, or individual tissue-concentration rows. Do not infer amount transfer or dimensional parameters from these concentrations alone. The dataset can inform a source-aware description of a term placental drug-transfer boundary and the metadata needed to assess it; it does not establish nutrient-delivery adequacy, embryo growth, continuous gestation, birth, or later health. Keep this study separate from other perfusion datasets. No author was contacted.


## Independent source-cell reconciliation (Cycle 232)

A raw-XML pass matched all 912 source value lexemes and checked 288 paired
FC/MC/FTR records within an absolute tolerance of 1e-5. It also exposed an
intake gap: 259 shared-formula follower cells had cached values in the workbook
but were not represented in the CSV formula/cache fields. Cycle 233 added the
shared-formula provenance and a repeatable audit. See the [Cycle 232 finding](artifacts/perfusion-intake-2026-10-10/faure-bardon-s1-reconciliation-cycle232.json)
and [Cycle 233 correction receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-s1-formula-provenance-cycle233.json).

This qualifies the source-defined fetal-to-maternal concentration ratio for
descriptive trajectories, while the intake remains a candidate pending human
review. The letermovir group-summary contributor mismatch and antipyrine Z40
value remain flagged. The workbook still lacks the per-run volume/removal and
recovery records needed to estimate amount, flux, or a dimensional transport
parameter.

## Shared-formula provenance correction (Cycle 233)

The intake now distinguishes ordinary formulas from Excel shared-formula groups.
It records the shared-formula index, group range, master cell, local expression
text where present, and cached result for all 304 mapped formula cells. This
includes 281 shared formulas, of which 259 follower cells do not contain local
formula text in the XLSX XML. Source value lexemes, source cell locators, and
record IDs were left unchanged. The standard-library audit verifies the
corrected mapping and rejects a tampered source value even if its manifest hash
is updated. Two focused tests pass. This only strengthens provenance: the
intake remains descriptive-only and dimensional fitting remains ineligible.

## Primary-source check of the letermovir summary discrepancy (Cycle 234)

The open [PLOS Results](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0232140)
reports five validated procedures among ten letermovir perfusions and three
among eight maribavir perfusions. It gives mean antipyrine FTR summaries of
31±2% and 21±1%, respectively, but does not name the included S1 labels.
Table 3 reports group means±SD without a denominator or label-level crosswalk.
The S1 workbook contains five letermovir labels, while its total-summary
formulas use four and omit the fifth label. The primary source does not explain
this discrepancy; keep it unresolved. Retain all five raw series and the
published formulas/summaries without recalculation or label exclusion. See the
[Cycle 234 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-summary-label-check-cycle234.json).

## Public peer-review history check (Cycle 235)

The [PLOS peer-review history](https://journals.plos.org/plosone/article/peerReview?id=10.1371/journal.pone.0232140)
records the reviewer's concern about the 3 MBV / 5 LMV validated sample sizes.
The authors explain that about half of perfusions met the antipyrine FTR >20%
criterion and cite procedural difficulty and cost; the reviewer accepts this
response and asks for the small-sample limitation to be stated. Neither the
author response nor later review maps the workbook's five visible LMV labels
to the validated procedures or explains why the group-summary formulas use
only four labels. A bounded DOI-plus-correction query surfaced no correction
notice, which is not a comprehensive post-publication search. Keep the label
discrepancy unresolved. See the [Cycle 235 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-peer-review-history-cycle235.json).

## Antipyrine label diagnostic at steady-state onset (Cycle 236)

The article says LMV measurements reached steady state at 30 minutes and
requires an antipyrine FTR above 20% for validation. At the 30-minute source
cells, labels 1, 2, 4 and 5 exceed 20%; label 3 is below. The workbook's
summary formulas include labels 1–4 and omit label 5. This is a pointwise
comparison only: the article does not say the 30-minute row alone determines
per-run validation. It therefore does not establish which workbook series
were validated or explain the summary scope. Keep all five series and the
published summaries unchanged. See the [Cycle 236 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-antipyrine-label-diagnostic-cycle236.json).

## Formula-count metadata consistency (Cycle 237)

The detailed formula/cache provenance section in the dataset manifest still
said 45 after Cycle 233 verified 304 mapped formulas (23 ordinary and 281
shared). The stale count is corrected. The source audit now checks this field
against the observed 304 formula cells, alongside its existing source-cell,
cache, and formula-type checks. A negative test confirms that changing only
the nested count back to 45 is rejected. The workbook, source CSV, record IDs,
and review status are unchanged. See the [Cycle 237 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-formula-count-consistency-cycle237.json).

## Workbook chart-summary scope (Cycle 238)

The pinned workbook's combined chart uses the LMV mean and SD columns (AH/AJ
and AI/AK) across the 19 timepoints. Those columns use Placenta labels 1–4;
the chart therefore reproduces the same four-label summary and contains no
independent series for label 5. The chart does not resolve why label 5 is
omitted. Preserve its source cell ranges and the raw fifth series without
reclassification. See the [Cycle 238 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-chart-summary-scope-cycle238.json).

## Workbook visibility and structure screen (Cycle 239)

The pinned workbook has one default-visible sheet, no defined names or
AutoFilter, and no hidden columns affecting the fifth LMV source columns or
the AH–AK summary/chart columns. This rules out a simple hidden-sheet or
hidden-column explanation, but it cannot establish whether the formula scope
was intentional. Keep the discrepancy unresolved. See the [Cycle 239
receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-workbook-visibility-screen-cycle239.json).

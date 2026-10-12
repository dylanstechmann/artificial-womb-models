# Dolutegravir perfusion observation intake — 2026-10-10

## Result

Mandelbrot et al.'s public PLOS ONE S1 workbook contains placenta-labeled repeated measurements and source-calculated transfer fields, so it supports a descriptive observation intake. The workbook’s formulas reference an external source workbook that is not bundled, but the published worksheet embeds cached cell results. The intake retains the formula text and cached value lexemes separately, does not recalculate them, and remains a candidate pending human transcription review.

## Sources

- Mandelbrot et al., *Placental transfer and tissue accumulation of dolutegravir in the ex vivo human cotyledon perfusion model*, [PLOS ONE article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0220323). The article identifies the study as five closed-circuit recirculating experiments, says the source data are in the manuscript and supporting files, and links S1 Table.
- Publisher [S1 Table XLSX](https://doi.org/10.1371/journal.pone.0220323.s001), pinned locally at `artifacts/perfusion-intake-2026-10-10/mandelbrot_2019_dolutegravir_S1.xlsx` with SHA-256 `193aef87db0c7d23df2e09a6de7fe2f7390b25d87efb379b9646d0c940a4adc2`.
- Candidate intake: [`mandelbrot_2019_dolutegravir_dataset.json`](config/perfusion_observations/mandelbrot_2019_dolutegravir_dataset.json) and [`mandelbrot_2019_dolutegravir_s1_cached_values.csv`](config/perfusion_observations/mandelbrot_2019_dolutegravir_s1_cached_values.csv).

## What the worksheet contains

S1 Table lists dolutegravir fetal/maternal concentrations and their source ratio, antipyrine fetal/maternal concentrations and ratio, and a clearance-index column, with source time labels in minutes. The worksheet labels five perfusion series as Placenta 1, 2, 3, 4, and 7. These labels are retained as table labels only; they are not donor identities.

The table contains 94 timepoint rows: 19 for four labels and 18 for Placenta 3. Placenta 3 has no source row at 180 minutes, although the article reports a group mean±SD at three hours for n=5. The missing endpoint remains missing. Blank antipyrine fetal cells and literal dash entries are preserved as blank and text, respectively.

In the publisher workbook, several worksheet cells are formulas referencing an external workbook; the linked source file itself is not included. The CSV retains nonempty source formula text and the published sheet's cached cell-result lexemes separately. It does not recalculate formulas or reconstruct values from figures or missing rows.

## Cycle 247 source-cell triage

A one-off raw-cell check matched all 658 selected field values across the 94 CSV rows to the pinned worksheet, with no source-value lexeme mismatches. It also found a formula-provenance gap: the antipyrine-ratio column has 90 formula-bearing cells, including 68 shared-formula followers whose XML cells have no local expression text. The CSV contains the five shared masters and 17 ordinary expression strings but omits shared-formula type/index/range/master metadata for the 68 followers. The manifest's `source_formula_cell_count: 22` therefore counts nonempty local expressions for that field, not all formula-bearing cells. A dedicated validator and clearer count field remain to be added; until then, formula provenance is incomplete and human review remains pending.

The source workbook still has no time-linked reservoir-volume/removal fields or individual recovery rows. No external workbook was retrieved or recalculated, and no author was contacted. See the [Cycle 247 triage receipt](artifacts/perfusion-intake-2026-10-10/mandelbrot-s1-source-cell-triage-cycle247.json).

## Cycle 248 formula-provenance repair

The intake CSV now records each selected cell's formula type and, for shared formulas, the shared index, range, and master cell. The manifest distinguishes formula-bearing cells from cells with local expression text: antipyrine ratio has 90 formula cells, 22 local expressions, 73 shared-formula cells, and 68 followers without local expression text. All 658 selected cached value lexemes remain unchanged. The new bounded validator matches source values, formulas, shared-group metadata, row keys, and missingness; its tamper tests reject changed group metadata, cached values, and a stale formula count. No formulas were evaluated and the external workbook remains unaccessed.

This repair makes the transcription provenance inspectable; it does not resolve the external workbook dependency, missing volume/removal/recovery data, or pending human source review. See the [Cycle 248 receipt](artifacts/perfusion-intake-2026-10-10/mandelbrot-s1-formula-provenance-reconciliation-cycle248.json), [updated candidate manifest](config/perfusion_observations/mandelbrot_2019_dolutegravir_dataset.json), and [validator](src/wombmodels/mandelbrot_source.py).

## Limits and intake decision

This source supports descriptive concentration and source-reported ratio trajectories only. The inspected article and S1 Table do not contain numeric run-by-time reservoir volumes, sample-removal amounts, or individual recovery/mass-balance records. Do not use the data for amount balance, net flux, or dimensional transfer fitting. It is an ex vivo term-placenta transfer study and contains no embryo-development, continuous-gestation, birth, or later-health outcomes. No author was contacted; independent human source/transcription review remains pending.

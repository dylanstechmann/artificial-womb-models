# Ollivier et al. 2026 aciclovir/antipyrine perfusion source screen

**Screen date:** 2026-11-12  
**Status:** Agent-assisted candidate intake; human source and scientific review pending.  
**Scope:** Hash-pinned source reconciliation, descriptive observation intake and arithmetic identifiability diagnostics. No experiment was performed, no figure was digitized, and no transport model was fitted.

## Citation, access and rights

Ollivier H, Faure Bardon V, Froelicher Bournaud L, et al. “Congenital CMV Infection: Determination of Transplacental Passage of Aciclovir by Ex Vivo Placental Perfusion.” *BJOG*. 2026;133(6):1241–1248. DOI [10.1111/1471-0528.70168](https://doi.org/10.1111/1471-0528.70168). PMID [41621825](https://pubmed.ncbi.nlm.nih.gov/41621825/). PMCID [PMC13040426](https://pmc.ncbi.nlm.nih.gov/articles/PMC13040426/).

The pinned JATS permissions identify **CC BY 4.0**. Local source bytes remain under the untracked `artifacts/` directory and are not redistributed by the Git tree. The article’s data-availability statement says supporting data are available on request and are not publicly available because of privacy or ethical restrictions. No author was contacted. This screen does not make a global claim that no other data copy exists.

## Byte-pinned local evidence

| Artifact | Bytes | SHA-256 | Audited role |
| --- | ---: | --- | --- |
| `pmc13040426.xml` | 86,739 | `4e4e7e52d4eaabdf334d3b1a3aa4072aea2bed000e61c93a94b09232249b529d` | JATS citation, license, Methods, Results, Table 1, MathML, cohort statements and author-reported summaries |
| `PMC13040426_supplementaryFiles.zip` | 321,806 | `70f3ebcb844b79dccf690395301beab4eca2f237ad2cf834511d7d6a0774585e` | Europe PMC supplementary archive; nine members inventoried without executing content |
| `BJO-133-1241-s003.docx` | 15,690 | `442a3272ef5230bf5a649d02432bc6438db09373a1356fd6786802499b99bf84` | Table S1 literal DOCX paragraphs/runs and all 44 numeric cells |
| `BJO-133-1241-s001.png` | 113,156 | `abe907575a4dc43dbb72c8577f4ac77fb2657e28e99440dd0d5f345c2d7ae3c5` | Figure S2 context; not digitized |
| `BJO-133-1241-s002.png` | 78,450 | `c65634aad1767eb8544ca17cc4551e4aed370ade201d631e13a5ad699c4ecd18` | Figure S1 context; not digitized |

The observation card directly declares the JATS and Table S1 DOCX artifacts. The [source inventory](config/source_inventories/ollivier_2026_aciclovir_perfusion.json) and [perfusion manifest](config/perfusion_observations/ollivier_2026_aciclovir_antipyrine_dataset.json) pin all five local artifacts and the tracked intake files.

## Table S1 source-cell reconciliation

The [44-row source-cell CSV](config/perfusion_observations/ollivier_2026_table_s1_source_cells.csv) has 21,774 bytes and SHA-256 `8fd97889e86b66e14fa8afad2cf35653ca0b0eed72841c5524361b7330b20199`. It preserves zero-based DOCX source indices: the header is row 0, the row-label column is column 0, Placenta 1–9 occupy rows 1–9, and Mean/Standard Deviation occupy rows 10–11.

- **36 placenta-perfusion cells:** nine placenta labels × four numeric columns, with `row_role="placenta_perfusion"`.
- **Eight printed summary cells:** Mean and Standard Deviation × the same four columns, with `row_role="source_reported_summary"`.
- Every decimal-comma lexeme is retained exactly (`8,09`, `7,07`, `36,81`, `87,39`, etc.), alongside the period-decimal numeric form (`8.09`, `7.07`, `36.81`, `87.39`).
- The audit requires one table, exactly 12 rows × five columns, literal paragraph/run text, the four exact source headers, all row labels, all 44 lexemes, numeric values, units, roles and source locators, plus DOCX/CSV SHA-256 and byte sizes.

### Independent Decimal recomputation

For each column, the audit computes the arithmetic mean and sample SD (`n − 1`) of the nine displayed values with `Decimal`, then compares two-decimal rounding with the printed summary rows:

| Table S1 endpoint | Recomputed mean | Recomputed sample SD | Printed values matched after rounding |
| --- | ---: | ---: | --- |
| Maternal antipyrine concentration (µg/mL) | 9.74 | 2.43 | Yes |
| Fetal antipyrine concentration (µg/mL) | 7.78 | 1.50 | Yes |
| Fetal transfer rate (%) | 39.44 | 12.19 | Yes |
| Fetal/maternal concentration ratio (%) | 80.98 | 6.87 | Yes |

For every placenta, `round(100 × Cf / Cm, 2)` matches the printed fetal/maternal ratio. These are arithmetic checks on displayed cells, not checks of the underlying assay or a model fit.

## Source discrepancies retained

### Results-versus-Table-S1 metric swap

The JATS Results sentence reports antipyrine FTR as **81% (SD: 6.9%)** and the concentration ratio as **39% (SD: 12.2%)**. Table S1 instead derives **FTR 39.44 ± 12.19%** and **fetal/maternal ratio 80.98 ± 6.87%**. The Results values therefore align with the opposite Table S1 columns after rounding.

The intake keeps the Table S1 column identities and the separate Results text. Every FTR and fetal/maternal-ratio observation carries an unresolved `results_table_metric_swap` qualification. Neither source is silently corrected.

### Missing per-placenta volumes and ratio identifiability

The Methods FTR MathML is checked as `100 × FC × FV` divided by `FC × FV + MC × MV`. Rearranging the displayed relationship gives:

`Vf/Vm = (FTR / (100 − FTR)) × (Cm / Cf)`.

Using each row’s displayed concentrations and FTR implies Vf/Vm values spanning **0.328392 (Placenta 5) to 1.333187 (Placenta 9)** after six-decimal rounding. This variation demonstrates why one shared volume ratio cannot reconstruct all nine printed rows.

Results reports only group-level 3-hour volumes: fetal **201 ± 57 mL** and maternal **247 ± 53 mL**. As a explicitly counterfactual sensitivity check, substituting 201/247 mL for every placenta gives:

- mean predicted FTR **39.664832%**, versus the displayed-cell mean **39.436667%**;
- mean absolute per-placenta discrepancy **9.154696 percentage points**;
- RMSE discrepancy **10.854836 percentage points**;
- maximum absolute discrepancy **18.290812 percentage points** at Placenta 5.

A similar cohort-average result therefore conceals substantial row-level discrepancies. Group mean volumes are not substitutes for the missing individual records and do not make amount, mass balance, net flux or dimensional transfer parameters identifiable.

### Table 1 umbilical-artery pH literal

Table 1 prints umbilical artery pH as **7.28 (SD: 1.60)**. The summary observation retains the printed SD and a `printed_summary_anomaly` qualification. No correction, unit conversion or clinical reinterpretation is inferred.

## Observation intake

The [observation card](config/observations/ollivier_2026_aciclovir_antipyrine_perfusion_candidate.json) has 214,815 bytes and SHA-256 `aa525b9799308e81376d9bda3eb39cfb181011101dfcc4cd348705b4ce1090fe`. It contains 47 observations, nine measurement pairs and three cohort-coverage records.

| Record group | Count | Intake treatment |
| --- | ---: | --- |
| Placenta-labeled antipyrine 3-hour endpoints | 36 | `measured`; 180 min of ex-vivo perfusion, explicitly not gestational time; source decimal lexeme qualified |
| Aciclovir 3-hour Results summaries | 3 | Maternal 7.55 ± 2.46 mg/L; fetal 1.85 ± 0.60 mg/L; FTR 17.4 ± 7.8% |
| Compartment-volume 3-hour Results summaries | 2 | Fetal 201 ± 57 mL; maternal 247 ± 53 mL |
| Perfusion QC Results summaries | 5 | Fetal pH 7.2 ± 0.1; maternal pH 7.4 ± 0.1; fetal temperature 37.4 ± 0.7 degC; maternal temperature 37.3 ± 0.5 degC; fetal arterial pressure 67.5 ± 30.9 mmHg |
| Table 1 clinical baseline summary | 1 | Umbilical artery pH 7.28 ± 1.60 pH units, with the printed-SD anomaly retained |
| Maternal/fetal antipyrine concentration pairs | 9 | `same_unit_same_time`, source-explicit pairing within each Table S1 placenta row |
| Cohort-coverage frames | 3 | Nine retained perfusions; the 2/7 cadence split; one five-hour extension within the nine |

All 11 summaries use `author_reported_summary`, `summary_only`, typed `mean_sd`, and reported sample size 9. The five QC averages are not assigned an invented 180-minute measurement time: their source does not specifically locate each average at that time. Group summaries are not linked to individual Table S1 rows. No individual aciclovir trajectory was reconstructed from a figure or summary.

Cohort coverage remains denominator-aware:

1. Nine placentas met the article’s antipyrine criteria. Total attempted and excluded runs are unreported, so count closure is `not_assessed`.
2. The Methods cadence strata contain two and seven placentas. They are mutually exclusive and exhaustive within the nine-placenta retained cohort, so aggregate closure is `matches`; no cadence-to-table-label mapping is inferred.
3. One of the nine placentas was extended to five hours. It is not a tenth experiment, and the source does not identify its Table S1 numeric label.

## Audit implementation and receipts

[`src/wombmodels/ollivier_source.py`](src/wombmodels/ollivier_source.py) uses only the Python standard library. It applies bounded reads, repository-relative path checks, symlink rejection, archive member/count/size limits, XML entity restrictions, exact hash/size checks and finite `Decimal` arithmetic.

- `audit_ollivier_table_s1`: DOCX/CSV source-cell reconciliation.
- `derive_ollivier_antipyrine_summary_and_volume_ratios`: independent summaries, F/M ratio checks, implied Vf/Vm and common-volume sensitivity.
- `audit_ollivier_jats_and_observation_card`: JATS Table 1, exact Methods sentence hash, MathML, Results sentences, canonical card, pairs, coverage, source inventory and all five local artifact pins.

Local receipts:

- [Table S1 source audit](artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12/ollivier-table-s1-source-audit.json)
- [Summary and volume-ratio diagnostic](artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12/ollivier-antipyrine-summary-volume-ratios.json)
- [JATS/card/inventory audit](artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12/ollivier-jats-observation-card-audit.json)
- [Validated observation bundle receipt](artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12/validated-observations/receipt.json)

The following commands were run with and without local source verification; the source-root run reports `complete` for both declared artifacts, and strict bundle verification reports 17/17 declared outputs with no undeclared files:

```bash
wombmodels validate-observations \
  --dataset config/observations/ollivier_2026_aciclovir_antipyrine_perfusion_candidate.json \
  --out <new-without-source-root-bundle>

wombmodels validate-observations \
  --dataset config/observations/ollivier_2026_aciclovir_antipyrine_perfusion_candidate.json \
  --source-root . \
  --out artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12/validated-observations

wombmodels verify-bundle --strict \
  --bundle artifacts/ollivier-2026-aciclovir-perfusion-2026-11-12/validated-observations
```

`tests/test_ollivier_source.py` separates tracked clean-clone checks from `@requires_local_evidence("ollivier-2026-aciclovir-perfusion-2026-11-12")` source audits. Negative tests cover cell-value tampering with an updated CSV hash, printed-summary tampering with refreshed DOCX/CSV pins, JATS metric-swap tampering with refreshed pins, and observation-card value tampering with refreshed pins. The local-evidence tests are skipped rather than reported as passed when `artifacts/` is absent.

## Eligibility and limitations

Eligible use is source-linked descriptive comparison of the displayed antipyrine endpoints and author-reported summaries, subject to human review and a frozen analysis plan. The following remain outside eligibility:

- per-placenta amount or mass-balance reconstruction;
- net flux or dimensional transfer-parameter fitting;
- substitution of group means for missing individual volumes or sampling histories;
- developmental-outcome, complete-gestation, artificial-womb-performance or later-health inference;
- clinical interpretation or recommendations.

Source transcription and scientific review remain pending. Placenta numbers are source-local labels, not personal identifiers or cross-study links. The discrepancies and missing records are retained as findings rather than resolved by assumption. These automated checks establish byte integrity and internal arithmetic consistency only; they do not establish experimental measurement quality or biological model validity.

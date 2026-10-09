# Placental interface source qualification

Agent-assisted file inspection on 2026-10-09. This is a candidate source audit
for E-Q2/E3/M6 and the interface questions in design gate G1. It has not been
reviewed by a human and establishes no reviewed physiological model contract.
The evidence ledger and all dimensionless model fixtures remain unchanged.

| Source and inspected scope | Permitted candidate analysis | Dynamic transport benchmark |
| --- | --- | --- |
| Hori 2024 publisher Source Data, Figure 5G; article Figure 5 caption | Reproduce the 48 published Papp values in 12 compound/group partitions and describe each partition | Not eligible from this file: raw trajectories and linked independent-unit identities are absent |
| Bhide 2026 supplementary attachments 5/6, Tables 3/4 | Preserve source locators and identify these as author-produced pairwise summary comparisons | Not eligible from these attachments: individual trajectories, unit identities and explicit metric units are absent; supplemental reuse terms need clarification |

No independent-unit calibration/evaluation split can be frozen from the
inspected files. Neither decision says that the underlying study did not
collect the necessary observations or that another attachment/request could
not supply them. No model fit, inferential test, biological experiment or
embryo-to-birth evidence claim was produced.

## Hori: a reproducible descriptive endpoint audit

[Hori et al., *Trophoblast stem cell-based organoid models of the human
placental barrier*, Nature Communications 15, 962 (2024)](https://www.nature.com/articles/s41467-024-45279-y)
links a [publisher Source Data workbook](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-024-45279-y/MediaObjects/41467_2024_45279_MOESM7_ESM.xlsx).
The article's Data availability section also directs requests for supporting
data to the corresponding author. No request was sent.

| File property | Inspected revision |
| --- | --- |
| File | `41467_2024_45279_MOESM7_ESM.xlsx` |
| Bytes | 38,822 |
| SHA-256 | `a2b741034f322e2ffc2f23adf09ed5a00aaa1b11a4c239b0feec283a81075e9b` |
| Local read-only copy | `artifacts/interface-qualification-2026-10-09/hori-publisher-source-data.xlsx` |
| Workbook inventory | 20 worksheets; eligibility audit limited to `Fig. 5G` |
| Source type | Published derived apparent-permeability coefficients, not raw concentration or flux trajectories |
| Article rights notice | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with exceptions for third-party material; workbook-specific rights were not independently confirmed |
| Review state | Candidate; human scientific transcription and source-specific reuse review pending |

The initial PMC attachment request returned an HTML browser check despite its
`.xlsx` filename. It was rejected as data. The inspected revision is the
publisher file above, checked as a ZIP/XLSX and pinned by its full hash.
Downloading the source is a manual, read-only step; the new audit command
never accesses the network.

Figure 5G has Antipyrine, Caffeine and Glyphosate in three separate column
pairs. For each compound, Cont, HU, ST and ST/HU each have four numeric
values. Cont is the acellular collagen-membrane comparator; HU denotes
HUVEC, and ST/HU denotes ST/HUVEC in the caption. Human is the study model
context, including that acellular comparator; it does not mean every row
contains human tissue.

| Compound | Group labels | Value cells | Unit header |
| --- | --- | --- | --- |
| Antipyrine | A4:A19 | B4:B19 | B3 |
| Caffeine | D4:D19 | E4:E19 | E3 |
| Glyphosate | G4:G19 | H4:H19 | H3 |

The literal header is `Papp (x10-6 cm/s)`. The audit preserves `x10-6 cm/s`
and the source numeric text; it does not silently multiply by a scale or
convert to dimensionless model quantities. Rows 4–7, 8–11, 12–15 and 16–19
are Cont, HU, ST and ST/HU respectively in each column pair.

The Figure 5 caption reports N=4 biologically independent samples for these
measurements. The workbook does not provide donor, construct, batch or
replicate identifiers. The audit retains the author's statement as a
limitation and records zero supplied unit identifiers. Cell coordinates are
locators, never unit identities. Matching row positions are not evidence of
pairing across compounds or with the separate TEER worksheet.

The caption specifically places the ST and ST/HUVEC observations in panels
F/G at model day 6. The intake therefore records day 6 for 24 ST/ST-HU
values, and null age bounds for 24 HU/Cont values. In-vitro model days are
not human gestational ages. Assay sampling times are not inferred from model
age. No same-unit developmental transitions are created.

The extraction plan is fixed to this file and these cells. Within each of
the 12 compound/group partitions, report value count, arithmetic mean,
sample standard deviation and range. These are descriptive file summaries;
there is no newly calculated p-value, confidence interval, standard-error
claim or held-out score. Other endpoints and worksheets are outside this
audit. A numerical Papp coefficient cannot by itself establish the raw
observations, uncertainty or mechanistic separation needed for E-Q2.

### Reproduce from the external source

From an editable installation, provide the exact publisher workbook and two
new output directories:

```powershell
wombmodels audit-hori-source --workbook artifacts/interface-qualification-2026-10-09/hori-publisher-source-data.xlsx --out artifacts/hori-source-audit-v1
wombmodels validate-observations --dataset artifacts/hori-source-audit-v1/input_dataset.json --source-root artifacts/interface-qualification-2026-10-09 --out artifacts/hori-intake-v1
wombmodels verify-bundle --bundle artifacts/hori-source-audit-v1 --strict
wombmodels verify-bundle --bundle artifacts/hori-intake-v1 --strict
```

The audit rejects a different source hash; a replacement publisher revision
requires a new source-specific audit. It reads bounded ZIP/XML with the
Python standard library and rejects formulas, unsupported types, altered
headers, missing/invalid values and malformed source structure. The receipt
binds the input workbook hash, package implementation and all generated
outputs. The original workbook stays external and untouched. Its manifest
is not a substitute for those bytes when reproducing extraction.

The generated dataset can use `--source-root` to check the workbook bytes.
The article artifact has no declared local file/hash in this dataset, so its
byte verification remains unassessed. This is explicit partial source-byte
verification, even when every workbook endpoint is extracted successfully.
The article-caption scope is agent-curated metadata requiring human review.

## Bhide: accessible supplements, insufficient unit-level inputs

[Bhide et al., *A functional placenta-on-chip model for maternal–fetal
transport* (2026)](https://doi.org/10.1088/1758-5090/ae7bc8)
provides a [supplemental files page](https://iopscience.iop.org/article/10.1088/1758-5090/ae7bc8/data).
The inspected kinetic links are
[attachment 5](https://doi.org/10.1088/1758-5090/ae7bc8/data5) and
[attachment 6](https://doi.org/10.1088/1758-5090/ae7bc8/data6).
Both downloaded as two-page PDFs. Their tables were checked in extracted
text and rendered pages, including continuations across the page breaks.

| Attachment | Content | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| 5 / Supplementary Table 3 | Pairwise Tukey comparisons of derived transport metrics among acellular, BeWo, BeWo+HTR8 and BeWo+HUVEC conditions | 199,509 | `2436f47881006442c81cd2d87b645fc46e8edda46c5af81ab68b62a34663478f` |
| 6 / Supplementary Table 4 | Pairwise comparisons among acellular/co-culture and normoglycemic/hyperglycemic conditions | 195,675 | `9d37a928aee5d5bf846d78ee7a0caa7c9ea666ba93eaf07384798fcf7496329a` |

These tables report mean differences, confidence limits, significance
labels and adjusted p-values for AUC, Cmax, time to peak, peak rate, MAGE and
time in range. Each table has six pairwise comparisons per metric. Such
comparisons are not individual concentration observations, and their
confidence limits are not replicate trajectories. Explicit metric units,
individual source-unit identities and source-unit linkage are not supplied
in these inspected tables. No summary values were relabeled as raw data.
The listed attachments 1–4 were not qualified here.

The main article's availability text refers to supporting data on
reasonable request and says the data are provided in the manuscript, with
no repository deposit needed. This audit does not infer that unit-level
machine-readable trajectories are available from that statement. The
supplemental page states that files are published
under licence by IOP and rights generally belong to the authors unless
otherwise specified. An explicit open reuse licence for these two files
was not established in this inspection. Public readability alone does not
resolve reuse or redistribution. The source PDFs remain local ignored
artifacts; no table transcription or redistribution was committed. Source
cards use the stable DOI links, not the temporary signed download URLs.

## What would change the benchmark decision

Before fitting any dimensional transport model, qualify an existing dataset
containing the following, with provenance and permissible reuse:

1. Exact donor/receiver quantities over actual observation time, including
   units, measured collection/sampling corrections, boundary inputs and
   missing/excluded observations.
2. Source-linked independent-unit and donor/batch identifiers; linkage
   across endpoints where pairing is claimed. Freeze a split by the actual
   independent unit, not a spreadsheet row or a time point.
3. Unit-linked compartment capacities and interface geometry, plus the
   uncertainty/calibration needed to compare held-out measured outputs.
   Without independently observed area, do not separately claim recovered
   permeability and area.
4. Human source review and a frozen analysis plan specifying which effective
   quantities passive exchange, exchange plus uptake/loss and the simpler
   reference can identify from the supplied observables.

This is a missing-data specification for existing evidence, not an
experimental protocol. A fitting step remains deferred until the contract
is met. The continuous early interface in design gate G1 remains open;
neither descriptive organoid endpoints nor chip-summary comparisons
establish implantation continuity, complete human gestation or healthy
long-term outcomes.

The subsequent [interface feasibility questions](INTERFACE_FEASIBILITY.md)
add an early implantation source/public-data inventory, a third transport
candidate and an executable observation-ambiguity diagnostic. Their source
classes, actual scope, overlapping presentations and missing unit/phenotype
linkage remain separate from this Hori/Bhide audit and from human gate results.

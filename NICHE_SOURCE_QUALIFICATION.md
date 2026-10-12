# Niche mechanics and developmental outcomes: source qualification

AI-assisted source audit, 2026-10-09. Candidate transcription; human source,
scientific and reuse review pending. No mechanical calibration, causal effect,
embryo procedure or human gestation result is produced.

The [feasibility strategy](FEASIBILITY_STRATEGY.md) proposes a remodelable
maternal niche and a growing living interface. This audit makes its next
empirical question more concrete: **what do existing mechanical and
developmental observations discriminate, given their actual source hierarchy?**

## Source and exact inspected scope

[Guo et al., Nature Communications (2026)](https://www.nature.com/articles/s41467-025-68039-y)
links a [Source Data workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-025-68039-y/MediaObjects/41467_2025_68039_MOESM18_ESM.xlsx).
The downloaded file has 55 worksheets; the executable audit reads five selected
Figure 4 panels and one supplemental profile sheet. Other sheets were inventoried,
not fully qualified. The source remains unchanged in ignored local artifacts.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `guo-source-data.xlsx` | 137,918 | `c84b1faf2ebe02c812af7ec73d94a10c6640a11fba677ac85947999b9dc33e8e` |

| Selected sheet | Observed scalar structure | Current interpretation |
| --- | --- | --- |
| `Fig4A` | Two labeled columns with 9 and 10 values | Figure axis labels relaxation half-time in seconds; caption says n=10 and 9 independent experiments for E5.5 decidua and 40-MG, respectively. Values are not linked across panels. |
| `Fig4C` | Three labeled columns with 10 values each | Figure axis labels Young's modulus in Pa on a logarithmic scale; caption says n=10 without defining the unit counted. This is not proof of equivalent stiffness. |
| `Fig4D` | Three labeled columns with 5 values each | Figure axis labels relaxation half-time in seconds; caption says n=5 without defining the unit counted. Values are not paired to modulus rows. |
| `Fig4E`, `Fig4F` | Each has 7, 4 and 5 percentage-valued cells across its three conditions | Caption-reported two-cavity and egg-cylinder outcomes at IVC days 3 and 4, respectively. The caption states `n ≥ 4` but does not define the unit counted by `n` or give exact group `n`; worksheet cell counts are not treated as biological denominators. |
| `Sup 10 I` | One X column and three response columns, each with 200 values | Maps by panel title and condition headers to Supplementary Fig. 10I: rheometer stress profiles, time in seconds, response σ/σ₀ (dimensionless) normalized to initial stress. This is 200 coordinates per condition, not 200 independent replicates. Panel I gives no n or curve aggregation; panel J gives n=3 independent experiments for half-time summaries but does not assign those runs to profile rows. |
| `Sup10J` | Three scalar half-time values for each of 40-MG, 40-MGT and 40-MGN | Maps by panel title and condition headers to Supplementary Fig. 10J. The caption reports mean ± s.d. and n=3 independent experiments; the cell count matches n, but experiment IDs and pairing across conditions are absent. |

The audit retains 96 endpoint-cell locators and 800 supplemental profile-cell
locators with original numeric lexemes. Only the 32 developmental percentages
enter `input_dataset.json`; mechanical endpoints and profiles remain in a
separate inventory because specimen/run identities and the profile-to-summary
hierarchy remain unqualified. The supplemental profile's axes, normalization,
assay and condition mapping are now source-qualified. Source condition titles are retained
exactly, without expanding them into a preparation recipe. Blank trailing cells
are not turned into zero or classified as excluded embryos.

## What the data permit now

Source tracing is executable: selected headers, finite values, exact populated
cell sets, original lexemes and the pinned workbook hash are checked. The
candidate observation dataset retains mouse species, actual elapsed culture
days, null unit IDs, unreported replicate roles and no continuity edges.
Elapsed culture time is not added to the embryo's source starting age.

The source panels motivate distinct mechanical and developmental observations,
but lack explicit links between them. A repeated condition title permits a
descriptive source partition; it does not authenticate a material batch or
embryo experiment. Equal row positions cannot establish repeated outcomes,
matched specimens or a material-to-development correlation.

For Fig. 4E/F, the caption supplies only a lower bound (`n ≥ 4`). It does not
say whether `n` counts embryos, culture experiments, or another unit. The
selected workbook has 7/4/5 percentage cells per condition in each panel, but
the number of cells is not itself a verified biological `n`; outcome
numerators, starting denominators, losses, and the mapping from each percentage
to an embryo or culture remain unqualified. Preserve the 32 source values as
percentage-valued cells with `replicate_role=not_reported`.

The paper's nonsignificant Young-modulus comparisons cannot establish
equivalence. A future equivalence question needs a reviewed margin appropriate
to the mechanical estimand, independent runs, uncertainty and measurement
comparability. This audit supplies no margin and computes no equivalence test.
The publisher Figure 4 axes do supply plotted units: seconds for relaxation
half-time in panels A/D and Pa for Young's modulus in panel C (logarithmic
axis). Supplementary Fig. 10I labels its horizontal axis Time (s), its
dimensionless response σ/σ₀, identifies a rheometer, and states the stress
profiles are normalized to initial stress. Its source-sheet condition labels
match the figure legend. Fig. 10J reports mean ± s.d. with n=3 independent
experiments for the rheometer half-time summary; this does not identify the
profile traces as runs or means, nor map J's replicates to I's rows.

The workbook's 200 shared time coordinates are unique and strictly increasing,
from 5.0 to 1000.249 s; it contains no zero-second row. The first recorded
response at 5 s is 1.0 in each condition, but the source does not label that
sample as the measured initial instant. The raw response columns contain 49,
30 and 78 adjacent increases for 40-MG, 40-MGN and 40-MGT, respectively.
These are properties of the transcribed traces, not replicate counts. Preserve
the values as supplied; do not insert a zero-time point, smooth the increases,
or fit a monotonic relaxation curve without a qualified analysis contract.

The separate `Sup10J` sheet supplies three half-time cells per condition.
The caption's n=3 independent-experiment count and the nine source cells
align in number. Recomputing each condition's mean and sample standard
deviation from those cells reproduces the summary scale shown in panel J, but
the workbook provides no experiment IDs and does not link the three rows
between conditions or to the Sup 10 I curves. These are mechanics evidence,
not developmental observations; retain them in a separate source-cell file.

A cross-panel 40-MG half-time check finds a second unresolved source issue.
Figure 4A's nine values span 5.834–12.986 s (mean 9.903 s), Figure 4D's five
values span the same range (mean 9.280 s), and Sup. Fig. 10J's three values
span 75.018–80.019 s (mean 78.352 s). Thus, the 10J mean is about 7.9× and
8.4× the Figure 4A and 4D means, and its source range does not overlap either
Figure 4 range. Figure 4D identifies nanoindentation and Fig. 10J identifies a
rheometer; Figure 4A's method is not explicitly mapped. Until protocol and
run/sample identities are reconciled, treat the scale gap as a source-review
flag rather than a direct contradiction, and do not pool or fit these values.

A source-cell comparison also finds five exact numeric lexemes shared by the
40-MG columns of `Fig4A` and `Fig4D`; these occupy six Fig4A cells because
`5.8339999999999996` occurs twice there, and five Fig4D cells. The workbook
provides no sample/run IDs or statement establishing whether these entries are
shared specimens, remeasurements, reused values or coincidence. Preserve this
as a value-overlap flag only: it cannot support a cross-panel join or establish
independent replication. The audit records exact lexemes and cell locators so
the observation can be reviewed without silently pairing points.

The Methods further distinguish two stress-relaxation measurements. The
rheological test uses 1% fixed strain, normalizes stress to the initial maximum,
and fits a three-element generalized Maxwell–Wiechert model; the hydrogel is
held at 37 °C for 60 minutes before that test. The nanoindentation section
describes a 4-second loading phase to 15,000 nm, a 40-second hold, and a
4-second unload, with three experiments per sample. Figure 4D names
nanoindentation, and Supplementary Fig. 10J names a rheometer. Figure 4A's
caption describes a characteristic relaxation timescale for E5.5 decidua and
40-MG, but names no assay or instrument; the Results text also does not assign
one. Thus the manuscript presents multiple methods without explicitly mapping
Figure 4A to either protocol. It also provides no point-level IDs linking the
workbook values to samples or repeats. The audit manifest records the reviewed
article HTML locators and verifies the pinned local snapshot hash before
reporting this boundary.

A raw profile check compares the first observed downward transition through
dimensionless σ/σ₀ = 0.5 in Supplementary Fig. 10I with the Sup10J source-cell
means. The adjacent time brackets are 80.018–85.020 s for 40-MG,
145.035–150.036 s for 40-MGT, and 160.038–165.041 s for 40-MGN; the respective
Sup10J means are 78.352, 145.035, and 150.037 s. The largest gap to a bracket
is 10.001 s. These traces have no stated run/summary hierarchy and no IDs link
them to the n=3 experiments, so this is only a panel-level timing-scale check.
The brackets retain adjacent raw points; no interpolation, smoothing, or fit
was applied.

Figure 4C's caption says its modulus was detected by nanoindenter. The Methods
also describe an AFM/Hertz loading-curve method for decidua and Matrigel, but do
not explicitly establish that method as the Figure 4C protocol. Keep this
method mapping unresolved rather than substituting the AFM description for the
captioned nanoindenter measurement.

Outcome percentages also need their original numerator, starting denominator,
experiment identity and exclusions. Recovering a likely integer denominator
from a rounded percentage would invent source metadata. Later morphology or
cardiac activity cannot substitute for the missing starting roster.

## Frozen candidate questions and missing observations

| Question | Candidate comparison | Required qualification |
| --- | --- | --- |
| Does the mechanical profile require time-dependent response? | Constant response under a reviewed held-deformation contract versus a relaxing response with a possible residual plateau | Exact assay mode, loading/holding history, time origin/units, normalization, geometry and independent profile mapping. |
| Are material groups mechanically comparable beyond stiffness? | A reviewed equivalence question for modulus, separately from relaxation/architecture | Independent material/run IDs, comparable measurement mode, uncertainty and a prespecified margin. |
| Does mechanical behavior explain developmental outcomes? | Stiffness-only explanation versus time-dependent response, retaining chemistry, adhesion, architecture and transport as possible confounds | Material-to-embryo/run links, outcome numerators/denominators, exclusions and prespecified contrasts. |

The current Kelvin–Voigt fixture represents creep/recovery under imposed
stress. Its time constant cannot be substituted for source relaxation half-time
or calibrated from these inventories. No profile fit, cross-panel regression,
held-out claim or causal estimate is performed here.

## Reproduce the audit and candidate intake

Provide the exact workbook and new output destinations:

```powershell
wombmodels audit-guo-source --workbook artifacts/feasibility-strategy-2026-10-09/guo-source-data.xlsx --out artifacts/guo-niche-audit
wombmodels validate-observations --dataset artifacts/guo-niche-audit/input_dataset.json --source-root artifacts/feasibility-strategy-2026-10-09 --out artifacts/guo-niche-intake
wombmodels verify-bundle --bundle artifacts/guo-niche-audit --strict
wombmodels verify-bundle --bundle artifacts/guo-niche-intake --strict
```

The standard-library reader evaluates no formulas or workbook programs and
rejects changed headers, populated-cell inventories, hashes and nonfinite
values. Publication is exclusive and receipt-last. Source hashing and bundle
integrity do not establish scientific transcription or review.

The article declares CC BY-NC-ND 4.0; workbook-specific reuse remains
unqualified. Original source bytes are external and untouched; local outputs
are reformatted candidate scalar inventories. No publisher data is committed,
no public redistribution is performed and no author inquiry has been sent.

The result advances data access for a niche-function comparison. The missing
material/experiment hierarchy, loading definitions, outcome denominators and
review contract remain prerequisites for an eligible analysis. It supplies no
human niche setting, sustained placenta replacement or embryo-to-birth path.

## Public sequence accessions and analysis-code availability

The [bounded public-data screen](GUO_PUBLIC_DATA_SCREEN_2026-10-10.md) finds
that the article names PRJCA004049 for scRNA-seq and PRJCA052100 for SmartSeq2,
but the displayed sample aliases/counts do not map one-to-one to the
corresponding Methods descriptions. The linked GitHub repository's E6.5/E8.5/D9
processed-cell counts match the article Results, which confirms group-level
identity but supplies no embryo or archive-run IDs. CNCB's PRJCA004049 archive
lists PD_SC/PDCO_SC/E45_SC as its single-cell sample aliases, E8.5 samples as
bulk, and no D9-labeled scRNA-seq BioSample. Its tracked code repository also
omits input matrices and RDS/text files read by the script. Preserve the
accession-to-assay discrepancy as a candidate data-availability gap; do not
interpret BioSample or run counts as embryo n, add transcriptomic observations,
or fit from the deposits without a matrix-to-run crosswalk. Structured record
details and limitations are in `public_data_accession_screen` under the Guo
source in
[`growing_interface_2026.json`](config/source_inventories/growing_interface_2026.json).

The pinned Supplementary Information PDF and linked Source Data workbook were
also searched for transcriptomic sample identifiers. Supplementary Fig. 7
shows scRNA-seq group-level QC for E6.5/E8.5/D9, but the inspected supplement,
workbook inventory, and tracked GitHub text contain no explicit accession or
matrix-to-run crosswalk. This is a bounded search and does not rule out a
separately downloadable archive metadata workbook. The source screen is
documented in
[`GUO_PUBLIC_DATA_SCREEN_2026-10-10.md`](GUO_PUBLIC_DATA_SCREEN_2026-10-10.md).

The tracked E6/E8 barcodes also have zero exact overlap with the stage-matched
Pijuan-Sala et al. E-MTAB-6967 atlas metadata, including after removing the
terminal `-1`. This weighs against direct cell-record reuse from that atlas,
but does not establish new sequencing or identify another source. The E6.5
origin remains unresolved; no transcriptomic observations are added.

Two additional public early-mouse GEO series, GSE100597 and GSE109071, include
E6.5 cells but have no inspected crosswalk to Guo's Cell Ranger matrices.
GSE109071's linked sample record documents Smart-seq2 and covers only through
E6.5. Treat both as possible annotation references, not as evidence of the
E6.5 group source. The structured candidate screen is recorded under
`candidate_reference_datasets_screen` in
[`growing_interface_2026.json`](config/source_inventories/growing_interface_2026.json).

The linked group's 2022 paper provides a closer provenance lead: Figure 6
reports a separate 10x dataset with natural E6.5 and E8.5 embryos and PDCO/PD
IVC-day-8–10 embryos. Its 14,935 E6.5 and 15,116 E8.5 filtered cells are
numerically near the 2026 post-QC counts (14,315 and 14,761), but no shared
barcodes or sample/run mapping was found. The 2022 data-availability statement
offers data from the corresponding author on request and gives no public
accession. The current PRJCA004049 listing instead describes its three
single-cell BioSamples as Drop-seq for day-2 PD, day-2 PDCO, and E4.5 groups.
Treat the 2022 dataset as the leading natural-stage source/comparison lead,
not a demonstrated reuse; it does not resolve D9 or raw-run provenance. No
author contact or observation promotion was made. Details are in the
[public-data screen](GUO_PUBLIC_DATA_SCREEN_2026-10-10.md).

The 2022 paper also reports phenotype-level outcomes that are more useful for
developmental-stage coverage than its cell-count provenance alone. It gives
PDCO summaries of 36 ± 6% for two-cavity formation on IVC day 3, 47 ± 15% for
egg-cylinder formation on day 5, and 11 ± 5% for a heartbeat-like stage on
days 8–10; the reported comparators are Petri dish, PD, and CO. The Figure 3
caption states 71 PDCO and 64 PD embryos for the comparison, while the article
does not provide per-timepoint denominators or per-embryo successes. Do not
reconstruct counts from rounded percentages or treat those stages as
independent cohorts. Figure 5 reports immunostained samples of 15 embryos per
condition for days 2–3 and 20 per condition for days 5–6, day 9, and day 10.
The paper describes neural-like and heart-tube-like morphology, marker
expression, and beating cardiomyocyte aggregates; it explicitly notes a gap
from E8.5. These findings support a mouse early-organogenesis milestone only,
not functional circulation, live birth, or postnatal health. The qualified
summary is stored in
[`gu_2022_uterus_inspired_niche.json`](config/source_inventories/gu_2022_uterus_inspired_niche.json);
no observations are promoted.

The GSA page's metadata workbook download was also retrieved and found to be
empty: its `Sample`, `Experiment`, and `Run` sheets each contain only `A1=ID`.
The archive page itself lists 12 BioSamples and experiment/run records, but
does not identify the 2026 scRNA matrices. Retain the workbook as a hashed
source artifact and treat the accession-to-matrix link as unresolved.

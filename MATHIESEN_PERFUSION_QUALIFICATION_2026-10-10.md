# Mathiesen et al. term placental perfusion qualification

Candidate evidence intake; source transcription and scientific review remain
pending. No author contact was sent.

## Source and recorded measurements

[Mathiesen et al. (2020), PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0233979)
reports ex vivo perfusion of term human placental tissue and concentrations of
cortisol, cortisone, tryptophan, serotonin and 5-HIAA. The pinned [S1 Data
workbook](https://doi.org/10.1371/journal.pone.0233979.s005) has 22 numbered
perfusion columns. The offline audit preserves 3,190 expected source cells,
2,908 numeric nM reservoir-concentration readings, 282 blanks, exact cell
locators and original numeric lexemes. It does not modify or redistribute the
original source files.

Maternal and fetal perfusate reservoirs are separate compartments. The source
labels `Mbefore` and `Fbefore` are kept as pre-exposure labels without invented
elapsed times; numeric labels such as `M0`, `M2`, `F2` and the subsequent
30-minute intervals remain in minutes. Every recorded value stays tied to its
workbook cell. The 22 table identifiers are perfusion-run IDs, not verified
personal donor identities or proven independent biological units.

The run-to-condition and acceptable-duration mapping is manually transcribed
from the pinned publisher Table 1 image. It records eight runs without an
antagonist, five carbenoxolone, four fluoxetine and five PCPA runs. Fifteen runs
are listed as acceptable for six hours; seven are listed for shorter durations.
All source cells remain in the data. Measurements later than the source-listed
acceptable duration are flagged rather than silently counted as valid
late-window observations. Human verification of this mapping remains pending.

A second visual pass against the pinned Table 1 image found no discrepancy in
the 22 ID-to-antagonist and acceptable-duration entries. This is an agent
self-check, not independent human verification; the source review status is
unchanged. Other Table 1 columns have not been transcribed into this intake.

## Additional supporting information inspected

The article lists S2–S4 in addition to the S1 Table and S1 Data used for the
cell-level audit. I pinned local copies in the ignored
`artifacts/tryptophan-perfusion-supporting-2020/` directory and checked their
hashes and table structures. S2 is a 29-row, two-column `Variable`/`Frequency`
table of aggregate donor descriptors. S3 is a 23-row, 14-column table: 22 data
rows under the `nr` key and columns for stress-questionnaire measures plus
selected fetal perfusion outcomes. S4 is a 43-row, 15-column correlation table.
I did not transcribe donor-level measurements from these files.

S3's 22 `nr` keys are exactly 1–22, the same numeric set as Table 1's perfusion
IDs. The article describes S3 as donor questionnaire data paired with selected
perfusion outcomes, but does not explicitly state that `nr` is the Table 1
perfusion ID or describe a crosswalk. Treat this as a candidate unit link only:
the observation intake keeps the S3 table separate and no donor-to-run join is
made. The inventory records the file hashes and this unresolved key question.

The Methods section says fetal reservoir volume was observed after each sample
and maternal/fetal volumes were measured at the end. It also gives source-level
perfusion success criteria. The inspected public workbook and S1–S4 tables do
not provide the numerical per-sample reservoir-volume/removal history or
per-run final volumes. The measurement procedure is described; its accounting
values are not present in the inspected public files. Calibration/uncertainty
records and original instrument chromatograms were also not found in those
files.

## Cited validation literature: bounded relevance check

I checked the public abstracts and institutional records for the validation
papers cited by the 2020 article and related follow-up studies. [Mathiesen et al. (2010), *Quality assessment
of a placental perfusion protocol*](https://pubmed.ncbi.nlm.nih.gov/20096346/)
reports positive- and negative-control checks and that 15% of 202 cannulated
placentae met its success checkpoints in one year's workflow. This is useful
method-quality and sample-yield context for an ex vivo term-placenta assay; it
also cautions against treating an assay setup as a routine high-yield process.

[Myllynen et al. (2010), *Preliminary interlaboratory comparison of the ex vivo
dual human placental perfusion system*](https://pubmed.ncbi.nlm.nih.gov/20434538/)
reports that two research groups obtained the same transfer ranking for three
model compounds, while curve fitting failed for a fourth. Its abstract says
detailed compound-transfer data were or would be published separately. I found
no row-level dataset linked from the PubMed or university publication records
checked here. The publisher full texts were not reviewed, so this is a bounded
discovery result, not evidence that no supplemental data exist elsewhere.

The related [Mose et al. (2012) NewGeneris meta-analysis](https://pubmed.ncbi.nlm.nih.gov/22374511/)
adds a key caution: it re-analyzed thirteen compounds from three ex vivo labs,
found that antipyrine transfer differed significantly across studies/labs, and
reported lower variance after antipyrine normalization. The abstract says this
only partially corrected small methodological differences and that ranks varied
slightly by endpoint. Its institutional record links to the publisher but no
row-level dataset; I reviewed abstracts, not the full paper or supplements.
These were different compounds and endpoints from the 2020 hormone/amino-acid
workbook, so the aggregate rankings cannot be pooled into that intake. The
normalization result reinforces that cross-study comparison needs recovery and
method context, which are missing from the 2020 source files inspected here.

Two later abstract-level reports give distinct throughput signals. [Karttunen et
al. (2015)](https://pubmed.ncbi.nlm.nih.gov/26055651/) describe more than 100
perfusion attempts at one center and report lower antipyrine transfer at
gestational durations over 40 weeks; [Conings et al.
(2017)](https://pubmed.ncbi.nlm.nih.gov/28522142/) report 34 successful
quality-controlled assays out of 89 collected placentas (38%) at another center.
These denominators and success definitions differ from each other and from the
2010 report of 15% at Copenhagen, so the percentages are not pooled or treated
as a universal success rate. They indicate that tissue availability, acceptance
criteria, gestational age, reference transfer and assay recovery need to be
logged as separate factors when assessing reproducibility and throughput.

The [2022 inter-centre standardization paper](https://doi.org/10.1016/j.placenta.2022.05.003)
describes variation in assay establishment, perfusate composition, gas conditions,
cannulation method, flow, tissue mass and quality-control practice, and proposes
a multi-centre pilot to test how these differences affect tissue function and
structure. It is a rationale and proposed study, not a completed comparative
dataset or a validated minimum reporting standard. I record those categories
only as candidate metadata prompts for future source intake. The publisher
abstract and an open-access repository listing were found; direct retrieval of
the PDF failed in this review, so its full text and supporting files remain
unchecked.

A later [2024 literature review](https://pubmed.ncbi.nlm.nih.gov/38570213/)
provides the strongest intake finding so far. It reviewed 135 drug-transfer
studies published from 2000 through 2022, restricted to uncomplicated full-term
placentas and fixed within-run setups. The authors report that studies remain
heterogeneous and are not readily comparable. Only 65.8% of setup parameters
were in the primary reports; another 13.6% were found in cited protocol papers,
while 20.6% remained undocumented, and some referenced protocols conflicted.
Their supplementary Tables S2–S5 contain extracted method metadata, not
measurement outcomes. I retrieved S1–S5 and inspected their headings and
structure: S1 is a country list; S2 covers preparation, S3 control, S4 test
substance, and S5 the experimental period, with tables split by transfer
direction. I did not import study-specific parameter values. The table notes
distinguish some values recovered from cited protocols, while a dash groups
unmentioned, omitted and incoherent values together; conflicting references
are also noted. This supports preserving field-level provenance and ambiguous
missingness in any future intake. The review's search closed in September 2022,
so it does not establish whether the 2022-proposed
multi-centre pilot later produced results. My targeted search found no such
outcome report. The 2024 review also excludes the 2020 stress/hormone workbook's
question and endpoint class, so its setup summaries are not poolable with that
dataset. I wrote a candidate, non-standard metadata crosswalk in
[PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md](PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md)
and recorded hashes and table phases in the inventory.

These papers make the citations important methodological context for the 2020
perfusion measurements, but they address isolated placental transfer and assay
quality. They provide no evidence of continuous embryo support, gestation,
birth, neonatal transition or later health. I added them as contextual sources
in the machine-readable inventory only; no sample-level values, protocol
parameters, or additional observations were imported, and no author was
contacted.

## Missingness and selection

Blank cells are not uniformly distributed. Of the 638 cells for each analyte,
the source workbook has 18 cortisol blanks, 17 cortisone blanks, 24 tryptophan
blanks, 79 serotonin blanks and 144 5-HIAA blanks. The source attributes missing
values to analysis errors but does not assign a cause to each cell. No missing
value is imputed and no missing-at-random assumption is made.

Across source-listed time windows, 2,920 expected cells are at or before each
run's acceptable duration; 2,711 are numeric and 209 blank. The shorter-run
post-window set has 270 expected cells, of which 197 are numeric and 73 blank.
The machine-readable `missingness_summary.csv` stratifies these counts by
analyte, reservoir and antagonist condition; `cell_observations.csv` retains
the individual cell-level flags.

The article's S1 Table separately reports 48 placentas received, 43
cannulations, 26 successful pre-perfusion/substance-added cases and 15
successful six-hour perfusions. Table 1 and the 22-column workbook describe a
different numbered set. The inspected source does not explain the intermediate
relationship between those population frames, so this intake preserves them
separately and does not infer success rates or reconcile the counts.

## Bounded descriptive check and eligibility

For the eight runs with no antagonist, the mean of the per-run fetal tryptophan
F360 concentration divided by maternal M0 concentration is 70.16% (range
62.47%–85.01%). This reproduces the article's approximately 70% concentration
comparison. It is not a mass balance, collected amount, net transport flux,
permeability estimate, nutrient sufficiency measure or inferential result.

This source supports a candidate source-linked description of measured reservoir
concentrations after the Table 1 mapping and source-cell transcription are
reviewed. It does not currently meet the requirements for a dimensional
transport fit. The inspected records do not provide numerical per-sample
reservoir-volume/removal histories, per-run final volumes, analyte inventory
and recovery, original instrument chromatograms, or calibration and uncertainty
records. A concentration cannot
be converted to amount or flux without the relevant volume and collection
accounting. These term-tissue assays do not measure embryo growth, continuous
gestation, birth, neonatal transition or later health.

The generic observation intake validates record structure and exact source
bindings, and verified the four pinned local artifacts (546,715 bytes) against
their SHA-256 values. This checks bytes and schema only; it does not authenticate
source transcription, independent-unit identity, reuse rights or biological
validity. The article page states CC BY 4.0; supplement/image item-specific reuse
review remains pending. No fit, experimental protocol, clinical recommendation
or source-ledger promotion is made.

## Reproduction

Original publisher files stay in the ignored local directory
`artifacts/tryptophan-perfusion-2020/`. The receipt-bound outputs are in
`artifacts/mathiesen-perfusion-audit-2026-10-10-v4/` and
`artifacts/mathiesen-perfusion-intake-2026-10-10-v4/`. Reproduce with the
repository's `dev` Compose service:

```sh
cd /workspace/artificial-womb-models
PYTHONPATH=src python3 -m wombmodels audit-mathiesen-source \
  --article artifacts/tryptophan-perfusion-2020/article.html \
  --workbook artifacts/tryptophan-perfusion-2020/supplement-s1-data.xlsx \
  --table1 artifacts/tryptophan-perfusion-2020/table1.png \
  --success-table artifacts/tryptophan-perfusion-2020/supplement-s1-table.docx \
  --s3-table artifacts/tryptophan-perfusion-supporting-2020/s3-stress-perfusion.docx \
  --out artifacts/mathiesen-perfusion-audit-<new-name>
PYTHONPATH=src python3 -m wombmodels validate-observations \
  --dataset artifacts/mathiesen-perfusion-audit-<new-name>/input_dataset.json \
  --source-root artifacts/tryptophan-perfusion-2020 \
  --out artifacts/mathiesen-perfusion-intake-<new-name>
PYTHONPATH=src python3 -m wombmodels verify-bundle \
  --bundle artifacts/mathiesen-perfusion-audit-<new-name> --strict
PYTHONPATH=src python3 -m wombmodels verify-bundle \
  --bundle artifacts/mathiesen-perfusion-intake-<new-name> --strict
```

Each command requires a new output directory. The article, workbook, Table 1
image, S1 Table and S3 Table are pinned by hash; source retrieval is not
performed by the audit command.

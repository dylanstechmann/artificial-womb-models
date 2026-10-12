# Human maternal–fetal interface atlas: candidate source qualification

Inspected 2026-10-10. Candidate-only, AI-assisted source transcription; human
scientific review and source-specific reuse review for downloaded portal data
remain pending. No author was contacted. No biological experiment, model fit,
or clinical inference was performed.

## The bounded question

Can this atlas provide a human identity and spatial-context reference for later
comparison with a model of the maternal–fetal interface? It can inform what
cell states and arrangements a comparator should preserve. It cannot calibrate
exchange or establish that a supported embryo is healthy.

The article describes samples from gestational weeks 5–39 and 16 second-trimester
basal-plate sections, each from an independent donor. The spatial sections are
restricted to selected basal-plate anatomy; the paper cautions that site and
microanatomy can confound comparisons of cell proportions. These are sampled
tissues, not longitudinal developmental units.

## Reproducible table checks

The publisher supplementary-tables ZIP is preserved locally at
`artifacts/human-mfi-atlas-2026-04-08/supplementary-tables.zip` (4,794,202
bytes; SHA-256
`ad8bfe9586bb475456587878feb533be71c4d24e7601bc85b3b7a712e1be1d1b`). ZIP
integrity checks passed. The inspected workbooks were extracted byte-for-byte
from that archive; hashes and source locators are in
[`config/source_inventories/wang_2026_human_mfi_atlas.json`](config/source_inventories/wang_2026_human_mfi_atlas.json).
Sample labels were compared internally to check joins, then omitted from this
report. No demographic fields were retained.

| Source table | Machine-checkable coverage | Interpretation |
| --- | --- | --- |
| Supplementary Table 1c, metadata; 1d, estimated-cell QC; 1e, post-QC counts | 23 sample labels in each table; all 23 labels match across all three. Metadata records 17 basal-plate and 6 decidua-basalis samples. The 23 post-QC counts sum to 191,735 nuclei. | The sum exactly matches the paper’s reported paired snRNA/snATAC profiles. This is a nucleus total nested within sample records, not a donor count or developmental outcome. |
| Supplementary Table 4a, spatial metadata; 4c, post-QC counts | 16 numeric sample labels match across both tables; each also contains a separate footnote row. The metadata records 16 basal-plate sections and source gestational labels from 18+6 to 24+1. | This agrees with the paper’s statement that the 16 spatial sections came from 16 independent donors. The table labels do not establish donor links to the separate multiome cohort. |
| Supplementary Table 4c, spatial QC | The 16 sample-level “cells passed QC” values sum to 1,155,086. A table footnote says cells assigned to the unknown-identity cluster were removed, leaving 1,077,690 cells for analysis; the arithmetic difference is 77,396. | Preserve these as two filtering stages. The difference is not a count of lost donors, pregnancies, or developmental units. |
| Supplementary Table 4d, vessel-density measurements | 62 vessel-level records across 5 slide labels. | Vessels are nested within tissue sections and donors; 62 is not the donor sample size. The article likewise reports 62 uterine vessels. |

The supplementary tables are a useful check on sample coverage, exact joins,
and processing denominators. The paper reports mean 8,336 paired nuclei per
sample; the table total divided by 23 is about 8,336.3, consistent with that
rounded description. Stage and tissue site remain distinct: the early
multiome samples include decidua basalis, while the spatial section set is
second-trimester basal plate only.

## Data access and limits

The [UCSF atlas portal](https://cell.ucsf.edu/snPlacenta/) currently offers
H5AD and count downloads, an ATAC fragments download, and spatial/CODEX
resources. Its integrated and count H5AD links resolve to files of 3,050,244,246
and 3,042,755,986 bytes, respectively; the linked ATAC fragments archive is
49,963,047,789 bytes. None was downloaded. The five Cirro viewers point to
JSONL assay payloads ranging from 523,265,489 to 37,783,844,305 bytes. Static
viewer code and each small companion index exposed a range-addressable schema;
the schema records shapes and metadata field names, including sample IDs,
gestational-week labels and cell classes. Index/schema sizes and hashes are
pinned in the source inventory. No complete H5AD, JSONL, or fragments file was
downloaded. An earlier 64-KiB range probe included a single gene-keyed record
in four JSONL payloads; its cell values were not inspected or retained. The
new schema and `sample_id` probes did not request expression features.

Two bounded `sample_id` column reads support useful but stage-limited checks.
In the spatial browser, the 1,077,690-row matrix has 16 sample categories; all
16 labels join to Supplementary Tables 4a and 4c. Its row total matches the
article/table-reported total after removing the unknown-identity cluster. Table
4c's 1,155,086 sample-level counts are from before that removal, so the
sample-specific removed counts cannot be recovered from the inspected table.
In `scPlacenta`, 193,202 rows cover all 23 sample categories in Table 1e; 22
sample counts match, while one category is 1,467 larger. The aggregate matrix
total is therefore 1,467 above the table's 191,735. The article separately
reports 221,380 high-quality RNA nuclei, 210,191 ATAC nuclei and 191,735 paired
nuclei ([paper](https://www.nature.com/articles/s41586-026-10316-x)); the
available viewer schema does not identify which count universe its 193,202-row
matrix represents. Keep this as an unresolved population/filtering
relationship, not as a donor loss or a corrected count. The fetched column
bytes were processed transiently; sample labels and per-cell values were not
retained.

The [public analysis repository](https://github.com/complexdisease/mf.interface)
was inspected read-only at commit `dd30d10195c9b72c3cf3748052121e14dc5a0df6`.
Its snRNA integration script reads sample-level Cell Ranger filtered matrices
and creates sample-labeled Seurat objects; the H5AD conversion script only
describes export. The inspected scripts do not reconcile the portal's 193,202
rows with the paired-nuclei table total. The spatial preprocessing notebook
applies cell/gene filters but does not give per-sample counts after unknown
identity-cluster removal. This review did not run the code.

The publisher's [Source Data Fig. 1 workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10316-x/MediaObjects/41586_2026_10316_MOESM4_ESM.xlsx)
and [Source Data Fig. 2 workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10316-x/MediaObjects/41586_2026_10316_MOESM5_ESM.xlsx)
were downloaded, hashed and inspected sheet-by-sheet. Their figure-level tables
contain proportions and spatial/statistical summaries; neither supplies
sample-level snRNA counts or a mapping of the 193,202 viewer rows to the
191,735 paired nuclei. The count-universe question therefore remains open.

The inspected multiome metadata does not establish a donor crosswalk. Table
S1c has a `Sample ID` field but no donor/participant identifier; the scPlacenta
viewer schema exposes `sample_id` but not `donor_id`. A separate snMultiome GEX
viewer does expose `donor_id` (27 categories across 38 `dataset` categories),
but neither category set matches the atlas's 23 S1e/scPlacenta sample IDs, even
after case and punctuation normalization. It therefore cannot support donor-
grouped splitting or cross-assay matching for the scPlacenta samples.

The portal's Stereo-seq H5AD
anchor is commented out and returns 404; its CODEX Box share resolves to a
public app shell but did not expose a file inventory in the static page. The
article states that raw FASTQ requires controlled
access through dbGaP (`phs004305.v1`); no access request was made. The article
is CC BY 4.0, but no dataset-specific reuse/license statement was found in the
inspected static portal page; terms for the portal-hosted processed matrices
remain unverified. The code repository has a separate GPL-3.0 license and was
not executed.

The article's GEO/NeMO accessions serve different purposes. Its methods use
[GSE198373](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE198373)
(second-trimester smooth-chorion and villus samples) and
[GSE212505](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212505)
(term placenta accreta-spectrum/control data) as independent EVT iScore
benchmarks. [GSE204684](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE204684)
and [NeMO `dat-oiif74w`](https://assets.nemoarchive.org/dat-oiif74w) are human
brain negative controls for a pregnancy-risk-cell analysis. These linked
datasets do not report the portal matrix's count-universe mapping; they must
not be conflated with the atlas cohort or its QC totals.

The atlas is cross-sectional and selected for normal or presumed-normal
pregnancies. Cell identity, expression, chromatin accessibility, spatial
proximity, or vessel density do not directly measure embryo-to-placenta
exchange, transport sufficiency, whole-embryo progression, live birth, or
long-term health. The spatial series is one developmental window and anatomy;
the multiome sample labels are not automatically independent donors. This
candidate must not be used to infer a continuous human developmental trajectory
or to set physiological operating parameters.

## Next public-record step

The bounded public-record audit is complete for the publisher article,
Supplementary Tables 1 and 4, Source Data Figs. 1–2, selected code, linked
GEO/NeMO records and available portal observation schemas. These records do not
resolve the scPlacenta count universe or the single +1,467 sample-category
difference. The inspected portal page states no dataset-specific license, and
the available metadata do not provide a sample-to-donor crosswalk. Retain those
three items as unresolved; do not use this matrix for count-dependent or
donor-grouped comparison unless the data version, reuse terms and unit mapping
are established. It remains a candidate identity/spatial-context reference
only, with sampling site and gestational stage preserved and donor as the split
unit where available. It cannot substitute for transport, developmental
competence or outcome validation. No author contact is needed for this
public-record work.

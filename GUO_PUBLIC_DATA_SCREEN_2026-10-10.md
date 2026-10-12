# Guo et al. 2026 public-data accession and code screen

Screened 2026-10-10 against the publisher article, CNCB-NGDC BioProject pages,
the linked 2022 article, and the public analysis-code repository. This is a
provenance and reproducibility screen only. No sequence files were downloaded,
no expression values were transcribed, and no authors were contacted.

## What the 2026 article says

The article's Data availability statement names **PRJCA004049** for scRNA-seq
and **PRJCA052100** for SmartSeq2. The scRNA-seq Methods describe three in-vivo
E8.5 embryos from three different pregnant mice and three IVC day-9 embryos.
The SmartSeq2 Methods describe trophoblast cells from three separate IVC-day-2
embryos for each of 40-MG and 40-MGT; that Methods passage does not mention
40-MGN. See the [article's Methods and Data availability
statement](https://www.nature.com/articles/s41467-025-68039-y).

## PRJCA004049: scRNA-seq sample mapping remains unresolved

The [CNCB-NGDC BioProject record](https://ngdc.cncb.ac.cn/bioproject/browse/PRJCA004049)
is titled “A uterus-inspired 3D niche drives embryo development beyond
implantation.” It records a 2020-12-16 submission and 2021-12-31 release, an
archive CRA004601, and 12 BioSamples. The [GSA archive experiment/run
listing](https://ngdc.cncb.ac.cn/gsa/browse/CRA004601) exposes these single-cell
records:

| Sample alias | BioSample | Experiment | Run accessions |
| --- | --- | --- | --- |
| `PD_SC` | `SAMC435198` | `CRX259699` | `CRR305004`–`CRR305008` |
| `PDCO_SC` | `SAMC435199` | `CRX259700` | `CRR305009`–`CRR305013` |
| `E45_SC` | `SAMC435200` | `CRX259701` | `CRR305014`–`CRR305018` |

The inventory also lists nine bulk-labeled BioSamples (`E75_bulk_1/2`,
`E85_bulk_1/2`, `D1_bulk_1/2`, `D8_bulk_1`, and `D10_bulk_1/2`). The E8.5
BioSamples `SAMC435203` and `SAMC435204` carry the `E85_bulk` labels; the
[BioSample record](https://ngdc.cncb.ac.cn/biosample/browse/SAMC435203)
describes `SAMC435203` as “Bulk RNA-Seq for E8.5 embryos.” The inventory has no
D9-labeled scRNA-seq BioSample. Run identifiers are sequencing records, not
verified independent-embryo counts.

The [2022 Advanced Science paper](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202202282)
reports 518 single cells in Figure 3 from day-2 PD and PDCO embryos plus
natural E4.5 embryos. Those conditions align with the three single-cell labels
in the older project record (`PD_SC`, `PDCO_SC`, and `E45_SC`), whose BioSample
descriptions identify Drop-seq. This is a plausible accession-to-early-paper
group mapping, though no cell/barcode-to-run bridge is present in the article
or current archive view. The 2022 Figure 6 dataset is a separate, later 10x
experiment (see below), not the 518-cell Figure 3 comparison. CNCB's current
BioProject page also lists the 2026 Nature Communications paper as a linked
publication. The displayed BioProject/GSA inventory does not explicitly
identify the 2026 E8.5 and IVC-day-9 scRNA-seq libraries: E8.5 records are
explicitly bulk-labeled, and no D9-labeled scRNA-seq BioSample is listed.

The linked code repository provides a stronger group-level check: `code.Rmd`
maps `E8` to E8.5, `E6` to E6.5, and `E8L` to D9; the tracked `meta.txt` has
39,832 data rows with 14,761 E8, 14,315 E6, and 10,756 E8L cells. Those counts
exactly match the post-QC cell counts reported for E8.5, E6.5, and D9 in the
2026 Results. This supports the identity of the processed group metadata, but
the file carries no embryo or run IDs. Also, the Results include E6.5
scRNA-seq, while the library-generation Methods paragraph names E8.5 and D9
but does not explain the E6.5 source. The archive's BioSample/Run-to-matrix,
cell-barcode, and figure crosswalk remains unresolved. Treat the evidence as a
processed-group match with a candidate accession-to-assay coverage gap, not
proof of incorrect deposition or absence of data elsewhere. Resolve the
BioSample/Run-to-matrix, cell-barcode, and figure crosswalk before attributing
these processed groups to deposited raw runs.

## PRJCA052100: SmartSeq2 counts do not map cleanly to the Methods sentence

The [CNCB-NGDC BioProject record](https://ngdc.cncb.ac.cn/bioproject/browse/PRJCA052100)
is titled “Bulk RNA sequencing of 40-MG, 40-MGT, and 40-MGN,” describes IVC-day-2
hydrogel-contact regions from all three groups, and lists 11 BioSamples: 3
`MG_EX`, 4 `MGT_EX`, and 4 `MGN_EX`. The 2026 article's SmartSeq2 Methods
sentence instead names three embryos each for 40-MG and 40-MGT and omits
40-MGN. The sample-count and condition difference may reflect additional
libraries, a different sample hierarchy, or a reporting/mapping issue; the
public BioSample count is not itself a verified independent-embryo count.
Retain the mismatch as unresolved until sample IDs map to methods, figures,
and biological units.

## Public analysis code is not self-contained

The article links the [analysis repository](https://github.com/dongjingxi/embryo-development-in-vitro)
(main commit `e71eaaac80486d00f6b01092a2a5ae6618a087b6`, checked 2026-10-10).
Its tracked tree contains `README.md`, `code.Rmd`, and `meta.txt`. `code.Rmd`
reads Cell Ranger matrices from `cellranger/E8-5`, `cellranger/E6-5`, and
`cellranger/E8-5-L`, and later reads `singerR/refdata-se.rds`, `GO_filter.txt`,
and `sce_harmony_final.rds`; those inputs are not in the tracked tree. The
repository therefore provides analysis scripts and group-level processed-cell
metadata, but is not reproducible from its own tracked contents alone. Raw
reads or source files elsewhere may permit reconstruction, but first require
sample/run mapping and the missing reference and intermediate-object
provenance.

## Supplement and source-data crosswalk search

The 31-page pinned [Supplementary Information PDF](artifacts/feasibility-strategy-2026-10-09/guo-supplementary-information.pdf)
contains Supplementary Fig. 7's scRNA-seq quality-control and cell-type
proportion panels for E6.5, E8.5, and IVC day 9, but text extraction found no
`PRJCA`, `SAMC`, `CRX`, or `CRR` identifiers and no sample/run mapping. The
publisher Source Data workbook has 55 worksheets and no Fig. 3-labeled sheet;
this does not show that no transcriptomic source files exist elsewhere. The
three tracked GitHub files likewise contain none of those accession patterns.
No matrix-to-run, embryo-unit, or E6.5 reference-source crosswalk was found in
these inspected materials. The GSA archive page exposes a `CRA004601.xlsx`
metadata download. The downloaded file is 13,792 bytes (SHA-256
`0251316C5FAAE7B0ADD532124DAA6CF5A86C728F239EAFD2B59E97891711E6C5`) and has
`Sample`, `Experiment`, and `Run` worksheets, each with only the single cell
`A1=ID`. Treat it as an empty export, not evidence that no additional archive
metadata exists. The archive landing page itself still lists 12 BioSamples
and their experiment/run records, but the displayed aliases do not identify
the 2026 E6.5/E8.5/D9 scRNA-seq matrices. The pinned workbook snapshot is
[`cra004601-metadata-export.xlsx`](artifacts/public-data-screen-2026-10-10/cra004601-metadata-export.xlsx).

## Check against the Pijuan-Sala gastrulation atlas

Because the 2026 article reports natural E6.5 cells but does not specify their
source in the library-generation Methods paragraph, I compared the repository
barcodes with the stage-matched metadata in Pijuan-Sala et al.'s 2019 mouse
gastrulation atlas ([article](https://www.nature.com/articles/s41586-019-0933-9),
[E-MTAB-6967](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-6967),
[Supplementary Table 4](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-019-0933-9/MediaObjects/41586_2019_933_MOESM6_ESM.csv)).
That table has 3,697 E6.5 rows (3,689 unique barcode strings) and 20,978
E8.5 rows (20,783 unique barcode strings). Guo's tracked `meta.txt` has 14,315
E6 and 14,761 E8 cell rows. Exact barcode overlap is zero for both matching
stages, and remains zero after removing the terminal `-1` from Guo's barcode
strings.

This weighs against direct cell-barcode reuse from E-MTAB-6967. It does not
identify whether Guo's E6.5 cells were newly sequenced, came from another
reference dataset, or were transformed by an undocumented processing step.
The article's Results include E6.5 scRNA-seq, while its library-generation
Methods paragraph names E8.5 and IVC day 9 but does not explain the E6.5
source. Keep that source unresolved and do not infer raw-run provenance or
biological replication from barcode strings or cell totals.

## Other public E6.5 reference candidates

I screened two other early-mouse GEO series as possible references, not as
presumed sources. [GSE100597](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE100597)
covers E3.5 through E6.5 and lists 721 sample records plus a processed count
table. [GSE109071](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE109071)
reports 1,724 cells from 28 pregastrula embryos at E5.25–E6.5; a linked
[E5.5 sample record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM2929812)
describes manually picked cells and Smart-seq2 library preparation. This
record documents a method used in the GSE109071 series; it is not an E6.5
sample-level match. Neither series supplies an identified sample/run-to-Guo-
matrix crosswalk in the metadata inspected here, and GSE109071 does not cover
E8.5.

Guo's tracked analysis points to Cell Ranger `filtered_feature_bc_matrix`
directories for E6.5, E8.5, and D9, while the article's library-generation
paragraph names 10x Chromium v3.1 for E8.5 and D9 but omits E6.5. The GEO
series make plausible annotation/reference sources, but they do not explain
the source of Guo's E6.5 matrix. A closer lead from the linked group's earlier
paper is screened below.

## The linked 2022 paper's later 10x dataset

The linked [2022 Advanced Science paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9534964/)
also reports a separate, later single-cell dataset: its Results say that the
authors used 10x Genomics on natural E6.5 and E8.5 embryos and PDCO/PD embryos
cultured on IVC days 8–10 (Figure 6c–f). Figure 6 reports 14,935 filtered
E6.5 cells, 15,116 E8.5 cells, 21,546 PDCO cells, and 16,989 PD cells. This is
a materially stronger candidate provenance lead than the GEO reference
screens because the stage, platform, research group, and publication overlap
the 2026 analysis.

The natural-stage counts are close to, but not equal to, the 2026 processed
counts: 14,315 E6.5 (620 fewer; 4.2%) and 14,761 E8.5 (355 fewer; 2.3%).
Count proximity alone cannot establish reuse: the papers do not provide a
shared cell/barcode crosswalk in the inspected materials, and differences
could reflect filtering, a distinct dataset, or another processing path. The
2022 paper's data-availability statement says data are available from the
corresponding author upon reasonable request and names no public accession.
No author contact was made.

The same paper's Methods section titled “Single-Cell Isolation and
Transcriptome Library Construction” describes the earlier day-2 PD/PDCO and
E4.5 comparison, but does not specify the Figure 6 10x collection/library
workflow. The Wiley article page lists one Supporting Information PDF and
seven supplemental movies; it lists no separate spreadsheet or source-data
file. The PDF link returned HTTP 403 in this read-only screen, so its contents
were not inspected. The attachment inventory therefore narrows the public
route but does not establish that the PDF contains no relevant details or
that no data are available elsewhere.

The current displayed `PRJCA004049`/`CRA004601` inventory does not bridge this
gap. Its three scRNA BioSamples are explicitly described as Drop-seq for
IVC-day-2 PD, IVC-day-2 PDCO, and natural E4.5 embryos. The listed aliases do
not identify Figure 6's later 10x E6.5/E8.5/IVC-day-8–10 groups. Thus the 2022
Figure 6 dataset is a plausible source or comparison lead for the 2026
natural-stage matrices, but it is not evidence that the matrices are shared,
nor does it explain the 2026 D9 group. Keep provenance unresolved and add no
observations. A wider public search using the 2022 article title, Figure 6
stages, and 10x terms returned PRJCA004049 as the directly relevant official
project record; it did not surface a second archive accession. This is a
bounded search result, not proof that no other record exists.

## Intake decision

Do not add observations or fit model parameters from these deposits at this
stage. The 2022 10x dataset is now the leading public-paper provenance lead
for the natural E6.5/E8.5 groups, but it lacks a public cell-level crosswalk;
the 2026 D9 and raw-run mappings also remain unresolved. A useful next step is
to search public supplementary/source-data and repository records for a
cell/barcode bridge or another archive identifier, while preserving the
embryo/pooled-material boundary. Until then, keep transcriptomic comparisons
out of the biological outcome ledger. This screen does not alter the separate
mechanics-source qualification or establish later developmental function.

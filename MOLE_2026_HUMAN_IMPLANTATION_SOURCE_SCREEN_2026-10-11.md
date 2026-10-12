# Molè et al. 2026 human implantation-interface source screen

Reviewed 2026-10-11. This is an AI-assisted source screen; status is candidate evidence and human review remains pending.

## Finding

Molè et al. describe CREST, a human embryo/endometrial-interface model with luminal, glandular and stromal endometrial compartments. The paper reports donated blastocysts beginning at 5–6 days post-fertilization and observations extending through a day-14 endpoint. It provides valuable evidence about implantation and early trophoblast/conceptus development. It does not report a placenta that supports later gestation, a transition to birth, or postnatal outcomes. Treat it as an early-interface component in an evidence map, not a complete artificial-womb system or a device specification.

Primary sources: [Cell article](https://doi.org/10.1016/j.cell.2025.10.027), [PubMed record](https://pubmed.ncbi.nlm.nih.gov/41443191/), and the author-published [Zenodo article record](https://zenodo.org/records/20022561). The open-access PDF is available from Zenodo under CC BY 4.0; its reviewed-copy SHA-256 and source-record MD5 are recorded in the [provenance manifest](artifacts/early-interface-model-2026-10-11/SOURCE.json). The repository retains only a sanitized study metadata extract and the run/sample relationship table, without detailed protocol descriptions.

## Units, sample selection and exclusions

The article reports 248 human blastocysts used across the study; this is not the denominator for a single day-14 endpoint or the molecular comparison. It also reports 17 implantation sites collected at day 14 for single-cell RNA sequencing. The official [BioStudies record](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-13629) provides seven source sample groups, divided across the two scaffold-condition labels as 3 and 4. Their ENA metadata crosswalks to 15 sequencing runs and 60 FASTQ file rows. The site-to-sample mapping is not supplied, so the 17 sites cannot be treated as 17 independently linked observations; runs, files and cells are not independent embryo units.

Only recovered blastocysts that had fully expanded advanced to scaffold experiments. The paper states that embryos degenerating before the target stage were excluded, but the number excluded and endpoint-specific attrition are not reported. Keep the total 248, the selected scaffold population and the 17-site sequencing collection distinct. The seven-row [sample crosswalk](config/source_inventories/crest_2026_emtab13629_sample_crosswalk.csv) preserves the submitted labels without inventing a site-level map.

## Public data routes

The [BioStudies metadata](https://www.ebi.ac.uk/biostudies/api/v1/studies/E-MTAB-13629) links to ENA submission ERP156726 / project PRJEB71939. All 60 FASTQ URLs in the SDRF returned HTTP 200 to metadata-only HEAD requests. No FASTQ contents were downloaded and no file checksums were recomputed. The ENA run report returns 15 run rows but leaves its FASTQ URL, checksum and byte-count columns blank; the separate SDRF URLs and HEAD results resolve file availability and declared lengths, not data integrity. See the [60-row metadata manifest](artifacts/early-interface-model-2026-10-11/emtab13629_fastq_manifest_head_checked_cycle191.csv) and the [structured source inventory](config/source_inventories/crest_2026_human_implantation.json).

The manuscript's processed-data DOI, [10.5281/zenodo.17930156](https://zenodo.org/records/17930156), resolves to four processed RDS files under the MIT license. Its code DOI, [10.5281/zenodo.17955321](https://zenodo.org/records/17955321), resolves to the v1.0 publication release under CC BY 4.0. The records were checked against both Zenodo and DataCite metadata. In a later static review, the small code archive was fetched in memory and hash-checked; no scripts were executed and no RDS files were downloaded.

## Intake decision and feasibility boundary

The code archive's QC export contains 15,673 cell rows and six batch labels, but no E-MTAB/ENA accession or implantation-site identifier that joins it to the seven submitted sample groups. Its `nCount_RNA` column contains only `SeuratProject`, so that field is not usable as a count without validation. The inspected Figure S5G script compares epithelial and stromal cell identities with a cell-level MAST test; it does not show a per-sample or per-embryo replication term. These cell-level results cannot substitute for linked embryo/site outcomes. The [static review receipt](artifacts/early-interface-model-2026-10-11/crest-code-release-analysis-cycle192.json) records the source hash and limits.

The publisher-hosted [supplemental PDF](https://ars.els-cdn.com/content/image/1-s2.0-S0092867425012322-mmc1.pdf) was reviewed visually. It is two pages; page 2 contains Table S1, “Human Endometrial Biopsies.” That table does not identify implantation sites or crosswalk the 17 sites to the seven E-MTAB-13629 groups. This is a bounded negative result for the inspected MMC1 PDF; no donor-level values were transcribed. See the [supplement screen receipt](artifacts/early-interface-model-2026-10-11/crest-supplement-screen-cycle193.json).

No biological outcome rows are promoted. The paper and public metadata establish useful stage and sample coverage, but the site-to-sample linkage is unresolved and the processed matrices have not been analyzed. This model can inform questions about the earliest embryo–endometrium interface. The paper explicitly notes that its model lacks immune and vascular compartments and does not recreate the full complexity of endometrium. It does not measure maternal-to-fetal exchange or establish continuous support after early implantation.

Next evidence step: retain the site-to-sample mapping as unresolved across the inspected BioStudies metadata, code-release exports and publisher supplemental PDF. Keep the result descriptive; cells and sequencing runs are not biological replicates. A separate early-interface model can be screened for source-linked experimental units without assuming it resolves this paper's mapping gap. No author contact is required.

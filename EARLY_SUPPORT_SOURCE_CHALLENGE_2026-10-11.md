# Early-support source and claim challenge

Date: 11 October 2026
Roadmap task: T05
Review status: provisional AI source-first challenge; independent scientific review remains pending
Contact: no authors or other people contacted

## Decision

The early-support memo's bounded decision survives: the imported candidate cards do not establish a source-qualified, same-unit delivery/use/progression chain, so they cannot select an architecture. Two limits need to stay explicit. First, the LIPT1 study supports keeping transfer, metabolism and development as separate outcomes, but it does not report a longitudinal same-embryo D/M/P chain. Second, the local card census is a repository metadata result, not a source-validated census of all public or controlled data. No biological gate moves.

This is a useful source-first challenge, but it is not independent scientific acceptance. The same AI process produced the earlier synthesis; an outside author was not asked to review it. T05 remains held for a genuinely independent reviewer. The author-contact restriction is preserved.

## Claim-by-claim result

| Claim under review | Verdict | Source-first finding and exact locator | Consequence |
| --- | --- | --- | --- |
| Song et al. is a relevant early human interface comparator. | Accept with scope limits | PubMed record, bibliographic lines 177–180 and abstract lines 263–267: human embryo/endometrial-organoid 3D co-culture, reported development to day 14 post-fertilization, Carnegie-stage landmarks and impaired progression after maternal-signal disruption. [Primary paper record](https://pubmed.ncbi.nlm.nih.gov/41443195/). | Keep as an early-interface comparator. Do not extend it to complete gestation, external support through birth, or a tested owned machine. Its two local group-summary candidate rows are not individual embryo trajectories; source denominator and stop/missingness mappings still need source-specific review. |
| LIPT1 evidence demonstrates that delivery, tissue use and development can disagree. | Revise and retain as an illustration | The primary article's “LIPT1 enables developmental metabolism” section reports no detected defect in mutant placental uptake or embryo transfer of labeled glucose/glutamine (Extended Data Fig. 5d,e), while the same article reports suppressed TCA-cycle labeling, organ/erythrocyte abnormalities and embryonic demise by GD11.5. See the article abstract, main-text section and Extended Data Fig. 5d–g and 6; [PubMed record and linked source data](https://pubmed.ncbi.nlm.nih.gov/35388219/), [open full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC9007737/). | This disease-model result supports measuring transfer, intracellular metabolism and developmental outcome separately. It is not a same-unit longitudinal D/M/P measurement chain, an artificial-support experiment, or evidence that an engineered component can substitute for placental function. Phrase it as an endpoint-separation example only. |
| The eight local candidate cards contain 976 observation rows, 947 early-stage rows, no source-reported independent-unit IDs and no declared measurement pairs. | Accept as local metadata accounting; insufficient as a source census | The earlier linkage memo pins the exact eight JSON input hashes and reports the row counts, declared review states and missing ID/pair fields. Those properties can be checked against those frozen files. The files remain marked `candidate`; intake validation is structural and does not validate their transcriptions, source coverage or reuse rights. | Keep the result bounded to the repository snapshot and those imported cards. Do not infer that no other public, institutional or controlled dataset exists. Any future source-qualified row or changed file requires a fresh census. |
| Current candidates cannot answer the target same-unit D→M→P question or rank architectures. | Accept within stated scope | The candidate cards' missing independent-unit keys and explicit measurement-pair links prevent a same-unit join from the imported records; no valid join may be inferred from matching group, stage or date labels. The Song primary abstract establishes an early co-culture model, not the missing cross-stage record. | Retain the observation contract. Do not calculate a predictive association, causal architecture effect or architecture ranking from these cards. Move only after new eligible source-linked observations arrive. |
| The proposed observation contract is sufficient for a later qualified comparison. | Insufficient for biological acceptance; retain as a minimum data contract | The six-part contract in [the early-support decision](EARLY_SUPPORT_LINKAGE_DECISION_2026-10-11.md) requires source-defined unit hierarchy and disposition, stage/time, named compartments and measures, explicit within-unit links, comparator/outcomes/missingness and source/reuse provenance. The reviewed papers do not demonstrate that all fields are available in one qualifying dataset. | Keep the contract as an acquisition/intake specification, not as a validated scientific instrument or sufficient biological design. Qualified specialists must set measurement methods and intended-use criteria. |

## Audit boundary

This challenge checked source claims and inference boundaries against the primary record metadata and article text. It did not independently reproduce the eight-card census, inspect every full-text supplementary source cell, validate candidate reuse permissions, or receive a second review. The local structural validator is relevant only to input shape; it cannot confirm whether a source transcription or biological interpretation is correct. No effect size, operating value, embryo-handling procedure, clinical recommendation or success rate is inferred.

The key correction is narrow: preserved tracer transfer in the LIPT1 disease model can coexist with impaired downstream metabolism and development at the study/group level. The observations motivate separate endpoints. They do not establish an individual-level causal chain or prove that an artificial system needs a particular architecture. The architecture remains unselected pending a qualified discriminator.

## Source locators

- Song et al., *Cell Stem Cell* (2026), PubMed record: title and citation, lines 177–180; abstract, lines 263–267. The abstract identifies the model, human embryo/endometrial organoid co-culture, day-14 post-fertilization endpoint and signal-blockade observation.
- Solmonson et al., *Nature* (2022), PubMed record and linked primary article: abstract for the mouse gestational interval and developmental phenotype; main-text section “LIPT1 enables developmental metabolism” for tracer uptake/transfer and downstream metabolism; Extended Data Fig. 5d–g for placental uptake/embryo transfer and metabolic labeling; Extended Data Fig. 6 for morphology and erythroid outcomes. The article provides source data.
- Local input record: `EARLY_SUPPORT_LINKAGE_DECISION_2026-10-11.md`, table “Exact candidate-card inputs and byte revisions used for this screen.” Its SHA-256 values bind the claimed repository census to a specific local snapshot.

## Roadmap disposition

- T05 receives this challenge artifact but remains **held** because an AI cannot certify its own earlier synthesis as independent review. The result is “revise the LIPT1 wording; accept the bounded Song and local-metadata conclusions with the limits above; independent scientific acceptance is insufficient/pending.”
- U01/U02/U03/U04 remain unresolved at the biological level. The eligible next discriminator remains source-qualified linkage of delivery, tissue use and independent developmental progression with full unit accounting.
- No public-data eligibility, human feasibility, support architecture, equipment ownership or gestational outcome gate changes.

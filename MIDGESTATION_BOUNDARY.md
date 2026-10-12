# Qualify the terminal support boundary before extending the architecture

AI-assisted source curation and design inference, 2026-10-09. Human scientific
review pending. This contains offline observation intake and functional
requirements, not embryo procedures, tissue manipulation, assembly instructions,
physiological settings or clinical guidance.

The [support-route comparison](FUNCTIONAL_SUPPORT_ROUTES.md) now has a more
specific failure question: can internal delivery and tissue function keep pace
with growth? Bulk availability, molecular resemblance and the presence of blood
vessels cannot individually answer it. Complete human gestation remains
unestablished.

## What the additional manuscript passages report

Results, Discussion and Figures 1-3 captions were checked against the pinned
official [Lokshtanov et al., bioRxiv v1 PDF](https://doi.org/10.64898/2026.03.17.710314).
The original PDF is retained with a SHA-256 hash in the
[Cycle 270 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/primary-pdf-qualification-cycle270.json).
The manuscript is explicitly marked as not certified by peer review. Exact main-figure denominators and supplementary figure labels were checked in
Cycles 271-272; embryo-linked records and normal-outcome numerators remain
unavailable.

The E7.5-start cohort reached approximately E12.5 after 5.5 culture days, but
not with an intact yolk sac throughout: the source says intact-yolk-sac embryos
did not progress past culture day 5, and the last ~12 hours required opening
the yolk sac while retaining umbilical vascular continuity. About 10-20% were
reported as properly developed at day 5.5 across strains. The manuscript also
reports slower late growth and terminal heart enlargement, pericardial edema,
internal hemorrhage and tissue necrosis (PDF page 6, printed lines 171-186).
The authors attribute injury to insufficient internal oxygen/nutrient delivery;
that mechanism is not independently identified here. Results report only a
small placental labyrinth portion, with junctional zone/decidua mostly absent
(PDF page 8, printed lines 259-265).

The separate E6.5-start cohort reached approximately E11.75 after six days,
with a reported final-day yield of 12-18% and a developmental delay. Keep that
cohort distinct from E7.5; do not combine its efficiency with the later E7.5
endpoint. The paper's isolated-gonad assay reports oocyte development after
further in-vitro culture, not live birth from an ex-utero-grown embryo.

Figure 1D and Figure 2D label 46 platform/day assessed-embryo counts and the
number of independent experiments. The
[Cycle 271 crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/figure-1d-2d-denominator-crosswalk-cycle271.csv)
keeps the two missing platform/day bars explicit. Since the figure summarizes
experiment-level outcome percentages as mean ± SEM, the labels cannot be used
to reconstruct pooled normal/total fractions. Counts across culture days are
not summed or treated as an individual risk set. The official supplementary
[PDF](artifacts/mouse-ex-utero-frontier-2026-10-11/Lokshtanov_2026_bioRxiv_Supplement_v1.pdf)
adds figure captions and Methods; the inspected tab exposed no separate
source-data table. Cycle 272 transcribed 42 further labels from Extended Data
Figures 3D and 3G. Figure 3D covers six strain/serum conditions, but its
caption does not define the unit for the printed `n` values; Figure 3G's caption
defines `emb` as embryos evaluated and `n` as independent experiments. The
The caption reports no evident difference between the CD1 × CD1 cord-serum and
adult-serum conditions in Figure 3D. Figure 4D is a separate E6.5-start serum
comparison: its caption defines `n` as independent experiments and provides no
embryo denominator. The primary Results contrasts no evident serum difference
for E7.5 starts with a higher HCS proper-development percentage after three
days for E6.5 starts. These are distinct starting-cohort contexts, not a pooled
comparison. The Cycle 274 search of official bioRxiv full-text/data/supplement
routes, NCBI GEO/BioProject, and DataCite found no separate Figure 4D source
table in the inspected routes. The GEO author query returned 11 titles/dates
that do not match this preprint; bounded exact-title/DOI queries returned no
match. This is not a global absence claim. Cycle 275 checked the official bioRxiv version API and Crossref, PubMed, Europe PMC and ORCID records: the target remains listed as bioRxiv v1/posted-content, with no journal-version match in those checks. A same-author PubMed result was a distinct preprint and was not substituted. This status screen does not rule out a retitled or incompletely indexed report. Cycle 276 extended the public-data screen to EMBL-EBI BioStudies and MetaboLights: exact BioStudies DOI/title queries and MetaboLights DOI/title/author queries returned no target; four broader BioStudies results were disambiguated as older, different papers. This is still a bounded index result. See the [Cycle 276 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle276.json) and [crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/biostudies-broad-query-crosswalk-cycle276.csv). Cycle 277 found one OpenAIRE exact-DOI publication record with an EPFL institutional full-text pointer and no exact-DOI dataset record. Direct requests to the EPFL record and bitstream were blocked (429), so this copy remains unverified; GitHub/Zenodo/Figshare outcomes are documented as bounded queries, with the Zenodo DOI route treated as an error. See the [Cycle 277 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle277.json). Cycle 278 queried the official Metabolomics Workbench title and last-name fields: the target-title and four coauthor queries returned zero, while seven broad “mouse embryo” records were disambiguated as different studies. The API has no DOI search field, so this remains a bounded metadata screen. See the [Cycle 278 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle278.json) and [crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/metabolomics-workbench-broad-title-crosswalk-cycle278.csv). See the [Cycle 272 crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/extended-data-fig3d-g-strain-replication-cycle272.csv),
[Cycle 273 crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/extended-data-fig4d-serum-stage-cycle273.csv)
and [Cycle 274 route-screen receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle274.json).

E6.5-start molecular endpoints approach E12.0 controls with cell-composition
deviations; E7.5-start profiles are compared with E12.5 controls (pages 9–10,
lines 282–322). Preserve starting cohorts, duration and modality-specific stage
comparisons. Discussion leaves direct environmental effects versus impaired
progression unresolved for an attenuated metabolic transition (page 18, lines
600–608).

These are qualitative source findings, not individual longitudinal records.
Neither transcriptomic resemblance nor partial placental tissue establishes
durable exchange or healthy later function. "Placental bypass" in this project's
comparison means external provision of selected functions over a bounded
interval; it does not mean all placental/extraembryonic tissue is absent.

## Runnable intake with explicit gaps

The [candidate dataset](config/observations/lokshtanov_2026_terminal_candidate.json)
contains eleven qualitative author-reported findings, one planned, missing
same-unit follow-up requirement, and 88 platform/timepoint coverage records.
It includes the E7.5 terminal-stage boundary, with four findings retaining
terminal adverse effects. It supplies exact PDF/printed-line locators and
preserves missing specimen/parent identities, unreported per-experiment outcome
numerators, unresolved event sequence and uncertainty. Both continuity edges remain
`not_reported`; missing follow-up is not counted as biological failure.

```powershell
python -m wombmodels validate-observations --dataset config/observations/lokshtanov_2026_terminal_candidate.json --out artifacts/lokshtanov-terminal-intake-NEW
python -m wombmodels verify-bundle --bundle artifacts/lokshtanov-terminal-intake-NEW --strict
```

Run with the project installed or `src` on the Python import path. Output
directories must be new. The command performs no network requests or biological
assay. It now retains `preprint` as an explicit source class in the JSON and
Markdown report. Candidate/human review and journal peer review stay separate.

The intake receipt pins the submitted curated JSON and generated outputs. The
separate Cycle 270 receipt pins the primary PDF and qualifies selected text
transcription; neither receipt establishes scientific eligibility. Numeric
source-scope containment stays unassessed because these
records retain textual stage conventions. No incidence estimate, biological fit,
operating parameter or ledger promotion is produced.

## Discriminate failures before choosing a replacement function

| Candidate explanation | Observations that could distinguish it in source-linked records | Inference to avoid |
| --- | --- | --- |
| Delivery fails within the growing unit | Spatially resolved receipt/clearance, route identity, growth and injury timing in linked units | Adequate bulk supply or vessel markers prove adequate delivery to internal tissue. |
| Tissue metabolic use fails despite delivery | Joint precursor/input, compartment processing and organ-specific function, with injury/progression retained | An altered label fraction uniquely identifies failed delivery or one correctable metabolic defect. |
| Vascular/fluid dysfunction contributes to injury | Linked circulation/compartment state and the onset of edema, hemorrhage and organ dysfunction | The reported adverse findings establish a specific cause or event sequence. |
| Missing developmental interactions constrain progression | Source-matched interface/tissue relationships, developmental function and comparable outcomes | A marker list or a later support system replaces the omitted interaction. |
| Selection or stage mismatch conceals the boundary | Starting rosters, failed/excluded units, actual stage and endpoint-assessment branch | Selected molecular endpoints represent every starting embryo or agree with chronological duration. |

This is a competing-explanation map, not a diagnosis or a proposed experimental
protocol. More than one explanation can contribute. The inspected passages do
not establish a unique terminal cause or show that adding a particular input
extends the interval.

## Consequences for the machine concept

Machine A's requirement becomes **maintaining effective delivery and relevant
extraembryonic/tissue function as the unit grows**. Interface formation is one
candidate route; a bounded external-function substitute is another. Their
comparison needs actual internal receipt and preserved development, including
losses across the transition. No particular connection, replacement material or
biological operating setting follows from this requirement.

Machine B must retain spatial/compartment evidence and adverse-outcome onset
alongside supply accounting, metabolism and stage progression. Do not collapse
these observations into a single success score. Destructive endpoint profiles
need their own sampling branch; they cannot be followed as surviving units.

The next useful source qualification is the **late-window cohort and compartment
dossier**: original source data, embryo/dam/litter and technical hierarchy,
starting/excluded/endpoint rosters, internal function, adverse findings and
assessment timing. Reconcile E6.5/E7.5 starts and modality-specific stage matches.
Then ask whether the observations discriminate delivery failure, tissue-use
failure or other mechanisms before extending the computational model.

The [material handoff refinement](MATERIAL_HANDOFF_REQUIREMENTS.md) now adds
failure within support tissue as a distinct possibility: uptake may occur while
onward passage or secretion is impaired. A separate mouse reference motivates
compartment/material/context intake; it does not diagnose this preprint's
terminal injury or establish that changing an input will extend support.

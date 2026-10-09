# Qualify a moving developmental boundary

AI-assisted evidence curation and design inference, 2026-10-09. Human scientific
review pending. This is an offline requirements document; it supplies no embryo
procedure, tissue manipulation, culture condition, device assembly, physiological
setting or clinical recommendation. Complete human ectogenesis remains
unestablished.

Machine A's maternal surrogate has to be assessed as a **changing relationship
between tissues**, alongside usable exchange. A permissive space or a support
component with favorable assays cannot alone establish coordinated development.
This refines the [joint support/development requirement](SUPPORT_DEVELOPMENT_DISCORDANCE.md);
it does not identify the cause of arrest in that source.

## Bounded comparative evidence

[Bondarenko et al., The EMBO Journal (2023)](https://doi.org/10.15252/embj.2022113280)
examines whole mouse peri-implantation development in an engineered uterine
context. The [candidate source inventory](config/source_inventories/bondarenko_coordination_2023.json)
pins a public full-text XML retrieval and repository metadata. Selected Results,
Discussion and captions were qualified; raw images and individual outcomes were
not reanalyzed. Source protocols remain external.

| Source finding | What it supports | Limit that must travel with it |
| --- | --- | --- |
| E3.5 entry; 12 of 26 embryos meet the Day 3 composite morphology criterion across three experiments | A bounded early mouse developmental endpoint | Criterion combines egg-cylinder formation, axis alignment and Reichert's membrane; E5.25 resemblance is not chronological equivalence or later viability |
| Reichert's membrane in 20 of 26 embryos | A distinct extraembryonic boundary endpoint | Membrane presence alone does not satisfy the composite criterion; no individual outcome roster inspected |
| Matrix-adhesion comparison reduces developmental efficiency when adhesion support is absent | Maternal-facing interaction matters within this model | Does not establish human adhesion requirements or isolate all downstream effects |
| Live imaging relates embryo elongation to trophoblast/membrane movement; geometry comparisons disrupt coordination | Boundary displacement and embryonic growth should be assessed together | Figure 6I/J summarizes two versus four independent experiments; time points/cells cannot be counted as independent embryos |
| Rac1-deficient embryos have impaired growth and parietal-endoderm defects | A perturbation phenotype consistent with failed coordination | Multiple affected tissues prevent a trophoblast-only causal conclusion |
| A wetting model describes measured shape changes | A bounded explanation of early shape dynamics | Adhesion/tension dynamics are inferred from shape and volume, not directly measured forces; later development and human implantation are outside the fit |

Results sections `embj2022113280-sec-0003` through `-0007`, Figure EV1E/E',
Figures 3B/C, 4G-J and 6G-J, and Discussion `-0008` are the locators. The
reported endpoint denominator is preserved as a source summary, not promoted
to independently verified biological units or a readiness percentage. In
Figure 6, embryo-length and epiblast-cell-count denominators differ; they must
not be joined as if they were one paired cohort.

The model's leave-one-out comparison concerns shape prediction within the
inspected experiments. It does not establish an identified mechanical cause,
nutritional sufficiency, a controller or a healthy-organism trajectory. The
authors' proposed soft-wetting account of implantation in vivo remains a
hypothesis beyond the demonstrated engineered context.

## What the new cohort qualification resolves

The Jin source's publisher Supplementary Information, Tables 1 and 2 (PDF pages
8-9), and Reporting Summary, Statistics and Life sciences study design (pages
1-2), were rendered and visually inspected. Exact retrieval hashes and selected
counts are in the [updated inventory](config/source_inventories/jin_yolk_sac_2026.json).

- Table 1 reports starting blastocyst, eYS and vasculogenesis counts for 15
  condition rows. These are aggregate endpoints, without individual identities,
  failure categories or a link to the eight-experiment formation summary in the
  main article. They cannot supply a paired embryo-arrest rate.
- Table 2 labels four post-quality-control cell totals: eYS, E8.5, E9.5 and
  E10.5. Cells are not embryo replicates, and these labels do not recover pool
  members or link transcriptional profiles to the protein/uptake assays.
- The reporting summary defines a biological replicate as an experiment
  beginning with a new blastocyst batch and declares at least three for key
  findings. This resolves a global definition, without authenticating the three
  Figure 5 scalar columns, identifying repeated specimens, or assigning a batch
  to each record. Its distinct-versus-repeated-measure statement is marked n/a.
- The summary reports sequencing QC exclusions and author-available other data.
  Neither statement supplies a complete starting-embryo disposition roster.
  CRA024449 retrieval failed; its sample/file inventory remains unqualified.

The selected PDFs do not resolve concentration units, the NC definition or the
VEGFA text/table timing difference. Resolving aggregation metadata narrows the
missing information; it does not remove selection or stage mismatch.

## Data eligibility before a coordination reanalysis

The [public imaging record](https://doi.org/10.5281/zenodo.6546550) describes
annotated nuclei and membrane volumes for segmentation training/validation.
Its `raw` and `label` HDF5 datasets concern images and instance segmentation.
They are not ground truth for developmental health or support sufficiency.
Only repository metadata was retrieved; the approximately 3.1 GB archive was
not downloaded, and its internal specimen/time hierarchy remains uninspected.
The article's GSE228264 sequencing accession is a separate resource; no
phenotype join is established.

Before fitting a boundary-growth relationship, require:

1. Actual embryo, experiment and source/litter identities, with the complete
   starting cohort and exclusions. A training/test stack split is insufficient.
2. Source-located trajectories for embryo growth and its boundary in the same
   units, with timestamps, stage assessment, coordinate definitions, registration
   and segmentation uncertainty. Multiple tracked cells remain nested in embryos.
3. Individual composite outcomes and adverse findings, including missing and
   failed units, plus the actual comparison/perturbation assignment.
4. Independently qualified support receipt/function if the question asks whether
   coordination fails *despite adequate support*. Growth/movement observations
   alone cannot decide that question.

Until these links are available, the [candidate intake](config/observations/bondarenko_2023_coordination_candidate.json)
contains qualitative author summaries and an explicitly missing follow-up.
Biological IDs are null, continuity is `not_reported`, and no biological model
is fitted. The new source does not explain Jin's arrest merely by sharing a
mouse species or an early developmental interval.

```powershell
python -m wombmodels validate-observations --dataset config/observations/bondarenko_2023_coordination_candidate.json --source-root . --out artifacts/boundary-intake-NEW
python -m wombmodels verify-bundle --bundle artifacts/boundary-intake-NEW --strict
```

Run with the package installed or `src` on the import path and a new output
directory. Local source hashing checks the declared XML if available; it does
not review the biology or fetch missing external files. The updated Jin intake
uses its existing command with a new output directory and now declares four
artifacts, including the two pinned PDFs; the rendered manuscript stays unpinned.

## Consequence for the machine hypothesis

**Machine A:** qualify the capacity of the maternal surrogate and endogenous
extraembryonic boundaries to accommodate coordinated growth over the actual
developmental interval. One fixed geometry or stiffness value cannot be assumed
to establish that capacity. No preferred geometry, material, motion or force
setting follows from this source curation.

**Machine B:** retain separate observations of recipient support, embryo
progression and boundary coordination, with specimen/experiment hierarchy and
adverse endpoints. Inferred force or stage must remain distinguishable from a
measured quantity. Segmentation accuracy is a measurement prerequisite, not a
developmental outcome.

**Next discriminator:** determine whether source trajectories link loss of
boundary coordination to a later morphological outcome within the same embryo,
against the appropriate source comparator. If only pooled traces or segmentation
training labels are obtainable, retain the comparative source finding and defer
an effect estimate. A positive bounded mouse result would still leave the
transition to sustained exchange, human implantation and healthy later outcomes
open.

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

Selected Results, Discussion and captions from a public
[rendered primary manuscript copy](https://www.researchgate.net/publication/403370800_Reconstituting_Mouse_Embryogenesis_Ex_Utero_from_Gastrulation_to_Fetal_Development_Reveals_Maternally_Independent_Metabolic_Programs)
were inspected, with matching DOI/date banners for
[Lokshtanov et al., bioRxiv v1](https://doi.org/10.64898/2026.03.17.710314).
This is a preprint. Original publisher source bytes, methods, figures,
supplements and copy/version integrity remain unqualified. An anonymous raw
mirror retrieval returned HTTP 403; no raw-source hash is asserted.

The manuscript reports slower late growth and terminal heart enlargement,
pericardial edema, internal hemorrhage and tissue necrosis (page 6, lines
179–186). The authors attribute injury to insufficient internal oxygen/nutrient
delivery; that mechanism is not independently identified here. Results also
report a small placental labyrinth portion, with junctional zone/decidua mostly
absent (page 8, lines 259–264).

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
contains nine qualitative author-reported findings and one planned, missing
same-unit follow-up requirement. Four findings retain terminal adverse effects.
It supplies exact manuscript locators and preserves missing specimen/parent
identities, incidence, event sequence and uncertainty. Both continuity edges
remain `not_reported`; missing follow-up is not counted as biological failure.

```powershell
python -m wombmodels validate-observations --dataset config/observations/lokshtanov_2026_terminal_candidate.json --out artifacts/lokshtanov-terminal-intake-NEW
python -m wombmodels verify-bundle --bundle artifacts/lokshtanov-terminal-intake-NEW --strict
```

Run with the project installed or `src` on the Python import path. Output
directories must be new. The command performs no network requests or biological
assay. It now retains `preprint` as an explicit source class in the JSON and
Markdown report. Candidate/human review and journal peer review stay separate.

The receipt pins the submitted curated JSON and generated outputs. It does not
pin the rendered source bytes, validate transcription or establish scientific
eligibility. Numeric source-scope containment stays unassessed because these
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

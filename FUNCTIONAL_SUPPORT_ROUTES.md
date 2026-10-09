# Preserve developmental functions while testing alternative support routes

AI-assisted exploration, 2026-10-09; human scientific review pending. These
are evidence requirements and competing functional architectures. No culture
procedure, device assembly, physiological setpoint or clinical implementation
is supplied. Complete human embryo-to-birth support remains unestablished.

The [early exchange transition](EARLY_EXCHANGE_TRANSITION.md) prioritizes
endogenous extraembryonic tissues. A further distinction matters: **preserving
their required functions does not prove that a formed placenta must supply
every function throughout every research interval**. Test that necessity by
interval and outcome. Do not assume either complete placental replacement or
universal dependence on one anatomical interface.

## A new candidate changes the comparison to investigate

[Lokshtanov et al., bioRxiv v1 (2026)](https://doi.org/10.64898/2026.03.17.710314)
reports mouse development from E6.5/E7.5 to approximately E12.5. Its abstract
describes an E10.5–E11.5 metabolic transition occurring ex utero without direct
uterine/placental cues, with environmental modulation insufficient to advance
the transition prematurely. This is a preprint claim, inspected through the
bioRxiv API and the [authors' institutional abstract](https://www.janelia.org/publication/reconstituting-mouse-embryogenesis-ex-utero-from-gastrulation-to-fetal-development).
It starts after implantation and does not establish embryo-to-birth support.

The API returns version 1, posted 2026-03-18, with `published: NA`. That is the
observed metadata, not proof that no later publication exists anywhere. Original
full-text retrieval failed and the API-listed XML request was rate limited.
Subsequent [terminal-boundary intake](MIDGESTATION_BOUNDARY.md) inspected selected
Results/Discussion and captions in a rendered primary manuscript copy. It retains
late adverse findings and an author-attributed delivery explanation, with no
observed raw-source hash. Original data, unit incidence, same-unit relationships,
copy integrity and causal identification remain unqualified.

**Design inference:** retain a bounded placental-bypass hypothesis for comparison
with the growing biological interface. A metabolic transition that is partly
intrinsic motivates testing whether support can accommodate development without
initiating its timing. It does not establish maternal-function dispensability,
human stage equivalence, or support beyond the reported interval.

## Delivery and developmental use need separate evidence

[Solmonson et al., Nature (2022)](https://www.nature.com/articles/s41586-022-04557-9)
is a peer-reviewed in-utero mouse reference. It reports different metabolic
programs in embryo, placenta and developing organs. In the LIPT1-deficient
comparison, the authors report preserved uptake/transfer of glucose and
glutamine labels, yet impaired embryonic TCA-cycle metabolism, organ/erythroid
development and death by GD11.5. Preserve those as source findings and author
interpretation, rather than a machine failure diagnosis or a proposed treatment.

**Design inference:** successful delivery is one necessary observation, with
metabolic use and development assessed independently. Additional external supply
cannot be assumed to repair a defect in how a developing tissue uses it.
Whole-unit averages can also conceal different organ responses. Conversely,
an altered labeling ratio does not alone identify impaired delivery: precursor
enrichment, tissue processing, pool composition and observation design matter.

## Source-data qualification narrows the first offline comparison

Two original source workbooks were retrieved and inspected read-only; hashes
and exact locators are recorded in the [candidate inventory](config/source_inventories/midgestation_frontier_2026.json).
No workbook was edited/exported, author analysis code executed, or biological
parameter fitted.

| Inspected source location | What is available | Eligibility limit |
| --- | --- | --- |
| Figure 2 workbook, `Figure 2b`, A23:J32 | Embryo tissue/tracer/time headers, sample labels and isotope-label entries | C25 identifies `WT47 E1 0`; I25 identifies `WT47 E4 30`. Distinct embryos appear at these times. Preserve the source time axis; it is not developmental age or a same-embryo trajectory. |
| Extended Data Figure 5 workbook, `Extended Data 5d`, B22:C23 | Normalization labels and their formula references | B22/B23 say “Blood/Placenta”; C22 is `=C20/$C9`, and C23 is `=C19/$C8`. The inspected references compute placenta/blood. Preserve this label/formula discrepancy and qualify quantity direction before intake. |
| Same sheet, C33:C55 | Placenta/embryo sample labels, source isotope entries and derived ratios | Matching labels support candidate tissue-pair relationships; they do not authenticate the full dam/litter/embryo hierarchy or establish longitudinal outcomes. |

These are published isotope-label quantities and derived ratios, not absolute
delivery/clearance fluxes. Mass amounts, appropriate pools, precursor inputs,
correction provenance and biological hierarchy would be needed for a suitable
kinetic model. The paper links isotope-correction code; it was not executed.
Nonsignificance in a source comparison is not an independently established
equivalence margin or proof of identical transport.

The first eligible offline target should be **a descriptive compartment/stage
comparison with qualified labels and pairing**, before any mechanism fit.
Do not pool glucose and glutamine, normalize away the source compartment, or
count isotope bins/technical repeats as independent embryos. Qualification of
published entries remains separate from complete support validation.

## Revise the architecture comparison

| Hypothesis | What it could reduce | What would disqualify it for the declared interval |
| --- | --- | --- |
| Growing endogenous extraembryonic/placental interface with a maternal surrogate | Burden of replacing unidentified tissue processing, signaling and developmental interactions | Interface formation/growth fails, needed functions disappear, or development is impaired despite adequate equipment behavior. |
| Bounded external support that bypasses selected placental functions while retaining embryo/extraembryonic development | Burden of recreating every maternal anatomical relationship in that interval | Delivery or metabolic/developmental function cannot be preserved, or extension/transfer loses continuity. |
| Fixed exchange component | Provides a narrower functional comparator | Matching passage/enrichment conceals abnormal metabolism, compartment state, injury or organ development. |

The preferred full-course hypothesis remains endogenous preservation. The new
branch changes which necessity assumption to test; it does not select a human
implementation. Later fetal-support evidence cannot close either branch's
missing earlier transitions.

Machine A must accommodate the tissue relationships required by its declared
route. Machine B must distinguish:

1. Material reaches the relevant compartment.
2. The compartment processes and uses it appropriately for the observed stage.
3. Relevant organ/lineage development proceeds with adverse findings retained.
4. The same starting units retain function across any support-route transition.

These are independent observation requirements, not controller targets. Do not
infer readiness from their count or infer health from agreement on selected
metabolites. An intrinsic developmental change still requires a compatible
external environment; independence from direct maternal cues is not independence
from support.

## Next feasibility milestone

Qualify the preprint's original results, supplements and cohort records, then compare the two
routes using a **function-by-interval dossier**: source species, actual starting
state, interface retained/replaced, delivery, metabolic use, development,
attrition and later transition. Keep destructive tissue endpoints separate from
longitudinal observations of a surviving unit. The 2021 and 2026 mouse intervals
are separate studies and must not be joined into a longer demonstrated path.

The immediate unresolved question is whether a supported interval ends because
exchange capacity, tissue metabolism, developmental interaction or another
function fails. Additional narrative findings narrow the question but do not
identify a unique cause. Resolving that
boundary, with adverse outcomes and comparators, would inform which function
Machine A actually needs next.

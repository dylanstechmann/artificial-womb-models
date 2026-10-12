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
reports mouse development from an E7.5-start cohort to approximately E12.5 and
a separate E6.5-start cohort to approximately E11.75. The official v1 PDF is
now pinned and hashed. The E7.5 cohort reaches its maximum reported morphology
after 5.5 culture days, but the embryos do not progress beyond day 5 with an
intact yolk sac; the additional ~12 hours uses opened yolk sac tissue while
retaining umbilical vascular continuity. Only 10-20% are reported as properly
developed at that final point across strains, and the authors report cardiac
enlargement, pericardial edema, internal hemorrhage and tissue necrosis. Their
internal oxygen/nutrient-delivery explanation remains an author-attributed
mechanism, not a source-linked causal estimate. The paper also reports an
E10.5-E11.5 metabolic transition recapitulated ex utero with environmental
modulation; this does not establish independence of all support functions.

The manuscript is explicitly marked as not certified by peer review. Its
cohort-level morphology and isolated-gonad oocyte assay do not establish
whole-animal birth or later health. Figures 1D and 2D have 46 source-linked
platform/timepoint embryo and experiment-count pairs. Extended Data Figures 3D
and 3G add 42 strain/serum and independent-laboratory emb/n labels; Figure 3D
does not define the unit for n in its caption, while Figure 3G defines n as
independent experiments. Figure 4D adds an E6.5-start HAS/HCS comparison with
caption-defined experiment counts but no embryo denominator; the primary Results
contrasts its HCS advantage after three days with the E7.5 no-evident-difference
report. Keep these stage contexts separate. The plotted experiment-level
percentages do not yield exact normal-embryo numerators, pooled success rates or
unit-level losses. A bounded supplement search found one PDF and no separate
source-data table on the inspected route. A Cycle 274 full-text/data-tab and
NCBI/DataCite screen did not locate a separate Figure 4D table in the queried
routes; this is a bounded access result, not proof of global absence.
Cycle 275 version checks still identify this source as bioRxiv v1/posted-content;
no journal-version match surfaced in the checked Crossref, PubMed, Europe PMC and
ORCID records. Independent scientific review remains open. Cycle 277 found one exact-DOI OpenAIRE publication record that points to an EPFL full-text file, but direct requests were blocked and the file could not be verified; no matching dataset record was indexed. Zenodo, Figshare and GitHub repository searches yielded no verified data/code match. See the [Cycle 277 route receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle277.json). Cycle 278 added the official Metabolomics Workbench title/author screen; it surfaced no target-linked record, and its seven broad mouse-embryo hits are unrelated indexed studies. Its documented API has no DOI input. See the [Cycle 278 route receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle278.json). Cycle 276 added official BioStudies and MetaboLights API searches; exact DOI/title and author searches did not locate a matching record, and four broader BioStudies hits were older unrelated papers. These are bounded public-index results, with no global data-absence claim. See the [Cycle 276 route receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle276.json). The
[terminal-boundary intake](MIDGESTATION_BOUNDARY.md) and
[primary-PDF receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/primary-pdf-qualification-cycle270.json)
preserve the source locators and distinctions.

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


### Exchange-transfer evidence depends on substrate, stage and denominator

[Sandovici et al. (2024)](https://doi.org/10.1242/dmm.050719) report in-utero mouse tracer measurements at E15.5 and E18.5. The result changes with tracer, denominator and sex: the combined-sex glucose panel shows lower accumulation per fetus but similar transfer per mm² labyrinthine surface area, while the amino-acid analogue is lower per fetus at both ages and lower per gram fetus and per mm² at E18.5. The sex-stratified glucose supplement shows an E18.5 per-area difference, stronger in females; the Discussion's surface-area-adjusted summary does not align cleanly with the combined-sex glucose panel. Preserve this source-level qualification. Transfer analyses use within-litter averages; values are not same-fetus trajectories.

**Design inference:** keep nutrient class, developmental interval, normalization denominator, sex, interface area, fetal growth, circulation and downstream use as distinct observations. A matched glucose endpoint cannot validate amino-acid exchange, and neither endpoint alone establishes healthy development. This is an animal-derived architecture constraint, not a human target or control setting. The [source screen](SANDOVICI_2024_MOUSE_PLACENTAL_DEMAND_SOURCE_SCREEN_2026-10-10.md) found no machine-readable per-litter transfer rows; the [panel inventory](config/source_inventories/sandovici_2024_transfer_panel_inventory.csv) retains source-reported cohort counts without importing or digitizing outcome values.

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

## What the four 2026 FLI posters establish about function

The EP09.20/22/31/40 evidence map separates direct function evidence from
biological response markers and selected outcomes. EP09.20 directly measures
serum IL-6 as an inflammatory-response marker; EP09.31 reports selected growth
and circulating biochemical summaries; EP09.40 reports circulating ACTH and
steroid summaries; EP09.22 reports four selected neonatal-transition cases.
These results describe fetal responses and some outcomes during or after
support. They do not, in this poster set, directly quantify net exchange or
clearance, establish interface-barrier performance, or show complete placental
function replacement. A circulating concentration is not a delivery or
clearance flux, and an endocrine concentration is not evidence that placental
endocrine functions were replaced.

Keep all four source frames distinct. Biochemical endpoint denominators are
unstated in EP09.31; timepoint denominators are unstated in EP09.20 and EP09.40;
EP09.22 contains four selected transition cases without an all-start denominator.
No same-unit linkage among posters is established. Thus these observations
cannot yet show that measured support function, developmental progression,
transition and follow-up coexist in the same starting unit. The detailed
claim-to-evidence boundaries and ranked intake gaps are recorded in the
[Cycle 311 sufficiency map](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle311/REPORT.md).

The [Cycle 313 row-level overlay](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle313/REPORT.md)
classifies 51 poster-candidate observation rows: 29 circulating response
summaries as proxies, 18 growth/transition observations as developmental
outcomes, four support-duration observations as exposure context, and zero as
direct exchange measurements. It pins each candidate hash and source row
locator. These classifications remain a review aid; candidate JSON files were
not modified and human source review is pending.

A [Cycle 314 temporary rehearsal](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle314/REPORT.md)
applied those tags to in-memory copies, ran the observation validator/exporter,
verified all four pinned poster PDFs and the generated bundles, and confirmed
the candidate files remained byte-for-byte unchanged. This establishes that the
intake path preserves the classification and source provenance; it does not
independently validate the scientific interpretation of each class.

The [Cycle 315 overlay](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle315/REPORT.md)
extends the same distinction to the peer-reviewed Eixarch 2023 sheep study.
Its six circuit-flow group summaries directly report support-circuit output,
while pH, lactate, and heart rate are response proxies; neither category
quantifies net exchange or substrate use. Survival-goal, survival-duration,
complication, and hydrops records are outcomes. The three assigned-goal frames
(n=8/10/10) remain distinct, and those cohort counts are not endpoint-specific
sample sizes or individual-unit links.

The [Cycle 316 gas-transfer screen](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle316/REPORT.md)
found a methods-level paired membrane blood-gas measurement route in that
article, but no numeric paired PaO2/PaCO2 results or net transfer estimates in
the inspected Results/Table 1 or candidate. Methods-level targets are not
treated as achieved function or added as operating settings. The article says
“Not applicable” for data availability; the search remains bounded to the
pinned article and checked route.

The [Cycle 317 intake change](PHENOTYPE_INTAKE.md) adds an optional dataset-level `measurement_pairs`
contract for records that a source explicitly pairs or that a curator links
with a cited mapping. It retains member roles and exact source location, rejects
unknown record/artifact references, and exports the relation for review. A
`same_unit_same_time` label also requires matching reported unit IDs and exact
non-null measurement times/units. The
2023 Eixarch candidate has no reported gas-result rows to pair, so no relation
was added there.

The [Cycle 319 public-source screen](artifacts/artificial-placenta-gas-pairability-2026-10-11-cycle319/REPORT.md)
compared two more sources that describe inlet/outlet gas sampling. The
inspected article routes provide no source-linked paired results; the in-vitro
oxygenator paper reports an aggregate device result only. Their methods support
the existence of a measurement route, not an achieved per-run exchange record.

The [Cycle 320 candidate](artifacts/omecinski-preemieox-2023-10-11-cycle320/REPORT.md)
adds the published Preemie-Ox in-vitro group summary through the typed mean±SD
intake. This device-level result is kept separate from fetal physiology and
developmental outcomes; the nine test samples are not treated as independent
biological units.

The [Cycle 321 source-resolution check](artifacts/omecinski-source-resolution-2026-10-11-cycle321/REPORT.md)
resolves the public PMC record to the current author-manuscript version and
records that its full text is readable while it is absent from the PMC OA
filter. Those access facts do not resolve article-specific reuse rights, and
the publisher DOI route was unavailable to inspection. The source hash and
candidate review therefore remain pending.

The [Cycle 322 test-context intake](artifacts/omecinski-flow-context-2026-10-11-cycle322/REPORT.md)
adds the co-reported Preemie-Ox mean blood flow (`163 ± 2 mL/min`, n=9) as an
aggregate environmental-condition summary. It is not paired to the aggregate
vCO2 result because the public record contains no run-level mapping.

The [Cycle 323 notation audit](artifacts/omecinski-uncertainty-scope-2026-10-11-cycle323/REPORT.md)
found that the paper does not define its `±` terms as SD or SE. The two
previously typed SD fields were corrected to source-neutral estimate ±
quantity records, and the SO2 result was added with a null denominator because
“all three cases” does not identify the denominator of that summary.

The [Cycle 324 hydraulic-constraint intake](artifacts/omecinski-device-constraints-2026-10-11-cycle324/REPORT.md)
adds the source-reported oxygenator resistance and priming volume as distinct
device-characterization observations. The resistance protocol's triplicate
count is kept separate from a biological sample size; no individual runs or
gas-exchange pairs are created.

The [Cycle 325 A-Maze-Ox intake](artifacts/schubert-amazeox-oxygen-transfer-2026-cycle325/REPORT.md)
adds five text-reported oxygen-transfer points with source-linked operating
mode and blood-flow conditions. In one porcine-blood proof-of-concept test,
adding the compartment raises transfer at 125 mL/min, but the reported maximum
remains below both paper-defined oxygen-transfer targets. Preserve the ISO
conditioning and the source's higher-than-fetal-reference inlet pO2 caveat;
these measurements establish neither fetal support nor clinical performance.

The [Cycle 326 hydraulic intake](artifacts/schubert-amazeox-pressure-loss-2026-cycle326/REPORT.md)
adds the source's 14.9 mmHg pressure drop at DC/50 mL/min and the report that
its 20 mmHg engineering criterion was exceeded at 90 mL/min. The final
pressure-sweep value retains an unresolved “190 mmHg” flow-label conflict;
it is not silently corrected or graph-digitized. The pressure finding makes
hydraulics a second limiting device function alongside oxygen transfer.

The [Cycle 327 data-route screen](artifacts/schubert-amazeox-data-route-2026-cycle327/REPORT.md)
found no raw per-operating-point dataset in the inspected publisher/PDF and
exact DOI-linked DataCite, Crossref, Figshare or OpenAIRE routes. Zenodo was
unavailable with HTTP 500. The article's on-request data route remains open;
no author was contacted and no global data-absence claim is made.

The [Cycle 328 target-provenance audit](artifacts/schubert-amazeox-target-audit-2026-cycle328/REPORT.md)
found a small internal difference: Table 1's derived oxygen-transfer targets
are 55.82/59.04 mL O2/L blood, while Results/Discussion uses 55.96/59.19.
The source does not resolve the difference. All five measured operating
points remain below either pair, so the device comparison's direction is
unchanged; the exact target basis stays source-located and open.

The [Cycle 329 reference-provenance audit](artifacts/schubert-amazeox-reference-provenance-2026-cycle329/REPORT.md) traces the cited flow, fetal blood-gas, hematology and transfer-equation sources. Recalculation from Table 1's displayed values closely reproduces both tabulated targets; the 0.14/0.15 mL O2/L difference in Results/Discussion remains unexplained, with hidden input precision plausible but unconfirmed. The equation source is pinned and hashed; the candidate is unchanged and no author was contacted.

The [Cycle 330 flow-sensitivity analysis](artifacts/schubert-amazeox-flow-sensitivity-2026-cycle330/REPORT.md) follows the paper's alternative Gerson et al. flow reference. Its published regression reproduces the paper's rounded 118 mL/min estimate at 24 weeks; using it instead of the selected Kiserud flow raises the derived OTR rate by 1.77×. The 28-week regression output is derived, not a directly reported age-specific value, and exceeds the oxygenator's 150 mL/min test ceiling. This remains a separate cohort scenario; the candidate is unchanged and no author was contacted.

The [Cycle 331 Kiserud source-access screen](artifacts/schubert-amazeox-kiserud-source-access-2026-cycle331/REPORT.md) confirms the reference cohort and Doppler measurement route from the primary abstract, but the exact regression and 24-/28-week flow outputs are not exposed there. The inspected Wiley full-text routes returned 403; PubMed and Crossref records are pinned. Retain Table 1's flows as attributed, not independently recalculated from full text.

The [Cycle 332 flow/weight sensitivity analysis](artifacts/schubert-amazeox-flow-weight-sensitivity-2026-cycle332/REPORT.md) keeps Gerson's absolute and weight-normalized regressions separate from the Kiserud-derived Table 1 means. Their cross-source OTR scenarios vary materially, so retain gestational age, fetal weight, absolute/normalized flow, and regression provenance as distinct evidence fields. No source observation was added and the candidate is unchanged.

The [Cycle 334 oxygen-uptake cross-check](artifacts/schubert-amazeox-uptake-comparison-2026-cycle334/REPORT.md) finds A-Maze-Ox's 28-week normalized transfer target nearly matches a historical human uptake endpoint, but the original table and uncertainty remain unverified. A modern MRI cohort measures in-vivo oxygen delivery, not uptake; the human critical delivery threshold is unknown. Candidate unchanged, no observations or pairs added, and no author contacted.

The [Cycle 335 primary-source recovery](artifacts/schubert-amazeox-assali-source-recovery-2026-cycle335/REPORT.md) recovers Assali et al.'s Table II from the 1960 issue scan and creates a review-pending candidate for its eight uptake cases, denominator and four blank rows. The 24-week A-Maze-Ox-derived rate is 20.6% above the one approximate same-week case; the 28-week value is within 0.25% of its one case. Treat this as a cross-source scale comparison, not validation or a specification. Reuse rights remain unconfirmed; no author was contacted.

The [Cycle 336 CO2 evidence comparison](artifacts/schubert-amazeox-co2-evidence-cycle336/REPORT.md) finds no fetus-only, absolute human CO2 production rate at 24–28 weeks in the inspected sources. The Bonds et al. abstract's 9.2 ± 1.2 mL/min/kg result combines fetus and placenta and leaves age, endpoint n and mass denominator unresolved; Wiberg et al.'s large cohort is term-only and reports a fractional index. Preemie-Ox's numeric bench removal exceeds the A-Maze-Ox modeled rate targets, but its flow and inlet conditions are not matched. One historical summary is retained as a review-pending candidate; no physiological requirement or safe acid-base envelope is inferred.

The [Cycle 333 fetal blood-gas provenance screen](artifacts/schubert-amazeox-gas-inputs-2026-cycle333/REPORT.md) compares A-Maze-Ox’s textbook-attributed inputs with two primary Soothill abstracts. The accessible values do not establish a source-matched 24-/28-week gas set; retain the source scopes, add no observations or UA/UV pairings, and do not contact authors.
The [Cycle 337 CO2 equation audit](artifacts/schubert-amazeox-co2-equation-audit-cycle337/REPORT.md) reproduces A-Maze-Ox Table 1's 24-/28-week CT targets and CTR rows from the displayed inputs and Khadka's equations. This closes the arithmetic check while leaving the textbook pH provenance and physiological representativeness open; the modeled targets remain distinct from direct fetal CO2 production evidence.
The [Cycle 338 blood-gas source audit](artifacts/schubert-amazeox-blood-gas-source-audit-cycle338/REPORT.md) traces A-Maze-Ox's shared pH and UA/UV gas tuple to an inaccessible textbook passage. Primary human fetal studies report gestational changes, but the inspected abstracts do not provide a full matched 24-/28-week tuple. Keep the published inputs attributed and preserve their source-age uncertainty; the broad-range Bon et al. UV summary is a candidate for separate abstract-level intake.

## Human gas evidence: broad gestational summaries do not supply an age-specific setpoint

The [Cycle 339 Bon et al. abstract intake](artifacts/schubert-amazeox-bon1997-intake-cycle339/REPORT.md) preserves six umbilical-vein group summaries from 73 AGA fetuses across 17–41 weeks. Its abstract leaves the meaning of each ± term and each endpoint denominator unspecified and provides no age-stratified cells. Keep this comparison separate from A-Maze-Ox's shared Smith's-textbook-attributed inputs. It does not establish values at 24 or 28 weeks, a support requirement, or an acid-base safety envelope.


The [Cycle 340 publisher-route audit](artifacts/schubert-amazeox-bon1997-publisher-access-cycle340/REPORT.md) locates Bon et al.'s exact JLE article. The publisher abstract repeats the candidate values, but the full text is freemium and its unauthenticated response exposes only an opening paragraph; the journal-level archive entry requires individual registration. This route confirms transcription provenance while leaving age-specific data and endpoint denominators open.


The [Cycle 341 Schröter et al. candidate](artifacts/schroeter-1997-gas-trends-intake-cycle341/REPORT.md) adds a source-reported age trend from 155 human AGA fetuses at 18–39 weeks. pH, pO2 and pCO2 were measured; oxygen saturation, bicarbonate and base excess were calculated. Because the abstract omits the regression coefficients, numeric 95% confidence bounds and age-bin counts, these trends only flag the need to verify age-specific gas inputs; they cannot supply 24-/28-week targets or ex-utero support specifications.


The [Cycle 342 source-window screen](artifacts/schubert-amazeox-age-window-source-screen-cycle342/REPORT.md) found no directly inspectable antenatal human cordocentesis table with numeric 24- and 28-week cells in the reviewed sources. Preserve the boundaries: the Soothill cohort mixes cordocentesis and fetoscopy routes, and the open Filippi et al. regression cohort sampled newborn cord blood after delivery. Neither supplies an antenatal machine target. The next access check is Nava et al. (1996), with any recovered pH/pO2 data kept endpoint-specific.


The [Cycle 343 Nava et al. intake](artifacts/nava-1996-ph-p02-trends-cycle343/REPORT.md) adds an independent in-utero cohort with source-reported decreases in venous pH and PO2 across 18–37 weeks. Its abstract gives no numeric age-specific table or regression coefficients, and samples both the placental cord insertion and intrahepatic vein. Keep the trends and sample sites qualified; they inform age dependence but supply no 24-/28-week target.


The [Cycle 344 Weiner et al. intake](artifacts/weiner-1992-reference-window-cycle344/REPORT.md) adds abstract-level trends for umbilical venous pCO2, pO2 and pressure across gestation. Its 80-fetus reference cohort was referred for maternal alloimmunization or infection, and the publisher marks the primary article PDF only. These trends flag age dependence but supply no numeric 24-/28-week values or machine requirements.

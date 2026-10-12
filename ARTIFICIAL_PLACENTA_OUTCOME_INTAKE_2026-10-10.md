# Fetal extracorporeal-support outcome intake

**Screen date:** 2026-10-10
**Status:** candidate evidence map; human scientific review pending.
**Purpose:** distinguish maintenance of fetal physiology from developmental
health, and record what a source must expose for longitudinal outcome intake.
This is evidence qualification, not an animal protocol, device design, or
clinical recommendation.

## Cohort-linkage screen update

A bounded public search on 2026-10-10 checked exact-title and repository-index
queries for a crosswalk among the BCNatal 2023 14-day milestone, the 12
experiments in the 2023-2024 fetaLife abstract, and the four transition cases
in ISUOG poster EP09.22. The abstract exposes aggregate results without
per-animal rows; EP09.22 labels its four rows only as Animals 1-4; and the
annual report gives no denominator. No shared animal identifier or public
crosswalk appeared in the sources checked. The cohorts may overlap, but the
available evidence does not establish how. This bounded search cannot rule out
private, embargoed, differently indexed, or unpublished linkage data, and no
author was contacted. The official poster PDF is now pinned and the single page was visually inspected. Animal 2's cell is confirmed as 24 days and remains unchanged. The source-linked candidate now contains 20 typed observations across the four poster-local cases, including the four printed FLI durations and four weights whose measurement time is not stated; its local source hash verifies against the pinned PDF. The displayed support values [9, 24, 8, 7] average 12.0 days (sample SD 8.04), while the poster summary says 9.6 ± 3.1 days. The Animal 2 gestational-age increment is 14 days versus 24 support days; Animal 4's increment is 10 days versus 7 support days. The poster does not explain whether these columns use different clock origins, so all printed fields remain separate. Three transition cases have post-transition survival of 2, 5 and 7 days; Animal 4 is reported to survive 13 months with one maze assessment at 3 months. The four transition cases do not supply an FLI-start denominator.

The public [2022 Eixarch et al. abstract](https://doi.org/10.1002/uog.25056)
also reports 18 sheep in an earlier version of the same group's learning-curve
program. The 2023 full paper reports 28 transfers with different goal bands.
No animal-level crosswalk clarifies whether these reports overlap, so their
sample sizes are not additive and should not be counted as independent
replications.

The 2022 abstract defines reproducible survival as two consecutive or three
non-consecutive goal-reaching experiments with stable hemodynamics and stated
oxygenation ranges. The 2023 full paper reports group percentages reaching
survival goals and uses “reproducible” in its conclusions, but its Methods do
not state that same repeated-success rule; its Discussion separately says 15
in-vivo experiments were needed for reproducible cannulation. Keep the 2022
criterion and 2023 goal-attainment rates as distinct measures. This text
difference alone does not show that the 2023 study failed the earlier rule.

The machine-readable companion is the [fetal ovine support and transition
inventory](config/source_inventories/fetal_ovine_support_transition_2023_2026.json).
It keeps each source and cohort separate and remains a candidate pending human
review.

## 2023 complication-table denominator flag

In Table 1 of the [2023 Eixarch et al. paper](https://doi.org/10.3390/biomedicines11030702),
the 4–24-hour group has n=10, but “Bubbles in the circuit” is printed as 1
(14.3%) and “Vasospasm” as 4 (57.1%). Each printed percentage corresponds to a
denominator of 7, while the paper does not identify that subgroup in the table
or its footnote. If the counts are interpreted against the full group of ten,
they would be 10% and 40%; retain the published count/percentage pairs and flag
the basis as unresolved rather than silently replacing the source values.
Complication categories may overlap, so the counts should not be summed as
distinct animals.

A row-by-row check of all four specific-complication rows finds that the 1–3 h
bubble (2 [25%]), decannulation (3 [37.5%]), and vessel-lesion (1 [12.5%])
cells are arithmetically consistent with group n=8. The 4–24 h bubble and
vasospasm cells still imply n=7 (1 [14.3%] and 4 [57.1%]) although the group
header says n=10. Section 2.2.6 and the table footnote define categorical
entries as counts and percentages but do not state row-specific denominators;
the Results discuss these events qualitatively without resolving the mismatch.
All seven table dashes remain uninterpreted rather than being converted to zero.
The specific rows are not assumed to be mutually exclusive or exhaustive of
the separate procedure-complication total. This denominator audit adds no
individual observations.

## 2023 public-data follow-up

To check whether a supplement or data file could explain the two 4–24 h
complication denominators, I inspected the [MDPI-hosted article PDF](https://mdpi-res.com/d_attachment/biomedicines/biomedicines-11-00702/article_deploy/biomedicines-11-00702-with-cover.pdf?version=1680090205),
the [PubMed record](https://pubmed.ncbi.nlm.nih.gov/36979681/), and bounded
exact-title/DOI searches. The PDF's Data Availability Statement says “Not
applicable” and its text has no Supplementary Materials section. PubMed lists
publisher and PMC full-text links, without a data/supplement item on the
inspected record surface. The publisher HTML page could not be retrieved in
this search run, so the result is limited to the accessible PDF, PubMed surface,
and returned search results; it does not rule out a separately hosted,
restricted, private, or unindexed file. No author was contacted. The Table 1
row denominators remain unresolved, and the candidate remains an aggregate
descriptive intake. The checked surfaces and boundaries are recorded in the
[source inventory](config/source_inventories/fetal_ovine_support_transition_2023_2026.json).

The Discussion also says 15 in-vivo experiments were needed, after intensive
ex-vivo team training, to achieve reproducible umbilical-cord cannulation.
Methods reports 28 transfers in three planned-goal groups (8, 10, and 10), but
the paper does not define the reproducibility criterion or map those 15
experiments to the 28 transfers, groups, or technique counts. The number is
retained as an unmapped learning-curve statement; it is not a 15/28 rate or a
success count. Reproducible cannulation does not establish prolonged
physiological stability or developmental health.

## Aggregate percentage/count reconciliation

The [2025 Eixarch et al. abstract](https://doi.org/10.1002/uog.70060)
reports 12 experiments and says 75%, 50%, and 17% reached days 7, 10, and
14. If each threshold uses all 12 experiments as its denominator, those
rounded percentages imply 9, 6, and 2 experiments, respectively (the exact
last fraction is 2/12 = 16.7%). Because these are nested thresholds, the same
assumption implies 3 did not reach day 7, 3 reached day 7 but not day 10, 4
reached day 10 but not day 14, and 2 reached day 14. These are bins of
threshold attainment, not recovered individual stopping times.

The abstract also reports 58% and 25% for two discontinuation causes. If those
also use all 12 experiments, the nearest counts are 7/12 (58.3%) and 3/12
(25%). Their sum of 10/12 is arithmetically consistent with 2/12 reaching day
14, but the abstract does not explicitly give cause-specific denominators,
state that the categories are mutually exclusive/exhaustive, or identify
individual animals. Treat all of these counts as derived checks, not observed
case-level data. With only 12 experiments, the percentages also remain coarse
cohort summaries; this screen does not infer a reliable population success
rate from them.


Cycle 288 audited the two unexplained Table 1 complication percentages against the official full text. In the 4–24 h group (n=10), `1 (14.3%)` for bubbles and `4 (57.1%)` for vasospasm both imply n=7 arithmetically; using the printed group n=10 would yield 10% and 40%. The generic table note defines counts/percentages, while the `#` note applies only to “Complications after 24 h survival.” Methods, Results, and Discussion do not define a seven-fetus risk set for these rows. The printed cells remain unchanged; no individual cases are inferred. See the [Cycle 288 audit](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle288/table1-complication-denominator-audit-cycle288.json).

Cycle 289 searched public DataCite, Zenodo, Figshare, and OSF metadata APIs. No Eixarch 2023 dataset or supplement was identified in the returned results. The Zenodo exact-DOI request returned HTTP 500 and is recorded as unavailable, not as a zero-result search. Figshare DOI/title/author queries returned broad, capped top-ten results; two artificial-placenta topical records were different papers. This bounded screen does not establish global data absence, changed no candidate observations, and involved no author contact. See the [Cycle 289 route summary](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle289/repository-route-summary-cycle289.json), [query crosswalk](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle289/repository-route-crosswalk-cycle289.csv), and [candidate intake](config/observations/eixarch_2023_support_outcomes_candidate.json).\n\nCycle 290 checked PubMed and Crossref publication metadata for a correction, erratum, retraction, or updated-version link. PubMed had no Comments/Corrections entry; exact-DOI and article-title correction searches returned zero; Crossref relation and update-to fields were empty. The MDPI article-notes page returned HTTP 403, so publisher notices remain unchecked. The Table 1 denominator issue is still unresolved and candidate values are unchanged. See the [Cycle 290 route screen](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle290/correction-notice-route-screen-cycle290.json).\n\nCycle 291 visually checked Table 1 in the publisher PDF (printed p. 5). It confirms the middle-group cells 1 (14.3%) for bubbles and 4 (57.1%) for vasospasm; neither has a row-specific footnote marker. The generic note only defines means ± SEM or n (%), while # marks the separate complications-after-24-hours row. This confirms the transcription but does not resolve the denominator; no observations changed. See the [Cycle 291 assessment](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle291/table1-visual-assessment-cycle291.json) and [rendered page](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle291/publisher-page5-table1-render-300dpi.png).\n\nCycle 292 queried Crossref’s reverse updates filter for records pointing to the article DOI; the API returned zero records. Because this is bounded to Crossref-deposited relations, it does not prove that no correction exists. The publisher-notes route remains unavailable, and the Table 1 denominator discrepancy remains unresolved. No observations changed. See the [Cycle 292 audit](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle292/correction-reverse-link-screen-cycle292.json).\n\nCycle 293 reconciled the 60 Table 1 cell positions from the publisher PDF to the candidate and source inventory. There are 51 reported cells, 7 printed dashes, and 2 N/A cells. Forty-two direct table observations match their group coverage declarations; three surgical-complication cells cross-check existing abstract summaries; five specific-complication values remain source-inventory-only because their assessment denominators are unclear; the later complication cell links to the existing Results count. No values changed and no individual animals were assigned. See the [Cycle 293 cell crosswalk](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle293/table1-cell-crosswalk-cycle293.csv) and [reconciliation](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle293/table1-cell-reconciliation-cycle293.json).\n\n## Eixarch et al. 2023 group-summary intake

The primary article abstract reports three consecutive planned survival-goal
groups for fetal sheep transferred to the AP system at 110–115 gestational
days. Table 1 reports mean total time in the AP system, pH and circuit flow at
30 minutes, and whole-experiment pH, lactate, heart rate, and circuit flow.
Section 2.2.6 states that continuous variables are reported as means ± SEM.
These group summaries have been added to the machine-readable candidate intake
alongside the six group-level rates; denominators remain in separate coverage
frames:

Cycle 286 pins the official PMC full-text XML (CC BY 4.0). The PMC Associated
Data section says “Not applicable,” and the pinned XML contains no
supplementary-material node. Figure 3 defines its points as per-animal
whole-experiment means, but gives no exact-value cells or persistent animal
IDs. The inspected article surface exposed no linked longitudinal file; this is
a bounded route result, not a claim that data are unavailable elsewhere. No
observation values changed in this source-pin cycle. Cycle 287 visually inspected publisher Figure 3 at 300 dpi; the dots have no labels and some overlap, so no approximate values were entered.

| Planned group target | Source n | Mean total AP support time (SEM) | pH at 30 min (SEM) | Heart rate at 30 min (bpm; SEM) | Circuit flow at 30 min (mL/kg/min; SEM) | Reached assigned survival goal | Cannulation complications |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1–3 h | 8 | 1.48 (0.78) h | 7.20 (0.06) | 134 (33) | 45 (24) | 25% | 75% |
| 4–24 h | 10 | 11 (3.42) h | 7.31 (0.04) | 205 (8) | 138 (23) | 70% | 50% |
| 48–168 h | 10 | 72.6 (12.9) h | 7.33 (0.02) | 182 (8) | 196 (13) ** | 80% | 0% |

The middle group is labeled 4–24 h in the Abstract, Methods, and Table 1
header, but the Results comparison sentence and Table 1 statistical footnote
refer to 3–24 h. Retain 4–24 h for the group-level records because it is the
cohort label repeated in those three locations; preserve the 3–24 h variants
as a source inconsistency. The text does not resolve whether the footnote's
comparison label is a typo, so its reported significance annotations are not
reinterpreted.

Table 1 also provides whole-experiment group summaries:

| Whole-experiment measure (mean ± SEM) | 1–3 h group (n=8) | 4–24 h group (n=10) | 48–168 h group (n=10) |
| --- | ---: | ---: | ---: |
| pH | 7.22 ± 0.07 | 7.29 ± 0.03 | 7.35 ± 0.01 |
| Lactate (mmol/L) | 6.2 ± 1.22 | 3.82 ± 0.78 | 2.50 ± 0.38 ** |
| Heart rate (bpm) | 222 ± 11 | 186 ± 9 | 177 ± 5 |
| Circuit flow (mL/kg/min) | 124 ± 12 | 115 ± 11 | 161 ± 8 |

Table 1 also reports transition-context measures:

| Transition-context measure (mean ± SEM) | 1–3 h group (n=8) | 4–24 h group (n=10) | 48–168 h group (n=10) |
| --- | ---: | ---: | ---: |
| Duration EXIT surgery (min) | 33.5 ± 3.3 | 44.1 ± 5.1 | 34.3 ± 5.1 |
| Duration of cannulation (min) | 8.04 ± 2.95 | 8.11 ± 0.93 | 6.89 ± 0.40 |
| Heart rate before connection (bpm) | 182 ± 18 | 168 ± 10 | 143 ± 6 |

The same table lists technique counts by group:

| Cannulation technique used (source label) | 1–3 h group (n=8) | 4–24 h group (n=10) | 48–168 h group (n=10) |
| --- | ---: | ---: | ---: |
| Direct cut-down | 6 (75%) | 0 | 0 |
| Sequential technique | 2 (25%) | 5 (50%) | 0 |
| ST + vasospasm prevention | 0 | 5 (50%) | 10 (100%) |

Table 1's separate “Complications surgical procedure” row reports 6 (75%),
5 (50%), and 0 for these same groups. Those cells arithmetically match the
abstract's 75%, 50%, and 0% “cannulation complications” rates using group sizes
8, 10, and 10. The labels differ, so this is recorded as a source-consistency
check rather than proof that the categories were coded identically; it adds no
duplicate outcome records and does not establish category completeness.

The Methods describe the technique changing over successive experiments:
direct cut-down was followed by a sequential approach, then by that approach
with intensive vasospasm prevention. Across those same three groups, the
technique mix and the separate procedure-complication row move together
(6/8, 5/10, and 0/10). This is a group-level co-trend only. The paper does not
cross-tab individual technique assignments with complications or report
randomized technique assignment, and experience/group sequence changes along
with technique; these summaries cannot identify a technique effect or isolate
the contribution of vasospasm prevention.

These are group summaries from a sequential learning-curve study. The table
does not provide the individual durations, and the paper does not report each
fetus's exact assigned goal within the broad ranges; group means do not fill
that gap. The 80% result is not an 80% seven-day survival rate. No per-animal
identifiers or outcomes are inferred. The Results also report that 4/10 lambs
in the 48–168 h group had complications after the first day (two
flow-interrupting cannulation accidents and two sepsis cases), and three had
hydrops at experiment end. Those group counts may overlap; no animal-level
crosswalk is reported. The same four-of-ten complication count appears in
Table 1 as `4 (40%)` under “Complications after 24 h survival #”; its footnote
limits that row to fetuses with >24 h survival. The existing adverse-outcome
record now cites both locations while retaining the Results wording (“after
the first day”) and the table's eligibility wording; this cross-check adds no
duplicate record and identifies no animals. Table 1 also gives group-level pH, heart-rate, and
circuit-flow values at 30 minutes after connection. Its ** marker on long-group circuit
flow is defined as p<0.05 versus the 1–3 h group; the comparison is not
recalculated. Table 1 does not provide measure-specific assessment n or exact
per-fetus 30-minute values. Figure 3's caption defines each plotted point as
one animal's mean over the whole experiment and the black square as the group
mean. The intake keeps only the table's group summaries: it does not reconstruct
trajectories, exact per-animal values, or row-specific assessment counts. The
long-group whole-experiment lactate value is marked ** with the same table
footnote comparison versus the 1–3 h group; that test is not recalculated. The
Results state there were no differences in overall surgical time, cannulation
time, or heart rate before connection, without giving exact test statistics in
that text. These measures are retained as group summaries, not operating
specifications. The
paper reports group comparisons (P=0.045 for goal
attainment and P=0.004 for cannulation complications); those annotations are
not recalculated. Methods state that fetuses were euthanized after reaching
their survival goals. The 25%, 70%, and 80% attainment rates with group n=8,
10, and 10 imply 2, 7, and 8 goal-reaching experiments, respectively; applying
the Methods protocol makes those implied planned-end euthanasia counts at the
group level, although the paper does not separately enumerate euthanasia
dispositions. The complementary 6, 3, and 2 experiments are only counts not
reported to have reached goal, not deaths. Results say a significant number in
the first group died shortly after connection but do not provide a complete
group-by-group disposition breakdown. Animal identities and individual
goal assignments are absent. This intake therefore does not report
post-support neonatal transition or later developmental health. The three
coverage-closure checks remain unassessed. Table 1 does not state that the
three cannulation technique
rows are a mutually exclusive and exhaustive partition, and it supplies no
per-fetus technique assignments; `ST` is retained as printed. See the
[candidate dataset](config/observations/eixarch_2023_support_outcomes_candidate.json),
[machine-readable source inventory](config/source_inventories/fetal_ovine_support_transition_2023_2026.json),
and [receipt-bound v11 output](artifacts/eixarch-2023-group-outcomes-2026-10-10-v11/REPORT.md).
Source: [Eixarch et al. 2023, primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC10044909/).

## Observation question

Do published fetal-lamb support studies link each attempted animal's starting
stage and disposition to repeated support observations, developmental outcomes,
and outcomes after support? Keep gestational age, elapsed support time, species,
biological unit, and outcome time separate. Do not combine maximum run duration
from one experiment with developmental endpoints from another as though they
were one continuous trajectory.

| Source | Study frame and unit coverage | Reported outcomes | Intake limit |
| --- | --- | --- | --- |
| [Eixarch et al. 2022, OC09.01](https://doi.org/10.1002/uog.25056) | Preliminary conference abstract: 18 fetal sheep at 110–115 gestational days; progressive survival goals of 1, 3–6, and 24 hours. | Reports experiment counts used to achieve reproducible survival criteria (9, 6, and 3, respectively); these are learning-curve goal counts, not post-support outcomes. | Same lead author and program as the 2023 full paper, but the goal bands and totals differ. No animal identifiers or public crosswalk establish whether the cohorts overlap; do not add n=18 to n=28 or count this as independent replication. |
| [Eixarch et al. 2023](https://doi.org/10.3390/biomedicines11030702) | Twenty-eight fetal sheep at 110–115 dGA entered the AP system across three sequential groups (n=8, 10, 10) with survival-goal windows of 1–3 h, 4–24 h, and 48–168 h. | Reported goal attainment of 25%, 70%, and 80% maps to 2/8, 7/10, and 8/10. In the 48–168 h group, mean total support was 72.6 ± 12.9 h (SEM); 4/10 had complications after 24 h (two flow-interrupting cannulation accidents, two sepsis), and hydrops was seen in 3/10 at experiment end. Animals were euthanized after the goal. | The 80% is not an 80% seven-day rate: per-animal goal assignment within the 48–168 h band is not reported. The title's “successful transition” refers to entry into AP support, not transition to neonatal life. No post-support developmental follow-up was assessed. |
| [BCNatal Annual Report 2023](https://bcnatalresearch.org/wp-content/uploads/2024/12/CAT-Memoria-anual-2023-_compressed.pdf) | An institutional annual report says the experimental ovine system reached a 14-day survival milestone in 2023 and metabolic/hormonal characterization had begun. | Aggregate project milestone; no denominator, per-animal outcomes, or measurement values are provided. | The report does not link this milestone to the 2025 abstract's 12 experiments or later cases; overlap with the 2023–24 abstract cohort is unresolved. |
| [Eixarch et al. 2025 conference abstract](https://doi.org/10.1002/uog.70060) | Twelve fetaLife experiments conducted in 2023–24, with fetal lambs at 110–125 dGA and planned support goals of 7–14 days. | The abstract reports mean survival of 9.5 ± 3.3 days; 75%, 50%, and 17% reached days 7, 10, and 14. It summarizes time-binned flow, heart rate, pH, and lactate; listed discontinuation causes are hemodynamic deterioration/low flow (58%) and acute circuit/cannula events (25%). | This is a conference abstract, not a full cohort paper. Values are aggregate summaries without a published per-animal disposition table or longitudinal dataset. Its stated planned maximum is 14 days, so it does not document the later 21-day announcement. No post-support follow-up is reported here. |
| [Partridge et al. 2017](https://www.nature.com/articles/ncomms15112) | The later Biobag cohort included eight ovine fetuses in two gestational-age groups: 105–108 dGA supported 25–28 days and 115–120 dGA supported 20–28 days. A separate earlier semi-closed CA/JV cohort included five fetuses. | The Biobag cohort reports hemodynamic and blood-gas observations, growth, lung maturation, and brain growth/myelination; one Biobag animal was ventilator-free for 10 h. In the separate semi-closed cohort, one lamb was supported 288 h and extubated. The same article's Table 1 reports a normal brain MRI at 1 year, while its Results text and Fig. 7d report postnatal T1/T2/diffusion MRI at 6 months with no ischaemia or structural defect. A one-record candidate intake preserves this as one disputed timepoint with no numeric measurement time: [`config/observations/partridge_2017_mri_time_conflict_candidate.json`](config/observations/partridge_2017_mri_time_conflict_candidate.json). | The MRI follow-up time conflicts within the primary article; its [corrigendum](https://doi.org/10.1038/ncomms15794) only adds an omitted patent disclosure and does not resolve the conflict. Preserve both times. This is one survival/transition case with limited brain imaging, not a comprehensive developmental assessment. No early-embryo or human result is reported. |
| [Church et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6151273/) | Five preterm lambs received about 10 days of artificial-placenta support before transition to mechanical ventilation; the five-row transition cohort is a subset of a larger project group (n=12), with a possible seven-day hemodynamic-stability selection rule noted but not mapped case by case. | Table 1 now has a source-hashed, 35-record transcription of all five lambs: AP/AP+MV/MV-alone durations, airway labels, Day 9 ductus status, complications, and row outcomes. The 26-hour MV-alone value and mucus-plugging/acute-respiratory-failure outcome remain separately recorded for AP Lamb 3 with no exact event time. | The paper prints AP+MV duration as 37±36 h, which matches the first four table values (mean 37, sample SD 36.25); all five values average 52.6 h. The statistic-specific denominator and excluded row are unstated, so all five rows are retained. Outcomes are not exact-time events; terminal assessment is not long-term follow-up. Candidate transcription and arithmetic receipt: [`config/observations/church_2018_lamb3_transition_candidate.json`](config/observations/church_2018_lamb3_transition_candidate.json) and [`duration check`](artifacts/fetal-ovine-transition-2026-10-11-cycle285/duration-aggregation-check-cycle285.json). |
| [Usuda et al. 2023](https://doi.org/10.3389/fphys.2023.1219185) | Six APT fetuses began at 93–94 dGA. The abstract states six age-matched in-utero controls, while Methods, Table 1, and Tables 3 and 6 report eight; the Results text reports four female, three male, and one control with sex unrecorded. All six APT fetuses were adapted. Mean survival was 250 ± 72 h, maximum 336 h; one reached the planned 336 h. Three were euthanized after bladder bleeding and two for umbilical-artery vasoconstriction. | Serial physiology and activity/urine observations; terminal body/organ measures. The APT group had reduced organ weights and humerus length and lower albumin, IGF-1, and phosphorus; edema affected body-weight interpretation. | A short, small ovine experiment with adverse dispositions and reduced growth despite maintained circulation. The article says controls were paired by gestational day but gives no individual-ID crosswalk or explanation reconciling six abstract controls with eight main-text/table controls. A candidate transcription preserves selected A-F weights, duration, source-coded bleeding/edema, and case-narrative disposition summaries; it is not the raw time series and has no per-case terminal growth outcomes. The two group-level umbilical-artery-vasoconstriction causes are not explicitly mapped to case IDs. The data statement says raw data will be made available by the authors. No supplementary-data link was identified in the inspected publisher HTML or pinned JATS full text, and this screen found no public raw-data repository. No contact was made. |
| [Peers de Nieuwburgh et al. 2024](https://doi.org/10.1038/s41390-024-03287-0) | The analyzed extremely-preterm EXTEND cohort is reported as 10 lambs beginning at 90–95 dGA. The planned study window was 10–14 days; mean support was 13.5 days (range 10–21), with one animal extended to 21 days for a thrombogenicity study after it met its 14-day endpoint. The Results explicitly link the four early-death intervals to causes: 3 days—iatrogenic fluid overload; 6 days—sudden cardiac arrest, with air embolism only suspected; and 7 and 8 days—sudden irreversible venous spasm. The Results describe cord movement as a likely trigger for the venous spasms, not a confirmed mechanism. These four event narratives have no persistent animal IDs linking them to the 10 numbered analyzed animals in Table 2. Table 2 supplies 17 per-animal fields for the ten analyzed lambs, including sex, cannula sizes, cannulation/necropsy ages and weights, run length, growth rate, brain/organ weights and ratios, and transfusion count; six of ten required at least one transfusion. This count describes care exposure, not injury or safety. Its Animal 5 row reports a 16-day run, although the Results say nine animals ended protocol at 10–14 days except Animal 2's 21-day extension; age subtraction and the group mean support the Table 2 cell, but the text discrepancy remains unresolved. After day 15, the plotted extremely-preterm group size was below three. | Brain MRI and histology were each reported for six of 10 analyzed animals: three brains were excluded after unsuccessful perfusion/fixation, and the 21-day animal was excluded from brain analysis because its brain was more mature than the target group. Table 2 reports terminal brain mass per animal (blank for Animal 3), not individual MRI or histology results; the identities of the six analyzed brains and three technical exclusions are not fully mapped. The cohort ended in euthanasia for endpoint analysis and has no post-support follow-up. A 170-record candidate intake transcribes all 17 Table 2 fields, retains footnote-qualified values, and preserves the Animal 5 duration discrepancy: [`config/observations/peers_2024_extend_table2_candidate.json`](config/observations/peers_2024_extend_table2_candidate.json). | Raw data are not publicly available because of an ongoing FDA submission; the statement offers access from the corresponding author on reasonable request. The PMC page lists one supplementary-figures PDF, `41390_2024_3287_MOESM1_ESM.pdf` (82.7 MB), described as “Supplemental figures_small animal-R3 paper”; it lists no separate raw-data file or workbook. The PDF itself was not inspected, so this metadata screen does not establish whether its plots contain animal-specific traces or transcribable values. No contact was made. |
| [Eixarch et al., ISUOG EP09.22 (2026 poster)](https://epostersonline.com/isuog2026/poster/543) ([poster PDF](https://epostersonline-2.s3.eu-west-1.amazonaws.com/isuog2026/isuog2026.21f04bd.NORMAL.pdf?v=1)) | Reports four lambs transitioned after fetal liquid-incubator support, with an animal-level table of gestational age, support duration, extubation, and post-transition survival. The summary gives mean support 9.6 ± 3.1 days. | Two animals were not successfully extubated; one died at 2 days and one was euthanized at 7 days; a third was extubated at 24 h and died at 5 days. The fourth was extubated on day 6, survived 13 months, and had a maze test at 3 months reported comparable to age-matched controls. A 12-record candidate observation intake is available in [`config/observations/eixarch_2026_neonatal_transition_candidate.json`](config/observations/eixarch_2026_neonatal_transition_candidate.json); it separates endpoints and uses only explicitly reported times. | Public conference poster, not a peer-reviewed cohort paper; four is the transition subset, not the number entering FLI. The poster conclusion says all had satisfactory respiratory parameters, while the table lists absent respiratory drive/no extubation for Animal 1 and no extubation for Animal 2. Text extraction shows 24 support days for Animal 2, which would make the four table durations average 12 days and conflicts with that row's 125-to-139 dGA interval; 14 is a plausible but unverified transcription hypothesis. The poster image could not be visually verified in the browser review, so the candidate is not analysis-ready. No case is identified as Gaia or linked to the separate 21-day milestone. |
| [Illa et al., ISUOG EP09.31 (2026 poster)](https://epostersonline.com/isuog2026/poster/535) ([poster PDF](https://epostersonline-2.s3.eu-west-1.amazonaws.com/isuog2026/isuog2026.217077e.NORMAL.pdf?v=1)) | The study-model graphic lists 29 lambs supported for at least 6 days: 5 below 115 gestational days and 24 at or above 115. Biochemistry is compared at baseline and days 6–7. | The poster plots increased total/conjugated bilirubin and blood urea nitrogen, decreased albumin, and no statistically significant AST/ALT change. It reports a growth-velocity comparison by gestational-age group (p = 0.186) and concludes gestational age, rather than parenteral nutrition, was the main determinant of cholestasis and fetal growth. | Public conference poster, not peer-reviewed or a raw-data release. The panel-specific denominators and per-animal series are not reported; the ≥6-day frame excludes failed/shorter attempts. It reports no post-support outcomes and supplies no animal IDs linking it to EP09.22 or the other fetaLife cohorts. |

### Bounded correction screen for the Animal 5 duration

A DOI-matched PubMed record and bounded exact-title/DOI searches across PubMed
and Nature-indexed results surfaced the original Peers et al. paper but no
correction notice addressing Animal 5's 16-day Table 2 value. The direct Nature
page redirected to cookie authorization during this screen. This limited search
does not establish that no correction exists; the two primary-article
statements remain unreconciled and the 16-day source value is unchanged. Search
scope and result are recorded in the structured source inventory. No author was
contacted.

### Peers de Nieuwburgh 2024 Table 2 reconstruction

The 170-record candidate intake preserves all 17 Table 2 fields for the ten
numbered analyzed animals. Fourteen numerical group summaries are reconstructed:
13 means are within source precision and 12 SEMs reproduce. The age-at-
cannulation and cannulation-weight SEMs remain unreproduced from rounded cells;
the brain-to-liver mean differs from the rounded rows after the printed Lamb 5
outlier exclusion. A separate growth-rate conflict is visible: all ten displayed
animal values reproduce 40.3 ± 5.4, although a table footnote says Lamb 1 was
excluded; excluding it yields 36.947 ± 4.719. Preserve both the row values and
footnote without correction. Six of ten animals had at least one transfusion
(mean 1, SEM 0.39); this is care exposure, not an injury measure. Terminal
weights and ratios do not establish organ function or post-support health. The
exact arithmetic and qualifications are in the
[summary reconstruction](config/source_inventories/peers_2024_table2_summary_reconstruction.csv).

### Peers et al. comparator cohort coverage

Table 1 separates the ten extremely preterm EXTEND animals from five extremely
preterm in-utero controls, ten historic late-gestation EXTEND animals, four
late-gestation controls, and a three-animal growth-restricted EXTEND pilot.
Brain MRI/histology counts are 0/0, 0/0, 3/3, and 0/0 for those four groups,
respectively. Table 2 provides only group-level comparator means ± SEM for the
control and historic EXTEND groups; row-specific denominators and numbered
animal identities are not given. The IUGR pilot has individual Table 2 rows,
but the authors say it was included for interest, not detailed analysis, and
excluded from statistical comparisons. A separate
[30-record IUGR pilot candidate](config/observations/peers_2024_iugr_table2_pilot_candidate.json)
transcribes ten available fields for its three labeled animals; seven numeric
means and SEMs recompute from those rows. These cohort frames remain separate
from the ten-animal candidate observations.

### Usuda case-level outcome linkage

Cycle 346 adds a separate [terminal group candidate](config/observations/usuda_2023_terminal_group_candidate.json)
from the pinned Europe PMC JATS source. It preserves all nine terminal numeric
Table 1 endpoints and all 21 Table 3 rows: 59 numeric group summaries and one
explicitly missing control cell. Mean/SD and median/IQR remain distinct;
the table/main-text count of eight controls is retained with the abstract's
six-control discrepancy. No group row is joined to Cases A–F, and no new
animals or transitions are implied by the added records.

Arithmetic on the published means gives APT/control ratios of 0.976 for
terminal body mass, 0.810 for lung mass, 0.704 for liver mass and 0.736 for
kidney mass; brain mass is 1.028. These are descriptive ratios of group means,
without age adjustment, individual pairing or a new uncertainty interval.
Different necropsy ages, edema and the unresolved control map limit the
comparison. It strengthens the requirement for independent organ/bone and
fluid-state observations alongside circulation/body weight. It does not
establish a causal nutritional/endocrine explanation or an intervention.
Exact source bone units and p/CI strings remain unchanged. See the
[reproducible audit](artifacts/usuda-terminal-development-cycle346/source-audit/REPORT.md).

The six APT cases share labels A–F across Tables 4 and 5, permitting a limited
within-study link between per-case survival/case summaries/body-weight rows and
experiment-average infusion/urine summaries. Table 4's bleeding and edema
cells are preserved as source-coded per-case text; embedded time marks remain
unparsed because their event-time meaning is not independently defined. The terminal comparisons are not
reported at that same case level: Table 1 gives group summaries for necropsy
body and organ measures and bone-length gains, Table 3 gives group summaries
for terminal hematology and biochemistry, and Table 6 gives a group cardiac
ultrasound comparison. The study reports no post-support follow-up. Thus its
case labels do not support joining each animal's support history to its later
growth, organ, or biochemical outcome, and the paper does not establish a
same-animal support-to-development association.

The Results also describe events for Cases A–F. Cases B, D, and E are directly
described with gross hematuria/bladder injury, and Case F's 336-hour Table 4
duration matches the single animal reported to reach the planned endpoint. The
paper reports two umbilical-artery-vasoconstriction euthanasia causes at group
level but does not identify those case labels. A/C are the residual labels if
the three bladder cases and Case F are subtracted from the six-case cohort;
that count-based mapping remains conditional and is not encoded as direct
case identity.

In the case-table candidate, the developmental interval denotes the whole
case-specific support episode, while `measurement_time` denotes the row's point
within it: induction weight is at time zero and conclusion weight is at the
reported case duration. The episode end is not copied into the baseline
measurement time.

As a transcription check, the A–F Table 4 values reproduce Table 1's APT
group mean ± SD after rounding: induction body weight 656 ± 42 g, conclusion
body weight 1323 ± 116 g, and survival duration 250 ± 72 h (sample SD, n−1).
This is a source-table consistency check only; it does not calculate per-case
growth changes or an association.

### Primate embryo-culture endpoint and denominator

The [Gong et al. 2023 primary paper](https://doi.org/10.1016/j.cell.2023.04.020)
reports intact cynomolgus embryos cultured from blastocyst through early
organogenesis at 25 days post-fertilization. Its Figure 1D defines the
stage-specific developmental rate as `(a-b-c-d)/(a-b)`, where `a` is the total
embryo count, `b` the number recovered at the preceding stage for examination,
`c` the number with abnormal morphology, and `d` the number dead. An
author-group [2024 protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC10826423/)
summarizes 226 embryos and 48.15% survival / 20.61% visible-structure
development at day 25. Do not turn 20.61% × 226 into an animal count: the
primary figure uses a stage-specific denominator, and its text does not supply
the per-stage numerator/denominator series. The primary article also reports
that the visible structures collapsed after another 1–2 days of culture. This
is a substantial early-development result, but not a stable handoff to fetal
support or a birth outcome.

The separate [Zhai et al. 2023 pIVC paper](https://doi.org/10.1016/j.cell.2023.04.019)
starts with cynomolgus blastocysts at d.p.f. 7 and follows culture through
d.p.f. 25. The primary article states 33.7% survival through d.p.f. 20 in
`n=91`; its Methods define survival morphologically and use Kaplan-Meier
analysis, censoring embryos removed for sequencing or immunofluorescence. The
paper also says all 10 embryos remaining in culture at d.p.f. 20 continued
growing through d.p.f. 25. An [Institute of Zoology release](https://ioz.cas.cn/gb2018/xwdt/kyjz/202305/t20230512_6752304.html)
instead attaches 33.7% to development at d.p.f. 25. Retain this unresolved
stage-wording discrepancy rather than relabel the primary paper's 33.7% as a
day-25 survival rate. The paper reports selected d.p.f. 22–25 neural-crest,
neural-tube, and neural-progenitor findings; its illustrated d.p.f. 25
sectioned embryos are `n=2`, not a cohort-wide healthy-development endpoint.
The article also says that 31 embryos were removed for structural or molecular
analysis beginning at d.p.f. 16; 19/31 (61%) showed embryonic-disc development
by immunofluorescence or single-cell multi-omics. Those removals are censored
in the survival analysis, so 19/31 is a selected-analysis result rather than a
survival numerator. The article says all 10 embryos still in culture at
d.p.f. 20 continued growing through d.p.f. 25; this conditional 10/10 is not
the denominator of the original 91-embryo cohort.
The paper points to Table S3 for survival-curve details and defines the
Kaplan-Meier risk set, apoptotic events, and analysis-removal censoring in its
Methods. This intake did not inspect a stage-by-stage Table S3 event/censor
ledger; a bounded search did not locate a separately accessible copy. That
search result does not establish that the published supplement is unavailable.
Until the table is inspected, keep exact risk sets, raw event counts, and
individual embryo histories unreported; they cannot be reconstructed from
the 33.7% estimate or the conditional 10/10 observation.
The public [GSE218525 GEO SuperSeries](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE218525)
contains an RNA subseries (GSE218523) and a bisulfite-sequencing subseries
(GSE218524). The processed RNA cell metadata has nine stage labels
(`E16-1`, `E16-2`, `E18-1`, `E20-1`, `E21-1`, `E22-1`, `E23-1`, `E24-1`,
`E25-1`) across eight stages. These are analysis-stage embryo labels, not
starting-cohort IDs; the reviewed metadata does not join them to the 91-embryo
survival risk set, censor times, or apoptotic events. The main text reports
3,850 RNA datasets after filtering, while the GEO series summary and processed
metadata expose 3,682 cell records; that count difference remains unresolved.
Do not treat GEO sample or cell-record counts as independent embryo counts.
The processed RNA metadata has nine embryo labels across eight GEO stages:
two labels at `E16` and one each at `E18`, `E20`, `E21`, `E22`, `E23`, `E24`,
and `E25`. Thus seven stage groups have only one embryo-level label. The
hundreds of cell rows within those groups are nested measurements, not
independent embryo replicates; they support exploratory cell-state description,
not estimates of how often a developmental outcome occurs across embryos. The
machine-readable inventory preserves the cell-row count per embryo label so
this hierarchy remains visible.
The authors identify the largest survival drop as occurring before gastrulation,
at d.p.f. 9–13, and hypothesize that better modeling of attachment/implantation
and maternal crosstalk could improve culture efficiency. They also state that
the present pIVC platform lacks motion and suggest shear may matter for stages
such as cardiogenesis or limb formation. These are author hypotheses and future
directions, not demonstrated interventions; exact day-specific loss counts
remain unavailable in this intake. The next useful evidence target is complete,
stage-resolved accounting through that early loss window, including every
starting embryo, event, analysis removal, and developmental observation.
The Gong and Zhai percentages are not directly comparable: they use distinct
culture platforms, start days, outcome definitions, and denominator rules.
Neither study reports fetal support, birth, or postnatal health.

### Measurement granularity in the 2023 learning-curve paper

The [2023 paper](https://doi.org/10.3390/biomedicines11030702) is not purely
aggregate: Figure 3 plots one whole-experiment mean per animal for pH, lactate,
circuit flow, and fetal heart rate; its caption defines each point as an
animal-level mean. Figure 2 gives longitudinal traces for one representative
animal per group. The paper's data-availability statement is “not applicable,”
and no persistent animal identifiers, exact point-value table, or raw
time-series files are linked. Treat Figure 3 as visually available
animal-summary evidence, not a recoverable longitudinal dataset that can be
joined to each animal's survival goal or complications.

## Developmental-stage coverage boundary

The systems mapped here cover separate biological windows, not one continuous
embryo-to-birth trajectory. An intact mouse-embryo ex-utero culture study
reports development from E5.5 to E11; a March 2026 preprint extends mouse
ex-utero culture from gastrulation to approximately E12.5. An intact
cynomolgus-monkey embryo culture study reaches 25 days post-fertilization and
early organogenesis. Separate cell-derived mouse and primate embryo models
reconstruct selected early stages, but they remain models and do not report a
healthy live birth. In contrast, artificial-placenta studies begin with already
developed fetal lambs (90–125 ovine gestational days across the mapped
programs), and test support for hours to weeks. These stage labels are
species-specific and must not be converted into human gestational ages.

| Evidence class | Source-reported stage window | What was shown | What remains unshown |
| --- | --- | --- | --- |
| [Intact mouse embryos, ex-utero culture](https://www.nature.com/articles/s41586-021-03416-3) | E5.5–E11 in the 2021 study; a [2026 preprint](https://doi.org/10.64898/2026.03.17.710314) reports gastrulation at E6.5/E7.5 through ~E12.5 | Development through late organogenesis in the first study; fetal-period metabolic/transcriptomic characterization in the preprint | Continuation through term, live birth, or postnatal health |
| [Intact cynomolgus monkey embryos, ex-utero culture](https://doi.org/10.1016/j.cell.2023.04.020) | Blastocyst to 25 days post-fertilization | Early organogenesis and molecular/cellular developmental observations | Fetal continuation, birth, or postnatal health |
| [Intact cynomolgus monkey embryos, 3D pIVC](https://doi.org/10.1016/j.cell.2023.04.019) | Blastocyst/day 7 to day 25 post-fertilization | 33.7% survival through day 20 in the primary article (n=91); 31 selected removals from day 16 onward yielded 19/31 embryonic-disc observations; all 10 embryos still cultured at day 20 grew through day 25; day-25 sectioned examples n=2 | Censored removals and the conditional 10/10 cannot be treated as full-cohort survivor counts. An institutional release places 33.7% at day 25, contrary to the primary article's day-20 wording; preserve as unresolved. No fetal continuation, birth, or postnatal health |
| Cell-derived embryo/embryoid models ([mouse](https://www.nature.com/articles/s41556-025-01793-9); [cynomolgus](https://doi.org/10.1016/j.cell.2026.05.023)) | Mouse model approximately E1.5–E7.5; cynomolgus model from totipotent-like cells through early organogenesis | Selected stage transitions and lineage programs; the primate model reports cardiac-like beating | Normal organism development, a linked fetal-support handoff, or offspring |
| Fetal-lamb artificial-placenta cohorts | 90–125 ovine gestational days at entry across separate programs | Fetal physiological support for hours to weeks; some cohorts report neonatal transition or later outcomes | A same-animal bridge from embryo-stage culture into fetal support and a complete healthy human outcome |

This comparison is an evidence boundary, not a claim that a future staged
system is impossible. Its feasibility test must identify the handoff between
stages and preserve the same biological-unit lineage, endpoint coverage, and
disposition across each handoff. The machine-readable companion records the
source-level windows and their limits.

## What the record supports

Together these reports establish that extracorporeal support can maintain
selected physiological functions in already-developed preterm fetal lambs for
days to weeks. Some cohorts also demonstrate transition to ventilation or
spontaneous respiration. The 2017 paper and the Gaia announcement describe
limited post-support outcomes. The 2017 paper's table and Results text conflict
on one lamb's MRI timing (one year versus six months). Newer company and
fundraising claims pair 21-day support with >16- or 18-month outcomes but do not
identify the animal. A separate 2026 conference poster supplies a four-animal
transition table: three animals died or were euthanized within seven days, and
one survived 13 months with a maze assessment at three months. The poster's
extracted support-duration table conflicts with its reported mean for one row
and needs source-image verification. These sources also expose distinct failure
modes and developmental concerns: early termination, bleeding, vascular-flow
disruption, edema, reduced organ/somatic growth, blood-loss burden, and a
separate metabolic poster's bilirubin/BUN increases and albumin decrease during
support, alongside small late-timepoint samples and sparse follow-up. The 2017 Biobag developmental
cohort, its separate earlier transition case, the 2023 growth observations,
the 2024 brain cohort, the 2023–24 fetaLife conference-abstract cohort, and the
later 2026 fetaLife transition poster, 21-day milestone, Gaia, and unlinked
company/fundraising claims must
remain distinct; their
endpoints cannot be assembled into one long-term healthy trajectory. The 2025
abstract's planned maximum was 14 days; the hospital's later 21-day maximum
and company claims of >16/18-month follow-up are not linked to that cohort or to
Gaia's separately reported 10-day support case. The source relationship among
the company claims, the 21-day animal, and Gaia remains unresolved.

Together these disconnected sources do not establish a same-unit path from
fertilization or early embryonic development through fetal support and birth,
continuous human development, or healthy human outcomes.
The 2026 poster narrows the animal feasibility question by linking four
anonymous transition cases to postnatal disposition, including one 13-month
survivor. It does not establish a reproducible same-stage cohort with complete
support-to-postnatal outcome coverage: three cases ended within seven days,
there is no denominator of all FLI attempts, and the long-term survivor has one
reported maze assessment. Ovine gestational days and human gestational ages
remain distinct model-specific coordinates.

## How far this evidence gets toward the original goal

| Developmental segment | Evidence state in this inventory | Remaining evidence gap |
| --- | --- | --- |
| Preimplantation embryo through implantation and early organogenesis | Separate mouse and primate embryo-culture or cell-derived model studies address parts of this interval, but they are not connected to the ovine fetal-support cohorts. | No evidence here shows a same-unit embryo-to-fetal-support handoff or continuation through birth. |
| Partial fetal support | Demonstrated in selected sheep cohorts, with study-specific runs from hours to weeks; separate 2026 posters report post-support transitions and metabolic changes during support. These are not one continuous trajectory. | Reproducible cohort performance, full disposition accounting, and normal growth/organ development remain unresolved; a conference poster reports cholestatic-marker and albumin changes, with no per-animal data. |
| Exit from support to neonatal life | Sheep cohorts demonstrate transition to ventilation or later spontaneous respiration. A 2026 poster reports four fetal-liquid-incubator-to-neonatal transitions and one 13-month survivor with a maze test at three months. | The four transitions are not a denominator of all FLI attempts; three cases ended within seven days, and a single test in one survivor does not establish cohort-level long-term health. |
| Sustained healthy development across a cohort | Not established. Growth deficits, adverse dispositions, small late-timepoint groups, and sparse single-animal follow-up remain in the record. | Defined multi-domain outcomes, complete denominators, and independent cohort replication are needed before making a cohort-level health claim. |
| Human application | The hospital targets 2028–2029 subject to investment; the fundraising page targets 2029 and says AEMPS engagement has begun. An Oct. 10 CEO interview reported a proposed ~€8M round (with ~€2M expected from EU aid), two years of integration tests, a late-2028/early-2029 first-human target, and possible EMA validation in early 2027. These are company/press-reported plans, not confirmed funding or agency action. | No human result or linked authorization is in this evidence set. The interview's pig-to-human and no-long-term-neurological-damage claim has no linked study or dataset; a preterm-fetal study would not test embryo-to-birth development. |
| Complete embryo-to-birth development in humans | Not demonstrated by this inventory. | This is a distinct, much broader objective than extracorporeal support after preterm delivery. |

This ladder prevents a result at one segment from being treated as evidence
for the next. The machine-readable source inventory keeps these claims and
their limits linked to their source records.

## Type every “transition” event

The same word can refer to different edges. Retain separate, unit-linked events:

| Event type | Boundary represented | Example in this screen |
| --- | --- | --- |
| `entry_to_support` | Transfer from the uterus into an extracorporeal support system | Eixarch et al. describe “successful transition” into AP support, then count whether the planned in-system survival goal was reached. |
| `exit_to_neonatal_support` | Removal from fetal support into neonatal ventilation or other postnatal support | Church et al. transition AP-supported lambs to mechanical ventilation; this does not itself mean ventilator independence. |
| `off_extracorporeal_support` | Discontinuation of the extracorporeal circuit, with any remaining respiratory support recorded separately | Four Church et al. lambs were fully weaned from ECLS but still received mechanical ventilation. |
| `spontaneous_respiration` | Breathing without ventilator or extracorporeal respiratory support, for a defined interval | The 2017 paper reports 10 ventilator-free hours for one Biobag lamb and extubation in a separate semi-closed-system lamb. |
| `post_support_follow_up` | Survival and prespecified function after exit, with an ascertainment time | The 2017 paper follows one semi-closed-system case to MRI, but its Table 1 says one year while the Results text/Fig. 7d say six months. Gaia is reported by the hospital/coordinator as surviving beyond a year and neurologically normal at 15 months, with no instrument specified. EP09.22 reports 13-month survival and one maze result at three months for a poster-anonymized case; no source links it to Gaia. Later company claims of >16/18 months remain unlinked. |

“Reached the planned in-system duration,” “survived delivery,” “off the
extracorporeal circuit,” “breathing spontaneously,” and “healthy at follow-up”
must remain separate fields. A preterm animal transferred from a pregnant ewe
into fetal support has not completed gestation; its eventual postnatal survival
does not establish embryo-to-term development.

## Public data-availability screen

On 2026-10-10, exact-name searches of the public DataCite, Zenodo, Figshare,
and OSF APIs for `fetaLife` returned no matching records. Searches for the
conference-abstract title and data/repository terms surfaced the published
abstract and institutional announcement, but no machine-readable full cohort
dataset. Two separately indexed [2026 ISUOG posters](https://epostersonline.com/isuog2026/poster/543)
provide a four-animal transition table with one 13-month follow-up case and
group-level metabolic/growth results from a 29-lamb study frame. The transition
poster has a visually confirmed but unresolved table/summary discrepancy: Animal
2's printed 24-day support cell differs from its 14-day gestational-age
increment, and Animal 4's 7-day support cell differs from its 10-day increment.
The metabolic poster has no per-animal series or panel-specific denominator.
These are conference posters, not a downloadable full-cohort dataset.
The official [ISUOG abstract PDF](https://fetalmedicine.org/abstracts/2025/var/pdf/abstracts/2025/07408.pdf)
confirms that the public 2023–24 report is an aggregate abstract with 7–14 day
goals. The [2026 hospital announcement](https://www.sjdhospitalbarcelona.org/en/news/bcnatals-fetalife-project-most-critically-premature-babies-achieves-21-days-survival-sheep-model-liquid-incubator)
reports a 21-day maximum and Gaia's follow-up but does not link a cohort
dataset. A [later company post](https://es.linkedin.com/posts/fetalife-technologies_hace-siete-a%C3%B1os-nos-planteamos-algo-que-entonces-activity-7503037372343828480-jweo)
and the [current fundraising page](https://capitalcell.com/en/campaign/fetalife/)
pair 21 days with >16 and 18 months of normal neurological development,
respectively, without identifying the animal. Their linkage to Gaia or to the
21-day animal remains unresolved. The hospital's [2024 donation-funded projects
report](https://www.sjdhospitalbarcelona.org/sites/default/files/content/file/2025/10/27/10/memoria-solidaria-2024-cast.pdf)
says the group continued the liquid-incubator project during 2024 but gives no
animal count, support duration, or outcome data in that section; it is retained
as program-status context only. The exact API queries and endpoints are preserved in the JSON
inventory. This bounded screen can miss private, embargoed, non-indexed,
differently titled, or not-yet-published records; no authors were contacted.

## Human-study status

A 2026-10-10 title-field search of the [ClinicalTrials.gov API](https://clinicaltrials.gov/api/v2/studies?query.titles=%22artificial%20placenta%22&pageSize=100)
returned no exact matches for “artificial placenta,” “extrauterine fetal
support,” or “fetaLife.” The [hospital's July 2026 update](https://www.sjdhospitalbarcelona.org/en/news/bcnatals-fetalife-project-most-critically-premature-babies-achieves-21-days-survival-sheep-model-liquid-incubator)
describes technology adaptation and ethical/legal preparations before a first
human study targeted for 2028–2029 if funding is available. The [current
company fundraising page](https://capitalcell.com/en/campaign/fetalife/) targets
2029 and says AEMPS engagement has begun. That is a company statement, not a
published authorization or proof that a trial is active. A [same-day business
press interview with fetaLife's CEO](https://www.elnacional.cat/oneconomia/es/empresas/fetalife-incubadora-liquida-eleva-supervivencia-prematuros-extremos_1707973_102.html)
reports a planned ~€8M funding round, with about €2M expected from European
aid, system-integration testing over the next two years, and first human studies
by late 2028 or early 2029. It also reports a possible EMA validation target
for early 2027; this is a company-reported expectation, not an EMA statement or
authorization. The CEO's further claim that pig testing establishes human
transferability and absence of long-term neurological damage has no linked
porcine report or dataset in that article. A 2023 [BCNatal/La Caixa project
announcement](https://www.clinicbarcelona.org/en/news/the-artificial-placenta-project-achieves-foetal-survival-of-12-days-in-good-health)
had described pig or another large-animal testing as a planned
2023–2026 phase-two milestone for cross-species transferability and longer-term
organ outcomes; it reported a plan, not those results. Public porcine artificial-
placenta studies do exist from other groups: [Toronto/SickKids reports from
2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7923578/) and
[2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9356302/) describe support
measured in hours and heart failure within days. A [2024 echocardiography
paper](https://doi.org/10.1002/pd.6612) reports signs of hydrops in all 13
piglets, with the same 46.4-hour support summary and a study period of
September 2020–July 2021; treat it as related characterization, not a clear
independent replication. A separate [2023 University of Memphis
report](https://pmc.ncbi.nlm.nih.gov/articles/PMC10224797/)
describes one seven-hour run and one early death. These publications establish that pig models have been
tested, but they are not linked to the fetaLife/BCNatal project and do not
verify its claimed long-term neurological outcome or human transferability.
The company's project-specific pig protocol, results, and follow-up remain
unlocated in this bounded public search; unpublished or differently indexed
work could exist. The sources screened here place human translation in a
future-study planning phase. The registry
search is not a global trial search or a regulatory authorization check, and it
does not change the evidence boundary: reported
work concerns extracorporeal support of already-developed preterm animals, not
embryo-to-birth development.

## Evidence-promotion gates

The next public evidence should close these gaps before the associated claims
are promoted:

For this intake, “healthy output” is a claim boundary, not a clinical diagnostic
standard. Promotion requires all-attempt denominators and same-unit linkage
through support exit; predefined, age-appropriate outcome domains at more than
one post-support timepoint; per-unit results, comparator context, test/scoring
methods, adverse outcomes, and missingness; and independent cohort replication.
A single survival statement, MRI, maze result, or unmeasured “normal” claim is
evidence for only that reported endpoint. Passing an animal-evidence gate would
still not establish a healthy human result.

| Gate | Current status | Public evidence needed |
| --- | --- | --- |
| Attempted cohort and disposition | Incomplete: the 2025 abstract has 12 experiments but no per-animal table; the 2026 poster gives four transitioned animals but no number entering FLI; the 21-day and public follow-up claims have no denominator. | Report every attempted run, with inclusion/exclusion, stopping time, disposition, and reason linked to the same animal. |
| Same-animal support-to-follow-up | Partially improved: the poster visually links four poster-local rows to support duration and post-transition outcomes, including one 13-month survivor. Printed durations [9, 24, 8, 7] differ from the 9.6 ± 3.1-day summary; gestational-age increments differ from FLI duration for Animals 2 and 4, and the poster does not define the clock relationship. These four are a selected transition subset and are not linked to Gaia, the 21-day maximum, company >16/18-month claims, or the abstract cohort. | Publish stable pseudonymous IDs across the full FLI attempt cohort, transition, follow-up, and source versions; define the support-duration clock and retain all attempts and missingness. |
| Defined developmental and metabolic outcomes | Incomplete: one transition-poster maze assessment at 3 months is reported comparable to age-matched controls, but test identity, scoring, comparator size, and assessor are not described. Gaia is called neurologically normal at 15 months without an instrument or thresholds. The 2017 paper's MRI time is inconsistent between Table 1 (1 year) and Results/Fig. 7d (6 months). A separate metabolic/growth poster reports bilirubin/BUN increases, albumin decrease, and a gestational-age comparison, but not per-animal values or panel-specific denominators. | Publish methods, timepoints, units, denominators, per-unit values and missingness for each functional, metabolic, growth, and developmental domain, with comparator context and adverse or discordant outcomes. |
| Cohort-level healthy-output qualification | Not met: reported long-term outcomes are selected cases; the 2017 MRI timing conflicts, the 2026 poster has one maze result, and Gaia's “normal” assessment lacks a stated instrument. No source supplies a linked, multi-domain post-support cohort. | Define the scope of the claim; link all attempts to same-unit follow-up; report prespecified growth, organ, respiratory/cardiovascular, neurological/cognitive, and other measured domains at repeated timepoints, with comparator, assessor, scores, missingness, and adverse outcomes; replicate independently. Human health claims require human outcome evidence. |
| Reproducible cohort performance | Incomplete: the 2025 abstract gives aggregate 7–14 day outcomes for 12 experiments; the 2026 release gives a 21-day maximum without a distribution or denominator. | Publish outcome distributions and adverse-event accounting for prospectively defined, independently repeated cohorts. A maximum-duration case alone does not demonstrate reproducibility. |
| Human-study status and scope | Future planned: the hospital targets 2028–2029; the company fundraising page targets 2029 and says AEMPS engagement has begun. The bounded ClinicalTrials.gov title search found no exact match. These statements do not establish authorization or an active trial. | Before calling a human study active or approved, link a registered protocol and jurisdiction-specific authorization. Keep any result scoped to the tested preterm-fetal use; it would not demonstrate embryo-to-birth development. |
| Cross-species pig-to-human claim | Unverified for fetaLife/BCNatal. A 2023 project announcement lists pig testing as a phase-two plan; peer-reviewed pig studies from other teams report short support and unresolved physiology, not fetaLife results or long-term neurological follow-up. | Link the project-specific protocol and cohort report, identify the tested system and outcomes, and provide animal-linked follow-up methods/results before promoting transferability or neurodevelopment claims. |

These are evidence-reporting gates, not experimental protocols. The structured
versions are in `evidence_promotion_gates` in the candidate inventory.

## Minimum fields for a future longitudinal intake

- Attempted starting cohort, every unit identifier, species, gestational-age
  convention, developmental stage, and support-start time.
- A disposition for each attempted unit: transitioned, supported, stopped,
  died, euthanized, excluded, or not assessed, with time, reason, and locator.
- Repeated observations tied to the same unit and exact elapsed time, retaining
  original units, uncertainty, missingness, assay/measurement definition, and
  whether values are individual, pooled, or group summaries.
- Comparator identity and timing; distinguish concurrent matched controls
  from historical/reference data. Do not treat repeated measurements as new
  independent animals.
- Growth and organ-specific outcomes, injury/maturation endpoints, their
  assessment times, and the fraction of the starting cohort actually assessed.
- Explicit end of support, transition outcome, live-birth status if assessed,
  typed transition events (entry, exit, circuit wean, spontaneous respiration),
  and post-support follow-up duration/function. A terminal necropsy is not a
  postnatal outcome.
- Public file/repository links, version, permissions, and source-data locators.
  A request-only statement is not equivalent to a publicly inspectable dataset;
  this project does not contact authors.

These are intake requirements, not instructions to collect new animal or
embryo data. If unit linkage, attempted denominators, or follow-up are missing,
retain a descriptive source screen and keep organism-level health unassessed.

## Cycle 282 — EP09.22 case-table intake and duration reconciliation (2026-10-11)

The visually reviewed table links four poster-local Animal 1-4 rows across gestational age at cannulation, weight, days on FLI support, gestational age at neonatal transition, extubation, survival and disposition. Four weight values (2.8, 2.0, 2.2, 2.7 kg) were added to the candidate with measurement time unset, and the poster PDF path was added so the intake validator could verify its SHA-256. The candidate now has 20 observations and its one declared source artifact verifies; no transition record or cohort rate was inferred.

The crosswalk preserves the printed FLI durations [9, 24, 8, 7] and the two gestational-age increments [9, 14, 8, 10] as distinct fields. Animal 2 differs by 10 days and Animal 4 by 3 days in the other direction; the poster does not define the clock relationship. The printed durations have mean 12.0 days and sample SD 8.04, unlike the displayed 9.6 ± 3.1-day summary. The 14-day replacement for Animal 2 remains only an arithmetic hypothesis. The poster conclusion's satisfactory-respiratory summary remains alongside two rows with no successful extubation. Three of the four selected cases have reported post-transition endpoints at 2, 5 and 7 days; one is reported alive at 13 months and had one maze assessment at 3 months. These selected cases cannot estimate the FLI-start transition or survival rate, and the poster-local labels do not connect to Gaia, the 21-day maximum or other cohorts.

The [case-table crosswalk](artifacts/fetal-ovine-transition-2026-10-11-cycle282/poster-case-table-crosswalk-cycle282.csv) and [reconciliation/validation receipt](artifacts/fetal-ovine-transition-2026-10-11-cycle282/duration-crosscheck-cycle282.json) preserve the values and checks. No author was contacted.

## Cycle 283 — official DOI and publisher-route screen (2026-10-11)

Crossref metadata for DOI `10.1002/uog.70305_731` identifies an item in *Ultrasound in Obstetrics & Gynecology*, volume 68, supplement issue S1, page 257. The official ISUOG EP09.22 record's “View Poster” node embeds the same public PDF already pinned in the candidate; its inspected record has no separate data or supplement link. The direct Wiley DOI page returned HTTP 403 with a Cloudflare challenge, so its page content and any supplementary links could not be reviewed. No additional report or case-level data file surfaced in these bounded official routes. The poster remains the only accessible four-case source inspected; this does not establish repository-wide absence. No author or presenter was contacted. See the [route-screen receipt](artifacts/fetal-ovine-transition-2026-10-11-cycle283/official-route-screen-cycle283.json), Crossref response, and [official ISUOG record](https://epostersonline.com/isuog2026/poster/543).

## Cycle 284 — DOI/title public repository screen (2026-10-11)

Extend the prior brand-name search with the poster DOI, exact title, EP09.22/fetal-liquid-incubator terms and Eixarch/preterm-lamb terms in DataCite, Zenodo, Figshare and OSF public APIs. DataCite, Figshare and OSF return no matching item in the bounded queries; Zenodo's exact-title query returns zero. Zenodo's exact-DOI request returns HTTP 500 and is recorded as unavailable, not as zero. Broad Zenodo queries return tens of thousands of hits; the capped 20 returned records were disambiguated by title and DOI and none is the EP09.22 source record. No case-level data were downloaded, no observations were added, and no author or presenter was contacted. See the [query receipt](artifacts/fetal-ovine-transition-2026-10-11-cycle284/repository-route-screen-cycle284.json) and [broad-hit crosswalk](artifacts/fetal-ovine-transition-2026-10-11-cycle284/zenodo-broad-query-crosswalk-cycle284.csv). This bounded screen does not prove that private, embargoed, differently titled or unindexed data do not exist.

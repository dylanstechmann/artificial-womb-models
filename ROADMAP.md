**Acceleration update, 2026-10-12:** [PROGRAM_PLAN.md](PROGRAM_PLAN.md) targets the earliest achievable owned equipment and at least one successful gestation, preferably within two to three years or sooner. Concurrent gestations and common-date outcomes are aspirations, not requirements; AI/robot care and development moved to a separate private repository. Assume 100+ embryos available upstream. [The register](config/program/roadmap.json) ties review to the relevant result and uses immediate/weekly decisions rather than annual pacing. No biological gate advances or supported completion forecast is asserted. Earlier revisions remain preserved in their artifact directories.

**Program baseline, 2026-10-11:** Select new work under [PROGRAM_PLAN.md](PROGRAM_PLAN.md), [the task/uncertainty register](config/program/roadmap.json), and [the progress comparison](PROGRAM_STATUS.md). M01 establishes planning/reporting only. T01 is the biological architecture priority; T16 and T13 prepare actual feedback resources and concurrent operation. Keep the biological and clinical gates open until their explicit evidence/review conditions are met.

**Active work filter, 2026-10-11:** Further trend-only gas abstracts are held at the known source gap. A new milestone must add usable quantitative constraints, challenge an architectural assumption, resolve same-unit developmental continuity, or repair a demonstrated intake defect. The transition comparison already exists in Cycles 310–315; do not duplicate it.

**Support versus organ development, 2026-10-11 (Cycle 346):** extract all nine terminal numeric Table 1 endpoints and the complete Table 3 from the pinned Usuda 2023 JATS source: 59 numeric group summaries and one missing control cell. Preserve neutral brain/body-mass findings alongside reduced organ/bone outcomes, SD versus IQR, the six/eight control discrepancy, exact source units, and unlinked animal identities. Unadjusted ratios of published means quantify the body-mass/organ-development mismatch without a causal effect or model fit. See artifacts/usuda-terminal-development-cycle346/.

**Partial source intervals, 2026-10-11 (Cycle 345):** preserve a known source starting bound with a null ending bound; enforce every known constraint and distinguish partial checks from full containment. Restore Weiner's reported 18-week start without inventing an ending week or assigning ages to its qualitative observations. Focused tests and the 549-test suite pass in the dev container. See artifacts/partial-source-interval-intake-cycle345/.

**Weiner et al. 1992 venous gas/pressure trends, 2026-10-11 (Cycle 344):** record source-reported pCO2 and umbilical-vein pressure increases and pO2 decrease in 80 referred fetuses found unaffected. The abstract gives no numeric age cells; Ovid marks the primary article PDF only. Keep the 50-fetus enzyme cohort separate. No author contacted. See artifacts/weiner-1992-reference-window-cycle344/.
**Nava et al. 1996 venous pH/PO2 trends, 2026-10-11 (Cycle 343):** add two abstract-level directional records from 157 fetuses spanning 18–37 weeks; preserve placental cord-insertion (n=125) and intrahepatic-vein (n=32) sites. PubMed gives no age-specific values or coefficients; Ovid returned HTTP 402 and Elsevier HTTP 403. No numeric values or author contact. See artifacts/nava-1996-ph-p02-trends-cycle343/.
**Antenatal gas source window, 2026-10-11 (Cycle 342):** screen five primary cohorts around the 24/28-week comparison. Accessible abstracts supplied cohort-wide summaries or trend directions, not age-specific values; Soothill combines sampling routes, while Filippi's open regressions come from newborns after delivery. No candidate changed and no author contacted. Next, check Nava et al. (1996) publisher/repository routes for age-stratified pH/pO2 tables. See artifacts/schubert-amazeox-age-window-source-screen-cycle342/.
**Schröter et al. 1997 age-trend candidate, 2026-10-11 (Cycle 341):** intake six abstract-level qualitative UV trends from 155 AGA fetuses spanning 18–39 weeks; preserve measured vs calculated endpoints, while the regression coefficients and 95% confidence bounds remain inaccessible. No 24-/28-week values or numeric targets inferred; no author contacted. See artifacts/schroeter-1997-gas-trends-intake-cycle341/.
**Bon et al. 1997 publisher route, 2026-10-11 (Cycle 340):** identify the exact JLE issue/article page and cross-check its abstract values. The publisher response exposes only an opening paragraph in a freemium panel; a journal-level catalog notes delayed full text with individual registration, but does not establish article-level access. Update source-resolution provenance only; candidate values remain unchanged and no author contacted. See artifacts/schubert-amazeox-bon1997-publisher-access-cycle340/.
**Bon et al. 1997 abstract-level blood-gas intake, 2026-10-11 (Cycle 339):** add six UV summary rows from the PubMed abstract while preserving the untyped ± values and unknown endpoint denominators. The 73-fetus, 17–41-week cohort count is separate metadata; no age-specific values, sample pairs, support thresholds or machine settings are inferred. Intake validates with the pinned XML hash; full text and reuse terms remain unresolved. No author contacted. See artifacts/schubert-amazeox-bon1997-intake-cycle339/.
**A-Maze-Ox blood-gas input source trace, 2026-10-11 (Cycle 338):** A-Maze-Ox's shared UA/UV pH and gas tuple is attributed to Smith's 8th-edition textbook, but the cited passage, sample frame and age basis remain unverified. Primary human cordocentesis studies show age-related pH/CO2 changes; accessible abstracts do not reproduce a complete 24-/28-week tuple. Keep the table inputs attributed, not age-specific evidence or a physiological requirement. Pin three PubMed XML records and queue the broad-range Bon et al. UV summary for separately qualified intake. See artifacts/schubert-amazeox-blood-gas-source-audit-cycle338/.

**A-Maze-Ox CO2 target equation audit, 2026-10-11 (Cycle 337):** reconstructing Khadka Eqs. 5–6 from the displayed pH, pCO2, saturation, Hb and flow inputs reproduces Table 1's 35.01/35.30 mL CO2/L targets and 2.33/3.90 mL/min rates after unit conversion and rounding. This verifies calculation arithmetic only; pH provenance remains a secondary-textbook attribution, and no human requirement is inferred. See artifacts/schubert-amazeox-co2-equation-audit-cycle337/.

**Human CO2 evidence versus A-Maze-Ox and Preemie-Ox, 2026-10-11 (Cycle 336):** no located human source supplies a fetus-only absolute CO2 production rate at 24–28 weeks. The Bonds abstract reports an indirect fetal-placental-unit estimate with gestational age, endpoint n and mass denominator unresolved; Wiberg's large cord-gas cohort is term-only and fractional. Device CO2 removal is numerically above modeled A-Maze-Ox transfer targets in a separate Preemie-Ox bench summary, but those flows and test conditions do not establish fetal margin. Add one review-pending Bonds summary candidate; preserve no human requirement or healthy acid-base envelope. See `artifacts/schubert-amazeox-co2-evidence-cycle336/`.
**A-Maze-Ox uptake cross-check against recovered primary data, 2026-10-11 (Cycle 335):** the original Assali et al. Table II is now visually verified from the 1960 issue scan. It reports eight approximate case values among 12 retained patients, with four blank uptake rows. A-Maze-Ox's derived 24-week rate is 20.6% above the single 24-week case; at 28 weeks it is within 0.25% of one case. The values are not means or design thresholds; source review remains pending and reuse terms are unconfirmed. See `artifacts/schubert-amazeox-assali-source-recovery-2026-cycle335/` and `config/observations/assali_1960_fetal_oxygen_uptake_candidate.json`.
**A-Maze-Ox fetal blood-gas input provenance, 2026-10-11 (Cycle 333):** the primary Soothill fetoscopy abstract reports second-trimester UA/UV group means that differ from the textbook-attributed A-Maze-Ox inputs; its exact gestational distribution and sO2 are unavailable in the abstract. A second 200-pregnancy study spans 16–38 weeks but its accessible abstract lacks numeric age-specific cells. Keep these as source-scoped comparisons; add no 24/28-week observations or pairings. See `artifacts/schubert-amazeox-gas-inputs-2026-cycle333/`.
**A-Maze-Ox oxygen-uptake cross-check, 2026-10-11 (Cycle 334):** Table 1 implies 5.55 and 5.39 mL O2/min/kg at 24/28 weeks. The 28-week value closely matches a historical 5.4 mL/min/kg endpoint cited by a later primary paper, but the original table, denominator and uncertainty were not recovered; modern in-vivo MRI evidence measures oxygen delivery rather than uptake. The human critical delivery threshold remains unknown. See `artifacts/schubert-amazeox-uptake-comparison-2026-cycle334/`.

**A-Maze-Ox flow and weight-model sensitivity, 2026-10-11 (Cycle 332):** Gerson's separate absolute-flow and weight-normalized regressions, combined with A-Maze-Ox's 670/1210 g weights, yield three distinct flow-dependent OTR scenarios at 24/28 weeks (Kiserud table 3.72/6.52; Gerson absolute 6.57/9.95; Gerson weight-normalized × A-Maze-Ox weight 5.42/9.71 mL O2/min). These are cross-source sensitivities, not a selected requirement. See `artifacts/schubert-amazeox-flow-weight-sensitivity-2026-cycle332/`.

**A-Maze-Ox selected flow-source access, 2026-10-11 (Cycle 331):** the Kiserud abstract confirms a 212-pregnancy low-risk cohort and intra-abdominal UV Doppler measurements, but not the exact flow regression or the 66.6/110.4 mL/min age values used by A-Maze-Ox. Inspected Wiley PDF routes returned 403; PubMed and Crossref records are pinned. Keep the values attributed to A-Maze-Ox Table 1/ref. 22 without independent full-text recalculation. See `artifacts/schubert-amazeox-kiserud-source-access-2026-cycle331/`.

**A-Maze-Ox flow sensitivity, 2026-10-11 (Cycle 330):** a second cited Doppler study's regression gives 117.78 mL/min at 24 weeks (matching its published 118), versus 66.6 mL/min used in Table 1. Applying the same per-liter OT targets changes derived OTR by 1.77× at 24 weeks; the alternative 28-week flow is a regression-derived 168.58 mL/min, above the device's 150 mL/min test ceiling. Preserve this as a separate sensitivity scenario, not a selected fetal requirement. See `artifacts/schubert-amazeox-flow-sensitivity-2026-cycle330/`.

**A-Maze-Ox reference provenance, 2026-10-11 (Cycle 329):** applying the cited oxygen-content equation to the displayed Table 1 inputs reproduces its 24/28-week targets within 0.0032/0.0029 mL O2/L blood. The Results/Discussion pair remains 0.14/0.15 higher; hidden saturation precision could account for that scale, but exact inputs and the paper's explanation are unavailable. The target discrepancy stays unresolved. See `artifacts/schubert-amazeox-reference-provenance-2026-cycle329/`.

**A-Maze-Ox oxygen-target provenance, 2026-10-11 (Cycle 328):** Table 1 reports 55.82/59.04 mL O2/L blood for the 24/28-week references, while Results/Discussion reports 55.96/59.19. Preserve both source locations; the Table 1 transfer-rate arithmetic aligns with its own targets, but the paper does not explain the small mismatch. The measured maximum remains below all four values. See `artifacts/schubert-amazeox-target-audit-2026-cycle328/`.

**A-Maze-Ox public data-route screen, 2026-10-11 (Cycle 327):** the article's data statement makes datasets available on request. The publisher/PDF and exact DOI-linked DataCite, Crossref, Figshare and OpenAIRE routes exposed no raw per-operating-point dataset; DataCite's one hit is the institutional article record, while Zenodo returned HTTP 500. Keep this bounded, make no global absence claim and do not contact authors. See `artifacts/schubert-amazeox-data-route-2026-cycle327/`.

**A-Maze-Ox pressure-loss constraint, 2026-10-11 (Cycle 326):** add the reported 14.9 mmHg pressure drop at DC/50 mL/min and preserve the statement that the 20 mmHg criterion was exceeded at 90 mL/min. Retain the Results text's “190 mmHg” condition for the 45.4 mmHg endpoint as unresolved rather than silently changing its units. See `artifacts/schubert-amazeox-pressure-loss-2026-cycle326/`.

**A-Maze-Ox oxygen-transfer intake, 2026-10-11 (Cycle 325):** preserve five text-reported operating points with source-linked mode/flow conditions. In the single porcine-blood test, maximum reported oxygen transfer remains below the paper's 24- and 28-week targets; the article also notes that its inlet pO2 exceeded the cited fetal umbilical-artery value. Do not interpret the values as fetal or clinical performance. See `artifacts/schubert-amazeox-oxygen-transfer-2026-cycle325/`.

**Preemie-Ox hydraulic constraints, 2026-10-11 (Cycle 324):** add the reported `51 ± 0 mmHg/L/min` resistance result with the Methods triplicate test count and unspecified ± type, plus the 15 mL priming-volume result without a replicate count. Keep these distinct from gas-exchange tests and biological outcomes. See `artifacts/omecinski-device-constraints-2026-10-11-cycle324/`.

**Unspecified ±-term and saturation intake, 2026-10-11 (Cycle 323):** source review found that the Preemie-Ox article reports ± quantities without defining SD versus SE. Replace the candidate's unsupported mean±SD labels with `reported_plus_minus`, add the SO2 summary with null n, and keep all summaries unpaired. See `artifacts/omecinski-uncertainty-scope-2026-10-11-cycle323/`.

**Preemie-Ox blood-flow context, 2026-10-11 (Cycle 322):** preserve the reported `163 ± 2 mL/min` blood-flow summary as a separate typed test-context record. The Results sentence co-reports `n=9`, but gives no run IDs or flow-to-vCO2 rows; keep it aggregate and unpaired. See `artifacts/omecinski-flow-context-2026-10-11-cycle322/`.

**Source version and rights intake, 2026-10-11 (Cycle 321):** separate archived-version identity, public full-text access, repository OA-subset membership, and reuse-rights status in observation artifacts. Resolve the Preemie-Ox PMC record to its current author-manuscript version and record the official filter result; the item-specific license remains unconfirmed, the source hash stays null, and the candidate remains pending. See `artifacts/omecinski-source-resolution-2026-10-11-cycle321/`.

**Typed mean±SD observation intake, 2026-10-11 (Cycle 320):** add `mean_sd` source-summary support and record the Preemie-Ox article's in-vitro vCO2 group result as a review-pending candidate. Preserve n=9 as gas-exchange test samples, not biological independent units; no run-level values or pairings are invented. Source bytes and reuse terms remain unresolved. See `artifacts/omecinski-preemieox-2023-10-11-cycle320/`.

**Public oxygenator pairability screen, 2026-10-11 (Cycle 319):** compare two primary artificial-placenta sources with declared inlet/outlet gas sampling. Both report methods routes, but neither inspected public route exposes source-linked paired gas rows; one provides an aggregate in-vitro device result. No values were digitized or promoted. This is bounded article-route coverage, not proof the underlying data do not exist elsewhere. See `artifacts/artificial-placenta-gas-pairability-2026-10-11-cycle319/`.

**Paired-record consistency, 2026-10-11 (Cycle 318):** constrain `same_unit_same_time` pairs to records with one shared reported unit ID and exactly matching non-null measurement time/unit. Mismatch and missingness cases fail validation; synthetic examples confirm the rule. No biological values or pair links were added. See `tests/test_observation_pair_consistency_cycle318.py`.

**Paired-measurement intake, 2026-10-11 (Cycle 317):** add optional dataset-level measurement-pair declarations with source/curator linkage, typed relationship, source locator, and member roles. Validation requires known records from the declared source artifact; exports preserve the pair map. The Eixarch 2023 candidate remains unchanged because its inspected Results do not expose paired gas values or pairable records. See `PHENOTYPE_INTAKE.md` and `tests/test_observation_measurement_pairs_cycle317.py`.

**2023 ovine gas-transfer evidence screen, 2026-10-11 (Cycle 316):** the pinned article describes membrane blood-gas measurement and methods-level gas targets, but the inspected Results/Table 1 and candidate provide no numeric paired PaO2/PaCO2 outcomes or net transfer estimates. Keep methods context separate from achieved function; no setpoints were reproduced and the candidate remains unchanged. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle316/`.

**2023 ovine support functional-evidence overlay, 2026-10-11 (Cycle 315):** classify all 50 group-summary records in the peer-reviewed Eixarch cohort. Six circuit-flow summaries are direct support-output measurements, 18 pH/lactate/heart-rate records are response proxies, 11 are survival/adverse outcomes, and 15 are operational context. Keep n=8/10/10 goal bands separate and do not interpret circuit flow as net exchange. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle315/`.

**Functional-classification intake rehearsal, 2026-10-11 (Cycle 314):** apply the row overlay only to temporary copies of the four FLI candidates and run the observation validator/exporter. All 51 rows validate and export; all four local poster files pass source-byte checks and their bundles verify. The original candidate files remain unchanged. This tests intake and provenance plumbing, not the scientific classification. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle314/`.

**Row-level functional evidence classification for four FLI posters, 2026-10-11 (Cycle 313):** create a hash-pinned, non-mutating overlay for all 51 candidate observation rows. It classifies 29 circulating response summaries as proxies, 18 growth/transition records as developmental outcomes, four support-duration rows as other/context, and none as a direct exchange measurement. The overlay is provisional and leaves source candidates unchanged. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle313/`.

**Typed functional-evidence role for observation intake, 2026-10-11 (Cycle 312):** add an optional record-level classification for direct process measurements, biological response proxies, and developmental outcomes; preserve omission as unclassified and export the field in observation and exact-group reports. Existing FLI candidates remain unchanged and source review remains pending. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle312/`.

**Four-poster functional-evidence sufficiency map, 2026-10-11 (Cycle 311):** distinguish direct exchange/function evidence from circulating response markers, growth summaries and selected transition outcomes in EP09.20/22/31/40. These posters add measured biology, but do not directly establish exchange flux, barrier integrity or a same-unit support-to-transition path. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle311/`.

**Four-poster feasibility coverage refresh, 2026-10-11 (Cycle 310):** consolidate IL-6, metabolic/growth, HPA/steroid, and selected neonatal-transition evidence without pooling poster counts. The main unresolved barrier is a same-unit, all-start longitudinal record through transition and follow-up; endpoint-specific n, transition conditions, and later coverage remain incomplete. No candidate values or transitions added. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle310/`.

**Four-poster public-record route crosswalk, 2026-10-11 (Cycle 309):** complete the EP09.20 lookup and consolidate all four FLI poster routes. Crossref lists one-page entries on pp.256, 257, 259, and 261–262 with empty relations; scoped exact searches found no indexed/repository records, and Wiley DOI pages returned HTTP 403. Candidate data remain unchanged; do not treat bounded search results as proof of absence. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle309/`.

**EP09.22 transition-poster fuller-record screen, 2026-10-11 (Cycle 308):** Crossref identifies a one-page volume 68 entry (p.257) with no relation links; exact DOI/title searches of PubMed, Europe PMC, DataCite, Zenodo, Figshare, and OSF found no match, and the Wiley route returned HTTP 403. Preserve the four displayed transition cases as the poster’s selected-case denominator; no new outcomes or transitions. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle308/`.

**EP09.31 fuller-record and data-route screen, 2026-10-11 (Cycle 307):** Crossref identifies a one-page volume 68 entry (p.259) with no relation links; exact DOI/title searches of PubMed, Europe PMC, DataCite, Zenodo, Figshare, and OSF found no match, and the Wiley route returned HTTP 403. Keep this as a bounded lookup, preserve the poster candidate unchanged, and do not infer global absence. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle307/`.

**Official ISUOG 2026 FLI poster portfolio, 2026-10-11 (Cycle 306):** reconcile the official De Roo-Puente author listing, exact BCNatal affiliation listing, and poster keyword results. Four distinct FLI-specific posters are present in the workspace (EP09.20/.22/.31/.40); an affiliation-string filter omits EP09.22, while adjacent Pre-EXIT and preterm-outcome posters are not FLI cohort reports. Add no observations and limit the completeness claim to this portal. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle306/`.

**EP09.40 fuller-record and dataset route screen, 2026-10-11 (Cycle 305):** exact-identifier searches of PubMed, Europe PMC, DataCite, Zenodo, Figshare, and OSF returned no matching full-report or repository record; Crossref has no relation entry and the Wiley DOI page returned HTTP 403. Treat this as a bounded lookup result, not proof of global absence. Keep the public poster as the located source, leave its candidate values unchanged, and do not contact authors. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle305/`.

**EP09.40 fetal HPA/steroid support profile, 2026-10-11 (Cycle 304):** intake six analytes from the official 16-lamb poster at 115–125 gestational days and ≥72 h FLI support. Preserve baseline/72 h median [IQR] values and continuous-time mixed-model p-values while leaving per-timepoint n and animal IDs missing; do not treat p-values as pairwise contrasts. Screen possible overlap with EP09.20, EP09.31, and EP09.22 without pooling. The next evidence gap remains same-unit linkage from support through neonatal transition and follow-up. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle304/`.

**EP09.20 IL-6 support profile intake, 2026-10-11 (Cycle 303):** pin the official 20-lamb poster and DOI metadata; structure the 6/7/7 coating groups, ≥6-day selection frame, and 0–144 h sample schedule. Preserve the median±IQR curves and author-reported attenuation/PMEA trend qualitatively because exact values, timepoint n, and the nonuniform axis transform are unstated. EP09.20, EP09.31, and EP09.22 frames may overlap; do not pool counts or infer a transition rate. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle303/`.

**FetaLife life-phase and outcome coverage, 2026-10-11 (Cycle 302):** map the 2023 paper, 2023 institutional milestone, 2025 abstract, and two 2026 posters by support phase, transition, and follow-up. Evidence covers late-fetal ovine support and reaches neonatal transition in four selected cases, but reports are not unit-linked; no embryo-to-birth trajectory or cohort-level healthy outcome is demonstrated. Preserve each denominator and source class. The next intake priority is an all-start, unit-linked path through support, transition, and follow-up. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle302/`.

**EP09.22 respiratory and developmental endpoint scope, 2026-10-11 (Cycle 301):** reconcile the four extubation rows with the prose claim of satisfactory respiratory parameters. The table gives 2 Yes/2 No; because the poster omits assessment conditions and support mode, treat this as an endpoint-scope mismatch, not a direct contradiction. One animal has 13-month survival and one qualitative maze result at 3 months; this does not establish comprehensive normal development. Narrow candidate wording, add no observations, and retain denominators as selected-case only. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle301/`.

**EP09.22/EP09.31 selected-cohort compatibility, 2026-10-11 (Cycle 300):** all four EP09.22 cases meet EP09.31’s printed ≥6-day FLI-support criterion and fall in its ≥115-day gestational-age stratum if the reports share a cohort. This supports a possible selected-subset hypothesis only; there are no shared IDs/dates, EP09.31 reports no transition outcomes, and n=29 is not a transition denominator. Keep records separate and add no transitions. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle300/`.

**Eixarch 2023/2025/2026 unit-identifier coverage, 2026-10-11 (Cycle 299):** inspect the 2023 official PMC XML, 2025 official Wiley abstract, and 2026 official ISUOG poster surfaces for a shared animal/experiment key. The 2023 animal-mean points are unlabeled, the 2025 report is aggregate-only, and EP09.22 Animal 1–4 are poster-local labels. Keep all pairwise cohort links unresolved, independent replication unestablished, and counts/transitions separate. Pin the official XML hash; candidates unchanged and human review pending. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle299/`.

# Development roadmap

**Eixarch 2025 OC14.07 to 2026 EP09.22 linkage screen, 2026-10-11 (Cycle 298):** compare the 12-experiment 2025 abstract (mean survival 9.5 ± 3.3 days) with four 2026 poster transition cases (mean FLI support 9.6 ± 3.1 days). Similar research context and close summaries make partial overlap/follow-up plausible, but endpoints differ, the poster has no experiment dates or IDs, and its printed case durations (9/24/8/7) conflict with its group summary. Keep independent-replication status unestablished, add no transitions, and do not pool counts. Verify the poster PDF hash and inspect its sole page at 300 dpi; no table values were corrected. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle298/`.

**Eixarch OC14.07 percentage-denominator ambiguity, 2026-10-11 (Cycle 297):** test the abstract's rounded 75%, 50%, and 17% survival-threshold values against conditional integer fractions. Both n=12 and n=24 reproduce all three under nearest-whole-percent rounding; the 58% and 25% discontinuation figures also admit arithmetic examples under separate denominator frames. This does not make n=24 a cohort claim. Keep every outcome denominator unreported, retain the 12 Methods experiments separately, and add no counts or disposition closure. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle297/`.

**Eixarch OC14.07 official PDF/ePDF route check, 2026-10-11 (Cycle 296):** try four canonical Wiley PDF/ePDF host/path variants recorded by the article's metadata. All four return HTTP 403 HTML bodies, with zero `%PDF-` responses; the direct PDF links are inaccessible through the web reader as well. Keep the abstract candidate tied to the official rendered page with a null source-byte hash, and leave the pH SD visual glyph check open. This bounded route screen is not a global absence claim. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle296/`.

**Eixarch 2023-to-2025 cross-report cohort-linkage screen, 2026-10-11 (Cycle 295):** compare the pinned 2023 PMC full text and the official 2025 OC14.07 abstract. Both describe ovine fetuses at overlapping gestational ages in the same research program; the 2023 report has 28 fetal sheep from 28 ewes and goals through 168 h, while the later abstract reports 12 experiments with a 7–14-day target. The 2023 article's ethics/manuscript dates and the 2025 phase years do not provide animal-level dates or a crosswalk; phase language suggests sequence but does not prove cohort disjointness. Keep counts source-specific, do not sum or compare them as independent samples, and add no transitions. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle295/`.

**Eixarch et al. 2025 OC14.07 aggregate abstract intake, 2026-10-11 (Cycle 294):** structure 18 abstract-reported survival, circuit-flow, heart-rate, pH, lactate and discontinuation summaries in a candidate dataset, with three separate cohort-coverage records. The 12 Methods experiments remain distinct from the animal outcome percentages: outcome and cause denominators are not stated, so no integer counts or animal-level stopping bins are inferred. Preserve the printed 0–7-day pH SD of 0.49 with a typography check flag. The official Wiley HTML page exposed the abstract through its web reader, while direct local HTML/PDF routes returned 403 and the older abstract-PDF route returned 404; the publisher-byte hash stays null. No OC14.07 supplementary data file is listed, no post-support outcomes are reported, and no join to the 2023 or 2026 reports is established. Candidate review remains pending. See `artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle294/`.

Reviewed against the code on 2026-10-06. The long-term research question remains
complete human ectogenesis from IVF through birth. This roadmap advances
mathematics, evidence quality and reproducible research software; it does not
turn disconnected developmental intervals into a demonstrated gestation system.

**Aguilera-Castrejon source-workbook intake update, 2026-10-11 (Cycle 267):**
two DOI-derived publisher static XLSX assets are now pinned and inspected.
MOESM11 Panel d reports E7.5 culture-efficiency fractions 227/230, 212/230,
155/185 and 126/163 at +Day 1 to +Day 4; the last is printed as 77%. The
denominator changes because experiment rows are not present at later timepoints;
the workbook states dash rows were not continued for experimental requirements.
MOESM12 Panel b reports a separate E6.5 static-culture series, 414/421 and
386/399. All six aggregate numerator/denominator pairs equal the sums of the
available experiment rows. Two E6.5 experiment-row percentages conflict with
their own fractions and remain flagged. These are morphology-based,
timepoint-specific assessed-set summaries, not survival probabilities or
same-embryo trajectories. The Nature listing-to-MOESM filename mapping is
content-compatible but not confirmed at the download-anchor level. The
candidate intake and arithmetic receipt are in
`artifacts/aguilera-castrejon-source-data-2026-10-11/`; human review remains
pending. No author was contacted.

**Aguilera-Castrejon Panel e length-cell intake, 2026-10-11 (Cycle 268):**
transcribe 216 source workbook cells across eight in-utero and ex-utero groups;
the numeric-cell counts are 13/32, 19/15, 15/43 and 38/41 for the adjacent
E8.5/+Day 1, E9.5/+Day 2, E10.5/+Day 3 and E11/+Day 4 source labels. The
workbook changes the measured axis from antero-posterior at E8.5 to crown-rump
from E9.5 onward. Derived means, sample SDs and SEMs are pinned separately and
were checked against each cell; no hypothesis tests were run. Embryo row labels
are local to a column, and +Day stays a culture-time label, so no individual
trajectory or matched comparison is inferred. This is morphology evidence,
not functional maturity or survival. The 216-row candidate, cell crosswalk,
summary and receipt are in
`artifacts/aguilera-castrejon-source-data-2026-10-11/`.

**Aguilera-Castrejon figure-caption/full-text route screen, 2026-10-11 (Cycle
269):** the official Nature PDF/article path returned the article preview,
while the Source data link redirected to cookie authorization and the Figure 1
media image timed out through the public reader. PubMed ESummary lists PMID,
DOI and PII identifiers but no PMCID in its articleids field. The measurement
caption's group-count/test details and exact article-link-to-MOESM mapping
remain unverified. The source workbook remains the basis for the 216
cell-located length values and derived descriptive summaries; no significance
test or paired comparison was inferred. The one-request metadata snapshot and
route receipt are pinned in the artifact folder. No author was contacted.

**Lokshtanov et al. official v1 PDF qualification, 2026-10-11 (Cycle 270):**
retrieve the official bioRxiv PDF, verify its hash and inspect the Results and
Figure 1-3 captions. It confirms a single E7.5-start culture series reaching a
maximum reported morphology of approximately E12.5 after 5.5 culture days.
However, the embryos do not progress beyond day 5 with an intact yolk sac; the
additional ~12 hours use an opened yolk sac with umbilical vascular continuity
maintained. The authors report only 10-20% proper morphology at day 5.5 across
strains and enlarged heart, pericardial edema, internal hemorrhage and internal
tissue necrosis. A distinct E6.5-start cohort reaches approximately E11.75,
with a 12-18% final-day proper-morphology report and developmental delay; do
not pool the starting cohorts. Ex-vivo oocyte development from isolated gonads
is a useful organ-function observation, not a whole-animal live-birth outcome.
The source is explicitly an unreviewed preprint. Candidate provenance now
points to the pinned official PDF; exact figure denominators, unit-level
attrition, causal mechanism and human review remain open. See the primary-PDF
receipt in `artifacts/mouse-ex-utero-frontier-2026-10-11/` and updated
`config/source_inventories/midgestation_frontier_2026.json`.

**Lokshtanov et al. figure denominator transcription, 2026-10-11 (Cycle
271):** inspect the official Figure 1D/2D panels and their captions at full
resolution, then transcribe all 46 printed embryo-assessed-count and
independent-experiment-count pairs into source-linked cohort coverage. Preserve
two absent bars as not reported: DASGIP at E7.5 +Day 5.5 and E6.5 +Day 6.
The captions define `emb` as embryos assessed and `n` as independent
experiments; plotted percentages are experiment-level mean ± SEM, so these
denominators do not supply normal-embryo numerators, pooled success rates or
cross-day identities. The official supplement PDF is pinned; its inspected
route exposed no separate source-data table. Candidate intake validation
passes with complete source-file hash verification; human review remains
pending. See `artifacts/mouse-ex-utero-frontier-2026-10-11/denominator-coverage-cycle271.json`
and the figure crosswalk beside it.

**Lokshtanov et al. strain/replication denominator transcription, 2026-10-11 (Cycle 272):** visually transcribe 42 additional emb/n labels from Extended Data Figure 3D and 3G. Figure 3D contributes six strain/serum conditions across six culture days, but its caption does not define the unit for n; those labels remain unassigned. Figure 3G contributes six CD1 × CD1 OxyStreamer labels from an independent laboratory identified in the caption as EPFL; there the caption defines emb as embryos evaluated and n as independent experiments. Exact normal-embryo numerators and day-to-day identities remain absent. The separate Figure 4D serum comparison is not pooled with Figure 3D and is the next qualification target. Candidate validation passes with both official PDF hashes verified and 88 coverage records; review remains pending. See the [Cycle 272 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/strain-replication-cycle272.json) and [crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/extended-data-fig3d-g-strain-replication-cycle272.csv).

**Lokshtanov et al. serum-by-stage qualification, 2026-10-11 (Cycle 273):** transcribe the 12 HAS/HCS experiment-count labels in Extended Data Figure 4D. Its caption defines n as independent experiments and supplies no embryo denominator. The primary Results assigns this comparison to E6.5-start cultures and contrasts it with no evident serum-efficiency difference in E7.5-start cultures; preserve the two stage contexts separately. Add the E6.5 serum response as a candidate qualitative record, validate 12 observations and 88 coverage records against both pinned PDFs, and keep embryo numerators and experiment-level data unresolved. See the [Cycle 273 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/serum-stage-qualification-cycle273.json) and [crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/extended-data-fig4d-serum-stage-cycle273.csv).

**Lokshtanov et al. public data-route screen, 2026-10-11 (Cycle 274):** inspect the official full-text, AJAX data tab and supplementary-material tab, then query NCBI GEO GDS/BioProject and DataCite by author, exact title and DOI. The publisher data tab and supplement route expose one PDF; no explicit data-availability statement or accession is visible in the full-text HTML. The author search returns 11 GEO records, all with titles/dates that do not match this 2026 paper; exact-title/DOI queries return no matches in the bounded databases. Preserve response snapshots and the 11-record disambiguation crosswalk. This does not establish global data absence. Candidate validation passes after recording that limitation; no author contact was made. See the [Cycle 274 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle274.json).

**Lokshtanov et al. version and publication-status check, 2026-10-11 (Cycle 275):** the official bioRxiv API returns only version 1, Crossref classifies its DOI as `posted-content`, and the matching ORCID work is typed as a preprint. Exact-title PubMed and DOI/title-author Europe PMC queries returned no match; Crossref title-author hits yielded no journal record for this title/DOI. A broader PubMed author query surfaced a distinct preprint DOI and was disambiguated. No journal-version match was located in these checked indexes; this does not rule out a retitled or incompletely indexed report. The candidate remains marked as a preprint and validates with 12 qualitative records and 88 coverage records. See the [Cycle 275 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/publication-version-check-cycle275.json).

**Lokshtanov et al. BioStudies/MetaboLights route extension, 2026-10-11 (Cycle 276):** query the official EMBL-EBI BioStudies and MetaboLights public study-index APIs by exact DOI/title and broader title/author terms. BioStudies exact DOI/title searches return zero; broader author-plus-embryo and title-term searches return four older records, all disambiguated as different papers. MetaboLights DOI/title/author searches return zero. No target-linked accession or source-data file was located in these routes; the result remains bounded and does not establish repository-wide absence. Candidate validation passes with 12 qualitative observations and 88 coverage records. See the [Cycle 276 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle276.json) and [BioStudies crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/biostudies-broad-query-crosswalk-cycle276.csv). No author was contacted.

**Lokshtanov et al. repository discovery extension, 2026-10-11 (Cycle 277):** check Zenodo, Figshare, GitHub repository search and OpenAIRE by exact DOI/title/author. OpenAIRE returns one exact-DOI publication record and no dataset record; its record points to an EPFL Infoscience full-text URL, but direct EPFL record/bitstream requests return HTTP 429, so the linked file remains unverified. GitHub title/author searches return zero; Figshare exact DOI/author queries return zero and its five broad title hits are unrelated 2021 supplement records. Zenodo title/author queries return zero, while exact-DOI search fails with HTTP 500 and is not counted as zero. Candidate remains at 12 qualitative observations and 88 coverage records; validation passes and no author was contacted. See the [Cycle 277 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle277.json) and [Figshare crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/figshare-title-search-crosswalk-cycle277.csv).

**Lokshtanov et al. Metabolomics Workbench screen, 2026-10-11 (Cycle 278):** query the official REST API's documented study-title and last-name fields. Full/core title, ex-utero, gastrulation and metabolic-program searches, plus four coauthor last-name searches, return zero; a broad “mouse embryo” query returns seven older or otherwise distinct studies, preserved in a crosswalk. The API has no DOI search field, so this is not an exact-DOI query. No target-linked metabolomics record is located and no values are promoted. Candidate validation passes with 12 qualitative observations and 88 coverage records. See the [Cycle 278 receipt](artifacts/mouse-ex-utero-frontier-2026-10-11/public-data-route-screen-cycle278.json), [crosswalk](artifacts/mouse-ex-utero-frontier-2026-10-11/metabolomics-workbench-broad-title-crosswalk-cycle278.csv), and official [REST API specification](https://www.metabolomicsworkbench.org/tools/MWRestAPIv1.2.pdf).

**Hiraoka GEO-to-SRA technical provenance, 2026-10-11 (Cycle 279):** reconcile the 21 GEO sample records across GSE279808/809/279268 to BioSample, SRX, SRR and BioProject metadata. Each maps to one distinct technical run; four ENA API failures were resolved from NCBI SRA ESummary. This clarifies repository identifiers but does not link molecular samples to later Figure 5 embryos or assay withdrawals. No reads or matrices were downloaded. See the [Cycle 279 receipt](artifacts/source-mapping-2026-10-09/hiraoka-sra-run-reconciliation-cycle279.json) and [crosswalk](artifacts/source-mapping-2026-10-09/hiraoka-geo-sra-run-crosswalk-cycle279.csv). Cycle 280 subsequently inspects the Bondarenko Zenodo ZIP directory and README with bounded HTTP ranges; the movement/outcome join remains unestablished.

**Bondarenko Zenodo archive range inspection, 2026-10-11 (Cycle 280):** inspect only the ZIP EOCD, central directory and small README member using three HTTP byte ranges (71,499 total bytes from a 3.08-GB archive). All 53 entries parse and the README CRC passes. The archive inventory lists HDF5 image/segmentation stacks, PNG thumbnails and README, with no tabular crosswalk member; README describes raw images and instance-segmentation labels, not later developmental outcomes. E/Ab filename aliases remain opaque; no movement-to-embryo/outcome join is verified. No image stacks were downloaded, no biological observations were added and no author was contacted. The result is bounded to directory and README inspection. See the Cycle 280 receipt and inventory in `artifacts/source-mapping-2026-10-09/`.

**Cross-source linkage register and intake gate, 2026-10-11 (Cycle 281):** consolidate the Hiraoka GEO/SRA technical chain and Bondarenko Figure 6/Zenodo source-key audits into a machine-readable register. One technical identifier chain is verified, one compound embryo-key relationship remains a candidate, and zero individual longitudinal biological joins are verified. The register specifies that source-authenticated biological keys, compatible units/times/assays and dispositions are required before adding same-unit transitions; null IDs and pools stay explicit. No candidate observations were changed. See `artifacts/source-mapping-2026-10-09/cross-source-linkage-register-cycle281.json` and its receipt.

**EP09.22 case-table intake and source-hash verification, 2026-10-11 (Cycle 282):** add the four poster-table weight values with measurement time left unset, add the pinned PDF as a local intake artifact, and validate the 20-record candidate with complete source-byte verification. A row-level reconciliation preserves the visibly printed support days [9, 24, 8, 7] and separate gestational-age increments [9, 14, 8, 10], exposing unexplained differences for Animals 2 and 4 without correction. The four poster-labeled neonatal-transition cases include three reported post-transition endpoints at 2, 5 and 7 days and one 13-month survivor; these are selected cases without an FLI-start denominator or cross-study IDs. See `artifacts/fetal-ovine-transition-2026-10-11-cycle282/`.

**EP09.22 DOI/publisher route screen, 2026-10-11 (Cycle 283):** Crossref places the DOI in *Ultrasound in Obstetrics & Gynecology* 68(S1), page 257; the official ISUOG EP09.22 “View Poster” node embeds the already pinned PDF and exposes no separate data or supplement link. The direct Wiley page returned HTTP 403 with a Cloudflare challenge, so the publisher page was not inspected and the result is bounded to accessible official routes. No new observations were added and no author/presenter was contacted. See `artifacts/fetal-ovine-transition-2026-10-11-cycle283/official-route-screen-cycle283.json`.

**EP09.22 DOI/title repository screen, 2026-10-11 (Cycle 284):** extend the earlier fetaLife-name search with exact DOI/title, EP09.22/Fetal Liquid Incubator and Eixarch/preterm-lamb terms across DataCite, Zenodo, Figshare and OSF. No target record surfaced in successful exact/title searches; Zenodo's exact DOI request returned HTTP 500 and is not counted as zero. Twenty capped broad Zenodo results were disambiguated by title/DOI and are not the target record. No observations or candidate values were added. See `artifacts/fetal-ovine-transition-2026-10-11-cycle284/`.

**EP09.22 transition-duration visual recheck, 2026-10-10:** a direct public
download of the one-page poster was pinned locally and visually inspected.
Animal 2's table cell reads 24 days. The four table values (9, 24, 8, 7) imply
12.0 ± 8.04 days (mean ± sample SD), versus the poster summary 9.6 ± 3.1 days;
the displayed Animal 2 gestational ages imply 14 days. A 14-day substitution
would bring the sample SD near 3.1 but the mean to 9.5, so the discrepancy is
not resolved and no value is corrected. The four source-reported durations now
appear in the candidate intake with a row-level inconsistency qualification
for Animal 2. The poster still reports no total FLI-start or transition-eligible
denominator, so these four cases do not estimate transition success.

**EP09.31 metabolic/growth poster intake, 2026-10-10:** the official public
poster is pinned and visually inspected. A 14-row candidate records six
baseline/day 6-7 biomarker displays and two gestational-age-group growth
summaries. The poster selects 29 lambs supported for at least six days and
prints growth-group n=5 and n=24, but biochemical endpoint/paired n is not
stated. Bracketed ranges are retained without assigning an IQR/SD meaning.
The growth figure's p=0.186 and adjusted-model age associations are separate
reported results. This improves description of sustained fetal support while
leaving individual trajectories, all-start success, post-support function and
links to the neonatal-transition poster unresolved.

**Goh et al. E-MTAB-10552/11673 metadata crosswalks, 2026-10-10:** E-MTAB-10552
has 22 sample/run rows at Carnegie stage 18 from three source-labeled
individuals (F61, F79, F80), with tissue and sorted immunophenotype strata.
E-MTAB-11673 has six unique yolk-sac/stalk samples from source-labeled F158 at
female CS17; its 18 SDRF rows repeat samples across three FASTQ files. The
source reports one lane excluded after cell-level QC, but processed matrices
were not inspected. These are metadata crosswalks, not longitudinal support
results or independent biological replicates. Four other paper accessions
remain unqualified. The cross-accession linkage to a matched coronal section
mentioned by E-MTAB-11673 was open during this initial screen and is resolved
below. No raw/expression analysis, biological fitting, observation promotion,
or author contact occurred.

**Goh et al. E-MTAB-10888 crosswalk, 2026-10-11:** the official BioStudies
SDRF contains 284 paired-end file rows that collapse to 142 unique yolk-sac
sample/run records: 71 source-labeled F79 records at CS18 and 71 F80 records at
CS15. F79/F80 labels recur in E-MTAB-10552, but no sample, BioSample or run IDs
overlap; the F80 stage labels conflict across accessions (CS18 versus CS15).
This does not establish paired specimens or identify the F158 matched coronal
accession mentioned by E-MTAB-11673. Three other accessions remain unqualified.
Only API/info/SDRF metadata were retrieved; no expression analysis, fitting,
observation promotion or author contact occurred.

**Remaining Goh accession metadata screen, 2026-10-11:** the other three listed
accessions are yolk-sac or liver CITE-seq records. Their SDRFs map 11 ENA sample
records across 528 runs and 1,582 FASTQ file rows; the API descriptions report
2, 3 and 6 biological replicates, respectively. Keep those source claims
separate from file/run counts and from the multiple source-individual labels.
E-MTAB-11618 sample ERS11465100 has only 46 index1 rows against 48 read1 and
read2 rows. A case-insensitive search of these API/SDRF records found neither
F158 nor “coronal”; that listed-accession-only screen did not resolve the
matched section accession. The separate ENA project is identified below. The
crosswalk is metadata-only; no read or matrix files were downloaded.

**F158 coronal-accession search, 2026-10-11:** exact BioStudies API queries for
F158, 16099 and “coronal section” returned 16/39/27 hits across all collections
and 3/5/9 in the ArrayExpress collection; E-MTAB-11673 was the only human
fetal/yolk-sac record identified. Direct ENA Browser XML confirmed that
ERP137250/PRJEB52523 and all six ENA sample/run records belong to the existing
F158 yolk-sac accession, without naming a second accession. These exact-term
searches did not surface the match; a subsequent NCBI/ENA project lookup
identified it as E-MTAB-11911 (PRJEB53919; ERP138734), described below. ENA
Portal global search attempts returned errors, so they do not support a global
absence claim. Search/XML snapshots are pinned in
`artifacts/early-exchange-transition-2026-10-11/` and inventoried.

**Matched F158 coronal-project resolution and section crosswalk, 2026-10-11:**
the public ENA project PRJEB53919 is submitted under the alias E-MTAB-11911
(secondary study ERP138734). Its title names the same F158/HDBR 16099 embryo;
its description lists 12 coronal sections and says the matched accession
contains the yolk sac and stalk. E-MTAB-11673 describes the reciprocal
relationship. The project’s 48 unique ENA sample/BioSample/experiment/run
records map to 12 section labels, four sample/run records per section; every
record is labeled F158, female and Carnegie stage 17. These are records from
one source-labeled embryo, not 48 independent embryos or assumed biological
replicates. This resolves the accession-level link but not cell-level pairing,
independent replication, functional exchange, or longitudinal support. The
[48-row ENA sample crosswalk](config/source_inventories/goh_2023_emtab11911_coronal_sample_crosswalk.csv)
and its XML/EUtils snapshots are pinned.

**Matched-project file-index screen, 2026-10-11:** the project description says
CellRanger filtered count matrices are attached with data combined across all
10x lanes, but it does not state whether separate matrices preserve section
labels. The ENA run-file report maps 48 runs to 144 FASTQ files (I1/R1/R2), or
12 files per section. The queried ENA analysis-file report returned only its
header; the project XML and these file reports expose no matrix filenames or
per-section matrix manifest. This is a file-index limitation, not evidence that
the described matrices do not exist. The 144-row
[FASTQ file manifest](config/source_inventories/goh_2023_emtab11911_coronal_fastq_manifest.csv)
is pinned; no FASTQs or matrices were downloaded.

A cycle-190 recheck retained that limit: the F158 analysis report again returned
only a header, while F137 report requests failed with HTTP 500 responses or
timeouts. The [route-probe receipt](artifacts/early-exchange-transition-2026-10-11/goh-f137-f158-ena-analysis-file-route-probe-cycle190.json)
records the response state. It does not show that matrices are absent; direct
matrix links and per-section partitioning remain unresolved.

**HDCA preprint/archive cross-check, 2026-10-11:** the 2026 bioRxiv v2 names
E-MTAB-11911 for F158 and E-MTAB-11504 for F137, while saying the listed data
accessions and atlas portal are private pending publication. Public ENA
records separately expose E-MTAB-11504 as alias PRJEB51328/ERP135952 with 45
public SRA runs, and E-MTAB-11911 as PRJEB53919/ERP138734 with 48 public
sample/run records and 144 FASTQs. Both project descriptions say filtered
CellRanger matrices are attached, but exact matrix download links and
per-section partitioning remain unverified. Anonymous BioStudies API requests
for all six listed ArrayExpress/BioImage Archive IDs returned HTTP 403,
"Study not accessible." BioStudies guidance says non-public data may require
credentials; the API does not expose why it denied these requests. The
preprint may therefore describe the BioStudies/processed-data packages while
ENA exposes linked raw-read records; the route-specific access state is
unresolved. Exact-term SRA searches returned no E-MTAB-11520 or E-MTAB-14785
hits, and a request for E-MTAB-16757 was rate-limited, so those screens do not
establish cross-archive privacy. A normal request to the portal returned only a
JavaScript shell. No credentials or access controls were bypassed, and no
sequence or matrix files were downloaded. This is a repository-status
cross-check, not a support outcome or evidence of function.

**F137 section crosswalk, 2026-10-11:** the public SRA/ENA records yield 45
unique sample/BioSample/experiment/run rows, all source-labeled F137, female,
Carnegie stage 16. ENA `fraction` labels cover all 12 coronal sections: one
sample/run row for section one and four for each of sections two through
twelve. The project description names `WS_wEMB10202360` as excluded from
downstream analysis for low mean read count; sample metadata maps it to section
seven, and the public run remains in the metadata crosswalk. Preserve that
distinction and the source's exclusion claim; do not infer the reason for the
unequal section-one count or treat lanes as independent embryos. The
[45-row F137 crosswalk](config/source_inventories/goh_2023_emtab11504_f137_sample_crosswalk.csv)
and its 45 direct ENA sample XML snapshots are pinned. No reads or count
matrices were downloaded.

**F137 run-level file metadata, 2026-10-11:** NCBI EFetch RunInfo returns 45
public run rows with SRA archive download paths, spot counts and base counts;
this is not a FASTQ-file manifest. The joined
[45-row RunInfo manifest](config/source_inventories/goh_2023_emtab11504_f137_runinfo_manifest.csv)
maps each run to its section. ENA filereport requests timed out for the study
and a single run in the first probe; a later project query returned a
[135-row FASTQ manifest](config/source_inventories/goh_2023_emtab11504_f137_fastq_manifest.csv)
with three submitted-file records per run, joined to the same 45
sample/section records. File names, sizes and MD5 strings are archive metadata
only; no FASTQ contents were downloaded and checksums were not recomputed. The
downstream-excluded `WS_wEMB10202360` run (ERR9034751) has 133,294 spots and
16,928,338 bases, about 0.026% of the median spot count in the other 44 runs.
This is compatible with the project's low-read note but remains sequencing
metadata, not an embryo outcome. No sequence or matrix data were downloaded.

**F137/F158 run-level coverage comparison, 2026-10-11:** join the 45 F137 and
48 F158 public RunInfo records to their 12-section crosswalks in the
[12-row section summary](config/source_inventories/goh_2023_f137_f158_coronal_run_coverage_comparison.csv).
F158 also has 144 ENA-submitted FASTQs in its pinned file manifest, but the
NCBI RunInfo record for ERR9882663 reports zero spots/bases and no SRA archive
path. A direct [run-metadata reconciliation](artifacts/early-exchange-transition-2026-10-11/ERR9882663-run-metadata-reconciliation-2026-10-11.json)
finds the same zero run counters in ENA Browser XML, while the NCBI SRA package
XML and ENA submitted-file reports list the same three I1/R1/R2 FASTQs with
matching sizes and declared MD5 strings. Header-only checks returned HTTP 200
and matching Content-Length values. This establishes public file declarations
and metadata-level endpoint availability, but does not resolve the zero-valued
run counters or verify file contents/checksums. Both FASTQ manifests now permit
comparison of archive-declared file counts and sizes by section; those summaries
do not establish read quality or cell yield. RunInfo spot/base totals are
sequencing metadata from one source-labeled embryo at each stage, not cell
counts or biological replicates.
The [93-row per-run crosscheck](config/source_inventories/goh_2023_f137_f158_run_file_crosscheck.csv)
confirms one declared I1, R1 and R2 FASTQ for each mapped run; ERR9882663 is
the only run with zero or blank RunInfo spot/base fields. This is an archive
metadata check, not a read-level or biological comparison.

**Goh supplementary Table S6 and candidate brain-reference screen, 2026-10-11:**
the official PMC supplementary-material API returned the external-dataset
catalog. Its 51 non-empty rows include three yolk-sac references but no F158,
16099 or coronal label. The `Fetal Brain` entry reports n=26 and 1,665,937
cells, pointing to the Linnarsson lab. Those details make EGA study
EGAS00001004107 a candidate reference, not an identified match: the table gives
3-6 PCW while the atlas abstract gives 5-14 PCW, and the public EGA sample
metadata does not name F158, 16099 or coronal tissue. Its two relevant datasets
contain 448 tissue-sample records and 29 distinct public subject-ID values;
these counts are not equated with the table's n=26. The 51-row extraction and
API snapshots are pinned. No EGA files, raw reads, expression matrices or
author contact were involved.

**Braun et al. brain-atlas sample crosswalk, 2026-10-11:** the author-provided
Table S1 has 408 sample rows, 406 distinct sample IDs and 28 specimen labels.
An exact sample-ID join maps 394 distinct IDs to EGA titles and confirms the
same specimen/subject label on every matched row. It preserves two repeated
sample-ID rows (10X109_1 and 10X109_7), 12 source rows without an EGA title
match and 54 EGA sample records absent from Table S1. Two BRC2073 dorsal
midbrain rows are labeled 6.6 weeks, but neither they nor the wider crosswalk
identify F158/HDBR 16099. The S6 n=26 and S1's 28 distinct specimen labels
remain unharmonized. The source workbook and 408-row join are pinned; the
matched coronal accession is resolved separately as E-MTAB-11911 above.

The [research program](RESEARCH_PROGRAM.md) defines the scientific questions,
transition map, source/data shortlist and E1–E6 work packages. Start its E1–E3
evidence/observation/data-eligibility work now alongside M1–M2. Additional
dimensionless stress cases should not postpone qualifying a real measurement
target. New sources in that plan are candidates awaiting source review; this
roadmap revision does not promote them into the evidence ledger.

## Next research sequence — 2026-10-09

AI-assisted planning after the boundary and maternal-interface source intakes;
human scientific review remains pending. Prioritize one inspectable empirical
result, with data qualification before biological fitting. Existing M1–M6
software milestones remain supporting work.

The primary feasibility question is whether earlier maternal-interface state
adds information about later embryonic progression after accounting for earlier
embryo state and actual recipient support. Current sources do not qualify that
joint analysis. The [maternal-interface requirements](MATERNAL_INTERFACE_REQUIREMENTS.md)
and [boundary reanalysis contract](BOUNDARY_REANALYSIS_CONTRACT.md) define its
missing observations. Start with the data/coverage milestone below.

| Order | Work package | Concrete deliverable | Acceptance / stop rule |
| --- | --- | --- | --- |
| 1 | Represent cohort coverage and disposition | Extend existing observation intake with optional source-linked aggregate population/denominator metadata; keep the individual phenotype matrix separate | Preserve counted entity, original cohort label, endpoint/selection definition, denominator timing and withdrawals. Missing identity stays unqualified; aggregate counts never create specimen IDs or continuous development |
| 2 | Resolve a bounded source-mapping question | A source-located mapping/eligibility report for Hiraoka's later endpoint cohorts and Bondarenko's movement/outcome link | Authenticate recipient/embryo/experiment relationships and dispositions from inspected public records. Preserve unresolved mappings and count discrepancies. Stop each source search after its specified public records are inspected or bounded retrieval fails; author inquiry may be prepared but remains unsent |
| 3 | Qualify one measured-data question | Freeze one source-specific question card and record a source/method review decision | Joint prediction requires individual earlier observations, later outcomes, actual support, complete disposition coverage and independent grouping. If unavailable, select only an eligible descriptive endpoint/coverage question; do not relabel it as mechanism or forecast validation |
| 4 | Run the eligible bounded analysis | One receipt-bound result with source ancestry, exclusions/unavailable outcomes, simpler comparator where applicable and reproduction instructions | Use the frozen statistic/model and scope. Predictive evaluation keeps all observations from an embryo and shared biological/experimental group together and excludes future inputs. Report a negative, inconclusive or non-identifiable result explicitly |
| 5 | Revise the architecture from that result | Update the physical-niche, reconstructed-living-interface and retained-maternal-tissue comparison | Name the assumption supported or contradicted, remaining observables and next developmental transition. Early attachment, markers or morphology cannot close sustained exchange, later function or human gestation gates |

### First implementation package

Add optional cohort-coverage metadata to the existing intake contract and its
reports. Design it around source declarations rather than reconstructed units:

- Separate embryos, recipient animals, tissue fragments, imaging subsamples and
  assay events. Preserve the source's aggregation convention and labels.
- Distinguish initially included, assessed, retained, shed, assay-withdrawn,
  excluded, missing and unassessed populations. A withdrawal from longitudinal
  assessment need not mean a biological failure or excluded collected data.
- Bind every count/denominator and selection statement to its exact artifact
  and locator. Preserve the original reported percentage separately from any
  count ratio when aggregation meaning is unresolved.
- Assess count closure only when a declared common cohort, observation window
  and exhaustive, mutually exclusive disposition categories justify it.
  Otherwise report the check as unassessed; shared `Exp` labels are insufficient.
- Keep malformed inputs distinct from valid declarations with unresolved source
  identity or accounting. Report unresolved/discrepant evidence without silently
  repairing or dropping it.
- Add invented software fixtures covering withdrawals, partial coverage,
  overlapping/unqualified denominators, source-label collisions and a declared
  complete-cohort count inconsistency. Verify provenance and output exclusivity.

**Implementation progress, 2026-10-09:** the optional cohort-coverage schema and
intake/report fields are implemented. The Hiraoka candidate now records its
endpoint-specific denominators, printed 24h percentage, imaging subsets and
source-located assay-selection notes. Closure remains unassessed for those
records, and the conditional `Exp3` discrepancy is not resolved by the new
metadata. The source remains a candidate pending human review.

**Software acceptance update, 2026-10-10:** artificial fixtures now cover
withdrawals outside an endpoint denominator, partial and unresolved coverage,
reused source labels, duplicate disposition categories, a valid complete
partition, and a declared complete-cohort count mismatch. They verify that
aggregate coverage does not add specimen records or continuity links, and that
source bytes and existing output bundles remain unchanged. The full standard-
library suite passed (183 tests) in the workspace `dev` Compose service. This
completes the intake software checks; it does not qualify a biological analysis
or replace human review of the Hiraoka source transcription.

**Hiraoka eligibility screen, 2026-10-10:** a fresh receipt-bound intake at
`artifacts/hiraoka-maternal-intake-2026-10-10-v4` retained 12 aggregate coverage
rows and 18 declarations. All 11 declared local source artifacts (9,028,901
bytes) matched their recorded hashes; strict bundle verification checked all 16
declared outputs. Every coverage-closure check remains unassessed, and the
source review state remains `candidate`. The available records do not establish
same-embryo/recipient links from assay inputs to later endpoints, so paired
prediction remains non-identifiable from this public record set. This is a
machine-checked data-eligibility screen, not human source review or verified
source transcription; no author contact was sent.

**Completion:** the Hiraoka candidate can retain its endpoint-specific
withdrawal/denominator statements structurally, with the existing conditional
count discrepancy still unresolved; the Bondarenko candidate still establishes
zero boundary/outcome joins. Tests demonstrate that neither aggregate counts nor
matching labels manufacture biological identity or continuity. Existing source
bytes, original measurements and human-review status remain intact.

**Peer-review evidence-intake recheck, 2026-10-10:** the preserved Hiraoka
review file matched its recorded hash and page count. Its author responses add
constraints relevant to feasibility, including initial 24-hour PDMS use and no
observed development beyond 96 hours despite an E5.5-like source correspondence.
The separate approximate PDMS-free attachment statement cross-maps to four
biologically independent recipient-mouse samples in Supplementary Fig. 1B;
embryo denominators were initially unresolved. A publisher-listed MOESM17
workbook supplies 30 exact attached/initially-loaded formulas across the eight
Fig. 1B groups, with one value per recipient mouse according to the caption.
Corrected receipt-bound v10 records these as anonymous independent observations and adds
coverage for all eight Fig. 1B conditions. It also adds the four-per-group
autologous/allogenic Fig. 1C comparison from the same workbook. The Fig. 1C
unweighted recipient means are 93.75% and 92.22% (sample SEMs 6.25 and 4.84
percentage points); its source figure reports P=0.8532 (ns), which is not an
equivalence test. The 750 μm and 1,500 μm unweighted recipient
means reproduce the text values (95.8% and 94.8%); the reconstructed SEMs are
4.17 and 2.89 percentage points. These are descriptive calculations only. The
source says the comparison is not significant, and the analysis does not infer
equivalence, pairing, or any later outcome. The PDMS-free rows have an unweighted
mean of 36.3%, while the rebuttal’s approximate statement remains ~35%. The
MOESM17 sheet 1D adds twelve anonymous recipient-level rates over four estrogen
labels (three recipient mice each). Their unweighted means are 94.44%, 88.15%,
43.62% and 36.67%; the source reports one-way ANOVA/Tukey annotations, which
were not recalculated. The 1D data do not establish cross-condition recipient
matching or a later endpoint. Sheet 1E adds ten Natural/PMSG endometrial-condition
recipient rates (n=3 and n=7). Its workbook header spells the treatment PMGS,
while the figure says PMSG; the reported P=0.0157 unpaired-test annotation is
retained without recalculation. Receipt-bound v12 has 76 observations, 29
coverage rows and 35 declarations. Sheet 1F adds six Natural/PMSG embryo-condition
rates (n=3 per group), with the workbook `PMGS` spelling retained alongside the
figure's PMSG label; P=0.8835 (ns) is preserved as reported. Receipt-bound v13
has 82 observations, 31 coverage rows and 37 declarations. Sheet 1G adds twelve
Naturally hatched/AT-hatched recipient rates (n=6 per group); the source's
P=0.3560 (ns) test annotation is retained without recalculation. Receipt-bound
v14 covers all six MOESM17 sheets (1B-1G) and has 94 observations, 33 coverage
rows and 39 declarations. The MOESM19 Fig. 4E intake adds twelve 96h sole-culture
morphogenesis-category fractions for plastic/PDMS bottoms with/without marker
expression; the caption's n=3 samples per group lack a specified physical unit.
These data do not resolve the distinct 72h persistent-ceiling cohort. Receipt-bound
v15 has 106 observations, 37 coverage rows and 43 declarations. MOESM15 adds
30 per-recipient 24h attachment, 24–48h shedding and 48h sustention ratios from
Figure 6 I–K, preserving its later-assay exclusion notes without inventing a
withdrawal count or cross-panel trajectory. Receipt-bound v16 has 136
observations, 46 coverage rows and 52 declarations; all coverage closure checks
remain unassessed. Cycles 104–106 complete the publisher's MOESM16 Fig. 7
source-data intake across sheets 7B, 7C, 7E, 7H and 7I. This adds 30 exact
recipient-level attachment/sustention formula rows, 31 embryo-level invading-
volume values, 17 recipient-level dpc 5.5 implantation-site counts and 119
implantation-site/embryo weight values, plus 15 coverage frames. The panel H/I
group totals (57, 16, 46) do not provide a mouse-to-site crosswalk; the panel
B/C `Exp` and panel E `Embryo` labels do not support cross-panel identities.
Receipt-bound v18 has 333 observations, 61 coverage rows and 67 declarations;
all coverage closure checks remain unassessed. All 16 declared source artifacts
(9,773,188 bytes) verified locally, and strict bundle verification checks all
16 outputs. Bundle v17 remains the prior verified intake; v16, v15, v14, v13,
v12, v11, v10 and v9 are preceding receipt-bound intakes; v8 is superseded
because a row-value regression was caught before final verification. Bundles
v4-v7 remain unchanged. The v6 intake still preserves the unquantified 72-hour
persistent-PDMS failure condition without assigning it the neighboring
sole-culture n=3. Neither the peer-review file nor MOESM17 provides assay-
withdrawal counts or same-unit links to later endpoints. The scope and identity
qualifications are in the source inventory and mapping report. Cycle 110 adds
the publisher's MOESM14 Fig. 5 source workbook, fully curating sheets 5F, 5G,
5I and 5K: 31 recipient-level ratio rows and 17 embryo-level volume rows, plus
eight coverage frames. The 5G/5I notes disclose later-assessment exclusions
without counting or identifying them; 5I explicitly says its experiment count
and denominators differ from 5F. The Fig. 5 Exp labels do not establish a
recipient trajectory. Cycle 111 added MOESM18 sheets 3C and 3D: 116 exact
EPI/TE cell counts in six groups plus 12 coverage frames. Cycle 112 adds the
publisher's MOESM20 sheets 9A-9D, 9G, 9I, 9J and 9K: 60 recipient-level ratio
rows, 11 normalized COX-2 area observations and nine embryo-level invasion
volumes, plus 22 coverage frames. The raw/normalized COX-2 pairs are retained
as alternate representations, not extra samples. Panel I/J captions state
n=3 vs4 while the workbook has three formulas per group; the missing fourth
value remains unresolved. Panel 9B's histology exclusion is unquantified.
Receipt-bound v21 has 577 observations, 103 coverage rows and 109 declarations;
all closure checks remain unassessed. The eighteen declared source files
(9,804,923 bytes) verified locally, and strict bundle verification checks all
18 outputs. Bundle v20 remains the prior verified intake; v19, v18, v17, v16,
v15, v14, v13, v12, v11, v10 and v9 are preceding receipt-bound intakes. The
Cycle 113 added MOESM21 Supplementary Fig. 10B: six exact per-sample
developmental-efficiency fractions and two coverage frames. The workbook's
`Celexoxib` spelling is qualified against the figure's `Celecoxib`; the figure's
P=0.7312 (ns) is retained without recalculation. Receipt-bound v22 had 583
observations, 105 coverage rows and 111 declarations. Cycle 114 adds MOESM22
Supplementary Fig. 14B: 84 normalized per-embryo pAKT intensity values across
five captioned groups. Its 84 raw values are preserved as paired alternate
representations, not additional samples; the source normalization is checked
against the 0h raw mean, and repeated embryo labels remain group-local.
Cycle 115 adds the remaining MOESM15 Fig. 6 source sheets 6F–6H and 6M:
21 normalized molecular measurements (paired raw values remain audit-only), 13
numeric invasion-volume values, and the literal D2 `N/A` with no inferred 100
μM group denominator. The `Exp` and `Embryo` labels remain unlinked; source
test annotations were not recalculated. Receipt-bound v24 has 701 observations,
119 coverage rows and 125 declarations; all closure checks remain unassessed.
Cycle 116 corrected stale current-scope notes for MOESM16 and MOESM17 after
their audits and tests confirmed all listed source-data sheets were already
curated. Cycle 117 adds a standard-library OOXML round-trip regression for the
pinned MOESM16 workbook: all 30 formula records and all 167 panel E/H/I values
are checked against workbook cells and the 197 corresponding observation
records. Cycle 118 adds the same direct source check for MOESM15, validating
all 30 formula records, 21 paired normalized/raw measurements, 13 numeric
panel-M values and the D2 `N/A` state against the original seven-sheet file.
Cycle 119 verifies all 78 MOESM17 sheet 1B–1G formulas and cached fractions
against the candidate records and source file, retaining the workbook's PMGS
header alongside caption PMSG. Cycle 120 checks each MOESM21 Fig. 10B formula
cell, cached fraction and candidate value, along with the `Celexoxib` source
header and separate caption n versus within-sample denominator.
Cycle 121 verifies all 116 MOESM18 EPI and TE values against the original 3C/3D
source cells, row labels, group headers and candidate records. Cycle 122 checks
all twelve MOESM19 formula cells and cached fractions against their source
rows and candidate records, preserving its source unit wording and separate
96h sole-culture scope. Cycle 123 cross-checks all 80 MOESM20 records against
the eight populated workbook sheets: 60 formula rows, 11 paired COX-2 values,
and nine invasion volumes. It retains the 9I/9J n mismatch and unquantified 9B
exclusion. These verification cycles do not change the candidate dataset or
v24. Cycle 124 verifies all 84 MOESM22 normalized measurements and their paired
raw cells against the source workbook and candidate records. It also corrects
the normalization note locator to I48; the pinned sheet contains no N48 cell.
Cycle 125 adds a direct MOESM14 Fig. 5 workbook round-trip regression: all 31
recipient formula/cache rows and 17 embryo-volume values match the pinned source
cells, labels and candidate records. The 5G/5I exclusion notes are checked at
their source cells, and the separate denominator-selection record is kept
outside the 48 worksheet-derived observations. This is verification only; the
candidate intake and receipt-bound v24 do not change.
Cycle 126 adds a candidate observation intake for Eixarch et al. 2023: six
group-level rates across the three reported planned-goal groups, with separate
denominator coverage frames and no per-fetus IDs or exact goal assignments.
The 80% result for the 48–168 h group is not promoted to a seven-day survival
rate. Receipt-bound v1 validates the six records and three coverage frames;
all coverage checks remain unassessed. The EP09.22 poster source page is listed,
but its in-browser PDF frame remains blank, so its separate duration
transcription stays unresolved and visually unverified.
The twenty declared source files (9,827,080 bytes) verified locally, and
strict bundle verification checks all 16 generated outputs. Bundle v23 remains the prior
verified intake; v22, v21, v20, v19, v18, v17, v16, v15, v14, v13, v12, v11,
v10 and v9 are preceding receipt-bound intakes. The intake remains descriptive;
no later outcome or cohort closure is
established.

Cycle 127 extends the Eixarch intake with Table 1's three group mean total
support durations: 1.48 ± 0.78 h, 11 ± 3.42 h, and 72.6 ± 12.9 h for the
1–3 h, 4–24 h, and 48–168 h planned-goal groups. The full text's §2.2.6
confirms continuous table values are means ± SEM. Three source-linked
group-summary observations carry those SEMs and group denominators; no
individual durations are reconstructed, and all coverage-closure checks remain
unassessed. Receipt-bound v2 contains nine observations and three coverage
frames; strict verification checks all 16 declared outputs. Source review
remains candidate, with no post-support outcomes added.

Cycle 128 adds two more Results-level counts for the 48–168 h group: four of
ten lambs had complications after the first day (two flow-interrupting
cannulation accidents and two sepsis cases), and three had hydrops at
experiment end. The candidate preserves them as distinct adverse outcomes;
they may overlap, and the paper supplies no animal-level crosswalk. Receipt-
bound v3 contains 11 observations and three coverage frames; all coverage
closure checks remain unassessed and strict verification checks all 16 declared
outputs. This records reported adverse events, not their causal relationship
to system components or long-term consequences.

Cycle 129 adds Table 1 pH and circuit flow at 30 minutes after connection for
all three groups: pH 7.20 ± 0.06, 7.31 ± 0.04, and 7.33 ± 0.02; flow 45 ± 24,
138 ± 23, and 196 ± 13 mL/kg/min. The table footnote defines values as means
± SEM and marks the long-group flow value ** (p<0.05 versus the 1–3 h group);
the marker is preserved without recalculating the test. The intake notes that
Table 1 does not state a separate assessment n for these measurements or
provide exact per-fetus 30-minute readings. Receipt-bound v4 contains 17
observations and three coverage frames; source review remains candidate.

Cycle 130 adds Table 1 whole-experiment group summaries for pH, lactate, heart
rate, and circuit flow across all three groups. Figure 3 defines the plotted
points as per-animal means over each whole experiment; the intake retains only
the Table 1 group mean and SEM, with source numeric lexemes, units, and the
lactate ** annotation preserved. These are not longitudinal trajectories, and
the source does not state a separate assessment n for each row. Receipt-bound
v5 contains 29 observations and three coverage frames; source review remains
candidate.

Cycle 131 adds nine transition-context summaries from Table 1: EXIT-surgery
duration, cannulation duration, and fetal heart rate before connection for all
three groups. It preserves means ± SEM, units, exact numeric lexemes, and the
source's qualitative no-difference statement without creating p-values. These
values are group context, not operating specifications or individual data.
Receipt-bound v6 contains 38 observations and three coverage frames; source
review remains candidate.

Cycle 132 adds the remaining Table 1 30-minute physiology measure: heart rate
after connection (134 ± 33, 205 ± 8, and 182 ± 8 bpm for the three groups).
It is recorded as a group mean ± SEM, with the timepoint and unresolved
row-specific assessment n retained. The 30-minute set now includes pH, heart
rate, and circuit flow. Receipt-bound v7 contains 41 observations and three
coverage frames; source review remains candidate.

Cycle 133 adds the nine Table 1 cannulation-technique count/percentage cells
across the three planned-goal groups. The paper's technique labels and cell
text are preserved, including the abbreviation `ST`; no animal-level technique
assignment is inferred. The table does not establish a complete mutually
exclusive partition, so coverage closure remains unassessed. Receipt-bound v8
contains 50 observations and three coverage frames; source review remains
candidate.

Cycle 134 cross-checks the abstract's cannulation-complication rates against
Table 1's “Complications surgical procedure” counts: 6/8, 5/10, and 0/10
reproduce 75%, 50%, and 0%. A regression ties each source-table cell to its
existing abstract-derived rate record, keeping the distinct source labels
visible and preventing duplicate outcome records. Numeric agreement does not
prove identical complication coding or category completeness. Receipt-bound v9
retains 50 observations and three coverage frames; source review remains
candidate.

Cycle 135 audits all specific-complication cells in Eixarch et al. Table 1.
The 1–3 h bubble, decannulation and vessel-lesion percentages agree
arithmetically with group n=8. The 4–24 h bubble and vasospasm cells imply n=7,
but the group header gives n=10 and neither §2.2.6 nor the table footnote
reports row-specific denominators. The Results text does not resolve this.
Printed dashes are retained without converting them to zeros, and the rows are
not assumed to be exclusive or exhaustive. No uncertain-denominator cells are
added as observations; the candidate remains at 50 records. Receipt-bound v10
retains the existing three coverage frames and candidate review status.

Cycle 136 links the existing four-of-ten late-complication record to Table 1's
“Complications after 24 h survival #” cell (4 [40%]). The table footnote limits
that row to fetuses with >24 h survival, while the Results describe four of ten
as having complications after the first day. Both source formulations remain
visible in the observation locator and inventory; no outcome record is
duplicated and no animal identities are inferred. Receipt-bound v11 contains
the same 50 observations and three coverage frames.

Cycle 137 screens whether an inspectable public supplement or dataset can
resolve the n=7 complication percentages. The article PDF says “Data
Availability Statement: Not applicable” and has no Supplementary Materials
section; the inspected PubMed surface lists full-text links but no data item,
and bounded title/DOI queries surfaced no article-specific data file. The
publisher HTML page could not be fetched in this run, so this is a bounded
search result, not proof that no other copy exists. No author was contacted;
the denominators stay unresolved and the v11 dataset remains unchanged.

Cycle 138 records the Discussion's statement that 15 in-vivo experiments were
required for reproducible cannulation after ex-vivo team training. The paper
reports 28 transfers split into groups of 8, 10, and 10 but does not map the 15
experiments to those groups or define the reproducibility threshold. The count
remains an unmapped learning-curve statement, not a 15/28 rate or outcome.
No new observation is added; the v11 aggregate candidate stays at 50 records.

Cycle 139 links the Methods' successive cannulation-technique refinements with
Table 1's group technique counts and procedure-complication cells. The
technique mix and complication rate co-vary across the three learning-curve
groups, but the article provides no individual technique-to-outcome cross-tab
or randomized assignment, and group sequence is entangled with technique.
Record this only as a non-causal group-level co-trend; do not infer a technique
effect or add observations. The v11 candidate remains at 50 records.

Cycle 140 qualifies the Eixarch 2023 goal-attainment rates against §2.2.5's
statement that fetuses were euthanized after reaching goal. The percentages and
group denominators imply counts of 2/8, 7/10, and 8/10 goal-reaching
experiments, and thus implied planned-end euthanasia counts, but euthanasia
dispositions are not separately enumerated. The complementary counts are not
classified as deaths; the paper's first-group death statement is qualitative
and lacks a complete disposition breakdown. Animal IDs and exact goal
assignments remain unavailable. This is a crosswalk only; v11 remains at 50
observations.

Cycle 141 records an internal goal-band label variation in Eixarch et al. 2023.
The Abstract, Methods, and Table 1 header identify the middle group as 4–24 h;
one Results sentence and the Table 1 statistical footnote use 3–24 h. Retain
4–24 h as the repeated cohort label and preserve the other references without
silently correcting them or reinterpreting significance annotations. No data
or observation count changes; v11 remains at 50 records.

Cycle 142 tightens Guo et al. 2026 Fig. 4E/F sample-size qualification. The
caption states n ≥ 4 but does not define the unit counted or exact group n; the
selected workbook contains 7/4/5 percentage-valued cells per condition. Treat
those as source-cell counts, not biological denominators, and retain the
unknown embryo numerators, starting denominators, attrition, and cell-to-unit
mapping. The 32-value candidate intake is unchanged; no fit or causal estimate
is made.

Cycle 143 visually inspects the publisher's Figure 4 axes and captions. Panels
A/D label stress-relaxation half-time in seconds; panel C labels Young's
modulus in Pa on a logarithmic axis. Panel A's caption explicitly calls its
10/9 values independent experiments; panels C/D provide n=10 and n=5 without
defining the counted unit. These axis labels qualify units but do not resolve
loading history, normalization, sample hierarchy or the mechanics-to-embryo
map. Mechanical values remain excluded from biological observation intake.

Cycle 144 records measurement context from the Methods. The rheology section
specifies fixed 1% strain, stress normalization to the initial maximum, and a
three-element generalized Maxwell–Wiechert fit; the nanoindentation section
specifies a 4 s load, 40 s hold and 4 s unload, with three experiments per
sample. Figure 4D names nanoindentation, but point-to-sample mapping remains
absent. Figure 4C says nanoindenter, while the separate AFM/Hertz modulus
description is not explicitly mapped to that panel. Preserve this method
boundary; do not fit or merge values across panels.

Cycle 145 compares source numeric lexemes across the inspected mechanical
condition columns. Five values in the Fig4D 40-MG column exactly match five
lexemes in the Fig4A 40-MG column, spanning six Fig4A cells because one value
repeats there. The audit records both sets of locators and the ambiguity: the
source does not say whether these are shared specimens, remeasurements, reused
values or coincidence. Do not join them or count them as independent evidence
without sample/run identifiers.

Cycle 146 pins the publisher's Supplementary Information PDF and qualifies the
`Sup 10 I` workbook sheet against Supplementary Fig. 10I: its rheometer stress
profiles use a linear Time (s) axis and dimensionless σ/σ₀ response
normalized to initial stress. The sheet title and three condition headers
match the panel and legend. Panel J reports mean ± s.d. with n=3 independent
experiments for half-time summaries, but no source IDs map those repeats to the
profile rows or show whether each trace is individual or aggregated. The audit
now records the axis units and links the supplement hash; the profiles remain
outside observation intake and fitting.

Cycle 147 qualifies the source time grid and records nonmonotone points without
changing the curves. The 200 coordinates are unique and strictly increasing
from 5.0 to 1000.249 s; there is no source row at zero seconds. All three
profiles first record 1.0 at 5 s, and the source arrays contain 49, 30 and 78
adjacent increases for 40-MG, 40-MGN and 40-MGT. This is not a replicate
estimate or a fit. Keep the traces as reported and do not backfill, smooth or
force monotonicity.

Cycle 148 extends the audit to the `Sup10J` source tab for Supplementary Fig.
10J. It contains three relaxation half-time cells for each of 40-MG, 40-MGT
and 40-MGN, matching the caption's n=3 independent experiments. The audit
transcribes the nine source lexemes separately and reconstructs means and
sample SDs as an arithmetic check. There are still no experiment IDs, row-wise
pairing across conditions or trace-to-summary links, and these mechanics
values do not enter biological observation intake.

Cycle 149 compares the 40-MG half-time scale across Figure 4A, Figure 4D and
Supplementary Figure 10J. Figure 4A's nine cells span 5.834–12.986 s (mean
9.903 s), Figure 4D's five cells span the same range (mean 9.280 s), and the
three 10J cells span 75.018–80.019 s (mean 78.352 s). The 10J mean is about
7.9× and 8.4× the Figure 4A and 4D means. Figure 4D identifies
nanoindentation, 10J identifies a rheometer, and Figure 4A's method mapping
remains unresolved. Record this as a source-reconciliation flag, not a direct
contradiction; require protocol and run/sample hierarchy before comparison or
pooling. These mechanical values remain outside developmental intake and fit.

Cycle 150 rechecks the pinned article text. Figure 4A's caption calls the
endpoint a characteristic relaxation timescale for E5.5 decidua and 40-MG but
does not name an assay or instrument; the Results text does not assign one.
Figure 4D's caption explicitly names nanoindentation, and Supplementary Fig.
10J's caption names rheometer. The article describes both rheology and
nanoindentation protocols but leaves Figure 4A's assignment open. The audit
manifest hash-checks the pinned article HTML and records the reviewed Results,
caption and Methods locators. Preserve this source-text boundary and do not
infer a method from neighboring panels.

Cycle 151 checks the raw Supplementary Fig. 10I response profiles against the
Sup10J source-cell half-time means without fitting or assigning runs. The first
observed downward σ/σ₀=0.5 brackets are 80.018–85.020 s (40-MG),
145.035–150.036 s (40-MGT), and 160.038–165.041 s (40-MGN); the 10J means are
78.352, 145.035, and 150.037 s. Their distances from the brackets are 1.666,
0, and 10.001 s. This is broad panel-level timing consistency only: Fig. 10I's
curve aggregation is unstated and no IDs map profiles to the three independent
Fig. 10J experiments. The audit retains adjacent raw cells and does not
interpolate, smooth, or fit.

Cycle 152 screens the public sequencing accessions and linked analysis code
for Guo et al. 2026. PRJCA004049's displayed sample inventory includes older
PD/PDCO/E4.5 single-cell labels and bulk timepoints, while the article cites it
for three E8.5 and three IVC-day-9 embryos; PRJCA052100 lists 3/4/4 samples for
MG/MGT/MGN while the Methods sentence names three embryos each for MG/MGT.
The GitHub repository tracks scripts and metadata but omits several matrix,
reference and intermediate files read by the script. Record these as
unresolved provenance and reproduction gaps, not as proof of incorrect
deposition. Add no observations or fits. See
[`GUO_PUBLIC_DATA_SCREEN_2026-10-10.md`](GUO_PUBLIC_DATA_SCREEN_2026-10-10.md)
and the structured screen in
[`growing_interface_2026.json`](config/source_inventories/growing_interface_2026.json).

Cycle 153 checks whether the code repository narrows the accession ambiguity.
It does: code.Rmd maps E8/E6/E8L to E8.5/E6.5/D9, and the 39,832-row meta.txt
has group counts 14,761/14,315/10,756, exactly matching the 2026 Results cell
counts. This confirms processed-group identity at the cell-count level, not
raw archive-run provenance or embryo-level independence. The Results include
E6.5 scRNA-seq, while the library-generation Methods paragraph does not say
where E6.5 came from. Next, test public archive/sample/run records for a
run-to-matrix and embryo-unit crosswalk; retain this as a data-access gate, not
a reason to add unlinked observations.

Cycle 154 follows the GSA archive linked from PRJCA004049. Its listed
single-cell samples are `PD_SC`, `PDCO_SC`, and `E45_SC`, each with one
BioSample/experiment and five run accessions; its E8.5 samples are explicitly
bulk-labeled, and no D9 scRNA-seq BioSample appears in the displayed project
inventory. This sharpens the issue to an unresolved candidate accession-to-
assay coverage gap: the code's processed-cell counts match the article, but
the raw-run records do not identify the E8.5/D9 matrices. Do not infer the
deposit is erroneous or absent elsewhere. Next, search public supplementary
and repository metadata for an explicit matrix-to-run or E6.5 reference-source
crosswalk; if none exists, freeze this as a documented non-reproducibility
boundary without author outreach.

Cycle 155 searches the pinned supplementary PDF, publisher workbook inventory,
and all tracked analysis-repository text for transcriptomic sample/run IDs.
Supplementary Fig. 7 names the E6.5/E8.5/D9 groups, but the text search finds
no PRJCA/SAMC/CRX/CRR identifiers; the 55-sheet workbook has no Fig. 3-labeled
worksheet, and the three tracked repository files contain no accession IDs.
This bounded public-material search finds no matrix-to-run, embryo-unit, or
E6.5 reference-source crosswalk. Preserve the gap without promoting cells to
independent-unit observations or contacting authors.

Cycle 156 compares the repository's E6/E8 barcode strings with the stage-
matched Pijuan-Sala et al. E-MTAB-6967 atlas metadata. It finds zero exact
matches, including after removing the terminal Cell Ranger `-1`; this weighs
against direct reuse of those atlas cell records. It does not establish new
sequencing or rule out another reference or processing route, so the E6.5
source stays unresolved and no cells are promoted. Next, inspect official
metadata for other reference sources or a matrix/run bridge, keeping each
candidate separate from Guo's reported groups.

Cycle 157 screens GEO's GSE100597 and GSE109071 as possible E6.5 reference
sources. Both include E6.5, but neither inspected record maps its samples or
cells to Guo's Cell Ranger matrices. GSE109071 is documented as Smart-seq2
and ends at E6.5; the Guo library-generation paragraph names 10x Chromium for
E8.5 and D9 but does not describe E6.5. These records are candidate references,
not a source crosswalk. Keep the E6.5 matrix unassigned and add no observations.
Next, use the 2026 paper's own reporting and accession metadata to test whether
its stated three-embryo E6.5 group can be reconciled with the listed deposit.

Cycle 158 downloads the `CRA004601.xlsx` workbook linked from the GSA archive.
The 13,792-byte file has `Sample`, `Experiment`, and `Run` sheets, each with
only one `ID` cell; preserve it as an empty export rather than treating it as
evidence that the archive has no further metadata. The landing page itself
lists 12 BioSamples and their linked experiment/run records, but those aliases
do not identify the 2026 E6.5/E8.5/D9 scRNA matrices. No observations are
promoted. Next, compare the archive's visible sample aliases with the earlier
published experiment and retain the group-to-run boundary unless a direct
bridge appears.

Cycle 159 checks the linked 2022 paper's later Figure 6 single-cell dataset.
That paper reports 10x Genomics for natural E6.5/E8.5 and cultured PDCO/PD
day-8–10 embryos, with 14,935 E6.5 and 15,116 E8.5 filtered cells. These are
near but unequal to the 2026 counts of 14,315 and 14,761, so they identify a
strong candidate source/comparison lead, not cell reuse. The paper's data
statement gives no public accession; its currently displayed PRJCA004049
single-cell BioSamples describe day-2 Drop-seq groups and E4.5 Drop-seq. No
barcodes or sample/run crosswalk bridge the two papers, and D9 remains
unexplained. No author contact or observations. Next, search public
supplementary/source-data and repository records for a cross-paper barcode or
archive link before revisiting raw-run attribution.

Cycle 160 checks the 2022 paper's own Methods and its publisher's supporting
file list. The single-cell Methods describe only the earlier day-2 PD/PDCO and
E4.5 comparison, not the Figure 6 10x workflow. Wiley lists one Supporting
Information PDF and seven movies, with no separate spreadsheet/source-data
file. The PDF download returned HTTP 403 and its contents were not inspected;
this bounds the public-material screen without implying the information is
unavailable elsewhere. Preserve the candidate status and no-contact boundary.

Cycle 161 distinguishes the 2022 paper's two single-cell analyses. Figure 3
reports 518 day-2 PD/PDCO and natural E4.5 cells, matching the group labels
and Drop-seq descriptions of PRJCA004049's three scRNA BioSamples at the
condition level. Figure 6 separately reports the later 10x E6.5/E8.5/PDCO/PD
groups; no cell-level or sample/run bridge links those profiles to the three
listed BioSamples. A bounded search by paper title, stages, and platform found
no second directly relevant official archive accession. This narrows the
likely scope of the old deposit but is not proof that no other record exists;
do not map the 2026 cells or add observations.

Cycle 162 returns to developmental outcomes. The 2022 PDCO paper reports
two-cavity formation (36 ± 6% at IVC day 3), egg-cylinder formation (47 ± 15%
at day 5), and a heartbeat-like stage (11 ± 5% across days 8–10). Figure 3
states 71 PDCO and 64 PD embryos, but does not supply stage-specific
denominators or per-embryo outcomes; no event counts are inferred. Figure 5
reports marker/morphology samples through day 10, including beating aggregates
and neural-/heart-like structures. Treat this as mouse early-organogenesis
evidence, not functional circulation, birth, or postnatal health. Record the
qualification without promoting observations or human-feasibility claims.

**Eixarch et al. 2023 full Table 1 cell reconciliation, 2026-10-11 (Cycle 293):** crosswalk all 60 cell positions in the publisher PDF against the candidate and source inventory. Preserve 51 reported values, 7 dashes, and 2 N/A states; link 42 table observations to group coverage, cross-check three complication cells against existing abstract summaries, keep five denominator-ambiguous complication values inventory-only, and link the after-24-hour cell to the existing Results count. No observations were changed. See the [cell crosswalk](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle293/table1-cell-crosswalk-cycle293.csv) and [receipt](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle293/table1-cell-reconciliation-cycle293.json).\n\n**Eixarch et al. 2023 reverse correction-link search, 2026-10-11 (Cycle 292):** use Crossref’s documented reverse updates filter against the article DOI. It returns zero update-linked records; preserve this as a bounded metadata result, not proof of no correction, because Crossref relations are deposited metadata and the publisher-notes page remains inaccessible. Leave the Table 1 denominator mismatch unresolved and add no observations. See the [screen receipt](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle292/correction-reverse-link-screen-cycle292.json).\n\n**Eixarch et al. 2023 Table 1 visual denominator check, 2026-10-11 (Cycle 291):** render and inspect the publisher PDF at printed p. 5. Confirm the middle-group bubbles 1 (14.3%) and vasospasm 4 (57.1%) cells; neither has a row-specific marker, while # is attached only to the separate after-24-hour complications row. The visual check confirms transcription but does not identify a denominator; retain the mismatch as unresolved and add no observations. See the [assessment](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle291/table1-visual-assessment-cycle291.json) and [render](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle291/publisher-page5-table1-render-300dpi.png).\n\n**Eixarch et al. 2023 correction-notice metadata screen, 2026-10-11 (Cycle 290):** PubMed has no Comments/Corrections entry and exact-DOI/title correction searches return zero; Crossref relation/update-to fields are empty. The MDPI article-notes route returned HTTP 403, leaving publisher notices unchecked. Keep the Table 1 denominator issue unresolved and the candidate values unchanged. See the [screen receipt](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle290/correction-notice-route-screen-cycle290.json).\n\n**Eixarch et al. 2023 public repository-route audit, 2026-10-11 (Cycle 289):** search DataCite, Zenodo, Figshare, and OSF metadata APIs for a linked dataset or supplement. No target record was identified in the inspected results. Zenodo exact-DOI returned HTTP 500; Figshare exact/title/author queries produced capped broad results, and two topical artificial-placenta records were unrelated papers. Keep the result bounded, preserve the 50-observation candidate unchanged, and make no author contact. See the [route summary](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle289/repository-route-summary-cycle289.json) and [crosswalk](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle289/repository-route-crosswalk-cycle289.csv).\n\n**Eixarch et al. 2023 Table 1 complication-denominator audit, 2026-10-11
(Cycle 288):** the 4–24 h group is n=10, but its bubbles `1 (14.3%)` and
vasospasm `4 (57.1%)` cells both imply denominator seven. The generic footnote
only defines means ± SEM or n (%); the `#` note applies to a later row about
complications after 24 h. Methods, Results, and Discussion do not define a
seven-fetus risk set for these cells. Preserve both printed counts and
percentages; do not assign the implied denominator or individual events. See
the [audit receipt](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle288/table1-complication-denominator-audit-cycle288.json)
and [source inventory](config/source_inventories/fetal_ovine_support_transition_2023_2026.json).

**Eixarch et al. 2023 Figure 3 visual assessment, 2026-10-11 (Cycle 287):**
retrieve the official publisher PDF, render printed page 6 at 300 dpi, and inspect
Figure 3. The caption confirms each dot is an animal-level whole-experiment
mean, but points have no labels and some overlap; the figure does not support a
reliable exact point-to-value transcription or cross-panel unit mapping. Keep
the existing 50-observation candidate unchanged and classify Figure 3 as
plot-only evidence. See the [visual assessment](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle287/figure3-visual-assessment-cycle287.json),
[publisher PDF](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle287/eixarch2023-publisher-version.pdf),
and [candidate intake](config/observations/eixarch_2023_support_outcomes_candidate.json).

**Eixarch et al. 2023 official-source pin, 2026-10-11 (Cycle 286):** pin
NCBI PMC EFetch XML for the 28-lamb learning-curve paper, verify the CC BY 4.0
front-matter license, and inspect the article's data/supplement route. The PMC
Data Availability Statement says “Not applicable”; the XML has no
supplementary-material node. Figure 3 shows per-animal whole-experiment means
as unlabeled points, without exact value rows or persistent animal IDs. The
existing 50-observation, three-coverage candidate therefore gains verified
source bytes but no new biological values. This bounded article-surface screen
does not establish global data absence. See the [candidate intake](config/observations/eixarch_2023_support_outcomes_candidate.json),
[source inventory](config/source_inventories/fetal_ovine_support_transition_2023_2026.json),
and [Cycle 286 receipt](artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle286/cycle286-receipt.json).

**Church et al. Table 1 case-row intake, 2026-10-11 (Cycle 285):** the
NCBI PMC full-text XML is pinned and hashed. All five AP Lamb rows are now
transcribed into 35 source-located candidate observations, with one cohort
coverage record and nine same-row phase links. The 26-hour MV-alone value and
mucus-plugging/acute-respiratory-failure narrative for AP Lamb 3 remain separate
and untimed relative to one another. A denominator check finds the printed
37±36-hour AP+MV summary matches the first four row values under mean/sample-SD
arithmetic, while all five row values average 52.6 hours; the source does not
identify the statistic-specific denominator or the excluded case. The five
animals are a transition subset within the larger n=12 project, with a
potential stability-selection rule not mapped case by case. This remains a
candidate intake with human review pending, terminal follow-up only, and no
claim of healthy development. See the [candidate intake](config/observations/church_2018_lamb3_transition_candidate.json),
[Table 1 crosswalk](artifacts/fetal-ovine-transition-2026-10-11-cycle285/church2018-table1-crosswalk-cycle285.csv),
and [duration check](artifacts/fetal-ovine-transition-2026-10-11-cycle285/duration-aggregation-check-cycle285.json).

**EXTEND early-death crosswalk, 2026-10-10:** a primary-text recheck resolves
the Results narrative's duration/cause pairs for the four premature deaths at
3, 6, 7, and 8 support days. It preserves the 6-day air-embolism explanation as
suspected and the proposed trigger for the two venous spasms as likely. These
event tuples do not supply persistent identities linking the deaths to Table
2's ten numbered analyzed animals, so they remain source-level death events,
not reconstructed specimen rows. The structured inventory now carries the
crosswalk and identity boundary. No author was contacted.

**EXTEND Table 2 animal-level intake, 2026-10-10:** seventeen source-reported
fields were transcribed for the ten numbered analyzed animals in a 170-record
candidate, including sex, cannula sizes, growth rate, terminal organ weights,
brain ratios and transfusion count. The blank Animal 3 brain and derived-ratio
cells remain missing. The 16-day Table 2 run for Animal 5 still conflicts with
the Results sentence that describes the other nine animals as ending at 10–14
days apart from Animal 2's 21-day extension. The age difference and group mean
support retaining the Table 2 value; a bounded exact-title/DOI search found no
correction notice, which is a search boundary rather than proof none exists.
Brain MRI/histology remains aggregate n=6 with no complete animal-ID mapping.
Table 1 comparison frames now preserve five extremely preterm controls, ten
historic late-gestation EXTEND animals, four late-gestation controls (MRI and
histology n=3), and the three-animal IUGR pilot. Table 2 comparator means are
group-only without row-specific denominators; the IUGR pilot is not part of
statistical comparisons; its three labeled rows now have a separate
[30-record candidate intake](config/observations/peers_2024_iugr_table2_pilot_candidate.json)
with seven checked numerical summaries. They are not joined to the ten numbered
observations.
The [candidate intake](config/observations/peers_2024_extend_table2_candidate.json)
is not a raw-data release or post-support health dataset.

Fourteen numerical group summaries are reconstructed in the
[summary ledger](config/source_inventories/peers_2024_table2_summary_reconstruction.csv).
Thirteen means are within source precision; the rounded brain-to-liver mean
remains unreproduced after applying the printed outlier exclusion. Twelve SEMs
reproduce; age-at-cannulation and cannulation-weight SEMs do not reproduce from
rounded cells. All ten growth-rate values reproduce 40.3 ± 5.4, although a
footnote says Lamb 1 was excluded; excluding that row yields 36.947 ± 4.719.
Preserve both statements. Transfusion counts show six of ten animals with at
least one; these describe care exposure. Terminal organ weights and ratios do
not establish function or post-support health.

### Bound the next public-data search

For Hiraoka, inspect the publisher peer-review material and declared sequencing
sample metadata only for explicit cohort/recipient/assay-withdrawal mappings and
the recorded source-count questions. Do not assume molecular samples provide
later phenotype records. For Bondarenko, inspect bounded Figure 1 archive
metadata and selected relevant tabular members if retrieval allows it; do not
download the large image archive merely to continue searching. Record the scope
and outcome of each inspection.

Missing source identities or measurements remain an eligibility finding. Prepare
a precise unsent data inquiry if public records do not resolve them. Any actual
author contact needs separate user authorization. Human source/method review is
required before the biological fit; software/data-contract work can proceed
while that review is pending.

The first result may therefore be a reusable coverage/non-identification report.
It must state exactly what information is missing and which claim cannot yet be
tested. A source-qualified paired-morphology description is a separate fallback,
with its selected population and unresolved generalization clearly retained.

**Inspection outcome (2026-10-09):** the [bounded source-mapping report](SOURCE_MAPPING_2026-10-09.md)
records the publisher peer-review file, all current Hiraoka GEO series/sample
metadata, and a range-limited inspection of Bondarenko's Figure 1 ZIP directory
and its two small tabular members. Hiraoka's sequencing inputs have source-level
pool and donor/recipient counts, but no individual keys linking them to Figure 5
later endpoints; the explicit assay-withdrawal counts and recorded count questions
remain unresolved. Six new cohort-coverage entries retain the separate scRNA-seq
embryo and tissue-site input populations in the candidate intake. Bondarenko's
Figure 1 tables add stage-labelled counts/dimensions without identity keys, so
the Figure 6 movement-to-outcome join remains unestablished. Neither paired
question is eligible for analysis. The inquiry in the report remains unsent;
the [candidate descriptive Hiraoka coverage card](HIRAOKA_COVERAGE_QUESTION_2026-10-09.md)
is prepared, and human source review is still required before selecting a result.

This sequence supplies research software and analysis requirements, without a
biological procedure, fabrication plan or operating specification. Complete
healthy human embryo-to-birth support remains unestablished.

**Human functional-source intake, 2026-10-10:** Antich et al. reports
separate trophoblast uptake, receiver-side nutrient measurements and
transporter activity in a human placental model. The bounded audit enumerated
all 16 publisher supplements and checked GEO/PRIDE file roles; neither the
supplements nor repository manifests provide a replicate-by-time functional
table or a functional replicate-to-source map. Retain the study as a
descriptive candidate only. The next transport-data milestone is to find an
existing source with measured concentrations, volume/recovery accounting and
independent-unit keys, or document that the candidate supports only a
figure-level description. No biological fit follows from the current files.

The [Roelofsen perfusion intake](COLLECTION_ACCOUNTING.md) is a stronger
machine-readable trace candidate, with native percent-of-dose trajectories
and a published correction for analyte removed during sampling. The S9/S10
transfer tables do not contain original concentration records or source-unit
links, and the analytes are not fetal nutrient adequacy measures. Check for any public
ancillary records that resolve those specific gaps; otherwise keep it to a
source-level percent-of-dose description and defer a dimensional fit.

**Supplementary object audit, 2026-10-10:** a fresh publisher retrieval matched
the pinned DOCX exactly. Objects 2/S4 and 3/S5 expose twelve native worksheets,
including thalidomide stability controls, source-titled percent-of-initial-dose
series, log transforms and Prism fit outputs. The new inventory preserves
figure/table locators, shapes and CSV hashes, while keeping transformed and
fitted values out of biological observation intake. The stability objects do
not provide unit-qualified placental-transfer concentrations, run-linked
volume histories or donor linkage. A field matrix separates published
method-level aliquot sizes and correction equations from the missing per-run
measurement histories. It also records that ex-vivo Papp depends on an average
term-placenta/cotyledon area scaling assumption rather than a measured area for
each perfused cotyledon. See the [accounting audit](COLLECTION_ACCOUNTING.md),
[auxiliary worksheet inventory](config/source_inventories/roelofsen_auxiliary_table_inventory.csv)
and [mass-balance field matrix](config/source_inventories/roelofsen_mass_balance_field_matrix.csv).
The citation chain and candidate population-level area-uncertainty source are
documented in the [surface-area lineage note](ROELOFSEN_SURFACE_AREA_LINEAGE_2026-10-10.md).
The audit found an apparent 100-fold unit discrepancy: Methods print 3371 dm²,
while Discussion's 11.8 m² divided by 35 implies about 3371 cm². The published
Table 1 reports ex-vivo Papp in cm/s, but the available supplement and tables do
not resolve which physical area entered the calculation; a bounded publisher/
PubMed title- and DOI-search and targeted institutional-repository/data-record
searches surfaced no correction or separate ex-vivo calculation dataset. No
correction is applied. The Table 1 mean±SD cells and the ten source-reported
cross-model ratio cells have now been transcribed into separate source-cell
inventories with exact source text, parsed values, source locators,
assay-family caption N, times and compound-addition conditions. The printed
ratios are kept distinct from the conditional 100× what-if values, and both
inventories remain descriptive and outside model inputs. Those fits still do not provide area measurements for the tested
cotyledons. Table 1 ex-vivo/BeWo Papp ratios are 0.34–0.54 for mixture-tested
BeWo compounds and 0.31–0.75 for separately tested compounds; if the larger
area was actually used, those ratios would conditionally become 34–54 and
31–75. This materially changes the quantitative comparison, but no correction is justified
without the calculation record. Although the 2017 supplement omits the numerical age unit, a later
Dallmann et al. methods paper describes a maximum fertilization age of 38
weeks; the 2017 mean fit at x=38 gives about 11.81 m², consistent with the
rounded 11.8 m² input. This is a model-lineage check, not a cotyledon-specific
observation or a cohort-matched area distribution; no cotyledon sensitivity
range has been calculated. A separate photographed birth cohort reported
3–37 visible maternal-surface cotyledons; its definition does not directly
match the transport-model denominator, so it is retained only as a warning
that count varies and must be operationally defined.

**Human concentration-source intake, 2026-10-10:** the pinned Mathiesen et al.
term-placenta workbook adds cell-located maternal/fetal nM reservoir readings
for five analytes and 22 numbered perfusion runs. The source-specific
[qualification](MATHIESEN_PERFUSION_QUALIFICATION_2026-10-10.md) and
[inventory](config/source_inventories/mathiesen_2020_placental_perfusion.json)
retain run-map review status, source-window flags, 282 blanks and their uneven
distribution, and the unreconciled 48→43→26→15 selection funnel versus the
22-run workbook. A bounded tryptophan concentration-ratio reproduction is
receipt-bound; it is not a flux estimate. Both strict bundle checks passed.
This is a stronger candidate for a source-cell descriptive report, but remains
ineligible for dimensional transport fitting because the inspected records do
not contain sample-volume/removal histories, inventory/recovery, calibration
and uncertainty, or original instrument records. Retain the source as a
candidate and do not promote its values to the evidence ledger or fit a
biological model. An independent human check of the transcribed run map and
source labels remains a gate before promotion. The public S3 table adds a
candidate `nr` key set matching Table 1 IDs 1–22, but does not explicitly define
the crosswalk; the machine audit records the match and makes no join. S2–S4 do
not provide the numerical volume/removal records described in Methods. No
author contact is needed for this public-record qualification and none was
sent.

**Cited validation evidence, 2026-10-10:** public abstract review of the two 2010
method papers and the 2012 NewGeneris cross-laboratory meta-analysis adds
method-quality context, not a route to whole-gestation evidence. The earlier
work reports low success yield and one model-compound curve-fit failure; the
meta-analysis reports between-study/lab variation in its antipyrine reference
and only partial variance correction after normalization. No row-level
validation datasets were found in the bibliographic records inspected; full
texts/supplements for the 2010 papers remain unreviewed. Additional 2015 and 2017 reports give
different single-center yield estimates, which are retained separately rather
than treated as a universal perfusion success rate. Keep independent human
source review as an open gate; continue with public-record source discovery
without contacting authors. A 2022 standardization rationale identifies
candidate metadata dimensions and proposes a multi-centre pilot; no completed
pilot result or validated reporting checklist was located in the reviewed
record, so those dimensions remain prompts rather than mandatory fields.
The 2024 literature review covers a 2000–2022 subset of 135 fixed-setup,
full-term drug-transfer studies and finds substantial heterogeneity; 20.6% of
protocol parameters remained missing even after checking cited protocols, and
some referenced methods conflicted. Its supplementary tables hold extracted
setup metadata but not transfer outcomes. The review does not resolve whether
the proposed pilot completed after its search cutoff, and its drug-transfer
scope is not poolable with the 2020 hormone/amino-acid study. The published
setup tables yielded the candidate, non-standard vocabulary in
[PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md](PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md).
Their source notes distinguish primary-report values from values recovered
from cited methods and preserve ambiguous missing/inconsistent states.

**Availability crosswalk, 2026-10-10:** the candidate vocabulary is applied to
the Mathiesen 2020 article and inventoried supplements in the
[field-by-field report](MATHIESEN_PERFUSION_AVAILABILITY_CROSSWALK_2026-10-10.md)
and [machine-readable crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).
The record separates reported concentrations, described measurements without
numeric records, missingness with only a global reason, and unresolved
identity/denominator links. Absence claims are bounded to named files; no
measurement is declared never performed. This improves descriptive eligibility
screening but does not change the no-flux, no-donor-join and no-developmental-
outcome gates. Five claim-specific gates now state what evidence would change
each eligibility decision. A bounded public-source search found the
[Spiess et al. 2023 candidate](https://pmc.ncbi.nlm.nih.gov/articles/PMC9868778/).
Its primary article reports group-mean concentration and recovery summaries;
the indexed dissertation excerpt exposes Table 3S per-perfusion characteristics,
total maternal/fetal volume loss at experiment end, and timing fields. The linked
supplement file itself still returned a PMC access challenge, and the repository
landing page requests a copy. These excerpts do not expose time-resolved
sample-removal/reservoir-volume records or run-linked concentration trajectories.
A separate, directly readable 2023 supplement likewise includes individual
placental characteristics and end-point volume loss, but concentration profiles
and recoveries are group summaries rather than individual trajectories. Both
studies are useful metadata comparators only; neither resolves the timepoint
volume/accounting and same-unit requirements for a dimensional fit. The updated
[Spiess screen](SPIESS_2023_PERFUSION_SUPPLEMENT_SCREEN_2026-10-10.md) records
the boundary and license. Next screen directly accessible public records for
individual concentration trajectories joined to explicit run-level volume and
recovery observations. Do not mix candidate values with Mathiesen 2020 or fill
gaps by contacting authors.

**Nutrient-transfer comparator screen, 2026-10-10:** Hirschmugl et al. report
term-placenta labeled-fatty-acid clearance and endogenous release as group
summaries, alongside a fitted compartment model. The five-page supplement is
now pinned and inspected: it adds mean-level FFA-mixture, quality-control,
population, and tissue-uptake summaries, but no individual source rows or
run-level accounting join. The plotted group comparison is distinct from the
single prediction-check experiment, and some model states have no matching
experimental measurement. Keep this as a mechanism/observation-contract
comparator, not a dimensional fit or support target. See the [source
screen](HIRSCHMUGL_2021_FATTY_ACID_PERFUSION_SOURCE_SCREEN_2026-10-10.md) and
[availability crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Vitamin-D exchange/metabolism candidate intake, 2026-10-10:** Ashley et al.'s Figure 1 source workbook exposes five per-perfusion values for each of four 13C-25(OH)D3 loss/metabolism/storage/fetal-appearance endpoints and five maternal/fetal 1,25(OH)2D3 rates. A 30-record candidate dataset and all-207-cell audit are source-located and byte-verified. The 25D component sums close within each workbook row, but those derived components must not be treated as independent validation. The 24,25D block stays excluded: workbook units differ by 1000-fold from the article label and the maternal mean/fetal SEM disagree with article summaries. This is a term-only ex-vivo placenta mechanism dataset, not a gestation-support target. See the [source screen](ASHLEY_2022_VITAMIN_D_PERFUSION_SOURCE_SCREEN_2026-10-10.md), [candidate observations](config/observations/ashley_2022_vitamin_d_perfusion_candidate.json), and [source-cell ledger](config/source_inventories/ashley_2022_figure1_source_cells.csv).

**Fetal-demand exchange screen, 2026-10-10:** Sandovici et al. (2024) report mouse tracer transfer at E15.5/E18.5. Their combined-sex results, sex-stratified supplement and Discussion do not summarize glucose transfer identically across per-fetus, fetal-mass and labyrinth-area denominators; preserve this qualification alongside the clearer E18.5 per-area reduction in system-A amino-acid tracer transfer. The Cambridge repository provides a 13-page supplement, now pinned by local SHA-256; the inspected article and supplement contain figures and cohort metadata but no machine-readable per-litter transfer rows. A 12-row metadata inventory records the reported litter/fetus counts, strata and panels without importing tracer outcomes. Keep tracer, denominator, age, sex and litter structure distinct. This is not human data or a gestation-support result. See the [source screen](SANDOVICI_2024_MOUSE_PLACENTAL_DEMAND_SOURCE_SCREEN_2026-10-10.md), [panel inventory](config/source_inventories/sandovici_2024_transfer_panel_inventory.csv), [source manifest](artifacts/sandovici-2024-mouse-placental-demand/SOURCE.json) and the [functional-route design implications](FUNCTIONAL_SUPPORT_ROUTES.md).

The original Mathiesen v4 raw-cell and standardized observation bundles matched across all 3,190 unique workbook locators, but v4 left duration status only in a parallel audit CSV. Cycle 39 adds optional typed `observation.source_qualifications` to the observation schema, validator and CSV export; the v5 Mathiesen intake carries each Table 1 duration declaration and locator on the corresponding row. The v5 round-trip audit matched all 3,190 cells and qualifications (2,908 numeric, 282 blank; 220 pre-exposure times unresolved, 2,700 within-window, 270 after-window). The v4 artifacts remain unchanged. The Table 1 run map is still awaiting human verification, and the new field records source declarations rather than validating them. Window flags do not fill the separate volume/removal, recovery, calibration or instrument-data gaps, so dimensional transport fitting remains ineligible.

**Doravirine public-source screen, 2026-10-10:** Bukkems et al.'s article and
both publisher supplements add closed–closed and closed–open human term-placenta
concentration and mass-balance summary figures. The closed–closed paper reports
four perfusions per direction and study-level recoveries; ESM1 explicitly says
its mass-balance calculations correct for sample-related volume loss. The
inspected public files do not expose the underlying per-run concentrations,
numeric volume/removal histories, or individual recovery totals. Keep this as
an aggregate accounting-method comparator; do not digitize figures into
pseudo-individual rows. See the [source screen](BUKKEMS_2022_DORAVIRINE_PERFUSION_SCREEN_2026-10-10.md)
and candidate details in the [perfusion crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Doravirine predecessor screen, 2026-10-10:** Le et al.'s 2021 open-circuit
paper reports a five-minute sampling schedule over 90 minutes, but its
publisher supplement contains only mean±SD concentration figures and a ratio
plot. It gives no numeric per-run concentrations, sample removals, or volume
histories. Retain it as a group-figure comparator separate from Bukkems et
al.'s closed-circuit study; see the [screen](LE_2021_DORAVIRINE_PERFUSION_SCREEN_2026-10-10.md)
and the [source crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Cabotegravir/bictegravir access screen, 2026-10-10:** Pencolé et al.'s
PubMed abstract reports aggregate transfer summaries for five cabotegravir and
six bictegravir perfusions. The publisher full-text route returned a payment
requirement, and no public supplement or dataset link was located in the
bounded search. Keep individual concentrations and volume/removal fields
unassessed because the full article and any supplements could not be inspected.
See the [access screen](CABOTEGRAVIR_BICTEGRAVIR_2020_ACCESS_SCREEN_2026-10-10.md)
and [candidate record](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Essential-substrate evidence screen, 2026-10-10:** Lofthouse et al.'s n=5 term-placenta phenylalanine study separates maternal uptake, fetal delivery, and placental tissue/protein retention, but reports aggregate mean±SE figures without unit-linked rows or a complete individual balance. The paper also states 2.7 nmol/L tracer in Methods and 2.7 pmol/L in Discussion; retain both unresolved. This strengthens interface evidence requirements but is not a calibration dataset or embryo-support result. See the [source screen](LOFTHOUSE_2016_PHENYLALANINE_PERFUSION_SOURCE_SCREEN_2026-10-10.md) and [perfusion crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**In-vivo amino-acid reference screen, 2026-10-10:** Holm et al. report 19-amino-acid concentrations and paired vessel differences in 179 uncomplicated term pregnancies. Two source-located CSVs preserve the 76 Table 2 concentration cells and 76 Table 3 crude/water-adjusted paired-difference cells, including an unusual source quartile, printed p-values and bold status. A cross-check distinguishes 17 positive adjusted umbilical medians from 14 source-bolded positive results and the bolded negative glutamic-acid result, matching the article narrative. The linked NSD record's latest metadata restricts individual-level provision to agreement with the principal investigator upon order; no file was requested. Concentration differences are not fluxes without blood-flow data, and the study is term-only. Keep it separate from ex-vivo perfusion and developmental-support evidence. See the [source screen](HOLM_2017_AMINO_ACID_INTAKE_SOURCE_SCREEN_2026-10-10.md) and [source crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Amino-acid metabolism comparator, 2026-10-10:** Day et al.'s public term-cotyledon tracer study reports aggregate uptake/tissue summaries and mean±SEM supplemental figures, but no run-level tracer/recovery join. Its finding that synthesized glutamine was mostly released to the maternal circuit reinforces the need to separate substrate uptake, metabolic conversion, tissue retention, and fetal delivery. Keep this short-duration ex-vivo result as a mechanism comparator, not a support-system target or row-level calibration source. See the [source screen](DAY_2013_GLUTAMINE_PERFUSION_SOURCE_SCREEN_2026-10-10.md) and [source crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Letermovir/maribavir observation intake, 2026-10-10:** Faure Bardon et al.'s public S1 XLSX adds 912 source-cell rows for active-drug and antipyrine FC/MC/FTR observations across five letermovir and three maribavir labels at 19 timepoints. All values, formula caches, blanks and locators are retained. A material source ambiguity remains: the article reports five validated letermovir perfusions, but the workbook's group summaries use only four of five visible labels. Keep the candidate pending human review, preserve this mismatch, and leave volume/recovery accounting and dimensional fitting ineligible. See the [intake note](FAURE_BARDON_2020_LETERMOVIR_MARIBAVIR_PERFUSION_INTAKE_2026-10-10.md) and [candidate manifest](config/perfusion_observations/faure_bardon_2020_lmv_mbv_dataset.json).

**Earlier dolutegravir access screen, 2026-10-10:** Schalkwijk et al. (2016) adds an abstract-level n=6 term-cotyledon summary, but the publisher full-text route required purchase and no run-level public file surfaced. Individual observations and volume/recovery fields remain unassessed; keep this cohort distinct from the 2019 Mandelbrot intake. See the [access screen](SCHALKWIJK_2016_DOLUTEGRAVIR_ACCESS_SCREEN_2026-10-10.md) and [perfusion crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).

**Dolutegravir observation intake, 2026-10-10:** the public Mandelbrot et al.
S1 workbook supports a source-linked descriptive intake of 94 timepoint rows
across five placenta labels. Preserve embedded formula-cache values, formula
text, source cells, literal dashes and blanks. Placenta 3 has no 180-minute
worksheet row despite the article's five-perfusion three-hour summary; no value
was imputed. The table lacks numeric volume/removal histories and individual
recoveries, so it does not support mass balance or dimensional fitting. The
[intake note](MANDELBROT_DOLUTEGRAVIR_PERFUSION_INTAKE_2026-10-10.md),
[candidate dataset manifest](config/perfusion_observations/mandelbrot_2019_dolutegravir_dataset.json),
and [source-cell CSV](config/perfusion_observations/mandelbrot_2019_dolutegravir_s1_cached_values.csv)
remain pending human transcription review.

**Public perfusion screen update, 2026-10-10:** Eliesen et al.'s publisher
supplement contains source-labeled maternal and fetal concentration trajectories
for three distinct term-placenta perfusions at ten times, including a separate
no-placenta system-control series. The paper reports recovery only as a group
summary; its methods describe volume estimates at sampling, but no numeric
per-run volume/removal histories or recovery rows appear in the inspected
article/supplement. This qualifies the trajectories for a source-linked
descriptive intake only, not a volume-based mass balance or dimensional fit.
The candidate details and field-level limits are in the
[public perfusion crosswalk](config/source_inventories/mathiesen_2020_placental_perfusion_crosswalk.json).
The source-labeled values are retained in a separate
[perfusion-concentration intake](config/perfusion_observations/eliesen_2024_tofacitinib_dataset.json)
with the exact table lexemes, time and concentration units, compartments,
source locators and the single `N/A` control entry. The developmental
observation validator was not used because its interval field represents
developmental stage, while these minutes are perfusion-assay time. Human source
and transcription review remain pending. The search milestone remains open for
a source with the complete per-run volume/removal/recovery join.

## Delivered baseline

- Reviewed evidence ledger with source class, species, developmental stage,
  stated interval, excluded inference and requirement links.
- `evidence-report`: explicit stage-transition edges with same-unit IDs,
  source/claim links and exact locators required before continuity can be
  marked demonstrated or contradicted; current human-target edges stay unknown.
- Exact piecewise exchange transitions, scheduled synthetic sensors, backup
  power/fault fixtures, receipts and input/implementation/output hashes.
- Integral-balance consistency diagnostics, noise-aware state estimation,
  prospective prefix-trained forecasts versus a last-reading baseline, and
  seeded cadence/noise/fault/event-timing sweeps.
- Dimensionless two-compartment transport and Kelvin–Voigt mechanics examples
  with simpler alternative models; developmental-observation JSON schema.
- `validate-observations`: bounded source-linked records, exact reported-unit
  partitions, optional local source-byte hashing, local source-review metadata,
  explicit continuity states and a receipt-bound ResearchDesk report. Intake
  validity is not analysis eligibility.
- Read-only ResearchDesk discovery and receipt-checked report display.

The 0.2.1 correction matches the transport reference to the combined capacity
of both compartments. It also distinguishes point-forecast availability from
approximate-interval availability when local parameter covariance is absent.
Neither a finite covariance nor a low residual establishes biological validity.

The TEBV Figure 8 case in RegenWorkbench is a descriptive measured-data
reanalysis with one donor, missing vessel identifiers and a recorded
workbook/caption sample-count discrepancy. It is not an external validation of
these equations or measured ectogenesis.

## M1 — Independently verify numerical accuracy

**First implementation milestone.** Conservation identities already exist;
add accuracy checks against independent solutions.

**Progress:** `verify-transport` publishes a receipt-bound, five-level
step-halving curve against a closed-form two-state reference.
`verify-transport-matrix` now repeats it across seven deterministic regimes,
including zero dynamics, isolated exchange/transfer, unequal rates, stable
high mixing and near-degenerate weak coupling. `verify-mechanics` compares
every output and load boundary against an independently evaluated,
`expm1`-stabilized piecewise-load convolution, including zero-elasticity creep.
Adversarial checks now cover adjacent sign-changing loads, endpoint loads,
very fast relaxation and the near-zero-elasticity limit. A test now compares the
closed-form transport reference with an independent 60-digit matrix exponential
across 85 coefficient-scale cases (rates 1e-12 to 1e4, times 1e-6 to 1e3); the
observed worst relative difference on 2026-10-08 was about 4e-16. M1 remains in
progress for the mechanics reference at coefficient extremes and for broader
floating-point limits.

1. Preserve the independently derived constant-coefficient two-compartment
   reference and check both compartments over the supported numerical domain.
2. Expand transport checks to additional coefficient-scale extremes; retain
   actual versus requested steps and each numerical regime in the
   receipt-bound report.
3. Extend mechanics analytic checks across additional degenerate
   elasticity/viscosity limits; test controlled rejection of unsupported
   inputs.
4. Publish equations, units (dimensionless here), assumptions, tolerances and
   error curves generated by a reproducible command.

**Acceptance:** independently derived reference values, quantitative convergence
tests, controlled failures at unsupported regimes, and a verification report
that cannot be mistaken for biological validation.

## M2 — Benchmark identifiability and forecast calibration

Depends on M1. The current bounded profile search and local covariance are a
baseline, not a complete identifiability study.

`transport-identifiability` now exports exact core-only rate-swap and
equilibrium scale counterexamples, their valid witness configurations and
paired-interface contrasts. It addresses a structural observation limit in
the existing dimensionless transport equations. It does not complete M2's
forecast calibration or establish empirical identifiability.

- Export the objective profile, search-bound hits, rank/singular-spectrum
  diagnostics and approximate interval availability with explicit reasons.
- Freeze separate calibration and evaluation scenarios before tuning. Vary
  initial state, power schedule, cadence, noise and model mismatch; reserve
  independent seeds and schedules for evaluation.
- Compare forecasts at prespecified horizons with last-value and simpler
  model baselines. Report error, bias, interval width and coverage together.
- Distinguish per-reading coverage from coverage variation across independent
  synthetic trajectories; include all failure/unavailable denominators.
- Test equilibrium, weak excitation, parameter boundaries and wrong model
  structure. Do not replace an unavailable forecast prediction interval with a
  sensor-noise-only interval under the same label.

**Acceptance:** machine-readable frozen scenario plans, no tuning on evaluation
data, negative controls that expose non-identification, and reproducible
baseline comparisons. Any use of profile likelihood or confidence language
needs its statistical assumptions and independent methods review.

## M3 — Add a causal observer benchmark

Depends on M2. Keep this a software fixture, separate from live hardware.

- Define a narrow observation interface carrying only measurements already
  available at each timestamp. Hide generator truth, injected fault labels
  and future measurements from the observer.
- Add delay, drift/bias, dropout, shared power loss and model mismatch cases.
  Document which power/event information is assumed known.
- Score state error, event-level misses, false alarms and detection delay;
  retain overlapping-event ambiguity and undetected-event outcomes.
- Keep truth exclusively in the evaluator. Add tests that future readings and
  hidden fault annotations cannot alter earlier observer outputs.

**Acceptance:** frozen held-out scenarios, past-only interface tests, explicit
event denominators and failure examples. No physiological alarms, clinical
thresholds or control recommendations.

## M4 — Enforce observation metadata and evidence intervals

Can proceed alongside M1–M3. The observation record and dataset-card contracts
now have a stdlib runtime validator; source coverage and scientific review
still need additional work.

**Progress:** `validate-observations` checks source-file references and declared hash metadata,
species, developmental intervals, endpoint units, independent-unit hierarchy,
missingness, calibration references and transition records. When given an
explicit local root, it hashes bounded relative source files and records the
match status without copying them. It partitions
records by exact reported categories without unit conversion or pooling, and
requires a reported unit identity plus same-source chronologically comparable
intervals before accepting a `demonstrated` continuity assertion. ResearchDesk
can display its receipt-bound output. This verifies record structure and byte
provenance, not a paper transcription, reviewer's identity or scientific
eligibility.

**Evidence-ledger progress:** `evidence-report` now accepts structured numeric
interval components on sources and claims. A claim must match the cited source's
axis and exact unit and stay within its bounds; missing or widened claim scopes
fail validation. This catches scope expansion in curated metadata without
converting units or pretending the validator checked a source transcription.
It also emits five explicit developmental transitions. A reported edge must
preserve species, cover both source stages, link exact source locators and unit
IDs across its claims, and use a peer-reviewed source. Announcement and regulator
records cannot establish same-unit continuity. All human-target edges remain
`not_reported`; this is a gap in the bounded ledger, not evidence of absence.

Remaining work includes source-locator review history, permission/access
confirmation and one qualified empirical dataset. Candidate sources stay
unpromoted until primary-source review. Curated transition locators and unit IDs
still need source-transcription checks and an auditable reviewer record.

**Observation interval progress (2026-10-09):** source artifacts can declare an
optional `developmental_scope` with species, stages, exact time unit, numeric
bounds and a source locator. Records citing that stage artifact must match its
categories and remain within its numeric interval. Textual or missing record
bounds stay explicitly unassessed. Receipt-bound source-scope and per-record
check tables preserve those distinctions. The new executable intake example is
entirely invented dimensionless metadata; no empirical source has been qualified
or promoted by this change. Source transcription and human review remain open.

- Validate examples and imported metadata with the stdlib runtime, including
  source version, species/model, independent unit, stage, actual interval,
  quantity/unit, missingness and calibration status.
- Extend structured intervals to eligible empirical observations and link them
  to exact source locators. Keep source-review records and dataset eligibility
  separate from machine-checked range containment.
- Add claim/source/assumption links, exact figure/table/workbook locators,
  reviewer identity/date/rationale and revision/supersession records.
- Separate reported experiments, institutional announcements, regulator
  discussions and hypotheses. Record adverse and null observations and
  distinguish physiological support from growth/development outcomes.

**Acceptance:** tests reject incompatible species, unsupported intervals,
source-class promotion and contradictory missingness/calibration fields.
Updating a source cannot silently change an existing reviewed claim.

The [mouse developmental study](https://www.nature.com/articles/s41586-021-03416-3)
and [FDA artificial-womb discussion](https://www.fda.gov/media/172252/download)
address distinct stages and questions. The
[preterm-lamb study](https://doi.org/10.3389/fphys.2023.1219185) also makes growth
limitations important to the evidence map. These sources do not establish
continuous human development from fertilization through birth.

## M5 — Make model bundles independently verifiable

Coordinate with [RegenWorkbench's roadmap](https://github.com/dylanstechmann/regen-workbench/blob/main/ROADMAP.md).

**Delivered 2026-10-07.** `identifiability-report` bundles copy the exact source
`simulate` receipt in as `source_receipt.json` and declare its hash and filename
in their own receipt metadata, so ancestry resolves after the source directory is
deleted. Every bundle now carries `reproduction_plan.json` with the package
version, Python version, declared dependencies, command template, inputs, the
complete expected file set and interpretation limits, and no absolute paths.
`wombmodels verify-bundle` validates receipt structure without a schema library,
rejects symlinked and oversize outputs before reading them, recomputes every hash
and byte count, and resolves the declared parent receipt. It reports
`bytes_verified`, `ancestry_resolved`, `scientific_review`
(`not_established_by_this_tool`) and `reproduction` (`not_attempted`) as separate
statuses; `--strict` also fails on undeclared files and unpublished bundle kinds.
Fifteen cases cover changed, missing, swapped-parent, symlinked, undeclared,
malformed-receipt and relocated bundles, including one that verifies a copied
bundle after deleting its source directory.

- Remaining: a rerun harness. Verification does not execute the recorded command,
  so "verified" and "reproduced" remain different claims. Bundles other than
  `identifiability-report` have no parent, so their ancestry status is
  `no_parent_declared` rather than resolved.

**Acceptance:** a fresh environment can verify and rerun the synthetic example;
missing parents or changed bytes fail explicitly. ResearchDesk remains an
optional consumer, not a runtime requirement of the model package. *Verification
and explicit failures are met; automated rerunning is not.*

## M6 — Establish an empirical benchmark with appropriate units

Begin the data-access audit early; fit only after the plan is frozen.

The [2026-10-09 interface source qualification](SOURCE_QUALIFICATION.md)
records a bounded Hori/Bhide file audit and executable candidate Hori endpoint
intake. The inspected files lack the linked trajectories and independent-unit
identities required for the dynamic benchmark. Human review and appropriate
source reuse confirmation remain pending; M6 is not complete.

**Public human reference qualification, 2026-10-10:** the candidate maternal–
fetal interface atlas supplement now has checked sample-label joins and
reconciled multiome/spatial QC totals. This supports a possible cell-identity
and spatial-context comparison only. It does not supply exchange measurements,
longitudinal embryo outcomes, or an eligible transport benchmark; portal data
reuse terms and human review remain pending. A public viewer-manifest audit
resolved five JSONL endpoints from 0.5 GB to 37.8 GB; no complete payload was
downloaded. Range-addressable schemas expose sample/category fields, and bounded
`sample_id` reads join 16 spatial categories to the supplement; the spatial
matrix row total matches the reported post-filter total. The 193,202-row
scPlacenta matrix remains 1,467 above the 191,735 paired-nuclei table total,
with one sample category accounting for that difference; its count universe is
unresolved. Publisher Source Data Figs. 1–2 and the linked GEO/NeMO records were
checked: the figure workbooks contain figure-level proportion/spatial summaries,
while the GEO/NeMO records are independent iScore benchmarks or brain controls;
none explains the atlas viewer's +1,467 rows. The portal schema exposes no
donor key for scPlacenta; a separate GEX viewer's 27 donor categories and 38
dataset categories have no label crosswalk to the 23 atlas sample IDs. No
dataset-specific reuse/license statement appears in the inspected portal page.
Close this bounded audit with count universe, reuse terms and sample-to-donor
mapping unresolved; exclude count-dependent and donor-grouped analyses unless
new public metadata establish them. Continue the next evidence milestone with
a source that reports functional exchange data and can meet unit/measurement
eligibility. See
[`HUMAN_MFI_ATLAS_QUALIFICATION_2026-10-10.md`](HUMAN_MFI_ATLAS_QUALIFICATION_2026-10-10.md).

**Public perfusion-observation screen, 2026-10-10:** Loza et al.'s open 2026
term-placenta pilot provides trial-labeled serial concentration figures,
explicit missing timepoints, and an assay detection limit, but not a
machine-readable observation table or timepoint-specific volume/removal history.
It is useful for tightening the observation-intake schema and missingness
capture; it does not qualify for a dimensional transport fit or provide
developmental outcomes. The field-level screen is in
[`MATHIESEN_PERFUSION_AVAILABILITY_CROSSWALK_2026-10-10.md`](MATHIESEN_PERFUSION_AVAILABILITY_CROSSWALK_2026-10-10.md)
and its JSON record. No author was contacted.

The [van Kammen et al. 2025 public perfusion screen](https://link.springer.com/article/10.1007/s13346-024-01715-6)
adds a group-mean maternal/fetal compartment-volume time course and a
publisher-listed supplement with per-placenta physiology summaries. The
supplement repeats an outflow column header and contains no individual volume
or concentration trajectories; the article offers the underlying dataset on
reasonable request. Keep it as an observation-schema comparator only, with the
ambiguous fields unresolved. See the JSON candidate screen for exact locators.

**Repository discovery screen, 2026-10-10:** bounded searches of Figshare,
Dryad, Zenodo, Mendeley Data and OSF found no public archive with linked,
per-run human placental concentration and volume/removal histories. The
[screen report](PERFUSION_DATA_REPOSITORY_SCREEN_2026-10-10.md) records partial
comparators and out-of-scope repository hits, including tissue imaging,
transcriptomics and a separate in-vivo pregnancy-PBPK dataset. These evidence
lanes remain separate; repository metadata alone do not qualify an individual
file for fitting. The finding is a search boundary, not proof that records do
not exist.

**Fetal-support outcome intake, 2026-10-10:** comparison of the 2017, 2018,
2023, 2024, and 2026 animal evidence confirms days-to-weeks of selected fetal
physiological support and several support-to-neonatal transitions. The 2017
paper records one earlier semi-closed-system lamb supported 288 hours and
extubated; its Table 1 gives a normal MRI at one year, while the Results text
and Fig. 7d give the MRI time as six months. Its separate eight-lamb Biobag
cohort addresses longer fetal support. A 2018 cohort reports brief ventilation
after support. A 2026 hospital
announcement reports one fetaLife ewe over a year old with normal
neurodevelopment, but does not link that case to the 21-day maximum or provide
a cohort dataset. The [BCNatal 2023 annual report](https://bcnatalresearch.org/wp-content/uploads/2024/12/CAT-Memoria-anual-2023-_compressed.pdf)
records a 14-day ovine support milestone and the start of metabolic/hormonal
characterization, but gives no denominator, unit-level results, or link to later
cases. A 2025 conference abstract for a 2023–24 phase summarizes 12 experiments
with 7–14 day goals (mean survival 9.5 days; 17% reached day 14)
and reports flow/circuit-related discontinuation reasons, but gives no
per-animal disposition table. Its study window precedes and is distinct from
the later 21-day announcement. A [public post by the project coordinator](https://es.linkedin.com/posts/elisenda-eixarch_cat-avui-%C3%A9s-un-dia-molt-especial-comparteixo-activity-7478820903385210880-_MZF)
says Gaia spent 10 days on the system and was neurologically normal at 15
months, but no individual record links Gaia to the abstract cohort. A later
[company post](https://es.linkedin.com/posts/fetalife-technologies_hace-siete-a%C3%B1os-nos-planteamos-algo-que-entonces-activity-7503037372343828480-jweo)
pairs 21 days of support with >16 months of normal neurological development;
the [current fundraising page](https://capitalcell.com/en/campaign/fetalife/)
pairs 21 days with 18 months. Neither names an animal, so neither claim is
linked to Gaia or the 21-day animal in the inventory. The fundraising page also
claims AEMPS engagement has begun and targets a 2029 first human study; that is
a company statement, not evidence of authorization or an active trial. An
[Oct. 10 interview with the CEO](https://www.elnacional.cat/oneconomia/es/empresas/fetalife-incubadora-liquida-eleva-supervivencia-prematuros-extremos_1707973_102.html)
reports a proposed ~€8M round (about €2M expected from EU aid), two years of
integration testing, and a late-2028/early-2029 first-human target. It also
reports a possible early-2027 EMA validation expectation; none of these
statements confirms financing, agency action, or trial activation. A 2023
[BCNatal/La Caixa announcement](https://www.clinicbarcelona.org/en/news/the-artificial-placenta-project-achieves-foetal-survival-of-12-days-in-good-health)
had listed pig testing as a planned phase-two milestone, but it reported no
results. Published fetal-pig artificial-placenta studies from Toronto/SickKids
and the University of Memphis are from other research groups. Toronto's 2024
echocardiography paper reports hydrops signs in all 13 pigs after a mean 46.4
hours and uses the same 2020–2021 preclinical study period described in the
group's earlier reports; count it as added characterization, not a separate
replication. These studies report unresolved physiology, not fetaLife results
or long-term neurological follow-up. The project-specific pig claim remains
unverified. A [2026
ISUOG poster](https://epostersonline.com/isuog2026/poster/543) adds a four-lamb
postnatal-transition table: three animals died or were euthanized within seven
days, while one survived 13 months and had a maze assessment at three months.
This supplies same-poster case linkage, but the four transitions are not the
denominator of all FLI attempts. The PDF text extraction gives 24 support days
for one row, which conflicts with the table's gestational ages and the reported
mean of 9.6 ± 3.1 days; retain that value as unresolved pending visual source
verification. The poster does not identify Gaia or link the four cases to the
21-day milestone or the newer company claims. A second [2026 ISUOG poster,
EP09.31](https://epostersonline.com/isuog2026/poster/535), lists 29 lambs in a
metabolic/growth study frame (5 below 115 gestational days and 24 at or above,
with support eligibility of at least six days). Baseline-to-day-6/7 plots show
bilirubin and BUN increases and albumin decrease, with no AST/ALT change; the
authors conclude gestational age was a greater determinant than parenteral
nutrition for cholestasis and growth. This is a poster-level group result with
no per-animal values or endpoint denominators, and it is not linked to EP09.22
or the separate Gaia/21-day reports. In the 2024
paper, raw data are not publicly available during
an ongoing FDA submission; no contact was made. These results do not establish
continuous embryo-to-birth development or human outcomes. The source-bounded
intake and minimum longitudinal fields are recorded in
[`ARTIFICIAL_PLACENTA_OUTCOME_INTAKE_2026-10-10.md`](ARTIFICIAL_PLACENTA_OUTCOME_INTAKE_2026-10-10.md)
and its [machine-readable candidate inventory](config/source_inventories/fetal_ovine_support_transition_2023_2026.json).
The four EP09.22 post-transition cases now also have a separate
[candidate observation intake](config/observations/eixarch_2026_neonatal_transition_candidate.json).
It now contains 20 typed rows: extubation, survival, disposition, limited
assessment, four support durations, and four weights whose measurement time is
not stated. It preserves the Animal 2 and Animal 4 duration/gestational-age
differences without correction and does not treat the selected transition
subset as an FLI-start denominator. The local poster SHA-256 verifies; human
source review remains pending.
That intake states the evidence ladder explicitly: the mapped program reaches
selected sheep fetal support and some post-support transitions, including one
poster-reported 13-month survivor and a separate poster's metabolic changes
during support; the fetaLife/ovine records in this intake have no embryo-stage
or complete human-development result. Separate early mouse and primate
embryo-culture/model sources do not link into those fetal-support cohorts. A
future preterm-fetal human study would address a different segment of the goal.

**Developmental-stage coverage update, 2026-10-10:** primary-source review
found separate early-development and fetal-support windows. Intact mouse
embryo ex-utero culture reaches E11 in a 2021 paper and approximately E12.5 in
a 2026 preprint; intact cynomolgus embryos have been cultured to 25 days
post-fertilization and early organogenesis. Newer mouse and primate
cell-derived embryo models cover early stages, with the reported limits and
model status retained in [EVIDENCE.md](EVIDENCE.md) and the structured stage
coverage note in the fetal-support intake inventory. Artificial-placenta
cohorts begin with already-developed lamb fetuses at 90–125 ovine gestational
days across separate programs. No cited source links the same unit across
early embryo development, fetal support, birth, and defined postnatal function.
The evidence-based next gate is to specify and measure the handoff between
stage-specific models; do not interpret the disconnected windows as one
demonstrated trajectory.

**E11 handoff qualification, 2026-10-10:** the 2021 mouse ex-utero paper's
E7.5-start cohort reaches approximately E11, then reports abrupt yolk-sac
circulation interruption, pericardial effusion, and rapid overnight death.
The authors describe inadequate supply relative to increased body size as a
consistent explanation. Figure captions clarify embryo and experiment counts,
including removals, but the source summaries reviewed here do not yield a
unit-linked event table. Its linked GEO series GSE149372 contains E8.5 and
E10.5 molecular samples but no sample labeled E11 or later, so these
destructive snapshots cannot supply the endpoint risk set or event timing.
GEO/SRA metadata also does not map the listed libraries to bulk versus
single-cell figures. The
finding identifies a late-organogenesis exchange
handoff as an evidence gap; it does not establish a repair or bridge to the
separate E12.5 preprint or fetal-support cohorts. See the
[source qualification](AGUILERA_CASTREJON_2021_E11_HANDOFF_2026-10-10.md) and
[structured inventory](config/source_inventories/aguilera_castrejon_2021_ex_utero.json).

**E12.5 preprint qualification, 2026-10-10:** the official Janelia publication
page for Lokshtanov et al. v1 confirms the separate mouse cohort window through
approximately E12.5 and scopes maternal/placental independence to a reported
E10.5–E11.5 metabolic transition. The abstract says oxygen affects the extent
of that transition but does not bring it forward. This is not a claim that all
development is independent of maternal support or that the cohort reached
birth. The preprint's full-text endpoint was unavailable through the current
web reader, so detailed terminal outcomes remain qualified only from selected
rendered manuscript passages; the candidate intake remains unpromoted. See the
[structured source screen](config/source_inventories/midgestation_frontier_2026.json).
A bounded follow-up search of NCBI BioProject/SRA/GEO, DataCite, and indexed
metabolomics repository pages found no DOI/title-linked accession; related
GEO records were kept separate. This narrows the public crosswalk but does not
show that underlying datasets do not exist.

**Healthy-output qualification gate, 2026-10-10:** the animal evidence does
not meet a cohort-level, multi-domain health claim. There is no complete
attempted-animal denominator. The Partridge paper's conflicting MRI ages are
preserved in a [candidate observation record](config/observations/partridge_2017_mri_time_conflict_candidate.json)
with measurement time unset rather than choosing six months or one year. The
transition poster offers one maze result, and Gaia's reported
“normal” neurodevelopment has no named instrument. The intake now requires
same-unit linkage, repeated age-appropriate outcomes across specified domains,
comparators, adverse outcomes and missingness, plus independent cohort
replication. Passing this animal gate would still not establish a healthy
human result.

The intake now types entry to support, exit to neonatal support, extracorporeal
weaning, spontaneous respiration, and post-support follow-up separately. This
prevents a study's successful in-system entry from being mistaken for successful
neonatal transition.
The 2026-10-10 ClinicalTrials.gov title-field screen found no exact-match
records, while the hospital's 2026 update describes technology adaptation and
ethics/legal preparation before a first human study planned for 2028–2029 if
funding is available. The current company fundraising page targets 2029 and
claims AEMPS engagement has begun. Treat both as future plans/company claims,
not trial activation or authorization; the bounded registry screen is not a
global registry or regulatory-authorization conclusion. The query URLs and search
limits, plus five explicit evidence-promotion gates for denominators, unit
linkage, outcome definitions, reproducibility, and human-study scope, are in the
structured inventory.

- Select openly licensed measurements relevant to a stated equation, with
  accessible independent-unit IDs, units, uncertainty and instrument context.
- Write a source/license card and applicability assessment. A developmental
  paper is not automatically a calibration dataset for a transport model.
- Prespecify outcomes, exclusions, independence level and grouped splits.
  If units or identifiers are unavailable, retain a descriptive analysis and
  label the missing validation opportunity.
- Compare simple alternatives and model discrepancy on held-out units; publish
  negative results and sensitivity to unverified assumptions.

**Acceptance:** licensed reproducible intake, frozen unit-safe evaluation,
data/model mismatch review and an externally reviewed methods report. No claim
of clinical prediction, complete gestation or reduced congenital defects.

**Early human implantation-interface intake, 2026-10-11:** the CREST paper provides a stage-bounded human implantation/endometrial model from blastocysts at 5–6 d.p.f. through a day-14 endpoint. The paper reports 248 embryos across the study and 17 day-14 sites for scRNA-seq; public metadata resolves to seven sample groups, 15 runs and 60 FASTQ file entries, but no site-to-sample or per-embryo outcome map. The raw-read URLs were HEAD-checked without downloading content. The exact processed-data and code Zenodo DOIs resolve to public records; neither large data files nor code archive was downloaded. No biological observation rows are promoted yet. See the [source screen](MOLE_2026_HUMAN_IMPLANTATION_SOURCE_SCREEN_2026-10-11.md), [sample crosswalk](config/source_inventories/crest_2026_emtab13629_sample_crosswalk.csv), and [structured inventory](config/source_inventories/crest_2026_human_implantation.json). This is early-interface evidence, not placental exchange, later gestation, birth or postnatal-health evidence.

**CREST code-release unit check, 2026-10-11:** the v1.0 archive hash-checks against Zenodo and contains a 15,673-row cell metadata table with six batch labels, but no link to the seven E-MTAB sample groups or the article's 17 implantation sites. Its `nCount_RNA` column is constant at `SeuratProject`. The inspected Figure S5G script compares cell types with a cell-level MAST test, without a per-sample/embryo replicate term. The archive was inspected statically in memory; no code was run and no processed RDS was downloaded. Preserve the unit-linkage gap and promote no biological outcomes. See the [static review receipt](artifacts/early-interface-model-2026-10-11/crest-code-release-analysis-cycle192.json) and [source screen](MOLE_2026_HUMAN_IMPLANTATION_SOURCE_SCREEN_2026-10-11.md).

**CREST supplement unit check, 2026-10-11:** the publisher-hosted two-page MMC1 PDF was retrieved, hash-pinned and visually reviewed. Its Table S1 covers endometrial biopsies, not the 17 day-14 implantation sites or the seven E-MTAB-13629 groups; no crosswalk was found in this inspected file. The negative result is bounded to MMC1. No donor-level values were copied and no outcome rows were promoted. The sample/site unit gap remains unresolved; a separate early-interface model is the next source-screen candidate. See the [supplement receipt](artifacts/early-interface-model-2026-10-11/crest-supplement-screen-cycle193.json) and [source screen](MOLE_2026_HUMAN_IMPLANTATION_SOURCE_SCREEN_2026-10-11.md).

**Li et al. implantation-failure model screen, 2026-10-11:** the PubMed abstract reports an in-chip human blastoid/endometrioid model and qualitative RIF-versus-fertile-control implantation differences. The publisher workbook contains a clinical/endometrial characteristics table with Ctrl n=18 and RIF n=40, but these are not verified assay denominators. Exact BioStudies/GEO queries did not surface a linked assay dataset; the result is bounded to those services and queries. The full article and assay-level source values remain unreviewed, so no outcomes are promoted. This is early-interface evidence only. See the [source screen](LI_2026_HUMAN_IMPLANTATION_FAILURE_MODEL_SOURCE_SCREEN_2026-10-11.md), [inventory](config/source_inventories/li_2026_human_implantation_failure.json), and [route/supplement receipt](artifacts/implantation-failure-model-2026-10-11/li-implantation-failure-route-and-supplement-screen-cycle194.json).

**Song et al. day-14 co-culture source check, 2026-10-11:** the publisher abstract reports a human embryo/endometrial-organoid model through day 14; the inspected supplementary workbook is a cluster-by-five-label proportion table, not an embryo-level outcome ledger. GSE263528 has no PubMed relation; the apparent Zhang X initials match resolves to distinct full names (Xinbao Zhang versus Xinwen Zhang), and no direct sample-to-article crosswalk was found. Keep it unjoined pending direct linkage. Keep the day-14 boundary and per-embryo denominator gap explicit. See the [source screen](SONG_2026_HUMAN_POSTIMPLANTATION_COCULTURE_SOURCE_SCREEN_2026-10-11.md), [inventory](config/source_inventories/song_2026_human_postimplantation_coculture.json), and [screen receipt](artifacts/postimplantation-coculture-2026-10-11/song-postimplantation-source-route-screen-cycle195.json).

**GSE263528 metadata-only intake, 2026-10-11:** a pinned Series record and 11 individual GSM metadata records resolve to 11 unique SRX experiment accessions, submitted in two batches (three in 2024 and eight in 2026). Preserve submitted sample labels without mapping day-2/day-4 to embryo age; GSM/SRX counts do not establish embryo, donor, or assay denominators, and no expression or read data were downloaded. The accession has a BioProject relation but no PubMed relation in the inspected Series metadata; bounded exact PubMed queries returned no match. Correct the earlier initials-only author screen: GEO's Xinbao Zhang is not an exact full-name match to Song et al.'s Xinwen Zhang. Keep the dataset unjoined to Song pending direct provenance and promote no observations. See the [metadata screen](GSE263528_HUMAN_BLASTOID_ENDOMETRIAL_ASSEMBLOID_METADATA_SCREEN_2026-10-11.md), [sample crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_sample_crosswalk.csv), [inventory](config/source_inventories/gse263528_human_embryo_endometrial_assembloid.json), and [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-metadata-screen-cycle196.json).

**Song article-to-repository link check, 2026-10-11:** NCBI PubMed-to-GEO and PubMed-to-SRA ELink requests returned no linked records for PMID 41443195. The checked publisher PDF route returned HTTP 403 and the article-text API route HTTP 429, leaving the data-availability statement unreviewed. Treat these as bounded route outcomes; GSE263528 stays unjoined pending a direct accession crosswalk. No expression files or article supplement were downloaded. See the [linkage receipt](artifacts/postimplantation-coculture-2026-10-11/song-article-to-repository-linkage-cycle197.json).

**GSE263528 SRA run-status crosscheck, 2026-10-11:** NCBI ESearch found all 11 GEO-linked SRX accessions, but each ESummary reported `status=suppressed` with an empty run list. GEO independently lists three supplementary entries per GSM (barcode, feature and UMI-matrix files); none was retrieved. The ENA run-report endpoint did not answer within the bounded wait and was stopped. Preserve this as an access/status boundary, not evidence that raw sequencing data do not exist. No embryo/replicate denominator or outcomes are established. See the [SRA crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_sra_experiment_status.csv), [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-run-status-screen-cycle198.json), and [inventory](config/source_inventories/gse263528_human_embryo_endometrial_assembloid.json).

**GSE263528 processed-matrix route check, 2026-10-11:** HEAD requests to all 11 GSM-listed UMI-matrix URLs returned HTTP 200 and Content-Length metadata. No matrix body or checksum was retrieved. Thus the processed-file route responds despite suppressed SRA experiment summaries, but no matrix values, cell counts, or sample-level outcomes are reviewed. This establishes route reachability only, not matrix integrity or biological denominator. See the [matrix status crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_matrix_head_status.csv) and [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-matrix-head-screen-cycle199.json).

**GSE263528 sidecar integrity screen, 2026-10-11:** temporarily retrieve the 22 GEO-listed barcode/feature sidecars, verify HTTP byte lengths and gzip end-of-stream, and retain only SHA-256 plus file-row counts. All 22 checks passed across 11 GSMs (11,569,917 compressed bytes); raw sidecars were deleted. Treat line counts as file structure, not embryos, donors or outcomes. The 11 UMI matrix routes declare 1,171,938,176 bytes total and remain unfetched; matrix values and per-sample outcomes are still unreviewed. See [sidecar crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_sidecar_integrity_cycle200.csv) and [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-sidecar-integrity-screen-cycle200.json).

**GSE263528 bounded matrix-header crosscheck, 2026-10-11:** each of the 11 matrix URLs accepted a 65,536-byte HTTP range; 720,896 compressed bytes total were sufficient to parse only the Matrix Market header. All header rows/columns match the retained feature/barcode sidecar row counts, and each header's total compressed-file size agrees with HEAD metadata. One file declares 36,602 feature rows and the other ten 36,601, matching their own sidecars. No sparse entry or expression value was read, no prefix was retained, and full matrix bodies/checksums remain unverified. See [dimension crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_matrix_prefix_dimensions_cycle201.csv) and [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-matrix-prefix-screen-cycle201.json).

**GSE263528 full-matrix integrity stream, 2026-10-11 (Cycle 260):** stream the complete 11 GEO-listed gzip Matrix Market files (1,171,938,176 compressed bytes total) without retaining files or expression values. All streams match their HEAD lengths, pass gzip CRC/end-of-file, reproduce the prefix dimensions, and have body-line counts matching the declared 314,202,222 nonzero entries. SHA-256 is recorded per sample. Only each matrix's first and last coordinate records were parsed for bounds; this is structural validation, not expression analysis, cell identity, biological replication or developmental outcome. See [full-integrity crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_matrix_full_integrity_cycle260.csv), [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-matrix-full-integrity-screen-cycle260.json), and [source screen](GSE263528_HUMAN_BLASTOID_ENDOMETRIAL_ASSEMBLOID_METADATA_SCREEN_2026-10-11.md).

**GSE263528 triplet-validation pilot, 2026-10-11 (Cycle 261):** test all sparse records in the smallest matrix (GSM9737919). All 16,843,623 passed three-integer syntax, coordinate-bound and positive-integer count-field checks; its hash matched Cycle 260. The 27-second pilot showed that a full structural pass was practical. See [pilot receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-matrix-triplet-syntax-pilot-cycle261.json).

**GSE263528 sparse-triplet syntax check, 2026-10-11 (Cycle 262):** validate every one of the 314,202,222 matrix records for exactly three integer fields, in-range row/column indices, and positive integer count-field syntax. All 11 files passed; re-streamed compressed SHA-256 values match Cycle 260, and no records or count values were retained. No expression summaries or biological comparisons were computed. See [triplet crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_matrix_triplet_syntax_cycle262.csv), [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-matrix-triplet-syntax-screen-cycle262.json), and [source screen](GSE263528_HUMAN_BLASTOID_ENDOMETRIAL_ASSEMBLOID_METADATA_SCREEN_2026-10-11.md).

**GSE263528 sidecar-key pilot, 2026-10-11 (Cycle 263):** for GSM8194085, verify barcode and feature sidecar keys are nonblank and unique, fields have the expected shape, and hashes/dimensions match prior receipts. Both sidecars passed; extend the check to all samples. See [Cycle 264 crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_sidecar_key_validation_cycle264.csv).

**GSE263528 barcode/feature sidecar consistency, 2026-10-11 (Cycle 264):** recheck all 22 sidecars against Cycle 200 hashes and Cycle 201 dimensions; validate expected row shape, nonblank fields, and uniqueness of barcode/feature keys. All passed across 2,663,026 rows with no duplicate keys or malformed rows; identifiers and raw files were not retained. See [crosswalk](artifacts/gse263528-maternal-interface-2026-10-11/GSE263528_geo_sidecar_key_validation_cycle264.csv), [receipt](artifacts/gse263528-maternal-interface-2026-10-11/gse263528-geo-sidecar-key-validation-cycle264.json), and [source screen](GSE263528_HUMAN_BLASTOID_ENDOMETRIAL_ASSEMBLOID_METADATA_SCREEN_2026-10-11.md).

**GSE263528 publication-index crosscheck, 2026-10-11:** Europe PMC exact accession and exact Series-title queries return zero hits. The Song DOI/PMID record is indexed as MED metadata but has no PMCID, PMC/Europe PMC full text, Europe PMC-indexed supplement, PDF, or text-mined accession flag. These service flags do not establish that a publisher supplement is absent. With the bounded publisher routes still unavailable, the Song data-availability statement and any GSE263528/article crosswalk remain unresolved. No author contact or data promotion. See [Europe PMC query receipt](artifacts/gse263528-maternal-interface-2026-10-11/europepmc-publication-linkage-screen-cycle202.json).

**Song workbook cell and denominator audit, 2026-10-11:** correct the Cycle 195 workbook structure description. `Sheet1` has proportion, count, stage-summary and consolidated Epi/TE blocks. Transcribe 106 exact source cells with labels and locators. All 35 top-block proportions reconcile to paired counts; the stage table has one percent mismatch (`E23` prints 0.01%; the listed count ratio rounds to 0.10%). The bottom summary count aggregation reconciles, but its Epi stage percentages use embryo-only totals while TE uses all-cluster totals; the workbook supplies no explanation. Preserve printed values, add no embryo-level observations, and leave the denominator/independent-unit gap open. See [cell extract](artifacts/postimplantation-coculture-2026-10-11/song-mmc2-source-cell-extract-cycle203.csv) and [audit receipt](artifacts/postimplantation-coculture-2026-10-11/song-mmc2-cell-audit-cycle203.json).

**Song supplemental-figure observation screen, 2026-10-11:** the 14-page publisher MMC1 PDF's Figure S1 caption reports morphology-assessed survival from d.p.f. 6–14 with `n=20` co-cultured and `n=16` sole embryos, plus figure-specific sample counts for diameter, interaction and staining panels. The caption does not define operational survival criteria, per-day denominators, attrition, embryo-linked fates or cohort overlap. Do not digitize graph values or promote these counts to individual survival records. Preserve the PDF hash and selected figure locators in the [Cycle 204 receipt](artifacts/postimplantation-coculture-2026-10-11/song-mmc1-caption-outcome-screen-cycle204.json); the data-availability section remains unreviewed.

**Song article survival and repository-access screen, 2026-10-11:** a third-party mirror of the publisher-typeset article reports d.p.f. 14 morphology-defined survival of 15/20 co-cultured and 6/16 sole-control embryos. The paper defines survival but also reports pre-analysis morphology exclusions and termination at d.p.f. 14 or primitive-streak formation; screened counts and early-stop membership remain unresolved. Preserve the rates as two group-level candidate summaries with separate aggregate cohort-coverage records; no embryo-level identities or fates are inferred. The article names GSA-Human HRA006892 and PRIDE PXD067943. GSA-Human currently labels HRA006892 controlled access despite the article's public-availability wording, while the PRIDE public accession endpoint returned 404 with a known-project control succeeding. Keep GSE263528 unjoined; it has no crosswalk to HRA006892. See the [candidate intake](config/observations/song_2026_postimplantation_survival_candidate.json), [Cycle 205 receipt](artifacts/postimplantation-coculture-2026-10-11/song-article-data-access-and-survival-cycle205.json), and [source screen](SONG_2026_HUMAN_POSTIMPLANTATION_COCULTURE_SOURCE_SCREEN_2026-10-11.md). The third-party mirror's publisher-byte equivalence is unverified.

**Song ProteomeXchange release-state check, 2026-10-11 (Cycle 206):** the official ProteomeXchange route for PXD067943 returns an accession-specific 404 page stating that PRIDE has reserved the accession for a deposited dataset that is not yet publicly released or announced. A known announced-project control resolves; the PRIDE public API still returns 404 for PXD067943. This clarifies the route state as reserved/not announced and the article's publication-time availability claim remains discrepant. It does not establish data absence. No files, reviewer route, access request or release request were used. See the [Cycle 206 receipt](artifacts/postimplantation-coculture-2026-10-11/song-proteomecentral-release-status-cycle206.json).

**Song GSA-Human partial-metadata screen, 2026-10-11 (Cycle 207):** the official HRA006892 page still labels the study controlled access but exposes partial tables to unauthenticated visitors. Its public individual/sample endpoint reports five repository individual accessions paired with five samples; the run endpoint reports ten rows across five samples and five experiments. The page says detailed metadata exports are limited to authorized users. Do not equate these repository rows with the 20/16 survival cohorts; no crosswalk is present. No IDs, detailed metadata export or controlled data files are retained or downloaded, and no request was made. See the [Cycle 207 receipt](artifacts/postimplantation-coculture-2026-10-11/song-gsa-human-public-metadata-screen-cycle207.json).

**Song NGDC BioProject cross-link screen, 2026-10-11 (Cycle 208):** HRA006892 links to PRJCA024289, a title-matched NGDC project whose broader description spans multiple model classes. Its public summary lists five BioSamples with four source-label categories; no label-to-survival-group crosswalk appears. Exact NCBI BioProject/SRA accession searches and an ENA read-run title query return zero rows. Preserve the label counts as repository metadata only; do not equate them with independent embryos, and do not infer data absence from bounded index searches. No sample identifiers or data files were retained or accessed. See the [Cycle 208 receipt](artifacts/postimplantation-coculture-2026-10-11/song-bioproject-crosslink-screen-cycle208.json).

**Song single-cell count reconciliation, 2026-10-11 (Cycle 209):** the article reports stage-associated scRNA `n` labels 25/16/33 at d.p.f. 9/12/14, while the linked project exposes five BioSample label rows and the Key Resources Table names multiple assay modalities under HRA006892. The Figure 4 caption does not independently define the `n` unit, and neither article nor public project summary supplies a sample/library-to-stage-n or survival-cohort crosswalk. Record the source labels but do not treat 74 as a verified embryo count, compare it with survival denominators, or explain the repository count difference. The PDF is a third-party mirror with byte equivalence unverified; no IDs or data files are retained. See the [Cycle 209 receipt](artifacts/postimplantation-coculture-2026-10-11/song-scrna-assay-n-and-repository-reconciliation-cycle209.json).

**Song GSA-Human sample-to-run metadata join, 2026-10-11 (Cycle 210):** join the public sample and run tables in memory, retaining only aggregate label counts: five samples map to ten run rows (2/2/4/2 for d.p.f. 9/12/14/`D14WE`). All list strategy RNA-Seq and platform Illumina NovaSeq 6000, which cannot distinguish the article's GEXSCOPE/10X and Smart-seq2 assay entries. No identifiers, file details or data files are retained or accessed; the run table still does not map to article `n` values or survival groups. See the [Cycle 210 receipt](artifacts/postimplantation-coculture-2026-10-11/song-gsa-sample-run-aggregate-join-cycle210.json).

**Song GSA-Human assay-title token screen, 2026-10-11 (Cycle 211):** search the public experiment and run title fields for the article's GEXSCOPE, 10X and Smart-seq2 labels. No title contains those tokens; the modality-to-run crosswalk remains unresolved because the public fields reviewed are insufficient. Do not read this as data absence. No titles, identifiers or files are retained. See the [Cycle 211 receipt](artifacts/postimplantation-coculture-2026-10-11/song-gsa-title-modality-token-screen-cycle211.json).

**Song GSA-Human experiment-detail field screen, 2026-10-11 (Cycle 212):** five public experiment-detail pages returned HTTP 200 but exposed none of the checked library strategy/name/layout/source/selection or instrument fields in their visible text. The modality-to-run crosswalk remains unresolved; this page-level check does not establish data absence on other routes. No page text, accessions, or files are retained. See the [Cycle 212 receipt](artifacts/postimplantation-coculture-2026-10-11/song-gsa-experiment-detail-field-screen-cycle212.json).

**Song GSA accession mirror check, 2026-10-11 (Cycle 213):** correct the run-table interpretation: ten table rows represent five distinct run accessions (two filename-metadata rows per accession) and five experiment accessions. NCBI SRA returned no hits for a combined exact-accession query; ENA returned zero read-run and read-experiment matches. Keep these as bounded metadata-route results. Do not count ten unique runs, infer file-pair semantics, or interpret zero hits as data absence. No accession strings, filenames or file contents were retained. See the [Cycle 213 receipt](artifacts/postimplantation-coculture-2026-10-11/song-gsa-accession-mirror-check-cycle213.json).

**Song GSA BioSample mirror check, 2026-10-11 (Cycle 214):** exact-accession queries for the five public GSA BioSample records returned zero rows in NCBI BioSample and ENA's sample index. This is an index-route result only, not data absence or proof of no other cross-link. No BioSample accessions, metadata files or sequence data are retained. See the [Cycle 214 receipt](artifacts/postimplantation-coculture-2026-10-11/song-gsa-biosample-mirror-check-cycle214.json).


**Heggarty public placental-transfer figure screen, 2026-10-11 (Cycle 216):**
the CC BY 4.0 Mendeley version-2 package contains two JPEG figures: a study-flow
diagram and per-placenta fetal-transfer-rate (%) plot. The figures report
transfer parameters for 11 dabrafenib and 7 trametinib placentas, but expose no
source-exact numeric rows, time-resolved concentrations, volume/removal history,
recovery, or assay uncertainty. The PubMed record has no abstract and the
publisher route returned HTTP 403, so the metric definition and gestational
frame remain unverified. Keep this as a figure-level functional-transfer
comparator, not a dimensional transport-fit dataset. No points were digitized
and no author was contacted. See the [source screen](HEGGARTY_2025_DABRAFENIB_TRAMETINIB_PERFUSION_SCREEN_2026-10-11.md),
[inventory](config/source_inventories/heggarty_2025_dabrafenib_trametinib.json),
and [Cycle 216 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/manifest-and-figure-screen-cycle216.json).


**Related IFPA abstract cross-check, 2026-10-11 (Cycle 217):** the official
2025 IFPA abstract P2.58 reports normal-term human placentas and group FTR
summaries of 8.6 ± 3.1% for trametinib and 15.3 ± 5.4% for dabrafenib. These
values match the Mendeley plot centers to visual precision, but the abstract
does not define ±, provide n or an FTR equation, or explicitly link its cohort
to the JAAD figure package. Treat it as related aggregate context, not an
independent replicate or row-level data. No values were promoted. See the
[Cycle 217 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ifpa2025-abstract-screen-cycle217.json)
and [source screen](HEGGARTY_2025_DABRAFENIB_TRAMETINIB_PERFUSION_SCREEN_2026-10-11.md).

**Related AJOG/SMFM record access check, 2026-10-11 (Cycle 218):** the official
EM Consulte record and SMFM program confirm the 2024 presentation identity,
title, authorship context and journal pages. EM Consulte's public article view
shows section headings but states that full text requires a subscription; its
linked PDF could not be read through the public web reader. A secondary-index
claim of 12 dabrafenib and 11 trametinib placentas successfully tested remains
unverified in accessible primary result text and is not reconciled to the
later 2025 JAAD flowchart. No values were promoted and no author was contacted.
See the [Cycle 218 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ajog-abstract-access-screen-cycle218.json).

**Related AJOG DOI-index check, 2026-10-11 (Cycle 219):** exact DOI-field
querying through PubMed E-utilities returns zero records, and Crossref's DOI
metadata has no abstract field. These index results do not mean the abstract is
absent; they add no evidence for the reported 12/11 counts or the cohort link.
See the [Cycle 219 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ajog-abstract-index-screen-cycle219.json).

**Related AJOG HAL archive check, 2026-10-11 (Cycle 220):** exact DOI and
title-phrase queries returned no HAL record for the 2024 abstract. A known
related 2025 JAAD DOI returned one metadata-only HAL record as a query control;
this validates the DOI field for that item but not HAL-wide coverage. No
abstract file was accessed and no counts or cohort links were inferred. See the
[Cycle 220 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ajog-abstract-hal-screen-cycle220.json).

**Secondary-index abstract lead, 2026-10-11 (Cycle 221):** a DOI-matched
SciSpace page exposes an abstract copy reporting 11 trametinib and 12
dabrafenib/metabolite successes, plus aggregate FTR, clearance-index and uptake
values. These do not fully match the official IFPA 2025 summaries, and the copy
is not verified against the subscription-gated publisher PDF. Keep as a
discovery lead only: no pooling, cohort reconciliation or observation
promotion. See the [Cycle 221 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ajog-secondary-abstract-screen-cycle221.json).

**Publisher metadata-export check, 2026-10-11 (Cycle 222):** EM Consulte's
public “with abstract” citation export returned a successful 470-byte text
attachment with an empty abstract field. Its volume/issue/pages also conflict
with the landing page citation. This only qualifies the metadata-export route;
it does not describe the subscription-gated PDF. See the
[Cycle 222 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ajog-metadata-export-screen-cycle222.json).

**Official SMFM program content check, 2026-10-11 (Cycle 223):** the event page
confirms the presentation slot and authors but exposes no abstract text, result
values, or download link in the inspected view. This is a page-level boundary
only; other meeting routes were not assessed. See the
[Cycle 223 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/smfm-program-detail-screen-cycle223.json).

**AJOG public Figures-route check, 2026-10-11 (Cycle 224):** the official
Figures tab resolves to the gated article shell and exposes no result figure,
caption or downloadable figure in the inspected public view. This does not
characterize the subscription PDF; no values were digitized. See the
[Cycle 224 receipt](artifacts/heggarty-2025-perfusion-2026-10-11/ajog-figures-tab-screen-cycle224.json).

**Benoit et al. 2026 aggregate perfusion comparator, 2026-10-11 (Cycle 225):**
the PubMed abstract reports osimertinib FTR 9.5%, CI 0.41 and cotyledon
accumulation 28.9%; for alectinib/M4 it reports no fetal detection and placental
accumulation 370.7%/178.3%. A publisher-indexed discussion excerpt gives median
CI 0.42, an unresolved discrepancy. Full text was unavailable and no group
denominators or individual rows were captured. Keep this separate from the
dabrafenib/trametinib studies; no values were promoted. See the
[Cycle 225 receipt](artifacts/benoit-2026-osimertinib-alectinib-2026-10-11/pubmed-and-publisher-screen-cycle225.json).

**Benoit et al. 2026 repository-linkage check, 2026-10-11 (Cycle 226):**
Europe PMC provides no PMCID/full-text URL, PubMed-to-PMC ELink returns no link,
HAL and quoted exact-DOI Zenodo searches return zero, and Crossref lists no
related dataset. Zenodo's unquoted query returned HTTP 500, not a negative
result. This does not resolve the publisher statement that supporting data are
detailed in the article. See the
[Cycle 226 receipt](artifacts/benoit-2026-osimertinib-alectinib-2026-10-11/repository-linkage-screen-cycle226.json).

**Benoit et al. 2026 public repository search, 2026-10-11 (Cycle 227):**
Mendeley Data's public exact-DOI search returned zero; Figshare exact-title
search returned zero, while its DOI-string query returned 10 broad records
without a target match; DataCite's related-identifier query returned zero.
The Figshare DOI result is not a comprehensive negative, and none of these
checks establishes data absence. No files were accessed and no observations
were promoted. See the [Cycle 227 receipt](artifacts/benoit-2026-osimertinib-alectinib-2026-10-11/repository-search-screen-cycle227.json).

**Benoit et al. 2026 OpenAIRE relation check, 2026-10-11 (Cycle 228):**
The exact-DOI query returns the target closed-access publication record, but
its relations field is null. Exact-DOI and conjunctive two-term title searches
on the dataset endpoint return zero. Treat these as bounded index results,
not proof of data absence. See the [Cycle 228 receipt](artifacts/benoit-2026-osimertinib-alectinib-2026-10-11/openaire-relation-screen-cycle228.json).

**Benoit et al. 2026 OpenAlex location check, 2026-10-11 (Cycle 229):**
OpenAlex marks the DOI closed access, reports no best open location, and lists
only the publisher and PubMed records. This is an index check, not proof that
no other copy or supplement exists. See the [Cycle 229 receipt](artifacts/benoit-2026-osimertinib-alectinib-2026-10-11/openalex-location-screen-cycle229.json).

## M7 — Add physiological scope only where it can be tested

After the relevant verification and data gates, consider coupled transport,
growth/remodeling or endocrine observation models. Each proposal needs an
explicit question, equations, parameter provenance, measurements, a simpler
comparator, identifiable quantities and falsifiers before implementation.

Do not prioritize additional disconnected toy models, a gestation readiness
score, device assembly instructions or biological operating parameters. The
most useful contribution is a model whose limitations another researcher can
reproduce and challenge.

## Order and reviewable outputs

1. Stage-transition/source-review records, executable observation validation
   and empirical data qualification (E1–E3; M4 and the M6 intake audit),
   alongside bounded numerical/uncertainty work (M1–M2).
2. One frozen empirical interface question and eligible baseline comparison
   (E4/M6), or an explicit data/non-identification report if the gate fails.
3. Portable verified dossier (E6/M5) and the synthetic observer benchmark
   after forecast calibration (E5; M2–M3).
4. A scoped next model or methods manuscript after independent review (M7).

Each milestone should produce a small release, executable example, documented
negative cases and concrete contributor tasks. A reviewed benchmark and
methods write-up are stronger evidence of research software ability than
repository count; they do not guarantee novelty, publication or employment.


**Placental transfer model-identifiability comparison, 2026-10-11 (Cycle 230):**
Among Mathiesen 2020, Heggarty 2025 and Benoit 2026, none currently meets
the per-run concentration plus time-resolved volume/removal gate for a
dimensional transport fit. Mathiesen provides the concentration workbook but
not the linked volume/removal ledger; Heggarty is figure/abstract level; Benoit
is aggregate abstract level. The strongest next intake target remains the
Spiess 2023 supplement, pending resolution of its official PMC file route.
These sources inform placental transfer measurement only, not embryo support
or artificial-womb outcomes. See the [Cycle 230 receipt](artifacts/perfusion-comparability-2026-10-11/transfer-identifiability-screen-cycle230.json).

**Spiess et al. 2023 PMC supplement route check, 2026-10-11 (Cycle 231):**
The official PMC article page is readable and exposes a named 2 MB Supporting
Information PDF. The linked attachment responds to HEAD with HTML challenge
content rather than a PDF; the legacy OA package endpoint returns 404. No
supplement content was retrieved or extracted. See the [Cycle 231 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-pmc-supplement-route-cycle231.json).

**Faure Bardon et al. 2020 source-cell reconciliation, 2026-10-11 (Cycle 232):**
All 912 source value lexemes match; 288 paired nonblank FC/MC/FTR records
recompute within 1e-5. The pass exposed 259 shared-formula followers whose
formula/cache metadata was omitted from the CSV; Cycle 233 added their shared
group and cache provenance and a standard-library audit. The corrected 304
formula mappings now match the pinned workbook. This supports descriptive
source-defined concentration ratios only; human review and dimensional-fit
gaps remain open. See the [Cycle 232 finding](artifacts/perfusion-intake-2026-10-10/faure-bardon-s1-reconciliation-cycle232.json)
and [Cycle 233 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-s1-formula-provenance-cycle233.json).

**Faure Bardon et al. 2020 shared-formula provenance repair, 2026-10-11 (Cycle 233):**
The intake now records all 304 mapped formula cells, including 281 shared
formulas and 259 follower cells without local expression text. The validator
checks group index/range/master cell and cached value, and rejects a changed
source cell even if the CSV hash is updated in the manifest. Source values and
record IDs are unchanged; dimensional model eligibility is unchanged. See the
[Cycle 233 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-s1-formula-provenance-cycle233.json).

**Faure Bardon et al. 2020 letermovir summary-label crosscheck, 2026-10-11 (Cycle 234):**
The PLOS Results reports five validated LMV perfusions; Table 3 gives no n or
label crosswalk, while the S1 summary formulas use four of five visible labels.
The primary source gives no explanation. Retain all five raw series and do not
recalculate or reinterpret the published group summary. See the [Cycle 234 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-summary-label-check-cycle234.json).

**Faure Bardon et al. 2020 public peer-review history, 2026-10-11 (Cycle 235):**
The reviewer raises the small 3/5 validated MBV/LMV sample sizes; the authors
explain the antipyrine threshold and procedural cost, and the reviewer accepts
the response after requesting a limitation statement. The published responses
do not link the five LMV workbook labels to the validated procedures or explain
the four-label formulas. A bounded DOI/correction query surfaced no correction
notice. Preserve the discrepancy without reclassifying labels. See the
[Cycle 235 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-peer-review-history-cycle235.json).

**Faure Bardon et al. 2020 antipyrine label diagnostic, 2026-10-11 (Cycle 236):**
At the paper's reported LMV steady-state onset (30 min), source FTR values for
labels 1, 2, 4 and 5 are over 20%; label 3 is below. The workbook summaries use
labels 1-4 and omit 5. Since the paper does not define the 30-minute row as the
per-run validation decision statistic, this does not resolve the discrepancy.
Keep the comparison diagnostic-only. See the [Cycle 236 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-antipyrine-label-diagnostic-cycle236.json).

**Faure Bardon et al. 2020 formula-count consistency, 2026-10-11 (Cycle 237):**
Corrected a stale nested manifest formula count (45 to 304) and extended the
source-cell auditor to reject inconsistent formula/cache metadata. A negative
test covers the stale-count case. Source workbook, CSV, and observations are
unchanged. See the [Cycle 237 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-formula-count-consistency-cycle237.json).

**Faure Bardon et al. 2020 chart-summary scope, 2026-10-11 (Cycle 238):**
The workbook's LMV chart reads its mean and SD columns, which summarize labels
1-4 across 19 timepoints. It does not contain a separate label-5 series and
does not resolve why that label is absent from the summary. Preserve raw label
data and formula references. See the [Cycle 238 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-chart-summary-scope-cycle238.json).

**Faure Bardon et al. 2020 workbook structure screen, 2026-10-11 (Cycle 239):**
The sheet is visible and has no defined names, filter, or hidden columns affecting
the fifth label or summary. No structural state explains the omission; author
intent remains unknown. See the [Cycle 239 receipt](artifacts/perfusion-intake-2026-10-10/faure-bardon-workbook-visibility-screen-cycle239.json).

**Placental-perfusion intake priority recheck, 2026-10-11 (Cycle 240):**
Spiess et al. 2023 protopine remains the highest-potential source for linked
recovery, concentration and endpoint-volume fields, but the official file route
is challenged and the repository offers request-copy access. The accessible
Spiess comparator has group curves and endpoint volume loss, not time-resolved
per-run accounting. Mathiesen remains the strongest audited concentration
dataset; none meets the dimensional-fit gate. Next, check only unchallenged
official metadata and publisher routes. See the [Cycle 240 receipt](artifacts/perfusion-comparability-2026-10-11/perfusion-source-priority-recheck-cycle240.json).

**Spiess protopine supplement route recheck, 2026-10-11 (Cycle 241):**
Europe PMC's full-text XML exposes the article and supplement filename, but its
file-serving path returned 403; the checked Thieme article-PDF route returned
404. No supplement bytes were retrieved. Close this route screen and move to
the accessible Spiess Frontiers comparator for field availability only. See the
[Cycle 241 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-europepmc-publisher-route-cycle241.json).

**Spiess Frontiers supplement field-availability audit, 2026-10-11 (Cycle 242):**
The group curves and per-experiment table have matching compound denominators
(4/3/4), but no table-run-to-curve key is supplied. The table reports signed
volume loss only at experiment end, not a time-resolved removal/volume ledger.
The source remains comparator-only. Next, audit the Eliesen 2024 individual
trajectory intake. See the [Cycle 242 receipt](artifacts/perfusion-comparability-2026-10-11/spiess-frontiers-field-availability-cycle242.json).

**Eliesen et al. 2024 Table S3 source-cell reconciliation, 2026-10-11 (Cycle 243):**
Added a standard-library audit that matches all 70 source time/series cells to
the pinned publisher DOCX and observation CSV. All 69 numeric lexemes match;
the no-placenta control's 1-minute `N/A` remains not assessed. The DOCX holds
literal text values, with no formula/cache layer. This confirms transcription
integrity only; human source review is pending, and the run-level volume,
sample-removal, and recovery records needed for dimensional fitting remain
absent. See the [Cycle 243 receipt](artifacts/perfusion-intake-2026-10-10/eliesen-table-s3-source-reconciliation-cycle243.json)
and [intake note](ELIESEN_2024_TOFACITINIB_SOURCE_RECONCILIATION_2026-10-11.md).

**Eliesen et al. 2024 Table S3 group-summary check, 2026-10-11 (Cycle 244):**
Recomputed arithmetic means and sample SDs for the three placenta labels at
each time, excluding the system-control series with unspecified n. The
180-minute maternal values reproduce 35.6 ± 5.5 nM. The fetal table values
produce 25.0 ± 5.0 nM, differing from the Results text's 24.8 ± 4.7 nM; their
one-decimal mean intervals do not overlap. Preserve both, pending human review.
Figure 2 was not digitized. See the [Cycle 244 receipt](artifacts/perfusion-intake-2026-10-10/eliesen-table-s3-group-summary-cycle244.json)
and [summary note](ELIESEN_2024_TOFACITINIB_GROUP_SUMMARY_CHECK_2026-10-11.md).

**Eliesen et al. 2024 antipyrine Table S2 endpoint control, 2026-10-11 (Cycle 245):**
Recomputed 180-minute maternal and fetal antipyrine mean/sample-SD summaries
from the same pinned supplement. Both reproduce the article after rounding,
providing a companion-table column-mapping control. No antipyrine values were
added to the tofacitinib intake, and the separate fetal Table S3 discrepancy
remains unresolved. See the [Cycle 245 receipt](artifacts/perfusion-intake-2026-10-10/eliesen-antipyrine-s2-endpoint-control-cycle245.json).

**Eliesen et al. 2024 public companion-dataset route screen, 2026-10-11 (Cycle 246):**
The Crossref work record has no dataset relations, the exact DataCite related-DOI
query returns zero records, and the publisher lists only the DOCX supplement with
data available on request. These are bounded metadata results, not a global
absence claim. No author contact was made. See the [Cycle 246 receipt](artifacts/perfusion-comparability-2026-10-11/eliesen-public-dataset-route-screen-cycle246.json)
and [intake note](ELIESEN_2024_PUBLIC_DATASET_ROUTE_SCREEN_2026-10-11.md).

**Mandelbrot et al. 2019 source-cell triage, 2026-10-11 (Cycle 247):**
The strongest remaining public machine-readable candidate has 94 placenta-label
timepoint rows, and all 658 selected field values match the pinned XLSX. However,
68 antipyrine-ratio cells are shared-formula followers with cached values but no
local formula text; their shared-group index/range/master metadata is absent from
the intake. The manifest's field count of 22 represents local formula-expression
text, not all 90 formula-bearing cells in that field. No linked volume/removal/
recovery data are present. Next add a bounded tested validator and repair this
provenance distinction. See the [Cycle 247 receipt](artifacts/perfusion-intake-2026-10-10/mandelbrot-s1-source-cell-triage-cycle247.json)
and [intake note](MANDELBROT_DOLUTEGRAVIR_PERFUSION_INTAKE_2026-10-10.md).

**Mandelbrot et al. 2019 shared-formula provenance repair, 2026-10-11 (Cycle 248):**
The 68 antipyrine-ratio shared-formula followers now retain group index, range,
and master-cell metadata; the manifest distinguishes 465 formula-bearing cells
from 397 local expression strings. A new bounded validator reconciles all 658
selected cached values, formula text, group metadata, row keys and missingness.
Tamper tests cover altered cached values, group metadata, and a stale formula
count. Values are unchanged and formulas remain unevaluated; the unbundled
external workbook and volume/removal/recovery records are still missing. See
the [Cycle 248 receipt](artifacts/perfusion-intake-2026-10-10/mandelbrot-s1-formula-provenance-reconciliation-cycle248.json)
and [validator](src/wombmodels/mandelbrot_source.py).

**Ashley et al. 2022 source-cell reconciliation, 2026-10-11 (Cycle 249):**
The candidate's 30 per-perfusion endpoints now reconcile against their exact
cells and five workbook labels; all 207 nonempty source-ledger cells also match
the pinned Figure 1 workbook. Ten row-6 records preserve the workbook's omitted
`/min` unit as a typed qualification to the article's Figure 1b rate unit.
Tamper tests reject altered values and removed qualifications. The 24,25D
block and placenta-only 1,25D row remain excluded, and human review is pending.
See the [Cycle 249 receipt](artifacts/perfusion-intake-2026-10-10/ashley-figure1-source-reconciliation-cycle249.json),
[source screen](ASHLEY_2022_VITAMIN_D_PERFUSION_SOURCE_SCREEN_2026-10-10.md),
and [validator](src/wombmodels/ashley_source.py).

**Ashley et al. 2022 endpoint-summary check, 2026-10-11 (Cycle 250):**
Recomputed the mean, sample SD and SEM for all six included per-perfusion
endpoint groups. All 18 summary statistics match the workbook's literal summary
cells within 1e-12 absolute tolerance. The five-label 25(OH)D3 partition also
closes exactly at stored precision. Because the component values may share
calculations, this is an arithmetic identity rather than independent validation;
no observations were added and no transport fit was performed. See the
[Cycle 250 receipt](artifacts/perfusion-intake-2026-10-10/ashley-endpoint-summary-check-cycle250.json),
[source screen](ASHLEY_2022_VITAMIN_D_PERFUSION_SOURCE_SCREEN_2026-10-10.md),
and [summary checker](src/wombmodels/ashley_summary.py).

**Holm et al. 2017 aggregate amino-acid summary intake, 2026-10-11 (Cycle 251):**
Add an optional typed `median_iqr` distribution field to observations and
export it losslessly in intake CSV. The candidate carries all 76 Table 2
analyte-by-vessel summaries, source literals and exact table-cell locators; its
vessel N remains explicitly non-analyte-specific. The unusual alanine
uterine-vein literal `255 [2, 294]` is flagged and preserved. These data remain
aggregate term in-vivo concentrations, separate from perfusion values and
ineligible as flux or developmental-support evidence. See the [Cycle 251
receipt](artifacts/observation-intake-2026-10-11/holm-table2-typed-summary-intake-cycle251.json),
[candidate intake](config/observations/holm_2017_term_amino_acid_concentrations_candidate.json),
and [source screen](HOLM_2017_AMINO_ACID_INTAKE_SOURCE_SCREEN_2026-10-10.md).

**Holm et al. 2017 paired-difference summary intake, 2026-10-11 (Cycle 252):**
Create a separate 76-record Table 3 candidate for crude and water-adjusted
arteriovenous/venoarterial concentration differences. Preserve each median and
Q1/Q3, circulation-level N scope, exact p-value literal, source bold marker, and
the paper's positive-difference convention as a source-linked declaration.
Tamper tests protect the p-value and FDR-marker provenance. These remain
aggregate concentrations, not participant pairs or flux observations. See the
[Cycle 252 receipt](artifacts/observation-intake-2026-10-11/holm-table3-paired-differences-cycle252.json),
[candidate intake](config/observations/holm_2017_term_amino_acid_differences_candidate.json),
and [source screen](HOLM_2017_AMINO_ACID_INTAKE_SOURCE_SCREEN_2026-10-10.md).

**Holm et al. 2017 publisher-PDF visual check, 2026-10-11 (Cycle 253):**
Render Table 2 from the publisher's version-of-record PDF and visually inspect
the Alanine / uterine-vein cell. The printed glyph is `2`, matching the XML and
PDF text extraction; retain `255 [2, 294]` while leaving its scientific/source
plausibility unresolved. Pin the PDF SHA-256 and printed-page locator in the
source inventory. No candidate value changed, participant data were not
accessed, and no author was contacted. See the
[source screen](HOLM_2017_AMINO_ACID_INTAKE_SOURCE_SCREEN_2026-10-10.md) and
[source inventory](config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json).

**Holm et al. 2017 Table 2 publisher-PDF reconciliation, 2026-10-11 (Cycle 254):**
Extract the ordered median/Q1/Q3 numeric groups from the publisher PDF text layer
and compare them with the XML-derived 76-cell ledger. All 76 summaries (228
numeric fields) match exactly after whitespace normalization. This confirms
cross-representation transcription agreement only; it does not validate
participant-level observations or recalculate the study analysis. See the
[Cycle 254 receipt](artifacts/observation-intake-2026-10-11/holm-table2-pdf-reconciliation-cycle254.json)
and [source inventory](config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json).

**Holm et al. 2017 Table 3 publisher-PDF reconciliation, 2026-10-11 (Cycle 255):**
Extract the 76 ordered median/Q1/Q3 summaries and printed p-values from the
publisher PDF text layer and compare them with the XML-derived paired-difference
ledger. All 76 summaries and p-value literals match. Plain text does not verify
bold formatting, so the XML-derived FDR markers remain the preserved source;
statistical tests and adjusted p-values are not recalculated. See the
[Cycle 255 receipt](artifacts/observation-intake-2026-10-11/holm-table3-pdf-reconciliation-cycle255.json)
and [source inventory](config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json).

**Holm et al. 2017 Table 3 PDF bold-marker check, 2026-10-11 (Cycle 256):**
Classify the embedded font in each of the 76 Table 3 summary-cell boxes and
compare it with the XML-derived bold/FDR marker. All 76 printed styles agree
with the ledger. This confirms formatting transcription, not the FDR calculation.
See the [Cycle 256 receipt](artifacts/observation-intake-2026-10-11/holm-table3-bold-marker-pdf-check-cycle256.json)
and [source inventory](config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json).

**Holm et al. 2017 table-header and denominator check, 2026-10-11 (Cycle 257):**
Confirm both PDF header rows against the ledgers. Table 2's vessel order, μmol/L
unit and N values (168, 177, 177, 162) match; Table 3's circulation order,
μmol/L unit and n values (166, 160) match. Retain the denominators at their
printed vessel/circulation scope, not as analyte-specific Ns. See the
[Cycle 257 receipt](artifacts/observation-intake-2026-10-11/holm-table-header-denominator-check-cycle257.json)
and [source inventory](config/source_inventories/holm_2017_in_vivo_amino_acid_summary.json).

**Song et al. 2026 full-text route check, 2026-10-11 (Cycle 258):**
Query the official NCBI PMC ID converter and Europe PMC record for PMID 41443195.
Neither checked route exposes the article full text; the candidate survival
summary therefore remains supported by a third-party mirror whose equivalence
to the publisher PDF is unverified. Keep the current candidate qualification
and do not seek author contact. See the
[Cycle 258 receipt](artifacts/postimplantation-coculture-2026-10-11/song-pmc-fulltext-route-screen-cycle258.json)
and [source screen](SONG_2026_HUMAN_POSTIMPLANTATION_COCULTURE_SOURCE_SCREEN_2026-10-11.md).

**Song et al. 2026 publisher-route check, 2026-10-11 (Cycle 259):**
The official ScienceDirect record reports open access and a CC BY license, but
its page and three tested publisher full-text/PDF routes returned HTTP 403 from
this environment. No publisher article body was obtained and no mirror
byte-equivalence was established. Keep the two survival summaries
mirror-qualified. See the [Cycle 259 receipt](artifacts/postimplantation-coculture-2026-10-11/song-publisher-route-screen-cycle259.json),
[source screen](SONG_2026_HUMAN_POSTIMPLANTATION_COCULTURE_SOURCE_SCREEN_2026-10-11.md),
and [official publisher listing](https://www.sciencedirect.com/science/article/pii/S1934590925004369).

# Early-support architecture and observation decision

Date: 11 October 2026
Roadmap tasks: T01, T02, T04 and T16
Scope: early embryo support; offline evidence intake; no author contact.

## Decision

Keep the hybrid living-interface route as a testable lead hypothesis, with staged support and more synthetic replacement retained as comparators. Do not select or buy a gestation architecture from the present evidence. The next scarce research resource should go to a source-qualified, identity-linked observation path that distinguishes **material delivery to the recipient (D)**, **use or processing in the recipient tissue (M)**, and **stage-appropriate developmental progression (P)** in the same source-defined units. This result moves the program's immediate allocation from architecture preference to measurement eligibility; it does not change any biological gate.

The reason is concrete. A current human embryo/endometrial-organoid co-culture report reaches a day-14 post-fertilization endpoint with reported developmental landmarks and shows that disrupting maternal signals impairs progression. That makes it a useful early-interface comparator. It is still an early model, not an external gestation machine or a demonstrated connection from a working exchange interface to later development. The paper's PubMed abstract states its scope and endpoint directly: [Song et al., *Cell Stem Cell* (2026)](https://pubmed.ncbi.nlm.nih.gov/41443195/).

The distinction between D, M and P matters because those measurements can disagree. A mouse genetic study reported preserved uptake/transfer despite impaired intracellular metabolic function and developmental outcomes in a specific in-utero disease model. That supports measuring each link separately; it does not demonstrate that any artificial support architecture will work: [LIPT1 study, *Nature* (2022)](https://www.nature.com/articles/s41586-022-04557-9).

| Allocation under comparison | Expected advantage | Discriminating observation | Result that weakens this allocation |
| --- | --- | --- | --- |
| Living-interface hybrid with external support functions | Retains coupled, changing extraembryonic and tissue interactions while using engineered functions where the living interface does not suffice | In the same units, source-defined interface function and external support are related to recipient tissue use and independent progression across stages | Interface/function measures remain present while tissue use or progression repeatedly fails, or the needed functions cannot be independently attributed |
| Staged support | Allows different support allocations across developmental intervals | Same-unit D/M/P immediately before and after each source-defined transition, including every loss or missing outcome | The transition produces unexplained discontinuity, attrition, or loss of function that cannot be bounded with existing observations |
| More fully synthetic replacement | Makes required functions explicit and potentially independently controllable | Each allocated function is measured separately and tied to same-unit M and P, with a comparator for the simpler allocation | Transport or component tests pass while tissue use or stage-appropriate progression does not |

The available evidence does not yet distinguish these predictions. A result showing D with impaired M or P changes effort away from delivery-only hardware and toward measuring or supplying the downstream function. Concordant D/M/P plus complete unit accounting would keep an allocation eligible for the next comparison, but would not establish causal sufficiency. Species differences, stage clocks, group-selection rules, missing identities and terminal measurements are confounds; they can make apparent continuity look stronger than the source supports.

## Bounded candidate-data screen

I screened the eight local observation-dataset JSON files that contain an early-stage record (`preimplantation`, `implantation_and_placentation` or `postimplantation_embryonic`). Together they contain 976 observation rows, of which 947 are early-stage tagged; the remaining 29 are other-stage rows in the same dataset cards. The 947 early rows cover seven mouse candidate datasets and one human candidate dataset. All eight declare source review state `candidate`.

| Candidate intake | Species | Early-stage rows | Source time labels in the intake |
| --- | --- | ---: | --- |
| Aguilera-Castrejon 2021, two source-data cards | Mouse | 222 | Days post coitum |
| Bondarenko 2023 coordination | Mouse | 11 | Source hours and stage/day labels |
| Hiraoka 2025 maternal interface | Mouse | 682 | Mixed source hours, context and stage labels |
| Jin 2026 yolk-sac candidate | Mouse | 4 | Source embryonic-stage labels |
| Koike 2023 material handoff | Mouse | 14 | Source embryonic-stage labels |
| Lokshtanov 2026 terminal candidate | Mouse | 12 | Source embryonic-stage/culture labels |
| Song 2026 post-implantation survival | Human | 2 | Days post fertilization |

The exact candidate-card inputs and byte revisions used for this screen are:

| Input card | SHA-256 |
| --- | --- |
| `config/observations/aguilera_castrejon_2021_length_source_candidate.json` | `2d5890793c4d1bce1f29bbec42f1760b06ac7fd70954b06835ceb97abeae1c94` |
| `config/observations/aguilera_castrejon_2021_source_data_candidate.json` | `e2944323772e4fc5b79b7253459480f23664b022b4618f305f3074a2ee078af8` |
| `config/observations/bondarenko_2023_coordination_candidate.json` | `37307d0f87c2e77f98d5a365c3f913c35dd31f4ca2e5a6b3af67adf7e55da270` |
| `config/observations/hiraoka_2025_maternal_interface_candidate.json` | `d737d0f77bb0cb157d5c00b6f8fe8a4f8a2d1da73960a59cb7906365506da2a6` |
| `config/observations/jin_2026_yolk_sac_candidate.json` | `c8d93f108fd33261245d7f8a3ffc888abdc078be98d4f594c74f134a242e1fac` |
| `config/observations/koike_2023_material_handoff_candidate.json` | `09a520d7dbbaf414801e8cb1c8db1e8fcde53a1ff307ce6441c2aba633a03d34` |
| `config/observations/lokshtanov_2026_terminal_candidate.json` | `2e7d07f5b8cd850aba510682ff4cbf82f71df921950de66e2a2d6df3f3e81a08` |
| `config/observations/song_2026_postimplantation_survival_candidate.json` | `b5e51a619c19cd53d14c3fbe44214cb33757dd8226cabfc71ab4d52a4193fec6` |

Across these 947 early-stage rows, **zero have a non-null source-reported independent-unit identifier, and zero of the eight dataset cards declare a measurement-pair link**. Six cards do contain seven transition records, but every one labels continuity `not_reported` and describes a gap or unlinked branch; none demonstrates same-unit continuity. The candidate records therefore cannot identify a same-unit D→M→P chain or estimate its within-unit association. This is a metadata-level result for the repository's current imported candidates, not proof that no additional public or controlled data exist. Each candidate dataset passes the repository's offline `validate-observations` intake command; that validates its declared structure, not source transcription, reuse rights, scientific review or biological adequacy. Source clocks, species, stages and endpoints remain separate and must not be concatenated.

The Song candidate is the closest human early-interface entry in this screen. Its two records describe separate group outcomes, not embryo rows; its source-linked candidate card records no embryo identifiers, no explicit pairs and unresolved screened-population/early-stop mappings. It can support a bounded group-summary description after source review, but cannot answer the same-unit question above. The repository's candidate intake points to the article DOI and marks the third-party full-text copy as not byte-verified; the structural validator does not resolve that source limitation.

**Eligibility ruling:** descriptive summaries of individual source-defined groups may be possible after source-specific review and rights checking. A predictive analysis of whether D or M forecasts P, and any causal comparison of architecture allocations, are **not eligible** from this screen. The required identities, linkage, common cohort definition, outcome timing, complete starting denominator and source/reuse basis are not established. No effect estimate or architecture ranking is produced.

## Minimum data contract for the next empirical decision

An institution or existing dataset must provide source-linked records sufficient to answer this question without inferring identity from matching labels:

1. A frozen starting roster and stable, de-identified unit key; parent/sample hierarchy; source-reported inclusion, exclusion, assay withdrawal, loss and final disposition for every starting unit.
2. Species/model, starting state, stage definition, stage-source citation, source clock and units for every observation. Separate stage labels and denominators remain separate until source evidence supports a join.
3. For each observation, a named compartment, material/readout, measurement role, quantity basis, time, assay context, source locator and any source-reported calibration or uncertainty. Classify D, M and P from the declared measurement and source—not from endpoint wording.
4. Explicit source-linked relationships connecting D, M and P within the same unit, including source-defined timing and whether a measurement is repeated, destructive or terminal. A source-defined group label or a curator's matching of dates is not a same-unit link.
5. Comparator/allocation, assessment window, adverse outcomes, missingness and complete cohort coverage. P is measured independently of the support proxy used for D or M.
6. Source version, data-access route, reuse terms, exact source locator, and a review state. Retain raw-versus-summary provenance and record what is not available.

At least three outcomes would change the next allocation. If D is present while M or P is impaired in linked units, reject “delivery alone is adequate” and prioritize the missing tissue-use/development function. If D, M and P remain linked and concordant across relevant stages with full starting-unit accounting, retain that allocation as a candidate for the next qualified comparison, not as proof of sufficiency. If the data lack identity or source rights, stop analysis and fund access to the missing records or a qualified prospective measurement capability. No biological operating values or procedure are specified here.

## First prediction-to-measurement loop

**Frozen qualitative prediction:** a delivery-only readout can disagree with tissue-use or developmental outcomes; consequently, a system that declares support adequate from D alone will sometimes misclassify a unit relative to independently assessed M and P. This prediction is deliberately qualitative because the current candidate inputs do not identify a common-unit numeric benchmark.

**Comparator:** the transport-only classification versus a separate joint assessment of D, M and P using source-defined records from the same unit. Do not fit a numeric threshold, combine species, or label this a blind prediction. The immediate replay boundary is the existing `validate-observations` pipeline on the eight local early-stage candidate dataset cards. It completed successfully on all eight, including the human Song card. This verifies the record format and exposes identity/pairing gaps; it is not an empirical feedback iteration and does not confirm the declared sources.

**Discrepancy response:** a disagreement between transport and outcome reopens the relevant allocation and measurement definition; a failed identity, time, rights or denominator check blocks the analysis and triggers the data-contract route. Preserve the source rows and old prediction, record the review and exact discrepancy, then update the design register. Independent scientific review remains pending.

**Next prospective question for a qualified research team:** within each complete starting cohort, which source-defined measurements of recipient delivery and tissue use are linked to independent stage-indexed progression and all-unit disposition in the same units, and which alternative support allocation best explains discordant outcomes? This is a measurement question, not a protocol.

## Resource and ownership implications

The currently available path is the local Windows computer, this repository's Python standard-library analysis/validation tools, and source-linked JSON/CSV plus inventoried workbook/PDF material. The user-estimated 24–48 AI agent-hours per week is not verified as account capacity. This workspace does not identify an accessible wet-lab or measurement facility, instrument data feed, qualified operating team, independent reviewer, quote or cash budget. Those capabilities are **unverified outside this workspace**, not asserted absent from the owner's life.

No new GPU workload is justified by this intake: the present blocker is linked biological data and specialist measurement capacity. Keep T08's owner-led, acquisition/licensing and co-development comparison active. Later-fetal platforms may be an owned-component or technology-rights route, but they do not close the early-entry gap. For example, the Barcelona program's own announcement describes its system as support for extremely premature fetuses and reports a sheep-model transition result; this is a later-fetal engineering precedent, not embryo-start evidence: [Sant Joan de Déu Barcelona fetaLife report](https://www.sjdhospitalbarcelona.org/en/news/bcnatals-fetalife-project-most-critically-premature-babies-achieves-21-days-survival-sheep-model-liquid-incubator).

The owner still prefers the earliest achievable owned platform for ten concurrent gestations and same-date births, ideally within two to three years or sooner. This evidence decision does not establish that timeline, a 100% success guarantee, human feasibility, healthy births, or the later tall-stature/learning outcomes. No person was contacted.

## Roadmap result

- **T01 — complete, planning only:** compared the living-interface, staged and synthetic-replacement allocations; D/M/P in shared units is the discriminator; architecture remains unselected.
- **T02 — complete, bounded rejection:** current imported candidates cannot test the same-unit target question; a route for additional public/controlled raw data remains open and should not be assumed absent.
- **T04 — complete, observation contract:** the six-part contract above defines the minimum existing-data or prospective-measurement input.
- **T16 / M22 — complete, feedback-contract planning:** resources, prediction/comparator, replay boundary, discrepancy rule and next specialist measurement question are recorded. No laboratory loop or biological result is claimed.
- **T05 — next review task:** source-first challenge of this contract and its exact source locators. The self-audit here is provisional AI work, not independent scientific acceptance. No author contact is part of this task.

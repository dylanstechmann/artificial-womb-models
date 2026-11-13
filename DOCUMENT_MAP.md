# Document map

Every Markdown document in the repository root, grouped by purpose. The [README](README.md) covers what the software does and how to run it; this page is for finding the rest. Dated file names carry the date the work was done. Unless a document says otherwise it is AI-assisted and not recorded as reviewed by the owner or an independent reviewer, and none of it establishes continuous human gestation.

`tests/test_document_map.py` fails when a root document is missing from this page, so add new documents to the matching group.

## Project rules, history and plan

| Document | What it is |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Project guidance for coding agents: scope limits, capability labels, verification rules |
| [AGENT_TOOLS.md](AGENT_TOOLS.md) | Portable agent-tooling configuration and CLI fallbacks |
| [CLAUDE.md](CLAUDE.md) | Claude Code entry point to the repository guidance |
| [CHANGELOG.md](CHANGELOG.md) | Dated record of changes |
| [PROGRAM_PLAN.md](PROGRAM_PLAN.md) | Master plan: completion program for owned ectogenesis equipment, with gates, requirements and tasks |
| [PROGRAM_STATUS.md](PROGRAM_STATUS.md) | Progress view of that plan, generated from `config/program/roadmap.json` |
| [ROADMAP.md](ROADMAP.md) | Development roadmap: cycle-by-cycle numerical, uncertainty and verification history |
| [INTEGRATED_PORTFOLIO_REVIEW_2026-11-13.md](INTEGRATED_PORTFOLIO_REVIEW_2026-11-13.md) | Held first-month integrated portfolio and resource review (T09); exposes the T05 dependency, planning only |
| [RESEARCH_PROGRAM.md](RESEARCH_PROGRAM.md) | Research program: from separate demonstrations to testable ectogenesis questions |
| [FEASIBILITY_STRATEGY.md](FEASIBILITY_STRATEGY.md) | Making the embryo-to-birth concept testable |

## Concept design, in silico modeling and methods

| Document | What it is |
| --- | --- |
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | Concept design: continuous ectogenesis platform (proposed functional architecture for research) |
| [WHOLE_SYSTEM_INSILICO_DESIGN_2026-10-17.md](WHOLE_SYSTEM_INSILICO_DESIGN_2026-10-17.md) | Whole-system in silico design: early-exchange platform v2 (T17) |
| [WHOLE_INTERVAL_INSILICO_DESIGN_2026-10-17.md](WHOLE_INTERVAL_INSILICO_DESIGN_2026-10-17.md) | Whole-interval in silico design: sustained exchange through neonatal transition (T18) |
| [INSILICO_MODELING_CORRECTION_2026-10-17.md](INSILICO_MODELING_CORRECTION_2026-10-17.md) | Correction record (D12): in silico modeling is the working mode; the T19-T22 modeling ladder |
| [NUMERICAL_INTEGRATION_QUALIFICATION_2026-10-22.md](NUMERICAL_INTEGRATION_QUALIFICATION_2026-10-22.md) | T26: advancing clocks, stiff-wall stability, event balance and independent convergence checks |
| [RECIPROCAL_COUPLING_QUALIFICATION_2026-10-24.md](RECIPROCAL_COUPLING_QUALIFICATION_2026-10-24.md) | T27: dimensionless damage-gated wall-to-fluidic feedback qualification |
| [SENSOR_FAILOVER_QUALIFICATION_2026-11-01.md](SENSOR_FAILOVER_QUALIFICATION_2026-11-01.md) | T28: independent-sensor disagreement, fault detection and frozen-supplement fallback |
| [COMMON_CAUSE_FAULT_QUALIFICATION_2026-11-12.md](COMMON_CAUSE_FAULT_QUALIFICATION_2026-11-12.md) | T29: shared-reference common-cause sensor and supplement-actuator fault qualification |
| [MULTI_UNIT_CONTENTION_QUALIFICATION_2026-11-12.md](MULTI_UNIT_CONTENTION_QUALIFICATION_2026-11-12.md) | T30: multi-unit shared-service contention and boundary-blindness qualification |
| [TRANSITION_DEMAND_QUALIFICATION_2026-11-13.md](TRANSITION_DEMAND_QUALIFICATION_2026-11-13.md) | T31: concurrent transition demand and shared-station contention qualification |
| [T05_SEQUENCING_CHALLENGE_2026-10-17.md](T05_SEQUENCING_CHALLENGE_2026-10-17.md) | Defer the independent reviewer and prioritize whole-system in silico design (D10) |
| [THEORETICAL_MODELS.md](THEORETICAL_MODELS.md) | Theoretical modules and the future measured-data contract |
| [METHODS.md](METHODS.md) | Methods and output interpretation: equations, boundaries and the reproducibility contract |

## Evidence ledger and source qualification

| Document | What it is |
| --- | --- |
| [EVIDENCE.md](EVIDENCE.md) | Evidence ledger: the bounded, manually reviewed map of sources and claims |
| [SOURCE_QUALIFICATION.md](SOURCE_QUALIFICATION.md) | Placental interface source qualification |
| [SOURCE_MAPPING_2026-10-09.md](SOURCE_MAPPING_2026-10-09.md) | Bounded public source mapping: source coverage and linkage, not a biological analysis |
| [NICHE_SOURCE_QUALIFICATION.md](NICHE_SOURCE_QUALIFICATION.md) | Niche mechanics and developmental outcomes: source qualification |
| [HUMAN_MFI_ATLAS_QUALIFICATION_2026-10-10.md](HUMAN_MFI_ATLAS_QUALIFICATION_2026-10-10.md) | Human maternal-fetal interface atlas: candidate source qualification |
| [COLLECTION_ACCOUNTING.md](COLLECTION_ACCOUNTING.md) | Transport collection accounting and native source recovery |
| [PHENOTYPE_INTAKE.md](PHENOTYPE_INTAKE.md) | Existing phenotype data intake |
| [PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md](PERFUSION_COMPARABILITY_INTAKE_2026-10-10.md) | Candidate intake fields for ex vivo placental-perfusion studies (a vocabulary, not a protocol) |
| [PERFUSION_DATA_REPOSITORY_SCREEN_2026-10-10.md](PERFUSION_DATA_REPOSITORY_SCREEN_2026-10-10.md) | Public placental-perfusion data repository screen |
| [ARTIFICIAL_PLACENTA_OUTCOME_INTAKE_2026-10-10.md](ARTIFICIAL_PLACENTA_OUTCOME_INTAKE_2026-10-10.md) | Fetal extracorporeal-support outcome intake |

## Interface, boundary and early-exchange questions

| Document | What it is |
| --- | --- |
| [INTERFACE_FEASIBILITY.md](INTERFACE_FEASIBILITY.md) | Interface feasibility: discriminating questions |
| [SELECTIVE_INTERFACE_FEASIBILITY.md](SELECTIVE_INTERFACE_FEASIBILITY.md) | Selective interface function: exploration and design refinement |
| [EARLY_EXCHANGE_TRANSITION.md](EARLY_EXCHANGE_TRANSITION.md) | Early support to sustained exchange: refine the missing transition |
| [FUNCTIONAL_SUPPORT_ROUTES.md](FUNCTIONAL_SUPPORT_ROUTES.md) | Preserve developmental functions while testing alternative support routes |
| [MIDGESTATION_BOUNDARY.md](MIDGESTATION_BOUNDARY.md) | Qualify the terminal support boundary before extending the architecture |
| [MATERIAL_HANDOFF_REQUIREMENTS.md](MATERIAL_HANDOFF_REQUIREMENTS.md) | Preserve usable material transfer, not just availability |
| [SUPPORT_DEVELOPMENT_DISCORDANCE.md](SUPPORT_DEVELOPMENT_DISCORDANCE.md) | Require support function and embryonic progression together |
| [DYNAMIC_BOUNDARY_REQUIREMENTS.md](DYNAMIC_BOUNDARY_REQUIREMENTS.md) | Qualify a moving developmental boundary |
| [MATERNAL_INTERFACE_REQUIREMENTS.md](MATERNAL_INTERFACE_REQUIREMENTS.md) | Maternal-interface state and embryo progression |
| [BOUNDARY_REANALYSIS_CONTRACT.md](BOUNDARY_REANALYSIS_CONTRACT.md) | Boundary coordination: three distinct questions |
| [CREST_REANALYSIS_CONTRACT.md](CREST_REANALYSIS_CONTRACT.md) | Early-interface functional reanalysis contract |
| [ROELOFSEN_DATA_REQUIREMENTS.md](ROELOFSEN_DATA_REQUIREMENTS.md) | Native placental-perfusion data: question and qualification card |
| [ROELOFSEN_SURFACE_AREA_LINEAGE_2026-10-10.md](ROELOFSEN_SURFACE_AREA_LINEAGE_2026-10-10.md) | Roelofsen ex vivo Papp: surface-area assumption lineage |
| [HIRAOKA_COVERAGE_QUESTION_2026-10-09.md](HIRAOKA_COVERAGE_QUESTION_2026-10-09.md) | Candidate question card: Hiraoka endpoint coverage |

## Decisions, contracts and planning records (2026-10-11)

| Document | What it is |
| --- | --- |
| [EARLY_SUPPORT_LINKAGE_DECISION_2026-10-11.md](EARLY_SUPPORT_LINKAGE_DECISION_2026-10-11.md) | Early-support architecture and observation decision (T01, T02, T04, T16) |
| [EARLY_SUPPORT_SOURCE_CHALLENGE_2026-10-11.md](EARLY_SUPPORT_SOURCE_CHALLENGE_2026-10-11.md) | Early-support source and claim challenge: provisional AI challenge, independent review pending |
| [OWNED_PLATFORM_OPTIONS_2026-10-11.md](OWNED_PLATFORM_OPTIONS_2026-10-11.md) | Owned-platform route and resource decision: initial options comparison, no quote or transaction |
| [TEN_UNIT_DEPENDENCY_ASSESSMENT_2026-10-11.md](TEN_UNIT_DEPENDENCY_ASSESSMENT_2026-10-11.md) | Ten-unit resource and fault-dependency assessment (an aspiration study, planning only) |
| [COMMON_DATE_READINESS_CONTRACT_2026-10-11.md](COMMON_DATE_READINESS_CONTRACT_2026-10-11.md) | Common-date birth and readiness contract (an aspiration) |
| [COMPUTE_CALIBRATION_T07_2026-10-11.md](COMPUTE_CALIBRATION_T07_2026-10-11.md) | T07 local compute calibration |
| [UNSENT_TECHNICAL_REVIEW_PACKET_DRAFT_2026-10-11.md](UNSENT_TECHNICAL_REVIEW_PACKET_DRAFT_2026-10-11.md) | Unsent technical-review packet draft: internal preparation only, not addressed or sent |
| [USUDA_SOURCE_AUDIT_REPRODUCTION_2026-10-11.md](USUDA_SOURCE_AUDIT_REPRODUCTION_2026-10-11.md) | Usuda terminal source-audit reproduction (cycle 347) |

## Source screens: early development, implantation and placental demand

| Document | What it is |
| --- | --- |
| [AGUILERA_CASTREJON_2021_E11_HANDOFF_2026-10-10.md](AGUILERA_CASTREJON_2021_E11_HANDOFF_2026-10-10.md) | Aguilera-Castrejon et al. 2021: E11 handoff qualification |
| [GUO_PUBLIC_DATA_SCREEN_2026-10-10.md](GUO_PUBLIC_DATA_SCREEN_2026-10-10.md) | Guo et al. 2026: public-data accession and code screen |
| [GSE263528_HUMAN_BLASTOID_ENDOMETRIAL_ASSEMBLOID_METADATA_SCREEN_2026-10-11.md](GSE263528_HUMAN_BLASTOID_ENDOMETRIAL_ASSEMBLOID_METADATA_SCREEN_2026-10-11.md) | GSE263528 human blastoid/endometrial assembloid metadata screen |
| [LI_2026_HUMAN_IMPLANTATION_FAILURE_MODEL_SOURCE_SCREEN_2026-10-11.md](LI_2026_HUMAN_IMPLANTATION_FAILURE_MODEL_SOURCE_SCREEN_2026-10-11.md) | Li et al. 2026: human implantation-failure model source screen |
| [MOLE_2026_HUMAN_IMPLANTATION_SOURCE_SCREEN_2026-10-11.md](MOLE_2026_HUMAN_IMPLANTATION_SOURCE_SCREEN_2026-10-11.md) | Molè et al. 2026: human implantation-interface source screen |
| [SONG_2026_HUMAN_POSTIMPLANTATION_COCULTURE_SOURCE_SCREEN_2026-10-11.md](SONG_2026_HUMAN_POSTIMPLANTATION_COCULTURE_SOURCE_SCREEN_2026-10-11.md) | Song et al. 2026: human post-implantation co-culture source screen |
| [SANDOVICI_2024_MOUSE_PLACENTAL_DEMAND_SOURCE_SCREEN_2026-10-10.md](SANDOVICI_2024_MOUSE_PLACENTAL_DEMAND_SOURCE_SCREEN_2026-10-10.md) | Sandovici et al. 2024: mouse placental nutrient-demand source screen |

## Source screens: placental perfusion and transfer

| Document | What it is |
| --- | --- |
| [ASHLEY_2022_VITAMIN_D_PERFUSION_SOURCE_SCREEN_2026-10-10.md](ASHLEY_2022_VITAMIN_D_PERFUSION_SOURCE_SCREEN_2026-10-10.md) | Ashley et al. 2022: vitamin-D placental-perfusion source screen |
| [BENOIT_2026_OSIMERTINIB_ALECTINIB_PERFUSION_SCREEN_2026-10-11.md](BENOIT_2026_OSIMERTINIB_ALECTINIB_PERFUSION_SCREEN_2026-10-11.md) | Benoit et al. 2026: osimertinib/alectinib human-perfusion screen |
| [BUKKEMS_2022_DORAVIRINE_PERFUSION_SCREEN_2026-10-10.md](BUKKEMS_2022_DORAVIRINE_PERFUSION_SCREEN_2026-10-10.md) | Bukkems 2022: doravirine perfusion source screen |
| [CABOTEGRAVIR_BICTEGRAVIR_2020_ACCESS_SCREEN_2026-10-10.md](CABOTEGRAVIR_BICTEGRAVIR_2020_ACCESS_SCREEN_2026-10-10.md) | Cabotegravir/bictegravir perfusion access screen |
| [DAY_2013_GLUTAMINE_PERFUSION_SOURCE_SCREEN_2026-10-10.md](DAY_2013_GLUTAMINE_PERFUSION_SOURCE_SCREEN_2026-10-10.md) | Day et al. 2013: glutamine perfusion source screen |
| [ELIESEN_2024_PUBLIC_DATASET_ROUTE_SCREEN_2026-10-11.md](ELIESEN_2024_PUBLIC_DATASET_ROUTE_SCREEN_2026-10-11.md) | Eliesen et al. 2024: public companion-dataset screen |
| [ELIESEN_2024_TOFACITINIB_GROUP_SUMMARY_CHECK_2026-10-11.md](ELIESEN_2024_TOFACITINIB_GROUP_SUMMARY_CHECK_2026-10-11.md) | Eliesen et al. 2024: Table S3 group-summary check |
| [ELIESEN_2024_TOFACITINIB_SOURCE_RECONCILIATION_2026-10-11.md](ELIESEN_2024_TOFACITINIB_SOURCE_RECONCILIATION_2026-10-11.md) | Eliesen et al. 2024: Table S3 source reconciliation |
| [FAURE_BARDON_2020_LETERMOVIR_MARIBAVIR_PERFUSION_INTAKE_2026-10-10.md](FAURE_BARDON_2020_LETERMOVIR_MARIBAVIR_PERFUSION_INTAKE_2026-10-10.md) | Faure Bardon et al. 2020: letermovir/maribavir perfusion intake |
| [HEGGARTY_2025_DABRAFENIB_TRAMETINIB_PERFUSION_SCREEN_2026-10-11.md](HEGGARTY_2025_DABRAFENIB_TRAMETINIB_PERFUSION_SCREEN_2026-10-11.md) | Heggarty et al. 2025: human placental transfer screen |
| [HIRSCHMUGL_2021_FATTY_ACID_PERFUSION_SOURCE_SCREEN_2026-10-10.md](HIRSCHMUGL_2021_FATTY_ACID_PERFUSION_SOURCE_SCREEN_2026-10-10.md) | Hirschmugl et al. 2021: fatty-acid placental-perfusion source screen |
| [HOLM_2017_AMINO_ACID_INTAKE_SOURCE_SCREEN_2026-10-10.md](HOLM_2017_AMINO_ACID_INTAKE_SOURCE_SCREEN_2026-10-10.md) | Holm et al. 2017: amino-acid exchange source screen |
| [LE_2021_DORAVIRINE_PERFUSION_SCREEN_2026-10-10.md](LE_2021_DORAVIRINE_PERFUSION_SCREEN_2026-10-10.md) | Le et al. 2021: doravirine placenta-perfusion public-source screen |
| [LOFTHOUSE_2016_PHENYLALANINE_PERFUSION_SOURCE_SCREEN_2026-10-10.md](LOFTHOUSE_2016_PHENYLALANINE_PERFUSION_SOURCE_SCREEN_2026-10-10.md) | Lofthouse et al. 2016: phenylalanine perfusion source screen |
| [MANDELBROT_DOLUTEGRAVIR_PERFUSION_INTAKE_2026-10-10.md](MANDELBROT_DOLUTEGRAVIR_PERFUSION_INTAKE_2026-10-10.md) | Mandelbrot et al.: dolutegravir perfusion observation intake |
| [MATHIESEN_PERFUSION_AVAILABILITY_CROSSWALK_2026-10-10.md](MATHIESEN_PERFUSION_AVAILABILITY_CROSSWALK_2026-10-10.md) | Mathiesen 2020: source availability crosswalk |
| [MATHIESEN_PERFUSION_QUALIFICATION_2026-10-10.md](MATHIESEN_PERFUSION_QUALIFICATION_2026-10-10.md) | Mathiesen et al.: term placental perfusion qualification |
| [OLLIVIER_2026_ACICLOVIR_PERFUSION_SOURCE_SCREEN_2026-11-12.md](OLLIVIER_2026_ACICLOVIR_PERFUSION_SOURCE_SCREEN_2026-11-12.md) | Ollivier et al. 2026: aciclovir/antipyrine perfusion source-cell audit and observation intake |
| [SCHALKWIJK_2016_DOLUTEGRAVIR_ACCESS_SCREEN_2026-10-10.md](SCHALKWIJK_2016_DOLUTEGRAVIR_ACCESS_SCREEN_2026-10-10.md) | Schalkwijk 2016: dolutegravir perfusion access screen |
| [SPIESS_2023_PERFUSION_SUPPLEMENT_SCREEN_2026-10-10.md](SPIESS_2023_PERFUSION_SUPPLEMENT_SCREEN_2026-10-10.md) | Spiess et al. 2023: placental-perfusion supplement screen |

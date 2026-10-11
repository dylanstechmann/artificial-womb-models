# Common-date birth and readiness contract

Date: 11 October 2026
Roadmap task: T14
Status: outcome-measurement contract; no date prediction or clinical standard

## Decision

Treat “ten children born on the same calendar date” as an observed result, not a start-time or controller setting. Each of ten identified units must independently meet the qualified readiness decision for the next transition, and all ten actual recorded civil birth dates must match under one predeclared calendar/time-zone rule. If one unit is not independently ready, has a missing/unverifiable event record, or has a different date, the ten-unit common-date requirement is not met. Keep the original result and reason; do not reschedule the definition after observing outcomes.

This contract closes T14 at the **planning/measurement-definition level**. The actual birth event, jurisdiction, IANA time-zone identifier, readiness standard, responsible qualified assessors and outcome data remain unselected/unavailable. M20 and G8 remain deferred/not established; no biological gate moves.

## Qualifying event and calendar rule

Record two separate events for each child:

1. **Technical transition event (provisional operational field):** the date/time at which the child has completely exited the external gestation-support equipment and entered the separately recorded neonatal-care state. Store the timestamp in UTC with its source clock, precision, synchronization/calibration record and uncertainty. This field describes machine transition performance; it does not itself determine a legal birth date.
2. **Civil birth event:** the birth date/time assigned and documented by the responsible birth facility under the rules applicable to the selected jurisdiction. Preserve that source record and its declared local date/time. The final owner outcome uses this civil event for the common-date comparison once the jurisdiction is selected. Do not substitute chamber shutdown, first sign of breathing, a scheduled target or a software alarm for the facility's recorded birth event.

For reproducible conversion, retain the raw UTC timestamp and the named IANA time-zone identifier used to display a local civil date. The final zone must be selected from the declared birth location or an explicit owner-selected reference zone before any result is scored; the computer's current local time zone is not a valid implicit choice. Record the exact IANA Time Zone Database release used because civil-time rules can change. [IANA describes the database as location-specific machine-readable rules for converting UTC to local time](https://www.iana.org/time-zones) and publishes versioned releases [here](https://www.iana.org/time-zones/releases). If units are born at different locations, preserve every local zone and separately apply the one predeclared reference zone to the common-date requirement.

The required timezone-selection rule is therefore defined, but the actual zone is intentionally **unset** because country/location is undecided. This prevents a technically reproducible comparison from being mistaken for a jurisdiction's legal date assignment.

## Independent readiness and all-unit record

For every unit, retain one row linked to the frozen starting-unit roster and the complete trajectory. The minimum row includes:

| Field | Required content |
| --- | --- |
| Unit identity | Stable de-identified unit key; lineage to the source-defined starting roster and its disposition |
| Concurrency interval | Independently recorded support-start and support-end timestamps, each with source clock and UTC conversion; establishes overlap, not readiness |
| Readiness decision | Result, assessment time, accountable qualified assessor and applicable independently approved criteria/version; keep `not assessed` distinct from a pass |
| Technical transition event | Actual UTC timestamp, precision/uncertainty, clock source and configuration; event definition above |
| Civil birth event | Facility source, recorded date/time, place/timezone and record status; restricted source record held under the responsible custodian's controls |
| Calendar conversion | Raw UTC instant, IANA zone identifier, tzdb release, conversion result and any correction/reconciliation history |
| Outcome/disposition | Complete outcome, adverse event, loss, withdrawal or missing follow-up; no survivor-only denominator |
| Target comparison | Per-unit civil date, whether it equals the predeclared target date, whether all ten dates agree, and reason for each miss/unresolved value |

The readiness decision must be made independently for each unit by qualified assessors using criteria suited to the actual use. A common scheduled time, machine maturity estimate, system telemetry or common start date cannot serve as readiness evidence. This document does not set medical criteria, acceptable developmental ranges or transition procedures.

## Cohort and scoring rule

- Freeze the ten unit keys included in the simultaneous-outcome evaluation before the qualifying birth events; retain prior selection and every exclusion/disposition in the complete upstream roster.
- Demonstrate actual overlap in the recorded support intervals for all ten units. Equal planned start times or ten separate sequential trajectories do not meet concurrency.
- Compare all ten **civil birth-event dates** using the single timezone/reference-zone rule frozen before scoring. Preserve the UTC instants and each official source date for audit.
- Record ten separate readiness decisions. A missing, unresolved or failed readiness decision prevents a pass; date equality cannot override readiness.
- The common-date condition passes only if all ten dates are known and equal under the frozen rule and every unit satisfies the separately approved readiness and outcome criteria. Date agreement alone is not a healthy-outcome result.
- Report target-date error, pairwise date spread and each unit's disposition descriptively. Do not calculate a probability of success without an eligible source-defined timing model and full-cohort evidence.

## Timing variability and evidence gap

No source-qualified timing distribution for ten concurrent embryo-start human artificial-gestation trajectories was identified in the current evidence record. The human Song co-culture report ends at day 14 post-fertilization and is an early-interface model; it does not estimate time to a birth event or date spread across ten units. The fetaLife institutional report describes a sheep model of later extreme-preterm support and a neonatal transition, not embryo-to-birth timing for ten units. [Song et al. primary record](https://pubmed.ncbi.nlm.nih.gov/41443195/); [Sant Joan de Déu report](https://www.sjdhospitalbarcelona.org/en/news/bcnatals-fetalife-project-most-critically-premature-babies-achieves-21-days-survival-sheep-model-liquid-incubator).

Accordingly, no biological timing distribution, variability bound, target-day selection method, shared-date probability or schedule is supplied. The owner's two-to-three-year preference concerns program urgency; it is not a gestational duration or evidence that ten units can be synchronized safely. The common-date requirement may conflict with independent readiness. If readiness dates do not align, the goal is unmet; this contract gives no instruction to alter any transition to force alignment.

## Next measurement and decision

Before actual outcome scoring, the owner/program must identify the intended birth location/jurisdiction and reference timezone, and the responsible qualified group must approve the exact readiness criteria, civil-event source and record custodian. Then T13's concurrent capacity requirements and the present contract can be combined into a preregistered ten-unit timestamp/readiness schema. M20 requires actual records, every starting-unit disposition, misses and independent review; a schema alone does not qualify the machine.

No person was contacted. The record remains a planning artifact, not a clinical, legal or scheduling recommendation.

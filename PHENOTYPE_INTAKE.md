# Existing phenotype data intake

AI-assisted software milestone, 2026-10-09. This implements the coverage and
hierarchy portion of the [early-interface reanalysis contract](CREST_REANALYSIS_CONTRACT.md).
The original functional measurements requested there remain unavailable in
the inspected sources. No source effect is estimated and no biological
feasibility gate closes through this command.

`validate-phenotypes` checks a declared starting specimen roster against
individual endpoint records. It preserves missing, excluded and unassessed
outcomes before any future analysis. The runtime is offline and uses only
the Python standard library.

## Run the artificial example

```powershell
wombmodels validate-phenotypes --dataset examples/phenotype_intake_fixture.json --out artifacts/phenotype-intake-example
wombmodels verify-bundle --bundle artifacts/phenotype-intake-example --strict
```

Use a new output directory each time. Every number, specimen, source,
experiment and condition in the example is invented. Values and times are
dimensionless software fixtures; none represents an embryo measurement or
gestational duration. The fixture includes a missing endpoint, an excluded
numeric value and an unassessed endpoint to exercise denominator checks.

## Fill the existing-data contract

The shape is in [phenotype-intake.schema.json](schemas/phenotype-intake.schema.json).
Its `observation_dataset` uses the existing observation contract for source
revisions, exact units, developmental context, measurement uncertainty,
missingness and optional local file hashes. Runtime validation additionally
enforces references, identities and matrix coverage.

Each cohort supplies:

- A source namespace and locator, a population declaration and a starting
  selection frame: `reported_complete`, `partial` or `not_reported`.
- Source-defined conditions, their comparator/exposure/other roles,
  assignment notes and source locators. These are metadata, not instructions
  to perform an experiment.
- Endpoints with exact assay names, units, ascertainment times, measurement
  definitions/version, calibration and uncertainty notes, and source locators.
  Unknown measurement metadata is explicitly null and remains unresolved.
- A roster of coded specimen IDs, experiment IDs, endometrial-source IDs,
  condition IDs and source locators. Unknown experiment/source IDs are null;
  software does not infer them or treat unknown IDs as a shared donor.
- One outcome for every roster specimen and endpoint, with a unique
  observation-record reference, status, reason and original-value locator.

Statuses are `observed`, `missing`, `excluded` and `not_assessed`. Observed
outcomes require finite numeric values. Missing/unassessed outcomes require
null values and reasons. Excluded outcomes require reasons and preserve any
numeric value supplied. Null values also retain the observation contract's
missingness reason. No row is created by silently dropping a specimen.

Every referenced record must be used exactly once. Duplicate specimens,
endpoint aliases, reused records, unreferenced observations and absent
specimen/endpoint entries fail. Individual IDs must match their observation
units; pooled, technical and author-summary rows cannot substitute for
individual phenotypes. Molecular identity alone cannot serve as a phenotype
endpoint in this contract.

Human embryos, human blastoids and other declared populations remain in
separate cohorts. Species, stages, model types/labels, laboratories and exact
developmental intervals cannot differ within a cohort. Preparation batch
IDs may differ; they remain in the original observation input. Assay units
and ascertainment must exactly match the endpoint contract, without
conversion. Exact-unit numeric ascertainment outside the declared
developmental interval fails; unavailable containment remains unresolved.

The input is bounded to 20 cohorts, 20 endpoints and conditions per cohort,
1,000 specimens per cohort, 5,000 total outcomes and 2 MB of JSON. Source
file verification uses the existing bounded, read-only `--source-root`
contract. It never fetches source URLs or executes source code.

## Review the outputs

`phenotype_outcomes.csv` preserves every outcome, source locator, status,
reason, value, uncertainty and ascertainment. `endpoint_groups.csv` reports
counts and observed minimum/median/maximum separately for each cohort,
endpoint, experiment, endometrial source and condition. Excluded numeric
values stay in the outcomes table and do not enter observed summaries.
Missing/unassessed values never become zeros. Groups with no observed
values have blank summaries. No overall pooled effect is emitted.
Both tables retain species, stage, model context and declared developmental
intervals with their exact units.

`hierarchy.csv` counts declared specimens and experiment/source labels.
These counts do not establish independent biological n. Different labels
may still share contributors; the actual hierarchy needs source review.
`phenotype_report.json` records coverage, byte verification, missing metadata
and unresolved requirements. Exact submitted input bytes, implementation
hashes and output hashes travel with the receipt.

Qualification stays unresolved for artificial fixtures, incomplete source
byte verification, absent included-review assertions, partial/unknown
starting frames, missing hierarchy/measurement/assignment metadata, absent
comparators or declared conditions without specimens/observed values.
When the recorded requirements are present, the status is only
`recorded_requirements_present_for_human_review`. Software authenticates
neither the roster, source transcription, rights, assignment nor the review.

There is no treatment-effect estimate, hypothesis test, biological
uncertainty interval, fitted mechanism, phenotype/transcriptomic join or
claim of continuous development. A subsequent analysis needs a reviewed
source contract, an estimand and an uncertainty method that respect the
actual experiment/source hierarchy. The current data inquiry remains unsent.

# Changelog

## Unreleased

- Add `verify-bundle`: a standalone, standard-library verifier for a published bundle's receipt structure, file hashes and byte counts, declared parent ancestry and recorded dependencies, with bounded reads, symlink rejection and a `--strict` mode for undeclared files and unpublished bundle kinds. Archive integrity, ancestry resolution, scientific review and reproduction are reported as four separate statuses; verification never reruns a model.
- Copy the exact source `simulate` receipt into `identifiability-report` bundles as `source_receipt.json` and declare its hash in receipt metadata, so ancestry resolves after the source directory is deleted.
- Publish `reproduction_plan.json` in every bundle with the package version, Python version, declared dependencies, command template, inputs, complete expected file set and interpretation limits, and no absolute paths.
- Add a machine-readable developmental transition map with explicit unknown edges, source locators and same-unit claim links; prevent announcements, species mixing and unsupported claims from establishing continuity.
- Export `transitions.csv` and include transition records in the receipt-bound evidence report for later ResearchDesk display.

## 0.4.0 — 2026-10-06

- Optionally hash locally available source files under an explicit root and report matching, mismatched, missing, and bounded-limit states without fetching or copying source data.
- Reject absolute, dot-segment, control-character, and symlink source paths; cap local hashing at 1 GB per artifact and 2 GB per intake.
- Preserve source-byte verification status in receipt-bound outputs for ResearchDesk while keeping external source bytes outside the bundle.

## 0.3.0 — 2026-10-06

- Add a stdlib developmental-observation intake validator with declared source-metadata binding, local source-review revisions, exact reported-unit partitions, missingness and explicit transition-continuity states.
- Reject same-unit observations mislabeled as independent and require source-linked, same-unit, chronologically comparable intervals before a transition can be recorded as demonstrated.
- Publish raw records, exact-group tables, transition tables, a bounded report and receipt-last hashes; include schema files in implementation fingerprints.
- Preserve the distinction between record validation, source review, analysis eligibility and biological evidence.

## 0.2.1 — 2026-10-06

- Match the transport reference's combined capacity to the two equal compartments; verify its rapid-mixing limit against an independently derived steady solution.
- Keep point forecasts but suppress approximate intervals when local parameter covariance is unavailable. Report interval availability and its replicate denominator separately from forecast availability.
- Replace the development roadmap with ordered milestones and explicit numerical, evidence, data and review acceptance criteria.

## 0.2.0 — 2026-10-06

- Add noise-aware state estimation and a forward temporal forecast that excludes later readings from fitting and prediction inputs.
- Require the simulation receipt and exact modeled event schedule to match before identifiability analysis.
- Relabel endpoint-based integral-balance residuals as consistency diagnostics, not forecasts.
- Extend seeded sweeps with forecast-versus-baseline error, approximate interval coverage/width, state-parameter recovery and explicit 70%-of-duration training semantics.
- Add dimensionless two-compartment transport and Kelvin–Voigt mechanics fixtures, alternative-model outputs and a shared developmental-observation schema.
- Expand offline test and command coverage for every report family.

All new numerical outputs remain software fixtures. This release does not add biological calibration, human gestation prediction, clinical advice, animal procedures, or device design parameters.

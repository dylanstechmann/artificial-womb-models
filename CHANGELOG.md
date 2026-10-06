# Changelog

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

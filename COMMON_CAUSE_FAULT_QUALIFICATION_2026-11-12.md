# T29 common-cause sensor and supplement-actuator fault qualification (2026-11-12)

**Roadmap task:** T29, registered by decision **D16**.  
**Status:** Qualified as a deterministic, dimensionless software fixture; no physical sensor, actuator, alarm or safe-state qualification is claimed.

## Scope

This AI-assisted software experiment extends the T28 whole-path fault register with two faults that pairwise sensor disagreement cannot identify: an identical bias or dropout on both bulk-stock sensors, and a downstream supplement-actuator offset. It also retains primary-only bias and dropout as controls. The three modes are `single_sensor`, `disagreement_freeze` and `balance_augmented_freeze`; the three interface variants produce nine trajectories.

The augmented detector adds two boundary channels to primary/secondary disagreement: `abs(primary_reading - nominal_bulk_stock)` and `abs(metered_supplement - commanded_supplement)`. The shadow trajectory uses the same substeps and commanded supplement but no actuator offset. Consequently, with no actuator fault, shadow and true bulk stock are identical; the no-fault balance residual is primary-sensor noise and the actuator residual is actuator-meter noise, up to floating-point subtraction.

Command:

```sh
PYTHONPATH=src python -m wombmodels common-cause-fault-model --config examples/common_cause_fault_fixture.json --out <new-dir>
```

The command preserves the exact configuration as `source_config.json`, publishes all nine trajectories, per-output-sample fault observations, a structured report, `REPORT.md`, a reproduction plan and a receipt. Strict bundle verification checks the published bytes; it does not rerun or scientifically validate the model.

## Frozen policy and result

The fixture uses disagreement and balance thresholds of 0.12, an actuator threshold of 0.10, actuator-meter noise standard deviation 0.01 and two-sample confirmation. Declared output samples include both fault-window endpoints; integration intervals remain half-open. A confirmation appears in the observation row immediately and in the trajectory policy state on the following output row. Accordingly, `detected_fault_samples` counts samples strictly after the first confirmation in each fault window.

| Variant | Mode | Primary bias | Common sensor bias | Actuator offset | False alarms | Max absolute bulk difference vs single-sensor |
|---|---|---:|---:|---:|---:|---:|
| living_interface | disagreement_freeze | 4/6 | 0/7 | 0/7 | 0 | 0.003839562917596462 |
| living_interface | balance_augmented_freeze | 4/6 | 5/7 | 5/7 | 0 | 0.18844479498039934 |
| staged | disagreement_freeze | 4/6 | 0/7 | 0/7 | 0 | 0.003839562917596462 |
| staged | balance_augmented_freeze | 4/6 | 5/7 | 5/7 | 0 | 0.18844479498039934 |
| synthetic | disagreement_freeze | 4/6 | 0/7 | 0/7 | 0 | 0.003839562917596462 |
| synthetic | balance_augmented_freeze | 4/6 | 5/7 | 5/7 | 0 | 0.18844479498039934 |

These are deterministic sample counts for this fixture, not detection probabilities or hardware alarm performance.

## Key findings

- Pairwise disagreement confirms the primary-only bias at dimensionless time 3.5, but never confirms the common bias at 8.0–11.0 or the actuator offset at 14.0–17.0. During common bias, the pairwise residual remains only the difference between the two independent noise draws.
- The augmented mode confirms the primary bias at 3.5, common bias at 8.5 and actuator offset at 14.5, with zero false-alarm samples in every variant. Its confirmed actuator response latches both frozen-supplement fallback and actuator isolation; after isolation, delivered supplement equals commanded supplement. Sensor-only detections do not pre-clamp later independent actuator challenges.
- In the three-fault run, final bulk stock is 1.8629040265086785 for single-sensor control and 1.866743589426275 for both fallback modes. The augmented mode's largest bulk-stock separation from single-sensor control is 0.18844479498039934. In the isolated actuator challenge it is 0.18848744874819312.
- In the isolated common-bias challenge, disagreement fallback never activates and its trajectory equals single-sensor control exactly. The augmented terminal bulk-stock difference from the no-fault trajectory is bounded by 0.003839562917596462 in the tested fixture. This positive-bias fixture does not demonstrate every sign, saturation or control-response combination.
- Regression runs establish exact no-fault equality with T21 for every shared trajectory column in all three variants. Primary-only bias/dropout regression also reproduces T28's independent-sensor trajectory and first detection timestamps. A separate common-dropout case makes both sensors unavailable and is detected by both fallback modes.
- Publication is deterministic, all nine trajectory files are present, and `verify_bundle(..., strict=True)` passes. Malformed schemas, thresholds, confirmation counts, fault kinds, dropout magnitudes, overlapping or off-grid events, excess faults and work-budget exhaustion are rejected; budget failure publishes no output directory.

## Hidden internal-state boundary

A paired check holds `serve_rate` at 2.0 and changes only `internal_efficiency` from 0.9 to 0.0. Across all 81 pre-fallback output samples, boundary channels and every sensor, balance and actuator residual are identical while deep receipt and progression differ. `internal_tissue_observed_by_fallback` is therefore `False`: the detector uses no internal tissue channel and cannot diagnose or repair an internal delivery, tissue-use or developmental shortfall.

## Engineering consequence and limits

T29 supplies an inspectable synthetic discriminator for independent-sensor disagreement, common-reference faults, actuator metering and a nominal commanded-supplement shadow. It supports a requirement to evaluate these mechanisms with qualified nonliving measurement infrastructure; it does not select hardware, thresholds or a physical fallback and does not advance M14/M15, G2/G3 or any other biological/clinical gate.

- Every value, fault, threshold, noise stream and time is an invented dimensionless software quantity.
- Seeded streams do not demonstrate physical sensor independence, actuator-meter accuracy, calibration traceability or uncertainty.
- Frozen supplement and actuator isolation are software accounting policies, not hardware-safe states, operating instructions or validated recovery procedures.
- The shadow shares the plant's nominal model. Model error, drift, delays, saturation, simultaneous faults and unmodelled common dynamics can cause missed or false innovations.
- Endpoint-inclusive sample accounting and next-row policy activation are reporting conventions, not physical latency measurements.
- No biological measurements, physiological calibration, machine controls, procurement, external contact or gate movement are established.

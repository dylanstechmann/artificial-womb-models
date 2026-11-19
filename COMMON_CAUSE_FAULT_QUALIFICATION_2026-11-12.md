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

## Held-out fault detector benchmark

The benchmark measures whether each detector raises its first alarm in time to identify an injected event. It runs the `synthetic` variant with the original thresholds and confirmation count. For each of 12 new noise seeds, it runs one control and one separate challenge for each configured fault. Both detectors see the same noise draws and event schedule. Sensor and actuator-meter noise standard deviations are scaled together by 1×, 2× and 4×.

Each fault keeps its configured magnitude and duration. Its start is shuffled across eligible grid times, excluding time zero and all starts in the source fixture. The benchmark samples starts without replacement for each template until its eligible times are exhausted. Across noise levels it reuses the same standardized noise draws and timings.

| Noise | Detector | Events detected | Events missed | Controls with a false alarm | Median delay on detections |
|---:|---|---:|---:|---:|---:|
| 1× | Sensor disagreement | 12/36 | 24 | 0/12 | 0.5 |
| 1× | Balance-augmented | 36/36 | 0 | 0/12 | 0.5 |
| 2× | Sensor disagreement | 11/36 | 25 | 2/12 | 0.5 |
| 2× | Balance-augmented | 33/36 | 3 | 2/12 | 0.5 |
| 4× | Sensor disagreement | 2/36 | 34 | 12/12 | 0.5 |
| 4× | Balance-augmented | 2/36 | 34 | 12/12 | 0.5 |

At 1× noise, all 12 disagreement detections were primary-only biases. The augmented detector also caught all 12 common biases and all 12 actuator offsets. At 4× noise, its first alarm preceded the injected fault in 34 of 36 challenges. The median delay of 0.5 dimensionless time units at that level describes only its two credited detections.

A detection requires the first confirmation to fall between the injected start and end, inclusive, and to precede the first confirmation in the paired control if that control alarms. Premature, coincident-control, late and absent alarms all count as misses. Delay runs from event onset to the confirming observation. Ground-truth fault times are used for scoring after simulation. These counts describe 12 paired software seeds and one simulated variant.

```sh
PYTHONPATH=src python -m wombmodels benchmark-fault-detectors --config examples/common_cause_fault_fixture.json --replicates 12 --out benchmark-results
PYTHONPATH=src python -m wombmodels verify-bundle --strict --bundle benchmark-results
```

`benchmark_runs.csv` records each of the 288 runs, including the first alarm in the paired control. `benchmark_report.json` gives detection counts and delays by fault type. `REPORT.md` summarizes the six comparisons. The bundle also contains the original configuration, the rerun command and the file hashes.

### Threshold calibration on separate controls

In the original benchmark, both detectors alarmed in every no-fault control at 4× noise. This follow-up asks whether raising the amplitude thresholds can reduce false alarms while retaining sensitivity. Codex ran the comparison on the repository’s dimensionless T29 simulator for this personal learning project.

For each detector and noise level, the simulator ran the same 12 calibration controls at threshold multipliers of 1, 2 and 4. Each multiplier applies to all three amplitude thresholds. The smallest multiplier with zero control alarms advances to evaluation. If every candidate alarms, the largest multiplier advances and the report flags the missed calibration target. The two-sample confirmation rule stays fixed.

The evaluation used 12 fresh noise seeds and reshuffled eligible onset times. Both policies saw the same noise, injected faults and paired controls. Each row below compares 36 injected faults and 12 controls per detector and policy. The totals of 216 calibration runs and 576 evaluation runs include repeated use of the same noise streams across settings.

| Simulated noise | Selected threshold multiplier (both detectors) | Disagreement detections, fixed → calibrated | Balance-augmented detections, fixed → calibrated | Controls with an alarm, fixed → calibrated (each detector) |
|---|---:|---:|---:|---:|
| 1× | 1× | 12/36 → 12/36 | 36/36 → 36/36 | 0/12 → 0/12 |
| 2× | 2× | 12/36 → 12/36 | 36/36 → 36/36 | 0/12 → 0/12 |
| 4× | 4× | 2/36 → 11/36 | 5/36 → 25/36 | 12/12 → 0/12 |

At 4× noise, the calibrated balance-augmented detector caught all 12 primary biases, all 12 shared biases and only **1 of 12 actuator offsets**. Its median delay among the 25 detections was 0.5 dimensionless time units. The 12 quiet evaluation controls describe this seed set. The experiment assumes a known simulated noise level and supports conclusions only about this fixture.

```sh
PYTHONPATH=src python -m wombmodels benchmark-fault-detectors --config examples/common_cause_fault_fixture.json --replicates 12 --calibrate-thresholds --out calibrated-benchmark
PYTHONPATH=src python -m wombmodels verify-bundle --strict --bundle calibrated-benchmark
```

`calibration_runs.csv` records each candidate’s first alarm on each calibration seed. `benchmark_runs.csv` identifies the policy and multiplier on each evaluation run. The JSON report includes per-fault counts, delays and the calibration target outcome. The reproduction plan records the comparison flag and replicate count.

### Separate actuator threshold

In the preceding 4× noise experiment, shared calibration raised the actuator threshold to 0.40 for an injected offset of 0.35. On replay, the actuator residual never exceeded that threshold on two consecutive samples in any of the eleven missed windows. This suggested testing whether the meter could use a lower threshold while the two sensor thresholds stayed at their fitted values.

Codex ran both policies on the balance-augmented detector. First, it fitted the shared multiplier on the same 12 no-fault calibration seeds as before. It then held the disagreement and balance thresholds fixed and tried actuator multipliers of 1, 2 and 4 on those controls. Both stages scored alarms from the complete detector, including confirmations caused by successive triggers on different channels. The smallest multiplier with zero control alarms advanced. If every candidate alarms, the benchmark uses 4 and flags the missed target.

Evaluation used 32 fresh seeds and reshuffled fault windows. Each policy saw identical challenges and a noise-matched control for each seed and noise level. The 216 calibration runs and 768 evaluation runs include repeated use of seeds across settings. The arrows below show the change from shared calibration to a separately fitted actuator threshold.

| Simulated noise | Sensor multiplier | Actuator multiplier | Actuator offsets caught | All faults caught | Controls with an alarm |
|---|---:|---:|---:|---:|---:|
| 1× | 1× | 1× → 1× | 32/32 → 32/32 | 96/96 → 96/96 | 0/32 → 0/32 |
| 2× | 2× | 2× → 1× | 32/32 → 32/32 | 96/96 → 96/96 | 0/32 → 0/32 |
| 4× | 4× | 4× → 1× | 5/32 → 32/32 | 68/96 → 94/96 | 0/32 → 1/32 |

At 4× noise the separate actuator threshold recovered 27 previously missed offsets. For the five offsets both policies caught, the median delay fell from 2.5 to 0.5 dimensionless time units. Both policies caught all 32 primary biases. Shared-bias detections fell from 31 to 30. In the lost case, the challenge and its no-fault control both first alarmed at time 27.5, so the paired scoring rule denied credit. These counts describe the simulated offsets, noise model and observation horizon in this fixture.

```sh
PYTHONPATH=src python -m wombmodels benchmark-fault-detectors --config examples/common_cause_fault_fixture.json --replicates 32 --compare-actuator-thresholds --out actuator-comparison
PYTHONPATH=src python -m wombmodels verify-bundle --strict --bundle actuator-comparison
```

The CSV records carry both multiplier values. The JSON and Markdown reports also show which matched faults each policy detected and which matched controls raised a false alarm.

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

# Actuator confirmation under persistent noise and short offsets

Comparing alarm rules by whether they confirm **before the offset ends** changes the result for short events. In the independent-noise case, the two-sample rule detected 508 of 512 one-unit offsets before they ended. The three-sample rule detected 6 in time, although the existing endpoint-inclusive score credited 511.

## False alarms per 40-unit control run

| Meter noise lag-one correlation | Current rule | Separate two-sample actuator | Separate three-sample actuator |
|---:|---:|---:|---:|
| 0.0 | 5/512 | 5/512 | 1/512 |
| 0.5 | 46/512 | 46/512 | 6/512 |
| 0.9 | 109/512 | 109/512 | 58/512 |

The separate two-sample rule and the current rule had the same counts in this actuator-only comparison. Three samples reduced false alarms at each correlation. At 0.9, the three-sample rule still alarmed in 11.3% of the control runs.

## Detection before the offset ends

Each cell gives the number of detections before the offset ended, followed by the endpoint-inclusive count in parentheses. Each condition has 512 offsets. The two-sample column uses the separate actuator counter.

| Meter noise lag-one correlation | Offset duration | Two samples | Three samples |
|---:|---:|---:|---:|
| 0.0 | 0.5 | 6 (508) | 0 (6) |
| 0.0 | 1.0 | 508 (508) | 6 (511) |
| 0.0 | 3.0 | 508 (508) | 511 (511) |
| 0.5 | 0.5 | 5 (493) | 0 (5) |
| 0.5 | 1.0 | 493 (493) | 5 (508) |
| 0.5 | 3.0 | 493 (493) | 508 (508) |
| 0.9 | 0.5 | 2 (450) | 0 (4) |
| 0.9 | 1.0 | 450 (450) | 4 (479) |
| 0.9 | 3.0 | 450 (450) | 479 (479) |

Detection still requires the first alarm to precede any alarm in the matched control. The simulator records the fault at both sample endpoints and applies it during integration up to the end. An endpoint alarm can therefore earn detection credit with zero active interval left. A streak can include a crossing immediately before onset, so a short offset can occasionally receive credit under the three-sample rule. [Existing scoring rule](https://github.com/dylanstechmann/artificial-womb-models/blob/83856bdfefe84323f3272f907ec8b7307b413ffc/src/wombmodels/fault_benchmark.py#L66) · [Integrated fault interval](https://github.com/dylanstechmann/artificial-womb-models/blob/83856bdfefe84323f3272f907ec8b7307b413ffc/src/wombmodels/whole_path_twin.py#L124)

## Method

Codex ran this follow-up on the artificial dimensionless fixture at `83856bdfefe84323f3272f907ec8b7307b413ffc`. It used 512 fresh seed groups and 81 half-unit samples per run. Onsets were reshuffled from the original grid. Each group shared the same onset and noise draws across the three rules and three offset durations. The positive offset magnitude was 0.35. The disagreement and balance thresholds were 0.48, and the actuator threshold was 0.10.

The actuator meter noise was stationary Gaussian AR(1), with lag-one correlation set to 0.0, 0.5 or 0.9 and marginal standard deviation fixed at 0.04. The sensor standard deviation was 0.08. These correlations are synthetic sensitivity cases. The comparison holds thresholds fixed and characterizes offsets of one magnitude. Alarm timer research derives consecutive crossings from the joint distribution of the samples. Transient detection research evaluates misses during a finite fault and false alarms over a reference window. [Tulsyan et al.](https://dais.chbe.ubc.ca/assets/preprints/2017J5_Tulsyan_AIChE.pdf) · [Mana et al.](https://doi.org/10.1080/07474946.2023.2171056)

The script validates the published input bundle and reproduces the first-alarm results from 128 runs at the fitted 4× noise thresholds before applying correlation. The output has 6,144 rows, each with the first alarm, outcome and detection delay under all three rules. A separate calculation verified all 18,432 scores against their corresponding control and fault window. A direct simulator check reproduced 1,092 first-alarm results with correlation and fallback active inside the simulator.

## Review findings for the next benchmark

- Report before-end and endpoint-inclusive detection together. The next comparison can include near-threshold offsets and compare confirmation counts at matched false-alarm rates, with fitting and evaluation on disjoint seeds. Keep the separate two-sample comparator. In the original study, splitting the sensor and actuator counters accounted for all 19 delays on matched sensor-bias detections. Increasing the separate actuator count from two to three accounted for the actuator delays and the five fewer control alarms. [Prior comparison](../alarm-confirmation/REPORT.md)
- Assert that the separate actuator fit changes evaluation outcomes in the existing CLI integration test. The test passed when an in-memory change evaluated both policies with the shared actuator threshold. The unmodified fixture has two 2× actuator detections unique to the separately fitted threshold. [Integration test](https://github.com/dylanstechmann/artificial-womb-models/blob/83856bdfefe84323f3272f907ec8b7307b413ffc/tests/test_fault_benchmark.py#L237)
- Put an opt-in comparison through the simulator's confirmation decision and record the exact confirmation counts, fit, seed block and paired delays in the artifact. Count the comparison's simulation and calibration work explicitly against the benchmark's existing budget. [Simulator decision](https://github.com/dylanstechmann/artificial-womb-models/blob/83856bdfefe84323f3272f907ec8b7307b413ffc/src/wombmodels/common_cause_fault.py#L231) · [Benchmark work limit](https://github.com/dylanstechmann/artificial-womb-models/blob/83856bdfefe84323f3272f907ec8b7307b413ffc/src/wombmodels/fault_benchmark.py#L245)

From the root of this checkout, run with Python 3.12 and an unused output path.

```sh
PYTHONPATH=src:studies/alarm-confirmation \
  python3 studies/alarm-persistence/stress.py \
  studies/benchmark-inputs/actuator-thresholds-83856bd.zip /tmp/alarm-persistence-runs.csv
```

[Before-end summary](summary.csv) · [Summary script](summarize.py) · [Stress replay](stress.py) · [Run records](runs.csv)

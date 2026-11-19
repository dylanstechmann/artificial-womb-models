# Actuator alarm confirmation at 4× simulated noise

Three consecutive actuator threshold crossings produced **0/512 false alarms**, compared with **5/512** under the current rule. Credited actuator-offset detections rose from **509/512 to 512/512**. The 509 offsets both rules detected took exactly 0.5 additional dimensionless time units to confirm.

| Confirmation rule | False alarms / controls | Actuator offsets detected | Primary biases detected | Shared sensor biases detected |
|---|---:|---:|---:|---:|
| Current two-sample combined rule | 5/512 | 509/512 | 508/512 | 499/512 |
| Separate actuator counter, two samples | 5/512 | 509/512 | 508/512 | 499/512 |
| Separate actuator counter, three samples | 0/512 | 512/512 | 510/512 | 500/512 |

The three-sample rule added credit for three actuator offsets, two primary biases and one shared sensor bias. In five of these cases it suppressed a pre-fault alarm. In the sixth it suppressed an alarm in the matched control. Every event the current rule detected still received credit. Among the sensor biases credited under both rules, the median delay was 0.5 under each. Eight of the 508 matched primary-bias alarms and 11 of the 499 matched shared-bias alarms arrived later. The largest added sensor-bias delay was 2.5 dimensionless time units. The zero control alarms give a one-sided 95% binomial upper bound of 0.58% per 40-unit run under the simulated noise model.

## Why compare these rules

The single high-noise control alarm in the previous benchmark came from actuator residuals of 0.10578 and 0.10708 at times 27.0 and 27.5, both above the 0.10 threshold. Both sensor residuals were below threshold in those two control samples. That motivated testing a longer confirmation window specifically for the actuator meter. [Prior synthetic benchmark](https://github.com/dylanstechmann/artificial-womb-models/blob/83856bdfefe84323f3272f907ec8b7307b413ffc/COMMON_CAUSE_FAULT_QUALIFICATION_2026-11-12.md#separate-actuator-threshold)

Adnan, Izadi and Chen describe an on-delay as a run of consecutive threshold crossings on one monitored variable and evaluate it using false alarms, misses and detection delay. Pollak describes monitoring separate streams and raising a system alarm when one chart signals. His analysis applies to particular control charts. The simulation here estimates the whole detector's outcomes directly. [Adnan et al., *Computing Detection Delays in Industrial Alarm Systems*](https://skoge.folk.ntnu.no/prost/proceedings/acc11/data/papers/1262.pdf) · [Pollak, *The Annals of Statistics*](https://doi.org/10.1214/20-aos1968)

## Design and reproduction

Codex found the references with Exa and ran this follow-up on the project's artificial dimensionless fixture. The current rule confirms when at least one residual exceeds its threshold at each of two consecutive samples. Different residuals may supply those crossings. The two alternatives use a two-sample sensor counter shared by the disagreement and balance residuals. A separate actuator counter confirms after two or three consecutive meter crossings. Either counter can independently confirm an alarm.

The benchmark used the fitted 4× noise settings from commit `83856bdfefe84323f3272f907ec8b7307b413ffc`. The disagreement and balance thresholds were both 0.48, and the actuator threshold was 0.10. The sensor and actuator noise standard deviations were 0.08 and 0.04. The study targeted this one Gaussian-noise condition because it produced the previous false alarm. All three rules saw the same 512 fresh sets of noise streams and fault timings. Each set included a no-fault control and one isolated run per fault kind. The first seed was `20261453`, with four streams per set. The first alarm earned detection credit when it fell within the fault window and preceded any alarm in the matched control.

The replay checks the existing rule against all 128 published runs at the selected noise and thresholds before evaluating the new cohort. It computes each first alarm from samples before that policy's fallback can affect the run. A separate check applied each rule inside the simulator with fallback enabled and reproduced every first alarm and score across all 2,048 runs. The input bundle SHA-256 is `aacf3d4c98d718c5585519c691842a6b04df16f6229b9a6f6822062e694af239`.

From the root of this checkout, run with Python 3.12 and paths to the artifacts in this workspace.

```sh
PYTHONPATH=src python3 studies/alarm-confirmation/replay.py \
  studies/benchmark-inputs/actuator-thresholds-83856bd.zip /tmp/confirmation-runs.csv
```

[Replay script](replay.py) · [Held-out run records](runs.csv)

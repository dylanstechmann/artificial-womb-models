# T28 sensor disagreement and freeze-fallback qualification (2026-11-01)

This AI-assisted software experiment tests a named engineering discriminator: can an independent synthetic bulk-stock sensor expose declared controller-sensor faults and change the control response without altering the canonical no-fault trajectory?

Run `wombmodels sensor-failover-model --config examples/sensor_failover_fixture.json --out <new-directory>`. The command compares single-sensor control with independent-sensor disagreement and a latching frozen-supplement fallback. It publishes per-sample sensor observations, all six trajectories, variant comparisons and a receipt-backed report.

## Frozen policy and result

The primary and secondary sensor streams use independent seeded noise. A missing primary reading or an absolute primary/secondary residual above the declared threshold counts as disagreement. Two consecutive disagreements trigger detection and freeze the synthetic supplement at its pre-detection value. The fallback does not select a replacement sensor, infer which sensor failed, or observe internal tissue.

For each of the three fixture variants, the run detects 8 of 10 samples inside declared fault windows, with the first sample of each fault window intentionally below the two-sample confirmation requirement. It reports zero false-alarm samples in this fixture and first detection at dimensionless time 4.5. The fallback remains active after the fault windows; this is reported, not treated as automatic recovery. These counts are one deterministic fixture result, not a detection probability or hardware alarm qualification.

Regression tests establish exact no-fault single-sensor trajectory equality with T21 for every shared output column. Both modes receive identical noise sequences and identical readings before their trajectories diverge. After fallback, different physical states naturally produce different sensor readings. Additional tests cover bias, dropout, confirmation, latching, false alarms, frozen supplement versus continuing internal state, malformed inputs, work-budget failure without publication, deterministic output and strict bundle verification.

## Engineering consequence

The experiment supplies a small, inspectable fault register for future review: declared controller bias and dropout, independent-sensor disagreement, confirmation delay, false alarms, fallback persistence and unobserved internal state. It supports a requirement to evaluate independent measurement and failure detection; it does not select a sensor, alarm threshold or physical fallback.

The next actual dependency remains a qualified measurement capability: sensor independence, calibration traceability, uncertainty, fault injection and safe fallback behavior must be established by responsible specialists using real nonliving measurement infrastructure. No laboratory, instrument feed or independent reviewer is identified by this work. This software result does not satisfy M14 or M15 and does not advance G2/G3 or any other biological/clinical gate.

## Limits

- Every quantity, threshold, fault and time is an invented dimensionless software value.
- Independent seeded streams do not demonstrate physical sensor independence or calibrated uncertainty.
- Freezing a synthetic supplement is not a hardware-safe state or operating instruction.
- Common-cause sensor faults, actuator faults, physical sensor drift and real measurement failures are not tested.
- The fallback cannot detect or repair hidden internal delivery, tissue-use or developmental failure.
- No biological measurements, physiological calibration, machine controls, procurement, external contact or gate movement are established.

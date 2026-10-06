# Methods and output interpretation

## Evidence mapping

`config/evidence.json` is a bounded, manually reviewed ledger with review date 2026-10-06. It is not a systematic literature search. Each source keeps its class, species/model, actual developmental interval, stage coverage and excluded inference. Each claim cites known source IDs and preserves species and stages. Regulator discussions and institutional announcements cannot be upgraded into peer-reviewed experimental results by the validator.

Three claims are mandatory gaps: complete human gestation, surrogacy replacement and fewer congenital defects. A stage map shows records by species; it has no readiness percentage or weighted capability score. Requirements trace relevant evidence and unresolved questions. `partially_documented` describes some relevant evidence, not a satisfied engineering or clinical requirement. The ledger does not mathematically establish absence of evidence outside its selected sources.

## Abstract exchange fixture

All variables and coefficients are artificial and dimensionless. The stocks `S` (substrate) and `W` (waste) are abstract accounting quantities. `R` is a synthetic power reserve, distinct from those stocks. Powered exchange indicator `p` is one with wall power or positive reserve during an outage, and zero otherwise.

```text
dS/dt = p*u - k*S
dW/dt = k*S - p*c*W
dR/dt = -b  during backup use; otherwise 0
```

`u`, `k`, `c` and `b` are invented fixture rates. `R` is neither recharged nor replenished in this first release. The source of power determines abstract input and clearance; conversion continues when power is absent. These choices define a software test problem and are not a physiological description.

Constant-coefficient intervals use closed-form analytic transitions. Separate formulas handle zero conversion, zero clearance, and equal conversion/clearance rates; `expm1` reduces cancellation near equal rates. The solver partitions time at output samples, outage boundaries, monitor-fault boundaries and exact reserve-depletion events. Event intervals are half open: `[start, end)`. A row at a start boundary has the new event state; at an end boundary the event has ended. Numerical values use IEEE floating-point arithmetic. Nonfinite or substantially negative solutions produce a controlled error; tiny roundoff negatives may be clamped to zero.

With cumulative supplied amount `I`, converted amount `K`, cleared amount `C` and reserve usage `B`, the reported residuals are:

```text
substrate residual = S - S_initial - I + K
waste residual     = W - W_initial - K + C
total residual     = S + W + C - S_initial - W_initial - I
reserve residual   = R + B - R_initial
```

The interval fluxes follow the analytic stock transitions. Their identities provide internal numerical accounting checks. Small residuals establish accounting consistency in these equations; they do not validate model structure, parameter values or biology. Model discrepancy cannot be estimated without external measurements.

## Synthetic monitoring benchmark

The simulated sensor reads `S` plus seeded Gaussian fixture noise. Artificial bias intervals add a constant; dropout intervals produce a missing reading. With `requires_exchange_power` enabled, loss of both wall power and reserve also removes sensor readings, explicitly illustrating a shared power dependency.

The software alarm uses a missing reading or the absolute difference between the synthetic reading and **known simulated truth** exceeding an invented residual threshold. This is an oracle-residual test fixture. Real monitoring cannot usually access true substrate state, so this algorithm must not be presented as a deployable detector.

The monitor samples only at scheduled output timestamps, including the final endpoint. Extra integration rows at event boundaries have `sensor_sampled=false` and no reading or alarm; they do not consume random noise draws or count toward detector metrics. The output includes true/false positive and negative counts, recall, false-positive rate, and dimensionless delays from modeled fault onset to the first sampled alarm. Faults between samples can be missed. Consecutive loss-of-power segments form one fault episode. Undefined ratios and undetected faults are `null`. The first alarm within an interval can reflect overlapping faults; it does not identify a cause. These samples are not independent experiments, and noise realization and sampling cadence affect the metrics. The metrics establish software behavior under the supplied fixture, not reliability rates, clinical alarm performance or safe biological limits.

Exchange efficiency and consumption can be observationally confounded. A monitored concentration alone cannot identify every transport process or establish tissue delivery, growth, placentation, immune/endocrine function, organ maturity or a favorable long-term outcome. None of those mechanisms are modeled here.

## Dimensionless parameter observability

`identifiability-report` takes the original fixture configuration and the `trajectory.csv` produced by `simulate`. It requires the adjacent simulation receipt to bind those exact input and trajectory bytes, verifies every scheduled timestamp, and checks all event times and modeled power labels against the source configuration. Fits use scheduled substrate sensor readings and the modeled power schedule; they ignore hidden substrate truth, integrated fluxes and the generator's chosen rates.

For each pair of adjacent usable readings, the method approximates the integrated exchange balance:

```text
change in observed substrate ≈ powered_input × powered-time
                             − conversion × trapezoidal observed-substrate area
```

The integral-balance diagnostic uses ordinary least squares to estimate two invented rates. It reports normalized design rank, feature correlation and condition number. Because each interval's observed change and trapezoidal predictor both use its endpoint readings, its residual score is a balance-consistency diagnostic, not a forecast.

A complementary state model uses `dS/dt = u × powered_state(t) − k × S`, with a nonnegative initial state, powered input `u`, and conversion rate `k`. It propagates this one-stock model exactly over the fixture's piecewise-constant power schedule. A bounded one-dimensional profile search over `k` solves nonnegative least squares for initial state and input. The fit assumes independent Gaussian sensor error at the standard deviation declared in the fixture; scheduled readings during known bias intervals are excluded, and dropouts stay missing. The profile covariance is a local linear approximation. A 95% prediction interval combines that parameter covariance with the declared observation noise and can be unreliable near boundaries or when the design is weakly identified.

The prospective forecast fits only unbiased scheduled observations with `time ≤ 0.7 × duration`; this cutoff is based on dimensionless time, not a fraction of usable intervals. It propagates the fitted state from the first training observation across the full modeled schedule and scores only later unbiased readings. Later readings never update the state or form predictors. Forecast RMSE, MAE, mean error, interval coverage and width are compared with a baseline that carries the last training observation forward. The temporal split is still one synthetic trajectory, not independent experimental validation.

The model assumes the fixture's power-source labels are known. Sensor noise, missed samples, synthetic fault injection, trapezoidal approximation and model mismatch can change the estimates and conditioning. A numerical estimate or full-rank design does not validate assumptions, demonstrate structural identifiability beyond these two parameters, or establish biological observability. There is no biological calibration, statistical confidence interval, hardware state inference or connection to a controller.

## Cadence, noise and event-timing design sweep

`design-sweep` runs nine bounded cadence/noise combinations: requested output-step factors of 0.5, 1 and 2 crossed with sensor-noise multipliers of 0, 1 and 2. If the source configuration contains monitor faults, each combination is run both with the configured bias/dropout intervals and with those injected monitor faults removed. If it contains any outage or monitor fault, each combination also uses a reflected event-timing profile, for up to 36 design conditions. Reflection maps every half-open interval `[start, end)` to `[duration-end, duration-start)`, preserving each interval's length and reflecting the schedule across the fixture midpoint. The comparison changes event location relative to the initial fixture state and output cadence; it is a deterministic timing sensitivity case, not a sampled outage distribution. Wall outages remain in both monitor-fault profiles, as do missing readings caused by the shared power dependency. Multipliers use the configuration's noise level as the reference; if that value is zero, the report records a small dimensionless reference derived from the fixture residual threshold. Each design condition uses 1–20 deterministic seeds, subject to a four-million scheduled-sample budget for the whole command. The fixture's maximum output resolution and noise bounds still apply, so a requested factor can be capped; both the requested factor and actual dimensionless setting are recorded.

Each synthetic trajectory is fit both with the integral-balance regression and with the nonnegative noise-aware state model. Generator-known rates are not passed into either fit; they are used only afterward to score parameter recovery. The prospective state forecast is trained through 70% of dimensionless duration and scored on later sensor values that were not used to fit parameters or as predictors. A last-training-reading baseline and approximate 95% prediction intervals are reported beside forecast error. The same-run and leave-one-seed-out balance residuals are retained for comparison but are labeled as consistency diagnostics because their interval predictors include observed endpoints. They are not predictive holdouts. Design summaries report forecastable replicate counts, median/nearest-rank 90th-percentile RMSE, baseline RMSE, nominal interval coverage and width. All designs share the same model family and event configuration; this is software robustness analysis, not independent experimental validation. Other summaries include the integral-fit estimable fraction, finite condition numbers, residual scale and synthetic parameter-recovery error. Replicate percentiles are descriptive and are not confidence intervals. A lower error, higher nominal coverage or better-conditioned design does not establish biological observability or recommend real measurement cadence.

## Reproducibility and publication

Commands preserve the exact original input bytes. `receipt.json` records their SHA-256, package/Python versions, implementation file hashes, and each output's SHA-256 and byte count. The source URLs in the evidence ledger are bibliographic links, not archived or hash-pinned copies of the external pages. Re-review is necessary when expanding or updating a claim.

No clock timestamp enters offline artifacts, so repeated identical runs using the same implementation and Python environment produce identical bytes. The output directory is created exclusively; existing destinations, including empty directories, are rejected. Artifact files are published atomically using same-filesystem hard links from a staging directory; the receipt is published last. The **entire directory is not atomically renamed**. A failed publication can leave an incomplete destination without a receipt. Consumers must require and verify all receipt hashes before accepting a bundle; choose a fresh destination for a retry. File systems without hard-link support raise an error rather than weakening publication guarantees.

Input JSON is capped at 2 MB, 64 nested container levels and 256 digits per integer. Duplicate keys and nonfinite numeric literals are rejected, simulations cap output/event counts, and configurations cannot select executable code or device endpoints. The optional loopback ResearchDesk request has a 30-second timeout and a 2 MB response cap, applies the same JSON limits, disables environment proxies and rejects redirects.

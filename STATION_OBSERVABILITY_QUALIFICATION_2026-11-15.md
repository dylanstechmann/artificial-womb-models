# T32 shared-station observability qualification (2026-11-15)

**Roadmap task:** T32, registered by decision **D20**.
**Status:** Qualified as a deterministic, artificially dimensionless software counterexample and operational measurement-requirement addendum. No biological or clinical gate advances; no hardware reliability, physical capacity, procurement or external-contact authorization is established.

## Scope and named discriminator

T31 established concurrent transition-demand waiting and stage overshoot, but left delay cause unattributable from unit-local channels. T32 asks a sharper question: when unit B has exactly the same readiness demand `d`, wait `s`, service start `d+s`, service end `d+2s`, complete unit-local twin trajectory and stage overshoot, can shared-station observations distinguish queue contention from station outage?

Two worlds are evaluated for every interface variant:

- **`queue_only`:** A and B both demand at `d`; there is no station outage. FIFO serves A over `[d,d+s)` and B over `[d+s,d+2s)`. B's ground-truth delay cause is `queue`.
- **`outage_only`:** A demands at `d-s` and finishes at `d`; B demands at `d`; the station has an outage over `[d,d+s)` and serves B over `[d+s,d+2s)`. B's ground-truth delay cause is `station_outage`.

The module calls T31's unmodified readiness evaluation, FIFO scheduler and overshoot calculation, and checks that its coupled wall run preserves T31's canonical fluidic trajectory. T31's dedicated control and canonical fixture remain unchanged. T23's one-way wall supplies the additional `wall_strain` and `wall_damage` local channels without changing fluidics.

Command:

```sh
PYTHONPATH=src python -m wombmodels station-observability-model --config examples/station_observability_fixture.json --out <new-dir>
```

The command preserves exact input bytes as `source_config.json`; publishes both B local series per variant, the event and station-observation tables, a structured report, `REPORT.md`, a relocatable reproduction plan and a receipt. Strict verification checks bytes only; it does not rerun the model or establish scientific validity.

## Delay-matched numerical result

The frozen service time is `s = 3.0`; the readiness threshold is 0.25. All times and overshoots are invented dimensionless software quantities.

| Variant | B demand `d` | Outage-world A demand `d-s` | B wait | B service start | B service end | B stage overshoot (both worlds) |
|---|---:|---:|---:|---:|---:|---:|
| living_interface | 12.5 | 9.5 | 3.0 | 15.5 | 18.5 | 0.07621185758956822 |
| staged | 17.5 | 14.5 | 3.0 | 20.5 | 23.5 | 0.053517864711518426 |
| synthetic | 32.0 | 29.0 | 3.0 | 35.0 | 38.0 | 0.024255711822430026 |

For every variant, the two complete B local CSV series are bit-for-bit identical. This includes all boundary observables, `wall_strain`, internal deep receipt, cumulative unserved amount, progression, reserve, supplement, controller reading and wall damage. Demand time, wait duration, service start/end and stage overshoot are also exactly equal. Therefore `unit_local_separates = false`: not even internal per-unit D/M/P channels can identify which world produced B's delay.

## Station-side discriminator

Station channels are sampled on the 0.5 output grid from `d` through `d+2s`. During the attribution window `[d,d+s)`, the observations are:

| Channel | `queue_only` | `outage_only` | Separates? |
|---|---|---|---|
| `station_operational_state` | `available` | `outage` | yes |
| `station_active_unit` | `serving_unit_A` | `idle_during_outage` | yes |
| `station_unavailable_flag` (busy or outage) | `true` | `true` | **no** |

Both independent structural channels separate the worlds. The coarse unavailable flag remains identical throughout the matched window, so `lumped_unavailable_separates = false`. A shared station therefore must not merely report "unavailable" or "not ready": it must distinguish active-service occupancy from fault/outage state.

## Operational measurement addendum

The report's bounded `measurement_addendum` is an operational shared-station addendum **alongside**, not a mutation of, T24/T25's frozen architecture-discrimination specification. It requires:

1. independently calibrated `station_operational_state` (`available` versus `outage`, independent of occupancy);
2. calibrated `station_active_unit` occupancy and unit identity, with synchronized station/unit clocks;
3. verification that available, outage, active-service and idle states remain distinguishable.

The coarse `station_unavailable_flag` is explicitly insufficient. Calibration is required for every operational channel. Every channel price and the total price are `null`. No quote, purchase, procurement route, hardware selection or external engagement is authorized.

## Verification and limits

The canonical bundle has 12 receipt-declared outputs and passes `verify-bundle --strict`. Twenty-five regression tests cover hand-calculated schedules, exact local/event equality, overshoot, unit-local and lumped-channel non-identifiability, both separating station channels, T31 canonical/dedicated behavior, addendum discipline, malformed/duplicate/boolean/nonfinite/out-of-range inputs, work-budget rejection without partial publication, exclusive destinations, determinism, CLI round-trip, exact receipt hashes, strict relocation and tamper behavior.

- This is only an artificially dimensionless counterexample; runtime is not gestational time and no physiological parameters are assigned.
- FIFO, readiness, service duration and outage intervals are modeling conventions, not transition procedures or neonatal readiness criteria.
- Independent station channels are required observations in the model, not demonstrated physical sensors or a hardware reliability claim.
- Two units and one shared station do not establish ten-unit concurrency, facility throughput or physical station capacity.
- No biological measurement, clinical claim, machine control, procurement, external contact or G1/G2/G3/other gate movement is made.

# Theoretical modules and future measured-data contract

These modules turn two research questions into inspectable equations. Their settings are dimensionless code fixtures. A developmental stage label organizes a question; it does not assign a biological mechanism, parameter, or time scale to that stage.

## Transport across two abstract compartments

The transport fixture represents a boundary, an interface stock `c₁`, and a core stock `c₂`:

```text
dc₁/dt = e(cᵦ − c₁) − d(c₁ − c₂) − ℓc₁	dc₂/dt = d(c₁ − c₂) − ℓc₂
```

`e` is boundary exchange, `d` is intercompartment transfer, and `ℓ` is a first-order loss. All quantities are dimensionless. Equal abstract capacities make internal transfer cancel in the discrete inventory. The software reports both state values, the interface-to-core gradient, boundary flux, loss, and the accounting residual. The alternative has their combined capacity and the same single boundary pathway: for `C = (c₁ + c₂)/2`, its equation is `dC/dt = (e/2)(cᵦ − C) − ℓC`. The factor of one half matches exchange per total capacity, so rapid internal mixing approaches this reference. The comparison is a difference in fixture trajectories, not data-driven model selection.

This equation can later be compared with paired boundary and internal measurements. A known boundary and the full core trace alone are still insufficient for globally unique exchange/transfer estimates: at zero initial states, `(e,d,ℓ)` and `(2d,e/2,ℓ)` give the same core equation and trajectory. Spatial measurements at equilibrium also leave a common rate-scale ambiguity. The new `transport-identifiability` command constructs these counterexamples, including distinct transient interface traces, from an [invented fixture](examples/transport_identifiability_fixture.json). Paired transient states can distinguish the illustrated pair; this is not a general identifiability guarantee for noisy or differently structured models. The derivation and future measured-data question are in [interface feasibility](INTERFACE_FEASIBILITY.md).

A biological data contract also needs the actual species, one developmental stage interval, model-system type, independent-unit IDs or an explicit missing-ID label, comparator, assay units, calibration, measurement uncertainty, raw-data license, and hashes. `schemas/developmental-observation.schema.json` records those fields without treating synthetic rows as assays.

## Viscoelastic response

The mechanics fixture uses a Kelvin–Voigt element under piecewise-constant dimensionless stress:

```text
η dε/dt + Eε = σ(t)
```

The exact solution is used between load changes. The report exposes strain over time and the dimensionless strain-response time `η/E` when `E > 0` (the current output calls this `relaxation_time`). An instantaneous linear-elastic response `ε = σ/E` supplies an alternative trajectory. It omits time-dependent strain response and is only a theory contrast. Estimating both parameters from future data requires a calibrated stress history, measured strain over time, independent replicate identities, and enough changing input to separate elasticity from viscosity.

Here `η/E` characterizes response under imposed stress, including creep and
recovery. Under held strain after a step, `dε/dt = 0` and `σ = Eε`; an ideal
Kelvin–Voigt element does not show finite exponential stress relaxation.
Do not equate its time constant with a published stress-relaxation half-time.
The [feasibility strategy](FEASIBILITY_STRATEGY.md) identifies an early mouse
niche source motivating a distinct future loading/observation contract;
this fixture remains uncalibrated.

## Keeping developmental tracks separate

Each fixture names one track: preimplantation, implantation/placentation, postimplantation embryonic development, partial fetal support, transition to neonatal life, or developmental outcomes. The code does not concatenate them. Each future measured record must cite the source used for its staging and keep species and the source's developmental interval intact. A culture-day label cannot be converted to an in-vivo embryonic day without a reviewed mapping.

## Evidence and validation gate

The present modules support model comparison and generate candidate observables. They contain no embryo, animal, patient, device, or organoid measurements. Before a fitted model can make a biological statement, a pinned and licensed dataset must include independent biological units, the prespecified comparator, raw observations or a documented author-summary-only status, calibration and uncertainty, missingness and adverse outcomes, and a frozen group-level split. The model and analysis plan must be frozen before the held-out units are opened. The two synthetic fixtures are method-development scaffolds, not a surrogate for that benchmark.

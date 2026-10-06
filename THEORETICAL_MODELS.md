# Theoretical modules and future measured-data contract

These modules turn two research questions into inspectable equations. Their settings are dimensionless code fixtures. A developmental stage label organizes a question; it does not assign a biological mechanism, parameter, or time scale to that stage.

## Transport across two abstract compartments

The transport fixture represents a boundary, an interface stock `c₁`, and a core stock `c₂`:

```text
dc₁/dt = e(cᵦ − c₁) − d(c₁ − c₂) − ℓc₁	dc₂/dt = d(c₁ − c₂) − ℓc₂
```

`e` is boundary exchange, `d` is intercompartment transfer, and `ℓ` is a first-order loss. All quantities are dimensionless. Equal abstract capacities make internal transfer cancel in the discrete inventory. The software reports both state values, the interface-to-core gradient, boundary flux, loss, and the accounting residual. The alternative has their combined capacity and the same single boundary pathway: for `C = (c₁ + c₂)/2`, its equation is `dC/dt = (e/2)(cᵦ − C) − ℓC`. The factor of one half matches exchange per total capacity, so rapid internal mixing approaches this reference. The comparison is a difference in fixture trajectories, not data-driven model selection.

This equation can later be compared with paired boundary and internal measurements. That comparison is not identifiable from a single bulk concentration alone: an independent input or boundary measurement and a spatially resolved response are needed to distinguish exchange from transfer and loss. A biological data contract also needs the actual species, one developmental stage interval, model-system type, independent-unit IDs or an explicit missing-ID label, comparator, assay units, calibration, measurement uncertainty, raw-data license, and hashes. `schemas/developmental-observation.schema.json` records those fields without treating synthetic rows as assays.

## Viscoelastic response

The mechanics fixture uses a Kelvin–Voigt element under piecewise-constant dimensionless stress:

```text
η dε/dt + Eε = σ(t)
```

The exact solution is used between load changes. The report exposes strain over time and the dimensionless relaxation time `η/E` when `E > 0`. An instantaneous linear-elastic response `ε = σ/E` supplies an alternative trajectory. It omits relaxation and is only a theory contrast. Estimating both parameters from future data requires a calibrated stress history, measured strain over time, independent replicate identities, and enough changing input to separate elasticity from viscosity.

## Keeping developmental tracks separate

Each fixture names one track: preimplantation, implantation/placentation, postimplantation embryonic development, partial fetal support, transition to neonatal life, or developmental outcomes. The code does not concatenate them. Each future measured record must cite the source used for its staging and keep species and the source's developmental interval intact. A culture-day label cannot be converted to an in-vivo embryonic day without a reviewed mapping.

## Evidence and validation gate

The present modules support model comparison and generate candidate observables. They contain no embryo, animal, patient, device, or organoid measurements. Before a fitted model can make a biological statement, a pinned and licensed dataset must include independent biological units, the prespecified comparator, raw observations or a documented author-summary-only status, calibration and uncertainty, missingness and adverse outcomes, and a frozen group-level split. The model and analysis plan must be frozen before the held-out units are opened. The two synthetic fixtures are method-development scaffolds, not a surrogate for that benchmark.
